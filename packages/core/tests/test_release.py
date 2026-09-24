import dataclasses
import hashlib
import json
from collections.abc import Callable
from typing import Any

import pytest
from burro_core import release as module
from burro_core.catalogue import FEATURES, HOLDS_CRIME, TAGS, band_of, percentile_of, tags_of
from burro_core.ids import (
    FeatureId,
    GrittyVariant,
    Mode,
    Part,
    PtBasis,
    Segment,
    TagId,
    Tenure,
    TravelStatus,
)
from burro_core.release import (
    EVIDENCE,
    HASHES,
    LOCK,
    MANIFEST,
    RULES,
    InMemoryRelease,
    Release,
    ReleaseError,
    Travel,
    open_release,
    open_served,
    parse_release,
    recipes_held,
)
from pydantic import ValidationError

from .support import (
    CARRIED,
    MATRICES,
    RELEASE_ID,
    area_id,
    build_worked_release,
    documents,
    fixture_release,
    preview_documents,
    preview_release,
    small_release,
    unplaced,
)

Documents = dict[str, Any]
Break = Callable[[Documents], object]


def rule_broken(broken: Documents) -> tuple[str, str]:
    with pytest.raises(ReleaseError) as caught:
        parse_release(broken)
    return caught.value.file, caught.value.rule


ROWS = {
    "manifest.json": "sources",
    "neighbourhoods.json": "neighbourhoods",
    "geometry.json": "features",
    "catalogue.json": "metrics",
    "destinations.json": "destinations",
    "places.json": "places",
}


def rows(found: Documents, file: str) -> list[dict[str, Any]]:
    return found[file][ROWS.get(file, "rows")]


def set_in(file: str, row: int | None, **changes: Any) -> Break:
    def change(found: Documents) -> None:
        target = found[file] if row is None else rows(found, file)[row]
        target.update(changes)

    return change


def drop(file: str, row: int) -> Break:
    return lambda found: rows(found, file).pop(row)


def repeat(file: str, row: int, **changes: Any) -> Break:
    return lambda found: rows(found, file).append(rows(found, file)[row] | changes)


def cell(matrix: str, row: int, column: int, value: int | None) -> Break:
    def change(found: Documents) -> None:
        found["travel.json"][matrix][row][column] = value

    return change


def real_release(found: Documents) -> None:
    found["manifest.json"].update(synthetic=False)


def says_it_is_a_preview(found: Documents) -> None:
    found["manifest.json"].update(preview=True)


def holds_no_journey_and_no_station(found: Documents) -> None:
    """Take every journey and every station out, and leave what each file says of its sources."""
    found["destinations.json"]["destinations"] = []
    found["places.json"]["places"] = []
    found["travel.json"]["destination_ids"] = []
    for matrix in MATRICES:
        found["travel.json"][matrix] = [[] for _ in found["travel.json"]["area_ids"]]
    found["stations.json"]["rows"] = []


def then(*breaks: Break) -> Break:
    def change(found: Documents) -> None:
        for break_it in breaks:
            break_it(found)

    return change


# What a part of a release states when it states where it came from and when, and when not.
UNSTATED: dict[str, Any] = {"source_ids": [], "as_of": None}


def one_way_neighbour(found: Documents) -> None:
    found["neighbourhoods.json"]["neighbourhoods"][0]["neighbours"] = [area_id(2)]
    # Area 8 still lists area 1, and area 1 no longer lists it back.


def score_with_no_feature_behind_it(found: Documents) -> None:
    # Give area 1 no figure for any part of Leafy, and keep its score.
    scored = [r for r in found["tags.json"]["rows"] if r["tag_id"] == "leafy"]
    assert scored[0]["area_id"] == area_id(1)
    assert scored[0]["score"] is not None
    parts = {term.feature_id.value for term in TAGS[TagId.LEAFY].terms}
    for row in found["features.json"]["rows"]:
        if row["area_id"] == area_id(1) and row["feature_id"] in parts:
            row.update(value=None, percentile=None)


def figure_of(unit: str, value: float) -> Break:
    """Give the first figure of a measure of this unit another value, and leave the rest."""

    def change(found: Documents) -> None:
        units = {m["feature_id"]: m["unit"] for m in found["catalogue.json"]["metrics"]}
        held = (r for r in found["features.json"]["rows"] if units[r["feature_id"]] == unit)
        next(row for row in held if row["value"] is not None)["value"] = value

    return change


def at_its_end(unit: str, value: float, highest: bool) -> Break:
    """Give the highest or the lowest figure of a measure of this unit another value.

    The figure stays where it stood among the others, so every percentile and
    every vibe that rests on one is as it was, and only the range is tried.
    """

    def change(found: Documents) -> None:
        units = {m["feature_id"]: m["unit"] for m in found["catalogue.json"]["metrics"]}
        first = next(f for f, held in units.items() if held == unit)
        held = [
            row
            for row in found["features.json"]["rows"]
            if row["feature_id"] == first and row["value"] is not None
        ]
        ordered = sorted(held, key=lambda row: row["value"], reverse=highest)
        assert ordered[0]["value"] != ordered[1]["value"]
        assert (value >= ordered[0]["value"]) if highest else (value <= ordered[0]["value"])
        ordered[0]["value"] = value

    return change


def vibe(found: Documents, tag_id: str) -> dict[str, Any]:
    return next(v for v in found["catalogue.json"]["vibes"] if v["tag_id"] == tag_id)


def a_hundredth_moved(found: Documents) -> None:
    # The scores in the release were worked out with core's recipe, not this one.
    terms = vibe(found, "leafy")["terms"]
    terms[0]["hundredths"] += 1
    terms[1]["hundredths"] -= 1


def the_count_ranked_on(found: Documents) -> None:
    (row,) = [
        metric
        for metric in found["catalogue.json"]["metrics"]
        if metric["feature_id"] == "venue_food_drink"
    ]
    assert row["rankable"] is False
    row.update(rankable=True)


def a_vibe_left_out(found: Documents) -> None:
    found["catalogue.json"]["vibes"] = [
        v for v in found["catalogue.json"]["vibes"] if v["tag_id"] != "pace"
    ]
    found["tags.json"]["rows"] = [r for r in found["tags.json"]["rows"] if r["tag_id"] != "pace"]


def works_and_warehouses_beside_gritty(found: Documents) -> None:
    # A release that carries Gritty holds the land as parts of it, and no vibe beside it.
    found["catalogue.json"]["vibes"].append(TAGS[TagId.WORKS_WAREHOUSES].model_dump(mode="json"))


