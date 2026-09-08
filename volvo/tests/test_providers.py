import pytest

from volvo.ai import providers


class FakeProvider:
    name = "fake"

    def __init__(self, reply: str = "ok"):
        self.reply = reply
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.reply


def test_fake_satisfies_the_protocol():
    assert isinstance(FakeProvider(), providers.LLMProvider)


def test_available_providers_is_a_list_of_names():
    names = providers.available_providers()

    assert isinstance(names, list)
    assert all(isinstance(n, str) for n in names)


def test_nothing_is_available_without_keys_or_a_local_server(monkeypatch):
    monkeypatch.setattr(providers, "OPENAI_API_KEY", None)
    monkeypatch.setattr(providers, "GEMINI_API_KEY", None)
    monkeypatch.setattr(providers, "ollama_running", lambda *a, **k: False)

    assert providers.available_providers() == []
    assert providers.get_provider() is None


def test_ollama_is_offered_when_the_server_answers(monkeypatch):
    monkeypatch.setattr(providers, "OPENAI_API_KEY", None)
    monkeypatch.setattr(providers, "GEMINI_API_KEY", None)
    monkeypatch.setattr(providers, "ollama_running", lambda *a, **k: True)
    monkeypatch.setattr(providers, "_sdk_present", lambda module: True)

    assert providers.available_providers() == ["ollama"]


def test_ollama_provider_targets_the_local_server(monkeypatch):
    monkeypatch.setattr(providers, "ollama_running", lambda *a, **k: True)
    monkeypatch.setattr(providers, "_sdk_present", lambda module: True)

    provider = providers.get_provider("ollama")

    assert provider.name == "ollama"
    assert "11434" in provider.base_url
    assert provider.api_key  # the SDK rejects an empty key even though Ollama ignores it


def test_ollama_running_is_false_on_a_dead_port(monkeypatch):
    monkeypatch.setattr(providers, "OLLAMA_BASE_URL", "http://localhost:1/v1")

    assert providers.ollama_running(timeout=0.05) is False


def test_get_provider_rejects_an_unknown_name():
    with pytest.raises(KeyError):
        providers.get_provider("nonexistent")


def test_a_missing_sdk_is_reported_clearly(monkeypatch):
    """The ai extra is optional; a missing SDK must not surface as ImportError."""
    monkeypatch.setitem(__import__("sys").modules, "openai", None)
    provider = providers.OpenAICompatibleProvider(api_key="x", model="m")

    with pytest.raises(providers.ProviderUnavailable):
        provider.generate("hello")


def test_preference_puts_the_free_local_provider_first(monkeypatch):
    """Auto-selection must not silently bill a hosted API when Ollama is up."""
    monkeypatch.setattr(providers, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(providers, "ollama_running", lambda *a, **k: True)
    monkeypatch.setattr(providers, "_sdk_present", lambda module: True)

    assert providers.available_providers()[0] == "ollama"
    assert providers.get_provider().name == "ollama"


def test_openai_is_used_when_no_local_server_is_running(monkeypatch):
    monkeypatch.setattr(providers, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(providers, "GEMINI_API_KEY", None)
    monkeypatch.setattr(providers, "ollama_running", lambda *a, **k: False)
    monkeypatch.setattr(providers, "_sdk_present", lambda module: True)

    provider = providers.get_provider()

    assert provider.name == "openai"
    assert provider.base_url is None  # hosted OpenAI, not a local endpoint


def test_describe_covers_every_provider():
    for name in providers.PREFERENCE:
        assert providers.describe(name)


def test_providers_carry_their_model_name():
    assert providers.OpenAICompatibleProvider(api_key="x", model="gpt-4o-mini").model
    assert "gemini" in providers.GeminiProvider(api_key="x").model


def test_gemini_holds_the_client_for_the_whole_call(monkeypatch):
    """A chained genai.Client(...).models.generate_content(...) lets the client be
    garbage-collected mid-request; httpx then raises 'client has been closed'."""
    import gc

    closed = []

    class FakeModels:
        def __init__(self, owner):
            self._owner = owner

        def generate_content(self, model, contents):
            gc.collect()
            if closed:
                raise RuntimeError("Cannot send a request, as the client has been closed.")
            return type("R", (), {"text": "OK"})()

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels(self)

        def __del__(self):
            closed.append(True)

    fake_genai = type("M", (), {"Client": FakeClient})
    monkeypatch.setitem(
        __import__("sys").modules, "google.genai", fake_genai
    )
    monkeypatch.setattr(
        providers.GeminiProvider, "_client_factory", staticmethod(FakeClient), raising=False
    )

    provider = providers.GeminiProvider(api_key="x")
    provider._client_factory = FakeClient
    assert provider.generate("hi") == "OK"


def test_gemini_model_is_configurable():
    assert providers.GeminiProvider(api_key="x", model="gemini-flash-latest").model == (
        "gemini-flash-latest"
    )


def test_describe_names_the_model_that_will_actually_be_called():
    from volvo import config

    assert config.GEMINI_MODEL in providers.describe("gemini")
    assert providers.GeminiProvider(api_key="x").model in providers.describe("gemini")
    assert providers._build("openai").model in providers.describe("openai")
