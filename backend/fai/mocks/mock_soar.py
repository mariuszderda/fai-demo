"""Mock SOAR implementation."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/mock/soar", tags=["mock"])

# In-memory case store: case_id -> {case}
_cases: dict[str, dict] = {}

# In-memory approval token registry (populated by approval gate in Phase 4)
_approval_tokens: dict[str, str] = {}


class CaseRequest(BaseModel):
    """Case creation request."""

    title: str
    severity: str
    description: str


class ObservableRequest(BaseModel):
    """Observable creation request."""

    case_id: str
    type: str
    value: str
    reputation: str | None = None
    mitre_technique_ids: list[str] | None = None


class IsolateHostRequest(BaseModel):
    """Host isolation request."""

    case_id: str
    host_id: str
    approval_token: str


@router.post("/case")
async def create_case(body: CaseRequest) -> dict:
    """Create a case."""
    case_id = str(uuid4())
    _cases[case_id] = {
        "case_id": case_id,
        "title": body.title,
        "severity": body.severity,
        "description": body.description,
        "observables": [],
        "responder_jobs": [],
    }
    return {"case_id": case_id}


@router.post("/observable")
async def create_observable(body: ObservableRequest) -> dict:
    """Create an observable."""
    if body.case_id not in _cases:
        raise HTTPException(status_code=404, detail="Case not found")

    observable_id = str(uuid4())
    observable = {
        "observable_id": observable_id,
        "type": body.type,
        "value": body.value,
        "reputation": body.reputation,
        "mitre_technique_ids": body.mitre_technique_ids or [],
    }
    _cases[body.case_id]["observables"].append(observable)

    return {"observable_id": observable_id}


@router.post("/responder/isolate-host")
async def isolate_host(body: IsolateHostRequest) -> dict:
    """Request host isolation."""
    if body.case_id not in _cases:
        raise HTTPException(status_code=404, detail="Case not found")

    if not body.approval_token:
        raise HTTPException(
            status_code=403,
            detail="Missing approval token",
        )

    # TODO: Validate token against registry in Phase 4
    # For now, accept any non-empty token

    job_id = str(uuid4())
    job = {
        "job_id": job_id,
        "host_id": body.host_id,
        "status": "queued",
        "approval_token": body.approval_token,
    }
    _cases[body.case_id]["responder_jobs"].append(job)

    return {"job_id": job_id, "status": "queued"}


@router.get("/case/{case_id}")
async def get_case(case_id: str) -> dict:
    """Retrieve a case with all observables and jobs."""
    if case_id not in _cases:
        raise HTTPException(status_code=404, detail="Case not found")

    return _cases[case_id]


def register_approval_token(token: str, incident_id: str) -> None:
    """Register an approval token (called by approval gate)."""
    _approval_tokens[token] = incident_id


def validate_approval_token(token: str) -> str | None:
    """Validate an approval token and return incident_id."""
    return _approval_tokens.get(token)

