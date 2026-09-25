"""What code checks of a model's answer before any of it is offered (contract, section 8.2).

Each check is tried on an answer that a model gave to a made-up sentence,
which is on disk word for word, and on answers written here to go wrong in
one way. No call is made: a stand-in hands the answer to the reader.

The checks are numbered as the contract numbers them. What is never offered
from a model, whatever it says, is held at the end, a test for each row.
"""

import json
from typing import Any

import pytest
from burro_api.guard import Check, thing_named
from burro_api.offers import FIRM, GUIDE, LESS, MORE, OFF
from burro_api.reader import ModelInterpreter
from burro_core.catalogue import FEATURES, HOLDS_CRIME
from burro_core.ids import (
    Dimension,
    FeatureId,
    InterpreterName,
    InterpretStatus,
    ModeChoice,
    Notice,
    Polarity,
    SegmentChoice,
    Step,
    StrictnessChoice,
    TagId,
    TenureChoice,
    UnmetCategory,
    WeightAction,
)
from burro_core.interpret import (
    SIGNS_OF_DOUBT,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
)
from burro_core.lexicon import lexicon_of
from burro_core.vocabulary import PHRASES_OF_DOUBT, TURNS_FIRMLY, WORDS_THAT_TURN_AWAY

from .support import (
    MODEL,
    UNREAD_FIRST,
    FakeModelClient,
    answers_on_disk,
    asked,
    client_for,
    guessed,
    make_deps,
    model_area,
    model_budget,
    model_commute,
    model_output,
    model_setting,
    model_tag,
    model_weight,
    offers,
    on_disk,
    quoted,
    read_again,
    release,
    renter,
    served_again,
    through_the_route,
)

LEXICON = lexicon_of(release().manifest.gritty_variant)


def fired(answer: Any, text: str) -> set[Check]:
    """The checks that fire on one answer to one sentence."""
    reader = ModelInterpreter(FakeModelClient(answer), MODEL, 512, 2.5)
    reader.interpret(InterpretRequest(text=text, spec=renter(), release=release()))
    return set(reader.fired)


def edits_of(result: InterpretResult) -> list[Any]:
    """Every edit that any way of any offer would send."""
    return [
        edit
        for offer in offers(result).values()
        for way in offer.choices
        for group in way.operations.model_dump(mode="json").values()
        for edit in group
    ]


# --- 1. The words are the person's -------------------------------------------------------


def test_words_a_model_copied_with_another_mark_are_found_and_the_budget_is_offered():
    # The model copied "£" as "#". The words are the person's all the same.
    result, text = read_again("own-019")

    assert quoted(result, text)["budget+"] == [
        "it's \N{POUND SIGN}1,600 a month for a two bed",
        "\N{POUND SIGN}1,600 a month",
        "a two bed",
    ]
    assert guessed(result) == {"budget+": GUIDE}


def test_words_either_side_of_the_end_of_a_sentence_are_the_persons():
    # "Nightlife, restaurants and theatres? No thanks." is two sentences, and
    # the wish is made of both.
    result, text = read_again("list-014")

    assert "Nightlife, restaurants and theatres? No thanks" in [
        words for found in quoted(result, text).values() for words in found
    ]
    # Against nightlife is towards Calm, and against restaurants is fewer of them.
    assert guessed(result) == {"tag:pace": LESS, "feature:venue_food_drink_per_homes": LESS}


@pytest.mark.parametrize(
    "words",
    [
        "a proper brunch place",  # a word the person did not type
        "brunch proper spot",  # their words in another order
        "proper brunch spots",  # part of a word is not the word
        "",
        "   ",
    ],
)
def test_words_the_person_did_not_type_make_no_offer(words: str):
    text = "I'd kill for a proper brunch spot, honestly"
    answer = model_output(weight_ops=[model_weight("venue_food_drink", words=words or " ")])

    result, _ = asked(answer, text=text)

    assert result.suggestions == ()
    assert Check.WORDS in fired(answer, text)


def test_what_is_shown_is_cut_from_the_text_and_is_never_the_models_copy():
    found, text = served_again("own-019")

    served = json.dumps(found, ensure_ascii=False)
    # The model wrote "#1,600". No word of its copy is in the answer, and no
    # word of the person's either: what is served is where the words stand.
    assert "#1,600" not in served and "two bed" not in served
    [budget] = [offer for offer in found["suggestions"] if offer["read_by"] == "model"]
    shown = text[budget["shown"]["start"] : budget["shown"]["end"]]
    assert shown == "it's \N{POUND SIGN}1,600 a month for a two bed"
    for span in budget["spans"]:
        assert budget["shown"]["start"] <= span["start"] < span["end"] <= budget["shown"]["end"]


# --- 2. A name is the whole of a name the release holds, as typed ------------------------


@pytest.mark.parametrize(
    ("case", "named", "minutes"),
    [("own-004", "Mirrowick Basin", 40), ("own-005", "Zorvane Halt", 45)],
)
def test_a_place_the_release_does_not_hold_is_asked_about_with_its_minutes(
    case: str, named: str, minutes: int
):
    # The rules ask about a place themselves where it is all that was typed.
    result, text = read_again(case, before=UNREAD_FIRST)

    [asks] = [offer for offer in offers(result).values() if offer.asks_place]
    assert asks.named_at is not None
    assert text[asks.named_at.start : asks.named_at.end] == named
    journeys = [edit for way in asks.choices for edit in way.operations.commute_ops]
    # The ways hold the minutes and no place: the place is the person's to choose.
    assert {(edit.place_id, edit.max_minutes) for edit in journeys} == {("", minutes)}
    assert {way.id for way in asks.choices} == {FIRM, GUIDE, "ignore"}


def test_words_that_are_the_whole_of_no_name_are_asked_about_with_what_the_release_holds():
    text = "My desk is in Pellam these days"
    answer = model_output(commute_ops=[model_commute(destination_text="Pellam", words=text)])

    result, _ = asked(answer, text=text)

    [asks] = [offer for offer in offers(result).values() if offer.asks_place]
    assert [option.name for option in asks.options] == [
        "Pellam Cross",
        "Pellam Exchange",
        "Pellam Infirmary",
    ]


@pytest.mark.parametrize(
    ("text", "named"),
    [
        ("I want a nice area, honestly", "Cindermoor Works"),  # a name the model brought
        ("I work in Pellamshire, honestly", "Pellam"),  # part of a word
        ("a works, maybe Cindermoor way", "Cindermoor Works"),  # another order
        ("I study at Wexmoor University these days", "Wexmoor"),  # part of a longer name
        ("somewhere, honestly", ""),
    ],
)
def test_a_name_the_person_did_not_type_is_no_journey(text: str, named: str):
    answer = model_output(commute_ops=[model_commute(destination_text=named, words=text)])

    result, _ = asked(answer, text=text)

    assert not [edit for edit in edits_of(result) if edit.get("place_id")] or (
        # What the rules noticed of a name that was typed in full is the rules' own.
        all(offer.read_by is InterpreterName.RULE for offer in offers(result).values())
    )
    assert not [offer for offer in offers(result).values() if offer.asks_place]


# --- 3. A least is never a most -------------------------------------------------------------


