from __future__ import annotations

from random import SystemRandom
from typing import Literal, cast

from fastapi import Request

DelayProfile = Literal["instant", "short", "standard"]
MAX_TRANSITION_DELAY_MS = 1800

_DELAY_MS: dict[DelayProfile, int] = {
    "instant": 0,
    "short": 180,
    "standard": 360,
}
_DELIVERY_DELAY_MS: dict[DelayProfile, int] = {
    "instant": 0,
    "short": 1200,
    "standard": 1800,
}

# Ranges are intentionally bounded by MAX_TRANSITION_DELAY_MS. The selected
# value is randomized for each rendered transition, rather than being a fixed
# per-route sleep.
_TRANSITION_RANGES: dict[str, dict[DelayProfile, tuple[int, int]]] = {
    "step": {
        "short": (140, 320),
        "standard": (220, 480),
        "instant": (0, 0),
    },
    "verification": {
        "short": (300, 650),
        "standard": (450, 900),
        "instant": (0, 0),
    },
    "link": {
        "short": (120, 280),
        "standard": (220, 450),
        "instant": (0, 0),
    },
    "mfa": {
        "short": (250, 550),
        "standard": (400, 800),
        "instant": (0, 0),
    },
    "qr": {
        "short": (280, 600),
        "standard": (420, 900),
        "instant": (0, 0),
    },
    "payment": {
        "short": (750, 1200),
        "standard": (1000, 1600),
        "instant": (0, 0),
    },
    "end": {
        "short": (220, 500),
        "standard": (350, 700),
        "instant": (0, 0),
    },
}

_RANDOM = SystemRandom()


def _valid_profile(
    value: str | None, default: DelayProfile = "short"
) -> DelayProfile:
    if value in {"instant", "short", "standard"}:
        return cast(DelayProfile, value)
    return default


def timing_for_request(
    request: Request,
    default: DelayProfile = "short",
) -> tuple[DelayProfile, int]:
    value = _valid_profile(request.query_params.get("delay"), default)
    return value, _DELAY_MS[value]


def delivery_delay_ms(profile: str) -> int:
    return _DELIVERY_DELAY_MS[_valid_profile(profile)]


def transition_delay_ms(
    kind: str = "step",
    profile: str = "short",
) -> int:
    """Return a fresh bounded transition delay for a simulation action."""
    normalized_kind = kind if kind in _TRANSITION_RANGES else "step"
    normalized_profile = _valid_profile(profile)
    lower, upper = _TRANSITION_RANGES[normalized_kind][normalized_profile]
    if upper <= 0:
        return 0
    selected = _RANDOM.randint(lower, upper)
    return min(MAX_TRANSITION_DELAY_MS, max(0, selected))
