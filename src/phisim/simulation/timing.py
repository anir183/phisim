from __future__ import annotations

from random import SystemRandom
from typing import Literal, cast

from fastapi import Request

DelayProfile = Literal["instant", "short", "standard"]
MAX_TRANSITION_DELAY_MS = 2500

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
        "short": (600, 900),
        "standard": (750, 1200),
        "instant": (0, 0),
    },
    "verification": {
        "short": (700, 1200),
        "standard": (900, 1600),
        "instant": (0, 0),
    },
    "link": {
        "short": (600, 900),
        "standard": (700, 1200),
        "instant": (0, 0),
    },
    "mfa": {
        "short": (700, 1100),
        "standard": (900, 1500),
        "instant": (0, 0),
    },
    "qr": {
        "short": (700, 1200),
        "standard": (900, 1600),
        "instant": (0, 0),
    },
    "payment": {
        "short": (1400, 2200),
        "standard": (1800, 2500),
        "instant": (0, 0),
    },
    "end": {
        "short": (600, 1000),
        "standard": (750, 1200),
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
