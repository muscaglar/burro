"""Each area's outline: its output areas joined, as a map can draw it.

Every file here is made up. The town is drawn in squares of 100 metres in the
North Sea, so no outline here can be laid over a real street.
"""

from dataclasses import replace
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

import pytest
from burro_core.release import Geometry
from burro_pipeline.cells import outline, shapes, spine
from burro_pipeline.cells.outline import Outline
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use
from burro_pipeline.release.write import canonical_json

from .support import (
    EAST,
    NORTH,
    SIDE,
    TOWN,
    contents,
    geopackage,
    held,
    inputs_of,
    oa_outlines,
    outline_blob,
    registry,
)

Q1, Q2, T1 = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
Ring = list[list[float]]


def built(folder: Path, **files: bytes) -> dict[str, Outline]:
    inputs = inputs_of(folder, contents() | files)
    return outline.build(inputs, spine.build(inputs))


def rings_of(found: Outline) -> list[Ring]:
    """Every ring of an outline, the outer ring of each piece first."""
    geometry = cast(dict[str, Any], found.geometry)
    pieces = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    return [ring for piece in pieces for ring in piece]


def twice_the_area(ring: Ring) -> float:
    """Above nothing for a ring that runs anticlockwise, below for one that runs clockwise."""
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in pairwise(ring))


def test_an_outline_is_the_areas_output_areas_joined_with_no_line_between(tmp_path: Path):
    found = built(tmp_path)[Q1]
    assert found.geometry["type"] == "Polygon"
    (ring,) = rings_of(found)
    corners = [(0, 0), (2, 0), (2, 2), (0, 2)]
    for across, up in corners:
        corner = shapes.longitude_and_latitude(EAST + across * SIDE, NORTH + up * SIDE)
        assert list(corner) in ring
    # Four output areas of five points each are one ring, with no point inside it.
    middle = list(shapes.longitude_and_latitude(EAST + SIDE, NORTH + SIDE))
    assert 5 <= len(ring) <= 9 and middle not in ring
    assert (found.units_used, found.units_expected, found.pieces) == (4, 4, 1)


def test_a_ring_is_closed_and_runs_as_the_standard_asks(tmp_path: Path):
    for found in built(tmp_path).values():
        for ring in rings_of(found):
            assert ring[0] == ring[-1] and len(ring) >= 4
            assert twice_the_area(ring) > 0
            assert all(round(part, 6) == part for point in ring for part in point)


def test_an_area_in_two_pieces_is_drawn_in_two(tmp_path: Path):
    found = built(tmp_path)[T1]
    assert (found.geometry["type"], found.pieces, len(rings_of(found))) == ("MultiPolygon", 2, 2)


def test_a_point_is_given_inside_the_largest_piece(tmp_path: Path):
    found = built(tmp_path)[T1]
    west, south = shapes.longitude_and_latitude(EAST + 4 * SIDE, NORTH)
    east, north = shapes.longitude_and_latitude(EAST + 6 * SIDE, NORTH + 2 * SIDE)
    assert west < found.centre[0] < east and south < found.centre[1] < north


def test_neighbours_share_a_side_and_each_names_the_other(tmp_path: Path):
    found = built(tmp_path)
    assert {area: found[area].neighbours for area in found} == {
        Q1: (Q2,),
        Q2: (Q1, T1),
        T1: (Q2,),
    }


def test_areas_that_meet_at_a_corner_are_not_neighbours(tmp_path: Path):
    """The second area is moved up, so that it meets the first and the third at a corner."""
    moved = [
        replace(unit, squares=tuple((column, row + 2) for column, row in unit.squares))
        if unit.msoa == "E02999002"
        else unit
        for unit in TOWN
    ]
    found = built(tmp_path, outlines=oa_outlines(moved))
    assert [found[area].neighbours for area in (Q1, Q2, T1)] == [(), (), ()]


def test_core_takes_every_outline_as_a_geometry_of_a_release(tmp_path: Path):
    for found in built(tmp_path).values():
        Geometry.model_validate(found.geometry)


def test_the_outlines_are_written_as_the_contract_lays_out_geometry_json(tmp_path: Path):
    collection = outline.feature_collection(built(tmp_path))
    features = cast(list[dict[str, Any]], collection["features"])
    assert collection["type"] == "FeatureCollection"
    assert [feature["id"] for feature in features] == [Q1, Q2, T1]
    assert all(feature["properties"] == {"area_id": feature["id"]} for feature in features)
    assert all(set(feature) == {"type", "id", "properties", "geometry"} for feature in features)


def test_the_same_files_give_the_same_bytes(tmp_path: Path):
    first = canonical_json(outline.feature_collection(built(tmp_path / "a")))
    assert first == canonical_json(outline.feature_collection(built(tmp_path / "b")))


