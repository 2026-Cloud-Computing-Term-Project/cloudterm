from uuid import UUID

from app.clients.runner import RunnerClient
from app.core.settings import settings
from app.repositories.runs import RunRepository
from app.schemas.runs import RunExecuteRequest, RunExecuteResponse, RunnerRunRequest


class RunService:
    def __init__(self, runner_client: RunnerClient, run_repository: RunRepository) -> None:
        self.runner_client = runner_client
        self.run_repository = run_repository

    async def execute_run(self, session_id: UUID, payload: RunExecuteRequest) -> RunExecuteResponse:
        runner_payload = RunnerRunRequest(
            language=payload.language,
            code=payload.code,
            stdin=payload.stdin,
            timeout_seconds=settings.run_timeout_seconds,
        )
        runner_response = await self.runner_client.run_code(runner_payload)
        run = await self.run_repository.create_run(
            session_id=session_id,
            language=payload.language,
            code=payload.code,
            stdin=payload.stdin,
            stdout=runner_response.stdout,
            stderr=runner_response.stderr,
            exit_code=runner_response.exit_code,
            timed_out=runner_response.timed_out,
        )
        return RunExecuteResponse(
            run_id=run.run_id,
            stdout=runner_response.stdout,
            stderr=runner_response.stderr,
            exit_code=runner_response.exit_code,
            timed_out=runner_response.timed_out,
        )