def a_row_of_gritty_where_no_recorded_crime_is_held(found: Documents) -> None:
    # A release that says it holds no recorded crime carries every vibe but Gritty.
    found.clear()
    found.update(documents(GrittyVariant.A))
    found["tags.json"]["rows"][0]["tag_id"] = "street_character"


def placed(found: Documents, tag_id: str = "pace") -> dict[str, Any]:
    """A row of `tags.json` that holds a band in the middle, so it can be moved either way."""
    return next(
        r for r in found["tags.json"]["rows"] if r["tag_id"] == tag_id and r["band"] in (2, 3, 4)
    )


def band(**changes: Any) -> Break:
    return lambda found: placed(found).update(changes)


def a_band_one_higher(found: Documents) -> None:
    row = placed(found)
    row.update(band=row["band"] + 1, spread_high=5)


def a_score_of_its_own(found: Documents) -> None:
    # What is ranked on is the score, and what is shown is the band of the raw value.
    row = placed(found, "leafy")
    row.update(score=round(100.0 - row["score"], 1) if row["score"] != 50.0 else 60.0)


def two_areas_in_each_others_place(found: Documents) -> None:
    # Each row agrees with itself, and neither agrees with the figures of its area.
    leafy = [r for r in found["tags.json"]["rows"] if r["tag_id"] == "leafy" and r["raw"]]
    ranked = sorted(leafy[:7], key=lambda row: row["raw"])
    low, high = ranked[0], ranked[-1]
    assert low["raw"] != high["raw"]
    held = ("raw", "score", "coverage", "band", "spread_low", "spread_high")
    low_was = {name: low[name] for name in held}
    low.update({name: high[name] for name in held})
    high.update(low_was)


def a_percentile_of_its_own(found: Documents) -> None:
    # The far end from where the value stands. No recipe holds this feature.
    row = next(
        r
        for r in found["features.json"]["rows"]
        if r["feature_id"] == "water_access" and r["percentile"] not in (None, 50.0)
    )
    row.update(percentile=round(100.0 - row["percentile"], 1))


def a_part_that_says_more_than_was_there(found: Documents) -> None:
    # Three recipes run short in this release, and one says that it does not.
    row = next(r for r in found["tags.json"]["rows"] if r["tag_id"] == "homes" and r["raw"])
    assert row["coverage"] == 0.75
    row.update(coverage=1.0)


def as_multipolygon(found: Documents, keep_type: bool = False) -> None:
    """Make the first area two squares. With `keep_type` it still claims to be a polygon."""
    geometry = found["geometry.json"]["features"][0]["geometry"]
    ring = geometry["coordinates"]
    moved = [[[lon + 0.01, lat] for lon, lat in ring[0]]]
    geometry["coordinates"] = [ring, moved]
    if not keep_type:
        geometry["type"] = "MultiPolygon"


