"""The typed edits. Sliders, chips and chat all produce `Operations`, and nothing else does.

It is six arrays, each of one type. Every field of every item is required, and
all six arrays are always present, empty when unused. There are no unions and
no optional fields, because a model's structured output cannot express them
well. A field that an edit has nothing to say in carries its sentinel:
`unchanged`, `none`, `default`, `0` or `0.0`.

An edit never carries text. A destination or an area named in words is
resolved to an id before it becomes an edit.
"""

from typing import Annotated

from pydantic import BeforeValidator, Field

from burro_core._record import Record
from burro_core.ids import (
    AreaAction,
    BudgetAction,
    Choice,
    CommuteAction,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    ModeChoice,
    SegmentChoice,
    SettingAction,
    Step,
    StrictnessChoice,
    TagId,
    TenureChoice,
    TowardChoice,
    WeightAction,
)
from burro_core.ids import Setting as SettingName


def _lower(value: object) -> object:
    # Structured output may change the case of an enum value.
    return value.lower() if isinstance(value, str) else value


_Lower = BeforeValidator(_lower)
# Not a number is refused here, so the reducer only ever compares real numbers.
_Number = Annotated[float, Field(allow_inf_nan=False)]


class BudgetEdit(Record):
    action: Annotated[BudgetAction, _Lower]
    tenure: Annotated[TenureChoice, _Lower]
    amount: int  # 0 for not given
    segment: Annotated[SegmentChoice, _Lower]
    strictness: Annotated[StrictnessChoice, _Lower]
    step: Annotated[Step, _Lower]
    provenance: Annotated[EditProvenance, _Lower]


class CommuteEdit(Record):
    action: Annotated[CommuteAction, _Lower]
    # A plain string, so that an id the release does not know, the empty
    # string included, is a rejected edit and not a validation error.
    place_id: str
    mode: Annotated[ModeChoice, _Lower]
    max_minutes: int  # 0 for not given
    strictness: Annotated[StrictnessChoice, _Lower]
    step: Annotated[Step, _Lower]  # moves max_minutes
    provenance: Annotated[EditProvenance, _Lower]


class WeightEdit(Record):
    action: Annotated[WeightAction, _Lower]
    feature_id: Annotated[FeatureId, _Lower]
    value: _Number  # read by set
    step: Annotated[Step, _Lower]  # read by nudge
    direction: Annotated[DirectionChoice, _Lower]
    provenance: Annotated[EditProvenance, _Lower]


class TagEdit(Record):
    action: Annotated[WeightAction, _Lower]
    tag_id: Annotated[TagId, _Lower]
    value: _Number  # read by set
    step: Annotated[Step, _Lower]  # read by nudge
    # Which end of a scale. `default` leaves it as it is, and is `high` for a
    # vibe that is not yet in the spec.
    toward: Annotated[TowardChoice, _Lower]
    provenance: Annotated[EditProvenance, _Lower]


class AreaEdit(Record):
    action: Annotated[AreaAction, _Lower]
    area_id: str
    provenance: Annotated[EditProvenance, _Lower]


class SettingEdit(Record):
    action: Annotated[SettingAction, _Lower]
    setting: Annotated[SettingName, _Lower]
    choice: Annotated[Choice, _Lower]
    value: _Number  # read when setting a weight
    step: Annotated[Step, _Lower]
    provenance: Annotated[EditProvenance, _Lower]


class Operations(Record):
    budget_ops: tuple[BudgetEdit, ...]
    commute_ops: tuple[CommuteEdit, ...]
    weight_ops: tuple[WeightEdit, ...]
    tag_ops: tuple[TagEdit, ...]
    area_ops: tuple[AreaEdit, ...]
    setting_ops: tuple[SettingEdit, ...]

    @property
    def count(self) -> int:
        return (
            len(self.budget_ops)
            + len(self.commute_ops)
            + len(self.weight_ops)
            + len(self.tag_ops)
            + len(self.area_ops)
            + len(self.setting_ops)
        )


NO_OPERATIONS = Operations(
    budget_ops=(), commute_ops=(), weight_ops=(), tag_ops=(), area_ops=(), setting_ops=()
)
