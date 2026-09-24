"""The shape a model must answer in, and what is read of an answer.

A model can name only ids of the catalogue, because the schema holds no
others. It never resolves a destination: it copies the words, and Burro's own
index turns them into an id. Every edit carries `words`, the words of the
person's that it rests on.

Four fields of an answer are no longer read (ADR 0012): `direction` on a
thing that runs one way, `value`, `strictness` and `provenance`. They stay in
the shape, because taking one out changes what a model answers, and that
needs a measurement of its own. `guard.py` says what is read in their place.
"""

from collections.abc import Mapping
from enum import StrEnum
from typing import Annotated, cast

from burro_core.ids import (
    AreaAction,
    CommuteAction,
    EditProvenance,
    ModeChoice,
    Step,
    StrictnessChoice,
    UnmetCategory,
)
from burro_core.interpret import MAX_TEXT
from burro_core.ops import BudgetEdit, SettingEdit, TagEdit, WeightEdit
from pydantic import BeforeValidator, Field, ValidationError

from burro_api.providers.interface import ModelError
from burro_api.wire import Body, Wire

# More edits than any sentence of 600 characters can mean. An answer that
# holds more is not an answer to what was asked.
MAX_EDITS = 24
MAX_NAME = 120


def _lower(value: object) -> object:
    # Structured output may change the case of an enum value.
    return value.lower() if isinstance(value, str) else value


_Lower = BeforeValidator(_lower)
# The words as they were typed. Kept out of every repr, and dropped once resolved.
_Name = Annotated[str, Field(max_length=MAX_NAME, repr=False)]
# The words of the person's that an edit rests on, as the model copied them.
# They are looked for in the text and dropped: what is kept is where they stand.
_Said = Annotated[str, Field(max_length=MAX_TEXT, repr=False)]


class ModelStatus(StrEnum):
    OK = "ok"
    OFF_TOPIC = "off_topic"


class PolicyFlag(StrEnum):
    """Part of the request was about who lives somewhere (ADR 0006)."""

    AVOID_GROUP = "avoid_group"
    SEEK_GROUP = "seek_group"


class ModelBudgetEdit(BudgetEdit):
    words: _Said


class ModelCommuteEdit(Wire):
    action: Annotated[CommuteAction, _Lower]
    # The destination as the person named it, or empty when `position` says which.
    destination_text: _Name
    # The 1-based position of a commute in the spec that was sent, for an
    # `update` or a `remove`. 0 for a destination named in `destination_text`.
    position: int
    mode: Annotated[ModeChoice, _Lower]
    max_minutes: int
    strictness: Annotated[StrictnessChoice, _Lower]
    step: Annotated[Step, _Lower]
    provenance: Annotated[EditProvenance, _Lower]
    words: _Said


class ModelWeightEdit(WeightEdit):
    words: _Said


class ModelTagEdit(TagEdit):
    words: _Said


class ModelAreaEdit(Wire):
    action: Annotated[AreaAction, _Lower]
    area_text: _Name
    provenance: Annotated[EditProvenance, _Lower]
    words: _Said


class ModelSettingEdit(SettingEdit):
    words: _Said


class ModelUnmet(Wire):
    """Something the person asked for that no feature or vibe covers, and where they said it."""

    category: Annotated[UnmetCategory, _Lower]
    words: _Said


def _with_words(value: object) -> object:
    """A bare category, as a model answered before it was asked for the words, with none."""
    return {"category": value, "words": ""} if isinstance(value, str) else value


class ModelOutput(Body):
    """What the model must answer in. Like `Operations`: no union, no optional field.

    Each edit is the edit of `Operations` with `words` beside it: the words of
    the person's that it rests on. It is held to the rule a request body is
    held to: a number in it must be a number. Left to itself the validator
    reads `true` as position 1, and takes out the journey that stands first
    in the person's spec.
    """

    status: Annotated[ModelStatus, _Lower]
    budget_ops: tuple[ModelBudgetEdit, ...]
    commute_ops: tuple[ModelCommuteEdit, ...]
    weight_ops: tuple[ModelWeightEdit, ...]
    tag_ops: tuple[ModelTagEdit, ...]
    area_ops: tuple[ModelAreaEdit, ...]
    setting_ops: tuple[ModelSettingEdit, ...]
    policy_flags: tuple[Annotated[PolicyFlag, _Lower], ...]
    unmet: tuple[Annotated[ModelUnmet, BeforeValidator(_with_words)], ...]

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


# Keys that describe a schema to a person. The model is told what each field
# means in the instructions, once, so the schema is sent without them.
_FOR_PEOPLE = frozenset({"title", "description"})
# What structured output does not take.
_UNSUPPORTED = frozenset({"maxLength", "minLength", "maximum", "minimum", "maxItems", "minItems"})


def _plain(schema: object, inside_properties: bool = False) -> object:
    """The schema with nothing in it that structured output does not take.

    Limits on length are checked here, when the answer is validated, and not
    by the provider. A key of `properties` is a field's name and is kept
    whatever it is.
    """
    if isinstance(schema, dict):
        dropped = frozenset[str]() if inside_properties else _FOR_PEOPLE | _UNSUPPORTED
        return {
            key: _plain(value, inside_properties=key == "properties" and not inside_properties)
            for key, value in cast(dict[str, object], schema).items()
            if key not in dropped
        }
    if isinstance(schema, list):
        return [_plain(item) for item in cast(list[object], schema)]
    return schema


SCHEMA: Mapping[str, object] = cast(dict[str, object], _plain(ModelOutput.model_json_schema()))


def parsed(output: str) -> ModelOutput:
    """A model's answer, or `ModelError` where it does not fit the shape. It says no more."""
    try:
        found = ModelOutput.model_validate_json(output)
    except ValidationError:
        # The error can quote the answer, and the answer can quote the person.
        raise ModelError from None
    if found.count > MAX_EDITS:
        raise ModelError
    return found
