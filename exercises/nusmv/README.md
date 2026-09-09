# NuSMV models

Three models. Two are reachability puzzles solved by refuting a reachability
negation and reading the counterexample as the solution; the third is a
concurrency protocol with safety, liveness and livelock properties.

## Running

```bash
./check.sh                 # all models
./check.sh peterson.smv    # one model
NUSMV=/path/to/NuSMV ./check.sh
```

## `missionaries_and_cannibals.smv`

Three missionaries and three cannibals, a boat for one or two, and cannibals
may never outnumber missionaries on a bank.

| Specification | Result | Meaning |
|---|---|---|
| `INVARSPEC safe` | true | vacuous under `INVAR safe`; states the intent |
| `!EF goal` | **false** | the counterexample is the eleven-crossing solution |
| `AG EF goal` | true | no safe state is a dead end |
| `AG EF start` | true | every crossing is reversible |

## `bridges.smv`

The seven bridges of Konigsberg, plus an eighth as a frozen variable. Degrees
without it: A 5, B 3, C 3, D 3 — four odd vertices, so no Eulerian path. With
the eighth bridge between B and C: A 5, B 4, C 4, D 3 — two odd vertices, so a
path exists and must start at A or D.

| Specification | Result | Meaning |
|---|---|---|
| `crossed <= (B8_PRESENT ? 8 : 7)` | true | no bridge is crossed twice |
| `!B8_PRESENT -> !EF all_crossed` | true | Euler's result |
| `!B8_PRESENT -> EF crossed = 6` | true | six of seven is the best possible |
| `B8_PRESENT -> ((LOCATION = lA \| LOCATION = lD) -> EF all_crossed)` | true | from an odd-degree vertex the walk exists |
| `B8_PRESENT -> ((LOCATION = lB \| LOCATION = lC) -> !EF all_crossed)` | true | from an even-degree vertex it does not |
| `!(B8_PRESENT & EF all_crossed)` | **false** | the counterexample is the Eulerian path |

## `peterson.smv`

Peterson's mutual exclusion for two processes. `FAIRNESS sched = 0/1` stops the scheduler from
starving a process. The frozen `BUGGY` drops the `turn` test from the entry
guard.

| Specification | Result | Meaning |
|---|---|---|
| `!(pc0 = crit & pc1 = crit)` | true | mutual exclusion, both variants |
| `!BUGGY -> G (pc0 = want -> F pc0 = crit)` | true | no starvation |
| `!BUGGY -> G (pc1 = want -> F pc1 = crit)` | true | no starvation |
| `!BUGGY -> AG EF pc0 = crit` | true | no dead end |
| `BUGGY -> EF AG !(pc0 = crit)` | true | without `turn`, both flags up livelocks — every state still has a successor, so it's not a deadlock |
