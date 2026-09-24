import pytest

from phisim.security.guardrails import (
    UnsafeMetadataError,
    enforce_safe_event_metadata,
)


def test_password_is_rejected_without_mutating_metadata() -> None:
    metadata = {
        "page": "/login",
        "username": "user123",
        "password": "super_secret_password",
        "timestamp": 12345,
    }
    original = metadata.copy()

    with pytest.raises(UnsafeMetadataError):
        enforce_safe_event_metadata(metadata)

    assert metadata == original


def test_other_sensitive_keys_are_rejected() -> None:
    metadata = {
        "token": "abc",
        "secret": "def",
        "passphrase": "ghi",
        "pin": "1234",
        "safe_value": "yes",
    }

    with pytest.raises(UnsafeMetadataError):
        enforce_safe_event_metadata(metadata)


def test_boolean_field_presence_is_allowed() -> None:
    metadata = {
        "channel": "website",
        "field_presence": {
            "username": True,
            "password": False,
        },
    }

    assert enforce_safe_event_metadata(metadata) == metadata


def test_nested_credential_keys_are_rejected() -> None:
    with pytest.raises(UnsafeMetadataError):
        enforce_safe_event_metadata(
            {"details": [{"password_hash": "not-persisted"}]},
        )
