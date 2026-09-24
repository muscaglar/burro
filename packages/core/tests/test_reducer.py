import dataclasses
import json
import random
from typing import Any

import pytest
from burro_core.ids import (
    AreaRuleKind,
    Direction,
    FeatureId,
    Mode,
    OpsGroup,
    Provenance,
    RejectReason,
    Segment,
    Step,
    Strictness,
    TagId,
    Tenure,
)
from burro_core.ops import (
    NO_OPERATIONS,
    AreaEdit,
    BudgetEdit,
    CommuteEdit,
    Operations,
    SettingEdit,
    TagEdit,
    WeightEdit,
)
from burro_core.rank import rank
from burro_core.reducer import ReducerResult, apply, nudged_amount, nudged_weight
from burro_core.spec import (
    DEFAULT_WEIGHTS,
    GIVE_WAY_TO_ONE_IN,
    LIMITS,
    MENTION_WEIGHT,
    FeatureWeight,
    PreferenceSpec,
    TagWeight,
    canonical,
    check_spec,
    default_spec,
    given_way,
    spec_hash,
)
from pydantic import ValidationError

from .support import area_id, draws, place_id, small_release

RENTER = default_spec(Tenure.RENT)
BUYER = default_spec(Tenure.BUY)


def budget(action: str = "set", **given: Any) -> BudgetEdit:
    blank = {
        "tenure": "unchanged",
        "amount": 0,
        "segment": "unchanged",
        "strictness": "unchanged",
        "step": "none",
        "provenance": "stated",
    }
    return BudgetEdit.model_validate({"action": action} | blank | given)


def commute(action: str, place: int | str, **given: Any) -> CommuteEdit:
    blank = {
        "mode": "unchanged",
        "max_minutes": 0,
        "strictness": "unchanged",
        "step": "none",
        "provenance": "stated",
    }
    chosen = place_id(place) if isinstance(place, int) else place
    return CommuteEdit.model_validate({"action": action, "place_id": chosen} | blank | given)


def weight(action: str, feature_id: str, **given: Any) -> WeightEdit:
    blank = {"value": 0.0, "step": "none", "direction": "default", "provenance": "stated"}
    return WeightEdit.model_validate({"action": action, "feature_id": feature_id} | blank | given)


def tag(action: str, tag_id: str, **given: Any) -> TagEdit:
    blank = {"value": 0.0, "step": "none", "provenance": "stated"}
    return TagEdit.model_validate({"action": action, "tag_id": tag_id} | blank | given)


def area(action: str, number: int | str, provenance: str = "stated") -> AreaEdit:
    chosen = area_id(number) if isinstance(number, int) else number
    return AreaEdit.model_validate({"action": action, "area_id": chosen, "provenance": provenance})


def setting(action: str, name: str, **given: Any) -> SettingEdit:
    blank = {"choice": "none", "value": 0.0, "step": "none", "provenance": "stated"}
    return SettingEdit.model_validate({"action": action, "setting": name} | blank | given)


Edit = BudgetEdit | CommuteEdit | WeightEdit | TagEdit | AreaEdit | SettingEdit
GROUPS: dict[type, str] = {
    BudgetEdit: "budget_ops",
    CommuteEdit: "commute_ops",
    WeightEdit: "weight_ops",
    TagEdit: "tag_ops",
    AreaEdit: "area_ops",
    SettingEdit: "setting_ops",
}


def ops(*edits: Edit) -> Operations:
    groups: dict[str, list[Edit]] = {name: [] for name in GROUPS.values()}
    for edit in edits:
        groups[GROUPS[type(edit)]].append(edit)
    return Operations.model_validate({name: tuple(found) for name, found in groups.items()})


def run(spec: PreferenceSpec, *edits: Edit) -> ReducerResult:
    return apply(spec, ops(*edits), small_release())


def reasons(result: ReducerResult) -> list[RejectReason]:
    return [r.reason for r in result.rejected]


def weights(spec: PreferenceSpec) -> dict[str, float]:
    return {w.feature_id.value: w.weight for w in spec.weights}


def asked_for(spec: PreferenceSpec) -> dict[str, float]:
    """The weights that count: every entry but one that records a weight taken off."""
    return {w.feature_id.value: w.weight for w in spec.active_weights}


def test_slider_and_chat_edits_reach_the_same_spec():
    # A slider sets a number and says so. Chat asks for a step. Both go
    # through the one reducer, and only the provenance tells them apart.
    slider = run(
        RENTER,
        tag("set", "leafy", value=0.5, provenance="ui_edit"),
        weight("set", "park_proximity", value=0.5, provenance="ui_edit"),
        weight("set", "air_no2", value=0.0, provenance="ui_edit"),
        budget(amount=1800, provenance="ui_edit"),
        commute("add", 2, mode="pt", max_minutes=45, strictness="soft", provenance="ui_edit"),
    ).spec
    chat = run(
        RENTER,
        tag("nudge", "leafy", step="up_large"),
        weight("nudge", "park_proximity", step="up_large"),
        weight("remove", "air_no2"),
        budget(amount=1800),
        commute("add", 2),
    ).spec

    assert canonical(slider) == canonical(chat)
    assert spec_hash(slider) == spec_hash(chat)
    assert slider.tags[0].provenance is Provenance.UI_EDIT
    assert chat.tags[0].provenance is Provenance.STATED
    assert check_spec(chat, small_release()) == ()


def test_bad_edit_is_rejected_and_the_rest_applied():
    result = run(
        RENTER,
        commute("add", 1, max_minutes=30),
        commute("add", "syn-p0099"),
        commute("add", ""),
        weight("set", "green_cover", value=0.4),
        weight("set", "noise_exposure", value=0.4, direction="more"),
        area("exclude", 3),
        area("exclude", 99),
    )
    assert [(r.group, r.index, r.reason) for r in result.rejected] == [
        (OpsGroup.COMMUTE, 1, RejectReason.UNKNOWN_PLACE),
        (OpsGroup.COMMUTE, 2, RejectReason.UNKNOWN_PLACE),
        (OpsGroup.WEIGHT, 1, RejectReason.DIRECTION_NOT_ALLOWED),
        (OpsGroup.AREA, 1, RejectReason.UNKNOWN_AREA),
    ]
    assert [(a.group, a.index, a.changed) for a in result.applied] == [
        (OpsGroup.COMMUTE, 0, True),
        (OpsGroup.WEIGHT, 0, True),
        (OpsGroup.AREA, 0, True),
    ]
    assert [c.place_id for c in result.spec.commutes] == [place_id(1)]
    assert weights(result.spec)["green_cover"] == 0.4
    # Nothing is half-applied: the rejected weight is what it would have been without the edit.
    without = run(RENTER, commute("add", 1, max_minutes=30)).spec
    noise = next(w for w in result.spec.weights if w.feature_id is FeatureId.NOISE_EXPOSURE)
    assert noise == next(w for w in without.weights if w.feature_id is FeatureId.NOISE_EXPOSURE)
    assert (noise.direction, noise.provenance) == (Direction.LESS, Provenance.DEFAULT)
    assert [a.area_id for a in result.spec.areas] == [area_id(3)]


