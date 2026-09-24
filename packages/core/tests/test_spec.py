import json
from typing import Any, cast

import pytest
from burro_core.ids import (
    AreaRuleKind,
    Direction,
    FeatureId,
    GrittyVariant,
    Mode,
    Provenance,
    Segment,
    SpecProblemKind,
    Strictness,
    TagId,
    Tenure,
    Toward,
)
from burro_core.rank import rank
from burro_core.spec import (
    LIMITS,
    AreaRule,
    Commute,
    FeatureWeight,
    PreferenceSpec,
    SpecError,
    TagWeight,
    canonical,
    check_spec,
    default_spec,
    snap,
    spec_hash,
    steps,
)
from pydantic import ValidationError

from .support import build_worked_spec, draws, small_release

WORKED_CANONICAL = (
    '{"areas":[],"budget":{"amount":1800,"segment":"bed_1","strictness":"soft","weight":16},'
    '"commute_combine":"slowest","commute_weight":20,"commutes":[{"max_minutes":40,"mode":"pt",'
    '"place_id":"syn-p0001","strictness":"soft"},{"max_minutes":30,"mode":"pt",'
    '"place_id":"syn-p0002","strictness":"hard"}],"pt_basis":"typical","schema_version":1,'
    '"tags":[{"tag_id":"leafy","weight":8}],"tenure":"rent","weights":[{"direction":"less",'
    '"feature_id":"noise_exposure","weight":6},{"direction":"less",'
    '"feature_id":"park_proximity","weight":10}]}'
)
WORKED_HASH = "bba9532c96393ce23be1d607aafa73d377e90885ad493868da0f51bff4d0dd6b"
BARE_CANONICAL = (
    '{"areas":[],"budget":null,"commutes":[],"schema_version":1,"tags":[],'
    '"tenure":"rent","weights":[]}'
)
BARE_HASH = "879be1ff788f9463f2dc60271c9190fdd35ea3df7522cce631dbde9ce8089a6b"


def commute(place: int, minutes: int = 40, mode: Mode = Mode.PT) -> Commute:
    return Commute(
        place_id=f"syn-p{place:04d}",
        mode=mode,
        max_minutes=minutes,
        strictness=Strictness.SOFT,
        provenance=Provenance.STATED,
    )


def weight(feature_id: FeatureId, value: float, direction: Direction) -> FeatureWeight:
    return FeatureWeight(
        feature_id=feature_id, weight=value, direction=direction, provenance=Provenance.STATED
    )


def with_provenance(value: Any, provenance: str) -> Any:
    """The same spec, as JSON, with every provenance replaced."""
    if isinstance(value, dict):
        document = cast(dict[str, Any], value)
        return {
            key: provenance
            if key == "provenance" or key.endswith("_from")
            else with_provenance(item, provenance)
            for key, item in document.items()
        }
    if isinstance(value, list):
        return [with_provenance(item, provenance) for item in cast(list[Any], value)]
    return value


def test_canonical_form_matches_the_published_vectors():
    worked = build_worked_spec()
    assert canonical(worked) == WORKED_CANONICAL
    assert spec_hash(worked) == WORKED_HASH

    bare = default_spec(Tenure.RENT).replace(weights=())
    assert canonical(bare) == BARE_CANONICAL
    assert spec_hash(bare) == BARE_HASH


@pytest.mark.parametrize("provenance", list(Provenance))
def test_the_hash_ignores_provenance(provenance: Provenance):
    document = build_worked_spec().model_dump(mode="json")
    changed = PreferenceSpec.model_validate(with_provenance(document, provenance.value))
    assert changed.tenure_from is provenance
    assert changed.commutes[0].provenance is provenance
    assert spec_hash(changed) == WORKED_HASH


def test_the_hash_ignores_the_order_of_keys_and_of_entries():
    document = build_worked_spec().model_dump(mode="json")
    reordered = {key: document[key] for key in reversed(list(document))}
    for name in ("commutes", "weights", "tags", "areas"):
        reordered[name] = list(reversed(reordered[name]))
    reordered["budget"] = dict(reversed(list(document["budget"].items())))
    as_sent = json.loads(json.dumps(reordered))
    assert spec_hash(PreferenceSpec.model_validate(as_sent)) == WORKED_HASH


def test_the_hash_is_the_same_however_the_entries_were_shuffled():
    draw = draws(3)
    spec = default_spec(Tenure.BUY)
    for _ in range(25):
        shuffled = spec.replace(weights=tuple(draw.sample(spec.weights, len(spec.weights))))
        assert shuffled == spec
        assert spec_hash(shuffled) == spec_hash(spec)


