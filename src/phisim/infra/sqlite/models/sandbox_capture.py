from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from phisim.infra.sqlite.connection import Base


class SandboxCapture(Base):
    """Persisted metadata for an explicitly enabled synthetic sandbox capture.

    Secret-like fields are represented by salted digests in ``secret_digests``.
    Exact values for those fields live only in the bounded process-local display
    cache maintained by :mod:`phisim.simulation.capture`.
    """

    __tablename__ = "sandbox_captures"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    capture_id: Mapped[str] = mapped_column(
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

    step: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    values: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    secret_digests: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
