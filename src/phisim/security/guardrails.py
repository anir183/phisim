from typing import Any


def enforce_safe_event_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure that sensitive information such as passwords do not enter the
    telemetry system.
    This modifies the dictionary in-place or creates a new one.
    """
    safe_metadata = metadata.copy()

    sensitive_keys = {"password", "secret", "token", "passphrase", "pin"}

    for key in list(safe_metadata.keys()):
        if key.lower() in sensitive_keys:
            # The correct behavior is to NOT retain it at all, not even hashed.
            del safe_metadata[key]

    return safe_metadata
