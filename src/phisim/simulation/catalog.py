from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_CATALOG_CANDIDATES = (
    Path(__file__).resolve().parents[2] / "scenarios" / "catalog.json",
    Path(__file__).resolve().parents[3] / "scenarios" / "catalog.json",
)
CATALOG_PATH = next(
    (path for path in _CATALOG_CANDIDATES if path.is_file()),
    _CATALOG_CANDIDATES[0],
)
DEFAULT_ORG_DOMAIN = "northstar.example"
KNOWN_ORG_DOMAINS = frozenset(
    {
        "northstar.example",
        "amazaun.example",
        "cloudbox.example",
        "paymate.example",
        "gemail.example",
    }
)


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    attack_type: str
    channel: str
    brand: str
    organization: str
    host: str
    title: str
    greeting: str
    message: str
    reminder: str
    indicators: tuple[str, ...]
    target_role: str = "trainee"
    workflow: tuple[str, ...] = ("landing", "outcome")
    delay_profile: str = "standard"
    target_scenario_id: str | None = None


@dataclass(frozen=True)
class EmailMessage:
    message_id: str
    attack_type: str
    brand: str
    sender_label: str
    sender_address: str
    recipient: str
    subject: str
    body: str
    link_label: str
    host: str
    organization: str
    reminder: str
    target_scenario_id: str
    timestamp: str
    folder: str
    unread: bool
    preview: str
    indicators: tuple[str, ...]
    target_role: str = "student"
    spoofed_url: str | None = None
    attachment_name: str | None = None
    attachment_preview: str | None = None


@dataclass(frozen=True)
class SmsThread:
    thread_id: str
    attack_type: str
    brand: str
    organization: str
    sender_label: str
    sender_number: str
    messages: tuple[str, ...]
    link_label: str
    host: str
    reminder: str
    target_scenario_id: str
    timestamp: str
    unread: int
    typing_delay_ms: int
    indicators: tuple[str, ...]
    target_role: str = "student"
    spoofed_url: str | None = None


@dataclass(frozen=True)
class MfaScenario:
    scenario_id: str
    attack_type: str
    channel: str
    brand: str
    organization: str
    host: str
    title: str
    service: str
    prompt_count: int
    message: str
    reminder: str
    indicators: tuple[str, ...]
    target_role: str = "trainee"
    workflow: tuple[str, ...] = ("notification", "prompt", "outcome")
    delay_profile: str = "short"


@dataclass(frozen=True)
class BaselineEmail:
    message_id: str
    sender_label: str
    sender_address: str
    subject: str
    preview: str
    body: str
    timestamp: str
    folder: str = "Inbox"
    unread: bool = False


@dataclass(frozen=True)
class BaselineSms:
    thread_id: str
    sender_label: str
    sender_number: str
    messages: tuple[str, ...]
    timestamp: str
    unread: int = 0


@dataclass(frozen=True)
class CatalogSummary:
    scenario_id: str
    attack_type: str
    channel: str
    brand: str
    title: str
    description: str
    target_role: str
    indicators: tuple[str, ...]
    delay_profile: str


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, Any]:
    try:
        raw = CATALOG_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Scenario catalog is unavailable at {CATALOG_PATH}."
        ) from exc

    data: dict[str, Any] = json.loads(raw)
    _validate_catalog(data)
    return data


