from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    channel: str
    organization: str
    host: str
    title: str
    greeting: str
    message: str
    reminder: str
    indicators: tuple[str, ...]


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        scenario_id="credential-basic-001",
        channel="website",
        organization="Techno Main Salt Lake",
        host="techno-main-sl-access.net",
        title="Mailbox Quota Exceeded Notice",
        greeting="Dear student,",
        message=(
            "Your university mailbox quota has been exceeded and will be "
            "suspended within 24 hours unless you confirm your account "
            "details on the login page."
        ),
        reminder=(
            "Simulated for security education only. Not an affiliate of any "
            "real institution. No credentials were kept."
        ),
        indicators=(
            "credential_request",
            "urgent_language",
            "domain_mismatch",
            "authority_impersonation",
        ),
    ),
)


def get_scenario(scenario_id: str) -> Scenario | None:
    for scenario in SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    return None
