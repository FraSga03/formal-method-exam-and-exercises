# NuSMV Verification Models

Formal verification models developed in NuSMV covering reachability problem-solving and concurrent protocol verification. Puzzles are solved by negating the target goal, allowing NuSMV's counterexample generator to synthesize the valid sequence of transitions.

## Running Verification

```bash
# Verify all models
./check.sh

# Verify a single model
./check.sh peterson.smv

# Explicit binary path
NUSMV=/path/to/NuSMV ./check.sh
```

## Missionaries and Cannibals (`missionaries_and_cannibals.smv`)

Models the classical river-crossing problem for three missionaries and three cannibals with a two-person boat. The safety invariant forbids cannibals from outnumbering missionaries on either bank whenever missionaries are present.

| Specification | Result | Interpretation |
|---|---|---|
| `INVARSPEC safe` | true | Confirms the state space respects the bank-balance invariant |
| `!EF goal` | **false** | Refuted: the generated counterexample trace provides the minimal 11-step solution |
| `AG EF goal` | true | The goal state remains reachable from every reachable valid configuration |
| `AG EF start` | true | Every transition sequence is reversible back to the initial state |

## Seven Bridges of Königsberg (`bridges.smv`)

Formalizes the Königsberg bridge problem with an optional eighth bridge modeled as a frozen boolean variable (`B8_PRESENT`). 

- **Without the 8th bridge**: vertices A, B, C, D have degrees 5, 3, 3, 3 respectively. Having four vertices of odd degree precludes an Eulerian path.
- **With the 8th bridge (B–C)**: degrees become A: 5, B: 4, C: 4, D: 3. With exactly two odd vertices, an Eulerian path exists and must start at either A or D.

| Specification | Result | Interpretation |
|---|---|---|
| `crossed <= (B8_PRESENT ? 8 : 7)` | true | Traversal terminates before reusing any bridge |
| `!B8_PRESENT -> !EF all_crossed` | true | Verifies Euler's theorem: complete traversal is impossible on the 7-bridge graph |
| `!B8_PRESENT -> EF crossed = 6` | true | Confirms that at most six distinct bridges can be traversed |
| `B8_PRESENT -> ((LOCATION = lA \| LOCATION = lD) -> EF all_crossed)` | true | A full path is reachable when starting from an odd-degree vertex |
| `B8_PRESENT -> ((LOCATION = lB \| LOCATION = lC) -> !EF all_crossed)` | true | Traversal cannot be completed starting from an even-degree vertex |
| `!(B8_PRESENT & EF all_crossed)` | **false** | Refuted: counterexample trace provides the Eulerian path |

## Peterson's Mutual Exclusion (`peterson.smv`)

Evaluates Peterson's two-process mutual exclusion algorithm. A fairness constraint (`FAIRNESS sched = 0/1`) guarantees fair interleaving. A frozen variable (`BUGGY`) enables ablation of the `turn` variable from the entry guard to observe concurrency failures.

| Specification | Result | Interpretation |
|---|---|---|
| `!(pc0 = crit & pc1 = crit)` | true | Mutual exclusion holds across both standard and buggy variants |
| `!BUGGY -> G (pc0 = want -> F pc0 = crit)` | true | Starvation-free: process 0 entering the intent state eventually enters critical |
| `!BUGGY -> G (pc1 = want -> F pc1 = crit)` | true | Starvation-free: process 1 entering the intent state eventually enters critical |
| `!BUGGY -> AG EF pc0 = crit` | true | The critical section remains reachable from all reachable configurations |
| `BUGGY -> EF AG !(pc0 = crit)` | true | Without `turn`, concurrent contention causes livelock where neither process advances |
