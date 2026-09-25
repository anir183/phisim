from phisim.simulation import timing


def test_transition_delays_are_randomized_within_public_bounds() -> None:
    kinds = {
        "step": (100, 500),
        "verification": (250, 950),
        "link": (100, 500),
        "mfa": (200, 850),
        "qr": (250, 950),
        "payment": (700, 1650),
        "end": (200, 750),
    }

    for kind, (lower, upper) in kinds.items():
        for profile in ("short", "standard"):
            values = [
                timing.transition_delay_ms(kind, profile) for _ in range(40)
            ]
            assert all(lower <= value <= upper for value in values)
            assert all(
                value <= timing.MAX_TRANSITION_DELAY_MS for value in values
            )

    assert timing.transition_delay_ms("payment", "instant") == 0
    assert timing.transition_delay_ms("unknown", "unknown") <= 500


def test_transition_delay_clamps_unexpected_random_output(
    monkeypatch,
) -> None:
    class OutOfRangeRandom:
        def randint(self, lower: int, upper: int) -> int:
            assert lower <= upper
            return 10_000

    monkeypatch.setattr(timing, "_RANDOM", OutOfRangeRandom())

    assert (
        timing.transition_delay_ms("payment", "standard")
        == timing.MAX_TRANSITION_DELAY_MS
    )


def test_delivery_profiles_respect_the_global_ceiling() -> None:
    for profile in ("instant", "short", "standard", "unknown"):
        assert 0 <= timing.delivery_delay_ms(profile) <= 1800
