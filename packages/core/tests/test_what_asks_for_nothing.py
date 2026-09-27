"""Words that ask for nothing are not said to be unread.

The reader says where the words stand that it made nothing of, so that a person
sees what was missed. Seen in a browser: after a sentence of thirteen things the
page said "Some of your words were not read", and marked "I want to live
somewhere". A person reads that as something Burro missed. How a wish is led in
to is no wish, so a stretch that holds nothing else is left out of what is said
to be unread. Nothing is guessed at: a word that is on none of core's lists is
unread wherever nothing was made of it, with the whole of the stretch it stands in.

What a person says of their own words is no wish either: "honestly", "I think".
Since 2026-09-27 a part of a sentence that is the whole of such a phrase, set
apart by a mark, asks for nothing. "Somewhere cheap, I think" was answered as
"somewhere cheap" is, but that the person was told that "I think" was not read.
"""

import pytest
from burro_core.grammar import ASKS_NOTHING
from burro_core.ids import InterpretStatus, Tenure, UnmetCategory
from burro_core.interpret import (
    InterpretRequest,
    InterpretResult,
    RuleInterpreter,
    asks_for_nothing,
)
from burro_core.ops import NO_OPERATIONS
from burro_core.spec import default_spec
from burro_core.vocabulary import (
    ASIDES,
    CAPS_FIRMLY,
    DREADS,
    ESSENTIAL,
    IMPORTANT,
    LARGE_STEP,
    PHRASES_OF_DOUBT,
    SMALL_STEP,
    STRENGTHENS,
    TAKES_OFF,
    TAKES_OFF_AFTER,
    TROUBLES,
    TURNS_DOWN,
    TURNS_DOWN_AFTER,
    TURNS_FIRMLY,
    TURNS_SOFTLY,
    WHO_ELSE,
    WISH,
    WISHES_OF_ANOTHER,
    WORDS_OF_DOUBT,
)

from .support import small_release

READER = RuleInterpreter()
# A sentence as a person would say it, of thirteen things, with a place of the made-up city.
AS_SAID = (
    "I want to live somewhere quiet, with access to parks, slightly affluent but with some "
    "culture around it, something with a real identity. At most 35-40min commute from "
    "Pellam Cross. If I'm renting, max £1,900 a month for a 1 bed flat."
)


def read(text: str) -> InterpretResult:
    request = InterpretRequest(text=text, spec=default_spec(Tenure.RENT), release=small_release())
    return READER.interpret(request)


def unread(text: str) -> list[str]:
    """The words that are said to be unread, cut from the text by where they stand."""
    return [text[span.start : span.end] for span in read(text).unread]


def left_out(text: str) -> list[str]:
    """The words nothing was made of that ask for nothing, which are not said to be unread."""
    return [text[span.start : span.end] for span in read(text).asks_nothing]


def test_how_a_wish_is_led_in_to_is_not_said_to_be_unread():
    result = read(AS_SAID)
    assert (result.status, result.operations) == (InterpretStatus.SUGGEST, NO_OPERATIONS)
    assert len(result.suggestions) > 10
    assert result.unread == ()
    # Nothing was made of these, and none of them asks for anything.
    assert left_out(AS_SAID) == [
        "I want to live somewhere",
        "with access to",
        "but with some",
        "around it, something with",
        "If I'm",
        "for",
    ]


@pytest.mark.parametrize(
    ("text", "said", "not_said"),
    [
        (
            "I want to live somewhere quiet with a lido",
            ["with a lido"],
            ["I want to live somewhere"],
        ),
        ("a park for the zebra", ["for the zebra"], ["a"]),
        ("I want a park, maybe", ["maybe"], ["I want a"]),
        (
            "I'd like somewhere leafy, not too far from a station, if you can",
            ["if you can"],
            ["I'd like somewhere", "not too far from a"],
        ),
        (
            "we're looking for somewhere with a park that is not busy",
            ["that is not busy"],
            ["we're looking for somewhere with a"],
        ),
    ],
)
def test_a_word_that_is_on_no_list_is_still_said_to_be_unread_with_the_stretch_it_stands_in(
    text: str, said: list[str], not_said: list[str]
):
    # A stretch is left out whole or not at all: none is cut to the word that is not known.
    assert (unread(text), left_out(text)) == (said, not_said)


@pytest.mark.parametrize(
    ("text", "said"),
    [
        # It compares, and says that pubs are not needed at all.
        ("I need pubs like I need noise", ["like I need"]),
        # It is somebody else's wish.
        ("some want pubs", ["some want"]),
        ("my love of pubs is low", ["my love of", "is low"]),
    ],
)
def test_a_wish_asks_for_nothing_only_where_it_stands_straight_after_the_speaker(
    text: str, said: list[str]
):
    assert unread(text) == said
    assert asks_for_nothing("I want") and asks_for_nothing("we'd love")
    # As a search is typed, to be looking for a thing is a wish with no speaker.
    assert asks_for_nothing("I am looking for") and asks_for_nothing("looking for")
    for wish in WISH.words:
        assert asks_for_nothing(f"we {wish}"), wish
        if "looking" not in wish:
            assert not asks_for_nothing(wish), wish
            assert not asks_for_nothing(f"pubs {wish}"), wish


