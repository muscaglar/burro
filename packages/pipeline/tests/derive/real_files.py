"""What the tests that read the real council tax tables share.

Nothing here is a figure. It opens the files of the first build through their
receipts, and reads rows of the publisher's tables that no step of the build
reads: the row for London as a whole, which the sum of the areas is held to,
and the LSOAs of every MSOA of England, which the reading of a dash is held to.
"""

import os
from collections.abc import Sequence
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.derive.rounded_counts import TOO_SMALL, Count
from burro_pipeline.evidence.lock import read_receipts
from burro_pipeline.fetch.store import FOLDER_VARIABLE, FolderStore
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

from ..cells.support import REPOSITORY, registry

STORE = os.environ.get(FOLDER_VARIABLE, "")
RECEIPTS = REPOSITORY / "data" / "receipts"
SKIPPED = pytest.mark.skipif(
    not (STORE and Path(STORE).is_dir() and RECEIPTS.is_dir()),
    reason=f"the store of fetched files is not here: {FOLDER_VARIABLE} names no folder",
)
# The publisher's row for London as a whole, by its kind and its code.
REGION, LONDON = "REGL", "E12000007"
# The gate of the pipeline design for a total: within 0.5 in 100 of the publisher's own.
GATE = 0.005


def real_inputs(work: Path) -> Inputs:
    return Inputs(registry(), read_receipts(RECEIPTS), FolderStore(Path(STORE)), work)


def lsoas_of_every_msoa(real: Inputs) -> dict[str, list[str]]:
    """The LSOAs of every MSOA of England, from the lookup. The spine holds London's alone."""
    lookup = real.open(spine.LOOKUP, Use.SCORING, edition=spine.LOOKUP_EDITION)
    pairs: set[tuple[str, str]] = set()
    with lookup.text() as text:
        for row in lookup.rows(text, (spine.LSOA, spine.MSOA)):
            pairs.add((row[spine.MSOA], row[spine.LSOA]))
    found: dict[str, list[str]] = {}
    for msoa, lsoa in sorted(pairs):
        found.setdefault(msoa, []).append(lsoa)
    return found


def row_of_london(
    opened: Opened, member: str, columns: Sequence[str], band: str | None = "All"
) -> dict[str, Count]:
    """The publisher's own counts for London as a whole, for the columns that are named."""
    read = ("geography", "ecode", *(("band",) if band else ()), *columns)
    with opened.text(member) as text:
        rows = [
            row
            for row in opened.rows(text, read)
            if (row["geography"], row["ecode"]) == (REGION, LONDON)
            and (band is None or row["band"] == band)
        ]
    (row,) = rows
    return {name: None if row[name] == TOO_SMALL else int(row[name]) for name in columns}


def within_the_gate(added: int, published: Count) -> bool:
    """Whether what the areas add up to is within 0.5 in 100 of the publisher's own total."""
    return published is not None and abs(added - published) <= GATE * published
