from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session

from phisim.utils.env import settings

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "phisim.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH}"


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    return settings.db_url or DEFAULT_DATABASE_URL


def create_database_engine() -> Engine:
    database_url = get_database_url()

    connect_args = {}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    if database_url.startswith("sqlite:///"):
        database_path = database_url.removeprefix("sqlite:///")

        if database_path != ":memory:":
            Path(database_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

    return create_engine(
        database_url,
        connect_args=connect_args,
    )


engine = create_database_engine()


def get_session() -> Session:
    return Session(engine)


def initialize_database() -> None:
    Base.metadata.create_all(engine)
