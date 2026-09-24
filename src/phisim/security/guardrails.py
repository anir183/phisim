from typing import Any


class UnsafeMetadataError(ValueError):
    """Raised when event metadata contains credential material."""


_FORBIDDEN_CREDENTIAL_KEYS = frozenset(
    {
        "credential",
        "credentials",
        "passwd",
        "password",
        "password_hash",
        "passwordhash",
        "pwd",
        "raw_credential",
        "raw_credentials",
        "rawcredential",
        "rawcredentials",
        "secret",
        "passphrase",
        "pin",
        "token",
        "user_name",
        "username",
    }
)


def _is_safe_field_presence(value: object) -> bool:
    return isinstance(value, dict) and all(
        isinstance(field_value, bool) for field_value in value.values()
    )


def _contains_forbidden_credential(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = (
                str(key).casefold().replace("-", "_").replace(" ", "_")
            )

            if normalized_key == "field_presence":
                if not _is_safe_field_presence(nested_value):
                    return True
                continue

            if normalized_key in _FORBIDDEN_CREDENTIAL_KEYS:
                return True

            if _contains_forbidden_credential(nested_value):
                return True

        return False

    if isinstance(value, list):
        return any(_contains_forbidden_credential(item) for item in value)

    return False


def enforce_safe_event_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Validate metadata without silently changing or echoing its contents.

    A boolean-only ``field_presence`` map is the sole credential-shaped
    exception. Any raw credential key, including nested keys, fails closed so
    callers cannot accidentally persist a secret by relying on sanitization.
    """
    if _contains_forbidden_credential(metadata):
        raise UnsafeMetadataError

    return metadata.copy()
