"""What a person typed of a home, and Burro cannot hold, is said where the prompt is applied.

Burro holds what homes sell for by kind of home and not by the number of
bedrooms, and what they rent for by bedrooms and not by kind. "Buying a 3 bed
house up to 600k" was applied, and "a 3 bed" was in no list: not applied, not
offered, not said to be unread. So was the terraced house of "renting a
terraced house up to £2,000 a month".

In a prompt that is offered the service has words for each, in the note of
the offer. A prompt that is applied says the same words: what cannot be held
is offered with nothing to choose but to leave it out, and its note says why.
The status of the prompt is as it was, and nothing of it is said to be unread.
Every sentence here is made up.
"""

from typing import Any

import pytest
from burro_core.ids import InterpretStatus, Tenure, UnmetCategory
from burro_core.interpret import (
    BY_BEDROOMS,
    BY_KIND,
    IGNORE,
    TO_RENT_ALONE,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.reducer import apply
from burro_core.spec import PreferenceSpec, default_spec

from .support import small_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
READER = RuleInterpreter()
QUIET = ("unchanged", "none", "default", 0, 0.0)


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=small_release()))


def said(edit: Any) -> dict[str, Any]:
    """An edit with its sentinels left out."""
    return {k: v for k, v in edit.model_dump(mode="json").items() if v not in QUIET}


def not_held(text: str, result: InterpretResult) -> list[tuple[str, str, list[str]]]:
    """What is said of a home that cannot be held: what it is, why, and the words it rests on."""
    return [
        (found.label, found.note, [text[span.start : span.end] for span in found.spans])
        for found in result.suggestions
    ]


def rested_on(text: str, result: InterpretResult) -> list[str]:
    return [text[found.start : found.end] for found in result.rests_on]


def held(spec: PreferenceSpec, result: InterpretResult) -> tuple[str, int | None, str, str]:
    after = apply(spec, result.operations, small_release())
    assert after.rejected == ()
    budget = after.spec.budget
    return after.spec.tenure, budget.amount, budget.segment, budget.strictness


# --- The bedrooms of a home to buy ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "spec", "applied", "label", "words"),
    [
        (
            "buying a 3 bed house up to 600k",
            RENTER,
            ("buy", 600_000, "terraced", "hard"),
            "A 3-bedroom home",
            "a 3 bed",
        ),
        (
            "I want to buy a 2 bed flat for 400k",
            RENTER,
            ("buy", 400_000, "flat", "soft"),
            "A 2-bedroom home",
            "a 2 bed",
        ),
        (
            "max £350k for a 1 bed flat",
            RENTER,
            ("buy", 350_000, "flat", "hard"),
            "A 1-bedroom home",
            "a 1 bed",
        ),
        (
            "a 2 bed terraced house for about £500,000",
            BUYER,
            ("buy", 500_000, "terraced", "soft"),
            "A 2-bedroom home",
            "a 2 bed",
        ),
        (
            "buying a semi-detached house, 4 bedrooms, 650k",
            RENTER,
            ("buy", 650_000, "semi_detached", "soft"),
            "A home with 4 or more bedrooms",
            "4 bedrooms",
        ),
        ("a 2-bed flat", BUYER, ("buy", None, "flat", "soft"), "A 2-bedroom home", "a 2-bed"),
    ],
)
def test_the_bedrooms_of_a_home_to_buy_are_said_where_the_prompt_is_applied(
    text: str,
    spec: PreferenceSpec,
    applied: tuple[str, int | None, str, str],
    label: str,
    words: str,
):
    result = read(text, spec)
    assert result.status is InterpretStatus.OK
    # All that the search can hold of it is applied, as it was.
    assert held(spec, result) == applied
    # And what it cannot hold is said, in the words of an offer.
    assert not_held(text, result) == [(label, BY_KIND, [words])]
    assert [choice for found in result.suggestions for choice in found.choices] == [IGNORE]
    # Nothing was taken from the words it rests on.
    assert not [taken for taken in rested_on(text, result) if taken in words]
    assert (result.unread, result.asks_nothing, result.unmet) == ((), (), ())


