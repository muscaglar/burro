"""The steps of the command line that upkeep owns: `fresh` and `moved`.

    python -m burro_pipeline fresh --on 2026-09-25          what is held, and how old it is
    python -m burro_pipeline fresh --on 2026-09-25 --table  the same, as a table for a person
    python -m burro_pipeline moved BEFORE AFTER --out FOLDER  what differs between two builds

`fresh` reads what the repository holds and nothing else: no store, no publisher and no
clock. `moved` reads two releases, each with the folder of its build beside it, and each
by its own catalogue. Neither reaches a network, and neither changes what it reads.

What each prints for anyone to read is lines of `key=value` that hold step names, ids of
the registry and of the catalogue, the names a list gives its files, days and counts,
under names that are on the list in `tools/public_log.py`. Words go to standard error.
Neither prints the name of an area, its id or a figure of one.
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from burro_core.release import ReleaseError

from burro_pipeline.command import NOT_IGNORED, PROG, Step, add_step, may_be_written
from burro_pipeline.evidence import LockError, Receipt, read_receipts
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.fetch.sources import LISTS, FetchList, ListError, load_list
from burro_pipeline.registry import RegistryError, load
from burro_pipeline.registry.cadence import WORDS, Cadence, read
from burro_pipeline.release.read import UnreadableRelease
from burro_pipeline.upkeep import fresh, moved, written
from burro_pipeline.upkeep.searches import Search, Unfit, read_searches

FRESH, MOVED = "fresh", "moved"
RECEIPTS = Path(RECEIPTS_FOLDER)
# The searches that are ranked before and after, as the panel of the review desk keeps them.
SEARCHES = Path("tools/desk/panel/searches.json")
COULD_NOT_START = (
    "It could not start: the day, the registry, a list or the folder of receipts is wrong. "
    "The reason is said in words"
)

STEPS = (
    Step(
        FRESH,
        "Say of every file that has a receipt how old it is, and whether it is due",
        f"""\
Run it to see what to fetch again. It says of every file that has a receipt:
its source, its list and its item, the day it was retrieved, how many days
ago that was, how often its publisher says it changes, whether it is due, and
what of its list a person must bring forward before a newer edition is let in.

The day is given with --on, and the days are counted from the day a file was
retrieved to that day. No clock is read, so the same day gives the same lines.

How often a publisher says a file changes is read from the first words of
`cadence`, in the entry of its source in the licence registry, into one of:
weekly, monthly, quarterly, yearly, rarely. A publisher that says daily is
read as weekly, and a rhythm between two of them as the shorter. Where the
words are not read, the cadence is not said, and the step names the source on
standard error: begin its `cadence` with a word the step reads.

  state=due        It was retrieved longer ago than its cadence: over 7 days,
                   31, 92 or 366. It is time to look at its publisher's page
  state=fresh      It was retrieved within its cadence, or changes rarely. A
                   file that changes rarely is never due by its age
  state=not_known  Its cadence is not said. It is never called fresh
  state=older      A file of the same item was retrieved since
  state=unlisted   No list names the file, so no build takes it

  pins=none                A fetch takes whatever the publisher gives now:
                           the file states its own edition and its period
  pins=period              Bring `data_period` forward in the list first
  pins=edition_and_period  Bring `edition` and `data_period` forward in the
                           list first, and the address where it names them

It asks nothing of a publisher. So it cannot say that a newer edition is out,
and a file that was fetched again and found to be the same is as old as it
was: its receipt stands. Due means look, and no more than that.

Reads the licence registry, the lists and the receipts. Writes nothing.
Reaches no network and no store, and refuses nothing: it reports.

Prints one line for each file, then one line of totals. With --table it
prints a table for a person in place of the lines, with the edition and the
period each receipt states, what is due first. Run `{PROG} plan` on a list
before a fetch of it.""",
        ("--on 2026-09-25", "--on 2026-09-25 --table", f"--on 2026-09-25 --receipts {RECEIPTS}"),
        {0: "Always, whatever is due", 2: COULD_NOT_START},
    ),
    Step(
        MOVED,
        "Say what differs between two builds, before the newer is approved",
        f"""\
Run it once a build is made and before its lock is committed. It is given two
releases: the one that is served, and the one that was built. Each is the
folder of a release, with the folder of its build beside it, named for it
with -build after. It reads each by its own catalogue, whatever its version,
and refuses only a release it cannot read, or that is not as it was built.