@pytest.mark.parametrize("feature_id", ["crime_violence_robbery", "crime_burglary_theft"])
@pytest.mark.parametrize(
    "edit",
    [{"action": "set", "value": 0.5}, {"action": "nudge", "step": "up_small"}],
    ids=["set", "nudge"],
)
def test_inferred_crime_weight_is_rejected(feature_id: str, edit: dict[str, Any]):
    inferred = run(RENTER, weight(feature_id=feature_id, provenance="inferred", **edit))
    assert reasons(inferred) == [RejectReason.CRIME_NEEDS_EXPLICIT_REQUEST]
    assert inferred.spec == RENTER

    # Asked for in words, or moved with its control, it is weighted.
    for provenance in ("stated", "ui_edit"):
        asked = run(RENTER, weight(feature_id=feature_id, provenance=provenance, **edit))
        assert asked.rejected == ()
        assert weights(asked.spec)[feature_id] > 0


def test_an_inferred_edit_may_turn_crime_down_to_nothing_but_not_leave_it_on():
    on = run(RENTER, weight("set", "crime_burglary_theft", value=0.5)).spec
    lower = run(
        on, weight("nudge", "crime_burglary_theft", step="down_small", provenance="inferred")
    )
    assert reasons(lower) == [RejectReason.CRIME_NEEDS_EXPLICIT_REQUEST]
    off = run(on, weight("remove", "crime_burglary_theft", provenance="inferred"))
    assert "crime_burglary_theft" not in weights(off.spec)


def test_crime_is_off_until_it_is_asked_for():
    assert not {"crime_violence_robbery", "crime_burglary_theft"} & set(weights(RENTER))
    assert not {"crime_violence_robbery", "crime_burglary_theft"} & set(weights(BUYER))


def test_a_step_moves_the_number_unless_it_is_at_a_limit():
    # At 50,000 a step of 5% is 2,500, half a unit, which rounds back to where it started.
    assert round(50_000 * 1.05 / 5_000) * 5_000 == 50_000
    buyer = run(BUYER, budget(amount=50_000)).spec
    up = run(buyer, budget("nudge", step="up_small"))
    assert up.spec.budget.amount == 55_000
    assert up.applied[0].changed

    # Already at the lower limit, a step down is in order and changes nothing.
    down = run(buyer, budget("nudge", step="down_small"))
    assert down.spec == buyer
    assert (down.rejected, down.applied[0].changed) == ((), False)


@pytest.mark.parametrize(
    ("tenure", "amount", "step", "moved"),
    [
        (Tenure.RENT, 1800, Step.UP_SMALL, 1900),  # 1,890 to the nearest 25
        (Tenure.RENT, 1800, Step.UP_LARGE, 2075),  # 2,070
        (Tenure.RENT, 1800, Step.DOWN_SMALL, 1700),  # 1,710
        (Tenure.RENT, 1800, Step.DOWN_LARGE, 1525),  # 1,530
        (Tenure.RENT, 300, Step.DOWN_LARGE, 300),
        (Tenure.RENT, 310, Step.DOWN_SMALL, 300),
        (Tenure.RENT, 20_000, Step.UP_SMALL, 20_000),
        (Tenure.RENT, 19_500, Step.UP_LARGE, 20_000),
        (Tenure.BUY, 450_000, Step.UP_SMALL, 470_000),  # 472,500 is a tie and goes to the even
        (Tenure.BUY, 450_000, Step.DOWN_LARGE, 380_000),  # 382,500 likewise
        (Tenure.BUY, 52_000, Step.DOWN_SMALL, 50_000),
        (Tenure.BUY, 20_000_000, Step.UP_LARGE, 20_000_000),
    ],
)
def test_a_budget_step_is_a_share_rounded_to_its_unit(
    tenure: Tenure, amount: int, step: Step, moved: int
):
    assert nudged_amount(amount, step, tenure) == moved


@pytest.mark.parametrize("tenure", list(Tenure))
def test_a_budget_step_always_moves_the_right_way_and_stays_within_its_limits(tenure: Tenure):
    limits = LIMITS.money(tenure)
    draw = draws(31)
    for _ in range(400):
        amount = draw.randrange(limits.minimum, min(limits.maximum, limits.minimum * 40) + 1)
        for step in (Step.UP_SMALL, Step.UP_LARGE, Step.DOWN_SMALL, Step.DOWN_LARGE):
            moved = nudged_amount(amount, step, tenure)
            assert limits.minimum <= moved <= limits.maximum
            up = step in (Step.UP_SMALL, Step.UP_LARGE)
            at_limit = amount == (limits.maximum if up else limits.minimum)
            assert moved == amount if at_limit else (moved > amount if up else moved < amount)
            assert moved % limits.unit == 0 or moved in (limits.minimum, limits.maximum)


@pytest.mark.parametrize(
    ("before", "step", "after"),
    [
        (0.0, Step.UP_SMALL, 0.10),
        (0.0, Step.UP_LARGE, 0.25),
        (0.30, Step.DOWN_SMALL, 0.20),
        (0.30, Step.DOWN_LARGE, 0.05),
        (0.20, Step.DOWN_LARGE, 0.0),
        (0.95, Step.UP_SMALL, 1.0),
        (1.0, Step.UP_LARGE, 1.0),
        (0.0, Step.DOWN_SMALL, 0.0),
    ],
)
def test_a_weight_step_is_bounded(before: float, step: Step, after: float):
    assert nudged_weight(before, step) == after


def test_ten_small_steps_up_from_nothing_reach_exactly_one():
    stepped = 0.0
    for _ in range(10):
        stepped = nudged_weight(stepped, Step.UP_SMALL)
    assert stepped == 1.0
    # Through the reducer the first step is a mention, which is worth a half, so five more do it.
    spec = RENTER
    for reached in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.0):
        spec = run(spec, tag("nudge", "leafy", step="up_small")).spec
        assert spec.tags[0].weight == reached
    for _ in range(10):
        spec = run(spec, tag("nudge", "leafy", step="down_small")).spec
    assert spec.tags == ()


# A quarter of each default, rounded down to a whole step and never under one:
# 0.35 in all for a renter and 0.45 for a buyer, against the 0.50 of one mention.
GIVEN_WAY = {
    Tenure.RENT: {
        "station_walk": 0.10,
        "station_lines": 0.05,
        "park_proximity": 0.05,
        "highstreet_access": 0.05,
        "noise_exposure": 0.05,
        "air_no2": 0.05,
    },
    Tenure.BUY: {
        "station_walk": 0.10,
        "park_proximity": 0.10,
        "green_cover": 0.05,
        "highstreet_access": 0.05,
        "noise_exposure": 0.05,
        "station_lines": 0.05,
        "air_no2": 0.05,
    },
}


def defaults_of(spec: PreferenceSpec) -> dict[str, float]:
    """The weights of the spec that nobody chose."""
    return {
        w.feature_id.value: w.weight for w in spec.weights if w.provenance is Provenance.DEFAULT
    }


