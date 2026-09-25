from __future__ import annotations

import hashlib
import secrets
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.models.sandbox_capture import SandboxCapture
from phisim.infra.sqlite.repos.sandbox_capture import SandboxCaptureRepository
from phisim.utils.datetime import serialize_utc_datetime
from phisim.utils.env import settings

SANDBOX_EMAIL_SUFFIXES = ("@example.com", "@gemail.com")
SANDBOX_VALUE_PREFIXES = (
    "sandbox-",
    "training-",
    "demo-",
    "local-",
    "test-",
    "sample-",
)
SANDBOX_PAYMENT_METHODS = frozenset(
    {
        "Fictional card ending 4242",
        "Northstar invoice account",
        "Pay at local pickup",
    }
)
SANDBOX_ACTIONS = frozenset({"approve", "deny", "scan"})

_EMAIL_FIELDS = frozenset(
    {
        "username",
        "email",
        "identifier",
        "work_email",
        "billing_email",
    }
)
_SECRET_FIELDS = frozenset(
    {
        "password",
        "confirmation",
        "verification_code",
        "payment_confirmation",
    }
)
_MAX_CAPTURE_FIELDS = 12
_MAX_VALUE_LENGTH = 256
_MEMORY_TTL = timedelta(hours=2)
_MEMORY_MAX_SESSIONS = 100


class SandboxCaptureError(ValueError):
    """Base exception for the explicit synthetic-capture feature."""


class SandboxCaptureValidationError(SandboxCaptureError):
    """Raised when a submitted value is not safe for the demo capture."""


@dataclass(frozen=True)
class _MemoryCapture:
    values: dict[str, str]
    created_at: datetime


# The exact display cache is intentionally process-local. It is only populated
# after the strict validator accepts a value, and it expires independently of
# the persisted safe metadata/digests.
_MEMORY_CAPTURES: OrderedDict[str, dict[str, _MemoryCapture]] = OrderedDict()
_MEMORY_LOCK = RLock()


def sandbox_capture_enabled() -> bool:
    return bool(
        settings.sandbox_capture
        and settings.env == "development"
        and settings.host in {"127.0.0.1", "localhost", "::1"}
    )


