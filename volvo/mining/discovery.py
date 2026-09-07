"""Process discovery over a loaded log. Stateless: log in, result out."""
import uuid
from dataclasses import dataclass, field
from typing import Literal

import pm4py
from pm4py.objects.petri_net.obj import Marking, PetriNet

from volvo.config import OUTPUT_DIR
from volvo.logs.loader import EventLogBundle

Algorithm = Literal["alpha", "heuristics", "inductive"]
ALGORITHMS: tuple[Algorithm, ...] = ("alpha", "heuristics", "inductive")


@dataclass
class DiscoveryResult:
    algorithm: Algorithm
    net: PetriNet
    initial_marking: Marking
    final_marking: Marking
    params: dict = field(default_factory=dict)
    image_path: str | None = None

    def statistics(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "num_places": len(self.net.places),
            "num_transitions": len(self.net.transitions),
            "num_arcs": len(self.net.arcs),
            "num_silent_transitions": sum(
                1 for t in self.net.transitions if t.label is None
            ),
            "params": dict(self.params),
        }


def _render(result: DiscoveryResult) -> str:
    path = OUTPUT_DIR / f"{result.algorithm}_{uuid.uuid4().hex[:8]}.png"
    pm4py.save_vis_petri_net(
        result.net, result.initial_marking, result.final_marking, str(path)
    )
    return str(path)


def discover(
    bundle: EventLogBundle,
    algorithm: Algorithm = "inductive",
    *,
    render: bool = True,
    **params,
) -> DiscoveryResult:
    """Discover a Petri net. Unknown algorithms raise rather than defaulting."""
    log = bundle.log

    if algorithm == "alpha":
        used: dict = {}
        net, im, fm = pm4py.discover_petri_net_alpha(log)
    elif algorithm == "heuristics":
        used = {"dependency_threshold": params.get("dependency_threshold", 0.5)}
        net, im, fm = pm4py.discover_petri_net_heuristics(log, **used)
    elif algorithm == "inductive":
        used = {"noise_threshold": params.get("noise_threshold", 0.0)}
        net, im, fm = pm4py.discover_petri_net_inductive(log, **used)
    else:
        raise ValueError(f"Unknown algorithm {algorithm!r}. Expected one of {ALGORITHMS}.")

    result = DiscoveryResult(
        algorithm=algorithm,
        net=net,
        initial_marking=im,
        final_marking=fm,
        params=used,
    )
    if render:
        result.image_path = _render(result)
    return result