@pytest.mark.parametrize("step", ["up_small", "up_large"])
def test_a_thing_simply_named_is_worth_a_half(step: str):
    # "Pubs" is a large step and "more pubs" a small one. On something with no
    # weight yet, the second counts for as much as the first.
    named = run(
        RENTER, tag("nudge", "leafy", step=step), weight("nudge", "venue_evening", step=step)
    )
    assert named.rejected == ()
    assert MENTION_WEIGHT == 0.5
    assert [(t.tag_id, t.weight, t.provenance) for t in named.spec.tags] == [
        ("leafy", 0.5, Provenance.STATED)
    ]
    assert weights(named.spec)["venue_evening"] == 0.5
    # A default is nobody's choice, so naming what has one is worth the same.
    park = run(RENTER, weight("nudge", "park_proximity", step=step)).spec
    assert weights(park)["park_proximity"] == 0.5
    assert "park_proximity" not in defaults_of(park)


def test_a_step_from_a_weight_the_person_chose_is_a_step_and_no_more():
    chosen = run(RENTER, tag("set", "leafy", value=0.2), weight("set", "green_cover", value=0.2))
    up = run(
        chosen.spec,
        tag("nudge", "leafy", step="up_small"),
        weight("nudge", "green_cover", step="up_large"),
    ).spec
    assert (up.tags[0].weight, weights(up)["green_cover"]) == (0.3, 0.45)
    # A mention never lowers a weight that is already above it.
    high = run(RENTER, tag("set", "leafy", value=0.9, provenance="inferred")).spec
    assert run(high, tag("nudge", "leafy", step="up_small")).spec.tags[0].weight == 1.0


@pytest.mark.parametrize("tenure", list(Tenure))
def test_the_defaults_give_way_the_first_time_a_wish_is_applied(tenure: Tenure):
    start = default_spec(tenure)
    assert sum(weights(start).values()) == pytest.approx(1.8 if tenure is Tenure.RENT else 2.1)
    wished = run(start, tag("nudge", "leafy", step="up_large"))
    assert [a.changed for a in wished.applied] == [True]
    # Each is a quarter of what it was, rounded down to a step. What was said now counts for more.
    assert weights(wished.spec) == defaults_of(wished.spec) == GIVEN_WAY[tenure]
    assert wished.spec.tags[0].weight > max(GIVEN_WAY[tenure].values())
    # The spec itself changed, so its hash did, and ranking is still a function of the spec.
    only_the_tag = start.replace(tags=wished.spec.tags)
    assert spec_hash(wished.spec) != spec_hash(only_the_tag)
    assert rank(wished.spec, small_release()) != rank(only_the_tag, small_release())
    # The budget and the commute settings are not weights of that kind. They stay.
    assert (wished.spec.budget, wished.spec.commute_weight) == (start.budget, 1.0)
    assert check_spec(wished.spec, small_release()) == ()


def every_single_wish() -> list[Edit]:
    """Each feature and each tag, simply named: one mention and nothing else."""
    named: list[Edit] = [
        weight("nudge", feature_id.value, step=step)
        for feature_id in FeatureId
        for step in ("up_small", "up_large")
    ]
    named += [
        tag("nudge", tag_id.value, step=step)
        for tag_id in TagId
        for step in ("up_small", "up_large")
    ]
    return named


@pytest.mark.parametrize("tenure", list(Tenure))
def test_one_stated_wish_outweighs_everything_that_was_left_unsaid(tenure: Tenure):
    # A third left a renter 0.55 unsaid and a buyer 0.70, against the 0.50 of
    # one mention, so the area the defaults liked best still came first.
    assert sum(GIVEN_WAY[tenure].values()) < MENTION_WEIGHT
    for edit in every_single_wish():
        wished = run(default_spec(tenure), edit).spec
        unsaid = sum(defaults_of(wished).values())
        said = sum(w.weight for w in wished.weights if w.provenance is not Provenance.DEFAULT)
        said += sum(t.weight for t in wished.tags)
        assert said == MENTION_WEIGHT, edit
        assert unsaid < said, edit


@pytest.mark.parametrize(
    ("default", "gives_way_to"),
    [
        *[(0.05, 0.05), (0.15, 0.05), (0.2, 0.05), (0.3, 0.05), (0.35, 0.05), (0.4, 0.1)],
        *[(0.5, 0.1), (0.55, 0.1), (0.6, 0.15), (0.8, 0.2), (1.0, 0.25), (0.0, 0.0)],
    ],
)
def test_a_default_gives_way_to_a_quarter_in_whole_steps(default: float, gives_way_to: float):
    # Counted in steps of 0.05 and rounded down, so that no float decides it:
    # 0.3 / 4 is 0.075, and whether that is nearer 0.05 or 0.10 is not left to chance.
    assert given_way(default) == gives_way_to
    assert GIVE_WAY_TO_ONE_IN == 4


def test_the_defaults_give_way_once():
    once = run(RENTER, tag("nudge", "leafy", step="up_large")).spec
    again = run(once, tag("nudge", "buzzy", step="up_large"), budget(amount=1500)).spec
    assert defaults_of(again) == defaults_of(once) == GIVEN_WAY[Tenure.RENT]
    more = run(again, weight("set", "green_cover", value=0.3, provenance="ui_edit")).spec
    assert defaults_of(more) == GIVEN_WAY[Tenure.RENT]


WISHES: list[Edit] = [
    budget(amount=1500),
    budget(segment="studio", provenance="ui_edit"),
    commute("add", 1),
    weight("set", "green_cover", value=0.4, provenance="ui_edit"),
    weight("nudge", "culture_venues", step="up_small", provenance="inferred"),
    weight("remove", "station_walk", provenance="ui_edit"),
    tag("set", "buzzy", value=1.0, provenance="ui_edit"),
    area("exclude", 2),
    setting("set", "pt_basis", choice="just_missed", provenance="ui_edit"),
    setting("set", "budget_weight", value=0.5, provenance="ui_edit"),
]


@pytest.mark.parametrize("edit", WISHES, ids=lambda e: f"{type(e).__name__}-{e.action}")
def test_a_wish_of_any_kind_from_words_or_from_a_control_makes_the_defaults_give_way(edit: Edit):
    result = run(RENTER, edit)
    assert [a.changed for a in result.applied] == [True]
    expected = dict(GIVEN_WAY[Tenure.RENT])
    if isinstance(edit, WeightEdit):
        expected.pop(edit.feature_id.value, None)
    assert defaults_of(result.spec) == expected


@pytest.mark.parametrize(
    "edit",
    [
        commute("add", "syn-p0099"),
        weight("set", "green_cover", value=1.2),
        weight("set", "crime_burglary_theft", value=0.5, provenance="inferred"),
        weight("remove", "green_cover"),
        weight("nudge", "green_cover", step="down_small"),
        tag("remove", "leafy"),
        area("clear", 1),
        budget("clear"),
        budget(tenure="rent"),
        setting("set", "commute_combine", choice="slowest"),
    ],
    ids=lambda e: f"{type(e).__name__}-{e.action}",
)
def test_an_edit_that_is_turned_away_or_changes_nothing_leaves_the_defaults_as_they_were(
    edit: Edit,
):
    result = run(RENTER, edit)
    assert not [a for a in result.applied if a.changed]
    assert result.spec == RENTER
    assert spec_hash(result.spec) == spec_hash(RENTER)


