from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Cloudterm Backend API"
    app_version: str = "0.1.0"
    frontend_base_url: str = "http://localhost:5173"
    database_url: str = "postgresql://cloudterm:cloudterm@postgres:5432/cloudterm"
    runner_url: str = "http://runner:8001"
    run_timeout_seconds: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


settings = Settings()
