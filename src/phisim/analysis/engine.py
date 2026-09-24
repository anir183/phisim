from phisim.analysis.schemas import Indicator
from phisim.telemetry.schemas import EventResponse


def analyze_event(event: EventResponse) -> list[Indicator]:
    indicators = []

    # Analyze based on event type or metadata
    metadata = event.metadata

    # 1. Credential Request
    # Could be triggered if the event is a page that asks for login,
    # or the event itself is a credential submission
    if (
        event.event_type == "credential_submission_attempted"
        or metadata.get("requests_credentials") is True
    ):
        indicators.append(
            Indicator(
                code="credential_request",
                category="credential_harvesting",
                context="high",
                evidence="Interaction with a credential submission form.",
                explanation=(
                    "The artifact asks the user to provide their password "
                    "or sensitive credentials."
                ),
            )
        )

    content = str(metadata.get("content", "")).lower()
    subject = str(metadata.get("subject", "")).lower()
    combined_text = f"{subject} {content}"

    # 2. Urgent Language
    urgent_keywords = [
        "urgent",
        "immediate",
        "disabled",
        "within 24 hours",
        "action required",
        "deadline",
    ]
    for keyword in urgent_keywords:
        if keyword in combined_text:
            indicators.append(
                Indicator(
                    code="urgent_language",
                    category="social_engineering",
                    context="medium",
                    evidence=f"Found urgent keyword: '{keyword}'",
                    explanation=(
                        "Urgent deadlines are commonly used to pressure "
                        "users into making hasty decisions."
                    ),
                )
            )
            break

    # 3. Authority Impersonation
    authority_keywords = [
        "it department",
        "administrator",
        "support team",
        "helpdesk",
        "ceo",
        "security alert",
    ]
    for keyword in authority_keywords:
        if keyword in combined_text:
            indicators.append(
                Indicator(
                    code="authority_impersonation",
                    category="social_engineering",
                    context="medium",
                    evidence=(
                        f"Found authority impersonation keyword: '{keyword}'"
                    ),
                    explanation=(
                        "Attackers often impersonate trusted authorities "
                        "to compel compliance."
                    ),
                )
            )
            break

    # 4. Domain Mismatch
    visible_link = metadata.get("visible_link")
    actual_target = metadata.get("actual_target")
    if visible_link and actual_target and visible_link != actual_target:
        indicators.append(
            Indicator(
                code="domain_mismatch",
                category="deception",
                context="high",
                evidence=(
                    f"Visible link '{visible_link}' points to '{actual_target}'"
                ),
                explanation=(
                    "The link appears to go to one destination but actually "
                    "leads to another."
                ),
            )
        )

    return indicators
