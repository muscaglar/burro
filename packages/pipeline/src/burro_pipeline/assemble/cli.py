"""The step of the command line that assemble owns: `preview`.

    python -m burro_pipeline preview --release-id ID --built-at TIME --out FOLDER

It is the whole of a first build in one command: seal, cells, derive,
assemble, check and report. What it prints may be read by anyone: one line of
`key=value` pairs for each of those, with counts and hashes. Why it stopped is
said in words on standard error. Neither holds a row, the name of an area or
the address of the store. What it works out names areas, so it is written to
files under the folder `--out` names and is never printed.
"""

import argparse
import csv
import hashlib
import io
import os
import re
import sys
import tempfile
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_core.catalogue import tags_of as vibes_of
from burro_core.facts import cost_key
from burro_core.ids import RELEASE_ID_PATTERN, FactKind, Tenure
from burro_core.income import INCOME_FOLDER, IncomeError
from burro_core.release import (
    BUILD_FOLDER,
    EVIDENCE,
    HASHES,
    LOCK,
    MANIFEST,
    Hashes,
    InMemoryRelease,
    ReleaseError,
    open_release,
)
from pydantic import ValidationError

from burro_pipeline import changes as decided
from burro_pipeline.assemble import names
from burro_pipeline.assemble.names import Bears, NamesError, Naming
from burro_pipeline.assemble.release import (
    GRITTY,
    Carried,
    Costed,
    Drawn,
    Named,
    evidence_of,
    release_of,
)
from burro_pipeline.cells import centres, land, outline, spine
from burro_pipeline.cells.spine import Spine
from burro_pipeline.command import NOT_IGNORED, PROG, Step, add_step, may_be_written
from burro_pipeline.derive import (
    brand_table,
    brands_nearby,
    household_income,
    price,
    price_paid,
    rent,
    station_places,
)
from burro_pipeline.derive.household_income import Estimated
from burro_pipeline.derive.measures import (
    MEASURES,
    TAGGED,
    Ground,
    Measure,
    behind,
    says_what_core_says,
)
from burro_pipeline.evidence.cli import (
    OWN_EDITION,
    TO_DO,
    add_edition,
    editions_of,
    in_full,
    named_once,
    public,
    taken_counted,
    taken_in_words,
)
from burro_pipeline.evidence.coverage import LeftOut as Reported
from burro_pipeline.evidence.coverage import cover, report, summary
from burro_pipeline.evidence.lock import (
    MEANING,
    Lock,
    LockError,
    Said,
    Taken,
    read_receipts,
    said_in,
    said_of,
    seal,
    take,
)
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER, Receipt
from burro_pipeline.evidence.record import FILE_ID_PATTERN, TIMESTAMP_PATTERN, in_words
from burro_pipeline.evidence.repository import NotRead, holds, tracks
from burro_pipeline.evidence.served import counted, served, unevidenced
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.cli import THE_STORE
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.fetch.run import WORDS, Why
from burro_pipeline.fetch.sources import Listed, ListError, load_list
from burro_pipeline.fetch.store import FolderStore, Store, StoreError, store_from_environment
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry, RegistryError, load
from burro_pipeline.registry.model import INTERNAL_USES, Use
from burro_pipeline.release.income import in_words as income_in_words
from burro_pipeline.release.income import write_income
from burro_pipeline.release.read import UnreadableRelease
from burro_pipeline.release.read import in_words as refusal_in_words
from burro_pipeline.release.write import canonical_json, packed, write_release

FILE_ID = re.compile(FILE_ID_PATTERN)
# What is built here is built from fetched files, so it is never a synthetic release.
RELEASE_ID = re.compile(RELEASE_ID_PATTERN.replace("(syn|lon)", "lon"))
TIMESTAMP = re.compile(TIMESTAMP_PATTERN)
# Beside the folder of the release, and never inside it: a release folder holds the files
# of the release and nothing else. Core names the folder and three of its files, because a
# release that is not made up is served only with them.
BESIDE = BUILD_FOLDER
COVERAGE, REPORT, HOMES, BUILD = "coverage.json", "coverage.md", "homes.json", "build.json"
# Every area with the name it bears, for a person to read. It names places, as the release
# does, and is written beside it where a build was given a draft of names.
NAMES = "names.csv"
NAMES_COLUMNS = (
    *("area_id", "borough", "label", "name", "state", "publishers", "source_ids"),
    *("neighbourhood", "output_areas_in_it", "output_areas"),
)
# Why a measure is left out of a release. Each is the name of a rule of the build.
NO_RECEIPT = "input_has_one_receipt"
# The name of the one file of changes a build takes: the founder's.
FOUNDERS_FILE = f"{decided.FOUNDER}.jsonl"
NOT_THE_FOUNDERS = f"the file of changes is named {FOUNDERS_FILE}: it is the founder's"
NOT_PUBLISHED = (
    "the file of changes is not the copy that was published: a build takes the file "
    "as the repository holds it, at the commit that is checked out. Make the copy "
    "with `make desk-publish`, commit it, and name that file"
)
HELD_BACK = "measure_is_not_held_back"
NOT_AS_CORE_SAYS = "measure_is_as_core_says"
NO_FIGURE = "measure_has_a_figure"
# Why the cost is left out of a release, where a list of the build names its file. The
# first is the rule of the check of a release, which would refuse the figure: a file that
# was fetched for an internal use stands behind no figure. A measure is left out by it too.
FETCHED_FOR_LESS = "input_is_allowed"
LEFT_OUT = (NO_RECEIPT, FETCHED_FOR_LESS, HELD_BACK, NOT_AS_CORE_SAYS, NO_FIGURE)
# The files a cost may be read from, and what each is called where a line says why it was
# left out. The sales come first: a median of them says how many it rests on.
PRICED_FROM: Mapping[str, str] = {
    price_paid.SOURCE: "A file of prices paid, or the postcode directory a sale is placed by,",
    price.SOURCE: "The workbook of median prices",
}
# The file a rent is read from, and what it is called where a line says why it was left out.
# It is placed by the postcode directory, as a sale is.
LET_FROM: Mapping[str, str] = {
    rent.SOURCE: "The workbook of rents, or the postcode directory an area is placed by,",
}
# What the record of a build says of its rents, where it carries them.
RENT_HELD = (
    "Burro holds the rent of the postcode district or of the borough an area lies in, as "
    "its publisher gives it, and never a rent of the area alone."
)
COST_LEFT_OUT: Mapping[str, tuple[str, str]] = {
    FETCHED_FOR_LESS: (
        "was fetched to validate against and for nothing wider, and a file that was fetched "
        "for an internal use stands behind no figure of a release",
        "Its receipt says what the licence gate was asked when the file was fetched, and the "
        "first receipt of a file stands. Name the file in the list for the use `scoring`, and "
        "have a person settle how its receipt is written again for that use.",
    ),
    NO_RECEIPT: (
        "has no receipt for the use the list names, or has more than one",
        "Fetch the file for the use the list names. If the folder holds a receipt of the file "
        "for another use, the first receipt of a file stands: a person settles how it is "
        "written again.",
    ),
    NO_FIGURE: (
        "has a figure for no area and no kind of home",
        "See what the file holds. Until an area has a figure, no cost is in the release.",
    ),
}
# The list of a build that is given none.
FIRST_LIST = "m1"

