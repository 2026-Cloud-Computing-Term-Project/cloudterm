from __future__ import annotations

import base64
import asyncio
import concurrent.futures
import logging
import time

import docker
from docker.errors import APIError, DockerException, ImageNotFound
from fastapi import APIRouter, HTTPException, status

from app.core.settings import settings
from app.schemas import RunRequest, RunResponse

router = APIRouter(tags=["run"])
logger = logging.getLogger(__name__)

SANDBOX_MAX_ATTEMPTS = 2


def _execute_python_in_docker_once(code: str, stdin: str, timeout_seconds: int) -> RunResponse:
    client = docker.from_env()
    logger.info("runner.sandbox.image_check image=%s", settings.sandbox_image)
    try:
        client.images.get(settings.sandbox_image)
    except ImageNotFound:
        logger.info("runner.sandbox.image_pull image=%s", settings.sandbox_image)
        client.images.pull(settings.sandbox_image)

    container = None
    try:
        logger.info(
            "runner.sandbox.start image=%s timeout_seconds=%s",
            settings.sandbox_image,
            timeout_seconds,
        )
        encoded_code = base64.b64encode(code.encode("utf-8")).decode("ascii")
        encoded_stdin = base64.b64encode(stdin.encode("utf-8")).decode("ascii")
        container = client.containers.create(
            image=settings.sandbox_image,
            command=["sh", "-lc", "while :; do sleep 3600; done"],
            detach=True,
            network_disabled=True,
            mem_limit=settings.sandbox_memory_limit,
            nano_cpus=settings.sandbox_cpu_nano,
            pids_limit=settings.sandbox_pids_limit,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges"],
            working_dir=settings.sandbox_workdir,
            environment={
                "RUNNER_CODE_B64": encoded_code,
                "RUNNER_STDIN_B64": encoded_stdin,
            },
        )
        container.start()

        def _run_exec() -> tuple[str, str, int]:
            exec_result = container.exec_run(
                cmd=[
                    "python",
                    "-c",
                    "import base64, io, os, sys; "
                    "code = base64.b64decode(os.environ['RUNNER_CODE_B64']).decode(); "
                    "stdin = base64.b64decode(os.environ['RUNNER_STDIN_B64']).decode(); "
                    "sys.stdin = io.StringIO(stdin); "
                    "exec(compile(code, '<runner>', 'exec'), {})",
                ],
                environment={
                    "RUNNER_CODE_B64": encoded_code,
                    "RUNNER_STDIN_B64": encoded_stdin,
                },
                demux=True,
            )

            stdout_bytes = b""
            stderr_bytes = b""
            if isinstance(exec_result.output, tuple):
                stdout_bytes = exec_result.output[0] or b""
                stderr_bytes = exec_result.output[1] or b""
            elif isinstance(exec_result.output, bytes):
                stdout_bytes = exec_result.output

            return (
                stdout_bytes.decode("utf-8", errors="replace"),
                stderr_bytes.decode("utf-8", errors="replace"),
                int(exec_result.exit_code),
            )

        timed_out = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_exec)
            try:
                stdout, stderr, exit_code = future.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                timed_out = True
                logger.warning(
                    "runner.sandbox.timeout container_id=%s timeout_seconds=%s",
                    container.id,
                    timeout_seconds,
                )
                try:
                    container.kill()
                except DockerException:
                    pass
                stdout = ""
                stderr = ""
                exit_code = 124

        logger.info(
            "runner.sandbox.complete container_id=%s exit_code=%s timed_out=%s",
            container.id,
            exit_code,
            timed_out,
        )
        return RunResponse(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timed_out=timed_out,
        )
    finally:
        if container is not None:
            try:
                container.remove(force=True)
                logger.info("runner.sandbox.cleanup container_id=%s", container.id)
            except DockerException:
                logger.warning("runner.sandbox.cleanup_failed container_id=%s", container.id)


def _execute_python_in_docker(code: str, stdin: str, timeout_seconds: int) -> RunResponse:
    last_error: Exception | None = None
    for attempt in range(1, SANDBOX_MAX_ATTEMPTS + 1):
        try:
            return _execute_python_in_docker_once(code, stdin, timeout_seconds)
        except (APIError, DockerException, ValueError, KeyError, TypeError) as exc:
            last_error = exc
            logger.exception(
                "runner.sandbox.failed attempt=%s max_attempts=%s",
                attempt,
                SANDBOX_MAX_ATTEMPTS,
            )
            if attempt < SANDBOX_MAX_ATTEMPTS:
                time.sleep(0.25 * attempt)
                continue
            raise DockerException(str(exc)) from exc

    assert last_error is not None
    raise DockerException(str(last_error))


@router.post("/run", response_model=RunResponse)
async def run_code(payload: RunRequest) -> RunResponse:
    if payload.language != "python":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only python execution is supported",
        )

    try:
        return await asyncio.to_thread(
            _execute_python_in_docker,
            payload.code,
            payload.stdin,
            payload.timeout_seconds,
        )
    except DockerException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker sandbox unavailable",
        ) from exc
