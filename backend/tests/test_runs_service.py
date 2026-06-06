import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.runs import RunService


class FakeRunRepository:
    def __init__(self, runs):
        self.runs = runs
        self.requested_session_id = None

    async def list_runs(self, session_id):
        self.requested_session_id = session_id
        return self.runs


class RunServiceHistoryTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_list_runs_returns_saved_code_and_result_fields(self) -> None:
        session_id = uuid4()
        run_id = uuid4()
        created_at = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)
        repository = FakeRunRepository(
            [
                SimpleNamespace(
                    run_id=run_id,
                    language="python",
                    code="print('saved')",
                    stdin="",
                    stdout="saved\n",
                    stderr="",
                    exit_code=0,
                    timed_out=False,
                    created_at=created_at,
                ),
            ],
        )

        service = RunService(runner_client=object(), run_repository=repository)
        result = await service.list_runs(session_id=session_id)

        self.assertEqual(repository.requested_session_id, session_id)
        self.assertEqual(len(result.runs), 1)
        self.assertEqual(result.runs[0].run_id, run_id)
        self.assertEqual(result.runs[0].code, "print('saved')")
        self.assertEqual(result.runs[0].stdout, "saved\n")
        self.assertEqual(result.runs[0].created_at, created_at)
