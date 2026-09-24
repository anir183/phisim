from collections.abc import Generator
from typing import cast

from sqlalchemy import Table, create_engine
from sqlalchemy.engine import Connection, Engine
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


def _sqlite_unique_index_columns(
    connection: Connection,
    table_name: str,
) -> set[tuple[str, ...]]:
    unique_columns: set[tuple[str, ...]] = set()
    index_rows = connection.exec_driver_sql(
        f'PRAGMA index_list("{table_name}")'
    )
    for index_row in index_rows:
        if int(index_row[2]) != 1:
            continue
        index_name = str(index_row[1])
        column_rows = connection.exec_driver_sql(
            f'PRAGMA index_info("{index_name}")'
        )
        columns = tuple(str(column_row[2]) for column_row in column_rows)
        if columns:
            unique_columns.add(columns)
    return unique_columns


def migrate_simulation_attack_schema(database_engine: Engine) -> bool:
    """Upgrade the local attack table from the first realism-pass schema.

    SQLite does not remove unique constraints with ``create_all``. Early local
    databases made the victim Session and context token unique, which prevents
    one pre-opened victim environment from receiving multiple independent
    attacks. Rebuild only that local table when those obsolete single-column
    indexes are present; all rows and safe timestamps are copied unchanged.
    """
    if database_engine.dialect.name != "sqlite":
        return False

    with database_engine.begin() as connection:
        table_exists = connection.exec_driver_sql(
            "SELECT 1 FROM sqlite_master "
            "WHERE type = 'table' AND name = 'simulation_attacks'"
        ).first()
        if table_exists is None:
            return False

        unique_columns = _sqlite_unique_index_columns(
            connection,
            "simulation_attacks",
        )
        legacy_constraints = {
            ("victim_session_id",),
            ("victim_token",),
        }
        if not unique_columns.intersection(legacy_constraints):
            return False

        index_rows = connection.exec_driver_sql(
            'PRAGMA index_list("simulation_attacks")'
        )
        index_names = [
            str(index_row[1])
            for index_row in index_rows
            if not str(index_row[1]).startswith("sqlite_autoindex_")
        ]
        for index_name in index_names:
            connection.exec_driver_sql(f'DROP INDEX IF EXISTS "{index_name}"')

        connection.exec_driver_sql(
            "ALTER TABLE simulation_attacks RENAME TO simulation_attacks_legacy"
        )

        import phisim.infra.sqlite.models_registry  # noqa: F401
        from phisim.infra.sqlite.models.simulation_attack import (
            SimulationAttack,
        )

        table = cast(Table, SimulationAttack.__table__)
        table.create(bind=connection)
        columns = tuple(column.name for column in table.columns)
        column_sql = ", ".join(columns)
        connection.exec_driver_sql(
            f"INSERT INTO simulation_attacks ({column_sql}) "
            f"SELECT {column_sql} FROM simulation_attacks_legacy"
        )
        connection.exec_driver_sql("DROP TABLE simulation_attacks_legacy")
    return True


def initialize_database() -> None:
    if settings.db_url is None:
        DEFAULT_DATABASE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    import phisim.infra.sqlite.models_registry  # noqa: F401

    Base.metadata.create_all(engine)
    migrate_simulation_attack_schema(engine)
