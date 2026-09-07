Log: BPI_Challenge_2013_incidents.xes.gz (7554 cases)

| Property | Formula | Satisfied | Violated | Ratio |
|---|---|---|---|---|
| Termination | `F(completed_closed \| completed_in_call \| completed_resolved \| completed_cancelled)` | 7546 | 8 | 0.999 |
| Resolution | `G(accepted_in_progress -> F(completed_closed \| completed_in_call \| completed_resolved))` | 7545 | 9 | 0.999 |
| No work after closure | `G(completed_closed -> !F(accepted_in_progress))` | 7435 | 119 | 0.984 |
| Queued work is picked up | `G(queued_awaiting_assignment -> F(accepted_in_progress))` | 7494 | 60 | 0.992 |
| Waiting on the user resumes | `G(accepted_wait_user -> F(accepted_in_progress \| completed_resolved \| completed_closed))` | 7550 | 4 | 0.999 |
| No unmatched events | `G(!unmatched_unmatched)` | 7549 | 5 | 0.999 |
| Formal closure | `G(accepted_in_progress -> F(completed_closed))` | 5591 | 1963 | 0.740 |
| Queueing precedes work | `(!accepted_in_progress) U queued_awaiting_assignment` | 1168 | 6386 | 0.155 |

## Counterexamples

### Termination

- case `1-739197171`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Queued+Awaiting Assignment → Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress
- case `1-740358991`: Accepted+In Progress → Accepted+In Progress → Accepted+In Progress → Accepted+Wait - Implementation
- case `1-740364822`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Queued+Awaiting Assignment → Accepted+Wait - User

### Resolution

- case `1-737379684`: Accepted+In Progress → Accepted+In Progress → Accepted+Wait - User → Accepted+In Progress → Completed+In Call → Accepted+In Progress → Completed+Cancelled
- case `1-739197171`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Queued+Awaiting Assignment → Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress
- case `1-740358991`: Accepted+In Progress → Accepted+In Progress → Accepted+In Progress → Accepted+Wait - Implementation

### No work after closure

- case `1-629883996`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress
- case `1-649830550`: Accepted+In Progress → Accepted+In Progress → Accepted+Wait - User → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Accepted+Wait - User → Completed+Resolved
- case `1-656241183`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Completed+Resolved → Completed+Closed → Accepted+In Progress → Queued+Awaiting Assignment

### Queued work is picked up

- case `1-717918204`: Queued+Awaiting Assignment → Accepted+In Progress → Queued+Awaiting Assignment → Completed+Resolved → Completed+Closed
- case `1-717918214`: Queued+Awaiting Assignment → Accepted+In Progress → Queued+Awaiting Assignment → Queued+Awaiting Assignment → Completed+Resolved → Completed+Closed
- case `1-729097375`: Queued+Awaiting Assignment → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Queued+Awaiting Assignment → Completed+Resolved → Completed+Closed

### Waiting on the user resumes

- case `1-740364822`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Queued+Awaiting Assignment → Accepted+Wait - User
- case `1-740538038`: Accepted+In Progress → Accepted+In Progress → Accepted+In Progress → Accepted+Wait - User
- case `1-740782031`: Accepted+In Progress → Accepted+Wait - User → Accepted+Wait - User → Accepted+Wait - Implementation

### No unmatched events

- case `1-722103633`: Accepted+In Progress → Accepted+In Progress → Accepted+Wait - User → Queued+Awaiting Assignment → Accepted+In Progress → Accepted+Wait - User → Accepted+In Progress → Completed+Resolved
- case `1-734778898`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Queued+Awaiting Assignment → Accepted+In Progress → Accepted+Assigned → Accepted+In Progress → Completed+Resolved
- case `1-734873980`: Accepted+In Progress → Accepted+In Progress → Completed+Resolved → Unmatched+Unmatched → Accepted+In Progress → Completed+Resolved → Completed+Closed

### Formal closure

- case `1-583200733`: Accepted+In Progress → Accepted+In Progress → Accepted+Wait - User → Accepted+Wait - User → Accepted+In Progress → Accepted+Wait → Accepted+In Progress → Completed+In Call
- case `1-718038855`: Accepted+In Progress → Accepted+In Progress → Accepted+Wait → Accepted+In Progress → Completed+In Call
- case `1-720600393`: Accepted+In Progress → Accepted+In Progress → Accepted+Wait - User → Accepted+In Progress → Completed+In Call

### Queueing precedes work

- case `1-364285768`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Completed+Resolved → Queued+Awaiting Assignment
- case `1-467153946`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Accepted+Wait - User → Queued+Awaiting Assignment → Accepted+In Progress → Accepted+Wait - Implementation
- case `1-503573772`: Accepted+In Progress → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress → Queued+Awaiting Assignment → Accepted+In Progress

