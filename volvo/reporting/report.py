"""Report generation.

The report is built from measured facts and is complete without an LLM; a
narrative section is added only when a provider is supplied and succeeds.
"""
from datetime import datetime
from pathlib import Path

from volvo.analysis.anomalies import summary as anomaly_summary
from volvo.analysis.health import health_score, insights
from volvo.logs.loader import EventLogBundle
from volvo.mining.conformance import evaluate
from volvo.mining.discovery import discover
from volvo.mining.performance import duration_summary, variant_summary, waiting_times
from volvo.verification.patterns import verify_all


def collect(
    bundle: EventLogBundle, *, algorithm: str = "inductive", max_cases: int = 500
) -> dict:
    facts = {
        "summary": bundle.summary(),
        "health": health_score(bundle),
        "insights": insights(bundle),
        "duration": duration_summary(bundle),
        "variants": variant_summary(bundle),
        "waiting": waiting_times(bundle),
        "anomalies": anomaly_summary(bundle),
        "properties": verify_all(bundle),
        "model": None,
    }
    try:
        result = discover(bundle, algorithm, render=False)
        metrics = evaluate(bundle, result, max_cases=max_cases)
        facts["model"] = {**result.statistics(), **metrics.as_dict()}
    except Exception as exc:  # noqa: BLE001 - reported in the document
        facts["model"] = {"error": str(exc)}
    return facts


def _narrative_prompt(facts: dict) -> str:
    health = facts["health"]
    failing = [p for p in facts["properties"] if p["ratio"] < 0.9]
    return (
        "Write three short paragraphs of executive summary for a process mining "
        "report on IT incident management. Be specific and avoid filler.\n\n"
        f"Cases: {facts['summary']['unique_cases']}, "
        f"events: {facts['summary']['total_events']}, "
        f"activities: {facts['summary']['unique_activities']}.\n"
        f"Health {health['score']:.1f}/100 (grade {health['grade']}), "
        f"components {health['components']}.\n"
        f"Median case duration {facts['duration']['median_hours']:.1f} hours.\n"
        f"Distinct variants: {facts['variants']['distinct_variants']}.\n"
        "Temporal properties that do not hold: "
        + ("; ".join(f"{p['name']} at {p['ratio']:.1%}" for p in failing) or "none")
    )


def render(facts: dict, narrative: str | None = None) -> str:
    summary = facts["summary"]
    health = facts["health"]
    duration = facts["duration"]
    variants = facts["variants"]

    lines = [
        f"# Process Mining Report — {summary['source']}",
        f"*Generated {datetime.now():%Y-%m-%d %H:%M}*",
        "",
        "## Dataset",
        f"- schema: `{summary['schema']}`, activity mode: `{summary['activity_mode']}`",
        f"- cases: {summary['unique_cases']:,}",
        f"- events: {summary['total_events']:,}",
        f"- activities: {summary['unique_activities']}",
        f"- range: {summary['time_range'][0][:10]} to {summary['time_range'][1][:10]}",
        "",
        "## Health",
        f"**{health['score']:.1f}/100 — grade {health['grade']}**",
        "",
        "| Component | Value |",
        "|---|---|",
    ]
    lines += [f"| {k} | {v:.3f} |" for k, v in health["components"].items()]

    lines += ["", "### Insights", ""]
    lines += [
        f"- **{i['severity']}** {i['title']} — {i['detail']}" for i in facts["insights"]
    ] or ["- No insight thresholds were crossed."]

    lines += [
        "",
        "## Performance",
        f"- median case duration: {duration['median_hours']:.1f} h",
        f"- p95: {duration['p95_hours']:.1f} h, max: {duration['max_hours']:.1f} h",
        f"- distinct variants: {variants['distinct_variants']:,} "
        f"({variants['variant_ratio']:.1%} of cases)",
        "",
        "### Waiting time after each activity (hours)",
        "",
        "| Activity | n | mean | median | max |",
        "|---|---|---|---|---|",
    ]
    for activity, row in facts["waiting"].iterrows():
        lines.append(
            f"| {activity} | {int(row['count'])} | {row['mean_hours']:.2f} "
            f"| {row['median_hours']:.2f} | {row['max_hours']:.2f} |"
        )

    lines += ["", "## Discovered model", ""]
    model = facts["model"] or {}
    lines += [f"- {k}: {v}" for k, v in model.items()]

    lines += [
        "",
        "## Temporal properties",
        "",
        "| Property | Formula | Satisfied | Violated | Ratio |",
        "|---|---|---|---|---|",
    ]
    for prop in facts["properties"]:
        formula = prop["formula"].replace("|", "\\|")
        lines.append(
            f"| {prop['name']} | `{formula}` | {prop['satisfied']} "
            f"| {prop['violated']} | {prop['ratio']:.3f} |"
        )

    lines += ["", "## Anomalies", ""]
    lines += [f"- {k}: {v}" for k, v in facts["anomalies"].items()]

    if narrative:
        lines += ["", "## Narrative", "", narrative]

    return "\n".join(lines) + "\n"


def build(bundle: EventLogBundle, *, provider=None, **kwargs) -> str:
    facts = collect(bundle, **kwargs)
    narrative = None
    if provider is not None:
        try:
            narrative = provider.generate(_narrative_prompt(facts))
        except Exception as exc:  # noqa: BLE001 - the report survives a dead provider
            narrative = f"_Narrative unavailable: {exc}_"
    return render(facts, narrative)


def save(text: str, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
