from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


class EventConnectionManager:
    def __init__(self) -> None:
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, event: dict[str, Any]) -> None:
        for websocket in self.connections.copy():
            try:
                await websocket.send_json(event)
            except RuntimeError, WebSocketDisconnect:
                self.disconnect(websocket)


manager = EventConnectionManager()
