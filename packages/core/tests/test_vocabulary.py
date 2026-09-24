"""The reader applies a prompt only when the whole of it is plain.

Listing the words that turn a wish round did not work: English has too many,
and people mistype them. Reading each sentence that was made of known words
did not work either, because no single word is ever the fault: "pubs are so
noisy" is made of words that are each harmless. So the reader has a grammar
of a plain prompt, and applies a prompt only when the grammar makes the
whole of it. For any other it applies nothing, and offers what it noticed.

These tests hold it to that three ways: by the sentences that went wrong, by
sentences made of every thing beside words it does not know, and by the share
of plain wishes it still reads, which is the price.
"""

from collections.abc import Iterator

import pytest
from burro_core import vocabulary
from burro_core.grammar import KNOWN_WORDS, read_into_crime
from burro_core.ids import (
    AreaAction,
    CommuteAction,
    DirectionChoice,
    GrittyVariant,
    InterpretStatus,
    Notice,
    OpsGroup,
    PlaceKind,
    Step,
    Tenure,
    TenureChoice,
    Toward,
    UnmetCategory,
    WeightAction,
)
from burro_core.interpret import (
    GENERIC_PLACES,
    POLICY_LEXICON,
    SIGNS_OF_DOUBT,
    VOCABULARY,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    sentences_of,
)
from burro_core.lexicon import lexicon_of, no_measure_of
from burro_core.ops import NO_OPERATIONS
from burro_core.places import Names, normalise
from burro_core.reducer import apply
from burro_core.spec import PreferenceSpec, default_spec
from burro_core.vocabulary import PLAIN, PLAIN_WORDS, WORDS_OF_DOUBT

from .sentences import (
    HELD_OUT,
    REVERSED,
    THEIRS,
    TURNED_LISTS,
    UNASKED,
    UNKNOWN_WORDS,
    Wishes,
)
from .sentences import PLAIN as PLAINLY
from .support import fixture_release, small_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
READER = RuleInterpreter()
NAMES = Names(fixture_release())
UP = (Step.UP_SMALL, Step.UP_LARGE)
# Every phrase that is a thing in the release that is served.
THINGS = lexicon_of(fixture_release().manifest.gritty_variant)
# Words that are known only inside a label of the catalogue, or a phrase for what
# Burro has no measure of.
IN_A_LABEL = ("away", "garden", "since", "small", "used", "what", "whose", "works")
IN_NO_MEASURE = ("cheap", "down", "fly", "kept", "run")


def read(text: str, spec: PreferenceSpec = RENTER) -> InterpretResult:
    return READER.interpret(InterpretRequest(text=text, spec=spec, release=fixture_release()))


def raised(result: InterpretResult) -> set[str]:
    """Every edit that raises a weight or a tag, adds a journey or an area rule, tightens a
    limit or changes the tenure. A question about a place, which adds nothing, is not one."""
    found: set[str] = set()
    for weight in result.operations.weight_ops:
        up = weight.action is WeightAction.SET or (
            weight.action is WeightAction.NUDGE and weight.step in UP
        )
        if up and weight.direction is not DirectionChoice.LESS:
            found.add(weight.feature_id.value)
    for tag in result.operations.tag_ops:
        if tag.action is WeightAction.SET or (tag.action is WeightAction.NUDGE and tag.step in UP):
            # Towards the low end of a scale it is a wish for that end: "calm".
            found.add(f"{tag.tag_id.value}{':low' if tag.toward == 'low' else ''}")
    for journey in result.operations.commute_ops:
        if journey.action is not CommuteAction.REMOVE and journey.place_id:
            found.add(f"journey:{journey.place_id}")
    for rule in result.operations.area_ops:
        if rule.action is not AreaAction.CLEAR:
            found.add(f"area:{rule.area_id}:{rule.action.value}")
    for budget in result.operations.budget_ops:
        found.add("budget")
        if budget.tenure is not TenureChoice.UNCHANGED:
            found.add(f"tenure:{budget.tenure.value}")
    return found


def edits(result: InterpretResult) -> int:
    """How many edits were made, leaving out a question about a place, which adds nothing."""
    asked = [edit for edit in result.operations.commute_ops if not edit.place_id]
    return result.operations.count - len(asked)


# --- P1. The vocabulary ---------------------------------------------------------


def test_every_plain_word_is_written_down_once_with_where_it_stands_and_why_it_is_safe():
    listed = [word for group in PLAIN for word in group.words]
    assert len(listed) == len(set(listed)) == len(PLAIN_WORDS)
    for group in PLAIN:
        assert len(group.why) > 20 and group.why.endswith(".")
        for word in group.words:
            assert word == word.lower().strip() == " ".join(word.split()), word


def test_the_list_of_plain_words_is_short_and_is_reviewed_as_a_whole():
    # Adding a word is the only way to widen what the grammar makes, so the
    # number is held here. Change it in the same change that adds the word,
    # with where the grammar places it and why it can turn no wish round there.
    # The phrases grew by the ways of saying where the speaker works, "from my office
    # at", each made of words that were known. No plain word was added for them.
    # 133: "around" and "around it" joined the words for nearby, which stand after a
    # thing and nowhere else.
    assert len(PLAIN_WORDS) == 133
    assert len(VOCABULARY) < 580
    assert len(KNOWN_WORDS) < 310


# Words that turn a wish round, weaken it, compare it, question it or give it to
# someone else. None may ever be read through.
NEVER_PLAIN = (
    "not no never none nothing nobody nowhere neither nor without less fewer few little "
    "hate dislike avoid stop quit rather instead than except unless if though although "
    "maybe perhaps possibly quite fairly pretty ideally preferably hopefully just only even "
    "was were did had used wanted liked loved needed worked lived once formerly "
    "he she they you people everyone anyone someone his her their your wants needs likes "
    "loves works lives who what why how when where which should could might do does "
    "far away off out over miles outside beyond distance too enough against all every "
    "anything anywhere everything everywhere other another else close can room short easy"
)


def test_no_plain_word_can_turn_weaken_compare_question_or_reassign_a_wish():
    for word in NEVER_PLAIN.split():
        assert word not in PLAIN_WORDS, word
    assert not PLAIN_WORDS & WORDS_OF_DOUBT
    # And no word that is known only with others beside it is known by itself.
    phrases = {phrase for phrase in VOCABULARY if " " in phrase}
    apart = {word for phrase in phrases for word in phrase.split()} - VOCABULARY
    alone = {"foot", "distance", "short", "easy", "well", "thank", "there", "corner", "get", "can"}
    assert alone <= apart
    assert not alone & VOCABULARY


