"""Pure functions behind the dashboard widgets. No Gradio imports belong here."""
import pandas as pd
import plotly.graph_objects as go

from volvo.ai import assistant as assistant_module
from volvo.ai.providers import available_providers, describe, get_provider
from volvo.analysis import anomalies
from volvo.analysis.health import health_score, insights
from volvo.analysis.predictor import MarkovModel, UnknownActivityError
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


def activity_choices(bundle) -> list[str]:
    """Populates the activity pickers; empty until a log is loaded."""
    if require_bundle(bundle):
        return []
    return sorted(bundle.df[ACTIVITY].unique().tolist())


def parse_relabelling(text: str) -> dict[str, str]:
    """One `old = new` per line. The first `=` separates; later ones are literal."""
    mapping = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if "=" not in line:
            raise ValueError(f"line {number}: expected `old = new`, got {line.strip()!r}")
        source, target = line.split("=", 1)
        if not source.strip() or not target.strip():
            raise ValueError(f"line {number}: both sides must be non-empty")
        mapping[source.strip()] = target.strip()
    return mapping


def apply_preprocessing(
    bundle,
    activities: list[str] | None,
    activity_action: str,
    start: str,
    end: str,
    min_events: int,
    max_events: int | None,
    dedupe: bool,
    relabelling: str,
):
    """Filters compose in a fixed order so the result does not depend on the widgets."""
    if require_bundle(bundle):
        return bundle, NO_LOG
    try:
        mapping = parse_relabelling(relabelling or "")
        result = bundle
        if activities:
            result = preprocessing.filter_activities(
                result, activities, exclude=activity_action == "exclude"
            )
        if start or end:
            result = preprocessing.filter_time_range(result, start or None, end or None)
        result = preprocessing.filter_case_length(
            result,
            min_events=int(min_events),
            max_events=int(max_events) if max_events else None,
        )
        if dedupe:
            result = preprocessing.drop_duplicate_events(result)
        if mapping:
            result = preprocessing.generalize_activities(result, mapping)
    except Exception as exc:  # surfaced in the UI
        return bundle, f"**Error:** {exc}"

    summary = result.summary()
    text = (
        f"{summary['total_events']:,} events across "
        f"{summary['unique_cases']:,} cases remain."
    )
    return result, text


def run_anomalies(
    bundle, threshold_std: float, rare_pct: float, wait_hours: float, min_support: int
):
    empty = pd.DataFrame()
    if require_bundle(bundle):
        return NO_LOG, empty, empty, empty, empty

    lengths = anomalies.unusual_trace_lengths(bundle, threshold_std=float(threshold_std))
    rare = anomalies.rare_activities(bundle, threshold_pct=float(rare_pct))
    waits = anomalies.long_waits(bundle, threshold_hours=float(wait_hours))
    transitions = anomalies.rare_transitions(bundle, min_support=int(min_support))

    text = (
        f"**{len(lengths['cases']) + len(rare) + len(waits) + len(transitions)} anomalies**\n\n"
        f"- case length outside {lengths['lower']:.1f}–{lengths['upper']:.1f} events "
        f"(mean {lengths['mean']:.1f}, sd {lengths['std']:.1f}): {len(lengths['cases'])} cases\n"
        f"- activities below {rare_pct:g}% of events: {len(rare)}\n"
        f"- waits over {wait_hours:g} h: {len(waits)} (top 50 shown)\n"
        f"- transitions seen fewer than {int(min_support)} times: {len(transitions)}"
    )
    return (
        text,
        pd.DataFrame(lengths["cases"]),
        pd.DataFrame(rare),
        pd.DataFrame(waits),
        pd.DataFrame(transitions),
    )


def predict_next(bundle, activity: str, top_k: int):
    if require_bundle(bundle):
        return NO_LOG, pd.DataFrame()
    try:
        successors = MarkovModel.fit(bundle).predict_next(activity, top_k=int(top_k))
    except UnknownActivityError as exc:
        return f"**Error:** {exc}", pd.DataFrame()

    if not successors:
        return f"**{activity}** has no successor — every case ends there.", pd.DataFrame()
    return (
        f"Most likely to follow **{activity}**, over {len(successors)} of its successors.",
        pd.DataFrame(successors),
    )


def predict_sequence(bundle, activity: str, length: int):
    if require_bundle(bundle):
        return NO_LOG
    try:
        walk = MarkovModel.fit(bundle).predict_sequence(activity, length=int(length))
    except UnknownActivityError as exc:
        return f"**Error:** {exc}"

    return " → ".join(walk)


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
