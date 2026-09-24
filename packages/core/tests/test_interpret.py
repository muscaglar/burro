import dataclasses
from typing import Any

import pytest
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import (
    AssumptionCode,
    EditProvenance,
    FeatureId,
    InterpreterName,
    InterpretStatus,
    Notice,
    OpsGroup,
    PlaceKind,
    Polarity,
    RejectReason,
    TagId,
    Tenure,
    UnmetCategory,
)
from burro_core.interpret import (
    LEXICON,
    NOTICES,
    NUISANCES,
    POLICY_LEXICON,
    Interpreter,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    assumptions_for,
    prepare,
)
from burro_core.ops import NO_OPERATIONS, Operations
from burro_core.reducer import ReducerResult, apply
from burro_core.release import InMemoryRelease
from burro_core.spec import PreferenceSpec, canonical, default_spec

from .support import area_id, place, place_id, small_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
# A string found nowhere else, to prove that what was typed is in nothing that comes back.
CANARY = "zqxjkvanary"


# One reader for every test: it keeps the names of the release and nothing else.
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
                "provenance": "stated",
            },
            {"action": "nudge", "tag_id": "leafy", "step": "up_large", "provenance": "stated"},
        ],
    }
    assert (result.unmet, result.clarify, result.notice) == ((), (), Notice.NONE)
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
                "provenance": "stated",
            }
        ],
        "commute_ops": [
            {"action": "add", "place_id": place_id(2), "provenance": "stated"},
            {"action": "add", "place_id": place_id(3), "provenance": "stated"},
        ],
    }
    # What the text did not say is stated as an assumption, pointing at its edit.
    assert [(a.code, a.group, a.index) for a in result.assumptions] == [
        (AssumptionCode.STRICTNESS, OpsGroup.BUDGET, 0),
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
    # Budget is soft unless the person says otherwise, and the slowest journey drives the score.
    assert after.spec.budget.strictness == "soft"
    assert after.spec.commute_combine == "slowest"


def test_request_to_avoid_a_group_gets_the_neutral_notice_and_the_rest_is_served():
    result = read("Somewhere quiet, not too many students, 30 minutes to Pellam Cross")
    assert result.status is InterpretStatus.POLICY_REDIRECT
    assert result.notice is Notice.NEUTRAL_PLACES
    assert NOTICES[result.notice] == (
        "Burro ranks places by what is there, such as schools, parks, venues and transport, "
        "and never by who lives there. The rest of your search has been applied."
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
    "lots of young families",
    "an area full of young professionals",
    "where people like me live",
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


def test_a_request_to_find_a_group_is_not_turned_into_the_tag_that_sounds_like_it():
    families = read("lots of young families, good primary schools and playgrounds")
    assert families.status is InterpretStatus.POLICY_REDIRECT
    assert edits(families) == {
        "weight_ops": [
            {
                "action": "nudge",
                "feature_id": "school_primary_attainment",
                "step": "up_large",
                "provenance": "stated",
            },
            {
                "action": "nudge",
                "feature_id": "play_space_proximity",
                "step": "up_large",
                "provenance": "stated",
            },
        ]
    }
    students = read("lots of students")
    assert students.operations.tag_ops == ()


def test_a_word_that_also_names_a_cuisine_is_not_a_word_for_people_on_its_own():
    result = read("Turkish cafes and Indian restaurants")
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert [e.feature_id for e in result.operations.weight_ops] == ["venue_food_drink"]
    pubs = read("Irish pubs")
    assert (pubs.status, pubs.unmet) == (InterpretStatus.OK, ())
    assert [e.feature_id for e in pubs.operations.weight_ops] == ["venue_evening"]


@pytest.mark.parametrize("text", ["white stucco houses", "black railings", "an English garden"])
def test_a_word_that_is_also_a_colour_or_a_country_asks_nothing_about_people(text: str):
    result = read(text)
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)


def test_the_rest_of_a_request_is_served_when_part_of_it_is_to_be_far_from_a_campus():
    # The rest is every other sentence. In one sentence with it, nothing is read:
    # a comma does not end a sentence, and "far" is no word of the reader's.
    together = read("Somewhere quiet, far from a university, 30 minutes to Pellam Cross")
    assert together.operations == NO_OPERATIONS
    assert together.notice is Notice.NEUTRAL_PLACES

    result = read("Somewhere quiet. Far from a university. 30 minutes to Pellam Cross.")
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
    (edit,) = result.operations.tag_ops
    assert (edit.tag_id, edit.action, edit.step) == ("near_universities", "nudge", "up_large")


def test_not_caring_about_a_campus_is_an_ordinary_edit():
    near = apply(RENTER, read("near a university").operations, small_release()).spec
    result = read("I don't care about universities", near)
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert [(e.tag_id, e.action) for e in result.operations.tag_ops] == [
        ("near_universities", "remove")
    ]
    assert apply(near, result.operations, small_release()).spec.tags == ()


def test_amenities_asked_for_by_name_are_ordinary_edits():
    result = read("good primary schools and playgrounds")
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert [e.feature_id for e in result.operations.weight_ops] == [
        FeatureId.SCHOOL_PRIMARY_ATTAINMENT,
        FeatureId.PLAY_SPACE_PROXIMITY,
    ]
    assert read("family friendly").operations.tag_ops[0].tag_id == "family_amenities"


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


def test_every_feature_and_tag_is_recognised_by_its_label():
    for feature_id, feature in FEATURES.items():
        result = read(f"I care about {feature.label}")
        found = {e.feature_id for e in result.operations.weight_ops}
        assert feature_id in found, feature.label
    for tag_id, tag in TAGS.items():
        result = read(f"somewhere with {tag.label.lower()} please")
        assert [e.tag_id for e in result.operations.tag_ops] == [tag_id], tag.label


def test_the_lexicon_names_only_what_is_in_the_catalogue():
    for phrase, target in LEXICON.items():
        assert phrase == prepare(phrase), phrase
        assert target.features or target.tags
        assert set(target.features) <= set(FEATURES)
        assert set(target.tags) <= set(TAGS)
    # Every feature and every tag can be reached by some phrase.
    assert {f for t in LEXICON.values() for f in t.features} == set(FEATURES)
    assert {g for t in LEXICON.values() for g in t.tags} == set(TAGS)


@pytest.mark.parametrize(
    ("text", "tenure", "amount", "segment"),
    [
        ("£1,500 pcm", "rent", 1500, "unchanged"),
        ("1500 a month", "rent", 1500, "unchanged"),
        ("budget 1.5k", "unchanged", 1500, "unchanged"),
        ("up to 1800", "unchanged", 1800, "unchanged"),
        ("max £2,000", "unchanged", 2000, "unchanged"),
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


def test_a_budget_is_soft_unless_the_words_make_it_a_limit():
    assert read("max £1,800 pcm").operations.budget_ops[0].strictness == "unchanged"
    assert read("no more than £1,800 pcm").operations.budget_ops[0].strictness == "hard"
    assert read("I cannot go over £1,800 a month").operations.budget_ops[0].strictness == "hard"


def test_a_number_of_minutes_or_bedrooms_is_not_mistaken_for_money():
    result = read("2 bed within 30 minutes of Pellam Cross")
    assert result.operations.budget_ops[0].amount == 0
    assert result.operations.commute_ops[0].max_minutes == 30
    assert read("up to 40 minutes to Foxholt Works").operations.budget_ops == ()


@pytest.mark.parametrize(
    ("text", "place", "mode", "minutes", "strictness"),
    [
        ("30 minutes to Pellam Cross", 1, "unchanged", 30, "unchanged"),
        ("within 25 mins of Foxholt Works", 2, "unchanged", 25, "unchanged"),
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
    ("there aren\N{RIGHT SINGLE QUOTATION MARK}t any pubs", FeatureId.VENUE_EVENING),
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
    ("no theatres", FeatureId.CULTURE_VENUES),
    ("not many independent shops", FeatureId.VENUE_INDEPENDENT),
    ("fewer primary schools", FeatureId.SCHOOL_PRIMARY_NEARBY),
    ("no pubs or parks", FeatureId.PARK_PROXIMITY),
]


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
    # The wish itself, to be away from the thing, is one no edit can express, and it is said.
    assert UnmetCategory.OTHER in result.unmet
    assert result.status is InterpretStatus.OK


@pytest.mark.parametrize(
    ("text", "tag_id"),
    [
        ("not leafy", TagId.LEAFY),
        ("not too buzzy", TagId.BUZZY),
        ("no nightlife", TagId.EVENING_VENUES),
        ("not by the water", TagId.WATERSIDE),
        ("I don't want a village", TagId.VILLAGE_FEEL),
    ],
)
def test_a_negated_wish_never_raises_a_tag(text: str, tag_id: TagId):
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
                        "provenance": "stated",
                    }
                ]
            }
        ),
        small_release(),
    ).spec
    for spec in (RENTER, wanted):
        result = read(text, spec)
        assert [e.tag_id for e in result.operations.tag_ops] == [tag_id]
        assert tag_weight_of(reduced(result, spec).spec, tag_id) <= tag_weight_of(spec, tag_id)
        assert UnmetCategory.OTHER in result.unmet


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