def _normalize_value(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise SandboxCaptureValidationError("Enter a text value to continue.")
    if not value.strip():
        raise SandboxCaptureValidationError("Enter a value to continue.")
    if len(value) > _MAX_VALUE_LENGTH:
        raise SandboxCaptureValidationError(
            "Keep the value under 256 characters."
        )
    if any(ord(character) < 32 for character in value):
        raise SandboxCaptureValidationError("Use a single-line text value.")
    return value


def _is_synthetic_secret(value: str) -> bool:
    normalized = value.casefold()
    return normalized.startswith(SANDBOX_VALUE_PREFIXES)


def _validate_field(name: str, value: str) -> None:
    comparable = value.strip().casefold()
    if name == "payment_method" and value not in SANDBOX_PAYMENT_METHODS:
        raise SandboxCaptureValidationError(
            "Choose one of the fictional payment options."
        )
    if name == "action" and value not in SANDBOX_ACTIONS:
        raise SandboxCaptureValidationError("Choose a fictional demo action.")
    if (
        name in _EMAIL_FIELDS
        and "@" in comparable
        and not comparable.endswith(SANDBOX_EMAIL_SUFFIXES)
    ):
        raise SandboxCaptureValidationError(
            "Use an email ending in @example.com or @gemail.com."
        )
    if name == "password" and not _is_synthetic_secret(comparable):
        raise SandboxCaptureValidationError(
            "Use a training-only value such as sandbox-password."
        )


def validate_capture_fields(fields: Mapping[str, object]) -> dict[str, str]:
    if len(fields) > _MAX_CAPTURE_FIELDS:
        raise SandboxCaptureValidationError("Too many values were submitted.")

    validated: dict[str, str] = {}
    for name, raw_value in fields.items():
        normalized_name = str(name).strip()
        if not normalized_name or len(normalized_name) > 64:
            raise SandboxCaptureValidationError("Invalid capture field name.")
        value = _normalize_value(normalized_name, raw_value)
        _validate_field(normalized_name, value)
        validated[normalized_name] = value
    return validated


def _digest(value: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        value.encode("utf-8"),
        salt,
        180_000,
    )
    return f"pbkdf2_sha256$180000${salt.hex()}${digest.hex()}"


def _prune_memory(now: datetime) -> None:
    cutoff = now - _MEMORY_TTL
    for session_id in list(_MEMORY_CAPTURES):
        captures = _MEMORY_CAPTURES[session_id]
        for capture_id in list(captures):
            if captures[capture_id].created_at < cutoff:
                del captures[capture_id]
        if not captures:
            del _MEMORY_CAPTURES[session_id]
        else:
            _MEMORY_CAPTURES.move_to_end(session_id)
    while len(_MEMORY_CAPTURES) > _MEMORY_MAX_SESSIONS:
        _MEMORY_CAPTURES.popitem(last=False)


def _remember_values(
    session_id: str,
    capture_id: str,
    values: dict[str, str],
    created_at: datetime,
) -> None:
    with _MEMORY_LOCK:
        _prune_memory(created_at)
        captures = _MEMORY_CAPTURES.setdefault(session_id, {})
        captures[capture_id] = _MemoryCapture(
            values=dict(values),
            created_at=created_at,
        )
        _MEMORY_CAPTURES.move_to_end(session_id)
        while len(_MEMORY_CAPTURES) > _MEMORY_MAX_SESSIONS:
            _MEMORY_CAPTURES.popitem(last=False)


def _remembered_values(
    session_id: str,
    capture_id: str,
) -> dict[str, str] | None:
    with _MEMORY_LOCK:
        _prune_memory(datetime.now(UTC))
        capture = _MEMORY_CAPTURES.get(session_id, {}).get(capture_id)
        return dict(capture.values) if capture is not None else None


def record_sandbox_capture(
    database_session: OrmSession,
    *,
    session_id: str,
    scenario_id: str,
    channel: str,
    step: int | str,
    fields: Mapping[str, object],
) -> dict[str, str] | None:
    """Validate and persist a synthetic capture without putting it in events.

    Non-secret accepted values are stored as-is. Secret-like values are stored
    only as salted one-way digests; their exact values are kept in the bounded
    process-local cache so the active Reveal/Console can demonstrate them.
    """
    if not sandbox_capture_enabled():
        return None

    validated = validate_capture_fields(fields)
    if not validated:
        return None

    now = datetime.now(UTC)
    capture_id = uuid4().hex
    safe_values = {
        name: value
        for name, value in validated.items()
        if name not in _SECRET_FIELDS
    }
    secret_digests = {
        name: _digest(value)
        for name, value in validated.items()
        if name in _SECRET_FIELDS
    }
    capture = SandboxCapture(
        capture_id=capture_id,
        session_id=session_id,
        scenario_id=scenario_id,
        channel=channel,
        step=str(step),
        values=safe_values,
        secret_digests=secret_digests,
        created_at=now,
    )
    SandboxCaptureRepository(database_session).create(capture)
    _remember_values(session_id, capture_id, validated, now)
    return validated


def _field_payload(
    name: str,
    value: str | None,
    *,
    secret: bool,
) -> dict[str, str | bool | None]:
    if secret:
        return {
            "name": name,
            "value": value,
            "storage": "active-session" if value is not None else "unavailable",
            "persisted_as": "salted_digest",
        }
    return {
        "name": name,
        "value": value,
        "storage": "database",
    }


def list_sandbox_captures(
    database_session: OrmSession,
    session_id: str,
) -> list[dict[str, Any]]:
    """Return safe persisted captures plus active-session display values."""
    if not sandbox_capture_enabled():
        return []

    records = SandboxCaptureRepository(database_session).list_by_session(
        session_id
    )
    captures: list[dict[str, Any]] = []
    for record in records:
        remembered = _remembered_values(session_id, record.capture_id) or {}
        fields: list[dict[str, str | bool | None]] = []
        for name, value in record.values.items():
            fields.append(_field_payload(name, str(value), secret=False))
        for name in record.secret_digests:
            fields.append(
                _field_payload(
                    name,
                    remembered.get(name),
                    secret=True,
                )
            )
        captures.append(
            {
                "capture_id": record.capture_id,
                "scenario_id": record.scenario_id,
                "channel": record.channel,
                "step": record.step,
                "created_at": serialize_utc_datetime(record.created_at),
                "fields": fields,
            }
        )
    return captures


def clear_sandbox_capture_memory(session_id: str | None = None) -> None:
    """Clear exact display values for tests or an explicit local reset."""
    with _MEMORY_LOCK:
        if session_id is None:
            _MEMORY_CAPTURES.clear()
        else:
            _MEMORY_CAPTURES.pop(session_id, None)
