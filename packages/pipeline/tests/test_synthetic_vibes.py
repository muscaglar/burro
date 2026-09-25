"""The vibes of the synthetic release: the parts they are made of, and what a person would find.

Every expectation here names a made-up area and holds for other seeds too.
The seed moves every figure a little, and the character of an area is set by
hand in `names.py`.
"""

import hashlib
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from itertools import combinations
from pathlib import Path

import pytest
from burro_core import apply, default_spec, rank
from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    FEATURES,
    GRITTY,
    SHOWN_BESIDE_THE_MIX,
    TAGS,
    band_of,
    tags_of,
)
from burro_core.ids import (
    Dimension,
    FeatureId,
    GrittyVariant,
    Polarity,
    TagId,
    TagShape,
    Tenure,
    Toward,
    TravelStatus,
)
from burro_core.likeness import similar
from burro_core.ops import NO_OPERATIONS, CommuteEdit, TagEdit
from burro_core.portrait import portrait
from burro_core.release import InMemoryRelease, parse_release
from burro_core.spec import PreferenceSpec
from burro_pipeline.release import build_synthetic, read_release
from burro_pipeline.release.cli import main
from burro_pipeline.release.synthetic import RELEASE_ID, RELEASE_IDS, SEED, build
from burro_pipeline.release.synthetic.names import AREAS

FIXTURE = Path(__file__).parents[3] / "data" / "fixtures" / "synthetic" / RELEASE_ID
SEEDS = [SEED, 1, 2, 3]
RENTER = default_spec(Tenure.RENT)
# The features of catalogue version 1, as the release holds them: one digest
# over every row, in id order. A newer part draws from a stream of its own, so
# adding one leaves this as it is. A change to the plan of an area does not:
# it moves the figures of that area, and this with them. It was last moved on
# 2026-09-24, when the distance to a station and to a town centre came to be given in
# metres. No area changed places on either.
AS_THEY_WERE = "4cae2da1bc1e6cdab14f7302ac947799f0c08d2e220b3f35b1a669f2bb9dfcb9"


@cache
def built(seed: int = SEED, variant: GrittyVariant = GrittyVariant.B) -> InMemoryRelease:
    return build_synthetic(seed, gritty_variant=variant)


def area_id(release: InMemoryRelease, name: str) -> str:
    return next(area.area_id for area in release.neighbourhoods if area.name == name)


def names(release: InMemoryRelease, area_ids: list[str]) -> list[str]:
    by_id = {area.area_id: area.name for area in release.neighbourhoods}
    return [by_id[found] for found in area_ids]


def test_the_committed_release_carries_gritty_and_is_what_the_generator_builds():
    committed = read_release(FIXTURE)
    assert committed.manifest.gritty_variant is GrittyVariant.B
    assert (committed.manifest.schema_version, committed.manifest.catalogue_version) == (2, 15)
    assert committed.vibes == tags_of(GrittyVariant.B)
    assert committed.features == built().features
    assert committed.tags == built().tags


@pytest.mark.parametrize("variant", GrittyVariant)
def test_a_release_is_built_with_gritty_and_without_and_which_moves_no_figure(
    variant: GrittyVariant,
):
    release = built(variant=variant)
    assert parse_release(release.documents()) == release
    assert release.manifest.gritty_variant is variant
    carried = {vibe.tag_id for vibe in release.vibes}
    # A release carries the thirteen, and the one that gritty is read as there: Gritty, or
    # Works and warehouses where no recorded crime is held. It never carries both.
    assert GRITTY[variant] in carried and len(carried) == 14
    assert (TagId.STREET_CHARACTER in carried) == (variant is GrittyVariant.B)
    assert (TagId.WORKS_WAREHOUSES in carried) == (variant is GrittyVariant.A)
    other = built(variant=GrittyVariant.A if variant is GrittyVariant.B else GrittyVariant.B)
    assert release.features == other.features
    assert release.costs == other.costs
    shared = carried & {vibe.tag_id for vibe in other.vibes}
    assert len(shared) == 13
    assert [row for row in release.tags if row.tag_id in shared] == [
        row for row in other.tags if row.tag_id in shared
    ]