def test_only_what_it_is_a_nuisance_to_have_is_marked_as_one():
    assert {
        FeatureId.CRIME_VIOLENCE_ROBBERY,
        FeatureId.CRIME_BURGLARY_THEFT,
        FeatureId.AIR_NO2,
        FeatureId.NOISE_EXPOSURE,
    } == NUISANCES
    # Each is a feature that lower is better for, and that can be no other way.
    assert {FEATURES[f].polarity for f in NUISANCES} == {Polarity.LESS}
    for phrase, target in LEXICON.items():
        if target.nuisance:
            assert set(target.features) <= NUISANCES, phrase
            assert not target.tags, phrase
    assert not LEXICON["clean air"].nuisance
    assert not LEXICON["safe"].nuisance


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
    assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)
    assert result.unmet == (UnmetCategory.OTHER,)
    assert result.clarify == ()
    assert reduced(result, spec).spec == spec


NOT_TO_A_PLACE = [
    "not near Pellam Cross",
    "nowhere near Pellam Cross",
    "I don't want to be near Foxholt Works",
    "I don't work at Foxholt Works",
    "I wouldn't want to be 30 minutes to Pellam Infirmary",
    "anywhere but near Foxholt Works",
    "far from Pellam Cross",
    "a long way from Pellam Cross Station",
    "I work at Foxholt Works, not really",
    "near Foxholt Works? No.",
    "30 minutes to Pellam Cross is too far",
]


