"""Regenerate every result, figure, table and document, in dependency order."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STEPS = [
    ([sys.executable, "scripts/run_baseline.py"], "discovery baseline"),
    ([sys.executable, "scripts/run_verification.py"], "LTL verification"),
    ([sys.executable, "scripts/run_analytics.py"], "analytics"),
    ([sys.executable, "scripts/run_report.py"], "reports"),
    ([sys.executable, "scripts/build_figures.py"], "figures"),
    ([sys.executable, "scripts/build_tables.py"], "tables"),
    (["latexmk", "-pdf", "-interaction=nonstopmode", "-cd", "docs/report/report.tex"], "report PDF"),
    (["latexmk", "-pdf", "-interaction=nonstopmode", "-cd",
      "docs/presentation/presentation.tex"], "presentation PDF"),
]


def main() -> int:
    for command, label in STEPS:
        print(f"\n=== {label} ===", flush=True)
        try:
            result = subprocess.run(command, cwd=ROOT)
        except FileNotFoundError as exc:
            print(f"FAILED at {label}: {exc}")
            return 1
        if result.returncode != 0:
            print(f"FAILED at {label} (exit {result.returncode})")
            return result.returncode

    print("\nAll artifacts regenerated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
