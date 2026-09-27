"""A visit, as a person types one.

A sentence that says a person is visiting makes the search a visit: "visiting",
"a trip", "a hotel", "somewhere to stay", "staying for a weekend". It is read
where the words say a visit and nothing else. "Visiting my mother" says what
the speaker does and not what they are looking for, "a holiday home" is a home,
and "I work at a hotel" is a workplace, so none of them makes a search a visit.

A visit holds no budget and no home. What a person types of either is said, in
the words Burro has for what it cannot hold, and is never applied. What a night
costs is no budget: Burro holds no price of a stay.

Every name and figure here is made up.
"""

import pytest
from burro_core.grammar import KNOWN_WORDS, LODGINGS, NIGHTS, STAYS, VISITS, VOCABULARY
from burro_core.ids import (
    InterpretStatus,
    Notice,
    Provenance,
    Tenure,
    TenureChoice,
    UnmetCategory,
)
from burro_core.interpret import (
    IGNORE,
    MAY_BE_ANOTHERS,
    NO_BUDGET_ON_A_VISIT,
    NO_HOME_ON_A_VISIT,
    NOTICES,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.reducer import ReducerResult, apply
from burro_core.spec import NO_BUDGET, PreferenceSpec, default_spec
from burro_core.vocabulary import OF_A_PERIOD, WORDS_OF_DOUBT

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
VISITOR = default_spec(Tenure.VISIT)
READER = RuleInterpreter()
(PELLAM_CROSS,) = (
    place.place_id for place in fixture_release().places if place.name == "Pellam Cross"
)


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=fixture_release()))


def applied(text: str, spec: PreferenceSpec = RENTER) -> ReducerResult:
    """The search as the service would leave it: the edits of the reading, through the reducer."""
    return apply(spec, read(text, spec).operations, fixture_release())


def tenures(result: InterpretResult) -> list[TenureChoice]:
    return [
        edit.tenure
        for edit in result.operations.budget_ops
        if edit.tenure is not TenureChoice.UNCHANGED
    ]


def offered(result: InterpretResult) -> dict[str, str]:
    """What is offered, by its target, with the label of each."""
    return {found.target: found.label for found in result.suggestions}


def offers_a_visit(result: InterpretResult) -> bool:
    return any(
        edit.tenure is TenureChoice.VISIT
        for found in result.suggestions
        for choice in found.choices
        for edit in choice.operations.budget_ops
    )


def rested_on(text: str, result: InterpretResult) -> list[str]:
    return [text[rests.start : rests.end] for rests in result.rests_on]


# The words

SAYS_A_VISIT = [
    "visiting",
    "Visiting",
    "I'm visiting",
    "we are visiting",
    "I am visiting",
    "I want to visit",
    "looking to visit",
    "visiting for a weekend",
    "I'm visiting for 3 nights",
    "we're visiting for the weekend",
    "visiting for two days",
    "a visit",
    "a short visit",
    "a weekend visit",
    "on a visit",
    "a trip",
    "a weekend trip",
    "a day trip",
    "our trip",
    "a city break",
    "a weekend break",
    "on holiday",
    "a holiday",
    "holiday",
    "on holiday for a week",
    "a hotel",
    "hotel",
    "hotels",
    "I need a hotel",
    "looking for a hotel",
    "find me a hotel",
    "a hotel for 3 nights",
    "a hostel",
    "a b&b",
    "a bed and breakfast",
    "a guest house",
    "an airbnb",
    "somewhere to stay",
    "looking for somewhere to stay",
    "I need somewhere to stay",
    "a place to stay",
    "an area to stay in",
    "staying for a weekend",
    "I'm staying for two nights",
    "we are staying for a week",
    "staying overnight",
    "staying in a hotel",
    "I'm staying at a hotel",
    "I want to stay for a weekend",
    "to stay for a fortnight",
    # The city itself is what is visited.
    "I'm visiting London",
    "visiting London for a weekend",
    "visiting for a weekend in London",
    "I'm visiting the city for a weekend",
    "a trip to London",
    "a weekend trip to London",
    "a hotel in London",
    "on holiday in London for a week",
    "somewhere to stay in London",
    "staying in London for 3 nights",
]