# --- The kind of house of a home to rent ---------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "spec", "applied", "label", "words"),
    [
        (
            "renting a terraced house up to £2,000 a month",
            RENTER,
            ("rent", 2_000, "bed_1", "hard"),
            "A terraced house",
            "a terraced house",
        ),
        (
            "renting a detached house, 4 bed, £4,000 a month",
            RENTER,
            ("rent", 4_000, "bed_4plus", "soft"),
            "A detached house",
            "a detached house",
        ),
        (
            "a 3 bed semi to rent",
            BUYER,
            ("rent", None, "bed_3", "soft"),
            "A semi-detached house",
            "semi",
        ),
        (
            "renting a 2 bed terraced house for £1,900 a month",
            RENTER,
            ("rent", 1_900, "bed_2", "soft"),
            "A terraced house",
            "terraced house",
        ),
    ],
)
def test_the_kind_of_house_of_a_home_to_rent_is_said_where_the_prompt_is_applied(
    text: str,
    spec: PreferenceSpec,
    applied: tuple[str, int | None, str, str],
    label: str,
    words: str,
):
    result = read(text, spec)
    assert result.status is InterpretStatus.OK
    assert held(spec, result) == applied
    assert not_held(text, result) == [(label, BY_BEDROOMS, [words])]
    assert [choice for found in result.suggestions for choice in found.choices] == [IGNORE]
    assert not [taken for taken in rested_on(text, result) if taken in words]
    assert (result.unread, result.asks_nothing, result.unmet) == ((), (), ())


# --- A studio or a room to buy --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "spec", "applied", "label", "words"),
    [
        (
            "buying a studio for 300k",
            RENTER,
            ("buy", 300_000, "flat", "soft"),
            "A studio",
            "a studio",
        ),
        (
            "a room to buy",
            RENTER,
            ("buy", None, "flat", "soft"),
            "A room in a shared home",
            "a room",
        ),
    ],
)
def test_a_studio_or_a_room_to_buy_is_said_where_the_prompt_is_applied(
    text: str,
    spec: PreferenceSpec,
    applied: tuple[str, int | None, str, str],
    label: str,
    words: str,
):
    result = read(text, spec)
    assert result.status is InterpretStatus.OK
    assert held(spec, result) == applied
    assert not_held(text, result) == [(label, TO_RENT_ALONE, [words])]
    assert (result.unread, result.asks_nothing, result.unmet) == ((), (), ())


# --- A home of which nothing can be held ---------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "spec", "label", "note"),
    [
        ("a two bed house", BUYER, "A 2-bedroom home", BY_KIND),
        ("two bedrooms", BUYER, "A 2-bedroom home", BY_KIND),
        ("studio", BUYER, "A studio", TO_RENT_ALONE),
        ("a terraced house", RENTER, "A terraced house", BY_BEDROOMS),
    ],
)
def test_a_home_of_which_nothing_can_be_held_says_why_and_is_not_said_to_be_unread(
    text: str, spec: PreferenceSpec, label: str, note: str
):
    """It was said to be unread, with no word of why, and a model was asked to read it."""
    result = read(text, spec)
    assert result.operations == NO_OPERATIONS
    assert not_held(text, result) == [(label, note, [text])]
    assert (result.unread, result.asks_nothing, result.unmet) == ((), (), ())
    # The status of a plain prompt does not say whether the search is to rent or to buy.
    other = BUYER if spec is RENTER else RENTER
    assert result.status is read(text, other).status is InterpretStatus.OK


def test_the_rest_of_a_plain_prompt_is_applied_beside_a_home_that_is_said_not_to_be_held():
    text = "leafy, a two bed house"
    result = read(text, BUYER)
    assert [edit.tag_id for edit in result.operations.tag_ops] == ["leafy"]
    assert result.operations.count == 1
    assert not_held(text, result) == [("A 2-bedroom home", BY_KIND, ["a two bed house"])]
    assert (result.status, result.unread, result.unmet) == (InterpretStatus.OK, (), ())


