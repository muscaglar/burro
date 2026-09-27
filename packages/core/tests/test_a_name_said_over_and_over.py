"""The times of a sentence are worked out once, however many names the sentence holds.

Whether the name of a place is turned away is asked of what stands before the
time that runs on to it, so every time of the sentence is read to find that
one. They were read again for each name, twice over, and to read them is to
read the whole sentence: a sentence that said one name sixty times read its
hundred and eighty words more than twenty thousand times. The service is open
to anybody, and such a sentence held its processor for seconds.

What the reader makes of a sentence is as it was. Every name here is made up.
"""

from collections.abc import Mapping, Sequence
from typing import Any

import pytest
from burro_core import interpret
from burro_core.ids import InterpretStatus, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.spec import default_spec

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
# What is said of one place, and the most often that 600 characters hold it.
SAID = ["1h of QH1", "QH1 an hour or", "30 mins of QH7 from", "QH2 max 30 minutes but"]
MOST = 600


def read(text: str) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=fixture_release()))


def times_worked_out(text: str, monkeypatch: pytest.MonkeyPatch) -> int:
    """How often the times of a sentence are worked out while `text` is read."""
    times_of = interpret._times_of  # pyright: ignore[reportPrivateUsage]
    asked: list[int] = []

    def counted(items: Sequence[Any], lexicon: Mapping[str, Any]) -> Any:
        asked.append(len(items))
        return times_of(items, lexicon)

    with monkeypatch.context() as patched:
        patched.setattr(interpret, "_times_of", counted)
        found = read(text)
    assert found.status is InterpretStatus.SUGGEST
    return len(asked)


@pytest.mark.parametrize("said", SAID)
def test_the_times_are_worked_out_no_more_often_for_many_names_than_for_two(
    said: str, monkeypatch: pytest.MonkeyPatch
):
    twice = " ".join([said] * 2)
    often = " ".join([said] * (MOST // (len(said) + 1)))

    assert times_worked_out(often, monkeypatch) == times_worked_out(twice, monkeypatch)


@pytest.mark.parametrize("said", SAID)
def test_a_name_said_often_is_offered_once_and_rests_on_every_place_it_stands(said: str):
    often = MOST // (len(said) + 1)
    text = " ".join([said] * often)

    found = read(text)

    [journey] = [one for one in found.suggestions if one.target == "commute"]
    assert len(journey.spans) >= often
    assert not found.operations.commute_ops
