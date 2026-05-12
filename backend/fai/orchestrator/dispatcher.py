"""Playbook dispatcher."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import HTTPException

from fai.analysis.llm_client import get_llm_client as build_llm_client
from fai.analysis.ioc_extractor import IocExtractor
from fai.analysis.mitre_mapper import MitreMapper
from fai.core.audit import make_event
from fai.core.models import Incident
from fai.orchestrator.approval_gate import get_approval_gate
from fai.orchestrator.incident_store import IncidentStore, get_incident_store
from fai.orchestrator.ioc_review_gate import get_ioc_review_gate
from fai.orchestrator.phishing import PhishingPlaybook
from fai.orchestrator.playbook import Playbook
from fai.orchestrator.ransomware import RansomwarePlaybook
from fai.reporting.generator import ReportGenerator
from fai.runtime import (
    get_audit_trail,
    get_chain_of_custody,
    get_event_bus_singleton,
    get_mitre_loader,
    get_runtime_dir,
    get_settings_cached,
    get_siem_consumer,
    get_threat_intel_client,
)

logger = logging.getLogger(__name__)
_background_tasks: set[asyncio.Task[None]] = set()


async def _build_playbooks(
    incident_store: IncidentStore,
    incident_id: str,
) -> dict[str, Playbook]:
    """Construct the shared playbook instances."""
    audit = get_audit_trail()
    llm_client = await build_llm_client(
        settings=get_settings_cached(),
        audit=audit,
        incident_id=incident_id,
    )
    event_bus = get_event_bus_singleton()
    ioc_review_gate = get_ioc_review_gate()
    approval_gate = get_approval_gate()
    siem_consumer = get_siem_consumer()
    threat_intel_client = get_threat_intel_client()
    report_generator = ReportGenerator(llm_client, audit, get_runtime_dir())
    chain_of_custody = get_chain_of_custody()
    ioc_extractor = IocExtractor(llm_client, audit)
    mitre_mapper = MitreMapper(llm_client, get_mitre_loader(), audit)
    return {
        "ransomware": RansomwarePlaybook(
            siem_consumer=siem_consumer,
            ioc_extractor=ioc_extractor,
            mitre_mapper=mitre_mapper,
            threat_intel_client=threat_intel_client,
            ioc_review_gate=ioc_review_gate,
            approval_gate=approval_gate,
            report_generator=report_generator,
            audit=audit,
            event_bus=event_bus,
            incident_store=incident_store,
            chain_of_custody=chain_of_custody,
        ),
        "phishing": PhishingPlaybook(
            siem_consumer=siem_consumer,
            ioc_extractor=ioc_extractor,
            mitre_mapper=mitre_mapper,
            threat_intel_client=threat_intel_client,
            ioc_review_gate=ioc_review_gate,
            approval_gate=approval_gate,
            report_generator=report_generator,
            audit=audit,
            event_bus=event_bus,
            incident_store=incident_store,
            chain_of_custody=chain_of_custody,
        ),
    }


async def dispatch(scenario: str, incident_store: IncidentStore | None = None) -> str:
    """Create an incident and launch the matching playbook in the background."""
    store = incident_store or get_incident_store()
    incident = store.create(scenario)
    playbooks = await _build_playbooks(store, incident.id)
    playbook = playbooks.get(scenario)
    if playbook is None:
        raise HTTPException(status_code=400, detail="Unsupported scenario")

    async def _run_playbook() -> None:
        try:
            await playbook.run(incident)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Playbook failed for incident %s", incident.id)
            store.update(
                incident.id,
                current_step="failed",
                completed_at_utc=datetime.now(timezone.utc),
            )
            await get_audit_trail().write(
                make_event(
                    incident_id=incident.id,
                    actor="dispatcher",
                    action="PLAYBOOK_FAILED",
                    object=playbook.name,
                    error_message=str(exc),
                )
            )
            await get_event_bus_singleton().publish(
                incident.id,
                "failed",
                {"step": incident.current_step, "error_message": str(exc)},
            )

    task = asyncio.create_task(_run_playbook())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return incident.id

