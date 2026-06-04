from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RunExecuteRequest(BaseModel):
    language: Literal["python"] = Field(default="python")
    code: str = Field(min_length=1)
    stdin: str = Field(default="")


class RunnerRunRequest(BaseModel):
    language: Literal["python"]
    code: str = Field(min_length=1)
    stdin: str = Field(default="")
    timeout_seconds: int = Field(gt=0)


class RunnerRunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


class RunExecuteResponse(BaseModel):
    run_id: UUID
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