def test_a_weight_of_zero_is_the_same_as_no_entry():
    spec = default_spec(Tenure.RENT).replace(weights=(), tags=())
    zeroed = spec.replace(
        weights=(weight(FeatureId.GREEN_COVER, 0.0, Direction.MORE),),
        tags=(TagWeight(tag_id=TagId.LEAFY, weight=0.0, provenance=Provenance.UI_EDIT),),
    )
    assert canonical(zeroed) == canonical(spec) == BARE_CANONICAL


def test_a_budget_with_no_amount_is_written_as_null_whatever_else_it_holds():
    spec = default_spec(Tenure.RENT).replace(weights=())
    other = spec.replace(
        budget=spec.budget.replace(segment=Segment.STUDIO, strictness=Strictness.HARD, weight=0.2)
    )
    assert canonical(other) == BARE_CANONICAL


def test_commute_settings_are_left_out_when_there_is_no_commute():
    spec = default_spec(Tenure.RENT)
    assert "commute_combine" not in canonical(spec)
    assert "commute_weight" in canonical(spec.replace(commutes=(commute(1),)))


def test_specs_with_the_same_canonical_form_rank_the_same():
    release = small_release()
    spec = default_spec(Tenure.RENT)
    same = spec.replace(
        weights=(*spec.weights, weight(FeatureId.HOMES_FLATS, 0.0, Direction.LESS)),
        budget=spec.budget.replace(segment=Segment.FLAT),  # no amount, so it is not read
        commute_weight=0.35,  # no commute, so it is not read
        tenure_from=Provenance.STATED,
    )
    assert spec != same
    assert canonical(spec) == canonical(same)
    assert check_spec(same, release) == ()
    assert rank(spec, release) == rank(same, release)


@pytest.mark.parametrize(
    ("given", "snapped"),
    [(0.0, 0.0), (0.02, 0.0), (0.025, 0.05), (0.30, 0.30), (0.33, 0.35), (0.974, 0.95), (1.0, 1.0)],
)
def test_a_weight_is_snapped_to_the_nearest_step_and_a_tie_goes_up(given: float, snapped: float):
    assert snap(given) == snapped
    assert weight(FeatureId.GREEN_COVER, given, Direction.MORE).weight == snapped


def test_every_step_survives_a_round_trip_through_a_weight():
    for count in range(21):
        assert steps(count / 20) == count
        assert snap(count / 20) == count / 20


@pytest.mark.parametrize("bad", [-0.01, 1.01, float("nan"), float("inf")])
def test_a_weight_outside_zero_to_one_is_refused(bad: float):
    with pytest.raises(ValidationError):
        weight(FeatureId.GREEN_COVER, bad, Direction.MORE)


def test_a_repeated_place_feature_tag_or_area_is_refused():
    spec = default_spec(Tenure.RENT)
    rule = AreaRule(area_id="syn-n0001", rule=AreaRuleKind.ONLY, provenance=Provenance.STATED)
    tag = TagWeight(tag_id=TagId.LEAFY, weight=0.5, provenance=Provenance.STATED)
    for field, value in (
        ("commutes", (commute(1), commute(1, minutes=20))),
        ("weights", (*spec.weights, spec.weights[0])),
        ("tags", (tag, tag)),
        ("areas", (rule, rule.replace(rule=AreaRuleKind.EXCLUDE))),
    ):
        with pytest.raises(ValidationError):
            spec.replace(**{field: value})


def test_a_fourth_commute_is_refused():
    with pytest.raises(ValidationError):
        default_spec(Tenure.RENT).replace(commutes=tuple(commute(n) for n in range(1, 5)))


@pytest.mark.parametrize("minutes", [0, 9, 121, -5])
def test_a_commute_cap_outside_ten_to_120_minutes_is_refused(minutes: int):
    with pytest.raises(ValidationError):
        commute(1, minutes=minutes)


@pytest.mark.parametrize("text", ["Foxholt Works", "", "p0001", "SYN-P0001", "syn-n0001"])
def test_a_spec_cannot_hold_a_place_name_or_any_other_text(text: str):
    with pytest.raises(ValidationError):
        Commute(
            place_id=text,
            mode=Mode.PT,
            max_minutes=30,
            strictness=Strictness.SOFT,
            provenance=Provenance.STATED,
        )
    with pytest.raises(ValidationError):
        PreferenceSpec.model_validate(
            default_spec(Tenure.RENT).model_dump(mode="json") | {"note": text}
        )