@pytest.mark.parametrize("text", SAYS_A_VISIT)
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renting", "buying"])
def test_a_sentence_that_says_a_visit_makes_the_search_one(text: str, spec: PreferenceSpec):
    result = read(text, spec)
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert tenures(result) == [TenureChoice.VISIT]
    assert (result.unmet, result.unread, result.suggestions) == ((), (), ())
    # One edit, which says the kind of search and nothing of a budget or a home.
    (edit,) = result.operations.budget_ops
    assert (edit.amount, edit.segment, edit.strictness) == (0, "unchanged", "unchanged")
    assert result.operations.replace(budget_ops=()) == NO_OPERATIONS
    # It rests on words of the sentence, and the search it leaves is a visit.
    assert rested_on(text, result) and all(rested_on(text, result))
    left = applied(text, spec)
    assert left.rejected == ()
    assert left.spec.tenure is Tenure.VISIT and left.spec.budget == NO_BUDGET
    # Nothing is assumed of a home that a visit does not hold.
    assert result.assumptions == ()


@pytest.mark.parametrize("text", ["visiting", "a hotel", "somewhere to stay", "on holiday"])
def test_to_say_a_visit_on_a_visit_is_to_choose_it_and_changes_nothing_else(text: str):
    left = applied(text, VISITOR)
    assert left.rejected == () and [found.changed for found in left.applied] == [True]
    assert left.spec == VISITOR.replace(tenure_from=left.spec.tenure_from)
    assert left.spec.tenure_from == "stated"


@pytest.mark.parametrize(
    ("text", "asked"),
    [
        ("visiting for a weekend, leafy and near a station", {"tag:leafy", "station"}),
        ("a hotel, near a park", {"park"}),
        ("on holiday, somewhere leafy", {"tag:leafy"}),
        ("I'm visiting and I want a park nearby", {"park"}),
        ("somewhere to stay, with a park nearby", {"park"}),
        ("leafy, near a park, staying for 3 nights", {"tag:leafy", "park"}),
    ],
)
def test_a_visit_is_read_beside_what_else_is_asked_for(text: str, asked: set[str]):
    result = read(text)
    assert result.status is InterpretStatus.OK and tenures(result) == [TenureChoice.VISIT]
    wished = {f"tag:{edit.tag_id.value}" for edit in result.operations.tag_ops}
    wished |= {
        "park" if "park" in edit.feature_id.value else "station"
        for edit in result.operations.weight_ops
    }
    assert wished == asked
    left = applied(text)
    assert left.rejected == () and left.spec.visiting


def test_a_hotel_near_a_place_is_a_visit_and_a_journey_to_the_place():
    for text in ("a hotel near Pellam Cross", "somewhere to stay close to Pellam Cross"):
        result = read(text)
        assert result.status is InterpretStatus.OK and tenures(result) == [TenureChoice.VISIT]
        assert [edit.place_id for edit in result.operations.commute_ops] == [PELLAM_CROSS]
        left = applied(text).spec
        assert left.visiting and [c.place_id for c in left.commutes] == [PELLAM_CROSS]


# What says something else

NO_VISIT = [
    # What the speaker does, and whom they visit: it says nothing of what they look for.
    "Visiting my mother in Pellam Cross",
    "visiting my mum",
    "visiting friends",
    "visiting family at the weekend",
    "I like visiting the park",
    "visiting hours",
    "a visit to my mother",
    "a trip to work",
    "my trip to work",
    "a trip to see my sister",
    # A home, a job or a day, by a word that is also a word for a visit.
    "a holiday home",
    "a holiday let",
    "holiday cottage",
    "bank holiday",
    "hotel work",
    "a hotel job",
    "I work at a hotel",
    "I work in a hotel",
    "my office is near a hotel",
    "near a hotel",
    "close to my hotel",
    # Somebody else's visit.
    "my mum is visiting",
    "my sister is staying for a weekend",
    "my parents need a hotel",
    "her hotel",
    # What is over, and what is turned away.
    "I was visiting",
    "no hotels",
    "not visiting",
    "not a hotel",
    "I don't want a hotel",
    "without a hotel",
    # To stay, with nothing of how long or where: it is as often to remain.
    "staying",
    "staying put",
    "I want to stay",
    "stay",
    "to stay near my job",
    "staying in London",
    "I want to stay in London",
    # The city, where nothing says a visit.
    "London",
    "I work in London",
    "I live in London",
    "outside London",
    "visiting London Road",
    # A length of time alone, and a time that is the length of a journey.
    "a weekend",
    "3 nights",
    "for a week",
    "a 20 minute trip to Pellam Cross",
]


@pytest.mark.parametrize("text", NO_VISIT)
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renting", "buying"])
def test_a_word_for_a_visit_that_says_something_else_makes_no_search_a_visit(
    text: str, spec: PreferenceSpec
):
    result = read(text, spec)
    assert TenureChoice.VISIT not in tenures(result)
    assert not offers_a_visit(result)
    left = applied(text, spec).spec
    assert left.tenure is spec.tenure and left.budget == spec.budget


