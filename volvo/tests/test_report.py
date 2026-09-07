import pytest

from volvo.reporting import report
from volvo.tests.test_anomalies import build
from volvo.tests.test_providers import FakeProvider


@pytest.fixture
def bundle():
    return build({str(i): "PQC" for i in range(6)} | {"odd": "PUC"})


def test_collect_gathers_every_section(bundle):
    facts = report.collect(bundle, max_cases=10)

    for key in (
        "summary", "health", "insights", "duration",
        "variants", "waiting", "anomalies", "properties", "model",
    ):
        assert key in facts


def test_render_produces_markdown_without_an_llm(bundle):
    text = report.render(report.collect(bundle, max_cases=10))

    assert text.startswith("#")
    assert "Health" in text
    assert "Waiting time" in text
    assert "Narrative" not in text


def test_render_includes_a_narrative_when_given_one(bundle):
    text = report.render(report.collect(bundle, max_cases=10), narrative="Some prose.")

    assert "Narrative" in text
    assert "Some prose." in text


def test_build_without_a_provider_still_returns_a_full_report(bundle):
    text = report.build(bundle, provider=None, max_cases=10)

    assert "Health" in text
    assert "Narrative" not in text


def test_build_with_a_provider_calls_it_once_and_embeds_the_reply(bundle):
    provider = FakeProvider(reply="Executive prose.")

    text = report.build(bundle, provider=provider, max_cases=10)

    assert len(provider.prompts) == 1
    assert "Executive prose." in text


def test_a_failing_provider_does_not_lose_the_report(bundle):
    class Broken:
        name = "broken"

        def generate(self, prompt: str) -> str:
            raise RuntimeError("api down")

    text = report.build(bundle, provider=Broken(), max_cases=10)

    assert "Health" in text
    assert "api down" in text


def test_save_writes_the_file(bundle, tmp_path):
    path = report.save("# hello", tmp_path / "r.md")

    assert path.exists()
    assert path.read_text().startswith("# hello")