STEPS = (
    Step(
        "preview",
        "Build the preview release of a first build, from the store to a folder a person opens",
        f"""\
Run it once the files of the list are fetched. It is the whole of a first build
in one command, in this order:

  seal      writes the lock: every file of the list that has a receipt, by hash
  cells     makes the geography: the areas, their outlines and their land
  derive    works out each measure for every area, with its evidence
  assemble  puts them together as a release, and holds it to every rule of core
  check     fails if a fact the release would show has no evidence behind it
  report    writes the coverage report: what is there, and what is missing

The release is a preview. It holds areas, outlines and measures. It holds no
journey time and no station near an area, and nothing stands in for either.
Every response the API makes from it says that it is a preview, and that it is
not made up.

An area is under its publisher's label, which is a borough and a number. With
--names it bears the name of a neighbourhood, from a draft of London's named
areas: the folder a draft was written to, or the gazetteer the review desk
compiled from it. An area bears the name of the drafted neighbourhood that
holds most of its output areas, and keeps its label where none does. Two areas
of one borough that bear one name each say which side they lie on. Every name
is a draft, and the release says so of each, until a person has decided it at
the review desk. The three files that are read of the draft are named in the
lock by their hashes. A name rests on the publisher's file that writes it, which
must be a file of the build: name the list that holds it. The line of names
counts the areas that bear one, and prints no name.

It names the stations of London as places to reach where a list of the build
names the file of London's stops, and then says of each area where its homes
stand. It holds no journey time all the same: a journey to a station is
estimated for a search, from distance, and is said to be an estimate. The line
of places says how many it names, or by which rule it names none.

It holds what a home sells for where a list of the build names the files of
prices paid, or the workbook of median prices: a median for each kind of
home, with no range. Where the files of prices paid have their receipts, and
the postcode directory has its own, the median is worked out from the sales,
and says how many it rests on. Where they have none it is the publisher's own
median, from the workbook. An area with no figure for a kind of home has none
in the release. The line of cost says which source was read and how many rows
it holds, or by which rule it holds none. A workbook that was fetched to
validate against stands behind no figure, whatever the registry has come to
allow: its receipt says what the gate was asked, and no run writes a second
receipt of the same file.

It holds what a home lets for where a list of the build names the workbook of
the rents of London, and the postcode directory has its receipt: the middle
monthly rent of each kind of home, with its quartiles, for the postcode
district an area lies in or for its borough. A figure is of that place and
never of the area alone, and its row says which place it is of. An area takes
the figure of a district where half or more of its homes stand in it, and of
its borough otherwise. An area with neither has no rent, and nothing is
filled in. A second line of cost says how many rows of rent it holds.

A measure is left out, and never filled in, when its file has no receipt, when
a check of its figures holds it back, or when what it measures is not what
core says the measure is. The line of derive says which, by the name of the
rule. A file of the list with no receipt is counted under `missing` and is not
in the lock.

With --changes it takes what a person decided at the panel of the review desk:
a file of changes, one line for each change, with who made it, the day and why.
The lines that stand are laid over the catalogue: the shares of a recipe, the
name of a vibe and of its ends, what a vibe cannot see, and the label of a
measure. Every band is then worked out with the recipe the release carries. A
chain that was moved to another tier, added or taken out is laid over the table
of tiers, and the measures of the chains are worked out by that table. The
file is read whole before a publisher's file is opened. A line that cannot be
read, a change that breaks a rule of a recipe or of a name, and a change that
was made of something other than what stands each stop the build: the line is
named by its number, and nothing it holds is printed. The lock names the file
by its hash, the manifest of the release says the same hash, and the record of
the build lists each line that was applied, by its number. With no --changes
the build is byte for byte what it was.

The file can be written by hand, so the build takes it only as it was
published: the founder's file, r1.jsonl, as the repository holds it at the
commit that is checked out. A file that is in no repository, that git does not
track, or that was changed since it was committed, is refused. A chain is
added only where the file of places gives its name to two places or more that
stand apart: one shop is no chain, and the name of a person is none.

With --published-changes it is given the place the review desk publishes the
founder's file to, whether or not anything was published. It is for a build
that is started with no person to name a file, as a hosted run is. Where the
repository tracks a file there, the build takes it as --changes takes one, and
holds it to every rule above. Where the repository tracks none, the build is
given none, and is byte for byte what it is with no file. What stands there
and is not tracked is never read, and stops the build.

A build may take the files of more than one list: give --list once for each.
A file that is in none of them is no part of the build, whatever receipts the
folder holds, and a measure that reads it is left out.

{OWN_EDITION}

Run it at the top of the repository, with everything committed. The lock names
the code by its commit, which is read from the repository. With no package
lockfile the build is a development build, which is never served to the public.

For each file, before it is read: the licence registry is asked whether the
file may be put to this use. Its receipt must be among those of the list. A
copy is taken from the store and held to the hash in the receipt, and the lock
must name it. When the release is written the registry is asked again, about
every source the release cites and the use its file needs.

Reads the list, the receipts, the licence registry and the files of the list,
each through its receipt. Reaches no publisher. Reaches the store, to list it
and to copy its files out, and writes nothing to it. No socket is open while a
file is read. Built twice from the same files, it writes the same bytes.

{THE_STORE}
A folder hands a file over as it is asked for. An object store is reached over
a network, so every file of the lock is copied out of it before any is read,
and a line says how many there were. A key that can only read the store is
enough.

Writes two folders under --out. What is in them is made from publishers' files,
so --out and --work are refused inside the repository, but for data/releases/
and scratch/, which git ignores.
  ID         the release, as `burro-release check` and the API read it
  ID{BESIDE}   {LOCK}, {EVIDENCE}, {HASHES}, {COVERAGE}, {REPORT},
             {HOMES} and {BUILD}, which says what was left out and why.
             With --names, {NAMES} too: every area with the name it bears

{HASHES} holds the hash of the manifest, of the evidence and of the lock. The
release is served only while all three are as they were written. To approve a
release is to commit its lock and its hashes.

Prints one line for each part of the work.""",
        (
            "--release-id lon-2026-10-02-01 --built-at 2026-10-02T09:00:00Z --out data/releases",
            "--release-id lon-2026-10-02-01 --built-at 2026-10-02T09:00:00Z --out data/releases "
            "--list m1 --work scratch/copies",
            "--release-id lon-2026-10-02-01 --built-at 2026-10-02T09:00:00Z --out data/releases "
            "--list m1 --list m2-places",
            "--release-id lon-2026-10-02-01 --built-at 2026-10-02T09:00:00Z --out data/releases "
            '--list m1 --list m2-places --edition fsa-camden="extract of 2026-09-16"',
            "--release-id lon-2026-10-02-01 --built-at 2026-10-02T09:00:00Z --out data/releases "
            "--list m1 --list m2-places --names scratch/draft",
            "--release-id lon-2026-10-02-01 --built-at 2026-10-02T09:00:00Z --out data/releases "
            "--list m1 --changes gazetteer/london/decisions/changes/r1.jsonl",
            "--release-id lon-2026-10-02-01 --built-at 2026-10-02T09:00:00Z --out data/releases "
            "--list m1 --published-changes gazetteer/london/decisions/changes/r1.jsonl",
        ),
        {
            0: "The release was written",
            1: "A fact of the release has no evidence behind it. Nothing was written",
            2: "A file may not be read, or is not what the step was written to read, or the "
            "release breaks a rule. The line names the rule. Or the store did not answer, or "
            "refused: the line says `why=8`. Nothing was written",
        },
    ),
)


class Refused(Exception):
    """The step could not start or could not finish. Says why, and never what a file holds."""


# What a person can do about a store that fails, as fetch says it of the same number.
WHAT_TO_DO_OF_THE_STORE = WORDS[Why.STORE].partition(". ")[2]


