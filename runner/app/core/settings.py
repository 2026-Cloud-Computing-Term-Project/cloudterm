from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    sandbox_image: str = "python:3.12-slim"
    sandbox_workdir: str = "/workspace"
    sandbox_memory_limit: str = "128m"
    sandbox_cpu_nano: int = 500_000_000
    sandbox_pids_limit: int = 64
    sandbox_tmpfs_size: str = "64m"
    sandbox_user: str = "1000:1000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="RUNNER_",
        extra="ignore",
    )


settings = Settings()
