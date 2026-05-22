from uuid import uuid4

from app.clients.runner import RunnerClient
from app.core.settings import settings
from app.schemas.runs import RunExecuteRequest, RunExecuteResponse, RunnerRunRequest


class RunService:
    def __init__(self, runner_client: RunnerClient) -> None:
        self.runner_client = runner_client

    async def execute_run(self, payload: RunExecuteRequest) -> RunExecuteResponse:
        runner_payload = RunnerRunRequest(
            language=payload.language,
            code=payload.code,
            stdin=payload.stdin,
            timeout_seconds=settings.run_timeout_seconds,
        )
        runner_response = await self.runner_client.run_code(runner_payload)
        return RunExecuteResponse(
            run_id=uuid4(),
            stdout=runner_response.stdout,
            stderr=runner_response.stderr,
            exit_code=runner_response.exit_code,
            timed_out=runner_response.timed_out,
        )

