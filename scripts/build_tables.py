"""LaTeX result tables generated from the analysis.

Nothing measured is ever typed into a .tex file by hand; rerun this and the
report is current.
"""
import sys
from pathlib import Path

from volvo.analysis.health import health_score
from volvo.config import DATA_DIR
from volvo.logs.loader import load
from volvo.mining.comparison import compare_algorithms
from volvo.mining.performance import waiting_times
from volvo.verification.patterns import verify_all

TABLES = Path(__file__).resolve().parent.parent / "docs" / "tables"

_ESCAPES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def latex_escape(text: str) -> str:
    return "".join(_ESCAPES.get(char, char) for char in str(text))


def latex_table(headers: list[str], rows: list[list[str]], spec: str) -> str:
    lines = [
        f"\\begin{{tabular}}{{{spec}}}",
        "\\toprule",
        " & ".join(latex_escape(h) for h in headers) + " \\\\",
        "\\midrule",
    ]
    lines += [" & ".join(latex_escape(c) for c in row) + " \\\\" for row in rows]
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


def _write(name: str, text: str) -> Path:
    TABLES.mkdir(parents=True, exist_ok=True)
    path = TABLES / name
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path}")
    return path


def main() -> int:
    logs = sorted(DATA_DIR.glob("*.xes.gz"))
    if not logs:
        print(f"No logs in {DATA_DIR}. Run scripts/fetch_data.py first.")
        return 1

    dataset_rows, health_rows = [], []
    for path in logs:
        bundle = load(path)
        summary = bundle.summary()
        health = health_score(bundle)
        dataset_rows.append([
            summary["source"].replace("BPI_Challenge_2013_", "").replace(".xes.gz", ""),
            f"{summary['unique_cases']:,}",
            f"{summary['total_events']:,}",
            str(summary["unique_activities"]),
            summary["time_range"][0][:10],
            summary["time_range"][1][:10],
        ])
        health_rows.append([
            summary["source"].replace("BPI_Challenge_2013_", "").replace(".xes.gz", ""),
            f"{health['score']:.1f}",
            health["grade"],
            *[f"{v:.3f}" for v in health["components"].values()],
        ])

    _write("dataset.tex", latex_table(
        ["Log", "Cases", "Events", "Activities", "From", "To"], dataset_rows, "lrrrll"))
    _write("health.tex", latex_table(
        ["Log", "Score", "Grade", "Completion", "Rework", "Standardisation", "Throughput"],
        health_rows, "lrlrrrr"))

    incidents = DATA_DIR / "BPI_Challenge_2013_incidents.xes.gz"
    discovery_rows = []
    for mode in ("status", "status_substatus"):
        bundle = load(incidents, mode=mode)
        for row in compare_algorithms(bundle, render=False, max_cases=500):
            if row["error"]:
                continue
            discovery_rows.append([
                mode.replace("_", "+"), row["algorithm"],
                f"{row['fitness']:.3f}", f"{row['precision']:.3f}",
                f"{row['generalization']:.3f}", f"{row['simplicity']:.3f}",
                str(row["num_places"]), str(row["num_transitions"]),
            ])
    _write("discovery.tex", latex_table(
        ["Mode", "Algorithm", "Fitness", "Precision", "Gen.", "Simpl.", "Places", "Trans."],
        discovery_rows, "llrrrrrr"))

    bundle = load(incidents)
    _write("ltl.tex", latex_table(
        ["Property", "Satisfied", "Violated", "Ratio"],
        [[r["name"], f"{r['satisfied']:,}", f"{r['violated']:,}", f"{r['ratio']:.3f}"]
         for r in verify_all(bundle)],
        "lrrr"))
    _write("waiting.tex", latex_table(
        ["Activity", "n", "Mean (h)", "Median (h)", "Max (h)"],
        [[a, f"{int(r['count']):,}", f"{r['mean_hours']:.2f}",
          f"{r['median_hours']:.2f}", f"{r['max_hours']:.2f}"]
         for a, r in waiting_times(bundle).iterrows()],
        "lrrrr"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
