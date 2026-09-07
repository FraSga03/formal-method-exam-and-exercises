"""Entry point: uv run python -m volvo.main"""
from volvo.ui.app import build

if __name__ == "__main__":
    build().launch(server_name="127.0.0.1", server_port=7860)
