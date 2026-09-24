"""Fine particles, worked out from the files their publishers gave.

Every other test of the measure runs on a made-up grid. These read the real
one, and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the count of rows read, the count of areas with a figure, and three
figures: London's lowest, middle and highest. None is said of a named area.
Each was worked out on 2026-09-24. Whatever else is held is held to what the
file itself gives, and to no number written here.

© Crown 2026 copyright Defra via uk-air.defra.gov.uk, licenced under the Open
Government Licence (OGL). Source: Office for National Statistics licensed under
the Open Government Licence v.3.0. Contains OS data © Crown copyright and
database right [year].

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import air_pm25
from burro_pipeline.derive.air_pm25 import Air
from burro_pipeline.derive.methods import cell_of
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs

from ..cells.support import held
from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The grid, the centres, the lookup and the table of homes, by the ids of their receipts.
GRID, CENTRES, LOOKUP, HOMES = (
    "f-cb95c290ef00",
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
    return real_inputs(tmp_path_factory.mktemp("real"))


@pytest.fixture(scope="module")
def found(real: Inputs) -> Spine:
    return spine.build(real)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Air:
    return air_pm25.build(real, found)


def values_of(made: Air) -> list[float]:
    return sorted(one.value for one in made.worked.values() if one.value is not None)


def test_the_grid_holds_as_many_rows_as_were_counted_and_one_has_no_value(made: Air):
    assert made.grid.file_id == GRID
    assert (made.grid.year, made.grid.rows, made.grid.without_a_value) == (2024, 254_905, 1)
    assert 0 not in made.grid.values.values()


def test_every_area_has_a_figure_and_is_wholly_covered(made: Air):
    assert len(made.worked) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {one.flags for one in made.worked.values()} == {()}
    assert all(one.units_used == one.units_expected for one in made.worked.values())


def test_the_lowest_the_middle_and_the_highest_figure_are_what_was_worked_out(made: Air):
    values = values_of(made)
    assert (values[0], statistics.median(values), values[-1]) == (7.2, 8.9, 11.0)


def test_no_figure_is_outside_what_the_grid_holds_under_london(
    real: Inputs, made: Air, found: Spine
):
    """A mean of squares lies between the lowest and the highest square it was taken over."""
    points = centres.build(real, found)
    under = [made.grid.values[cell_of(*points[oa])] for oa in found.area_of]
    values = values_of(made)
    assert min(under) - 0.05 <= values[0] and values[-1] <= max(under) + 0.05


def test_the_areas_differ_little_as_the_product_says_beside_the_figure(made: Air):
    """The highest area is not twice the lowest, and many areas share a figure."""
    values = values_of(made)
    assert values[-1] < 2 * values[0]
    assert len(set(values)) < len(values) / 10


def test_every_figure_rests_on_the_four_files_and_the_method_of_the_grid(made: Air):
    assert len(made.rows) == 1_002
    assert [row.fact_id for row in made.rows] == [
        f"{area}/feature/air_pm25" for area in sorted(made.worked)
    ]
    assert {row.inputs for row in made.rows} == {tuple(sorted([GRID, CENTRES, LOOKUP, HOMES]))}
    assert {row.derivation_id for row in made.rows} == {"grid_at_homes@1"}
    assert all(row.value == made.worked[row.area_id].value for row in made.rows)
    # From the day of the census, which the weights are of, to the end of the grid's year.
    span = Period(start="2021-03-21", end="2024-12-31")
    assert all(row.data_period == span for row in made.rows)
    assert {row.retrieved_on for row in made.rows} == {"2026-09-23"}
    assert Evidence.of("lon-2026-10-02-01", made.files, air_pm25.METHODS, made.rows)


def test_what_the_row_of_the_catalogue_would_say_names_the_year_and_every_source(made: Air):
    assert made.proposed.vintage == "2024"
    assert made.proposed.source_ids == (
        "defra-pcm-background-air",
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )


def test_the_grid_of_nitrogen_dioxide_is_not_opened(real: Inputs, made: Air):
    kept = [one.publisher_file for one in real.receipts if one.source_id == air_pm25.SOURCE]
    assert "mapno22024.csv" in kept and "mappm252024g.csv" in kept
    opened = [one.receipt for one in real.opened if one.receipt.source_id == air_pm25.SOURCE]
    assert [one.publisher_file for one in opened] == ["mappm252024g.csv"]


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: Air, before: dict[str, tuple[int, int]]
):
    copies = held(real.work)
    assert sorted(Path(name).parts[0] for name in copies) == sorted([GRID, CENTRES, LOOKUP, HOMES])
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
