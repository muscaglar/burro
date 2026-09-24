"""The step of the command line that cells owns.

    python -m burro_pipeline cells --release-id ID --out FOLDER

What it prints may be read by anyone: one line of `key=value` pairs, the step,
its status and counts. Why it stopped is said in words on standard error. Neither
holds a row, the name of an area or the address of the store. What it works out
names areas, so it is written to files in the folder `--out` names and is never
printed.
"""

import argparse
import csv
import io
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import ValidationError

from burro_pipeline.cells import land, outline, spine
from burro_pipeline.cells.land import Land
from burro_pipeline.cells.outline import Outline
from burro_pipeline.cells.spine import Spine
from burro_pipeline.command import NOT_IGNORED, PROG, Step, add_step, may_be_written
from burro_pipeline.evidence.cli import in_full, public
from burro_pipeline.evidence.lock import LockError, read_lock, read_receipts
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER, Receipt
from burro_pipeline.evidence.record import FILE_ID_PATTERN, in_words
from burro_pipeline.evidence.row import FULLY_COVERED, EvidenceRow, State
from burro_pipeline.evidence.served import BOUNDARY, NAME
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.fetch.store import FOLDER_VARIABLE, StoreError, store_from_environment
from burro_pipeline.inputs import Inputs, period_of, retrieved_on
from burro_pipeline.registry import RegistryError, load
from burro_pipeline.release.write import canonical_json

FILE_ID = re.compile(FILE_ID_PATTERN)
# What is made here is made from fetched files, so it is never of a synthetic release.
RELEASE_ID = re.compile(r"lon-\d{4}-\d{2}-\d{2}-\d{2}")
AREAS, GEOMETRY, CELLS, LAND, EVIDENCE = (
    "areas.json",
    "geometry.json",
    "cells.csv",
    "land.csv",
    "evidence.json",
)

STEPS = (
    Step(
        "cells",
        "Make the geography of a build: London's output areas, the areas, outlines and land",
        f"""\
Run it after the files are fetched, and before any figure is worked out. Every
figure of a build is worked out on what it makes.

London is the rows of the statistics office's lookup whose local authority
code starts E09. An area is an MSOA, under the statistics office's own label
for it: its borough and a number. A home is a household at the census of 2021.
An outline is the generalised outlines of the area's output areas joined. The
land of an LSOA is what its generalised outline encloses.

It counts what the files hold and holds the count to no number. It stops when
an output area is listed twice, has no count of homes or has no outline, when a
unit is part of two larger ones, and when the outlines do not fit together.

For each file, before it is read: the licence registry is asked whether the
file may be put to this use. Its receipt must be in the folder of receipts. A
copy is taken from the store and held to the hash in the receipt. With --lock,
the lock of the build must name the file. Without it the build is a
development build, which is never served.

Reads the lookup, the census table of accommodation type, the output area
boundaries and the LSOA boundaries, each through its receipt, and the licence
registry. Reaches no publisher. Reaches the store, to copy its files out, and
writes nothing to it. No socket is open while a file is read.

The store is named by the environment, and is never printed. This step takes
a folder, which {FOLDER_VARIABLE} names.

Writes five files to the folder --out names. What is in them is made from
publishers' files, so --out and --work are refused inside the repository, but
for data/releases/ and scratch/, which git ignores.
  {AREAS}     each area: its id, label, borough, a point inside it, its
                 neighbours, its homes and its land in hectares
  {GEOMETRY}  each area's outline, as the contract lays out geometry.json
  {CELLS}     each output area: its LSOA, MSOA, borough and area, and its homes
  {LAND}      each LSOA's land in hectares
  {EVIDENCE}  the evidence behind each area's label and outline

Prints one line of counts.""",
        # Beside the folder of the release, and not inside it: a release folder holds the
        # files of the release and nothing else.
        ("--release-id lon-2026-10-02-01 --out data/releases/cells-lon-2026-10-02-01",),
        {
            0: "The files were written",
            2: "A file may not be read, or is not what the step was written to read. "
            "The line names the rule",
        },
    ),
)


