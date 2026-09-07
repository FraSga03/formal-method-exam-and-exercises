
# BPI_Challenge_2013_closed_problems.xes.gz

- cases: 1487, distinct variants: 327 (22.0%)
- case duration: median 1968.5 h, p95 15836.5 h, max 54116.4 h
- health: 65.9/100 (grade D)
    - completion: 1.000
    - rework: 0.655
    - standardisation: 0.780
    - throughput: 0.000

## Waiting time after each activity (hours)

| Activity | n | mean | median | max |
|---|---|---|---|---|
| Unmatched+Unmatched | 10 | 12896.20 | 15829.77 | 23016.73 |
| Accepted+Assigned | 614 | 3228.40 | 1044.45 | 23396.54 |
| Accepted+Wait | 527 | 2198.49 | 817.25 | 18505.73 |
| Accepted+In Progress | 3066 | 857.53 | 0.15 | 28153.21 |
| Queued+Awaiting Assignment | 875 | 521.36 | 11.98 | 54116.07 |
| Completed+Closed | 78 | 357.37 | 66.62 | 4009.12 |
| Completed+Cancelled | 3 | 333.56 | 15.36 | 982.69 |

## Anomalies

- unusual_trace_lengths: 78
- rare_activities: 2
- long_waits: 50
- rare_transitions: 2

## Insights

- **high** Heavy rework — Only 65% of events are a first occurrence of their activity within the case.
- **medium** Slow throughput — Median case duration is 1969 hours.

## Most likely next activity

- Accepted+Assigned -> Accepted+In Progress (62.5%)
- Accepted+In Progress -> Completed+Closed (41.3%)
- Accepted+Wait -> Completed+Closed (49.7%)
- Completed+Cancelled -> Accepted+In Progress (100.0%)
- Completed+Closed -> Accepted+In Progress (100.0%)
- Queued+Awaiting Assignment -> Accepted+In Progress (84.3%)
- Unmatched+Unmatched -> Completed+Closed (50.0%)

# BPI_Challenge_2013_incidents.xes.gz

- cases: 7554, distinct variants: 2278 (30.2%)
- case duration: median 181.2 h, p95 856.6 h, max 18512.4 h
- health: 74.4/100 (grade C)
    - completion: 0.999
    - rework: 0.481
    - standardisation: 0.698
    - throughput: 0.748

## Waiting time after each activity (hours)

| Activity | n | mean | median | max |
|---|---|---|---|---|
| Completed+Closed | 143 | 143.31 | 95.28 | 736.50 |
| Accepted+Wait - Vendor | 313 | 131.63 | 28.15 | 1633.67 |
| Accepted+Wait - Implementation | 491 | 130.22 | 26.00 | 3500.55 |
| Accepted+Wait - Customer | 101 | 115.45 | 54.39 | 1488.93 |
| Completed+Resolved | 6025 | 114.15 | 176.25 | 192.10 |
| Accepted+Wait - User | 4214 | 109.97 | 26.36 | 5059.88 |
| Accepted+Wait | 1533 | 97.99 | 3.45 | 4992.31 |
| Completed+In Call | 153 | 70.88 | 1.56 | 677.31 |
| Accepted+Assigned | 3220 | 36.31 | 1.36 | 17334.07 |
| Queued+Awaiting Assignment | 11544 | 26.16 | 0.59 | 6838.52 |
| Accepted+In Progress | 30237 | 10.63 | 0.03 | 7896.28 |
| Unmatched+Unmatched | 5 | 0.19 | 0.07 | 0.61 |

## Anomalies

- unusual_trace_lengths: 366
- rare_activities: 5
- long_waits: 50
- rare_transitions: 4

## Insights

- **high** Heavy rework — Only 48% of events are a first occurrence of their activity within the case.

## Most likely next activity

- Accepted+Assigned -> Accepted+In Progress (96.5%)
- Accepted+In Progress -> Queued+Awaiting Assignment (28.0%)
- Accepted+Wait -> Accepted+In Progress (33.5%)
- Accepted+Wait - Customer -> Completed+Resolved (37.6%)
- Accepted+Wait - Implementation -> Accepted+In Progress (34.8%)
- Accepted+Wait - User -> Accepted+In Progress (36.1%)
- Accepted+Wait - Vendor -> Completed+Resolved (38.3%)
- Completed+Closed -> Accepted+In Progress (77.6%)
- Completed+In Call -> Accepted+In Progress (88.9%)
- Completed+Resolved -> Completed+Closed (94.7%)
- Queued+Awaiting Assignment -> Accepted+In Progress (92.7%)
- Unmatched+Unmatched -> Accepted+In Progress (100.0%)

# BPI_Challenge_2013_open_problems.xes.gz

- cases: 819, distinct variants: 182 (22.2%)
- case duration: median 41.5 h, p95 7779.3 h, max 42260.1 h
- health: 70.0/100 (grade D)
    - completion: 0.435
    - rework: 0.746
    - standardisation: 0.778
    - throughput: 0.942

## Waiting time after each activity (hours)

| Activity | n | mean | median | max |
|---|---|---|---|---|
| Accepted+Wait | 134 | 2647.94 | 608.46 | 17089.55 |
| Accepted+Assigned | 128 | 874.03 | 133.40 | 16451.74 |
| Accepted+In Progress | 949 | 586.44 | 0.20 | 26905.31 |
| Queued+Awaiting Assignment | 290 | 421.14 | 18.35 | 12666.38 |
| Completed+Closed | 31 | 272.56 | 75.21 | 1696.89 |

## Anomalies

- unusual_trace_lengths: 32
- rare_activities: 0
- long_waits: 50
- rare_transitions: 1

## Insights

- **high** Cases do not reach completion — 356 of 819 cases end in a Completed status.

## Most likely next activity

- Accepted+Assigned -> Accepted+In Progress (54.7%)
- Accepted+In Progress -> Completed+Closed (33.5%)
- Accepted+Wait -> Completed+Closed (44.0%)
- Completed+Closed -> Accepted+In Progress (96.8%)
- Queued+Awaiting Assignment -> Accepted+In Progress (69.0%)
