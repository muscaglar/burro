"""The reader reads a sentence only when it knows every token in it.

Listing the words that turn a wish round did not work: English has too many,
and people mistype them. So the rule is the other way round. The reader keeps
the list of what it knows, and a sentence that holds anything else makes no
edit. These tests hold it to that three ways: by the sentences that went
wrong, by sentences made of every thing beside words it does not know, and by
the share of plain wishes it still reads, which is the price.
"""

from collections.abc import Iterator

import pytest
from burro_core import vocabulary
from burro_core.ids import (
    AreaAction,
    CommuteAction,
    DirectionChoice,
    InterpretStatus,
    Notice,
    OpsGroup,
    PlaceKind,
    Step,
    Tenure,
    TenureChoice,
    UnmetCategory,
    WeightAction,
)
from burro_core.interpret import (
    GENERIC_PLACES,
    LEXICON,
    POLICY_LEXICON,
    VOCABULARY,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    clauses_of,
    sentences_of,
    signs_of_doubt,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.places import Names, normalise
from burro_core.reducer import apply
from burro_core.spec import PreferenceSpec, default_spec
from burro_core.vocabulary import PLAIN, PLAIN_PHRASES, PLAIN_WORDS, WORDS_OF_DOUBT

from .sentences import HELD_OUT, REVERSED, THEIRS, UNASKED, UNKNOWN_WORDS, Wishes
from .sentences import PLAIN as PLAINLY
from .support import fixture_release, small_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)
READER = RuleInterpreter()
NAMES = Names(fixture_release())
UP = (Step.UP_SMALL, Step.UP_LARGE)


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
            found.add(tag.tag_id.value)
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


def test_every_plain_word_is_written_down_once_with_why_it_is_safe():
    listed = [word for group in PLAIN for word in group.words]
    assert len(listed) == len(set(listed)) == len(PLAIN_WORDS)
    for group in PLAIN:
        assert len(group.why) > 20 and group.why.endswith(".")
        for word in group.words:
            assert word == word.lower().strip() and " " not in word, word
    for phrase in PLAIN_PHRASES:
        assert " " in phrase and phrase == phrase.lower().strip(), phrase


def test_the_list_of_plain_words_is_short_and_is_reviewed_as_a_whole():
    # Adding a word is the only way to widen what the reader reads, so the
    # number is held here. Change it in the same change that adds the word,
    # with the reason the word can never turn a wish round.
    assert len(PLAIN_WORDS) == 128
    assert len(PLAIN_PHRASES) == 34
    assert len(VOCABULARY) < 420


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
    apart = {word for phrase in PLAIN_PHRASES for word in phrase.split()} - PLAIN_WORDS
    alone = {"foot", "distance", "short", "easy", "well", "thank", "kids", "dog", "door", "get"}
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
    assert not ruled & PLAIN_PHRASES
    assert {"no", "not", "without", "less", "fewer", "avoid", "only", "at most"} <= ruled
    assert {"up to", "under", "within", "no more than"} <= vocabulary.CAPS | ruled
    assert "more" in vocabulary.SMALL_STEP
    # A number that is a minimum is no word of the reader's at all.
    for minimum in ("at least", "more than", "no less than", "further than", "minimum", "over"):
        assert minimum not in VOCABULARY, minimum


def test_the_words_that_are_not_known_are_many_and_none_is_in_the_vocabulary():
    assert len(UNKNOWN_WORDS) == len(set(UNKNOWN_WORDS)) >= 500
    known = {word for phrase in (*VOCABULARY, *LEXICON, *POLICY_LEXICON) for word in phrase.split()}
    assert not known & set(UNKNOWN_WORDS)
    assert not GENERIC_PLACES & set(UNKNOWN_WORDS)
    for must in ("hate", "yuck", "don;t", "dint", "donut", "mum", "stalker", "was", "should"):
        assert must in UNKNOWN_WORDS, must


# --- The sentences that went wrong ---------------------------------------------------

# What a sentence of the adversary's does ask for, in plain words, beside what it does not.
ASKED_FOR = {"I want somewhere noisy and lively": {"buzzy"}}


