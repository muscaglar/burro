"""Primary schools close by, worked out from the files their publishers gave.

Every other test of the measure runs on a made-up register. These read the
real one, which a person saved on 2026-09-24, and are skipped where the store
of fetched files is not. The store is named by BURRO_STORE_FOLDER, and each
file is read through its receipt in `data/receipts/`.

They hold the counts of the register, the count of areas with a figure, and
three figures of each of two measures: London's lowest, middle and highest.
None is said of a named area or of a borough, and no school is named. Each was
worked out on 2026-09-24, and no person has checked one.

Nothing is written to the store. A file is copied out of it to be read.
"""

import os
import statistics
from collections import Counter
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import school_primary_nearby, schools_file
from burro_pipeline.derive.school_primary_nearby import COUNTS, KINDS, PHASES, STATUSES, Nearby
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.receipt import How, Period
from burro_pipeline.evidence.row import State
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry
from .schools_support import HELD

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"


def has_a_receipt() -> bool:
    return RECEIPTS.is_dir() and any(
        receipt.source_id == schools_file.SOURCE for receipt in read_receipts(RECEIPTS)
    )


pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and has_a_receipt()),
    reason=f"the register is not here: {FOLDER_VARIABLE} names no folder, or it has no receipt",
)
# The register, the centres, the lookup and the table of homes, by the ids of their receipts.
REGISTER, CENTRES, LOOKUP, HOMES = (
    "f-e2cf7e0c0508",
    "f-00e1d0532798",
    "f-49321b95f212",
    "f-af7b512615ea",
)
DAY = "2026-09-24"


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
def made(real: Inputs, found: Spine) -> Nearby:
    return school_primary_nearby.build(real, found)


@pytest.fixture(scope="module")
def saved(real: Inputs) -> Opened:
    return real.open(schools_file.SOURCE, Use.SCORING, named=school_primary_nearby.is_the_register)


# The file


def test_the_receipt_says_a_person_saved_it_and_for_what(saved: Opened):
    assert saved.file_id == REGISTER
    assert saved.receipt.how is How.BY_HAND
    assert saved.receipt.use is Use.SCORING
    assert (saved.receipt.edition, saved.receipt.data_period.days()) == (DAY, (DAY, DAY))


def test_the_zip_holds_the_establishment_download_of_the_day_of_its_receipt(saved: Opened):
    assert schools_file.member_of(saved) == "edubasealldata20260924.csv"


def test_the_made_up_register_has_the_columns_of_the_real_one(saved: Opened):
    """The tests that run everywhere read a register laid out as this one is."""
    assert schools_file.columns_of(saved) == HELD


def test_every_column_that_is_read_and_every_one_that_is_forbidden_is_in_the_file(
    saved: Opened,
):
    """A forbidden column that the publisher names anew would be on neither list."""
    named = set(schools_file.columns_of(saved))
    assert len(named) == 135
    assert named >= schools_file.MAY_BE_READ | schools_file.FORBIDDEN


def test_the_register_holds_as_many_rows_as_were_counted(made: Nearby):
    found = made.schools
    assert (found.file_id, found.day) == (REGISTER, DAY)
    assert (found.england.rows, found.london.rows) == (52_582, 5_901)
    assert (found.england.open_rows, found.london.open_rows) == (27_204, 3_189)


def test_every_value_of_the_three_columns_is_one_the_measure_knows(saved: Opened):
    """The build stops on a value it has not met. These are all it met."""
    read = (schools_file.STATUS, schools_file.KIND, schools_file.PHASE)
    held: dict[str, set[str]] = {name: set() for name in read}
    for row in schools_file.rows(saved, read):
        for name in read:
            held[name].add(row[name])
    assert held[schools_file.STATUS] == set(STATUSES)
    assert held[schools_file.KIND] == set(KINDS)
    assert held[schools_file.PHASE] == set(PHASES)


# Which schools count


def test_the_schools_that_count_are_as_many_as_were_counted(made: Nearby):
    england, london = made.schools.england, made.schools.london
    assert (england.counted, london.counted) == (16_840, 1_795)
    assert england.counted_by_kind == {
        "Academy converter": 6_230,
        "Academy sponsor led": 1_914,
        "Community school": 4_717,
        "Foundation school": 453,
        "Free schools": 350,
        "Voluntary aided school": 1_851,
        "Voluntary controlled school": 1_325,
    }
    assert london.counted_by_kind == {
        "Academy converter": 432,
        "Academy sponsor led": 136,
        "Community school": 771,
        "Foundation school": 30,
        "Free schools": 79,
        "Voluntary aided school": 342,
        "Voluntary controlled school": 5,
    }
    assert set(england.counted_by_kind) == set(COUNTS)


def test_what_each_column_dropped_in_london_is_what_was_counted(made: Nearby):
    london = made.schools.london
    assert london.dropped_by_status == {"Closed": 2_712}
    assert sum(london.dropped_by_kind.values()) == 943
    assert london.dropped_by_kind == {
        "Academy 16 to 19 sponsor led": 1,
        "Academy 16-19 converter": 3,
        "Academy alternative provision converter": 7,
        "Academy alternative provision sponsor led": 2,
        "Academy special converter": 40,
        "Academy special sponsor led": 6,
        "City technology college": 1,
        "Community special school": 78,
        "Foundation special school": 8,
        "Free schools 16 to 19": 12,
        "Free schools alternative provision": 10,
        "Free schools special": 31,
        "Further education": 30,
        "Higher education institutions": 36,
        "Local authority nursery school": 74,
        "Miscellaneous": 21,
        "Non-maintained special school": 3,
        "Other independent school": 420,
        "Other independent special school": 89,
        "Pupil referral unit": 34,
        "Sixth form centres": 5,
        "Special post 16 institution": 23,
        "Studio schools": 4,
        "University technical college": 5,
    }
    assert london.dropped_by_phase == {"16 plus": 1, "Secondary": 450}
    assert london.rows == 2_712 + 943 + 451 + london.counted


