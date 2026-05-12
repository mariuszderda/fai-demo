"""Ransomware playbook."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fai.core.models import ApprovalDecision, Incident, IoC, IocStatus, Reputation, Severity
from fai.orchestrator.playbook import Playbook


class RansomwarePlaybook(Playbook):
    """End-to-end ransomware incident playbook."""

    name = "ransomware"

    async def run(self, incident: Incident) -> None:
        """Run the ransomware playbook."""
        await self._advance(incident, "ingesting")
        artifacts = await self.siem_consumer.ingest_alert(incident.id, incident.scenario)
        alert = self.siem_consumer.last_alert or {}
        self.incident_store.update(
            incident.id,
            siem_alert_id=alert.get("alert_id", incident.siem_alert_id),
            host_id=alert.get("host", incident.host_id),
            alert_summary=alert.get("summary", incident.alert_summary),
            artifact_count=len(artifacts),
        )

        await self._advance(incident, "collecting")
        artifact_contents: dict[str, str] = {}
        for artifact in artifacts:
            artifact_path = self._artifact_path(incident.id, artifact.id, artifact.filename)
            artifact_contents[artifact.filename] = artifact_path.read_text(encoding="utf-8", errors="ignore")

        await self._advance(incident, "ioc_extraction")
        iocs = await self.ioc_extractor.extract(incident.id, artifacts, artifact_contents)
        self.incident_store.set_iocs(incident.id, iocs)
        await self.event_bus.publish(incident.id, "ioc_extracted", {"count": len(iocs)})

        await self._advance(incident, "ioc_review")
        await self.ioc_review_gate.submit(incident.id, iocs)
        await self.ioc_review_gate.wait_for_finalize(incident.id)
        reviewed_iocs = self.ioc_review_gate.list_pending(incident.id)
        self.incident_store.set_iocs(incident.id, reviewed_iocs)

        await self._advance(incident, "mitre_mapping")
        accepted_iocs = [ioc for ioc in reviewed_iocs if ioc.status == IocStatus.ACCEPTED]
        accepted_iocs = await self.mitre_mapper.map_iocs(incident.id, accepted_iocs)
        all_iocs = self.ioc_review_gate.list_pending(incident.id)
        self.incident_store.set_iocs(incident.id, all_iocs)
        await self.event_bus.publish(
            incident.id,
            "mitre_mapped",
            {"technique_ids": self._accepted_techniques(accepted_iocs)},
        )

        await self._advance(incident, "ti_lookup")
        accepted_iocs = await self.threat_intel_client.lookup_all(incident.id, accepted_iocs)
        self.incident_store.set_iocs(incident.id, all_iocs)
        malicious_count = len([ioc for ioc in accepted_iocs if ioc.reputation == Reputation.MALICIOUS])
        await self.event_bus.publish(
            incident.id,
            "ti_lookup_completed",
            {"malicious_count": malicious_count},
        )

        malicious_iocs = [ioc for ioc in accepted_iocs if ioc.reputation == Reputation.MALICIOUS]
        techniques = self._accepted_techniques(accepted_iocs)
        if malicious_iocs and any(tech in {"T1486", "T1490"} for tech in techniques):
            severity = Severity.CRITICAL
        elif malicious_iocs:
            severity = Severity.HIGH
        else:
            severity = Severity.MEDIUM
        self.incident_store.update(incident.id, severity=severity)

        if severity == Severity.CRITICAL:
            top_technique_id = next((tech for tech in techniques if tech in {"T1486", "T1490"}), techniques[0] if techniques else "unknown")
            host_id = incident.host_id or alert.get("host", "unknown-host")
            reason = (
                f"Ransomware confirmed on {host_id}: {top_technique_id} + "
                f"{len(malicious_iocs)} malicious IoCs"
            )
            approval = await self.approval_gate.request(
                incident.id,
                host_id=host_id,
                reason=reason,
                isolation_target="host_network",
            )
            self.incident_store.update(
                incident.id,
                approval_id=approval.id,
                isolation_target=approval.isolation_target,
            )
            approved = await self.approval_gate.wait_for_decision(approval.id)
            self.incident_store.update(incident.id, isolation_decision=approved.decision)
            if approved.decision == ApprovalDecision.APPROVED and approved.isolation_token:
                case_response = await self.siem_consumer.client.post(
                    "/mock/soar/case",
                    json={
                        "title": f"Ransomware incident {incident.id}",
                        "severity": severity.value,
                        "description": reason,
                    },
                )
                case_response.raise_for_status()
                case_id = case_response.json()["case_id"]
                isolate_response = await self.siem_consumer.client.post(
                    "/mock/soar/responder/isolate-host",
                    json={
                        "case_id": case_id,
                        "host_id": host_id,
                        "approval_token": approved.isolation_token,
                    },
                )
                isolate_response.raise_for_status()

        await self._advance(incident, "report_generation")
        await self.report_generator.generate(incident, all_iocs, artifacts)
        report_md_path = Path(self.report_generator.runtime_dir) / "reports" / f"{incident.id}.md"
        report_html_path = Path(self.report_generator.runtime_dir) / "reports" / f"{incident.id}.html"
        self.incident_store.update(
            incident.id,
            report_path=str(report_html_path),
            report_md_path=str(report_md_path),
            report_html_path=str(report_html_path),
        )
        await self.event_bus.publish(incident.id, "report_ready", {"report_path": str(report_html_path)})

        self.incident_store.update(incident.id, completed_at_utc=datetime.now(timezone.utc))
        await self._advance(incident, "done")

