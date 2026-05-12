"""Server-sent events bus for pub/sub messaging."""

from __future__ import annotations

import asyncio
import json
from functools import lru_cache


class EventBus:
    """In-memory pub/sub event bus for SSE delivery."""

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._queues: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, incident_id: str) -> asyncio.Queue:
        """Subscribe to events for an incident."""
        if incident_id not in self._queues:
            self._queues[incident_id] = []
        queue: asyncio.Queue = asyncio.Queue()
        self._queues[incident_id].append(queue)
        return queue

    def unsubscribe(self, incident_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from events for an incident."""
        if incident_id in self._queues:
            self._queues[incident_id] = [
                q for q in self._queues[incident_id] if q is not queue
            ]
            if not self._queues[incident_id]:
                del self._queues[incident_id]

    async def publish(
        self, incident_id: str, event_type: str, payload: dict
    ) -> None:
        """Publish an event to all subscribers for an incident."""
        if incident_id not in self._queues:
            return

        event = json.dumps({"event_type": event_type, "payload": payload})
        tasks = []
        for queue in self._queues[incident_id]:
            tasks.append(queue.put(event))

        if tasks:
            await asyncio.gather(*tasks)

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._queues.clear()


@lru_cache(maxsize=1)
def get_event_bus() -> EventBus:
    """Get the singleton event bus instance."""
    return EventBus()

