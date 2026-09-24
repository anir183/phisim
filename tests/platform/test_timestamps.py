from datetime import datetime, timedelta, timezone

from pydantic import BaseModel

from phisim.utils.datetime import UtcDateTime, serialize_utc_datetime


class TimestampPayload(BaseModel):
    value: UtcDateTime


def test_naive_timestamp_is_treated_as_utc() -> None:
    value = datetime(2026, 9, 24, 12, 30, 45)

    assert serialize_utc_datetime(value) == "2026-09-24T12:30:45Z"


def test_non_utc_timestamp_is_converted_to_utc() -> None:
    value = datetime(
        2026,
        9,
        24,
        17,
        45,
        tzinfo=timezone(timedelta(hours=5, minutes=30)),
    )

    assert serialize_utc_datetime(value) == "2026-09-24T12:15:00Z"


def test_pydantic_serialization_is_stable() -> None:
    payload = TimestampPayload(value=datetime(2026, 9, 24, 12, 30, 45))

    first = payload.model_dump_json()
    second = payload.model_dump_json()

    assert first == second
    assert first == '{"value":"2026-09-24T12:30:45Z"}'
