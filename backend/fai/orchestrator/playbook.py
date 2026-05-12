"""Base playbook abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from time import monotonic

from fai.analysis.ioc_extractor import IocExtractor
from fai.analysis.mitre_mapper import MitreMapper
from fai.analysis.threat_intel import ThreatIntelClient
from fai.core.audit import AuditTrail, make_event
from fai.core.chain_of_custody import ChainOfCustody
from fai.core.events import EventBus
from fai.core.models import Incident, IoC
from fai.ingestion.siem_consumer import SiemConsumer
from fai.orchestrator.approval_gate import ApprovalGate
from fai.orchestrator.incident_store import IncidentStore
from fai.orchestrator.ioc_review_gate import IocReviewGate
from fai.reporting.generator import ReportGenerator


class Playbook(ABC):
    """Abstract base for incident playbooks."""

    name: str

    def __init__(
        self,
        *,
        siem_consumer: SiemConsumer,
        ioc_extractor: IocExtractor,
        mitre_mapper: MitreMapper,
        threat_intel_client: ThreatIntelClient,
        ioc_review_gate: IocReviewGate,
        approval_gate: ApprovalGate,
        report_generator: ReportGenerator,
        audit: AuditTrail,
        event_bus: EventBus,
        incident_store: IncidentStore,
        chain_of_custody: ChainOfCustody,
    ) -> None:
        """Initialize the shared playbook dependencies."""
        self.siem_consumer = siem_consumer
        self.ioc_extractor = ioc_extractor
        self.mitre_mapper = mitre_mapper
        self.threat_intel_client = threat_intel_client
        self.ioc_review_gate = ioc_review_gate
        self.approval_gate = approval_gate
        self.report_generator = report_generator
        self.audit = audit
        self.event_bus = event_bus
        self.incident_store = incident_store
        self.chain_of_custody = chain_of_custody
        self._step_clock: dict[str, float] = {}

    async def _advance(self, incident: Incident, step_name: str) -> None:
        """Update the incident step, emit audit, and publish SSE progress."""
        previous_started = self._step_clock.get(incident.current_step)
        now = monotonic()
        duration_ms = None if previous_started is None else int((now - previous_started) * 1000)
        self._step_clock[step_name] = now
        self.incident_store.update(incident.id, current_step=step_name)
        await self.audit.write(
            make_event(
                incident_id=incident.id,
                actor=self.name,
                action="PIPELINE_STEP",
                object=step_name,
                status="running",
                duration_ms=duration_ms,
            )
        )
        payload: dict[str, object] = {"step": step_name, "status": "running"}
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        await self.event_bus.publish(incident.id, "pipeline_step", payload)

    def _artifact_path(self, incident_id: str, artifact_id: str, filename: str) -> Path:
        """Return the on-disk path for a collected artifact."""
        return self.chain_of_custody.artifacts_dir / incident_id / f"{artifact_id}__{filename}"

    def _accepted_techniques(self, iocs: list[IoC]) -> list[str]:
        """Return unique MITRE technique IDs from a set of IoCs."""
        techniques: list[str] = []
        for ioc in iocs:
            for technique_id in ioc.mitre_technique_ids:
                if technique_id not in techniques:
                    techniques.append(technique_id)
        return techniques

    @abstractmethod
    async def run(self, incident: Incident) -> None:
        """Execute the playbook for the given incident."""