@dataclass(frozen=True)
class LeftOut:
    """A measure that is not in the release, and the rule that kept it out."""

    measure: Measure
    rule: str

    @property
    def waits_on(self) -> tuple[str, ...]:
        """What would bring the measure in: what it says of itself, or what the rule asks.

        Of a measure that is held back, what the check found comes first, and
        then what else is not settled: both keep it out.
        """
        if self.rule == HELD_BACK:
            return (*self.measure.held_back, *self.measure.waits_on)
        said = self.measure.waits_on if self.rule == NOT_AS_CORE_SAYS else ()
        return said or (f"{self.to_do}.",)

    @property
    def why(self) -> str:
        """What the rule means, as it is said after "It"."""
        return COST_LEFT_OUT[self.rule][0] if self.rule == FETCHED_FOR_LESS else MEANING[self.rule]

    @property
    def to_do(self) -> str:
        """What a person does about it, with no full stop."""
        if self.rule == FETCHED_FOR_LESS:
            return COST_LEFT_OUT[self.rule][1].removesuffix(".")
        return TO_DO[self.rule]

    def reported(self) -> Reported:
        """The measure as the coverage report says it, with its rule and what it waits on."""
        return Reported(
            f"{FactKind.FEATURE}/{self.measure.feature}", self.rule, self.why, self.waits_on
        )


@dataclass(frozen=True)
class CostLeftOut:
    """Why a release holds no cost, where a list of the build names the file of one."""

    rule: str
    # The use of a receipt of the file that is in the folder and is no part of the build,
    # where there is one. It says why a file that was fetched has no receipt in the build.
    fetched_for: str | None = None
    # The source the cost would have been read from.
    source: str = price.SOURCE
    # Whether it is what a home sells for that is left out, or what one lets for.
    tenure: Tenure = Tenure.BUY

    @property
    def why(self) -> str:
        return COST_LEFT_OUT[self.rule][0]

    @property
    def waits_on(self) -> tuple[str, ...]:
        found = (COST_LEFT_OUT[self.rule][1],)
        if self.fetched_for is None:
            return found
        return (
            f"A receipt of the file is in the folder, for the use `{self.fetched_for}`.",
            *found,
        )

    def reported(self) -> tuple[Reported, ...]:
        """The cost of each kind of home, as the coverage report says what was left out."""
        if self.tenure is Tenure.RENT:
            keys = [cost_key(Tenure.RENT, home) for home in rent.HOMES]
        else:
            keys = [home.cost_key for home in price.HOMES if home.cost_key is not None]
        return tuple(
            Reported(f"{FactKind.COST}/{key}", self.rule, self.why, self.waits_on) for key in keys
        )


def _said(file: Listed | Receipt) -> Said:
    return said_in(file) if isinstance(file, Receipt) else said_of(file)


def _paired(
    receipts: Sequence[Receipt], listed: Sequence[Listed], editions: Mapping[str, str] | None
) -> tuple[list[tuple[Listed, Receipt]], list[Listed], tuple[Taken, ...]]:
    """Each file of a list with its receipt, the files that have none, and what was taken.

    The folder of receipts holds the receipts of every list. A receipt is of
    this list when it says of its file what the list says: the source, the
    use, the edition and the period, and the columns that were taken where
    part of the file was. Where two files are said alike, the address tells
    them apart. Where a publisher hands a download on, the
    address in the receipt is not the list's, and they are counted: more
    receipts than the list names files is refused, because nothing says which
    is meant.

    A list states no edition of a file that states its own. `take` in the
    lock says which receipts are of such a file, and which one the build
    takes. The receipts of its other editions are left alone.
    """
    taken, none_of = take(receipts, listed, editions)
    dated = {one.item: one.receipt for one in taken}
    aside = {held.file_id for one in taken for held in (one.receipt, *one.passed_over)}
    left = [receipt for receipt in receipts if receipt.file_id not in aside]
    paired: list[tuple[Listed, Receipt]] = []
    waiting: list[Listed] = []
    without: list[Listed] = []
    for file in listed:
        if file.edition_from is not None:
            if file.item in none_of:
                without.append(file)
            else:
                paired.append((file, dated[file.item]))
            continue
        same = [r for r in left if _said(r) == _said(file) and r.url == file.url]
        if len(same) == 1:
            paired.append((file, same[0]))
            left.remove(same[0])
        else:
            waiting.append(file)
    for said in dict.fromkeys(_said(file) for file in waiting):
        files = [file for file in waiting if _said(file) == said]
        found = [receipt for receipt in left if _said(receipt) == said]
        if len(found) > len(files):
            raise LockError("listed_file_has_one_receipt", found[-1].file_id)
        paired += zip(files, found, strict=False)
        without += files[len(found) :]
    order = {file.item: n for n, file in enumerate(listed)}
    paired.sort(key=lambda pair: order[pair[0].item])
    without.sort(key=lambda file: order[file.item])
    return paired, without, taken


def of_the_list(
    receipts: Sequence[Receipt],
    listed: Sequence[Listed],
    editions: Mapping[str, str] | None = None,
) -> tuple[list[Receipt], list[Listed], list[Listed]]:
    """The receipts of a list, the files of it that have one, and the files that have none.

    Of a file that states its own edition the receipt is the one the build
    takes: the edition `editions` names for it, or the newest.
    """
    paired, without, _ = _paired(receipts, listed, editions)
    return [receipt for _, receipt in paired], [file for file, _ in paired], without


def _lists(args: argparse.Namespace) -> list[str]:
    """The lists of the build, as they were given. With none given it is the first build's."""
    return list(args.list or [FIRST_LIST])


def _listed(lists: Sequence[str]) -> list[Listed]:
    """Every file of the lists of a build, in the order the lists were given.

    A file is told from another by the name its list gives it, so two lists
    that give one name are refused: nothing says which file is meant.
    """
    listed: list[Listed] = []
    for which in lists:
        try:
            listed += load_list(Path(which) if which.endswith(".toml") else which).files
        except ListError as error:
            raise Refused(f"the list of the build cannot be read: {error}") from None
    if len({file.item for file in listed}) != len(listed):
        raise Refused(
            "two lists of the build name a file alike, so nothing says which is meant. Give "
            "each list once, and give each file one name"
        )
    return listed


def _drafted(args: argparse.Namespace) -> dict[str, bytes] | None:
    """The files of the draft of names the build was given, or nothing where it was given none.

    Each is read as a table before anything else is done, so that a draft that
    cannot be read stops the build before a file of a publisher is opened.
    """
    if args.names is None:
        return None
    try:
        found = names.files_of(args.names)
        names.to_lock(found)
        names.draft_of(found)
    except NamesError as error:
        raise Refused(f"the draft of names cannot be built on: {error}") from None
    return found


@dataclass(frozen=True)
class Changed:
    """The file of changes a build was given: its name, its bytes and its lines."""

    name: str
    content: bytes
    lines: tuple[decided.Change, ...]

    def record(self) -> dict[str, object]:
        """What the record of a build says of it. It holds no reason and no value."""
        stands = decided.standing(self.lines)
        return {
            "file": self.name,
            "sha256": hashlib.sha256(self.content).hexdigest(),
            "lines": len(self.lines),
            "stand": len(stands),
            "applied": decided.applied(self.lines, decided.APPLIED),
            "flagged": sum(one.what in decided.FOR_A_PERSON for one in stands),
        }


