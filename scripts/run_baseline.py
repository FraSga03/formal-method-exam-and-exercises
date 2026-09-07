"""Run the algorithm comparison on the real incidents log and print a table."""
import sys

from volvo.config import DATA_DIR
from volvo.logs.loader import load
from volvo.mining.comparison import compare_algorithms

LOG = DATA_DIR / "BPI_Challenge_2013_incidents.xes.gz"


def main() -> int:
    if not LOG.exists():
        print(f"{LOG} not found. Run scripts/fetch_data.py first.")
        return 1

    for mode in ("status", "status_substatus"):
        bundle = load(LOG, mode=mode)
        summary = bundle.summary()
        print(f"\n## mode={mode} "
              f"({summary['unique_activities']} activities, "
              f"{summary['unique_cases']} cases)\n")
        print("| Algorithm | Fitness | Precision | Generalization | Simplicity | Places | Transitions |")
        print("|---|---|---|---|---|---|---|")
        for row in compare_algorithms(bundle, render=True, max_cases=500):
            if row["error"]:
                print(f"| {row['algorithm']} | error: {row['error'][:60]} | | | | | |")
                continue
            print(
                f"| {row['algorithm']} "
                f"| {row['fitness']:.3f} | {row['precision']:.3f} "
                f"| {row['generalization']:.3f} | {row['simplicity']:.3f} "
                f"| {row['num_places']} | {row['num_transitions']} |"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
