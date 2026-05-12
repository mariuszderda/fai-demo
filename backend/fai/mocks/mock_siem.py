"""Mock SIEM implementation."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/mock/siem", tags=["mock"])

# In-memory store: alert_id -> scenario_name
_alerts: dict[str, str] = {}

# Path to data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "scenarios"


@router.post("/trigger/{scenario}")
async def trigger_alert(scenario: str) -> dict:
    """Trigger a mock SIEM alert for a scenario."""
    if scenario not in ("ransomware", "phishing"):
        raise HTTPException(status_code=400, detail="Invalid scenario")

    alert_id = str(uuid4())
    _alerts[alert_id] = scenario

    # Load the scenario's alert.json
    alert_path = DATA_DIR / scenario / "alert.json"
    if not alert_path.exists():
        raise HTTPException(status_code=500, detail="Alert file not found")

    with open(alert_path, "r", encoding="utf-8") as f:
        alert = json.load(f)

    # Inject the fresh alert_id
    alert["alert_id"] = alert_id

    return alert


@router.get("/alert/{alert_id}")
async def get_alert(alert_id: str) -> dict:
    """Retrieve a stored alert."""
    if alert_id not in _alerts:
        raise HTTPException(status_code=404, detail="Alert not found")

    scenario = _alerts[alert_id]
    alert_path = DATA_DIR / scenario / "alert.json"

    with open(alert_path, "r", encoding="utf-8") as f:
        alert = json.load(f)

    alert["alert_id"] = alert_id
    return alert


@router.get("/artifacts/{alert_id}")
async def list_artifacts(alert_id: str) -> list[dict]:
    """List artifacts available for an alert."""
    if alert_id not in _alerts:
        raise HTTPException(status_code=404, detail="Alert not found")

    scenario = _alerts[alert_id]
    scenario_dir = DATA_DIR / scenario

    artifacts = []
    for path in sorted(scenario_dir.iterdir()):
        if path.is_file() and path.name not in ("alert.json", "README.txt"):
            artifacts.append(
                {
                    "filename": path.name,
                    "download_url": f"/mock/siem/artifacts/{alert_id}/{path.name}",
                }
            )

    return artifacts


@router.get("/artifacts/{alert_id}/{filename}")
async def download_artifact(alert_id: str, filename: str) -> FileResponse:
    """Download an artifact file."""
    if alert_id not in _alerts:
        raise HTTPException(status_code=404, detail="Alert not found")

    scenario = _alerts[alert_id]
    artifact_path = DATA_DIR / scenario / filename

    if not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")

    return FileResponse(
        artifact_path,
        media_type="application/octet-stream",
        filename=filename,
    )

