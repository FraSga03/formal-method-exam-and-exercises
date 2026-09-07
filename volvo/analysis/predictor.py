"""First-order Markov model over activity transitions."""
from collections import Counter, defaultdict

import pandas as pd

from volvo.logs.loader import ACTIVITY, EventLogBundle
from volvo.mining.performance import _traces


class UnknownActivityError(Exception):
    """Raised when predicting from an activity the log never contained."""


class MarkovModel:
    def __init__(self, transitions: dict[str, Counter], activities: tuple[str, ...]):
        self._transitions = transitions
        self.activities = activities

    @classmethod
    def fit(cls, bundle: EventLogBundle) -> "MarkovModel":
        transitions: dict[str, Counter] = defaultdict(Counter)
        for trace in _traces(bundle):
            for source, target in zip(trace, trace[1:]):
                transitions[source][target] += 1
        activities = tuple(sorted(bundle.df[ACTIVITY].unique().tolist()))
        return cls(dict(transitions), activities)

    def predict_next(self, activity: str, top_k: int = 3) -> list[dict]:
        if activity not in self.activities:
            raise UnknownActivityError(
                f"{activity!r} does not occur in this log. Known: {list(self.activities)}"
            )
        successors = self._transitions.get(activity)
        if not successors:
            return []
        total = sum(successors.values())
        return [
            {"activity": target, "probability": count / total}
            for target, count in successors.most_common(top_k)
        ]

    def transition_matrix(self) -> pd.DataFrame:
        matrix = pd.DataFrame(
            0.0, index=list(self.activities), columns=list(self.activities)
        )
        for source, successors in self._transitions.items():
            total = sum(successors.values())
            for target, count in successors.items():
                matrix.loc[source, target] = count / total
        return matrix

    def predict_sequence(self, start: str, length: int = 5) -> list[str]:
        """Greedy walk along the most likely successor. Stops at a terminal activity."""
        sequence = [start]
        current = start
        while len(sequence) < length:
            top = self.predict_next(current, top_k=1)
            if not top:
                break
            current = top[0]["activity"]
            sequence.append(current)
        return sequence