@pytest.mark.parametrize("text", NOT_TO_A_PLACE)
def test_a_place_named_in_a_doubtful_clause_adds_no_journey(text: str):
    # "Nowhere near Pellam Cross" added a journey to it, and put its area first.
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert (result.status, result.clarify) == (InterpretStatus.OK, ())
    assert result.unmet == (UnmetCategory.OTHER,)
    assert reduced(result).spec.commutes == ()


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


def test_the_rest_of_a_request_is_read_when_one_sentence_is_in_doubt():
    # A comma does not end a sentence, so with the doubt in it nothing of it is read.
    one = read("Quiet, 30 minutes to Pellam Cross, £1,500 pcm, and I can't live without a park")
    assert (one.operations, one.unmet) == (NO_OPERATIONS, (UnmetCategory.OTHER,))

    result = read("Quiet, 30 minutes to Pellam Cross, £1,500 pcm. I can't live without a park.")
    assert edits(result) == {
        "budget_ops": [{"action": "set", "tenure": "rent", "amount": 1500, "provenance": "stated"}],
        "commute_ops": [
            {"action": "add", "place_id": place_id(1), "max_minutes": 30, "provenance": "stated"}
        ],
        "tag_ops": [
            {
                "action": "nudge",
                "tag_id": "quiet_residential",
                "step": "up_large",
                "provenance": "stated",
            }
        ],
    }
    assert result.unmet == (UnmetCategory.OTHER,)