def test_the_words_the_reader_has_a_rule_for_are_not_plain_words():
    ruled = (
        vocabulary.TURNS_FIRMLY
        | vocabulary.TURNS_SOFTLY
        | vocabulary.TAKES_OFF
        | vocabulary.TAKES_OFF_AFTER
        | vocabulary.TURNS_DOWN
        | vocabulary.TURNS_DOWN_AFTER
        | vocabulary.CAPS_FIRMLY
        | vocabulary.ONLY_IN
        | vocabulary.NOT_IN
    )
    assert not ruled & PLAIN_WORDS
    assert {"no", "not", "without", "less", "fewer", "avoid", "only", "at most"} <= ruled
    assert {"up to", "under", "within", "no more than"} <= vocabulary.CAPS | ruled
    assert "more" in vocabulary.SMALL_STEP
    # A number that is a minimum is no word of the reader's at all.
    for minimum in ("at least", "more than", "no less than", "further than", "minimum", "over"):
        assert minimum not in VOCABULARY, minimum


def test_the_words_that_are_not_known_are_many_and_none_is_in_the_vocabulary():
    assert len(UNKNOWN_WORDS) == len(set(UNKNOWN_WORDS)) >= 500
    # No word of a phrase of the grammar, and no word of who lives somewhere.
    assert not KNOWN_WORDS & set(UNKNOWN_WORDS)
    assert not {word for phrase in POLICY_LEXICON for word in phrase.split()} & set(UNKNOWN_WORDS)
    assert not GENERIC_PLACES & set(UNKNOWN_WORDS)
    # A thing is known by the whole of a phrase. A label of the catalogue may hold
    # a word that is not known by itself, "Away from main roads", and the word
    # is still not known: the generated test below puts each beside every thing.
    for variant in GrittyVariant:
        things = set(lexicon_of(variant)) | set(no_measure_of(variant))
        assert not things & set(UNKNOWN_WORDS)
        inside = {word for phrase in things for word in phrase.split()} & set(UNKNOWN_WORDS)
        assert inside <= {*IN_A_LABEL, *IN_NO_MEASURE}
    for must in ("hate", "yuck", "don;t", "dint", "donut", "mum", "stalker", "was", "should"):
        assert must in UNKNOWN_WORDS, must


# --- The sentences that went wrong ---------------------------------------------------


@pytest.mark.parametrize("text", REVERSED)
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renter", "buyer"])
def test_a_sentence_that_was_read_backwards_raises_nothing(text: str, spec: PreferenceSpec):
    result = read(text, spec)
    assert raised(result) == set()
    assert result.clarify == ()
    # It says that it did not read it, or that it is about who lives somewhere,
    # or it read the whole of it as a wish for less: "no pubs or loads of restaurants".
    less = [
        edit
        for edit in result.operations.weight_ops
        if edit.direction is DirectionChoice.LESS or edit.action is WeightAction.REMOVE
    ]
    told = UnmetCategory.OTHER in result.unmet or result.notice is Notice.NEUTRAL_PLACES
    assert told or (less and len(less) == result.operations.count)
    # And what it noticed is offered with no direction chosen: every choice is
    # the person's to make, and to leave it out is always one of them.
    for found in result.suggestions:
        assert found.choices[-1].direction == "ignore"
    after = apply(spec, result.operations, fixture_release())
    assert after.spec.commutes == spec.commutes and after.spec.areas == spec.areas
    assert after.spec.tenure is spec.tenure and after.spec.budget == spec.budget


@pytest.mark.parametrize("text", UNASKED)
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renter", "buyer"])
def test_a_sentence_that_made_an_edit_nobody_asked_for_makes_none(text: str, spec: PreferenceSpec):
    result = read(text, spec)
    assert result.operations == NO_OPERATIONS
    assert UnmetCategory.OTHER in result.unmet
    assert apply(spec, result.operations, fixture_release()).spec == spec


def test_the_adversarys_sentences_are_all_here():
    assert len(REVERSED) == len(set(REVERSED)) == 100
    assert len(UNASKED) == len(set(UNASKED)) == 24


# --- Every thing and every name beside a word that is not known ---------------------

# Where the word stands, and what stands between it and the thing.
BESIDE_A_THING = (
    "{word} {thing}",
    "{thing} {word}",
    "I {word} {thing}",
    "I want {thing} {word}",
    "{word} I want {thing}",
    "{thing}, {word}",
    "{word}, {thing}",
    "{thing}: {word}",
    "{word}: {thing}",
    "{thing} - {word}",
    "{thing} \N{EM DASH} {word}",
    "{thing} ({word})",
    "({word}) {thing}",
    "{thing}; {word}",
    "I want {thing} and {word}",
    "{word} and {thing}",
    "{thing} or {word}",
    "lots of {thing} but {word}",
    "{thing} is {word}",
    "{thing} would be {word}",
    "a {word} {thing} please",
    "somewhere with {thing} {word} nearby",
    '"{word}" {thing}',
    "{thing} {word}!",
    "{word}-{thing}",
    "{thing}/{word}",
    "{word}{thing}",
    "{thing} for the {word}",
    "{thing} to {word}",
    "{thing} on my {word}",
    "my {word} wants {thing}",
    "{word} want {thing}",
    # A sentence of its own, which holds doubt and names nothing (P4).
    "{thing}. {word}.",
    "I want {thing}. {word}.",
    "{thing}? {word}",
    "{thing}... {word}",
    "{thing}\n{word}",
    "{word}\n{thing}",
    "{word}:\n{thing}\n{thing}",
    "{word}.\n- {thing}\n- {thing}",
)
BESIDE_A_NAME = (
    "I work at {name} {word}",
    "{word} I work at {name}",
    "I {word} work at {name}",
    "I work at {name}, {word}",
    "I work at {name} ({word})",
    "I work at {name}. {word}.",
    "my {word} works at {name}",
    "{word} work at {name}",
    "near {name} {word}",
    "{word} near {name}",
    "30 minutes to {name} {word}",
    "{word} 30 minutes to {name}",
    "no more than 30 minutes to {name} {word}",
    "within 30 minutes of {name}\n{word}",
    "I commute to {name} - {word}",
    "only in {name} {word}",
    "{word} only in {name}",
    "{word}: only {name}",
    "not {name} {word}",
    "avoid {name}, {word}",
    "{word} avoid {name}",
    "{word} {name}",
)
BESIDE_A_HOME = (
    "{word} renting",
    "renting {word}",
    "I want to buy {word}",
    "{word} buying",
    "buying. {word}.",
    "to rent, {word}",
    "{word} £1,500 a month",
    "under £1,500 {word}",
    "a 2 bed flat to rent {word}",
)


def names_of_the_release() -> list[str]:
    release = fixture_release()
    found = {name for place in release.places for name in (place.name, *place.aliases)}
    found |= {name for area in release.neighbourhoods for name in (area.name, *area.aliases)}
    return sorted(found)


def beside(template: str, word: str, name: str) -> Iterator[str]:
    """A word beside a name, unless the two together are a name of the release themselves.

    "Works" is a word the reader does not know, and "Cindermoor Works" is a place.
    """
    names = NAMES
    together = (normalise(f"{name} {word}"), normalise(f"{word} {name}"))
    if not any(names.whole_place(both) or names.whole_area(both) for both in together):
        yield template.format(word=word, name=name)


