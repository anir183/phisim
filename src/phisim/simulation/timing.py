from typing import Literal, cast

from fastapi import Request

DelayProfile = Literal["instant", "short", "standard"]
_DELAY_MS: dict[DelayProfile, int] = {
    "instant": 0,
    "short": 180,
    "standard": 360,
}
_DELIVERY_DELAY_MS: dict[DelayProfile, int] = {
    "instant": 0,
    "short": 1200,
    "standard": 2400,
}


def timing_for_request(
    request: Request,
    default: DelayProfile = "short",
) -> tuple[DelayProfile, int]:
    value = request.query_params.get("delay", default)
    profile = cast(DelayProfile, value)
    if profile not in _DELAY_MS:
        profile = default
    return profile, _DELAY_MS[profile]


def delivery_delay_ms(profile: str) -> int:
    if profile in _DELIVERY_DELAY_MS:
        return _DELIVERY_DELAY_MS[profile]  # type: ignore[index]
    return _DELIVERY_DELAY_MS["short"]
