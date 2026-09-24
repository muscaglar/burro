"""The method: one for each way of working a figure out.

A method is named and numbered, `lsoa_to_area_by_homes@1`, and the number
rises when the arithmetic changes. Its sentence is what the methods page
prints, so every parameter must stand in it: a distance that changes the
figure and is not said is a figure nobody can check.
"""

import re
from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, StrictFloat, StrictInt, StrictStr, model_validator

from burro_pipeline.evidence.record import EvidenceRecord

DERIVATION_ID_PATTERN = r"^[a-z][a-z0-9_]*@[1-9][0-9]*$"
MODULE_PATTERN = r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$"
PARAMETER_PATTERN = r"^[a-z][a-z0-9_]*$"

DerivationId = Annotated[str, Field(pattern=DERIVATION_ID_PATTERN)]
Parameter = StrictInt | StrictFloat | StrictStr


class Kind(StrEnum):
    """What the screen must say of a figure worked out this way."""

    MEASURED = "measured"
    MODELLED = "modelled"
    AVERAGED = "averaged"


def _numbers_in(sentence: str) -> list[str]:
    """Every number a sentence states, with 1,000 read as 1000."""
    return re.findall(r"\d+(?:\.\d+)?", re.sub(r"(?<=\d),(?=\d{3})", "", sentence))


def _stated(value: Parameter, sentence: str) -> bool:
    if isinstance(value, str):
        return bool(value) and value in sentence
    # 300.0 is written 300.
    written = str(int(value)) if float(value).is_integer() else str(value)
    return written in _numbers_in(sentence)


class Method(EvidenceRecord):
    derivation_id: DerivationId
    # One sentence for the methods page, with every parameter in it.
    sentence: str = Field(min_length=2)
    kind: Kind
    # Distances, thresholds, windows.
    parameters: dict[str, Parameter] = Field(default_factory=dict[str, Parameter])
    # The module that holds the arithmetic. The lock names the commit.
    code: str = Field(pattern=MODULE_PATTERN)

    @model_validator(mode="after")
    def _is_one_sentence_that_states_every_parameter(self) -> Self:
        if not self.sentence.endswith(".") or re.search(r"[.!?]\s|\n", self.sentence):
            raise ValueError("sentence is one sentence, ending in a full stop")
        for name, value in self.parameters.items():
            if not re.fullmatch(PARAMETER_PATTERN, name):
                raise ValueError("a parameter is named in lower case, as a_b_c")
            if not _stated(value, self.sentence):
                raise ValueError("the sentence does not state every parameter")
        return self

    @property
    def name(self) -> str:
        return self.derivation_id.split("@")[0]

    @property
    def version(self) -> int:
        return int(self.derivation_id.split("@")[1])