def test_a_place_that_is_visited_is_offered_as_any_place_that_is_named():
    """ "Visiting my mother in Pellam Cross" names a place, and no kind of search.

    The place is offered as the rules offer any name that stands beside
    somebody else: as a journey that may be somebody else's, which no press
    takes with others. So is a name that is an area's too. It was offered as
    a rule for the area, to look only there or to leave it out, which is
    neither of them what was said (`test_a_name_that_is_an_areas_too.py`).
    """
    text = "Visiting my mother in Cindermoor Works"
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert offered(result) == {"commute": "Cindermoor Works"}
    (journey,) = result.suggestions
    assert journey.note == MAY_BE_ANOTHERS
    (add, leave) = journey.choices
    assert [edit.max_minutes for edit in add.operations.commute_ops] == [0]
    assert leave == IGNORE
    theirs = read("Visiting my mother in Pellam Cross")
    assert offered(theirs) == {"commute": "Pellam Cross"}
    assert [found.note for found in theirs.suggestions] == [MAY_BE_ANOTHERS]
    # The length of a journey is a journey, as it was.
    trip = read("a 20 minute trip to Pellam Cross")
    assert [e.place_id for e in trip.operations.commute_ops] == [PELLAM_CROSS]
    assert [e.max_minutes for e in trip.operations.commute_ops] == [20]
    assert trip.operations.budget_ops == ()


NOTICED = [
    ("We are planning a trip and want somewhere leafy", "a trip"),
    ("thinking about a city break, somewhere leafy", "a city break"),
    ("I'm visiting for a weekend with my dog, zebra", "visiting for a weekend"),
    ("zebra, but I need a hotel", "hotel"),
    ("Coming to town on holiday for a week", "on holiday for a week"),
    ("visiting Pellam Cross", "visiting"),
    # A visit that may be over is the person's to say, as any wish that may be over is.
    ("we were on holiday", "on holiday"),
    # A word that only says how much of a visit it is stands before it, and changes nothing.
    ("just visiting, zebra", "visiting"),
    ("I'm only visiting for a weekend, honestly", "visiting for a weekend"),
    # What Burro has no measure of, and what it has, may stand straight after.
    ("zebra, a hotel outside London", "hotel"),
    ("zebra, a hotel parking nearby", "hotel"),
]


@pytest.mark.parametrize(("text", "words"), NOTICED)
def test_in_a_sentence_that_is_not_plain_a_visit_is_offered_and_not_applied(text: str, words: str):
    result = read(text)
    assert result.operations.budget_ops == ()
    assert result.status is InterpretStatus.SUGGEST
    (visit,) = (found for found in result.suggestions if found.target == "tenure")
    assert visit.label == "Visiting" and visit.note == ""
    assert [text[span.start : span.end] for span in visit.spans] == [words]
    (take, leave) = visit.choices
    assert (take.label, leave) == ("Set visiting", IGNORE)
    (edit,) = take.operations.budget_ops
    assert (edit.tenure, edit.amount, edit.segment) == ("visit", 0, "unchanged")
    assert edit.provenance == "ui_edit"
    pressed = apply(RENTER, take.operations, fixture_release())
    assert pressed.rejected == () and pressed.spec.visiting


def test_a_visit_is_not_offered_where_the_person_chose_one_already():
    text = "We are planning a trip and want somewhere leafy"
    chosen = VISITOR.replace(tenure_from=Provenance.UI_EDIT)
    result = read(text, chosen)
    assert "tenure" not in offered(result)
    # The words were heard: nothing of them is said to be unread.
    assert not any("trip" in text[span.start : span.end] for span in result.unread)


