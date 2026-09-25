import dataclasses
from typing import Any

import pytest
from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    FEATURES,
    GRITTY,
    HOLDS_RESIDENTS,
    NUISANCES,
    RANKED_AS,
    ROUGH_GUIDES,
    TAGS,
    Tag,
    tags_of,
)
from burro_core.ids import (
    AssumptionCode,
    EditProvenance,
    FeatureId,
    FeatureKind,
    GrittyVariant,
    InterpreterName,
    InterpretStatus,
    Notice,
    OpsGroup,
    PlaceKind,
    Polarity,
    RejectReason,
    SuggestionDirection,
    TagId,
    TagShape,
    Tenure,
    UnmetCategory,
)
from burro_core.interpret import (
    LEXICON,
    NOTICES,
    POLICY_LEXICON,
    Interpreter,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    assumptions_for,
    not_in_release_of,
    prepare,
    sentences_of,
)
from burro_core.lexicon import (
    COUNTED_AT_THE_CENSUS,
    ENDS_NAMED_AS_HOMES,
    HOME_WORDS,
    WHAT_AGE,
    WHO_IS_COUNTED,
    counts_residents,
    lexicon_of,
)
from burro_core.ops import NO_OPERATIONS, Operations
from burro_core.reducer import ReducerResult, apply
from burro_core.release import InMemoryRelease
from burro_core.spec import PreferenceSpec, canonical, default_spec
from burro_core.vocabulary import CAPS, CAPS_FIRMLY, FIRM_OF_MINUTES, FIRM_OF_MONEY

from .support import (
    area_id,
    carrying,
    place,
    place_id,
    preview_release,
    small_release,
    unplaced,
)

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
# A string found nowhere else, to prove that what was typed is in nothing that comes back.
CANARY = "zqxjkvanary"


# One reader for them all: it makes the names of a release ready once.
READER = RuleInterpreter()


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    request = InterpretRequest(text=text, spec=spec, release=small_release())
    return READER.interpret(request)


def edits(result: InterpretResult) -> dict[str, list[dict[str, Any]]]:
    """The edits that say something, each with its sentinels left out."""
    quiet = ("unchanged", "none", "default", 0, 0.0)
    found = result.operations.model_dump(mode="json")
    return {
        group: [{k: v for k, v in edit.items() if v not in quiet} for edit in items]
        for group, items in found.items()
        if items
    }


def reduced(result: InterpretResult, spec: PreferenceSpec = RENTER) -> ReducerResult:
    return apply(spec, result.operations, small_release())


def test_a_plain_request_becomes_edits_to_the_things_it_names():
    result = read("Somewhere quiet and leafy, near a park")
    assert result.status is InterpretStatus.OK
    assert edits(result) == {
        "weight_ops": [
            {
                "action": "nudge",
                "feature_id": "park_proximity",
                "step": "up_large",
                "provenance": "stated",
            }
        ],
        "tag_ops": [
            {
                "action": "nudge",
                "tag_id": "quiet_residential",
                "step": "up_large",
                "toward": "high",
                "provenance": "stated",
            },
            {
                "action": "nudge",
                "tag_id": "leafy",
                "step": "up_large",
                "toward": "high",
                "provenance": "stated",
            },
        ],
    }
    assert (result.unmet, result.clarify, result.notice) == ((), (), Notice.NONE)
    assert (result.suggestions, result.unread) == ((), ())
    assert (result.interpreter, result.degraded) == (InterpreterName.RULE, False)
    assert result.usage.model_dump() == {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
    }

    after = reduced(result)
    assert after.rejected == ()
    # Each thing named is worth a half, the park too, though it had a default of its own.
    assert {t.tag_id.value: t.weight for t in after.spec.tags} == {
        "leafy": 0.5,
        "quiet_residential": 0.5,
    }
    park = next(w for w in after.spec.weights if w.feature_id is FeatureId.PARK_PROXIMITY)
    assert (park.weight, park.provenance) == (0.5, "stated")
    # What was not said has given way to it: 0.30 in all, against 1.50 that was said.
    unsaid = [w.weight for w in after.spec.weights if w.provenance == "default"]
    assert sorted(unsaid) == [0.05, 0.05, 0.05, 0.05, 0.1]


def test_a_request_with_two_workplaces_and_a_budget():
    result = read(
        "I work at Foxholt Works and I study at Wexmoor University. "
        "We can spend up to £1,800 a month on a two bed."
    )
    assert result.status is InterpretStatus.OK
    assert edits(result) == {
        "budget_ops": [
            {
                "action": "set",
                "tenure": "rent",
                "amount": 1800,
                "segment": "bed_2",
                "strictness": "hard",
                "provenance": "stated",
            }
        ],
        "commute_ops": [
            {"action": "add", "place_id": place_id(2), "provenance": "stated"},
            {"action": "add", "place_id": place_id(3), "provenance": "stated"},
        ],
    }
    # What the text did not say is stated as an assumption, pointing at its edit. How
    # firm the budget is was said: "up to" is the most that can be spent.
    assert [(a.code, a.group, a.index) for a in result.assumptions] == [
        (AssumptionCode.MODE, OpsGroup.COMMUTE, 0),
        (AssumptionCode.MAX_MINUTES, OpsGroup.COMMUTE, 0),
        (AssumptionCode.STRICTNESS, OpsGroup.COMMUTE, 0),
        (AssumptionCode.MODE, OpsGroup.COMMUTE, 1),
        (AssumptionCode.MAX_MINUTES, OpsGroup.COMMUTE, 1),
        (AssumptionCode.STRICTNESS, OpsGroup.COMMUTE, 1),
    ]

    after = reduced(result)
    assert after.rejected == ()
    assert [(c.place_id, c.mode, c.max_minutes, c.strictness) for c in after.spec.commutes] == [
        (place_id(2), "pt", 45, "soft"),
        (place_id(3), "pt", 45, "soft"),
    ]
    assert (after.spec.budget.amount, after.spec.budget.segment) == (1800, "bed_2")
    # A budget is soft unless the person says otherwise, and "up to" says it. The slowest
    # journey drives the score.
    assert after.spec.budget.strictness == "hard"
    assert after.spec.commute_combine == "slowest"


def test_request_to_avoid_a_group_gets_the_neutral_notice_and_the_rest_is_served():
    result = read("Somewhere quiet, not too many students, 30 minutes to Pellam Cross")
    assert result.status is InterpretStatus.POLICY_REDIRECT
    assert result.notice is Notice.NEUTRAL_PLACES
    assert NOTICES[result.notice] == (
        "Burro ranks places by what is there. Of who lives in a place it counts only their "
        "age and their households, at the census of 2021, and you cannot ask for fewer of "
        "anyone. The rest of your search has been applied."
    )
    # No edit for that part, and every other edit is made.
    assert edits(result) == {
        "commute_ops": [
            {"action": "add", "place_id": place_id(1), "max_minutes": 30, "provenance": "stated"}
        ],
        "tag_ops": [
            {
                "action": "nudge",
                "tag_id": "quiet_residential",
                "step": "up_large",
                "toward": "high",
                "provenance": "stated",
            }
        ],
    }
    after = reduced(result)
    assert after.rejected == ()
    assert [t.tag_id for t in after.spec.tags] == ["quiet_residential"]


WHO_LIVES_THERE = [
    "not too many students",
    "fewer immigrants please",
    "where people like me live",
    # What people do for work, and whether they have a partner, are counted by nothing.
    "an area full of professionals",
    "young couples",
    "singles",
    "somewhere with no old people",
    "a diverse area",
    "mostly white people",
    "a Jewish neighbourhood with lots of Jewish people",
    "away from council tenants",
    "a gay area",
    "a Polish community",
    "quiet neighbours",
    "an older population",
    "somewhere without Pakistani families",
    # A group named as a noun, with no word for people beside it.
    "no blacks",
    "somewhere without Asians",
    "a gay-friendly area",
    "avoid areas full of benefit claimants",
    # A word for a group closes the noun after it, whatever the noun is.
    "gay village",
    "student village",
    "a Jewish quarter",
    "a Muslim part of town",
    # To be far from a campus is a way to ask for fewer students.
    "far from a university",
    "nowhere near a university",
    "as far from the university as possible",
    "far from the campus",
    "not near a university",
    "away from the universities",
    "I don't want to be near a uni",
    "no universities nearby",
    "I hate being near a campus",
    # Said in words the reader has no rule for. It is in doubt, and a campus
    # in a doubtful clause is a request about who lives somewhere.
    "as far as possible from the university",
    "as far away as possible from a university",
    "as far as possible from universities",
    "a long way from the university",
    "miles from the university",
    "I want to be miles from any university",
    "further from the university",
    "somewhere that isn't near a university",
    "isn't near a campus",
    "outside the university area",
    "anywhere but near a university",
    "a university is the last thing I want nearby",
    "I love Wexmoor. University is not for me.",
    "a university? No thanks.",
    "the campus, I'd rather not",
    # And by name: a journey to it was added, and its area came first.
    "not near Wexmoor University",
    "nowhere near Wexmoor University",
    "I don't want to be near Wexmoor University",
    "Wexmoor University is not for me",
    "I wouldn't want to work at Wexmoor University",
    # A word for how well off the people of a place are, with no word for people beside it.
    # "Affluent" and "posh" are not among them: each is offered, as of the place.
    "a wealthy area",
    "somewhere wealthy",
    "well off",
    "well to do",
    # A wish for fewer of those who are counted. Burro counts their age and their
    # households, and no words ask for fewer of anyone.
    "no families",
    "fewer young professionals",
    "not too many young people",
    "somewhere without many pensioners",
    "away from old people",
    "I don't want young families nearby",
    "too many retirees",
    "less family friendly",
    "I worry about young people",
    "I don't care about families",
    "a family area is the last thing I want",
    "young people? No thanks.",
    # Those who are counted, beside a word for what was not decided on.
    "white families",
    "young Muslim families",
    "middle class families",
    "wealthy retirees",
    "posh young professionals",
    "rich young people",
    "Polish families",
]


@pytest.mark.parametrize("text", WHO_LIVES_THERE)
def test_a_request_about_who_lives_somewhere_makes_no_edit_at_all(text: str):
    result = read(text)
    assert result.status is InterpretStatus.POLICY_REDIRECT
    assert result.notice is Notice.NEUTRAL_PLACES
    # It is not quietly turned into a tag, a feature or an excluded area.
    assert result.operations == NO_OPERATIONS
    assert reduced(result).spec == RENTER


@pytest.mark.parametrize("text", WHO_LIVES_THERE)
def test_the_same_notice_is_given_whoever_is_asked_about(text: str):
    assert NOTICES[read(text).notice] == NOTICES[Notice.NEUTRAL_PLACES]
    assert read(text, BUYER).model_dump() == read(text, RENTER).model_dump()


@pytest.mark.parametrize("text", WHO_LIVES_THERE)
def test_a_request_about_who_lives_somewhere_is_offered_nothing_that_counts_them(text: str):
    offered = {found.target for found in read(text).suggestions}
    assert not offered & {f"feature:{feature_id}" for feature_id in COUNTS_RESIDENTS}
    assert not offered & {f"tag:{tag_id}" for tag_id in HOLDS_RESIDENTS}


MORE, IGNORE = SuggestionDirection.MORE, SuggestionDirection.IGNORE
YOUNG, OLD = "feature:residents_aged_20_34", "feature:residents_aged_65_over"
FAMILY_AREA, FAMILY_AMENITIES = "tag:family_area", "tag:family_amenities"
# What is typed of who lives somewhere that Burro counts, and what each is offered as.
# Decided on 2026-09-24: each is offered, and never applied from a word.
OFFERED_FOR_WHO_IS_COUNTED = {
    "young professionals": ["tag:young_professionals"],
    "an area full of young professionals": ["tag:young_professionals"],
    "young people": [YOUNG],
    "people my age": [YOUNG, OLD],
    "a family area": [FAMILY_AREA],
    "family friendly": [FAMILY_AREA, FAMILY_AMENITIES],
    "good for kids": [FAMILY_AREA, FAMILY_AMENITIES],
    "families": [FAMILY_AREA],
    "lots of young families": [FAMILY_AREA],
    "other families nearby": [FAMILY_AREA],
    "older and quieter": ["tag:quiet_residential", OLD],
    "retirees": [OLD],
    "older people": [OLD],
    "more households of one person": ["feature:households_one_person"],
    "more households with children": ["feature:households_dependent_children"],
    "I want more young adults": [YOUNG],
    "young adults": [YOUNG],
    "Residents aged 65 and over as a share of all residents, Census 2021": [OLD],
    "young people are essential": [YOUNG],
}


@pytest.mark.parametrize("text", OFFERED_FOR_WHO_IS_COUNTED)
def test_a_phrase_for_who_is_counted_is_offered_towards_more_and_never_applied(text: str):
    for spec in (RENTER, BUYER):
        result = read(text, spec)
        assert (result.status, result.notice) == (InterpretStatus.SUGGEST, Notice.NONE)
        assert result.operations == NO_OPERATIONS
        assert [found.target for found in result.suggestions] == OFFERED_FOR_WHO_IS_COUNTED[text]
        for found in result.suggestions:
            counted = found.target in (FAMILY_AMENITIES, "tag:quiet_residential")
            # More of what is counted, and to leave it out. Never less, and never to take off.
            assert [choice.direction for choice in found.choices] == [MORE, IGNORE]
            assert found.note.endswith(COUNTED_AT_THE_CENSUS) is not counted
            (more, _) = found.choices
            after = apply(spec, more.operations, small_release())
            assert after.rejected == () and after.spec != spec


def test_what_is_said_where_who_lives_somewhere_is_offered():
    assert COUNTED_AT_THE_CENSUS == (
        "Burro counts who was living there at the census of 2021. It measures places first."
    )
    # A person's own age is not known, so the words are answered with a question.
    (young, old) = read("people my age").suggestions
    assert young.note == old.note == WHAT_AGE
    assert WHAT_AGE.startswith("What age? ") and WHAT_AGE.endswith(COUNTED_AT_THE_CENSUS)
    # A vibe that counts places alone says nothing of the census.
    (area, amenities) = read("family friendly").suggestions
    assert (area.note, amenities.note) == (COUNTED_AT_THE_CENSUS, "")


def test_no_choice_of_what_counts_who_lives_somewhere_is_ever_less():
    for phrase in sorted(WHO_IS_COUNTED):
        for text in (phrase, f"maybe {phrase}", f"is it {phrase}", f"{phrase}, I suppose"):
            for found in read(text).suggestions:
                named = found.target.partition(":")[2]
                if named in COUNTS_RESIDENTS or named in HOLDS_RESIDENTS:
                    assert [choice.direction for choice in found.choices] == [MORE, IGNORE], text
                    edits = found.choices[0].operations
                    assert all(edit.direction == "more" for edit in edits.weight_ops), text
                    assert all(edit.toward == "high" for edit in edits.tag_ops), text
                    assert all(
                        edit.action == "nudge" for edit in (*edits.weight_ops, *edits.tag_ops)
                    )
    assert all(counts_residents(LEXICON[phrase]) for phrase in WHO_IS_COUNTED)


TURNS_BEFORE = (
    *("no", "not", "fewer", "less", "without", "avoid", "not too many", "away from"),
    *("far from", "I don't want", "I hate", "anything but", "too many", "never"),
)


@pytest.mark.parametrize("turn", TURNS_BEFORE)
def test_a_word_that_turns_before_who_is_counted_draws_the_notice_and_nothing_else(turn: str):
    for phrase in sorted(WHO_IS_COUNTED):
        text = f"{turn} {phrase}"
        result = read(text)
        assert (result.status, result.notice) == (
            InterpretStatus.POLICY_REDIRECT,
            Notice.NEUTRAL_PLACES,
        ), text
        assert result.operations == NO_OPERATIONS, text
        offered = {found.target for found in result.suggestions}
        assert not offered & {f"feature:{feature_id}" for feature_id in COUNTS_RESIDENTS}, text
        assert not offered & {f"tag:{tag_id}" for tag_id in HOLDS_RESIDENTS}, text
        assert reduced(result).spec == RENTER, text


