"""Approval API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from fai.api.schemas import ApprovalDecideRequest
from fai.core.models import ApprovalDecision
from fai.orchestrator.approval_gate import get_approval_gate

router = APIRouter(prefix="/approvals", tags=["approvals"])

_DECISION_MAP: dict[str, ApprovalDecision] = {
    "APPROVE": ApprovalDecision.APPROVED,
    "DENY": ApprovalDecision.DENIED,
    "KILLSWITCH": ApprovalDecision.KILLSWITCH,
}


@router.get("/pending")
async def list_pending_approvals() -> list[dict]:
    """Return all pending approvals."""
    return [approval.model_dump() for approval in get_approval_gate().list_pending()]


@router.get("/{approval_id}")
async def get_approval(approval_id: str) -> dict:
    """Return a single approval request."""
    approval = get_approval_gate().get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return approval.model_dump()


@router.post("/{approval_id}/decide", status_code=status.HTTP_200_OK)
async def decide_approval(approval_id: str, body: ApprovalDecideRequest) -> dict:
    """Decide an approval request."""
    decision = _DECISION_MAP.get(body.decision)
    if decision is None:
        raise HTTPException(status_code=400, detail="Invalid decision")
    approval = await get_approval_gate().decide(approval_id, decision, body.decided_by)
    return approval.model_dump()

