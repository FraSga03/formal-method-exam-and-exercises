"""Write a report for every downloaded log."""
import sys

from volvo.ai.providers import get_provider
from volvo.config import BASE_DIR, DATA_DIR
from volvo.logs.loader import load
from volvo.reporting import report


def main() -> int:
    logs = sorted(DATA_DIR.glob("*.xes.gz"))
    if not logs:
        print(f"No logs in {DATA_DIR}. Run scripts/fetch_data.py first.")
        return 1

    provider = get_provider()
    print(f"Narrative provider: {provider.name if provider else 'none'}")

    for path in logs:
        text = report.build(load(path), provider=provider)
        target = report.save(text, BASE_DIR / "docs" / "results" / f"report-{path.stem}.md")
        print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
