"""Load BPI 2013 logs into an attribute-preserving bundle."""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pm4py
from pm4py.objects.log.obj import EventLog

from volvo.domain import (
    DEFAULT_ACTIVITY_MODE,
    ActivityMode,
    LogSchema,
    derive_activity,
    detect_schema,
)

CASE = "case:concept:name"
ACTIVITY = "concept:name"
TIMESTAMP = "time:timestamp"
RESOURCE = "org:resource"


@dataclass
class EventLogBundle:
    """A loaded log plus the full source frame.

    The reference project keeps only three columns; every downstream
    organizational analysis needs the rest, so both are carried together.
    """

    log: EventLog
    df: pd.DataFrame
    schema: LogSchema
    mode: ActivityMode
    source: str

    def summary(self) -> dict:
        activities = sorted(self.df[ACTIVITY].unique().tolist())
        return {
            "source": self.source,
            "schema": self.schema.name,
            "activity_mode": self.mode,
            "total_events": int(len(self.df)),
            "unique_cases": int(self.df[CASE].nunique()),
            "unique_activities": len(activities),
            "activities": activities,
            "time_range": (
                str(self.df[TIMESTAMP].min()),
                str(self.df[TIMESTAMP].max()),
            ),
            "top_activities": self.df[ACTIVITY].value_counts().head(20).to_dict(),
            "retained_columns": sorted(self.df.columns.tolist()),
        }


def normalize(
    df: pd.DataFrame,
    schema: LogSchema,
    mode: ActivityMode,
    source: str,
) -> EventLogBundle:
    """Add XES-standard columns to a raw frame without dropping anything."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    df[TIMESTAMP] = pd.to_datetime(df[schema.timestamp], errors="coerce", utc=True)
    df = df.dropna(subset=[TIMESTAMP])
    if df.empty:
        raise ValueError(
            f"No rows with a parseable '{schema.timestamp}' remained in {source}."
        )

    df[CASE] = df[schema.case_id].astype(str)

    substatus = (
        df[schema.substatus]
        if schema.substatus and schema.substatus in df.columns
        else pd.Series([None] * len(df), index=df.index)
    )
    df[ACTIVITY] = [
        derive_activity(s, ss, mode) for s, ss in zip(df[schema.status], substatus)
    ]

    if schema.resource and schema.resource in df.columns:
        df[RESOURCE] = df[schema.resource].astype(str)

    df = df.sort_values([CASE, TIMESTAMP], kind="stable").reset_index(drop=True)

    log = pm4py.convert_to_event_log(df)
    return EventLogBundle(log=log, df=df, schema=schema, mode=mode, source=source)


def _read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV, trying the delimiters the dataset is distributed with."""
    errors = []
    for delimiter in (",", ";", "\t", "|"):
        try:
            df = pd.read_csv(path, sep=delimiter, encoding="utf-8-sig", low_memory=False)
        except Exception as exc:  # noqa: BLE001 - reported below if all fail
            errors.append(f"{delimiter!r}: {exc}")
            continue
        if df.shape[1] > 1:
            return df
    raise ValueError(f"Could not parse {path} with any known delimiter. {errors}")


def load(path: str | Path, mode: ActivityMode = DEFAULT_ACTIVITY_MODE) -> EventLogBundle:
    """Load an XES or CSV BPI 2013 log."""
    path = Path(path)
    suffixes = {s.lower() for s in path.suffixes}

    if ".xes" in suffixes:
        df = pm4py.read_xes(str(path))
    elif ".csv" in suffixes:
        df = _read_csv(path)
    else:
        raise ValueError(
            f"Unsupported file type {path.suffix!r}. Expected .csv, .xes or .xes.gz."
        )

    schema = detect_schema(df.columns)
    return normalize(df, schema, mode, source=path.name)