def _changed(args: argparse.Namespace) -> Changed | None:
    """The file of changes the build was given, or nothing where it was given none.

    It is read whole, and what stands of it is laid over core's own, before
    anything else is done: a change that cannot be built stops the build before
    a file of a publisher is opened.
    """
    path: Path | None = args.changes if args.changes is not None else _published(args)
    if path is None:
        return None
    try:
        content = path.read_bytes()
    except OSError:
        raise Refused("the file of changes cannot be read from the disk") from None
    if not content:
        raise Refused(
            "the file of changes holds no line. Build with no --changes, or name a file "
            "that holds one"
        )
    try:
        lines = decided.read(content)
        # Only the founder's file is built. Another reviewer's change is a proposal, which
        # the founder keeps as their own or does not.
        if lines[0].by != decided.FOUNDER:
            raise decided.ChangesError(1, "changes_are_the_founders")
        decided.adjusted(vibes_of(GRITTY), lines)
        decided.labels_hold(lines)
        decided.table_with(brand_table.the_table(), lines)
        not_yet = [
            one
            for one in decided.standing(lines)
            if one.what not in decided.APPLIED | decided.FOR_A_PERSON
        ]
        if not_yet:
            raise decided.ChangesError(not_yet[0].n, "change_is_one_a_build_applies")
    except decided.ChangesError as error:
        raise Refused(
            f"the file of changes cannot be built on: line {error.line} breaks the rule "
            f"{error.rule}. Look at the line at the panel, or take it back there"
        ) from None
    if path.name != FOUNDERS_FILE:
        raise Refused(NOT_THE_FOUNDERS)
    # A file of changes can be written by hand. What a build takes is the copy that was
    # published: the one the repository holds, at the commit that is checked out. So a
    # file that was written by hand is built only once it has been committed, where it is
    # read as any other change is. That nothing is staged is the lock's to say.
    try:
        published = holds(args.root, path, content)
    except NotRead as error:
        raise Refused(f"the repository cannot be read: {error}") from None
    if not published:
        raise Refused(NOT_PUBLISHED)
    return Changed(path.name, content, lines)


def _published(args: argparse.Namespace) -> Path | None:
    """The founder's published file of changes, where the repository tracks one.

    A build that no person starts by hand is given the place the desk publishes
    the file to, whether or not anything was published. Where the repository
    tracks a file there, it is taken as `--changes` takes one, and held to the
    same rules. Where it tracks none the build is given none. What stands there
    and is not tracked was written by a run or by a hand: it is never read, and
    the build stops, so that no build is ever made from less than it seems.
    """
    place: Path | None = args.published_changes
    if place is None:
        return None
    if place.name != FOUNDERS_FILE:
        raise Refused(NOT_THE_FOUNDERS)
    try:
        if tracks(args.root, place):
            return place
    except NotRead as error:
        raise Refused(f"the repository cannot be read: {error}") from None
    if place.is_symlink() or place.exists():
        raise Refused(NOT_PUBLISHED)
    return None


def _chains_are_seen(changed: Changed | None, inputs: Inputs, found: Spine) -> None:
    """Refuse a chain that a line adds and that the file of places does not show to be one.

    The name of a chain is said in what Burro says of a measure. So a name that
    is of a person, or of one shop, is said nowhere: `seen_to_be_a_chain` says
    how a chain is told from either. A build that reads no file of places with
    their brands can tell nothing, and adds none.
    """
    added = decided.added(brand_table.of_the_repository(), changed.lines) if changed else ()
    if not added:
        return
    written: Mapping[str, Mapping[str, int]] = {}
    counted: Mapping[str, int] = {}
    try:
        held = brands_nearby.build(inputs, found).held
        written, counted = held.written, held.counted
    except LockError as error:
        if error.rule != NO_RECEIPT:
            raise
    for line in added:
        if not decided.seen_to_be_a_chain(line, written, counted):
            raise Refused(
                f"the file of changes cannot be built on: line {line.n} breaks the rule "
                f"{decided.NOT_SEEN}. Look at the line at the panel, or take it back there"
            )


def _sealed(
    args: argparse.Namespace,
    registry: Registry,
    store: Store,
    drafted: Mapping[str, bytes] | None = None,
    changed: Changed | None = None,
) -> tuple[Lock, list[Receipt], list[Listed], tuple[Taken, ...]]:
    listed = _listed(_lists(args))
    editions = editions_of(args)
    paired, without, taken = _paired(read_receipts(args.receipts), listed, editions)
    receipts = [receipt for _, receipt in paired]
    packages = hashlib.sha256(args.packages.read_bytes()).hexdigest() if args.packages else None
    lock = seal(
        args.release_id,
        args.built_at,
        args.commit,
        receipts,
        {held.key: held.bytes for held in store.list()},
        registry,
        args.root,
        packages,
        # The files of a draft of names are no publisher's files. The lock names each by
        # its hash, so that a release says which draft its names were chosen from. It names
        # the file of changes so too, so that a release says which changes it was built with.
        others=(
            *(names.to_lock(drafted) if drafted is not None else ()),
            *((decided.to_lock(changed.name, changed.content),) if changed is not None else ()),
        ),
        listed=[file for file, _ in paired],
        editions=editions,
    )
    return lock, receipts, without, taken


def _fetched_for_less(inputs: Inputs, measure: Measure) -> bool:
    """Whether a file the measure reads was fetched for an internal use, and for nothing wider.

    Such a file is not read: the check of a release would refuse every figure
    that rested on it, and a build must not fail on a measure it can leave out.
    """
    return any(
        receipt.use in INTERNAL_USES
        for receipt in inputs.receipts
        if receipt.source_id == measure.source and measure.reads(receipt.publisher_file)
    )


def _measured(inputs: Inputs, ground: Ground) -> tuple[list[Carried], list[LeftOut]]:
    """Every measure that can be worked out, and every one that is left out, with the rule.

    A measure that is held back is worked out as any other, so that a file it
    cannot read stops the build, and is then left out whatever core says of it.
    """
    carried: list[Carried] = []
    left_out: list[LeftOut] = []
    for measure in MEASURES:
        if _fetched_for_less(inputs, measure):
            left_out.append(LeftOut(measure, FETCHED_FOR_LESS))
            continue
        try:
            measured = measure.build(inputs, ground)
        except LockError as error:
            if error.rule != NO_RECEIPT:
                raise
            left_out.append(LeftOut(measure, NO_RECEIPT))
            continue
        if measure.held_back:
            left_out.append(LeftOut(measure, HELD_BACK))
        elif not says_what_core_says(measured.metric):
            left_out.append(LeftOut(measure, NOT_AS_CORE_SAYS))
        elif all(figure.value is None for figure in measured.worked.values()):
            left_out.append(LeftOut(measure, NO_FIGURE))
        else:
            carried.append(Carried(measure, measured))
    return carried, left_out


def _sold(inputs: Inputs, found: Spine) -> tuple[Costed | None, CostLeftOut | None]:
    """What a home sells for, worked out from the sales, or the rule that keeps it out.

    The files of sales are read with the postcode directory, which says where
    a sale is. Where either has no receipt in the build nothing is read.
    """
    try:
        sold = price_paid.build(inputs, found)
    except LockError as error:
        if error.rule != NO_RECEIPT:
            raise
        return None, CostLeftOut(NO_RECEIPT, source=price_paid.SOURCE)
    rows = price_paid.costs(sold)
    if not rows:
        return None, CostLeftOut(NO_FIGURE, source=price_paid.SOURCE)
    counts = sold.counts
    counted: dict[str, object] = {
        "since": sold.since,
        "until": sold.until,
        "fewest_sales": price_paid.FEWEST,
        "rows": counts.rows,
        "rows_by_year": {str(year): held for year, held in counts.by_year.items()},
        "additional": counts.additional,
        "of_no_kind_of_home": counts.of_no_kind_of_home,
        "placed": counts.placed,
        "not_placed": counts.not_placed,
        "placed_by_home": {str(home): held for home, held in counts.by_home.items()},
        "newly_built_by_home": {str(home): held for home, held in counts.newly_built.items()},
        "at_an_ended_postcode": counts.at_an_ended_postcode,
    }
    made = Costed(
        rows,
        price_paid.evidence(sold),
        sold.files,
        price_paid.METHODS,
        price_paid.SOURCE,
        price_paid.CANNOT_SEE,
        counted,
    )
    return made, None


