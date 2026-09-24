"""The command line of the review desk.

    python -m desk serve    [--reviewer r1] [--port 8765] [--data FOLDER] [--keep FOLDER]
    python -m desk fill     --from FOLDER --data FOLDER, or --made-up
    python -m desk compile  [--data FOLDER] [--gazetteer FOLDER]
    python -m desk publish  [--data FOLDER] --to FOLDER

`serve` starts the desk and prints the address to open. It opens nothing itself.
With no `--data` it serves `data/raw/desk` if that holds items. If not, it serves
the made-up city from `data/raw/desk-synthetic`, and fills that folder first if it
is empty. Both are under `data/raw/`, which git ignores. So a second copy of every
line is kept in a folder outside the repository, and real data is not served
without one. `--keep` names the folder. With no `--keep` it is the folder
`burro-desk-decisions` in the home folder of whoever starts the desk, where that
is there: the desk makes no folder for the copy by itself.

`fill` makes the queues from a draft folder. `compile` makes a build's files from
the lines of decisions. `publish` makes the copy of the decisions that may be
committed: the queues that may be published, the lines that stand, the day and
never the hour. `make desk`, `make desk-fill`, `make desk-compile` and
`make desk-publish` run these.

Exit codes: 0, or 2 where something was refused and nothing was written.

Standard library only. See docs/design/desk.md, section 7.
"""

import argparse
import importlib
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final, Protocol, cast

from desk import compile as make
from desk import publish as copy
from desk import records, server

ROOT: Final = Path(__file__).resolve().parents[2]
HERE: Final = Path(__file__).resolve().parent
PAGE, QUESTIONS = HERE / "page", HERE / "questions.json"
REAL, MADE_UP = ROOT / "data" / "raw" / "desk", ROOT / "data" / "raw" / "desk-synthetic"
FIXTURE: Final = ROOT / "data" / "fixtures" / "synthetic"
# How a folder that may hold the made-up city is named. Nothing of London is ever looked
# for in such a folder, so nothing made up can be taken for London.
NAMED_MADE_UP: Final = "-synthetic"
# The folder of the home folder where the second copy of every decision is kept, unless
# another is named. The guide says how to make it.
KEPT_IN_HOME: Final = server.KEPT_IN_HOME
OK, REFUSED = 0, 2
# What a person flagged, in the words the last lines of `compile` say it in.
LOOK: Final = {
    make.WRONG: "called wrong",
    make.NOT_KNOWN: "not known",
    make.MARKED: "marked for a second reviewer",
    make.SKIPPED: "skipped with a note or a mark",
}


class Fill(Protocol):
    """The step that fills the queues, which is a part of its own: `desk.fill`."""

    def run(self, source: Path, data: Path, *, synthetic: bool) -> int: ...


def _fill() -> Fill:
    # Asked for only when a queue is filled, so that the desk starts without it.
    return cast(Fill, importlib.import_module("desk.fill"))


def _near(path: Path) -> str:
    """A path as a person would type it from where they stand."""
    here = Path.cwd().resolve()
    whole = path.resolve()
    return str(whole.relative_to(here)) if whole.is_relative_to(here) else str(whole)


def _default() -> Path:
    return REAL if (REAL / "items").is_dir() else MADE_UP


def _refuse(words: str) -> int:
    sys.stderr.write(f"{words.rstrip('.')}.\n")
    return REFUSED


def kept_in_home() -> Path | None:
    """The folder of the home folder where the second copy is kept, where it is there.
    The desk makes none: a folder it made could be taken for the copy of an earlier
    sitting, and would hold nothing of it."""
    try:
        folder = Path.home() / KEPT_IN_HOME
    except RuntimeError:
        return None
    return folder if folder.is_dir() else None


