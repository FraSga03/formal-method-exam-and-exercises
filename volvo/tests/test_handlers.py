import pandas as pd
import plotly.graph_objects as go
import pytest

from volvo.ui import charts, handlers
from volvo.tests.test_anomalies import build


def test_require_bundle_flags_a_missing_log():
    assert handlers.require_bundle(None).startswith("**Error:**")


def test_require_bundle_passes_a_loaded_log():
    assert handlers.require_bundle(build({"1": "PC"})) is None


def test_available_logs_lists_filenames():
    names = handlers.available_logs()
    assert isinstance(names, list)
    assert all(isinstance(n, str) for n in names)


def test_load_log_rejects_an_unknown_name():
    state, summary, table, figure = handlers.load_log("nope.xes.gz", "status_substatus")

    assert state is None
    assert summary.startswith("**Error:**")
    assert isinstance(figure, go.Figure)


@pytest.mark.parametrize(
    "builder",
    [
        charts.activity_frequency,
        charts.waiting_time_bar,
        charts.duration_histogram,
        charts.transition_heatmap,
    ],
)
def test_every_chart_returns_a_figure(builder):
    assert isinstance(builder(build({"1": "PQC", "2": "PC"})), go.Figure)


def test_charts_survive_a_single_event_log():
    """A one-event case has no waiting time and no transitions."""
    bundle = build({"1": "P"})

    assert isinstance(charts.waiting_time_bar(bundle), go.Figure)
    assert isinstance(charts.transition_heatmap(bundle), go.Figure)


def test_handlers_refuse_a_missing_log():
    assert handlers.run_discovery(None, "inductive", 0.5)[1] == handlers.NO_LOG
    assert handlers.run_conformance(None, "inductive", "token", 100)[0] == handlers.NO_LOG
    assert handlers.run_ltl(None, "G(a)", 10)[0] == handlers.NO_LOG
    assert handlers.run_analytics(None)[0] == handlers.NO_LOG


def test_run_discovery_returns_an_image_and_a_structure_table():
    image, text, table = handlers.run_discovery(build({"1": "PQC", "2": "PC"}), "inductive", 0.0)

    assert image is not None
    assert "inductive" in text
    assert "num_places" in table.columns.tolist() or "metric" in table.columns.tolist()


def test_run_conformance_reports_four_metrics():
    text, table = handlers.run_conformance(build({"1": "PQC", "2": "PC"}), "inductive", "token", 100)

    assert not table.empty
    joined = " ".join(str(v) for v in table.to_numpy().ravel()) + text
    for metric in ("fitness", "precision", "generalization", "simplicity"):
        assert metric in joined.lower()


def test_run_ltl_reports_a_ratio():
    text, table = handlers.run_ltl(build({"1": "PC"}), "F(completed_closed)", 5)

    assert "100" in text or "1.0" in text
    assert isinstance(table, pd.DataFrame)


def test_run_ltl_reports_a_bad_formula_without_raising():
    text, table = handlers.run_ltl(build({"1": "PC"}), "G(((", 5)

    assert text.startswith("**Error:**")
    assert table.empty


def test_property_choices_match_the_library():
    from volvo.verification.patterns import PROPERTIES

    assert len(handlers.property_choices()) == len(PROPERTIES)
    assert handlers.property_formula(PROPERTIES[0].key) == PROPERTIES[0].formula


def test_run_analytics_returns_three_figures():
    text, table, *figures = handlers.run_analytics(build({"1": "PQC", "2": "PC"}))

    assert "health" in text.lower()
    assert len(figures) == 3
    assert all(isinstance(f, go.Figure) for f in figures)


def test_apply_preprocessing_filters_and_reports():
    bundle, text = handlers.apply_preprocessing(build({"short": "P", "long": "PQC"}), 2, False)

    assert bundle.summary()["unique_cases"] == 1
    assert "3 events" in text


def test_apply_preprocessing_keeps_the_log_when_a_filter_empties_it():
    original = build({"1": "PC"})

    bundle, text = handlers.apply_preprocessing(original, 50, False)

    assert bundle is original
    assert text.startswith("**Error:**")


def test_apply_preprocessing_refuses_a_missing_log():
    assert handlers.apply_preprocessing(None, 1, False) == (None, handlers.NO_LOG)


def test_provider_choices_always_offer_none():
    assert "none" in handlers.provider_choices()


def test_provider_help_is_never_empty():
    assert handlers.provider_help()


def test_generate_report_without_a_log():
    text, path = handlers.generate_report(None, "none")

    assert text == handlers.NO_LOG
    assert path is None


def test_generate_report_works_with_no_provider():
    text, path = handlers.generate_report(build({"1": "PQC", "2": "PC"}), "none")

    assert "Health" in text
    assert path is not None


def test_ask_assistant_without_a_provider_explains_itself():
    from volvo.ai.assistant import NO_PROVIDER

    assert handlers.ask_assistant(build({"1": "PC"}), "why?", "none") == NO_PROVIDER


def test_default_log_is_the_first_available():
    logs = handlers.available_logs()

    assert handlers.default_log() == (logs[0] if logs else None)


def test_chat_appends_a_user_and_assistant_turn():
    history, box = handlers.chat(build({"1": "PC"}), "hello", [], "none")

    assert box == ""
    assert [turn["role"] for turn in history] == ["user", "assistant"]
    assert history[0]["content"] == "hello"


def test_chat_keeps_earlier_turns():
    first, _ = handlers.chat(build({"1": "PC"}), "one", [], "none")
    second, _ = handlers.chat(build({"1": "PC"}), "two", first, "none")

    assert len(second) == 4
    assert second[2]["content"] == "two"


def test_chat_ignores_an_empty_message():
    history, _ = handlers.chat(build({"1": "PC"}), "   ", [], "none")

    assert history == []


def test_chat_without_a_log_still_answers_in_the_transcript():
    history, _ = handlers.chat(None, "hello", [], "none")

    assert history[1]["content"].startswith("**Error:**")


def test_suggested_questions_are_offered():
    assert len(handlers.SUGGESTED_QUESTIONS) >= 5
    assert all(q.endswith("?") for q in handlers.SUGGESTED_QUESTIONS)


def test_documented_questions_match_the_code():
    """docs/assistant-questions.md must not drift from SUGGESTED_QUESTIONS."""
    from pathlib import Path

    doc = Path(__file__).resolve().parents[2] / "docs" / "assistant-questions.md"
    text = doc.read_text(encoding="utf-8")

    for question in handlers.SUGGESTED_QUESTIONS:
        assert question in text, f"undocumented question: {question}"
