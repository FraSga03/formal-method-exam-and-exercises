import pandas as pd
import pytest

from volvo.domain import CSV_SCHEMA
from volvo.logs.loader import normalize
from volvo.mining.performance import (
    case_durations,
    duration_summary,
    variant_summary,
    variants,
    waiting_times,
)


def build_bundle() -> "object":
    """Two cases. Case 1: A(+1h) B(+3h) C. Case 2: A(+2h) C."""
    rows = [
        ("1", "2013-01-01 00:00:00", "Accepted", "In Progress"),
        ("1", "2013-01-01 01:00:00", "Queued", "Awaiting Assignment"),
        ("1", "2013-01-01 04:00:00", "Completed", "Closed"),
        ("2", "2013-01-02 00:00:00", "Accepted", "In Progress"),
        ("2", "2013-01-02 02:00:00", "Completed", "Closed"),
    ]
    frame = pd.DataFrame(
        rows, columns=["SR Number", "Change Date+Time", "Status", "Sub Status"]
    )
    frame["Owner First Name"] = "a"
    return normalize(frame, CSV_SCHEMA, "status_substatus", "fixture")


def test_waiting_time_is_the_gap_to_the_next_event():
    table = waiting_times(build_bundle())

    assert table.loc["Accepted+In Progress", "mean_hours"] == pytest.approx(1.5)
    assert table.loc["Accepted+In Progress", "count"] == 2
    assert table.loc["Queued+Awaiting Assignment", "mean_hours"] == pytest.approx(3.0)


def test_last_event_of_a_case_has_no_waiting_time():
    """Completed+Closed ends both cases, so it must not appear at all."""
    assert "Completed+Closed" not in waiting_times(build_bundle()).index


def test_waiting_times_are_sorted_by_mean_descending():
    means = waiting_times(build_bundle())["mean_hours"].tolist()
    assert means == sorted(means, reverse=True)


def test_case_durations():
    durations = case_durations(build_bundle())

    assert durations["1"] == pytest.approx(4.0)
    assert durations["2"] == pytest.approx(2.0)


def test_duration_summary():
    summary = duration_summary(build_bundle())

    assert summary["cases"] == 2
    assert summary["mean_hours"] == pytest.approx(3.0)
    assert summary["max_hours"] == pytest.approx(4.0)


def test_variants_are_ranked():
    rows = variants(build_bundle())

    assert len(rows) == 2
    assert all(row["count"] == 1 for row in rows)
    assert rows[0]["share"] == pytest.approx(0.5)


def test_variant_summary():
    summary = variant_summary(build_bundle())

    assert summary["distinct_variants"] == 2
    assert summary["cases"] == 2
    assert summary["variant_ratio"] == pytest.approx(1.0)
    assert summary["singleton_share"] == pytest.approx(1.0)


def test_a_single_event_case_contributes_no_waiting_time():
    frame = pd.DataFrame(
        [("9", "2013-01-01 00:00:00", "Accepted", "In Progress")],
        columns=["SR Number", "Change Date+Time", "Status", "Sub Status"],
    )
    frame["Owner First Name"] = "a"
    bundle = normalize(frame, CSV_SCHEMA, "status_substatus", "fixture")

    assert waiting_times(bundle).empty
    assert case_durations(bundle)["9"] == pytest.approx(0.0)
