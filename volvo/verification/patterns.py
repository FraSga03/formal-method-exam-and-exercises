"""Named LTLf properties for the VINST incident-management process.

Each is a real formula evaluated by the same engine as user-written ones -- no
canned code paths behind a label.
"""
import re
from dataclasses import dataclass

from volvo.logs.loader import EventLogBundle
from volvo.verification.ltl import Alphabet, verify

_OPERATORS = {"G", "F", "X", "U"}


@dataclass(frozen=True)
class Property:
    key: str
    name: str
    description: str
    formula: str
    expected: float  # measured on the incidents log; guards against regressions

    def propositions(self) -> set[str]:
        used = set(re.findall(r"\b[a-z_][a-z0-9_]*\b", self.formula))
        return used - _OPERATORS


PROPERTIES: tuple[Property, ...] = (
    Property(
        key="termination",
        name="Termination",
        description="Every incident reaches a Completed state.",
        formula=(
            "F(completed_closed | completed_in_call | completed_resolved "
            "| completed_cancelled)"
        ),
        expected=0.999,
    ),
    Property(
        key="resolution",
        name="Resolution",
        description="Work started is always brought to some completion.",
        formula=(
            "G(accepted_in_progress -> F(completed_closed | completed_in_call "
            "| completed_resolved))"
        ),
        expected=0.999,
    ),
    Property(
        key="no_reopen",
        name="No work after closure",
        description="Once formally closed, an incident is never worked again.",
        formula="G(completed_closed -> !F(accepted_in_progress))",
        expected=0.984,
    ),
    Property(
        key="queued_gets_worked",
        name="Queued work is picked up",
        description="Anything queued for assignment is eventually taken into progress.",
        formula="G(queued_awaiting_assignment -> F(accepted_in_progress))",
        expected=0.992,
    ),
    Property(
        key="wait_user_resumes",
        name="Waiting on the user resumes",
        description="Time parked on the user is never where a case ends.",
        formula=(
            "G(accepted_wait_user -> F(accepted_in_progress | completed_resolved "
            "| completed_closed))"
        ),
        expected=0.999,
    ),
    Property(
        key="no_unmatched",
        name="No unmatched events",
        description="Unmatched is a VINST export artifact, not a process step.",
        formula="G(!unmatched_unmatched)",
        expected=0.999,
    ),
    # The two below are expected to FAIL. They encode what the documented
    # procedure claims; the gap between claim and log is the finding.
    Property(
        key="formal_closure",
        name="Formal closure",
        description=(
            "Every worked incident ends in formal closure. Fails: a quarter of "
            "incidents settle as Completed+In Call without formal closure."
        ),
        formula="G(accepted_in_progress -> F(completed_closed))",
        expected=0.740,
    ),
    Property(
        key="queue_before_work",
        name="Queueing precedes work",
        description=(
            "Procedure says an incident is queued before anyone works it. Fails "
            "badly: 84% start directly in progress -- the push-to-front pattern "
            "this dataset is known for."
        ),
        formula="(!accepted_in_progress) U queued_awaiting_assignment",
        expected=0.155,
    ),
)


_BY_KEY = {p.key: p for p in PROPERTIES}


def get_property(key: str) -> Property:
    if key not in _BY_KEY:
        raise KeyError(f"Unknown property {key!r}. Known: {sorted(_BY_KEY)}")
    return _BY_KEY[key]


def applicable(bundle: EventLogBundle) -> list[Property]:
    """Properties mentioning at least one activity this log contains.

    Not a subset test: the three BPI logs have different alphabets, and a
    property referring to one absent activity is still meaningful.
    """
    known = set(Alphabet.from_bundle(bundle).symbols)
    return [p for p in PROPERTIES if p.propositions() & known]


def verify_all(bundle: EventLogBundle) -> list[dict]:
    """Verify every applicable property; one result row each."""
    rows = []
    for prop in applicable(bundle):
        result = verify(bundle, prop.formula, strict=False)
        rows.append(
            {
                "key": prop.key,
                "name": prop.name,
                "description": prop.description,
                **result.as_dict(),
            }
        )
    return rows
