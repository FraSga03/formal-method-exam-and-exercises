from volvo.mining.comparison import compare_algorithms
from volvo.tests.test_conformance import build_bundle


def test_comparison_covers_every_algorithm():
    rows = compare_algorithms(build_bundle())
    assert {row["algorithm"] for row in rows} == {"alpha", "heuristics", "inductive"}


def test_comparison_rows_carry_metrics_and_structure():
    for row in compare_algorithms(build_bundle()):
        if row["error"]:
            continue
        assert 0.0 <= row["fitness"] <= 1.0
        assert row["num_places"] > 0


def test_a_failing_algorithm_does_not_sink_the_others():
    """Alpha can produce an unsound net on odd logs; the table must still render."""
    rows = compare_algorithms(build_bundle())
    assert any(row["error"] is None for row in rows)
