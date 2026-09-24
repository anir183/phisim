from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.models.simulation_attack import SimulationAttack
from phisim.infra.sqlite.repos.simulation_attack import (
    SimulationAttackRepository,
)
from phisim.security.guardrails import (
    UnsafeMetadataError,
    enforce_safe_event_metadata,
)
from phisim.simulation.timing import delivery_delay_ms

ATTACK_STATUSES = frozenset(
    {
        "DRAFT",
        "ARMED",
        "LAUNCHING",
        "DELIVERED",
        "ENGAGED",
        "COMPLETED",
        "ABANDONED",
        "EXPIRED",
        "BLOCKED",
    }
)

_TRANSITIONS: dict[str, frozenset[str]] = {
    "DRAFT": frozenset({"ARMED", "ABANDONED"}),
    "ARMED": frozenset({"LAUNCHING", "DELIVERED", "ABANDONED", "EXPIRED"}),
    "LAUNCHING": frozenset({"DELIVERED", "ABANDONED", "EXPIRED"}),
    "DELIVERED": frozenset({"ENGAGED", "ABANDONED", "EXPIRED"}),
    "ENGAGED": frozenset({"COMPLETED", "ABANDONED", "EXPIRED"}),
    "COMPLETED": frozenset(),
    "ABANDONED": frozenset(),
    "EXPIRED": frozenset(),
    "BLOCKED": frozenset(),
}

_ALLOWED_STATE_KEYS = frozenset(
    {
        "delivered_message_ids",
        "read_message_ids",
        "delivered_thread_ids",
        "read_thread_ids",
        "current_step",
        "last_action",
        "notification_seen",
        "website_viewed",
        "attachment_opened",
        "processing",
        "result_revealed",
    }
)
_ALLOWED_ACTIONS = frozenset(
    {
        "attack_armed",
        "message_delivered",
        "message_opened",
        "link_clicked",
        "website_viewed",
        "attachment_opened",
        "qr_scan_simulated",
        "mfa_prompt_displayed",
        "mfa_prompt_responded",
        "attack_completed",
        "attack_abandoned",
        "processing_started",
    }
)


class SimulationAttackError(ValueError):
    """Raised when an attack transition or state update is invalid."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _safe_state(state: dict[str, Any]) -> dict[str, Any]:
    unknown = set(state) - _ALLOWED_STATE_KEYS
    if unknown:
        raise SimulationAttackError("Unsupported attack state fields.")
    try:
        safe_state = enforce_safe_event_metadata(state)
    except UnsafeMetadataError:
        raise SimulationAttackError("Unsafe attack state.") from None

    for key in (
        "delivered_message_ids",
        "read_message_ids",
        "delivered_thread_ids",
        "read_thread_ids",
    ):
        values = safe_state.get(key, [])
        if not isinstance(values, list) or len(values) > 100:
            raise SimulationAttackError("Invalid attack delivery state.")
        if any(
            not isinstance(value, str) or not value or len(value) > 64
            for value in values
        ):
            raise SimulationAttackError("Invalid attack delivery state.")

    current_step = safe_state.get("current_step")
    if current_step is not None and (
        isinstance(current_step, bool)
        or not isinstance(current_step, int)
        or not 0 <= current_step <= 50
    ):
        raise SimulationAttackError("Invalid attack workflow step.")

    for key in (
        "notification_seen",
        "website_viewed",
        "attachment_opened",
        "processing",
        "result_revealed",
    ):
        value = safe_state.get(key)
        if value is not None and not isinstance(value, bool):
            raise SimulationAttackError("Invalid notification state.")

    last_action = safe_state.get("last_action")
    if last_action is not None and last_action not in _ALLOWED_ACTIONS:
        raise SimulationAttackError("Invalid attack action.")

    return safe_state


class SimulationAttackService:
    def __init__(self, repository: SimulationAttackRepository) -> None:
        self.repository = repository

    def create(
        self,
        *,
        run_id: str,
        operator_session_id: str,
        victim_session_id: str,
        scenario_id: str,
        channel: str,
        delay_profile: str,
        victim_token: str | None = None,
    ) -> SimulationAttack:
        now = datetime.now(UTC)
        attack = SimulationAttack(
            attack_id=uuid4().hex,
            run_id=run_id,
            operator_session_id=operator_session_id,
            victim_session_id=victim_session_id,
            victim_token=victim_token or uuid4().hex,
            scenario_id=scenario_id,
            channel=channel,
            status="ARMED",
            state=_safe_state(
                {
                    "delivered_message_ids": [],
                    "read_message_ids": [],
                    "delivered_thread_ids": [],
                    "read_thread_ids": [],
                    "last_action": "attack_armed",
                }
            ),
            delivery_due_at=now
            + timedelta(milliseconds=delivery_delay_ms(delay_profile)),
            created_at=now,
            updated_at=now,
        )
        return self.repository.create(attack)

    def get_by_attack_id(self, attack_id: str) -> SimulationAttack:
        attack = self.repository.get_by_attack_id(attack_id)
        if attack is None:
            raise SimulationAttackError("Attack not found.")
        return attack

    def get_by_token(self, token: str) -> SimulationAttack:
        attack = self.repository.get_by_victim_token(token)
        if attack is None:
            raise SimulationAttackError("Victim context not found.")
        return attack

    def get_active_by_token(self, token: str) -> SimulationAttack | None:
        return self.repository.get_active_by_victim_token(token)

    def get_any_by_token(self, token: str) -> SimulationAttack | None:
        return self.repository.get_by_victim_token(token)

    def get_by_run_id(self, run_id: str) -> SimulationAttack | None:
        return self.repository.get_by_run_id(run_id)

    def transition(
        self,
        attack: SimulationAttack,
        status: str,
        *,
        now: datetime | None = None,
    ) -> SimulationAttack:
        if status not in ATTACK_STATUSES:
            raise SimulationAttackError("Unknown attack status.")
        if status == attack.status:
            return attack
        if status not in _TRANSITIONS[attack.status]:
            raise SimulationAttackError("Invalid attack state transition.")
        current = _as_utc(now or datetime.now(UTC))
        attack.status = status
        if status == "DELIVERED":
            attack.delivered_at = current
        elif status == "ENGAGED":
            attack.engaged_at = current
        elif status == "COMPLETED":
            attack.completed_at = current
        return self.repository.save(attack)

    def update_state(
        self,
        attack: SimulationAttack,
        changes: dict[str, Any],
    ) -> SimulationAttack:
        attack.state = {**attack.state, **_safe_state(changes)}
        return self.repository.save(attack)

    def deliver_if_due(
        self,
        attack: SimulationAttack,
        *,
        now: datetime | None = None,
    ) -> bool:
        current = _as_utc(now or datetime.now(UTC))
        if current < _as_utc(attack.delivery_due_at):
            return False
        if attack.status not in {"ARMED", "LAUNCHING"}:
            return False
        self.transition(attack, "DELIVERED", now=current)
        if attack.channel == "email":
            key = "delivered_message_ids"
        elif attack.channel == "sms":
            key = "delivered_thread_ids"
        else:
            key = "current_step"
        if key == "current_step":
            self.update_state(attack, {"current_step": 1})
        else:
            values = list(attack.state.get(key, []))
            if attack.scenario_id not in values:
                values.append(attack.scenario_id)
            self.update_state(
                attack,
                {key: values, "last_action": "message_delivered"},
            )
        return True


def create_attack_service(
    database_session: OrmSession,
) -> SimulationAttackService:
    return SimulationAttackService(SimulationAttackRepository(database_session))
