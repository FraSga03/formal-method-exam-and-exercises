"""LTLf verification over event logs, backed by flloat.

Activity labels such as "Accepted+In Progress" are not valid proposition
symbols, so everything is verified in a symbol alphabet and translated back for
display.
"""
import re
from dataclasses import dataclass, field

from flloat.parser.ltlf import LTLfParser

from volvo.domain import VINST_ACTIVITIES
from volvo.logs.loader import ACTIVITY, CASE, EventLogBundle

_NON_IDENTIFIER = re.compile(r"[^a-z0-9]+")


def to_symbol(activity: str) -> str:
    """Turn an activity label into a valid LTLf proposition symbol."""
    symbol = _NON_IDENTIFIER.sub("_", str(activity).lower()).strip("_")
    if not symbol:
        symbol = "empty"
    if symbol[0].isdigit():
        symbol = f"a_{symbol}"
    return symbol


class Alphabet:
    """Bidirectional activity <-> proposition mapping for one log."""

    def __init__(self, activities):
        self.mapping: dict[str, str] = {}
        seen: set[str] = set()
        for activity in sorted(set(activities)):
            symbol = to_symbol(activity)
            if symbol in seen:
                suffix = 2
                while f"{symbol}_{suffix}" in seen:
                    suffix += 1
                symbol = f"{symbol}_{suffix}"
            seen.add(symbol)
            self.mapping[activity] = symbol
        self._reverse = {v: k for k, v in self.mapping.items()}

    @classmethod
    def from_bundle(cls, bundle: EventLogBundle) -> "Alphabet":
        return cls(bundle.df[ACTIVITY].unique().tolist())

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(self.mapping.values())

    def symbol(self, activity: str) -> str:
        return self.mapping[activity]

    def activity(self, symbol: str) -> str:
        return self._reverse[symbol]


class LTLParseError(Exception):
    """Raised when a formula cannot be parsed or references unknown symbols."""


@dataclass
class VerificationResult:
    formula: str
    satisfied: int = 0
    violated: int = 0
    total: int = 0
    ratio: float = 0.0
    counterexamples: list[dict] = field(default_factory=list)
    error: str | None = None

    def as_dict(self) -> dict:
        return {
            "formula": self.formula,
            "satisfied": self.satisfied,
            "violated": self.violated,
            "total": self.total,
            "ratio": self.ratio,
            "counterexamples": self.counterexamples,
            "error": self.error,
        }


def encode_trace(activities: list[str], alphabet: Alphabet) -> list[dict[str, bool]]:
    """One propositional interpretation per event.

    flloat requires a dict per position with every symbol present; a set raises
    AttributeError inside its evaluator.
    """
    symbols = alphabet.symbols
    encoded = []
    for activity in activities:
        active = alphabet.symbol(activity)
        encoded.append({symbol: symbol == active for symbol in symbols})
    return encoded


VINST_SYMBOLS: frozenset[str] = frozenset(
    to_symbol(activity) for activity in VINST_ACTIVITIES
)


def propositions_in(formula: str) -> set[str]:
    """Lowercase identifiers in a formula. LTLf operators are uppercase."""
    return set(re.findall(r"\b[a-z_][a-z0-9_]*\b", formula))


def _parse(formula: str, alphabet: Alphabet, strict: bool):
    """Parse and validate, returning the formula and the symbols this log lacks."""
    try:
        parsed = LTLfParser()(formula)
    except Exception as exc:  # noqa: BLE001 - flloat raises assorted parser errors
        raise LTLParseError(f"Could not parse formula: {exc}") from exc

    known = set(alphabet.symbols)
    absent = sorted(propositions_in(formula) - known)
    if strict:
        unknown = sorted(set(absent) - VINST_SYMBOLS)
        if unknown:
            raise LTLParseError(
                f"Unknown proposition(s): {', '.join(unknown)}. "
                f"Available: {', '.join(sorted(known | VINST_SYMBOLS))}"
            )
    return parsed, absent


def verify(
    bundle: EventLogBundle,
    formula: str,
    *,
    max_counterexamples: int = 10,
    strict: bool = True,
) -> VerificationResult:
    """Check an LTLf formula against every trace in the log.

    A proposition absent from this log is evaluated as always false; strict mode
    additionally rejects one that names no known VINST activity at all.
    """
    alphabet = Alphabet.from_bundle(bundle)

    try:
        parsed, absent = _parse(formula, alphabet, strict)
    except LTLParseError as exc:
        return VerificationResult(formula=formula, error=str(exc))

    result = VerificationResult(formula=formula)
    grouped = bundle.df.groupby(CASE, sort=False)[ACTIVITY].apply(list)
    padding = {symbol: False for symbol in absent}

    for case_id, activities in grouped.items():
        trace = [{**step, **padding} for step in encode_trace(activities, alphabet)]
        holds = parsed.truth(trace, 0)
        if holds:
            result.satisfied += 1
        else:
            result.violated += 1
            if len(result.counterexamples) < max_counterexamples:
                result.counterexamples.append(
                    {"case": str(case_id), "trace": activities}
                )

    result.total = result.satisfied + result.violated
    result.ratio = result.satisfied / result.total if result.total else 0.0
    return result