def test_what_each_column_dropped_in_england_adds_up_to_the_rows(made: Nearby):
    england = made.schools.england
    assert england.dropped_by_status == {"Closed": 25_346, "Proposed to open": 32}
    assert sum(england.dropped_by_kind.values()) == 7_168
    assert england.dropped_by_phase == {
        "16 plus": 1,
        "Middle deemed secondary": 86,
        "Secondary": 3_109,
    }
    assert england.rows == 25_378 + 7_168 + 3_196 + england.counted


# Where a school stands


def test_every_school_of_london_that_counts_has_a_point(made: Nearby):
    """11 open schools of London have none. None of them is a school that counts."""
    london = made.schools.london
    assert (london.open_without_a_point, london.without_a_point) == (11, 0)


def test_three_schools_of_england_that_count_have_no_point(made: Nearby):
    england = made.schools.england
    assert (england.open_without_a_point, england.without_a_point) == (721, 3)
    assert len(made.schools.points) == 16_837
    assert len(made.schools.past_the_edge) == 16_837 - 1_795


def test_some_schools_share_a_point_and_each_is_counted(made: Nearby):
    found = made.schools
    assert (found.shared_points, found.on_a_shared_point) == (228, 457)
    of_london = Counter(found.points) - Counter(found.past_the_edge)
    shared = [held for held in of_london.values() if held > 1]
    assert (len(shared), sum(shared)) == (49, 99)


# The edge of London


def test_schools_past_the_edge_of_london_are_within_reach_of_homes_in_it(made: Nearby):
    """The register is of England, so the measure sees them."""
    assert (made.reached, made.reached_past_the_edge) == (1_811, 16)
    # Every school of London that counts is within reach of a home.
    assert made.reached - made.reached_past_the_edge == made.schools.london.counted


# The figures


def test_every_output_area_has_a_count_and_a_nearest_school(made: Nearby, found: Spine):
    assert len(made.within) == len(made.metres) == len(found.area_of) == 26_369
    assert round(max(made.metres.values())) == 2_076
    assert (min(made.within.values()), max(made.within.values())) == (0, 13)
    assert sum(1 for held in made.within.values() if held == 0) == 768


def test_every_area_has_a_figure_and_is_wholly_covered(made: Nearby):
    assert len(made.worked) == 1_002
    assert Counter(one.state for one in made.worked.values()) == {State.PRESENT: 1_002}
    assert {one.weight_covered for one in made.worked.values()} == {1.0}
    assert {one.flags for one in made.worked.values()} == {()}


def test_the_lowest_the_middle_and_the_highest_count_are_what_was_worked_out(made: Nearby):
    values = sorted(one.value for one in made.worked.values() if one.value is not None)
    assert (values[0], statistics.median(values), values[-1]) == (0.3, 3.25, 9.9)
    assert len(set(values)) == 89 and 0.0 not in values


def test_the_lowest_the_middle_and_the_highest_distance_are_what_was_worked_out(made: Nearby):
    values = sorted(one.value for one in made.nearest.values() if one.value is not None)
    assert len(values) == 1_002
    assert (values[0], statistics.median(values), values[-1]) == (130.0, 340.0, 1_000.0)
    # In all but six areas the nearest school is within the reach of the count.
    assert sum(1 for value in values if value <= school_primary_nearby.REACH) == 996


# The evidence


def test_every_figure_rests_on_the_four_files_and_the_method_of_the_measure(made: Nearby):
    assert len(made.rows) == 1_002
    assert {row.inputs for row in made.rows} == {tuple(sorted([REGISTER, CENTRES, LOOKUP, HOMES]))}
    assert {row.derivation_id for row in made.rows} == {"points_within_800m_by_homes@1"}
    # From the day of the census, which the weights are of, to the day of the register.
    span = Period(start="2021-03-21", end=DAY)
    assert all(row.data_period == span for row in made.rows)
    assert {row.retrieved_on for row in made.rows} == {DAY}
    assert all(row.value == made.worked[row.area_id].value for row in made.rows)
    assert Evidence.of("lon-2026-10-09-01", made.files, school_primary_nearby.METHODS, made.rows)


def test_the_row_of_the_catalogue_names_the_day_and_every_source(made: Nearby):
    assert made.metric.vintage == DAY
    assert made.metric.source_ids == (
        "dfe-gias",
        "ons-census-2021-housing-tables",
        "ons-oa-pwc-2021",
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
    )
    for source_id in made.metric.source_ids:
        assert Use.SCORING in registry().get(source_id).uses


def test_the_files_are_read_from_copies_and_the_store_is_as_it_was(
    real: Inputs, made: Nearby, before: dict[str, tuple[int, int]]
):
    copies = sorted(path for path in real.work.rglob("*") if path.is_file())
    assert sorted(path.relative_to(real.work).parts[0] for path in copies) == sorted(
        [REGISTER, CENTRES, LOOKUP, HOMES]
    )
    # The register is read where it is, inside its zip. Nothing of it is unpacked.
    assert not [path for path in copies if path.name.startswith("edubase")]
    assert Path(STORE).resolve() not in real.work.resolve().parents
    # Other steps may add a file to the store while this runs. None that was there has changed.
    after = listing()
    assert {name: after.get(name) for name in before} == before