def _costed(
    inputs: Inputs, found: Spine, in_the_folder: Sequence[Receipt], listed: Collection[str]
) -> tuple[Costed | None, CostLeftOut | None]:
    """What a home sells for, as the build carries it, or the rule that keeps it out.

    It is asked only of a build whose list names the files of prices paid or
    the workbook of median prices. `listed` is the sources the lists name.
    The sales come first: a median of them says how many sales it rests on.
    Where they have no receipt, or give no figure, the cost is the
    publisher's own median, where a list names the workbook.

    A workbook that was fetched for an internal use is not read: `check`
    would refuse every figure that rested on it, and a build must not fail on
    a cost it can leave out. `in_the_folder` is every receipt of the folder,
    which says whether the file was fetched for another use than the list
    names.
    """
    gone: CostLeftOut | None = None
    if price_paid.SOURCE in listed:
        made, gone = _sold(inputs, found)
        if made is not None:
            return made, None
    if price.SOURCE not in listed:
        return None, gone
    is_it = price.is_the_workbook
    ours = [r for r in inputs.receipts if r.source_id == price.SOURCE and is_it(r.publisher_file)]
    if any(receipt.use in INTERNAL_USES for receipt in ours):
        return None, CostLeftOut(FETCHED_FOR_LESS)
    try:
        prices = price.build(inputs, found)
    except LockError as error:
        if error.rule != NO_RECEIPT:
            raise
        others = sorted(
            receipt.use
            for receipt in in_the_folder
            if receipt.source_id == price.SOURCE and is_it(receipt.publisher_file)
        )
        return None, CostLeftOut(NO_RECEIPT, others[0] if others else None)
    rows = price.costs(prices)
    if not rows:
        return None, CostLeftOut(NO_FIGURE)
    made = Costed(
        rows, price.evidence(prices), prices.files, price.METHODS, price.SOURCE, price.CANNOT_SEE
    )
    return made, None


def _let(inputs: Inputs, found: Spine) -> tuple[Costed | None, CostLeftOut | None]:
    """What a home lets for, for the place an area lies in, or the rule that keeps it out.

    It is asked only of a build whose list names the workbook of rents. The
    workbook is read with the postcode directory, which says which district a
    postcode is of. Where either has no receipt in the build nothing is read.
    A workbook that was fetched for an internal use is not read: `check` would
    refuse every figure that rested on it.
    """
    ours = [
        receipt
        for receipt in inputs.receipts
        if receipt.source_id == rent.SOURCE and rent.is_the_workbook(receipt.publisher_file)
    ]

    def gone(rule: str) -> CostLeftOut:
        return CostLeftOut(rule, source=rent.SOURCE, tenure=Tenure.RENT)

    if any(receipt.use in INTERNAL_USES for receipt in ours):
        return None, gone(FETCHED_FOR_LESS)
    try:
        rents = rent.build(inputs, found)
    except LockError as error:
        if error.rule != NO_RECEIPT:
            raise
        return None, gone(NO_RECEIPT)
    rows = rent.costs(rents)
    if not rows:
        return None, gone(NO_FIGURE)
    counts = rents.counts
    counted: dict[str, object] = {
        "since": rents.since,
        "until": rents.until,
        "fewest_rents": rent.FEWEST,
        "least_share_of_homes_percent": rent.HALF,
        "boroughs": counts.boroughs,
        "districts": counts.districts,
        "areas_of_a_district": counts.areas_of_a_district,
        "areas_of_no_district": counts.areas_of_no_district,
        "areas_by_home": {str(home): dict(by) for home, by in counts.by_home.items()},
    }
    made = Costed(
        rows,
        rent.evidence(rents),
        rents.files,
        rent.METHODS,
        rent.SOURCE,
        rent.CANNOT_SEE,
        counted,
    )
    return made, None


def _both(costed: Costed | None, let: Costed | None) -> Costed | None:
    """What a home sells for and what one lets for, as the one set of costs of a release.

    Each keeps its own rows of evidence, its own files and its own methods.
    The rows are in the order a release keeps them.
    """
    if costed is None or let is None:
        return costed or let
    files = {receipt.file_id: receipt for receipt in (*costed.files, *let.files)}
    methods = {method.derivation_id: method for method in (*costed.methods, *let.methods)}
    rows = sorted((*costed.rows, *let.rows), key=lambda row: (row.area_id, row.tenure, row.segment))
    return Costed(
        tuple(rows),
        (*costed.evidence, *let.evidence),
        tuple(files[file_id] for file_id in sorted(files)),
        tuple(methods[name] for name in sorted(methods)),
        costed.source,
        costed.cannot_see,
        costed.counted,
    )


def _places(inputs: Inputs, found: Spine) -> tuple[Named | None, str | None]:
    """The stations a person can name and where the homes of each area stand, or the rule
    that keeps them out.

    The gate is asked whether the file of stops may be put to destination
    search, and whether the centres of output areas may be put to the naming
    of places, before either is read. A build whose lists name no file of
    London's stops names no place, and goes on.
    """
    of_the_stops = [
        receipt
        for receipt in inputs.receipts
        if receipt.source_id == station_places.SOURCE
        and station_places.is_the_file(receipt.publisher_file)
    ]
    if any(receipt.use in INTERNAL_USES for receipt in of_the_stops):
        return None, FETCHED_FOR_LESS
    try:
        places = station_places.build(inputs)
    except LockError as error:
        if error.rule != NO_RECEIPT:
            raise
        return None, NO_RECEIPT
    placed = inputs.open(centres.CENTRES, Use.GAZETTEER, edition=centres.CENTRES_EDITION)
    homes_at = centres.middles_of(centres.centres_of(placed, found), found)
    return Named(places.places, places.file, placed.receipt, homes_at), None


def _places_record(named: Named | None, rule: str | None) -> dict[str, object]:
    """What the record of a build says of the places to reach. It holds counts, and no name."""
    return {
        "source_id": station_places.SOURCE,
        "places": len(named.places) if named is not None else 0,
        "areas_with_homes_placed": len(named.homes_at) if named is not None else 0,
        "left_out": None if rule is None else {"rule": rule, "why": f"It {MEANING[rule]}."},
        "journeys": "No journey time is held. A journey by public transport to a place is "
        "estimated for a search, from distance, and is said to be an estimate."
        if named is not None
        else "No place is named, so no journey can be asked for.",
    }