def test_no_word_that_turns_weakens_compares_or_says_how_much_asks_for_nothing():
    never = (
        TURNS_FIRMLY
        | TURNS_SOFTLY
        | TAKES_OFF
        | TAKES_OFF_AFTER
        | TURNS_DOWN
        | TURNS_DOWN_AFTER
        | TROUBLES
        | CAPS_FIRMLY
        | SMALL_STEP
        | LARGE_STEP
        | ESSENTIAL
        | STRENGTHENS.words
        | IMPORTANT.words
        | DREADS
        | WHO_ELSE
        | WISHES_OF_ANOTHER
        | WORDS_OF_DOUBT
        | PHRASES_OF_DOUBT
    )
    assert not ASKS_NOTHING & never
    for words in sorted(never):
        assert not asks_for_nothing(words), words
        assert not asks_for_nothing(f"I want {words} a"), words
    # "Not far from" is near, and is one phrase. Part of it is a word that turns.
    assert asks_for_nothing("not far from") and not asks_for_nothing("not far")


@pytest.mark.parametrize(
    "words",
    [
        "zebra",
        "I want a zebra",
        "to",
        "want",
        "that, is",
        "to. live",
        "somewhere-ish",
        "\N{LEFT DOUBLE QUOTATION MARK}somewhere\N{RIGHT DOUBLE QUOTATION MARK}",
        "1500",
    ],
)
def test_what_core_does_not_place_asks_for_something_as_far_as_anyone_can_say(words: str):
    # A word that is on no list, a wish with no speaker, a phrase put together across a
    # mark or the end of a sentence, a token with a mark inside it, and a number.
    assert not asks_for_nothing(words)


def test_that_nothing_was_made_of_a_word_is_said_as_it_was():
    # `other` says that the reader made nothing of some word, whatever the word. It is
    # what a caller asks a model by, and it has not moved.
    for text in (AS_SAID, "I like noise", "I want somewhere affluent", "If we buy a flat"):
        result = read(text)
        assert result.unread == () and result.asks_nothing
        assert UnmetCategory.OTHER in result.unmet
    whole = read("quiet")
    assert (whole.unread, whole.asks_nothing, whole.unmet) == ((), (), ())


def test_what_is_left_out_is_where_the_words_stand_and_never_the_words():
    canary = "zqxjkvanary"
    result = read(f"I want to live somewhere quiet, with a {canary}")
    assert [(span.start, span.end) for span in result.asks_nothing] == [(0, 24)]
    assert [(span.start, span.end) for span in result.unread] == [(32, 50)]
    assert canary not in result.model_dump_json()
    assert "somewhere" not in result.model_dump_json()


# --- What is said of the words alone -----------------------------------------------------

# What was typed, and the words nothing was made of, none of which asks for anything.
SAID_OF_THE_WORDS = [
    ("somewhere cheap, I think", ["I think"]),
    ("leafy and quiet, I guess", ["and", "I guess"]),
    ("a park, to be honest", ["a", "to be honest"]),
    ("Honestly, somewhere calm", ["Honestly, somewhere"]),
    ("I think, a park, ideally", ["I think, a", "ideally"]),
    (
        "I'd like somewhere leafy, not too far from a station, if possible",
        ["I'd like somewhere", "not too far from a", "if possible"],
    ),
]


@pytest.mark.parametrize(("text", "not_said"), SAID_OF_THE_WORDS)
def test_what_is_said_of_the_words_alone_is_not_said_to_be_unread(text: str, not_said: list[str]):
    result = read(text)

    assert (unread(text), left_out(text)) == ([], not_said)
    # Nothing was made of it all the same, which is said as it was.
    assert UnmetCategory.OTHER in result.unmet
    assert result.operations == NO_OPERATIONS


@pytest.mark.parametrize(
    ("text", "alone"),
    [
        ("somewhere cheap, I think", "somewhere cheap"),
        ("honestly, somewhere cheap", "somewhere cheap"),
        ("somewhere cheap, to be honest", "somewhere cheap"),
    ],
)
def test_somewhere_cheap_is_read_beside_what_is_said_of_the_words_as_it_is_by_itself(
    text: str, alone: str
):
    """ "Cheap" is heard as a word for what a person can afford, of which Burro says nothing.

    It is no word for the mix of brands, as "cheap and cheerful" is, so
    nothing is offered of it, by itself or beside what is said of the words.
    """
    found, by_itself = read(text), read(alone)

    assert (found.status, found.operations) == (by_itself.status, by_itself.operations)
    assert (found.suggestions, found.unread) == (by_itself.suggestions, by_itself.unread)
    assert (found.status, found.suggestions, found.unread) == (InterpretStatus.OK, (), ())
    assert by_itself.unmet == (UnmetCategory.AFFORDABILITY_VERDICT,)
    assert found.unmet == (UnmetCategory.AFFORDABILITY_VERDICT, UnmetCategory.OTHER)


@pytest.mark.parametrize(
    ("text", "said"),
    [
        # A word that is on no list stands in the stretch, which is unread whole, as it was.
        ("a park, honestly, bleh", ["honestly, bleh"]),
        ("honestly bleh, a park", ["honestly bleh, a"]),
        # No mark sets it apart, so it is said with the words it stands among.
        ("a park I think", ["I think"]),
        ("honestly a park", ["honestly a"]),
        ("a park, I think not", ["I think not"]),
        # It is in quotes, and may be named and not said.
        ('a park, "honestly"', ["honestly"]),
        # "Maybe" is none of them: it may stand for a wish that is not.
        ("a park, maybe", ["maybe"]),
    ],
)
def test_what_is_not_set_apart_or_is_no_such_phrase_is_said_to_be_unread_as_it_was(
    text: str, said: list[str]
):
    assert unread(text) == said


def test_every_phrase_that_is_said_of_the_words_alone_asks_for_nothing_between_two_marks():
    for phrase in sorted(ASIDES):
        text = f"a park, {phrase}, leafy"
        assert unread(text) == [], phrase
        assert phrase in left_out(text), phrase
        # Standing among other words it is one the reader does not know.
        assert unread(f"a park {phrase} bleh") == [f"{phrase} bleh"], phrase
