"""The scorer is a measuring instrument, so it is tested with readers whose faults are known.

Each stand-in below answers one way whatever it is asked, so a test can say
what the scorer must make of it. None needs a model or a network.

    uv run pytest evals/reader
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest
from burro_core.ids import (
    AreaAction,
    CommuteAction,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    InterpreterName,
    InterpretStatus,
    ModeChoice,
    Notice,
    Step,
    StrictnessChoice,
    TagId,
    WeightAction,
)
from burro_core.interpret import NO_USAGE, InterpretRequest, InterpretResult
from burro_core.ops import NO_OPERATIONS, AreaEdit, CommuteEdit, Operations, TagEdit, WeightEdit

_SPEC = importlib.util.spec_from_file_location("reader_score", Path(__file__).with_name("score.py"))
assert _SPEC is not None and _SPEC.loader is not None
score = importlib.util.module_from_spec(_SPEC)
sys.modules["reader_score"] = score
_SPEC.loader.exec_module(score)

RELEASE = score.load_release(None)
NAMES = score.Names(RELEASE)
CASES, PROBLEMS = score.load_cases(score.CASES, RELEASE)
BY_TEXT = {case.text: case for case in CASES}
STATED = EditProvenance.STATED


def answer(operations: Operations = NO_OPERATIONS, notice: Notice = Notice.NONE) -> InterpretResult:
    return InterpretResult(
        status=InterpretStatus.OK,
        operations=operations,
        assumptions=(),
        unmet=(),
        clarify=(),
        notice=notice,
        interpreter=InterpreterName.RULE,
        degraded=False,
        usage=NO_USAGE,
    )


def edits(**groups: tuple[Any, ...]) -> Operations:
    return NO_OPERATIONS.replace(**groups)


def weight(
    feature_id: FeatureId,
    action: WeightAction = WeightAction.NUDGE,
    step: Step = Step.UP_LARGE,
    direction: DirectionChoice = DirectionChoice.DEFAULT,
    provenance: EditProvenance = STATED,
) -> WeightEdit:
    return WeightEdit(
        action=action,
        feature_id=feature_id,
        value=0.0,
        step=step,
        direction=direction,
        provenance=provenance,
    )


def tag(tag_id: TagId) -> TagEdit:
    return TagEdit(
        action=WeightAction.NUDGE, tag_id=tag_id, value=0.0, step=Step.UP_LARGE, provenance=STATED
    )


def journey(name: str, minutes: int = 0, strictness: str = "unchanged") -> CommuteEdit:
    return CommuteEdit(
        action=CommuteAction.ADD,
        place_id=NAMES.place(name, "test")[0],
        mode=ModeChoice.UNCHANGED,
        max_minutes=minutes,
        strictness=StrictnessChoice(strictness),
        step=Step.NONE,
        provenance=STATED,
    )


class Says:
    """A reader that gives the same answer whatever it is asked."""

    name = "stand-in"

    def __init__(self, result: InterpretResult) -> None:
        self.result = result

    def interpret(self, request: InterpretRequest) -> InterpretResult:
        return self.result


def outcome(text: str, result: InterpretResult) -> str:
    return score.score(BY_TEXT[text], Says(result), RELEASE, NAMES).outcome.value


PUBS_UP = edits(weight_ops=(weight(FeatureId.VENUE_EVENING),))
PUBS_FEWER = edits(weight_ops=(weight(FeatureId.VENUE_EVENING, direction=DirectionChoice.LESS),))
PARK_UP = edits(weight_ops=(weight(FeatureId.PARK_PROXIMITY),))


def test_every_case_can_be_scored_as_it_is_written():
    assert PROBLEMS == []


def test_the_set_holds_four_hundred_cases_and_every_group():
    assert len(CASES) >= 400
    assert {case.group for case in CASES} == set(score.GROUPS)
    assert all(sum(case.group == group for case in CASES) >= 25 for group in score.GROUPS)


def test_no_case_holds_more_words_than_the_service_accepts():
    assert all(1 <= len(case.text) <= 600 for case in CASES)


def test_a_reader_that_does_nothing_reverses_nothing_and_invents_nothing():
    scored = score.run(CASES, score.load_reader("nothing"), RELEASE, workers=1)
    found = {s.outcome for s in scored}
    assert found <= {score.Outcome.CORRECT, score.Outcome.DECLINED}
    # It is right exactly where the words ask for nothing.
    assert all((s.outcome is score.Outcome.CORRECT) is not s.case.asks for s in scored)


def test_a_reader_that_raises_whatever_is_named_is_caught_reversing():
    scored = score.run(CASES, score.load_reader("keywords"), RELEASE, workers=1)
    reversed_ = [s.case.text for s in scored if s.outcome is score.Outcome.REVERSED]
    # If this reader passes, the cases have lost their teeth.
    assert len(reversed_) >= 100
    assert "I don't want pubs nearby" in reversed_
    assert "My ex works at Pellam Infirmary so I'd rather be elsewhere" in reversed_


def test_a_thing_raised_that_was_to_fall_is_reversed():
    assert outcome("I don't want pubs nearby", answer(PUBS_UP)) == "reversed"


def test_a_thing_turned_to_fewer_has_fallen():
    assert outcome("I don't want pubs nearby", answer(PUBS_FEWER)) == "correct"


def test_a_thing_taken_off_that_held_no_weight_has_still_fallen():
    taken_off = edits(weight_ops=(weight(FeatureId.VENUE_EVENING, action=WeightAction.REMOVE),))
    assert outcome("I don't want pubs nearby", answer(taken_off)) == "correct"


def test_a_thing_lowered_that_was_to_rise_is_reversed():
    taken_off = edits(weight_ops=(weight(FeatureId.PARK_PROXIMITY, action=WeightAction.REMOVE),))
    assert outcome("I can't live without a park", answer(taken_off)) == "reversed"


def test_a_thing_that_was_only_not_to_rise_may_be_left_alone_or_lowered():
    assert outcome("Pubs are for other people", answer()) == "correct"
    assert outcome("Pubs are for other people", answer(PUBS_FEWER)) == "correct"
    assert outcome("Pubs are for other people", answer(PUBS_UP)) == "reversed"


def test_a_thing_nobody_named_that_moves_is_unasked():
    both = edits(weight_ops=(weight(FeatureId.PARK_PROXIMITY), weight(FeatureId.VENUE_EVENING)))
    assert outcome("parks", answer(PARK_UP)) == "correct"
    assert outcome("parks", answer(both)) == "unasked"


def test_the_defaults_giving_way_is_no_move():
    # A park is named, so every default gives way. Nothing but the park was edited.
    found = score.score(BY_TEXT["parks"], Says(answer(PARK_UP)), RELEASE, NAMES)
    assert [f.what for f in found.findings if f.verdict.value != "met"] == []


def test_an_edit_the_reducer_turns_away_moves_nothing():
    inferred = edits(
        weight_ops=(weight(FeatureId.CRIME_BURGLARY_THEFT, provenance=EditProvenance.INFERRED),)
    )
    stated = edits(weight_ops=(weight(FeatureId.CRIME_BURGLARY_THEFT),))
    assert outcome("somewhere safe", answer(inferred)) == "correct"
    assert outcome("somewhere safe", answer(stated)) == "unasked"


def test_one_of_several_is_enough_and_the_wrong_way_is_reversed():
    text = "peace and quiet"
    quiet = edits(tag_ops=(tag(TagId.QUIET_RESIDENTIAL),))
    noise = edits(weight_ops=(weight(FeatureId.NOISE_EXPOSURE),))
    off = edits(weight_ops=(weight(FeatureId.NOISE_EXPOSURE, action=WeightAction.REMOVE),))
    assert outcome(text, answer(quiet)) == "correct"
    assert outcome(text, answer(noise)) == "correct"
    assert outcome(text, answer(off)) == "reversed"
    assert outcome(text, answer()) == "declined"


def test_part_of_what_was_asked_is_read_in_part():
    assert outcome("Somewhere quiet and leafy, near a park", answer(PARK_UP)) == "partial"


def test_a_journey_to_a_place_that_was_refused_is_reversed():
    text = "My ex works at Pellam Infirmary so I'd rather be elsewhere"
    added = edits(commute_ops=(journey("Pellam Infirmary"),))
    assert outcome(text, answer(added)) == "reversed"
    assert outcome(text, answer()) == "correct"


def test_a_journey_with_minutes_or_a_limit_nobody_gave_is_unasked():
    text = "I work at Cindermoor Works"
    assert outcome(text, answer(edits(commute_ops=(journey("Cindermoor Works"),)))) == "correct"
    short = edits(commute_ops=(journey("Cindermoor Works", minutes=10),))
    hard = edits(commute_ops=(journey("Cindermoor Works", strictness="hard"),))
    other = edits(commute_ops=(journey("Foxholt Market"),))
    assert outcome(text, answer(short)) == "unasked"
    assert outcome(text, answer(hard)) == "unasked"
    assert outcome(text, answer(other)) == "unasked"


def test_minutes_that_were_given_and_not_read_are_read_in_part():
    text = "30 minutes to Pellam Exchange"
    assert outcome(text, answer(edits(commute_ops=(journey("Pellam Exchange"),)))) == "partial"
    whole = edits(commute_ops=(journey("Pellam Exchange", minutes=30),))
    assert outcome(text, answer(whole)) == "correct"


def test_the_other_rule_for_an_area_is_reversed():
    area_id = NAMES.area("Wexmoor", "test")[0]
    only = edits(area_ops=(AreaEdit(action=AreaAction.ONLY, area_id=area_id, provenance=STATED),))
    out = edits(area_ops=(AreaEdit(action=AreaAction.EXCLUDE, area_id=area_id, provenance=STATED),))
    assert outcome("anywhere but Wexmoor", answer(only)) == "reversed"
    assert outcome("anywhere but Wexmoor", answer(out)) == "correct"


def test_a_notice_that_was_called_for_and_not_given_is_missed():
    assert outcome("fewer immigrants", answer()) == "declined"
    assert outcome("fewer immigrants", answer(notice=Notice.NEUTRAL_PLACES)) == "correct"


def test_a_notice_nobody_called_for_is_not_correct():
    assert outcome("an English garden", answer(notice=Notice.NEUTRAL_PLACES)) == "partial"


def test_of_a_reader_that_raises_only_the_class_is_kept():
    class Breaks:
        name = "stand-in"

        def interpret(self, request: InterpretRequest) -> InterpretResult:
            raise ValueError(request.text)

    found = score.score(BY_TEXT["parks are essential"], Breaks(), RELEASE, NAMES)
    assert (found.outcome.value, found.error) == ("failed", "ValueError")


def scored_as(*outcomes: str) -> list[Any]:
    return [score.Scored(case, score.Outcome(o)) for case, o in zip(CASES, outcomes, strict=False)]


def test_one_reversed_case_fails_the_run_whatever_the_share():
    floor = {"stand-in": {"correct_share": 0.0}}
    assert score.gate(scored_as("correct", "correct"), floor, "stand-in") == []
    assert score.gate(scored_as("correct", "reversed"), floor, "stand-in") != []


def test_a_share_below_the_floor_fails_the_run():
    floor = {"stand-in": {"correct_share": 0.75}}
    assert (
        score.gate(scored_as("correct", "correct", "correct", "declined"), floor, "stand-in") == []
    )
    assert score.gate(scored_as("correct", "declined"), floor, "stand-in") != []


def test_more_unasked_than_the_ceiling_fails_the_run():
    floor = {"stand-in": {"correct_share": 0.0, "unasked_ceiling": 1}}
    assert score.gate(scored_as("correct", "unasked"), floor, "stand-in") == []
    assert score.gate(scored_as("unasked", "unasked"), floor, "stand-in") != []


def test_a_reader_with_no_floor_fails_the_run():
    assert score.gate(scored_as("correct"), {}, "stand-in") != []


BAD: tuple[tuple[dict[str, Any], str], ...] = (
    ({"text": "a park", "tenure": "rent", "expect": {}, "why": "w"}, "'id' is missing"),
    ({"id": "a", "text": "", "tenure": "rent", "expect": {}, "why": "w"}, "1 to 600"),
    ({"id": "a", "text": "x" * 601, "tenure": "rent", "expect": {}, "why": "w"}, "1 to 600"),
    ({"id": "a", "text": "p", "tenure": "rent", "expect": {"rises": []}, "why": "w"}, "not a key"),
    (
        {"id": "a", "text": "p", "tenure": "rent", "expect": {"rise": ["feature:x"]}, "why": "w"},
        "not a feature",
    ),
    (
        {
            "id": "a",
            "text": "p",
            "tenure": "rent",
            "expect": {"journeys": {"add": ["Nowhere Junction"]}},
            "why": "w",
        },
        "is not in the release",
    ),
    (
        {
            "id": "a",
            "text": "p",
            "tenure": "rent",
            "expect": {"rise": ["tag:leafy"], "fall": ["tag:leafy"]},
            "why": "w",
        },
        "under both",
    ),
    (
        {
            "id": "a",
            "text": "p",
            "tenure": "rent",
            "expect": {"budget": {"segment": "detached"}},
            "why": "w",
        },
        "does not suit the tenure",
    ),
)


@pytest.mark.parametrize(("case", "problem"), BAD)
def test_a_case_that_cannot_be_scored_is_refused_with_its_reason(
    tmp_path: Path, case: dict[str, Any], problem: str
):
    (tmp_path / "bad.jsonl").write_text(json.dumps(case) + "\n", encoding="utf-8")
    cases, problems = score.load_cases(tmp_path, RELEASE)
    assert cases == []
    assert len(problems) == 1
    assert problem in problems[0]


def test_the_report_holds_the_sentence_of_a_reversed_case_and_nothing_a_reader_said():
    case = BY_TEXT["I don't want pubs nearby"]
    scored = [score.score(case, Says(answer(PUBS_UP)), RELEASE, NAMES)]
    listed = score.listing(scored, score.Outcome.REVERSED)
    assert case.text in listed
    assert case.id in listed
