import json
import logging
from typing import List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return

        payload = json.dumps(message, default=str)
        dead_connections = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Error sending WebSocket message: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


ws_manager = ConnectionManager()