def test_a_default_the_person_has_touched_is_theirs_and_does_not_give_way():
    # Moved to the very number the default gave, it is still a choice.
    kept = run(RENTER, weight("set", "park_proximity", value=0.3, provenance="ui_edit"))
    assert [a.changed for a in kept.applied] == [True]
    park = next(w for w in kept.spec.weights if w.feature_id is FeatureId.PARK_PROXIMITY)
    assert (park.weight, park.provenance) == (0.3, Provenance.UI_EDIT)
    # And so is one moved to the number it would have given way to.
    low = run(RENTER, weight("set", "park_proximity", value=0.1, provenance="ui_edit"))
    assert [a.changed for a in low.applied] == [True]
    park = next(w for w in low.spec.weights if w.feature_id is FeatureId.PARK_PROXIMITY)
    assert (park.weight, park.provenance) == (0.1, Provenance.UI_EDIT)
    assert "park_proximity" not in defaults_of(low.spec)
    later = run(low.spec, tag("nudge", "leafy", step="up_large")).spec
    assert weights(later)["park_proximity"] == 0.1


def test_caring_less_about_a_default_starts_from_where_it_gave_way_to():
    # Parks at 0.30 by default give way to 0.05, and a small step down from there is nothing.
    less = run(RENTER, weight("nudge", "park_proximity", step="down_small"))
    assert [a.changed for a in less.applied] == [True]
    assert "park_proximity" not in asked_for(less.spec)
    # The walk to a station gives way from 0.50 to 0.10, and not from 0.50 to 0.40.
    station = run(BUYER, weight("set", "station_walk", value=0.5, provenance="ui_edit")).spec
    assert (
        asked_for(run(station, weight("nudge", "station_walk", step="down_small")).spec)[
            "station_walk"
        ]
        == 0.4
    )
    assert "station_walk" not in asked_for(
        run(BUYER, weight("nudge", "station_walk", step="down_small")).spec
    )


def test_a_default_weight_that_is_not_a_default_of_the_tenure_is_left_as_it_is():
    # A spec from the wire can hold anything. What has no default has nothing to give way to.
    odd = RENTER.replace(
        weights=(
            *RENTER.weights,
            FeatureWeight(
                feature_id=FeatureId.CULTURE_VENUES,
                weight=0.7,
                direction=Direction.MORE,
                provenance=Provenance.DEFAULT,
            ),
        ),
        tags=(TagWeight(tag_id=TagId.LEAFY, weight=0.9, provenance=Provenance.DEFAULT),),
    )
    after = run(odd, budget(amount=1500)).spec
    assert weights(after) == GIVEN_WAY[Tenure.RENT] | {"culture_venues": 0.7}
    assert after.tags == odd.tags


def test_switching_to_buying_resets_what_nobody_chose_to_the_buyers_default():
    buyer = run(RENTER, budget(tenure="buy"))
    assert buyer.rejected == ()
    assert (buyer.spec.tenure, buyer.spec.tenure_from) == (Tenure.BUY, Provenance.STATED)
    assert (buyer.spec.budget.amount, buyer.spec.budget.segment) == (None, Segment.FLAT)
    # The buyer's defaults, which hold green cover and weigh parks more. The
    # switch is itself a wish, so they have given way.
    assert weights(buyer.spec) == defaults_of(buyer.spec) == GIVEN_WAY[Tenure.BUY]
    assert [w.direction for w in buyer.spec.weights] == [
        w.direction for w in default_spec(Tenure.BUY).weights
    ]
    assert check_spec(buyer.spec, small_release()) == ()
    # And back again.
    renter = run(buyer.spec, budget(tenure="rent", provenance="ui_edit")).spec
    assert weights(renter) == defaults_of(renter) == GIVEN_WAY[Tenure.RENT]
    assert renter.budget.segment is Segment.BED_1


def test_switching_tenure_keeps_everything_the_person_set():
    renter = run(
        RENTER,
        budget(amount=1800, segment="bed_2", strictness="hard"),
        commute("add", 1, max_minutes=30),
        weight("set", "park_proximity", value=0.7),
        weight("nudge", "venue_evening", step="up_large", direction="less"),
        weight("remove", "station_lines"),
        tag("nudge", "leafy", step="up_large", provenance="inferred"),
        area("exclude", 3),
        setting("set", "pt_basis", choice="just_missed", provenance="ui_edit"),
        setting("set", "budget_weight", value=0.6, provenance="ui_edit"),
    ).spec
    buyer = run(renter, budget(tenure="buy", provenance="ui_edit")).spec

    chosen = {w.feature_id.value: (w.weight, w.direction, w.provenance) for w in buyer.weights}
    assert chosen["park_proximity"] == (0.7, Direction.LESS, Provenance.STATED)
    assert chosen["venue_evening"] == (0.5, Direction.LESS, Provenance.STATED)
    assert buyer.tags == renter.tags
    assert (buyer.commutes, buyer.areas) == (renter.commutes, renter.areas)
    assert (buyer.pt_basis, buyer.pt_basis_from) == ("just_missed", Provenance.UI_EDIT)
    assert (buyer.budget.strictness, buyer.budget.weight) == (Strictness.HARD, 0.6)
    # What nobody chose is the buyer's default now, less what the person set
    # for themselves and what they took off: the lines, which a buyer's
    # default would weigh, stay off.
    expected = dict(GIVEN_WAY[Tenure.BUY])
    del expected["park_proximity"]
    del expected["station_lines"]
    assert defaults_of(buyer) == expected
    assert "station_lines" not in asked_for(buyer)
    # A rent is not a price and no segment suits both, so those two cannot be kept.
    assert (buyer.budget.amount, buyer.budget.segment) == (None, Segment.FLAT)


def test_switching_tenure_resets_a_setting_that_is_still_at_its_default():
    # Only a spec from the wire can hold a setting that differs from its
    # default and is still marked as nobody's choice.
    odd = RENTER.replace(commute_combine="mean", commute_weight=0.4, pt_basis="just_missed")
    odd = odd.replace(pt_basis_from=Provenance.STATED)
    buyer = run(odd, budget(tenure="buy")).spec
    assert (buyer.commute_combine, buyer.commute_weight) == ("slowest", 1.0)
    assert (buyer.pt_basis, buyer.pt_basis_from) == ("just_missed", Provenance.STATED)


def test_switching_tenure_leaves_out_a_default_the_release_cannot_rank():
    release = small_release()
    partial = dataclasses.replace(
        release, metrics=tuple(m for m in release.metrics if m.feature_id != "green_cover")
    )
    buyer = apply(RENTER, ops(budget(tenure="buy")), partial).spec
    assert "green_cover" not in weights(buyer)
    assert check_spec(buyer, partial) == ()


def test_the_reducer_is_the_only_way_a_spec_changes():
    with pytest.raises(ValidationError):
        RENTER.commute_weight = 0.2  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(ValidationError):
        RENTER.budget.amount = 1  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises((TypeError, AttributeError)):
        RENTER.weights.append(RENTER.weights[0])  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]

    before = RENTER.model_dump_json()
    result = run(RENTER, budget(amount=1500), weight("remove", "air_no2"), commute("add", 1))
    # The spec that went in is as it was. The result is a new one.
    assert RENTER.model_dump_json() == before
    assert result.spec is not RENTER
    assert result.spec != RENTER


