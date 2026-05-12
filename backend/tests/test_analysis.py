"""Tests for analysis layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from fai.analysis.ioc_extractor import IocExtractor
from fai.analysis.llm_client import StubLlmClient
from fai.analysis.mitre_mapper import MitreMapper
from fai.analysis.threat_intel import ThreatIntelClient
from fai.core.audit import AuditTrail
from fai.core.models import Artifact, Confidence, IocType, Severity
from fai.mitre.loader import MitreLoader


@pytest.fixture
def temp_runtime_dir(tmp_path: Path) -> Path:
    """Create a temporary runtime directory."""
    return tmp_path / "runtime"


@pytest.fixture
def audit_trail(temp_runtime_dir: Path) -> AuditTrail:
    """Create an audit trail instance."""
    return AuditTrail(temp_runtime_dir)


@pytest.fixture
def stub_llm_client() -> StubLlmClient:
    """Create a stub LLM client."""
    return StubLlmClient()


@pytest.fixture
def mitre_loader() -> MitreLoader:
    """Create a MITRE loader with the real dataset."""
    dataset_path = Path(__file__).parent.parent.parent / "data" / "mitre" / "enterprise-attack.json"
    return MitreLoader(dataset_path)


# ============================================================================
# IoC Extractor Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ioc_extractor_ransomware_scenario(
    audit_trail: AuditTrail,
    stub_llm_client: StubLlmClient,
) -> None:
    """Test IoC extraction for ransomware scenario."""
    incident_id = str(uuid4())
    extractor = IocExtractor(stub_llm_client, audit_trail)

    # Create dummy artifacts
    artifacts = [
        Artifact(
            incident_id=incident_id,
            filename="syslog.log",
            source="host",
            size_bytes=1024,
            sha256="abc123",
            collected_at_utc=datetime.now(timezone.utc),
            collector_version="1.0",
        ),
    ]

    # Dummy content with ransomware markers
    artifact_contents = {
        "syslog.log": "cryptdaemon process spawned. Connection to c2-relay.evil-corp-demo.test established.",
    }

    # Extract
    iocs = await extractor.extract(incident_id, artifacts, artifact_contents)

    # Verify
    assert len(iocs) >= 3
    values = [ioc.value for ioc in iocs]
    assert "203.0.113.47" in values
    assert "c2-relay.evil-corp-demo.test" in values


@pytest.mark.asyncio
async def test_ioc_extractor_private_ip_filtered(
    audit_trail: AuditTrail,
    stub_llm_client: StubLlmClient,
) -> None:
    """Test that private IPs are filtered."""
    incident_id = str(uuid4())
    extractor = IocExtractor(stub_llm_client, audit_trail)

    artifacts = [
        Artifact(
            incident_id=incident_id,
            filename="test.log",
            source="host",
            size_bytes=100,
            sha256="test123",
            collected_at_utc=datetime.now(timezone.utc),
            collector_version="1.0",
        ),
    ]

    artifact_contents = {"test.log": "Private IP 192.168.1.1 observed"}

    # Extract (with stub that could theoretically return private IPs)
    iocs = await extractor.extract(incident_id, artifacts, artifact_contents)

    # Verify no private IPs in result
    for ioc in iocs:
        if ioc.type == IocType.IPV4:
            assert not ioc.value.startswith("192.168")
            assert not ioc.value.startswith("10.")
            assert not ioc.value.startswith("172.")


@pytest.mark.asyncio
async def test_ioc_extractor_phishing_scenario(
    audit_trail: AuditTrail,
    stub_llm_client: StubLlmClient,
) -> None:
    """Test IoC extraction for phishing scenario."""
    incident_id = str(uuid4())
    extractor = IocExtractor(stub_llm_client, audit_trail)

    artifacts = [
        Artifact(
            incident_id=incident_id,
            filename="email.eml",
            source="mail",
            size_bytes=512,
            sha256="test456",
            collected_at_utc=datetime.now(timezone.utc),
            collector_version="1.0",
        ),
    ]

    artifact_contents = {
        "email.eml": "From: faktury-online.evil-corp-demo.test\nSubject: Invoice\n",
    }

    # Extract
    iocs = await extractor.extract(incident_id, artifacts, artifact_contents)

    # Verify
    assert len(iocs) >= 3
    values = [ioc.value for ioc in iocs]
    assert "evil-corp-demo.test" in values
    assert "faktury-online.evil-corp-demo.test" in values


# ============================================================================
# MITRE Loader Tests
# ============================================================================


def test_mitre_loader_loads_dataset(mitre_loader: MitreLoader) -> None:
    """Test that MITRE loader loads techniques."""
    # Should have loaded some techniques
    assert len(mitre_loader.techniques) > 0
    assert "T1486" in mitre_loader.techniques


def test_mitre_loader_validates_technique_id(mitre_loader: MitreLoader) -> None:
    """Test MITRE technique ID validation."""
    # Valid techniques
    assert mitre_loader.is_valid_technique("T1486")
    assert mitre_loader.is_valid_technique("T1566")

    # Invalid techniques
    assert not mitre_loader.is_valid_technique("T9999")
    assert not mitre_loader.is_valid_technique("INVALID")


def test_mitre_loader_get_technique(mitre_loader: MitreLoader) -> None:
    """Test getting technique metadata."""
    tech = mitre_loader.get_technique("T1486")
    assert tech is not None
    assert tech.technique_id == "T1486"
    assert len(tech.name) > 0


def test_mitre_loader_get_matrix(mitre_loader: MitreLoader) -> None:
    """Test getting MITRE matrix structure."""
    matrix = mitre_loader.get_matrix()

    assert "tactics" in matrix
    assert len(matrix["tactics"]) > 0

    # Check structure
    for tactic in matrix["tactics"]:
        assert "id" in tactic
        assert "name" in tactic
        assert "techniques" in tactic


# ============================================================================
# MITRE Mapper Tests
# ============================================================================


@pytest.mark.asyncio
async def test_mitre_mapper_ransomware_scenario(
    audit_trail: AuditTrail,
    stub_llm_client: StubLlmClient,
    mitre_loader: MitreLoader,
) -> None:
    """Test MITRE mapping for ransomware."""
    incident_id = str(uuid4())
    mapper = MitreMapper(stub_llm_client, mitre_loader, audit_trail)

    # Create dummy IoCs
    from fai.core.models import IoC, IocStatus

    iocs = [
        IoC(
            incident_id=incident_id,
            type=IocType.IPV4,
            value="203.0.113.47",
            confidence=Confidence.HIGH,
            source_artifact_id="test",
            rationale="C2 beacon",
            status=IocStatus.PENDING_REVIEW,
        ),
    ]

    # Map
    result = await mapper.map_iocs(incident_id, iocs)

    # Verify techniques are populated
    assert len(result) > 0
    assert len(result[0].mitre_technique_ids) > 0

    # Verify hallucinated techniques are excluded
    assert "T9999" not in result[0].mitre_technique_ids

    # Verify valid techniques are included
    valid_techniques = result[0].mitre_technique_ids
    for tech in valid_techniques:
        assert mitre_loader.is_valid_technique(tech)


@pytest.mark.asyncio
async def test_mitre_mapper_hallucination_detection(
    audit_trail: AuditTrail,
    stub_llm_client: StubLlmClient,
    mitre_loader: MitreLoader,
) -> None:
    """Test that hallucinated techniques are rejected and audited."""
    incident_id = str(uuid4())
    mapper = MitreMapper(stub_llm_client, mitre_loader, audit_trail)

    from fai.core.models import IoC, IocStatus

    iocs = [
        IoC(
            incident_id=incident_id,
            type=IocType.DOMAIN,
            value="c2-relay.evil-corp-demo.test",
            confidence=Confidence.HIGH,
            source_artifact_id="test",
            rationale="C2 domain",
            status=IocStatus.PENDING_REVIEW,
        ),
    ]

    # Map (stub will include T9999)
    result = await mapper.map_iocs(incident_id, iocs)

    # Verify T9999 was rejected
    assert "T9999" not in result[0].mitre_technique_ids

    # Verify audit event was written
    events = await audit_trail.read(incident_id, action="HALLUCINATION_REJECTED")
    assert len(events) > 0


# ============================================================================
# Threat Intel Tests
# ============================================================================


@pytest.mark.asyncio
async def test_threat_intel_misp_fallback(
    audit_trail: AuditTrail,
) -> None:
    """Test Threat Intel client using MISP fallback."""
    misp_path = Path(__file__).parent.parent.parent / "data" / "misp_fallback.json"

    import httpx
    from fai.config import Settings
    from fai.core.models import IoC, IocStatus

    settings = Settings(otx_api_key=None)  # Force fallback

    async with httpx.AsyncClient() as client:
        ti = ThreatIntelClient(client, settings, audit_trail, misp_path)

        incident_id = str(uuid4())

        # Test known malicious IoC
        ioc = IoC(
            incident_id=incident_id,
            type=IocType.IPV4,
            value="203.0.113.47",
            confidence=Confidence.HIGH,
            source_artifact_id="test",
            rationale="test",
            status=IocStatus.PENDING_REVIEW,
        )

        reputation, source = await ti.lookup(ioc)

        # Verify
        from fai.core.models import Reputation
        assert reputation == Reputation.MALICIOUS
        assert source == "misp"

        # Test lookup_all
        iocs = [ioc]
        result = await ti.lookup_all(incident_id, iocs)

        assert result[0].reputation == Reputation.MALICIOUS
        assert result[0].reputation_source == "misp"


# ============================================================================
# Report Generator Tests
# ============================================================================


@pytest.mark.asyncio
async def test_report_generator_basic(
    audit_trail: AuditTrail,
    stub_llm_client: StubLlmClient,
    temp_runtime_dir: Path,
) -> None:
    """Test basic report generation."""
    from fai.core.models import Incident, IoC, IocStatus
    from fai.reporting.generator import ReportGenerator

    generator = ReportGenerator(stub_llm_client, audit_trail, temp_runtime_dir)

    incident_id = str(uuid4())

    incident = Incident(
        id=incident_id,
        scenario="ransomware",
        siem_alert_id="SIEM-001",
        started_at_utc=datetime.now(timezone.utc),
        severity=Severity.HIGH,
        current_step="analysis",
    )

    artifacts = [
        Artifact(
            incident_id=incident_id,
            filename="test.log",
            source="host",
            size_bytes=100,
            sha256="abc123def456",
            collected_at_utc=datetime.now(timezone.utc),
            collector_version="1.0",
        ),
    ]

    iocs = [
        IoC(
            incident_id=incident_id,
            type=IocType.DOMAIN,
            value="evil.example.com",
            confidence=Confidence.HIGH,
            source_artifact_id="test.log",
            rationale="Found in logs",
            status=IocStatus.ACCEPTED,
        ),
    ]

    # Generate report
    markdown, html = await generator.generate(incident, iocs, artifacts)

    # Verify output
    assert len(markdown) > 0
    assert len(html) > 0
    assert "evil.example.com" in markdown
    assert "Raport incydentu" in html


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_end_to_end_ransomware_analysis(
    audit_trail: AuditTrail,
    stub_llm_client: StubLlmClient,
    mitre_loader: MitreLoader,
) -> None:
    """End-to-end test: ransomware scenario extraction + mapping."""
    incident_id = str(uuid4())

    # Setup extractors
    extractor = IocExtractor(stub_llm_client, audit_trail)
    mapper = MitreMapper(stub_llm_client, mitre_loader, audit_trail)

    # Create artifacts
    artifacts = [
        Artifact(
            incident_id=incident_id,
            filename="syslog.log",
            source="host",
            size_bytes=2048,
            sha256="ransomware_hash_123",
            collected_at_utc=datetime.now(timezone.utc),
            collector_version="1.0",
        ),
    ]

    artifact_contents = {
        "syslog.log": "cryptdaemon spawned. Connection to c2-relay.evil-corp-demo.test. Files encrypted.",
    }

    # Extract IoCs
    iocs = await extractor.extract(incident_id, artifacts, artifact_contents)
    assert len(iocs) >= 3

    # Map MITRE techniques
    mapped_iocs = await mapper.map_iocs(incident_id, iocs)

    # Verify at least one IoC has techniques
    has_techniques = any(len(ioc.mitre_technique_ids) > 0 for ioc in mapped_iocs)
    assert has_techniques

    # Verify no hallucinations present
    for ioc in mapped_iocs:
        for tech_id in ioc.mitre_technique_ids:
            assert mitre_loader.is_valid_technique(tech_id)