@pytest.mark.parametrize("tenure", list(Tenure))
def test_the_default_spec_is_what_the_contract_lists(tenure: Tenure):
    spec = default_spec(tenure)
    rent = tenure is Tenure.RENT
    assert spec.budget.amount is None
    assert spec.budget.segment is (Segment.BED_1 if rent else Segment.FLAT)
    assert spec.budget.strictness is Strictness.SOFT
    assert spec.budget.weight == 0.30
    assert (spec.commutes, spec.tags, spec.areas) == ((), (), ())
    assert (spec.commute_combine, spec.pt_basis, spec.commute_weight) == (
        "slowest",
        "typical",
        0.40,
    )
    expected = (
        {
            "station_walk": 0.5,
            "station_lines": 0.3,
            "park_proximity": 0.3,
            "highstreet_access": 0.3,
            "noise_exposure": 0.2,
            "air_no2": 0.2,
        }
        if rent
        else {
            "station_walk": 0.4,
            "park_proximity": 0.4,
            "green_cover": 0.3,
            "highstreet_access": 0.3,
            "noise_exposure": 0.3,
            "station_lines": 0.2,
            "air_no2": 0.2,
        }
    )
    assert {w.feature_id.value: w.weight for w in spec.weights} == expected
    provenances = {w.provenance for w in spec.weights} | {
        spec.budget.provenance,
        spec.tenure_from,
        spec.commute_combine_from,
        spec.pt_basis_from,
        spec.commute_weight_from,
    }
    assert provenances == {Provenance.DEFAULT}


@pytest.mark.parametrize("tenure", list(Tenure))
def test_the_default_spec_can_be_ranked_and_weights_no_crime(tenure: Tenure):
    spec = default_spec(tenure)
    assert check_spec(spec, small_release()) == ()
    assert not any(w.feature_id.value.startswith("crime") for w in spec.weights)


def problems(spec: PreferenceSpec) -> list[tuple[str, SpecProblemKind]]:
    return [(p.path, p.problem) for p in check_spec(spec, small_release())]


def test_check_spec_names_the_path_and_the_problem():
    spec = default_spec(Tenure.RENT).replace(
        budget=default_spec(Tenure.RENT).budget.replace(amount=150, segment=Segment.DETACHED),
        commutes=(commute(1, minutes=100), commute(9), commute(2, minutes=70, mode=Mode.WALK)),
        weights=(weight(FeatureId.NOISE_EXPOSURE, 0.4, Direction.MORE),),
        areas=(AreaRule(area_id="syn-n0099", rule=AreaRuleKind.ONLY, provenance="stated"),),  # pyright: ignore[reportArgumentType]
    )
    assert problems(spec) == [
        ("budget.segment", SpecProblemKind.SEGMENT_NOT_FOR_TENURE),
        ("budget.amount", SpecProblemKind.OUT_OF_RANGE),
        # The cutoff of this release is 90 minutes by public transport and 60 on foot.
        ("commutes[0].max_minutes", SpecProblemKind.OUT_OF_RANGE),
        ("commutes[1].max_minutes", SpecProblemKind.OUT_OF_RANGE),
        ("commutes[2].place_id", SpecProblemKind.UNKNOWN_PLACE),
        ("weights[0].direction", SpecProblemKind.DIRECTION_NOT_ALLOWED),
        ("areas[0].area_id", SpecProblemKind.UNKNOWN_AREA),
    ]


def vibe(tag_id: TagId, toward: Toward = Toward.HIGH, weight: float = 0.5) -> TagWeight:
    return TagWeight(tag_id=tag_id, weight=weight, toward=toward, provenance=Provenance.STATED)


def test_the_end_of_a_vibe_is_written_into_the_hash_only_when_it_is_the_low_end():
    # A vibe towards its high end is what a tag was before a vibe had ends, so
    # every hash that was published before then still stands.
    renter = default_spec(Tenure.RENT)
    buzzy = renter.replace(tags=(vibe(TagId.PACE),))
    calm = renter.replace(tags=(vibe(TagId.PACE, Toward.LOW),))
    assert '"tags":[{"tag_id":"pace","weight":10}]' in canonical(buzzy)
    assert '"tags":[{"tag_id":"pace","toward":"low","weight":10}]' in canonical(calm)
    assert spec_hash(buzzy) != spec_hash(calm)
    assert "toward" not in canonical(build_worked_spec())
    assert spec_hash(build_worked_spec()) == WORKED_HASH


def test_the_end_of_a_vibe_may_be_left_out_of_a_body_and_is_then_the_high_end():
    sent = {"tag_id": "pace", "weight": 0.5, "provenance": "stated"}
    assert TagWeight.model_validate(sent).toward is Toward.HIGH
    assert TagWeight.model_validate(sent).model_dump(mode="json")["toward"] == "high"
    assert TagWeight.model_validate(sent | {"toward": "low"}).toward is Toward.LOW
    with pytest.raises(ValidationError):
        TagWeight.model_validate(sent | {"toward": "default"})


@pytest.mark.parametrize(
    "retired",
    ["buzzy", "evening_venues", "historic_character", "creative", "waterside"],
)
def test_a_spec_that_names_a_retired_tag_is_refused(retired: str):
    body = default_spec(Tenure.RENT).model_dump(mode="json")
    body["tags"] = [{"tag_id": retired, "weight": 0.5, "provenance": "stated"}]
    with pytest.raises(ValidationError):
        PreferenceSpec.model_validate(body)


