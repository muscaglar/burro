"""A word typed with an ampersand between its letters, and what the reader makes of it.

The name of a shop is often typed so, and so are two things typed as one. The
ampersand is read as the "and" it stands for, and the word is read whole or
not at all, as a word typed with a hyphen is. Every sentence here is made up.
"""

import pytest
from burro_core.ids import FeatureId, InterpretStatus, Tenure
from burro_core.interpret import InterpretRequest, InterpretResult, RuleInterpreter
from burro_core.reading import lines_of
from burro_core.spec import default_spec

from .support import small_release


def read(text: str) -> InterpretResult:
    request = InterpretRequest(text=text, spec=default_spec(Tenure.RENT), release=small_release())
    return RuleInterpreter().interpret(request)


def tokens(text: str) -> list[tuple[str, str, bool, bool]]:
    return [
        (token.word, token.bare, token.joined, token.odd)
        for line in lines_of(text)
        for token in line.tokens
    ]


def test_an_ampersand_between_letters_is_read_as_the_and_it_stands_for():
    assert tokens("pubs&bars") == [("pubs&bars", "pubs and bars", True, False)]
    assert tokens("Fish&Chips") == [("fish&chips", "fish and chips", True, False)]
    # One that stands alone between two words was always read as the word.
    assert [word for word, *_ in tokens("parks & pubs")] == ["parks", "and", "pubs"]


@pytest.mark.parametrize("text", ["&", "&pubs", "pubs&", "pubs&&bars", "pubs&;bars", "a&b&"])
def test_an_ampersand_anywhere_else_makes_a_token_the_reader_does_not_place(text: str):
    assert all(odd or word == "and" for word, _, _, odd in tokens(text))
    assert read(text).operations.count == 0


def test_two_things_typed_as_one_are_read_as_the_thing_the_whole_names():
    """It is a phrase only as a whole, as a word typed with a hyphen is."""
    result = read("pubs&bars")
    assert result.status is InterpretStatus.OK
    wished = [edit.feature_id for edit in result.operations.weight_ops]
    assert wished == [FeatureId.VENUE_EVENING_PER_HOMES]
    assert (result.unmet, result.unread) == ((), ())


def test_a_whole_that_names_nothing_is_not_read_in_part():
    """ "Parks&recreation" holds the word for a park, and is no wish for one."""
    for text in ("parks&recreation", "fish&chips nearby", "leafy&quiet"):
        result = read(text)
        assert result.operations.count == 0
        assert result.suggestions == ()
        assert [(span.start, span.end) for span in result.unread] == [(0, len(text))]