@pytest.mark.parametrize(
    ("case", "look"),
    [
        ("journey-028", 1),
        ("journey-028", 2),
        ("journey-028", 3),
        ("journey-030", 1),
        ("journey-030", 2),
        ("journey-030", 3),
        ("own-020", 1),
        ("own-020", 2),
    ],
)
def test_a_least_distance_is_never_offered_as_a_journey(case: str, look: int):
    result, _ = read_again(case, look)

    # The model read "Minimum 45 minutes from" as a cap of 45 minutes, every
    # time it was asked. Burro cannot keep a person away from a place.
    assert not [edit for edit in edits_of(result) if "max_minutes" in edit]
    assert guessed(result) == {}
    [notice] = [offer for offer in offers(result).values() if offer.target == "commute"]
    assert [way.id for way in notice.choices] == ["ignore"]


def test_a_least_distance_is_stopped_though_the_model_copies_the_number_alone():
    text = "Minimum 45 minutes from Pellam Infirmary, honestly"
    journey = model_commute(
        destination_text="Pellam Infirmary", max_minutes=45, words="45 minutes from"
    )

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    assert not [edit for edit in edits_of(result) if "max_minutes" in edit]


def test_a_cap_that_holds_a_word_of_doubt_loses_its_minutes_and_keeps_its_journey():
    # What the check costs: "can't be more than 45 minutes" is a cap. The
    # rules' own offer of the journey stands, with no number of the model's.
    result, _ = read_again("own-022")

    works = offers(result)["commute"]
    assert [way.id for way in works.choices] == [MORE, "ignore"]
    assert [edit.max_minutes for way in works.choices for edit in way.operations.commute_ops] == [0]
    assert guessed(result).get("commute") is None


# --- 4. Raised against a word that turns ---------------------------------------------------


@pytest.mark.parametrize("look", [1, 2, 3])
def test_a_wish_raised_against_a_word_that_turns_is_offered_with_no_guess(look: int):
    # "miles from the nearest station", read as a wish to be nearer one.
    result, _ = read_again("neg-061", look)

    station = offers(result)["feature:station_walk"]
    assert not any(way.guess for way in station.choices)
    # Every way is still open, as the rules alone give them.
    assert [way.id for way in station.choices] == [MORE, OFF, "ignore"]


@pytest.mark.parametrize("words", ["not near a station", "a station", "station"])
def test_a_turn_is_found_though_the_model_copies_the_thing_alone(words: str):
    text = "Honestly, not near a station"
    raised = model_weight("station_walk", direction="less", words=words)

    result, _ = asked(model_output(weight_ops=[raised]), text=text)

    assert guessed(result) == {}
    assert Check.TURNED in fired(model_output(weight_ops=[raised]), text)


def test_what_leads_in_to_a_thing_is_no_turn():
    text = "Honestly, not too far from a park"
    raised = model_weight("park_proximity", step="up_small", words="not too far from a park")

    result, _ = asked(model_output(weight_ops=[raised]), text=text)

    assert guessed(result) == {"feature:park_proximity": MORE}


def test_to_want_fewer_of_a_thing_is_the_wish_a_turn_makes():
    result, _ = read_again("neg-029")

    # "nightlife" with a face that says no: fewer pubs and bars is the guess.
    assert LESS in guessed(result).values()


@pytest.mark.parametrize("case", ["double-006", "long-007"])
def test_what_the_check_costs_is_a_guess_and_never_the_offer(case: str):
    # "a park wouldn't go amiss" and "a supermarket within walking distance"
    # are wishes, and each holds a word core lists. The thing is still offered.
    result, _ = read_again(case)

    lost = "feature:park_proximity" if case == "double-006" else "feature:grocery_walk"
    assert lost in offers(result) and lost not in guessed(result)


def test_a_nuisance_that_is_only_named_is_offered_with_no_guess():
    # "I like noise": to raise the weight is to ask for less of it.
    for case in ("sugg-014", "neg-040"):
        result, _ = read_again(case)
        assert guessed(result) == {}


def test_a_nuisance_under_a_turn_is_the_wish_itself():
    result, _ = read_again("long-004")

    assert guessed(result)["feature:road_major_exposure"] == LESS


def _beside(sign: str, thing: str) -> str:
    return f"honestly {sign} {thing} round here"


THINGS = sorted(
    phrase
    for phrase, target in LEXICON.items()
    if not target.nuisance and not target.note and (target.features or target.tags)
)
TURNS = sorted(WORDS_THAT_TURN_AWAY | TURNS_FIRMLY | PHRASES_OF_DOUBT)


def _raised(thing: str) -> Any:
    target = LEXICON[thing]
    return model_output(
        weight_ops=[model_weight(feature.value, words=thing) for feature in target.features],
        tag_ops=[
            model_tag(tag.value, toward=target.toward.value, words=thing) for tag in target.tags
        ],
    )


def _no_guess_for(turns: list[str], things: list[str]) -> list[str]:
    wrong: list[str] = []
    for sign in turns:
        for thing in things:
            result, _ = asked(_raised(thing), text=_beside(sign, thing))
            for way in (way for offer in offers(result).values() for way in offer.choices):
                raises = way.id == MORE or way.id.endswith(f"/{MORE}")
                if way.guess and raises:
                    wrong.append(f"{sign} {thing}")
    return wrong


def test_no_word_that_turns_lets_a_raise_be_marked_as_the_guess():
    # A fixed sample. `make test ARGS="-m full"` tries every one beside every thing.
    assert _no_guess_for(TURNS[::9], THINGS[::11]) == []


@pytest.mark.full
def test_every_word_that_turns_beside_every_thing_takes_the_guess_away():
    assert _no_guess_for(TURNS, THINGS) == []


def test_every_sign_of_doubt_keeps_a_thing_out_of_add_all():
    # A guess is held to the words that turn. "Add all" presses for the
    # person, so it is held to every sign of doubt core lists.
    left_in: list[str] = []
    for sign in sorted(SIGNS_OF_DOUBT)[::7]:
        text = _beside(sign, "parks")
        found = through_the_route(_raised("parks"), text)
        left_in += [sign for offer in found["suggestions"] if offer["add_all"]]
    assert left_in == []


# --- The words around a thing: what turns it round, and whose wish it is -------------------


def _raise_of(feature: str, words: str) -> Any:
    """An answer that raises one thing, and rests it on some words."""
    either = FEATURES[FeatureId(feature)].polarity is Polarity.EITHER
    direction = "more" if either else "default"
    return model_output(weight_ops=[model_weight(feature, direction=direction, words=words)])


AROUND = [
    # A word of dread or distaste stands after the thing, beyond a mark. The model
    # copies the thing alone, and the words that turn the wish are not in what it quotes.
    ("a station, god forbid", "station_walk", "a station"),
    ("honestly a lido round the corner, heaven forbid", "park_facilities", "a lido"),
    ("a nightclub next door, God no", "venue_evening", "a nightclub next door"),
    ("a park on the doorstep, perish the thought", "park_proximity", "a park"),
    ("a playground by the house, I'd hate that", "play_space_proximity", "a playground"),
    ("honestly a boozer on the corner, no more of those", "venue_evening", "a boozer"),
    ("a high street, anything but", "highstreet_access", "a high street"),
    # It stands after the thing with no mark between them.
    ("honestly a high street would be hell", "highstreet_access", "a high street"),
    ("a brunch spot on every corner is my idea of hell", "venue_food_drink", "a brunch spot"),
    ("theatres would be ghastly, honestly", "culture_venues", "theatres"),
    # It stands before the thing, beyond a mark, with no wish of the speaker's between.
    ("No, a park", "park_proximity", "a park"),
    ("What I don't want: a station", "station_walk", "a station"),
]


