import pandas as pd
import pytest

from volvo.analysis.anomalies import (
    long_waits,
    rare_activities,
    rare_transitions,
    summary,
    unusual_trace_lengths,
)
from volvo.domain import CSV_SCHEMA
from volvo.logs.loader import normalize

STEP = {
    "P": ("Accepted", "In Progress"),
    "Q": ("Queued", "Awaiting Assignment"),
    "C": ("Completed", "Closed"),
    "U": ("Unmatched", "Unmatched"),
}


def build(shape: dict[str, str], gap_hours: int = 1):
    """shape maps case id -> a string of STEP keys."""
    rows = []
    for case, steps in shape.items():
        for index, key in enumerate(steps):
            status, substatus = STEP[key]
            rows.append(
                {
                    "SR Number": case,
                    "Change Date+Time": pd.Timestamp("2013-01-01")
                    + pd.Timedelta(hours=index * gap_hours),
                    "Status": status,
                    "Sub Status": substatus,
                    "Owner First Name": "a",
                }
            )
    return normalize(pd.DataFrame(rows), CSV_SCHEMA, "status_substatus", "fixture")


def test_unusual_trace_lengths_flags_the_outlier():
    shape = {str(i): "PC" for i in range(10)}
    shape["long"] = "P" * 40 + "C"

    result = unusual_trace_lengths(build(shape))

    assert [c["case"] for c in result["cases"]] == ["long"]
    assert result["cases"][0]["length"] == 41


def test_no_outliers_when_all_traces_match():
    result = unusual_trace_lengths(build({str(i): "PC" for i in range(10)}))
    assert result["cases"] == []


def test_rare_activities_uses_a_percentage_threshold():
    shape = {str(i): "PC" for i in range(50)}
    shape["odd"] = "PUC"

    rare = rare_activities(build(shape), threshold_pct=1.0)

    assert [r["activity"] for r in rare] == ["Unmatched+Unmatched"]
    assert rare[0]["count"] == 1


def test_long_waits_are_reported_with_their_case():
    waits = long_waits(build({"1": "PC"}, gap_hours=48), threshold_hours=24.0)

    assert len(waits) == 1
    assert waits[0]["case"] == "1"
    assert waits[0]["activity"] == "Accepted+In Progress"
    assert waits[0]["wait_hours"] == pytest.approx(48.0)


def test_long_waits_respects_the_threshold():
    assert long_waits(build({"1": "PC"}, gap_hours=1), threshold_hours=24.0) == []


def test_long_waits_are_sorted_worst_first():
    waits = long_waits(build({"1": "PQC"}, gap_hours=48), threshold_hours=1.0)
    hours = [w["wait_hours"] for w in waits]
    assert hours == sorted(hours, reverse=True)


def test_rare_transitions_are_below_support():
    shape = {str(i): "PQC" for i in range(5)}
    shape["odd"] = "PUC"

    rare = rare_transitions(build(shape), min_support=2)
    pairs = {(r["source"], r["target"]) for r in rare}

    assert ("Accepted+In Progress", "Unmatched+Unmatched") in pairs
    assert ("Accepted+In Progress", "Queued+Awaiting Assignment") not in pairs


def test_summary_counts_every_detector():
    result = summary(build({str(i): "PC" for i in range(10)}))

    for key in ("unusual_trace_lengths", "rare_activities", "long_waits", "rare_transitions"):
        assert key in result
        assert isinstance(result[key], int)
