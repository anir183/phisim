from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from phisim.infra.sqlite.connection import Base


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "scenario_id",
            name="uq_simulation_runs_session_scenario",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    run_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id"),
        nullable=False,
        index=True,
    )

    scenario_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    state: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