def _validate_catalog(data: dict[str, Any]) -> None:
    required_sections = (
        "website",
        "email",
        "sms",
        "mfa",
        "baseline_email",
        "baseline_sms",
    )
    missing = [name for name in required_sections if name not in data]
    if missing:
        raise ValueError(f"Scenario catalog is missing sections: {missing}")

    identifiers: set[str] = set()
    catalog_sections = ("website", "email", "sms", "mfa")
    website_ids = {str(item["scenario_id"]) for item in data["website"]}
    for section in catalog_sections:
        for item in data[section]:
            identifier = str(
                item.get(
                    "scenario_id",
                    item.get("message_id", item.get("thread_id", "")),
                )
            )
            if not identifier:
                raise ValueError(
                    f"Catalog {section} contains an empty identifier"
                )
            if identifier in identifiers:
                raise ValueError(f"Duplicate catalog identifier: {identifier}")
            identifiers.add(identifier)
            if not str(item.get("attack_type", "")).strip():
                raise ValueError(
                    f"Catalog item {identifier} has no attack_type"
                )
            if not str(item.get("indicators", [])):
                raise ValueError(f"Catalog item {identifier} has no indicators")

    for item in data["email"] + data["sms"]:
        target_id = str(item["target_scenario_id"])
        if target_id not in website_ids:
            raise ValueError(
                f"Catalog item {item.get('message_id', item.get('thread_id'))} "
                f"targets unknown website scenario {target_id}"
            )

    for item in data["website"]:
        target_id = item.get("target_scenario_id")
        if target_id is not None and str(target_id) not in website_ids:
            raise ValueError(
                f"Catalog item {item['scenario_id']} targets unknown scenario "
                f"{target_id}"
            )
        host = str(item.get("host", ""))
        if host and not host.endswith((".example", ".test", ".invalid")):
            raise ValueError(
                f"Catalog host is not reserved fictional space: {host}"
            )

    for item in data["mfa"]:
        host = str(item.get("host", ""))
        if host and not host.endswith((".example", ".test", ".invalid")):
            raise ValueError(
                f"Catalog host is not reserved fictional space: {host}"
            )

    for section, identifier_key in (
        ("baseline_email", "message_id"),
        ("baseline_sms", "thread_id"),
    ):
        for item in data[section]:
            identifier = str(item.get(identifier_key, ""))
            if not identifier or identifier in identifiers:
                raise ValueError(
                    f"Invalid or duplicate baseline identifier: {identifier}"
                )
            identifiers.add(identifier)


def _indicators(item: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(value) for value in item.get("indicators", []))


def _workflow(
    item: dict[str, Any], default: tuple[str, ...]
) -> tuple[str, ...]:
    return tuple(str(value) for value in item.get("workflow", default))


def _website_scenarios(data: dict[str, Any]) -> tuple[Scenario, ...]:
    return tuple(
        Scenario(
            scenario_id=str(item["scenario_id"]),
            attack_type=str(item["attack_type"]),
            channel=str(item["channel"]),
            brand=str(item["brand"]),
            organization=str(item["organization"]),
            host=str(item["host"]),
            title=str(item["title"]),
            greeting=str(item["greeting"]),
            message=str(item["message"]),
            reminder=str(item["reminder"]),
            indicators=_indicators(item),
            target_role=str(item.get("target_role", "trainee")),
            workflow=_workflow(item, ("landing", "outcome")),
            delay_profile=str(item.get("delay_profile", "standard")),
            target_scenario_id=(
                str(item["target_scenario_id"])
                if item.get("target_scenario_id")
                else None
            ),
        )
        for item in data["website"]
    )


def _email_messages(data: dict[str, Any]) -> tuple[EmailMessage, ...]:
    return tuple(
        EmailMessage(
            message_id=str(item["message_id"]),
            attack_type=str(item["attack_type"]),
            brand=str(item["brand"]),
            sender_label=str(item["sender_label"]),
            sender_address=str(item["sender_address"]),
            recipient=str(item["recipient"]),
            subject=str(item["subject"]),
            body=str(item["body"]),
            link_label=str(item["link_label"]),
            host=str(item["host"]),
            organization=str(item["organization"]),
            reminder=str(item["reminder"]),
            target_scenario_id=str(item["target_scenario_id"]),
            timestamp=str(item["timestamp"]),
            folder=str(item.get("folder", "Inbox")),
            unread=bool(item.get("unread", True)),
            preview=str(item.get("preview", item["subject"])),
            indicators=_indicators(item),
            target_role=str(item.get("target_role", "student")),
            spoofed_url=(
                str(item["spoofed_url"]) if item.get("spoofed_url") else None
            ),
            attachment_name=(
                str(item["attachment_name"])
                if item.get("attachment_name")
                else None
            ),
            attachment_preview=(
                str(item["attachment_preview"])
                if item.get("attachment_preview")
                else None
            ),
        )
        for item in data["email"]
    )