@pytest.mark.parametrize(
    ("text", "said_of_it"),
    [
        (
            "quiet, no main roads, a two bed flat to buy for 400k",
            ("A 2-bedroom home", BY_KIND, ["a two bed"]),
        ),
        (
            "no pubs, buying a 3 bed house up to 600k",
            ("A 3-bedroom home", BY_KIND, ["a 3 bed"]),
        ),
        ("no pubs, a studio to buy", ("A studio", TO_RENT_ALONE, ["a studio"])),
        (
            "not too noisy and no main roads, renting a terraced house for £2,000 a month",
            ("A terraced house", BY_BEDROOMS, ["a terraced house"]),
        ),
        (
            "I don't want pubs. I want to buy a 3 bed semi for 500k",
            ("A 3-bedroom home", BY_KIND, ["a 3 bed"]),
        ),
    ],
)
def test_a_wish_that_is_turned_round_beside_a_home_turns_nothing_of_the_home_away(
    text: str, said_of_it: tuple[str, str, list[str]]
):
    """The home is one the grammar took, whatever was turned round before it."""
    result = read(text)
    assert result.status is InterpretStatus.OK
    assert result.operations.budget_ops and result.operations.weight_ops
    assert not_held(text, result) == [said_of_it]
    assert (result.unread, result.asks_nothing, result.unmet) == ((), (), ())


# --- What the search holds is applied, and nothing more is said -----------------------------------


@pytest.mark.parametrize(
    ("text", "spec", "applied"),
    [
        ("a two bed house", RENTER, ("rent", None, "bed_2", "soft")),
        ("studio", RENTER, ("rent", None, "studio", "soft")),
        ("a terraced house", BUYER, ("buy", None, "terraced", "soft")),
        ("a 2 bed flat to rent", BUYER, ("rent", None, "bed_2", "soft")),
        ("renting a 1 bed flat for about £1,700 a month", RENTER, ("rent", 1_700, "bed_1", "soft")),
        ("a three bed house for £2,400 a month", RENTER, ("rent", 2_400, "bed_3", "soft")),
        ("buying a terraced house, about £600k", RENTER, ("buy", 600_000, "terraced", "soft")),
        ("buying a flat, about £400k", RENTER, ("buy", 400_000, "flat", "soft")),
        ("buying a house, about £600k", RENTER, ("buy", 600_000, "terraced", "soft")),
    ],
)
def test_a_home_the_search_holds_whole_is_applied_and_nothing_is_said_of_it(
    text: str, spec: PreferenceSpec, applied: tuple[str, int | None, str, str]
):
    result = read(text, spec)
    assert held(spec, result) == applied
    assert (result.status, result.suggestions) == (InterpretStatus.OK, ())
    assert (result.unread, result.unmet) == ((), ())


@pytest.mark.parametrize(
    "text",
    [
        "buying a 3 bed house up to 600k",
        "I want to buy a 2 bed flat for 400k",
        "renting a terraced house up to £2,000 a month",
        "renting a detached house, 4 bed, £4,000 a month",
        "buying a studio for 300k",
        "a two bed house",
        "a terraced house",
    ],
)
def test_nothing_of_a_prompt_that_is_applied_is_left_for_a_model_to_read(text: str):
    """A model is asked where words were left unread, and what it reads is applied by nobody."""
    for spec in (RENTER, BUYER):
        result = read(text, spec)
        assert result.status is InterpretStatus.OK
        assert (result.unread, result.asks_nothing) == ((), ())
        assert UnmetCategory.OTHER not in result.unmet