BROKEN: list[tuple[str, str, Break]] = [
    ("versions_match", "manifest.json", set_in("manifest.json", None, schema_version=1)),
    ("versions_match", "manifest.json", set_in("manifest.json", None, catalogue_version=1)),
    ("versions_match", "catalogue.json", set_in("catalogue.json", None, catalogue_version=0)),
    ("synthetic_is_consistent", "manifest.json", real_release),
    ("synthetic_is_consistent", "manifest.json", set_in("manifest.json", None, city="lon")),
    (
        "synthetic_is_consistent",
        "manifest.json",
        set_in("manifest.json", None, release_id="lon-2026-09-23-01"),
    ),
    ("synthetic_is_consistent", "places.json", set_in("places.json", 3, place_id="lon-p0004")),
    (
        "synthetic_is_consistent",
        "manifest.json",
        set_in("manifest.json", 0, attribution="Contains real data."),
    ),
    ("synthetic_is_consistent", "manifest.json", set_in("manifest.json", 0, source_id="ons")),
    ("ids_are_unique", "neighbourhoods.json", repeat("neighbourhoods.json", 0)),
    ("ids_are_unique", "neighbourhoods.json", set_in("neighbourhoods.json", 1, slug="alderwick")),
    ("ids_are_unique", "features.json", repeat("features.json", 5)),
    ("ids_are_unique", "tags.json", repeat("tags.json", 5)),
    ("ids_are_unique", "cost.json", repeat("cost.json", 0, median=1200)),
    ("ids_are_unique", "places.json", repeat("places.json", 0)),
    ("ids_are_unique", "destinations.json", repeat("destinations.json", 0)),
    ("ids_are_unique", "catalogue.json", repeat("catalogue.json", 0)),
    ("ids_are_unique", "stations.json", set_in("stations.json", 2, nearest=True)),
    ("ids_are_unique", "stations.json", set_in("stations.json", 0, name="Another Name")),
    (
        "ids_are_unique",
        "stations.json",
        set_in("stations.json", 0, lines=["Birch line", "Amber line"]),
    ),
    (
        "references_resolve",
        "neighbourhoods.json",
        set_in("neighbourhoods.json", 0, neighbours=[area_id(2), "syn-n0099"]),
    ),
    ("references_resolve", "features.json", set_in("features.json", 0, area_id="syn-n0099")),
    ("references_resolve", "features.json", drop("catalogue.json", 0)),
    ("references_resolve", "tags.json", set_in("tags.json", 0, area_id="syn-n0099")),
    ("references_resolve", "cost.json", set_in("cost.json", 0, area_id="syn-n0099")),
    ("references_resolve", "stations.json", set_in("stations.json", 0, area_id="syn-n0099")),
    ("references_resolve", "places.json", set_in("places.json", 1, destination_id="syn-d0099")),
    ("references_resolve", "places.json", set_in("places.json", 1, coarse_place_id="syn-p0099")),
    # A landmark cannot stand in for another place: only a station or a district can.
    ("references_resolve", "places.json", set_in("places.json", 2, coarse_place_id="syn-p0002")),
    ("references_resolve", "cost.json", set_in("cost.json", 0, source_ids=["ons-rents"])),
    ("references_resolve", "places.json", set_in("places.json", 0, source_id="os-names")),
    ("references_resolve", "travel.json", set_in("travel.json", None, source_ids=["osm"])),
    ("references_resolve", "geometry.json", set_in("geometry.json", 0, id="syn-n0099")),
    ("catalogue_matches_core", "catalogue.json", set_in("catalogue.json", 0, polarity="more")),
    ("catalogue_matches_core", "catalogue.json", set_in("catalogue.json", 3, label="Best schools")),
    ("catalogue_matches_core", "catalogue.json", set_in("catalogue.json", 3, unit="points")),
    (
        "catalogue_matches_core",
        "catalogue.json",
        set_in("catalogue.json", 0, feature_id="student_share"),
    ),
    ("catalogue_matches_core", "features.json", set_in("features.json", 0, feature_id="age")),
    ("catalogue_matches_core", "tags.json", set_in("tags.json", 0, tag_id="young_professionals")),
    # A tag of catalogue version 1 is retired, and its id names nothing.
    ("catalogue_matches_core", "tags.json", set_in("tags.json", 0, tag_id="buzzy")),
    ("catalogue_matches_core", "catalogue.json", set_in("catalogue.json", 3, short_label="Best")),
    ("catalogue_matches_core", "catalogue.json", set_in("catalogue.json", 0, kind="taste")),
    ("catalogue_matches_core", "catalogue.json", set_in("catalogue.json", 0, describes="place")),
    ("catalogue_matches_core", "catalogue.json", set_in("catalogue.json", 0, family="green")),
    ("catalogue_matches_core", "catalogue.json", set_in("catalogue.json", 0, in_likeness=True)),
    ("catalogue_matches_core", "catalogue.json", set_in("catalogue.json", 0, method="modelled")),
    # What core shows and never ranks on is said to be ranked on.
    ("catalogue_matches_core", "catalogue.json", the_count_ranked_on),
    ("vibes_match_core", "catalogue.json", a_hundredth_moved),
    ("vibes_match_core", "catalogue.json", a_vibe_left_out),
    ("vibes_match_core", "catalogue.json", works_and_warehouses_beside_gritty),
    (
        "vibes_match_core",
        "catalogue.json",
        lambda found: vibe(found, "pace").update(high_end="Lively"),
    ),
    ("vibes_match_core", "catalogue.json", lambda found: vibe(found, "leafy").update(lens=False)),
    # The manifest says the release holds no recorded crime, and it carries Gritty.
    ("vibes_match_core", "catalogue.json", set_in("manifest.json", None, gritty_variant="a")),
    # A row for a vibe the release does not carry.
    ("references_resolve", "tags.json", a_row_of_gritty_where_no_recorded_crime_is_held),
    ("bands_match_raw", "tags.json", a_band_one_higher),
    ("bands_match_raw", "tags.json", band(band=None, spread_low=None, spread_high=None)),
    ("bands_match_raw", "tags.json", band(spread_low=5, spread_high=5)),
    ("bands_match_raw", "tags.json", band(spread_low=1, spread_high=1)),
    ("bands_match_raw", "tags.json", band(spread_low=None)),
    ("values_are_in_range", "tags.json", band(band=6)),
    ("values_are_in_range", "tags.json", band(spread_low=0)),
    ("shape_is_valid", "manifest.json", set_in("manifest.json", None, gritty_variant="c")),
    ("rows_are_complete", "features.json", drop("features.json", 4)),
    ("rows_are_complete", "tags.json", drop("tags.json", 4)),
    ("rows_are_complete", "geometry.json", drop("geometry.json", 4)),
    # A destination that no journey was routed to.
    (
        "rows_are_complete",
        "travel.json",
        repeat("destinations.json", 0, destination_id="syn-d0009"),
    ),
    (
        "rows_are_complete",
        "travel.json",
        set_in("travel.json", None, area_ids=[area_id(n) for n in range(1, 8)]),
    ),
    ("rows_are_complete", "travel.json", lambda found: found["travel.json"]["walk"].pop()),
    ("rows_are_complete", "travel.json", lambda found: found["travel.json"]["cycle"][2].pop()),
    ("values_are_in_range", "features.json", set_in("features.json", 1, percentile=100.5)),
    ("values_are_in_range", "features.json", set_in("features.json", 1, coverage=1.2)),
    ("values_are_in_range", "tags.json", set_in("tags.json", 1, score=-1)),
    ("values_are_in_range", "tags.json", set_in("tags.json", 1, raw=1.01)),
    ("values_are_in_range", "cost.json", set_in("cost.json", 0, median=10)),
    ("values_are_in_range", "cost.json", set_in("cost.json", 0, upper_quartile=1)),
    ("values_are_in_range", "cost.json", set_in("cost.json", 0, segment="detached")),
    ("values_are_in_range", "travel.json", cell("pt_typical", 0, 0, 91)),
    ("values_are_in_range", "travel.json", cell("walk", 0, 0, 61)),
    ("values_are_in_range", "travel.json", cell("cycle", 0, 0, -2)),
    ("values_are_in_range", "travel.json", cell("pt_just_missed", 0, 0, 10)),
    (
        "values_are_in_range",
        "travel.json",
        set_in("travel.json", None, cutoff_minutes={"pt": 0, "cycle": 60, "walk": 60}),
    ),
    ("values_are_in_range", "stations.json", set_in("stations.json", 2, walk_minutes=11)),
    ("values_are_in_range", "stations.json", set_in("stations.json", 0, walk_minutes=-1)),
    (
        "values_are_in_range",
        "neighbourhoods.json",
        set_in("neighbourhoods.json", 0, centroid=[0.1, 95.0]),
    ),
    # A figure is held to what its unit can be: a share of the whole, or a count or a level.
    ("values_are_in_range", "features.json", figure_of("%", 140.0)),
    ("values_are_in_range", "features.json", figure_of("%", -0.1)),
    ("values_are_in_range", "features.json", figure_of("µg/m³", -5.0)),
    ("values_are_in_range", "features.json", figure_of("per ha", -1.0)),
    ("values_are_in_range", "features.json", figure_of("m", -1.0)),
    ("null_means_null", "features.json", set_in("features.json", 1, percentile=None)),
    ("null_means_null", "features.json", set_in("features.json", 0, percentile=50.0)),
    ("null_means_null", "tags.json", set_in("tags.json", 1, score=None)),
    ("null_means_null", "tags.json", set_in("tags.json", 1, raw=None)),
    # Below half coverage the source saw too little of the area to give a value.
    ("null_means_null", "features.json", set_in("features.json", 1, coverage=0.49)),
    ("null_means_null", "tags.json", set_in("tags.json", 1, coverage=0.55)),
    ("sources_are_stated", "catalogue.json", set_in("catalogue.json", 0, source_ids=[])),
    ("sources_are_stated", "catalogue.json", set_in("catalogue.json", 0, vintage="")),
    ("sources_are_stated", "cost.json", set_in("cost.json", 0, source_ids=[])),
    ("sources_are_stated", "cost.json", set_in("cost.json", 0, as_of="")),
    ("sources_are_stated", "travel.json", set_in("travel.json", None, as_of="")),
    ("sources_are_stated", "stations.json", set_in("stations.json", None, source_ids=[])),
    ("sources_are_stated", "neighbourhoods.json", set_in("neighbourhoods.json", None, as_of="")),
    ("sources_are_stated", "places.json", set_in("places.json", 0, source_id="")),
    ("sources_are_stated", "tags.json", score_with_no_feature_behind_it),
    # Only a preview may leave the sources of its journeys and its stations unstated.
    (
        "sources_are_stated",
        "travel.json",
        then(holds_no_journey_and_no_station, set_in("travel.json", None, **UNSTATED)),
    ),
    (
        "sources_are_stated",
        "stations.json",
        then(holds_no_journey_and_no_station, set_in("stations.json", None, **UNSTATED)),
    ),
    # And only where it holds none: a journey or a station must have a source to cite.
    (
        "sources_are_stated",
        "travel.json",
        then(says_it_is_a_preview, set_in("travel.json", None, **UNSTATED)),
    ),
    (
        "sources_are_stated",
        "stations.json",
        then(says_it_is_a_preview, set_in("stations.json", None, **UNSTATED)),
    ),
    # A source with no date, or a date with no source, is neither stated nor left out.
    (
        "sources_are_stated",
        "travel.json",
        then(says_it_is_a_preview, set_in("travel.json", None, as_of=None)),
    ),
    (
        "sources_are_stated",
        "stations.json",
        then(says_it_is_a_preview, set_in("stations.json", None, source_ids=[])),
    ),
    ("sources_are_stated", "neighbourhoods.json", set_in("neighbourhoods.json", None, **UNSTATED)),
    ("neighbours_are_symmetric", "neighbourhoods.json", one_way_neighbour),
    # A release that holds no journey, no cost or no station is not finished, and says so.
    ("finished_release_is_whole", "manifest.json", holds_no_journey_and_no_station),
    (
        "finished_release_is_whole",
        "manifest.json",
        lambda found: found["cost.json"].update(rows=[]),
    ),
    (
        "finished_release_is_whole",
        "manifest.json",
        lambda found: found["stations.json"].update(rows=[]),
    ),
    ("percentiles_match_values", "features.json", a_percentile_of_its_own),
    ("raw_matches_recipe", "tags.json", two_areas_in_each_others_place),
    ("raw_matches_recipe", "tags.json", a_part_that_says_more_than_was_there),
    ("scores_match_raw", "tags.json", a_score_of_its_own),
    ("shape_is_valid", "features.json", set_in("features.json", 0, note="looks fine to me")),
    ("shape_is_valid", "neighbourhoods.json", set_in("neighbourhoods.json", 0, population=4100)),
    ("shape_is_valid", "neighbourhoods.json", set_in("neighbourhoods.json", 0, rankable="yes")),
    ("shape_is_valid", "manifest.json", set_in("manifest.json", None, built_at="yesterday")),
    ("shape_is_valid", "manifest.json", set_in("manifest.json", None, preview="no")),
    ("shape_is_valid", "manifest.json", lambda found: found["manifest.json"].pop("preview")),
    ("shape_is_valid", "geometry.json", lambda found: as_multipolygon(found, keep_type=True)),
    ("files_are_expected", "cost.json", lambda found: found.pop("cost.json")),
    ("files_are_expected", "notes.json", lambda found: found.update({"notes.json": {}})),
]


