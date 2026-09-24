"""Nitrogen dioxide, worked out from the files their publishers gave.

Every other test of the measure runs on a made-up grid. These read the real
one, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts and a few figures, so that a publisher's file that changes
is noticed. A figure here is London's lowest, middle or highest, or that of all
of London. None is said of a named area. Each was worked out on 2026-09-23.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.spine import Homes, Spine
from burro_pipeline.derive import air_no2
from burro_pipeline.derive.air_no2 import Air
from burro_pipeline.derive.methods import grid_at_homes
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, held, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)
# The grid, the centres, the lookup and the table of homes, by the ids of their receipts.
GRID, CENTRES, LOOKUP, HOMES = (
    "f-d169e49479d8",
    "f-00e1d0532798",
    "f-49321b95f212",
    "f-af7b512615ea",
)


def listing() -> dict[str, tuple[int, int]]:
    """Every file of the store, with its size and when it was last written."""
    return {
        path.relative_to(STORE).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(Path(STORE).rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def before() -> dict[str, tuple[int, int]]:
    return listing()


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory, before: dict[str, tuple[int, int]]) -> Inputs:
    work = tmp_path_factory.mktemp("real")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Air:
    return air_no2.build(real, found)


def values_of(made: Air) -> list[float]:
    return sorted(one.value for one in made.worked.values() if one.value is not None)


# The grid


def test_the_grid_holds_as_many_squares_as_were_counted(made: Air):
    assert made.grid.file_id == GRID
    assert (made.grid.year, made.grid.rows, made.grid.without_a_value) == (2024, 254_905, 0)
    assert len(made.grid.values) == 254_905


def test_the_grid_covers_britain_and_no_square_holds_nought(made: Air):
    east = sorted(square[0] for square in made.grid.values)
    north = sorted(square[1] for square in made.grid.values)
    # A square is kept by its corner. One lies west of the grid's origin.
    assert (east[0], east[-1], north[0], north[-1]) == (-1_000, 655_000, 5_000, 1_219_000)
    levels = sorted(made.grid.values.values())
    assert (round(levels[0], 2), round(levels[-1], 2)) == (0.51, 35.46)


def test_every_home_of_london_stands_on_a_square_with_a_value(made: Air, found: Spine):
    assert made.squares_read == 1_444
    assert sum(one.units_used for one in made.worked.values()) == 26_369
    assert all(one.units_used == one.units_expected for one in made.worked.values())


# The figures


def test_every_area_has_a_figure_and_is_wholly_covered(made: Air):
    assert len(made.worked) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {one.flags for one in made.worked.values()} == {()}


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(made: Air):
    values = values_of(made)
    assert (values[0], statistics.median(values), values[-1]) == (8.8, 17.4, 32.7)


def test_no_figure_is_outside_what_the_grid_holds_under_london(made: Air):
    """A mean of squares lies between the lowest and the highest square it was taken over."""
    values = values_of(made)
    assert values[0] > 7.9 and values[-1] < 34.7
    # Eleven areas are at 30 or over, and none reaches 40.
    assert sum(value >= 30 for value in values) == 11
    assert sum(value >= 40 for value in values) == 0


def test_the_figure_of_all_of_london_is_what_was_worked_out(real: Inputs, made: Air, found: Spine):
    """The same method with London as one area: the value at every centre, by homes."""
    points = centres.build(real, found)
    london = Homes(area_of=dict.fromkeys(found.area_of, "london"), homes=found.homes)
    whole = grid_at_homes(made.grid.values, points, london)["london"]
    assert whole.value is not None and round(whole.value, 2) == 17.99
    assert (whole.units_used, whole.weight_covered) == (26_369, 1.0)


def test_neighbouring_areas_share_squares_so_many_share_a_figure(made: Air):
    """The grid is coarser than the areas. It is counted, so that nobody is surprised."""
    assert len(set(values_of(made))) == 181


# The evidence


def test_every_figure_rests_on_the_four_files_and_the_method_of_the_grid(made: Air):
    assert len(made.rows) == 1_002
    assert {row.inputs for row in made.rows} == {tuple(sorted([GRID, CENTRES, LOOKUP, HOMES]))}
    assert {row.derivation_id for row in made.rows} == {"grid_at_homes@1"}
    # From the day of the census, which the weights are of, to the end of the grid's year.
    span = Period(start="2021-03-21", end="2024-12-31")
    assert all(row.data_period == span for row in made.rows)
    assert {row.retrieved_on for row in made.rows} == {"2026-09-23"}
    assert Evidence.of("lon-2026-10-02-01", made.files, air_no2.METHODS, made.rows)


def test_the_row_of_the_catalogue_names_the_year_and_every_source(made: Air):
    assert made.metric.vintage == "2024"
    assert made.metric.source_ids == (
        "defra-pcm-background-air",
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    for source_id in made.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_grid_is_told_from_the_other_file_of_its_source(real: Inputs, made: Air):
    """The store holds a file of another pollutant from the same source. It is not opened."""
    kept = [one.publisher_file for one in real.receipts if one.source_id == air_no2.SOURCE]
    assert "mapno22024.csv" in kept and len(kept) > 1
    opened = [one.receipt for one in real.opened if one.receipt.source_id == air_no2.SOURCE]
    assert [one.publisher_file for one in opened] == ["mapno22024.csv"]


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: Air, before: dict[str, tuple[int, int]]
):
    copies = held(real.work)
    assert sorted(Path(name).parts[0] for name in copies) == sorted([GRID, CENTRES, LOOKUP, HOMES])
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
