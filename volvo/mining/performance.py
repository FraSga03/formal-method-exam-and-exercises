"""Time and variant analysis straight from the log. No discovered model needed."""
from collections import Counter

import pandas as pd

from volvo.logs.loader import ACTIVITY, CASE, TIMESTAMP, EventLogBundle

HOUR = 3600.0


def _with_waiting(bundle: EventLogBundle) -> pd.DataFrame:
    df = bundle.df.sort_values([CASE, TIMESTAMP], kind="stable")
    gap = df.groupby(CASE)[TIMESTAMP].shift(-1) - df[TIMESTAMP]
    df = df.assign(wait_hours=gap.dt.total_seconds() / HOUR)
    return df.dropna(subset=["wait_hours"])


def waiting_times(bundle: EventLogBundle) -> pd.DataFrame:
    """Hours between each event and the next one in its case, grouped by activity."""
    waits = _with_waiting(bundle)
    if waits.empty:
        return pd.DataFrame(
            columns=["count", "mean_hours", "median_hours", "max_hours", "total_hours"]
        )

    table = waits.groupby(ACTIVITY)["wait_hours"].agg(
        count="count", mean_hours="mean", median_hours="median",
        max_hours="max", total_hours="sum",
    )
    table.index.name = "activity"
    return table.sort_values("mean_hours", ascending=False)


def case_durations(bundle: EventLogBundle) -> pd.Series:
    spans = bundle.df.groupby(CASE)[TIMESTAMP].agg(["min", "max"])
    return ((spans["max"] - spans["min"]).dt.total_seconds() / HOUR).rename("hours")


def duration_summary(bundle: EventLogBundle) -> dict:
    durations = case_durations(bundle)
    return {
        "cases": int(len(durations)),
        "mean_hours": float(durations.mean()),
        "median_hours": float(durations.median()),
        "p95_hours": float(durations.quantile(0.95)),
        "max_hours": float(durations.max()),
    }


def _traces(bundle: EventLogBundle) -> pd.Series:
    df = bundle.df.sort_values([CASE, TIMESTAMP], kind="stable")
    return df.groupby(CASE, sort=False)[ACTIVITY].apply(tuple)


def variants(bundle: EventLogBundle, top: int = 20) -> list[dict]:
    counts = Counter(_traces(bundle))
    total = sum(counts.values())
    return [
        {"variant": variant, "count": count, "share": count / total}
        for variant, count in counts.most_common(top)
    ]


def variant_summary(bundle: EventLogBundle) -> dict:
    counts = Counter(_traces(bundle))
    cases = sum(counts.values())
    singletons = sum(1 for c in counts.values() if c == 1)
    top10 = sum(c for _, c in counts.most_common(10))
    return {
        "distinct_variants": len(counts),
        "cases": cases,
        "variant_ratio": len(counts) / cases,
        "singleton_share": singletons / len(counts),
        "top10_coverage": top10 / cases,
    }
