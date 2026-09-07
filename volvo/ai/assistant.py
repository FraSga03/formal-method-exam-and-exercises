"""Question answering grounded in the loaded log."""
from volvo.analysis.health import health_score
from volvo.logs.loader import EventLogBundle
from volvo.mining.performance import duration_summary, variant_summary, waiting_times
from volvo.verification.patterns import verify_all

NO_LOG_LOADED = (
    "**Error:** no log is loaded. Open the **Data** tab, pick a log in the "
    "dropdown, click **Load**, then come back here."
)

NO_PROVIDER = (
    "**No provider selected.** The dropdown above is set to `none`: pick one of "
    "the other entries and ask again.\n\n"
    "If `none` is the only entry, no provider is usable yet:\n\n"
    "- **local, free, no key** — install Ollama, run `ollama pull llama3.2`, "
    "then `uv sync --extra ai`\n"
    "- **hosted** — put `OPENAI_API_KEY` or `GEMINI_API_KEY` in `.env` (see "
    "`.env.example`), then `uv sync --extra ai`\n\n"
    "Restart the dashboard afterwards; the list is built at startup. Every "
    "other feature works without any of this."
)


HOLDS_THRESHOLD = 0.9


def context(bundle: EventLogBundle) -> str:
    summary = bundle.summary()
    health = health_score(bundle)
    duration = duration_summary(bundle)
    variants = variant_summary(bundle)
    waits = waiting_times(bundle).head(5)

    lines = [
        f"Log: {summary['source']} ({summary['activity_mode']})",
        f"cases: {summary['unique_cases']}, events: {summary['total_events']}, "
        f"activities: {summary['unique_activities']}",
        f"activity list: {', '.join(summary['activities'])}",
        f"health: {health['score']:.1f}/100 grade {health['grade']}. "
        "Components are scores where higher is better, not rates: "
        + ", ".join(f"{k} {v:.3f}" for k, v in health["components"].items())
        + f". A rework score of {health['components']['rework']:.3f} means "
        f"{health['components']['rework']:.0%} of events are the first occurrence "
        "of their activity in the case, so the remainder is repetition.",
        f"median case duration: {duration['median_hours']:.1f} h, "
        f"p95 {duration['p95_hours']:.1f} h",
        f"distinct variants: {variants['distinct_variants']} "
        f"({variants['variant_ratio']:.1%})",
        "slowest activities by mean waiting hours: "
        + ", ".join(f"{a} {r['mean_hours']:.1f}" for a, r in waits.iterrows()),
        "temporal properties, as the share of cases satisfying each. "
        f"A property below {HOLDS_THRESHOLD:.0%} is marked DOES NOT HOLD and is a "
        "finding about the process: "
        + "; ".join(
            f"{p['name']} {p['ratio']:.1%}"
            + ("" if p["ratio"] >= HOLDS_THRESHOLD else " DOES NOT HOLD")
            for p in verify_all(bundle)
        ),
    ]
    return "\n".join(lines)


HISTORY_TURNS = 8


def _transcript(history) -> str:
    """Recent turns only; the fact block matters more than a long tail."""
    recent = list(history or [])[-HISTORY_TURNS:]
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in recent)


def ask(
    bundle: EventLogBundle | None,
    question: str,
    provider=None,
    history=None,
) -> str:
    if bundle is None:
        return NO_LOG_LOADED
    if provider is None:
        return NO_PROVIDER

    conversation = _transcript(history)
    prompt = (
        "You are answering questions about a process mining analysis. Use only "
        "the facts below. Quote figures exactly as given and never invent one. "
        "If the facts do not settle the question, say so.\n\n"
        f"{context(bundle)}\n\n"
        + (f"Conversation so far:\n{conversation}\n\n" if conversation else "")
        + f"Question: {question}"
    )
    try:
        return provider.generate(prompt)
    except Exception as exc:  # noqa: BLE001 - surfaced to the user
        return f"**Error:** {exc}"