def _open(folder: Path, reviewer: str, keep: Path | None) -> server.Desk:
    """Read what the desk serves. Real data with no folder named for the second copy is
    served with the copy in the folder of the home folder, and not served without it."""
    try:
        return server.open_desk(folder, PAGE, QUESTIONS, reviewer, keep=keep, outside=ROOT)
    except server.NeedsKeep:
        found = kept_in_home()
        if found is None:
            raise
    return server.open_desk(folder, PAGE, QUESTIONS, reviewer, keep=found, outside=ROOT)


def serve(reviewer: str, port: int, data: Path | None, keep: Path | None = None) -> int:
    folder = data or _default()
    if data is None and folder == MADE_UP and not (folder / "items").is_dir():
        print("Filling the made-up city, for the first time.")
        status = _fill().run(FIXTURE, folder, synthetic=True)
        if status != OK:
            return status
    try:
        desk = _open(folder, reviewer, keep)
        running = server.serve(desk, port)
    except records.Unfit as unfit:
        return _refuse(f"The desk did not start. {unfit}")
    except OSError:
        return _refuse(
            f"The desk did not start. Port {port} is taken, or may not be used. "
            f'Stop the other desk, or choose another: make desk ARGS="--port {port + 1}"'
        )
    stands = server.state(desk)
    broken, mended = stands["broken_lines"], stands["mended_lines"]
    print(f"The review desk, as {reviewer}.")
    print(server.BANNER[desk.synthetic])
    print(
        f"Decisions are kept in {_near(folder)}: in {records.PUBLIC_TREE}, "
        f"and in {records.PRIVATE_TREE} those that are never published."
    )
    if broken:
        print(f"Lines of decisions that cannot be read: {broken}. They are kept, and not applied.")
    if mended:
        print(
            f"Lines that a fault cut short, and that were then written again whole: {mended}. "
            "Nothing was lost."
        )
    if desk.keep is not None:
        lacked = f" It lacked {desk.brought_up}, which were written." if desk.brought_up else ""
        print(f"A second copy of every decision is kept in {_near(desk.keep)}.{lacked}")
    print(f"Open http://{server.LOOPBACK}:{running.server_address[1]}/")
    print("Ctrl-C stops it. Every decision is on disk already.", flush=True)
    try:
        running.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        running.server_close()
    return OK


def fill(source: Path | None, data: Path | None, made_up: bool) -> int:
    if made_up:
        folder = data or MADE_UP
        if not folder.resolve().name.endswith(NAMED_MADE_UP):
            return _refuse(
                "Not filled. The made-up city is filled only into a folder whose name ends "
                f"{NAMED_MADE_UP}, such as {MADE_UP.relative_to(ROOT)}"
            )
        return _fill().run(source or FIXTURE, folder, synthetic=True)
    if source is None or data is None:
        return _refuse(
            "Say where the draft is and where the queues go: --from FOLDER --data FOLDER"
        )
    return _fill().run(source, data, synthetic=False)


