"""
WebSocket connection manager for real-time notifications.
Singleton `manager` is imported by routers and the main WebSocket endpoint.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages active WebSocket connections and broadcasts messages to all clients."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WS connected  – total clients: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WS disconnected – total clients: %d", len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a JSON message to every connected client; prune dead connections."""
        if not self.active_connections:
            return
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for ws in list(self.active_connections):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_to(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """Send a JSON message to a single client."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception:
            self.disconnect(websocket)


# Singleton shared across the whole application
manager = WebSocketManager()