def _sms_threads(data: dict[str, Any]) -> tuple[SmsThread, ...]:
    return tuple(
        SmsThread(
            thread_id=str(item["thread_id"]),
            attack_type=str(item["attack_type"]),
            brand=str(item["brand"]),
            organization=str(item["organization"]),
            sender_label=str(item["sender_label"]),
            sender_number=str(item["sender_number"]),
            messages=tuple(str(value) for value in item["messages"]),
            link_label=str(item["link_label"]),
            host=str(item["host"]),
            reminder=str(item["reminder"]),
            target_scenario_id=str(item["target_scenario_id"]),
            timestamp=str(item["timestamp"]),
            unread=int(item.get("unread", 0)),
            typing_delay_ms=int(item.get("typing_delay_ms", 0)),
            indicators=_indicators(item),
            target_role=str(item.get("target_role", "student")),
            spoofed_url=(
                str(item["spoofed_url"]) if item.get("spoofed_url") else None
            ),
        )
        for item in data["sms"]
    )


def _baseline_emails(data: dict[str, Any]) -> tuple[BaselineEmail, ...]:
    return tuple(
        BaselineEmail(
            message_id=str(item["message_id"]),
            sender_label=str(item["sender_label"]),
            sender_address=str(item["sender_address"]),
            subject=str(item["subject"]),
            preview=str(item["preview"]),
            body=str(item["body"]),
            timestamp=str(item["timestamp"]),
            folder=str(item.get("folder", "Inbox")),
            unread=bool(item.get("unread", False)),
        )
        for item in data["baseline_email"]
    )


def _baseline_sms(data: dict[str, Any]) -> tuple[BaselineSms, ...]:
    return tuple(
        BaselineSms(
            thread_id=str(item["thread_id"]),
            sender_label=str(item["sender_label"]),
            sender_number=str(item["sender_number"]),
            messages=tuple(str(value) for value in item["messages"]),
            timestamp=str(item["timestamp"]),
            unread=int(item.get("unread", 0)),
        )
        for item in data["baseline_sms"]
    )


def _mfa_scenarios(data: dict[str, Any]) -> tuple[MfaScenario, ...]:
    return tuple(
        MfaScenario(
            scenario_id=str(item["scenario_id"]),
            attack_type=str(item["attack_type"]),
            channel=str(item["channel"]),
            brand=str(item["brand"]),
            organization=str(item["organization"]),
            host=str(item["host"]),
            title=str(item["title"]),
            service=str(item["service"]),
            prompt_count=int(item["prompt_count"]),
            message=str(item["message"]),
            reminder=str(item["reminder"]),
            indicators=_indicators(item),
            target_role=str(item.get("target_role", "trainee")),
            workflow=_workflow(
                item,
                ("notification", "prompt", "outcome"),
            ),
            delay_profile=str(item.get("delay_profile", "short")),
        )
        for item in data["mfa"]
    )


_CATALOG = _load_catalog()
SCENARIOS: tuple[Scenario, ...] = _website_scenarios(_CATALOG)
EMAIL_MESSAGES: tuple[EmailMessage, ...] = _email_messages(_CATALOG)
SMS_THREADS: tuple[SmsThread, ...] = _sms_threads(_CATALOG)
MFA_SCENARIOS: tuple[MfaScenario, ...] = _mfa_scenarios(_CATALOG)
BASELINE_EMAILS: tuple[BaselineEmail, ...] = _baseline_emails(_CATALOG)
BASELINE_SMS: tuple[BaselineSms, ...] = _baseline_sms(_CATALOG)