def _rent_record(let: Costed | None, gone: CostLeftOut | None) -> dict[str, object]:
    """What the record of a build says of its rents. It holds counts, and no figure and no
    name of a place."""
    rows = let.evidence if let is not None else ()
    carried: list[dict[str, object]] = []
    for home in rent.HOMES if let is not None else ():
        key = f"{FactKind.COST}/{cost_key(Tenure.RENT, home)}"
        states = [row.state for row in rows if row.measure == key]
        counted = {state: states.count(state) for state in sorted(set(states))}
        carried.append({"tenure": "rent", "segment": home, "areas": len(states), **counted})
    left_out = None
    if gone is not None:
        left_out = {"rule": gone.rule, "why": f"It {gone.why}.", "waits_on": list(gone.waits_on)}
    return {
        "source_id": rent.SOURCE,
        "listed": True,
        "as_of": let.rows[0].as_of if let is not None else None,
        "carried": carried,
        "left_out": left_out,
        "methods": [method.derivation_id for method in (let.methods if let else ())],
        "cannot_see": list(rent.CANNOT_SEE),
        "said": RENT_HELD if let is not None else price.NO_RENT,
        # What the step that read the workbook counted. It holds no rent and names no place.
        "counted": dict(let.counted) if let is not None and let.counted else None,
    }


def _cost_record(
    asked: bool, costed: Costed | None, gone: CostLeftOut | None, let: Costed | None = None
) -> dict[str, object]:
    """What the record of a build says of the cost. It holds counts, and no figure."""
    rows = costed.evidence if costed is not None else ()
    carried: list[dict[str, object]] = []
    for home in price.HOMES:
        states = [row.state for row in rows if row.measure == f"{FactKind.COST}/{home.cost_key}"]
        if home.segment is not None and costed is not None:
            counted = {state: states.count(state) for state in sorted(set(states))}
            carried.append(
                {"tenure": "buy", "segment": home.segment, "areas": len(states), **counted}
            )
    left_out = None
    if gone is not None:
        left_out = {"rule": gone.rule, "why": f"It {gone.why}.", "waits_on": list(gone.waits_on)}
    source = costed.source if costed is not None else gone.source if gone else price.SOURCE
    return {
        "source_id": source,
        "listed": asked,
        "as_of": costed.rows[0].as_of if costed is not None else None,
        "carried": carried,
        "left_out": left_out,
        "methods": [method.derivation_id for method in (costed.methods if costed else ())],
        "cannot_see": list(costed.cannot_see if costed is not None else price.CANNOT_SEE),
        "rent": RENT_HELD if let is not None else price.NO_RENT,
        # What the step that read the sales counted. It holds no price and names no area.
        "counted": dict(costed.counted) if costed is not None and costed.counted else None,
    }


def _income_record(estimated: Estimated | None) -> dict[str, object]:
    """What the build record says of household income. It holds counts, and no figure."""
    if estimated is None:
        return {"asked": False}
    return {
        "asked": True,
        "source_id": household_income.SOURCE,
        "shown_and_never_ranked_on": True,
        "areas": len(estimated.areas),
        "areas_with_an_estimate": estimated.given,
        "folder": INCOME_FOLDER,
    }


def _opened(release: InMemoryRelease) -> InMemoryRelease:
    """The release as core reads it back from the bytes that would be written."""
    try:
        return open_release(release.manifest.release_id, packed(release))
    except ReleaseError as error:
        words = refusal_in_words(error, Path(release.manifest.release_id))
        raise Refused(f"the release breaks a rule of the contract: {words}") from None


def _named(
    drafted: Mapping[str, bytes],
    found: Spine,
    outlines: Mapping[str, outline.Outline],
    inputs: Inputs,
) -> Naming:
    """The name each area bears, from the draft the build was given."""
    try:
        return names.build(
            drafted,
            found.areas,
            found.weights.of_area,
            {area: outlines[area].centre for area in sorted(outlines)},
            inputs.receipts,
            inputs.lock,
            inputs.registry,
        )
    except NamesError as error:
        raise Refused(f"the draft of names cannot be built on: {error}") from None


def _names_record(naming: Naming | None) -> dict[str, object] | None:
    """What the record of a build says of its names. It holds counts, and no name."""
    if naming is None:
        return None
    return {
        "method": names.NAMED.derivation_id,
        "rests_on": [receipt.file_id for receipt in naming.files],
        "source_ids": list(naming.source_ids),
        **naming.counts(),
    }


def names_table(drawn: Drawn, registry: Registry) -> bytes:
    """Every area with the name it bears, as a table for a person to read."""
    bears: Mapping[str, Bears] = drawn.naming.bears if drawn.naming else {}
    text = io.StringIO(newline="")
    table = csv.DictWriter(text, NAMES_COLUMNS, lineterminator="\n")
    table.writeheader()
    for area in drawn.spine.areas:
        borne = bears.get(area.area_id)
        sources = borne.source_ids if borne else ()
        table.writerow(
            {
                "area_id": area.area_id,
                "borough": area.borough,
                "label": area.name,
                "name": borne.name if borne else "",
                "state": borne.written.state.value if borne else "",
                "publishers": "; ".join(
                    dict.fromkeys(registry.get(source).publisher for source in sources)
                ),
                "source_ids": "; ".join(sources),
                "neighbourhood": borne.written.place_id if borne else "",
                "output_areas_in_it": borne.held if borne else "",
                "output_areas": len(drawn.spine.weights.of_area[area.area_id]),
            }
        )
    return text.getvalue().encode("utf-8")


