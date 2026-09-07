import pandas as pd
import pytest

from volvo.domain import CSV_SCHEMA
from volvo.logs.loader import normalize
from volvo.verification.ltl import Alphabet, encode_trace, verify

EVENTS = {
    "ok": [("Accepted", "In Progress"), ("Queued", "Awaiting Assignment"), ("Completed", "Closed")],
    "unresolved": [("Accepted", "In Progress"), ("Queued", "Awaiting Assignment")],
}


def build_bundle(shape: dict[str, str]):
    """shape maps case id -> a key of EVENTS."""
    rows = []
    for case, kind in shape.items():
        for index, (status, substatus) in enumerate(EVENTS[kind]):
            rows.append(
                {
                    "SR Number": case,
                    "Change Date+Time": f"2013-01-01 1{index}:00:00",
                    "Status": status,
                    "Sub Status": substatus,
                    "Owner First Name": "a",
                }
            )
    return normalize(pd.DataFrame(rows), CSV_SCHEMA, "status_substatus", "fixture")


def test_encode_trace_marks_exactly_one_proposition_per_event():
    alphabet = Alphabet(["Accepted+In Progress", "Completed+Closed"])
    trace = encode_trace(["Accepted+In Progress", "Completed+Closed"], alphabet)

    assert len(trace) == 2
    assert trace[0] == {"accepted_in_progress": True, "completed_closed": False}
    assert trace[1] == {"accepted_in_progress": False, "completed_closed": True}


def test_response_property_holds_on_a_resolved_case():
    bundle = build_bundle({"1": "ok"})
    result = verify(bundle, "G(accepted_in_progress -> F(completed_closed))")

    assert result.satisfied == 1
    assert result.violated == 0
    assert result.ratio == pytest.approx(1.0)


def test_response_property_fails_on_an_unresolved_case():
    bundle = build_bundle({"1": "unresolved"})
    result = verify(bundle, "G(accepted_in_progress -> F(completed_closed))")

    assert result.satisfied == 0
    assert result.violated == 1


def test_counterexamples_name_the_offending_cases():
    bundle = build_bundle({"1": "ok", "2": "unresolved"})
    result = verify(bundle, "G(accepted_in_progress -> F(completed_closed))")

    assert result.ratio == pytest.approx(0.5)
    assert [c["case"] for c in result.counterexamples] == ["2"]
    assert result.counterexamples[0]["trace"][0] == "Accepted+In Progress"


def test_counterexamples_are_capped():
    bundle = build_bundle({str(i): "unresolved" for i in range(20)})
    result = verify(
        bundle, "G(accepted_in_progress -> F(completed_closed))", max_counterexamples=3
    )

    assert result.violated == 20
    assert len(result.counterexamples) == 3


def test_absence_property():
    bundle = build_bundle({"1": "ok"})
    assert verify(bundle, "G(!unmatched_unmatched)").ratio == pytest.approx(1.0)


def test_precedence_property():
    bundle = build_bundle({"1": "ok"})
    result = verify(bundle, "(!completed_closed) U queued_awaiting_assignment")

    assert result.satisfied == 1


def test_next_at_the_end_of_a_finite_trace_is_false():
    """LTLf semantics: X has no successor at the last position."""
    bundle = build_bundle({"1": "ok"})
    result = verify(bundle, "F(completed_closed & X(completed_closed))")

    assert result.satisfied == 0


def test_malformed_formula_reports_an_error_rather_than_raising():
    bundle = build_bundle({"1": "ok"})
    result = verify(bundle, "G(((")

    assert result.error is not None
    assert result.total == 0


def test_unknown_proposition_reports_an_error():
    bundle = build_bundle({"1": "ok"})
    result = verify(bundle, "G(no_such_activity)")

    assert result.error is not None
    assert "no_such_activity" in result.error