INDICATOR_INFO: dict[str, str] = {
    "credential_request": "It directly asked for usernames or passwords.",
    "urgent_language": "It applied a deadline or threat to rush the decision.",
    "domain_mismatch": (
        "The displayed identity did not match the expected fictional domain."
    ),
    "authority_impersonation": (
        "It pretended to be a trusted person or service."
    ),
    "personalization": (
        "It used contextual details to appear tailored to the recipient."
    ),
    "spoiled_links": (
        "The visible link identity differed from the local destination."
    ),
    "invoice_fraud": "It referenced an invoice or payment request.",
    "attachment_lure": "It used an attachment to encourage a follow-up action.",
    "request_confirmation": (
        "It asked the recipient to confirm account or login details."
    ),
    "mfa_fatigue": "It repeatedly asked the recipient to approve a sign-in.",
    "incident_fear": "It claimed a security incident to create pressure.",
    "tech_support": "It impersonated a fictional support or service team.",
    "out_of_band": "It moved the interaction to an unexpected channel.",
}


def get_scenario(scenario_id: str) -> Scenario | None:
    return next(
        (
            scenario
            for scenario in SCENARIOS
            if scenario.scenario_id == scenario_id
        ),
        None,
    )


def get_email_message(message_id: str) -> EmailMessage | None:
    return next(
        (
            message
            for message in EMAIL_MESSAGES
            if message.message_id == message_id
        ),
        None,
    )


def get_sms_thread(thread_id: str) -> SmsThread | None:
    return next(
        (thread for thread in SMS_THREADS if thread.thread_id == thread_id),
        None,
    )


def get_mfa_scenario(scenario_id: str) -> MfaScenario | None:
    return next(
        (
            scenario
            for scenario in MFA_SCENARIOS
            if scenario.scenario_id == scenario_id
        ),
        None,
    )


def get_baseline_email(message_id: str) -> BaselineEmail | None:
    return next(
        (
            message
            for message in BASELINE_EMAILS
            if message.message_id == message_id
        ),
        None,
    )


def get_baseline_sms(thread_id: str) -> BaselineSms | None:
    return next(
        (thread for thread in BASELINE_SMS if thread.thread_id == thread_id),
        None,
    )


def all_scenario_records() -> tuple[
    Scenario | EmailMessage | SmsThread | MfaScenario,
    ...,
]:
    return (*SCENARIOS, *EMAIL_MESSAGES, *SMS_THREADS, *MFA_SCENARIOS)


def catalog_summaries() -> tuple[CatalogSummary, ...]:
    summaries: list[CatalogSummary] = []
    for scenario in SCENARIOS:
        summaries.append(
            CatalogSummary(
                scenario_id=scenario.scenario_id,
                attack_type=scenario.attack_type,
                channel=scenario.channel,
                brand=scenario.brand,
                title=scenario.title,
                description=scenario.message,
                target_role=scenario.target_role,
                indicators=scenario.indicators,
                delay_profile=scenario.delay_profile,
            )
        )
    for message in EMAIL_MESSAGES:
        summaries.append(
            CatalogSummary(
                scenario_id=message.message_id,
                attack_type=message.attack_type,
                channel="email",
                brand=message.brand,
                title=message.subject,
                description=message.preview,
                target_role=message.target_role,
                indicators=message.indicators,
                delay_profile="standard",
            )
        )
    for thread in SMS_THREADS:
        summaries.append(
            CatalogSummary(
                scenario_id=thread.thread_id,
                attack_type=thread.attack_type,
                channel="sms",
                brand=thread.brand,
                title=thread.sender_label,
                description=thread.messages[0],
                target_role=thread.target_role,
                indicators=thread.indicators,
                delay_profile="short",
            )
        )
    for scenario in MFA_SCENARIOS:
        summaries.append(
            CatalogSummary(
                scenario_id=scenario.scenario_id,
                attack_type=scenario.attack_type,
                channel="mfa",
                brand=scenario.brand,
                title=scenario.title,
                description=scenario.message,
                target_role=scenario.target_role,
                indicators=scenario.indicators,
                delay_profile=scenario.delay_profile,
            )
        )
    return tuple(summaries)


def attack_types() -> tuple[str, ...]:
    return tuple(
        sorted({summary.attack_type for summary in catalog_summaries()})
    )


def known_domain(host: str) -> bool:
    normalized = host.casefold().rstrip(".")
    return normalized in KNOWN_ORG_DOMAINS or normalized.endswith(
        (".example", ".test", ".invalid")
    )
