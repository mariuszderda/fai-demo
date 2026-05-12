"""Audit trail implementation."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import AuditEvent


class AuditTrail:
    """Append-only audit trail with per-incident locking."""

    def __init__(self, runtime_dir: Path) -> None:
        """Initialize audit trail with runtime directory."""
        self.runtime_dir = Path(runtime_dir)
        self.audit_dir = self.runtime_dir / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, incident_id: str) -> asyncio.Lock:
        """Get or create a lock for an incident."""
        if incident_id not in self._locks:
            self._locks[incident_id] = asyncio.Lock()
        return self._locks[incident_id]

    async def write(self, event: AuditEvent) -> None:
        """Append an audit event to the incident's log."""
        lock = self._get_lock(event.incident_id)
        async with lock:
            log_path = self.audit_dir / f"{event.incident_id}.jsonl"
            line = event.model_dump_json() + "\n"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line)

    async def read(
        self,
        incident_id: str,
        *,
        action: str | None = None,
        actor: str | None = None,
        since: datetime | None = None,
    ) -> list[AuditEvent]:
        """Read and filter audit events (newest first)."""
        log_path = self.audit_dir / f"{incident_id}.jsonl"
        if not log_path.exists():
            return []

        events: list[AuditEvent] = []
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    event_dict = json.loads(line)
                    event = AuditEvent(**event_dict)

                    # Apply filters
                    if action and event.action != action:
                        continue
                    if actor and event.actor != actor:
                        continue
                    if since and event.ts_utc < since:
                        continue

                    events.append(event)

        # Return newest first
        return list(reversed(events))


def make_event(
    incident_id: str,
    actor: str,
    action: str,
    object: str,
    **details: object,
) -> AuditEvent:
    """Create an audit event with current timestamp."""
    return AuditEvent(
        incident_id=incident_id,
        actor=actor,
        action=action,
        object=object,
        ts_utc=datetime.now(timezone.utc),
        details=details,
    )