def test_the_small_release_is_valid_before_it_is_broken():
    found = parse_release(documents())
    assert len(found.neighbourhoods) == 8
    # Four features are in core and in no release yet.
    assert len(found.metrics) == 43
    assert found.manifest.synthetic is True
    assert [vibe.tag_id for vibe in found.vibes] == [
        vibe.tag_id for vibe in tags_of(GrittyVariant.B)
    ]


@pytest.mark.parametrize(
    ("variant", "gritty", "not_carried"),
    [
        (GrittyVariant.A, TagId.WORKS_WAREHOUSES, TagId.STREET_CHARACTER),
        (GrittyVariant.B, TagId.STREET_CHARACTER, TagId.WORKS_WAREHOUSES),
    ],
)
def test_a_release_carries_the_ten_vibes_and_the_one_its_manifest_says_gritty_is(
    variant: GrittyVariant, gritty: TagId, not_carried: TagId
):
    found = parse_release(documents(variant))
    assert found.manifest.gritty_variant is variant
    assert found.vibes == tags_of(variant)
    assert len(found.vibes) == 11
    carried = {vibe.tag_id for vibe in found.vibes}
    assert gritty in carried and not_carried not in carried
    assert {row.tag_id for row in found.tags} == carried
    assert parse_release(found.documents()) == found


def as_real(found: Documents) -> Documents:
    """The same release as a real one is written: real ids, and a source that is not made up."""
    text = json.dumps(found).replace("syn-", "lon-")
    # The source id, wherever it is a value. The manifest's flag is a key, and is set below.
    text = text.replace('["synthetic"]', '["ons-data"]').replace(': "synthetic"', ': "ons-data"')
    real: Documents = json.loads(text)
    real["manifest.json"].update(synthetic=False, city="lon", seed=None)
    real["manifest.json"]["sources"][0]["attribution"] = "Source: a publisher, under a licence."
    return real


def test_gritty_as_a_scale_is_carried_by_a_release_that_is_not_made_up():
    # Decided on 2026-09-24: gritty is one vibe, and recorded criminal damage and recorded
    # anti-social behaviour are parts of it, in a release of London as in a made-up one
    # (ADR 0013, as amended). It was refused on any release that is not made up.
    real = parse_release(as_real(documents(GrittyVariant.B)))
    assert (real.manifest.synthetic, real.manifest.gritty_variant) == (False, GrittyVariant.B)
    assert TagId.STREET_CHARACTER in {vibe.tag_id for vibe in real.vibes}
    # Works and warehouses is a part of it, and is not served beside it.
    assert TagId.WORKS_WAREHOUSES not in {vibe.tag_id for vibe in real.vibes}
    # What holds recorded crime still says so, and a release that holds none carries none.
    assert TagId.STREET_CHARACTER in HOLDS_CRIME
    other = parse_release(as_real(documents(GrittyVariant.A)))
    assert TagId.STREET_CHARACTER not in {vibe.tag_id for vibe in other.vibes}
    assert other.tag("lon-n0001", TagId.STREET_CHARACTER) is None


