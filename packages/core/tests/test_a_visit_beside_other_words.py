"""A visit is read where its words stand beside what else is wished, with no mark between.

The service was driven with the sentences of somebody who looks for a hotel or
a short stay. "A hotel, somewhere lively" made the search a visit, and "a hotel
somewhere lively" left it a search for a home to rent: "a hotel somewhere" was
said to be unread, and the rest was offered as to a renter. So did "city
break", "weekend trip" and "a weekend away", which are what a visit is called,
"tourist", who a visitor is, "short stay" and "where to stay", and a hotel that
is wanted "nearby".

Each is read now. "Somewhere" opens a wish after the words of a visit as it
does after a mark, and the words of a visit are still a closed list: what says
something else says it as it did (`test_a_visit_in_words.py`).

And a search that is a visit already is not offered a visit again. Nobody is a
visitor until they say so, so there is nothing for them to choose: the words
were heard, and are not said to be unread.

Every name and every sentence here is made up, and the first list is the
sentences the service was driven with.
"""

import pytest
from burro_core.ids import InterpretStatus, Notice, Provenance, Tenure, TenureChoice
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.reducer import apply
from burro_core.spec import NO_BUDGET, PreferenceSpec, default_spec

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
VISITOR = default_spec(Tenure.VISIT)
READER = RuleInterpreter()
PLACES = {place.name: place.place_id for place in fixture_release().places}


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=fixture_release()))


def asked(result: InterpretResult) -> set[str]:
    """What a reading applies beside the kind of search: each thing, and each place to reach."""
    edits = result.operations
    return {
        *(f"feature:{edit.feature_id.value}" for edit in edits.weight_ops),
        *(f"tag:{edit.tag_id.value}" for edit in edits.tag_ops),
        *(f"journey:{edit.place_id}" for edit in edits.commute_ops),
    }


def offers_a_visit(result: InterpretResult) -> list[str]:
    """The labels of the offers that would make the search a visit."""
    return [
        found.label
        for found in result.suggestions
        for choice in found.choices
        for edit in choice.operations.budget_ops
        if edit.tenure is TenureChoice.VISIT
    ]


def unread(text: str, result: InterpretResult) -> list[str]:
    return [text[span.start : span.end] for span in result.unread]


CULTURE = "feature:culture_venues_per_homes"
DRIVEN = [
    ("a hotel somewhere lively", {"tag:pace"}),
    ("a hotel somewhere", set[str]()),
    ("city break, lively, near a station", {"tag:pace", "feature:station_walk"}),
    ("weekend trip, near museums and good food", {CULTURE, "tag:foodie"}),
    ("a weekend away, near museums", {CULTURE}),
    ("a weekend away", set[str]()),
    ("tourist, 3 nights, near museums", {CULTURE}),
    ("short stay near Pellam Cross", {f"journey:{PLACES['Pellam Cross']}"}),
    ("where to stay in London", set[str]()),
]
MORE = [
    # "Somewhere" and "anywhere" open a wish after the words of a visit.
    ("a hotel somewhere leafy and quiet", {"tag:leafy", "tag:quiet_residential"}),
    ("visiting for a weekend somewhere lively", {"tag:pace"}),
    ("a city break somewhere with a park nearby", {"feature:park_proximity"}),
    ("I need a hotel somewhere near a station", {"feature:station_walk"}),
    # A visit by what it is called, with no article.
    ("city break", set[str]()),
    ("weekend break, near a park", {"feature:park_proximity"}),
    ("day trip", set[str]()),
    ("a night away", set[str]()),
    ("weekend away, near a station", {"feature:station_walk"}),
    ("a short stay", set[str]()),
    ("a weekend stay near a park", {"feature:park_proximity"}),
    ("I'm a tourist", set[str]()),
    ("where to stay", set[str]()),
    # How long the stay is, in a part of its own beside the visit.
    ("a hotel, 3 nights", set[str]()),
    ("visiting, for a weekend, near a park", {"feature:park_proximity"}),
    # A hotel that is wanted near, with nothing said of what it is near.
    ("I need a hotel nearby", set[str]()),
    ("a hotel close by", set[str]()),
]


@pytest.mark.parametrize(("text", "wished"), [*DRIVEN, *MORE])
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renting", "buying"])
def test_a_visit_is_read_with_what_is_wished_beside_it(
    text: str, wished: set[str], spec: PreferenceSpec
):
    result = read(text, spec)
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    (edit,) = result.operations.budget_ops
    assert (edit.tenure, edit.amount, edit.segment) == (TenureChoice.VISIT, 0, "unchanged")
    assert asked(result) == wished
    assert (result.suggestions, result.unread, result.unmet) == ((), (), ())
    left = apply(spec, result.operations, fixture_release())
    assert left.rejected == ()
    assert left.spec.tenure is Tenure.VISIT and left.spec.budget == NO_BUDGET


OFFERED = [
    # A word that is only offered makes the sentence one that is not plain.
    ("a hotel somewhere affluent", "hotel", set[str]()),
    # The sentence the service was driven with: a place to reach, and a hotel near it.
    (
        "I'm coming for a conference at Cindermoor Works and need a hotel nearby",
        "hotel",
        {"Cindermoor Works"},
    ),
    ("honestly, a weekend away near a park", "a weekend away", set[str]()),
    ("zebra, city break", "city break", set[str]()),
    ("zebra, weekend trip", "weekend trip", set[str]()),
    ("zebra, where to stay", "where to stay", set[str]()),
    ("zebra, short stay", "short stay", set[str]()),
    ("I'm a tourist, honestly", "a tourist", set[str]()),
]


