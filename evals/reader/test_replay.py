"""The answers on disk, read again, are held to the floor below which no model is turned on.

    uv run pytest evals/reader/test_replay.py

The floor is the contract's (section 8.2): nothing applied without a press,
nothing offered that is never to be offered, no right reading of the rules
lost, and no more than one backwards reading in a hundred marked as the
guess. It is held on the first look of every sentence. What the counts were
when the guard was built is held too, so that a change to the guard that
moves one is seen.
"""

import importlib.util
import sys
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
RELEASE = score.load_release(None)
ROWS = replay.answers_of(replay.ANSWERS, replay.MODEL)
FOUND: list[tuple[dict[str, Any], Any, int]] = replay.replayed(
    ROWS, replay.cases_for(replay.ANSWERS, RELEASE), RELEASE
)
FIRST = [(row, scored, calls) for row, scored, calls in FOUND if row["look"] == 1]


def test_every_answer_on_disk_is_of_a_sentence_that_a_case_holds():
    assert len(ROWS) == 129 and len(FIRST) == 112
    assert len({(row["id"], row["look"]) for row in ROWS}) == len(ROWS)
    # One call was refused and one failed, and each is on disk as what it was.
    assert sorted(row["failed"] for row in ROWS if "output" not in row) == ["error", "refused"]


def test_the_first_look_of_every_sentence_is_within_the_floor():
    assert score.offers_gate([scored for _, scored, _ in FIRST]) == []


def test_nothing_is_applied_and_nothing_is_offered_that_is_never_to_be_offered():
    counts = replay.counted(FOUND)

    assert counts["applied with no press"] == 0
    assert counts["never to be offered, and offered"] == 0
    assert counts["backwards, applied"] == 0
    assert counts["right readings of the rules lost"] == 0


def test_no_call_is_made_for_a_prompt_the_rules_read_the_whole_of():
    calls = {row["id"]: made for row, _, made in FIRST}

    # "not near a station" is plain, and "pace" is the name of a scale alone.
    assert (calls["neg-003"], calls["vibe-036"], calls["own-001"]) == (0, 0, 0)
    assert calls["own-021"] == 1
    # A journey and a budget that are all that was typed are plain too.
    assert (calls["own-003"], calls["own-004"], calls["budget-016"]) == (0, 0, 0)
    assert sum(calls.values()) == 77


def test_the_two_calls_that_failed_are_never_made_now_because_the_rules_read_both():
    failed = [
        (row["id"], scored.outcome, made) for row, scored, made in FOUND if "output" not in row
    ]

    # "I'm worried about violent crime" and "not near a station" are plain.
    # What the route does when a call fails is held in the API's own tests.
    assert failed == [
        ("crime-004", score.Outcome.CORRECT, 0),
        ("neg-003", score.Outcome.CORRECT, 0),
    ]


def test_what_the_guard_made_of_the_answers_when_it_was_built():
    # Of 112 sentences read once each. The rules alone read 61 of them rightly.
    # One backwards reading is marked as the guess: a wish of somebody else's,
    # in words core does not list.
    assert replay.counted(FIRST) == {
        "answers": 112,
        "calls the reader made": 77,
        "answered by the rules, with no call or in a model's place": 35,
        "right": 84,
        "in part": 11,
        "not read": 13,
        "a guess nobody asked for": 3,
        "backwards, offered with no guess marked": 0,
        "backwards, marked as the guess": 1,
        "backwards, applied": 0,
        "never to be offered, and offered": 0,
        "applied with no press": 0,
        "right readings of the rules lost": 0,
    }