# --- Two sizes, or two kinds ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "offered"),
    [
        (
            "renting a 2 bed or a 3 bed for £2,000",
            ["Set a 2-bedroom home", "Set a 3-bedroom home"],
        ),
        (
            "renting a studio or a 1 bed for £1,200",
            ["Set a studio", "Set a 1-bedroom home"],
        ),
        (
            "buying a flat or a terraced house for 400k",
            ["Set a flat, to buy", "Set a terraced house, to buy"],
        ),
        (
            "buying a 2 bed terraced house, 500k, or a semi",
            ["Set a terraced house, to buy", "Set a semi-detached house, to buy"],
        ),
    ],
)
def test_two_sizes_or_two_kinds_of_home_are_not_plain_and_each_is_offered(
    text: str, offered: list[str]
):
    """One was applied, and the other was in no list. Nobody can say which is meant."""
    result = read(text)
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    homes = [
        choice.label
        for found in result.suggestions
        if found.target == "budget" and "budget of" not in found.label
        for choice in found.choices
        if choice is not IGNORE
    ]
    assert homes == offered


def test_two_sizes_after_a_wish_that_is_turned_round_are_not_plain_either():
    """The first was applied, and the second was in no list, as where nothing was turned."""
    text = "quiet, no main roads, a two bed or a three bed to rent"
    result = read(text)
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    # Each is offered or is said to be unread: what is offered after a word that turns is
    # the offers' own to say, and neither size is in no list.
    listed = [
        *(text[span.start : span.end] for found in result.suggestions for span in found.spans),
        *(text[span.start : span.end] for span in result.unread),
    ]
    for size in ("two bed", "three bed"):
        assert [words for words in listed if size in words], size


@pytest.mark.parametrize(
    ("text", "spec", "held_of_it", "rests_on"),
    [
        (
            "I can pay up to £1,300 for a studio or a one bed",
            RENTER,
            ("unchanged", 1_300, "hard"),
            ["up to £1,300"],
        ),
        (
            "buying a flat or a terraced house for 400k",
            RENTER,
            ("buy", 400_000, "unchanged"),
            ["buying", "400k"],
        ),
        (
            "renting a 2 bed or a 3 bed, leafy",
            BUYER,
            ("rent", 0, "unchanged"),
            ["renting", "leafy"],
        ),
    ],
)
def test_of_two_sizes_the_rest_of_what_was_said_is_still_what_the_reader_makes_of_it(
    text: str, spec: PreferenceSpec, held_of_it: tuple[str, int, str], rests_on: list[str]
):
    """For whoever holds a guess to the reader's own reading: the budget is as plainly said.

    Nobody can say which of two sizes is meant, so neither is the reader's
    reading. The amount beside them was marked as what one press may take,
    and is still.
    """
    request = InterpretRequest(text=text, spec=spec, release=small_release())
    alone = READER.by_sentence(request)
    (edit,) = alone.operations.budget_ops
    assert (edit.tenure, edit.amount, edit.strictness) == held_of_it
    assert edit.segment == "unchanged"
    assert sorted(text[found.start : found.end] for found in alone.rests_on) == sorted(rests_on)
    # The reader itself applies none of it.
    assert READER.interpret(request).operations == NO_OPERATIONS


@pytest.mark.parametrize(
    "text",
    [
        "I want to buy a 2 bed flat for 400k",
        "renting a terraced house up to £2,000 a month",
        "a two bed house",
        "no pubs, a studio to buy",
    ],
)
def test_what_the_reader_makes_of_each_sentence_of_a_plain_prompt_is_its_answer(text: str):
    for spec in (RENTER, BUYER):
        request = InterpretRequest(text=text, spec=spec, release=small_release())
        assert READER.by_sentence(request) == READER.interpret(request)


@pytest.mark.parametrize(
    ("text", "segment"),
    [
        ("renting a 2 bed flat, 2 bedrooms, £2,000 a month", "bed_2"),
        ("buying a flat, 400k, an apartment", "flat"),
    ],
)
def test_one_size_or_one_kind_said_twice_is_said_once(text: str, segment: str):
    result = read(text)
    assert result.status is InterpretStatus.OK
    (edit,) = result.operations.budget_ops
    assert edit.segment == segment