@pytest.mark.parametrize(("text", "words", "journeys"), OFFERED)
def test_in_a_sentence_that_is_not_plain_the_visit_is_offered(
    text: str, words: str, journeys: set[str]
):
    result = read(text)
    assert result.operations.budget_ops == ()
    assert offers_a_visit(result) == ["Visiting"]
    (visit,) = (found for found in result.suggestions if found.target == "tenure")
    assert words in [text[span.start : span.end] for span in visit.spans]
    assert {found.label for found in result.suggestions if found.target == "commute"} == journeys
    # No word of the visit is said to be unread.
    assert not [left for left in unread(text, result) if "hotel" in left or words in left]


def test_how_long_the_stay_is_stands_with_the_visit_it_is_said_beside():
    """ "3 nights" in a part of its own was said to be unread, beside a visit that was read."""
    text = "zebra, a hotel, 3 nights"
    result = read(text)
    (visit,) = (found for found in result.suggestions if found.target == "tenure")
    # The offer rests on the words for the visit, as it did, so that what is said of it
    # is asked of those words alone. How long the stay is was heard.
    assert [text[span.start : span.end] for span in visit.spans] == ["hotel"]
    assert unread(text, result) == ["zebra, a"]
    # Where nothing says a visit, it is said to be unread, as it was.
    assert unread("zebra, 3 nights", read("zebra, 3 nights")) == ["zebra, 3 nights"]
    # And it was heard where the search is a visit already.
    assert unread("zebra, 3 nights", read("zebra, 3 nights", VISITOR)) == ["zebra"]


STILL_NO_VISIT = [
    # How long, where nothing says a visit.
    "3 nights",
    "a weekend",
    "leafy, 3 nights",
    # Away, where it is how far off something is, or what is kept away from.
    "a long way away",
    "30 minutes away from Pellam Cross",
    "away from the station",
    "a weekend away from my mother",
    # Who visits somewhere, and is not the speaker.
    "popular with tourists",
    "no tourists",
    "away from the tourists",
    "a tourist trap",
    # To stay, which is as often to remain.
    "to stay near my job",
    "I want to stay somewhere leafy",
    "a long stay",
    # Somewhere, after what is no visit.
    "visiting my mother somewhere leafy",
    "a holiday home somewhere quiet",
]


@pytest.mark.parametrize("text", STILL_NO_VISIT)
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renting", "buying"])
def test_what_says_something_else_makes_no_search_a_visit(text: str, spec: PreferenceSpec):
    result = read(text, spec)
    assert not [edit for edit in result.operations.budget_ops if edit.tenure == "visit"]
    assert offers_a_visit(result) == []
    assert apply(spec, result.operations, fixture_release()).spec.tenure is spec.tenure


def test_a_weekend_away_near_a_place_keeps_nobody_away_from_it():
    """ "Away" is a word for far anywhere else, and a place beside one is no place to reach."""
    for text in ("a weekend away near Cindermoor Works", "zebra, a weekend away near Pellam Cross"):
        result = read(text)
        journeys = [
            edit.place_id
            for choices in (
                [result.operations],
                *([choice.operations for choice in found.choices] for found in result.suggestions),
            )
            for operations in choices
            for edit in operations.commute_ops
        ]
        assert len(journeys) == 1
        assert not [found for found in result.suggestions if not found.choices[:-1]]


# A search that is a visit already

ON_A_VISIT = [
    "a hotel for £150 a night, honestly",
    "a hotel, honestly",
    "visiting, honestly",
    "honestly, a hotel near a park",
    "We are planning a trip and want somewhere leafy",
    "a hotel somewhere affluent",
]


@pytest.mark.parametrize("text", ON_A_VISIT)
@pytest.mark.parametrize(
    "chosen_by", [Provenance.DEFAULT, Provenance.UI_EDIT, Provenance.STATED], ids=str
)
def test_a_search_that_is_a_visit_already_is_not_offered_a_visit_again(
    text: str, chosen_by: Provenance
):
    result = read(text, VISITOR.replace(tenure_from=chosen_by))
    assert offers_a_visit(result) == []
    assert "tenure" not in {found.target for found in result.suggestions}
    # The words were heard: none of them is said to be unread.
    left = " ".join(unread(text, result))
    assert not [word for word in ("hotel", "visiting", "trip") if word in left]


def test_to_say_a_visit_plainly_on_a_visit_is_still_to_choose_it():
    """A plain sentence is applied, and says who chose the kind of search. Nothing else moves."""
    result = read("a hotel somewhere", VISITOR)
    left = apply(VISITOR, result.operations, fixture_release())
    assert left.spec == VISITOR.replace(tenure_from=Provenance.STATED)


def test_a_renter_is_still_offered_a_visit_and_a_home_to_rent():
    assert offers_a_visit(read("honestly, a hotel near a park", RENTER)) == ["Visiting"]
    offered = {found.label for found in read("renting, honestly", RENTER).suggestions}
    assert offered == {"Renting"}
