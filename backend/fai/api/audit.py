"""Audit API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from fai.runtime import get_audit_trail

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{incident_id}")
async def get_audit(
    incident_id: str,
    action: str | None = Query(default=None),
    actor: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
) -> list[dict]:
    """Return filtered audit events for an incident."""
    events = await get_audit_trail().read(
        incident_id,
        action=action,
        actor=actor,
        since=since,
    )
    return [event.model_dump() for event in events[:1000]]

