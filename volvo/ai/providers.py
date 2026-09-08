"""LLM providers behind one protocol.

SDKs are imported inside generate(): the `ai` extra is optional and the app must
run, and its tests pass, without it installed. Ollama, Groq and OpenRouter all
speak the OpenAI wire format, so one class covers them via base_url.
"""
import importlib.util
import socket
import sys
from typing import Protocol, runtime_checkable
from urllib.parse import urlparse

from volvo.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
)


OPENAI_MODEL = "gpt-4o-mini"


class ProviderUnavailable(Exception):
    """Raised when a provider's SDK, key or server is missing at call time."""


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def generate(self, prompt: str) -> str: ...


class OpenAICompatibleProvider:
    def __init__(self, api_key, model, base_url=None, name="openai"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.name = name

    def generate(self, prompt: str) -> str:
        try:
            from openai import OpenAI
        except Exception as exc:
            raise ProviderUnavailable(
                "openai is not installed. Run: uv sync --extra ai"
            ) from exc
        if not self.api_key:
            raise ProviderUnavailable(f"No API key configured for {self.name}.")

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content or ""


class GeminiProvider:
    name = "gemini"
    _client_factory = None  # tests substitute a fake here

    def __init__(self, api_key, model=GEMINI_MODEL):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        try:
            from google import genai
        except Exception as exc:
            raise ProviderUnavailable(
                "google-genai is not installed. Run: uv sync --extra ai"
            ) from exc
        if not self.api_key:
            raise ProviderUnavailable("GEMINI_API_KEY is not set.")

        # Bind the client: a chained Client(...).models.generate_content(...) lets
        # the client be collected mid-request, closing httpx under the call.
        client = self._client_factory or genai.Client
        client = client(api_key=self.api_key)
        response = client.models.generate_content(model=self.model, contents=prompt)
        return response.text or ""


def _sdk_present(module: str) -> bool:
    if sys.modules.get(module, False) is None:  # monkeypatched away in tests
        return False
    return importlib.util.find_spec(module) is not None


def ollama_running(timeout: float = 0.3) -> bool:
    """TCP probe only — an HTTP round trip would stall the UI when nothing listens."""
    url = urlparse(OLLAMA_BASE_URL)
    try:
        with socket.create_connection((url.hostname, url.port or 11434), timeout):
            return True
    except OSError:
        return False


def _build(name: str):
    if name == "ollama":
        return OpenAICompatibleProvider(
            api_key="ollama", model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, name="ollama"
        )
    if name == "openai":
        return OpenAICompatibleProvider(
            api_key=OPENAI_API_KEY, model=OPENAI_MODEL, name="openai"
        )
    if name == "gemini":
        return GeminiProvider(api_key=GEMINI_API_KEY)
    raise KeyError(f"Unknown provider {name!r}. Known: ['ollama', 'openai', 'gemini']")


def _usable(name: str) -> bool:
    if name == "ollama":
        return _sdk_present("openai") and ollama_running()
    if name == "openai":
        return bool(OPENAI_API_KEY) and _sdk_present("openai")
    if name == "gemini":
        return bool(GEMINI_API_KEY) and _sdk_present("google.genai")
    return False


# Local first: auto-selection must never silently spend money on a hosted API.
PREFERENCE = ("ollama", "openai", "gemini")


def available_providers() -> list[str]:
    return [name for name in PREFERENCE if _usable(name)]


def get_provider(name: str | None = None):
    if name is not None:
        provider = _build(name)  # raises KeyError on an unknown name
        return provider if _usable(name) or name == "ollama" else None
    for candidate in available_providers():
        return _build(candidate)
    return None


def describe(name: str) -> str:
    """One line for the UI, so the user knows what picking this costs."""
    return {
        "ollama": f"local {OLLAMA_MODEL}, free, first call is slow while the model loads",
        "openai": f"hosted {OPENAI_MODEL}, billed to your OpenAI account",
        "gemini": f"hosted {GEMINI_MODEL}, free tier available",
    }.get(name, name)
