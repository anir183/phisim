from phisim.simulation.catalog import (
    EMAIL_MESSAGES,
    MFA_SCENARIOS,
    SCENARIOS,
    SMS_THREADS,
    all_scenario_records,
    catalog_summaries,
    get_scenario,
)


def test_catalog_uses_only_reserved_fictional_domains() -> None:
    records = all_scenario_records()
    assert records

    for record in records:
        host = getattr(record, "host", "")
        if host:
            assert host.endswith((".example", ".test", ".invalid"))
        sender = getattr(record, "sender_address", "")
        if sender and "@" in sender:
            assert sender.rsplit("@", 1)[1].endswith(".example")
        spoofed = getattr(record, "spoofed_url", None)
        if spoofed:
            assert ".example" in spoofed

    assert all(
        "techno-main" not in str(record).casefold() for record in records
    )


def test_every_link_target_resolves_to_a_website_scenario() -> None:
    for message in EMAIL_MESSAGES:
        target = get_scenario(message.target_scenario_id)
        assert target is not None
        assert target.channel == "website"
    for thread in SMS_THREADS:
        target = get_scenario(thread.target_scenario_id)
        assert target is not None
        assert target.channel == "website"


def test_catalog_summaries_cover_all_workflows() -> None:
    summaries = catalog_summaries()
    assert len(summaries) == (
        len(SCENARIOS)
        + len(EMAIL_MESSAGES)
        + len(SMS_THREADS)
        + len(MFA_SCENARIOS)
    )
    assert {summary.channel for summary in summaries} == {
        "website",
        "email",
        "sms",
        "qr",
        "mfa",
    }
    assert all(summary.indicators for summary in summaries)