@pytest.mark.parametrize(("text", "feature", "words"), AROUND)
def test_a_raise_is_no_guess_where_the_words_around_the_thing_turn_it_round(
    text: str, feature: str, words: str
):
    for quoted_by_the_model in (words, text):
        result, _ = asked(_raise_of(feature, quoted_by_the_model), text=text)

        assert guessed(result) == {}, quoted_by_the_model
        # The thing is still offered, with every way open.
        assert [way.id for offer in offers(result).values() for way in offer.choices if way.meant]


ANOTHERS = [
    ("my dad is after a playground", "play_space_proximity", "a playground"),
    ("honestly my partner wants a pub nearby", "venue_evening", "a pub nearby"),
    ("my mum, bless her, would like a park", "park_proximity", "a park"),
    ("a brunch spot nearby is what my sister wants", "venue_food_drink", "a brunch spot"),
    ("honestly everyone wants a station", "station_walk", "a station"),
    ("she needs a playground close by", "play_space_proximity", "a playground close by"),
    ("the landlord likes a high street, honestly", "highstreet_access", "a high street"),
]


@pytest.mark.parametrize(("text", "feature", "words"), ANOTHERS)
def test_a_wish_is_no_guess_where_the_words_around_the_thing_give_it_to_somebody_else(
    text: str, feature: str, words: str
):
    for quoted_by_the_model in (words, text):
        result, _ = asked(_raise_of(feature, quoted_by_the_model), text=text)

        assert guessed(result) == {}, quoted_by_the_model
        assert [way.id for offer in offers(result).values() for way in offer.choices if way.meant]


def test_what_somebody_else_is_against_is_no_guess_of_what_the_person_is_against():
    # The model reads the words rightly, as a wish for fewer pubs. The wish is the friend's.
    text = "honestly my friend hates pubs"
    fewer = model_weight("venue_evening", direction="less", words="hates pubs")

    result, _ = asked(model_output(weight_ops=[fewer]), text=text)

    assert guessed(result) == {}
    assert list(offers(result)) == ["feature:venue_evening_per_homes"]


@pytest.mark.parametrize(
    ("text", "answer", "guesses"),
    [
        # Two wishes in one sentence, of which one is the speaker's own.
        (
            "My brother wants a pub nearby and I want a park",
            model_output(
                weight_ops=[
                    model_weight("venue_evening", direction="more", words="a pub nearby"),
                    model_weight("park_proximity", words="I want a park"),
                ]
            ),
            {"feature:park_proximity": MORE},
        ),
        # What is said of one thing is not said of the thing beside it.
        (
            "Honestly, a park, not pubs",
            model_output(
                weight_ops=[
                    model_weight("park_proximity", words="a park"),
                    model_weight("venue_evening", direction="less", words="not pubs"),
                ]
            ),
            {"feature:park_proximity": MORE, "feature:venue_evening_per_homes": LESS},
        ),
        (
            "Honestly, pubs are awful and parks are great",
            model_output(
                weight_ops=[
                    model_weight("park_proximity", words="parks are great"),
                    model_weight("venue_evening", direction="less", words="pubs are awful"),
                ]
            ),
            {"feature:park_proximity": MORE, "feature:venue_evening_per_homes": LESS},
        ),
        (
            "Honestly, I can't stand pubs, I want a park",
            model_output(weight_ops=[model_weight("park_proximity", words="a park")]),
            {"feature:park_proximity": MORE},
        ),
        # What says where a thing is wanted is no word of distance from it.
        (
            "Honestly, a park within walking distance",
            model_output(weight_ops=[model_weight("park_proximity", words="a park")]),
            {"feature:park_proximity": MORE},
        ),
        ("Honestly, I would love a park nearby", _raise_of("park_proximity", "a park"), None),
        ("Honestly, a park would be lovely", _raise_of("park_proximity", "a park"), None),
        ("Honestly, a park, please", _raise_of("park_proximity", "a park"), None),
    ],
)
def test_a_wish_that_nothing_around_it_turns_is_still_the_guess(
    text: str, answer: Any, guesses: dict[str, str] | None
):
    result, _ = asked(answer, text=text)

    assert guessed(result) == (guesses or {"feature:park_proximity": MORE})


@pytest.mark.parametrize(
    ("text", "feature", "words"),
    [
        ("a station, god forbid", "station_walk", "a station"),
        ("my mum, bless her, would like a park", "park_proximity", "a park"),
        ("honestly a lido round the corner, heaven forbid", "park_facilities", "a lido"),
    ],
)
def test_a_wish_in_doubt_is_asked_and_what_is_shown_takes_in_the_words_that_turned_it(
    text: str, feature: str, words: str
):
    found = through_the_route(_raise_of(feature, words), text)

    [offer] = found["suggestions"]
    shown = text[offer["shown"]["start"] : offer["shown"]["end"]]
    assert shown == text
    assert not any(way["guess"] for way in offer["choices"])
    # It is a question, and the one button takes none of it.
    assert offer["does"].endswith("?") and offer["add_all"] == ""


def _by_the_rules_alone(text: str) -> list[dict[str, Any]]:
    """What route 1 offers of a sentence where no model reads."""
    response = client_for(make_deps()).post("/v1/interpret", json={"text": text})
    assert response.status_code == 200
    return response.json()["data"]["suggestions"]


def test_what_the_rules_alone_offer_is_offered_as_it_was():
    # The new checks are made of what a model read. Where no model reads, a sister's
    # playground is offered as the rules always offered it, and so is a journey to
    # where a partner works, which is a place to reach and nobody's wish.
    [playground] = _by_the_rules_alone("My sister wants a playground")
    [journey] = _by_the_rules_alone("My partner works at Pellam Infirmary")

    assert (playground["does"], playground["add_all"]) == (
        "Rank areas higher for this: nearer a play space.",
        "more",
    )
    assert (journey["target"], journey["add_all"]) == ("commute", "more")


def test_a_wish_a_model_read_that_is_somebody_elses_is_asked_and_not_said():
    text = "My sister wants a playground"
    found = through_the_route(_raise_of("play_space_proximity", "a playground"), text)

    [playground] = found["suggestions"]
    assert playground["does"] == "Nearer a play space: count it?"
    assert playground["add_all"] == ""
    assert not any(way["guess"] for way in playground["choices"])


def test_a_word_of_dread_beside_a_nuisance_takes_no_guess_away():
    # To dread noise is to want less of it, so the word of dread turns nothing round.
    text = "honestly no traffic noise, god forbid"
    noise = model_weight("noise_exposure", words="no traffic noise")

    result, _ = asked(model_output(weight_ops=[noise]), text=text)

    assert guessed(result) == {"feature:noise_exposure": LESS}


# --- 5. A scale with no end ----------------------------------------------------------------


