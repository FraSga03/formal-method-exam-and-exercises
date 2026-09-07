# BPI Challenge 2013 — Volvo IT Belgium (VINST)

Three event logs from Volvo IT's incident and problem management system.
Published by 4TU.ResearchData / figshare. Not committed to this repository.

Fetch with `uv run python scripts/fetch_data.py`, which resolves the download
URLs through the figshare API (file ids change between platform migrations).

## Verified shape

Loaded via `volvo.logs.loader.load` with the default `status_substatus` mode.
Case and event counts match the published figures.

| Log | Cases | Events | Activities | Range | File |
|---|---|---|---|---|---|
| Incidents | 7,554 | 65,533 | 13 | 2010-03-31 → 2012-05-22 | `raw/BPI_Challenge_2013_incidents.xes.gz` |
| Open problems | 819 | 2,351 | 5 | 2006-11-07 → 2012-06-15 | `raw/BPI_Challenge_2013_open_problems.xes.gz` |
| Closed problems | 1,487 | 6,660 | 7 | 2006-01-11 → 2012-05-31 | `raw/BPI_Challenge_2013_closed_problems.xes.gz` |

All three use the XES schema (`volvo.domain.XES_SCHEMA`): the activity label is
derived from `concept:name` (Status) and `lifecycle:transition` (Sub Status).
There is no activity column.

## Incident activity alphabet

```
Accepted+Assigned              Accepted+Wait - User        Completed+In Call
Accepted+In Progress           Accepted+Wait - Vendor      Completed+Resolved
Accepted+Wait                  Completed+Cancelled         Queued+Awaiting Assignment
Accepted+Wait - Customer       Completed+Closed            Unmatched+Unmatched
```

Under `mode="status"` this collapses to four activities and the discovered model
becomes trivial — the comparison is a reportable finding, not a bug.

## Quirks

- `open_problems` misspells a column as `oranization country` in the source data.
  It is carried through verbatim; do not "fix" it silently.
- `Unmatched+Unmatched` is a data-quality artifact of the VINST export, not a
  real process step.
