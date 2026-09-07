"""A single comparison score for a log.

The weights and the 30-day throughput horizon are arbitrary but fixed. The score
compares logs and activity modes against each other; it is not an absolute verdict.
"""
from volvo.logs.loader import EventLogBundle
from volvo.mining.performance import _traces, duration_summary, variant_summary

WEIGHTS = {"completion": 0.30, "rework": 0.25, "standardisation": 0.25, "throughput": 0.20}
THROUGHPUT_HORIZON_HOURS = 720.0
GRADES = ((90, "A"), (80, "B"), (70, "C"), (60, "D"))


def _components(bundle: EventLogBundle) -> tuple[dict, dict]:
    traces = _traces(bundle)
    variant = variant_summary(bundle)
    duration = duration_summary(bundle)

    completed = sum(1 for t in traces if t and t[-1].startswith("Completed"))
    events = sum(len(t) for t in traces)
    first_occurrences = sum(len(set(t)) for t in traces)

    components = {
        "completion": completed / len(traces),
        "rework": first_occurrences / events,
        "standardisation": 1.0 - variant["variant_ratio"],
        "throughput": 1.0
        - min(1.0, duration["median_hours"] / THROUGHPUT_HORIZON_HOURS),
    }
    metrics = {
        "cases": variant["cases"],
        "events": events,
        "distinct_variants": variant["distinct_variants"],
        "median_hours": duration["median_hours"],
        "completed_cases": completed,
    }
    return components, metrics


def health_score(bundle: EventLogBundle) -> dict:
    components, metrics = _components(bundle)
    score = 100.0 * sum(components[k] * w for k, w in WEIGHTS.items())
    grade = next((g for threshold, g in GRADES if score >= threshold), "F")
    return {"score": score, "grade": grade, "components": components, "metrics": metrics}


def insights(bundle: EventLogBundle) -> list[dict]:
    components, metrics = _components(bundle)
    found = []

    if components["completion"] < 0.95:
        found.append({
            "severity": "high",
            "title": "Cases do not reach completion",
            "detail": f"{metrics['completed_cases']} of {metrics['cases']} cases end in a "
                      f"Completed status.",
        })
    if components["rework"] < 0.7:
        found.append({
            "severity": "high",
            "title": "Heavy rework",
            "detail": f"Only {components['rework']:.0%} of events are a first occurrence of "
                      f"their activity within the case.",
        })
    if components["standardisation"] < 0.5:
        found.append({
            "severity": "medium",
            "title": "Low standardisation",
            "detail": f"{metrics['distinct_variants']} distinct variants across "
                      f"{metrics['cases']} cases.",
        })
    if components["throughput"] < 0.5:
        found.append({
            "severity": "medium",
            "title": "Slow throughput",
            "detail": f"Median case duration is {metrics['median_hours']:.0f} hours.",
        })
    return found
