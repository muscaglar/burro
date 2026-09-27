"""What a client makes of every held sentence, where it takes what is offered and asks nothing.

The website applies what Burro read and asks nothing (ADR 0012, as amended on
2026-09-26). It takes one way of every offer: the way one press may add, of a
limit the guide, the way that is the guess, and of a thing that runs one way
that way. So what the service offers, marks and leaves to a person is what
reaches a ranking, and a way that is offered in doubt is a search that may be
turned round.

This holds the service to the evaluation set, by the scorer's own judgement,
as `test_to_press_every_guess_of_the_rules_does_the_opposite_of_no_case_that_is_held`
holds what it marks as the guess. It counts, and the counts are a ceiling and
a floor: a change that reads more sentences backwards for such a client fails
here. What is still read backwards is in words that core does not list, which
is what no list of words can close.

Every sentence of the set is made up, but one, which is the founder's own.
"""

from functools import cache
from typing import Any

from burro_api.guard import plainly_said, settled
from burro_api.offers import Offer, Way, in_add_all, of_the_rules, waits_for_a_person
from burro_api.typed import Typed
from burro_core.grammar import Grammar
from burro_core.ids import AreaAction, StrictnessChoice, SuggestionDirection, WeightAction
from burro_core.interpret import InterpretRequest, RuleInterpreter
from burro_core.places import Names

from .support import scorer

# What the same client made of the same sentences before the service marked the way the
# words give and said what waits for a person: of the 1,026 the set holds, it read 87
# backwards and made an edit nobody asked for in 39, and 674 were right.
READ_BACKWARDS_AT_MOST = 31
UNASKED_AT_MOST = 33
RIGHT_AT_LEAST = 704


def _stops(way: Way) -> bool:
    wishes = [*way.operations.weight_ops, *way.operations.tag_ops]
    return bool(wishes) and all(edit.action is WeightAction.REMOVE for edit in wishes)


def _firmness(way: Way) -> list[StrictnessChoice]:
    limits = [*way.operations.budget_ops, *way.operations.commute_ops]
    return [edit.strictness for edit in limits]


def taken_of(offer: Offer, typed: Typed) -> Way | None:
    """The way of an offer that the website takes of itself, as `lib/search/takes.ts` chooses.

    What waits for a person is left, and so is a journey to a place that is
    yet to be chosen: no sentence of the set offers one by the rules alone.
    """
    if waits_for_a_person(offer) or offer.asks_place:
        return None
    every = [way for way in offer.choices if way.direction is not SuggestionDirection.IGNORE]
    said = in_add_all(offer) if settled(offer, typed) else None
    if said is not None:
        return said
    open_to = [way for way in every if not _stops(way)]
    guides = [
        way
        for way in open_to
        if any(firm is not StrictnessChoice.UNCHANGED for firm in _firmness(way))
        and StrictnessChoice.HARD not in _firmness(way)
    ]
    guessed = [way for way in open_to if way.guess]
    if guides or guessed:
        return (guides or guessed)[0]
    ruled = any(
        edit.action is not AreaAction.CLEAR for way in open_to for edit in way.operations.area_ops
    )
    more = [way for way in open_to if way.direction is SuggestionDirection.MORE]
    less = [way for way in open_to if way.direction is SuggestionDirection.LESS]
    if ruled or (more and less):
        return None
    return (more or open_to or [None])[0]


@cache
def outcomes() -> dict[str, tuple[str, ...]]:
    """How every held sentence ends for such a client. It is worked out once."""
    return {outcome: tuple(cases) for outcome, cases in _outcomes().items()}


def _outcomes() -> dict[str, list[str]]:
    score: Any = scorer()
    held = score.load_release(None)
    names, grammar, rules = score.Names(held), Grammar(Names(held), held), RuleInterpreter()
    cases, problems = score.load_cases(score.CASES, held)
    assert not problems
    found: dict[str, list[str]] = {}
    for case in cases:
        asked = InterpretRequest(text=case.text, spec=case.start, release=held)
        read = rules.interpret(asked)
        typed = Typed(case.text, grammar, held)
        noticed = [of_the_rules(suggestion) for suggestion in read.suggestions]
        offers = plainly_said(noticed, typed, case.start)
        took = [way for way in (taken_of(offer, typed) for offer in offers) if way is not None]
        edits = score._together([read.operations, *(way.operations for way in took)])
        outcome = score.outcome_of(score.judge(case, read, held, names, edits))
        found.setdefault(outcome.value, []).append(case.id)
    return found


def test_a_client_that_asks_nothing_reads_no_more_sentences_backwards_than_it_did():
    found = outcomes()

    assert set(found) <= {"correct", "partial", "declined", "reversed", "unasked"}
    assert len(found["reversed"]) <= READ_BACKWARDS_AT_MOST, sorted(found["reversed"])
    assert len(found["unasked"]) <= UNASKED_AT_MOST, sorted(found["unasked"])
    assert len(found["correct"]) >= RIGHT_AT_LEAST


def test_the_sentences_that_were_seen_to_be_read_backwards_are_read_so_no_longer():
    found = outcomes()

    # "Calm" as buzzy and "fewer pubs" as more was what taking the first of two ways
    # did. A station that is never used, a park that somebody else is after and a noise
    # that is liked were each taken for a wish.
    mended = {
        "sugg-032",  # Honestly, somewhere calm
        "sugg-035",  # Honestly, fewer pubs
        "sugg-037",  # I never use the station
        "sugg-038",  # I hate culture
        "sugg-040",  # Things I hate. Pubs. A station.
        "list-003",  # Dealbreakers: pubs, a station, nightlife
        "list-030",  # no parks, playgrounds or schools
        "neg-037",  # I like noise
        "neg-060",  # somewhere that isn't near a station
        "neg-061",  # miles from the nearest station
        "other-004",  # My ex works at Pellam Infirmary so I'd rather be elsewhere
        "sugg-022",  # my mum is after a park
        "ask-019",  # A park? no thanks
    }
    assert not mended & {*found["reversed"], *found["unasked"]}


def test_a_plain_prompt_is_applied_as_it_was_and_offers_nothing_to_take():
    score: Any = scorer()
    held = score.load_release(None)
    rules = RuleInterpreter()
    cases, _ = score.load_cases(score.CASES, held)
    plain = [case for case in cases if case.plain]
    assert len(plain) > 100
    for case in plain:
        read = rules.interpret(InterpretRequest(text=case.text, spec=case.start, release=held))
        offered = [of_the_rules(suggestion) for suggestion in read.suggestions]
        # What a plain prompt says of a home that the search cannot hold has no way to take.
        assert not [way for offer in offered for way in offer.choices if way.id != "ignore"]
