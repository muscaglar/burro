"""A made-up lookup between the areas of two censuses, laid out as the publisher lays out its own.

Nothing here is real. The areas are those of the made-up town of the tests of
cells: Quillhaven 001 and 002 and Tallowgate 001, and one district outside
London. Every code is shaped like the statistics office's and is none it has
given out.

The file has the publisher's own layout, as it was read on 2026-09-24: nine
columns under their own names, a mark at the start of the file, and lines that
end with a line feed. Every name of an area and of an authority is a canary:
no step reads one.

    area of 2011   mark   area of 2021
    E02999001       U     E02999001   Quillhaven 001, as it was
    E02999002       U     E02999002   Quillhaven 002, as it was
    E02999803       M     E02999003   Tallowgate 001, made by joining two areas of 2011
    E02999804       M     E02999003
    E02999901       U     E02999901   outside London, and passed over
    W02999001       U     W02999001   in Wales, and passed over
"""

import csv
import io
from collections.abc import Sequence
from pathlib import Path

from burro_pipeline.derive import areas_of_2011
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, receipt_of

# The publisher's name for the download, with what says it is made up.
NAME = (
    "MSOA_(2011)_to_MSOA_(2021)_to_Local_Authority_District_(2022)_Exact_Fit_Lookup_for_EW_"
    "(V2)_made_up.csv"
)
# The nine columns of the file, in its order.
COLUMNS = (
    "MSOA11CD",
    "MSOA11NM",
    "CHNGIND",
    "MSOA21CD",
    "MSOA21NM",
    "LAD22CD",
    "LAD22NM",
    "LAD22NMW",
    "ObjectId",
)
QUILLHAVEN, TALLOWGATE, OUTSIDE, WALES = "E09000901", "E09000902", "E07000901", "W06999001"
# One row: the area of 2011, the mark, the area of 2021 and the authority.
Row = tuple[str, str, str, str]
AS_THEY_WERE: tuple[Row, ...] = (
    ("E02999001", "U", "E02999001", QUILLHAVEN),
    ("E02999002", "U", "E02999002", QUILLHAVEN),
)
JOINED: tuple[Row, ...] = (
    ("E02999803", "M", "E02999003", TALLOWGATE),
    ("E02999804", "M", "E02999003", TALLOWGATE),
)
ELSEWHERE: tuple[Row, ...] = (
    ("E02999901", "U", "E02999901", OUTSIDE),
    ("W02999001", "U", "W02999001", WALES),
)
TOWN: tuple[Row, ...] = (*AS_THEY_WERE, *JOINED, *ELSEWHERE)
# The town, had Quillhaven been one area in 2011 that was split into its two of 2021.
SPLIT: tuple[Row, ...] = (
    ("E02999801", "S", "E02999001", QUILLHAVEN),
    ("E02999801", "S", "E02999002", QUILLHAVEN),
    *JOINED,
    *ELSEWHERE,
)


def lookup_csv(rows: Sequence[Row] = TOWN, columns: Sequence[str] = COLUMNS) -> bytes:
    """The lookup, as the portal writes this one: a mark at the start, and lines that end LF."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, columns, extrasaction="ignore", lineterminator="\n")
    table.writeheader()
    for number, (of_2011, mark, of_2021, authority) in enumerate(rows, start=1):
        table.writerow(
            {
                "MSOA11CD": of_2011,
                "MSOA11NM": CANARY,
                "CHNGIND": mark,
                "MSOA21CD": of_2021,
                "MSOA21NM": CANARY,
                "LAD22CD": authority,
                "LAD22NM": CANARY,
                "LAD22NMW": CANARY,
                "ObjectId": number,
            }
        )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def with_the_lookup(given: Inputs, folder: Path, content: bytes | None = None) -> Inputs:
    """The files of a made-up build, and the lookup between the censuses beside them.

    The lookup is fetched for `cells`, as its list states, and is read for
    `scoring`, which is what the step puts it to.
    """
    content = lookup_csv() if content is None else content
    path = folder / "given" / NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    given.store.put(areas_of_2011.SOURCE, NAME, path)
    receipt = receipt_of(
        areas_of_2011.SOURCE, Use.CELLS, NAME, content, areas_of_2011.EDITION
    ).model_copy(update={"data_period": Period(as_at="2022-12")})
    return Inputs(given.registry, [*given.receipts, receipt], given.store, given.work)