def test_a_scale_the_model_names_with_no_end_is_offered_with_both_ends_and_no_guess():
    text = "I keep hearing about the pace of a place, whatever that means"
    no_end = model_tag("pace", action="set", value=0.5, step="none", words="the pace of a place")

    result, _ = asked(model_output(tag_ops=[no_end]), text=text)

    pace = offers(result)["tag:pace"]
    assert [way.id for way in pace.choices] == [MORE, LESS, "ignore"]
    assert guessed(result) == {}
    assert Check.NO_END in fired(model_output(tag_ops=[no_end]), text)


@pytest.mark.parametrize(
    ("text", "tag", "guess"),
    [
        # The person said which way: one end is named, and the other is turned away.
        ("houses not flats", "homes", LESS),
        ("honestly flats, not houses", "homes", MORE),
        ("a house rather than a flat, honestly", "homes", LESS),
        ("honestly no flats, a house", "homes", LESS),
        ("somewhere calm, not buzzy, honestly", "pace", LESS),
        ("honestly historic, not newer", "built_age", MORE),
        # One end is named, and turned away: it is a wish for the other.
        ("honestly not buzzy at all", "pace", LESS),
        ("honestly not flats", "homes", LESS),
    ],
)
def test_a_guess_on_a_scale_takes_the_end_the_person_named(text: str, tag: str, guess: str):
    # Whichever end the model names that the words bear out, and where it names none.
    right = {MORE: "high", LESS: "low"}[guess]
    for toward in (right, "default"):
        for words in (text, text.removeprefix("honestly ").removesuffix(", honestly")):
            answer = model_output(tag_ops=[model_tag(tag, toward=toward, words=words)])

            result, _ = asked(answer, text=text)

            assert guessed(result) == {f"tag:{tag}": guess}, (toward, words)


@pytest.mark.parametrize(
    ("text", "tag", "wrong"),
    [
        ("houses not flats", "homes", "high"),
        ("somewhere calm, not buzzy, honestly", "pace", "high"),
        ("honestly not buzzy at all", "pace", "high"),
        ("honestly buzzy, not calm", "pace", "low"),
    ],
)
def test_the_end_a_model_names_against_the_words_is_no_guess(text: str, tag: str, wrong: str):
    # The words name one end, and the model the other. Both are offered, and neither is marked.
    answer = model_output(tag_ops=[model_tag(tag, toward=wrong, words=text)])

    result, _ = asked(answer, text=text)

    assert guessed(result) == {}
    assert [way.id for way in offers(result)[f"tag:{tag}"].choices][:2] == [MORE, LESS]


@pytest.mark.parametrize(
    ("text", "tag", "toward"),
    [
        # A word for a home says what is being looked for, and no more.
        ("honestly a flat would do", "homes", "high"),
        ("honestly houses", "homes", "low"),
        ("honestly a 1 bed flat for the two of us", "homes", "high"),
        # Both ends of it are named, and neither is turned away.
        ("honestly houses and flats alike", "homes", "low"),
        # The name of the scale holds the word for each end, and names neither: a word
        # that turns beside it turns no end away.
        ("honestly a long way houses or flats round here", "homes", "high"),
        ("honestly not houses or flats round here", "homes", "low"),
        # Two words that turn leave nobody sure which way.
        ("honestly I wouldn't say no to flats", "homes", "high"),
        ("honestly never not buzzy", "pace", "high"),
        # An end that is only named, where the model names none: no more than the rules noticed.
        ("honestly nightlife, I suppose", "pace", "default"),
        ("honestly calm by day and buzzy by night", "pace", "default"),
    ],
)
def test_a_scale_stays_a_question_where_the_words_do_not_say_which_end(
    text: str, tag: str, toward: str
):
    for named in (toward, "default"):
        answer = model_output(tag_ops=[model_tag(tag, toward=named, words=text)])

        result, _ = asked(answer, text=text)

        assert guessed(result).get(f"tag:{tag}") is None, named


def test_houses_not_flats_is_offered_as_houses_with_the_guess_marked():
    text = "houses not flats"
    answer = model_output(tag_ops=[model_tag("homes", toward="low", words=text)])

    found = through_the_route(answer, text)

    [homes] = found["suggestions"]
    assert homes["does"] == "Add Houses or flats, towards Houses."
    assert [(way["label"], way["guess"]) for way in homes["choices"]] == [
        ("Towards Flats", False),
        ("Towards Houses", True),
        ("Skip", False),
    ]
    assert text[homes["shown"]["start"] : homes["shown"]["end"]] == text


def test_the_name_of_a_scale_alone_is_the_rules_to_offer_and_no_model_is_asked():
    # "pace" and "built age": the model chose the high end of each.
    for case in ("vibe-036", "vibe-037"):
        text, spec, client = on_disk(case)
        reader = ModelInterpreter(client, MODEL, 512, 2.5)
        result = reader.interpret(InterpretRequest(text=text, spec=spec, release=release()))
        assert client.calls == [] and guessed(result) == {}
        [scale] = result.suggestions
        assert [choice.direction for choice in scale.choices] == ["more", "less", "ignore"]


# --- 6. Recorded crime -----------------------------------------------------------------------


@pytest.mark.parametrize("case", ["vibe-034", "long-013", "own-007", "own-021"])
def test_a_vibe_that_counts_recorded_crime_is_never_offered_from_a_model(case: str):
    # "somewhere with street character", "interesting streets", "a bit rough
    # around the edges", "slightly affluent": each read as Street character.
    for look in (1, 2, 3):
        try:
            result, _ = read_again(case, look)
        except KeyError:
            continue
        for offer in offers(result).values():
            for way in offer.choices:
                crime = any(tag.tag_id in HOLDS_CRIME for tag in way.operations.tag_ops)
                # Where the words name the scale, the rules offer it, and mark no guess.
                assert not crime or (way.ruled and not way.guess and not way.meant)


@pytest.mark.parametrize("case", ["crime-013", "crime-014", "crime-015"])
def test_recorded_crime_is_not_offered_on_words_core_does_not_read_as_crime(case: str):
    # What the check costs: "no muggings" and "I got burgled last year" are
    # right readings, and neither is offered. To offer one, add the word to core.
    result, _ = read_again(case)

    assert result.suggestions == ()


@pytest.mark.parametrize("provenance", ["stated", "inferred", "ui_edit"])
def test_what_a_model_calls_stated_makes_no_crime_count(provenance: str):
    text = "somewhere secure, honestly"
    crime = model_weight("crime_burglary_theft", provenance=provenance, words="somewhere secure")

    result, _ = asked(model_output(weight_ops=[crime]), text=text)

    assert result.suggestions == ()


def test_crime_that_is_named_in_cores_own_words_may_be_the_guess():
    text = "Honestly, I worry about burglary round here"
    crime = model_weight("crime_burglary_theft", words="I worry about burglary")

    result, _ = asked(model_output(weight_ops=[crime]), text=text)

    assert guessed(result) == {"feature:crime_burglary_theft": LESS}


# --- 7. How firm is code's ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("case", "first"),
    [
        # Decided on 2026-09-24: "up to" and "max" say the most that can be paid.
        ("long-003", FIRM),  # "up to £1,300 for a studio"
        ("own-021", FIRM),  # "max £1,900 a month"
        ("own-022", FIRM),  # "Max £475k for a flat."
        ("own-013", FIRM),  # "for no more than £650,000"
        ("own-024", GUIDE),  # "under £1,600 a month"
    ],
)
def test_a_limit_is_firm_only_where_the_persons_words_make_it_one(case: str, first: str):
    # The model called every one of these a firm limit.
    result, _ = read_again(case)

    budget = next(offer for name, offer in offers(result).items() if name.startswith("budget"))
    assert [way.id for way in budget.choices] == [
        first,
        FIRM if first == GUIDE else GUIDE,
        "ignore",
    ]
    assert [way.id for way in budget.choices if way.guess] == [first]


