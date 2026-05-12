"""IoC review gate implementation."""

from __future__ import annotations

import asyncio
from functools import lru_cache

from fastapi import HTTPException

from fai.core.audit import make_event
from fai.core.models import IoC, IocStatus
from fai.runtime import get_audit_trail, get_event_bus_singleton


class IocReviewGate:
    """Pause point for analyst IoC review."""

    def __init__(self) -> None:
        """Initialize the review gate."""
        self._events: dict[str, asyncio.Event] = {}
        self._iocs: dict[str, list[IoC]] = {}
        self._lock = asyncio.Lock()
        self._audit = get_audit_trail()
        self._event_bus = get_event_bus_singleton()

    def _get_event(self, incident_id: str) -> asyncio.Event:
        """Get or create the incident event."""
        if incident_id not in self._events:
            self._events[incident_id] = asyncio.Event()
        return self._events[incident_id]

    async def submit(self, incident_id: str, iocs: list[IoC]) -> None:
        """Store IoCs and notify that review is required."""
        async with self._lock:
            stored_iocs = [ioc.model_copy(update={"status": IocStatus.PENDING_REVIEW}) for ioc in iocs]
            self._iocs[incident_id] = stored_iocs
            event = self._get_event(incident_id)
            event.clear()
        await self._audit.write(
            make_event(
                incident_id=incident_id,
                actor="ioc_review_gate",
                action="IOC_REVIEW_REQUESTED",
                object="ioc_review",
                count=len(iocs),
            )
        )
        await self._event_bus.publish(incident_id, "ioc_review_requested", {"count": len(iocs)})

    async def update_ioc(
        self,
        incident_id: str,
        ioc_id: str,
        status: IocStatus,
        analyst_note: str | None,
    ) -> IoC:
        """Update a stored IoC review decision."""
        if status not in {IocStatus.ACCEPTED, IocStatus.REJECTED}:
            raise HTTPException(status_code=400, detail="Invalid IoC review status")

        async with self._lock:
            iocs = self._iocs.get(incident_id)
            if iocs is None:
                raise HTTPException(status_code=404, detail="Incident not found in IoC review gate")
            for ioc in iocs:
                if ioc.id == ioc_id:
                    ioc.status = status
                    ioc.analyst_note = analyst_note
                    break
            else:
                raise HTTPException(status_code=404, detail="IoC not found")

        updated = self._iocs[incident_id]
        for ioc in updated:
            if ioc.id == ioc_id:
                await self._audit.write(
                    make_event(
                        incident_id=incident_id,
                        actor="analyst",
                        action="IOC_REVIEWED",
                        object=ioc.value,
                        ioc_id=ioc.id,
                        status=ioc.status.value,
                        analyst_note=analyst_note,
                    )
                )
                return ioc
        raise HTTPException(status_code=404, detail="IoC not found")

    async def finalize(self, incident_id: str, operator: str) -> list[IoC]:
        """Finalize review and release the pipeline once all IoCs are decided."""
        async with self._lock:
            iocs = self._iocs.get(incident_id)
            if iocs is None:
                raise HTTPException(status_code=404, detail="Incident not found in IoC review gate")
            pending = [ioc for ioc in iocs if ioc.status == IocStatus.PENDING_REVIEW]
            if pending:
                raise HTTPException(status_code=400, detail="Cannot finalize while IoCs remain pending")
            self._get_event(incident_id).set()
            accepted = [ioc for ioc in iocs if ioc.status == IocStatus.ACCEPTED]

        await self._audit.write(
            make_event(
                incident_id=incident_id,
                actor=operator,
                action="IOC_REVIEW_FINALIZED",
                object="ioc_review",
                accepted_count=len(accepted),
                rejected_count=len([ioc for ioc in iocs if ioc.status == IocStatus.REJECTED]),
            )
        )
        await self._event_bus.publish(
            incident_id,
            "ioc_review_finalized",
            {
                "accepted": len(accepted),
                "rejected": len([ioc for ioc in iocs if ioc.status == IocStatus.REJECTED]),
            },
        )
        return accepted

    async def wait_for_finalize(self, incident_id: str) -> list[IoC]:
        """Wait for the review gate to finalize and return accepted IoCs."""
        event = self._get_event(incident_id)
        await event.wait()
        return [ioc for ioc in self._iocs.get(incident_id, []) if ioc.status == IocStatus.ACCEPTED]

    def list_pending(self, incident_id: str) -> list[IoC]:
        """Return the stored IoCs for an incident."""
        return list(self._iocs.get(incident_id, []))

    def clear(self) -> None:
        """Clear the review registry."""
        self._events.clear()
        self._iocs.clear()


@lru_cache(maxsize=1)
def get_ioc_review_gate() -> IocReviewGate:
    """Return the shared IoC review gate."""
    return IocReviewGate()

