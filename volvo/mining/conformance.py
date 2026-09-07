"""Conformance checking on a discovered model.

Alignment-based metrics are exact but do not finish on the full incidents log
(65k events), so every entry point takes an explicit case cap.
"""
from dataclasses import asdict, dataclass

import pm4py
from pm4py.objects.log.obj import EventLog

from volvo.logs.loader import EventLogBundle
from volvo.mining.discovery import DiscoveryResult

DEFAULT_MAX_CASES = 1000


@dataclass
class ConformanceMetrics:
    fitness: float
    precision: float
    generalization: float
    simplicity: float
    method: str
    sampled_cases: int | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def sample_log(bundle: EventLogBundle, max_cases: int) -> EventLog:
    """Return at most `max_cases` traces, taken from the front for determinism."""
    log = bundle.log
    if len(log) <= max_cases:
        return log
    return EventLog(log[:max_cases])


def evaluate(
    bundle: EventLogBundle,
    result: DiscoveryResult,
    *,
    method: str = "token",
    max_cases: int = DEFAULT_MAX_CASES,
) -> ConformanceMetrics:
    """Score a discovered model on the four standard dimensions."""
    if method not in ("token", "alignment"):
        raise ValueError(f"Unknown method {method!r}. Expected 'token' or 'alignment'.")

    log = sample_log(bundle, max_cases)
    net, im, fm = result.net, result.initial_marking, result.final_marking

    if method == "token":
        fitness = pm4py.fitness_token_based_replay(log, net, im, fm)["log_fitness"]
        precision = pm4py.precision_token_based_replay(log, net, im, fm)
    else:
        fitness = pm4py.fitness_alignments(log, net, im, fm)["log_fitness"]
        precision = pm4py.precision_alignments(log, net, im, fm)

    return ConformanceMetrics(
        fitness=float(fitness),
        precision=float(precision),
        generalization=float(pm4py.generalization_tbr(log, net, im, fm)),
        simplicity=float(pm4py.simplicity_petri_net(net, im, fm)),
        method=method,
        sampled_cases=len(log),
    )
