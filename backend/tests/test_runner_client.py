import unittest
import sys
from pathlib import Path
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.clients.runner import RunnerClient, RunnerExecutionError, RunnerUnavailableError
from app.schemas.runs import RunnerRunRequest


class FakeAsyncClient:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def post(self, *_args, **_kwargs) -> httpx.Response:
        return self.response


class RunnerClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_run_code_maps_4xx_to_runner_execution_error(self) -> None:
        request = httpx.Request("POST", "http://runner:8001/run")
        response = httpx.Response(400, request=request, json={"detail": "invalid payload"})

        with patch("app.clients.runner.httpx.AsyncClient", return_value=FakeAsyncClient(response)):
            client = RunnerClient()
            payload = RunnerRunRequest(language="python", code="print('hi')", stdin="", timeout_seconds=3)

            with self.assertRaises(RunnerExecutionError) as context:
                await client.run_code(payload)

        self.assertEqual(context.exception.detail, "invalid payload")

    async def test_run_code_maps_5xx_to_runner_unavailable_error(self) -> None:
        request = httpx.Request("POST", "http://runner:8001/run")
        response = httpx.Response(500, request=request, json={"detail": "boom"})

        with patch("app.clients.runner.httpx.AsyncClient", return_value=FakeAsyncClient(response)):
            client = RunnerClient()
            payload = RunnerRunRequest(language="python", code="print('hi')", stdin="", timeout_seconds=3)

            with self.assertRaises(RunnerUnavailableError):
                await client.run_code(payload)
