import asyncio
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.session import AsyncSessionLocal
from app.repositories.sessions import SessionRepository
from app.services.sessions import SessionNotFoundError, SessionService
from app.ws.manager import session_ws_manager

router = APIRouter(tags=["ws"])

HEARTBEAT_INTERVAL_SECONDS = 30
HEARTBEAT_TIMEOUT_SECONDS = HEARTBEAT_INTERVAL_SECONDS * 2


async def _handle_heartbeat_message(websocket: WebSocket, message: str) -> bool:
    normalized_message = message.strip().lower()
    if normalized_message == "ping":
        await websocket.send_json({"type": "pong"})
        return True
    if normalized_message == "pong":
        return True
    return False


@router.websocket("/ws/sessions/{session_id}")
async def session_websocket(session_id: UUID, websocket: WebSocket) -> None:
    async with AsyncSessionLocal() as db_session:
        session_service = SessionService(repository=SessionRepository(db_session=db_session))
        try:
            await session_service.get_session(session_id=session_id)
        except SessionNotFoundError:
            await websocket.close(code=1008)
            return

    await session_ws_manager.connect(session_id=session_id, websocket=websocket)
    try:
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=HEARTBEAT_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                await websocket.close(
                    code=1001,
                    reason="heartbeat timeout",
                )
                break

            await _handle_heartbeat_message(websocket=websocket, message=message)
    except WebSocketDisconnect:
        pass
    finally:
        session_ws_manager.disconnect(session_id=session_id, websocket=websocket)
