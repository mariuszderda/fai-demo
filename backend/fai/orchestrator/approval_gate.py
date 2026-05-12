"""Approval gate implementation."""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from uuid import uuid4

from fastapi import HTTPException

from fai.core.audit import make_event
from fai.core.models import ApprovalDecision, ApprovalRequest
from fai.runtime import get_audit_trail, get_event_bus_singleton, get_settings_cached


@dataclass(slots=True)
class _TokenRecord:
    approval_id: str
    expires_at: datetime
    used: bool = False


class ApprovalGate:
    """Human approval gate with TTL and one-time isolation tokens."""

    def __init__(self) -> None:
        """Initialize the approval gate."""
        self._requests: dict[str, ApprovalRequest] = {}
        self._token_registry: dict[str, _TokenRecord] = {}
        self._decision_events: dict[str, asyncio.Event] = {}
        self._ttl_tasks: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()
        self._token_lock = threading.Lock()
        self._audit = get_audit_trail()
        self._event_bus = get_event_bus_singleton()
        self._settings = get_settings_cached()

    def _get_decision_event(self, approval_id: str) -> asyncio.Event:
        """Get or create the decision event for an approval request."""
        if approval_id not in self._decision_events:
            self._decision_events[approval_id] = asyncio.Event()
        return self._decision_events[approval_id]

    async def request(
        self,
        incident_id: str,
        host_id: str,
        reason: str,
        isolation_target: str = "host_network",
    ) -> ApprovalRequest:
        """Create a new approval request and start its TTL timer."""
        created_at = datetime.now(timezone.utc)
        approval = ApprovalRequest(
            incident_id=incident_id,
            host_id=host_id,
            reason=reason,
            created_at_utc=created_at,
            ttl_seconds=self._settings.approval_ttl_seconds,
            isolation_target=isolation_target,  # type: ignore[arg-type]
        )

        async with self._lock:
            self._requests[approval.id] = approval
            self._get_decision_event(approval.id).clear()
            self._ttl_tasks[approval.id] = asyncio.create_task(self._expire_after_ttl(approval.id))

        await self._audit.write(
            make_event(
                incident_id=incident_id,
                actor="approval_gate",
                action="APPROVAL_REQUESTED",
                object=approval.id,
                host_id=host_id,
                reason=reason,
                isolation_target=isolation_target,
                ttl_seconds=approval.ttl_seconds,
            )
        )
        await self._event_bus.publish(
            incident_id,
            "approval_pending",
            {
                "approval_id": approval.id,
                "host_id": host_id,
                "reason": reason,
                "ttl_seconds": approval.ttl_seconds,
            },
        )
        return approval

    async def _expire_after_ttl(self, approval_id: str) -> None:
        """Auto-timeout the request once the TTL elapses."""
        approval = self._requests.get(approval_id)
        if approval is None:
            return
        await asyncio.sleep(approval.ttl_seconds)
        await self._timeout_if_pending(approval_id)

    async def _timeout_if_pending(self, approval_id: str) -> ApprovalRequest | None:
        """Mark a pending request as timed out if it is still open."""
        async with self._lock:
            approval = self._requests.get(approval_id)
            if approval is None or approval.decision != ApprovalDecision.PENDING:
                return approval
            approval.decision = ApprovalDecision.TIMEOUT
            approval.decided_at_utc = datetime.now(timezone.utc)
            approval.decided_by = "system"
            self._get_decision_event(approval_id).set()
            self._ttl_tasks.pop(approval_id, None)

        await self._audit.write(
            make_event(
                incident_id=approval.incident_id,
                actor="system",
                action="APPROVAL_DECIDED",
                object=approval_id,
                decision=approval.decision.value,
                decided_by=approval.decided_by,
            )
        )
        await self._event_bus.publish(
            approval.incident_id,
            "approval_decided",
            {"approval_id": approval_id, "decision": approval.decision.value},
        )
        return approval

    async def decide(
        self,
        approval_id: str,
        decision: ApprovalDecision,
        decided_by: str,
    ) -> ApprovalRequest:
        """Finalize an approval request with a human decision."""
        async with self._lock:
            approval = self._requests.get(approval_id)
            if approval is None:
                raise HTTPException(status_code=404, detail="Approval request not found")
            if approval.decision != ApprovalDecision.PENDING:
                raise HTTPException(status_code=400, detail="Approval request is no longer pending")

            approval.decision = decision
            approval.decided_at_utc = datetime.now(timezone.utc)
            approval.decided_by = decided_by
            task = self._ttl_tasks.pop(approval_id, None)
            if task is not None:
                task.cancel()
            self._get_decision_event(approval_id).set()

            if decision == ApprovalDecision.APPROVED:
                token = str(uuid4())
                approval.isolation_token = token
                self._register_token(token, approval.id)
            else:
                approval.isolation_token = None

        await self._audit.write(
            make_event(
                incident_id=approval.incident_id,
                actor=decided_by,
                action="APPROVAL_DECIDED",
                object=approval_id,
                decision=approval.decision.value,
            )
        )
        await self._event_bus.publish(
            approval.incident_id,
            "approval_decided",
            {"approval_id": approval.id, "decision": approval.decision.value},
        )
        return approval

    def _register_token(self, token: str, approval_id: str) -> None:
        """Store a one-time token in the registry."""
        with self._token_lock:
            self._token_registry[token] = _TokenRecord(
                approval_id=approval_id,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=60),
            )

    def validate_token(self, token: str) -> str | None:
        """Validate a one-time token and mark it used on first successful lookup."""
        now = datetime.now(timezone.utc)
        with self._token_lock:
            record = self._token_registry.get(token)
            if record is None:
                return None
            if record.used or record.expires_at <= now:
                self._token_registry.pop(token, None)
                return None
            record.used = True
            return record.approval_id

    def list_pending(self) -> list[ApprovalRequest]:
        """Return all pending approval requests."""
        return [request for request in self._requests.values() if request.decision == ApprovalDecision.PENDING]

    def get(self, approval_id: str) -> ApprovalRequest | None:
        """Return a request by identifier."""
        return self._requests.get(approval_id)

    async def wait_for_decision(self, approval_id: str) -> ApprovalRequest:
        """Wait until a request is decided."""
        event = self._get_decision_event(approval_id)
        await event.wait()
        approval = self._requests.get(approval_id)
        if approval is None:
            raise HTTPException(status_code=404, detail="Approval request not found")
        return approval

    async def close(self) -> None:
        """Cancel pending TTL tasks."""
        async with self._lock:
            tasks = list(self._ttl_tasks.values())
            self._ttl_tasks.clear()
        for task in tasks:
            task.cancel()

    def clear(self) -> None:
        """Clear all approval state and tokens."""
        self._requests.clear()
        self._token_registry.clear()
        self._decision_events.clear()


@lru_cache(maxsize=1)
def get_approval_gate() -> ApprovalGate:
    """Return the shared approval gate."""
    return ApprovalGate()

