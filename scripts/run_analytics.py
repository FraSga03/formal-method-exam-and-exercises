"""Performance, anomaly and health figures for every downloaded log."""
import sys

from volvo.analysis.anomalies import summary as anomaly_summary
from volvo.analysis.health import health_score, insights
from volvo.analysis.predictor import MarkovModel
from volvo.config import DATA_DIR
from volvo.logs.loader import load
from volvo.mining.performance import duration_summary, variant_summary, waiting_times


def report(path) -> None:
    bundle = load(path)
    print(f"\n# {path.name}\n")

    duration = duration_summary(bundle)
    variant = variant_summary(bundle)
    health = health_score(bundle)

    print(f"- cases: {duration['cases']}, distinct variants: "
          f"{variant['distinct_variants']} ({variant['variant_ratio']:.1%})")
    print(f"- case duration: median {duration['median_hours']:.1f} h, "
          f"p95 {duration['p95_hours']:.1f} h, max {duration['max_hours']:.1f} h")
    print(f"- health: {health['score']:.1f}/100 (grade {health['grade']})")
    for name, value in health["components"].items():
        print(f"    - {name}: {value:.3f}")

    print("\n## Waiting time after each activity (hours)\n")
    print("| Activity | n | mean | median | max |")
    print("|---|---|---|---|---|")
    for activity, row in waiting_times(bundle).iterrows():
        print(f"| {activity} | {int(row['count'])} | {row['mean_hours']:.2f} "
              f"| {row['median_hours']:.2f} | {row['max_hours']:.2f} |")

    print("\n## Anomalies\n")
    for name, count in anomaly_summary(bundle).items():
        print(f"- {name}: {count}")

    print("\n## Insights\n")
    for insight in insights(bundle) or [{"severity": "low", "title": "None", "detail": "-"}]:
        print(f"- **{insight['severity']}** {insight['title']} — {insight['detail']}")

    model = MarkovModel.fit(bundle)
    print("\n## Most likely next activity\n")
    for activity in model.activities:
        top = model.predict_next(activity, top_k=1)
        if top:
            print(f"- {activity} -> {top[0]['activity']} ({top[0]['probability']:.1%})")


def main() -> int:
    logs = sorted(DATA_DIR.glob("*.xes.gz"))
    if not logs:
        print(f"No logs in {DATA_DIR}. Run scripts/fetch_data.py first.")
        return 1
    for path in logs:
        report(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
