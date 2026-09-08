from main import parse_args, resolve_key


def test_api_key_defaults_to_none():
    assert parse_args([]).api_key is None


def test_api_key_is_read_from_the_command_line():
    assert parse_args(["--api-key", "sk-cli"]).api_key == "sk-cli"


def test_the_command_line_key_wins_over_the_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    assert resolve_key("sk-cli") == "sk-cli"


def test_the_environment_is_used_when_no_key_is_passed(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    assert resolve_key(None) == "sk-env"


def test_no_key_anywhere_resolves_to_none(monkeypatch):
    monkeypatch.setattr("main.load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert resolve_key(None) is None
