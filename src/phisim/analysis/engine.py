from collections.abc import Mapping
from typing import Any

from phisim.analysis.schemas import Indicator
from phisim.telemetry.schemas import EventResponse


def _text(metadata: Mapping[str, Any], *keys: str) -> str:
    values: list[str] = []
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str):
            values.append(value)
    return " ".join(values).casefold()


def _is_true(metadata: Mapping[str, Any], key: str) -> bool:
    return metadata.get(key) is True


def analyze_event(event: EventResponse) -> list[Indicator]:
    """Return deterministic, explainable indicators for one safe Event."""
    metadata = event.metadata
    combined_text = _text(metadata, "subject", "content")
    indicators: list[Indicator] = []
    seen_codes: set[str] = set()

    def add(
        code: str,
        category: str,
        context: str,
        evidence: str,
        explanation: str,
    ) -> None:
        if code in seen_codes:
            return
        seen_codes.add(code)
        indicators.append(
            Indicator(
                code=code,
                category=category,
                context=context,
                evidence=evidence,
                explanation=explanation,
            )
        )

    if event.event_type == "credential_submission_attempted" or _is_true(
        metadata, "requests_credentials"
    ):
        add(
            "credential_request",
            "credential_harvesting",
            "high",
            "Interaction with a credential submission form.",
            "The artifact asks the user to provide their password or "
            "sensitive credentials.",
        )

    urgent_keywords = (
        "urgent",
        "immediate",
        "disabled",
        "within 24 hours",
        "action required",
        "deadline",
    )
    for keyword in urgent_keywords:
        if keyword in combined_text:
            add(
                "urgent_language",
                "social_engineering",
                "medium",
                f"Found urgent keyword: '{keyword}'",
                "Urgent deadlines are commonly used to pressure users into "
                "making hasty decisions.",
            )
            break

    authority_keywords = (
        "it department",
        "administrator",
        "support team",
        "helpdesk",
        "ceo",
        "security alert",
    )
    for keyword in authority_keywords:
        if keyword in combined_text:
            add(
                "authority_impersonation",
                "social_engineering",
                "medium",
                f"Found authority impersonation keyword: '{keyword}'",
                "Attackers often impersonate trusted authorities to compel "
                "compliance.",
            )
            break

    visible_link = metadata.get("visible_link")
    actual_target = metadata.get("actual_target")
    if visible_link and actual_target and visible_link != actual_target:
        add(
            "domain_mismatch",
            "deception",
            "high",
            f"Visible link '{visible_link}' points to '{actual_target}'",
            "The link appears to go to one destination but actually leads "
            "to another.",
        )
    elif _is_true(metadata, "domain_mismatch"):
        add(
            "domain_mismatch",
            "deception",
            "high",
            "The displayed sender or link domain differs from the known "
            "organization domain.",
            "A mismatched domain is a common sign of impersonation.",
        )

    link_url = _text(metadata, "link_url")
    if link_url and "login" not in link_url and "reset" in link_url:
        add(
            "unexpected_link",
            "deception",
            "medium",
            f"Found unexpected link pattern: '{link_url}'",
            "Links that are unexpected or use generic reset patterns are "
            "often suspicious.",
        )

    attachment_name = _text(metadata, "attachment_name")
    suspicious_extensions = (".exe", ".scr", ".js", ".vbs", ".bat", ".iso")
    for extension in suspicious_extensions:
        if attachment_name.endswith(extension):
            add(
                "suspicious_attachment",
                "malware_delivery",
                "high",
                f"Attachment '{attachment_name}' has suspicious extension "
                f"'{extension}'",
                "Executable or script attachments are commonly used to "
                "deliver malware.",
            )
            break

    if event.event_type == "mfa_prompt_displayed" and _is_true(
        metadata, "is_unusual_context"
    ):
        add(
            "unusual_mfa_request",
            "credential_harvesting",
            "high",
            "MFA prompt displayed in an unusual context or location.",
            "Attackers use unexpected MFA prompts to bypass two-factor "
            "authentication (MFA fatigue).",
        )

    # Simulation catalog flags keep these rules deterministic without
    # inferring intent from arbitrary user-provided prose.
    flag_rules = (
        (
            "authority_impersonation",
            "social_engineering",
            "medium",
            "The artifact presents itself as an authority or trusted role.",
            "Attackers often impersonate trusted authorities to compel "
            "compliance.",
        ),
        (
            "urgent_language",
            "social_engineering",
            "medium",
            "The artifact uses urgency or a deadline.",
            "Urgent deadlines are commonly used to pressure users into making "
            "hasty decisions.",
        ),
        (
            "personalization",
            "social_engineering",
            "medium",
            "The artifact uses personal or contextual details.",
            "Personalization can make a fraudulent message appear tailored "
            "to the recipient.",
        ),
        (
            "incident_fear",
            "social_engineering",
            "medium",
            "The artifact claims a security incident or unusual activity.",
            "Claims of an incident can create pressure to act immediately.",
        ),
        (
            "tech_support",
            "authority_impersonation",
            "medium",
            "The artifact presents itself as a technical support or service "
            "team.",
            "Support-themed impersonation is a common phishing tactic.",
        ),
        (
            "invoice_fraud",
            "financial_fraud",
            "high",
            "The artifact references an invoice, payment, or financial "
            "request.",
            "Unexpected financial requests can be used to steal funds or "
            "credentials.",
        ),
        (
            "request_confirmation",
            "credential_harvesting",
            "high",
            "The artifact asks the recipient to confirm account or login "
            "details.",
            "Requests to confirm authentication details can be a pretext for "
            "credential harvesting.",
        ),
        (
            "out_of_band",
            "social_engineering",
            "medium",
            "The interaction moved the recipient to an unexpected channel.",
            "Moving a conversation outside its normal channel can reduce "
            "normal verification safeguards.",
        ),
        (
            "spoiled_links",
            "deception",
            "high",
            "The visible link text does not match its local simulation "
            "destination.",
            "Deceptive link destinations can hide the true target from a "
            "recipient.",
        ),
        (
            "attachment_lure",
            "delivery",
            "medium",
            "An attachment was used to encourage a follow-up interaction.",
            "Attachments can make a fraudulent request appear more official "
            "or urgent.",
        ),
        (
            "mfa_fatigue",
            "credential_harvesting",
            "high",
            "Multiple MFA approval prompts were requested in one session.",
            "Repeated approval prompts can pressure a recipient into "
            "approving an attacker request.",
        ),
    )
    for code, category, context, evidence, explanation in flag_rules:
        if _is_true(metadata, code):
            add(code, category, context, evidence, explanation)

    if event.event_type == "attachment_opened":
        add(
            "attachment_lure",
            "delivery",
            "medium",
            "A simulated attachment was opened.",
            "An attachment can be used to make a fraudulent request appear "
            "more official or urgent.",
        )

    if event.event_type == "mfa_prompt_responded" and _is_true(
        metadata, "mfa_fatigue"
    ):
        add(
            "mfa_fatigue",
            "credential_harvesting",
            "high",
            "The final MFA prompt completed a repeated approval sequence.",
            "Repeated approval prompts can pressure a recipient into "
            "approving an attacker request.",
        )

    return indicators
