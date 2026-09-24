"""The steps of the command line that evidence owns: seal, check and coverage.

    python -m burro_pipeline seal --release-id ID --built-at TIME --list LIST --vault-listing FILE
    python -m burro_pipeline check FOLDER --evidence FILE
    python -m burro_pipeline coverage FOLDER --evidence FILE --out REPORT

What it prints may be read by anyone. On standard output it prints one line of
`key=value` pairs: the step, its status, counts and hashes. That is the form
`tools/public_log.py` lets through to a public log. Why a step was refused is
said in words on standard error, which a public log withholds. Neither ever
holds a row, a key, the address of the vault or the name of an area. What is
longer than a line is written to a file the caller names.
"""

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from burro_core.release import EVIDENCE, HASHES, LOCK, MANIFEST, Hashes, InMemoryRelease
from pydantic import ValidationError

from burro_pipeline.command import PROG, Step, add_step
from burro_pipeline.evidence.coverage import LeftOut, cover, report, summary
from burro_pipeline.evidence.lock import (
    LOCKS_FOLDER,
    MEANING,
    LockError,
    Taken,
    read_lock,
    read_receipts,
    seal,
    take,
)
from burro_pipeline.evidence.made_up import made_up_evidence
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER
from burro_pipeline.evidence.record import FILE_ID_PATTERN, given, in_words
from burro_pipeline.evidence.served import counted, served, unevidenced
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.fetch.sources import FetchList, ListError, load_list
from burro_pipeline.registry import RegistryError, load
from burro_pipeline.release.read import UnreadableRelease, read_release

FILE_ID = re.compile(FILE_ID_PATTERN)
# The step of a build each command is, as the pipeline design names them.
STEP = {"seal": "seal", "check": "check", "coverage": "report"}

SYNTHETIC = "data/fixtures/synthetic/syn-2026-09-23-01"
# Where the record of a build says what it left out.
LEFT_OUT = "measures_left_out"
UNREADABLE = "An input could not be read, or an argument is wrong. The reason is said in words"
REFUSED = "A file may not be in the build, or an input could not be read. The line names the rule"
MADE_UP = """\
With --made-up it runs on a synthetic release and on evidence made up for it,
so that the step can be tried before any file is fetched."""
# What `seal` and `preview` both say of a file that states its own edition.
OWN_EDITION = """\
A file that states its own edition may have a receipt for each of several
editions: its publisher puts another file at the same address, and each that
was fetched stands beside the last. The build takes one of them. With
--edition ITEM=EDITION it takes the edition that is named, of the file the
list calls ITEM, written as its receipt writes it. Told nothing, it takes the
newest, by the day the file states of itself. The lock says which edition was
taken of each such file, so a later build that is given the editions a lock
names reads the files that lock names, whatever has arrived since. Two
receipts of one file that state one edition stop the build."""