It says:

  catalogue  its version on each side. Of each vibe both carry: the parts of
             its recipe that came or went, the shares that changed, and
             whether it became a rough guide. A name or a label that changed
  areas      which came or went, which bear another name, and which another
             outline
  measures   which came or went. Of each that both carry: how many areas
             changed their figure, by how much in the middle and at most, and
             how many gained a figure or lost one
  vibes      which came or went. Of each that both carry: how many areas
             changed band, and by how many bands
  prices     the same as of a measure, for what a home of each kind sells for
  files      which files of publishers behind the build are other files than
             before, from the two locks, each with the edition and the period
             its receipt states
  searches   the first ten areas of each search of --searches, before and
             after, ranked on each build by what that build holds. A vibe a
             search asks for that a build does not hold is said of that side

What it prints is counts: a line for each measure, vibe, source and search
that moved, and one for the whole. It never prints the name of an area, its
id or a figure. With --out it writes what it found to that folder, whole as
{written.JSON} and as a page for a person as {written.PAGE}. Both name areas
and give figures, so --out is refused inside the repository, but for
data/releases/ and scratch/, which git ignores.

A made-up release has no lock, so no file of it is compared. With no receipt
of a file, the file is known by its id alone, and a file that changed is said
to have gone and another to have come.

Reads the two releases, the receipts, the lists and the file of searches.
Reaches no network and no store. Changes nothing it reads.""",
        (
            "data/releases/lon-2026-09-25-01 data/releases/lon-2026-10-02-01",
            "data/releases/lon-2026-09-25-01 data/releases/lon-2026-10-02-01 "
            "--out data/releases/moved",
        ),
        {
            0: "The two were compared, whatever moved",
            2: "It could not start: a release cannot be read or has no lock beside it, "
            "the two are not of one city, the searches or the receipts could not be read, or "
            "--out is where git would take it in. The reason is said in words",
        },
    ),
)


class Stop(Exception):
    """The step cannot start. The message is safe to print."""


def a_day(given: str) -> date:
    """The day `--on` names. What was given is not repeated: it may be anything."""
    try:
        if len(given) != len("2026-09-25"):
            raise ValueError
        return date.fromisoformat(given)
    except ValueError:
        raise argparse.ArgumentTypeError("it is a day, as 2026-09-25") from None


def _lists(folder: Path) -> list[FetchList]:
    try:
        lists = [load_list(path) for path in sorted(folder.glob("*.toml"))]
    except ListError as error:
        raise Stop(str(error)) from None
    if not lists:
        raise Stop("the folder of lists holds no list")
    return lists


def _cadences(path: Path | None) -> dict[str, Cadence]:
    """The rhythm of every source of the registry. No rule of the registry is asked: the
    step fetches nothing and reads no file of a publisher, and a rule reads the clock."""
    try:
        return {source.id: read(source.cadence) for source in load(path, enforce=False)}
    except RegistryError as error:
        raise Stop(str(error)) from None


def _fresh(args: argparse.Namespace) -> int:
    with sockets_refused():
        try:
            receipts = [one for one in read_receipts(args.receipts) if not one.made_up]
        except LockError as error:
            raise Stop(str(error)) from None
        if not receipts:
            raise Stop("the folder of receipts holds no receipt")
        try:
            files = fresh.held(receipts, _lists(args.lists), _cadences(args.registry), args.on)
        except fresh.Before:
            raise Stop(
                "--on is before the day a file was retrieved. Give the day that is today"
            ) from None
    if args.table:
        print(fresh.table(files))
    else:
        for file in files:
            print(file.line())
    counts = " ".join(f"{name}={count}" for name, count in fresh.counted(files).items())
    print(f"step={FRESH} status=ok on={args.on.isoformat()} {counts}", flush=True)
    unsaid = sorted({file.receipt.source_id for file in files if file.cadence is Cadence.NOT_SAID})
    if unsaid:
        known = ", ".join(word for words in WORDS.values() for word in words)
        print(
            "note: the registry does not say how often a source changes, in words that are "
            f"read, of: {', '.join(unsaid)}. Begin the `cadence` of its entry with one of: "
            f"{known}",
            file=sys.stderr,
        )
    return 0


def _opened(folder: Path) -> moved.Build:
    try:
        return moved.open_build(folder)
    except UnreadableRelease as error:
        raise Stop(f"a release cannot be read: {error}") from None
    except ReleaseError as error:
        raise Stop(f"a release cannot be read: {error.file} [{error.rule}]") from None
    except moved.NoLock:
        raise Stop(
            f"{folder.name} has no lock beside it that can be read. A release that is not "
            "made up is compared with the folder of its build beside it"
        ) from None


def _receipts(folder: Path) -> tuple[Receipt, ...]:
    """The receipts of a folder. None where the folder is not there: a file is then known
    by its id alone."""
    if not folder.is_dir():
        return ()
    try:
        return tuple(one for one in read_receipts(folder) if not one.made_up)
    except LockError as error:
        raise Stop(str(error)) from None


def _searches(args: argparse.Namespace) -> tuple[Search, ...]:
    path: Path = args.searches if args.searches is not None else args.root / SEARCHES
    try:
        return read_searches(path, args.root)
    except Unfit as unfit:
        raise Stop(
            f"{unfit}. Name the file with --searches, and the top of the repository with --root"
        ) from None


def _moved(args: argparse.Namespace) -> int:
    out: Path | None = args.out
    if out is not None and not may_be_written(out, args.root):
        raise Stop(f"--out {NOT_IGNORED}")
    with sockets_refused():
        before, after = _opened(args.before), _opened(args.after)
        receipts = _receipts(args.receipts)
        lists = _lists(args.lists) if receipts else []
        try:
            found = moved.compare(
                before, after, receipts=receipts, lists=lists, searches=_searches(args)
            )
        except moved.OtherCity:
            raise Stop(
                "the two releases are not of one city, so there is nothing to compare. Name "
                "two releases of one city"
            ) from None
        if out is not None:
            written.write(found, out)
    for line in moved.lines(found):
        print(line)
    return 0


def build(prog: str = PROG) -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The steps upkeep owns, as the command line takes them: the whole, and each step of it."""
    whole = argparse.ArgumentParser(
        prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = whole.add_subparsers(dest="command", required=True)
    step = {step.name: add_step(commands, step, prog) for step in STEPS}
    step[FRESH].add_argument(
        "--on",
        required=True,
        type=a_day,
        metavar="DAY",
        help="the day the days are counted to, as 2026-09-25. Give the day that is today",
    )
    step[FRESH].add_argument(
        "--receipts",
        type=Path,
        default=RECEIPTS,
        metavar="FOLDER",
        help=f"the folder of receipts (default: {RECEIPTS})",
    )
    step[FRESH].add_argument(
        "--lists",
        type=Path,
        default=LISTS,
        metavar="FOLDER",
        help="the folder of the lists, each a .toml file (default: the lists of this repository)",
    )
    step[FRESH].add_argument(
        "--registry",
        type=Path,
        metavar="PATH",
        help="the licence registry, a file or a folder (default: this repository's)",
    )
    step[FRESH].add_argument(
        "--table",
        action="store_true",
        help="print a table for a person in place of the lines, with each edition and period",
    )
    step[MOVED].add_argument(
        "before", type=Path, metavar="BEFORE", help="the folder of the release that is served"
    )
    step[MOVED].add_argument(
        "after", type=Path, metavar="AFTER", help="the folder of the release that was built"
    )
    step[MOVED].add_argument(
        "--out",
        type=Path,
        metavar="FOLDER",
        help=f"write what was found to this folder, as {written.JSON} and {written.PAGE}. "
        "It names areas, so it is a folder git ignores, or one outside the repository",
    )
    step[MOVED].add_argument(
        "--receipts",
        type=Path,
        default=RECEIPTS,
        metavar="FOLDER",
        help=f"the folder of receipts, which say the edition of each file (default: {RECEIPTS})",
    )
    step[MOVED].add_argument(
        "--lists",
        type=Path,
        default=LISTS,
        metavar="FOLDER",
        help="the folder of the lists, each a .toml file (default: the lists of this repository)",
    )
    step[MOVED].add_argument(
        "--searches",
        type=Path,
        metavar="FILE",
        help=f"the searches that are ranked before and after (default: {SEARCHES})",
    )
    step[MOVED].add_argument(
        "--root",
        type=Path,
        default=Path(),
        metavar="FOLDER",
        help="the top of the repository, which holds the sentences the searches name and "
        "which --out is held to (default: here)",
    )
    return whole, step


def parsed(argv: Sequence[str] | None = None, prog: str = PROG) -> argparse.Namespace:
    """The arguments of a step. Stops with the step's usage if they are not ones it takes."""
    return build(prog)[0].parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parsed(argv)
    try:
        return _fresh(args) if args.command == FRESH else _moved(args)
    except Stop as stop:
        print(f"error: {stop}", file=sys.stderr)
    except OSError as error:
        print(f"error: cannot read or write a file: {error.strerror}", file=sys.stderr)
    return 2
