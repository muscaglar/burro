"""The nearest pharmacy, worked out from the files their publishers gave.

Every other test of the measure runs on a made-up list. These read the real
list, the real postcode directory and the real centres of output areas, and
are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and each file is read through its receipt in
`data/receipts/`.

They hold the counts of the list, what became of the contractors that count,
the count of areas with a figure, and three figures: London's lowest, middle
and highest. None is said of a named area or of a borough, and no postcode
and no name is held. Each was worked out on 2026-09-24, from the list of the
first quarter of 2026-27 as it was fetched that day.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import centres, postcodes, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import nearest_by_postcode, pharmacy_walk
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.derive.nearest_by_postcode import Placing
from burro_pipeline.derive.pharmacy_walk import Listed, Walk
from burro_pipeline.evidence.receipt import How, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs

from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The list, by the id of its receipt.
LIST = "f-ffed833c1913"
QUARTER = Period(start="2026-04-01", end="2026-06-30")


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
def listed(real: Inputs) -> Listed:
    opened = real.open(pharmacy_walk.SOURCE, pharmacy_walk.USE, named=pharmacy_walk.is_the_list)
    return pharmacy_walk.read(opened)


@pytest.fixture(scope="module")
def made(real: Inputs, found: Spine) -> Walk:
    return pharmacy_walk.build(real, found)


# The list


def test_the_list_is_the_one_that_was_fetched_and_its_receipt_says_so(real: Inputs):
    receipt = real.open(
        pharmacy_walk.SOURCE, pharmacy_walk.USE, named=pharmacy_walk.is_the_list
    ).receipt
    assert (receipt.file_id, receipt.publisher_file) == (LIST, "consol_pharmacy_list_202606q1.csv")
    assert (receipt.how, receipt.edition) == (How.FETCHED, "2026-27 Quarter 1")
    assert receipt.data_period == QUARTER


def test_every_type_of_contract_in_the_list_is_one_the_page_names(listed: Listed):
    """The step was written from the publisher's page. The file writes the three types it names."""
    assert listed.rows == 10_507
    assert listed.by_type == {"community": 10_385, "dac": 112, "lps": 10}
    assert set(listed.by_type) == set(pharmacy_walk.COUNTS)


def test_an_appliance_contractor_is_left_out_and_every_other_contractor_counts(listed: Listed):
    assert len(listed.postcodes) == 10_395 == listed.rows - listed.by_type["dac"]


def test_what_is_printed_of_the_list_is_counts(listed: Listed):
    assert repr(listed) == "Listed(rows=10507, counted=10395)"


# The figure


def test_1723_pharmacies_are_placed_in_london_and_the_rest_are_placed_nowhere(made: Walk):
    """The directory holds London's rows alone, so a pharmacy elsewhere is placed nowhere."""
    assert made.placing == Placing(
        listed=10_395,
        placed=1_723,
        at_an_ended_postcode=4,
        not_a_postcode=0,
        not_of_london=8_672,
        too_coarse=0,
    )


def test_every_one_of_the_1002_areas_has_a_figure(made: Walk, found: Spine):
    assert len(made.worked) == len(found.areas) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {
        State.PRESENT: 951,
        State.PARTIAL: 51,
    }


def test_the_lowest_the_middle_and_the_highest_of_london(made: Walk):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert (values[0], statistics.median(values), values[-1]) == (100.0, 400.0, 2_000.0)
    assert all(value % nearest_by_postcode.NEAREST == 0 for value in values)
    assert len(set(values)) == 14


def test_the_distance_of_26139_output_areas_is_known(made: Walk, found: Spine):
    assert len(found.cells) == 26_369
    assert (len(made.distances.of_oa), len(made.distances.near_the_edge)) == (26_139, 230)
    known = sorted(made.distances.of_oa.values())
    assert (round(known[0]), round(statistics.median(known)), round(known[-1])) == (0, 345, 3_254)


# The edge of London


def test_the_edge_leaves_homes_out_of_the_figure_and_no_area_without_one(made: Walk, found: Spine):
    """A pharmacy outside London is placed nowhere, so a home near the edge has no distance."""
    assert sum(found.homes[oa] for oa in made.distances.near_the_edge) == 29_716
    assert not [area for area, one in made.worked.items() if one.value is None]
    touched = {found.area_of[oa] for oa in made.distances.near_the_edge}
    partial = {area for area, one in made.worked.items() if one.state is State.PARTIAL}
    assert partial <= touched


# The evidence, and the row of the catalogue


def test_a_row_names_the_files_behind_it_and_holds_the_figure(made: Walk):
    by_source = {receipt.source_id: receipt.file_id for receipt in made.files}
    assert set(by_source) == {
        pharmacy_walk.SOURCE,
        postcodes.SOURCE,
        centres.CENTRES,
        spine.LOOKUP,
        spine.HOMES,
    }
    assert by_source[pharmacy_walk.SOURCE] == LIST
    ids = tuple(sorted(by_source.values()))
    assert all(row.inputs == ids for row in made.rows)
    assert [row.value for row in made.rows] == [
        made.worked[row.fact_id.split("/")[0]].value for row in made.rows
    ]
    evidence = Evidence(
        release_id="lon-2026-09-24-01",
        methods=pharmacy_walk.METHODS,
        receipts=made.files,
        rows=made.rows,
    )
    assert len(evidence.rows) == 1_002


def test_the_row_of_the_catalogue_is_cores_and_says_the_quarter_and_no_day(made: Walk):
    """No page and no column says what day the list is as at, so the words say the quarter."""
    assert says_what_core_says(made.metric)
    assert (made.metric.unit, made.metric.vintage) == ("m", "2026-04-01 to 2026-06-30")
    assert "for the period from 2026-04-01 to 2026-06-30" in made.metric.definition
    assert "as at" not in made.metric.definition


def test_nothing_was_written_to_the_store(made: Walk, before: dict[str, tuple[int, int]]):
    assert made.worked and listing() == before