def every_sentence() -> Iterator[str]:
    """Every unknown word in every place it can stand, beside each thing and each name in turn."""
    things, names = sorted(THINGS), names_of_the_release()
    for row, word in enumerate(UNKNOWN_WORDS):
        for column, template in enumerate(BESIDE_A_THING):
            yield template.format(word=word, thing=things[(row * 7 + column) % len(things)])
        for column, template in enumerate(BESIDE_A_NAME):
            yield from beside(template, word, names[(row * 5 + column) % len(names)])
        for template in BESIDE_A_HOME:
            yield template.format(word=word)


def a_sample() -> Iterator[str]:
    """Every thing and every name, each beside a different word in several places.

    It is fixed: the same sentences every time, with no source of chance.
    """
    words = UNKNOWN_WORDS
    for row, thing in enumerate(sorted(THINGS)):
        for turn in range(8):
            template = BESIDE_A_THING[(row + turn * 5) % len(BESIDE_A_THING)]
            yield template.format(word=words[(row * 8 + turn) % len(words)], thing=thing)
    for row, name in enumerate(names_of_the_release()):
        for turn in range(8):
            template = BESIDE_A_NAME[(row + turn * 3) % len(BESIDE_A_NAME)]
            yield from beside(template, words[(row * 11 + turn) % len(words)], name)
    for row, word in enumerate(words):
        yield BESIDE_A_THING[row % len(BESIDE_A_THING)].format(word=word, thing="a park")
        yield BESIDE_A_NAME[row % len(BESIDE_A_NAME)].format(word=word, name="Pellam Cross")
        yield BESIDE_A_HOME[row % len(BESIDE_A_HOME)].format(word=word)


def held_to_the_promise(sentences: Iterator[str]) -> int:
    """No sentence may raise a weight or a tag, add a journey or an area rule, tighten a
    limit or change the tenure. None may lower anything either: it makes no edit at all."""
    wrong: list[str] = []
    tried = 0
    for text in sentences:
        tried += 1
        result = read(text[:600])
        # It says that it did not read it. A campus in a sentence it did not
        # read gets the notice as well (section 8.4).
        if edits(result) or UnmetCategory.OTHER not in result.unmet:
            wrong.append(text)
    assert not wrong, f"{len(wrong)} of {tried} sentences, among them {wrong[:12]}"
    return tried


def test_a_word_that_is_not_known_beside_any_thing_or_name_makes_the_sentence_unread():
    sample = list(a_sample())
    assert len(set(sample)) > 3_500
    for thing in THINGS:
        assert any(thing in text for text in sample), thing
    for name in names_of_the_release():
        assert any(name in text for text in sample), name
    assert held_to_the_promise(iter(sample)) == len(sample)


@pytest.mark.full
def test_every_word_that_is_not_known_in_every_place_makes_the_sentence_unread():
    assert held_to_the_promise(every_sentence()) > 40_000


def test_a_sentence_with_an_unknown_word_reports_one_unmet_request_of_kind_other():
    for text, unread in (
        ("a park for the zebra", ["a", "for the zebra"]),
        ("leafy, quiet, zebra", ["zebra"]),
        ("zebra near Pellam Cross", ["zebra near"]),
    ):
        result = read(text)
        assert result.operations == NO_OPERATIONS
        assert result.unmet == (UnmetCategory.OTHER,)
        assert (result.status, result.notice) == (InterpretStatus.SUGGEST, Notice.NONE)
        assert [text[span.start : span.end] for span in result.unread] == unread


# --- Sentences made of nothing but words the reader knows ---------------------------


