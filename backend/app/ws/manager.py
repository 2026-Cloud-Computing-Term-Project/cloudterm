from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class SessionWsManager:
    def __init__(self) -> None:
        self._connections: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, session_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id].add(websocket)

    def disconnect(self, session_id: UUID, websocket: WebSocket) -> None:
        connections = self._connections.get(session_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(session_id, None)

    async def broadcast(self, session_id: UUID, message: dict) -> None:
        connections = list(self._connections.get(session_id, set()))
        for websocket in connections:
            await websocket.send_json(message)


session_ws_manager = SessionWsManager()

