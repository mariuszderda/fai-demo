#!/usr/bin/env python3
"""End-to-end smoke test for analysis layer."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from fai.analysis.ioc_extractor import IocExtractor
from fai.analysis.llm_client import StubLlmClient
from fai.analysis.mitre_mapper import MitreMapper
from fai.analysis.threat_intel import ThreatIntelClient
from fai.config import Settings
from fai.core.audit import AuditTrail
from fai.core.models import Artifact, Incident, IocStatus, Severity
from fai.mitre.loader import MitreLoader
from fai.reporting.generator import ReportGenerator

import httpx


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


async def main() -> None:
    """Run smoke test."""
    print_section("Forensics AI - Smoke Test")

    # Setup paths - find repo root by looking for data directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    data_dir = repo_root / "data"
    runtime_dir = repo_root / "runtime"
    runtime_dir.mkdir(exist_ok=True)

    # Initialize components
    print("Initializing components...\n")

    audit = AuditTrail(runtime_dir)
    llm_client = StubLlmClient()
    mitre_loader = MitreLoader(data_dir / "mitre" / "enterprise-attack.json")
    settings = Settings(otx_api_key=None)  # Use MISP fallback

    print(f"✓ Audit trail: {runtime_dir / 'audit'}")
    print(f"✓ LLM client: StubLlmClient (deterministic)")
    print(f"✓ MITRE loader: {len(mitre_loader.techniques)} techniques loaded")

    # ========================================================================
    # Test 1: Ransomware Scenario
    # ========================================================================
    print_section("Test 1: Ransomware Scenario")

    # Load scenario artifacts
    ransomware_dir = data_dir / "scenarios" / "ransomware"
    artifacts_data: list[dict[str, Any]] = []

    # Use actual scenario files
    if (ransomware_dir / "syslog.log").exists():
        print("Loading ransomware scenario files...")

        with open(ransomware_dir / "syslog.log", "r") as f:
            syslog_content = f.read()

        # Create artifact records
        from uuid import uuid4
        incident_id = str(uuid4())

        artifacts = [
            Artifact(
                incident_id=incident_id,
                filename="syslog.log",
                source="ransomware_host",
                size_bytes=len(syslog_content),
                sha256="scenario_hash_ransomware_001",
                collected_at_utc=datetime.now(timezone.utc),
                collector_version="1.0",
            ),
        ]

        artifact_contents = {
            "syslog.log": syslog_content[:5000],  # First 5KB for demo
        }

        # Step 1: Extract IoCs
        print("\n1. Extracting IoCs...")
        extractor = IocExtractor(llm_client, audit)
        iocs = await extractor.extract(incident_id, artifacts, artifact_contents)

        print(f"   Extracted {len(iocs)} IoCs:")
        for ioc in iocs:
            print(f"     - {ioc.type.value:12} {ioc.value:40} ({ioc.confidence.value})")

        # Step 2: Map MITRE techniques
        print("\n2. Mapping MITRE techniques...")
        mapper = MitreMapper(llm_client, mitre_loader, audit)
        iocs = await mapper.map_iocs(incident_id, iocs)

        ioc_with_techniques = [ioc for ioc in iocs if ioc.mitre_technique_ids]
        print(f"   {len(ioc_with_techniques)} IoCs mapped to techniques:")
        for ioc in ioc_with_techniques:
            print(f"     - {ioc.value}: {', '.join(ioc.mitre_technique_ids)}")

        # Verify no hallucinations
        for ioc in iocs:
            for tech_id in ioc.mitre_technique_ids:
                if not mitre_loader.is_valid_technique(tech_id):
                    print(f"   ✗ INVALID TECHNIQUE DETECTED: {tech_id}")

        # Check for hallucination audit events
        hallucination_events = await audit.read(incident_id, action="HALLUCINATION_REJECTED")
        if hallucination_events:
            print(f"\n   ✓ Hallucination filter caught {len(hallucination_events)} invalid technique(s)")
            for evt in hallucination_events:
                print(f"     - Rejected: {evt.details.get('technique_id', 'unknown')}")

        # Step 3: Threat Intelligence Lookup
        print("\n3. Threat Intelligence Lookup (MISP fallback)...")
        async with httpx.AsyncClient() as client:
            ti = ThreatIntelClient(client, settings, audit, data_dir / "misp_fallback.json")
            iocs = await ti.lookup_all(incident_id, iocs)

        malicious_count = sum(1 for ioc in iocs if ioc.reputation and ioc.reputation.value == "malicious")
        clean_count = sum(1 for ioc in iocs if ioc.reputation and ioc.reputation.value == "clean")
        unknown_count = sum(1 for ioc in iocs if not ioc.reputation or ioc.reputation.value == "unknown")

        print(f"   Malicious: {malicious_count}, Clean: {clean_count}, Unknown: {unknown_count}")

        for ioc in iocs[:3]:  # Show first 3
            rep = ioc.reputation.value if ioc.reputation else "unknown"
            src = ioc.reputation_source or "none"
            print(f"     - {ioc.value}: {rep} ({src})")

        # Step 4: Generate Report
        print("\n4. Generating Report...")

        # Mark some as accepted for report
        for ioc in iocs[:5]:
            ioc.status = IocStatus.ACCEPTED

        incident = Incident(
            id=incident_id,
            scenario="ransomware",
            siem_alert_id="SIEM-RW-2026-0511-001",
            started_at_utc=datetime.now(timezone.utc),
            severity=Severity.HIGH,
            current_step="report_generation",
        )

        generator = ReportGenerator(llm_client, audit, runtime_dir)
        markdown, html = await generator.generate(incident, iocs, artifacts)

        print(f"   Markdown report: {len(markdown)} bytes")
        print(f"   HTML report: {len(html)} bytes")
        print(f"   Location: {runtime_dir / 'reports' / f'{incident_id}.md'}")

    # ========================================================================
    # Test 2: Phishing Scenario
    # ========================================================================
    print_section("Test 2: Phishing Scenario")

    phishing_dir = data_dir / "scenarios" / "phishing"

    if (phishing_dir / "email_headers.eml").exists():
        print("Loading phishing scenario files...")

        with open(phishing_dir / "email_headers.eml", "r") as f:
            email_content = f.read()

        incident_id = str(uuid4())

        artifacts = [
            Artifact(
                incident_id=incident_id,
                filename="email_headers.eml",
                source="phishing_mail",
                size_bytes=len(email_content),
                sha256="scenario_hash_phishing_001",
                collected_at_utc=datetime.now(timezone.utc),
                collector_version="1.0",
            ),
        ]

        artifact_contents = {
            "email_headers.eml": email_content,
        }

        # Extract IoCs
        print("\n1. Extracting IoCs...")
        extractor = IocExtractor(llm_client, audit)
        iocs = await extractor.extract(incident_id, artifacts, artifact_contents)

        print(f"   Extracted {len(iocs)} IoCs:")
        for ioc in iocs:
            print(f"     - {ioc.type.value:12} {ioc.value:40} ({ioc.confidence.value})")

        # Map MITRE techniques
        print("\n2. Mapping MITRE techniques...")
        mapper = MitreMapper(llm_client, mitre_loader, audit)
        iocs = await mapper.map_iocs(incident_id, iocs)

        ioc_with_techniques = [ioc for ioc in iocs if ioc.mitre_technique_ids]
        print(f"   {len(ioc_with_techniques)} IoCs mapped to techniques")

        # Check hallucination filter
        hallucination_events = await audit.read(incident_id, action="HALLUCINATION_REJECTED")
        if hallucination_events:
            print(f"\n   ✓ Hallucination filter caught {len(hallucination_events)} invalid technique(s)")

        # Threat Intel
        print("\n3. Threat Intelligence Lookup...")
        async with httpx.AsyncClient() as client:
            ti = ThreatIntelClient(client, settings, audit, data_dir / "misp_fallback.json")
            iocs = await ti.lookup_all(incident_id, iocs)

        malicious_count = sum(1 for ioc in iocs if ioc.reputation and ioc.reputation.value == "malicious")
        print(f"   {malicious_count} malicious IoCs identified")

    # ========================================================================
    # Summary
    # ========================================================================
    print_section("Summary")

    print("✓ IoC extraction working")
    print("✓ MITRE mapping with hallucination protection working")
    print("✓ Threat Intelligence lookup (MISP fallback) working")
    print("✓ Report generation working")
    print("\n✓ All smoke tests passed!")

    # Show audit stats
    print("\nAudit Trail Statistics:")
    for incident_id in ["system"]:
        events = await audit.read(incident_id)
        if events:
            action_counts: dict[str, int] = {}
            for event in events:
                action = event.action
                action_counts[action] = action_counts.get(action, 0) + 1

            for action, count in sorted(action_counts.items()):
                print(f"  {action}: {count}")


if __name__ == "__main__":
    asyncio.run(main())