def test_undo_is_keeping_the_spec_from_before_and_a_step_back_returns_to_it():
    history = [RENTER]
    edits: list[Edit] = [
        budget(amount=1600, segment="bed_2"),
        commute("add", 1, max_minutes=35),
        tag("nudge", "leafy", step="up_large"),
        weight("nudge", "park_proximity", step="up_small"),
        area("exclude", 2),
        setting("set", "pt_basis", choice="just_missed"),
    ]
    for edit in edits:
        history.append(run(history[-1], edit).spec)
    assert len({spec_hash(spec) for spec in history}) == len(history)
    # Every earlier spec is still there, unchanged, to go back to. That is what undo is.
    assert history[0] == default_spec(Tenure.RENT)
    assert run(history[2], edits[2]).spec == history[3]

    # Taking each thing off again gets back to a search that asks for nothing
    # but the defaults. They have given way by then, and they stay so: only
    # the spec from before is the search from before.
    undone = run(
        history[-1],
        budget("clear"),
        budget(segment="bed_1"),
        commute("remove", 1),
        tag("remove", "leafy"),
        weight("remove", "park_proximity"),
        area("clear", 2),
        setting("set", "pt_basis", choice="typical"),
    )
    assert undone.rejected == ()
    gone = run(RENTER, weight("remove", "park_proximity")).spec
    assert canonical(undone.spec) == canonical(gone)
    assert spec_hash(undone.spec) != spec_hash(RENTER)


def test_the_same_edits_give_the_same_spec_every_time():
    edits = ops(budget(amount=1500), commute("add", 3), tag("set", "buzzy", value=0.6))
    first = apply(RENTER, edits, small_release())
    assert all(apply(RENTER, edits, small_release()) == first for _ in range(50))


def test_groups_apply_in_a_fixed_order_and_a_later_edit_wins():
    # The setting is given first here, and is still applied after the commute.
    result = apply(
        RENTER,
        Operations(
            setting_ops=(setting("set", "commute_weight", value=0.5),),
            area_ops=(),
            tag_ops=(),
            weight_ops=(
                weight("set", "green_cover", value=0.2),
                weight("set", "green_cover", value=0.7),
            ),
            commute_ops=(commute("add", 1), commute("update", 1, max_minutes=20)),
            budget_ops=(budget(amount=1000), budget(amount=1200)),
        ),
        small_release(),
    )
    assert [a.group for a in result.applied] == [
        OpsGroup.BUDGET,
        OpsGroup.BUDGET,
        OpsGroup.COMMUTE,
        OpsGroup.COMMUTE,
        OpsGroup.WEIGHT,
        OpsGroup.WEIGHT,
        OpsGroup.SETTING,
    ]
    assert result.spec.budget.amount == 1200
    assert result.spec.commutes[0].max_minutes == 20
    assert weights(result.spec)["green_cover"] == 0.7


def test_no_edits_change_nothing():
    assert apply(RENTER, NO_OPERATIONS, small_release()) == ReducerResult(
        spec=RENTER, applied=(), rejected=()
    )


def test_changing_tenure_clears_the_amount_and_resets_the_segment():
    renter = run(RENTER, budget(amount=1800, segment="bed_2", strictness="hard")).spec
    buyer = run(renter, budget(tenure="buy", provenance="ui_edit")).spec
    assert (buyer.tenure, buyer.tenure_from) == (Tenure.BUY, Provenance.UI_EDIT)
    assert (buyer.budget.amount, buyer.budget.segment) == (None, Segment.FLAT)
    # What is not about the kind of home stays: strictness and weight.
    assert buyer.budget.strictness is Strictness.HARD
    assert check_spec(buyer, small_release()) == ()


def test_changing_tenure_keeps_what_the_same_edit_supplies():
    buyer = run(RENTER, budget(tenure="buy", amount=450_000, segment="terraced")).spec
    assert (buyer.tenure, buyer.budget.amount) == (Tenure.BUY, 450_000)
    assert buyer.budget.segment is Segment.TERRACED


def test_naming_the_tenure_already_chosen_clears_nothing():
    renter = run(RENTER, budget(amount=1800)).spec
    again = run(renter, budget(tenure="rent"))
    assert again.spec == renter
    assert [a.changed for a in again.applied] == [False]


def test_clearing_a_budget_touches_nothing_else():
    renter = run(RENTER, budget(amount=1800, segment="studio", strictness="hard")).spec
    cleared = run(renter, budget("clear", amount=5, segment="bed_3", tenure="buy")).spec
    assert cleared.budget == renter.budget.replace(amount=None)
    assert cleared.tenure is Tenure.RENT


def test_a_commute_added_without_detail_takes_the_defaults():
    added = run(RENTER, commute("add", 1)).spec.commutes[0]
    assert (added.mode, added.max_minutes, added.strictness) == (Mode.PT, 45, Strictness.SOFT)
    assert added.provenance is Provenance.STATED


def test_adding_a_place_already_in_the_spec_updates_it():
    once = run(RENTER, commute("add", 1, max_minutes=30)).spec
    twice = run(once, commute("add", 1, mode="cycle", strictness="hard"))
    assert twice.rejected == ()
    assert len(twice.spec.commutes) == 1
    updated = twice.spec.commutes[0]
    assert (updated.mode, updated.max_minutes, updated.strictness) == ("cycle", 30, "hard")

    # Said again with nothing new, it is in order and changes nothing.
    again = run(once, commute("add", 1))
    assert (again.spec, again.rejected, again.applied[0].changed) == (once, (), False)


def test_a_fourth_commute_is_rejected():
    result = run(RENTER, *(commute("add", n) for n in range(1, 5)))
    assert reasons(result) == [RejectReason.TOO_MANY_COMMUTES]
    assert [c.place_id for c in result.spec.commutes] == [place_id(n) for n in (1, 2, 3)]


def test_a_commute_step_moves_the_cap_and_stops_at_the_cutoff():
    spec = run(RENTER, commute("add", 1, mode="walk", max_minutes=50)).spec
    up = run(spec, commute("update", 1, step="up_large")).spec
    # The release routed walks up to 60 minutes, so the cap may go no higher.
    assert up.commutes[0].max_minutes == 60
    assert run(up, commute("update", 1, step="up_small")).applied[0].changed is False
    assert run(spec, commute("update", 1, step="down_small")).spec.commutes[0].max_minutes == 45
    low = run(spec, commute("update", 1, max_minutes=10)).spec
    assert run(low, commute("update", 1, step="down_large")).spec.commutes[0].max_minutes == 10


def test_a_step_is_read_only_when_no_number_is_given():
    spec = run(RENTER, commute("add", 1, max_minutes=30)).spec
    both = run(spec, commute("update", 1, max_minutes=40, step="down_large")).spec
    assert both.commutes[0].max_minutes == 40


def test_changing_mode_brings_the_cap_within_the_new_cutoff():
    spec = run(RENTER, commute("add", 1, mode="pt", max_minutes=80)).spec
    walking = run(spec, commute("update", 1, mode="walk"))
    assert walking.rejected == ()
    assert walking.spec.commutes[0].max_minutes == 60
    assert check_spec(walking.spec, small_release()) == ()


