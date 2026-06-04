from __future__ import annotations

import asyncio
import logging
import tempfile
import time
from pathlib import Path

import docker
from docker.errors import APIError, DockerException, ImageNotFound
from fastapi import APIRouter, HTTPException, status

from app.core.settings import settings
from app.schemas import RunRequest, RunResponse

router = APIRouter(tags=["run"])
logger = logging.getLogger(__name__)

SANDBOX_OUTPUT_DIR = f"{settings.sandbox_workdir}/output"
SANDBOX_INPUT_DIR = f"{settings.sandbox_workdir}/input"
SANDBOX_MAX_ATTEMPTS = 2


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _execute_python_in_docker_once(code: str, stdin: str, timeout_seconds: int) -> RunResponse:
    client = docker.from_env()
    logger.info("runner.sandbox.image_check image=%s", settings.sandbox_image)
    try:
        client.images.get(settings.sandbox_image)
    except ImageNotFound:
        logger.info("runner.sandbox.image_pull image=%s", settings.sandbox_image)
        client.images.pull(settings.sandbox_image)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_dir = temp_path / "input"
        output_dir = temp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        (input_dir / "main.py").write_text(code, encoding="utf-8")
        (input_dir / "stdin.txt").write_text(stdin, encoding="utf-8")

        container = None
        try:
            logger.info(
                "runner.sandbox.start image=%s timeout_seconds=%s",
                settings.sandbox_image,
                timeout_seconds,
            )
            container = client.containers.create(
                image=settings.sandbox_image,
                command=[
                    "sh",
                    "-lc",
                    "python -I /workspace/input/main.py "
                    "< /workspace/input/stdin.txt "
                    "1>/workspace/output/stdout.txt "
                    "2>/workspace/output/stderr.txt",
                ],
                detach=True,
                network_disabled=True,
                read_only=True,
                mem_limit=settings.sandbox_memory_limit,
                nano_cpus=settings.sandbox_cpu_nano,
                pids_limit=settings.sandbox_pids_limit,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                working_dir=settings.sandbox_workdir,
                tmpfs={
                    "/tmp": f"rw,nosuid,nodev,noexec,size={settings.sandbox_tmpfs_size}",
                },
                volumes={
                    str(input_dir): {"bind": SANDBOX_INPUT_DIR, "mode": "ro"},
                    str(output_dir): {"bind": SANDBOX_OUTPUT_DIR, "mode": "rw"},
                },
            )
            container.start()

            deadline = time.monotonic() + timeout_seconds
            timed_out = False

            while True:
                container.reload()
                if container.status == "exited":
                    break
                if time.monotonic() >= deadline:
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
                    break
                time.sleep(0.05)

            container.reload()
            exit_code = int(container.attrs["State"]["ExitCode"])
            if timed_out:
                exit_code = 124

            logger.info(
                "runner.sandbox.complete container_id=%s exit_code=%s timed_out=%s",
                container.id,
                exit_code,
                timed_out,
            )
            return RunResponse(
                stdout=_read_text(output_dir / "stdout.txt"),
                stderr=_read_text(output_dir / "stderr.txt"),
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