@pytest.mark.parametrize(
    "text",
    [
        # A word that turns, with nothing after it to turn.
        "pubs are not for me",
        "pubs, no",
        "pubs: no",
        "no: pubs",
        "avoid - pubs",
        "I do not want: pubs, bars",
        "pubs not",
        "pubs are no good",
        "pubs are a no",
        "parks, pubs, not",
        "I want a park or not",
        "my need for pubs is low",
        "pubs would be good to avoid",
        "pubs are not my thing",
        "pubs are something I avoid",
        "a park is not a must",
        "a park is important, pubs not so",
        "I like pubs a lot less",
        # Two words that turn: nobody can say which way they leave the wish.
        "not without a park",
        "I can not live without a park",
        "no place without a park",
        "avoid areas with no parks",
        "I would avoid a place without a park",
        "I do not want to avoid pubs",
        "not only parks",
        "only parks",
        "not under £1,500",
        # Known words that mean the opposite together.
        "pubs are a bit much",
        "pubs are so so",
        "I want the pubs to close",
        "can the pubs",
        "pubs or no pubs",
        "plenty of room",
        # A word that is known as what the speaker does, standing where it compares.
        "I need pubs like I need noise",
        "I need a station like I need more noise",
        "somewhere like that with pubs",
        "my love of pubs is low",
        # Asked for and turned away in one request.
        "to buy or not to buy",
        "I commute to Pellam Cross and I want to not commute to Pellam Cross",
        "I live near pubs and I need to not live near pubs",
        # A nuisance that is said to be a must, and not to matter.
        "pollution is a must",
        "noise is essential",
    ],
)
def test_known_words_that_no_rule_accounts_for_leave_the_sentence_unread(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert result.unmet == (UnmetCategory.OTHER,)


NOTHING: set[str] = set()


@pytest.mark.parametrize(
    ("text", "lowered", "asked"),
    [
        # A turn governs the thing straight after it. "But", a wish of the speaker's
        # and a word of the thing's own begin a new wish.
        ("leafy, not near a station", {"station_walk"}, {"leafy"}),
        ("no pubs, but a park nearby", {"venue_evening"}, {"park_proximity"}),
        ("no pubs, I want parks", {"venue_evening"}, {"park_proximity"}),
        ("no pubs, near a park", {"venue_evening"}, {"park_proximity"}),
        ("no pubs and good schools", {"venue_evening"}, {"school_primary_attainment"}),
        # And the things joined to that by "or".
        ("no pubs or bars", {"venue_evening"}, NOTHING),
        (
            "no theatres or playgrounds",
            {"culture_venues_per_homes", "play_space_proximity"},
            NOTHING,
        ),
        ("I don't care about parks or schools", {"park_proximity"}, NOTHING),
    ],
)
def test_a_word_that_turns_governs_the_thing_after_it_and_what_is_joined_to_that_by_or(
    text: str, lowered: set[str], asked: set[str]
):
    result = read(text)
    assert asked <= raised(result) and not raised(result) & lowered
    less = {e.feature_id.value for e in result.operations.weight_ops if e.direction == "less"}
    off = {
        e.feature_id.value for e in result.operations.weight_ops if e.action is WeightAction.REMOVE
    }
    assert lowered <= less | off
    assert (result.status, result.unread) == (InterpretStatus.OK, ())


@pytest.mark.parametrize(
    "text",
    [
        # The reader cannot say whether the turn reaches the bare name after it.
        "no pubs, bars",
        "no pubs and parks",
        "no parks, playgrounds or schools",
        "leafy, no station, quiet",
        "I don't care about parks, schools",
        # Nor whether what is said after the last of a list is said of each.
        "parks, playgrounds and schools are not important",
        # No word joins the two, so nothing says where one wish ends.
        "I want parks not pubs",
        "no pubs near a park",
        "I can live without pubs",
        "big no to pubs",
        "I want a place with a park that is not near pubs",
    ],
)
def test_a_turn_that_may_reach_further_makes_the_whole_prompt_not_plain(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert result.status is InterpretStatus.SUGGEST
    # Every thing it names is offered, and none is turned either way for the person.
    assert len(result.suggestions) >= 1
    assert UnmetCategory.OTHER in result.unmet


@pytest.mark.parametrize(("text", "turned_away"), TURNED_LISTS, ids=[t for t, _ in TURNED_LISTS])
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renter", "buyer"])
def test_what_is_said_after_the_last_thing_of_a_turned_list_never_begins_a_new_wish(
    text: str, turned_away: set[str], spec: PreferenceSpec
):
    # "Nearby", "on my doorstep" and "within walking distance" may be said of
    # every thing of the list. Either the turn carries, or the prompt is not plain.
    result = read(text, spec)
    assert not raised(result) & turned_away
    if result.status is InterpretStatus.OK:
        assert result.unread == ()
    else:
        assert result.operations == NO_OPERATIONS
        assert result.status is InterpretStatus.SUGGEST and result.suggestions


@pytest.mark.parametrize(
    ("text", "less", "off", "calm"),
    [
        # Joined by "or", the turn carries, whatever is said after the last thing.
        (
            "I don't want pubs or restaurants nearby",
            {"venue_evening", "venue_food_drink_per_homes"},
            (),
            (),
        ),
        (
            "no pubs or restaurants close by",
            {"venue_evening", "venue_food_drink_per_homes"},
            (),
            (),
        ),
        (
            "no pubs or lots of restaurants nearby",
            {"venue_evening", "venue_food_drink_per_homes"},
            (),
            (),
        ),
        ("somewhere without parks or pubs nearby", {"venue_evening"}, {"park_proximity"}, ()),
        ("no pubs or nightlife nearby", {"venue_evening"}, (), {"pace"}),
        ("I don't want nightlife or pubs on my doorstep", {"venue_evening"}, (), {"pace"}),
        (
            "without a park or a station within walking distance",
            (),
            {"park_proximity", "station_walk"},
            (),
        ),
    ],
)
def test_a_turn_carries_over_or_to_a_thing_with_words_after_it(
    text: str, less: set[str], off: set[str], calm: set[str]
):
    result = read(text)
    assert (result.status, result.unread, raised(result) - {"pace:low"}) == ("ok", (), set())
    weights = result.operations.weight_ops
    assert {e.feature_id.value for e in weights if e.direction == "less"} == set(less)
    assert {e.feature_id.value for e in weights if e.action is WeightAction.REMOVE} == set(off)
    assert {e.tag_id.value for e in result.operations.tag_ops if e.toward == "low"} == set(calm)
    assert len(weights) + len(result.operations.tag_ops) == result.operations.count


@pytest.mark.parametrize(
    "text",
    [
        # Joined by "and" or a comma, nobody can say whether the turn reaches it.
        "avoid pubs and restaurants nearby",
        "no pubs and a park nearby",
        "no pubs, restaurants nearby",
        # After "or" nothing begins a new wish but a turn of its own.
        "no pubs or good restaurants",
        "not near a station or near a pub",
        # What is said to count, after the last thing, may be said of each.
        "no pubs or restaurants would be good",
        "no parks or pubs are important",
        "no pubs or parks matter to me",
        # What troubles a person is read of a nuisance alone, carried or not.
        "I worry about noise or pubs",
    ],
)
def test_a_turned_list_that_may_be_read_two_ways_is_not_plain(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert result.status is InterpretStatus.SUGGEST
    assert UnmetCategory.OTHER in result.unmet
    # Whatever is offered, the direction is the person's to choose.
    for found in result.suggestions:
        assert found.choices[-1].direction == "ignore"


# --- An everyday hedge -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "asked"),
    [
        # A word of degree before a thing says how much it is wanted, and never whether.
        ("somewhere leafy and fairly quiet", {"leafy", "quiet_residential"}),
        ("quite leafy", {"leafy"}),
        ("pretty quiet", {"quiet_residential"}),
        ("reasonably quiet", {"quiet_residential"}),
        ("relatively calm", {"pace:low"}),
        ("fairly near a park", {"park_proximity"}),
        ("a fairly big park", {"parks_close_by"}),
        ("I would quite like a park", {"park_proximity"}),
        ("we'd quite like somewhere leafy", {"leafy"}),
        # Two words that cap one number cap it still.
        ("within about 30 minutes of Pellam Cross", {"journey:syn-p0012"}),
        ("up to about £1,500 a month", {"budget", "tenure:rent"}),
        ("under around £450k", {"budget", "tenure:buy"}),
        # A job the speaker has is where the speaker works.
        ("I have a job at Cindermoor Works", {"journey:syn-p0021"}),
        ("I have a job in Pellam Cross", {"journey:syn-p0012"}),
        (
            "I'm looking for somewhere leafy and fairly quiet, not too far from a decent pub",
            {"leafy", "quiet_residential", "venue_evening"},
        ),
        (
            "I have a job at Cindermoor Works. Somewhere leafy and fairly quiet, not too far "
            "from a decent pub. I can spend about £1,600 a month on a one bed flat.",
            {*("leafy", "quiet_residential", "venue_evening", "journey:syn-p0021"), "budget"},
        ),
    ],
)
def test_a_hedge_that_cannot_turn_a_wish_round_leaves_the_prompt_plain(text: str, asked: set[str]):
    # "Fairly", "quite", "pretty" and "reasonably" made a prompt a question,
    # where "a bit" and "slightly" were read. None of them can turn a wish round.
    result = read(text)
    assert (result.status, result.unread, result.suggestions) == (InterpretStatus.OK, (), ())
    assert asked <= raised(result), raised(result)
    assert apply(RENTER, result.operations, fixture_release()).rejected == ()


def test_a_wish_that_is_hedged_is_worth_what_a_mention_is():
    for text in ("fairly quiet", "quite quiet", "a bit quiet", "quiet"):
        (edit,) = read(text).operations.tag_ops
        after = apply(RENTER, read(text).operations, fixture_release()).spec
        assert [(tag.tag_id, tag.weight) for tag in after.tags] == [("quiet_residential", 0.5)]
        assert edit.step is (Step.UP_LARGE if text == "quiet" else Step.UP_SMALL)


@pytest.mark.parametrize(
    "text",
    [
        # Under a word that turns, a word of degree is more than one rule can read.
        *("not fairly quiet", "not quite leafy", "no pretty parks", "without quite so many pubs"),
        # A word of degree with nothing after it to be the degree of.
        *("fairly", "quite", "leafy, quite", "a park, fairly"),
        # A word that weakens the whole wish says whether, and not how much.
        *("maybe leafy", "ideally near a park", "leafy if possible", "probably quiet"),
        *("I think I want a park", "leafy, I suppose", "perhaps a park", "possibly quiet"),
        # The past, and someone else's job.
        *("I had a job at Cindermoor Works", "she has a job at Cindermoor Works"),
        "I have never had a job at Cindermoor Works",
    ],
)
def test_a_hedge_that_may_say_whether_a_thing_is_wanted_is_still_not_plain(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert UnmetCategory.OTHER in result.unmet and result.unread


# --- P2. Where a sentence ends ---------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "leafy, yuck",
        "leafy; yuck",
        "leafy: yuck",
        "leafy - yuck",
        "leafy \N{EM DASH} yuck",
        "leafy (yuck)",
        'leafy "yuck"',
        "yuck, leafy",
        "yuck: leafy, quiet, near a park",
    ],
)
def test_a_comma_a_colon_a_dash_a_bracket_and_a_quote_do_not_end_a_sentence(text: str):
    assert read(text).operations == NO_OPERATIONS


@pytest.mark.parametrize("mark", [". ", "! ", "? ", "\n", "\r\n", "... ", ".\n\n"])
def test_a_full_stop_a_question_mark_an_exclamation_mark_and_a_line_break_end_one(mark: str):
    # The park is a sentence of its own, in which the speaker says what they want.
    text = f"We are moving next spring{mark}I want a park"
    assert [said.known for said in sentences_of(text)] == [False, True]
    assert [said.known for said in sentences_of(f"zebra{mark}I want a park")] == [False, True]
    # One sentence that is not plain makes the prompt not plain, so nothing is
    # applied. The park is offered, and the first sentence is what was not read.
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert [found.target for found in result.suggestions] == ["feature:park_proximity"]
    assert text[result.unread[0].start : result.unread[0].end].startswith("We are moving next")


@pytest.mark.parametrize(
    "text",
    [
        "I don;t want pubs",
        "I don,t want pubs",
        "I don.t want pubs",
        "I don/t want pubs",
        "pubs:(",
        "pubs :(",
        "pubs-",
        "-pubs",
        "!pubs",
        "~pubs",
        "pubs/bars",
        "pubs.bars",
        "pubs\N{FACE WITH ROLLING EYES}",
        "pubs \N{FACE WITH ROLLING EYES}",
        "pubs \N{THUMBS DOWN SIGN}",
        "'pubs'",
        "0 pubs",
        "2 pubs",
    ],
)
def test_a_token_is_never_split_at_a_mark_inside_it(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert result.unmet == (UnmetCategory.OTHER,)


def test_a_word_written_with_a_hyphen_is_read_whole_or_not_at_all():
    for text, asked in (
        ("well-connected", "station_lines"),
        ("tree-lined streets", "leafy"),
        ("family-friendly", "family_amenities"),
        ("a 20-minute walk to Pellam Cross", "journey:syn-p0012"),
        ("a two-bed to rent", "budget"),
    ):
        assert asked in raised(read(text)), text
    for text in ("pub-free", "no-pubs", "park-less", "non-leafy", "anti-pub", "pubs-not"):
        assert read(text).operations == NO_OPERATIONS, text


@pytest.mark.parametrize(
    "text",
    [
        "I work at Foxholt (market research)",
        "I work at Foxholt, Market",
        "I work at Foxholt-Market",
        "I work at Foxholt/Market",
        'I work at "Foxholt" Market',
        "I work at Foxholt\nMarket",
        "I work at Foxholt. Market",
        "near Wexmoor (university towns bore me)",
        "only in Pellam/Cross",
        "not Lantern-Yard",
    ],
)
def test_a_name_is_never_put_together_across_a_mark_or_a_line_break(text: str):
    result = read(text)
    whole = {"journey:syn-p0019", "journey:syn-p0026", "area:syn-n0018:only"}
    assert not raised(result) & (whole | {"area:syn-n0012:exclude"})


# --- P3. A question, and a wish that is someone else's -----------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Should I avoid Cindermoor?",
        "only Wexmoor?",
        "avoid Cindermoor?",
        "a park?",
        "near a park?",
        "I want a park?",
        "renting?",
        "30 minutes to Pellam Cross?",
        "no pubs?",
        "I don't care about parks?",
        "is there a park nearby",
        "are there pubs",
        "can I have a park",
        "would I want a pub next door",
        "must I live near a station",
        "am I near a park",
    ],
)
def test_a_question_makes_no_edit(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert all(said.asked and not said.known for said in sentences_of(text, NAMES))
    # What it names is offered, and what is left of it is said not to be read.
    assert result.suggestions or result.unmet == (UnmetCategory.OTHER,)
    assert (UnmetCategory.OTHER in result.unmet) == bool(result.unread)


@pytest.mark.parametrize(
    "text",
    [
        "my mum wants a park",
        "my partner works at Pellam Infirmary",
        "he wants pubs",
        "they need a station",
        "people love pubs",
        "everyone wants a high street",
        "kids love playgrounds",
        "the kids need a playground",
        "you want pubs",
        "some work at Pellam Cross",
        "many commute to Pellam Cross",
        "some avoid Tallowgate",
        "they avoid Cindermoor",
        "lots avoid Cindermoor",
        "I wanted a park",
        "I loved pubs",
        "I worked at Pellam Infirmary",
        "I was commuting to Pellam Cross",
        "we were near a park",
    ],
)
def test_a_sentence_whose_subject_is_not_the_speaker_makes_no_edit(text: str):
    result = read(text)
    assert edits(result) == 0 and result.clarify == ()
    assert UnmetCategory.OTHER in result.unmet


# --- P4. Doubt that names nothing ------------------------------------------------------


@pytest.mark.parametrize(
    "doubt", ["No thanks.", "None of that for me.", "Not really.", "I disagree.", "Just kidding"]
)
@pytest.mark.parametrize(
    "wish",
    [
        "I want a station.",
        "Pubs, bars and restaurants.",
        "I work at Pellam Infirmary.",
        "Only in Cindermoor.",
        "I want to buy!",
        "No more than £1,500 a month.",
    ],
)
def test_a_sentence_that_holds_doubt_and_names_nothing_takes_back_what_was_raised(
    wish: str, doubt: str
):
    assert raised(read(wish))
    result = read(f"{wish} {doubt}")
    assert result.operations == NO_OPERATIONS
    assert UnmetCategory.OTHER in result.unmet
    taken_back, closing = sentences_of(f"{wish} {doubt}", NAMES, fixture_release())
    assert (taken_back.known, taken_back.taken_back) == (False, True)
    assert not closing.known


def test_doubt_that_names_nothing_is_said_of_a_list_as_far_as_the_list_goes():
    for text in (
        "Pubs. Bars. None of it.",
        "Dealbreakers:\npubs\nbars\na station",
        "Things I hate\n- pubs\n- bars",
        "No.\nPubs\nBars",
        "What I can't stand. Pubs. Bars.",
    ):
        assert read(text).operations == NO_OPERATIONS, text
        assert not any(said.known for said in sentences_of(text, NAMES, fixture_release())), text

    def known(text: str) -> list[bool]:
        return [said.known for said in sentences_of(text, NAMES, fixture_release())]

    # A sentence in which the speaker says what they want stands by itself, for a
    # caller that holds edits to each sentence. The reader applies none of these.
    assert known("I want a park. Pubs. Bars. None of it.") == [True, False, False, False]
    assert known("Things I hate. Pubs. Bars. I want a park.") == [False, False, False, True]
    # And a sentence that names something keeps its doubt to itself.
    assert known("I want a park. I can't stand pubs.") == [True, False]
    for text in (
        "I want a park. Pubs. Bars. None of it.",
        "I want a park. I can't stand pubs.",
        "I don't care about parks. Whatever.",
    ):
        assert read(text).operations == NO_OPERATIONS, text
    # Courtesy is a sentence the grammar makes, so the wish beside it is applied.
    assert raised(read("Hello. I would like a park.")) == {"park_proximity"}


# --- P5. A number that is a minimum -------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "At least 30 minutes from Pellam Cross",
        "at least 30 minutes to Pellam Cross",
        "More than 40 minutes from Pellam Cross please",
        "No less than 30 minutes from Foxholt Market",
        "not less than 30 minutes from Foxholt Market",
        "Further than 20 minutes from Foxholt Market",
        "Minimum 45 minutes from Pellam Infirmary",
        "a minimum of 45 minutes from Pellam Infirmary",
        "over 30 minutes to Pellam Cross",
        "30 minutes or more from Pellam Cross",
        "30+ minutes from Pellam Cross",
        "not within 30 minutes of Pellam Cross",
        "more than 15 minutes walk from a pub",
        "further than 5 minutes from a high street",
        "at least £2,000 a month",
        "more than £500k",
        "no less than 3 bedrooms",
        "at most 2 pubs",
        "up to 3 pubs",
        "no more than 1 pub",
    ],
)
def test_a_number_that_is_a_minimum_is_never_a_cap(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    assert UnmetCategory.OTHER in result.unmet


def test_a_campus_a_person_wants_distance_from_gets_the_notice_and_no_journey():
    result = read("At least 30 minutes from Wexmoor University")
    assert result.operations == NO_OPERATIONS
    assert (result.status, result.notice) == (
        InterpretStatus.POLICY_REDIRECT,
        Notice.NEUTRAL_PLACES,
    )


@pytest.mark.parametrize(
    ("text", "minutes", "strictness"),
    [
        ("no more than 30 minutes to Pellam Cross", 30, "hard"),
        ("at most 30 minutes to Pellam Cross", 30, "hard"),
        # Decided on 2026-09-24: "max" and "within" make a number of minutes a firm limit.
        ("within 30 minutes of Pellam Cross", 30, "hard"),
        ("max 30 minutes to Pellam Cross", 30, "hard"),
        ("30 minutes max to Pellam Cross", 30, "hard"),
        # With none of those words it stays a guide.
        ("up to 30 minutes to Pellam Cross", 30, "unchanged"),
        ("under 30 minutes to Pellam Cross", 30, "unchanged"),
        ("less than 30 minutes from Pellam Cross", 30, "unchanged"),
        ("30 minutes to Pellam Cross", 30, "unchanged"),
    ],
)
def test_a_number_that_is_the_most_is_a_cap(text: str, minutes: int, strictness: str):
    (edit,) = read(text).operations.commute_ops
    assert (edit.place_id, edit.max_minutes, edit.strictness) == ("syn-p0012", minutes, strictness)


# --- P6. To rent or to buy -------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "I'm done renting",
        "Renting is dead money",
        "I've had it up to here with renting",
        "Finally escaping the rental market",
        "Buying is out of the question",
        "I'm not looking to buy",
        "I don't want to rent",
        "renting is not for me",
        "renting? never",
        "no renting",
        "renting, sadly",
        "my landlord is selling so no more renting",
    ],
)
def test_a_word_for_renting_or_buying_sets_the_tenure_only_in_a_sentence_that_is_known(
    text: str,
):
    for spec in (RENTER, BUYER):
        result = read(text, spec)
        assert result.operations == NO_OPERATIONS
        assert apply(spec, result.operations, fixture_release()).spec == spec


