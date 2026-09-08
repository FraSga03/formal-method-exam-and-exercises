"""Pure functions behind the dashboard widgets. No Gradio imports belong here."""
import pandas as pd
import plotly.graph_objects as go

from volvo.ai import assistant as assistant_module
from volvo.ai.providers import available_providers, describe, get_provider
from volvo.analysis.health import health_score, insights
from volvo.config import DATA_DIR, OUTPUT_DIR
from volvo.logs import preprocessing
from volvo.logs.loader import ACTIVITY, EventLogBundle, load
from volvo.mining.comparison import compare_algorithms
from volvo.mining.conformance import evaluate
from volvo.mining.discovery import discover
from volvo.mining.performance import duration_summary, variant_summary, waiting_times
from volvo.reporting import report as report_module
from volvo.ui import charts
from volvo.verification.ltl import verify
from volvo.verification.patterns import PROPERTIES, get_property, verify_all

NO_LOG = (
    "**Error:** no log is loaded. Open the **Data** tab, pick a log in the "
    "dropdown, click **Load**, then come back here."
)
NONE_PROVIDER = "none"


def require_bundle(bundle: EventLogBundle | None) -> str | None:
    return None if bundle is not None else NO_LOG


def available_logs() -> list[str]:
    return sorted(p.name for p in DATA_DIR.glob("*.xes*")) if DATA_DIR.exists() else []


def default_log() -> str | None:
    """Preselected on startup so the dashboard opens with a log already loaded."""
    logs = available_logs()
    return logs[0] if logs else None


def load_log(name: str, mode: str):
    path = DATA_DIR / name
    if not name or not path.exists():
        return None, f"**Error:** no log named {name!r} in {DATA_DIR}.", pd.DataFrame(), go.Figure()

    try:
        bundle = load(path, mode=mode)
    except Exception as exc:  # surfaced in the UI
        return None, f"**Error:** {exc}", pd.DataFrame(), go.Figure()

    summary = bundle.summary()
    text = (
        f"**{summary['source']}** — schema `{summary['schema']}`, "
        f"mode `{summary['activity_mode']}`\n\n"
        f"- cases: {summary['unique_cases']:,}\n"
        f"- events: {summary['total_events']:,}\n"
        f"- activities: {summary['unique_activities']}\n"
        f"- range: {summary['time_range'][0][:10]} to {summary['time_range'][1][:10]}"
    )
    counts = bundle.df[ACTIVITY].value_counts()
    table = pd.DataFrame({"activity": counts.index, "events": counts.values})
    return bundle, text, table, charts.activity_frequency(bundle)


def run_discovery(bundle, algorithm: str, threshold: float):
    if require_bundle(bundle):
        return None, NO_LOG, pd.DataFrame()

    params = (
        {"dependency_threshold": threshold}
        if algorithm == "heuristics"
        else {"noise_threshold": threshold}
        if algorithm == "inductive"
        else {}
    )
    try:
        result = discover(bundle, algorithm, render=True, **params)
    except Exception as exc:  # surfaced in the UI
        return None, f"**Error:** {exc}", pd.DataFrame()

    stats = result.statistics()
    table = pd.DataFrame(
        {"metric": list(stats), "value": [str(v) for v in stats.values()]}
    )
    text = f"Discovered with **{algorithm}** using `{result.params or 'defaults'}`."
    return result.image_path, text, table


def run_conformance(bundle, algorithm: str, method: str, max_cases: int):
    if require_bundle(bundle):
        return NO_LOG, pd.DataFrame()
    try:
        result = discover(bundle, algorithm, render=False)
        metrics = evaluate(bundle, result, method=method, max_cases=int(max_cases))
    except Exception as exc:  # surfaced in the UI
        return f"**Error:** {exc}", pd.DataFrame()

    data = metrics.as_dict()
    table = pd.DataFrame({"metric": list(data), "value": [str(v) for v in data.values()]})
    return f"**{algorithm}** scored by `{method}` on {metrics.sampled_cases} cases.", table


def run_comparison(bundle, max_cases: int):
    if require_bundle(bundle):
        return NO_LOG, pd.DataFrame()
    rows = compare_algorithms(bundle, render=False, max_cases=int(max_cases))
    return "Every algorithm scored on the same sample.", pd.DataFrame(rows)


def property_choices() -> list[str]:
    return [p.key for p in PROPERTIES]


