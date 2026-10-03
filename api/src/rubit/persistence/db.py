import os
from pathlib import Path

from platformdirs import user_data_path
from sqlalchemy import Engine, inspect, text
from sqlmodel import create_engine

from rubit.persistence.models import MortgageRecord

DB_PATH_ENV = "RUBIT_DB_PATH"


def default_db_path() -> Path:
    """``$RUBIT_DB_PATH``, or ``rubit.db`` in the OS app-data directory."""
    if env_path := os.environ.get(DB_PATH_ENV):
        return Path(env_path)
    return user_data_path("rubit-finance", appauthor=False) / "rubit.db"


def create_db_engine(path: Path) -> Engine:
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    MortgageRecord.metadata.create_all(engine)
    _add_missing_columns(engine)
    return engine


def _add_missing_columns(engine: Engine) -> None:
    """Bring databases created before a column existed up to date (no migration tool yet)."""
    columns = {column["name"] for column in inspect(engine).get_columns("mortgages")}
    if "start_date" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE mortgages ADD COLUMN start_date DATE"))
