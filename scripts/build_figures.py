"""Static figures for the report. Matplotlib, not Plotly: these must print."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display on a build machine
import matplotlib.pyplot as plt  # noqa: E402

from volvo.analysis.predictor import MarkovModel  # noqa: E402
from volvo.config import DATA_DIR  # noqa: E402
from volvo.logs.loader import ACTIVITY, EventLogBundle, load  # noqa: E402
from volvo.mining.discovery import ALGORITHMS, discover  # noqa: E402
from volvo.mining.performance import (  # noqa: E402
    case_durations,
    variants,
    waiting_times,
)

FIGURES = Path(__file__).resolve().parent.parent / "docs" / "figures"


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def figures_for(bundle: EventLogBundle, outdir: Path) -> list[Path]:
    outdir = Path(outdir)
    written = []

    counts = bundle.df[ACTIVITY].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(counts.index, counts.values)
    ax.set_xlabel("Events")
    written.append(_save(fig, outdir / "activity_frequency.png"))

    table = waiting_times(bundle).head(10).sort_values("mean_hours")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if not table.empty:
        y = range(len(table))
        ax.barh([i + 0.2 for i in y], table["mean_hours"], height=0.4, label="mean")
        ax.barh([i - 0.2 for i in y], table["median_hours"], height=0.4, label="median")
        ax.set_yticks(list(y))
        ax.set_yticklabels(table.index)
        ax.legend()
    ax.set_xlabel("Hours")
    written.append(_save(fig, outdir / "waiting_times.png"))

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(case_durations(bundle).values, bins=50)
    ax.set_xlabel("Case duration (hours)")
    ax.set_ylabel("Cases")
    written.append(_save(fig, outdir / "duration_hist.png"))

    rows = variants(bundle, top=20)
    fig, ax = plt.subplots(figsize=(7, 4))
    cumulative, running = [], 0.0
    for row in rows:
        running += row["share"]
        cumulative.append(running * 100)
    ax.plot(range(1, len(cumulative) + 1), cumulative, marker="o")
    ax.set_xlabel("Variant rank")
    ax.set_ylabel("Cumulative share of cases (%)")
    written.append(_save(fig, outdir / "variant_pareto.png"))

    matrix = MarkovModel.fit(bundle).transition_matrix()
    fig, ax = plt.subplots(figsize=(7, 6))
    image = ax.imshow(matrix.to_numpy(), aspect="auto")
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=90, fontsize=6)
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index, fontsize=6)
    fig.colorbar(image, ax=ax)
    written.append(_save(fig, outdir / "transition_heatmap.png"))

    return written


def main() -> int:
    log = DATA_DIR / "BPI_Challenge_2013_incidents.xes.gz"
    if not log.exists():
        print(f"{log} not found. Run scripts/fetch_data.py first.")
        return 1

    for path in figures_for(load(log), FIGURES):
        print(f"wrote {path}")

    for mode in ("status", "status_substatus"):
        bundle = load(log, mode=mode)
        for algorithm in ALGORITHMS:
            result = discover(bundle, algorithm, render=True)
            if result.image_path:
                target = FIGURES / f"petri_{algorithm}_{mode}.png"
                target.write_bytes(Path(result.image_path).read_bytes())
                print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