class Refused(Exception):
    """The step could not start. Says why, and never what a file holds."""


def _row(
    area_id: str, key: str, method: str, files: Sequence[Receipt], used: int, of: int
) -> EvidenceRow:
    covered = used / of if of else 0.0
    return EvidenceRow(
        fact_id=f"{area_id}/area/{key}",
        derivation_id=method,
        inputs=tuple(sorted(receipt.file_id for receipt in files)),
        data_period=period_of(files),
        retrieved_on=retrieved_on(files),
        units_used=used,
        units_expected=of,
        weight_covered=covered,
        state=State.PRESENT if covered >= FULLY_COVERED else State.PARTIAL,
    )


def evidence_of(
    release_id: str, inputs: Inputs, found: Spine, outlines: Mapping[str, Outline]
) -> Evidence:
    """The evidence behind each area's label and its outline."""
    by_source = {opened.receipt.source_id: opened.receipt for opened in inputs.opened}
    lookup, boundaries = by_source[spine.LOOKUP], by_source[outline.BOUNDARIES]
    rows: list[EvidenceRow] = []
    for area in found.areas:
        drawn = outlines[area.area_id]
        of = drawn.units_expected
        rows.append(_row(area.area_id, NAME, spine.LABELLED.derivation_id, [lookup], of, of))
        rows.append(
            _row(
                area.area_id,
                BOUNDARY,
                outline.JOINED.derivation_id,
                [lookup, boundaries],
                drawn.units_used,
                of,
            )
        )
    return Evidence.of(release_id, [lookup, boundaries], (spine.LABELLED, outline.JOINED), rows)


def areas_of(found: Spine, outlines: Mapping[str, Outline], measured: Land) -> dict[str, object]:
    """Each area as the step writes it down."""
    homes = dict.fromkeys((area.area_id for area in found.areas), 0)
    for cell in found.cells:
        homes[found.area_of[cell.oa]] += cell.homes
    return {
        "areas": [
            {
                "area_id": area.area_id,
                "msoa21cd": area.code,
                "name": area.name,
                "slug": area.slug,
                "borough": area.borough,
                "lad22cd": area.borough_code,
                "centroid": list(outlines[area.area_id].centre),
                "neighbours": list(outlines[area.area_id].neighbours),
                "homes": homes[area.area_id],
                "hectares": measured.of_area[area.area_id],
            }
            for area in found.areas
        ]
    }


def _table(names: Sequence[str], rows: Sequence[Sequence[object]]) -> bytes:
    text = io.StringIO(newline="")
    table = csv.writer(text, lineterminator="\n")
    table.writerow(names)
    table.writerows(rows)
    return text.getvalue().encode()


