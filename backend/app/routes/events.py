"""Server-Sent Events (SSE) Router for API Sentinel Real-Time Telemetry.

Streams real-time events to connected dashboards:
- scan_created
- scan_running
- scan_completed
- scan_failed
- critical_finding
- retest_completed
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse

from app.services.event_service import event_broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["Events & Real-Time Telemetry"])


@router.get(
    "",
    summary="Subscribe to live security telemetry via Server-Sent Events (SSE)",
    description="Provides real-time streaming updates for scan lifecycle events, new findings, critical alerts, and retests.",
)
async def subscribe_events(request: Request):
    """Establish SSE stream connection with the dashboard."""
    q = await event_broadcaster.add_subscriber()

    async def event_generator():
        try:
            # 1. Handshake event
            handshake = {
                "status": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "channel": "api_sentinel_live_telemetry",
            }
            yield f"event: connected\ndata: {json.dumps(handshake)}\n\n"

            # 2. Continuous event stream loop
            while True:
                if await request.is_disconnected():
                    logger.debug("SSE client connection terminated by client.")
                    break

                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"id: {msg['id']}\nevent: {msg['event']}\ndata: {json.dumps(msg['data'])}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment every 15s prevents proxy/browser timeouts
                    yield ": ping\n\n"

        except asyncio.CancelledError:
            logger.debug("SSE streaming generator cancelled.")
        finally:
            await event_broadcaster.remove_subscriber(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get(
    "/status",
    summary="Check real-time SSE event broadcaster health",
)
def get_event_status():
    """Returns number of active real-time dashboard subscribers."""
    return {
        "status": "online",
        "protocol": "Server-Sent Events (SSE)",
        "active_subscribers": event_broadcaster.subscriber_count(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
