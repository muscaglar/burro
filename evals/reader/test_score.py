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
    BudgetAction,
    CommuteAction,
    DirectionChoice,
    EditProvenance,
    FeatureId,
    InterpreterName,
    InterpretStatus,
    ModeChoice,
    Notice,
    SegmentChoice,
    Step,
    StrictnessChoice,
    SuggestionDirection,
    TagId,
    TenureChoice,
    TowardChoice,
    WeightAction,
)
from burro_core.interpret import (
    IGNORE,
    NO_USAGE,
    Choice,
    InterpretRequest,
    InterpretResult,
    Span,
    Suggestion,
)
from burro_core.ops import (
    NO_OPERATIONS,
    AreaEdit,
    BudgetEdit,
    CommuteEdit,
    Operations,
    TagEdit,
    WeightEdit,
)

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


def answer(
    operations: Operations = NO_OPERATIONS,
    notice: Notice = Notice.NONE,
    suggestions: tuple[Suggestion, ...] = (),
) -> InterpretResult:
    return InterpretResult(
        status=InterpretStatus.SUGGEST if suggestions else InterpretStatus.OK,
        operations=operations,
        assumptions=(),
        unmet=(),
        clarify=(),
        notice=notice,
        interpreter=InterpreterName.RULE,
        degraded=False,
        usage=NO_USAGE,
        suggestions=suggestions,
    )


