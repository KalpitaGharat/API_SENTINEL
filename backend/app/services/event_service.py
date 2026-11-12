"""Real-time Event Broadcaster for API Sentinel.

Provides asynchronous Server-Sent Events (SSE) broadcasting for live dashboard updates,
including scan creation, progress, completion, failure, critical vulnerability discovery,
and verification retest outcomes.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Set, Optional

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """Thread-safe and async-safe pub/sub event broadcaster for Server-Sent Events."""

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    def subscriber_count(self) -> int:
        """Return the number of actively connected SSE dashboard clients."""
        return len(self._subscribers)

    async def add_subscriber(self) -> asyncio.Queue:
        """Register a new dashboard client connection queue."""
        q = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(q)
        logger.debug("New SSE client subscribed. Total clients: %d", len(self._subscribers))
        return q

    async def remove_subscriber(self, q: asyncio.Queue):
        """Unregister a disconnected dashboard client queue."""
        async with self._lock:
            self._subscribers.discard(q)
        logger.debug("SSE client disconnected. Remaining clients: %d", len(self._subscribers))

    def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to all connected dashboard clients.
        
        Safe to call from synchronous service functions or background threads.
        """
        payload = {
            "id": str(uuid.uuid4()),
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Deliver to all subscriber queues safely
        dead_queues = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("Dropping event for slow SSE subscriber (queue full).")
            except Exception as e:
                logger.warning("Failed to queue event for subscriber: %s", e)
                dead_queues.append(q)

        for dead in dead_queues:
            self._subscribers.discard(dead)


# Global singleton instance
event_broadcaster = EventBroadcaster()
