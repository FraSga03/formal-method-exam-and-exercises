import pytest

from volvo.analysis.health import health_score, insights
from volvo.tests.test_anomalies import build


def test_a_clean_log_scores_well():
    result = health_score(build({str(i): "PC" for i in range(10)}))

    assert result["components"]["completion"] == pytest.approx(1.0)
    assert result["components"]["rework"] == pytest.approx(1.0)
    assert result["components"]["standardisation"] == pytest.approx(0.9)
    assert result["grade"] in {"A", "B"}


def test_rework_lowers_the_score():
    clean = health_score(build({str(i): "PC" for i in range(10)}))["score"]
    noisy = health_score(build({str(i): "PPPPC" for i in range(10)}))["score"]

    assert noisy < clean


def test_incomplete_cases_lower_completion():
    result = health_score(build({"1": "PC", "2": "PQ"}))
    assert result["components"]["completion"] == pytest.approx(0.5)


def test_score_is_bounded():
    for shape in ({"1": "PC"}, {str(i): "PQUC" * 5 for i in range(20)}):
        result = health_score(build(shape))
        assert 0.0 <= result["score"] <= 100.0
        for value in result["components"].values():
            assert 0.0 <= value <= 1.0


def test_grade_bands():
    assert health_score(build({str(i): "PC" for i in range(10)}))["grade"] in set("ABCDF")


def test_insights_are_severity_tagged():
    for insight in insights(build({str(i): "PQUC" * 5 for i in range(20)})):
        assert insight["severity"] in {"high", "medium", "low"}
        assert insight["title"]
        assert insight["detail"]
