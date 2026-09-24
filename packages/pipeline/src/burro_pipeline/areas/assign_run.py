"""Draft the areas: read the seeds and the ground, give every output area, write the files.

    python -m burro_pipeline.areas.assign_run --seeds FILE --receipts FOLDER --out FOLDER

It is run by hand while the areas are drafted, and is not yet a step of
`python -m burro_pipeline`.

**The seeds** are a table with a header: `seed_id`, `easting`, `northing` and
`weight`, and `name` where the seed stands for one. A point is on the National
Grid, in metres. Where the table has a column `area_id`, that is the id the
area will have, and if not its `seed_id` is. The `seed_id` is taken for the id
of the publisher's record the seed was read from, which is what joins a seed
to the settlement a road names. A weight is how much stands behind the name: of
two seeds too close, the heavier stands. Any other column is left unread. No
seed is made up here, and none is moved.

**The store** is named by the environment and is never printed. The folder
`--out` names must be outside what git tracks: what is written there is made
from publishers' files.

What it prints may be read by anyone: counts, and nothing a file holds. Why it
stopped is said in words on standard error.
"""

import argparse
import csv
import math
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from burro_pipeline.areas import assign_files, assign_outline, assign_write
from burro_pipeline.areas.assign import Draft, Rules, draft
from burro_pipeline.areas.assign_files import Ground, Reading, SeedPoint
from burro_pipeline.areas.assign_outline import Outlines
from burro_pipeline.evidence.lock import LockError, read_receipts
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.fetch.store import StoreError, store_from_environment
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import RegistryError, find, load

SEED_ID, EASTING, NORTHING, WEIGHT, NAME = "seed_id", "easting", "northing", "weight", "name"
AREA_ID = "area_id"
NEEDED = (SEED_ID, EASTING, NORTHING, WEIGHT)


class Refused(Exception):
    """The run could not start. Says why, and never what a file holds."""


def read_seeds(path: Path) -> list[SeedPoint]:
    """The seeds of a file, each a point with a weight. It stops at a row that is not one."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as text:
            rows = csv.DictReader(text)
            if not set(NEEDED) <= set(rows.fieldnames or ()):
                raise Refused(f"the file of seeds lacks one of: {', '.join(NEEDED)}")
            named = AREA_ID if AREA_ID in (rows.fieldnames or ()) else SEED_ID
            found = [
                SeedPoint(
                    seed_id=row[named],
                    point=(float(row[EASTING]), float(row[NORTHING])),
                    weight=float(row[WEIGHT]),
                    name=row.get(NAME) or "",
                    record=row[SEED_ID],
                )
                for row in rows
            ]
    except (OSError, UnicodeDecodeError, csv.Error, ValueError, TypeError):
        raise Refused("the file of seeds could not be read as a table of points") from None
    if not found or len({seed.seed_id for seed in found}) != len(found):
        raise Refused("the file of seeds holds no seed, or holds one twice")
    if not all(
        seed.seed_id and all(math.isfinite(part) for part in (*seed.point, seed.weight))
        for seed in found
    ):
        raise Refused("a seed has no id, or a number that is no number")
    return found


def drafted(
    inputs: Inputs,
    seeds: Sequence[SeedPoint],
    rules: Rules | None = None,
    reading: Reading | None = None,
) -> tuple[Draft, Ground, Outlines]:
    """The draft, the ground it was made on and the outline of each area."""
    ground = assign_files.read_ground(inputs, seeds, reading)
    found = draft(ground.cells, ground.seeds, ground.roads, ground.beside, rules)
    return found, ground, assign_outline.outlines_of(found.drawn, ground.outlines)


def tracked(folder: Path) -> bool:
    """Whether a folder is inside this repository and outside the folders git ignores for data."""
    try:
        root = find().parents[1]
        inside = folder.resolve().relative_to(root.resolve())
    except (RegistryError, ValueError):
        return False
    return inside.parts[:2] not in (("data", "raw"), ("data", "releases"))


def parser() -> argparse.ArgumentParser:
    given = argparse.ArgumentParser(
        prog="python -m burro_pipeline.areas.assign_run",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    given.add_argument("--seeds", required=True, type=Path, metavar="FILE")
    given.add_argument("--out", required=True, type=Path, metavar="FOLDER")
    given.add_argument("--receipts", type=Path, default=Path(RECEIPTS_FOLDER), metavar="FOLDER")
    given.add_argument("--registry", type=Path, metavar="FOLDER")
    given.add_argument("--work", type=Path, metavar="FOLDER")
    return given


def _run(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    if tracked(args.out):
        raise Refused("the folder to write to is one git tracks. Name one outside the repository")
    if not args.receipts.is_dir():
        raise Refused("the folder of receipts is not there")
    seeds = read_seeds(args.seeds)
    try:
        store = store_from_environment(environment)
    except StoreError as error:
        raise Refused(str(error)) from None
    with tempfile.TemporaryDirectory(prefix="burro-areas-") as scratch:
        inputs = Inputs(
            registry=load(args.registry or find()),
            receipts=read_receipts(args.receipts),
            store=store,
            work=args.work or Path(scratch),
        )
        with sockets_refused():
            found, ground, outlines = drafted(inputs, seeds)
        assign_write.write(assign_write.files_of(found, ground, outlines), args.out)
    counted = {"output_areas": len(found.given), "areas": len(found.drawn)} | found.counts()
    line = " ".join(f"{key}={value}" for key, value in counted.items())
    sys.stdout.write(f"step=areas-draft status=ok {line}\n")
    return 0


def main(argv: Sequence[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return _run(args, os.environ if environment is None else environment)
    except LockError as error:
        sys.stderr.write(f"error: {error}\n")
    except (Refused, RegistryError, ValueError) as error:
        sys.stderr.write(f"error: {error}\n")
    except OSError as error:
        sys.stderr.write(f"error: cannot read or write a file: {error.strerror}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
