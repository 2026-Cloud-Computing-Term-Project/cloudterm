from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Cloudterm Backend API"
    app_version: str = "0.1.0"
    database_url: str = "postgresql://cloudterm:cloudterm@postgres:5432/cloudterm"
    runner_url: str = "http://runner:8001"
    run_timeout_seconds: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