STEPS = (
    Step(
        "seal",
        "Write the lock of a build: every input by its hash, and the commit of the code",
        f"""\
Run it after the files are fetched and before anything is built from them. A
build then reads nothing the lock does not name.

Run it at the top of the repository, with everything committed. The lock
names the code by its commit, which is read from the repository: the commit
that is checked out. A working copy with changes is refused, because no
commit names the code it holds. Git's own files are read, and no program is
run. A file that git does not track is not looked at.

The repository is looked for in the folder --root names and in every folder
above it, as git looks for it. So in a folder inside the repository the step
reads the same commit, and refuses the same changes, as at the top of it.

It takes the list of the build, which is the list the files were fetched
from. Every file the list names must have its receipt in the folder, and the
folder must hold no receipt that the list does not name. So a receipt of an
edition that is no longer listed is moved out of the folder first. It stays
in the history of the repository.

{OWN_EDITION}

For each receipt, in this order: the licence registry is asked again whether
the file may be used as its receipt says, because a source can lose its
approval after it was fetched. Then the vault's listing must hold the file, at
the size the receipt gives. Then any licence evidence the receipt names must
be saved under registry/evidence/. It stops at the first file that fails, and
names it by its file id and the rule it broke.

Reads the list, the receipts, the vault's listing and the licence registry.
Make the listing first, with `{PROG} held --out listing.json`.
Reaches no network and no store.

Writes the lock, named for the release, under --out. Commit it with the
receipts: to approve a release is to commit its lock.

{MADE_UP}""",
        (
            "--release-id lon-2026-10-02-01 --built-at 2026-10-02T09:00:00Z "
            "--list m1 --vault-listing listing.json",
            "--release-id lon-2026-10-02-01 --built-at 2026-10-02T09:00:00Z "
            "--list m2-places --vault-listing listing.json "
            '--edition fsa-camden="extract of 2026-09-16"',
            f"--made-up {SYNTHETIC} --out scratch/locks",
        ),
        {0: "The lock was written", 2: REFUSED},
    ),
    Step(
        "check",
        "Fail if a fact of a release has no evidence behind it",
        f"""\
Run it on a release before it is served. It asks the ranking engine for every
fact the release would show, and looks for the row of evidence behind each: a
row with a figure, resting on a file from every source the fact cites. Every
file a row rests on must be in the lock of the build. A release that is not
made up is not checked without its lock.

The row of a measure or of a tag holds the figure, and the release is held to
it. A release that is not made up is held to the hashes of its build too: the
manifest, the evidence and the lock must each be as they were written.

Every method the evidence holds must name a module of the pipeline or of core
that is there, so that a person can read how a figure was worked out.

No row may rest on a file that is kept for the audit or for the census table:
one fetched for either, or one whose source the licence registry holds for
either. Such a row is found, and so is every fact that is served from it.

Reads the release, its evidence, the lock of its build and the licence
registry. Writes nothing, unless --list names a file for the facts it found.
Reaches no network.

Prints one line: how many facts, rows and files, and how many findings by rule.
Which facts were found is never printed: it goes to the file --list names.

{MADE_UP}""",
        (
            f"{SYNTHETIC} --made-up",
            "releases/lon-2026-10-02-01 --evidence evidence.json "
            "--lock data/locks/lon-2026-10-02-01.json --hashes hashes.json --list findings.txt",
        ),
        {0: "Every fact has evidence behind it", 1: "Some fact has none", 2: UNREADABLE},
    ),
    Step(
        "coverage",
        "Write the coverage report of a release: what is there, and what is missing",
        f"""\
Run it on a release before it is approved. For every area and every measure it
gives one of seven states, and the report counts them by source, by measure
and by area, and lists every gap. Nothing is filled in: a figure that is
missing is counted as missing.

A build may work a measure out and leave it out of the release. Give --build
the record the build wrote beside the release, and the report says of each
such measure which rule kept it out and what it waits on. Without it such a
measure reads as one that no step works out.

Reads the release, its evidence if one is given, and the record of the build
if one is given. Reaches no network.

Writes the report, in Markdown, to the file --out names. The report names
areas, so it is written to a file and never printed. Prints one line of counts.

{MADE_UP}""",
        (
            f"{SYNTHETIC} --made-up --out coverage.md",
            "releases/lon-2026-10-02-01 --evidence evidence.json --out coverage.md "
            "--homes homes.json --json coverage.json --build build.json",
        ),
        {0: "The report was written", 2: UNREADABLE},
    ),
)