def test_a_journey_is_firm_where_the_words_say_at_most():
    # The rules read the sentence alone as a plain one, and apply it firm.
    result, _ = read_again("own-003", before=UNREAD_FIRST)

    [journey] = offers(result).values()
    assert [way.id for way in journey.choices if way.guess] == [FIRM]


def test_a_firm_limit_nobody_gave_is_counted_where_a_model_gives_one():
    text = "Honestly, under \N{POUND SIGN}1,700 a month"
    budget = model_budget(amount=1700, strictness="hard", words=text)

    assert Check.FIRM in fired(model_output(budget_ops=[budget]), text)


# --- 8. The way of travelling is code's ------------------------------------------------


def test_a_way_of_travelling_no_word_names_is_public_transport_and_the_offer_says_so():
    # A nurse who named no way, read as on foot.
    found, _ = served_again("long-003")

    [journey] = [offer for offer in found["suggestions"] if offer["target"] == "commute"]
    modes = {
        edit["mode"] for way in journey["choices"] for edit in way["operations"]["commute_ops"]
    }
    assert modes == {ModeChoice.UNCHANGED.value}
    assert "You named no way of travelling: Burro took public transport." in journey["said"]


def test_on_foot_is_kept_where_a_word_of_the_sentence_says_so():
    found, _ = served_again("own-027")

    [journey] = found["suggestions"]
    modes = {
        edit["mode"] for way in journey["choices"] for edit in way["operations"]["commute_ops"]
    }
    assert modes == {"walk"}
    assert journey["does"].endswith("at most 25 minutes, on foot.")
    assert journey["said"] == []


def test_a_walk_to_the_shops_is_not_the_way_to_work():
    # "a supermarket within walking distance; and no more than 35 minutes to
    # the office": one sentence, and the walk is said of another thing.
    found, text = served_again("long-007")

    [journey] = [offer for offer in found["suggestions"] if offer["target"] == "commute"]
    modes = {
        edit["mode"] for way in journey["choices"] for edit in way["operations"]["commute_ops"]
    }
    assert "walking distance" in text and modes == {ModeChoice.UNCHANGED.value}
    assert journey["does"] == (
        "Add a journey to Pellam Exchange: at most 35 minutes, by public transport."
    )


@pytest.mark.parametrize(
    ("text", "mode"),
    [
        ("Honestly, 20 minutes on foot to Cindermoor Works", "walk"),
        ("Honestly, I cycle to Cindermoor Works, 20 minutes", "cycle"),
        ("Honestly, a park I can walk to; 20 minutes to Cindermoor Works", "unchanged"),
        ("Honestly, 20 minutes to Cindermoor Works. I like to cycle at weekends", "unchanged"),
    ],
)
def test_the_way_of_travelling_is_read_from_the_clause_of_the_journey(text: str, mode: str):
    journey = model_commute(
        destination_text="Cindermoor Works", max_minutes=20, mode="cycle", words=text
    )
    if mode == "unchanged":
        journey["words"] = "20 minutes to Cindermoor Works"

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    edits = [e for w in offers(result)["commute"].choices for e in w.operations.commute_ops]
    assert {edit.mode.value for edit in edits} == {mode}


def test_a_word_for_walking_makes_a_journey_on_foot_though_the_model_says_otherwise():
    text = "Honestly, 20 minutes to Cindermoor Works by bike"
    journey = model_commute(
        destination_text="Cindermoor Works", max_minutes=20, mode="walk", words=text
    )

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    modes = {edit["mode"] for edit in edits_of(result) if "mode" in edit}
    assert modes == {"cycle"}


# --- 9. No number of the model's ------------------------------------------------------------


def test_no_weight_is_ever_a_number_a_model_chose():
    for (case, look), row in answers_on_disk().items():
        if "output" not in row:
            continue
        result, _ = read_again(case, look)
        for offer in offers(result).values():
            for way in offer.choices:
                for wish in (*way.operations.weight_ops, *way.operations.tag_ops):
                    assert wish.action is not WeightAction.SET or wish.value == 1.0, case
                    assert wish.step in (Step.NONE, Step.UP_SMALL, Step.UP_LARGE), case


@pytest.mark.parametrize(
    ("words", "action", "step"),
    [
        ("somewhere with a proper brunch spot", "nudge", "up_large"),
        ("somewhere with slightly more of a brunch spot", "nudge", "up_small"),
        ("a brunch spot is essential", "set", "none"),
    ],
)
def test_how_much_a_wish_counts_is_read_from_the_persons_words(words: str, action: str, step: str):
    text = f"Honestly, {words}"
    chose = model_weight("venue_food_drink", action="set", value=0.35, step="none", words=words)

    result, _ = asked(model_output(weight_ops=[chose]), text=text)

    eating = offers(result)["feature:venue_food_drink_per_homes"]
    [more] = [way for way in eating.choices if way.id == MORE]
    [edit] = more.operations.weight_ops
    assert (edit.action, edit.step) == (action, step)
    assert edit.value == (1.0 if action == "set" else 0.0)


def test_a_model_that_names_a_thing_that_is_never_ranked_on_is_read_as_core_reads_the_word():
    # The count of places to eat and drink is shown, and a wish for them is ranked on the
    # places for each 1,000 homes. A model is told of both, and may name either.
    text = "Honestly, somewhere with a proper brunch spot"
    offered = [
        offers(asked(model_output(weight_ops=[model_weight(named, words=text)]), text=text)[0])
        for named in ("venue_food_drink", "venue_food_drink_per_homes")
    ]

    assert offered[0] == offered[1]
    assert list(offered[0]) == ["feature:venue_food_drink_per_homes"]
    for way in offered[0]["feature:venue_food_drink_per_homes"].choices:
        assert {edit.feature_id for edit in way.operations.weight_ops} <= {
            "venue_food_drink_per_homes"
        }


def test_a_wish_set_to_nothing_is_a_wish_to_stop_counting_it():
    text = "Honestly, the station is of no use to me"
    nothing = model_weight("station_walk", action="set", value=0.0, step="none", words=text)

    result, _ = asked(model_output(weight_ops=[nothing]), text=text)

    assert guessed(result) == {"feature:station_walk": OFF}


# --- 10. A budget keeps its amount -------------------------------------------------------


def test_a_budget_keeps_its_amount_and_tenure_where_only_the_size_does_not_fit():
    # A buyer's "somewhere small", read as the size of a home to rent.
    text = "If I'm buying, max \N{POUND SIGN}400k for somewhere small"
    budget = model_budget(
        tenure="buy", amount=400000, segment="bed_1", strictness="hard", words=text
    )

    found = through_the_route(model_output(budget_ops=[budget]), text)

    [offer] = found["suggestions"]
    edits = [edit for way in offer["choices"] for edit in way["operations"]["budget_ops"]]
    assert {(edit["tenure"], edit["amount"], edit["segment"]) for edit in edits} == {
        (TenureChoice.BUY.value, 400000, SegmentChoice.UNCHANGED.value)
    }
    assert offer["does"] == "Set a budget of \N{POUND SIGN}400,000 to buy, as a firm limit."
    assert offer["said"] == [
        "Burro has prices by the kind of home, not by bedrooms: it left the size out."
    ]


