from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.settings import settings


def upgrade_database() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    alembic_ini = backend_root / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.sqlalchemy_database_url)
    command.upgrade(config, "head")
