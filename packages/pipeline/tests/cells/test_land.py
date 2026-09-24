"""The land each LSOA covers, and each area, in hectares.

Every file here is made up. A square of the made-up town is 100 metres wide,
which is one hectare, so the land of any part of it can be counted by eye.
"""

import math
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, land, spine
from burro_pipeline.cells.shapes import outline_of
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.registry.model import Use

from .support import (
    CENTRES_COLUMNS,
    EAST,
    LONDON,
    NORTH,
    TOWN,
    centres_csv,
    contents,
    inputs_of,
    lsoa_outlines,
    registry,
)


def built(folder: Path, **files: bytes) -> land.Land:
    inputs = inputs_of(folder, contents() | files)
    return land.build(inputs, spine.build(inputs))


def test_the_land_of_an_lsoa_is_what_its_outline_encloses(tmp_path: Path):
    found = built(tmp_path)
    assert len(found.of_lsoa) == 6
    # Two squares side by side, but for the last, which has an island of one square more.
    assert found.of_lsoa["E01999001"] == 2.0
    assert found.of_lsoa["E01999006"] == 3.0


def test_the_land_of_an_area_is_the_sum_of_its_lsoas(tmp_path: Path):
    found = built(tmp_path)
    assert found.of_area == {
        "lon-ne02999001": 4.0,
        "lon-ne02999002": 4.0,
        "lon-ne02999003": 5.0,
    }
    assert sum(found.of_area.values()) == sum(found.of_lsoa.values())


def test_the_land_is_kept_with_a_half_taken_upward_as_every_figure_is(tmp_path: Path):
    """The language's own rounding takes this half downward. A person with a pencil does not."""
    found = spine.build(inputs_of(tmp_path, contents()))
    # One hectare and ten and a half square metres: 1.00105 hectares.
    odd = outline_of([[[(0.0, 0.0), (1.0, 0.0), (1.0, 10_010.5), (0.0, 10_010.5), (0.0, 0.0)]]])
    one = outline_of([[[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0), (0.0, 0.0)]]])
    first, *others = found.lsoas
    measured = land.land_of(found, {first: odd} | dict.fromkeys(others, one), "f-0123456789ab")
    assert round(1.00105, land.DECIMALS) == 1.001
    assert measured.of_lsoa[first] == land.kept(1.00105) == 1.0011
    assert land.kept(math.fsum([1.00105, 1.0])) == 2.0011


def test_the_land_names_the_file_it_was_measured_on(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    found = land.build(inputs, spine.build(inputs))
    (opened,) = [one for one in inputs.opened if one.receipt.source_id == land.BOUNDARIES]
    assert found.file_id == opened.file_id


def test_the_land_is_measured_on_boundaries_registered_for_scoring(tmp_path: Path):
    """One measure divides by the land, so its source must be one the gate allows to score."""
    assert Use.SCORING in registry().get(land.BOUNDARIES).uses
    assert built(tmp_path)


def test_an_lsoa_with_no_outline_stops_the_build(tmp_path: Path):
    with pytest.raises(LockError) as refused:
        built(tmp_path, lsoa_outlines=lsoa_outlines(TOWN[2:]))
    assert refused.value.rule == "input_is_as_described"
    assert "no outline" in str(refused.value)


# The centres of population


def centred(folder: Path, **files: bytes) -> dict[str, tuple[float, float]]:
    inputs = inputs_of(folder, contents() | files)
    return centres.build(inputs, spine.build(inputs))


def test_a_centre_is_the_point_the_file_gives_for_an_output_area(tmp_path: Path):
    found = centred(tmp_path)
    assert set(found) == {unit.oa for unit in LONDON}
    assert found["E00999003"] == (EAST + 50.25, NORTH + 50.75)


def test_an_output_area_with_no_centre_is_left_out_and_nothing_stands_in(tmp_path: Path):
    found = centred(tmp_path, centres=centres_csv(TOWN[1:]))
    assert TOWN[0].oa not in found
    assert len(found) == len(LONDON) - 1


def test_a_point_that_is_no_number_stops_the_build(tmp_path: Path):
    broken = centres_csv().replace(b"700050.2500", b"Zzyzx Parva")
    with pytest.raises(LockError) as refused:
        centred(tmp_path, centres=broken)
    assert refused.value.rule == "input_is_as_described"
    assert "Zzyzx" not in str(refused.value)


def test_the_file_of_centres_has_the_columns_the_publishers_has():
    assert centres_csv().splitlines()[0] == b"\xef\xbb\xbf" + ",".join(CENTRES_COLUMNS).encode()
