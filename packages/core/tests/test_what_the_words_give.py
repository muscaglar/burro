"""What core holds for whoever marks the way the words give of a thing that is only offered.

The reader applies a prompt only when the whole of it is plain, and of any
other it offers what it noticed. A client that takes what is offered and asks
nothing needs to be told which way the words give, and the service says so by
the reader's own reading of each sentence (contract, section 8.2). Core holds
four lists of words for it, and one rule of what a sentence takes back. None
is a word of the grammar: a prompt that holds one is still not plain, and
nothing of it is applied.

Every sentence here is made up.
"""

import pytest
from burro_core.grammar import MUST_BE_READ, VOCABULARY, Grammar
from burro_core.ids import Tenure
from burro_core.interpret import (
    SIGNS_OF_DOUBT,
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    known_in,
    taken_back_in,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.places import Names
from burro_core.spec import default_spec
from burro_core.vocabulary import (
    ASIDES,
    CANNOT_BEAR,
    CARRIES_A_TURN,
    DREADS,
    GIVES_A_REASON,
    HEADS_WHAT_IS_WANTED,
    JOINS,
    LEADS_IN_A_WISH,
    LEADS_IN_WHAT_IS_SAID_NEXT,
    OPENS_A_HEADING,
    PHRASES_OF_DOUBT,
    SAYS_HOW_LONG,
    TURNS_NOTHING,
    TURNS_WHERE_IT_STANDS_ALONE,
    WHO_ELSE,
    WORDS_OF_DOUBT,
    WORDS_THAT_TURN_AWAY,
)

from .support import fixture_release

RENTER = default_spec(Tenure.RENT)
READER = RuleInterpreter()
GRAMMAR = Grammar(Names(fixture_release()), fixture_release())
# Every word that turns a wish, puts it in doubt or gives it to somebody else.
IN_DOUBT = SIGNS_OF_DOUBT | WORDS_OF_DOUBT | WORDS_THAT_TURN_AWAY | MUST_BE_READ | DREADS | WHO_ELSE


def request(text: str) -> InterpretRequest:
    return InterpretRequest(text=text, spec=RENTER, release=fixture_release())


def read(text: str) -> InterpretResult:
    return READER.interpret(request(text))


def wishes(result: InterpretResult) -> list[str]:
    edits = result.operations
    return [
        *(edit.feature_id.value for edit in edits.weight_ops),
        *(edit.tag_id.value for edit in edits.tag_ops),
    ]


def known(text: str) -> list[str]:
    """The sentences of a text that the reader reads, each by itself."""
    return [text[span.start : span.end] for span in known_in(text, GRAMMAR)]


# --- What is said of one's own words --------------------------------------------------------


def test_no_aside_turns_a_wish_asks_compares_or_names_anybody_but_the_speaker():
    assert len(ASIDES) == 16
    words = {word for aside in ASIDES for word in aside.split()}

    assert not ASIDES & IN_DOUBT
    # "If" leads a clause in, "if possible", and is a sign of no doubt there.
    assert words & IN_DOUBT <= {"if"}
    for never in ("maybe", "perhaps", "probably", "not", "no", "never", "but", "you", "they"):
        assert never not in words


@pytest.mark.parametrize("aside", sorted(ASIDES))
def test_a_prompt_that_holds_an_aside_is_not_plain_and_nothing_of_it_is_applied(aside: str):
    for text in (f"{aside}, leafy and quiet", f"leafy and quiet, {aside}"):
        found = read(text)
        assert found.operations == NO_OPERATIONS, text
        assert {offer.target for offer in found.suggestions} >= {"tag:leafy"}, text


# --- What carries a turn on, and what heads a wish ------------------------------------------


def test_what_carries_a_turn_on_is_a_word_that_turns_and_never_a_plain_one():
    assert frozenset({"nor", "than"}) == CARRIES_A_TURN
    assert CARRIES_A_TURN <= WORDS_THAT_TURN_AWAY
    assert not CARRIES_A_TURN & VOCABULARY


def test_what_heads_a_list_of_wishes_holds_no_word_of_doubt():
    assert not HEADS_WHAT_IS_WANTED & IN_DOUBT - {"wants", "needs", "likes"}
    # Each is the third person of a wish, which says whose wish it is only where
    # somebody stands straight before it: "Wants: a park" is the heading of a list.
    assert {"wants", "needs", "likes"} <= HEADS_WHAT_IS_WANTED
    for heading in ("dealbreakers", "cons", "avoid", "negatives", "red flags", "turn offs"):
        assert heading not in HEADS_WHAT_IS_WANTED


@pytest.mark.parametrize("heading", sorted(HEADS_WHAT_IS_WANTED))
def test_a_prompt_under_a_heading_is_not_plain_whatever_the_heading(heading: str):
    found = read(f"{heading}: a park, a station")

    assert found.operations == NO_OPERATIONS
    assert {offer.target for offer in found.suggestions} >= {"feature:park_proximity"}


def test_what_a_person_cannot_bear_is_dreaded_or_turns_firmly_and_is_no_bare_turn():
    assert CANNOT_BEAR <= DREADS | WORDS_THAT_TURN_AWAY | SIGNS_OF_DOUBT
    assert {"hate", "cant stand", "avoid", "dont want"} <= CANNOT_BEAR
    # A word that turns and says no more of what heads nothing: "Not sure where to begin".
    assert not CANNOT_BEAR & {"no", "not", "never", "without", "none"}


# --- What a sentence that names nothing takes back -------------------------------------------


@pytest.mark.parametrize("doubt", ["No thanks.", "None of that for me.", "Not really."])
def test_a_sentence_that_holds_a_word_of_doubt_takes_back_the_one_before_it(doubt: str):
    text = f"I want a station. {doubt}"

    assert known(text) == []
    assert wishes(READER.by_sentence(request(text), listed=True)) == []


@pytest.mark.parametrize(
    "beside", ["QuorvexMib TandleFrosk.", "Moving next month.", "It is for work.", "I disagree."]
)
def test_a_sentence_of_words_that_core_does_not_list_takes_nothing_back(beside: str):
    for text in (f"I want a station. {beside}", f"{beside} I want a station."):
        assert known(text) == ["I want a station"], text
        assert wishes(READER.by_sentence(request(text), listed=True)) == ["station_walk"], text


def test_the_reader_applies_nothing_of_a_prompt_that_holds_such_a_sentence_all_the_same():
    for text in ("I want a station. QuorvexMib TandleFrosk.", "I want a station. I disagree."):
        assert read(text).operations == NO_OPERATIONS
        # Held to the reader's own rule, the sentence beside it takes it back.
        assert wishes(READER.by_sentence(request(text))) == []


@pytest.mark.parametrize(
    ("text", "read_of_it"),
    [
        ("Dealbreakers:\npubs\na station", []),
        ("Things I hate\n- pubs\n- a station", []),
        ("No.\nPubs\nA station", []),
        # A heading of words that are not known, which ends in no colon, heads nothing.
        ("Requirements\npubs\na station", ["pubs", "a station"]),
        # A wish of the speaker's own stands by itself, whatever heads the list.
        ("Dealbreakers:\npubs\nI want a station", ["I want a station"]),
    ],
)
def test_what_is_listed_under_a_heading_is_headed_by_it(text: str, read_of_it: list[str]):
    assert known(text) == read_of_it


def taken_back(text: str) -> list[str]:
    """The sentences of a text that a sentence beside them takes back, or heads."""
    return [text[span.start : span.end] for span in taken_back_in(text, GRAMMAR)]


def test_a_sentence_is_taken_back_whether_or_not_the_reader_reads_it():
    # The reader reads the first of these and not the second, and each is taken back.
    for wish in ("I want a station", "A good pub within stumbling distance"):
        assert taken_back(f"{wish}. Actually no, scrap that.") == [wish]
        assert taken_back(f"{wish}. Moving next month.") == []
    assert known("I want a station. Moving next month.") == ["I want a station"]
    assert known("A good pub within stumbling distance. Moving next month.") == []
    assert taken_back("Things I hate\n- pubs\n- a station") == ["pubs", "a station"]
    assert taken_back("Requirements\npubs\na station") == []


# --- Where what is said next begins -----------------------------------------------------------


def test_what_begins_what_is_said_next_turns_nothing_and_puts_nothing_in_doubt():
    assert frozenset({"and", "but", "so", "plus", "also"}) == LEADS_IN_A_WISH
    assert LEADS_IN_A_WISH | {"or"} == LEADS_IN_WHAT_IS_SAID_NEXT
    assert frozenset({"because"}) == GIVES_A_REASON
    begins = LEADS_IN_WHAT_IS_SAID_NEXT | GIVES_A_REASON
    assert not begins & IN_DOUBT
    # Each leads in words that are said next. A word that says when or how much is as
    # often part of what is said of the thing before it, and begins nothing.
    for never in ("as", "since", "while", "though", "than", "with", "if", "unless"):
        assert never not in begins


def test_or_leads_in_no_wish_since_it_carries_a_turn():
    assert "or" in JOINS.words and "or" not in LEADS_IN_A_WISH


@pytest.mark.parametrize(
    "text",
    [
        "I don't want pubs or need a station",
        "I don't need a station or want pubs nearby",
        "no pubs or want a station",
        "I don't like parks or love pubs",
    ],
)
def test_a_wish_with_no_speaker_begins_nothing_after_or_where_a_turn_is_carried(text: str):
    found = read(text)

    # Nobody can say from the words of the grammar whether the turn reaches it.
    assert found.operations == NO_OPERATIONS
    assert found.suggestions


@pytest.mark.parametrize(
    ("text", "asked"),
    [
        # A turn of its own, the speaker, and "and" or "but" each begin a new wish.
        ("I don't want pubs and need a station", ["venue_evening_per_homes", "station_walk"]),
        ("I don't want pubs but need a station", ["venue_evening_per_homes", "station_walk"]),
        ("I don't want pubs or I need a station", ["venue_evening_per_homes", "station_walk"]),
        # Where no turn is carried, a wish after "or" is a wish.
        ("I want a park or need a station", ["park_proximity", "station_walk"]),
        ("I rent and want a park", ["park_proximity"]),
    ],
)
def test_a_wish_with_no_speaker_is_read_as_it_was_anywhere_else(text: str, asked: list[str]):
    assert wishes(read(text)) == asked


# --- What holds a word that turns, and turns nothing -------------------------------------------


def test_what_turns_nothing_holds_a_word_that_turns_and_is_no_word_of_the_grammar():
    assert frozenset({"a few", "quite a few", "a little", "nothing but"}) == TURNS_NOTHING
    turns = WORDS_THAT_TURN_AWAY | PHRASES_OF_DOUBT
    for phrase in TURNS_NOTHING:
        assert phrase in turns or set(phrase.split()) & turns, phrase
        assert phrase not in VOCABULARY, phrase
    # What says few, none or not at all is never among them.
    for never in ("few", "little", "nothing", "anything but", "all but", "not a few"):
        assert never not in TURNS_NOTHING


def test_what_turns_where_it_stands_alone_is_no_word_of_doubt_and_no_word_of_the_grammar():
    assert frozenset({"pass", "hard pass"}) == TURNS_WHERE_IT_STANDS_ALONE
    # Among other words each says something else, "a park I pass on my way to work", so
    # none is doubt wherever it stands. "Pass on" is, and is listed as a phrase.
    assert not TURNS_WHERE_IT_STANDS_ALONE & (IN_DOUBT | DREADS | VOCABULARY)
    assert "pass on" in PHRASES_OF_DOUBT
    for text in ("pubs, pass", "pubs, hard pass", "a park I pass on my way to work"):
        assert read(text).operations == NO_OPERATIONS, text


@pytest.mark.parametrize("phrase", sorted(TURNS_NOTHING))
def test_a_prompt_that_holds_such_words_is_not_plain_and_nothing_of_it_is_applied(phrase: str):
    found = read(f"{phrase} parks")

    assert found.operations == NO_OPERATIONS
    assert {offer.target for offer in found.suggestions} == {"feature:park_proximity"}


# --- What opens a heading, and what a heading says of the words under it ------------------------


def test_what_opens_a_heading_and_what_says_how_long_say_nothing_of_a_wish():
    assert frozenset({"what", "things", "the things"}) == OPENS_A_HEADING
    assert len(SAYS_HOW_LONG) == 5
    words = {word for phrase in SAYS_HOW_LONG for word in phrase.split()}
    assert not SAYS_HOW_LONG & IN_DOUBT and not words & IN_DOUBT
    # "What" asks anywhere else, and is a sign of doubt there.
    assert {"what"} == OPENS_A_HEADING & IN_DOUBT
    assert not (OPENS_A_HEADING | SAYS_HOW_LONG) & (HEADS_WHAT_IS_WANTED | ASIDES)


@pytest.mark.parametrize("heading", ["What I want", "Things I care about", *sorted(SAYS_HOW_LONG)])
def test_a_prompt_under_such_a_heading_is_not_plain_and_nothing_of_it_is_applied(heading: str):
    found = read(f"{heading}: a park, a station")

    assert found.operations == NO_OPERATIONS
    assert {offer.target for offer in found.suggestions} >= {"feature:park_proximity"}
