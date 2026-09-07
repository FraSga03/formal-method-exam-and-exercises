import pytest

from volvo.analysis.predictor import MarkovModel, UnknownActivityError
from volvo.tests.test_anomalies import build


def test_predicts_the_only_successor():
    model = MarkovModel.fit(build({"1": "PC", "2": "PC"}))

    top = model.predict_next("Accepted+In Progress")

    assert top[0]["activity"] == "Completed+Closed"
    assert top[0]["probability"] == pytest.approx(1.0)


def test_probabilities_reflect_frequency():
    model = MarkovModel.fit(build({"1": "PC", "2": "PC", "3": "PQ"}))

    top = {p["activity"]: p["probability"] for p in model.predict_next("Accepted+In Progress")}

    assert top["Completed+Closed"] == pytest.approx(2 / 3)
    assert top["Queued+Awaiting Assignment"] == pytest.approx(1 / 3)


def test_predictions_are_ranked_and_capped():
    model = MarkovModel.fit(build({"1": "PC", "2": "PQ", "3": "PU"}))

    top = model.predict_next("Accepted+In Progress", top_k=2)

    assert len(top) == 2
    assert top[0]["probability"] >= top[1]["probability"]


def test_a_terminal_activity_predicts_nothing():
    model = MarkovModel.fit(build({"1": "PC"}))
    assert model.predict_next("Completed+Closed") == []


def test_unknown_activity_raises():
    model = MarkovModel.fit(build({"1": "PC"}))
    with pytest.raises(UnknownActivityError):
        model.predict_next("Nonexistent")


def test_transition_matrix_rows_sum_to_one_or_zero():
    matrix = MarkovModel.fit(build({"1": "PQC", "2": "PC"})).transition_matrix()

    for _, row in matrix.iterrows():
        total = row.sum()
        assert total == pytest.approx(1.0) or total == pytest.approx(0.0)


def test_predict_sequence_stops_at_a_terminal_activity():
    model = MarkovModel.fit(build({"1": "PC"}))

    assert model.predict_sequence("Accepted+In Progress", length=5) == [
        "Accepted+In Progress",
        "Completed+Closed",
    ]


def test_predict_sequence_respects_length():
    model = MarkovModel.fit(build({"1": "PPPPPPPP"}))
    assert len(model.predict_sequence("Accepted+In Progress", length=4)) == 4
