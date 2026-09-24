from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from phisim.infra.sqlite.connection import Base


class SimulationAttack(Base):
    __tablename__ = "simulation_attacks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    attack_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("simulation_runs.run_id"),
        nullable=False,
        unique=True,
        index=True,
    )

    operator_session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id"),
        nullable=False,
        index=True,
    )

    victim_session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sessions.session_id"),
        nullable=False,
        index=True,
    )

    victim_token: Mapped[str] = mapped_column(
        String(96),
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

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="ARMED",
        index=True,
    )

    state: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    delivery_due_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    engaged_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