def compile_(data: Path | None, gazetteer: Path | None) -> int:
    folder = data or _default()
    try:
        made = make.run(folder, gazetteer, QUESTIONS)
    except (records.Unfit, FileNotFoundError) as unfit:
        return _refuse(f"Nothing was written. {unfit}")
    except make.Refused as refused:
        sys.stderr.write("Nothing was written. These checks failed:\n")
        for problem in refused.problems:
            sys.stderr.write(f"  {problem.rstrip('.')}.\n")
        return REFUSED
    built = made.built
    print(f"Made from {'the made-up city' if made.desk.synthetic else 'real data for London'}.")
    print(f"{'queue':<10} {'applied':>8} {'not applied':>12} {'flagged':>8}")
    for queue in made.desk.queues:
        counts = (built.applied[queue], built.set_aside[queue], built.flagged[queue])
        print(f"{queue:<10} {counts[0]:>8} {counts[1]:>12} {counts[2]:>8}")
    looked = [f"{built.look[why]} {words}" for why, words in LOOK.items() if built.look[why]]
    print(f"To look at: {', '.join(looked) if looked else 'nothing'}.")
    if looked:
        listed = _near(make.where(folder, built, make.TO_LOOK_AT))
        print(f"They are listed in {listed}, each with its note.")
    if built.broken:
        print(f"Lines that cannot be read: {built.broken}. They are kept, and not applied.")
    if built.by_rule:
        each = ", ".join(f"{count} in {queue}" for queue, count in built.by_rule.items())
        print(f"Settled by a rule the founder adopted: {each}.")
    if built.waits:
        one = built.waits == 1
        print(
            f"{built.waits} {'name was' if one else 'names were'} turned down while "
            f"{'its area has' if one else 'their areas have'} ground. "
            f"{'It is' if one else 'They are'} set aside until the draft is made again."
        )
        print(
            f"Make the draft again from {_near(folder / 'out' / 'names.csv')}, fill the "
            "queues again, and only then look at borders."
        )
    if made.gazetteer is not None:
        print(f"Wrote {len(built.gazetteer)} files to {_near(made.gazetteer)}")
        print(f"What was not applied is in {make.NOT_APPLIED}, each with its reason.")
    print(f"Wrote {len(built.out) - len(built.private)} files to {_near(folder / 'out')}")
    if built.private:
        kept = _near(folder / "out" / make.PRIVATE)
        print(f"Wrote {len(built.private)} files to {kept}. They are never published.")
    return OK


def publish(data: Path | None, to: Path | None) -> int:
    if to is None:
        return _refuse("Say where the copy goes: --to FOLDER, such as gazetteer/london")
    try:
        found = copy.run(data or _default(), to, QUESTIONS)
    except (records.Unfit, FileNotFoundError, copy.Refused) as refused:
        return _refuse(f"Nothing was written. {refused}")
    lines = f"{found.lines} {'line' if found.lines == 1 else 'lines'}"
    queues = f"{len(found.queues)} {'queue' if len(found.queues) == 1 else 'queues'}"
    print(f"Wrote {lines} of {queues} to {_near(to / copy.TREE)}.")
    print("Each line says the day it was written, and not the hour.")
    if found.notes:
        print("These notes are in it. Read each one before you commit:")
        for note in found.notes:
            print(f"  {note}")
    else:
        print("No note is in it.")
    return OK


def parser() -> argparse.ArgumentParser:
    held = argparse.ArgumentParser(prog="python -m desk", description="The review desk.")
    steps = held.add_subparsers(dest="step", required=True)
    one = steps.add_parser("serve", help="start the desk, and print the address to open")
    one.add_argument("--reviewer", default="r1", help="r1 is the founder, r2 the second reviewer")
    one.add_argument("--port", type=int, default=server.PORT)
    one.add_argument("--data", type=Path, help="the folder of items, layers and decisions")
    one.add_argument(
        "--keep",
        type=Path,
        help="a folder outside the repository for a second copy of each line. With none, "
        f"the folder {KEPT_IN_HOME} in your home folder, where it is there",
    )
    two = steps.add_parser("fill", help="fill the queues from a draft folder")
    two.add_argument("--from", dest="source", type=Path, help="the draft folder")
    two.add_argument("--data", type=Path, help="the folder the queues are written to")
    two.add_argument("--made-up", action="store_true", help="fill the made-up city")
    three = steps.add_parser("compile", help="make a build's files from the lines of decisions")
    three.add_argument("--data", type=Path, help="the folder of items and decisions")
    three.add_argument("--gazetteer", type=Path, help="the folder the curated files go to")
    four = steps.add_parser("publish", help="make the copy of the decisions that may be published")
    four.add_argument("--data", type=Path, help="the folder of items and decisions")
    four.add_argument("--to", type=Path, help="the folder the copy goes to, in a folder decisions")
    return held


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.step == "serve":
        return serve(args.reviewer, args.port, args.data, args.keep)
    if args.step == "fill":
        return fill(args.source, args.data, args.made_up)
    if args.step == "publish":
        return publish(args.data, args.to)
    return compile_(args.data, args.gazetteer)
