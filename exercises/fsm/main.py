import argparse
import asyncio
import os
import sys

import openai
from colorama import Fore, Style, init
from dotenv import load_dotenv

from states import fsm

GREETING = (
    "Hi. I am a movie review assistant. Do you want to review a film,"
    " read past reviews, or change one you already wrote?"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Movie review assistant.")
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key; falls back to OPENAI_API_KEY in the environment or .env",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use; fsm-llm defaults to gpt-4o when not passed",
    )
    return parser.parse_args(argv)


def resolve_key(cli_key: str | None) -> str | None:
    load_dotenv()
    return cli_key or os.getenv("OPENAI_API_KEY")


async def main() -> int:
    init(autoreset=True)
    args = parse_args()

    key = resolve_key(args.api_key)
    if not key:
        print(
            "No API key. Pass --api-key, or set OPENAI_API_KEY in the environment or .env.",
            file=sys.stderr,
        )
        return 1

    client = openai.AsyncOpenAI(api_key=key)
    print(f"{Fore.GREEN}Agent\t{GREETING}{Style.RESET_ALL}")

    while not fsm.is_completed():
        try:
            user_input = input(f"{Fore.CYAN}You\t{Style.RESET_ALL}")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_input.strip().lower() in {"quit", "exit"}:
            fsm.set_next_state("END")
            break

        run_state = await fsm.run_state_machine(client, user_input=user_input, model=args.model)
        print(f"{Fore.GREEN}Agent\t{run_state.response}{Style.RESET_ALL}")

    print(f"{Fore.GREEN}Agent\tGoodbye!{Style.RESET_ALL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