def test_the_tenure_is_still_read_where_every_word_is_known():
    assert raised(read("I want to buy", RENTER)) == {"budget", "tenure:buy"}
    assert raised(read("renting", BUYER)) == {"budget", "tenure:rent"}
    assert raised(read("I want to buy, not rent")) == {"budget", "tenure:buy"}
    assert raised(read("renting, not buying")) == {"budget", "tenure:rent"}


# --- P7. A nuisance the person says they like -------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "I like noise",
        "I love noise",
        "I want noise",
        "noise",
        "noisy",
        "lots of noise",
        "more noise",
        "somewhere noisy",
        "I actually like a bit of noise",
        "I enjoy the noise and bustle of a main road",
        "I love crime",
        "crime",
        "pollution",
        "I like pollution",
        "traffic noise please",
    ],
)
def test_a_nuisance_that_is_liked_or_only_named_makes_no_edit(text: str):
    result = read(text)
    assert result.operations == NO_OPERATIONS
    # It is offered, and less of it is the one thing that can be chosen.
    assert result.status is InterpretStatus.SUGGEST
    for found in result.suggestions:
        if found.label.startswith(("Less", "Cleaner", "Away")):
            assert [choice.direction for choice in found.choices] == ["less", "ignore"]
    assert (UnmetCategory.OTHER in result.unmet) == bool(result.unread)