def property_formula(key: str) -> str:
    return get_property(key).formula


def run_ltl(bundle, formula: str, max_counterexamples: int):
    if require_bundle(bundle):
        return NO_LOG, pd.DataFrame()

    result = verify(bundle, formula, max_counterexamples=int(max_counterexamples))
    if result.error:
        return f"**Error:** {result.error}", pd.DataFrame()

    text = (
        f"`{result.formula}`\n\n"
        f"- satisfied: {result.satisfied:,} of {result.total:,} ({result.ratio:.1%})\n"
        f"- violated: {result.violated:,}"
    )
    table = pd.DataFrame(
        [
            {"case": c["case"], "trace": " -> ".join(c["trace"][:12])}
            for c in result.counterexamples
        ]
    )
    return text, table


def run_property_library(bundle):
    if require_bundle(bundle):
        return NO_LOG, pd.DataFrame()
    rows = [
        {
            "property": r["name"],
            "formula": r["formula"],
            "satisfied": r["satisfied"],
            "violated": r["violated"],
            "ratio": round(r["ratio"], 4),
        }
        for r in verify_all(bundle)
    ]
    return "Shipped property library, verified against every case.", pd.DataFrame(rows)


def run_analytics(bundle):
    if require_bundle(bundle):
        return NO_LOG, pd.DataFrame(), go.Figure(), go.Figure(), go.Figure()

    health = health_score(bundle)
    duration = duration_summary(bundle)
    variant = variant_summary(bundle)

    text = (
        f"**Health {health['score']:.1f}/100 (grade {health['grade']})**\n\n"
        f"- median case duration: {duration['median_hours']:.1f} h\n"
        f"- p95 case duration: {duration['p95_hours']:.1f} h\n"
        f"- distinct variants: {variant['distinct_variants']:,} "
        f"({variant['variant_ratio']:.1%} of cases)\n\n"
        + "\n".join(f"- _{i['severity']}_ **{i['title']}** — {i['detail']}" for i in insights(bundle))
    )
    table = waiting_times(bundle).reset_index()
    return (
        text,
        table,
        charts.waiting_time_bar(bundle),
        charts.duration_histogram(bundle),
        charts.transition_heatmap(bundle),
    )


def apply_preprocessing(bundle, min_events: int, dedupe: bool):
    if require_bundle(bundle):
        return bundle, NO_LOG
    try:
        result = preprocessing.filter_case_length(bundle, min_events=int(min_events))
        if dedupe:
            result = preprocessing.drop_duplicate_events(result)
    except Exception as exc:  # surfaced in the UI
        return bundle, f"**Error:** {exc}"

    summary = result.summary()
    text = (
        f"{summary['total_events']:,} events across "
        f"{summary['unique_cases']:,} cases remain."
    )
    return result, text


def provider_choices() -> list[str]:
    return [NONE_PROVIDER, *available_providers()]


def provider_help() -> str:
    """What each available provider costs, so nobody bills themselves by accident."""
    usable = available_providers()
    if not usable:
        return "No provider configured — see .env.example."
    return " | ".join(f"{name}: {describe(name)}" for name in usable)


def _resolve(provider_name: str | None):
    if not provider_name or provider_name == NONE_PROVIDER:
        return None
    return get_provider(provider_name)


def generate_report(bundle, provider_name: str):
    if require_bundle(bundle):
        return NO_LOG, None

    text = report_module.build(bundle, provider=_resolve(provider_name))
    path = report_module.save(text, OUTPUT_DIR.parent / "report.md")
    return text, str(path)


def ask_assistant(bundle, question: str, provider_name: str) -> str:
    return assistant_module.ask(bundle, question, provider=_resolve(provider_name))


SUGGESTED_QUESTIONS = [
    "Where is the most time being lost in this process?",
    "Why is the health score not higher?",
    "Which temporal properties fail, and what does that say about the process?",
    "How much rework is there, and where does it come from?",
    "Is this process standardised, or does every case follow its own path?",
    "What would you fix first?",
]


def chat(bundle, message: str, history, provider_name: str):
    """Append one exchange. Returns the transcript and an empty box."""
    history = list(history or [])
    if not message or not message.strip():
        return history, ""

    answer = assistant_module.ask(
        bundle, message, provider=_resolve(provider_name), history=history
    )
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer})
    return history, ""