def test_a_size_the_person_typed_is_the_rules_to_offer_and_a_model_adds_nothing_to_it():
    # The rules offer a buyer's "1 bed flat" as a flat, with what Burro holds prices by.
    text = "If I'm buying, max \N{POUND SIGN}400k for a 1 bed flat"
    budget = model_budget(
        tenure="buy", amount=400000, segment="bed_1", strictness="hard", words=text
    )

    found = through_the_route(model_output(budget_ops=[budget]), text)
    alone = client_for(make_deps()).post("/v1/interpret", json={"text": text}).json()["data"]

    assert [offer["target"] for offer in found["suggestions"]] == ["tenure", "budget", "budget"]
    assert {offer["read_by"] for offer in found["suggestions"]} == {"rule"}
    # Each is offered the one way the rules give it, which is the guess because it was
    # plainly said, and is what the rules offer with no model.
    assert [[way["guess"] for way in o["choices"]] for o in found["suggestions"]] == [
        [True, False]
    ] * 3
    assert found["suggestions"] == alone["suggestions"]
    assert "not by the number of bedrooms" in found["suggestions"][-1]["note"]


def test_an_amount_the_person_did_not_type_is_no_budget():
    text = "Honestly, about \N{POUND SIGN}1,500 a month"
    budget = model_budget(amount=1800, words=text)

    result, _ = asked(model_output(budget_ops=[budget]), text=text)

    assert 1800 not in [edit["amount"] for edit in edits_of(result) if "amount" in edit]
    assert Check.NOT_TYPED in fired(model_output(budget_ops=[budget]), text)


@pytest.mark.parametrize(
    ("typed", "amount"),
    [
        ("\N{POUND SIGN}400k", 400_000),
        ("1.2m", 1_200_000),
        ("2,000 quid", 2000),
        ("1800", 1800),
    ],
)
def test_an_amount_is_the_persons_however_they_wrote_it(typed: str, amount: int):
    text = f"Honestly, {typed} would do"
    budget = model_budget(amount=amount, words=text)

    result, _ = asked(model_output(budget_ops=[budget]), text=text, spec=renter())

    assert amount in [edit["amount"] for edit in edits_of(result) if "amount" in edit]


# --- 11. An edit that would change nothing ------------------------------------------------


@pytest.mark.parametrize("case", ["crime-022", "crime-008"])
def test_what_is_not_counted_is_not_offered_to_be_taken_off(case: str):
    # Four offers to take off recorded crime that was not on.
    result, _ = read_again(case)

    assert not [way for offer in offers(result).values() for way in offer.choices if way.id == OFF]
    assert guessed(result) == {}


def test_a_thing_that_runs_two_ways_and_is_not_held_is_offered_as_fewer():
    # "pubs, forget it": the model took pubs off, and no pubs were on.
    result, _ = read_again("neg-031")

    assert guessed(result) == {"feature:venue_evening_per_homes": LESS}


def test_a_thing_that_counts_because_nobody_chose_may_be_taken_off():
    found, _ = served_again("neg-032")

    [station] = found["suggestions"]
    assert station["does"] == "Stop counting this: nearer a station."
    assert "It counts a little now, because nobody chose." in station["follows"]
    assert [way["id"] for way in station["choices"] if way["guess"]] == [OFF]


# --- 12. One thing, pulled two ways in one answer -----------------------------------------


def test_one_thing_pulled_two_ways_is_one_offer_with_both_ways_and_no_guess():
    # Fewer places to eat for "not above a takeaway", more for "a decent cafe".
    result, text = read_again("long-004")

    [eating] = [
        offer
        for offer in offers(result).values()
        if any(
            edit.feature_id == "venue_food_drink_per_homes"
            for way in offer.choices
            for edit in way.operations.weight_ops
        )
    ]
    assert not any(way.guess for way in eating.choices)
    both = {way.id.rsplit("/", 1)[-1] for way in eating.choices if "venue_food_drink" in way.id}
    assert both == {MORE, LESS}
    rested = [text[span.start : span.end] for span in eating.spans]
    assert "Not above a pub or a takeaway" in rested and "a decent cafe" in rested


def test_two_budgets_in_one_answer_are_one_offer_and_neither_is_the_guess():
    found, _ = served_again("budget-042")

    budget = next(offer for offer in found["suggestions"] if offer["read_by"] == "model")
    amounts = [
        edit["amount"] for way in budget["choices"] for edit in way["operations"]["budget_ops"]
    ]
    assert amounts == [1800, 2200]
    assert not any(way["guess"] for way in budget["choices"]) and budget["add_all"] == ""
    # Each way says all that it holds, since neither is said above them.
    labels = [way["label"] for way in budget["choices"]]
    assert len(set(labels)) == 3 and "1,800" in labels[0] and "2,200" in labels[1]


# --- 13. Who lives somewhere ---------------------------------------------------------------


def test_no_offer_rests_on_words_about_who_lives_somewhere():
    # "near the university but not in the student bit": the model raised the campus.
    result, _ = read_again("who-039")

    assert result.notice is Notice.NEUTRAL_PLACES
    assert result.status is InterpretStatus.POLICY_REDIRECT
    assert result.suggestions == ()


def test_a_journey_to_a_campus_is_not_offered_in_a_prompt_that_is_not_plain():
    result, _ = read_again("own-030")

    assert result.notice is Notice.NEUTRAL_PLACES
    assert not [edit for edit in edits_of(result) if "place_id" in edit]
    # The rest of the request is still offered.
    assert "budget" in offers(result)


@pytest.mark.parametrize("flags", [["avoid_group"], ["seek_group"], ["avoid_group", "seek_group"]])
def test_where_only_the_model_says_it_is_about_people_nothing_of_its_answer_is_offered(
    flags: list[str],
):
    text = "lots of young mums about, near a park"
    answer = model_output(
        weight_ops=[model_weight("park_proximity", words="near a park")],
        tag_ops=[model_tag("family_amenities", words="lots of young mums about")],
        policy_flags=flags,
    )

    ruled, _ = asked(model_output(), text=text)
    result, _ = asked(answer, text=text)

    # The rules hear nothing about people in it, and the model does.
    assert ruled.notice is Notice.NONE
    assert result.notice is Notice.NEUTRAL_PLACES
    # What the rules noticed is offered as the rules give it, with no guess.
    assert list(offers(result)) == ["feature:park_proximity"]
    assert guessed(result) == {}
    assert all(offer.read_by is InterpreterName.RULE for offer in offers(result).values())


def test_a_notice_the_model_gives_without_cause_takes_no_offer_away():
    # What the check costs: "somewhere safe for a single woman".
    result, text = read_again("crime-034")
    ruled = asked(model_output(), text=text)[0]

    assert result.notice is Notice.NEUTRAL_PLACES
    assert [offer.target for offer in result.suggestions] == [
        offer.target for offer in ruled.suggestions
    ]


# --- What is never offered from a model, whatever it says --------------------------------


