"""A flat and a house are two kinds of home, and neither is taken for the other.

"Buying a flat or a house up to 500k" was applied as a search for a flat, with
a firm budget, and the house was in no list: not applied, not offered, not said
to be unread. A price is held by the kind of home, and a house is no flat, so
the two are two kinds of which the search holds one. Nobody can say which is
meant. The prompt is not plain, nothing of it is applied, and each is offered
or is said to be unread.

A rent is held by the number of bedrooms, whatever kind of home it is for, so
a flat or a house to rent is as it was. A room and a studio are kinds of home
that a rent is held by, so beside either a flat or a house is another kind:
"renting a room or a flat for £900 a month" was applied as a room, and the flat
was in no list. Every sentence here is made up.
"""

import pytest
from burro_core.ids import InterpretStatus, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.ops import NO_OPERATIONS
from burro_core.spec import PreferenceSpec, default_spec

from .support import small_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
READER = RuleInterpreter()


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=small_release()))


def listed(text: str, result: InterpretResult) -> list[str]:
    """The words that an edit rests on, that are offered, or that are said to be unread."""
    return [
        *(text[found.start : found.end] for found in result.rests_on),
        *(text[span.start : span.end] for found in result.suggestions for span in found.spans),
        *(text[span.start : span.end] for span in result.unread),
    ]


@pytest.mark.parametrize(
    ("text", "spec"),
    [
        ("buying a flat or a house up to 500k", RENTER),
        ("buying a house or a flat up to 500k", RENTER),
        ("a flat or house to buy for 500k", RENTER),
        ("buying a house or flat", RENTER),
        ("buying a flat and a house up to 500k", RENTER),
        ("buying a 3 bed house up to 600k or a flat", RENTER),
        ("buying a 2 bed flat or a 3 bed house up to 500k", RENTER),
        ("leafy, buying a flat or a house up to 500k", RENTER),
        ("a flat or a house up to 500k", BUYER),
        ("a house or a flat", BUYER),
        # More flats than one are flats, and the houses beside them were a terraced house.
        ("buying flats or houses up to 500k", RENTER),
        ("buying apartments or a house up to 500k", RENTER),
        ("flats or houses up to 500k", BUYER),
        # To rent, a room or a studio beside a flat or a house.
        ("renting a flat or house share", RENTER),
        ("renting a room or a flat for £900 a month", RENTER),
        ("renting a flat or a room for £900 a month", RENTER),
        ("renting a studio or a house for £1,200 a month", RENTER),
        ("renting a house or a studio for £1,200 a month", RENTER),
        ("renting a house share or flats up to £900 a month", RENTER),
    ],
)
def test_a_flat_and_a_house_to_buy_are_not_plain_and_neither_is_dropped(
    text: str, spec: PreferenceSpec
):
    result = read(text, spec)
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    for home in ("flat", "apartment", "house", "room", "studio"):
        if home in text:
            assert [words for words in listed(text, result) if home in words], home
    # No way of any offer holds both the amount and a kind of home that was not chosen.
    for found in result.suggestions:
        for choice in found.choices:
            for edit in choice.operations.budget_ops:
                assert not (edit.amount and edit.segment != "unchanged"), found.label


@pytest.mark.parametrize(
    ("text", "segment"),
    [
        # The house is part of what the kind is called.
        ("buying a terraced house up to 500k", "terraced"),
        ("buying a semi-detached house up to 500k", "semi_detached"),
        # A house of no kind beside a kind of house is that kind.
        ("buying a terraced house or a house up to 500k", "terraced"),
        # The same kind said twice is one kind.
        ("buying a flat or maisonette up to 400k", "flat"),
        ("buying a flat, an apartment, up to 400k", "flat"),
    ],
)
def test_one_kind_of_home_is_applied_as_it_was(text: str, segment: str):
    result = read(text)
    assert result.status is InterpretStatus.OK
    (edit,) = result.operations.budget_ops
    assert (edit.tenure, edit.segment) == ("buy", segment)


@pytest.mark.parametrize(
    ("text", "segment"),
    [
        ("renting a studio flat for £1,000 a month", "studio"),
        ("renting a flat share for £700 a month", "room"),
        ("renting a house share for £700 a month", "room"),
        ("renting a studio for £1,000 a month", "studio"),
    ],
)
def test_one_kind_of_home_to_rent_is_applied_as_it_was(text: str, segment: str):
    result = read(text)
    assert result.status is InterpretStatus.OK
    (edit,) = result.operations.budget_ops
    assert (edit.tenure, edit.segment) == ("rent", segment)


@pytest.mark.parametrize(
    "text",
    [
        "renting a flat or a house for £2,000 a month",
        "renting a house or flat for £2,000 a month",
    ],
)
def test_a_flat_or_a_house_to_rent_is_applied_as_it_was(text: str):
    """A rent is held by the number of bedrooms, so neither kind changes what is held."""
    result = read(text)
    assert result.status is InterpretStatus.OK
    (edit,) = result.operations.budget_ops
    assert (edit.tenure, edit.amount, edit.segment) == ("rent", 2000, "unchanged")