@pytest.mark.parametrize(
    ("text", "cared_about"),
    [
        ("less noise", "noise_exposure"),
        ("no noise", "noise_exposure"),
        ("not too noisy", "noise_exposure"),
        ("low noise", "noise_exposure"),
        ("without traffic noise", "noise_exposure"),
        ("I worry about noise", "noise_exposure"),
        ("noise matters to me", "noise_exposure"),
        ("low pollution", "air_no2"),
        ("less pollution", "air_no2"),
        ("clean air", "air_no2"),
        ("low crime", "crime_burglary_theft"),
        ("I worry about burglary", "crime_burglary_theft"),
        ("I care about crime", "crime_violence_robbery"),
        ("quiet", "quiet_residential"),
    ],
)
def test_wanting_less_of_a_nuisance_is_still_caring_about_it(text: str, cared_about: str):
    result = read(text)
    assert cared_about in raised(result)
    assert result.unmet == ()


def test_what_is_liked_beside_a_nuisance_is_offered_and_not_applied():
    result = read("I want somewhere noisy and lively")
    assert result.operations == NO_OPERATIONS
    assert [(found.target, found.label) for found in result.suggestions] == [
        ("feature:noise_exposure", "Less transport noise"),
        ("tag:pace", "Going out"),
    ]


# --- P8. Two phrases of the lexicon that overlap ------------------------------------------------


@pytest.mark.parametrize(
    ("text", "asked"),
    [
        ("good transport links", {"station_lines"}),
        ("Good transport links are a must", {"station_lines"}),
        ("great food scene", {"foodie"}),
        ("Great food scene", {"foodie"}),
        ("good primary schools", {"school_primary_attainment"}),
        ("a good high street", {"highstreet_access"}),
        ("near a station nearby", {"station_walk"}),
        ("30 minutes to Pellam Cross station", {"journey:syn-p0012"}),
        ("near Wexmoor University", {"journey:syn-p0026"}),
        ("I work in Dulcimer Green", {"journey:syn-p0004"}),
    ],
)
def test_the_reading_that_leaves_no_word_over_is_the_one_that_is_taken(text: str, asked: set[str]):
    result = read(text)
    assert raised(result) == asked
    assert result.unmet == ()


