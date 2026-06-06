from typing import Literal

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    language: Literal["python"]
    code: str = Field(min_length=1)
    stdin: str = Field(default="")
    timeout_seconds: int = Field(gt=0)


class RunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
