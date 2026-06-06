import unittest
import sys
from types import SimpleNamespace
from pathlib import Path
from uuid import uuid4
from types import ModuleType

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.modules.setdefault("asyncpg", ModuleType("asyncpg"))

from app.api.routes.sessions import execute_session_code, get_session_runs
from app.clients.runner import RunnerExecutionError, RunnerUnavailableError
from app.schemas.runs import RunExecuteRequest
from app.services.sessions import SessionNotFoundError


class FakeSessionService:
    async def get_session(self, session_id):
        return SimpleNamespace(session_id=session_id)


class FakeMissingSessionService:
    async def get_session(self, session_id):
        raise SessionNotFoundError


class FakeRunServiceExecutionError:
    async def execute_run(self, session_id, payload):
        raise RunnerExecutionError("runner rejected the execution request")


class FakeRunServiceUnavailableError:
    async def execute_run(self, session_id, payload):
        raise RunnerUnavailableError()


class FakeRunHistoryService:
    async def list_runs(self, session_id):
        return SimpleNamespace(runs=[])


class SessionRouteRunnerMappingTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_execute_session_code_maps_runner_execution_error_to_400(self) -> None:
        session_id = uuid4()
        payload = RunExecuteRequest(code="print('hi')")

        with self.assertRaises(HTTPException) as context:
            await execute_session_code(
                session_id=session_id,
                payload=payload,
                session_service=FakeSessionService(),
                run_service=FakeRunServiceExecutionError(),
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "runner rejected the execution request")

    async def test_execute_session_code_maps_runner_unavailable_error_to_502(self) -> None:
        session_id = uuid4()
        payload = RunExecuteRequest(code="print('hi')")

        with self.assertRaises(HTTPException) as context:
            await execute_session_code(
                session_id=session_id,
                payload=payload,
                session_service=FakeSessionService(),
                run_service=FakeRunServiceUnavailableError(),
            )

        self.assertEqual(context.exception.status_code, 502)
        self.assertEqual(context.exception.detail, "Runner unavailable")

    async def test_get_session_runs_maps_missing_session_to_404(self) -> None:
        session_id = uuid4()

        with self.assertRaises(HTTPException) as context:
            await get_session_runs(
                session_id=session_id,
                session_service=FakeMissingSessionService(),
                run_service=FakeRunHistoryService(),
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Session not found")
