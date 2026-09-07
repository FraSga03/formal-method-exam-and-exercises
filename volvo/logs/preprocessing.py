"""Log filtering and relabelling. Every function returns a new bundle."""
import pandas as pd
import pm4py

from volvo.logs.loader import ACTIVITY, CASE, TIMESTAMP, EventLogBundle


class PreprocessingError(Exception):
    """Raised when a step would leave no events behind."""


def _rebuild(bundle: EventLogBundle, df: pd.DataFrame, step: str) -> EventLogBundle:
    if df.empty:
        raise PreprocessingError(f"{step} removed every event from {bundle.source}.")
    df = df.sort_values([CASE, TIMESTAMP], kind="stable").reset_index(drop=True)
    return EventLogBundle(
        log=pm4py.convert_to_event_log(df),
        df=df,
        schema=bundle.schema,
        mode=bundle.mode,
        source=bundle.source,
    )


def filter_activities(
    bundle: EventLogBundle, activities: list[str], *, exclude: bool = False
) -> EventLogBundle:
    mask = bundle.df[ACTIVITY].isin(activities)
    if exclude:
        mask = ~mask
    return _rebuild(bundle, bundle.df[mask], "filter_activities")


def filter_time_range(
    bundle: EventLogBundle, start: str | None = None, end: str | None = None
) -> EventLogBundle:
    df = bundle.df
    if start:
        df = df[df[TIMESTAMP] >= pd.Timestamp(start, tz="UTC")]
    if end:
        df = df[df[TIMESTAMP] <= pd.Timestamp(end, tz="UTC")]
    return _rebuild(bundle, df, "filter_time_range")


def drop_duplicate_events(bundle: EventLogBundle) -> EventLogBundle:
    df = bundle.df.drop_duplicates(subset=[CASE, ACTIVITY, TIMESTAMP])
    return _rebuild(bundle, df, "drop_duplicate_events")


def filter_case_length(
    bundle: EventLogBundle, min_events: int = 1, max_events: int | None = None
) -> EventLogBundle:
    sizes = bundle.df.groupby(CASE)[ACTIVITY].transform("size")
    mask = sizes >= min_events
    if max_events is not None:
        mask &= sizes <= max_events
    return _rebuild(bundle, bundle.df[mask], "filter_case_length")


def generalize_activities(
    bundle: EventLogBundle, mapping: dict[str, str]
) -> EventLogBundle:
    df = bundle.df.copy()
    df[ACTIVITY] = df[ACTIVITY].map(lambda a: mapping.get(a, a))
    return _rebuild(bundle, df, "generalize_activities")