# What a person can do about each refusal of the lock. It is said after what is wrong.
TO_DO = {
    "input_is_locked": "Seal the lock again if the file belongs in the build",
    "input_has_one_receipt": f"Fetch the file, or bring its receipt back with `{PROG} "
    "receipts`. If two editions of it have a receipt, move the one that is no part of this "
    "build out of the folder",
    "input_is_as_described": f"See what the file holds with `{PROG} describe`. If its "
    "publisher has changed its layout, the step that reads it is changed to suit",
    "measure_is_as_core_says": "Change the catalogue in core or the measure, in a change a "
    "person reads. Until then the measure is left out of the release",
    "measure_has_a_figure": f"See what the file holds with `{PROG} describe`. Until an area "
    "has a figure the measure is left out of the release",
    "measure_is_not_held_back": "Settle what the measure says holds it back, and take that out "
    "of its module in a change a person reads. Until then the measure is left out of the "
    "release",
    "gate_refuses": "The registry entry says what would change this. Until it does, take the "
    "receipt out of the build",
    "file_is_for_the_product": "Take its receipt out of the build. A file about residents is "
    "kept in a store of its own, and no figure of the product rests on it",
    "real_build_needs_a_registry": "Give --registry, or run the step in the repository",
    "listed_file_has_a_receipt": f"Fetch the file, or bring its receipt back with `{PROG} "
    "receipts`. A file has a receipt only once the list states its edition and its period. "
    "If the file is no part of this build, take it out of the list",
    "receipt_is_listed": "If the file is part of this build, name it in the list. If it is "
    "not, move its receipt out of the folder: it stays in the history of the repository",
    "listed_file_has_one_receipt": "Move the receipt of the file that is no part of this build "
    "out of the folder",
    "named_edition_has_a_receipt": "Give --edition the name the list gives the file, and an "
    "edition as a receipt of that file writes it. Or leave --edition out, and the build takes "
    "the newest",
    "real_release_needs_a_lock": "Give --lock, with the lock that was sealed for the build",
    "real_release_needs_a_registry": "Give --registry, or run the step in the repository",
    "real_release_needs_its_hashes": "Give --hashes, with the hashes the build wrote beside "
    "the release",
    "build_is_as_it_was_written": "Build the release again under a new id. A release, its "
    "evidence and its lock are never changed once written",
    "file_is_in_the_vault": f"Make the listing again with `{PROG} held --out FILE`. If the file "
    "is not in it, fetch the file again",
    "licence_evidence_is_saved": "Save a dated copy of the terms there, under the name the "
    "receipt gives",
    "one_receipt_for_a_file": "Keep the first receipt of the file, and delete the other",
    "lock_has_an_input": "Fetch the files of the build, and bring their receipts to the "
    "folder of receipts",
    "made_up_is_consistent": "A build is made of fetched files or of made-up ones, never of both",
    "commit_is_named": "Run the step at the top of the repository, or name the repository "
    "with --root. Give --commit only where no folder above holds a repository to read",
    "commit_is_checked_out": "Leave --commit out, and the commit is read. Or check out the "
    "commit that is meant",
    "tree_has_no_changes": "Commit the changes or put them aside, and seal again. `git status` "
    "shows them",
    "repository_is_read": "See that `git status` runs there. A repository that git reads and "
    "this step does not is sealed from a fresh clone",
    "receipt_is_valid": "A receipt is written by fetch and is never edited. Restore it as it "
    "was committed, or fetch the file again",
    "lock_is_valid": "Look at --release-id, --built-at and --commit against the step's help, "
    "or seal the lock again",
}


class Refused(Exception):
    """An input could not be read. Says which and why, and never what it holds."""


def in_full(error: LockError) -> str:
    """A refusal of the lock on one line: what is wrong, what to do, and the rule's name."""
    wrong = str(error).removesuffix(f" [{error.rule}]").rstrip(".")
    return f"{wrong}. {TO_DO[error.rule]} [{error.rule}]"


def public(step: str, status: str, **counted: object) -> str:
    """One line that may be read by anyone: the step, its status, counts and hashes."""
    pairs = {"step": step, "status": status} | counted
    return " ".join(f"{key}={value}" for key, value in pairs.items())


def an_edition(given: str) -> tuple[str, str]:
    """What `--edition` names: a file of the list, and the edition to take of it."""
    item, _, edition = given.partition("=")
    if not item or not edition:
        # What was given is not repeated: it may be anything.
        raise argparse.ArgumentTypeError(
            "it is given as ITEM=EDITION: the name the list gives the file, and the edition "
            "as a receipt of the file writes it"
        )
    return item, edition


def add_edition(step: argparse.ArgumentParser) -> None:
    """Let a step be told which edition to take of a file that states its own."""
    step.add_argument(
        "--edition",
        action="append",
        type=an_edition,
        metavar="ITEM=EDITION",
        help="the edition to take of a file that states its own: the name the list gives "
        'the file, and the edition as its receipt writes it, as fsa-camden="extract of '
        '2026-09-16". Give it once for each file. Of a file that is not named the newest '
        "edition is taken",
    )


def editions_of(args: argparse.Namespace) -> dict[str, str]:
    """What a build was told to take, by the name the list gives each file."""
    return dict(args.edition or ())


def named_once(args: argparse.Namespace) -> bool:
    """Whether `--edition` names each file once. Named twice, nothing says which is meant."""
    return len(editions_of(args)) == len(args.edition or ())


def taken_counted(taken: Sequence[Taken]) -> dict[str, int]:
    """What a line says of the files that state their own edition. It names none of them.

    How many the build took, how many of those it was told to take, and how
    many receipts of other editions it passed over. A build that reads no
    such file says nothing of them, and prints as it did before there were any.
    """
    if not taken:
        return {}
    return {
        "own_edition": len(taken),
        "named": sum(one.named for one in taken),
        "passed_over": sum(len(one.passed_over) for one in taken),
    }


