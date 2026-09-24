"""The step that drafts the names and the seeds of London's areas.

    python -m burro_pipeline.areas.names_cli --out FOLDER --draft

It is not yet one of the steps of `python -m burro_pipeline`: the parts of the
areas are built side by side, and each joins the one way in when they are put
together. It is laid out as every step is, so that joining it is a line.

What it prints may be read by anyone: one line of `key=value` pairs, the step,
its status and counts. Why it stopped is said in words on standard error.
Neither holds a row, the name of a place or the address of the store. What it
works out names places, so it is written to files in the folder `--out` names
and is never printed.
"""

import argparse
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from burro_pipeline.areas import names_centres, names_draft
from burro_pipeline.areas.seeds import Rules
from burro_pipeline.command import Step, add_step
from burro_pipeline.evidence.cli import in_full, public
from burro_pipeline.evidence.lock import LockError, read_lock, read_receipts
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER, Receipt
from burro_pipeline.evidence.record import FILE_ID_PATTERN
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.fetch.store import FOLDER_VARIABLE, Store, StoreError, store_from_environment
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import RegistryError, load

PROG = "python -m burro_pipeline.areas.names_cli"
NAMES = "names"
FILE_ID = re.compile(FILE_ID_PATTERN)

STEPS = (
    Step(
        NAMES,
        "Draft the names and the seeds of London's areas, for a person to decide",
        f"""\
Run it after the files are fetched. It drafts, and decides nothing: a person
reads every name at the review desk before it ships.

Every name is one that a registered publisher's file holds, at a point or an
outline that the file gives. Nothing is supplied by a model or by whoever runs
this. A name is never changed. It reads nothing about who lives anywhere, and
nothing from OpenStreetMap.

For each file, before it is read: the licence registry is asked whether the
file may be put to the use `gazetteer`. A source it refuses is not read. Its
receipt must be in the folder of receipts. A copy is taken from the store and
held to the hash in the receipt.

A file may have no receipt, as the town centres had none until their list
stated the period of their data. With --draft such a file is read too, and
every name, point and seed that rests on it is marked. Without --draft the step
stops there, as a build would. A draft is for a person's eyes and is never served.

Reads OS Open Names, Boundary-Line, OS Open Roads, the town centres, the
output area boundaries and the lookup of output areas, and the licence
registry. Reaches no publisher. Reaches the store, to copy its files out, and
writes nothing to it. No socket is open while a file is read.

The store is named by the environment, and is never printed. This step takes
a folder, which {FOLDER_VARIABLE} names.

Writes to the folder --out names, which must be outside what git tracks: what
is in it is made from publishers' files.
  candidates.csv     every record of every file that names a place
  places.csv         every place, its points, and what it is put forward as
  seeds.csv          every name put forward as an area, and where its seed stands
  name_records.csv   every record beside every name, and how it writes the name
  hard_look.csv      every reason to look hard at a name
  stations.csv       every railway station, to check a mark against
  ids.csv            the id of each place, to hand to the next draft
  counts.json        every count of the draft
  draft/             the files of names as the review desk reads them

Prints one line of counts.""",
        # Beside the folder of a release, which git ignores, and not inside one.
        ("--out data/releases/names-draft --draft",),
        {
            0: "The files were written",
            2: "A file may not be read, or is not what the step was written to read. "
            "The line names the rule",
        },
    ),
)


class Refused(Exception):
    """The step could not start. Says why, and never what a file holds."""


def _receipts(args: argparse.Namespace, store: Store) -> tuple[Receipt, ...]:
    """The receipts of the build: the folder's, or the copies the store keeps beside its files."""
    if not args.receipts_kept_in_store:
        if not args.receipts.is_dir():
            raise Refused(
                f"the folder of receipts {args.receipts.name} is not there. Name it with "
                "--receipts, or pass --receipts-kept-in-store"
            )
        return read_receipts(args.receipts)
    try:
        kept = store.receipts()
        return tuple(
            sorted(
                (Receipt.model_validate_json(kept[key]) for key in sorted(kept)),
                key=lambda receipt: receipt.file_id,
            )
        )
    except (StoreError, ValueError):
        raise Refused("the store keeps a receipt that cannot be read") from None