@pytest.mark.parametrize(
    "text",
    ["renting or visiting", "a hotel or a flat to rent", "buying, or maybe just a visit"],
)
def test_two_kinds_of_search_in_one_prompt_are_the_persons_to_choose_between(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert "tenure" in offered(result)
    assert applied(text).spec == RENTER


# A visit holds no budget and no home, and says so


def test_an_amount_beside_a_visit_is_said_to_be_what_a_visit_cannot_hold():
    text = "visiting for a weekend, up to £2,000"
    result = read(text)
    assert result.status is InterpretStatus.OK and tenures(result) == [TenureChoice.VISIT]
    # No edit holds the amount, so none is turned away: it is said in words of Burro's own.
    (visit,) = result.operations.budget_ops
    assert (visit.tenure, visit.amount, visit.strictness) == ("visit", 0, "unchanged")
    (amount,) = result.suggestions
    assert (amount.target, amount.label) == ("budget", "A budget of £2,000")
    assert (amount.note, amount.choices) == (NO_BUDGET_ON_A_VISIT, (IGNORE,))
    assert [text[span.start : span.end] for span in amount.spans] == ["up to £2,000"]
    assert result.unread == () and result.not_in_release == ()
    left = applied(text)
    assert left.rejected == () and left.spec.visiting and left.spec.budget == NO_BUDGET


@pytest.mark.parametrize(
    ("text", "label", "words"),
    [
        ("visiting, a 2 bed flat", "A flat", "a 2 bed flat"),
        ("a hotel, 3 bedrooms", "A 3-bedroom home", "3 bedrooms"),
        ("on holiday, a studio", "A studio", "a studio"),
        ("a terraced house, staying for a week", "A terraced house", "a terraced house"),
    ],
)
def test_a_home_beside_a_visit_is_said_to_be_what_a_visit_cannot_hold(
    text: str, label: str, words: str
):
    result = read(text)
    assert result.status is InterpretStatus.OK and tenures(result) == [TenureChoice.VISIT]
    (home,) = result.suggestions
    assert (home.target, home.label, home.note) == ("budget", label, NO_HOME_ON_A_VISIT)
    assert home.choices == (IGNORE,)
    assert [text[span.start : span.end] for span in home.spans] == [words]
    assert result.unread == () and UnmetCategory.OTHER not in result.unmet
    left = applied(text)
    assert left.rejected == () and left.spec.budget == NO_BUDGET


@pytest.mark.parametrize(
    ("text", "label"),
    [
        ("a 2 bed flat", "A flat"),
        ("3 bedrooms", "A 3-bedroom home"),
        ("a studio", "A studio"),
        ("a terraced house", "A terraced house"),
        ("a room", "A room in a shared home"),
    ],
)
def test_a_home_that_is_named_on_a_visit_is_said_and_never_set(text: str, label: str):
    result = read(text, VISITOR)
    assert result.operations == NO_OPERATIONS
    (home,) = result.suggestions
    assert (home.target, home.label, home.note) == ("budget", label, NO_HOME_ON_A_VISIT)
    assert home.choices == (IGNORE,)
    assert result.unread == () and UnmetCategory.OTHER not in result.unmet
    assert applied(text, VISITOR).spec == VISITOR


def test_an_amount_on_a_visit_is_not_held_unless_the_words_say_what_it_is_of():
    # An amount alone may be what the visit may cost. It is of no home, and is not held.
    for text, label in (
        ("up to £1,500", "A budget of £1,500"),
        ("a budget of £2000", "A budget of £2,000"),
        ("£450,000", "A budget of £450,000"),
    ):
        result = read(text, VISITOR)
        assert result.operations == NO_OPERATIONS
        (amount,) = result.suggestions
        assert (amount.target, amount.label) == ("budget", label)
        assert (amount.note, amount.choices) == (NO_BUDGET_ON_A_VISIT, (IGNORE,))
        assert result.unread == () and result.not_in_release == ()
        assert applied(text, VISITOR).spec == VISITOR
    # By the month it is a rent, and the words for renting and buying say which they mean.
    rent = applied("up to £1,500 a month", VISITOR).spec
    assert (rent.tenure, rent.budget.amount, rent.budget.strictness) == ("rent", 1500, "hard")
    renting = applied("renting a 2 bed up to £1,500", VISITOR).spec
    assert (renting.tenure, renting.budget.amount) == ("rent", 1500)
    assert renting.budget.segment == "bed_2"
    buying = applied("buying a flat, max £400k", VISITOR).spec
    assert (buying.tenure, buying.budget.amount, buying.budget.segment) == ("buy", 400_000, "flat")


def test_what_is_asked_of_the_place_is_read_on_a_visit_as_on_any_search():
    left = applied("leafy and quiet, near a park", VISITOR)
    assert left.rejected == () and left.spec.visiting
    assert {tag.tag_id for tag in left.spec.tags} == {"leafy", "quiet_residential"}
    there = applied("30 minutes to Pellam Cross", VISITOR).spec
    assert there.visiting and [c.max_minutes for c in there.commutes] == [30]


# What a night costs

BY_THE_NIGHT = [
    ("£150 a night", "£150 a night"),
    ("£150 per night", "£150 per night"),
    ("up to £150 a night", "£150 a night"),
    ("150 quid a night", "150 quid a night"),
    ("£150 nightly", "£150 nightly"),
    ("£150 each night", "£150 each night"),
    ("£90 for one night", "£90 for one night"),
]


@pytest.mark.parametrize(("text", "words"), BY_THE_NIGHT)
@pytest.mark.parametrize("spec", [RENTER, BUYER, VISITOR], ids=["renting", "buying", "visiting"])
def test_what_a_night_costs_is_no_budget_and_is_said_to_be_what_burro_cannot_hold(
    text: str, words: str, spec: PreferenceSpec
):
    result = read(text, spec)
    assert result.operations == NO_OPERATIONS
    assert "budget" not in offered(result)
    assert UnmetCategory.PRICES_AND_HOURS in result.unmet
    # The amount was heard, with the night it is paid by: it is not said to be unread.
    unread = [text[span.start : span.end] for span in result.unread]
    assert not any(part in one for one in unread for part in words.split())
    assert applied(text, spec).spec == spec


def test_a_hotel_at_so_much_a_night_is_a_visit_with_no_budget():
    text = "a hotel for £150 a night near Pellam Cross"
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert offered(result) == {"tenure": "Visiting", "commute": "Pellam Cross"}
    assert UnmetCategory.PRICES_AND_HOURS in result.unmet
    assert [text[span.start : span.end] for span in result.unread] == []


@pytest.mark.parametrize(
    "text",
    ["£350 a week", "350pw", "£18,000 a year", "£700 a fortnight", "£9,000 for 6 months"],
)
def test_an_amount_by_any_other_period_is_as_it_was(text: str):
    """The week is worked out by the month and offered. The rest is not read."""
    result = read(text)
    assert UnmetCategory.PRICES_AND_HOURS not in result.unmet
    assert result.operations == NO_OPERATIONS


@pytest.mark.parametrize(
    "text",
    [
        "staying for a week at £350",
        "£350 staying for a week",
        "visiting for a week, £350",
        "a hotel for 3 nights, £400",
    ],
)
def test_an_amount_beside_how_long_a_stay_is_never_an_amount_by_that_period(text: str):
    """How long a stay is is no period an amount is paid by: no amount is set by it."""
    for spec in (RENTER, BUYER, VISITOR):
        left = applied(text, spec).spec
        assert left.budget.amount is None


def test_what_burro_says_it_is_for_holds_a_visit_too():
    """It is said where nothing that was typed is about a place to live or to stay."""
    assert NOTICES[Notice.OFF_TOPIC] == (
        "Burro helps you choose where to live, or where to stay on a visit. Tell it what you "
        "want from a place, or choose your space requirements to build your search without "
        "typing."
    )
    # The founder named them "Space requirements", and no page says "the settings".
    assert "settings" not in NOTICES[Notice.OFF_TOPIC]


# The vocabulary


def test_the_name_of_the_city_is_no_word_of_the_grammar_and_names_no_place_by_itself():
    """ "London" is read as what is visited, after a word for a visit, and nowhere else.

    A place that a person names after "I work at" may begin with it, and is
    asked about as any place the release does not hold: a word of the grammar
    there would end the name before it began.
    """
    assert not {"london", "capital"} & KNOWN_WORDS
    asked = read("I work at London Zoo")
    assert asked.status is InterpretStatus.CLARIFY and asked.clarify is not None
    (journey,) = asked.operations.commute_ops
    assert journey.place_id == "" and tenures(asked) == []


def test_the_words_for_a_visit_are_closed_lists_and_none_is_a_word_of_doubt():
    every = VISITS | STAYS | LODGINGS
    assert every <= VOCABULARY
    words = {word for phrase in every for word in phrase.split()}
    assert words <= KNOWN_WORDS
    assert not (words | NIGHTS) & WORDS_OF_DOUBT
    assert LODGINGS <= VISITS and not STAYS & VISITS
    # To stay is a visit only with how long or where, and a trip is a journey too: none
    # of these says a visit by itself.
    assert not {"stay", "staying", "to stay", "trip", "break", "weekend"} & VISITS
    # How long a stay is, is said in words for a period, and in no word for a month. No
    # word for a period is a word of the grammar: each is read as part of its visit alone.
    assert NIGHTS <= OF_A_PERIOD and not {"month", "months"} & NIGHTS
    assert not (NIGHTS | {"overnight"}) & KNOWN_WORDS
    for alone in ("a weekend", "3 nights", "for a week", "overnight", "leafy for a week"):
        result = read(alone)
        assert result.operations == NO_OPERATIONS
        assert UnmetCategory.OTHER in result.unmet