def taken_in_words(taken: Sequence[Taken]) -> list[str]:
    """A note for each file of which the build took one edition of several, or a named one."""
    notes: list[str] = []
    for one in taken:
        if not (one.named or one.passed_over):
            continue
        editions = len(one.passed_over) + 1
        held = "1 edition" if editions == 1 else f"{editions} editions"
        how = "the one that was named" if one.named else "the newest"
        notes.append(
            f"note: {one.item} has {held} with a receipt. This build takes {how}, and its "
            f"lock says which. To take another, give --edition {one.item}=EDITION"
        )
    return notes


def _json(path: Path, what: str) -> object:
    try:
        return json.loads(path.read_bytes())
    except OSError as error:
        raise Refused(f"cannot read {what} {path.name}: {error.strerror}") from None
    except ValueError:
        raise Refused(f"{what} {path.name} is not valid JSON") from None


def _evidence(args: argparse.Namespace, release: InMemoryRelease) -> Evidence:
    if args.made_up:
        try:
            return made_up_evidence(release)
        except ValueError as error:
            raise Refused(str(error)) from None
    try:
        return Evidence.model_validate(_json(args.evidence, "evidence"))
    except ValidationError as error:
        raise Refused(f"{args.evidence.name} is not valid evidence: {in_words(error)}") from None


def _numbers(path: Path, what: str) -> dict[str, int]:
    found = _json(path, what)
    if not isinstance(found, dict) or not all(
        isinstance(count, int) for count in cast(dict[str, object], found).values()
    ):
        raise Refused(f"{what} {path.name} is not a table of whole numbers")
    return cast(dict[str, int], found)


def _list(which: str) -> FetchList:
    """The list of a build, named as fetch names it: by its name, or by the path of a file."""
    try:
        return load_list(Path(which) if which.endswith(".toml") else which)
    except ListError as error:
        raise Refused(f"the list of the build cannot be read: {error}") from None


def _seal(args: argparse.Namespace) -> int:
    editions = editions_of(args)
    if args.made_up:
        release = read_release(args.made_up)
        receipts = made_up_evidence(release).receipts
        release_id, built_at = release.manifest.release_id, release.manifest.built_at
        registry, vault, listed = None, dict[str, int](), None
    else:
        listing: Path = args.vault_listing
        if not listing.is_file():
            made_by = f"{PROG} held --out {listing.name}"
            raise Refused(f"there is no listing at {listing.name}. Make it with `{made_by}`")
        listed = _list(args.list).files
        receipts = read_receipts(args.receipts)
        release_id, built_at = args.release_id, args.built_at
        registry, vault = load(args.registry), _numbers(listing, "the vault's listing")
    packages = hashlib.sha256(args.packages.read_bytes()).hexdigest() if args.packages else None
    lock = seal(
        release_id,
        built_at,
        args.commit,
        receipts,
        vault,
        registry,
        args.root,
        packages,
        listed=listed,
        editions=editions,
    )
    taken, _ = take(receipts, listed or (), editions)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / lock.path().name).write_bytes(lock.canonical())
    print(
        public(
            "seal",
            "ok",
            release=lock.release_id,
            inputs=len(lock.inputs),
            **taken_counted(taken),
            development=int(lock.development),
            lock_sha256=lock.digest(),
        )
    )
    for note in taken_in_words(taken):
        print(note, file=sys.stderr)
    return 0


