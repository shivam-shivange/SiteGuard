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
        # Signed-in dashboard sockets -> their user (for role-based notifications)
        self._users: dict[WebSocket, dict[str, Any]] = {}

    async def connect(self, ws: WebSocket, user: dict[str, Any] | None = None) -> None:
        await ws.accept()
        self._connections.add(ws)
        if user is not None:
            self._users[ws] = user
        logger.info("WebSocket connected (%d active)", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        self._users.pop(ws, None)
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

    async def notify_users(self, user_ids: set[int], payload: dict[str, Any]) -> int:
        """Send a notification to every socket of the given users and all admins."""
        message = json.dumps({"event": "notification", "data": payload})
        sent = 0
        for ws, user in list(self._users.items()):
            if user["role"] != "admin" and user["id"] not in user_ids:
                continue
            try:
                await ws.send_text(message)
                sent += 1
            except Exception:
                self.disconnect(ws)
        return sent

    @property
    def active_count(self) -> int:
        return len(self._connections)


# Module-level singletons used by the application.
hub = WebSocketHub()
ws_hub = hub

