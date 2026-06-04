import httpx

from app.core.settings import settings
from app.schemas.runs import RunnerRunRequest, RunnerRunResponse


class RunnerUnavailableError(Exception):
    pass


class RunnerExecutionError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class RunnerClient:
    async def run_code(self, payload: RunnerRunRequest) -> RunnerRunResponse:
        try:
            timeout = httpx.Timeout(
                connect=2.0,
                read=settings.run_timeout_seconds + 2.0,
                write=5.0,
                pool=5.0,
            )
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.runner_url}/run",
                    json=payload.model_dump(),
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if 400 <= exc.response.status_code < 500:
                detail = "Runner rejected the execution request"
                try:
                    payload_detail = exc.response.json().get("detail")
                    if isinstance(payload_detail, str) and payload_detail.strip():
                        detail = payload_detail
                except ValueError:
                    pass
                raise RunnerExecutionError(detail) from exc
            raise RunnerUnavailableError from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise RunnerUnavailableError from exc

        return RunnerRunResponse.model_validate(response.json())
