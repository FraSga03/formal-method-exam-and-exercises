"""Statistical outliers in an event log."""
from collections import Counter

from volvo.logs.loader import ACTIVITY, CASE, EventLogBundle
from volvo.mining.performance import _traces, _with_waiting


def unusual_trace_lengths(bundle: EventLogBundle, threshold_std: float = 2.0) -> dict:
    lengths = bundle.df.groupby(CASE)[ACTIVITY].size()
    mean, std = float(lengths.mean()), float(lengths.std(ddof=0))
    lower, upper = mean - threshold_std * std, mean + threshold_std * std
    outliers = lengths[(lengths < lower) | (lengths > upper)].sort_values(ascending=False)
    return {
        "mean": mean,
        "std": std,
        "lower": lower,
        "upper": upper,
        "cases": [{"case": str(c), "length": int(n)} for c, n in outliers.items()],
    }


def rare_activities(bundle: EventLogBundle, threshold_pct: float = 1.0) -> list[dict]:
    counts = bundle.df[ACTIVITY].value_counts()
    total = int(counts.sum())
    rare = [
        {"activity": str(a), "count": int(n), "share": n / total}
        for a, n in counts.items()
        if n / total * 100 < threshold_pct
    ]
    return sorted(rare, key=lambda r: r["count"])


def long_waits(
    bundle: EventLogBundle, threshold_hours: float = 24.0, top: int = 50
) -> list[dict]:
    waits = _with_waiting(bundle)
    flagged = waits[waits["wait_hours"] > threshold_hours].nlargest(top, "wait_hours")
    return [
        {
            "case": str(row[CASE]),
            "activity": str(row[ACTIVITY]),
            "wait_hours": float(row["wait_hours"]),
        }
        for _, row in flagged.iterrows()
    ]


def rare_transitions(bundle: EventLogBundle, min_support: int = 2) -> list[dict]:
    pairs = Counter()
    for trace in _traces(bundle):
        pairs.update(zip(trace, trace[1:]))
    return sorted(
        (
            {"source": s, "target": t, "count": n}
            for (s, t), n in pairs.items()
            if n < min_support
        ),
        key=lambda r: r["count"],
    )


def summary(bundle: EventLogBundle) -> dict:
    return {
        "unusual_trace_lengths": len(unusual_trace_lengths(bundle)["cases"]),
        "rare_activities": len(rare_activities(bundle)),
        "long_waits": len(long_waits(bundle)),
        "rare_transitions": len(rare_transitions(bundle)),
    }