def test_the_other_way_of_gritty_is_written_under_an_id_of_its_own(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    assert RELEASE_IDS == {GrittyVariant.B: RELEASE_ID, GrittyVariant.A: "syn-2026-09-23-02"}
    assert main(["build-synthetic", "--out", str(tmp_path), "--gritty", "a"]) == 0
    assert "syn-2026-09-23-02" in capsys.readouterr().out
    written = read_release(tmp_path / "syn-2026-09-23-02")
    assert written.manifest.gritty_variant is GrittyVariant.A
    assert TagId.WORKS_WAREHOUSES in {vibe.tag_id for vibe in written.vibes}
    # It is built on demand and never committed.
    assert [entry.name for entry in FIXTURE.parent.iterdir() if entry.is_dir()] == [RELEASE_ID]


def test_no_figure_of_an_older_feature_moves_when_a_newer_part_is_added():
    rows = sorted(
        (row.model_dump(mode="json") for row in built().features if row.feature_id in build.FIRST),
        key=lambda row: (row["area_id"], row["feature_id"]),
    )
    text = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert hashlib.sha256(text.encode()).hexdigest() == AS_THEY_WERE
    assert len(build.FIRST) == 23 and len(build.SECOND) == 17
    assert not set(build.FIRST) & set(build.SECOND)
    # What joined later draws from a stream of its own, and moved no figure of either.
    assert build.LATER[:8] == (
        FeatureId.VENUE_FOOD_DRINK_PER_HOMES,
        FeatureId.PRICE_MEDIAN,
        FeatureId.CULTURE_VENUES_PER_HOMES,
        FeatureId.VENUE_CAFE,
        FeatureId.VENUE_CAFE_PER_HOMES,
        FeatureId.VENUE_GYM,
        FeatureId.VENUE_GYM_PER_HOMES,
        FeatureId.VENUE_EVENING_PER_HOMES,
    )
    # The chains of grocers, gyms and coffee came after those, and each has a stream too.
    brands = {f for f in FeatureId if FEATURES[f].dimension is Dimension.BRANDS}
    assert set(build.LATER[8:56]) == brands
    # The measures of how near stops are came after the chains, and each has one too.
    assert build.LATER[56:61] == (
        FeatureId.UNDERGROUND_PROXIMITY,
        FeatureId.RAIL_PROXIMITY,
        FeatureId.BUS_STOPS_NEARBY,
        FeatureId.OVERGROUND_PROXIMITY,
        FeatureId.BUS_ROUTES_NEARBY,
    )
    # The four made-up census figures came after those, and moved no figure of what came
    # before.
    assert build.LATER[61:65] == (
        FeatureId.RESIDENTS_AGED_20_34,
        FeatureId.RESIDENTS_AGED_65_OVER,
        FeatureId.HOUSEHOLDS_DEPENDENT_CHILDREN,
        FeatureId.HOUSEHOLDS_ONE_PERSON,
    )
    assert set(build.LATER[61:65]) == COUNTS_RESIDENTS
    # The homes in the higher bands, and how far what homes sold for has risen, came after.
    assert build.LATER[65:68] == (
        FeatureId.HOMES_HIGHER_BANDS,
        FeatureId.PRICE_RISE_5Y,
        FeatureId.PRICE_RISE_10Y,
    )
    # How much of the nearest high street lies in a conservation area came after, and the
    # traffic near where homes stand came last.
    assert build.LATER[68:] == (FeatureId.HIGHSTREET_CONSERVED, FeatureId.ROAD_TRAFFIC_NEARBY)
    assert len(build.LATER) == 8 + 48 + 5 + 4 + 3 + 1 + 1
    assert len(set(build.LATER)) == len(build.LATER)
    assert not set(build.LATER) & {*build.FIRST, *build.SECOND}


def test_the_release_carries_forty_one_features_and_four_wait_for_a_source():
    carried = {metric.feature_id for metric in built().metrics}
    assert carried == set(build.CARRIED)
    assert set(FeatureId) - carried == {
        FeatureId.PRIVATE_OUTDOOR_SPACE,
        FeatureId.CUISINE_VARIETY,
        FeatureId.GP_WALK,
        FeatureId.PHARMACY_WALK,
    }
    # So three recipes run short, as they would on real data today.
    short = {
        vibe.tag_id: sum(t.hundredths for t in vibe.terms if t.feature_id in carried)
        for vibe in built().vibes
    }
    assert {tag_id: held for tag_id, held in short.items() if held < 100} == {
        TagId.EVERYDAY_ON_FOOT: 70,
        TagId.HOMES: 75,
        TagId.FOODIE: 80,
    }


MEANS = (
    FeatureId.VENUE_FOOD_DRINK,
    FeatureId.CULTURE_VENUES,
    FeatureId.VENUE_EVENING,
    FeatureId.VENUE_CAFE,
    FeatureId.VENUE_GYM,
    *(f for f in SHOWN_BESIDE_THE_MIX if FEATURES[f].unit == "count"),
    FeatureId.BUS_STOPS_NEARBY,
    FeatureId.BUS_ROUTES_NEARBY,
)


@pytest.mark.parametrize("seed", SEEDS)
def test_every_figure_is_one_its_unit_can_hold(seed: int):
    for row in built(seed).features:
        if row.value is None:
            continue
        unit = FEATURES[row.feature_id].unit
        assert row.value >= 0
        if unit == "%":
            assert row.value <= 100
        # The places, the venues and the stops within reach are a mean over an area's
        # homes, and no whole number.
        if unit in ("count", "min", "m") and row.feature_id not in MEANS:
            assert row.value == int(row.value)
        if row.feature_id is FeatureId.GROCERY_WALK:
            # No walk in the release is under 2 minutes, as no journey is.
            assert row.value >= 2
        if row.feature_id is FeatureId.STATION_WALK:
            # A station is as far as its row of the stations says, at 80 metres a minute.
            assert row.value >= 2 * build.METRES_A_MINUTE


# The areas that hold both ends of a scale, with the band each sits in and the range it is
# drawn as. One for each scale that both ways of gritty carry.
MIXED = {
    # The busiest high street outside the centre, and quiet streets behind it.
    ("Foxholt", TagId.PACE): (4, 3, 5),
    # Old wharves, and new studios built between them.
    ("Kindlewharf", TagId.BUILT_AGE): (3, 2, 4),
    # New blocks on the water, and streets of houses behind them.
    ("Sable Reach", TagId.HOMES): (4, 3, 5),
}


@pytest.mark.parametrize("variant", GrittyVariant)
@pytest.mark.parametrize("seed", SEEDS)
def test_core_works_out_every_band_and_three_areas_are_mixed_by_hand(
    seed: int, variant: GrittyVariant
):
    release = built(seed, variant)
    rankable = [area.rankable for area in release.neighbourhoods]
    name_of = {area.area_id: area.name for area in release.neighbourhoods}
    mixed: dict[tuple[str, TagId], tuple[int | None, int | None, int | None]] = {}
    for vibe in release.vibes:
        rows = [release.tag(area.area_id, vibe.tag_id) for area in release.neighbourhoods]
        assert all(row is not None for row in rows)
        found = [row for row in rows if row is not None]
        assert [row.band for row in found] == list(band_of([row.raw for row in found], rankable))
        for row in found:
            if row.spread_low != row.spread_high:
                spread = (row.band, row.spread_low, row.spread_high)
                mixed[name_of[row.area_id], row.tag_id] = spread
    assert mixed == MIXED
    assert set(MIXED) == build.MIXED
    # Each spans three bands, which is what it takes to be said as a range.
    assert all(high - low == 2 for _, low, high in MIXED.values())


@pytest.mark.parametrize("variant", GrittyVariant)
@pytest.mark.parametrize("seed", SEEDS)
def test_every_vibe_has_areas_in_every_band(seed: int, variant: GrittyVariant):
    release = built(seed, variant)
    rankable = {area.area_id for area in release.neighbourhoods if area.rankable}
    for vibe in release.vibes:
        bands = Counter(
            row.band
            for row in release.tags
            if row.tag_id is vibe.tag_id and row.area_id in rankable and row.band is not None
        )
        # Both ends of a scale are lived in, and so is everything between them. Areas
        # that are level share a band, so a band may hold one fewer than its fifth.
        assert sorted(bands) == [1, 2, 3, 4, 5], vibe.tag_id
        assert min(bands.values()) >= 3, (vibe.tag_id, bands)


@pytest.mark.parametrize("seed", SEEDS)
def test_the_new_town_can_be_placed_on_homes_and_on_nothing_else(seed: int):
    release = built(seed)
    otterby = portrait(release, area_id(release, "Otterby Fields"))
    assert otterby is not None
    placed = [*otterby.scales, *otterby.more, *otterby.less, *otterby.others]
    assert [mark.tag_id for mark in placed] == [TagId.HOMES]
    assert len(otterby.unplaced) == 13
    # No census reached it either: it has no figure of who lives there.
    for feature_id in COUNTS_RESIDENTS:
        row = release.feature(area_id(release, "Otterby Fields"), feature_id)
        assert row is not None and row.value is None
    for feature_id in (*build.SECOND, *build.LATER):
        row = release.feature(area_id(release, "Otterby Fields"), feature_id)
        assert row is not None and row.value is None


@pytest.mark.parametrize("name", ["Grapnel Dock", "Sedgewater Marsh"])
def test_an_area_with_too_few_homes_has_no_share_of_homes_and_no_rate(name: str):
    release = built()
    for feature_id in build.SECOND:
        row = release.feature(area_id(release, name), feature_id)
        assert row is not None
        feature = FEATURES[feature_id]
        of_homes = "homes" in feature.label.lower() or feature.unit.startswith("per 1,000")
        assert (row.value is None) == of_homes, feature_id


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", ["Grapnel Dock", "Sedgewater Marsh"])
def test_an_area_with_too_few_homes_is_placed_only_where_enough_of_a_recipe_is_known(
    name: str, seed: int
):
    release = built(seed)
    found = portrait(release, area_id(release, name))
    assert found is not None
    # Each of these is made mostly of shares of homes and of rates, which the area
    # does not have. Nothing is filled in, so Burro says it cannot place the area.
    assert {mark.tag_id for mark in found.unplaced} == {
        # The places and the venues for each 1,000 homes and the distance to a town
        # centre are the whole of Going out.
        TagId.PACE,
        TagId.QUIET_RESIDENTIAL,
        TagId.BUILT_AGE,
        TagId.EVERYDAY_ON_FOOT,
        TagId.HOMES,
        # The places for each 1,000 homes are half of what a release holds of it.
        TagId.FOODIE,
        TagId.STREET_CHARACTER,
        # Too few live there for a share of them to be steady, and the places and the
        # venues for each 1,000 homes are most of the rest of it.
        TagId.YOUNG_PROFESSIONALS,
        # How much of the nearest high street lies in a conservation area is a mean over
        # homes, and homes built before 1919 a share of them: 60 in 100 of it.
        TagId.VILLAGE_FEEL,
    }
    # Family area is placed on the schools, the play space and the park, which are 60 in
    # 100 of it, and its fact says that it rests on three of its four parts.
    family = release.tag(area_id(release, name), TagId.FAMILY_AREA)
    assert family is not None and (family.coverage, family.band is None) == (0.6, False)
    for feature_id in COUNTS_RESIDENTS:
        row = release.feature(area_id(release, name), feature_id)
        assert row is not None and row.value is None
    for mark in found.unplaced:
        row = release.tag(area_id(release, name), mark.tag_id)
        assert row is not None
        assert (row.raw, row.score, row.band) == (None, None, None)


def pace(toward: str) -> PreferenceSpec:
    edit = TagEdit.model_validate(
        {
            "action": "nudge",
            "tag_id": "pace",
            "value": 0.0,
            "step": "up_large",
            "toward": toward,
            "provenance": "stated",
        }
    )
    return apply(RENTER, NO_OPERATIONS.replace(tag_ops=(edit,)), built()).spec


@pytest.mark.parametrize("seed", SEEDS)
def test_a_wish_for_calm_puts_the_nightlife_quarter_last_and_one_for_buzz_puts_it_first(
    seed: int,
):
    release = built(seed)
    calm = names(release, [a.area_id for a in rank(pace("low"), release).ranked])
    buzzy = names(release, [a.area_id for a in rank(pace("high"), release).ranked])
    assert "Lantern Yard" in calm[-3:] and "Pellam Cross" in calm[-3:]
    assert "Lantern Yard" not in calm[:10]
    assert "Lantern Yard" in buzzy[:4] and "Pellam Cross" in buzzy[:3]
    assert {"Gorsebeck", "Alderwick"} & set(calm[:3])
    assert pace("low").tags[0].toward is Toward.LOW
    if seed == SEED:
        # Asked for beside a renter's usual settings, the old town stands above the
        # nightlife quarter, which is third. Asked for alone, the nightlife quarter is
        # second: pubs and bars are 35 in 100 of Going out.
        assert buzzy[:3] == ["Pellam Cross", "Tallowgate", "Lantern Yard"]
        assert calm[-1] == "Lantern Yard"
        alone = searched(built(seed, GrittyVariant.B), TagId.PACE)
        assert alone[:3] == ["Pellam Cross", "Lantern Yard", "Tallowgate"]


def two_journeys(release: InMemoryRelease) -> PreferenceSpec:
    places = {place.name: place.place_id for place in release.places}
    edits = tuple(
        CommuteEdit.model_validate(
            {
                "action": "add",
                "place_id": places[name],
                "mode": "pt",
                "max_minutes": minutes,
                "strictness": "soft",
                "step": "none",
                "provenance": "ui_edit",
            }
        )
        for name, minutes in (("Cindermoor Works", 35), ("Wexmoor University", 40))
    )
    return apply(RENTER, NO_OPERATIONS.replace(commute_ops=edits), release).spec


@pytest.mark.parametrize("seed", SEEDS)
def test_an_area_far_from_one_workplace_is_not_first_because_another_has_no_time(seed: int):
    release = built(seed)
    result = rank(two_journeys(release), release)
    order = names(release, [area.area_id for area in result.ranked])
    assert "Gorsebeck" not in order[:5]
    gorsebeck = result.ranked[order.index("Gorsebeck")]
    to_the_works, to_the_campus = gorsebeck.legs
    # Over the limit to the first, and no time at all to the second.
    assert to_the_works.minutes is not None and to_the_works.minutes > 35
    assert (to_the_campus.status, to_the_campus.minutes) == (TravelStatus.MISSING, None)
    commute = next(c for c in gorsebeck.contributions if c.component == "commute")
    assert (commute.present, commute.utility) == (True, 0.0)
    if seed == SEED:
        assert to_the_works.minutes == 63


@pytest.mark.parametrize("seed", SEEDS)
def test_the_village_swallowed_by_the_city_is_most_like_the_other_old_village(seed: int):
    release = built(seed)
    found = similar(release, area_id(release, "Thrushcombe"))
    assert len(found) == 5
    assert "Wickerford" in names(release, [between.area_id for between in found])
    assert all(between.measures == 23 for between in found)
    # Likeness runs on places, so the docks and the centre are no village.
    for name in ("Grapnel Dock", "Pellam Cross", "Cindermoor"):
        assert area_id(release, name) not in [between.area_id for between in found]


def searched(release: InMemoryRelease, tag_id: TagId, toward: str = "high") -> list[str]:
    """The areas in the order a search for one vibe, and for nothing else, puts them."""
    # Many tests ask the same of the same release, and the answer is a pure function of it.
    seed, variant = release.manifest.seed, release.manifest.gritty_variant
    assert seed is not None and release is built(seed, variant)
    return list(_searched(seed, variant, tag_id, str(toward)))


@cache
def _searched(seed: int, variant: GrittyVariant, tag_id: TagId, toward: str) -> tuple[str, ...]:
    release = built(seed, variant)
    edit = TagEdit.model_validate(
        {
            "action": "set",
            "tag_id": tag_id.value,
            "value": 1.0,
            "step": "none",
            "toward": toward,
            "provenance": "ui_edit",
        }
    )
    ops = NO_OPERATIONS.replace(tag_ops=(edit,))
    spec = apply(RENTER.replace(weights=()), ops, release).spec
    return tuple(names(release, [area.area_id for area in rank(spec, release).ranked]))


def gritty(release: InMemoryRelease, toward: str = "high") -> list[str]:
    """The areas in the order a search for gritty alone puts them, in the way it was built."""
    return searched(release, GRITTY[release.manifest.gritty_variant], toward)


LEAFY_EDGE = {
    *("Alderwick", "Larkspur Hill", "Gorsebeck", "Wickerford", "Brackenhythe"),
    *("Eskerfold", "Thrushcombe"),
}


@pytest.mark.parametrize("seed", SEEDS)
def test_built_from_land_use_gritty_finds_the_works_and_depots(seed: int):
    order = gritty(built(seed, GrittyVariant.A))
    # Works and depots at the eastern end of the Amber line. The docks hold
    # more still, and have too few homes to rank.
    assert order[0] == "Cindermoor"
    # Last are areas the plan gives no works at all: the leafy edge, the two
    # villages and the old town.
    no_works = {plan.name for plan in AREAS if plan.industry == 0 and plan.works is None}
    assert len(no_works) == 7
    assert set(order[-4:]) <= no_works


@pytest.mark.parametrize("seed", SEEDS)
def test_gritty_finds_where_the_city_goes_out_at_night_and_polished_the_leafy_edge(
    seed: int,
):
    # What is recorded is 45 in 100 of it, and works and warehouses 30, so it follows
    # where the most is recorded and then the works. The nightlife quarter is first:
    # the most is recorded where people go out late, and its yards are workshops. The
    # works and depots come after the middle of town, and before everywhere else.
    release = built(seed, GrittyVariant.B)
    towards_gritty, towards_polished = gritty(release), gritty(release, "low")
    assert towards_gritty[0] == "Lantern Yard"
    assert set(towards_gritty[:3]) <= {
        "Lantern Yard",
        "Kindlewharf",
        "Pellam Cross",
        "Hollinsworth Quay",
    }
    assert 3 < towards_gritty.index("Cindermoor") < 6
    assert set(towards_gritty[-4:]) <= LEAFY_EDGE
    # Where no recorded crime is held, Works and warehouses finds the works first. Gritty
    # does not.
    assert searched(built(seed, GrittyVariant.A), TagId.WORKS_WAREHOUSES)[0] == "Cindermoor"
    # The same spec with the end turned is the same order, turned.
    assert towards_polished == list(reversed(towards_gritty))


@dataclass(frozen=True)
class End:
    """One end of a vibe, and the area a search for that alone should put first."""

    tag_id: TagId
    toward: Toward
    first: str  # in the committed release
    because: str  # what `names.py` says of that area
    # Where another seed may put a neighbour of the same kind first instead.
    or_else: tuple[str, ...] = ()


_HIGH, _LOW = Toward.HIGH, Toward.LOW
ENDS = (
    End(TagId.LEAFY, _HIGH, "Alderwick", "a leafy hillside of large houses"),
    End(TagId.VILLAGE_FEEL, _HIGH, "Thrushcombe", "a village with its green and its own shops"),
    End(TagId.PACE, _HIGH, "Pellam Cross", "the centre"),
    End(
        TagId.PACE,
        _LOW,
        "Marrowfen",
        "far out, and nowhere near a line",
        ("Gorsebeck", "Alderwick"),
    ),
    End(
        TagId.QUIET_RESIDENTIAL,
        _HIGH,
        "Gorsebeck",
        "fields, few shops, no station",
        ("Alderwick",),
    ),
    End(TagId.BUILT_AGE, _HIGH, "Tallowgate", "the old town"),
    End(TagId.BUILT_AGE, _LOW, "Sable Reach", "new flats inside the bend", ("Marrowfen",)),
    End(
        TagId.EVERYDAY_ON_FOOT,
        _HIGH,
        "Foxholt",
        "the busiest high street outside the centre, with a station",
        # The old town, on the seeds that put its station nearer.
        ("Tallowgate", "Dulcimer Green"),
    ),
    End(
        TagId.PARKS_CLOSE_BY,
        _HIGH,
        "Brackenhythe",
        "meadows along the north bank",
        ("Wickerford",),
    ),
    End(TagId.HOMES, _HIGH, "Pellam Cross", "the centre, where homes are flats"),
    End(TagId.HOMES, _LOW, "Otterby Fields", "a new town of houses", ("Farrowmere",)),
    End(
        TagId.FOODIE,
        _HIGH,
        "Kindlewharf",
        "kitchens and bars on the south bank",
        ("Hollinsworth Quay", "Lantern Yard"),
    ),
    End(
        TagId.FAMILY_AMENITIES,
        _HIGH,
        "Dulcimer Green",
        "schools and playgrounds",
        ("Larkspur Hill", "Alderwick", "Osierholm"),
    ),
    End(
        TagId.FAMILY_AREA,
        _HIGH,
        "Eskerfold",
        "a suburb at the end of a line, where the households with children are",
    ),
    End(
        TagId.YOUNG_PROFESSIONALS,
        _HIGH,
        "Hollinsworth Quay",
        "old quays turned studios, one stop from the centre",
        # The busiest high street outside the centre, on the seed that puts its station nearer.
        ("Foxholt",),
    ),
    End(TagId.WORKS_WAREHOUSES, _HIGH, "Cindermoor", "works and depots"),
    End(
        TagId.WELL_CONNECTED,
        _HIGH,
        "Farrowmere",
        "far out, where a line ends at the bus station of the eastern suburbs",
    ),
    End(TagId.STREET_CHARACTER, _HIGH, "Lantern Yard", "where the city goes out at night"),
    End(
        TagId.STREET_CHARACTER,
        _LOW,
        "Larkspur Hill",
        "a leafy suburb with no station of its own",
        ("Alderwick", "Wickerford", "Gorsebeck"),
    ),
)


def ends_of(release: InMemoryRelease) -> list[End]:
    carried = {vibe.tag_id for vibe in release.vibes}
    return [end for end in ENDS if end.tag_id in carried]


def test_every_end_of_every_vibe_is_named_here():
    expected = {
        (vibe.tag_id, toward)
        for vibe in TAGS.values()
        for toward in ((_HIGH, _LOW) if vibe.shape is TagShape.SCALE else (_HIGH,))
    }
    assert {(end.tag_id, end.toward) for end in ENDS} == expected
    assert len(ENDS) == len(expected)


@pytest.mark.parametrize("variant", GrittyVariant)
def test_each_vibe_puts_the_area_a_person_would_expect_first(variant: GrittyVariant):
    release = built(SEED, variant)
    for end in ends_of(release):
        order = searched(release, end.tag_id, end.toward)
        assert order[0] == end.first, f"{end.tag_id} towards {end.toward}: {end.because}"


@pytest.mark.parametrize("variant", GrittyVariant)
def test_each_vibe_puts_a_different_area_first(variant: GrittyVariant):
    release = built(SEED, variant)
    firsts = {
        (end.tag_id, end.toward): searched(release, end.tag_id, end.toward)[0]
        for end in ends_of(release)
    }
    # Pace and Homes are made only of figures of the first catalogue, which do
    # not move, and at their high ends both find the centre: the most goes on
    # there and the most homes are flats. Private outdoor space is the part that
    # would tell them apart, and no release carries it yet.
    centre = firsts.pop((TagId.HOMES, _HIGH))
    assert centre == firsts[TagId.PACE, _HIGH] == "Pellam Cross"
    # Every other end of every vibe finds an area of its own.
    assert len(set(firsts.values())) == len(firsts), firsts


@pytest.mark.parametrize("variant", GrittyVariant)
@pytest.mark.parametrize("seed", SEEDS)
def test_which_area_a_vibe_puts_first_comes_from_the_plan_and_not_from_the_seed(
    seed: int, variant: GrittyVariant
):
    release = built(seed, variant)
    for end in ends_of(release):
        order = searched(release, end.tag_id, end.toward)
        assert order[0] in (end.first, *end.or_else), (end.tag_id, end.toward, order[:3])
        # Where a neighbour is first, the area expected is still among the five that a
        # results page shows in full.
        assert end.first in order[:5], (end.tag_id, end.toward, order[:5])


def test_every_part_of_a_recipe_that_a_person_may_turn_is_a_taste_in_places():
    for vibe in TAGS.values():
        for term in vibe.terms:
            feature = FEATURES[term.feature_id]
            if feature.polarity is Polarity.EITHER:
                assert feature.kind == "taste"


# How alike two vibes may be. The slice is there so that a person can feel what each
# vibe adds, and they cannot where two words colour the map the same way. As the city
# was first drawn, eleven vibes moved as about three: Homes and Food and drink ran
# together at 0.97, and Pace shared all of its first five areas with both. Works and
# warehouses is 30 in 100 of Gritty, so the two stand nearest of any pair: they ran
# together at 0.92 until what is recorded was drawn to follow the works less.
SHARED_AT_MOST = 3  # of the first five areas that a search for each alone finds
ALIKE_AT_MOST = 0.8  # the rank correlation of two vibes across the areas, either way


def ends_in(release: InMemoryRelease) -> list[tuple[TagId, Toward]]:
    """Every end of every vibe of a release: what a person may ask for by one word."""
    return [
        (vibe.tag_id, toward)
        for vibe in release.vibes
        for toward in ((_HIGH, _LOW) if vibe.shape is TagShape.SCALE else (_HIGH,))
    ]


def rank_correlation(one: Sequence[float], other: Sequence[float]) -> float:
    """Spearman's: how far two orders of the same areas agree, from -1 to 1.

    Areas that are level share the middle of the ranks they take up.
    """

    def ranks(values: Sequence[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda at: values[at])
        found = [0.0] * len(values)
        start = 0
        while start < len(order):
            end = start
            while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
                end += 1
            for at in order[start : end + 1]:
                found[at] = (start + end) / 2
            start = end + 1
        return found

    a, b = ranks(one), ranks(other)
    mean = (len(a) - 1) / 2
    spread = sum((x - mean) ** 2 for x in a) * sum((y - mean) ** 2 for y in b)
    return sum((x - mean) * (y - mean) for x, y in zip(a, b, strict=True)) / spread**0.5


def test_a_rank_correlation_is_one_for_the_same_order_and_minus_one_for_it_turned():
    assert rank_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == 1
    assert rank_correlation([1, 2, 3, 4], [4, 3, 2, 1]) == -1
    assert rank_correlation([1, 2, 3, 4], [2, 1, 4, 3]) == pytest.approx(0.6)
    # Two areas that are level share a rank, and pull neither way.
    assert rank_correlation([1, 1, 2, 2], [1, 2, 1, 2]) == 0


@pytest.mark.parametrize("variant", GrittyVariant)
@pytest.mark.parametrize("seed", SEEDS)
def test_no_two_vibes_find_the_same_first_five_areas(seed: int, variant: GrittyVariant):
    release = built(seed, variant)
    first = {end: set(searched(release, *end)[:5]) for end in ends_in(release)}
    alike = {
        (one[0].value, one[1].value, other[0].value, other[1].value): sorted(shared)
        for one, other in combinations(first, 2)
        if one[0] is not other[0] and len(shared := first[one] & first[other]) > SHARED_AT_MOST
    }
    assert not alike


@pytest.mark.parametrize("variant", GrittyVariant)
@pytest.mark.parametrize("seed", SEEDS)
def test_no_two_vibes_put_the_areas_in_the_same_order(seed: int, variant: GrittyVariant):
    release = built(seed, variant)
    placed = {
        vibe.tag_id: {
            row.area_id: row.raw
            for area in release.neighbourhoods
            if area.rankable
            and (row := release.tag(area.area_id, vibe.tag_id)) is not None
            and row.raw is not None
        }
        for vibe in release.vibes
    }
    alike: dict[tuple[str, str], float] = {}
    for one, other in combinations(placed, 2):
        both = sorted(placed[one].keys() & placed[other].keys())
        assert len(both) >= 20
        together = rank_correlation(
            [placed[one][area] for area in both], [placed[other][area] for area in both]
        )
        if abs(together) > ALIKE_AT_MOST:
            alike[one.value, other.value] = round(together, 2)
    assert not alike


@dataclass(frozen=True)
class Apart:
    """An area that one vibe finds and its neighbour does not, as `names.py` plans it."""

    area: str
    is_high_on: TagId
    and_on: TagId
    # High on both, where the city at large is high on one and low on the other.
    too: bool = False
    # The highest band the area may stand in on the second, where it is not high on both.
    at_most: int = 2


APART = {
    # Food and drink is ranked on the places for each 1,000 homes, which the streets round
    # a campus have many of, all of them chains. So it stands no higher than the middle.
    "lively, and no place for food": Apart("Wexmoor", TagId.PACE, TagId.FOODIE, at_most=3),
    "old, and not leafy": Apart("Tallowgate", TagId.BUILT_AGE, TagId.LEAFY),
    "leafy, and on a main road": Apart("Dulcimer Green", TagId.LEAFY, TagId.QUIET_RESIDENTIAL),
    "flats, and quiet": Apart("Farrowmere", TagId.HOMES, TagId.QUIET_RESIDENTIAL, too=True),
    "leafy, and lively": Apart("Thrushcombe", TagId.LEAFY, TagId.PACE, too=True),
    "old, and calm": Apart("Alderwick", TagId.BUILT_AGE, TagId.PACE),
    "a park close by, and not leafy": Apart("Foxholt", TagId.PARKS_CLOSE_BY, TagId.LEAFY),
    "leafy, and no park close by": Apart("Alderwick", TagId.LEAFY, TagId.PARKS_CLOSE_BY),
    # An old high street among newer homes, which stand apart.
    "a centre of its own, and not old": Apart("Cindermoor", TagId.VILLAGE_FEEL, TagId.BUILT_AGE),
    "schools and play space, and nothing old": Apart(
        "Osierholm", TagId.FAMILY_AMENITIES, TagId.BUILT_AGE
    ),
    # How near stops are is not how much goes on: the end of a line is calm.
    "well connected, and calm": Apart("Farrowmere", TagId.WELL_CONNECTED, TagId.PACE),
    # Family area counts the households that hold children, and Family amenities counts
    # places alone. So each finds an area that the other does not.
    "many households with children, and few schools": Apart(
        "Marrowfen", TagId.FAMILY_AREA, TagId.FAMILY_AMENITIES, at_most=3
    ),
    "schools and play space, and fewer households with children": Apart(
        "Osierholm", TagId.FAMILY_AMENITIES, TagId.FAMILY_AREA, at_most=3
    ),
}


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("said", APART)
def test_each_vibe_has_an_area_that_its_neighbour_does_not_find(said: str, seed: int):
    release, found = built(seed), APART[said]
    one = release.tag(area_id(release, found.area), found.is_high_on)
    other = release.tag(area_id(release, found.area), found.and_on)
    assert one is not None and one.band is not None and one.band >= 4, said
    assert other is not None and other.band is not None
    assert (other.band >= 4) if found.too else (other.band <= found.at_most), said
