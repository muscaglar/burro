import re

import pytest
from burro_core.catalogue import (
    FEATURES,
    TAGS,
    Tag,
    default_direction,
    direction_allowed,
    percentile_of,
    tag_raw,
)
from burro_core.ids import Dimension, Direction, FeatureId, Polarity, TagId
from burro_core.ops import TagEdit, WeightEdit
from burro_core.spec import FeatureWeight
from pydantic import ValidationError

from .support import documents, draws

# Words for who lives somewhere. None may appear in anything a user can rank on.
RESIDENT_WORDS = (
    r"residents?|people|population|households?|famil(?:y|ies)|students?|tenure|tenants?|"
    r"owners?|ages?|aged|young|old|elderly|child(?:ren)?|kids?|ethnic\w*|rac(?:e|ial)|"
    r"religio\w*|faith|born|birth|languages?|gender|sex\w*|disab\w*|health|incomes?|"
    r"depriv\w*|poor|rich|wealth\w*|class|migrants?|immigra\w*|nationalit\w*"
)
# "per 1,000 residents" is the denominator of a crime rate, which is how a rate
# is written down. It describes the place's recorded crime, not who lives there.
ALLOWED = ("per 1,000 residents a year", "family amenities")
RESIDENTS = re.compile(rf"\b(?:{RESIDENT_WORDS})\b", re.IGNORECASE)


def names_residents(text: str) -> bool:
    # An id is written with underscores, which would hide a word from `\b`.
    lowered = text.lower().replace("_", " ")
    for phrase in ALLOWED:
        lowered = lowered.replace(phrase, "")
    return RESIDENTS.search(lowered) is not None


def test_no_feature_or_tag_describes_residents():
    definitions = [m["definition"] for m in documents()["catalogue.json"]["metrics"]]
    texts = [
        *(f"{f.feature_id} {f.label} {f.unit} {f.higher} {f.lower}" for f in FEATURES.values()),
        *(f"{t.tag_id} {t.label}" for t in TAGS.values()),
        *definitions,
    ]
    assert [t for t in texts if names_residents(t)] == []


@pytest.mark.parametrize(
    "text",
    ["student_share", "Share of residents aged 20 to 24", "Households with children", "median_age"],
)
def test_the_denylist_would_catch_a_feature_that_describes_residents(text: str):
    assert names_residents(text)


def test_the_catalogue_holds_every_feature_and_tag_once():
    assert set(FEATURES) == set(FeatureId)
    assert set(TAGS) == set(TagId)
    assert len(FEATURES) == 23
    assert len(TAGS) == 12


@pytest.mark.parametrize("unknown", ["student_share", "median_age", "ethnicity", "", "tenure"])
def test_the_allowlist_refuses_an_unknown_feature_id(unknown: str):
    with pytest.raises(ValueError, match="is not a valid FeatureId"):
        FeatureId(unknown)
    with pytest.raises(ValidationError):
        FeatureWeight.model_validate(
            {"feature_id": unknown, "weight": 0.5, "direction": "more", "provenance": "stated"}
        )
    edit = {"action": "set", "value": 0.5, "step": "none", "provenance": "stated"}
    with pytest.raises(ValidationError):
        WeightEdit.model_validate(edit | {"feature_id": unknown, "direction": "default"})
    with pytest.raises(ValidationError):
        TagEdit.model_validate(edit | {"tag_id": unknown})


@pytest.mark.parametrize("tag", TAGS.values(), ids=[str(t) for t in TAGS])
def test_every_tag_formula_sums_to_one_and_names_no_crime_feature(tag: Tag):
    assert sum(term.hundredths for term in tag.terms) == 100
    assert all(FEATURES[t.feature_id].dimension is not Dimension.CRIME for t in tag.terms)
    assert len({t.feature_id for t in tag.terms}) == len(tag.terms)


@pytest.mark.parametrize("tag", TAGS.values(), ids=[str(t) for t in TAGS])
def test_conservation_areas_never_decide_a_tag_alone(tag: Tag):
    # A condition of the source. With the coverage rule, a tag that has only
    # its conservation term present is below 60 hundredths and so is unknown.
    carried = sum(t.hundredths for t in tag.terms if t.feature_id is FeatureId.CONSERVATION_COVER)
    assert carried < 60
    if carried:
        assert tag_raw(tag.tag_id, {FeatureId.CONSERVATION_COVER: 90.0}).raw is None


def test_crime_has_a_fixed_direction_and_university_cannot_be_asked_to_be_far():
    for feature_id in (FeatureId.CRIME_BURGLARY_THEFT, FeatureId.CRIME_VIOLENCE_ROBBERY):
        assert FEATURES[feature_id].polarity is Polarity.LESS
    # "Far from a university" would be a way to ask for fewer students.
    assert not direction_allowed(FeatureId.UNIVERSITY_PROXIMITY, Direction.MORE)
    assert direction_allowed(FeatureId.UNIVERSITY_PROXIMITY, Direction.LESS)


