"""In-memory incident store used as the source of truth for the API."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from fai.core.models import Incident, IoC, Severity


class IncidentStore:
    """Simple in-memory incident repository."""

    def __init__(self) -> None:
        """Initialize the store."""
        self._incidents: dict[str, Incident] = {}
        self._iocs: dict[str, list[IoC]] = {}

    def _scenario_alert_path(self, scenario: str) -> Path:
        """Return the alert fixture path for a scenario."""
        return Path(__file__).resolve().parents[3] / "data" / "scenarios" / scenario / "alert.json"

    def _load_scenario_alert(self, scenario: str) -> dict[str, Any]:
        """Load the scenario alert fixture."""
        alert_path = self._scenario_alert_path(scenario)
        if not alert_path.exists():
            return {}
        return json.loads(alert_path.read_text(encoding="utf-8"))

    def create(self, scenario: str) -> Incident:
        """Create a new incident record for a scenario."""
        alert = self._load_scenario_alert(scenario)
        started_at = datetime.now(timezone.utc)
        incident = Incident(
            scenario=scenario,  # type: ignore[arg-type]
            siem_alert_id=alert.get("alert_id", "pending"),
            started_at_utc=started_at,
            severity=Severity(alert.get("severity", Severity.INFO.value)),
            current_step="ingesting",
            host_id=alert.get("host"),
            alert_summary=alert.get("summary"),
        )
        self._incidents[incident.id] = incident
        self._iocs[incident.id] = []
        return incident

    def get(self, incident_id: str) -> Incident | None:
        """Return a single incident by identifier."""
        return self._incidents.get(incident_id)

    def update(self, incident_id: str, **fields: Any) -> Incident:
        """Update an incident and return the updated record."""
        incident = self._incidents[incident_id]
        for field_name, value in fields.items():
            setattr(incident, field_name, value)
        if "completed_at_utc" in fields and fields["completed_at_utc"] is not None:
            incident.completed_at_utc = fields["completed_at_utc"]
        return incident

    def list(self) -> list[Incident]:
        """List incidents newest first."""
        return list(reversed(list(self._incidents.values())))

    def list_iocs(self, incident_id: str) -> list[IoC]:
        """List IoCs for an incident."""
        return list(self._iocs.get(incident_id, []))

    def set_iocs(self, incident_id: str, iocs: list[IoC]) -> None:
        """Replace the IoCs for an incident and update counts."""
        self._iocs[incident_id] = list(iocs)
        incident = self._incidents.get(incident_id)
        if incident is None:
            return
        incident.ioc_count = len(iocs)
        incident.technique_count = len({tech for ioc in iocs for tech in ioc.mitre_technique_ids})

    def clear(self) -> None:
        """Clear all incident state."""
        self._incidents.clear()
        self._iocs.clear()


@lru_cache(maxsize=1)
def get_incident_store() -> IncidentStore:
    """Return the shared incident store."""
    return IncidentStore()