def test_a_weight_that_reaches_nothing_counts_for_nothing_by_any_action():
    for edit in (
        weight("set", "station_walk", value=0.0),
        weight("set", "station_walk", value=0.02),
        weight("nudge", "station_walk", step="down_large"),
        weight("nudge", "station_walk", step="down_large", provenance="ui_edit"),
        weight("remove", "station_walk"),
    ):
        spec = run(RENTER, edit, edit).spec
        assert "station_walk" not in asked_for(spec)
        assert canonical(spec) == canonical(run(RENTER, weight("remove", "station_walk")).spec)
        assert '"station_walk"' not in canonical(spec)
    # A feature no tenure has a default for leaves nothing behind, and nor does a tag.
    for edit in (
        weight("set", "culture_venues", value=0.0),
        weight("nudge", "culture_venues", step="down_large"),
        weight("remove", "culture_venues"),
    ):
        wanted = run(RENTER, weight("set", "culture_venues", value=0.2)).spec
        assert "culture_venues" not in weights(run(wanted, edit).spec)
    leafy = run(RENTER, tag("set", "leafy", value=0.2)).spec
    assert run(leafy, tag("remove", "leafy")).spec.tags == ()


TAKEN_OFF: list[Edit] = [
    weight("remove", "air_no2", provenance="ui_edit"),
    weight("set", "air_no2", value=0.0, provenance="ui_edit"),
    weight("nudge", "air_no2", step="down_large"),
    weight("nudge", "air_no2", step="down_small", provenance="inferred"),
]


@pytest.mark.parametrize("edit", TAKEN_OFF, ids=lambda e: f"{e.action}-{e.provenance}")
@pytest.mark.parametrize("tenure", list(Tenure))
def test_a_default_the_person_took_off_stays_off_when_the_tenure_changes(
    edit: WeightEdit, tenure: Tenure
):
    other = Tenure.BUY if tenure is Tenure.RENT else Tenure.RENT
    off = run(default_spec(tenure), edit)
    assert [a.changed for a in off.applied] == [True]
    assert "air_no2" not in asked_for(off.spec)

    # It came back at 0.05, because nothing recorded that it had been taken off.
    moved = run(off.spec, budget(tenure=other.value, provenance="ui_edit")).spec
    assert moved.tenure is other
    assert "air_no2" not in asked_for(moved)
    expected = dict(GIVEN_WAY[other])
    del expected["air_no2"]
    assert defaults_of(moved) == asked_for(moved) == expected
    back = run(moved, budget(tenure=tenure.value, provenance="ui_edit")).spec
    assert "air_no2" not in asked_for(back)

    # What records it is an entry of nothing, in the person's name, which is
    # not hashed, not checked and not ranked: zero still has one canonical form.
    (entry,) = (w for w in off.spec.weights if w.feature_id is FeatureId.AIR_NO2)
    assert (entry.weight, entry.provenance) == (0.0, Provenance(edit.provenance.value))
    without = off.spec.replace(weights=off.spec.active_weights)
    assert canonical(off.spec) == canonical(without)
    assert rank(off.spec, small_release()) == rank(without, small_release())
    assert check_spec(off.spec, small_release()) == ()


def test_a_weight_the_person_chose_and_then_took_off_stays_off_too():
    chosen = run(RENTER, weight("set", "park_proximity", value=0.7, provenance="ui_edit")).spec
    off = run(chosen, weight("remove", "park_proximity", provenance="ui_edit")).spec
    buyer = run(off, budget(tenure="buy")).spec
    assert "park_proximity" not in asked_for(buyer)
    # Green cover is a default of a buyer's alone. Nobody took it off, so it comes.
    assert asked_for(buyer)["green_cover"] == GIVEN_WAY[Tenure.BUY]["green_cover"]


def test_what_was_taken_off_and_is_named_again_is_worth_a_mention():
    off = run(RENTER, weight("remove", "park_proximity")).spec
    for step in ("up_small", "up_large"):
        again = run(off, weight("nudge", "park_proximity", step=step, provenance="inferred")).spec
        (park,) = (w for w in again.weights if w.feature_id is FeatureId.PARK_PROXIMITY)
        assert (park.weight, park.provenance) == (MENTION_WEIGHT, Provenance.INFERRED)
    # Taken off a second time, nothing changes, and whose choice it was is left alone.
    twice = run(off, weight("remove", "park_proximity", provenance="ui_edit"))
    assert ([a.changed for a in twice.applied], twice.spec) == ([False], off)
    less = run(off, weight("nudge", "park_proximity", step="down_small", provenance="ui_edit"))
    assert ([a.changed for a in less.applied], less.spec) == ([False], off)


def test_taking_off_what_was_never_there_leaves_nothing_behind():
    # A renter has no default for green cover, so there is nothing to take off
    # and nothing is recorded. It is a default of a buyer's and comes with the switch.
    same = run(RENTER, weight("remove", "green_cover"))
    assert ([a.changed for a in same.applied], same.spec) == ([False], RENTER)
    assert "green_cover" in asked_for(run(same.spec, budget(tenure="buy")).spec)


def test_default_direction_leaves_the_direction_in_the_spec_alone():
    fewer = run(RENTER, weight("set", "venue_evening", value=0.5, direction="less")).spec
    assert fewer.weights[-1].feature_id is FeatureId.VENUE_EVENING
    nudged = run(fewer, weight("nudge", "venue_evening", step="up_small")).spec
    entry = next(w for w in nudged.weights if w.feature_id is FeatureId.VENUE_EVENING)
    assert (entry.weight, entry.direction) == (0.6, Direction.LESS)

    # For a weight not yet in the spec it is what the polarity gives, and `more` for `either`.
    fresh = run(
        RENTER, weight("set", "homes_flats", value=0.3), weight("set", "water_access", value=0.3)
    )
    directions = {w.feature_id.value: w.direction for w in fresh.spec.weights}
    assert directions["homes_flats"] is Direction.MORE
    assert directions["water_access"] is Direction.MORE
    assert directions["noise_exposure"] is Direction.LESS


def test_a_direction_against_a_fixed_polarity_is_rejected_and_default_never_is():
    against = run(
        RENTER,
        weight("set", "park_proximity", value=0.5, direction="more"),
        weight("set", "university_proximity", value=0.5, direction="more"),
        weight("set", "green_cover", value=0.5, direction="less"),
        weight("set", "green_cover", value=0.5, direction="default"),
        weight("set", "homes_density", value=0.5, direction="less"),
    )
    assert reasons(against) == [RejectReason.DIRECTION_NOT_ALLOWED] * 3
    assert [a.index for a in against.applied] == [3, 4]


def test_exclude_and_only_replace_each_other_for_the_same_area():
    excluded = run(RENTER, area("exclude", 1)).spec
    only = run(excluded, area("only", 1), area("only", 2)).spec
    assert [(a.area_id, a.rule) for a in only.areas] == [
        (area_id(1), AreaRuleKind.ONLY),
        (area_id(2), AreaRuleKind.ONLY),
    ]
    cleared = run(only, area("clear", 1), area("clear", 5))
    assert [a.area_id for a in cleared.spec.areas] == [area_id(2)]
    assert [a.changed for a in cleared.applied] == [True, False]