def _sha256(path: Path, what: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise Refused(f"cannot read {what} {path.name}: {error.strerror}") from None


def _hold_to_the_hashes(args: argparse.Namespace, release: InMemoryRelease) -> None:
    """Refuse a release that is not made up unless it is as the hashes of its build say."""
    release_id = release.manifest.release_id
    if args.lock is None:
        raise LockError("real_release_needs_a_lock", release_id)
    if args.hashes is None:
        raise LockError("real_release_needs_its_hashes", release_id)
    try:
        hashes = Hashes.model_validate(_json(args.hashes, "the hashes"))
    except ValidationError:
        raise Refused(f"{args.hashes.name} is not the hashes of a build") from None
    held = (
        (HASHES, hashes.release_id, release_id),
        (MANIFEST, hashes.manifest_sha256, _sha256(args.folder / MANIFEST, "the manifest")),
        (EVIDENCE, hashes.evidence_sha256, _sha256(args.evidence, "evidence")),
        (LOCK, hashes.lock_sha256, _sha256(args.lock, "the lock")),
    )
    for name, written, found in held:
        if written != found:
            raise LockError("build_is_as_it_was_written", name)


def _check(args: argparse.Namespace) -> int:
    release = read_release(args.folder)
    if not release.manifest.synthetic:
        _hold_to_the_hashes(args, release)
    evidence = _evidence(args, release)
    # A made-up release cites no source, so no registry is read for it.
    registry = None if release.manifest.synthetic else load(args.registry)
    lock = read_lock(args.lock) if args.lock else None
    findings = unevidenced(release, evidence, lock, registry)
    if args.list:
        args.list.write_text("".join(f"{finding}\n" for finding in findings), encoding="utf-8")
    elif findings:
        # Which facts they are is never printed. A person is told how to have them written down.
        facts = "1 fact" if len(findings) == 1 else f"{len(findings)} facts"
        to_do = "Run it again with --list FILE to have each written down, with the rule it breaks"
        print(f"error: {facts} may not be served. {to_do}", file=sys.stderr)
    print(
        public(
            "check",
            "failed" if findings else "ok",
            release=release.manifest.release_id,
            facts=len(dict(served(release))),
            rows=len(evidence.rows),
            files=len(evidence.receipts),
            findings=len(findings),
            evidence_sha256=evidence.digest(),
            **counted(findings),
        )
    )
    return 1 if findings else 0


def _left_out(path: Path) -> list[LeftOut]:
    """What a build worked out and left out of its release, from the record it wrote."""
    what = "the record of the build"
    found = _json(path, what)
    listed = cast(dict[str, object], found).get(LEFT_OUT) if isinstance(found, dict) else None
    if not isinstance(listed, list):
        raise Refused(f"{what} {path.name} does not say what was left out")
    said: list[LeftOut] = []
    for one in cast(list[object], listed):
        row = cast(dict[str, object], one) if isinstance(one, dict) else {}
        feature, rule, waits_on = row.get("feature_id"), row.get("rule"), row.get("waits_on")
        if not (isinstance(feature, str) and isinstance(rule, str) and rule in MEANING):
            raise Refused(f"{what} {path.name} names a measure left out by no rule of a build")
        sentences = cast(list[object], waits_on) if isinstance(waits_on, list) else []
        if not all(isinstance(sentence, str) for sentence in sentences):
            raise Refused(f"{what} {path.name} does not say in words what a measure waits on")
        waits = tuple(str(sentence) for sentence in sentences)
        said.append(LeftOut(f"feature/{feature}", rule, MEANING[rule], waits))
    return said


def _coverage(args: argparse.Namespace) -> int:
    release = read_release(args.folder)
    evidence = _evidence(args, release) if args.made_up or args.evidence else None
    homes = _numbers(args.homes, "the count of homes") if args.homes else None
    left_out = _left_out(args.build) if args.build else []
    try:
        coverage = cover(release, evidence, homes)
        written = report(coverage, left_out)
    except ValueError as error:
        raise Refused(str(error)) from None
    args.out.write_text(written, encoding="utf-8")
    if args.json:
        args.json.write_bytes(coverage.canonical())
    print(f"{public('report', 'ok')} {summary(coverage)}")
    return 0


def build(prog: str = PROG) -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The steps evidence owns, as the command line takes them: the whole, and each step of it."""
    whole = argparse.ArgumentParser(
        prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = whole.add_subparsers(dest="command", required=True)
    step = {step.name: add_step(commands, step, prog) for step in STEPS}

    sealing = step["seal"]
    sealing.add_argument(
        "--release-id", metavar="ID", help="the release the lock is for, as lon-2026-10-02-01"
    )
    sealing.add_argument(
        "--built-at",
        metavar="TIME",
        help="when the build is said to be made, in UTC, as 2026-10-02T09:00:00Z. It is an "
        "input and is never read from the clock, so that a build repeats",
    )
    sealing.add_argument(
        "--commit",
        help="the commit of the code that builds, in full. In a repository it is read, and "
        "this is refused unless it is the commit that is checked out. It is needed only "
        "where there is no repository to read",
    )
    sealing.add_argument(
        "--list",
        metavar="LIST",
        help="the list of the build, as fetch takes it: a name, as m1, or the path of a "
        ".toml file shaped like it",
    )
    add_edition(sealing)
    sealing.add_argument(
        "--receipts",
        type=Path,
        default=Path(RECEIPTS_FOLDER),
        help=f"the folder of receipts, which holds the receipts of the list and no other "
        f"(default: {RECEIPTS_FOLDER})",
    )
    sealing.add_argument(
        "--vault-listing",
        type=Path,
        metavar="FILE",
        help=f"the size of each file in the store by its key, as `{prog} held --out` writes it",
    )
    sealing.add_argument(
        "--registry",
        type=Path,
        help="the licence registry, a file or a folder (default: this repository's)",
    )
    sealing.add_argument(
        "--packages",
        type=Path,
        metavar="FILE",
        help="the package lockfile, if one is committed. Without it the lock is of a "
        "development build, which is never served",
    )
    sealing.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="the top of the repository, where saved licence evidence is looked for. The "
        "commit is read from the repository this folder is in (default: here)",
    )
    sealing.add_argument(
        "--out",
        type=Path,
        default=Path(LOCKS_FOLDER),
        help=f"the folder the lock is written to (default: {LOCKS_FOLDER})",
    )
    sealing.add_argument(
        "--made-up",
        type=Path,
        metavar="FOLDER",
        help="a synthetic release: seal the made-up files behind it, in place of --release-id, "
        "--built-at, --list and --vault-listing",
    )

    for name in ("check", "coverage"):
        command = step[name]
        command.add_argument("folder", type=Path, help="the folder of the release")
        command.add_argument(
            "--evidence", type=Path, metavar="FILE", help="the evidence of the release, as JSON"
        )
        command.add_argument(
            "--made-up",
            action="store_true",
            help="make the evidence up, for a synthetic release, in place of --evidence",
        )
    step["check"].add_argument(
        "--lock",
        type=Path,
        metavar="FILE",
        help="the lock of the build, to hold every row to. It may be left out for a made-up "
        "release, and for no other",
    )
    step["check"].add_argument(
        "--hashes",
        type=Path,
        metavar="FILE",
        help="the hashes of the build, as the build wrote them beside the release. They may "
        "be left out for a made-up release, and for no other",
    )
    step["check"].add_argument(
        "--registry",
        type=Path,
        help="the licence registry, a file or a folder (default: this repository's). It is "
        "not read for a made-up release",
    )
    step["check"].add_argument(
        "--list", type=Path, metavar="FILE", help="write each fact found, and its rule, here"
    )
    step["coverage"].add_argument(
        "--homes",
        type=Path,
        metavar="FILE",
        help="the count of homes in each area, as JSON. With it a share of the whole is a "
        "share of homes. Without it every area counts once, and the report says so",
    )
    step["coverage"].add_argument(
        "--build",
        type=Path,
        metavar="FILE",
        help="the record the build wrote beside the release, as JSON. With it the report "
        "says why each measure that was worked out and left out is not in the release",
    )
    step["coverage"].add_argument(
        "--out", type=Path, required=True, metavar="REPORT", help="write the report here"
    )
    step["coverage"].add_argument(
        "--json", type=Path, metavar="FILE", help="write every cell of the coverage here, as JSON"
    )
    return whole, step


def parsed(argv: Sequence[str] | None = None, prog: str = PROG) -> argparse.Namespace:
    """The arguments of a step. Stops with the step's usage if they are not ones it takes."""
    whole, _ = build(prog)
    args = whole.parse_args(argv)
    if args.command == "seal":
        real = given(args.release_id, args.built_at, args.list, args.vault_listing)
        if real is None or real == (args.made_up is not None):
            whole.error(
                "seal takes --made-up, or --release-id, --built-at, --list and --vault-listing"
            )
        if args.made_up is not None and args.edition:
            whole.error("seal takes --edition for a list, and a made-up release has none")
        if not named_once(args):
            whole.error("seal takes --edition once for each file")
    elif args.command == "check" and bool(args.made_up) == bool(args.evidence):
        whole.error("check takes --evidence or --made-up")
    elif args.made_up and args.evidence:
        whole.error("coverage takes --evidence or --made-up, and not both")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parsed(argv)
    run = {"seal": _seal, "check": _check, "coverage": _coverage}[args.command]
    step = STEP[args.command]
    try:
        return run(args)
    except LockError as error:
        named = {"file_id": error.subject} if FILE_ID.fullmatch(error.subject) else {}
        print(public(step, "refused", **{error.rule: 1}, **named))
        print(f"error: {in_full(error)}", file=sys.stderr)
    except (Refused, UnreadableRelease, RegistryError) as error:
        print(public(step, "unreadable"))
        print(f"error: {error}", file=sys.stderr)
    except OSError as error:
        print(public(step, "unreadable"))
        print(f"error: cannot read or write a file: {error.strerror}", file=sys.stderr)
    return 2
