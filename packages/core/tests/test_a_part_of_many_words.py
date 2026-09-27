"""A part of a sentence of many words is not read over again for each word it holds.

A home may stand before a journey or a wish with no word between them, "2 bed
within 30 minutes of the works", so a part that is no one thing is looked
through for two: at each word it may be cut at, what stands before is read,
and what stands after. Each reading runs as far as the words let it, so a part
of three hundred words was read three hundred times over, and a sentence of
600 characters held the processor of a service that is open to anybody for
seconds: "a" said over and over, with a wish in the middle.

No part that is two things is near as long as that. A part is looked through
for two things only where it holds no more words than `LONGEST_OF_TWO`, and a
longer one is not plain. Every name here is made up.
"""

import pytest
from burro_core import grammar
from burro_core.grammar import LONGEST_OF_TWO
from burro_core.ids import InterpretStatus, ModeChoice, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.spec import default_spec

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
# The most that 600 characters hold of a word of one letter.
MOST = 300
# The longest sentences of two things that the reader was driven with, in words: a home
# and the journey from it, each said in full.
TWO_THINGS = [
    "2 bed within 30 minutes of Cindermoor Works",
    "renting a two bed flat up to £1,500 a month within 30 minutes of Cindermoor Works by bike",
]


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=fixture_release()))


def homes_read(text: str, monkeypatch: pytest.MonkeyPatch) -> int:
    """How often the grammar sets out to read a home while `text` is read."""
    segment = grammar._Segment  # pyright: ignore[reportPrivateUsage]
    home = segment.home
    asked: list[int] = []

    def counted(self: object) -> object:
        asked.append(1)
        return home(self)  # pyright: ignore[reportArgumentType]

    with monkeypatch.context() as patched:
        patched.setattr(segment, "home", counted)
        read(text)
    return len(asked)


@pytest.mark.parametrize(
    "words",
    [
        ["a"] * MOST,
        ["a"] * 147 + ["near", "a", "park"] + ["a"] * 147,
        ["renting"] + ["a"] * (MOST - 5),
        ["a"] * (MOST - 5) + ["park", "near"],
    ],
    ids=["one word", "a wish in the middle", "a home at the head", "a thing at the foot"],
)
def test_a_part_of_many_words_is_read_no_more_often_than_one_of_forty(
    words: list[str], monkeypatch: pytest.MonkeyPatch
):
    forty = " ".join(["a"] * 40)

    assert homes_read(" ".join(words), monkeypatch) <= homes_read(forty, monkeypatch)


def test_a_part_of_many_words_is_not_plain_and_nothing_of_it_is_applied():
    # It was read as a home and a wish, whatever stood before them.
    found = read(" ".join(["a"] * 45 + ["2", "bed", "flat", "near", "a", "park"]))

    assert found.status is InterpretStatus.SUGGEST
    assert not any(found.operations.model_dump().values())
    assert {one.target for one in found.suggestions} >= {"feature:park_proximity"}


@pytest.mark.parametrize("text", TWO_THINGS)
def test_two_things_with_no_word_between_them_are_read_as_they_were(text: str):
    found = read(text)

    assert found.status is InterpretStatus.OK
    [journey] = found.operations.commute_ops
    assert (journey.max_minutes, len(found.operations.budget_ops)) == (30, 1)
    assert journey.mode in (ModeChoice.UNCHANGED, ModeChoice.CYCLE)


def test_the_longest_part_that_is_looked_through_is_far_longer_than_any_that_is_two_things():
    longest = max(len(text.split()) for text in TWO_THINGS)

    assert longest * 2 <= LONGEST_OF_TWO
