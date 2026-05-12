"""Incident API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from fai.api.schemas import (
    IncidentCreateRequest,
    IncidentCreateResponse,
    IncidentDetailResponse,
    IncidentSummaryResponse,
)
from fai.orchestrator.dispatcher import dispatch
from fai.orchestrator.incident_store import get_incident_store
from fai.runtime import get_chain_of_custody

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_incident(body: IncidentCreateRequest) -> IncidentCreateResponse:
    """Create a new incident and start the matching playbook."""
    incident_id = await dispatch(body.scenario, get_incident_store())
    return IncidentCreateResponse(incident_id=incident_id, status="ingesting")


@router.get("", response_model=list[IncidentSummaryResponse])
async def list_incidents() -> list[IncidentSummaryResponse]:
    """List incidents newest first."""
    store = get_incident_store()
    result: list[IncidentSummaryResponse] = []
    for incident in store.list():
        result.append(
            IncidentSummaryResponse(
                id=incident.id,
                scenario=incident.scenario,
                severity=incident.severity.value,
                current_step=incident.current_step,
                started_at_utc=incident.started_at_utc,
                completed_at_utc=incident.completed_at_utc,
                ioc_count=incident.ioc_count,
                technique_count=incident.technique_count,
                isolation_decision=incident.isolation_decision.value if incident.isolation_decision else None,
            )
        )
    return result


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(incident_id: str) -> IncidentDetailResponse:
    """Return the full state of an incident."""
    store = get_incident_store()
    incident = store.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentDetailResponse(**incident.model_dump(), iocs=store.list_iocs(incident_id))


@router.post("/{incident_id}/verify-coc")
async def verify_coc(incident_id: str) -> list[dict]:
    """Verify the incident chain of custody."""
    return await get_chain_of_custody().verify_integrity(incident_id)

