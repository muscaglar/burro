"""What the tests that read the real food register share.

Nothing here is a figure. It opens the 33 files of the register through their
receipts, as a build does, and names the editions that the first fetch kept,
so that a test holds what it held whatever has arrived since.

Contains public sector information licensed under the Open Government Licence
v3.0. Source: Food Standards Agency.
"""

import os
from pathlib import Path

import pytest
from burro_pipeline.assemble.cli import of_the_list
from burro_pipeline.derive import food_register
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch.sources import load_list
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
SKIPPED = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)
# The lists whose files a build of the measures takes.
LISTS = ("m1", "m2-places")
# The day each file stated when it was first fetched. 24 of the 33 stated the newest day.
NEWEST = "2026-09-16"
EARLIER = {
    "fsa-hounslow": "2026-09-09",
    "fsa-havering": "2026-09-10",
    "fsa-haringey": "2026-09-11",
    "fsa-islington": "2026-09-12",
    "fsa-greenwich": "2026-09-13",
    "fsa-barnet": "2026-09-15",
    "fsa-croydon": "2026-09-15",
    "fsa-hackney": "2026-09-15",
    "fsa-hammersmith-and-fulham": "2026-09-15",
}


def real_inputs(work: Path) -> Inputs:
    """The files of the two lists, with the register as the first fetch kept it."""
    listed = [file for name in LISTS for file in load_list(name).files]
    first_fetched = {
        file.item: f"extract of {EARLIER.get(file.item, NEWEST)}"
        for file in listed
        if file.source_id == food_register.SOURCE
    }
    receipts, _, _ = of_the_list(read_receipts(RECEIPTS), listed, first_fetched)
    return Inputs(registry(), receipts, FolderStore(Path(STORE)), work)


def listing() -> dict[str, tuple[int, int]]:
    """Every file of the store, with its size and when it was last written."""
    return {
        path.relative_to(STORE).as_posix(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(Path(STORE).rglob("*"))
        if path.is_file()
    }
