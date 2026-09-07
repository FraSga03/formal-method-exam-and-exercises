import pandas as pd
import pytest

from volvo.domain import CSV_SCHEMA
from volvo.logs.loader import normalize
from volvo.mining.discovery import discover


@pytest.fixture
def bundle():
    frame = pd.DataFrame(
        {
            "SR Number": ["1", "1", "1", "2", "2", "2", "3", "3"],
            "Change Date+Time": [
                "2013-01-01 10:00:00",
                "2013-01-01 11:00:00",
                "2013-01-01 12:00:00",
                "2013-01-02 10:00:00",
                "2013-01-02 11:00:00",
                "2013-01-02 12:00:00",
                "2013-01-03 10:00:00",
                "2013-01-03 11:00:00",
            ],
            "Status": [
                "Accepted", "Queued", "Completed",
                "Accepted", "Queued", "Completed",
                "Accepted", "Completed",
            ],
            "Sub Status": [
                "In Progress", "Awaiting Assignment", "Closed",
                "In Progress", "Awaiting Assignment", "Closed",
                "In Progress", "Closed",
            ],
            "Owner First Name": ["a"] * 8,
        }
    )
    return normalize(frame, CSV_SCHEMA, "status_substatus", "fixture")


@pytest.mark.parametrize("algorithm", ["alpha", "heuristics", "inductive"])
def test_discovery_produces_a_net(bundle, algorithm):
    result = discover(bundle, algorithm, render=False)

    assert result.algorithm == algorithm
    assert len(result.net.places) > 0
    assert len(result.net.transitions) > 0
    assert len(result.initial_marking) > 0


def test_statistics_are_counts(bundle):
    stats = discover(bundle, "inductive", render=False).statistics()

    assert stats["num_places"] > 0
    assert stats["num_transitions"] > 0
    assert stats["num_arcs"] > 0
    assert stats["num_silent_transitions"] >= 0


def test_params_are_recorded(bundle):
    result = discover(bundle, "inductive", render=False, noise_threshold=0.2)
    assert result.params["noise_threshold"] == 0.2


def test_heuristics_threshold_is_passed_through(bundle):
    result = discover(bundle, "heuristics", render=False, dependency_threshold=0.9)
    assert result.params["dependency_threshold"] == 0.9


def test_unknown_algorithm_raises(bundle):
    with pytest.raises(ValueError, match="Unknown algorithm"):
        discover(bundle, "genetic", render=False)


def test_rendering_writes_a_png(bundle):
    result = discover(bundle, "inductive", render=True)

    assert result.image_path is not None
    from pathlib import Path

    assert Path(result.image_path).exists()
    assert Path(result.image_path).stat().st_size > 0
