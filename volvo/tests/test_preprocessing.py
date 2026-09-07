import pytest

from volvo.logs.loader import ACTIVITY, CASE
from volvo.logs.preprocessing import (
    PreprocessingError,
    drop_duplicate_events,
    filter_activities,
    filter_case_length,
    filter_time_range,
    generalize_activities,
)
from volvo.tests.test_anomalies import build


def test_filter_activities_keeps_only_the_named_ones():
    result = filter_activities(build({"1": "PQC"}), ["Accepted+In Progress"])

    assert set(result.df[ACTIVITY]) == {"Accepted+In Progress"}


def test_filter_activities_can_exclude():
    result = filter_activities(build({"1": "PQC"}), ["Queued+Awaiting Assignment"], exclude=True)

    assert "Queued+Awaiting Assignment" not in set(result.df[ACTIVITY])
    assert len(result.df) == 2


def test_filtering_does_not_mutate_the_input():
    bundle = build({"1": "PQC"})
    before = len(bundle.df)

    filter_activities(bundle, ["Accepted+In Progress"])

    assert len(bundle.df) == before


def test_filter_time_range():
    bundle = build({"1": "PQC"}, gap_hours=24)

    result = filter_time_range(bundle, start="2013-01-02")

    assert len(result.df) == 2


def test_drop_duplicate_events():
    bundle = build({"1": "PPQ"}, gap_hours=0)

    result = drop_duplicate_events(bundle)

    assert len(result.df) == 2


def test_filter_case_length():
    bundle = build({"short": "P", "long": "PQC"})

    result = filter_case_length(bundle, min_events=2)

    assert set(result.df[CASE]) == {"long"}


def test_generalize_activities_merges_labels():
    bundle = build({"1": "PQC"})
    mapping = {
        "Accepted+In Progress": "Work",
        "Queued+Awaiting Assignment": "Work",
    }

    result = generalize_activities(bundle, mapping)

    assert sorted(set(result.df[ACTIVITY])) == ["Completed+Closed", "Work"]


def test_generalize_leaves_unmapped_activities_alone():
    result = generalize_activities(build({"1": "PQC"}), {"Accepted+In Progress": "Work"})

    assert "Completed+Closed" in set(result.df[ACTIVITY])


def test_a_step_that_would_empty_the_log_raises():
    with pytest.raises(PreprocessingError):
        filter_activities(build({"1": "PQC"}), ["Nonexistent"])