@pytest.mark.parametrize("toward", ["high", "low", "default"])
@pytest.mark.parametrize(
    "text",
    [
        "somewhere with a proper bit of grit, honestly",
        "somewhere slightly affluent, honestly",
        "interesting streets, honestly",
        "somewhere edgy, honestly",
        "street character, honestly",
    ],
)
def test_never_a_vibe_that_counts_recorded_crime(text: str, toward: str):
    for provenance in ("stated", "inferred", "ui_edit"):
        tag = model_tag("street_character", toward=toward, provenance=provenance, words=text)
        result, _ = asked(model_output(tag_ops=[tag]), text=text)
        for offer in offers(result).values():
            # Where the words name the scale, the rules offer it and mark no guess.
            assert offer.read_by is InterpreterName.RULE and offer.note
            assert not any(way.guess or way.meant for way in offer.choices)


def test_never_a_weight_on_recorded_crime_that_the_words_do_not_name():
    crimes = [
        feature_id
        for feature_id, feature in FEATURES.items()
        if feature.dimension is Dimension.CRIME
    ]
    for crime in crimes:
        text = "somewhere I can leave my bike out, honestly"
        raised = model_weight(crime.value, provenance="stated", words=text)
        result, _ = asked(model_output(weight_ops=[raised]), text=text)
        assert result.suggestions == ()


NOTED = sorted(phrase for phrase, target in LEXICON.items() if target.note)


@pytest.mark.parametrize("phrase", NOTED)
def test_never_a_reading_of_a_word_the_rules_offer_what_is_nearest_for(phrase: str):
    # "Safe", "a sense of community", and every word core adds with a note of
    # what Burro cannot measure: a word about wealth, a word about identity.
    # What the rules offer for it is kept, and a model adds no reading of its own.
    text = f"somewhere {phrase}, honestly"
    ruled, _ = asked(model_output(), text=text)
    answer = model_output(
        weight_ops=[
            model_weight("venue_independent", words=text),
            model_weight("crime_burglary_theft", provenance="stated", words=phrase),
        ],
        tag_ops=[
            model_tag("village_feel", action="set", value=1.0, words=phrase),
            model_tag("street_character", toward="low", words=f"somewhere {phrase}"),
        ],
    )

    result, _ = asked(answer, text=text)

    assert [(o.target, o.note) for o in result.suggestions] == [
        (o.target, o.note) for o in ruled.suggestions
    ]
    assert ruled.suggestions and guessed(result) == {}
    for offer in offers(result).values():
        assert offer.read_by is InterpreterName.RULE
        assert [way.id for way in offer.choices] == [
            way.id for way in offers(ruled)[offer.target].choices
        ]


def _kept_by_the_rules(ruled: InterpretResult) -> dict[str, Any]:
    """What the rules offer with a note of what Burro cannot measure, as they give it."""
    return {
        offer.target: ([way.id for way in offer.choices], offer.spans, offer.note)
        for offer in offers(ruled).values()
        if offer.note and thing_named(offer.target) is not None
    }


def _as_served(result: InterpretResult, targets: Any) -> dict[str, Any]:
    return {
        offer.target: ([way.id for way in offer.choices], offer.spans, offer.note)
        for offer in offers(result).values()
        if offer.target in targets
    }


def _marked(result: InterpretResult, targets: Any) -> list[str]:
    """Every way of some offers that a model's reading is marked on, as a guess or not."""
    return [
        f"{offer.target} {way.id}"
        for offer in offers(result).values()
        if offer.target in targets
        for way in offer.choices
        if way.guess or way.meant
    ]


@pytest.mark.parametrize("phrase", NOTED)
def test_never_a_guess_at_a_reading_the_rules_keep_whatever_words_a_model_rests_it_on(
    phrase: str,
):
    # The readings of a word about identity, about wealth, about safety: each is the
    # rules' to offer, as they offer it with no model. A model that names the same
    # thing, and rests it on other words of the sentence, adds no guess and no way to it.
    text = f"somewhere {phrase}, and a proper brunch spot, honestly"
    ruled, _ = asked(model_output(), text=text)
    kept = _kept_by_the_rules(ruled)
    things = [thing_named(target) for target in kept]
    answer = model_output(
        weight_ops=[
            model_weight(thing.value, direction=way, words="a proper brunch spot")
            for thing in things
            if isinstance(thing, FeatureId)
            for way in ("more", "less")
        ],
        tag_ops=[
            model_tag(thing.value, toward=end, words="and a proper brunch spot")
            for thing in things
            if isinstance(thing, TagId)
            for end in ("high", "low")
        ],
    )

    result, _ = asked(answer, text=text)

    assert kept and _as_served(result, kept) == kept
    assert _marked(result, kept) == []


def test_what_the_rules_keep_is_served_as_the_rules_give_it_whatever_a_model_answered():
    # "A real identity", in the sentence of `own-021`: in one look the model rested the
    # age of buildings on the words about culture, and the rules' reading of the word
    # about identity gained a way and a guess could have been marked on it.
    changed: list[str] = []
    for (case, look), row in answers_on_disk().items():
        if "output" not in row:
            continue
        text, spec, _ = on_disk(case, look)
        ruled = RuleInterpreter().interpret(
            InterpretRequest(text=text, spec=spec, release=release())
        )
        kept = _kept_by_the_rules(ruled)
        result, _ = read_again(case, look)
        if _as_served(result, kept) != kept or _marked(result, kept):
            changed.append(f"{case} look {look}")
    assert changed == []


def test_never_anything_about_who_lives_somewhere():
    text = "full of bankers and students, honestly"
    answer = model_output(
        tag_ops=[model_tag("family_amenities", words="students")],
        weight_ops=[model_weight("school_primary_attainment", words="students")],
    )

    result, _ = asked(answer, text=text)

    assert result.notice is Notice.NEUTRAL_PLACES and result.suggestions == ()


def test_what_a_model_reads_into_words_for_who_is_counted_is_dropped():
    # The rules offer Family area for the words, and a model's reading of them is not
    # put beside it: nothing about who lives somewhere is read into a measure of a place.
    text = "full of bankers and young families, honestly"
    answer = model_output(
        tag_ops=[model_tag("family_amenities", words="young families")],
        weight_ops=[model_weight("school_primary_attainment", words="young families")],
    )

    ruled, _ = asked(model_output(), text=text)
    result, _ = asked(answer, text=text)

    assert [offer.target for offer in ruled.suggestions] == ["tag:family_area"]
    assert [(o.target, o.note) for o in result.suggestions] == [
        (o.target, o.note) for o in ruled.suggestions
    ]
    assert guessed(result) == {}


@pytest.mark.parametrize(
    ("words", "meant"),
    [
        ("under \N{POUND SIGN}1,700", StrictnessChoice.SOFT),
        ("around \N{POUND SIGN}1,700 a month", StrictnessChoice.SOFT),
        ("maximum \N{POUND SIGN}1,700", StrictnessChoice.SOFT),
        # Decided on 2026-09-24: these say the most that can be paid.
        ("up to \N{POUND SIGN}1,700 a month", StrictnessChoice.HARD),
        ("max \N{POUND SIGN}1,700", StrictnessChoice.HARD),
        ("\N{POUND SIGN}1,700 a month max", StrictnessChoice.HARD),
        ("at most \N{POUND SIGN}1,700", StrictnessChoice.HARD),
        ("no more than \N{POUND SIGN}1,700", StrictnessChoice.HARD),
    ],
)
def test_never_a_firm_limit_nobody_gave(words: str, meant: StrictnessChoice):
    text = f"Honestly, {words}"
    budget = model_budget(amount=1700, strictness="hard", words=words)

    result, _ = asked(model_output(budget_ops=[budget]), text=text)

    [offer] = offers(result).values()
    guess = [way for way in offer.choices if way.guess]
    strictness = [edit.strictness for way in guess for edit in way.operations.budget_ops]
    assert strictness == [meant]