def _build_record(
    args: argparse.Namespace,
    lock: Lock,
    without: Sequence[Listed],
    carried: Sequence[Carried],
    left_out: Sequence[LeftOut],
    evidence: Evidence,
    cost: Mapping[str, object],
    named: Mapping[str, object] | None,
    places: Mapping[str, object],
    income: Mapping[str, object],
    changed: Changed | None = None,
    let: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """What was built, from what, and what was left out and why. It holds no figure."""
    return {
        "release_id": args.release_id,
        "built_at": args.built_at,
        # One list is said by its name, as it was in the first build. More are joined, in
        # the order of their names and not of the arguments, so that a build repeats.
        "list": "+".join(sorted(Path(which).stem for which in _lists(args))),
        "commit": lock.commit,
        "development": lock.development,
        "files_sealed": [locked.name for locked in lock.inputs],
        # In the order of their names and not of the lists, so that a build repeats.
        "files_of_the_list_with_no_receipt": [
            {"item": file.item, "source_id": file.source_id}
            for file in sorted(without, key=lambda file: file.item)
        ],
        "measures_carried": [
            {
                "feature_id": one.feature,
                "source_id": one.measure.source,
                "methods": [method.derivation_id for method in one.measure.methods],
                "keyed_by": one.measured.geography,
                "cannot_see": list(one.measure.cannot_see),
            }
            for one in carried
        ],
        "measures_left_out": [
            {
                "feature_id": one.measure.feature,
                "source_id": one.measure.source,
                "rule": one.rule,
                "why": f"It {one.why}. {one.to_do}",
                "waits_on": list(one.waits_on),
            }
            for one in left_out
        ],
        "cost": dict(cost),
        # A build whose lists name no workbook of rents says nothing more of rents, as before.
        **({"rent": dict(let)} if let is not None else {}),
        # A build that was given no draft of names says nothing of names, as before.
        **({"names": dict(named)} if named is not None else {}),
        "places": dict(places),
        # What stands beside the release to be shown on an area's page, and is no part of it.
        "income": dict(income),
        # A build that was given no file of changes says nothing of changes, as before.
        **({"changes": changed.record()} if changed is not None else {}),
    }


def _preview(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    out: Path = args.out
    if not RELEASE_ID.fullmatch(args.release_id):
        raise Refused("--release-id is not the id of a release of London, as lon-2026-10-02-01")
    if not TIMESTAMP.fullmatch(args.built_at):
        raise Refused("--built-at is not a time in UTC, as 2026-10-02T09:00:00Z")
    for name, folder in (("--out", out), ("--work", args.work)):
        if folder is not None and not may_be_written(folder, args.root):
            raise Refused(f"{name} {NOT_IGNORED}")
    target, beside = out / args.release_id, out / f"{args.release_id}{BESIDE}"
    for folder in (target, beside, out / f"{args.release_id}{INCOME_FOLDER}"):
        if folder.exists():
            raise Refused(
                f"the folder {folder.name} is there already. A release is never written over: "
                "a correction is a new release, under a new id"
            )
    # What a person decided is read first: a change that cannot be built stops the build
    # before the store is looked for, and before a file of a publisher is opened. So a
    # file of changes is held to the copy that was published whatever kind of store is
    # named, and where none is.
    changed = _changed(args)
    try:
        store = store_from_environment(environment)
    except StoreError as error:
        raise Refused(str(error)) from None
    registry = load(args.registry)

    drafted = _drafted(args)
    lock, receipts, without, taken = _sealed(args, registry, store, drafted, changed)
    # The cost is asked for only where a list of the build names a file of prices, and the
    # rent only where one names the workbook of rents.
    of_the_lists = {file.source_id for file in _listed(_lists(args))}
    priced_from = of_the_lists & set(PRICED_FROM)
    asked = bool(priced_from)
    let_asked = bool(of_the_lists & set(LET_FROM))
    print(
        public(
            "seal",
            "ok",
            release=lock.release_id,
            inputs=len(lock.inputs),
            missing=len(without),
            **taken_counted(taken),
            development=int(lock.development),
            lock_sha256=lock.digest(),
        )
    )
    if changed is not None:
        said = changed.record()
        print(
            public(
                "changes",
                "ok",
                release=args.release_id,
                lines=said["lines"],
                stand=said["stand"],
                applied=len(decided.applied(changed.lines, decided.APPLIED)),
                changes_sha256=said["sha256"],
            )
        )
    for note in taken_in_words(taken):
        print(note, file=sys.stderr)
    for file in without:
        print(
            f"note: {file.item} of the list has no receipt, so it is no part of this build. "
            f"{TO_DO['listed_file_has_a_receipt']}",
            file=sys.stderr,
        )

    with tempfile.TemporaryDirectory(prefix="burro-preview-") as scratch:
        inputs = Inputs(
            registry=registry,
            receipts=receipts,
            store=store,
            work=args.work or Path(scratch),
            lock=lock,
        )
        if store.kind != FolderStore.kind:
            # A file is read with no socket open, and this store is reached over a network.
            copied, size = inputs.copy_out()
            print(public("store", "ok", kind=store.kind, files=copied, bytes=size), flush=True)
        with sockets_refused():
            found = spine.build(inputs)
            outlines = outline.build(inputs, found)
            measured_land = land.build(inputs, found)
            by_source = {opened.receipt.source_id: opened.receipt for opened in inputs.opened}
            naming = _named(drafted, found, outlines, inputs) if drafted is not None else None
            drawn = Drawn(
                found, outlines, by_source[spine.LOOKUP], by_source[outline.BOUNDARIES], naming
            )
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
                )
            )
            if naming is not None:
                print(
                    public(
                        "names",
                        "ok",
                        release=args.release_id,
                        areas=naming.areas,
                        named=len(naming.bears),
                        files=len(naming.files),
                    )
                )
            # The table of tiers, with what a person decided of it laid over it. With no
            # file of changes it is the table of the repository, as before.
            tiers = decided.table_with(
                brand_table.the_table(), changed.lines if changed is not None else ()
            )
            with brand_table.using(tiers):
                carried, left_out = _measured(inputs, Ground(found, measured_land))
                _chains_are_seen(changed, inputs, found)
            costed, cost_gone = (
                _costed(inputs, found, read_receipts(args.receipts), priced_from)
                if asked
                else (None, None)
            )
            let, let_gone = _let(inputs, found) if let_asked else (None, None)
            # Household income is read where a list of the build names its workbook and
            # the workbook has a receipt. It is shown beside the release, and is no measure.
            estimated = (
                household_income.build(inputs, found)
                if any(receipt.source_id == household_income.SOURCE for receipt in receipts)
                else None
            )
            named, not_named = _places(inputs, found)
    for one in carried:
        figures = list(one.measured.worked.values())
        print(
            public(
                "derive",
                "ok",
                feature=one.feature,
                source=one.measure.source,
                areas=len(figures),
                values=sum(figure.value is not None for figure in figures),
                files=len(one.measured.files),
            )
        )
    for gone in left_out:
        print(
            public(
                "derive",
                "skipped",
                feature=gone.measure.feature,
                source=gone.measure.source,
                **{gone.rule: 1},
            )
        )
        print(
            f"note: {gone.measure.feature} is left out of the release. It {gone.why}. {gone.to_do}",
            file=sys.stderr,
        )
    if costed is not None:
        print(
            public(
                "cost",
                "ok",
                source=costed.source,
                areas=len({row.area_id for row in costed.rows}),
                rows=len(costed.rows),
                files=len(costed.files),
            )
        )
    if cost_gone is not None:
        print(public("cost", "skipped", source=cost_gone.source, **{cost_gone.rule: 1}))
        print(
            f"note: what a home sells for is left out of the release. "
            f"{PRICED_FROM[cost_gone.source]} {cost_gone.why}. {' '.join(cost_gone.waits_on)}",
            file=sys.stderr,
        )
    if let is not None:
        print(
            public(
                "cost",
                "ok",
                source=let.source,
                areas=len({row.area_id for row in let.rows}),
                rows=len(let.rows),
                files=len(let.files),
            )
        )
    if let_gone is not None:
        print(public("cost", "skipped", source=let_gone.source, **{let_gone.rule: 1}))
        print(
            f"note: what a home lets for is left out of the release. "
            f"{LET_FROM[let_gone.source]} {let_gone.why}. {' '.join(let_gone.waits_on)}",
            file=sys.stderr,
        )
    if named is not None:
        print(
            public(
                "places",
                "ok",
                source=station_places.SOURCE,
                rows=len(named.places),
                areas=len(named.homes_at),
                files=len(named.files),
            )
        )
    else:
        print(public("places", "skipped", source=station_places.SOURCE, **{str(not_named): 1}))
        print(
            "note: no place to reach is named in the release, so no journey can be asked for. "
            f"The file of London's stops {MEANING[str(not_named)]}.",
            file=sys.stderr,
        )
    if not carried:
        raise Refused("no measure could be worked out, so there is no release to write")

    try:
        release = release_of(
            args.release_id,
            args.built_at,
            drawn,
            carried,
            registry,
            _both(costed, let),
            named,
            changes=changed.lines if changed is not None else (),
            changes_sha256=(
                hashlib.sha256(changed.content).hexdigest() if changed is not None else None
            ),
        )
        written = _opened(release)
        evidence = evidence_of(written, drawn, carried, _both(costed, let), named)
    except ValidationError as error:
        raise Refused(f"the release could not be put together: {in_words(error)}") from None
    except decided.ChangesError as error:
        raise Refused(
            f"the file of changes cannot be built on: line {error.line} breaks the rule "
            f"{error.rule}. Look at the line at the panel, or take it back there"
        ) from None

    files = packed(release)
    print(
        public(
            "assemble",
            "ok",
            release=args.release_id,
            areas=len(written.neighbourhoods),
            measures=len(written.metrics),
            files=len(files),
            manifest_sha256=hashlib.sha256(files[MANIFEST]).hexdigest(),
        )
    )
    committed = {receipt.file_id: receipt for receipt in receipts}
    findings = unevidenced(
        written, evidence, lock, registry, behind(), TAGGED.derivation_id, committed
    )
    checked = public(
        "check",
        "failed" if findings else "ok",
        release=args.release_id,
        facts=len(dict(served(written))),
        rows=len(evidence.rows),
        files=len(evidence.receipts),
        findings=len(findings),
        evidence_sha256=evidence.digest(),
        **counted(findings),
    )
    print(checked)
    if findings:
        facts = "1 fact" if len(findings) == 1 else f"{len(findings)} facts"
        print(
            f"error: {facts} may not be served, so nothing was written. Each has no evidence "
            "behind it, or evidence that may not stand behind it",
            file=sys.stderr,
        )
        return 1

    written = write_release(release, out, registry)
    if estimated is not None:
        try:
            shown = household_income.income_of(args.release_id, estimated, registry)
            write_income(shown, written, out, registry)
        except IncomeError as error:
            raise Refused(income_in_words(error, out)) from None
        print(
            public(
                "income",
                "ok",
                source=household_income.SOURCE,
                areas=len(estimated.areas),
                values=estimated.given,
                files=1,
            )
        )
    homes = drawn.homes()
    coverage = cover(written, evidence, homes)
    beside.mkdir(parents=True)
    hashes = Hashes(
        release_id=args.release_id,
        manifest_sha256=hashlib.sha256(files[MANIFEST]).hexdigest(),
        evidence_sha256=evidence.digest(),
        lock_sha256=lock.digest(),
    )
    kept = {
        LOCK: lock.canonical(),
        EVIDENCE: evidence.canonical(),
        HASHES: canonical_json(hashes.model_dump(mode="json")),
        COVERAGE: coverage.canonical(),
        REPORT: report(
            coverage,
            [
                *(gone.reported() for gone in left_out),
                *(cost_gone.reported() if cost_gone is not None else ()),
                *(let_gone.reported() if let_gone is not None else ()),
            ],
        ).encode(),
        HOMES: canonical_json(homes),
        BUILD: canonical_json(
            _build_record(
                args,
                lock,
                without,
                carried,
                left_out,
                evidence,
                _cost_record(asked, costed, cost_gone, let),
                _names_record(drawn.naming),
                _places_record(named, not_named),
                _income_record(estimated),
                changed,
                _rent_record(let, let_gone) if let_asked else None,
            )
        ),
    }
    if drawn.naming is not None:
        kept[NAMES] = names_table(drawn, registry)
    for name, content in kept.items():
        (beside / name).write_bytes(content)
    print(f"{public('report', 'ok')} {summary(coverage)}")
    return 0


