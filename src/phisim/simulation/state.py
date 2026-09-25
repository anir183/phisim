from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from phisim.infra.sqlite.models.simulation_run import SimulationRun
from phisim.infra.sqlite.repos.simulation_run import SimulationRunRepository
from phisim.security.guardrails import (
    UnsafeMetadataError,
    enforce_safe_event_metadata,
)


class SimulationStateError(ValueError):
    """Raised when simulation state is not safe or supported."""


_ALLOWED_STATE_KEYS = frozenset(
    {
        "read_message_ids",
        "read_thread_ids",
        "auth_stage",
        "username_present",
        "attachment_opened",
        "mfa_step",
        "mfa_decision",
        "last_action",
        "typing",
        "completion_outcome",
    }
)
_ALLOWED_AUTH_STAGES = frozenset(
    {"landing", "username", "password", "destination", "complete"}
)
_ALLOWED_ACTIONS = frozenset(
    {
        "scenario_started",
        "message_opened",
        "attachment_previewed",
        "credential_submitted",
        "credential_incomplete",
        "scenario_completed",
        "destination_reached",
    }
)


def _validate_state(state: dict[str, Any]) -> dict[str, Any]:
    unknown = set(state) - _ALLOWED_STATE_KEYS
    if unknown:
        raise SimulationStateError("Unsupported simulation state fields.")

    try:
        safe_state = enforce_safe_event_metadata(state)
    except UnsafeMetadataError:
        raise SimulationStateError("Unsafe simulation state.") from None

    for key in ("read_message_ids", "read_thread_ids"):
        values = safe_state.get(key, [])
        if not isinstance(values, list) or len(values) > 100:
            raise SimulationStateError("Invalid simulation read state.")
        if any(
            not isinstance(value, str) or not value or len(value) > 64
            for value in values
        ):
            raise SimulationStateError("Invalid simulation read state.")

    auth_stage = safe_state.get("auth_stage")
    if auth_stage is not None and auth_stage not in _ALLOWED_AUTH_STAGES:
        raise SimulationStateError("Invalid authentication stage.")

    completion_outcome = safe_state.get("completion_outcome")
    if completion_outcome is not None and completion_outcome not in {
        "ended_by_user",
        "training_complete",
    }:
        raise SimulationStateError("Invalid completion outcome.")

    for key in ("username_present", "attachment_opened", "typing"):
        value = safe_state.get(key)
        if value is not None and not isinstance(value, bool):
            raise SimulationStateError("Invalid simulation boolean state.")

    mfa_step = safe_state.get("mfa_step")
    if mfa_step is not None and (
        isinstance(mfa_step, bool)
        or not isinstance(mfa_step, int)
        or not 1 <= mfa_step <= 20
    ):
        raise SimulationStateError("Invalid MFA state.")

    mfa_decision = safe_state.get("mfa_decision")
    if mfa_decision is not None and mfa_decision not in {"approve", "deny"}:
        raise SimulationStateError("Invalid MFA decision.")

    last_action = safe_state.get("last_action")
    if last_action is not None and last_action not in _ALLOWED_ACTIONS:
        raise SimulationStateError("Invalid simulation action.")

    return safe_state


class SimulationStateService:
    def __init__(self, repository: SimulationRunRepository) -> None:
        self.repository = repository

    def get_or_create(
        self,
        *,
        session_id: str,
        scenario_id: str,
        channel: str,
        initial_state: dict[str, Any] | None = None,
    ) -> SimulationRun:
        existing = self.repository.get_by_session_and_scenario(
            session_id,
            scenario_id,
        )
        if existing is not None:
            return existing

        now = datetime.now(UTC)
        run = SimulationRun(
            run_id=uuid4().hex,
            session_id=session_id,
            scenario_id=scenario_id,
            channel=channel,
            state=_validate_state(initial_state or {}),
            started_at=now,
            updated_at=now,
        )
        try:
            return self.repository.create(run)
        except IntegrityError:
            existing = self.repository.get_by_session_and_scenario(
                session_id,
                scenario_id,
            )
            if existing is not None:
                return existing
            raise

    def update(
        self,
        run_id: str,
        changes: dict[str, Any],
    ) -> SimulationRun:
        run = self.repository.get_by_run_id(run_id)
        if run is None:
            raise SimulationStateError("Simulation run not found.")

        changes = _validate_state(changes)
        run.state = {**run.state, **changes}
        return self.repository.save(run)

    def get(self, run_id: str) -> SimulationRun:
        run = self.repository.get_by_run_id(run_id)
        if run is None:
            raise SimulationStateError("Simulation run not found.")
        return run
