"""MITRE API routes."""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, HTTPException

from fai.api.schemas import MitreCoverageResponse, MitreDetectedTechnique
from fai.core.models import Confidence
from fai.orchestrator.incident_store import get_incident_store
from fai.runtime import get_mitre_loader

router = APIRouter(tags=["mitre"])

_CONFIDENCE_ORDER = {
    Confidence.LOW.value: 0,
    Confidence.MEDIUM.value: 1,
    Confidence.HIGH.value: 2,
}


def _highest_confidence(values: list[str]) -> str:
    """Return the highest confidence level from a list."""
    if not values:
        return Confidence.LOW.value
    return max(values, key=lambda value: _CONFIDENCE_ORDER.get(value, 0))


def _coverage_for_iocs(iocs: list[dict]) -> list[MitreDetectedTechnique]:
    """Build coverage items from a list of serialised IoCs."""
    by_technique: dict[str, dict[str, object]] = defaultdict(lambda: {"ioc_ids": [], "confidence": []})
    for ioc in iocs:
        technique_ids = ioc.get("mitre_technique_ids", [])
        for technique_id in technique_ids:
            entry = by_technique[technique_id]
            entry["ioc_ids"].append(ioc["id"])
            entry["confidence"].append(ioc.get("confidence", Confidence.LOW.value))
    return [
        MitreDetectedTechnique(
            technique_id=technique_id,
            ioc_ids=list(entry["ioc_ids"]),
            confidence=_highest_confidence(list(entry["confidence"])),
        )
        for technique_id, entry in sorted(by_technique.items())
    ]


@router.get("/mitre/techniques")
async def get_techniques() -> dict:
    """Return the MITRE matrix structure."""
    return get_mitre_loader().get_matrix()


@router.get("/mitre-coverage/global", response_model=MitreCoverageResponse)
async def global_coverage() -> MitreCoverageResponse:
    """Return coverage aggregated across all incidents."""
    store = get_incident_store()
    iocs: list[dict] = []
    for incident in store.list():
        iocs.extend([ioc.model_dump(mode="json") for ioc in store.list_iocs(incident.id)])
    return MitreCoverageResponse(detected=_coverage_for_iocs(iocs))


@router.get("/incidents/{incident_id}/mitre-coverage", response_model=MitreCoverageResponse)
async def incident_coverage(incident_id: str) -> MitreCoverageResponse:
    """Return coverage for a single incident."""
    store = get_incident_store()
    incident = store.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return MitreCoverageResponse(
        detected=_coverage_for_iocs([ioc.model_dump(mode="json") for ioc in store.list_iocs(incident_id)]),
    )

