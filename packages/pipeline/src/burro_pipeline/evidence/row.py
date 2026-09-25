"""The evidence row: one for each figure, and one for each figure that is missing.

Its key is the `fact_id` of contract 7.1, so a fact and its evidence cannot
part. It says which files the figure was worked out from, by which method, how
much of the area the data covered, and in which state that leaves the figure.
A missing figure has a row too: the row is what says why it is missing.

The row of a measure or of a tag holds the figure too. A row that only said
there was a figure would stand behind any figure at all. The row of a cost
holds it where the cost is one number, a median with no range, and where it is
a rent of a wider place than the area, of which it holds the median.
"""

from enum import StrEnum
from typing import Annotated, Self

from burro_core.ids import FactKind
from pydantic import Field, model_validator

from burro_pipeline.evidence.method import DerivationId
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.record import (
    Day,
    EvidenceRecord,
    FileId,
    Share,
    given,
    strictly_increasing,
)

# The kinds of fact that have a row of their own. A `budget_fit` rests on the row of its
# cost, a `missing` on the row of the area's name, and a journey on the row of its mode. A
# `likeness` rests on the rows of the measures it was counted from.
ROW_KINDS = (
    FactKind.AREA,
    FactKind.FEATURE,
    FactKind.TAG,
    FactKind.COST,
    FactKind.STATION,
    FactKind.TRAVEL,
)
ROW_ID_PATTERN = rf"^(syn|lon)-n[0-9a-z]+/({'|'.join(ROW_KINDS)})/[0-9a-z][0-9a-z_.-]*$"
# The kinds of fact that are one number: the figure of a measure, the score of a tag, and a
# cost that is a publisher's median with no range. A cost that is a range Burro worked out
# is three numbers, and its row holds none. A rent that is of a wider place is a range as
# its publisher wrote it, and its row holds its median.
HOLDS_A_FIGURE = (FactKind.FEATURE, FactKind.TAG, FactKind.COST)
# At or above this share of an area's homes, a figure is said to cover the area.
FULLY_COVERED = 0.99

RowId = Annotated[str, Field(pattern=ROW_ID_PATTERN)]


class State(StrEnum):
    """The state of one measure in one area. There is no blank."""

    PRESENT = "present"  # a value, with at least 99% covered
    PARTIAL = "partial"  # a value, with less covered. The share is shown
    BELOW_THRESHOLD = "below_threshold"  # too little covered. The value is null
    SOURCE_GAP = "source_gap"  # the publisher holds nothing for these units
    SUPPRESSED = "suppressed"  # the publisher withheld it
    NOT_PUBLISHED = "not_published"  # the publisher does not publish it for areas this small
    NOT_CARRIED = "not_carried"  # this build does not work the measure out


HAS_A_VALUE = frozenset({State.PRESENT, State.PARTIAL})
# `not_published` is said once and is not counted: no source could close it.
IS_A_GAP = frozenset({State.BELOW_THRESHOLD, State.SOURCE_GAP, State.SUPPRESSED, State.NOT_CARRIED})
NEEDS_NO_FILE = frozenset({State.NOT_PUBLISHED, State.NOT_CARRIED})


class Flag(StrEnum):
    """What a reader of the figure should know."""

    ROUNDED_IN_SOURCE = "rounded_in_source"
    SUPPRESSED_IN_SOURCE = "suppressed_in_source"
    UNIT_SPLIT = "unit_split"


def not_carried(fact_id: str) -> "EvidenceRow":
    """The row that says a release holds no figure, because it carries no such measure."""
    return EvidenceRow(
        fact_id=fact_id,
        derivation_id=None,
        inputs=(),
        data_period=None,
        retrieved_on=None,
        units_used=0,
        units_expected=0,
        weight_covered=0.0,
        state=State.NOT_CARRIED,
    )


def state_of(has_value: bool, covered: float) -> State:
    """The state a figure is in, from whether it has a value and how much was covered.

    It cannot tell a figure the publisher withheld from one the publisher never
    held. Only the step that read the file can, and it says so in the row.
    """
    if has_value:
        return State.PRESENT if covered >= FULLY_COVERED else State.PARTIAL
    return State.BELOW_THRESHOLD if covered > 0 else State.SOURCE_GAP


class EvidenceRow(EvidenceRecord):
    fact_id: RowId
    # Null only where no file was read: the measure is not carried, or is not published.
    derivation_id: DerivationId | None
    # Every file the figure was worked out from, the crosswalk and the weights included.
    inputs: tuple[FileId, ...]
    # The span of the inputs, and the latest day any was retrieved.
    data_period: Period | None
    retrieved_on: Day | None
    # How many of the source's units the area takes in, and how many had data.
    units_used: int = Field(ge=0)
    units_expected: int = Field(ge=0)
    # The share of the area's homes, or land, that had data.
    weight_covered: Share
    state: State
    flags: tuple[Flag, ...] = ()
    # The figure itself, as the release gives it: the value of a measure, the score of a
    # tag, or the median of a cost that has no range. `check` holds the release to it, so a
    # figure changed after the build is found.
    value: float | None = Field(default=None, allow_inf_nan=False)

    @model_validator(mode="after")
    def _holds_together(self) -> Self:
        if not strictly_increasing(self.inputs) or not strictly_increasing(self.flags):
            raise ValueError("inputs and flags are sorted, each once")
        if self.units_used > self.units_expected:
            raise ValueError("units_used is more than units_expected")
        bare = not self.inputs
        if bare and self.state not in NEEDS_NO_FILE:
            raise ValueError("a row in this state names the files it rests on")
        if not bare and self.state is State.NOT_CARRIED:
            raise ValueError("a measure that is not carried rests on no file")
        if given(self.derivation_id, self.data_period, self.retrieved_on) is not (not bare):
            raise ValueError("a method, a period and a date are given exactly when a file is")
        if not self._weight_suits_the_state():
            raise ValueError("weight_covered does not suit the state")
        if self.value is not None and self.state not in HAS_A_VALUE:
            raise ValueError("a figure is held only by a row that has one")
        if self.value is not None and self.fact_id.split("/")[1] not in HOLDS_A_FIGURE:
            raise ValueError(
                "a figure is held only by a row of a measure or of a tag, or of a cost"
            )
        return self

    def _weight_suits_the_state(self) -> bool:
        covered, used = self.weight_covered, self.units_used
        if self.state is State.PRESENT:
            return covered >= FULLY_COVERED
        if self.state in (State.PARTIAL, State.BELOW_THRESHOLD):
            return 0 < covered < FULLY_COVERED
        if self.state is State.SUPPRESSED:
            return True
        return covered == 0 and used == 0

    @property
    def area_id(self) -> str:
        return self.fact_id.split("/")[0]

    @property
    def measure(self) -> str:
        """What is measured, whatever the area: `feature/park_proximity`."""
        return self.fact_id.split("/", 1)[1]

    @property
    def has_a_value(self) -> bool:
        return self.state in HAS_A_VALUE
