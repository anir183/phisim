from phisim.security.guardrails import enforce_safe_event_metadata


def test_password_stripped_from_metadata():
    metadata = {
        "page": "/login",
        "username": "user123",
        "password": "super_secret_password",
        "timestamp": 12345,
    }

    safe_metadata = enforce_safe_event_metadata(metadata)

    assert "page" in safe_metadata
    assert "username" in safe_metadata
    assert "timestamp" in safe_metadata
    assert "password" not in safe_metadata


def test_other_sensitive_keys_stripped():
    metadata = {
        "token": "abc",
        "secret": "def",
        "passphrase": "ghi",
        "pin": "1234",
        "safe_value": "yes",
    }

    safe_metadata = enforce_safe_event_metadata(metadata)

    assert "safe_value" in safe_metadata
    assert "token" not in safe_metadata
    assert "secret" not in safe_metadata
    assert "passphrase" not in safe_metadata
    assert "pin" not in safe_metadata