@pytest.mark.parametrize("text", REVERSED)
@pytest.mark.parametrize("spec", [RENTER, BUYER], ids=["renter", "buyer"])
def test_a_sentence_that_was_read_backwards_raises_nothing(text: str, spec: PreferenceSpec):
    result = read(text, spec)
    assert raised(result) == ASKED_FOR.get(text, set())
    assert result.clarify == ()
    # It says that it did not read it, or that it is about who lives somewhere,
    # or it read the whole of it as a wish for less: "no pubs or loads of restaurants".
    less = [e for e in result.operations.weight_ops if e.direction is DirectionChoice.LESS]
    told = UnmetCategory.OTHER in result.unmet or result.notice is Notice.NEUTRAL_PLACES
    assert told or (less and len(less) == result.operations.count)
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
    things, names = sorted(LEXICON), names_of_the_release()
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
    for row, thing in enumerate(sorted(LEXICON)):
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
    for thing in LEXICON:
        assert any(thing in text for text in sample), thing
    for name in names_of_the_release():
        assert any(name in text for text in sample), name
    assert held_to_the_promise(iter(sample)) == len(sample)


@pytest.mark.full
def test_every_word_that_is_not_known_in_every_place_makes_the_sentence_unread():
    assert held_to_the_promise(every_sentence()) > 40_000


def test_a_sentence_with_an_unknown_word_reports_one_unmet_request_of_kind_other():
    for text in ("a park for the zebra", "leafy, quiet, zebra", "zebra near Pellam Cross"):
        result = read(text)
        assert result.operations == NO_OPERATIONS
        assert result.unmet == (UnmetCategory.OTHER,)
        assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE)


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
        ("I want parks not pubs", {"venue_evening"}, {"park_proximity"}),
        ("leafy, not near a station", {"station_walk"}, {"leafy"}),
        ("no pubs, but a park nearby", {"venue_evening"}, {"park_proximity"}),
        ("no pubs, I want parks", {"venue_evening"}, {"park_proximity"}),
        ("no pubs near a park", {"venue_evening"}, NOTHING),
        ("no parks, playgrounds or schools", NOTHING, NOTHING),
        ("no pubs, bars", {"venue_evening"}, NOTHING),
        ("leafy, no station, quiet", {"station_walk"}, {"leafy"}),
        ("I can live without pubs", {"venue_evening"}, NOTHING),
        ("big no to pubs", {"venue_evening"}, NOTHING),
        ("I want a place with a park that is not near pubs", {"venue_evening"}, {"park_proximity"}),
    ],
)
def test_a_word_that_turns_governs_the_first_thing_after_it_and_no_more(
    text: str, lowered: set[str], asked: set[str]
):
    result = read(text)
    assert raised(result) == asked
    less = {e.feature_id.value for e in result.operations.weight_ops if e.direction == "less"}
    off = {
        e.feature_id.value for e in result.operations.weight_ops if e.action is WeightAction.REMOVE
    }
    assert lowered <= less | off


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
    result = read(f"We are moving next spring{mark}I want a park")
    assert raised(result) == {"park_proximity"}
    assert [text.known for text in sentences_of(f"zebra{mark}I want a park")] == [False, True]


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
    assert result.unmet == (UnmetCategory.OTHER,)


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
    assert not sentences_of(f"{wish} {doubt}")[0].known


def test_doubt_that_names_nothing_is_said_of_a_list_as_far_as_the_list_goes():
    for text in (
        "Pubs. Bars. None of it.",
        "Dealbreakers:\npubs\nbars\na station",
        "Things I hate\n- pubs\n- bars",
        "No.\nPubs\nBars",
        "What I can't stand. Pubs. Bars.",
    ):
        assert read(text).operations == NO_OPERATIONS, text
    # A sentence in which the speaker says what they want stands by itself.
    assert raised(read("I want a park. Pubs. Bars. None of it.")) == {"park_proximity"}
    assert raised(read("Things I hate. Pubs. Bars. I want a park.")) == {"park_proximity"}
    assert raised(read("Hello. I would like a park.")) == {"park_proximity"}
    # And a sentence that names something keeps its doubt to itself.
    assert raised(read("I want a park. I can't stand pubs.")) == {"park_proximity"}
    # What was lowered is not taken back: only what was raised.
    lowered = read("I don't care about parks. Whatever.").operations.weight_ops
    assert [edit.action for edit in lowered] == [WeightAction.REMOVE]


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
        ("up to 30 minutes to Pellam Cross", 30, "unchanged"),
        ("under 30 minutes to Pellam Cross", 30, "unchanged"),
        ("within 30 minutes of Pellam Cross", 30, "unchanged"),
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
    assert result.unmet == (UnmetCategory.OTHER,)


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