def build(prog: str = PROG) -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The step assemble owns, as the command line takes it: the whole, and the step."""
    whole = argparse.ArgumentParser(
        prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = whole.add_subparsers(dest="command", required=True)
    step = {step.name: add_step(commands, step, prog) for step in STEPS}
    preview = step["preview"]
    preview.add_argument(
        "--release-id",
        required=True,
        metavar="ID",
        help="the release that is built, as lon-2026-10-02-01",
    )
    preview.add_argument(
        "--built-at",
        required=True,
        metavar="TIME",
        help="when the build is said to be made, in UTC, as 2026-10-02T09:00:00Z. It is an "
        "input and is never read from the clock, so that a build repeats",
    )
    preview.add_argument(
        "--out",
        required=True,
        type=Path,
        metavar="FOLDER",
        help="the folder the release and what stands beside it are written under, each in a "
        "folder of its own that must not be there yet",
    )
    preview.add_argument(
        "--list",
        action="append",
        metavar="LIST",
        help="a list of the build, as fetch takes it: a name, or the path of a .toml file "
        f"shaped like one. Give it once for each list the build takes (default: {FIRST_LIST})",
    )
    add_edition(preview)
    preview.add_argument(
        "--names",
        type=Path,
        metavar="FOLDER",
        help="a draft of London's named areas: the folder a draft was written to, or the "
        "gazetteer the review desk compiled from it. Each area then bears the name of the "
        "drafted neighbourhood that holds most of its output areas. Without it each area is "
        "under its publisher's label",
    )
    # A build is given a file of changes, or the place one is published to, and never both.
    changes = preview.add_mutually_exclusive_group()
    changes.add_argument(
        "--changes",
        type=Path,
        metavar="FILE",
        help="a file of changes: what a person decided at the panel of the review desk, one "
        "line for each change. The lines that stand are laid over the catalogue. Without it "
        "the build is what it was",
    )
    changes.add_argument(
        "--published-changes",
        type=Path,
        metavar="FILE",
        help="the place the review desk publishes the founder's file of changes to. Where the "
        "repository tracks a file there it is taken as --changes takes one. Where it tracks "
        "none the build is what it is with no file",
    )
    preview.add_argument(
        "--receipts",
        type=Path,
        default=Path(RECEIPTS_FOLDER),
        help=f"the folder of receipts. It may hold the receipts of other lists, which are "
        f"left alone (default: {RECEIPTS_FOLDER})",
    )
    preview.add_argument(
        "--registry",
        type=Path,
        help="the licence registry, a file or a folder (default: this repository's)",
    )
    preview.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="the top of the repository, where the commit is read and saved licence "
        "evidence is looked for (default: here)",
    )
    preview.add_argument(
        "--commit",
        help="the commit of the code that builds, in full. In a repository it is read, and "
        "this is refused unless it is the commit that is checked out. It is needed only "
        "where there is no repository to read",
    )
    preview.add_argument(
        "--packages",
        type=Path,
        metavar="FILE",
        help="the package lockfile, if one is committed. Without it the build is a "
        "development build, which is never served to the public",
    )
    preview.add_argument(
        "--work",
        type=Path,
        metavar="FOLDER",
        help="where the copies of the files are put while they are read, and left. Without it "
        "they are put in a folder that is removed when the step ends",
    )
    return whole, step


def parsed(argv: Sequence[str] | None = None, prog: str = PROG) -> argparse.Namespace:
    """The arguments of the step. Stops with the step's usage if they are not ones it takes."""
    whole, _ = build(prog)
    args = whole.parse_args(argv)
    if not named_once(args):
        whole.error("preview takes --edition once for each file")
    return args


def main(argv: Sequence[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    args = parsed(argv)
    try:
        return _preview(args, os.environ if environment is None else environment)
    except LockError as error:
        named = {"file_id": error.subject} if FILE_ID.fullmatch(error.subject) else {}
        print(public("assemble", "refused", **{error.rule: 1}, **named))
        print(f"error: {in_full(error)}", file=sys.stderr)
    except (Refused, RegistryError, UnreadableRelease) as error:
        print(public("assemble", "unreadable"))
        print(f"error: {error}", file=sys.stderr)
    except ReleaseError as error:
        print(public("assemble", "refused"))
        print(f"error: the release was refused: {error.file} [{error.rule}]", file=sys.stderr)
    except StoreError as error:
        # The store was named, and then did not answer or refused. Why is said by the
        # number fetch gives a store that fails. What a store's refusal says is fixed
        # words and a status: it names no address, no bucket and no key.
        print(public("assemble", "failed", why=Why.STORE.value))
        print(f"error: {error}. {WHAT_TO_DO_OF_THE_STORE}", file=sys.stderr)
    except OSError as error:
        print(public("assemble", "unreadable"))
        print(f"error: cannot read or write a file: {error.strerror}", file=sys.stderr)
    return 2
