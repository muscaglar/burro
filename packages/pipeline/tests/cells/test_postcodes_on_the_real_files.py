"""The postcode directory a person saved on 2026-09-24, read through its receipt.

Every other test of the lookup runs on a made-up directory. These read the real
one, and are skipped where the store of fetched files is not. The store is
named by BURRO_STORE_FOLDER, and the zip is read through its receipt in
`data/receipts/`.

They hold counts over all of London, so that a directory that changes is
noticed. Each was counted on 2026-09-24. They hold no postcode, no point and
no figure of an area.

Nothing is written to the store. The zip is copied out of it to be read.
"""

import os
import zipfile
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.cells import postcodes, spine
from burro_pipeline.cells.postcodes import Lookup
from burro_pipeline.cells.spine import Spine
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.receipt import How
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

from .postcodes_support import DIRECTORY, NEVER_LAST
from .support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
EDITION = "August 2026"


def has_a_receipt() -> bool:
    return RECEIPTS.is_dir() and any(
        receipt.source_id == postcodes.SOURCE for receipt in read_receipts(RECEIPTS)
    )


pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and has_a_receipt()),
    reason=f"the directory is not here: {FOLDER_VARIABLE} names no folder, or it has no receipt",
)


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Inputs:
    work = tmp_path_factory.mktemp("postcodes")
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


@pytest.fixture(scope="module")
def saved(real: Inputs) -> Opened:
    return real.open(postcodes.SOURCE, postcodes.USE, edition=EDITION)


@pytest.fixture(scope="module")
def opened_by_the_reader(saved: Opened) -> tuple[Lookup, list[str]]:
    """The lookup, and the name of every file of the zip that was opened to make it."""
    seen: list[str] = []
    really_open = zipfile.ZipFile.open

    def watched(self: zipfile.ZipFile, name: Any, *args: Any, **kwargs: Any) -> Any:
        seen.append(name.filename if isinstance(name, zipfile.ZipInfo) else str(name))
        return really_open(self, name, *args, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(zipfile.ZipFile, "open", watched)
        found = postcodes.read(saved)
    return found, seen


@pytest.fixture(scope="module")
def lookup(opened_by_the_reader: tuple[Lookup, list[str]]) -> Lookup:
    return opened_by_the_reader[0]


@pytest.fixture(scope="module")
def ground(real: Inputs) -> Spine:
    return spine.build(real)


def test_the_receipt_says_a_person_saved_it_and_of_which_month(saved: Opened):
    assert saved.receipt.how is How.BY_HAND
    assert saved.receipt.use is Use.CELLS
    assert saved.receipt.data_period.days() == ("2026-08-01", "2026-08-31")
    assert postcodes.credits_of(saved.receipt)[0].endswith(" 2026")


def test_the_zip_holds_the_file_of_124_areas_and_every_one_names_the_same_columns(saved: Opened):
    files = postcodes.area_files(saved)
    assert len(files) == 124
    assert postcodes.NORTHERN_IRELAND in files
    for area, name in files.items():
        if area != postcodes.NORTHERN_IRELAND:
            assert postcodes.columns_of(saved, name) == postcodes.HELD, area


def test_the_file_of_northern_ireland_was_never_opened(
    saved: Opened, opened_by_the_reader: tuple[Lookup, list[str]]
):
    found, seen = opened_by_the_reader
    files = postcodes.area_files(saved)
    assert files[postcodes.NORTHERN_IRELAND] not in seen
    assert sorted(seen) == sorted(
        name for area, name in files.items() if area != postcodes.NORTHERN_IRELAND
    )
    assert (found.counts.files, found.counts.opened) == (124, 123)
    # No file of another area holds a line of Northern Ireland.
    assert found.counts.dropped_for_northern_ireland == 0
    assert postcodes.NORTHERN_IRELAND not in found.counts.areas


def test_london_is_as_many_postcodes_as_were_counted(lookup: Lookup):
    assert lookup.counts.rows == 2_665_796
    assert (lookup.counts.london, lookup.counts.in_use, lookup.counts.ended) == (
        332_885,
        180_965,
        151_920,
    )
    assert len(lookup) == 332_885


def test_the_rows_of_london_are_in_22_postcode_areas(lookup: Lookup):
    assert len(lookup.counts.areas) == 22
    assert sum(lookup.counts.areas.values()) == lookup.counts.london
    # Three of them hold under 1,000 rows of London each: they lie mostly outside it.
    assert sorted(lookup.counts.areas.values())[:3] == [3, 23, 573]


def test_nearly_every_postcode_in_use_has_a_point_at_one_of_its_own_addresses(lookup: Lookup):
    assert lookup.counts.quality_in_use == {1: 180_447, 3: 5, 5: 385, 6: 128}
    assert lookup.counts.quality_ended == {
        1: 95_863,
        3: 327,
        4: 34,
        5: 8_824,
        6: 12_644,
        8: 34_228,
    }


def test_every_postcode_in_use_but_one_is_in_an_area_of_the_build(lookup: Lookup, ground: Spine):
    assert ground.counts()["areas"] == 1_002
    assert lookup.not_of(ground) == {
        # The point of one postcode stands in a London borough of today, and in an output
        # area of 2021 that is outside London.
        "in_no_area": 1,
        "in_use_in_no_area": 1,
        "in_another_borough": 42,
        "in_use_in_another_borough": 7,
        "output_areas_in_another_lsoa_or_msoa": 0,
        "output_areas_with_none_in_use": 15,
    }


def test_every_postcode_that_has_ended_is_in_an_area_of_the_build(lookup: Lookup, ground: Spine):
    rows = lookup._rows.values()  # pyright: ignore[reportPrivateUsage]
    ended = [kept for kept in rows if kept[4] is not None]
    assert len(ended) == 151_920
    assert all(kept[2] in ground.area_of for kept in ended)
    # Seven in ten have a point that a distance is measured to.
    measured_to = sum(1 for kept in ended if kept[3] in postcodes.GOOD_FOR_A_DISTANCE)
    assert (measured_to, len(ended) - measured_to) == (105_048, 46_872)


def test_every_borough_has_postcodes_in_use_and_they_add_up(lookup: Lookup, ground: Spine):
    found = lookup.in_use_by_borough()
    assert set(found) == {cell.borough for cell in ground.cells}
    assert len(found) == 33
    assert sum(found.values()) == lookup.counts.in_use
    assert (min(found.values()), max(found.values())) == (1_561, 13_063)


def test_no_postcode_of_the_directory_can_be_one_of_the_made_up_ones(saved: Opened, lookup: Lookup):
    # The made-up postcodes of the tests begin with a letter no postcode area begins with,
    # and end in letters no postcode of London ends in.
    assert not [area for area in postcodes.area_files(saved) if area.startswith("Q")]
    keys = lookup._rows  # pyright: ignore[reportPrivateUsage]
    assert not [1 for key in keys if set(key[-2:]) & set(NEVER_LAST)]
    for row in DIRECTORY:
        assert lookup.place(row.postcode) is None


def test_what_the_lookup_says_of_itself_is_counts(lookup: Lookup):
    assert repr(lookup) == "Lookup(london=332885, in_use=180965, ended=151920)"
