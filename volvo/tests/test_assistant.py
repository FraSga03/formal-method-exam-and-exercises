import pytest

from volvo.ai import assistant
from volvo.tests.test_anomalies import build
from volvo.tests.test_providers import FakeProvider


@pytest.fixture
def bundle():
    return build({str(i): "PQC" for i in range(5)})


def test_context_states_the_measured_facts(bundle):
    text = assistant.context(bundle)

    assert "cases" in text.lower()
    assert "Accepted+In Progress" in text


def test_ask_without_a_provider_explains_itself(bundle):
    answer = assistant.ask(bundle, "why is it slow?", provider=None)

    assert answer == assistant.NO_PROVIDER


def test_ask_grounds_the_question_in_the_log(bundle):
    provider = FakeProvider(reply="Because of waiting.")

    answer = assistant.ask(bundle, "why is it slow?", provider=provider)

    assert answer == "Because of waiting."
    prompt = provider.prompts[0]
    assert "why is it slow?" in prompt
    assert "Accepted+In Progress" in prompt


def test_ask_without_a_loaded_log(bundle):
    answer = assistant.ask(None, "anything", provider=FakeProvider())

    assert answer.startswith("**Error:**")


def test_ask_survives_a_broken_provider(bundle):
    class Broken:
        name = "broken"

        def generate(self, prompt: str) -> str:
            raise RuntimeError("rate limited")

    answer = assistant.ask(bundle, "q", provider=Broken())

    assert answer.startswith("**Error:**")
    assert "rate limited" in answer


def test_context_labels_the_direction_of_each_component(bundle):
    """A bare 'rework: 0.48' reads as 48% rework; it is the opposite."""
    text = assistant.context(bundle)

    assert "higher is better" in text.lower()
    assert "repetition" in text.lower()


def test_history_is_included_in_the_prompt(bundle):
    provider = FakeProvider(reply="second")
    history = [
        {"role": "user", "content": "what is the health score?"},
        {"role": "assistant", "content": "74.4 out of 100."},
    ]

    assistant.ask(bundle, "why?", provider=provider, history=history)

    prompt = provider.prompts[0]
    assert "what is the health score?" in prompt
    assert "74.4 out of 100." in prompt


def test_history_is_truncated_to_recent_turns(bundle):
    provider = FakeProvider()
    history = [
        {"role": "user", "content": f"question {i}"} for i in range(40)
    ]

    assistant.ask(bundle, "now", provider=provider, history=history)

    assert "question 0" not in provider.prompts[0]
    assert "question 39" in provider.prompts[0]


def test_ask_works_without_history(bundle):
    assert assistant.ask(bundle, "q", provider=FakeProvider(reply="a")) == "a"


def test_context_marks_properties_that_do_not_hold():
    from volvo.config import DATA_DIR
    from volvo.logs.loader import load

    path = DATA_DIR / "BPI_Challenge_2013_incidents.xes.gz"
    if not path.exists():
        pytest.skip("BPI 2013 logs absent")

    text = assistant.context(load(path))

    assert "Queueing precedes work 15.5% DOES NOT HOLD" in text
    assert "Formal closure 74.0% DOES NOT HOLD" in text
    assert "Termination 99.9% DOES NOT HOLD" not in text
