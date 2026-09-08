"""Entry point: uv run python -m volvo.main"""
import argparse
import os

KEY_FLAGS = (
    ("openai_api_key", "OPENAI_API_KEY"),
    ("gemini_api_key", "GEMINI_API_KEY"),
    ("ollama_base_url", "OLLAMA_BASE_URL"),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="volvo.main", description="Process mining dashboard for the BPI 2013 logs."
    )
    parser.add_argument("--openai-api-key", default=None, help="overrides OPENAI_API_KEY")
    parser.add_argument("--gemini-api-key", default=None, help="overrides GEMINI_API_KEY")
    parser.add_argument("--ollama-base-url", default=None, help="overrides OLLAMA_BASE_URL")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    return parser.parse_args(argv)


def apply_key_overrides(args: argparse.Namespace) -> None:
    """config.py reads these once at import, so a flag has to land before that."""
    for attribute, variable in KEY_FLAGS:
        value = getattr(args, attribute)
        if value:
            os.environ[variable] = value


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    apply_key_overrides(args)

    from volvo.ui.app import build

    build().launch(server_name=args.host, server_port=args.port)


if __name__ == "__main__":
    main()
