"""Declared schema for the BPI Challenge 2013 Volvo IT (VINST) logs.

The dataset ships in two shapes: a CSV export with human-readable headers, and
XES where the activity is split across concept:name and lifecycle:transition.
Both are declared here rather than guessed at load time.
"""
from dataclasses import dataclass
from typing import Iterable, Literal

ActivityMode = Literal["status", "substatus", "status_substatus"]
DEFAULT_ACTIVITY_MODE: ActivityMode = "status_substatus"


class UnknownSchemaError(Exception):
    """Raised when a log's columns match no declared schema."""


@dataclass(frozen=True)
class LogSchema:
    name: str
    case_id: str
    timestamp: str
    status: str
    substatus: str | None
    resource: str | None
    attributes: tuple[str, ...]

    @property
    def required(self) -> tuple[str, ...]:
        return (self.case_id, self.timestamp, self.status)


CSV_SCHEMA = LogSchema(
    name="bpi2013-csv",
    case_id="SR Number",
    timestamp="Change Date+Time",
    status="Status",
    substatus="Sub Status",
    resource="Owner First Name",
    attributes=(
        "Involved ST Function Div",
        "Involved Org line 3",
        "Involved ST",
        "Country",
        "Owner Country",
        "Impact",
        "Product",
        "Resource Country",
    ),
)

XES_SCHEMA = LogSchema(
    name="bpi2013-xes",
    case_id="case:concept:name",
    timestamp="time:timestamp",
    status="concept:name",
    substatus="lifecycle:transition",
    resource="org:resource",
    attributes=(
        "org:group",
        "org:role",
        "organization involved",
        "organization country",
        "resource country",
        "impact",
        "product",
    ),
)

SCHEMAS = (CSV_SCHEMA, XES_SCHEMA)

# Union of the composite labels across the three BPI 2013 logs. A single log
# carries only part of it, so verification uses this to tell an activity that is
# merely absent from a typo.
VINST_ACTIVITIES: tuple[str, ...] = (
    "Accepted+Assigned",
    "Accepted+In Progress",
    "Accepted+Wait",
    "Accepted+Wait - Customer",
    "Accepted+Wait - Implementation",
    "Accepted+Wait - User",
    "Accepted+Wait - Vendor",
    "Completed+Cancelled",
    "Completed+Closed",
    "Completed+In Call",
    "Completed+Resolved",
    "Queued+Awaiting Assignment",
    "Unmatched+Unmatched",
)


def detect_schema(columns: Iterable[str]) -> LogSchema:
    """Return the schema whose required columns are all present."""
    present = {str(c).strip() for c in columns}
    for schema in SCHEMAS:
        if all(col in present for col in schema.required):
            return schema
    raise UnknownSchemaError(
        f"No declared schema matches these columns: {sorted(present)}. "
        f"Expected one of: {[s.required for s in SCHEMAS]}"
    )


def derive_activity(status: str, substatus: str | None, mode: ActivityMode) -> str:
    """Build the activity label. BPI 2013 has no activity column."""
    status = str(status).strip() if status is not None else ""
    substatus = str(substatus).strip() if substatus is not None else ""

    if mode == "status":
        return status
    if mode == "substatus":
        return substatus or status
    if not substatus:
        return status
    return f"{status}+{substatus}"