def test_only_features_of_buildings_and_venues_let_the_user_choose_the_direction():
    either = {f.feature_id for f in FEATURES.values() if f.polarity is Polarity.EITHER}
    assert either == {
        FeatureId.VENUE_FOOD_DRINK,
        FeatureId.VENUE_EVENING,
        FeatureId.HOMES_FLATS,
        FeatureId.HOMES_PRE1919,
        FeatureId.HOMES_DENSITY,
    }
    assert all(default_direction(f) is Direction.MORE for f in either)


def test_percentile_is_the_mid_rank_of_the_contract_example():
    values = [310.0, 120.0, 640.0, 310.0, 900.0]
    assert percentile_of(values, [True] * 5) == (40.0, 10.0, 70.0, 40.0, 90.0)


def test_percentile_is_unknown_exactly_where_the_value_is():
    assert percentile_of([5.0, None, 7.0], [True, True, True]) == (25.0, None, 75.0)


def test_an_area_that_is_not_rankable_is_placed_without_joining_the_population():
    # The population is 10 and 30. The unrankable 20 sits between them, and
    # leaves their percentiles as they would be without it.
    assert percentile_of([10.0, 20.0, 30.0], [True, False, True]) == (25.0, 50.0, 75.0)


def test_percentile_is_unknown_when_no_rankable_area_has_a_value():
    assert percentile_of([4.0, None], [False, True]) == (None, None)
    assert percentile_of([], []) == ()


def test_percentile_refuses_flags_that_do_not_match_the_values():
    with pytest.raises(ValueError, match="one rankable flag"):
        percentile_of([1.0, 2.0], [True])


def test_percentile_does_not_depend_on_the_order_of_the_areas():
    draw = draws(7)
    values = [draw.choice([None, *range(12)]) for _ in range(40)]
    floats = [None if v is None else float(v) for v in values]
    flags = [draw.random() < 0.8 for _ in floats]
    expected = dict(zip(range(40), percentile_of(floats, flags), strict=True))
    for _ in range(20):
        order = draw.sample(range(40), 40)
        shuffled = percentile_of([floats[i] for i in order], [flags[i] for i in order])
        assert dict(zip(order, shuffled, strict=True)) == expected


def test_percentiles_stay_within_bounds_and_follow_the_values():
    draw = draws(11)
    for _ in range(50):
        values = [float(draw.randrange(30)) for _ in range(draw.randrange(1, 25))]
        found = [p for p in percentile_of(values, [True] * len(values)) if p is not None]
        assert len(found) == len(values)
        assert all(0 <= p <= 100 for p in found)
        in_value_order = [p for _, p in sorted(zip(values, found, strict=True))]
        assert in_value_order == sorted(found)


def test_tag_is_the_weighted_mean_of_the_terms_that_are_present():
    # Leafy: 0.45 green_cover high, 0.30 park_proximity low, 0.25 homes_density low.
    full = tag_raw(
        TagId.LEAFY,
        {
            FeatureId.GREEN_COVER: 80.0,
            FeatureId.PARK_PROXIMITY: 10.0,
            FeatureId.HOMES_DENSITY: 40.0,
        },
    )
    assert full.coverage == 1.0
    assert full.raw == pytest.approx(0.45 * 0.8 + 0.30 * 0.9 + 0.25 * 0.6)


def test_a_missing_term_is_dropped_and_the_rest_reweighted():
    found = tag_raw(TagId.LEAFY, {FeatureId.GREEN_COVER: 80.0, FeatureId.PARK_PROXIMITY: None})
    assert found.coverage == 0.45
    assert found.raw is None  # 45 hundredths is below 60

    kept = tag_raw(TagId.LEAFY, {FeatureId.GREEN_COVER: 80.0, FeatureId.PARK_PROXIMITY: 10.0})
    assert kept.coverage == 0.75
    assert kept.raw == pytest.approx((0.45 * 0.8 + 0.30 * 0.9) / 0.75)


def test_tag_coverage_of_exactly_sixty_hundredths_is_enough():
    # 0.30 + 0.15 + 0.15. As floats these need not sum to 0.6; as hundredths they do.
    found = tag_raw(
        TagId.VILLAGE_FEEL,
        {
            FeatureId.VENUE_INDEPENDENT: 50.0,
            FeatureId.HIGHSTREET_ACCESS: 50.0,
            FeatureId.PARK_PROXIMITY: 50.0,
        },
    )
    assert found.coverage == 0.6
    assert found.raw == 0.5
