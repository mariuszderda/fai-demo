"""Tests for audit trail."""

from __future__ import annotations

import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from fai.core.audit import AuditTrail, make_event
from fai.core.models import AuditEvent


@pytest.mark.asyncio
async def test_write_and_read_events() -> None:
    """Test writing and reading audit events."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditTrail(Path(tmpdir))

        # Create and write three events
        event1 = make_event("incident1", "system", "ACTION1", "object1")
        event2 = make_event("incident1", "system", "ACTION2", "object2")
        event3 = make_event("incident1", "operator", "ACTION3", "object3")

        await audit.write(event1)
        await audit.write(event2)
        await audit.write(event3)

        # Read all events (should be in reverse order)
        events = await audit.read("incident1")
        assert len(events) == 3
        assert events[0].action == "ACTION3"
        assert events[1].action == "ACTION2"
        assert events[2].action == "ACTION1"


@pytest.mark.asyncio
async def test_action_filter() -> None:
    """Test filtering by action."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditTrail(Path(tmpdir))

        event1 = make_event("incident1", "system", "ACTION_A", "obj1")
        event2 = make_event("incident1", "system", "ACTION_B", "obj2")
        event3 = make_event("incident1", "system", "ACTION_A", "obj3")

        await audit.write(event1)
        await audit.write(event2)
        await audit.write(event3)

        # Filter by action
        filtered = await audit.read("incident1", action="ACTION_A")
        assert len(filtered) == 2
        assert all(e.action == "ACTION_A" for e in filtered)


@pytest.mark.asyncio
async def test_actor_filter() -> None:
    """Test filtering by actor."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditTrail(Path(tmpdir))

        event1 = make_event("incident1", "system", "ACTION", "obj1")
        event2 = make_event("incident1", "operator", "ACTION", "obj2")
        event3 = make_event("incident1", "system", "ACTION", "obj3")

        await audit.write(event1)
        await audit.write(event2)
        await audit.write(event3)

        # Filter by actor
        filtered = await audit.read("incident1", actor="system")
        assert len(filtered) == 2
        assert all(e.actor == "system" for e in filtered)


@pytest.mark.asyncio
async def test_concurrent_writes() -> None:
    """Test concurrent writes for the same incident."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditTrail(Path(tmpdir))

        async def write_events(event_count: int) -> None:
            for i in range(event_count):
                event = make_event("incident1", "system", f"ACTION_{i}", "object")
                await audit.write(event)

        # Write from 20 concurrent tasks
        await asyncio.gather(*[write_events(1) for _ in range(20)])

        # Verify all 20 lines were written
        events = await audit.read("incident1")
        assert len(events) == 20


@pytest.mark.asyncio
async def test_read_nonexistent_incident() -> None:
    """Test reading from nonexistent incident."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit = AuditTrail(Path(tmpdir))
        events = await audit.read("nonexistent")
        assert events == []