def _cells(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    out: Path = args.out
    if not RELEASE_ID.fullmatch(args.release_id):
        raise Refused("--release-id is not the id of a release of London, as lon-2026-10-02-01")
    for name, folder in (("--out", out), ("--work", args.work)):
        # The step is run at the top of the repository, which is where the receipts are read.
        if folder is not None and not may_be_written(folder, Path()):
            raise Refused(f"{name} {NOT_IGNORED}")
    if out.exists() and any(out.iterdir()):
        raise Refused(f"the folder {out.name} holds something already. Name a folder that is new")
    if not environment.get(FOLDER_VARIABLE):
        raise Refused(f"no store is named. Set {FOLDER_VARIABLE} to the folder that is the store")
    try:
        store = store_from_environment(environment)
    except StoreError as error:
        raise Refused(str(error)) from None
    with tempfile.TemporaryDirectory(prefix="burro-cells-") as scratch:
        inputs = Inputs(
            registry=load(args.registry),
            receipts=read_receipts(args.receipts),
            store=store,
            work=args.work or Path(scratch),
            lock=read_lock(args.lock) if args.lock else None,
        )
        with sockets_refused():
            found = spine.build(inputs)
            outlines = outline.build(inputs, found)
            measured = land.build(inputs, found)
    try:
        evidence = evidence_of(args.release_id, inputs, found, outlines)
    except ValidationError as error:
        raise Refused(f"the evidence could not be written: {in_words(error)}") from None
    area_of = found.area_of
    written = {
        AREAS: canonical_json(areas_of(found, outlines, measured)),
        GEOMETRY: canonical_json(outline.feature_collection(outlines)),
        CELLS: _table(
            ("oa21cd", "lsoa21cd", "msoa21cd", "lad22cd", "area_id", "homes"),
            [
                (cell.oa, cell.lsoa, cell.msoa, cell.borough, area_of[cell.oa], cell.homes)
                for cell in found.cells
            ],
        ),
        LAND: _table(
            ("lsoa21cd", "hectares"),
            [(lsoa, f"{measured.of_lsoa[lsoa]:.4f}") for lsoa in found.lsoas],
        ),
        EVIDENCE: evidence.canonical(),
    }
    out.mkdir(parents=True, exist_ok=True)
    for name, content in written.items():
        (out / name).write_bytes(content)
    counts = found.counts()
    print(
        public(
            "cells",
            "ok",
            release=args.release_id,
            areas=counts["areas"],
            output_areas=counts["output_areas"],
            lsoas=counts["lsoas"],
            msoas=counts["msoas"],
            boroughs=counts["boroughs"],
            files=len(inputs.opened),
            rows=len(evidence.rows),
            development=int(inputs.development),
            evidence_sha256=evidence.digest(),
        )
    )
    return 0


def build(prog: str = PROG) -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The step cells owns, as the command line takes it: the whole, and the step."""
    whole = argparse.ArgumentParser(
        prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = whole.add_subparsers(dest="command", required=True)
    step = {step.name: add_step(commands, step, prog) for step in STEPS}
    cells = step["cells"]
    cells.add_argument(
        "--release-id",
        required=True,
        metavar="ID",
        help="the release the geography is for, as lon-2026-10-02-01",
    )
    cells.add_argument(
        "--out",
        required=True,
        type=Path,
        metavar="FOLDER",
        help="the folder the five files are written to. It is new, or empty",
    )
    cells.add_argument(
        "--receipts",
        type=Path,
        default=Path(RECEIPTS_FOLDER),
        help=f"the folder of receipts (default: {RECEIPTS_FOLDER})",
    )
    cells.add_argument(
        "--lock",
        type=Path,
        metavar="FILE",
        help="the lock of the build. Without it the build is a development build, which is "
        "never served",
    )
    cells.add_argument(
        "--registry",
        type=Path,
        help="the licence registry, a file or a folder (default: this repository's)",
    )
    cells.add_argument(
        "--work",
        type=Path,
        metavar="FOLDER",
        help="where the copies of the files are put while they are read, and left. Without it "
        "they are put in a folder that is removed when the step ends",
    )
    return whole, step


def parsed(argv: Sequence[str] | None = None, prog: str = PROG) -> argparse.Namespace:
    """The arguments of the step. Stops with the step's usage if they are not ones it takes."""
    return build(prog)[0].parse_args(argv)


def main(argv: Sequence[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    args = parsed(argv)
    try:
        return _cells(args, os.environ if environment is None else environment)
    except LockError as error:
        named = {"file_id": error.subject} if FILE_ID.fullmatch(error.subject) else {}
        print(public("cells", "refused", **{error.rule: 1}, **named))
        print(f"error: {in_full(error)}", file=sys.stderr)
    except (Refused, RegistryError) as error:
        print(public("cells", "unreadable"))
        print(f"error: {error}", file=sys.stderr)
    except OSError as error:
        print(public("cells", "unreadable"))
        print(f"error: cannot read or write a file: {error.strerror}", file=sys.stderr)
    return 2