# --- P9. The words an edit rests on --------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "rests"),
    [
        ("Somewhere quiet and leafy", {("tag_ops", 0): ["quiet"], ("tag_ops", 1): ["leafy"]}),
        ("no pubs please", {("weight_ops", 0): ["no pubs"]}),
        # The words a wish is opened with are no part of what it rests on.
        ("I really want parks", {("weight_ops", 0): ["parks"]}),
        ("parks are essential", {("weight_ops", 0): ["parks are essential"]}),
        ("not far from a park", {("weight_ops", 0): ["not far from a park"]}),
        (
            "I cycle to work at Foxholt Market",
            {("commute_ops", 0): ["cycle to work at Foxholt Market"]},
        ),
        (
            "No more than 35 minutes to Pellam Cross by tube",
            {("commute_ops", 0): ["No more than 35 minutes to Pellam Cross by tube"]},
        ),
        ("not Cindermoor", {("area_ops", 0): ["not Cindermoor"]}),
        (
            "Renting a 2 bed, up to £1,500 a month",
            {("budget_ops", 0): ["Renting", "2 bed", "up to £1,500"]},
        ),
        (
            "Hello.\nI'd like a PARK",
            {("weight_ops", 0): ["a PARK"]},
        ),
    ],
)
def test_every_edit_says_which_words_of_the_text_it_rests_on(
    text: str, rests: dict[tuple[str, int], list[str]]
):
    result = read(text)
    found: dict[tuple[str, int], list[str]] = {}
    for said in result.rests_on:
        found.setdefault((said.group.value, said.index), []).append(text[said.start : said.end])
    assert found == rests


def test_every_edit_of_every_plain_sentence_rests_on_words_of_one_sentence():
    for text, _ in (*PLAINLY, *HELD_OUT):
        result = read(text)
        pointed = {(said.group, said.index) for said in result.rests_on}
        every = {
            (group, index)
            for group in OpsGroup
            for index in range(len(getattr(result.operations, group.value)))
        }
        assert pointed == every, text
        known = [(s.start, s.end) for s in sentences_of(text, NAMES) if s.known]
        for said in result.rests_on:
            assert 0 <= said.start < said.end <= len(text), text
            group = getattr(result.operations, said.group.value)
            if said.group is not OpsGroup.BUDGET or group[said.index].amount:
                assert any(a <= said.start and said.end <= b for a, b in known), text
        # It says where the words are, and never what they are.
        for said in result.rests_on:
            assert set(type(said).model_fields) == {"group", "index", "start", "end"}


def test_what_an_edit_rests_on_is_offsets_and_holds_no_word_of_the_text():
    result = read("I work at Pellam Cross and want a park")
    assert len(result.rests_on) == 2
    assert "pellam" not in result.model_dump_json().casefold()
    # And what is offered, or was not read, is offsets too. A suggestion is
    # called by the release's name for a place, and never by what was typed.
    canary = "Zqxjkvanary"
    unread = read(f"{canary}. I work at pellam cross and want a park")
    assert (unread.operations, len(unread.suggestions)) == (NO_OPERATIONS, 2)
    assert [(span.start, span.end) for span in unread.unread] == [(0, 22), (36, 46)]
    assert canary.casefold() not in unread.model_dump_json().casefold()
    assert "pellam cross" not in unread.model_dump_json()
    assert [found.label for found in unread.suggestions] == ["Pellam Cross", "Nearer a park"]


# --- The price: how many plain wishes are still read ----------------------------------------------


def met(text: str, wishes: Wishes) -> bool:
    result = read(text)
    after = apply(RENTER, result.operations, fixture_release())
    applied = {(a.group, a.index) for a in after.applied}
    kept = result.model_copy(
        update={
            "operations": result.operations.model_copy(
                update={
                    group.value: tuple(
                        edit
                        for index, edit in enumerate(getattr(result.operations, group.value))
                        if (group, index) in applied
                    )
                    for group in OpsGroup
                }
            )
        }
    )
    return all(raised(kept) & wish for wish in wishes)


def share_read(sentences: tuple[tuple[str, Wishes], ...]) -> tuple[int, list[str]]:
    declined = [text for text, wishes in sentences if not met(text, wishes)]
    return len(sentences) - len(declined), declined


def test_the_share_of_plain_wishes_that_is_read_does_not_fall_without_being_noticed():
    # Before the closed vocabulary the reader read 145 of these 170 in full, 85.3%.
    # With it, 142, 83.5%. With the grammar of a plain prompt it reads 137, 80.6%:
    # a prompt is applied whole or not at all, and a vibe answers to fewer words.
    # Of the adversary's own 90 it read 70, then 69, and then 67. Every one it
    # no longer applies is offered as a suggestion, which the person may choose.
    # With a word of degree read before a thing, "fairly", "quite", it reads
    # 138 and 68. "A garden" and "safe" are offered now and never applied,
    # which cost none of these: the one sentence that holds "safe" names low
    # crime beside it.
    # If this fails, a word was taken out of the grammar or a rule was
    # tightened: say what it cost in the change that does it, and move the floor.
    assert len(PLAINLY) == len({text for text, _ in PLAINLY}) >= 150
    read_in_full, declined = share_read(PLAINLY)
    assert read_in_full >= 138, declined
    theirs, _ = share_read(PLAINLY[:THEIRS])
    assert theirs >= 68


def test_the_share_of_sentences_the_vocabulary_was_not_settled_on_is_held_too():
    # Written after the vocabulary was settled and never used to widen it, so
    # this is the fairer measure of the price: 55 of 60 before, 91.7%, 46 with
    # the closed vocabulary, 76.7%, and 45 with the grammar, 75.0%. Do not add a
    # word to make one of these pass without the place the grammar gives it, and
    # the reason it can turn no wish round there.
    assert len(HELD_OUT) == 60
    read_in_full, declined = share_read(HELD_OUT)
    assert read_in_full >= 45, declined


# --- What is still read, for every thing and every name ------------------------------------------

PLAIN_WISHES = (
    "{thing}",
    "I want {thing}",
    "somewhere with {thing}",
    "{thing} please",
    "we would really like {thing}",
    "lots of {thing}",
    "{thing} is essential",
    "quiet and {thing}",
    "I'm looking for a place with {thing}, thanks",
)


