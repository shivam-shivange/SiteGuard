"""WebSocket connection hub — typed manager for broadcast events."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("siteguard.ws")


class WebSocketHub:
    """Tracks active dashboard WebSocket connections and fans out events."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        logger.info("WebSocket connected (%d active)", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        logger.info("WebSocket disconnected (%d active)", len(self._connections))

    async def broadcast(self, event_or_data: str | dict[str, Any], data: dict[str, Any] | None = None) -> None:
        """Send event payload to every connected client; silently drop dead sockets."""
        if not self._connections:
            return
        if isinstance(event_or_data, dict):
            message = json.dumps(event_or_data)
        else:
            message = json.dumps({"event": event_or_data, "data": data or {}})

        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.discard(ws)
        if dead:
            logger.debug("Pruned %d dead WebSocket(s)", len(dead))

    @property
    def active_count(self) -> int:
        return len(self._connections)


# Module-level singletons used by the application.
hub = WebSocketHub()
ws_hub = hub

