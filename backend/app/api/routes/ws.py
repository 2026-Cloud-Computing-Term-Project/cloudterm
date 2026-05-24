from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.session import AsyncSessionLocal
from app.repositories.sessions import SessionRepository
from app.services.sessions import SessionNotFoundError, SessionService
from app.ws.manager import session_ws_manager

router = APIRouter(tags=["ws"])


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
            await websocket.receive_text()
    except WebSocketDisconnect:
        session_ws_manager.disconnect(session_id=session_id, websocket=websocket)
