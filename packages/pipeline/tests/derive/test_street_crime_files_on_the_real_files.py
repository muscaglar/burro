"""The crime files of the zip a person saved on 2026-09-24, read through its receipt.

Every other test of the reader runs on a made-up zip. These read the real one,
and are skipped where the store of fetched files is not. The store is named by
BURRO_STORE_FOLDER, and the zip is read through its receipt in `data/receipts/`.

The zip holds outcomes and stop and search beside the crime files. These hold
the counts of its names, which are read from the list the zip keeps of itself,
and that nothing but a crime file is opened. They hold no row, no figure and
no name of a place.

Nothing is written to the store. The zip is copied out of it to be read.
"""

import os
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.derive.street_crime_files import (
    EDITION,
    ENDS,
    FORCES,
    HELD,
    MAY_BE_READ,
    SOURCE,
    columns_of,
    crime_files,
    rows,
)
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.evidence.receipt import How
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"


def has_a_receipt() -> bool:
    return RECEIPTS.is_dir() and any(
        receipt.source_id == SOURCE for receipt in read_receipts(RECEIPTS)
    )


pytestmark = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and has_a_receipt()),
    reason=f"the zip is not here: {FOLDER_VARIABLE} names no folder, or it has no receipt",
)

# What the zip holds, by how a name ends. Counted from the names alone.
CRIME, OUTCOMES, STOPPED = 72, 72, 71
MONTHS, FIRST, LAST = 36, "2023-08", "2026-07"


@pytest.fixture(scope="module")
def saved(tmp_path_factory: pytest.TempPathFactory) -> Opened:
    work = tmp_path_factory.mktemp("street-crime")
    real = Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)
    return real.open(SOURCE, Use.SCORING, edition=EDITION)


def test_the_receipt_says_a_person_saved_it_and_for_what(saved: Opened):
    assert saved.receipt.how is How.BY_HAND
    assert saved.receipt.use is Use.SCORING
    assert saved.receipt.data_period.days() == (f"{FIRST}-01", f"{LAST}-31")


def test_the_zip_holds_three_kinds_of_file_and_the_reader_names_one(saved: Opened):
    with zipfile.ZipFile(saved.path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
    ends = Counter(
        next(
            (
                kind
                for kind in ("-outcomes.csv", "-stop-and-search.csv", ENDS)
                if name.endswith(kind)
            ),
            "",
        )
        for name in names
    )
    assert ends == {ENDS: CRIME, "-outcomes.csv": OUTCOMES, "-stop-and-search.csv": STOPPED}
    found = crime_files(saved)
    assert len(found) == CRIME
    assert {file.name for file in found} == {name for name in names if name.endswith(ENDS)}


def test_there_is_a_crime_file_for_each_force_and_each_month_the_list_states(saved: Opened):
    found = crime_files(saved)
    months = sorted({file.month for file in found})
    assert (len(months), months[0], months[-1]) == (MONTHS, FIRST, LAST)
    assert Counter(file.force for file in found) == dict.fromkeys(FORCES, MONTHS)


def test_every_crime_file_names_the_columns_the_reader_knows(saved: Opened):
    for file in crime_files(saved):
        assert columns_of(saved, file.name) == HELD, (file.month, file.force)


def test_a_month_is_read_and_nothing_but_a_crime_file_is_opened(
    saved: Opened, monkeypatch: pytest.MonkeyPatch
):
    seen: list[str] = []
    really_open = zipfile.ZipFile.open

    def watched(self: zipfile.ZipFile, name: Any, *args: Any, **kwargs: Any) -> Any:
        seen.append(name.filename if isinstance(name, zipfile.ZipInfo) else str(name))
        return really_open(self, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "open", watched)
    # The smaller force, so that the test is quick: its last month.
    (file,) = [file for file in crime_files(saved) if (file.month, file.force) == (LAST, FORCES[0])]
    read = list(rows(saved, file.name, sorted(MAY_BE_READ)))
    assert read
    assert {row["Month"] for row in read} == {LAST}
    assert all(set(row) == MAY_BE_READ for row in read)
    assert seen == [file.name]
