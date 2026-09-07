"""Run every discovery algorithm and score them side by side."""
from volvo.logs.loader import EventLogBundle
from volvo.mining.conformance import DEFAULT_MAX_CASES, evaluate
from volvo.mining.discovery import ALGORITHMS, discover


def compare_algorithms(
    bundle: EventLogBundle,
    *,
    render: bool = False,
    max_cases: int = DEFAULT_MAX_CASES,
) -> list[dict]:
    """One row per algorithm. A failure in one is reported, not raised."""
    rows = []
    for algorithm in ALGORITHMS:
        try:
            result = discover(bundle, algorithm, render=render)
            metrics = evaluate(bundle, result, max_cases=max_cases)
            rows.append(
                {
                    "algorithm": algorithm,
                    **{
                        k: v
                        for k, v in metrics.as_dict().items()
                        if k not in ("method", "sampled_cases")
                    },
                    "num_places": len(result.net.places),
                    "num_transitions": len(result.net.transitions),
                    "num_arcs": len(result.net.arcs),
                    "image_path": result.image_path,
                    "error": None,
                }
            )
        except Exception as exc:  # noqa: BLE001 - surfaced in the table
            rows.append(
                {
                    "algorithm": algorithm,
                    "fitness": None,
                    "precision": None,
                    "generalization": None,
                    "simplicity": None,
                    "num_places": None,
                    "num_transitions": None,
                    "num_arcs": None,
                    "image_path": None,
                    "error": str(exc),
                }
            )
    return rows
