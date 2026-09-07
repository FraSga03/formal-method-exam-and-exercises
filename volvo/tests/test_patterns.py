import pytest

from volvo.tests.test_ltl_verify import build_bundle
from volvo.verification.ltl import Alphabet, verify
from volvo.verification.patterns import (
    PROPERTIES,
    applicable,
    get_property,
    verify_all,
)


def test_every_property_has_a_unique_key():
    keys = [p.key for p in PROPERTIES]
    assert len(keys) == len(set(keys))


def test_every_property_parses_against_the_full_alphabet():
    """Guards against typos in the shipped formulas."""
    alphabet = Alphabet(
        [
            "Accepted+In Progress",
            "Accepted+Wait - User",
            "Queued+Awaiting Assignment",
            "Completed+Cancelled",
            "Completed+Closed",
            "Completed+In Call",
            "Completed+Resolved",
            "Unmatched+Unmatched",
        ]
    )
    from volvo.verification.ltl import _parse

    for prop in PROPERTIES:
        _parse(prop.formula, alphabet, strict=True)


def test_resolution_property_distinguishes_the_two_fixtures():
    prop = get_property("resolution")

    assert verify(build_bundle({"1": "ok"}), prop.formula).ratio == pytest.approx(1.0)
    assert verify(build_bundle({"1": "unresolved"}), prop.formula).ratio == pytest.approx(0.0)


def test_unknown_key_raises():
    with pytest.raises(KeyError):
        get_property("nope")


def test_applicable_keeps_properties_touching_the_logs_alphabet():
    bundle = build_bundle({"1": "ok"})
    names = {p.key for p in applicable(bundle)}

    assert "resolution" in names
    assert "no_unmatched" not in names  # mentions only an absent activity


def test_verify_all_returns_one_row_per_applicable_property():
    bundle = build_bundle({"1": "ok", "2": "unresolved"})
    rows = verify_all(bundle)

    assert len(rows) == len(applicable(bundle))
    for row in rows:
        assert row["error"] is None
        assert 0.0 <= row["ratio"] <= 1.0
