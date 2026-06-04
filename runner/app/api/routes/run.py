from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.schemas import RunRequest, RunResponse

router = APIRouter(tags=["run"])


async def _execute_python(code: str, stdin: str, timeout_seconds: int) -> RunResponse:
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "main.py"
        script_path.write_text(code, encoding="utf-8")

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-I",
            str(script_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input=stdin.encode("utf-8")),
                timeout=timeout_seconds,
            )
            timed_out = False
            exit_code = int(process.returncode or 0)
        except asyncio.TimeoutError:
            process.kill()
            stdout_bytes, stderr_bytes = await process.communicate()
            timed_out = True
            exit_code = 124

    return RunResponse(
        stdout=stdout_bytes.decode("utf-8", errors="replace"),
        stderr=stderr_bytes.decode("utf-8", errors="replace"),
        exit_code=exit_code,
        timed_out=timed_out,
    )


@router.post("/run", response_model=RunResponse)
async def run_code(payload: RunRequest) -> RunResponse:
    if payload.language != "python":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only python execution is supported",
        )
    return await _execute_python(
        code=payload.code,
        stdin=payload.stdin,
        timeout_seconds=payload.timeout_seconds,
    )
