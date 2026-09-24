from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session

from phisim.utils.env import settings
from phisim.utils.paths import DB_FILE

DEFAULT_DATABASE_PATH = DB_FILE
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

    return create_engine(
        database_url,
        connect_args=connect_args,
    )


engine = create_database_engine()


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session


def initialize_database() -> None:
    if settings.db_url is None:
        DEFAULT_DATABASE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    import phisim.infra.sqlite.models_registry  # noqa: F401

    Base.metadata.create_all(engine)