def test_what_is_liked_beside_a_nuisance_is_still_read():
    assert raised(read("I want somewhere noisy and lively")) == {"buzzy"}


# --- P8. Two phrases of the lexicon that overlap ------------------------------------------------


@pytest.mark.parametrize(
    ("text", "asked"),
    [
        ("good transport links", {"station_lines"}),
        ("Good transport links are a must", {"station_lines"}),
        ("great food scene", {"foodie"}),
        ("Great food scene", {"foodie"}),
        ("good primary schools", {"school_primary_attainment"}),
        ("a good high street", {"strong_high_street"}),
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
        ("I really want parks", {("weight_ops", 0): ["really want parks"]}),
        ("parks are essential", {("weight_ops", 0): ["parks are essential"]}),
        ("not far from a park", {("weight_ops", 0): ["not far from a park"]}),
        (
            "I cycle to work at Foxholt Market",
            {("commute_ops", 0): ["work at Foxholt Market"]},
        ),
        (
            "No more than 35 minutes to Pellam Cross by tube",
            {("commute_ops", 0): ["No more than 35 minutes to Pellam Cross", "tube"]},
        ),
        ("not Cindermoor", {("area_ops", 0): ["not Cindermoor"]}),
        (
            "Renting a 2 bed, up to £1,500 a month",
            {("budget_ops", 0): ["Renting", "2 bed", "up to £1,500"]},
        ),
        (
            "\N{GRINNING FACE} hello.\nI'd like a PARK",
            {("weight_ops", 0): ["PARK"]},
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
    canary = "Zqxjkvanary"
    result = read(f"{canary}. I work at Pellam Cross and want a park")
    assert len(result.rests_on) == 2
    assert canary.casefold() not in result.model_dump_json().casefold()
    assert "pellam" not in result.model_dump_json().casefold()


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
    # It now reads 142, 83.5%. Of the adversary's own 90 it read 70 and reads 69.
    # If this fails, a word was taken out of the vocabulary or a rule was
    # tightened: say what it cost in the change that does it, and move the floor.
    assert len(PLAINLY) == len({text for text, _ in PLAINLY}) >= 150
    read_in_full, declined = share_read(PLAINLY)
    assert read_in_full >= 142, declined
    theirs, _ = share_read(PLAINLY[:THEIRS])
    assert theirs >= 69


def test_the_share_of_sentences_the_vocabulary_was_not_settled_on_is_held_too():
    # Written after the vocabulary was settled and never used to widen it, so
    # this is the fairer measure of the price: 55 of 60 before, 91.7%, and 46
    # after, 76.7%. Do not add a word to make one of these pass without the
    # reason the word can never turn a wish round.
    assert len(HELD_OUT) == 60
    read_in_full, declined = share_read(HELD_OUT)
    assert read_in_full >= 46, declined


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
    for phrase, target in sorted(LEXICON.items()):
        if target.nuisance and not target.wanted_low:
            continue  # a nuisance that is only named is no wish the reader can read (P7)
        asked = {f.value for f in target.features} | {t.value for t in target.tags}
        for template in PLAIN_WISHES:
            text = template.format(thing=phrase)
            result = read(text)
            if target.direction is DirectionChoice.LESS:
                # "Low density" says which way it is wanted, and is a wish all the same.
                (edit,) = result.operations.weight_ops
                assert (edit.feature_id.value, edit.direction) == (*asked, target.direction), text
                assert edit.action is WeightAction.SET or edit.step in UP, text
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
        assert result.operations.commute_ops == (), text
        assert result.clarify == (), text
        assert (result.status, result.notice) == (InterpretStatus.OK, Notice.NONE), text
        # And the word is not read as a wish for schools or for a campus either.
        assert not result.operations.weight_ops, text
        assert [e.tag_id.value for e in result.operations.tag_ops] in ([], ["leafy"]), text


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
    # Every edit the reader made rests on words of a sentence it knows.
    result = read(text)
    known = [(s.start, s.end) for s in found if s.known]
    assert result.rests_on
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
        assert signs_of_doubt(text), text
        assert any(clause.doubtful for clause in clauses_of(text)), text
        assert any(s.doubt for s in sentences_of(text)), text
    for text in ("a proper brunch near a park", "somewhere leafy", "I work at Pellam Cross"):
        assert signs_of_doubt(text) == (), text
        assert not any(clause.doubtful for clause in clauses_of(text)), text
