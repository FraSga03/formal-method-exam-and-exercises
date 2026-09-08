import gradio as gr

from volvo.ui.app import build


def _tab_labels(demo: gr.Blocks) -> set:
    return {
        getattr(block, "label", None)
        for block in demo.blocks.values()
        if isinstance(block, gr.Tab)
    }


def test_build_returns_blocks_without_launching():
    assert isinstance(build(), gr.Blocks)


def test_app_declares_every_tab():
    labels = _tab_labels(build())

    assert {"Data", "Preprocessing", "Discovery", "Conformance", "LTL", "Analytics"} <= labels


def test_app_declares_the_report_and_assistant_tabs():
    labels = _tab_labels(build())

    assert {"Report", "Assistant"} <= labels


def test_app_holds_session_state():
    demo = build()
    assert any(isinstance(b, gr.State) for b in demo.blocks.values())


def test_app_loads_a_log_at_startup():
    demo = build()

    triggers = {trigger for fn in demo.fns.values() for _, trigger in fn.targets}

    assert "load" in triggers


def test_every_activity_mode_is_offered():
    from typing import get_args

    from volvo.domain import ActivityMode
    from volvo.ui.app import MODES

    radios = [b for b in build().blocks.values() if isinstance(b, gr.Radio)]
    offered = {choice for radio in radios for choice, _ in radio.choices}

    assert set(MODES) == set(get_args(ActivityMode))
    assert set(get_args(ActivityMode)) <= offered
