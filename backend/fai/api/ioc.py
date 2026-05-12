"""IoC review API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from fai.api.schemas import IocFinalizeRequest, IocUpdateRequest
from fai.core.models import IocStatus
from fai.orchestrator.incident_store import get_incident_store
from fai.orchestrator.ioc_review_gate import get_ioc_review_gate

router = APIRouter(prefix="/incidents/{incident_id}/ioc", tags=["ioc"])


@router.get("")
async def list_iocs(incident_id: str) -> list[dict]:
    """Return all IoCs for an incident, including undecided ones."""
    return [ioc.model_dump() for ioc in get_ioc_review_gate().list_pending(incident_id)]


@router.patch("/{ioc_id}")
async def update_ioc(
    incident_id: str,
    ioc_id: str,
    body: IocUpdateRequest,
) -> dict:
    """Update the status of a single IoC."""
    status_value = IocStatus.ACCEPTED if body.status == "accepted" else IocStatus.REJECTED
    updated = await get_ioc_review_gate().update_ioc(
        incident_id,
        ioc_id,
        status_value,
        body.analyst_note,
    )
    get_incident_store().set_iocs(incident_id, get_ioc_review_gate().list_pending(incident_id))
    return updated.model_dump()


@router.post("/finalize")
async def finalize_iocs(incident_id: str, body: IocFinalizeRequest) -> dict:
    """Finalize IoC review and release the playbook."""
    accepted = await get_ioc_review_gate().finalize(incident_id, body.operator)
    all_iocs = get_ioc_review_gate().list_pending(incident_id)
    rejected = [ioc for ioc in all_iocs if ioc.status == IocStatus.REJECTED]
    get_incident_store().set_iocs(incident_id, all_iocs)
    return {"accepted_count": len(accepted), "rejected_count": len(rejected)}