def test_wanting_fewer_of_something_is_a_direction_where_the_feature_allows_one():
    fewer = read("fewer pubs").operations.weight_ops[0]
    assert (fewer.feature_id, fewer.direction, fewer.step) == ("venue_evening", "less", "up_large")
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
        assert (edit.feature_id, edit.direction, edit.action) == ("venue_evening", "less", "nudge")
        assert read(text).unmet == ()


def test_crime_is_weighted_only_when_it_is_asked_for_in_so_many_words():
    asked = read("low crime")
    assert {e.provenance for e in asked.operations.weight_ops} == {EditProvenance.STATED}
    assert reduced(asked).rejected == ()
    assert {w.feature_id for w in reduced(asked).spec.weights} >= {
        FeatureId.CRIME_BURGLARY_THEFT,
        FeatureId.CRIME_VIOLENCE_ROBBERY,
    }

    # "Safe" is read into crime, not said. The reducer turns it away.
    implied = read("somewhere safe")
    assert {e.provenance for e in implied.operations.weight_ops} == {EditProvenance.INFERRED}
    assert {a.code for a in implied.assumptions} == {AssumptionCode.WEIGHT}
    after = reduced(implied)
    assert {r.reason for r in after.rejected} == {RejectReason.CRIME_NEEDS_EXPLICIT_REQUEST}
    assert after.spec == RENTER

    both = read("somewhere safe, with low crime")
    assert {e.provenance for e in both.operations.weight_ops} == {EditProvenance.STATED}


@pytest.mark.parametrize(
    ("text", "unmet"),
    [
        ("fast broadband", [UnmetCategory.BROADBAND]),
        ("not at risk of flooding", [UnmetCategory.FLOOD_RISK]),
        ("a good GP nearby", [UnmetCategory.HEALTH_SERVICES]),
        ("easy parking, I drive to work", [UnmetCategory.DRIVING]),
        ("show me listings", [UnmetCategory.LISTINGS]),
        ("what is on the market", [UnmetCategory.LISTINGS]),
        ("can I afford it?", [UnmetCategory.AFFORDABILITY_VERDICT]),
        ("is it good value", [UnmetCategory.AFFORDABILITY_VERDICT]),
        ("somewhere in the commuter belt", [UnmetCategory.OUTSIDE_THE_CITY]),
        ("what is the capital of France", [UnmetCategory.OTHER]),
        ("asdf ghjk", [UnmetCategory.OTHER]),
        # "Fast" is no word of the reader's, so the park is not read, and that is said.
        ("fast broadband near a park", [UnmetCategory.BROADBAND, UnmetCategory.OTHER]),
        ("broadband, and a park nearby", [UnmetCategory.BROADBAND]),
    ],
)
def test_what_burro_cannot_answer_is_reported_by_category(text: str, unmet: list[UnmetCategory]):
    result = read(text)
    assert list(result.unmet) == unmet
    assert result.status is InterpretStatus.OK


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
        assert result.status in (InterpretStatus.OK, InterpretStatus.CLARIFY)
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
    stated = apply(chosen, read("to rent").operations, small_release()).spec
    assert stated.tenure_from == "default"  # naming the tenure already chosen changes nothing
    assert assumptions_for(NO_OPERATIONS, RENTER) == ()


def test_an_edit_that_names_everything_leaves_nothing_assumed():
    said = read("no more than 30 minutes to Pellam Cross by bike")
    assert said.assumptions == ()
    ops = Operations.model_validate(said.operations.model_dump())
    assert assumptions_for(ops, RENTER) == ()
