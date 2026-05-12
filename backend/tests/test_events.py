"""Tests for SSE event bus."""

from __future__ import annotations

import asyncio
import json

import pytest

from fai.core.events import EventBus, get_event_bus


@pytest.mark.asyncio
async def test_subscribe_and_publish() -> None:
    """Test subscribing and publishing events."""
    bus = EventBus()

    queue = bus.subscribe("incident1")
    await bus.publish("incident1", "TEST_EVENT", {"data": "test"})

    # Receive the event
    msg = await asyncio.wait_for(queue.get(), timeout=1.0)
    event = json.loads(msg)

    assert event["event_type"] == "TEST_EVENT"
    assert event["payload"]["data"] == "test"


@pytest.mark.asyncio
async def test_multiple_subscribers() -> None:
    """Test multiple subscribers receiving same event."""
    bus = EventBus()

    queue1 = bus.subscribe("incident1")
    queue2 = bus.subscribe("incident1")

    await bus.publish("incident1", "TEST", {"msg": "hello"})

    # Both subscribers receive
    msg1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
    msg2 = await asyncio.wait_for(queue2.get(), timeout=1.0)

    assert json.loads(msg1)["payload"]["msg"] == "hello"
    assert json.loads(msg2)["payload"]["msg"] == "hello"


@pytest.mark.asyncio
async def test_unsubscribe() -> None:
    """Test unsubscribing drops messages."""
    bus = EventBus()

    queue = bus.subscribe("incident1")
    bus.unsubscribe("incident1", queue)

    await bus.publish("incident1", "TEST", {"data": "lost"})

    # Queue should not receive
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(queue.get(), timeout=0.1)


@pytest.mark.asyncio
async def test_isolated_incidents() -> None:
    """Test events are isolated per incident."""
    bus = EventBus()

    queue1 = bus.subscribe("incident1")
    queue2 = bus.subscribe("incident2")

    await bus.publish("incident1", "EVENT", {"for": "incident1"})
    await bus.publish("incident2", "EVENT", {"for": "incident2"})

    msg1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
    msg2 = await asyncio.wait_for(queue2.get(), timeout=1.0)

    assert json.loads(msg1)["payload"]["for"] == "incident1"
    assert json.loads(msg2)["payload"]["for"] == "incident2"


def test_event_bus_singleton() -> None:
    """Test get_event_bus returns singleton."""
    bus1 = get_event_bus()
    bus2 = get_event_bus()
    assert bus1 is bus2