def test_what_a_release_ranks_on_is_what_it_shows_and_what_its_figures_make():
    # The reviewer's three: a score moved apart from its raw value, two areas
    # in each other's place, and a percentile at the far end from its value.
    # Each was accepted, because only the band was held to the raw value.
    for break_it, rule in (
        (a_score_of_its_own, "scores_match_raw"),
        (two_areas_in_each_others_place, "raw_matches_recipe"),
        (a_percentile_of_its_own, "percentiles_match_values"),
    ):
        broken = documents()
        break_it(broken)
        assert rule_broken(broken)[1] == rule
    # The release that is committed keeps all three, in both ways gritty is built.
    for variant in GrittyVariant:
        assert parse_release(documents(variant)).manifest.gritty_variant is variant
    assert fixture_release().manifest.synthetic


def test_a_band_in_a_release_is_the_one_core_works_out_from_the_raw_values():
    release = small_release()
    rankable = [area.rankable for area in release.neighbourhoods]
    for found in release.vibes:
        rows = [release.tag(area.area_id, found.tag_id) for area in release.neighbourhoods]
        assert [row.band if row else None for row in rows] == list(
            band_of([row.raw if row else None for row in rows], rankable)
        )


@pytest.mark.parametrize(
    ("rule", "file", "break_it"),
    BROKEN,
    ids=[f"{rule}-{file}-{n}" for n, (rule, file, _) in enumerate(BROKEN)],
)
def test_a_release_that_breaks_a_rule_is_refused_for_that_rule(
    rule: str, file: str, break_it: Break
):
    broken = documents()
    break_it(broken)
    assert rule_broken(broken) == (file, rule)


def test_every_rule_of_the_contract_has_a_release_that_breaks_it():
    contract = {
        "versions_match",
        "synthetic_is_consistent",
        "ids_are_unique",
        "references_resolve",
        "catalogue_matches_core",
        "vibes_match_core",
        "rows_are_complete",
        "values_are_in_range",
        "null_means_null",
        "bands_match_raw",
        "sources_are_stated",
        "neighbours_are_symmetric",
        "finished_release_is_whole",
        "percentiles_match_values",
        "raw_matches_recipe",
        "scores_match_raw",
    }
    assert {getattr(rule, "__name__", "") for rule in RULES} == contract
    assert contract <= {rule for rule, _, _ in BROKEN}


def test_a_refusal_does_not_repeat_the_name_of_a_field_that_should_not_be_there():
    broken = documents()
    broken["places.json"]["places"][2]["Canary Wharfside"] = 1
    with pytest.raises(ReleaseError) as caught:
        parse_release(broken)
    assert str(caught.value) == "places.json: places[2]: shape_is_valid"