def test_check_spec_refuses_the_low_end_of_a_one_way_vibe_and_a_vibe_the_release_lacks():
    spec = default_spec(Tenure.RENT).replace(
        tags=(
            vibe(TagId.LEAFY, Toward.LOW),
            vibe(TagId.PACE, Toward.LOW),
            # A release that holds no recorded crime carries no Gritty.
            vibe(TagId.STREET_CHARACTER),
            # What counts for nothing is passed over, as `canonical` passes over it.
            vibe(TagId.QUIET_RESIDENTIAL, Toward.LOW, weight=0.0),
        ),
    )
    without = small_release(GrittyVariant.A)
    assert [(p.path, p.problem) for p in check_spec(spec, without)] == [
        ("tags[0].toward", SpecProblemKind.DIRECTION_NOT_ALLOWED),
        ("tags[3].tag_id", SpecProblemKind.NOT_IN_RELEASE),
    ]
    with pytest.raises(SpecError):
        rank(spec, without)
    # The release of the tests carries it.
    assert problems(spec) == [("tags[0].toward", SpecProblemKind.DIRECTION_NOT_ALLOWED)]


def test_a_problem_points_into_the_spec_as_it_is_kept_whatever_order_it_was_sent_in():
    # A spec keeps its commutes, weights and areas in id order, and that is the
    # order every response gives them back in. A path indexes that order. It
    # cannot index the order sent, which the spec does not keep.
    sent = default_spec(Tenure.RENT).model_dump(mode="json") | {
        "commutes": [commute(number).model_dump(mode="json") for number in (9999, 1, 2)],
        "weights": [
            weight(FeatureId.STATION_WALK, 0.5, Direction.MORE).model_dump(mode="json"),
            weight(FeatureId.AIR_NO2, 0.2, Direction.LESS).model_dump(mode="json"),
        ],
    }
    spec = PreferenceSpec.model_validate(sent)
    found = check_spec(spec, small_release())
    assert [(p.path, p.problem) for p in found] == [
        ("commutes[2].place_id", SpecProblemKind.UNKNOWN_PLACE),
        ("weights[1].direction", SpecProblemKind.DIRECTION_NOT_ALLOWED),
    ]
    # Each path names the element at that position of the spec itself.
    assert spec.commutes[2].place_id == "syn-p9999"
    assert spec.weights[1].feature_id is FeatureId.STATION_WALK
    as_returned = spec.model_dump(mode="json")
    assert as_returned["commutes"][2]["place_id"] == "syn-p9999"
    assert [c["place_id"] for c in as_returned["commutes"]] == sorted(
        c["place_id"] for c in sent["commutes"]
    )


def test_rank_refuses_a_spec_that_does_not_fit_the_release_without_repeating_it():
    spec = default_spec(Tenure.RENT).replace(commutes=(commute(9),))
    with pytest.raises(SpecError) as caught:
        rank(spec, small_release())
    assert [p.problem for p in caught.value.problems] == [SpecProblemKind.UNKNOWN_PLACE]
    # A place id says where someone works. It must not reach a message that may be logged.
    assert "syn-p0009" not in str(caught.value)
    assert str(caught.value) == "commutes[0].place_id: unknown_place"


def test_limits_hold_the_numbers_of_the_contract():
    assert (LIMITS.weight_step_small, LIMITS.weight_step_large) == (0.10, 0.25)
    assert LIMITS.rent.model_dump() == {"minimum": 300, "maximum": 20_000, "unit": 25}
    assert LIMITS.buy.model_dump() == {"minimum": 50_000, "maximum": 20_000_000, "unit": 5_000}
    assert (LIMITS.minutes_min, LIMITS.minutes_max, LIMITS.max_commutes) == (10, 120, 3)
    assert (LIMITS.minutes_step_small, LIMITS.minutes_step_large) == (5, 15)
    assert (LIMITS.budget_step_small_percent, LIMITS.budget_step_large_percent) == (5, 15)


def test_a_validation_error_says_where_and_why_and_never_shows_what_was_sent():
    sent = default_spec(Tenure.RENT).model_dump(mode="json")
    sent["commutes"] = [
        {
            "place_id": "the clinic on Knurl Street",
            "mode": "pt",
            "max_minutes": 30,
            "strictness": "soft",
            "provenance": "stated",
        }
    ]
    with pytest.raises(ValidationError) as caught:
        PreferenceSpec.model_validate(sent)
    assert "clinic" not in str(caught.value)
    assert "clinic" not in repr(caught.value)
    assert "commutes.0.place_id" in str(caught.value)