def test_the_setting_an_edit_touches_takes_its_provenance():
    result = run(
        RENTER,
        budget(amount=1500, provenance="ui_edit"),
        weight("nudge", "air_no2", step="up_small", provenance="inferred"),
        setting("set", "commute_combine", choice="mean", provenance="ui_edit"),
        setting("set", "budget_weight", value=0.5, provenance="stated"),
    ).spec
    assert result.budget.provenance is Provenance.STATED  # the weight, which came last
    assert result.commute_combine_from is Provenance.UI_EDIT
    by_feature = {w.feature_id.value: w.provenance for w in result.weights}
    assert by_feature["air_no2"] is Provenance.INFERRED
    # What no edit touched is still nobody's choice.
    assert by_feature["station_walk"] is Provenance.DEFAULT
    assert (result.tenure_from, result.pt_basis_from) == (Provenance.DEFAULT, Provenance.DEFAULT)


@pytest.mark.parametrize(
    "edit",
    [
        weight("set", "station_walk", value=0.5, provenance="ui_edit"),
        weight("nudge", "station_walk", step="up_small", provenance="ui_edit"),
        setting("set", "commute_combine", choice="slowest", provenance="ui_edit"),
        setting("set", "pt_basis", choice="typical", provenance="ui_edit"),
        setting("set", "commute_weight", value=1.0, provenance="ui_edit"),
        setting("nudge", "commute_weight", step="up_large", provenance="ui_edit"),
        setting("set", "budget_weight", value=0.8, provenance="ui_edit"),
        budget("clear", provenance="ui_edit"),
        budget(segment="bed_1", strictness="soft", provenance="ui_edit"),
        weight("remove", "green_cover", provenance="ui_edit"),
        tag("remove", "leafy", provenance="ui_edit"),
        tag("nudge", "leafy", step="down_small", provenance="ui_edit"),
        area("clear", 1, provenance="ui_edit"),
    ],
    ids=lambda e: f"{type(e).__name__}-{e.action}",
)
def test_an_edit_that_changes_nothing_is_applied_and_leaves_provenance_alone(edit: Edit):
    spec = run(RENTER, weight("set", "station_walk", value=0.5, provenance="stated")).spec
    if isinstance(edit, WeightEdit) and edit.action == "nudge":
        spec = run(spec, weight("set", "station_walk", value=1.0)).spec
    result = run(spec, edit)
    assert result.rejected == ()
    assert [a.changed for a in result.applied] == [False]
    assert result.spec == spec


REJECTIONS: list[tuple[Edit, RejectReason]] = [
    (commute("add", "syn-p0099"), RejectReason.UNKNOWN_PLACE),
    (commute("add", ""), RejectReason.UNKNOWN_PLACE),
    (commute("add", "Foxholt Works"), RejectReason.UNKNOWN_PLACE),
    (commute("remove", "nowhere"), RejectReason.UNKNOWN_PLACE),
    (commute("update", 2, max_minutes=30), RejectReason.NO_SUCH_COMMUTE),
    (commute("remove", 2), RejectReason.NO_SUCH_COMMUTE),
    (commute("update", 1), RejectReason.NOTHING_TO_CHANGE),
    (commute("add", 2, max_minutes=5), RejectReason.OUT_OF_RANGE),
    (commute("add", 2, max_minutes=121), RejectReason.OUT_OF_RANGE),
    (commute("add", 2, max_minutes=-30), RejectReason.OUT_OF_RANGE),
    # Within 10 to 120, but the release routed public transport only to 90 minutes.
    (commute("add", 2, max_minutes=100), RejectReason.OUT_OF_RANGE),
    (commute("update", 1, max_minutes=70, mode="cycle"), RejectReason.OUT_OF_RANGE),
    (area("exclude", "syn-n0099"), RejectReason.UNKNOWN_AREA),
    (area("only", ""), RejectReason.UNKNOWN_AREA),
    (area("clear", "syn-n0099"), RejectReason.UNKNOWN_AREA),
    (budget(), RejectReason.NOTHING_TO_CHANGE),
    (budget("nudge", step="none"), RejectReason.NOTHING_TO_CHANGE),
    (budget(amount=299), RejectReason.OUT_OF_RANGE),
    (budget(amount=20_001), RejectReason.OUT_OF_RANGE),
    (budget(amount=-1800), RejectReason.OUT_OF_RANGE),
    (budget(amount=450_000), RejectReason.OUT_OF_RANGE),
    (budget(tenure="buy", amount=1800), RejectReason.OUT_OF_RANGE),
    (budget(segment="detached"), RejectReason.SEGMENT_NOT_FOR_TENURE),
    (budget(tenure="buy", segment="bed_2"), RejectReason.SEGMENT_NOT_FOR_TENURE),
    (weight("set", "green_cover", value=1.2), RejectReason.OUT_OF_RANGE),
    (weight("set", "green_cover", value=-0.1), RejectReason.OUT_OF_RANGE),
    (weight("nudge", "green_cover"), RejectReason.NOTHING_TO_CHANGE),
    (weight("set", "air_no2", value=0.5, direction="more"), RejectReason.DIRECTION_NOT_ALLOWED),
    (
        weight("set", "crime_burglary_theft", value=0.5, provenance="inferred"),
        RejectReason.CRIME_NEEDS_EXPLICIT_REQUEST,
    ),
    (tag("set", "leafy", value=7), RejectReason.OUT_OF_RANGE),
    (tag("nudge", "leafy"), RejectReason.NOTHING_TO_CHANGE),
    (setting("set", "commute_combine", choice="typical"), RejectReason.MISMATCHED_CHOICE),
    (setting("set", "commute_combine", choice="none"), RejectReason.MISMATCHED_CHOICE),
    (setting("set", "pt_basis", choice="mean"), RejectReason.MISMATCHED_CHOICE),
    (setting("nudge", "pt_basis", step="up_small"), RejectReason.MISMATCHED_CHOICE),
    (setting("nudge", "commute_combine", step="up_small"), RejectReason.MISMATCHED_CHOICE),
    (setting("set", "commute_weight", value=1.5), RejectReason.OUT_OF_RANGE),
    (setting("set", "budget_weight", value=-1), RejectReason.OUT_OF_RANGE),
    (setting("nudge", "budget_weight"), RejectReason.NOTHING_TO_CHANGE),
]


@pytest.mark.parametrize(
    ("edit", "reason"), REJECTIONS, ids=[f"{n}-{r.value}" for n, (_, r) in enumerate(REJECTIONS)]
)
def test_each_bad_edit_is_rejected_for_its_reason_and_changes_nothing(
    edit: Edit, reason: RejectReason
):
    spec = run(RENTER, commute("add", 1)).spec
    result = run(spec, edit)
    assert reasons(result) == [reason]
    assert result.applied == ()
    assert result.spec == spec


def test_every_reason_for_rejecting_an_edit_can_be_reached():
    reached = {reason for _, reason in REJECTIONS}
    reached |= {RejectReason.TOO_MANY_COMMUTES, RejectReason.NOT_IN_RELEASE}
    assert reached == set(RejectReason)


def test_nudging_a_budget_with_no_amount_is_rejected():
    assert RENTER.budget.amount is None
    assert reasons(run(RENTER, budget("nudge", step="up_large"))) == [
        RejectReason.NOTHING_TO_CHANGE
    ]


