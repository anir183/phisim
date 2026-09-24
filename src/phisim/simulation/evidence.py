from typing import Any

from phisim.simulation.catalog import (
    DEFAULT_ORG_DOMAIN,
    EmailMessage,
    MfaScenario,
    Scenario,
    SmsThread,
)

_FLAG_CODES = frozenset(
    {
        "authority_impersonation",
        "domain_mismatch",
        "incident_fear",
        "invoice_fraud",
        "out_of_band",
        "personalization",
        "request_confirmation",
        "spoiled_links",
        "tech_support",
        "urgent_language",
    }
)


def _catalog_flags(indicators: tuple[str, ...]) -> dict[str, Any]:
    flags: dict[str, Any] = {
        code: True for code in indicators if code in _FLAG_CODES
    }
    if "credential_request" in indicators:
        flags["requests_credentials"] = True
    return flags


def _sender_domain(sender_address: str) -> str:
    return sender_address.rsplit("@", maxsplit=1)[-1].casefold()


def _target_path(scenario_id: str) -> str:
    return f"/scenario/{scenario_id}"


def scenario_evidence(scenario: Scenario) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "channel": scenario.channel,
        "attack_type": scenario.attack_type,
        "brand": scenario.brand,
        "content": scenario.message,
        "subject": scenario.title,
        "target_role": scenario.target_role,
        **_catalog_flags(scenario.indicators),
    }
    if "domain_mismatch" in scenario.indicators:
        evidence["display_host"] = scenario.host
        evidence["known_domain"] = DEFAULT_ORG_DOMAIN
    return evidence


def email_evidence(message: EmailMessage) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "channel": "email",
        "attack_type": message.attack_type,
        "brand": message.brand,
        "content": message.body,
        "subject": message.subject,
        "sender_label": message.sender_label,
        "sender_domain": _sender_domain(message.sender_address),
        "recipient": message.recipient,
        "display_host": message.host,
        "link_label": message.link_label,
        "target_scenario_id": message.target_scenario_id,
        "timestamp": message.timestamp,
        **_catalog_flags(message.indicators),
    }
    if message.spoofed_url:
        evidence["visible_link"] = message.spoofed_url
        evidence["actual_target"] = _target_path(message.target_scenario_id)
    return evidence


def email_link_evidence(message: EmailMessage) -> dict[str, Any]:
    evidence = email_evidence(message)
    evidence["target_url"] = _target_path(message.target_scenario_id)
    if message.spoofed_url:
        evidence["visible_link"] = message.spoofed_url
        evidence["actual_target"] = _target_path(message.target_scenario_id)
    return evidence


def email_attachment_evidence(message: EmailMessage) -> dict[str, Any]:
    evidence = email_evidence(message)
    evidence["attachment_name"] = message.attachment_name or ""
    evidence["attachment_lure"] = True
    evidence["target_url"] = _target_path(message.target_scenario_id)
    return evidence


def sms_evidence(thread: SmsThread) -> dict[str, Any]:
    return {
        "channel": "sms",
        "attack_type": thread.attack_type,
        "brand": thread.brand,
        "content": " ".join(thread.messages),
        "subject": thread.sender_label,
        "sender_label": thread.sender_label,
        "sender_number": thread.sender_number,
        "display_host": thread.host,
        "link_label": thread.link_label,
        "target_scenario_id": thread.target_scenario_id,
        "timestamp": thread.timestamp,
        **_catalog_flags(thread.indicators),
    }


def sms_link_evidence(thread: SmsThread) -> dict[str, Any]:
    evidence = sms_evidence(thread)
    evidence["target_url"] = _target_path(thread.target_scenario_id)
    return evidence


def qr_evidence(scenario: Scenario) -> dict[str, Any]:
    return scenario_evidence(scenario) | {
        "target_scenario_id": scenario.scenario_id,
    }


def mfa_evidence(
    scenario: MfaScenario,
    step: int,
    *,
    action: str | None = None,
) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "channel": "mfa",
        "attack_type": scenario.attack_type,
        "brand": scenario.brand,
        "content": scenario.message,
        "subject": scenario.title,
        "target_role": scenario.target_role,
        "step": step,
        "total_steps": scenario.prompt_count,
        **_catalog_flags(scenario.indicators),
    }
    if step > 1:
        evidence["is_unusual_context"] = True
    if action is not None:
        evidence["action"] = action
    if action == "approve" and step == scenario.prompt_count:
        evidence["mfa_fatigue"] = True
    return evidence
