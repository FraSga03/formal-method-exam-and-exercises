"""Verify the shipped LTLf property library against the real incidents log."""
import sys

from volvo.config import DATA_DIR
from volvo.logs.loader import load
from volvo.verification.patterns import verify_all

LOG = DATA_DIR / "BPI_Challenge_2013_incidents.xes.gz"


def main() -> int:
    if not LOG.exists():
        print(f"{LOG} not found. Run scripts/fetch_data.py first.")
        return 1

    bundle = load(LOG)
    rows = verify_all(bundle)

    print(f"Log: {bundle.source} ({bundle.summary()['unique_cases']} cases)\n")
    print("| Property | Formula | Satisfied | Violated | Ratio |")
    print("|---|---|---|---|---|")
    for row in rows:
        formula = row["formula"].replace("|", "\\|")  # keep the markdown cell intact
        print(
            f"| {row['name']} | `{formula}` "
            f"| {row['satisfied']} | {row['violated']} | {row['ratio']:.3f} |"
        )

    print("\n## Counterexamples\n")
    for row in rows:
        if not row["counterexamples"]:
            continue
        print(f"### {row['name']}\n")
        for example in row["counterexamples"][:3]:
            print(f"- case `{example['case']}`: {' → '.join(example['trace'][:8])}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