def test_nothing_is_written_to_the_store_or_beside_the_file(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    before = held(tmp_path / "store")
    outline.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before
    assert sorted(path.name for path in (tmp_path / "work").rglob("*.gpkg*")) == [
        "Output_Areas_2021_EW_BGC_V2_made_up.gpkg"
    ]


# From the National Grid to longitude and latitude


def test_a_point_of_the_grid_is_turned_by_one_fixed_operation():
    """Held to what the operation gave on 2026-09-23, so that a library that moves it is seen.

    A test on the real boundaries holds it to the publisher's own latitude and longitude.
    """
    assert shapes.longitude_and_latitude(EAST, NORTH) == (2.513016, 53.411393)
    assert shapes.longitude_and_latitude(530000, 180000) == (-0.128354, 51.503991)


def test_the_same_operation_run_the_other_way_gives_the_point_of_the_grid_back():
    """A longitude and a latitude are given to six decimal places, about a tenth of a metre."""
    places = [(float(EAST), float(NORTH)), (530_000.0, 180_000.0), (503_000.5, 155_000.25)]
    there = [shapes.longitude_and_latitude(east, north) for east, north in places]
    back = shapes.national_grid([one[0] for one in there], [one[1] for one in there])
    assert len(back) == len(places)
    for (east, north), (found_east, found_north) in zip(places, back, strict=True):
        assert abs(found_east - east) < 0.1 and abs(found_north - north) < 0.1
    assert shapes.national_grid([], []) == []
    assert not shapes.may_reach_a_network()


def test_the_operation_reads_no_grid_file_and_reaches_no_network():
    assert "helmert" in shapes.TO_LONGITUDE_AND_LATITUDE
    assert "grid" not in shapes.TO_LONGITUDE_AND_LATITUDE
    shapes.longitude_and_latitude(EAST, NORTH)
    assert not shapes.may_reach_a_network()


def test_the_middle_of_the_grids_square_tq_38_is_in_london():
    """The square TQ 38 of the National Grid is east London, which any map of the grid shows."""
    longitude, latitude = shapes.longitude_and_latitude(535_000, 185_000)
    assert -0.1 < longitude < 0.0 and 51.5 < latitude < 51.6


# What stops the build


def refusal(folder: Path, **files: bytes) -> LockError:
    with pytest.raises(LockError) as refused:
        built(folder, **files)
    return refused.value


def test_an_output_area_with_no_outline_stops_the_build(tmp_path: Path):
    error = refusal(tmp_path, outlines=oa_outlines(TOWN[1:]))
    assert (error.rule, "no outline" in str(error)) == ("input_is_as_described", True)


def test_outlines_in_another_grid_stop_the_build(tmp_path: Path):
    blobs = {unit.oa: outline_blob(unit.squares, grid=4326) for unit in TOWN}
    error = refusal(tmp_path, outlines=geopackage("OA_2021_EW_BGC_V2", "OA21CD", blobs, 4326))
    assert error.rule == "input_is_as_described"
    # A layer that says it is in the grid, and whose outlines say they are not.
    error = refusal(tmp_path / "b", outlines=geopackage("OA_2021_EW_BGC_V2", "OA21CD", blobs))
    assert error.rule == "input_is_as_described"


def test_a_file_that_is_no_geopackage_stops_the_build(tmp_path: Path):
    error = refusal(tmp_path, outlines=b"Made up for a test. It is no GeoPackage.\n")
    assert error.rule == "input_is_as_described"
    assert "Made up" not in str(error)


def test_outlines_that_lie_over_each_other_stop_the_build(tmp_path: Path):
    """An output area of the second area is drawn over one of the first."""
    over = [replace(unit, squares=((1, 1),)) if unit.oa == "E00999005" else unit for unit in TOWN]
    error = refusal(tmp_path, outlines=oa_outlines(over))
    assert (error.rule, "fit together" in str(error)) == ("input_is_as_described", True)


# The gate


def test_the_boundaries_are_read_for_cells_and_never_for_scoring(tmp_path: Path):
    """The registry holds the output area boundaries for cells and not for scoring."""
    source = registry().get(outline.BOUNDARIES)
    assert Use.CELLS in source.uses and Use.SCORING not in source.uses
    assert built(tmp_path)  # so the step asked for a use the entry has


def test_the_gate_is_asked_before_the_boundaries_are_read(tmp_path: Path):
    sources = [
        source.model_copy(update={"uses": (Use.GAZETTEER,)})
        if source.id == outline.BOUNDARIES
        else source
        for source in registry()
    ]
    inputs = inputs_of(tmp_path, contents(), registry=Registry(tuple(sources)))
    with pytest.raises(LockError) as refused:
        outline.build(inputs, spine.build(inputs))
    assert refused.value.rule == "gate_refuses"
    assert {opened.receipt.source_id for opened in inputs.opened} == {spine.LOOKUP, spine.HOMES}