@pytest.mark.parametrize(
    ("words", "meant"),
    [
        ("30 minutes to Foxholt Market", StrictnessChoice.SOFT),
        ("up to 30 minutes to Foxholt Market", StrictnessChoice.SOFT),
        ("under 30 minutes to Foxholt Market", StrictnessChoice.SOFT),
        # Decided on 2026-09-24: these make a number of minutes a firm limit, and a range
        # is one at its longer end.
        ("within 30 minutes of Foxholt Market", StrictnessChoice.HARD),
        ("max 30 minutes to Foxholt Market", StrictnessChoice.HARD),
        ("at most 30 minutes to Foxholt Market", StrictnessChoice.HARD),
        ("no more than 30 minutes to Foxholt Market", StrictnessChoice.HARD),
        ("25-30min to Foxholt Market", StrictnessChoice.HARD),
        ("25 to 30 minutes to Foxholt Market", StrictnessChoice.HARD),
    ],
)
def test_a_journey_is_a_firm_limit_only_where_the_words_or_a_range_make_it_one(
    words: str, meant: StrictnessChoice
):
    text = f"Honestly, {words}"
    journey = model_commute(
        destination_text="Foxholt Market", max_minutes=30, strictness="hard", words=words
    )

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    [offer] = offers(result).values()
    guess = [way for way in offer.choices if way.guess]
    strictness = [edit.strictness for way in guess for edit in way.operations.commute_ops]
    assert strictness == [meant]


def test_the_shorter_end_of_a_range_is_never_a_firm_limit():
    """Whoever says 25 to 30 minutes would take 30, so 25 leaves out what they would take."""
    text = "Honestly, 25-30min to Foxholt Market"
    journey = model_commute(
        destination_text="Foxholt Market", max_minutes=25, strictness="hard", words=text
    )

    result, _ = asked(model_output(commute_ops=[journey]), text=text)

    [offer] = offers(result).values()
    firm = [
        edit.strictness for way in offer.choices if way.guess for edit in way.operations.commute_ops
    ]
    assert firm == [StrictnessChoice.SOFT]


@pytest.mark.parametrize(
    "words",
    [
        "at most \N{POUND SIGN}1,700 a month",
        "no more than \N{POUND SIGN}1,700",
        "I can't go over \N{POUND SIGN}1,700",
    ],
)
def test_a_firm_limit_that_was_given_is_the_guess_and_the_guide_is_beside_it(words: str):
    text = f"Honestly, {words}"
    budget = model_budget(amount=1700, strictness="soft", words=words)

    result, _ = asked(model_output(budget_ops=[budget]), text=text)

    [offer] = offers(result).values()
    assert [way.id for way in offer.choices] == [FIRM, GUIDE, "ignore"]
    assert [way.id for way in offer.choices if way.guess] == [FIRM]


def test_never_a_least_distance_as_a_journey():
    for sign in ("at least", "minimum", "no less than", "more than", "further than"):
        text = f"Honestly, {sign} 30 minutes from Pellam Cross"
        journey = model_commute(
            destination_text="Pellam Cross", max_minutes=30, strictness="hard", words=text
        )
        result, _ = asked(model_output(commute_ops=[journey]), text=text)
        assert not [edit for edit in edits_of(result) if edit.get("max_minutes")], sign
        assert not [edit for edit in edits_of(result) if "place_id" in edit], sign


def test_never_a_number_for_a_weight():
    text = "Honestly, a proper brunch spot and somewhere leafy-ish"
    answer = model_output(
        weight_ops=[
            model_weight("venue_food_drink", action="set", value=0.7, step="none", words=text)
        ],
        tag_ops=[model_tag("leafy", action="set", value=0.3, step="none", words=text)],
    )

    result, _ = asked(answer, text=text)

    values = {edit["value"] for edit in edits_of(result) if "value" in edit}
    assert values <= {0.0} and Check.NUMBER in fired(answer, text)


def test_never_a_place_an_area_or_an_amount_the_person_did_not_type():
    text = "Honestly, a short hop to work and not a fortune"
    answer = model_output(
        commute_ops=[model_commute(destination_text="Pellam Exchange", max_minutes=20, words=text)],
        area_ops=[model_area("only", "Wexmoor", words=text)],
        budget_ops=[model_budget(amount=1500, words=text)],
    )

    result, _ = asked(answer, text=text)

    assert result.suggestions == ()
    assert {Check.NAME, Check.AREA, Check.NOT_TYPED} <= fired(answer, text)


@pytest.mark.parametrize(
    ("case", "rule"), [("own-009", "exclude"), ("own-026", "only"), ("long-004", "exclude")]
)
def test_never_a_rule_for_an_area_as_a_guess(case: str, rule: str):
    # The rules notice every name typed in full, and offer the rules for it.
    result, _ = read_again(case)

    areas = [offer for offer in offers(result).values() if offer.target == "area"]
    assert areas
    for offer in areas:
        assert offer.read_by is InterpreterName.RULE
        assert not any(way.guess or way.meant for way in offer.choices)
        assert rule in [edit.action for way in offer.choices for edit in way.operations.area_ops]


def test_a_setting_a_step_of_the_budget_and_a_journey_changed_are_not_offered():
    text = "Honestly, a bit cheaper, and the slowest journey is what matters"
    answer = model_output(
        budget_ops=[model_budget(action="nudge", step="down_small", words="a bit cheaper")],
        commute_ops=[model_commute(action="remove", position=1, words=text)],
        setting_ops=[model_setting("commute_combine", choice="slowest", words=text)],
    )

    result, _ = asked(answer, text=text)

    assert result.suggestions == () and result.unmet == (UnmetCategory.OTHER,)
    assert fired(answer, text) == {Check.NOT_WORDED}


# --- What is known to get through ---------------------------------------------------------


@pytest.mark.parametrize(("case", "look"), [("sugg-022", 1), ("sugg-022", 2), ("sugg-022", 3)])
def test_someone_elses_wish_is_not_marked_as_the_guess(case: str, look: int):
    # "my mum is after a park": the model read it as the person's own wish, every time
    # it was asked. Core lists the words that say whose wish it is.
    result, _ = read_again(case, look)

    assert guessed(result) == {}
    assert list(offers(result)) == ["feature:park_proximity"]


@pytest.mark.xfail(strict=True, reason="contract, section 8.2: what the guard cannot do")
@pytest.mark.parametrize(
    "text",
    [
        "boozers on every corner would finish me off",
        "a proper brunch spot would bankrupt me",
    ],
)
def test_a_wish_turned_round_in_words_core_does_not_list_is_not_the_guess(text: str):
    answer = model_output(
        weight_ops=[model_weight("venue_evening_per_homes", direction="more", words=text)]
    )

    result, _ = asked(answer, text=text)

    assert guessed(result) == {}
