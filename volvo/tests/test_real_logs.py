from pathlib import Path

import pytest

from volvo.logs.loader import load
from volvo.mining.performance import duration_summary, variant_summary, waiting_times
from volvo.verification.ltl import verify
from volvo.verification.patterns import PROPERTIES

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
INCIDENTS = RAW / "BPI_Challenge_2013_incidents.xes.gz"

pytestmark = pytest.mark.skipif(
    not INCIDENTS.exists(), reason="BPI 2013 logs absent; run scripts/fetch_data.py"
)


def test_incidents_log_shape():
    summary = load(INCIDENTS).summary()
    assert summary["unique_cases"] == 7554
    assert summary["total_events"] == 65533


def test_incidents_attributes_are_retained():
    bundle = load(INCIDENTS)
    assert len(bundle.df.columns) > 5
    assert "org:resource" in bundle.df.columns


def test_activity_mode_changes_the_alphabet():
    status_only = load(INCIDENTS, mode="status").summary()["unique_activities"]
    composite = load(INCIDENTS, mode="status_substatus").summary()["unique_activities"]
    assert status_only < composite


@pytest.fixture(scope="module")
def incidents():
    return load(INCIDENTS)


@pytest.mark.parametrize("prop", PROPERTIES, ids=lambda p: p.key)
def test_property_matches_measured_ratio(prop, incidents):
    result = verify(incidents, prop.formula, strict=False)

    assert result.error is None
    assert result.ratio == pytest.approx(prop.expected, abs=0.002)


def test_measured_waiting_times():
    table = waiting_times(load(INCIDENTS))

    assert table.loc["Accepted+Wait - User", "count"] == 4214
    assert table.loc["Accepted+Wait - User", "mean_hours"] == pytest.approx(109.97, abs=0.05)
    assert table.loc["Accepted+In Progress", "median_hours"] == pytest.approx(0.03, abs=0.01)
    assert "Accepted+Wait - Vendor" in table.index


def test_measured_case_durations():
    summary = duration_summary(load(INCIDENTS))

    assert summary["cases"] == 7554
    assert summary["median_hours"] == pytest.approx(181.18, abs=0.05)
    assert summary["p95_hours"] == pytest.approx(856.6, abs=1.0)


def test_measured_variants():
    summary = variant_summary(load(INCIDENTS))

    assert summary["distinct_variants"] == 2278
    assert summary["variant_ratio"] == pytest.approx(0.302, abs=0.001)
    assert summary["singleton_share"] == pytest.approx(0.849, abs=0.002)
    assert summary["top10_coverage"] == pytest.approx(0.481, abs=0.002)
