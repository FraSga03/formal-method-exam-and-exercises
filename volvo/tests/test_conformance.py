import pandas as pd
import pytest

from volvo.domain import CSV_SCHEMA
from volvo.logs.loader import normalize
from volvo.mining.conformance import evaluate, sample_log
from volvo.mining.discovery import discover


def build_bundle(cases: int = 3):
    rows = []
    for case in range(cases):
        for index, (status, substatus) in enumerate(
            [("Accepted", "In Progress"), ("Queued", "Awaiting Assignment"), ("Completed", "Closed")]
        ):
            rows.append(
                {
                    "SR Number": str(case),
                    "Change Date+Time": f"2013-01-{case + 1:02d} 1{index}:00:00",
                    "Status": status,
                    "Sub Status": substatus,
                    "Owner First Name": "a",
                }
            )
    return normalize(pd.DataFrame(rows), CSV_SCHEMA, "status_substatus", "fixture")


@pytest.fixture
def bundle():
    return build_bundle()


def test_perfectly_fitting_model_scores_one(bundle):
    result = discover(bundle, "inductive", render=False)
    metrics = evaluate(bundle, result)

    assert metrics.fitness == pytest.approx(1.0)


def test_all_metrics_are_in_range(bundle):
    result = discover(bundle, "inductive", render=False)
    metrics = evaluate(bundle, result)

    for name, value in metrics.as_dict().items():
        if isinstance(value, float):
            assert 0.0 <= value <= 1.0, f"{name} out of range: {value}"


def test_alignment_method_is_selectable(bundle):
    result = discover(bundle, "inductive", render=False)
    metrics = evaluate(bundle, result, method="alignment")

    assert metrics.method == "alignment"
    assert metrics.fitness == pytest.approx(1.0)


def test_unknown_method_raises(bundle):
    result = discover(bundle, "inductive", render=False)
    with pytest.raises(ValueError, match="Unknown method"):
        evaluate(bundle, result, method="magic")


def test_sampling_caps_the_case_count():
    bundle = build_bundle(cases=10)
    sampled = sample_log(bundle, max_cases=4)

    assert len(sampled) == 4


def test_sampling_is_a_noop_when_under_the_cap():
    bundle = build_bundle(cases=3)
    assert len(sample_log(bundle, max_cases=100)) == 3


def test_metrics_record_the_sample_size():
    bundle = build_bundle(cases=10)
    result = discover(bundle, "inductive", render=False)
    metrics = evaluate(bundle, result, max_cases=4)

    assert metrics.sampled_cases == 4
