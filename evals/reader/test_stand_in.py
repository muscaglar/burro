"""The stand-ins that measure the guard are instruments too, so they are tested on a few cases.

The whole measurement takes a minute and is run by hand:

    uv run python evals/reader/stand_in.py

These run the cases that start from a search that holds something, which is
where what is sent could matter, and the two cases that are known to come
through the guard against what the case says.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "reader_stand_in", Path(__file__).with_name("stand_in.py")
)
assert _SPEC is not None and _SPEC.loader is not None
stand_in = importlib.util.module_from_spec(_SPEC)
sys.modules["reader_stand_in"] = stand_in
_SPEC.loader.exec_module(stand_in)

score = stand_in.score
RELEASE = score.load_release(None)
CASES, _ = score.load_cases(score.CASES, RELEASE)
BY_ID = {case.id: case for case in CASES}
HOLDING = [case for case in CASES if case.start != score.default_spec(case.tenure)]
# A few that hold nothing: a journey, wishes, a wish turned round, a question, a request
# about who lives somewhere.
PLAIN = ["journey-002", "plain-001", "plainp-001", "neg-003", "ask-001", "who-001", "short-001"]
STAND_INS = {"right": stand_in.right, "backwards": stand_in.backwards}


def outcomes(reads: str, with_settings: bool, cases: list[Any]) -> dict[str, str]:
    scored = stand_in.measured(STAND_INS[reads], with_settings, cases, RELEASE)
    return {one.case.id: one.outcome.value for one in scored}


def test_the_cases_that_start_from_a_search_are_the_ones_the_measurement_counts():
    assert sorted(case.id for case in HOLDING) == [
        "budget-025",
        "budget-026",
        "budget-035",
        "crime-029",
        "double-024",
        "journey-033",
        "journey-034",
        "neg-072",
    ]


@pytest.mark.parametrize("reads", STAND_INS)
def test_what_comes_through_the_guard_is_the_same_whether_or_not_the_settings_are_sent(
    reads: str,
):
    cases = [*HOLDING, *(BY_ID[case_id] for case_id in PLAIN)]

    alone = outcomes(reads, False, cases)

    assert alone == outcomes(reads, True, cases)
    assert "failed" not in alone.values()


def test_a_stand_in_that_is_sent_the_words_alone_names_no_journey_it_was_not_told_of():
    known = stand_in.Known(RELEASE)
    follow_up = BY_ID["journey-034"]
    sent = {"commutes": [{"position": 1}]}

    # "make that 30 minutes": nothing in the words says which journey.
    assert stand_in.right(follow_up, known, None)["commute_ops"] == []
    [by_position] = stand_in.right(follow_up, known, sent)["commute_ops"]
    assert (by_position["action"], by_position["position"]) == ("update", 1)
    assert by_position["destination_text"] == ""


def test_a_careful_stand_in_reads_more_than_the_rules_and_reverses_nothing():
    cases = [BY_ID[case_id] for case_id in PLAIN]

    through = outcomes("right", False, cases)

    assert "reversed" not in through.values() and "unasked" not in through.values()
    assert list(through.values()).count("correct") >= 4


@pytest.mark.parametrize(
    ("case_id", "reads"),
    [("crime-040", "right"), ("crime-040", "backwards"), ("sugg-004", "backwards")],
)
def test_through_a_model_nothing_is_applied_in_a_prompt_that_is_not_plain(case_id: str, reads: str):
    # The rules apply a prompt whole or not at all, and apply neither of
    # these. Nothing a model reads is applied, so nothing is: two wishes
    # beside "safe", and a wish that the next sentence takes back, are offered.
    [scored] = stand_in.measured(STAND_INS[reads], False, [BY_ID[case_id]], RELEASE)

    assert scored.outcome.value not in ("unasked", "reversed")
    assert scored.offer is not score.Offered.APPLIED


def test_a_stand_in_that_reads_backwards_has_nothing_applied_and_loses_nothing_of_the_rules():
    # The last two hold a journey the rules read the minutes of, which a
    # stand-in that quotes the name alone once lost.
    more = ("neg-061", "sugg-022", "list-034", "ask-015")
    cases = [*HOLDING, *(BY_ID[case_id] for case_id in (*PLAIN, *more))]

    scored = stand_in.measured(stand_in.backwards, False, cases, RELEASE)

    assert not [one.case.id for one in scored if one.outcome.value in ("unasked", "reversed")]
    assert not [one.case.id for one in scored if one.lost]
    assert not [one.case.id for one in scored if one.offer is score.Offered.APPLIED]
