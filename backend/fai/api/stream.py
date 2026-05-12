"""SSE stream API routes."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from starlette.responses import StreamingResponse

from fai.runtime import get_event_bus_singleton

router = APIRouter(prefix="/incidents", tags=["stream"])


@router.get("/{incident_id}/stream")
async def stream_incident(incident_id: str) -> StreamingResponse:
    """Stream incident events using Server-Sent Events."""
    bus = get_event_bus_singleton()
    queue = bus.subscribe(incident_id)

    async def event_generator() -> AsyncIterator[str]:
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield "event: heartbeat\ndata: {}\n\n"
                    continue
                payload = json.loads(message)
                event_type = payload.get("event_type", "message")
                data = json.dumps(payload.get("payload", {}))
                yield f"event: {event_type}\ndata: {data}\n\n"
        finally:
            bus.unsubscribe(incident_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

