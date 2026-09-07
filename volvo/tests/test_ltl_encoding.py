import pandas as pd
import pytest

from volvo.domain import CSV_SCHEMA
from volvo.logs.loader import normalize
from volvo.verification.ltl import Alphabet, to_symbol


def build_bundle():
    frame = pd.DataFrame(
        {
            "SR Number": ["1", "1", "1", "2", "2"],
            "Change Date+Time": [
                "2013-01-01 10:00:00",
                "2013-01-01 11:00:00",
                "2013-01-01 12:00:00",
                "2013-01-02 10:00:00",
                "2013-01-02 11:00:00",
            ],
            "Status": ["Accepted", "Queued", "Completed", "Accepted", "Queued"],
            "Sub Status": [
                "In Progress", "Awaiting Assignment", "Closed", "Wait - User", "Awaiting Assignment",
            ],
            "Owner First Name": ["a"] * 5,
        }
    )
    return normalize(frame, CSV_SCHEMA, "status_substatus", "fixture")


@pytest.mark.parametrize(
    "activity,expected",
    [
        ("Accepted+In Progress", "accepted_in_progress"),
        ("Queued+Awaiting Assignment", "queued_awaiting_assignment"),
        ("Accepted+Wait - User", "accepted_wait_user"),
        ("Completed+Closed", "completed_closed"),
        ("Unmatched+Unmatched", "unmatched_unmatched"),
    ],
)
def test_symbols_are_valid_identifiers(activity, expected):
    assert to_symbol(activity) == expected


def test_symbol_never_starts_with_a_digit():
    assert to_symbol("3rd Line").startswith("a_")


def test_alphabet_roundtrips():
    alphabet = Alphabet.from_bundle(build_bundle())
    for activity, symbol in alphabet.mapping.items():
        assert alphabet.activity(symbol) == activity
        assert alphabet.symbol(activity) == symbol


def test_alphabet_covers_every_activity():
    bundle = build_bundle()
    alphabet = Alphabet.from_bundle(bundle)
    assert len(alphabet.symbols) == bundle.summary()["unique_activities"]


def test_colliding_activities_get_distinct_symbols():
    alphabet = Alphabet(["Wait - User", "Wait  User", "wait user"])
    assert len(set(alphabet.symbols)) == 3


def test_unknown_activity_raises():
    alphabet = Alphabet.from_bundle(build_bundle())
    with pytest.raises(KeyError):
        alphabet.symbol("Nonexistent")