def offer(label: str, **choices: Operations) -> Suggestion:
    """A thing that is offered, with the edits each direction would send."""
    return Suggestion(
        target="feature:venue_evening",
        label=label,
        spans=(Span(start=0, end=1),),
        choices=(
            *(
                Choice(direction=SuggestionDirection(direction), label=direction, operations=sent)
                for direction, sent in choices.items()
            ),
            IGNORE,
        ),
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


def tag(tag_id: TagId, toward: TowardChoice = TowardChoice.HIGH) -> TagEdit:
    return TagEdit(
        action=WeightAction.NUDGE,
        tag_id=tag_id,
        value=0.0,
        step=Step.UP_LARGE,
        toward=toward,
        provenance=STATED,
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


def test_the_set_holds_seven_hundred_cases_and_every_group():
    assert len(CASES) >= 700
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


def test_a_reader_that_offers_what_was_asked_for_and_moves_nothing_has_suggested():
    text = "I don't want pubs nearby"
    both = offer("Pubs and bars", more=PUBS_UP, less=PUBS_FEWER)
    assert outcome(text, answer(suggestions=(both,))) == "suggested"
    # One that offers only the other direction has declined.
    assert outcome(text, answer(suggestions=(offer("Pubs and bars", more=PUBS_UP),))) == "declined"
    # And one that offers it and moves something as well is judged by what it moved.
    assert outcome(text, answer(PUBS_UP, suggestions=(both,))) == "reversed"
    assert outcome(text, answer(PARK_UP, suggestions=(both,))) == "unasked"


def test_a_suggestion_is_never_reversed_or_unasked_because_nothing_moved():
    wrong = offer("Pubs and bars", more=PUBS_UP)
    for case in CASES:
        scored = score.score(case, Says(answer(suggestions=(wrong,))), RELEASE, NAMES)
        assert scored.outcome not in (score.Outcome.REVERSED, score.Outcome.UNASKED), case.id
        # Where nothing was asked for it is still right to have left the search alone.
        if not case.asks:
            assert (scored.outcome, scored.offered) == (score.Outcome.CORRECT, True), case.id


def test_a_prompt_that_is_not_plain_may_have_no_edit_applied_to_it():
    case = BY_TEXT["Moving next month. Somewhere leafy."]
    assert case.plain is False
    leafy = edits(tag_ops=(tag(TagId.LEAFY),))
    # The edit is the one the words ask for, and the reader was still not to apply it.
    assert score.score(case, Says(answer(leafy)), RELEASE, NAMES).outcome.value == "unasked"
    offered = answer(suggestions=(offer("Leafy", more=leafy),))
    assert score.score(case, Says(offered), RELEASE, NAMES).outcome.value == "suggested"


def test_a_scale_rises_towards_its_high_end_and_falls_towards_its_low_end():
    calm = edits(tag_ops=(tag(TagId.PACE, TowardChoice.LOW),))
    buzzy = edits(tag_ops=(tag(TagId.PACE),))
    assert outcome("not buzzy", answer(calm)) == "correct"
    assert outcome("not buzzy", answer(buzzy)) == "reversed"


def test_every_plain_prompt_must_be_read_correctly_or_the_run_fails():
    plain = [case for case in CASES if case.plain is True]
    assert len(plain) >= 22
    scored = [score.Scored(case, score.Outcome.CORRECT) for case in CASES]
    floor = {"rule": {"correct_share": 0.0, "unasked_ceiling": 9, "plain_correct_share": 1}}
    assert score.gate(scored, floor, "rule") == []
    scored[CASES.index(plain[0])] = score.Scored(plain[0], score.Outcome.SUGGESTED)
    (reason,) = score.gate(scored, floor, "rule")
    assert reason.startswith("correct share of plain prompts")


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


# Which floor a model is held to.

PROVIDERS = ("gemini", "openai", "deepseek", "anthropic")


class ByAModel(Says):
    name = InterpreterName.MODEL


def test_the_floors_are_for_the_rules_the_two_controls_and_each_provider_and_name_no_other():
    floors = json.loads(score.FLOOR.read_text(encoding="utf-8"))

    assert set(floors) == {"about", "rule", "nothing", "keywords", *PROVIDERS}
    # No provider has been measured, so none has a floor yet: a run of one
    # fails only where a case is reversed.
    for provider in PROVIDERS:
        assert floors[provider] == {"correct_share": None, "unasked_ceiling": None, "groups": {}}


@pytest.mark.parametrize("provider", PROVIDERS)
def test_a_model_is_held_to_the_floor_of_the_provider_that_runs_it(provider: str):
    env = {"BURRO_MODEL_PROVIDER": f" {provider.upper()} "}

    # Asked for by the one word, and as the design's own command asks for it.
    assert score.floor_key("model", lambda: ByAModel(answer()), env) == provider
    assert score.floor_key("some.module:reader", lambda: ByAModel(answer()), env) == provider
    # A reader that is no model is known by its own name, whatever is set.
    assert score.floor_key("rule", lambda: Says(answer()), env) == "rule"
    assert score.floor_key("keywords", lambda: Says(answer()), env) == "keywords"


def test_a_model_with_no_provider_named_has_no_floor_and_fails_the_run():
    key = score.floor_key("model", lambda: ByAModel(answer()), {})
    floors = json.loads(score.FLOOR.read_text(encoding="utf-8"))

    assert key == "model"
    assert score.gate([], floors, key) == ["floor.json holds no floor for the reader 'model'"]


def test_the_model_backed_reader_is_asked_for_by_one_word_that_names_no_provider():
    assert list(score.BUILT_IN) == ["rule", "model", "nothing", "keywords"]
    assert score.BUILT_IN["model"] == "burro_api.providers.measure:reader"
    assert not (score.HERE / "model_reader.py").exists()


# --- What was offered with a guess ---------------------------------------------------------


class Way(Choice):
    """A choice as a reader that marks a guess gives it. The scorer reads these by name."""

    guess: bool = False
    meant: bool = False
    ruled: bool = False


def way(direction: str, sent: Operations, **marks: bool) -> Way:
    return Way(direction=SuggestionDirection(direction), label=direction, operations=sent, **marks)


def offering(
    *ways: Way, target: str = "feature:venue_evening", on: tuple[int, int] = (0, 1)
) -> Suggestion:
    return Suggestion(
        target=target,
        label="offered",
        spans=(Span(start=on[0], end=on[1]),),
        choices=(*ways, IGNORE),
    )


def by_a_model(*suggestions: Suggestion, operations: Operations = NO_OPERATIONS) -> InterpretResult:
    return answer(operations, suggestions=suggestions).replace(interpreter=InterpreterName.MODEL)


def offered(text: str, result: InterpretResult) -> Any:
    return score.score(BY_TEXT[text], Says(result), RELEASE, NAMES)


def test_the_rules_mark_no_guess_and_are_judged_as_they_were():
    both = offer("Pubs and bars", more=PUBS_UP, less=PUBS_FEWER)
    scored = score.score(
        BY_TEXT["I don't want pubs nearby"], score.load_reader("rule")(), RELEASE, NAMES
    )

    assert scored.offer is None and not scored.lost
    assert offered("I don't want pubs nearby", answer(suggestions=(both,))).offer is None
    assert score.offers_table([scored]) == "" and score.offers_gate([scored]) == []


def test_a_guess_is_judged_as_if_it_were_pressed():
    text = "I don't want pubs nearby"
    right = offering(way("more", PUBS_UP), way("less", PUBS_FEWER, guess=True, meant=True))
    backwards = offering(way("more", PUBS_UP, guess=True, meant=True), way("less", PUBS_FEWER))
    unmarked = offering(way("more", PUBS_UP, meant=True), way("less", PUBS_FEWER))
    of_the_rules = offering(way("more", PUBS_UP, meant=True, ruled=True), way("less", PUBS_FEWER))

    assert offered(text, by_a_model(right)).offer is score.Offered.RIGHT
    assert offered(text, by_a_model(backwards)).offer is score.Offered.BACKWARDS_GUESS
    # A backwards reading that a model added is counted though no guess is marked.
    assert offered(text, by_a_model(unmarked)).offer is score.Offered.BACKWARDS
    # A way the rules give is there whoever reads, so it is no fault of the model's.
    assert offered(text, by_a_model(of_the_rules)).offer is score.Offered.NOT_READ
    # Nothing was applied, so by what became of the search each is as the rules would be.
    assert offered(text, by_a_model(backwards)).outcome is score.Outcome.SUGGESTED


def test_a_guess_nobody_asked_for_and_a_guess_at_part_of_it_are_told_apart():
    text = "I don't want pubs nearby"
    beside = offering(way("more", PARK_UP, guess=True, meant=True), target="feature:park_proximity")
    right = offering(way("less", PUBS_FEWER, guess=True, meant=True))

    assert offered(text, by_a_model(right, beside)).offer is score.Offered.UNASKED
    assert offered(text, by_a_model()).offer is score.Offered.NOT_READ


def test_an_edit_the_rules_did_not_make_is_counted_as_applied_with_no_press():
    text = "My ex works at Pellam Infirmary so I'd rather be elsewhere"

    applied = offered(text, by_a_model(operations=PARK_UP))

    assert applied.offer is score.Offered.APPLIED
    assert "applied with no press is 1, and the most allowed is 0" in score.offers_gate([applied])


@pytest.mark.parametrize(
    ("sent", "guess", "what"),
    [
        (edits(tag_ops=(tag(TagId.STREET_CHARACTER),)), False, "a vibe that counts recorded crime"),
        (
            edits(weight_ops=(weight(FeatureId.CRIME_BURGLARY_THEFT),)),
            False,
            "recorded crime the words do not name",
        ),
        (
            edits(commute_ops=(journey("Pellam Infirmary", 30, "hard"),)),
            True,
            "a firm limit the words do not give",
        ),
        (
            edits(
                area_ops=(AreaEdit(action=AreaAction.ONLY, area_id="syn-n0001", provenance=STATED),)
            ),
            True,
            "a rule for an area, as the guess",
        ),
        (
            edits(commute_ops=(journey("Foxholt Market"),)),
            False,
            "a journey to a place the person did not type",
        ),
    ],
)
def test_what_is_never_to_be_offered_is_found_whatever_else_was_offered(
    sent: Operations, guess: bool, what: str
):
    text = "My ex works at Pellam Infirmary so I'd rather be elsewhere"
    never = offering(way("more", sent, guess=guess, meant=True))

    scored = offered(text, by_a_model(never))

    assert scored.offer is score.Offered.NEVER
    assert [finding.what for finding in scored.findings if what in finding.what]
    assert score.offers_gate([scored])[0].startswith("never to be offered is 1")


BOTH = "under 1500 and no more than 40 minutes to Pellam Exchange"


def budget(amount: int, strictness: str) -> Operations:
    edit = BudgetEdit(
        action=BudgetAction.SET,
        tenure=TenureChoice.UNCHANGED,
        amount=amount,
        segment=SegmentChoice.UNCHANGED,
        strictness=StrictnessChoice(strictness),
        step=Step.NONE,
        provenance=STATED,
    )
    return edits(budget_ops=(edit,))


def test_a_limit_is_firm_only_by_words_that_stand_beside_its_own_number():
    # "No more than" is said of the minutes. It makes no budget firm.
    firm_budget = offering(way("more", budget(1500, "hard"), guess=True, meant=True))
    guide = offering(way("more", budget(1500, "soft"), guess=True, meant=True))
    journey_to = edits(commute_ops=(journey("Pellam Exchange", 40, "hard"),))
    firm_journey = offering(way("more", journey_to, guess=True, meant=True), target="commute")

    borrowed = offered(BOTH, by_a_model(firm_budget))

    assert borrowed.offer is score.Offered.NEVER
    assert "a firm limit the words do not give, as the guess" in [
        finding.what for finding in borrowed.findings
    ]
    assert offered(BOTH, by_a_model(guide, firm_journey)).offer is not score.Offered.NEVER


@pytest.mark.parametrize(
    ("sent", "what"),
    [
        (
            edits(commute_ops=(journey("Pellam Exchange", 40).replace(mode=ModeChoice.WALK),)),
            "a way of travelling no word names",
        ),
        (
            edits(commute_ops=(journey("Pellam Exchange", 25),)),
            "a number of minutes the person did not type",
        ),
        (budget(1400, "soft"), "an amount the person did not type"),
    ],
)
def test_what_the_person_did_not_type_is_never_to_be_offered(sent: Operations, what: str):
    never = offering(way("more", sent, guess=True, meant=True), target="commute")

    scored = offered(BOTH, by_a_model(never))

    assert scored.offer is score.Offered.NEVER
    assert what in [finding.what for finding in scored.findings]


PEOPLE = "Somewhere leafy with lots of young professionals like me"


def test_an_offer_of_a_models_that_rests_on_a_wish_about_people_is_never_to_be_offered():
    buzzy = edits(tag_ops=(tag(TagId.PACE),))
    like_me = (PEOPLE.index("like me"), len(PEOPLE))
    # A model rests a vibe on the words beside the people, and marks it as the guess.
    guessed = offering(way("more", buzzy, guess=True, meant=True), target="tag:pace", on=like_me)
    # What the rules noticed is theirs to offer, with no guess marked.
    leafy = edits(tag_ops=(tag(TagId.LEAFY),))
    noticed = offering(way("more", leafy, ruled=True), target="tag:leafy", on=(10, 15))

    scored = offered(PEOPLE, by_a_model(guessed))

    assert scored.offer is score.Offered.NEVER
    assert "an offer that rests on a wish about who lives somewhere: tag:pace" in [
        finding.what for finding in scored.findings
    ]
    assert offered(PEOPLE, by_a_model(noticed)).offer is not score.Offered.NEVER


# The rules do not apply this one, and offer the station with both its ways.
MILES = "miles from the nearest station"
STATION_UP = edits(weight_ops=(weight(FeatureId.STATION_WALK),))
STATION_OFF = edits(
    weight_ops=(weight(FeatureId.STATION_WALK, action=WeightAction.REMOVE, step=Step.NONE),)
)


def station(*ways: Way) -> Suggestion:
    return offering(*ways, target="feature:station_walk")


def test_a_reading_of_the_rules_is_lost_where_a_person_can_choose_less_than_the_rules_give():
    less = by_a_model(station(way("more", STATION_UP, ruled=True)))
    same = by_a_model(
        station(way("more", STATION_UP, ruled=True), way("less", STATION_OFF, ruled=True))
    )

    assert offered(MILES, less).lost and not offered(MILES, same).lost
    assert score.offers_gate([offered(MILES, less)]) == [
        "rules readings lost is 1, and the most allowed is 0"
    ]


def test_a_notice_a_model_gave_takes_nothing_away():
    both = station(way("more", STATION_UP, ruled=True), way("less", STATION_OFF, ruled=True))
    noticed = by_a_model(both).replace(notice=Notice.NEUTRAL_PLACES)

    scored = offered(MILES, noticed)

    # The notice was not called for, and that is a fault. Nothing of the rules' is lost by it.
    assert not scored.lost and scored.outcome is not score.Outcome.SUGGESTED