def _names(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    out: Path = args.out
    if out.exists() and any(out.iterdir()) and not args.again:
        raise Refused(f"the folder {out.name} holds something already. Name a folder that is new")
    if (args.points is None) != (args.publishers is None):
        raise Refused("--points and --publishers are given together, or not at all")
    if not environment.get(FOLDER_VARIABLE):
        raise Refused(f"no store is named. Set {FOLDER_VARIABLE} to the folder that is the store")
    try:
        store = store_from_environment(environment)
    except StoreError as error:
        raise Refused(str(error)) from None
    with tempfile.TemporaryDirectory(prefix="burro-names-") as scratch:
        inputs = Inputs(
            registry=load(args.registry),
            receipts=_receipts(args, store),
            store=store,
            work=args.work or Path(scratch),
            lock=read_lock(args.lock) if args.lock else None,
        )
        with sockets_refused():
            held = names_draft.read(inputs, draft=args.draft)
            drafted = names_draft.make(
                held,
                Rules(),
                ids=names_draft.read_ids(args.ids) if args.ids else None,
                points=args.points,
                publishers=args.publishers,
            )
    names_draft.write(out, drafted)
    sys.stdout.write(
        public(
            NAMES,
            "ok",
            files=len(held.files),
            records=len(drafted.candidates.records),
            places=len(drafted.candidates.places),
            areas=len(drafted.seeds.areas),
            points=drafted.seeds.points,
            publishers=drafted.seeds.publishers,
            in_range=int(drafted.seeds.in_range),
            marks=len(drafted.looks),
            rows=len(drafted.rows),
            no_receipt=sum(not file.has_receipt for file in held.files.values()),
        )
        + "\n"
    )
    return 0


def build(prog: str = PROG) -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The step, as the command line takes it: the whole, and the step."""
    whole = argparse.ArgumentParser(
        prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = whole.add_subparsers(dest="command", required=True)
    step = {step.name: add_step(commands, step, prog) for step in STEPS}
    names = step[NAMES]
    names.add_argument(
        "--out",
        required=True,
        type=Path,
        metavar="FOLDER",
        help="the folder the files are written to. It is new, or empty",
    )
    names.add_argument(
        "--draft",
        action="store_true",
        help="read the one file that has no receipt, and mark all that rests on it",
    )
    names.add_argument(
        "--again",
        action="store_true",
        help="write over the files of an earlier draft in the folder --out names",
    )
    names.add_argument(
        "--ids",
        type=Path,
        metavar="FILE",
        help="the ids.csv of an earlier draft, so that every place keeps its id",
    )
    names.add_argument(
        "--points",
        type=int,
        metavar="N",
        help="the points an area needs. Without it, the design's 6 is moved until the count "
        "of areas lands in range",
    )
    names.add_argument(
        "--publishers",
        type=int,
        metavar="N",
        help="the publishers an area's points must come from. Given with --points",
    )
    names.add_argument(
        "--receipts",
        type=Path,
        default=Path(RECEIPTS_FOLDER),
        help=f"the folder of receipts (default: {RECEIPTS_FOLDER})",
    )
    names.add_argument(
        "--receipts-kept-in-store",
        action="store_true",
        help="read the copies of the receipts that the store keeps beside its files, for a "
        "working copy that holds no folder of receipts",
    )
    names.add_argument(
        "--lock",
        type=Path,
        metavar="FILE",
        help="the lock of the build. Without it the build is a development build, which is "
        "never served",
    )
    names.add_argument(
        "--registry",
        type=Path,
        help="the licence registry, a file or a folder (default: this repository's)",
    )
    names.add_argument(
        "--work",
        type=Path,
        metavar="FOLDER",
        help="where the copies of the files are put while they are read, and left. Without it "
        "they are put in a folder that is removed when the step ends",
    )
    return whole, step


def parsed(argv: Sequence[str] | None = None, prog: str = PROG) -> argparse.Namespace:
    """The arguments of the step. Stops with the step's usage if they are not ones it takes."""
    words = list(sys.argv[1:] if argv is None else argv)
    return build(prog)[0].parse_args(words if words[:1] == [NAMES] else [NAMES, *words])


def main(argv: Sequence[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    args = parsed(argv)
    try:
        return _names(args, os.environ if environment is None else environment)
    except LockError as error:
        named = {"file_id": error.subject} if FILE_ID.fullmatch(error.subject) else {}
        sys.stdout.write(public(NAMES, "refused", **{error.rule: 1}, **named) + "\n")
        sys.stderr.write(f"error: {in_full(error)}\n")
        if error.subject == names_centres.SOURCE and not args.draft:
            sys.stderr.write(
                "A draft may read this file though it has no receipt: pass --draft, and all "
                "that rests on the file is marked.\n"
            )
    except (Refused, RegistryError, ValueError) as error:
        sys.stdout.write(public(NAMES, "unreadable") + "\n")
        sys.stderr.write(f"error: {error}\n")
    except OSError as error:
        sys.stdout.write(public(NAMES, "unreadable") + "\n")
        sys.stderr.write(f"error: cannot read or write a file: {error.strerror}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
