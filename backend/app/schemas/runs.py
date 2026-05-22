from uuid import UUID

from pydantic import BaseModel, Field


class RunExecuteRequest(BaseModel):
    language: str = Field(default="python")
    code: str
    stdin: str = Field(default="")


class RunnerRunRequest(BaseModel):
    language: str
    code: str
    stdin: str
    timeout_seconds: int


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