def test_a_refusal_names_the_file_the_row_and_the_rule_and_never_a_value():
    broken = documents()
    broken["features.json"]["rows"][7]["percentile"] = 4321.5
    broken["places.json"]["places"][0]["name"] = "Canary Wharfside"
    with pytest.raises(ReleaseError) as caught:
        parse_release(broken)
    assert str(caught.value) == "features.json: rows[7].percentile: values_are_in_range"
    assert (caught.value.file, caught.value.row) == ("features.json", "rows[7].percentile")
    assert "4321.5" not in repr(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__


def test_a_real_release_may_not_cite_the_synthetic_source_and_a_synthetic_one_nothing_else():
    mixed = documents()
    mixed["manifest.json"]["sources"].append(
        mixed["manifest.json"]["sources"][0] | {"source_id": "ons-rents"}
    )
    assert rule_broken(mixed) == ("manifest.json", "synthetic_is_consistent")


def of_london() -> Documents:
    """The small release with the ids and the source of a real one. It is still in open sea.

    Nothing in it is real. It is the made-up release under another flag, for
    the rules that hold a release that is not made up. It carries gritty as
    land use: the scale holds recorded crime, and no real release may carry it.
    """
    return as_real(documents(GrittyVariant.A))


def test_a_real_release_with_real_ids_and_sources_is_accepted():
    found = parse_release(of_london())
    assert found.manifest.synthetic is False
    assert found.neighbourhood("lon-n0001") is not None


# Some way off: three degrees east and three south of where the small release is drawn.
FAR_OFF = (2.9, -2.95)


def test_an_outline_drawn_far_from_the_point_inside_its_area_is_refused():
    """A slip in a builder would draw an area somewhere else."""
    moved = documents()
    ring = moved["geometry.json"]["features"][0]["geometry"]["coordinates"][0]
    ring[1] = list(FAR_OFF)
    assert rule_broken(moved) == ("geometry.json", "values_are_in_range")
    with pytest.raises(ReleaseError) as caught:
        parse_release(moved)
    assert caught.value.row == "features[0]"
    assert "2.9" not in str(caught.value)


def test_an_area_placed_far_from_its_neighbours_is_refused():
    moved = documents()
    moved["neighbourhoods.json"]["neighbourhoods"][2]["centroid"] = list(FAR_OFF)
    assert rule_broken(moved) == ("neighbourhoods.json", "values_are_in_range")


def test_a_release_is_held_to_itself_and_to_no_place_on_the_map():
    """So a made-up city may be drawn in open sea, and a test may draw one where it likes."""
    elsewhere = documents()
    for area in elsewhere["neighbourhoods.json"]["neighbourhoods"]:
        area["centroid"] = [area["centroid"][0] + 30, area["centroid"][1] - 20]
    for feature in elsewhere["geometry.json"]["features"]:
        ring = feature["geometry"]["coordinates"][0]
        feature["geometry"]["coordinates"] = [[[lon + 30, lat - 20] for lon, lat in ring]]
    assert len(parse_release(elsewhere).neighbourhoods) == 8


def test_a_figure_at_either_end_of_what_its_unit_allows_is_a_figure():
    whole = documents()
    at_its_end("%", 100.0, highest=True)(whole)
    at_its_end("per ha", 0.0, highest=False)(whole)
    # Each stands where it stood among the others: only the range is looked at here.
    assert parse_release(whole).manifest.synthetic is True


def test_an_area_may_be_drawn_as_one_polygon_or_as_several():
    several = documents()
    as_multipolygon(several)
    found = parse_release(several)
    first, second = found.geometry(area_id(1)), found.geometry(area_id(2))
    assert first is not None and second is not None
    assert (first.type, len(first.coordinates)) == ("MultiPolygon", 2)
    assert (second.type, len(second.coordinates)) == ("Polygon", 1)
    assert parse_release(found.documents()) == found


def test_a_preview_with_no_journey_and_no_station_states_no_source_for_either():
    """There is no timetable to cite, and naming one would be making a source up."""
    found = parse_release(preview_documents())
    assert found.manifest.preview is True
    assert (found.destinations, found.places, found.costs, found.station_rows) == ((), (), (), ())
    for part in (Part.TRAVEL, Part.STATIONS):
        origin = found.origin(part)
        assert (origin.source_ids, origin.as_of, origin.stated) == ((), None, False)
    # Its areas still say where they came from: that is not the preview's to leave out.
    assert found.origin(Part.NEIGHBOURHOODS).stated
    assert parse_release(found.documents()) == found


def test_a_release_says_how_much_of_each_recipe_it_holds_and_what_each_vibe_waits_on():
    """A vibe with no band said nothing of why, and its card showed a list with nothing in it."""
    whole = small_release()
    held = {found.tag_id: found for found in recipes_held(whole)}
    assert list(held) == [vibe.tag_id for vibe in whole.vibes]
    # Every recipe adds up to 100, and the release of the tests lacks four measures.
    for vibe in whole.vibes:
        found = held[vibe.tag_id]
        carried = [term for term in vibe.terms if term.feature_id in CARRIED]
        assert found.held == sum(term.hundredths for term in carried)
        assert found.held + sum(part.hundredths for part in found.waits_on) == 100
        assert [part.feature_id for part in found.waits_on] == [
            term.feature_id for term in vibe.terms if term.feature_id not in CARRIED
        ]
        assert (found.needed, found.placed) == (60, True)
    homes = held[TagId.HOMES]
    assert homes.held == 75
    assert [(part.label, part.hundredths) for part in homes.waits_on] == [
        ("Homes with private outdoor space", 25)
    ]
    assert held[TagId.LEAFY].waits_on == ()


def test_a_vibe_is_placed_only_where_some_area_has_a_band_for_it():
    release = unplaced(small_release(), TagId.LEAFY)
    assert not release.placed(TagId.LEAFY) and release.placed(TagId.PACE)
    found = {held.tag_id: held.placed for held in recipes_held(release)}
    assert found[TagId.LEAFY] is False and found[TagId.PACE] is True
    # A vibe the release does not carry is placed nowhere.
    assert not small_release(GrittyVariant.A).placed(TagId.STREET_CHARACTER)


def test_a_kind_of_home_is_costed_only_where_some_area_has_an_estimate_for_it():
    assert small_release().costed(Tenure.RENT, Segment.STUDIO)
    assert small_release().costed(Tenure.BUY, Segment.DETACHED)
    # A kind of home of the other tenure has no cost, and a preview holds no cost at all.
    assert not small_release().costed(Tenure.RENT, Segment.DETACHED)
    assert not any(
        preview_release().costed(tenure, segment) for tenure in Tenure for segment in Segment
    )


def test_a_preview_answers_that_a_journey_is_missing_and_never_that_it_takes_no_time():
    found = preview_release()
    for area in found.neighbourhoods:
        assert found.stations(area.area_id) == ()
        for mode in Mode:
            journey = found.travel(area.area_id, "syn-d0001", mode, PtBasis.TYPICAL)
            assert (journey.status, journey.minutes) == (TravelStatus.MISSING, None)


def test_a_release_with_no_journey_may_not_say_it_is_finished():
    """It once could, if its empty files named a source. A person shown it was told it was whole."""
    empty = documents()
    holds_no_journey_and_no_station(empty)
    assert rule_broken(empty) == ("manifest.json", "finished_release_is_whole")
    says_it_is_a_preview(empty)
    found = parse_release(empty)
    assert found.manifest.preview is True
    assert found.origin(Part.TRAVEL).stated and found.origin(Part.STATIONS).stated


def test_the_small_release_is_finished_and_holds_every_part():
    found = small_release()
    assert found.manifest.preview is False
    assert found.destinations and found.places and found.costs and found.station_rows


def test_a_preview_that_states_its_sources_is_a_release_like_any_other():
    whole = documents()
    says_it_is_a_preview(whole)
    found = parse_release(whole)
    assert found.manifest.preview is True
    assert found.origin(Part.TRAVEL).stated and found.origin(Part.STATIONS).stated


def test_a_release_may_carry_fewer_features_than_the_catalogue_holds():
    fewer = documents()
    dropped = FeatureId.SCHOOL_PRIMARY_ATTAINMENT.value
    fewer["catalogue.json"]["metrics"] = [
        m for m in fewer["catalogue.json"]["metrics"] if m["feature_id"] != dropped
    ]
    fewer["features.json"]["rows"] = [
        r for r in fewer["features.json"]["rows"] if r["feature_id"] != dropped
    ]
    found = parse_release(fewer)
    assert len(found.metrics) == 42
    assert found.feature(area_id(1), FeatureId.SCHOOL_PRIMARY_ATTAINMENT) is None


def packed(found: Documents) -> tuple[str, dict[str, bytes]]:
    """A release as it sits in its folder: bytes, and a manifest that lists their checksums."""
    files = {
        name: (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for name, document in found.items()
        if name != "manifest.json"
    }
    manifest = found["manifest.json"] | {
        "files": [
            {"name": name, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
            for name, content in sorted(files.items())
        ]
    }
    files["manifest.json"] = json.dumps(manifest).encode()
    return manifest["release_id"], files


def refused(folder: str, files: dict[str, bytes]) -> tuple[str, str]:
    with pytest.raises(ReleaseError) as caught:
        open_release(folder, files)
    return caught.value.file, caught.value.rule


def test_a_release_opens_from_its_bytes():
    folder, files = packed(documents())
    opened = open_release(folder, files)
    assert opened.manifest.release_id == RELEASE_ID
    assert len(opened.manifest.files) == 10
    assert dataclasses_equal_but_for_the_manifest(opened, small_release())


def dataclasses_equal_but_for_the_manifest(one: InMemoryRelease, other: InMemoryRelease) -> bool:
    return dataclasses.replace(one, manifest=other.manifest) == other


def test_release_with_a_changed_file_is_refused():
    folder, files = packed(documents())
    # One digit of one rent, with the length of the file left the same.
    changed = files["cost.json"].replace(b"1400", b"1300", 1)
    assert changed != files["cost.json"]
    assert len(changed) == len(files["cost.json"])
    files["cost.json"] = changed
    assert refused(folder, files) == ("cost.json", "files_match_manifest")


def test_release_with_a_file_of_another_length_is_refused():
    folder, files = packed(documents())
    files["tags.json"] += b" "
    assert refused(folder, files) == ("tags.json", "files_match_manifest")


def test_release_with_an_extra_or_a_missing_file_is_refused():
    folder, files = packed(documents())
    assert refused(folder, files | {"extra.json": b"{}"}) == ("extra.json", "files_match_manifest")
    missing = {name: content for name, content in files.items() if name != "places.json"}
    assert refused(folder, missing) == ("places.json", "files_match_manifest")
    no_manifest = {name: content for name, content in files.items() if name != "manifest.json"}
    assert refused(folder, no_manifest) == ("manifest.json", "files_match_manifest")


def test_release_in_a_folder_of_another_name_is_refused():
    folder, files = packed(documents())
    assert folder == RELEASE_ID
    assert refused("syn-2026-09-24-01", files) == ("manifest.json", "release_id_matches_folder")


def test_a_file_that_is_not_json_is_refused_without_repeating_it():
    found = documents()
    folder, files = packed(found)
    files["manifest.json"] = b"{not json, Canary Wharfside"
    with pytest.raises(ReleaseError) as caught:
        open_release(folder, files)
    assert (caught.value.file, caught.value.rule) == ("manifest.json", "json_is_valid")
    assert "Canary" not in str(caught.value)

    for content in (b'{"rows": [NaN]}', b"\xff\xfe", b'{"rows": [Infinity]}'):
        _, again = packed(found)
        again["features.json"] = content
        manifest = json.loads(again["manifest.json"])
        for entry in manifest["files"]:
            if entry["name"] == "features.json":
                entry.update(sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))
        again["manifest.json"] = json.dumps(manifest).encode()
        assert refused(folder, again) == ("features.json", "json_is_valid")


def test_a_release_written_out_and_read_back_is_the_same_release():
    release = small_release()
    assert parse_release(release.documents()) == release
    assert parse_release(json.loads(json.dumps(release.documents()))) == release
    assert set(release.documents()) == set(module.DATA_FILES) | {module.MANIFEST}


def test_a_release_is_the_same_whatever_order_its_rows_were_written_in():
    forwards = documents()
    backwards = documents()
    for file in ("features.json", "tags.json", "cost.json", "places.json", "stations.json"):
        rows(backwards, file).reverse()
    rows(backwards, "geometry.json").reverse()
    rows(backwards, "catalogue.json").reverse()
    assert parse_release(backwards) == parse_release(forwards)
    assert parse_release(backwards).documents() == parse_release(forwards).documents()


def test_in_memory_release_is_a_release():
    release: Release = small_release()
    assert [n.area_id for n in release.neighbourhoods] == [area_id(n) for n in range(1, 9)]
    assert [m.feature_id for m in release.metrics] == sorted(CARRIED)
    assert [v.shelf_order for v in release.vibes] == [*range(1, 11), 12]
    assert [p.place_id for p in release.places] == sorted(p.place_id for p in release.places)
    assert release.cutoff(Mode.PT) == 90
    assert release.cutoff(Mode.WALK) == 60
    assert release.origin(Part.TRAVEL).as_of == "2026-09"
    assert release.origin(Part.NEIGHBOURHOODS).source_ids == ("synthetic",)
    assert release.origin(Part.STATIONS).source_ids == ("synthetic",)


def test_an_id_the_release_does_not_know_is_none():
    release = small_release()
    assert release.neighbourhood("syn-n0099") is None
    assert release.geometry("syn-n0099") is None
    assert release.place("syn-p0099") is None
    assert release.feature("syn-n0099", FeatureId.AIR_NO2) is None
    assert release.tag("syn-n0099", TagId.LEAFY) is None
    assert release.stations("syn-n0099") == ()
    # The last rankable area has no estimate, on purpose. That is None, not a guess.
    assert release.cost(area_id(7), Tenure.RENT, Segment.BED_1) is None
    assert release.cost("syn-n0099", Tenure.RENT, Segment.BED_1) is None
    assert release.cost(area_id(1), Tenure.RENT, Segment.BED_1) is not None


def test_stations_are_given_nearest_first():
    release = small_release()
    for area in release.neighbourhoods:
        found = release.stations(area.area_id)
        assert [s.nearest for s in found] == [True] + [False] * (len(found) - 1)
    assert len(release.stations(area_id(2))) == 2


def test_travel_never_returns_none_and_spells_each_kind_of_cell_one_way():
    release = small_release()
    ok = release.travel(area_id(1), "syn-d0001", Mode.PT, PtBasis.TYPICAL)
    assert (ok.status, ok.minutes) == (TravelStatus.OK, 15)
    missed = release.travel(area_id(1), "syn-d0001", Mode.PT, PtBasis.JUST_MISSED)
    assert missed.minutes == 20
    # Not computed, which is missing data.
    unknown = release.travel(area_id(3), "syn-d0002", Mode.PT, PtBasis.TYPICAL)
    assert (unknown.status, unknown.minutes) == (TravelStatus.MISSING, None)
    # No journey within the cutoff, which is data.
    beyond = release.travel(area_id(4), "syn-d0003", Mode.PT, PtBasis.TYPICAL)
    assert (beyond.status, beyond.minutes) == (TravelStatus.BEYOND_CUTOFF, None)
    # The basis is ignored by bike and on foot.
    by_bike = [release.travel(area_id(1), "syn-d0001", Mode.CYCLE, basis) for basis in PtBasis]
    assert by_bike[0] == by_bike[1]
    assert by_bike[0].minutes == 25
    assert release.travel("", "", Mode.WALK, PtBasis.TYPICAL).status is TravelStatus.MISSING


def test_no_travel_time_is_ever_a_number_that_stands_for_unknown():
    release = small_release()
    seen: set[TravelStatus] = set()
    for area in release.neighbourhoods:
        for destination in release.destinations:
            for mode in Mode:
                found = release.travel(
                    area.area_id, destination.destination_id, mode, PtBasis.TYPICAL
                )
                seen.add(found.status)
                assert (found.minutes is None) == (found.status is not TravelStatus.OK)
                assert found.minutes is None or 0 <= found.minutes <= release.cutoff(mode)
    assert seen == set(TravelStatus)
    with pytest.raises(ValidationError):
        Travel(status=TravelStatus.MISSING, minutes=0)
    with pytest.raises(ValidationError):
        Travel(status=TravelStatus.OK, minutes=None)


def test_the_release_holds_no_count_of_residents():
    # A count of residents that is not in the release cannot be ranked on or shown.
    text = json.dumps(small_release().documents()).lower()
    assert "population" not in text
    # The unit of a rate of recorded crime says residents, and so does the one name that
    # may: the share of them that transport noise reaches. Neither is a count of them.
    noise = FEATURES[FeatureId.NOISE_EXPOSURE].label.lower()
    assert noise == "share of residents exposed to 55 db or more of transport noise"
    for said in ("per 1,000 residents a year", noise):
        text = text.replace(said, "")
    assert "residents" not in text


def test_percentiles_in_the_small_release_are_the_ones_the_catalogue_would_compute():
    release = small_release()
    rankable = [n.rankable for n in release.neighbourhoods]
    for metric in release.metrics:
        found = [release.feature(n.area_id, metric.feature_id) for n in release.neighbourhoods]
        values = [f.value if f else None for f in found]
        assert [f.percentile if f else None for f in found] == list(percentile_of(values, rankable))


def test_a_release_built_by_hand_is_not_checked():
    # The worked example gives percentiles no four areas could have. It is
    # built by hand, so nothing refuses it, and rank reads it as it stands.
    release = build_worked_release()
    assert [f.percentile for f in release.features if f.feature_id == "park_proximity"] == [
        20.0,
        60.0,
        10.0,
        30.0,
    ]


# A release that is not made up is served only with what it was built with


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def built_beside(files: dict[str, bytes], **changes: str) -> dict[str, bytes]:
    """What stands beside a real release: its evidence, its lock, and the hashes of the build.

    The evidence and the lock are not read by core. It holds their bytes to the
    hashes, and nothing more, so any bytes will do here.
    """
    beside = {EVIDENCE: b'{"rows":[]}\n', LOCK: b'{"inputs":[]}\n'}
    hashes = {
        "release_id": json.loads(files[MANIFEST])["release_id"],
        "manifest_sha256": sha256(files[MANIFEST]),
        "evidence_sha256": sha256(beside[EVIDENCE]),
        "lock_sha256": sha256(beside[LOCK]),
    } | changes
    return beside | {HASHES: json.dumps(hashes).encode()}


def not_served(
    folder: str, files: dict[str, bytes], beside: dict[str, bytes] | None
) -> tuple[str, str]:
    with pytest.raises(ReleaseError) as caught:
        open_served(folder, files, beside)
    return caught.value.file, caught.value.rule


def test_a_made_up_release_is_served_with_nothing_beside_it():
    folder, files = packed(documents())
    assert open_served(folder, files, None).manifest.synthetic is True


def test_a_real_release_is_served_with_its_evidence_and_its_lock_beside_it():
    folder, files = packed(of_london())
    served = open_served(folder, files, built_beside(files))
    assert served == open_release(folder, files)
    assert served.manifest.synthetic is False


def test_a_real_release_with_nothing_beside_it_is_not_served():
    """A figure with no evidence behind it is not a figure."""
    folder, files = packed(of_london())
    assert not_served(folder, files, None) == (HASHES, "real_release_has_its_build")
    assert not_served(folder, files, {}) == (HASHES, "real_release_has_its_build")


@pytest.mark.parametrize("missing", [HASHES, EVIDENCE, LOCK])
def test_a_real_release_that_lacks_a_file_of_its_build_is_not_served(missing: str):
    folder, files = packed(of_london())
    beside = {name: held for name, held in built_beside(files).items() if name != missing}
    assert not_served(folder, files, beside) == (missing, "real_release_has_its_build")


def test_a_release_changed_after_it_was_built_is_not_served():
    """The manifest holds the hash of every file, so a figure that is changed changes it."""
    folder, files = packed(of_london())
    beside = built_beside(files)
    changed = of_london()
    # Raised, and left where it stood among the others, so that core still reads the release.
    at_its_end("%", 99.0, highest=True)(changed)
    _, after = packed(changed)
    assert after["features.json"] != files["features.json"]
    assert open_release(folder, after).manifest.synthetic is False
    assert not_served(folder, after, beside) == (MANIFEST, "build_is_as_it_was_written")


@pytest.mark.parametrize("changed", [EVIDENCE, LOCK])
def test_evidence_or_a_lock_changed_after_the_build_is_not_served(changed: str):
    folder, files = packed(of_london())
    beside = built_beside(files)
    beside[changed] += b" "
    assert not_served(folder, files, beside) == (changed, "build_is_as_it_was_written")


def test_the_build_of_another_release_is_not_served():
    folder, files = packed(of_london())
    beside = built_beside(files, release_id="lon-2026-09-22-01")
    assert not_served(folder, files, beside) == (HASHES, "build_is_of_this_release")


@pytest.mark.parametrize(
    ("hashes", "rule"),
    [
        (b"{not json, Canary Wharfside", "json_is_valid"),
        (b'{"release_id": "lon-2026-09-23-01"}', "shape_is_valid"),
        (b'{"release_id": "lon-2026-09-23-01", "manifest_sha256": "abc"}', "shape_is_valid"),
    ],
)
def test_hashes_that_cannot_be_read_are_refused_without_repeating_them(hashes: bytes, rule: str):
    folder, files = packed(of_london())
    beside = built_beside(files) | {HASHES: hashes}
    with pytest.raises(ReleaseError) as caught:
        open_served(folder, files, beside)
    assert (caught.value.file, caught.value.rule) == (HASHES, rule)
    assert "Canary" not in str(caught.value) and "abc" not in str(caught.value)


def test_a_release_that_breaks_a_rule_is_refused_before_its_build_is_looked_at():
    folder, files = packed(of_london())
    files["tags.json"] += b" "
    assert not_served(folder, files, None) == ("tags.json", "files_match_manifest")
