"""What the tests of the whole draft share: one made-up store that every part can read.

Nothing here is real. The town is the one `names_support.py` draws: Quillhaven
and Tallowgate, in squares of 500 metres in the North Sea. Two files are added
to its store, which the parts that draw borders read and the names do not: the
centre of each output area, and the outlines an area is drawn with. Both are
made from the same squares.
"""

import atexit
import csv
import io
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path

from burro_pipeline.areas import assign, draft_run
from burro_pipeline.areas.assign_files import Reading
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import CENTRES_COLUMNS, receipt_of, registry
from . import names_support as town

CENTRES, OUTLINES = "ons-oa-pwc-2021", "ons-output-areas-2021"
# A town of thirty-one squares: every area may be small, and the roads are one small piece.
SETTINGS = draft_run.Settings(
    of_seeds=town.RULES,
    of_areas=assign.Rules(smallest=2),
    of_reading=Reading(margin=500.0, least_water=1.0, least_piece=3),
)


def centres_csv() -> bytes:
    """The centre of each output area: the middle of its square."""
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, CENTRES_COLUMNS, lineterminator="\n")
    table.writeheader()
    for number, square in enumerate((*town.LONDON, town.BEYOND), start=1):
        east, north = town.middle(square)
        table.writerow(
            {
                "X": f"{east:.4f}",
                "Y": f"{north:.4f}",
                "FID": number,
                "OA21CD": town.oa(square),
                "GlobalID": f"{{made-up-{number}}}",
                "GlobalID_2": f"{{made-up-{number}-2}}",
            }
        )
    return b"\xef\xbb\xbf" + text.getvalue().encode()


def outlines_to_draw() -> bytes:
    """The outlines an area is drawn with: the same squares, under the other edition's name."""
    return town.contents()["outlines"].replace(b"BFC_V8", b"BGC_V2")


def more() -> dict[str, tuple[str, bytes, str]]:
    """The two files added to the town's store: the publisher's name, the bytes, the edition."""
    return {
        CENTRES: ("Output_Areas_2021_PWC_V4_made_up.csv", centres_csv(), "V4"),
        OUTLINES: ("Output_Areas_2021_EW_BGC_V2_made_up.gpkg", outlines_to_draw(), "BGC V2"),
    }


def receipts_folder(folder: Path, receipts: list[Receipt]) -> Path:
    """The receipts written to a folder, as a working copy keeps them."""
    for receipt in receipts:
        path = folder / receipt.source_id / f"{receipt.file_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(receipt.model_dump_json(), encoding="utf-8")
    return folder


def given(folder: Path, held_by: Registry | None = None) -> town.Given:
    """Every file of the whole draft in one store, each with its receipt but the town centres."""
    found = town.given(folder, held_by=held_by)
    store = FolderStore(found.store)
    receipts = list(found.receipts)
    for source_id, (name, content, edition) in more().items():
        handed = folder / "given" / "more" / name
        handed.parent.mkdir(parents=True, exist_ok=True)
        handed.write_bytes(content)
        store.put(source_id, name, handed)
        receipts.append(receipt_of(source_id, Use.GAZETTEER, name, content, edition))
    inputs = Inputs(held_by or registry(), receipts, store, folder / "work")
    return town.Given(inputs, found.store, receipts)


@dataclass(frozen=True)
class Made:
    """One whole draft of the made-up town, as a run leaves it."""

    out: Path
    store: Path
    counted: Mapping[str, object]

    def rows(self, name: str) -> list[dict[str, str]]:
        with (self.out / name).open(encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def columns(self, name: str) -> tuple[str, ...]:
        with (self.out / name).open(encoding="utf-8", newline="") as file:
            return tuple(next(csv.reader(file)))


def make(folder: Path, settings: draft_run.Settings = SETTINGS) -> Made:
    """The whole draft of the made-up town, made in a folder."""
    found = given(folder)
    counted = draft_run.make(found.inputs, folder / "out", settings=settings)
    return Made(folder / "out", found.store, counted)


@cache
def made() -> Made:
    """The whole draft, made once for every test that only reads it."""
    folder = Path(tempfile.mkdtemp(prefix="burro-made-up-draft-"))
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    return make(folder)


@cache
def made_with_every_name_read() -> Made:
    """The whole draft with every name put to a person, made once. Two names of the
    town stand by the rule on one official publisher, and the desk is handed no line of
    either: what is said beside a name is tested on the draft in which each is an item."""
    folder = Path(tempfile.mkdtemp(prefix="burro-made-up-draft-read-"))
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    return make(folder, replace(SETTINGS, read_every_name=True))