@pytest.mark.parametrize(
    "text",
    [
        "young people, no main roads",
        "families but not too many pubs",
        "young professionals and no pubs",
        "retirees, not near a station",
    ],
)
def test_a_word_that_turns_something_else_turns_nobody_away(text: str):
    result = read(text)
    assert (result.status, result.notice) == (InterpretStatus.SUGGEST, Notice.NONE)
    counted = {f"feature:{f}" for f in COUNTS_RESIDENTS} | {f"tag:{t}" for t in HOLDS_RESIDENTS}
    assert {found.target for found in result.suggestions} & counted


def test_the_rest_is_served_where_part_of_a_request_asks_for_fewer_of_anyone():
    result = read("Somewhere quiet, not too many young people, 30 minutes to Pellam Cross")
    assert (result.status, result.notice) == (
        InterpretStatus.POLICY_REDIRECT,
        Notice.NEUTRAL_PLACES,
    )
    assert [edit.tag_id for edit in result.operations.tag_ops] == ["quiet_residential"]
    assert [edit.place_id for edit in result.operations.commute_ops] == [place_id(1)]
    assert result.operations.weight_ops == () and result.suggestions == ()
    # Where the words draw the notice, a vibe that counts places alone is still offered,
    # and the vibe that counts households is not.
    both = read("family friendly, not too many families")
    assert [found.target for found in both.suggestions] == [FAMILY_AMENITIES]
    assert both.notice is Notice.NEUTRAL_PLACES


def test_a_request_to_find_a_group_is_not_turned_into_the_tag_that_sounds_like_it():
    families = read("lots of young families, good primary schools and playgrounds")
    # No word applies what counts who lives somewhere, so nothing of the prompt is
    # applied: each thing is offered, and Family amenities is not among them.
    assert (families.status, families.notice) == (InterpretStatus.SUGGEST, Notice.NONE)
    assert families.operations == NO_OPERATIONS
    assert [found.target for found in families.suggestions] == [
        FAMILY_AREA,
        "feature:school_primary_attainment",
        "feature:play_space_proximity",
    ]
    students = read("lots of students")
    assert students.operations.tag_ops == () and students.suggestions == ()


def test_a_word_that_also_names_a_cuisine_is_not_a_word_for_people_on_its_own():
    result = read("Turkish cafes and Indian restaurants")
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert [e.feature_id for e in result.operations.weight_ops] == [
        "venue_cafe_per_homes",
        "venue_food_drink_per_homes",
    ]
    pubs = read("Irish pubs")
    assert (pubs.status, pubs.unmet) == (InterpretStatus.OK, ())
    assert [e.feature_id for e in pubs.operations.weight_ops] == ["venue_evening_per_homes"]


@pytest.mark.parametrize("text", ["white stucco houses", "black railings", "an English garden"])
def test_a_word_that_is_also_a_colour_or_a_country_asks_nothing_about_people(text: str):
    result = read(text)
    assert (result.notice, result.operations) == (Notice.NONE, NO_OPERATIONS)
    # A garden is offered for itself, and the country it is called after asks nothing.
    offered = [found.target for found in result.suggestions]
    assert offered == (["feature:land_gardens"] if "garden" in text else [])
    assert result.status is (InterpretStatus.SUGGEST if offered else InterpretStatus.OK)


def test_the_rest_of_a_request_is_served_when_part_of_it_is_to_be_kept_from_a_campus():
    # "Far" is no word of the grammar, so a prompt that holds it is not plain, in
    # one sentence or in three. Nothing of it is applied, and the rest is offered.
    for text in (
        "Somewhere quiet, far from a university, 30 minutes to Pellam Cross",
        "Somewhere quiet. Far from a university. 30 minutes to Pellam Cross.",
    ):
        unread = read(text)
        assert unread.operations == NO_OPERATIONS
        assert (unread.status, unread.notice) == (
            InterpretStatus.POLICY_REDIRECT,
            Notice.NEUTRAL_PLACES,
        )
        # The campus is never offered: nothing that was typed can weigh it.
        assert [s.target for s in unread.suggestions] == ["tag:quiet_residential", "commute"]

    # Said in the words the grammar has, the campus makes no edit and the rest is applied.
    result = read("Somewhere quiet, not near a university, 30 minutes to Pellam Cross")
    assert (result.status, result.notice) == (
        InterpretStatus.POLICY_REDIRECT,
        Notice.NEUTRAL_PLACES,
    )
    assert edits(result) == {
        "commute_ops": [
            {"action": "add", "place_id": place_id(1), "max_minutes": 30, "provenance": "stated"}
        ],
        "tag_ops": [
            {
                "action": "nudge",
                "tag_id": "quiet_residential",
                "step": "up_large",
                "toward": "high",
                "provenance": "stated",
            }
        ],
    }


@pytest.mark.parametrize(
    "text", ["near a university", "close to the campus", "not far from a university"]
)
def test_to_be_near_a_campus_is_a_wish_about_a_place(text: str):
    result = read(text)
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    # A campus is one measure, so it is a feature, and no vibe is made of it.
    (edit,) = result.operations.weight_ops
    assert (edit.feature_id, edit.action, edit.step) == (
        "university_proximity",
        "nudge",
        "up_large",
    )
    assert result.operations.tag_ops == ()


def test_not_caring_about_a_campus_is_an_ordinary_edit():
    near = apply(RENTER, read("near a university").operations, small_release()).spec
    assert FeatureId.UNIVERSITY_PROXIMITY in {w.feature_id for w in near.active_weights}
    result = read("I don't care about universities", near)
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert [(e.feature_id, e.action) for e in result.operations.weight_ops] == [
        ("university_proximity", "remove")
    ]
    after = apply(near, result.operations, small_release()).spec
    assert FeatureId.UNIVERSITY_PROXIMITY not in {w.feature_id for w in after.active_weights}


def test_amenities_asked_for_by_name_are_ordinary_edits():
    result = read("good primary schools and playgrounds")
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert [e.feature_id for e in result.operations.weight_ops] == [
        FeatureId.SCHOOL_PRIMARY_ATTAINMENT,
        FeatureId.PLAY_SPACE_PROXIMITY,
    ]
    # A place that is good for a family may be one where families live, or one with
    # schools and play space. The words do not say which, so both are offered.
    friendly = read("family friendly")
    assert friendly.operations == NO_OPERATIONS
    assert [found.target for found in friendly.suggestions] == [FAMILY_AREA, FAMILY_AMENITIES]
    assert read("family amenities").operations.tag_ops[0].tag_id == "family_amenities"


COMMUNITY_AMENITIES = [
    "near a mosque",
    "kosher shops nearby",
    "close to a church",
    # A school, a shop or a venue for a community is its amenity, and no feature covers one.
    "muslim schools",
    "jewish schools nearby",
    "a Catholic primary school",
    "gay bars",
    "Polish shops",
    "an Asian supermarket",
]


@pytest.mark.parametrize("text", COMMUNITY_AMENITIES)
def test_a_request_for_a_communitys_amenities_is_heard_and_reported_as_unmet(text: str):
    result = read(text)
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert result.unmet == (UnmetCategory.COMMUNITY_AMENITIES,)
    assert result.operations == NO_OPERATIONS


def test_the_policy_lexicon_holds_words_for_people_and_never_for_buildings():
    buildings = {"mosque", "church", "synagogue", "temple", "gurdwara", "kosher", "halal", "school"}
    buildings |= {"university", "campus", "playground", "nursery", "flat", "house"}
    words = {word for phrase in POLICY_LEXICON for word in phrase.split()}
    assert not words & buildings
    assert not set(POLICY_LEXICON) & set(LEXICON)
    assert {prepare(phrase) for phrase in POLICY_LEXICON} == set(POLICY_LEXICON)
    # No phrase for what was not decided on is a thing of the lexicon: not ethnic group,
    # religion or nationality, not class, and not what people earn or do.
    undecided = {"muslim", "jewish", "christian", "polish", "white", "black", "asian"}
    undecided |= {"ethnic", "immigrants", "students", "student", "professionals", "singles"}
    undecided |= {"class", "wealthy", "rich", "poor", "diverse", "religious", "foreign"}
    assert not undecided & set(LEXICON)
    for variant in GrittyVariant:
        assert not undecided & set(lexicon_of(variant))


def test_every_feature_and_vibe_is_recognised_by_its_label_and_its_short_label():
    for feature_id, feature in FEATURES.items():
        for name in (feature.label, feature.short_label):
            if prepare(name) in HOME_WORDS:
                continue  # "Flats" is what is being looked for, and no wish for more of them
            result = read(f"I care about {name}")
            found = {e.feature_id for e in result.operations.weight_ops}
            if feature_id in COUNTS_RESIDENTS:
                # Its own name is offered, and never applied.
                assert result.operations == NO_OPERATIONS, name
                assert [s.target for s in result.suggestions] == [f"feature:{feature_id}"], name
                continue
            # What is shown and never ranked on is a wish for what is ranked in its place.
            assert RANKED_AS.get(feature_id, feature_id) in found, name
            assert not found & set(RANKED_AS), name
    for vibe in small_release().vibes:
        if vibe.shape is TagShape.SCALE:
            continue  # the name of a scale names no end
        for name in {vibe.label, vibe.short_label}:
            result = read(f"somewhere with {name.lower()} please")
            if vibe.tag_id in HOLDS_RESIDENTS | ROUGH_GUIDES:
                # Its own name is offered, and never applied.
                assert result.operations == NO_OPERATIONS, name
                assert [s.target for s in result.suggestions] == [f"tag:{vibe.tag_id}"], name
                continue
            assert [e.tag_id for e in result.operations.tag_ops] == [vibe.tag_id], name


NOISE_NAME = FEATURES[FeatureId.NOISE_EXPOSURE].label


@pytest.mark.parametrize(
    "text",
    [
        f"I care about {NOISE_NAME}",
        f"I care about {NOISE_NAME.lower()}",
        f"Near a park. I care about {NOISE_NAME}",
    ],
)
def test_the_whole_name_of_transport_noise_is_read_as_the_measure_and_asks_about_nobody(
    text: str,
):
    # The one name of the catalogue that says residents (ADR 0006). Typed whole, it names
    # the measure, as the name of every other measure does.
    result = read(text)
    assert result.notice is Notice.NONE
    assert FeatureId.NOISE_EXPOSURE in {edit.feature_id for edit in result.operations.weight_ops}


@pytest.mark.parametrize(
    "text",
    [
        "residents exposed to transport noise",
        "share of residents exposed to transport noise",
        "share of residents exposed to 65 dB or more of transport noise",
        "share of older residents exposed to 55 dB or more of transport noise",
        "share of residents",
        "quiet residents",
        "fewer residents",
        f"{NOISE_NAME} and young residents",
        f"no residents, {NOISE_NAME}",
    ],
)
def test_a_word_for_who_lives_somewhere_is_still_heard_outside_the_whole_name_of_the_measure(
    text: str,
):
    result = read(text)
    assert result.notice is Notice.NEUTRAL_PLACES


# "Homes" is the name of a scale and a word for a home, which is a thing by no name.
# Gritty is named for its high end, so its name is a wish for that end.
SCALES = [
    vibe
    for vibe in tags_of(GrittyVariant.B)
    if vibe.shape is TagShape.SCALE
    and prepare(vibe.label) not in HOME_WORDS
    and vibe.label != vibe.high_end
]
SAID_OF_A_SCALE = [
    "{}",
    "somewhere with {}",
    "I want {}",
    "{} please",
    "not {}",
    "more {}",
    "no {}",
]


@pytest.mark.parametrize("said", SAID_OF_A_SCALE)
@pytest.mark.parametrize("vibe", SCALES, ids=[vibe.tag_id.value for vibe in SCALES])
def test_the_name_of_a_scale_names_no_end_so_it_is_offered_and_never_applied(vibe: Tag, said: str):
    # "Street character" was read as a wish for Gritty, and "pace" for Buzzy.
    result = read(said.format(vibe.label.lower()))
    assert result.operations == NO_OPERATIONS
    assert (result.status, result.assumptions) == (InterpretStatus.SUGGEST, ())
    (found,) = result.suggestions
    assert (found.target, found.label) == (f"tag:{vibe.tag_id}", vibe.short_label)
    # Both ends are offered, and the person chooses.
    assert [choice.direction for choice in found.choices] == ["more", "less", "ignore"]
    towards = [edit.toward for choice in found.choices for edit in choice.operations.tag_ops]
    assert towards == ["high", "low"]
    assert str(vibe.high_end) in found.choices[0].label
    assert str(vibe.low_end) in found.choices[1].label


@pytest.mark.parametrize("text", ["I don't care about pace", "pace is not important"])
def test_to_take_a_scale_off_names_no_end_and_needs_none(text: str):
    held = apply(RENTER, read("buzzy").operations, small_release()).spec
    result = read(text, held)
    assert edits(result) == {
        "tag_ops": [{"action": "remove", "tag_id": "pace", "provenance": "stated"}]
    }
    assert reduced(result, held).spec.tags == ()


def test_a_scale_is_recognised_by_the_name_of_each_end():
    for vibe in small_release().vibes:
        if vibe.shape is not TagShape.SCALE or vibe.tag_id is TagId.HOMES:
            continue
        for end, toward in ((vibe.low_end, "low"), (vibe.high_end, "high")):
            assert end is not None
            (edit,) = read(f"somewhere {end.lower()}").operations.tag_ops
            assert (edit.tag_id, edit.toward, edit.step) == (vibe.tag_id, toward, "up_large"), end


@pytest.mark.parametrize("text", ["homes", "flats", "houses", "a flat", "I want a house"])
def test_a_word_for_a_home_is_no_wish_for_a_kind_of_street(text: str):
    # "Flats" is the name of an end of a scale, and it is also what is being
    # looked for. The reader cannot say which, so it is a thing by no name.
    assert read(text).operations.tag_ops == ()
    assert read("suburban").operations.tag_ops[0].toward == "low"
    assert read("city living").operations.tag_ops[0].toward == "high"


def test_a_word_for_a_home_names_an_end_of_the_scale_and_is_in_no_lexicon():
    # It is held for the guard on a model, which has been told that the scale is meant:
    # "houses not flats" says which end. The reader reads none of it.
    assert ENDS_NAMED_AS_HOMES == {
        TagId.HOMES: {"houses": "low", "house": "low", "flats": "high", "flat": "high"}
    }
    for variant in GrittyVariant:
        for ends in ENDS_NAMED_AS_HOMES.values():
            assert not set(ends) & set(lexicon_of(variant))
            assert set(ends) <= HOME_WORDS
    for text in ("houses not flats", "flats, not houses", "not flats"):
        assert read(text).operations == NO_OPERATIONS, text


def test_a_vibe_the_release_does_not_carry_answers_to_no_word():
    # A release that holds no recorded crime carries no Gritty, and the name the scale
    # had names nothing there.
    without = small_release(GrittyVariant.A)
    assert GRITTY[GrittyVariant.B] not in {vibe.tag_id for vibe in without.vibes}
    assert "street character" not in lexicon_of(GrittyVariant.A)
    for text in ("street character", "gritty", "polished", "rough", "affluent"):
        result = READER.interpret(InterpretRequest(text=text, spec=RENTER, release=without))
        named = {edit.tag_id for edit in result.operations.tag_ops}
        named |= {found.target.removeprefix("tag:") for found in result.suggestions}
        assert GRITTY[GrittyVariant.B] not in named, text


def test_the_lexicon_names_only_what_is_in_the_catalogue():
    for variant in GrittyVariant:
        for phrase, target in lexicon_of(variant).items():
            assert phrase == prepare(phrase), phrase
            assert target.features or target.tags
            assert set(target.features) <= set(FEATURES)
            assert set(target.tags) <= {vibe.tag_id for vibe in tags_of(variant)}, phrase
        # Every feature and every vibe of the release can be reached by some phrase, but
        # for what is shown and never ranked on: no word asks to be ranked on that.
        reached = lexicon_of(variant).values()
        assert {f for t in reached for f in t.features} == set(FEATURES) - set(RANKED_AS)
        assert {g for t in reached for g in t.tags} == {v.tag_id for v in tags_of(variant)}
    assert set(LEXICON) <= set(lexicon_of(GrittyVariant.A)) | set(lexicon_of(GrittyVariant.B))


