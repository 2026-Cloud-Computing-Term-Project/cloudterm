import httpx

from app.core.settings import settings
from app.schemas.runs import RunnerRunRequest, RunnerRunResponse


class RunnerUnavailableError(Exception):
    pass


class RunnerClient:
    async def run_code(self, payload: RunnerRunRequest) -> RunnerRunResponse:
        try:
            async with httpx.AsyncClient(timeout=settings.run_timeout_seconds + 2) as client:
                response = await client.post(
                    f"{settings.runner_url}/run",
                    json=payload.model_dump(),
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RunnerUnavailableError from exc

        return RunnerRunResponse.model_validate(response.json())

