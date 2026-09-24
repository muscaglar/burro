import dataclasses
import hashlib
import json
from collections.abc import Callable
from typing import Any

import pytest
from burro_core import release as module
from burro_core.catalogue import percentile_of
from burro_core.ids import FeatureId, Mode, Part, PtBasis, Segment, TagId, Tenure, TravelStatus
from burro_core.release import (
    RULES,
    InMemoryRelease,
    Release,
    ReleaseError,
    Travel,
    open_release,
    parse_release,
)
from pydantic import ValidationError

from .support import RELEASE_ID, area_id, build_worked_release, documents, small_release

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


def one_way_neighbour(found: Documents) -> None:
    found["neighbourhoods.json"]["neighbourhoods"][0]["neighbours"] = [area_id(2)]
    # Area 8 still lists area 1, and area 1 no longer lists it back.


def score_with_no_feature_behind_it(found: Documents) -> None:
    # Waterside is water_access alone. Give area 1 no water figure, and keep its score.
    scored = [r for r in found["tags.json"]["rows"] if r["tag_id"] == "waterside"]
    assert scored[0]["area_id"] == area_id(1)
    assert scored[0]["score"] is not None
    for row in found["features.json"]["rows"]:
        if (row["area_id"], row["feature_id"]) == (area_id(1), "water_access"):
            row.update(value=None, percentile=None)


def as_multipolygon(found: Documents, keep_type: bool = False) -> None:
    """Make the first area two squares. With `keep_type` it still claims to be a polygon."""
    geometry = found["geometry.json"]["features"][0]["geometry"]
    ring = geometry["coordinates"]
    moved = [[[lon + 0.01, lat] for lon, lat in ring[0]]]
    geometry["coordinates"] = [ring, moved]
    if not keep_type:
        geometry["type"] = "MultiPolygon"


BROKEN: list[tuple[str, str, Break]] = [
    ("versions_match", "manifest.json", set_in("manifest.json", None, schema_version=2)),
    ("versions_match", "manifest.json", set_in("manifest.json", None, catalogue_version=2)),
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
    ("neighbours_are_symmetric", "neighbourhoods.json", one_way_neighbour),
    ("shape_is_valid", "features.json", set_in("features.json", 0, note="looks fine to me")),
    ("shape_is_valid", "neighbourhoods.json", set_in("neighbourhoods.json", 0, population=4100)),
    ("shape_is_valid", "neighbourhoods.json", set_in("neighbourhoods.json", 0, rankable="yes")),
    ("shape_is_valid", "manifest.json", set_in("manifest.json", None, built_at="yesterday")),
    ("shape_is_valid", "geometry.json", lambda found: as_multipolygon(found, keep_type=True)),
    ("files_are_expected", "cost.json", lambda found: found.pop("cost.json")),
    ("files_are_expected", "notes.json", lambda found: found.update({"notes.json": {}})),
]


def test_the_small_release_is_valid_before_it_is_broken():
    found = parse_release(documents())
    assert len(found.neighbourhoods) == 8
    assert len(found.metrics) == 23
    assert found.manifest.synthetic is True


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
        "rows_are_complete",
        "values_are_in_range",
        "null_means_null",
        "sources_are_stated",
        "neighbours_are_symmetric",
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


def test_a_real_release_with_real_ids_and_sources_is_accepted():
    text = json.dumps(documents()).replace("syn-", "lon-")
    # The source id, wherever it is a value. The manifest's flag is a key, and is set below.
    text = text.replace('["synthetic"]', '["ons-data"]').replace(': "synthetic"', ': "ons-data"')
    real: Documents = json.loads(text)
    real["manifest.json"].update(synthetic=False, city="lon", seed=None)
    real["manifest.json"]["sources"][0]["attribution"] = "Source: a publisher, under a licence."
    found = parse_release(real)
    assert found.manifest.synthetic is False
    assert found.neighbourhood("lon-n0001") is not None


def test_an_area_may_be_drawn_as_one_polygon_or_as_several():
    several = documents()
    as_multipolygon(several)
    found = parse_release(several)
    first, second = found.geometry(area_id(1)), found.geometry(area_id(2))
    assert first is not None and second is not None
    assert (first.type, len(first.coordinates)) == ("MultiPolygon", 2)
    assert (second.type, len(second.coordinates)) == ("Polygon", 1)
    assert parse_release(found.documents()) == found


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
    assert len(found.metrics) == 22
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
    assert [m.feature_id for m in release.metrics] == sorted(FeatureId)
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
    assert release.cost(area_id(1), Tenure.RENT, Segment.BED_4PLUS) is None
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
    assert "residents" not in text.replace("per 1,000 residents a year", "")


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