@pytest.mark.parametrize(
    ("text", "tenure", "amount", "segment"),
    [
        ("£1,500 pcm", "rent", 1500, "unchanged"),
        ("1500 a month", "rent", 1500, "unchanged"),
        ("budget 1.5k", "unchanged", 1500, "unchanged"),
        ("under 1800", "unchanged", 1800, "unchanged"),
        ("maximum £2,000", "unchanged", 2000, "unchanged"),
        ("under £950 for a studio to rent", "rent", 950, "studio"),
        ("renting a room for £700", "rent", 700, "room"),
        ("3 bedroom house to rent", "rent", 0, "bed_3"),
        ("a five-bed to rent", "rent", 0, "bed_4plus"),
        ("buying a terraced house for £650k", "buy", 650_000, "terraced"),
        ("2 bed flat to buy under 450k", "buy", 450_000, "flat"),
        ("a semi-detached house, £1.2m, to buy", "buy", 1_200_000, "semi_detached"),
        ("a detached place, we want to buy", "buy", 0, "detached"),
        ("flats for sale under £400,000", "buy", 400_000, "unchanged"),
        # No word says rent or buy, and no rent is this high.
        ("around £500,000", "buy", 500_000, "unchanged"),
    ],
)
def test_a_budget_is_read_with_its_tenure_and_the_kind_of_home(
    text: str, tenure: str, amount: int, segment: str
):
    (edit,) = read(text).operations.budget_ops
    assert (edit.action, edit.tenure, edit.amount, edit.segment) == ("set", tenure, amount, segment)
    assert edit.strictness == "unchanged"
    assert reduced(read(text)).rejected == ()


def test_a_number_too_long_to_be_money_is_turned_away_by_the_reducer():
    result = read("£" + "9" * 40 + " pcm")
    assert result.operations.budget_ops[0].amount == 10**12
    assert [r.reason for r in reduced(result).rejected] == [RejectReason.OUT_OF_RANGE]
    late = read("9" * 40 + " minutes to Pellam Cross")
    assert [r.reason for r in reduced(late).rejected] == [RejectReason.OUT_OF_RANGE]


FIRM_BUDGETS = [
    "max £1,800 pcm",
    "£1,800 pcm max",
    "up to £1,800 pcm",
    "at most £1,800 pcm",
    "no more than £1,800 pcm",
    "I cannot go over £1,800 a month",
    "max £400k for a flat",
    "up to 1800",
]
GUIDES = [
    "£1,800 pcm",
    "under £1,800 pcm",
    "below £1,800 pcm",
    "less than £1,800 pcm",
    "around £1,800 pcm",
    "maximum £1,800 pcm",
    "£1,800 pcm tops",
]


@pytest.mark.parametrize("text", FIRM_BUDGETS)
def test_a_budget_is_a_firm_limit_where_the_words_say_the_most_that_can_be_paid(text: str):
    """Decided on 2026-09-24: "max", "up to", "at most" and "no more than".

    Read as a guide, "max £400k" put first an area where a home sold for far more.
    """
    result = read(text)
    (edit,) = result.operations.budget_ops
    assert edit.strictness == "hard"
    assert AssumptionCode.STRICTNESS not in {found.code for found in result.assumptions}
    assert reduced(result).spec.budget.strictness == "hard"


@pytest.mark.parametrize("text", GUIDES)
def test_a_budget_with_none_of_the_words_that_make_it_firm_stays_a_guide(text: str):
    result = read(text)
    (edit,) = result.operations.budget_ops
    assert edit.strictness == "unchanged"
    assert reduced(result).spec.budget.strictness == "soft"


def test_each_kind_of_limit_is_held_to_the_words_that_were_decided_for_it():
    """ "Up to" makes no journey firm, and "within" is no word of money."""
    assert {"max", "up to"} == FIRM_OF_MONEY - CAPS_FIRMLY
    assert {"max", "within"} == FIRM_OF_MINUTES - CAPS_FIRMLY
    assert {"max", "up to", "within"} <= CAPS
    (journey,) = read("up to 30 minutes to Pellam Cross").operations.commute_ops
    assert (journey.max_minutes, journey.strictness) == (30, "unchanged")


def test_a_number_of_minutes_or_bedrooms_is_not_mistaken_for_money():
    result = read("2 bed within 30 minutes of Pellam Cross")
    assert result.operations.budget_ops[0].amount == 0
    assert result.operations.commute_ops[0].max_minutes == 30
    assert read("up to 40 minutes to Foxholt Works").operations.budget_ops == ()


@pytest.mark.parametrize(
    ("text", "place", "mode", "minutes", "strictness"),
    [
        ("30 minutes to Pellam Cross", 1, "unchanged", 30, "unchanged"),
        ("within 25 mins of Foxholt Works", 2, "unchanged", 25, "hard"),
        ("I work at Wexmoor University", 3, "unchanged", 0, "unchanged"),
        ("I work at the Pellam Infirmary", 4, "unchanged", 0, "unchanged"),
        ("near Foxholt Works", 2, "unchanged", 0, "unchanged"),
        ("I cycle to work at Foxholt Works", 2, "cycle", 0, "unchanged"),
        ("20 minute walk to Pellam Cross Station", 1, "walk", 20, "unchanged"),
        ("no more than 35 minutes to Pellam Cross by tube", 1, "pt", 35, "hard"),
        ("I study at Wexmoor, 40 minute commute", 3, "unchanged", 40, "unchanged"),
        ("I work at Foxholt Works and want a park nearby", 2, "unchanged", 0, "unchanged"),
    ],
)
def test_a_destination_is_read_with_its_mode_and_its_cap(
    text: str, place: int, mode: str, minutes: int, strictness: str
):
    result = read(text)
    (edit,) = result.operations.commute_ops
    assert (edit.action, edit.place_id) == ("add", place_id(place))
    assert (edit.mode, edit.max_minutes, edit.strictness) == (mode, minutes, strictness)
    assert result.status is InterpretStatus.OK
    assert reduced(result).rejected == ()


@pytest.mark.parametrize(
    ("text", "mode", "minutes", "strictness"),
    [
        # The minutes stand apart from the place, and how they are travelled
        # and whether they are a limit stand with the minutes.
        ("I work at Foxholt Works. A 40 minute commute on foot.", "walk", 40, "unchanged"),
        ("I commute to Foxholt Works, 35 minutes max by bike", "cycle", 35, "hard"),
        ("I work at Foxholt Works, a 35 minute commute by bike", "cycle", 35, "unchanged"),
        ("I work at Foxholt Works, no more than 35 minutes", "unchanged", 35, "hard"),
        ("I work at Foxholt Works. At most a 30 minute commute by tube.", "pt", 30, "hard"),
        ("I cycle to Foxholt Works, 25 minutes tops", "cycle", 25, "unchanged"),
        ("I walk to Foxholt Works, a 20 minute walk", "walk", 20, "unchanged"),
        ("within 35 minutes of Foxholt Works, no more than 35 minutes", "unchanged", 35, "hard"),
    ],
)
def test_minutes_said_apart_from_a_place_keep_their_way_of_travelling_and_their_limit(
    text: str, mode: str, minutes: int, strictness: str
):
    result = read(text)
    (edit,) = result.operations.commute_ops
    assert (edit.place_id, edit.mode, edit.max_minutes) == (place_id(2), mode, minutes)
    assert edit.strictness == strictness
    assert (result.status, result.unread) == (InterpretStatus.OK, ())
    # What was said is not said to be assumed.
    assumed = {found.code for found in result.assumptions}
    assert (AssumptionCode.MODE in assumed) is (mode == "unchanged")
    assert (AssumptionCode.STRICTNESS in assumed) is (strictness == "unchanged")
    assert AssumptionCode.MAX_MINUTES not in assumed
    # And the journey rests on the words that gave it its minutes too.
    rested = " ".join(text[found.start : found.end] for found in result.rests_on)
    assert "Foxholt Works" in rested and str(minutes) in rested


def test_minutes_said_apart_are_the_limit_of_each_journey_that_was_given_none():
    text = "I work at Foxholt Works and study at Wexmoor University, a 40 minute commute by bike"
    result = read(text)
    assert [(e.place_id, e.mode, e.max_minutes) for e in result.operations.commute_ops] == [
        (place_id(2), "cycle", 40),
        (place_id(3), "cycle", 40),
    ]


