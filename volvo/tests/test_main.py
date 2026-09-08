import os

import pytest

from volvo.main import apply_key_overrides, parse_args


def test_keys_default_to_none():
    args = parse_args([])
    assert args.openai_api_key is None
    assert args.gemini_api_key is None


def test_host_and_port_have_defaults():
    args = parse_args([])
    assert args.host == "127.0.0.1"
    assert args.port == 7860


def test_port_is_parsed_as_an_integer():
    assert parse_args(["--port", "8080"]).port == 8080


@pytest.mark.parametrize(
    "flag,value,variable",
    [
        ("--openai-api-key", "sk-cli", "OPENAI_API_KEY"),
        ("--gemini-api-key", "gm-cli", "GEMINI_API_KEY"),
        ("--ollama-base-url", "http://elsewhere/v1", "OLLAMA_BASE_URL"),
    ],
)
def test_a_flag_lands_in_the_environment(monkeypatch, flag, value, variable):
    monkeypatch.delenv(variable, raising=False)
    apply_key_overrides(parse_args([flag, value]))
    assert os.environ[variable] == value


def test_a_flag_overrides_what_the_environment_already_holds(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    apply_key_overrides(parse_args(["--openai-api-key", "sk-cli"]))
    assert os.environ["OPENAI_API_KEY"] == "sk-cli"


def test_an_absent_flag_leaves_the_environment_alone(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    apply_key_overrides(parse_args([]))
    assert os.environ["OPENAI_API_KEY"] == "sk-env"