def test_a_feature_the_release_does_not_rank_cannot_be_weighted():
    release = small_release()
    switched_off = tuple(
        m.replace(rankable=False) if m.feature_id is FeatureId.GREEN_COVER else m
        for m in release.metrics
        if m.feature_id is not FeatureId.WATER_ACCESS
    )
    partial = dataclasses.replace(release, metrics=switched_off)
    result = apply(
        RENTER,
        ops(
            weight("set", "green_cover", value=0.5),  # carried, but switched off for ranking
            weight("nudge", "water_access", step="up_small"),  # not carried at all
            weight("set", "park_proximity", value=0.5),
            weight("remove", "green_cover"),  # a weight can always be taken off
        ),
        partial,
    )
    assert reasons(result) == [RejectReason.NOT_IN_RELEASE, RejectReason.NOT_IN_RELEASE]
    assert [a.index for a in result.applied] == [2, 3]
    assert check_spec(BUYER, partial)[0].problem == "not_in_release"


def test_a_stale_commute_or_area_can_still_be_taken_out():
    # A spec from an older release may name a place or an area this one has dropped.
    stale = RENTER.model_dump(mode="json") | {
        "commutes": [
            {
                "place_id": "syn-p0099",
                "mode": "pt",
                "max_minutes": 30,
                "strictness": "soft",
                "provenance": "stated",
            }
        ],
        "areas": [{"area_id": "syn-n0099", "rule": "exclude", "provenance": "stated"}],
    }
    spec = PreferenceSpec.model_validate(stale)
    assert len(check_spec(spec, small_release())) == 2
    fixed = run(spec, commute("remove", "syn-p0099"), area("clear", "syn-n0099"))
    assert fixed.rejected == ()
    assert check_spec(fixed.spec, small_release()) == ()


def test_enum_values_are_lower_cased_before_validation():
    shouted = WeightEdit.model_validate(
        {
            "action": "NUDGE",
            "feature_id": "Park_Proximity",
            "value": 0,
            "step": "UP_SMALL",
            "direction": "Default",
            "provenance": "Stated",
        }
    )
    assert shouted == weight("nudge", "park_proximity", step="up_small")
    with pytest.raises(ValidationError):
        WeightEdit.model_validate(shouted.model_dump() | {"step": "sideways"})


def walk(schema: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(schema, dict):
        found.append(schema)  # pyright: ignore[reportUnknownArgumentType]
        for value in schema.values():  # pyright: ignore[reportUnknownVariableType]
            found += walk(value)
    elif isinstance(schema, list):
        for value in schema:  # pyright: ignore[reportUnknownVariableType]
            found += walk(value)
    return found


def test_operations_have_no_unions_and_no_optional_fields():
    schema = Operations.model_json_schema()
    nodes = walk(schema)
    assert not [n for n in nodes if {"anyOf", "oneOf", "allOf"} & set(n)]
    assert "null" not in json.dumps(schema)
    objects = [n for n in nodes if n.get("type") == "object"]
    assert len(objects) == 7  # the six edits, and Operations itself
    for node in objects:
        assert sorted(node["required"]) == sorted(node["properties"])
        assert not [p for p in node["properties"].values() if "default" in p]
    # Each array holds one type.
    for name in GROUPS.values():
        items = schema["properties"][name]["items"]
        assert list(items) == ["$ref"]


def test_operations_refuse_a_missing_array_or_field_and_any_text_field():
    whole = ops(commute("add", 1)).model_dump(mode="json")
    for name in GROUPS.values():
        with pytest.raises(ValidationError):
            Operations.model_validate({k: v for k, v in whole.items() if k != name})
    with pytest.raises(ValidationError):
        CommuteEdit.model_validate(commute("add", 1).model_dump() | {"destination_text": "x"})
    with pytest.raises(ValidationError):
        BudgetEdit.model_validate({k: v for k, v in budget().model_dump().items() if k != "step"})


def random_edit(draw: random.Random) -> Edit:
    steps = [s.value for s in Step]
    provenance = draw.choice(["stated", "inferred", "ui_edit"])
    number = draw.choice([-1, 0, 0.0, 0.3, 0.5, 1, 1.0, 1.7])
    kind = draw.randrange(6)
    if kind == 0:
        return budget(
            draw.choice(["set", "clear", "nudge"]),
            tenure=draw.choice(["rent", "buy", "unchanged"]),
            amount=draw.choice([0, 0, -5, 250, 1500, 2600, 30_000, 450_000, 10**9]),
            segment=draw.choice([s.value for s in Segment] + ["unchanged"]),
            strictness=draw.choice(["soft", "hard", "unchanged"]),
            step=draw.choice(steps),
            provenance=provenance,
        )
    if kind == 1:
        return commute(
            draw.choice(["add", "update", "remove"]),
            draw.choice([1, 2, 3, 4, "", "syn-p0099", "anything at all"]),
            mode=draw.choice(["pt", "cycle", "walk", "unchanged"]),
            max_minutes=draw.choice([0, 0, -10, 5, 10, 45, 60, 61, 90, 120, 500]),
            strictness=draw.choice(["soft", "hard", "unchanged"]),
            step=draw.choice(steps),
            provenance=provenance,
        )
    if kind == 2:
        return weight(
            draw.choice(["set", "nudge", "remove"]),
            draw.choice(list(FeatureId)).value,
            value=number,
            step=draw.choice(steps),
            direction=draw.choice(["more", "less", "default"]),
            provenance=provenance,
        )
    if kind == 3:
        return tag(
            draw.choice(["set", "nudge", "remove"]),
            draw.choice(list(TagId)).value,
            value=number,
            step=draw.choice(steps),
            provenance=provenance,
        )
    if kind == 4:
        return area(
            draw.choice(["exclude", "only", "clear"]),
            draw.choice([1, 2, 8, "", "syn-n0099", "Alderwick"]),
            provenance,
        )
    return setting(
        draw.choice(["set", "nudge"]),
        draw.choice(["commute_combine", "pt_basis", "commute_weight", "budget_weight"]),
        choice=draw.choice(["slowest", "mean", "typical", "just_missed", "none"]),
        value=number,
        step=draw.choice(steps),
        provenance=provenance,
    )


def test_the_reducer_never_raises_and_never_makes_a_spec_that_cannot_be_ranked():
    release = small_release()
    draw = draws(41)
    spec = RENTER
    seen: set[RejectReason] = set()
    for _ in range(300):
        edits = ops(*(random_edit(draw) for _ in range(draw.randrange(1, 7))))
        result = apply(spec, edits, release)
        assert len(result.applied) + len(result.rejected) == edits.count
        assert check_spec(result.spec, release) == ()
        # A weight of nothing is kept only to record that a person took off
        # what a tenure weighs by default, and every weight is on a step.
        for entry in (*result.spec.weights, *result.spec.tags):
            if entry.weight == 0:
                assert isinstance(entry, FeatureWeight)
                assert any(entry.feature_id in held for held in DEFAULT_WEIGHTS.values())
                assert entry.provenance is not Provenance.DEFAULT
            assert round(entry.weight * 20) == pytest.approx(entry.weight * 20)
        changed = [a for a in result.applied if a.changed]
        assert bool(changed) == (result.spec != spec)
        seen |= {r.reason for r in result.rejected}
        spec = result.spec
    assert len(seen) >= 9
