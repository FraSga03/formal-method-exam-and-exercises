import pandas as pd
import pytest

from volvo.domain import CSV_SCHEMA
from volvo.logs.loader import normalize


def make_csv_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SR Number": ["1-1", "1-1", "1-1", "2-2", "2-2"],
            "Change Date+Time": [
                "2013-01-01 10:00:00",
                "2013-01-01 11:00:00",
                "2013-01-01 12:00:00",
                "2013-01-02 09:00:00",
                "2013-01-02 15:00:00",
            ],
            "Status": ["Accepted", "Queued", "Completed", "Accepted", "Completed"],
            "Sub Status": ["In Progress", "Awaiting Assignment", "Closed", "Wait - User", "Closed"],
            "Owner First Name": ["Anne", "Anne", "Bob", "Bob", "Bob"],
            "Impact": ["Medium", "Medium", "Medium", "High", "High"],
            "Product": ["PROD1", "PROD1", "PROD1", "PROD2", "PROD2"],
        }
    )


def test_normalize_builds_xes_standard_columns():
    bundle = normalize(make_csv_frame(), CSV_SCHEMA, "status_substatus", "test")
    for column in ("case:concept:name", "concept:name", "time:timestamp"):
        assert column in bundle.df.columns


def test_normalize_retains_source_attributes():
    bundle = normalize(make_csv_frame(), CSV_SCHEMA, "status_substatus", "test")
    assert "Impact" in bundle.df.columns
    assert "Product" in bundle.df.columns
    assert bundle.df["Impact"].tolist() == ["Medium", "Medium", "Medium", "High", "High"]


def test_normalize_derives_composite_activity():
    bundle = normalize(make_csv_frame(), CSV_SCHEMA, "status_substatus", "test")
    assert bundle.df["concept:name"].iloc[0] == "Accepted+In Progress"
    # 5 events, but Completed+Closed occurs twice
    assert bundle.summary()["unique_activities"] == 4


def test_status_mode_collapses_activities():
    bundle = normalize(make_csv_frame(), CSV_SCHEMA, "status", "test")
    assert bundle.summary()["unique_activities"] == 3


def test_normalize_maps_resource():
    bundle = normalize(make_csv_frame(), CSV_SCHEMA, "status_substatus", "test")
    assert bundle.df["org:resource"].iloc[0] == "Anne"


def test_summary_counts():
    summary = normalize(make_csv_frame(), CSV_SCHEMA, "status_substatus", "test").summary()
    assert summary["total_events"] == 5
    assert summary["unique_cases"] == 2
    assert summary["activities"] == sorted(set(summary["activities"]))


def test_events_are_sorted_within_a_case():
    frame = make_csv_frame().iloc[::-1].reset_index(drop=True)
    bundle = normalize(frame, CSV_SCHEMA, "status_substatus", "test")
    first_case = bundle.df[bundle.df["case:concept:name"] == "1-1"]
    assert first_case["time:timestamp"].is_monotonic_increasing


def test_rows_with_unparseable_timestamps_are_dropped():
    frame = make_csv_frame()
    frame.loc[0, "Change Date+Time"] = "not a date"
    bundle = normalize(frame, CSV_SCHEMA, "status_substatus", "test")
    assert bundle.summary()["total_events"] == 4


def test_empty_frame_raises():
    with pytest.raises(ValueError):
        normalize(make_csv_frame().iloc[0:0], CSV_SCHEMA, "status_substatus", "test")


from pathlib import Path

from volvo.domain import UnknownSchemaError
from volvo.logs.loader import load


def test_load_csv_roundtrip(tmp_path: Path):
    path = tmp_path / "sample.csv"
    make_csv_frame().to_csv(path, index=False)

    bundle = load(path)

    assert bundle.summary()["total_events"] == 5
    assert bundle.summary()["unique_cases"] == 2
    assert bundle.schema.name == "bpi2013-csv"


def test_load_csv_honours_activity_mode(tmp_path: Path):
    path = tmp_path / "sample.csv"
    make_csv_frame().to_csv(path, index=False)

    assert load(path, mode="status").summary()["unique_activities"] == 3
    assert load(path, mode="status_substatus").summary()["unique_activities"] == 4


def test_load_semicolon_delimited_csv(tmp_path: Path):
    path = tmp_path / "sample.csv"
    make_csv_frame().to_csv(path, index=False, sep=";")

    assert load(path).summary()["total_events"] == 5


def test_load_rejects_unknown_columns(tmp_path: Path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"foo": [1], "bar": [2]}).to_csv(path, index=False)

    with pytest.raises(UnknownSchemaError):
        load(path)


def test_load_rejects_unsupported_extension(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text("nope")

    with pytest.raises(ValueError, match="Unsupported"):
        load(path)
