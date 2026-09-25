"""The nearest food shop, worked out from the files their publishers gave.

Every other test of the measure runs on made-up places. These read the part
of the real file of places that the list `m2-culture` takes, and the real
centres of output areas, and are skipped where the store of fetched files is
not. The store is named by BURRO_STORE_FOLDER, and each file is read through
its receipt in `data/receipts/`.

They hold the table of kinds to the part, the counts of the records, the
count of areas with a figure, and three figures: London's lowest, middle and
highest. None is said of a named area or of a borough, and no name of a
business is read. Each was worked out on 2026-09-24, from the part as it was
fetched that day.

Nothing is written to the store. A file is copied out of it to be read.
"""

import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import land, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import (
    culture_check,
    culture_file,
    culture_reach,
    grocery_walk,
    homes_density,
)
from burro_pipeline.derive.food_shop_kinds import IS, IS_NOT, PARENTS, READ_UNDER
from burro_pipeline.derive.grocery_walk import Nearest
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.evidence.receipt import How, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.inputs import Inputs

from .real_files import SKIPPED, STORE, real_inputs

pytestmark = SKIPPED
# The part of the file of places, the centres, the lookup and the table of homes, by the ids
# of their receipts.
PLACES, CENTRES, LOOKUP, HOMES = (
    "f-ee34c537f281",
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
def made(real: Inputs, found: Spine) -> Nearest:
    return grocery_walk.build(real, found)


# The file


def test_the_part_is_the_one_that_was_fetched_and_its_receipt_says_so(real: Inputs):
    receipt = culture_file.opened_of(real).receipt
    assert (receipt.file_id, receipt.how) == (PLACES, How.FETCHED)
    assert (receipt.edition, receipt.data_period) == ("2026-09-23.0", Period(as_at="2026-09-23"))
    assert receipt.taken is not None
    assert receipt.taken.box == (-0.53, 51.28, 0.33, 51.71)
    assert "names" not in receipt.taken.columns and "brand" not in receipt.taken.columns


# The table, held to the part


def test_every_category_of_the_branch_that_the_part_holds_is_on_the_table(made: Nearest):
    """36 categories: 11 are a kind, 24 are left out by name, and one is the parent."""
    counted, left_out = set(made.held.counted_as), set(made.held.left_out_as)
    assert (len(counted), len(left_out)) == (11, 25)
    assert counted == set(IS) - {"supermarket"}
    assert left_out == set(IS_NOT) | PARENTS
    assert not counted & left_out and PARENTS < READ_UNDER


def test_the_part_holds_11749_records_of_a_food_shop(made: Nearest):
    held = made.held
    assert held.rows == 683_409
    assert held.by_kind == {"convenience_store": 5_623, "grocer": 6_126}
    assert len(held.records) == sum(held.counted_as.values()) == 11_749
    assert held.counted_as == {
        "asian_grocery_store": 9,
        "convenience_store": 5_623,
        "ethical_grocery_store": 70,
        "grocery_store": 5_366,
        "indian_grocery_store": 3,
        "international_grocery_store": 40,
        "korean_grocery_store": 454,
        "mexican_grocery_store": 2,
        "organic_grocery_store": 165,
        "russian_grocery_store": 1,
        "superstore": 16,
    }


def test_what_is_left_out_is_counted_by_the_reason_and_by_the_category(made: Nearest):
    """No record of a food shop says that it has closed for good, and each has a point."""
    assert made.held.left_out == {
        "no_category": 51_966,
        "not_a_food_shop": 614_230,
        "not_a_kind": 4_410,
        "parent_alone": 1_054,
    }
    left_out = made.held.left_out_as
    assert sum(left_out.values()) == 4_410 + 1_054
    assert left_out["food_and_beverage_store"] == 1_054
    assert (left_out["butcher_shop"], left_out["produce_store"], left_out["fishmonger"]) == (
        948,
        298,
        141,
    )
    assert (left_out["liquor_store"], left_out["health_food_store"]) == (911, 632)


def test_which_of_the_publishers_sources_gave_each_record_is_kept(made: Nearest):
    assert made.held.by_dataset == {
        "AllThePlaces": 1_133,
        "Foursquare": 1_834,
        "Microsoft": 1_718,
        "Overture": 11_749,
        "meta": 7_064,
    }


# The figure


def test_every_one_of_the_1002_areas_has_a_figure(made: Nearest, found: Spine):
    assert len(made.worked) == len(found.areas) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}


def test_the_lowest_the_middle_and_the_highest_of_london(made: Nearest):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert (values[0], statistics.median(values), values[-1]) == (70.0, 210.0, 800.0)
    tenths = statistics.quantiles(values, n=10)
    assert (tenths[0], tenths[-1]) == (120.0, 380.0)
    assert len(set(values)) == 60


def test_the_distance_of_every_output_area_is_known(made: Nearest, found: Spine):
    """The box reaches 2,000 metres beyond London's homes, and the furthest shop is nearer."""
    assert len(found.cells) == 26_369
    assert (len(made.found_of_oa), len(made.of_oa), made.beyond_the_edge) == (26_369, 26_369, ())
    known = sorted(made.of_oa.values())
    assert (round(known[0]), round(statistics.median(known)), round(known[-1])) == (0, 204, 2_304)
    assert sum(1 for far in known if far > 800) == 306


def test_the_figure_stands_mostly_in_the_order_of_how_built_up_an_area_is(
    real: Inputs, made: Nearest, found: Spine
):
    """A food shop is nearer where homes stand closer together, and nearer the middle."""
    density = homes_density.build(real, found, land.build(real, found)).worked
    ground = culture_reach.ground_of(real, found)
    held = culture_check.held_against(
        "grocery_walk",
        {area: one.value for area, one in made.worked.items()},
        {area: one.value for area, one in density.items()},
        dict(culture_check.distance_from_the_middle(found, ground.at)),
        {area: one.value for area, one in density.items()},
    )
    assert held.areas == 1_002
    assert held.with_density is not None and held.with_distance is not None
    assert (round(held.with_density, 2), round(held.with_distance, 2)) == (-0.75, 0.67)


# The evidence, and the row of the catalogue


def test_a_row_names_the_four_files_and_holds_the_figure(made: Nearest):
    ids = tuple(sorted((PLACES, CENTRES, LOOKUP, HOMES)))
    assert tuple(sorted(receipt.file_id for receipt in made.files)) == ids
    assert all(row.inputs == ids for row in made.rows)
    assert [row.value for row in made.rows] == [
        made.worked[row.fact_id.split("/")[0]].value for row in made.rows
    ]
    evidence = Evidence(
        release_id="lon-2026-09-24-01",
        methods=grocery_walk.METHODS,
        receipts=made.files,
        rows=made.rows,
    )
    assert len(evidence.rows) == 1_002


def test_the_row_of_the_catalogue_is_cores_and_says_which_release_was_read(made: Nearest):
    assert says_what_core_says(made.metric)
    assert (made.metric.unit, made.metric.vintage) == ("m", "2026-09-23")
    assert "release 2026-09-23.0 of Overture Maps Places" in made.metric.definition
    assert made.metric.source_ids == (
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "overture-places",
    )


def test_nothing_was_written_to_the_store(made: Nearest, before: dict[str, tuple[int, int]]):
    assert made.worked and listing() == before
