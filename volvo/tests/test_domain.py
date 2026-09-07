import pytest

from volvo.domain import (
    CSV_SCHEMA,
    XES_SCHEMA,
    UnknownSchemaError,
    derive_activity,
    detect_schema,
)


def test_detects_csv_schema():
    columns = ["SR Number", "Change Date+Time", "Status", "Sub Status", "Impact"]
    assert detect_schema(columns) is CSV_SCHEMA


def test_detects_xes_schema():
    columns = ["case:concept:name", "concept:name", "lifecycle:transition", "time:timestamp"]
    assert detect_schema(columns) is XES_SCHEMA


def test_unknown_schema_reports_the_columns_it_saw():
    with pytest.raises(UnknownSchemaError) as excinfo:
        detect_schema(["foo", "bar"])
    assert "foo" in str(excinfo.value)
    assert "bar" in str(excinfo.value)


def test_derive_activity_combines_status_and_substatus():
    assert derive_activity("Accepted", "In Progress", "status_substatus") == "Accepted+In Progress"


def test_derive_activity_status_only():
    assert derive_activity("Accepted", "In Progress", "status") == "Accepted"


def test_derive_activity_substatus_only():
    assert derive_activity("Accepted", "In Progress", "substatus") == "In Progress"


def test_derive_activity_tolerates_missing_substatus():
    assert derive_activity("Accepted", None, "status_substatus") == "Accepted"
    assert derive_activity("Accepted", "", "status_substatus") == "Accepted"


def test_derive_activity_strips_whitespace():
    assert derive_activity(" Accepted ", " In Progress ", "status_substatus") == "Accepted+In Progress"