def test_a_plain_wish_for_each_thing_is_still_read():
    tried = 0
    for phrase, target in sorted(THINGS.items()):
        if target.nuisance and not target.wanted_low:
            continue  # a nuisance that is only named is no wish the reader can read (P7)
        if target.no_end:
            continue  # the name of a scale names no end, so it is offered and not applied
        if read_into_crime(target):
            continue  # crime counts only when it is asked for by name, so it is offered
        if target.note:
            continue  # Burro has no measure of it, so what is nearest is offered
        asked = {f.value for f in target.features} | {t.value for t in target.tags}
        for template in PLAIN_WISHES:
            text = template.format(thing=phrase)
            result = read(text)
            if target.direction is DirectionChoice.LESS:
                # "Low density" says which way it is wanted, and is a wish all the same.
                (edit,) = result.operations.weight_ops
                assert (edit.feature_id.value, edit.direction) == (*asked, target.direction), text
                assert edit.action is WeightAction.SET or edit.step in UP, text
            elif target.toward is Toward.LOW:
                # "Calm" names the low end of a scale, and is a wish for that end.
                assert {f"{wanted}:low" for wanted in asked} <= raised(result), text
            else:
                assert asked <= raised(result), text
            assert result.status is InterpretStatus.OK, text
            assert UnmetCategory.OTHER not in result.unmet, text
            tried += 1
    assert tried > 1_500


def test_a_plain_journey_to_each_place_is_still_read():
    release = fixture_release()
    tried = 0
    for place in release.places:
        for name in (place.name, *place.aliases):
            for text, minutes in (
                (f"I work at {name}", 0),
                (f"30 minutes to {name}", 30),
                (f"within 25 minutes of {name} by bike", 25),
                (f"near {name}", 0),
                (f"somewhere not far from {name}", 0),
                (f"no more than 40 minutes to {name}", 40),
                (f"leafy, and I commute to {name}", 0),
            ):
                result = read(text)
                found = [(e.action, e.max_minutes) for e in result.operations.commute_ops]
                assert found == [(CommuteAction.ADD, minutes)], text
                (edit,) = result.operations.commute_ops
                assert edit.place_id == place.place_id, text
                assert result.status is InterpretStatus.OK, text
                tried += 1
    assert tried > 300


def test_a_plain_area_rule_for_each_area_is_still_read():
    release = fixture_release()
    tried = 0
    for area in release.neighbourhoods:
        for name in (area.name, *area.aliases):
            for text, action in (
                (f"only in {name}", AreaAction.ONLY),
                (f"it has to be in {name}", AreaAction.ONLY),
                (f"not {name}", AreaAction.EXCLUDE),
                (f"avoid {name}", AreaAction.EXCLUDE),
                (f"anywhere but {name}", AreaAction.EXCLUDE),
                (f"leafy, not {name} please", AreaAction.EXCLUDE),
                (f"I want to avoid {name}", AreaAction.EXCLUDE),
            ):
                result = read(text)
                assert [(e.action, e.area_id) for e in result.operations.area_ops] == [
                    (action, area.area_id)
                ], text
                assert result.operations.commute_ops == (), text
                tried += 1
    assert tried > 150


GENERIC = ["work", "the office", "my office", "school", "uni", "university", "home", "my job"]
NO_PLACE = [*GENERIC, "the city", "town", "college", "a school", "an office"]


@pytest.mark.parametrize("words", NO_PLACE)
@pytest.mark.parametrize("cue", ["I commute to", "I travel to", "I work at", "I study at"])
def test_a_generic_word_after_a_cue_for_a_place_names_no_place(cue: str, words: str):
    assert words.split()[-1] in GENERIC_PLACES
    for text in (f"{cue} {words}", f"{cue} {words} by bike", f"{cue} {words}, somewhere leafy"):
        result = read(text)
        # No edit and no question: there is nothing to choose from.
        assert result.operations == NO_OPERATIONS, text
        assert result.clarify == (), text
        assert result.status in (InterpretStatus.OK, InterpretStatus.SUGGEST), text
        assert result.notice is Notice.NONE, text
        # And the word is not offered as a wish for schools or for a campus either.
        assert [found.target for found in result.suggestions] in ([], ["tag:leafy"]), text


def test_words_given_as_the_name_of_a_place_that_are_the_name_of_none_are_asked_about():
    known = small_release()

    def asked(text: str) -> InterpretResult:
        return READER.interpret(InterpretRequest(text=text, spec=RENTER, release=known))

    found = asked("I work at Wexmoor University")
    assert [e.place_id for e in found.operations.commute_ops] == ["syn-p0003"]
    for text in ("I work at Nowhereville", "30 minutes to Nowhereville", "I work at Pellam"):
        result = asked(text)
        assert result.status is InterpretStatus.CLARIFY, text
        # A question adds nothing: the edit carries no place, and the reducer turns it away.
        assert [e.place_id for e in result.operations.commute_ops] == [""], text
        assert apply(RENTER, result.operations, known).spec == RENTER, text
    # It is asked only where a name was expected, and where nothing else is said after it.
    for text in (
        "near Nowhereville",
        "not Nowhereville",
        "only in Nowhereville",
        "I work at Nowhereville sadly no more",
        "20 minutes from the nearest bar",
        "I don't work at Nowhereville",
        "my ex works at Nowhereville",
    ):
        result = asked(text)
        assert result.clarify == () and result.operations == NO_OPERATIONS, text


def test_the_campus_of_the_release_is_a_university():
    kinds = {p.name: p.kind for p in fixture_release().places}
    assert kinds["Wexmoor University"] is PlaceKind.UNIVERSITY


# --- For a caller that holds edits the reader did not make --------------------------------


def test_the_reader_says_of_each_sentence_whether_it_read_it():
    text = "Quiet and leafy. No pubs! A proper brunch, near a park. I don;t want a station?"
    found = sentences_of(text, NAMES, fixture_release())
    assert [text[s.start : s.end] for s in found] == [
        "Quiet and leafy",
        "No pubs",
        "A proper brunch, near a park",
        "I don;t want a station",
    ]
    assert [(s.known, s.turning, s.doubt, s.asked) for s in found] == [
        (True, False, False, False),
        (True, True, False, False),
        (False, False, False, False),
        (False, False, True, True),
    ]
    # One sentence of it is not plain, so the reader applies none of it.
    assert read(text).operations == NO_OPERATIONS
    # Every edit the reader makes rests on words of a sentence it knows.
    plain = "Quiet and leafy. No pubs! Near a park."
    result = read(plain)
    known = [(s.start, s.end) for s in sentences_of(plain, NAMES, fixture_release()) if s.known]
    assert len(known) == 3 and len(result.rests_on) == 4
    for said in result.rests_on:
        assert any(start <= said.start and said.end <= end for start, end in known)


def test_the_written_list_of_doubt_is_heard_in_a_sentence_the_reader_does_not_read():
    for text in (
        "anything but leafy",
        "a park would be a nightmare",
        "I hate pubs",
        "pubs? never",
        "I used to like pubs",
        "pubs \N{THUMBS DOWN SIGN}",
        "I don;t want pubs",
    ):
        assert any(s.doubt for s in sentences_of(text)), text
        assert read(text).operations == NO_OPERATIONS, text
    for text in ("a proper brunch near a park", "somewhere leafy", "I work at Pellam Cross"):
        assert not any(s.doubt for s in sentences_of(text)), text
    # The words a caller is given to look for, beside its own reading.
    assert {"hate", "never", "no", "not", "without", "worry about"} <= SIGNS_OF_DOUBT
