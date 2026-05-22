from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.runner import RunnerClient, RunnerUnavailableError
from app.db.session import get_db_session
from app.repositories.comments import CommentRepository
from app.repositories.sessions import SessionRepository
from app.schemas.comments import (
    CommentCreateRequest,
    CommentListResponse,
    CommentResponse,
    ReplyCreateRequest,
    ReplyResponse,
)
from app.schemas.runs import RunExecuteRequest, RunExecuteResponse
from app.schemas.sessions import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDetailResponse,
)
from app.services.comments import CommentNotFoundError, CommentService
from app.services.runs import RunService
from app.services.sessions import SessionNotFoundError, SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_service(db_session: AsyncSession = Depends(get_db_session)) -> SessionService:
    repository = SessionRepository(db_session=db_session)
    return SessionService(repository=repository)


def get_run_service() -> RunService:
    return RunService(runner_client=RunnerClient())


def get_comment_service(db_session: AsyncSession = Depends(get_db_session)) -> CommentService:
    repository = CommentRepository(db_session=db_session)
    return CommentService(repository=repository)


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreateRequest,
    session_service: SessionService = Depends(get_session_service),
) -> SessionCreateResponse:
    return await session_service.create_session(title=payload.title)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    session_service: SessionService = Depends(get_session_service),
) -> SessionDetailResponse:
    try:
        return await session_service.get_session(session_id=session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc


@router.post("/{session_id}/run", response_model=RunExecuteResponse)
async def execute_session_code(
    session_id: UUID,
    payload: RunExecuteRequest,
    session_service: SessionService = Depends(get_session_service),
    run_service: RunService = Depends(get_run_service),
) -> RunExecuteResponse:
    try:
        await session_service.get_session(session_id=session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc

    try:
        return await run_service.execute_run(payload=payload)
    except RunnerUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Runner unavailable") from exc


@router.get("/{session_id}/comments", response_model=CommentListResponse)
async def get_comments(
    session_id: UUID,
    session_service: SessionService = Depends(get_session_service),
    comment_service: CommentService = Depends(get_comment_service),
) -> CommentListResponse:
    try:
        await session_service.get_session(session_id=session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc

    return await comment_service.list_comments(session_id=session_id)


@router.post("/{session_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    session_id: UUID,
    payload: CommentCreateRequest,
    session_service: SessionService = Depends(get_session_service),
    comment_service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    try:
        await session_service.get_session(session_id=session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc

    return await comment_service.create_comment(session_id=session_id, payload=payload)


@router.post(
    "/{session_id}/comments/{comment_id}/replies",
    response_model=ReplyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reply(
    session_id: UUID,
    comment_id: UUID,
    payload: ReplyCreateRequest,
    session_service: SessionService = Depends(get_session_service),
    comment_service: CommentService = Depends(get_comment_service),
) -> ReplyResponse:
    try:
        await session_service.get_session(session_id=session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found") from exc

    try:
        return await comment_service.create_reply(session_id=session_id, comment_id=comment_id, payload=payload)
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found") from exc