@pytest.mark.parametrize(
    "text",
    [
        # Said of no journey: there is nothing for the minutes to be the limit of.
        "a 40 minute commute",
        "a 40 minute commute by bike",
        "leafy, a 30 minute commute",
        # Said against the journey they stand beside.
        "I cycle to Foxholt Works, 25 minutes on foot",
        "30 minutes to Pellam Cross. A 40 minute commute by bike.",
        "I walk to Foxholt Works, a 20 minute commute by tube",
        # Two that disagree.
        "I work at Foxholt Works. A 40 minute commute. A 30 minute commute.",
        "I work at Foxholt Works, a 30 minute commute by bike. A 30 minute commute on foot.",
    ],
)
def test_minutes_said_of_no_journey_or_against_one_are_not_said_to_have_been_read(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert UnmetCategory.OTHER in result.unmet and result.unread


def test_a_name_written_with_its_article_is_found_with_it_and_without():
    exchange = place(1).replace(
        place_id=place_id(9),
        name="Pellam Exchange",
        kind=PlaceKind.DISTRICT,
        aliases=("The Clinkers",),
    )
    known = small_release()
    release = dataclasses.replace(known, places=(*known.places, exchange))

    def place_read(text: str) -> list[str]:
        request = InterpretRequest(text=text, spec=RENTER, release=release)
        result = RuleInterpreter().interpret(request)
        assert result.status is InterpretStatus.OK
        return [edit.place_id for edit in result.operations.commute_ops]

    # The article is part of this name, so setting it aside would lose the match.
    assert place_read("I work at the Clinkers") == [place_id(9)]
    assert place_read("30 minutes to The Clinkers by tube") == [place_id(9)]
    # And it is no part of this one.
    assert place_read("I work at the Pellam Infirmary") == [place_id(4)]


def test_the_word_station_in_a_stations_name_is_not_a_wish_to_live_near_one():
    result = read("30 minutes to Pellam Cross Station")
    assert result.operations.weight_ops == ()
    assert read("near a station").operations.weight_ops[0].feature_id == "station_walk"


def test_a_destination_that_matches_nothing_is_asked_about():
    result = read("I work at Nowhereville and want somewhere leafy")
    assert result.status is InterpretStatus.CLARIFY
    # The edit that could not be settled carries an empty id, and the rest are made.
    assert [e.place_id for e in result.operations.commute_ops] == [""]
    assert [e.tag_id for e in result.operations.tag_ops] == ["leafy"]
    assert [(c.group, c.index, c.options) for c in result.clarify] == [(OpsGroup.COMMUTE, 0, ())]
    after = reduced(result)
    assert [(r.group, r.reason) for r in after.rejected] == [
        (OpsGroup.COMMUTE, RejectReason.UNKNOWN_PLACE)
    ]
    assert [t.tag_id for t in after.spec.tags] == ["leafy"]


def test_a_destination_that_matches_several_places_offers_them():
    result = read("I work near Pellam")
    assert result.status is InterpretStatus.CLARIFY
    (asked,) = result.clarify
    assert [(o.id, o.name, o.kind) for o in asked.options] == [
        (place_id(1), "Pellam Cross", "station"),
        (place_id(4), "Pellam Infirmary", "hospital"),
    ]
    assert result.operations.commute_ops[asked.index].place_id == ""


@pytest.mark.parametrize(
    ("text", "rules"),
    [
        ("not Cindermoor", [("exclude", 3)]),
        ("avoid Dulcimer Green and avoid Alderwick", [("exclude", 4), ("exclude", 1)]),
        ("anywhere but Eskerfold", [("exclude", 5)]),
        ("only in Farrowmere", [("only", 6)]),
    ],
)
def test_an_area_is_excluded_or_selected_by_name(text: str, rules: list[tuple[str, int]]):
    result = read(text)
    assert [(e.action, e.area_id) for e in result.operations.area_ops] == [
        (action, area_id(number)) for action, number in rules
    ]
    assert reduced(result).rejected == ()


def test_not_before_something_that_is_no_area_excludes_nothing():
    for text in ("not bothered about pubs", "not too noisy", "not a lot of traffic noise"):
        assert read(text).operations.area_ops == ()


def with_areas(*names: str) -> InMemoryRelease:
    """The small release with areas added, each named to begin like an ordinary word."""
    known = small_release()
    added = tuple(
        known.neighbourhoods[0].replace(
            area_id=area_id(90 + n), slug=name.lower().replace(" ", "-"), name=name
        )
        for n, name in enumerate(names)
    )
    return dataclasses.replace(known, neighbourhoods=(*known.neighbourhoods, *added))


ORDINARY = [
    # "Far" begins Farrowmere, which the small release holds.
    "not far from a station",
    "not far from a park",
    "somewhere not far from Pellam Cross",
    "not too noisy",
    "not too far out",
    "avoid ma",
    "avoid far too much noise",
    "only a short walk to the shops",
    "only far from the centre if it is cheap",
    "anywhere but too",
    "not a",
    "not b",
]


@pytest.mark.parametrize("text", ORDINARY)
def test_an_ordinary_word_that_begins_a_name_is_never_read_as_the_name(text: str):
    # The release holds names that begin "Far", "Too", "Ma" and "A", as whole
    # words and as parts of one.
    release = with_areas("Too Bridge", "Toovey Marsh", "Far Tansy", "Marrowfen", "A Hundred Osiers")
    result = RuleInterpreter().interpret(InterpretRequest(text=text, spec=RENTER, release=release))
    assert result.operations.area_ops == ()
    assert not [c for c in result.clarify if c.group is OpsGroup.AREA]
    assert apply(RENTER, result.operations, release).spec.areas == ()


def test_an_area_is_excluded_only_when_the_whole_of_its_name_is_given():
    release = with_areas("Too Bridge", "Far Tansy")
    for text, number in (("not Too Bridge", 90), ("avoid Far Tansy", 91), ("not Farrowmere", 6)):
        request = InterpretRequest(text=text, spec=RENTER, release=release)
        (edit,) = RuleInterpreter().interpret(request).operations.area_ops
        assert (edit.action, edit.area_id) == ("exclude", area_id(number))


def test_not_far_from_a_place_is_a_wish_to_be_near_it():
    result = read("somewhere not far from Pellam Cross")
    assert result.status is InterpretStatus.OK
    assert [e.place_id for e in result.operations.commute_ops] == [place_id(1)]
    assert result.operations.area_ops == ()


@pytest.mark.parametrize(
    "text", ["I work at b", "I work at f", "30 minutes to pel", "I work at Foxh"]
)
def test_part_of_a_name_after_a_cue_that_expects_one_is_asked_about_and_not_taken(text: str):
    result = read(text)
    assert result.status is InterpretStatus.CLARIFY
    # The edit carries no id, so the reducer turns it away and nothing is added.
    assert [e.place_id for e in result.operations.commute_ops] == [""]
    assert reduced(result).spec.commutes == ()
    (asked,) = result.clarify
    assert (asked.group, asked.index) == (OpsGroup.COMMUTE, 0)


@pytest.mark.parametrize(
    "text", ["near b", "near f", "close to pel", "next to Foxh", "near Pellam", "near far"]
)
def test_near_takes_a_place_only_when_the_whole_of_its_name_is_given(text: str):
    result = read(text)
    assert result.operations.commute_ops == ()
    assert result.clarify == ()
    assert read("near Foxholt").operations.commute_ops[0].place_id == place_id(2)


@pytest.mark.parametrize(
    ("text", "action", "value", "step"),
    [
        ("parks", "nudge", 0.0, "up_large"),
        ("a bit more weight on parks", "nudge", 0.0, "up_small"),
        ("parks matter slightly", "nudge", 0.0, "up_large"),
        ("slightly closer to parks", "nudge", 0.0, "up_small"),
        ("somewhat near parks", "nudge", 0.0, "up_small"),
        ("much closer to parks", "nudge", 0.0, "up_large"),
        ("I really want parks", "nudge", 0.0, "up_large"),
        ("way more parks", "nudge", 0.0, "up_large"),
        ("parks are essential", "set", 1.0, "none"),
        ("parks are a must have", "set", 1.0, "none"),
        ("the most important thing is parks", "set", 1.0, "none"),
        ("I don't care about parks", "remove", 0.0, "none"),
        ("ignore parks", "remove", 0.0, "none"),
        ("not bothered about parks", "remove", 0.0, "none"),
        ("I care less about parks", "nudge", 0.0, "down_small"),
        ("parks are much less important", "nudge", 0.0, "down_large"),
        ("parks are not essential", "nudge", 0.0, "down_small"),
        ("parks are not a priority", "nudge", 0.0, "down_small"),
        ("parks are not important", "remove", 0.0, "none"),
        ("parks don't matter", "remove", 0.0, "none"),
    ],
)
def test_the_step_words_become_bounded_steps(text: str, action: str, value: float, step: str):
    (edit,) = read(text).operations.weight_ops
    assert edit.feature_id is FeatureId.PARK_PROXIMITY
    assert (edit.action, edit.value, edit.step) == (action, value, step)


def test_a_relative_request_never_sets_a_number_of_its_own_choosing():
    for text in ("much more nightlife", "a bit quieter", "really leafy", "parks", "less noise"):
        found = read(text).operations
        assert found.count >= 1
        for edit in (*found.weight_ops, *found.tag_ops):
            assert edit.action == "nudge"
            assert edit.value == 0


def weight_of(spec: PreferenceSpec, feature_id: FeatureId) -> float:
    return next((w.weight for w in spec.weights if w.feature_id is feature_id), 0.0)


def tag_weight_of(spec: PreferenceSpec, tag_id: TagId) -> float:
    return next((t.weight for t in spec.tags if t.tag_id is tag_id), 0.0)


NEGATED: list[tuple[str, FeatureId]] = [
    # A negative written as a contraction, which was read as a wish for the thing.
    ("somewhere that isn't near a station", FeatureId.STATION_WALK),
    ("I wouldn't want a station nearby", FeatureId.STATION_WALK),
    ("I won't live near a station", FeatureId.STATION_WALK),
    ("I don't really want a station nearby", FeatureId.STATION_WALK),
    ("there shouldn't be a park nearby", FeatureId.PARK_PROXIMITY),
    ("there aren\N{RIGHT SINGLE QUOTATION MARK}t any pubs", FeatureId.VENUE_EVENING_PER_HOMES),
    ("there arent any parks", FeatureId.PARK_PROXIMITY),
    # Distance, said in ways no list of phrases held.
    ("as far as possible from the high street", FeatureId.HIGHSTREET_ACCESS),
    ("a long way from the station", FeatureId.STATION_WALK),
    ("miles from the nearest station", FeatureId.STATION_WALK),
    ("further from the station", FeatureId.STATION_WALK),
    ("zero parks", FeatureId.PARK_PROXIMITY),
    # A list shares its doubt: it was turned for its first item alone.
    ("no parks, playgrounds or schools", FeatureId.PLAY_SPACE_PROXIMITY),
    ("no parks, playgrounds or schools", FeatureId.SCHOOL_PRIMARY_ATTAINMENT),
    ("no parks, playgrounds or schools", FeatureId.SCHOOL_SECONDARY_ATTAINMENT),
    ("neither parks nor playgrounds", FeatureId.PARK_PROXIMITY),
    ("neither parks nor playgrounds", FeatureId.PLAY_SPACE_PROXIMITY),
    # The doubt comes after the thing, or apart from it.
    ("parks are unimportant", FeatureId.PARK_PROXIMITY),
    ("a park is the last thing I want", FeatureId.PARK_PROXIMITY),
    ("a park? no thanks", FeatureId.PARK_PROXIMITY),
    ("near a station. Not!", FeatureId.STATION_WALK),
    ("not near a station", FeatureId.STATION_WALK),
    ("no parks nearby", FeatureId.PARK_PROXIMITY),
    ("I hate parks", FeatureId.PARK_PROXIMITY),
    ("away from the high street", FeatureId.HIGHSTREET_ACCESS),
    ("less green space", FeatureId.GREEN_COVER),
    ("far from the high street", FeatureId.HIGHSTREET_ACCESS),
    ("nowhere near a station", FeatureId.STATION_WALK),
    ("I don't want to be near a park", FeatureId.PARK_PROXIMITY),
    ("without a playground", FeatureId.PLAY_SPACE_PROXIMITY),
    ("no theatres", FeatureId.CULTURE_VENUES_PER_HOMES),
    ("not many independent shops", FeatureId.INDEPENDENTS_NEARBY),
    ("fewer primary schools", FeatureId.SCHOOL_PRIMARY_NEARBY),
    ("no pubs or parks", FeatureId.PARK_PROXIMITY),
]


# Of those, the ones the grammar makes: a turn, and the thing straight after it.
PLAINLY_TURNED = {
    "not near a station",
    "no parks nearby",
    "less green space",
    "without a playground",
    "no theatres",
    "not many independent shops",
    "fewer primary schools",
    "no pubs or parks",
}


@pytest.mark.parametrize(("text", "feature_id"), NEGATED, ids=[text for text, _ in NEGATED])
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renter", "buyer"])
def test_a_negated_wish_never_raises_a_weight(
    text: str, feature_id: FeatureId, spec: PreferenceSpec
):
    result = read(text, spec)
    for edit in result.operations.weight_ops:
        if edit.feature_id is feature_id:
            assert (edit.action, edit.step) in {("remove", "none"), ("nudge", "down_small")}
    after = reduced(result, spec)
    assert after.rejected == ()
    assert weight_of(after.spec, feature_id) <= weight_of(spec, feature_id)
    if text in PLAINLY_TURNED:
        # The turn is one the grammar has, so the weight is taken off or turned down.
        assert (result.status, result.unmet, result.unread) == (InterpretStatus.OK, (), ())
        assert feature_id in {edit.feature_id for edit in result.operations.weight_ops}
    else:
        # Nothing is applied. The thing is offered, and the person says which way.
        assert result.operations == NO_OPERATIONS
        assert result.status is InterpretStatus.SUGGEST
        assert UnmetCategory.OTHER in result.unmet and result.unread
        assert f"feature:{feature_id}" in {found.target for found in result.suggestions}


def test_no_suggestion_would_raise_a_weight_by_a_direction_the_reader_chose():
    # Pubs are a taste, so both directions are offered and neither is chosen.
    # A thing with one direction is offered as it is, or to be taken off, and
    # only where the spec holds a weight to take off.
    (pubs,) = read("hardly any pubs").suggestions
    assert (pubs.target, pubs.label) == ("feature:venue_evening_per_homes", "Pubs and bars")
    assert [(c.direction, c.label) for c in pubs.choices] == [
        ("more", "More pubs and bars"),
        ("less", "Fewer pubs and bars"),
        ("ignore", "Leave it out"),
    ]
    (park,) = read("I hate parks").suggestions
    assert [(c.direction, c.label) for c in park.choices] == [
        ("more", "Nearer a park"),
        ("less", "Take it off"),
        ("ignore", "Leave it out"),
    ]
    # A renter's default weighs no play space, so there is nothing to take off.
    (play,) = read("I hate playgrounds").suggestions
    assert [c.direction for c in play.choices] == ["more", "ignore"]


@pytest.mark.parametrize(
    ("text", "tag_id"), [("not leafy", TagId.LEAFY), ("I don't want a village", TagId.VILLAGE_FEEL)]
)
def test_a_negated_wish_never_raises_a_vibe_that_has_one_direction(text: str, tag_id: TagId):
    wanted = apply(
        RENTER,
        Operations.model_validate(
            NO_OPERATIONS.model_dump()
            | {
                "tag_ops": [
                    {
                        "action": "set",
                        "tag_id": tag_id,
                        "value": 0.5,
                        "step": "none",
                        "toward": "high",
                        "provenance": "stated",
                    }
                ]
            }
        ),
        small_release(),
    ).spec
    for spec in (RENTER, wanted):
        result = read(text, spec)
        assert [(e.tag_id, e.action) for e in result.operations.tag_ops] == [(tag_id, "remove")]
        assert tag_weight_of(reduced(result, spec).spec, tag_id) == 0.0
        assert (result.status, result.unmet) == (InterpretStatus.OK, ())


@pytest.mark.parametrize(
    ("text", "tag_id", "toward", "step"),
    [
        ("not buzzy", TagId.PACE, "low", "up_large"),
        ("not too buzzy", TagId.PACE, "low", "up_small"),
        ("no nightlife", TagId.PACE, "low", "up_large"),
        ("not calm", TagId.PACE, "high", "up_large"),
        ("not historic", TagId.BUILT_AGE, "low", "up_large"),
        ("not gritty", TagId.STREET_CHARACTER, "low", "up_large"),
        ("not polished", TagId.STREET_CHARACTER, "high", "up_large"),
    ],
)
def test_an_end_of_a_scale_that_is_turned_away_is_a_wish_for_the_other_end(
    text: str, tag_id: TagId, toward: str, step: str
):
    (edit,) = read(text).operations.tag_ops
    assert (edit.tag_id, edit.action, edit.toward, edit.step) == (tag_id, "nudge", toward, step)
    (held,) = reduced(read(text)).spec.tags
    assert (held.tag_id, held.toward) == (tag_id, toward)
    # And never both ends at once.
    end = text.removeprefix("not too ").removeprefix("not ").removeprefix("no ")
    both = read(f"{end} and {text}")
    assert (both.operations, both.status) == (NO_OPERATIONS, InterpretStatus.SUGGEST)


@pytest.mark.parametrize(
    ("text", "feature_id"),
    [
        ("less traffic noise", FeatureId.NOISE_EXPOSURE),
        ("no noise", FeatureId.NOISE_EXPOSURE),
        ("not too noisy", FeatureId.NOISE_EXPOSURE),
        ("without traffic noise", FeatureId.NOISE_EXPOSURE),
        ("I worry about noise", FeatureId.NOISE_EXPOSURE),
        ("no fumes", FeatureId.AIR_NO2),
        ("less pollution", FeatureId.AIR_NO2),
        ("without much burglary", FeatureId.CRIME_BURGLARY_THEFT),
        ("no violent crime", FeatureId.CRIME_VIOLENCE_ROBBERY),
    ],
)
def test_wanting_less_of_a_nuisance_is_caring_about_it(text: str, feature_id: FeatureId):
    result = read(text)
    (edit,) = (e for e in result.operations.weight_ops if e.feature_id is feature_id)
    assert (edit.action, edit.direction) == ("nudge", "default")
    assert edit.step in ("up_small", "up_large")
    assert result.unmet == ()
    after = reduced(result)
    assert after.rejected == ()
    assert weight_of(after.spec, feature_id) >= 0.5


# The plain ways a person asks for little traffic, and what each is read as.
LITTLE_TRAFFIC: list[tuple[str, tuple[FeatureId, ...]]] = [
    ("no traffic", (FeatureId.ROAD_TRAFFIC_NEARBY,)),
    ("less traffic", (FeatureId.ROAD_TRAFFIC_NEARBY,)),
    ("low traffic", (FeatureId.ROAD_TRAFFIC_NEARBY,)),
    ("without heavy traffic", (FeatureId.ROAD_TRAFFIC_NEARBY,)),
    ("no busy roads", (FeatureId.ROAD_TRAFFIC_NEARBY,)),
    ("Less traffic nearby", (FeatureId.ROAD_TRAFFIC_NEARBY,)),
    # A main road is asked of as the homes beside one and as the traffic near home.
    ("away from main roads", (FeatureId.ROAD_MAJOR_EXPOSURE, FeatureId.ROAD_TRAFFIC_NEARBY)),
    ("not near a main road", (FeatureId.ROAD_MAJOR_EXPOSURE, FeatureId.ROAD_TRAFFIC_NEARBY)),
    ("no main roads", (FeatureId.ROAD_MAJOR_EXPOSURE, FeatureId.ROAD_TRAFFIC_NEARBY)),
]


@pytest.mark.parametrize(
    ("text", "features"), LITTLE_TRAFFIC, ids=[said for said, _ in LITTLE_TRAFFIC]
)
def test_a_wish_for_little_traffic_is_a_weight_on_the_traffic_near_home(
    text: str, features: tuple[FeatureId, ...]
):
    result = read(text)
    assert result.status is InterpretStatus.OK and result.unmet == ()
    assert [edit.feature_id for edit in result.operations.weight_ops] == list(features)
    assert {(e.action, e.direction) for e in result.operations.weight_ops} == {("nudge", "default")}
    assert result.operations.tag_ops == ()
    after = reduced(result)
    assert after.rejected == ()
    for feature_id in features:
        assert weight_of(after.spec, feature_id) >= 0.25
        held = next(w for w in after.spec.weights if w.feature_id is feature_id)
        assert held.direction == "less"


def test_a_release_that_ranks_no_area_on_main_roads_alone_still_answers_with_traffic():
    """A build of London shows main roads and ranks no area on them alone. A person who
    asks to be away from them is answered with the traffic near home, and is told that
    the other is not in the data: never that alone."""
    release = small_release()
    shown_only = dataclasses.replace(
        release,
        metrics=tuple(
            m.replace(rankable=False) if m.feature_id is FeatureId.ROAD_MAJOR_EXPOSURE else m
            for m in release.metrics
        ),
    )
    result = READER.interpret(
        InterpretRequest(text="away from main roads", spec=RENTER, release=shown_only)
    )
    after = apply(RENTER, result.operations, shown_only)
    assert [(r.group, r.reason) for r in after.rejected] == [("weight_ops", "not_in_release")]
    assert weight_of(after.spec, FeatureId.ROAD_TRAFFIC_NEARBY) >= 0.5
    assert weight_of(after.spec, FeatureId.ROAD_MAJOR_EXPOSURE) == 0.0


@pytest.mark.parametrize("text", ["quiet road", "a quiet road", "quiet roads"])
def test_a_quiet_road_is_a_quiet_street(text: str):
    (edit,) = read(text).operations.tag_ops
    assert (edit.tag_id, edit.action, edit.toward) == (TagId.QUIET_RESIDENTIAL, "nudge", "high")
    assert read(text).operations.weight_ops == ()
    assert read(text).operations == read(text.replace("road", "street")).operations


@pytest.mark.parametrize(
    "text",
    [
        "not on a busy road",
        "I don't want to live on a busy road",
        "somewhere that isn't on a main road",
        "traffic",
        "busy roads",
        "I don't mind a bit of traffic",
        "I like being on a busy road, it feels alive",
    ],
)
def test_traffic_in_words_the_rules_cannot_place_is_offered_one_way_and_never_applied(text: str):
    """'On' is no word the grammar places, and a nuisance that is only named may be liked.
    So nothing is applied, and less of it is the one thing that can be chosen."""
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert result.status is InterpretStatus.SUGGEST
    offered = {found.target: found for found in result.suggestions}
    traffic = offered[f"feature:{FeatureId.ROAD_TRAFFIC_NEARBY}"]
    assert traffic.label == "Less traffic nearby"
    assert [choice.direction for choice in traffic.choices] == ["less", "ignore"]
    for found in result.suggestions:
        assert "more" not in [choice.direction for choice in found.choices], found.target


def test_the_noise_of_traffic_is_the_noise_and_not_the_traffic():
    for text in ("less traffic noise", "no traffic noise"):
        assert [e.feature_id for e in read(text).operations.weight_ops] == [
            FeatureId.NOISE_EXPOSURE
        ]


def test_only_what_it_is_a_nuisance_to_have_is_marked_as_one():
    assert {
        FeatureId.CRIME_VIOLENCE_ROBBERY,
        FeatureId.CRIME_BURGLARY_THEFT,
        FeatureId.AIR_NO2,
        FeatureId.NOISE_EXPOSURE,
        FeatureId.ROAD_MAJOR_EXPOSURE,
        FeatureId.EVENING_CLUSTER_EXPOSURE,
        FeatureId.INCIDENT_CRIMINAL_DAMAGE,
        FeatureId.INCIDENT_ANTISOCIAL,
        FeatureId.ROAD_TRAFFIC_NEARBY,
    } == NUISANCES
    assert {f for f, feature in FEATURES.items() if feature.kind is FeatureKind.NUISANCE} == (
        NUISANCES
    )
    # Each is a feature that lower is better for, and that can be no other way.
    assert {FEATURES[f].polarity for f in NUISANCES} == {Polarity.LESS}
    for phrase, target in LEXICON.items():
        if target.nuisance:
            assert set(target.features) <= NUISANCES, phrase
            assert not target.tags, phrase
        if target.wanted_low:
            assert target.nuisance, phrase
    # A phrase that says low is the wish itself. One that only names is not.
    assert LEXICON["clean air"].wanted_low and LEXICON["low crime"].wanted_low
    assert not LEXICON["noise"].wanted_low
    assert not LEXICON["safe"].nuisance


@pytest.mark.parametrize("text", ["noise", "I like noise", "I love crime", "pollution, pubs"])
def test_a_nuisance_that_is_only_named_or_is_liked_makes_no_edit(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert result.status is InterpretStatus.SUGGEST
    for found in result.suggestions:
        if found.target.removeprefix("feature:") in {f.value for f in NUISANCES}:
            # Less of it is the one thing that can be chosen.
            assert [c.direction for c in found.choices] == ["less", "ignore"]


@pytest.mark.parametrize("text", ["I care about noise", "noise matters to me", "low crime"])
def test_a_nuisance_that_is_said_to_count_is_cared_about(text: str):
    result = read(text)
    assert result.status is InterpretStatus.OK
    assert {e.action for e in result.operations.weight_ops} == {"nudge"}
    assert {e.feature_id for e in result.operations.weight_ops} <= NUISANCES


@pytest.mark.parametrize(
    ("text", "feature_id"),
    [
        ("not far from a station", FeatureId.STATION_WALK),
        ("not too far from a park", FeatureId.PARK_PROXIMITY),
        ("less than 10 minutes to a park", FeatureId.PARK_PROXIMITY),
        ("no more than 10 minutes to a park", FeatureId.PARK_PROXIMITY),
        ("much more green space", FeatureId.GREEN_COVER),
        ("within walking distance of a station", FeatureId.STATION_WALK),
        ("no students near a park", FeatureId.PARK_PROXIMITY),
        ("not Cindermoor, near a park", FeatureId.PARK_PROXIMITY),
        ("no students, but a park nearby", FeatureId.PARK_PROXIMITY),
    ],
)
def test_a_turn_of_phrase_the_reader_understands_is_a_wish(text: str, feature_id: FeatureId):
    # Each holds a word that turns, and each is a fixed turn of phrase with one
    # meaning that the reader has a rule for: "not far from", a limit on a number.
    result = read(text)
    (edit,) = (e for e in result.operations.weight_ops if e.feature_id is feature_id)
    assert (edit.action, edit.step) == ("nudge", "up_large")
    assert UnmetCategory.OTHER not in result.unmet
    assert weight_of(reduced(result).spec, feature_id) >= 0.5


TWO_SIGNS = [
    # Two of them made a wish again, by counting. The count was wrong as often as right.
    "I don't want to be far from a park",
    "never far from the high street",
    "I can't live without a park",
    "I cannot do without a station",
    "nothing beats a good park",
    "why not a park",
    "I wouldn't say no to a park",
    "not without a park",
    "I would never avoid a park",
    "it isn't that I dislike parks",
    "no parks? not likely",
    # Words the reader does not know, each of which once stood in a rule of its own.
    "nothing too buzzy",
    "far from the river",
    "I hate village life, not a village",
    "away from traffic noise",
    "I hate noise",
    "far from the fumes",
    "a few theatres",
    "far more parks",
    "I hate pubs",
    "away from the bars",
    "nowhere near a pub",
    "slightly fewer parks than now",
    # One word that turns, and words the reader has no rule for.
    "I would not mind a park",
    "no end of parks",
    "not only parks",
    "parks, not that I care",
    "it doesn't have to be leafy",
    "it isn't leafy",
    "anything but leafy",
    "too leafy",
    "leafy enough",
    "somewhere leafy that isn't too far out",
]


@pytest.mark.parametrize("text", TWO_SIGNS)
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renter", "buyer"])
def test_in_doubt_the_reader_makes_no_edit_and_says_so(text: str, spec: PreferenceSpec):
    result = read(text, spec)
    assert result.operations == NO_OPERATIONS
    # The thing is offered, and the words that were not read are pointed to.
    assert (result.status, result.notice) == (InterpretStatus.SUGGEST, Notice.NONE)
    assert result.unmet == (UnmetCategory.OTHER,)
    assert result.suggestions and result.unread
    assert result.clarify == ()
    assert reduced(result, spec).spec == spec


# A place that the words ask to be kept away from, by a word for far or by a least. It
# is heard, and nothing of it can be chosen: Burro cannot rank on being far from a place.
FAR_FROM_A_PLACE = [
    "not near Pellam Cross",
    "nowhere near Pellam Cross",
    "anywhere but near Foxholt Works",
    "far from Pellam Cross",
    "a long way from Pellam Cross Station",
    "at least 45 minutes from Foxholt Works",
    # By what stands after it, too.
    "30 minutes to Pellam Cross is too far",
]
# A place that is turned away by what stands before it.
AWAY_FROM_A_PLACE = [
    "I don't want to be near Foxholt Works",
    "I don't work at Foxholt Works",
    "I wouldn't want to be 30 minutes to Pellam Infirmary",
]
# And one that is put in doubt by what stands after it.
NOT_TO_A_PLACE = [
    "I work at Foxholt Works, not really",
    "near Foxholt Works? No.",
    "maybe near Foxholt Works",
]


@pytest.mark.parametrize("text", [*FAR_FROM_A_PLACE, *AWAY_FROM_A_PLACE, *NOT_TO_A_PLACE])
def test_a_place_named_in_a_doubtful_clause_adds_no_journey(text: str):
    # "Nowhere near Pellam Cross" added a journey to it, and put its area first.
    result = read(text)
    assert (result.operations, result.clarify) == (NO_OPERATIONS, ())
    assert result.unmet == (UnmetCategory.OTHER,)
    assert reduced(result).spec.commutes == ()
    journeys = [found for found in result.suggestions if found.target == "commute"]
    if text in FAR_FROM_A_PLACE:
        # It is said to have been heard, with nothing to choose but to leave it out.
        (heard,) = journeys
        assert [c.direction for c in heard.choices] == ["ignore"]
        assert heard.note == "Burro cannot rank on being far from a place."
    elif text in AWAY_FROM_A_PLACE:
        # To add the journey would be the opposite of what was said, so it is not offered.
        assert (result.status, journeys) == (InterpretStatus.OK, [])
    else:
        # The journey is offered, and is added only if the person chooses it.
        (journey,) = journeys
        assert [c.direction for c in journey.choices] == ["more", "ignore"]
        assert result.status is InterpretStatus.SUGGEST


@pytest.mark.parametrize(
    "text",
    [
        "why not Cindermoor",
        "I would not avoid Cindermoor",
        "not only in Farrowmere",
        "only in Farrowmere? no",
        "I wouldn't say only in Farrowmere",
        "never avoid Cindermoor",
        "except Cindermoor",
        "unless it is Cindermoor",
        "rather than Cindermoor",
        "not Cindermoor, not really",
        "Cindermoor is not for me",
    ],
)
def test_an_area_rule_is_made_only_in_the_words_the_contract_gives(text: str):
    result = read(text)
    assert result.operations.area_ops == ()
    assert reduced(result).spec.areas == ()
    assert result.unmet == (UnmetCategory.OTHER,)


@pytest.mark.parametrize(
    "text",
    [
        "I'm not looking to buy",
        "I don't want to rent",
        "not a studio",
        "we are not buying",
        "I wouldn't rent again",
        "renting? never",
    ],
)
def test_a_tenure_or_a_kind_of_home_in_a_doubtful_clause_is_left_alone(text: str):
    # "I'm not looking to buy" moved the search to buying.
    for spec in (RENTER, BUYER):
        result = read(text, spec)
        assert result.operations == NO_OPERATIONS
        assert reduced(result, spec).spec == spec
    assert read("I want to buy, not rent").operations.budget_ops[0].tenure == "buy"
    assert read("renting, not buying").operations.budget_ops[0].tenure == "rent"


@pytest.mark.parametrize(
    "text",
    [
        "Quiet, 30 minutes to Pellam Cross, £1,500 pcm, and I can't live without a park",
        "Quiet, 30 minutes to Pellam Cross, £1,500 pcm. I can't live without a park.",
    ],
)
def test_nothing_of_a_request_is_applied_when_one_sentence_of_it_is_in_doubt(text: str):
    # It is all or nothing, in one sentence or in two: no single word is ever the
    # fault, so not even the budget is applied. Everything that was noticed is offered.
    result = read(text)
    assert (result.operations, result.unmet) == (NO_OPERATIONS, (UnmetCategory.OTHER,))
    assert result.status is InterpretStatus.SUGGEST
    assert [(found.target, found.label) for found in result.suggestions] == [
        ("tag:quiet_residential", "Quiet streets"),
        ("commute", "Pellam Cross"),
        ("budget", "A budget of £1,500 a month"),
        ("feature:park_proximity", "Nearer a park"),
    ]
    assert [text[span.start : span.end] for span in result.unread] == [
        "and I can't live without a" if "and" in text else "I can't live without a",
    ]
    # Every choice is the person's own edit, and none is turned away.
    for found in result.suggestions:
        *choices, ignore = found.choices
        assert (ignore.direction, ignore.operations) == ("ignore", NO_OPERATIONS)
        for choice in choices:
            chosen = apply(RENTER, choice.operations, small_release())
            assert chosen.rejected == () and chosen.spec != RENTER
            for group in OpsGroup:
                for edit in getattr(choice.operations, group.value):
                    assert edit.provenance == "ui_edit"
    # A choice says all that it holds: the place, and the minutes said of it.
    (journey,) = (found for found in result.suggestions if found.target == "commute")
    assert journey.choices[0].label == "Add a journey to Pellam Cross within 30 minutes"
    assert journey.choices[0].operations.commute_ops[0].max_minutes == 30
    assert [text[span.start : span.end] for span in journey.spans] == ["30 minutes to Pellam Cross"]


# Prompts that are not plain, in which something stands beside a place, an
# amount or a home that the choice once carried and its label did not say.
NOT_PLAIN = [
    "I used to pay £1,800 a month for a 3 bed flat",
    "Happy anywhere as long as it is under £450k",
    "at least 45 minutes from Foxholt Works",
    "30 minutes to Pellam Cross by bike is too long",
    "not within 40 minutes of Foxholt Works",
    "My budget is about £2,000 a month for a two bed flat, I think",
    "maybe a studio to rent for £900 pcm",
    "I was renting a room for £700, now buying a terraced house for about £650k",
    "we might buy a semi detached house near Pellam Infirmary, no more than 30 minutes by tube",
    "Quiet, 30 minutes to Pellam Cross, £1,500 pcm, and I can't live without a park",
    "I love Cindermoor but my partner prefers Alderwick",
    "pubs are so noisy",
    "is it gritty or polished",
]
SAID_OF_A_HOME = {
    "bed_1": "1-bedroom home",
    "bed_2": "2-bedroom home",
    "bed_3": "3-bedroom home",
    "studio": "studio",
    "room": "room in a shared home",
    "flat": "flat",
    "terraced": "terraced house",
    "semi_detached": "semi-detached house",
    "detached": "detached house",
}


def named_in(label: str, edit: dict[str, Any], release: InMemoryRelease) -> list[str]:
    """What an edit holds that the label of its choice does not say."""
    unsaid: list[str] = []

    def must(field: str, *words: str) -> None:
        if field in edit and not any(word in label for word in words):
            unsaid.append(f"{field}: {edit[field]}")

    if "amount" in edit:
        must("amount", f"£{edit['amount']:,}")
    if "tenure" in edit:
        must("tenure", {"rent": "rent", "buy": "buy"}[edit["tenure"]])
    if "segment" in edit:
        must("segment", SAID_OF_A_HOME[edit["segment"]])
    if "place_id" in edit:
        place = release.place(edit["place_id"])
        must("place_id", place.name if place else "?")
    if "area_id" in edit:
        area = release.neighbourhood(edit["area_id"])
        must("area_id", area.name if area else "?")
    if "max_minutes" in edit:
        must("max_minutes", f"{edit['max_minutes']} minutes")
    for field, said in (("mode", "by"), ("strictness", "no more than")):
        must(field, said)
    return unsaid


@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renter", "buyer"])
@pytest.mark.parametrize("text", NOT_PLAIN)
def test_a_choice_holds_nothing_that_its_label_does_not_say(text: str, spec: PreferenceSpec):
    result = read(text, spec)
    assert result.operations == NO_OPERATIONS
    quiet = ("unchanged", "none", "default", 0, 0.0)
    for found in result.suggestions:
        for choice in found.choices:
            held = choice.operations.model_dump(mode="json")
            for group in ("budget_ops", "commute_ops", "area_ops"):
                for edit in held[group]:
                    said = {k: v for k, v in edit.items() if v not in quiet}
                    assert named_in(choice.label, said, small_release()) == [], choice.label
    # And the words a choice does not rest on are said to be unread.
    rested = [(span.start, span.end) for found in result.suggestions for span in found.spans]
    for span in result.unread:
        assert not any(start < span.end and span.start < end for start, end in rested)


def test_a_budget_is_offered_as_its_amount_and_the_size_of_home_as_a_choice_of_its_own():
    result = read("My budget is about £2,000 a month for a two bed flat, I think")
    assert [(found.target, found.label) for found in result.suggestions] == [
        ("budget", "A budget of £2,000 a month"),
        ("budget", "A 2-bedroom home"),
    ]
    amount, size = (found.choices[0] for found in result.suggestions)
    assert (amount.label, size.label) == ("Set a budget of £2,000 a month", "Set a 2-bedroom home")
    assert edits_of(amount) == [{"action": "set", "amount": 2000, "provenance": "ui_edit"}]
    assert edits_of(size) == [{"action": "set", "segment": "bed_2", "provenance": "ui_edit"}]
    text = "My budget is about £2,000 a month for a two bed flat, I think"
    rested = [[text[s.start : s.end] for s in found.spans] for found in result.suggestions]
    assert rested == [["£2,000 a month"], ["a two bed flat"]]
    unread = [text[span.start : span.end] for span in result.unread]
    assert unread == ["My budget is about", "I think"]
    # What stands between the amount and the home asks for nothing, and is not called unread.
    assert [text[span.start : span.end] for span in result.asks_nothing] == ["for"]


def test_words_that_say_what_the_search_already_holds_are_not_called_unread():
    # Seen in a browser: words that named what the search held were marked as not read.
    # There is nothing to offer for them, and they were heard all the same.
    holds = reduced(read("I work at Pellam Cross")).spec
    assert [journey.place_id for journey in holds.commutes] == [place_id(1)]
    text = "I have never lived there. I work at Pellam Cross, near a station."
    result = read(text, holds)
    assert [(found.target, found.label) for found in result.suggestions] == [
        ("feature:station_walk", "Nearer a station")
    ]
    unread = [text[span.start : span.end] for span in result.unread]
    assert unread == ["I have never lived there. I work at"]


def test_a_home_is_offered_whether_or_not_the_search_already_holds_it():
    # "On a one bed flat", typed by a renter whose search is for one bedroom, was
    # offered nowhere, because to choose it would change nothing. A person who
    # names a home is now told that it was heard.
    text = "I have never lived there. I can spend about £1,600 a month on a one bed flat."
    assert RENTER.budget.segment == "bed_1"
    result = read(text)
    assert [(found.target, found.label) for found in result.suggestions] == [
        ("budget", "A budget of £1,600 a month"),
        ("budget", "A 1-bedroom home"),
    ]
    unread = [text[span.start : span.end] for span in result.unread]
    assert unread == ["I have never lived there. I can spend about"]
    assert [text[span.start : span.end] for span in result.asks_nothing] == ["on"]
    other = read(text.replace("one bed", "two bed"))
    assert [found.label for found in other.suggestions][1:] == ["A 2-bedroom home"]
    # A terraced house is no kind of home to rent. Nobody has chosen to rent
    # here, so it is offered as what it can be held as, and the choice says so.
    text = "I have never lived there. A terraced house."
    (found,) = read(text).suggestions
    assert [choice.label for choice in found.choices] == [
        "Set a terraced house, to buy",
        "Leave it out",
    ]
    assert found.note == "Burro holds rents by the number of bedrooms, and not by kind of home."
    assert [text[s.start : s.end] for s in read(text).unread] == ["I have never lived there"]


def edits_of(choice: Any) -> list[dict[str, Any]]:
    quiet = ("unchanged", "none", "default", 0, 0.0)
    held = choice.operations.model_dump(mode="json")
    return [
        {k: v for k, v in edit.items() if v not in quiet}
        for group in held.values()
        for edit in group
    ]


def test_an_amount_that_cannot_be_of_the_tenure_of_the_search_says_which_it_is_of():
    # No rent is this high, so the choice moves the search to buying, and says so.
    (found,) = read("Happy anywhere as long as it is under £450k", RENTER).suggestions
    assert found.choices[0].label == "Set a budget of £450,000, to buy"
    assert edits_of(found.choices[0]) == [
        {"action": "set", "tenure": "buy", "amount": 450000, "provenance": "ui_edit"}
    ]
    (found,) = read("Happy anywhere as long as it is under £450k", BUYER).suggestions
    assert found.choices[0].label == "Set a budget of £450,000"
    (found,) = read("maybe £1,500 a month", BUYER).suggestions
    assert found.choices[0].label == "Set a budget of £1,500 a month, to rent"
    # An amount that is no rent and no price is offered to nobody.
    assert read("maybe £40,000").suggestions == ()


@pytest.mark.parametrize(
    "text",
    ["I don't rent", "I want to stop renting", "not buying", "I can't buy", "never a studio"],
)
def test_what_stands_straight_after_a_word_that_turns_it_away_is_not_offered_to_be_set(text: str):
    # The one choice there was would have been the opposite of what was said.
    result = read(text)
    assert (result.operations, result.suggestions) == (NO_OPERATIONS, ())
    assert result.unmet == (UnmetCategory.OTHER,)


def test_an_area_that_is_only_named_may_be_the_only_one_or_be_left_out():
    (found,) = read("I love Cindermoor").suggestions
    assert [(choice.direction, choice.label) for choice in found.choices] == [
        ("more", "Look only in Cindermoor"),
        ("less", "Leave out Cindermoor"),
        ("ignore", "Leave it out"),
    ]
    only, out, _ = found.choices
    assert [edit.action for edit in only.operations.area_ops] == ["only"]
    assert [edit.action for edit in out.operations.area_ops] == ["exclude"]
    # After a word that turns it away, to look only there is not offered.
    (found,) = read("please avoid Cindermoor if you can").suggestions
    assert [choice.direction for choice in found.choices] == ["less", "ignore"]


def test_wanting_fewer_of_something_is_a_direction_where_the_feature_allows_one():
    fewer = read("fewer pubs").operations.weight_ops[0]
    assert (fewer.feature_id, fewer.direction, fewer.step) == (
        "venue_evening_per_homes",
        "less",
        "up_large",
    )
    more = read("lots of pubs").operations.weight_ops[0]
    assert (more.direction, more.step) == ("default", "up_large")
    # Noise has one direction. Wanting less of it is caring about it.
    noise = read("less traffic noise").operations.weight_ops[0]
    assert (noise.feature_id, noise.direction, noise.action) == (
        "noise_exposure",
        "default",
        "nudge",
    )
    assert reduced(read("fewer pubs and less traffic noise")).rejected == ()
    for text in ("no pubs", "I don't want pubs", "without bars", "not near a pub", "avoid pubs"):
        (edit,) = read(text).operations.weight_ops
        assert (edit.feature_id, edit.direction, edit.action) == (
            "venue_evening_per_homes",
            "less",
            "nudge",
        )
        assert read(text).unmet == ()


def test_crime_is_weighted_only_when_it_is_asked_for_in_so_many_words():
    asked = read("low crime")
    assert {e.provenance for e in asked.operations.weight_ops} == {EditProvenance.STATED}
    assert reduced(asked).rejected == ()
    assert {w.feature_id for w in reduced(asked).spec.weights} >= {
        FeatureId.CRIME_BURGLARY_THEFT,
        FeatureId.CRIME_VIOLENCE_ROBBERY,
    }

    # "Safe" names no crime, so it sets none counting. Recorded crime is
    # offered by its name, and counts if the person chooses it.
    for text in ("somewhere safe", "somewhere safe, near a park"):
        implied = read(text)
        assert (implied.operations, implied.assumptions) == (NO_OPERATIONS, ())
        assert reduced(implied).spec == RENTER
        assert [found.target for found in implied.suggestions][:2] == [
            "feature:crime_violence_robbery",
            "feature:crime_burglary_theft",
        ]
    # Beside a wish that names it, the person has asked by name.
    both = read("somewhere safe, with low crime")
    assert {e.provenance for e in both.operations.weight_ops} == {EditProvenance.STATED}
    assert (both.status, both.suggestions, both.unread) == (InterpretStatus.OK, (), ())
    assert reduced(both).rejected == ()
    # A model that reads it into crime is still turned away by the reducer.
    inferred = asked.operations.replace(
        weight_ops=tuple(e.replace(provenance="inferred") for e in asked.operations.weight_ops)
    )
    turned_away = apply(RENTER, inferred, small_release())
    assert {r.reason for r in turned_away.rejected} == {RejectReason.CRIME_NEEDS_EXPLICIT_REQUEST}


CANNOT_SAY_SAFE = (
    "Burro cannot say how safe a place is. It can count recorded crime. "
    "Recorded crime depends on what is reported, and locations are approximate."
)
NO_POOLS = (
    "Burro cannot tell a swimming pool or a leisure centre from any other place to train. "
    "The nearest it can count is gyms and fitness studios."
)
# What is nearest is Village feel, which is a rough guide, and its offer says so.
NO_NEIGHBOURS = (
    "Burro cannot measure whether neighbours know each other. The nearest it can count is "
    "a village feel: a high street in a conservation area, homes that stand apart and "
    "period homes. Rough guide. Of the areas it puts highest, about half read as villages "
    "to people, and it takes some busy main roads and some grand inner streets for villages."
)
NOT_ONE_HOME = (
    "Burro cannot see whether one home has a garden. "
    "It can count how much of an area is residential garden."
)
# The first words a newcomer reaches for, what is offered for each, and what is said.
NEWCOMER = [
    ("safe", "feature:crime_violence_robbery", "less", CANNOT_SAY_SAFE),
    ("somewhere safe", "feature:crime_burglary_theft", "less", CANNOT_SAY_SAFE),
    ("I want to feel safe", "feature:crime_violence_robbery", "less", CANNOT_SAY_SAFE),
    ("a swimming pool nearby", "feature:venue_gym_per_homes", "more", NO_POOLS),
    ("a leisure centre", "feature:venue_gym_per_homes", "more", NO_POOLS),
    ("a sense of community", "tag:village_feel", "more", NO_NEIGHBOURS),
    ("community feel", "tag:village_feel", "more", NO_NEIGHBOURS),
    ("somewhere neighbourly", "tag:village_feel", "more", NO_NEIGHBOURS),
    ("a big garden", "feature:land_gardens", "more", NOT_ONE_HOME),
    ("I want a big garden", "feature:land_gardens", "more", NOT_ONE_HOME),
    ("a flat with a garden", "feature:land_gardens", "more", NOT_ONE_HOME),
    ("leafy, quiet and safe", "feature:crime_violence_robbery", "less", CANNOT_SAY_SAFE),
]


@pytest.mark.parametrize(("text", "target", "direction", "note"), NEWCOMER)
def test_a_word_burro_has_no_measure_for_is_offered_what_is_nearest_and_told_what_it_lacks(
    text: str, target: str, direction: str, note: str
):
    # Each of these led nowhere: no edit, no suggestion, and a line about settings.
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert (result.status, result.assumptions) == (InterpretStatus.SUGGEST, ())
    found = next(found for found in result.suggestions if found.target == target)
    assert found.note == note
    # What is nearest can be chosen, and to choose it changes the search.
    first = found.choices[0]
    assert (first.direction, found.choices[-1].direction) == (direction, "ignore")
    pressed = apply(RENTER, first.operations, small_release())
    assert pressed.rejected == () and pressed.spec != RENTER
    # The words it rests on are not reported as words nothing was made of.
    rested = [(span.start, span.end) for span in found.spans]
    assert rested and not [
        span for span in result.unread if any(s < span.end and span.start < e for s, e in rested)
    ]


# What a person asks for by name, and the figure for each 1,000 homes it is ranked on. The
# count of each is shown beside it, and no word asks to be ranked on a count.
BY_NAME = [
    ("cafes", "venue_cafe_per_homes", "stated"),
    ("coffee shops", "venue_cafe_per_homes", "stated"),
    ("good coffee", "venue_cafe_per_homes", "inferred"),
    ("near a gym", "venue_gym_per_homes", "stated"),
    ("gyms", "venue_gym_per_homes", "stated"),
    ("yoga", "venue_gym_per_homes", "inferred"),
    ("pubs", "venue_evening_per_homes", "stated"),
    ("a good pub", "venue_evening_per_homes", "stated"),
    ("bars", "venue_evening_per_homes", "stated"),
]


@pytest.mark.parametrize(("text", "feature_id", "provenance"), BY_NAME)
def test_a_wish_for_cafes_gyms_or_pubs_is_ranked_on_the_figure_for_each_1000_homes(
    text: str, feature_id: str, provenance: str
):
    result = read(text)
    assert (result.status, result.suggestions, result.unread) == (InterpretStatus.OK, (), ())
    (edit,) = result.operations.weight_ops
    assert (edit.feature_id, edit.provenance) == (feature_id, provenance)
    assert (edit.action, edit.direction) == ("nudge", "default")
    assert edit.feature_id not in RANKED_AS
    pressed = apply(RENTER, result.operations, small_release())
    assert pressed.rejected == () and pressed.spec != RENTER


def test_a_cafe_is_no_longer_read_as_any_place_to_eat_and_drink():
    """It was, while Burro had no count of cafes. A restaurant still is."""
    for text, feature_id in (
        ("cafes", "venue_cafe_per_homes"),
        ("restaurants", "venue_food_drink_per_homes"),
        ("places to eat", "venue_food_drink_per_homes"),
    ):
        assert [e.feature_id for e in read(text).operations.weight_ops] == [feature_id]


def test_a_wish_for_no_cafes_or_gyms_takes_the_measure_off_and_one_for_no_pubs_is_read():
    """A person may want fewer pubs. A cafe and a gym have the one direction, more."""
    for text, feature_id in (
        ("no cafes", "venue_cafe_per_homes"),
        ("no gyms", "venue_gym_per_homes"),
    ):
        (off,) = read(text).operations.weight_ops
        assert (off.feature_id, off.action, off.direction) == (feature_id, "remove", "default")
    (fewer,) = read("no pubs").operations.weight_ops
    assert (fewer.feature_id, fewer.direction) == ("venue_evening_per_homes", "less")


def test_recorded_crime_that_is_chosen_from_an_offer_counts_as_asked_for_by_name():
    # The offer names recorded crime on its face, so to press it is to ask by name.
    result = read("somewhere safe")
    labels = [[choice.label for choice in found.choices] for found in result.suggestions]
    assert labels == [
        ["Less recorded violence and robbery", "Leave it out"],
        ["Less recorded burglary and theft", "Leave it out"],
    ]
    spec = RENTER
    for found in result.suggestions:
        spec = apply(spec, found.choices[0].operations, small_release()).spec
    weighed = {w.feature_id: w.provenance for w in spec.active_weights}
    assert weighed[FeatureId.CRIME_VIOLENCE_ROBBERY] == "ui_edit"
    assert weighed[FeatureId.CRIME_BURGLARY_THEFT] == "ui_edit"


@pytest.mark.parametrize("text", ["cheap", "somewhere cheap", "cheap rent", "low rent"])
def test_cheap_is_no_verdict_burro_gives_and_is_heard_as_that(text: str):
    # It was a word the reader did not know, so nothing at all was said of it.
    result = read(text)
    assert (result.operations, result.status) == (NO_OPERATIONS, InterpretStatus.OK)
    assert result.unmet == (UnmetCategory.AFFORDABILITY_VERDICT,)
    assert (result.suggestions, result.unread) == ((), ())
    # Beside a wish that is plain, the wish is applied and cheap is heard.
    beside = read(f"leafy, {text}")
    assert [edit.tag_id for edit in beside.operations.tag_ops] == ["leafy"]
    assert beside.unmet == (UnmetCategory.AFFORDABILITY_VERDICT,)


@pytest.mark.parametrize(
    ("text", "unmet"),
    [
        # "Fast" and "risk" are no words of the grammar, and that is said too.
        ("fast broadband", [UnmetCategory.BROADBAND, UnmetCategory.OTHER]),
        ("not at risk of flooding", [UnmetCategory.FLOOD_RISK, UnmetCategory.OTHER]),
        ("broadband", [UnmetCategory.BROADBAND]),
        ("no flooding", [UnmetCategory.FLOOD_RISK]),
        ("a good dentist nearby", [UnmetCategory.HEALTH_SERVICES]),
        ("easy parking, I drive to work", [UnmetCategory.DRIVING]),
        ("show me listings", [UnmetCategory.LISTINGS]),
        ("what is on the market", [UnmetCategory.LISTINGS, UnmetCategory.OTHER]),
        ("can I afford it?", [UnmetCategory.AFFORDABILITY_VERDICT]),
        ("is it good value", [UnmetCategory.AFFORDABILITY_VERDICT]),
        ("somewhere in the commuter belt", [UnmetCategory.OUTSIDE_THE_CITY]),
        ("what is the capital of France", [UnmetCategory.OTHER]),
        ("asdf ghjk", [UnmetCategory.OTHER]),
        ("broadband, and a park nearby", [UnmetCategory.BROADBAND]),
        # What no open data measures at the scale of a neighbourhood.
        ("clean streets", [UnmetCategory.STREET_CLEANLINESS]),
        ("well maintained", [UnmetCategory.UPKEEP]),
        ("highly rated", [UnmetCategory.RATINGS]),
        ("opening hours", [UnmetCategory.PRICES_AND_HOURS]),
        ("good mobile signal", [UnmetCategory.MOBILE_COVERAGE]),
        ("gentrifying", [UnmetCategory.CHANGE_OVER_TIME]),
    ],
)
def test_what_burro_cannot_answer_is_reported_by_category(text: str, unmet: list[UnmetCategory]):
    result = read(text)
    assert list(result.unmet) == unmet
    assert result.status is InterpretStatus.OK
    # `other` is there exactly when some stretch of the text was made nothing of.
    assert (UnmetCategory.OTHER in result.unmet) == bool(result.unread or result.asks_nothing)


def test_what_is_heard_rests_on_the_words_said_of_it_and_the_rest_is_offered():
    # "Fast" is no word of the grammar, so the park is not applied. It is offered.
    result = read("fast broadband near a park")
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    assert result.unmet == (UnmetCategory.BROADBAND, UnmetCategory.OTHER)
    assert [(span.start, span.end) for span in result.unread] == [(0, 4)]
    assert [found.target for found in result.suggestions] == ["feature:park_proximity"]
    # Said plainly, the park is applied.
    plain = read("broadband near a park")
    assert [e.feature_id for e in plain.operations.weight_ops] == ["park_proximity"]
    assert plain.unmet == (UnmetCategory.BROADBAND,)


def test_the_rule_interpreter_never_answers_off_topic_and_never_fails():
    texts = ["?", "🙂", "a" * 600, "£", "not", "near", "work at", "30 minutes to", "\n\t", "0"]
    texts += ["' OR 1=1 --", "{}{}{0}", "%s %d", "only", "avoid", "under", "£££ k m"]
    texts += [
        "£" + "9" * 500,
        "9" * 400 + " minutes to Pellam Cross",
        "budget 1e999",
        "9" * 30 + "k",
    ]
    texts += ["not " * 150, "work at " * 75, "near " * 120, "1,1,1," * 100, "£1.2.3.4m", "0 bed"]
    for text in texts:
        result = read(text)
        assert result.status in (
            InterpretStatus.OK,
            InterpretStatus.CLARIFY,
            InterpretStatus.SUGGEST,
        )
        assert result.notice is Notice.NONE
        reduced(result)


@pytest.mark.parametrize("text", ["", "a" * 601])
def test_text_outside_one_to_600_characters_is_refused_without_repeating_it(text: str):
    with pytest.raises(ValueError, match="1 to 600 characters") as caught:
        InterpretRequest(text=text + CANARY * bool(text), spec=RENTER, release=small_release())
    assert CANARY not in str(caught.value)


def test_a_request_does_not_show_its_text_when_it_is_printed():
    request = InterpretRequest(text=f"I work at {CANARY}", spec=RENTER, release=small_release())
    assert CANARY not in repr(request)
    assert CANARY not in str(request)
    assert CANARY not in f"{request}"


@pytest.mark.parametrize(
    "text",
    [
        f"I work at {CANARY} and want a quiet place",
        f"near {CANARY} Cross",
        f"not {CANARY}, avoid {CANARY}",
        f"{CANARY} {CANARY} students {CANARY}",
        f"30 minutes to {CANARY} Works by bike, £1,500 pcm",
        f"my {CANARY} needs fast broadband",
    ],
)
def test_interpret_result_holds_no_user_text(text: str):
    result = read(text)
    assert CANARY not in result.model_dump_json()
    assert CANARY not in repr(result)
    after = reduced(result)
    assert CANARY not in after.model_dump_json()
    assert CANARY not in canonical(after.spec)


def test_the_rule_interpreter_is_an_interpreter_and_gives_the_same_answer_every_time():
    interpreter: Interpreter = RuleInterpreter()
    assert interpreter.name is InterpreterName.RULE
    request = InterpretRequest(
        text="Quiet, near a park, 30 minutes to Pellam Cross, £1,600 pcm",
        spec=RENTER,
        release=small_release(),
    )
    first = interpreter.interpret(request)
    assert all(interpreter.interpret(request) == first for _ in range(20))


def test_both_interpreters_would_state_the_same_assumptions_for_the_same_edits():
    result = read("I work at Foxholt Works, budget £1,500, more pubs")
    assert assumptions_for(result.operations, RENTER) == result.assumptions
    assert {a.code for a in result.assumptions} == {
        AssumptionCode.TENURE,
        AssumptionCode.SEGMENT,
        AssumptionCode.STRICTNESS,
        AssumptionCode.MODE,
        AssumptionCode.MAX_MINUTES,
        AssumptionCode.DIRECTION,
    }
    for assumption in result.assumptions:
        group = getattr(result.operations, assumption.group.value)
        assert 0 <= assumption.index < len(group)

    # Once it is in the spec by the person's own word, it is no longer an assumption.
    chosen = apply(RENTER, result.operations, small_release()).spec
    # Nobody has yet said rent or buy, so that is still assumed.
    assert [a.code for a in assumptions_for(result.operations, chosen)] == [AssumptionCode.TENURE]
    # To name the tenure that a default had chosen is to choose it. Nothing
    # else of the spec moves, and its hash does not.
    stated = apply(chosen, read("to rent").operations, small_release()).spec
    assert stated.tenure_from == "stated"
    assert stated == chosen.replace(tenure_from="stated")
    assert assumptions_for(result.operations, stated) == ()
    assert assumptions_for(NO_OPERATIONS, RENTER) == ()


def test_an_edit_that_names_everything_leaves_nothing_assumed():
    said = read("no more than 30 minutes to Pellam Cross by bike")
    assert said.assumptions == ()
    ops = Operations.model_validate(said.operations.model_dump())
    assert assumptions_for(ops, RENTER) == ()


def test_the_reader_says_what_it_makes_of_each_sentence_for_a_caller_that_holds_a_models_edits():
    request = InterpretRequest(
        text="Quiet, 30 minutes to Pellam Cross. I can't live without a park. No pubs.",
        spec=RENTER,
        release=small_release(),
    )
    reader = RuleInterpreter()
    # The reader itself applies none of it: one sentence of the three is not plain.
    assert reader.interpret(request).operations == NO_OPERATIONS
    alone = reader.by_sentence(request)
    assert edits(alone) == {
        "commute_ops": [
            {"action": "add", "place_id": place_id(1), "max_minutes": 30, "provenance": "stated"}
        ],
        "weight_ops": [
            {
                "action": "nudge",
                "feature_id": "venue_evening_per_homes",
                "step": "up_large",
                "direction": "less",
                "provenance": "stated",
            }
        ],
        "tag_ops": [
            {
                "action": "nudge",
                "tag_id": "quiet_residential",
                "step": "up_large",
                "toward": "high",
                "provenance": "stated",
            }
        ],
    }
    # Each edit rests on words of a sentence the reader knows, and the park on none.
    known = [
        (s.start, s.end) for s in sentences_of(request.text, release=small_release()) if s.known
    ]
    assert len(known) == 2
    for said in alone.rests_on:
        assert any(start <= said.start and said.end <= end for start, end in known)
    assert (alone.suggestions, alone.unmet) == ((), (UnmetCategory.OTHER,))
    assert alone.unread


def test_by_sentence_a_plain_prompt_is_read_as_the_reader_reads_it():
    for text in ("leafy and quiet, near a park", "no pubs", "I work at Pellam and want a park"):
        request = InterpretRequest(text=text, spec=RENTER, release=small_release())
        assert RuleInterpreter().by_sentence(request) == RuleInterpreter().interpret(request)


def test_by_sentence_a_wish_that_a_sentence_beside_it_takes_back_makes_no_edit():
    for text in ("I want a station. Not really.", "No thanks.\nPubs\nBars"):
        request = InterpretRequest(text=text, spec=RENTER, release=small_release())
        assert RuleInterpreter().by_sentence(request).operations == NO_OPERATIONS
    people = InterpretRequest(
        text="Near a park. Far from a university.", spec=RENTER, release=small_release()
    )
    found = RuleInterpreter().by_sentence(people)
    assert (found.status, found.notice) == (InterpretStatus.POLICY_REDIRECT, Notice.NEUTRAL_PLACES)
    assert [e.feature_id for e in found.operations.weight_ops] == ["park_proximity"]


# --- The words for gritty, in the two ways it is built -------------------------------


def read_in(variant: GrittyVariant, text: str) -> InterpretResult:
    request = InterpretRequest(text=text, spec=RENTER, release=small_release(variant))
    return RuleInterpreter().interpret(request)


@pytest.mark.parametrize("word", ["gritty", "edgy", "raw"])
def test_built_from_land_use_a_word_with_two_meanings_is_read_as_its_place_part_and_quoted(
    word: str,
):
    result = read_in(GrittyVariant.A, f"somewhere a bit {word}, near a park")
    assert result.status is InterpretStatus.OK
    (edit,) = result.operations.tag_ops
    assert (edit.tag_id, edit.toward, edit.step, edit.provenance) == (
        "works_warehouses",
        "high",
        "up_small",
        "inferred",
    )
    # The chip quotes the word, as the lexicon spells it, and says it was assumed.
    assert [(a.code, a.group, a.index, a.word) for a in result.assumptions] == [
        (AssumptionCode.WEIGHT, OpsGroup.TAG, 0, ""),
        (AssumptionCode.WORD, OpsGroup.TAG, 0, word),
    ]
    # And the person is told that Burro has no measure of how clean a street is.
    assert result.unmet == (UnmetCategory.STREET_CLEANLINESS,)
    assert [e.feature_id for e in result.operations.weight_ops] == ["park_proximity"]
    after = apply(RENTER, result.operations, small_release(GrittyVariant.A))
    assert after.rejected == ()
    assert [(t.tag_id, t.weight) for t in after.spec.tags] == [("works_warehouses", 0.5)]


@pytest.mark.parametrize("text", ["polished", "somewhere smart", "well kept", "not gritty"])
def test_built_from_land_use_a_word_for_upkeep_makes_no_edit_and_says_so(text: str):
    result = read_in(GrittyVariant.A, text)
    assert (result.status, result.operations) == (InterpretStatus.OK, NO_OPERATIONS)
    assert (result.unmet, result.unread) == ((UnmetCategory.UPKEEP,), ())


@pytest.mark.parametrize("text", ["industrial", "warehouses", "railway arches"])
def test_built_from_land_use_the_works_are_named_outright(text: str):
    (edit,) = read_in(GrittyVariant.A, text).operations.tag_ops
    assert (edit.tag_id, edit.provenance) == ("works_warehouses", "stated")
    assert read_in(GrittyVariant.A, text).assumptions == ()


@pytest.mark.parametrize(("text", "toward"), [("gritty", "high"), ("polished", "low")])
def test_built_as_a_scale_the_names_of_its_ends_are_wishes_for_them(text: str, toward: str):
    result = read_in(GrittyVariant.B, text)
    (edit,) = result.operations.tag_ops
    assert (edit.tag_id, edit.toward, edit.provenance) == ("street_character", toward, "stated")
    assert (result.unmet, result.assumptions) == ((), ())


COUNTS_CRIME = (
    "Gritty counts recorded criminal damage and arson, and recorded anti-social behaviour. "
    "Recorded crime depends on what is reported, and locations are approximate."
)


@pytest.mark.parametrize(
    "text",
    [
        *("edgy", "raw", "well kept", "somewhere well kept", "I want somewhere a bit edgy"),
        # The name the scale had, and an end of it in a prompt that is not plain.
        *("street character", "gritty, I suppose", "is it polished"),
    ],
)
def test_built_as_a_scale_a_word_that_is_read_into_it_is_offered_and_says_it_counts_crime(
    text: str,
):
    # The scale holds recorded incidents, and crime counts only when it is
    # asked for by name. A word that is only read into the scale never asks.
    result = read_in(GrittyVariant.B, text)
    assert result.operations == NO_OPERATIONS
    assert (result.status, result.assumptions) == (InterpretStatus.SUGGEST, ())
    (found,) = result.suggestions
    assert (found.target, found.label, found.note) == (
        "tag:street_character",
        "Gritty",
        COUNTS_CRIME,
    )
    assert [(choice.direction, choice.label) for choice in found.choices] == [
        ("more", "Towards Gritty, counting recorded crime"),
        ("less", "Towards Polished, counting recorded crime"),
        ("ignore", "Leave it out"),
    ]
    # A choice that is pressed is the person's own, and is applied.
    for choice in found.choices[:2]:
        pressed = apply(RENTER, choice.operations, small_release(GrittyVariant.B))
        assert pressed.rejected == ()
        assert [tag.tag_id for tag in pressed.spec.tags] == ["street_character"]


def test_a_suggestion_says_more_only_where_there_is_more_to_say():
    for text in ("pubs are so noisy", "maybe leafy", "is it buzzy"):
        assert [found.note for found in read(text).suggestions if found.note] == []


def test_a_word_read_into_a_vibe_that_holds_no_crime_is_still_applied_as_assumed():
    for text, tag_id in (("lively", "pace"), ("peaceful", "quiet_residential")):
        (edit,) = read_in(GrittyVariant.B, text).operations.tag_ops
        assert (edit.tag_id, edit.provenance) == (tag_id, "inferred")
    # Where gritty is built from land use alone it holds no crime, and is read.
    (edit,) = read_in(GrittyVariant.A, "edgy").operations.tag_ops
    assert (edit.tag_id, edit.provenance) == ("works_warehouses", "inferred")


@pytest.mark.parametrize(
    "text", ["industrial", "warehouses", "railway arches", "works and warehouses"]
)
def test_a_word_for_works_and_warehouses_is_read_into_gritty_and_offered(text: str):
    """Works and warehouses is a part of Gritty, and is not served beside it.

    So a word for it is read into the scale, as "edgy" is. Nothing is applied: the
    scale is offered, and the offer says that it counts recorded crime.
    """
    result = read_in(GrittyVariant.B, text)
    assert result.operations == NO_OPERATIONS
    (found,) = result.suggestions
    assert (found.target, found.note) == ("tag:street_character", COUNTS_CRIME)
    # Where no recorded crime is held the land is the vibe, and the word is applied.
    (edit,) = read_in(GrittyVariant.A, text).operations.tag_ops
    assert (edit.tag_id, edit.toward, edit.provenance) == ("works_warehouses", "high", "stated")


def test_no_word_weighs_a_part_of_recorded_crime_but_by_name():
    # The rates of recorded incidents are nuisances, so each is read only under
    # a turn or where it is said to count, and is never read into looser words.
    for text in ("vandalism", "anti social behaviour", "I like vandalism"):
        assert read_in(GrittyVariant.B, text).operations == NO_OPERATIONS
    (edit,) = read_in(GrittyVariant.B, "less vandalism").operations.weight_ops
    assert (edit.feature_id, edit.provenance) == ("incident_criminal_damage", "stated")


# --- What a person asks for that the release holds for no area ---------------------


def on(release: InMemoryRelease, text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return RuleInterpreter().interpret(InterpretRequest(text=text, spec=spec, release=release))


def missing(
    release: InMemoryRelease, text: str, spec: PreferenceSpec = RENTER
) -> list[tuple[str, str, list[str]]]:
    """What a reading asked for and the release lacks: its target, its label and its words."""
    result = on(release, text, spec)
    turned_away = apply(spec, result.operations, release).rejected
    return [
        (thing.target, thing.label, [text[span.start : span.end] for span in thing.spans])
        for thing in not_in_release_of(result, turned_away)
    ]


# --- The words for Everyday on foot and for its parts ------------------------------

# A release that carries the distance to a GP practice and to a pharmacy, as a build of
# London may. The releases of the tests carry neither.
WITH_A_SURGERY = carrying(small_release(), FeatureId.GP_WALK, FeatureId.PHARMACY_WALK)
ON_FOOT = [
    ("walkable", "tag:everyday_on_foot", "stated"),
    ("walkability", "tag:everyday_on_foot", "stated"),
    ("everything on foot", "tag:everyday_on_foot", "inferred"),
    ("I want everything on foot", "tag:everyday_on_foot", "inferred"),
    # A town centre is where the shops are. A food shop is asked for by its name.
    ("shops nearby", "feature:highstreet_access", "inferred"),
    ("near a supermarket", "feature:grocery_walk", "stated"),
    ("a food shop nearby", "feature:grocery_walk", "stated"),
    ("near a GP", "feature:gp_walk", "stated"),
    ("near a doctor", "feature:gp_walk", "stated"),
    ("a doctor's surgery nearby", "feature:gp_walk", "stated"),
    ("close to a GP surgery", "feature:gp_walk", "stated"),
    ("a GP practice", "feature:gp_walk", "stated"),
    ("near a pharmacy", "feature:pharmacy_walk", "stated"),
    ("a pharmacy", "feature:pharmacy_walk", "stated"),
    ("a chemist nearby", "feature:pharmacy_walk", "stated"),
    # A word that is a person's too, with what says near before it or after it.
    ("a doctor nearby", "feature:gp_walk", "stated"),
    ("close to a good doctor", "feature:gp_walk", "stated"),
    ("within walking distance of a GP", "feature:gp_walk", "stated"),
    ("a GP within walking distance", "feature:gp_walk", "stated"),
    ("10 minutes from a doctor", "feature:gp_walk", "stated"),
    ("a doctor within a 10 minute walk", "feature:gp_walk", "stated"),
    ("I want to be near a surgery", "feature:gp_walk", "stated"),
    ("we need a chemist round the corner", "feature:pharmacy_walk", "stated"),
]


@pytest.mark.parametrize(("text", "target", "provenance"), ON_FOOT)
def test_the_words_for_everyday_on_foot_and_its_parts_are_heard_and_applied(
    text: str, target: str, provenance: str
):
    result = on(WITH_A_SURGERY, text)
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert (result.unmet, result.unread, result.suggestions) == ((), (), ())
    (edit,) = (*result.operations.weight_ops, *result.operations.tag_ops)
    named = getattr(edit, "feature_id", None) or getattr(edit, "tag_id", None)
    assert f"{target.split(':')[0]}:{named}" == target
    assert (edit.action, edit.step, edit.provenance) == ("nudge", "up_large", provenance)
    after = apply(RENTER, result.operations, WITH_A_SURGERY)
    assert after.rejected == () and [one.changed for one in after.applied] == [True]
    if target.startswith("tag:"):
        assert tag_weight_of(after.spec, TagId(named)) == 0.5
    else:
        assert weight_of(after.spec, FeatureId(named)) == 0.5


def test_each_distance_of_everyday_on_foot_is_wanted_nearer_and_never_further():
    for feature_id in (FeatureId.GROCERY_WALK, FeatureId.GP_WALK, FeatureId.PHARMACY_WALK):
        feature = FEATURES[feature_id]
        assert (feature.unit, feature.polarity) == ("m", Polarity.LESS)
    # A wish that is turned round takes the weight off, and raises nothing.
    for text in ("not near a GP", "no pharmacy", "I don't care about supermarkets"):
        result = on(WITH_A_SURGERY, text)
        assert [edit.action for edit in result.operations.weight_ops] == ["remove"], text


@pytest.mark.parametrize(
    ("text", "target", "label"),
    [
        ("near a GP", "feature:gp_walk", "Nearer a GP surgery"),
        ("near a doctor", "feature:gp_walk", "Nearer a GP surgery"),
        ("near a pharmacy", "feature:pharmacy_walk", "Nearer a pharmacy"),
        ("a chemist nearby", "feature:pharmacy_walk", "Nearer a pharmacy"),
    ],
)
def test_a_surgery_the_release_holds_no_figure_for_is_named_as_not_in_it(
    text: str, target: str, label: str
):
    """It is no longer what Burro has no measure of: the release is what lacks it."""
    release = small_release()
    assert FeatureId(target.removeprefix("feature:")) not in {
        metric.feature_id for metric in release.metrics
    }
    result = on(release, text)
    assert (result.status, result.unmet, result.unread) == (InterpretStatus.OK, (), ())
    after = apply(RENTER, result.operations, release)
    assert [(one.group, one.reason) for one in after.rejected] == [("weight_ops", "not_in_release")]
    assert missing(release, text) == [(target, label, [text])]


def test_a_gp_and_a_chemist_are_two_parts_of_everyday_on_foot():
    result = on(WITH_A_SURGERY, "a GP and a chemist nearby")
    assert [edit.feature_id for edit in result.operations.weight_ops] == [
        "gp_walk",
        "pharmacy_walk",
    ]
    parts = {term.feature_id for term in TAGS[TagId.EVERYDAY_ON_FOOT].terms}
    assert {FeatureId.GP_WALK, FeatureId.PHARMACY_WALK, FeatureId.GROCERY_WALK} <= parts


def test_a_dentist_is_still_what_burro_has_no_measure_of():
    for release in (small_release(), WITH_A_SURGERY):
        result = on(release, "a dentist nearby")
        assert (result.operations, result.unmet) == (
            NO_OPERATIONS,
            (UnmetCategory.HEALTH_SERVICES,),
        )


# A doctor is a person too, and so are a GP and a chemist, and surgery is an operation.
# None is a place to be near but where the words beside it say so.
A_SURGERY_OR_A_PHARMACY = {"feature:gp_walk", "feature:pharmacy_walk"}
SAID_OF_NO_PLACE = [
    ("I am a doctor", "doctor"),
    ("I'm a doctor", "doctor"),
    ("we are two doctors", "doctors"),
    ("I want to be a doctor", "doctor"),
    ("my GP said so", "GP"),
    ("I'm a GP", "GP"),
    ("I'm a chemist", "chemist"),
    ("I am having surgery next month", "surgery"),
    # "By" is near in "by a park", and says who did a thing here.
    ("I was told by a doctor to move", "doctor"),
    # What is said of the next thing is not said of the speaker.
    ("I'm a doctor, close to a station", "doctor"),
    ("I'm a chemist, station nearby", "chemist"),
    ("I'm a GP and I want a park nearby", "GP"),
    # The word alone says nothing of where, and nor does a good word for one. Nor does
    # a list that says near of nothing. The founder decided on 2026-09-25 that a bare
    # "doctor" in a list stays unheard.
    ("doctor", "doctor"),
    ("a good GP", "GP"),
    ("parks and a doctor", "doctor"),
]


def asked_for(release: InMemoryRelease, text: str) -> set[str]:
    """Everything a text set, was offered, or was told the release does not hold."""
    result = on(release, text)
    edits = result.operations.weight_ops
    after = apply(RENTER, result.operations, release)
    return {
        *(f"feature:{edit.feature_id}" for edit in edits),
        *(found.target for found in result.suggestions),
        *(thing.target for thing in not_in_release_of(result, after.rejected)),
    }


@pytest.mark.parametrize(("text", "word"), SAID_OF_NO_PLACE)
def test_a_word_that_is_a_persons_too_asks_for_no_place_where_nothing_says_near(
    text: str, word: str
):
    """ "I am a doctor" was offered a surgery, and "I'm a chemist" set how near a pharmacy is."""
    for release in (small_release(), WITH_A_SURGERY):
        assert not asked_for(release, text) & A_SURGERY_OR_A_PHARMACY, text
        # Nothing was made of the word, and the answer says where it stands.
        unread = [text[span.start : span.end] for span in on(release, text).unread]
        assert any(word in left for left in unread), (text, unread)


@pytest.mark.parametrize(
    ("text", "target"),
    [
        ("my partner wants to be near a doctor", "feature:gp_walk"),
        ("my mother has to be close to a good doctor", "feature:gp_walk"),
        ("she needs to get to a doctor", "feature:gp_walk"),
        ("he has to be 10 minutes from a GP", "feature:gp_walk"),
        ("they would like a surgery within walking distance", "feature:gp_walk"),
        ("is there a chemist nearby?", "feature:pharmacy_walk"),
        ("does it have a chemist within a ten minute walk?", "feature:pharmacy_walk"),
    ],
)
def test_a_word_that_is_a_persons_too_is_offered_where_the_words_beside_it_say_near(
    text: str, target: str
):
    """In a prompt that is not plain it is offered, and nothing is applied."""
    result = on(WITH_A_SURGERY, text)
    assert result.operations == NO_OPERATIONS
    assert [found.target for found in result.suggestions] == [target]
    assert [choice.direction for choice in result.suggestions[0].choices] == ["more", "ignore"]


@pytest.mark.parametrize(
    ("text", "wished"),
    [
        # What is said after the last thing of a list is said of every thing of it.
        ("a GP and a chemist nearby", ["gp_walk", "pharmacy_walk"]),
        ("a park, a doctor and a pharmacy nearby", ["park_proximity", "gp_walk", "pharmacy_walk"]),
        # And so is what leads the first.
        ("near a park and a doctor", ["park_proximity", "gp_walk"]),
        ("close to a station, a GP and a chemist", ["station_walk", "gp_walk", "pharmacy_walk"]),
    ],
)
def test_what_says_near_of_a_list_says_it_of_a_doctor_in_the_list(text: str, wished: list[str]):
    result = on(WITH_A_SURGERY, text)
    assert (result.status, result.unread, result.suggestions) == (InterpretStatus.OK, (), ())
    assert [edit.feature_id for edit in result.operations.weight_ops] == wished
    assert {edit.action for edit in result.operations.weight_ops} == {"nudge"}


def test_a_doctor_that_is_turned_away_is_still_a_surgery_where_near_is_said():
    for text, turned in (("not near a GP", "gp_walk"), ("no chemist nearby", "pharmacy_walk")):
        result = on(WITH_A_SURGERY, text)
        assert [edit.feature_id for edit in result.operations.weight_ops] == [turned], text
        assert [edit.action for edit in result.operations.weight_ops] == ["remove"], text


def test_a_plain_wish_the_release_holds_for_no_area_is_named_and_the_rest_is_applied():
    # "Leafy and quiet" was ranked as quiet alone, under both words, and nothing
    # said that half the wish had been dropped.
    release = unplaced(small_release(), TagId.LEAFY)
    text = "leafy and quiet"
    result = on(release, text)
    assert result.status is InterpretStatus.OK
    after = apply(RENTER, result.operations, release)
    assert [(r.group, r.reason) for r in after.rejected] == [("tag_ops", "not_in_release")]
    assert [tag.tag_id for tag in after.spec.tags] == ["quiet_residential"]
    assert missing(release, text) == [("tag:leafy", "Leafy", ["leafy"])]
    # A release that places areas on it has nothing to say.
    assert missing(small_release(), text) == []


def test_a_budget_and_a_journey_are_named_where_a_preview_holds_no_cost_and_no_place():
    preview = preview_release()
    # "A month" says that it is a rent, which is kept. The amount is what is missing.
    assert missing(preview, "up to £1,500 a month") == [("budget", "A budget", ["up to £1,500"])]
    # No spelling can match, so nothing is asked: the journey is said to be missing.
    text = "I work at Pellam Cross"
    result = on(preview, text)
    assert (result.status, result.clarify) == (InterpretStatus.OK, ())
    assert missing(preview, text) == [("commute", "A journey", ["work at Pellam Cross"])]
    # Where the release names places, a name it does not know is still asked about.
    asked = on(small_release(), "I work at Nowhere Works")
    assert asked.status is InterpretStatus.CLARIFY and len(asked.clarify) == 1
    assert missing(small_release(), "I work at Nowhere Works") == []


def test_what_is_said_of_the_home_is_kept_where_the_amount_cannot_be_tested():
    # "Buying a terraced house under £450k" left the search a renter's, because the
    # one edit that held the amount held the tenure too, and was turned away whole.
    preview = preview_release()
    text = "Buying a terraced house under £450k"
    result = on(preview, text)
    assert edits(result) == {
        "budget_ops": [
            {"action": "set", "tenure": "buy", "segment": "terraced", "provenance": "stated"},
            {"action": "set", "amount": 450000, "provenance": "stated"},
        ]
    }
    after = apply(RENTER, result.operations, preview)
    assert [(a.group, a.index) for a in after.applied] == [("budget_ops", 0)]
    assert [(r.index, r.reason) for r in after.rejected] == [(1, "not_in_release")]
    assert (after.spec.tenure, after.spec.tenure_from) == ("buy", "stated")
    assert (after.spec.budget.segment, after.spec.budget.amount) == ("terraced", None)
    # Each edit rests on its own words, and what is missing is the amount alone.
    assert missing(preview, text) == [("budget", "A budget", ["under £450k"])]
    # What the first edit said is not said to be assumed of the second.
    assert [(a.code, a.index) for a in result.assumptions] == [(AssumptionCode.STRICTNESS, 1)]
    rests = {(r.index, text[r.start : r.end]) for r in result.rests_on}
    assert rests == {(0, "Buying"), (0, "terraced"), (1, "under £450k")}
    # A limit that was said firmly goes with the amount it was said of.
    firm = on(preview, "renting, no more than £1,800 pcm").operations.budget_ops
    assert [(e.tenure, e.amount, e.strictness) for e in firm] == [
        ("rent", 0, "unchanged"),
        ("unchanged", 1800, "hard"),
    ]
    # Where the release holds the cost, it is one edit, as it always was.
    (whole,) = on(small_release(), text).operations.budget_ops
    assert (whole.tenure, whole.amount, whole.segment) == ("buy", 450_000, "terraced")
    # An amount alone has nothing to keep, and is one edit.
    (alone,) = on(preview, "up to £1,500").operations.budget_ops
    assert (alone.tenure, alone.amount) == ("unchanged", 1500)


def test_what_was_noticed_and_is_in_no_area_is_said_to_be_missing_and_never_offered():
    # The sentence is not plain, so nothing is applied. What can be chosen is
    # offered. What the release holds for no area is said, and not offered:
    # pressed, it left no area ranked.
    release = unplaced(preview_release(), TagId.LEAFY)
    text = "My partner wants somewhere leafy and quiet, for £1,500 a month, with a short commute."
    result = on(release, text)
    assert result.operations == NO_OPERATIONS
    assert [found.target for found in result.suggestions] == ["tag:quiet_residential"]
    assert [
        (thing.target, thing.label, [text[s.start : s.end] for s in thing.spans])
        for thing in result.not_in_release
    ] == [
        ("tag:leafy", "Leafy", ["leafy"]),
        ("budget", "A budget of £1,500 a month", ["£1,500 a month"]),
        ("commute", "A journey", ["commute"]),
    ]
    assert missing(release, text) == [
        ("tag:leafy", "Leafy", ["leafy"]),
        ("budget", "A budget of £1,500 a month", ["£1,500 a month"]),
        ("commute", "A journey", ["commute"]),
    ]
    # What was said to be missing was heard, and is not among what was not read.
    unread = [text[span.start : span.end] for span in result.unread]
    assert not any(word in words for words in unread for word in ("leafy", "£1,500", "commute"))
    # A release that holds all three offers all three, and says nothing is missing.
    whole = on(small_release(), text)
    assert whole.not_in_release == ()
    assert [found.target for found in whole.suggestions] == [
        "tag:leafy",
        "tag:quiet_residential",
        "budget",
    ]


def test_a_measure_the_release_does_not_carry_is_named_by_its_short_label():
    whole = small_release()
    release = dataclasses.replace(
        whole,
        metrics=tuple(
            m for m in whole.metrics if m.feature_id is not FeatureId.CULTURE_VENUES_PER_HOMES
        ),
    )
    label = FEATURES[FeatureId.CULTURE_VENUES_PER_HOMES].short_label
    named = "feature:culture_venues_per_homes"
    assert missing(release, "theatres") == [(named, label, ["theatres"])]
    unsure = "maybe theatres, I suppose"
    assert on(release, unsure).suggestions == ()
    assert missing(release, unsure) == [(named, label, ["theatres"])]


def test_a_journey_is_listened_for_by_its_words_only_where_the_release_names_no_place():
    text = "My partner has a long commute, sadly."
    assert [thing.target for thing in on(preview_release(), text).not_in_release] == ["commute"]
    # Where the release names places, a journey is noticed by the name of its place.
    assert on(small_release(), text).not_in_release == ()
    # A journey that is turned away asks for none.
    assert on(preview_release(), "My partner does not commute, luckily.").not_in_release == ()


def test_a_journey_the_grammar_makes_is_said_to_be_missing_once_and_by_all_its_words():
    # Its words were named twice where the release names no place: once as the grammar
    # read them, and once more for the phrase that says a journey, which stands inside them.
    text = "Maybe somewhere quiet. At most 25-30min commute from Quillhaven Lane."
    assert missing(preview_release(), text) == [
        ("commute", "A journey", ["At most 25-30min commute from Quillhaven Lane"])
    ]
    unread = [text[s.start : s.end] for s in on(preview_release(), text).unread]
    assert not any("commute" in words for words in unread)


def test_a_thing_turned_away_for_any_other_reason_is_not_said_to_be_missing():
    # A flat is a kind of home to buy, and the search is a renter's.
    assert missing(small_release(), "maybe a flat") == []
    assert missing(preview_release(), "maybe a flat") == []


@pytest.mark.parametrize("word", ["wealthy", "well off", "well to do"])
def test_a_word_for_how_well_off_people_are_is_heard_in_a_sentence_that_is_not_plain(word: str):
    # In a long sentence the word sat inside what was not read, and drew no notice.
    text = f"Maybe somewhere quiet, a {word} part of town, but with some life to it."
    result = read(text)
    assert (result.status, result.notice) == (
        InterpretStatus.POLICY_REDIRECT,
        Notice.NEUTRAL_PLACES,
    )
    assert result.operations == NO_OPERATIONS
    assert "tag:quiet_residential" in [found.target for found in result.suggestions]
    assert not any(found.target.startswith("tag:street") for found in result.suggestions)
    unread = [text[span.start : span.end] for span in result.unread]
    assert not any(word in words for words in unread)


@pytest.mark.parametrize("word", ["affluent", "posh"])
def test_a_smart_area_is_offered_as_of_the_place_in_a_sentence_that_is_not_plain(word: str):
    # A smart area is a kind of place. The word is offered towards the polished end of
    # the scale, with the note that Burro measures places, and draws no notice about people.
    text = f"Maybe somewhere quiet, fairly {word}, but with some life to it."
    result = read(text)
    assert (result.status, result.notice) == (InterpretStatus.SUGGEST, Notice.NONE)
    assert result.operations == NO_OPERATIONS
    offered = {found.target: found for found in result.suggestions}
    assert {"tag:quiet_residential", "tag:street_character"} <= set(offered)
    smart = offered["tag:street_character"]
    assert [text[span.start : span.end] for span in smart.spans] == [word]
    # The grammar does not make this sentence, so nobody can say which way the word is
    # meant: both ends are offered, and each says that it counts recorded crime.
    assert [choice.label for choice in smart.choices] == [
        "Towards Gritty, counting recorded crime",
        "Towards Polished, counting recorded crime",
        "Leave it out",
    ]
    assert smart.note.startswith(
        "Burro reads this of the place, and not of the people who live there."
    )
    unread = [text[span.start : span.end] for span in result.unread]
    assert not any(word in words for words in unread)
