"""The answers on disk, read again, are held to the floor below which no model is turned on.

    uv run pytest evals/reader/test_replay.py

The floor is the contract's (section 8.2): nothing applied without a press,
nothing offered that is never to be offered, no right reading of the rules
lost, and no more than one backwards reading in a hundred marked as the
guess. It is held on the first look of every sentence. What the counts are
is held too, so that a change to the guard that moves one is seen.
"""

import copy
import importlib.util
import sys
from functools import cache
from pathlib import Path
from typing import Any

_SPEC = importlib.util.spec_from_file_location(
    "reader_replay", Path(__file__).with_name("replay.py")
)
assert _SPEC is not None and _SPEC.loader is not None
replay = importlib.util.module_from_spec(_SPEC)
sys.modules["reader_replay"] = replay
_SPEC.loader.exec_module(replay)

score = replay.score
ROWS = replay.answers_of(replay.ANSWERS, replay.MODEL)


@cache
def _read_once() -> list[tuple[dict[str, Any], Any, int]]:
    """Every answer on disk, read again. It is read once, by the first test that asks.

    Every process that runs tests imports this file to learn which tests it holds, and
    one of them runs them. Read as the file was imported, the answers were read again
    in every process.
    """
    release = score.load_release(None)
    return replay.replayed(ROWS, replay.cases_for(replay.ANSWERS, release), release)


def found() -> list[tuple[dict[str, Any], Any, int]]:
    """Every answer on disk, read again: a copy that is the test's own.

    What is read once is handed to no test. A test that changes what it was handed
    changes its copy, and nothing that the next test reads.
    """
    return copy.deepcopy(_read_once())


def first() -> list[tuple[dict[str, Any], Any, int]]:
    """The first look of every sentence."""
    return [(row, scored, calls) for row, scored, calls in found() if row["look"] == 1]


def test_a_test_that_changes_what_it_was_handed_changes_nothing_the_next_reads():
    handed = found()
    before = repr(handed)
    handed[0][0]["look"] = "changed by a test"
    del handed[1:]

    assert repr(found()) == before and len(first()) == 112


def test_every_answer_on_disk_is_of_a_sentence_that_a_case_holds():
    assert len(ROWS) == 129 and len(first()) == 112
    assert len({(row["id"], row["look"]) for row in ROWS}) == len(ROWS)
    # One call was refused and one failed, and each is on disk as what it was.
    assert sorted(row["failed"] for row in ROWS if "output" not in row) == ["error", "refused"]


def test_the_first_look_of_every_sentence_is_within_the_floor():
    assert score.offers_gate([scored for _, scored, _ in first()]) == []


def test_nothing_is_applied_and_nothing_is_offered_that_is_never_to_be_offered():
    counts = replay.counted(found())

    assert counts["applied with no press"] == 0
    assert counts["never to be offered, and offered"] == 0
    assert counts["backwards, applied"] == 0
    assert counts["right readings of the rules lost"] == 0


def test_no_call_is_made_for_a_prompt_the_rules_read_the_whole_of():
    calls = {row["id"]: made for row, _, made in first()}

    # "not near a station" is plain, and "pace" is the name of a scale alone.
    assert (calls["neg-003"], calls["vibe-036"], calls["own-001"]) == (0, 0, 0)
    assert calls["own-021"] == 1
    # A journey and a budget that are all that was typed are plain too.
    assert (calls["own-003"], calls["own-004"], calls["budget-016"]) == (0, 0, 0)
    # A prompt that holds a word for Village feel is no longer read whole: it is a rough
    # guide since 2026-09-25, and is taken by a press of its own. Two such were plain.
    assert (calls["own-011"], calls["own-023"]) == (1, 1)
    assert sum(calls.values()) == 79


def test_the_two_calls_that_failed_are_never_made_now_because_the_rules_read_both():
    failed = [
        (row["id"], scored.outcome, made) for row, scored, made in found() if "output" not in row
    ]

    # "I'm worried about violent crime" and "not near a station" are plain.
    # What the route does when a call fails is held in the API's own tests.
    assert failed == [
        ("crime-004", score.Outcome.CORRECT, 0),
        ("neg-003", score.Outcome.CORRECT, 0),
    ]


def test_what_the_guard_makes_of_the_answers_on_disk():
    # Of 112 sentences read once each. The rules alone read 61 of them rightly.
    # No backwards reading is marked as the guess. One was, a wish of somebody
    # else's, until the guard read whose wish it is. "Lots of young families" was right
    # when it drew the notice alone. It is offered a family area now, which no press has
    # taken up. Two sentences that ask for a village feel were right while the rules
    # applied it. It is a rough guide since 2026-09-25: it is offered with no guess, so
    # to press every guess takes the rest of each and leaves it for a press of its own.
    assert replay.counted(first()) == {
        "answers": 112,
        "calls the reader made": 79,
        "answered by the rules, with no call or in a model's place": 33,
        "right": 82,
        "in part": 13,
        "not read": 14,
        "a guess nobody asked for": 3,
        "backwards, offered with no guess marked": 0,
        "backwards, marked as the guess": 0,
        "backwards, applied": 0,
        "never to be offered, and offered": 0,
        "applied with no press": 0,
        "right readings of the rules lost": 0,
    }
