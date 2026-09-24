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

from burro_core.release import InMemoryRelease
from pydantic import ValidationError

from burro_pipeline.command import PROG, Step, add_step
from burro_pipeline.evidence.coverage import cover, report, summary
from burro_pipeline.evidence.lock import LOCKS_FOLDER, LockError, read_lock, read_receipts, seal
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
UNREADABLE = "An input could not be read, or an argument is wrong. The reason is said in words"
REFUSED = "A file may not be in the build, or an input could not be read. The line names the rule"
MADE_UP = """\
With --made-up it runs on a synthetic release and on evidence made up for it,
so that the step can be tried before any file is fetched."""

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
            "--lock data/locks/lon-2026-10-02-01.json --list findings.txt",
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

Reads the release, and its evidence if one is given. Reaches no network.

Writes the report, in Markdown, to the file --out names. The report names
areas, so it is written to a file and never printed. Prints one line of counts.

{MADE_UP}""",
        (
            f"{SYNTHETIC} --made-up --out coverage.md",
            "releases/lon-2026-10-02-01 --evidence evidence.json --out coverage.md "
            "--homes homes.json --json coverage.json",
        ),
        {0: "The report was written", 2: UNREADABLE},
    ),
)


# What a person can do about each refusal of the lock. It is said after what is wrong.
TO_DO = {
    "input_is_locked": "Seal the lock again if the file belongs in the build",
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
    "real_release_needs_a_lock": "Give --lock, with the lock that was sealed for the build",
    "real_release_needs_a_registry": "Give --registry, or run the step in the repository",
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
    )
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / lock.path().name).write_bytes(lock.canonical())
    print(
        public(
            "seal",
            "ok",
            release=lock.release_id,
            inputs=len(lock.inputs),
            development=int(lock.development),
            lock_sha256=lock.digest(),
        )
    )
    return 0


def _check(args: argparse.Namespace) -> int:
    release = read_release(args.folder)
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


def _coverage(args: argparse.Namespace) -> int:
    release = read_release(args.folder)
    evidence = _evidence(args, release) if args.made_up or args.evidence else None
    homes = _numbers(args.homes, "the count of homes") if args.homes else None
    try:
        coverage = cover(release, evidence, homes)
    except ValueError as error:
        raise Refused(str(error)) from None
    args.out.write_text(report(coverage), encoding="utf-8")
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
