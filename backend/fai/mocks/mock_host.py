"""Mock host isolation implementation."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/mock/host", tags=["mock"])

# In-memory host state: host_id -> {host_id, status, isolated_at}
_hosts: dict[str, dict] = {}


class IsolationResponse(BaseModel):
    """Host isolation response."""

    host_id: str
    status: str
    isolated_at: str | None = None


@router.post("/{host_id}/isolate")
async def isolate_host(
    host_id: str,
    x_approval_token: str | None = Header(None),
) -> dict:
    """Isolate a host."""
    if not x_approval_token:
        raise HTTPException(
            status_code=403,
            detail="Missing X-Approval-Token header",
        )

    now = datetime.now(timezone.utc).isoformat()

    if host_id not in _hosts:
        _hosts[host_id] = {}

    _hosts[host_id]["host_id"] = host_id
    _hosts[host_id]["status"] = "isolated"
    _hosts[host_id]["isolated_at"] = now
    _hosts[host_id]["approval_token"] = x_approval_token

    return {
        "host_id": host_id,
        "status": "isolated",
        "isolated_at": now,
    }


@router.post("/{host_id}/restore")
async def restore_host(host_id: str) -> dict:
    """Restore a host to online status."""
    if host_id not in _hosts:
        _hosts[host_id] = {}

    _hosts[host_id]["host_id"] = host_id
    _hosts[host_id]["status"] = "online"

    return {
        "host_id": host_id,
        "status": "online",
    }


@router.get("/{host_id}")
async def get_host_status(host_id: str) -> dict:
    """Get the current state of a host."""
    if host_id not in _hosts:
        return {
            "host_id": host_id,
            "status": "online",
        }

    return _hosts[host_id]

