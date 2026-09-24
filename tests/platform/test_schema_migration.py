from datetime import UTC, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from phisim.infra.sqlite.connection import (
    Base,
    migrate_simulation_attack_schema,
)
from phisim.infra.sqlite.models.scenario import Scenario
from phisim.infra.sqlite.models.session import Session as SessionModel
from phisim.infra.sqlite.models.simulation_attack import SimulationAttack
from phisim.infra.sqlite.models.simulation_run import SimulationRun


def test_legacy_attack_uniqueness_is_upgraded_idempotently() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    now = datetime.now(UTC)

    with Session(engine) as database_session:
        database_session.add_all(
            [
                Scenario(
                    scenario_id="legacy-scenario",
                    name="Legacy scenario",
                    scenario_type="website",
                    description="Legacy local fixture.",
                    created_at=now,
                ),
                Scenario(
                    scenario_id="legacy-scenario-2",
                    name="Legacy scenario 2",
                    scenario_type="website",
                    description="Legacy local fixture.",
                    created_at=now,
                ),
            ]
        )
        database_session.add_all(
            [
                SessionModel(
                    session_id="operator-session",
                    scenario_id="legacy-scenario",
                    started_at=now,
                    completed_at=None,
                    status="active",
                ),
                SessionModel(
                    session_id="victim-session",
                    scenario_id="legacy-scenario",
                    started_at=now,
                    completed_at=None,
                    status="active",
                ),
            ]
        )
        database_session.add_all(
            [
                SimulationRun(
                    run_id="legacy-run-1",
                    session_id="operator-session",
                    scenario_id="legacy-scenario",
                    channel="website",
                    state={},
                    started_at=now,
                    updated_at=now,
                ),
                SimulationRun(
                    run_id="legacy-run-2",
                    session_id="operator-session",
                    scenario_id="legacy-scenario-2",
                    channel="website",
                    state={},
                    started_at=now,
                    updated_at=now,
                ),
            ]
        )
        database_session.flush()
        database_session.add_all(
            [
                SimulationAttack(
                    attack_id="legacy-attack-1",
                    run_id="legacy-run-1",
                    operator_session_id="operator-session",
                    victim_session_id="victim-session",
                    victim_token="legacy-token",
                    scenario_id="legacy-scenario",
                    channel="website",
                    status="COMPLETED",
                    state={},
                    delivery_due_at=now,
                    created_at=now,
                    updated_at=now,
                ),
            ]
        )
        database_session.commit()

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "DROP INDEX IF EXISTS ix_simulation_attacks_victim_session_id"
        )
        connection.exec_driver_sql(
            "DROP INDEX IF EXISTS ix_simulation_attacks_victim_token"
        )
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX ix_simulation_attacks_victim_session_id "
            "ON simulation_attacks(victim_session_id)"
        )
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX ix_simulation_attacks_victim_token "
            "ON simulation_attacks(victim_token)"
        )

    assert migrate_simulation_attack_schema(engine) is True
    assert migrate_simulation_attack_schema(engine) is False

    with engine.connect() as connection:
        indexes = connection.exec_driver_sql(
            'PRAGMA index_list("simulation_attacks")'
        ).all()
        unique_columns = {
            tuple(
                str(column[2])
                for column in connection.exec_driver_sql(
                    f'PRAGMA index_info("{index[1]}")'
                )
            )
            for index in indexes
            if int(index[2]) == 1
        }
        count = connection.execute(
            text("SELECT COUNT(*) FROM simulation_attacks")
        ).scalar_one()
    assert ("victim_session_id",) not in unique_columns
    assert ("victim_token",) not in unique_columns
    assert count == 1

    with Session(engine) as database_session:
        database_session.add(
            SimulationAttack(
                attack_id="legacy-attack-2",
                run_id="legacy-run-2",
                operator_session_id="operator-session",
                victim_session_id="victim-session",
                victim_token="legacy-token",
                scenario_id="legacy-scenario",
                channel="website",
                status="COMPLETED",
                state={},
                delivery_due_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        database_session.commit()

    engine.dispose()
