"""The steps of the command line that kept owns: `keep` and `take`.

    python -m burro_pipeline keep FOLDER --release ID        keep a release that was built
    python -m burro_pipeline take --release ID --out FOLDER  take the release a lock names

The store of releases is named by the environment: BURRO_RELEASES_FOLDER for
a folder, or BURRO_RELEASES_ENDPOINT, BURRO_RELEASES_BUCKET,
BURRO_RELEASES_KEY_ID and BURRO_RELEASES_SECRET for a bucket, and never both.
None of these is ever printed.

What each prints may be read by anyone: lines of `key=value` that hold step
names, the id of a release, counts and hashes. Why a step stopped is said in
words on standard error. Neither holds a figure, the name of a place, a key
or the address of a store.
"""

import argparse
import os
import re
import shutil
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from burro_core.ids import RELEASE_ID_PATTERN, SYNTHETIC_PREFIX
from burro_core.release import BUILD_FOLDER, ReleaseError

from burro_pipeline.command import NOT_IGNORED, PROG, Step, add_step, may_be_written
from burro_pipeline.evidence.cli import public
from burro_pipeline.fetch.store import NotTheFile, StoreError, hash_file
from burro_pipeline.kept.lock import (
    APPROVED,
    BESIDE,
    RELEASE,
    LockRefused,
    approved,
    read_lock,
)
from burro_pipeline.kept.store import (
    FOLDER_VARIABLE,
    S3_VARIABLES,
    Differs,
    Kept,
    kept_from_environment,
)
from burro_pipeline.release.read import IGNORED, UnreadableRelease, read_release, read_served

KEEP, TAKE = "keep", "take"
RELEASE_ID = re.compile(RELEASE_ID_PATTERN)
# The made-up city, as it is committed. An image carries it where no release is approved.
MADE_UP = Path("data/fixtures/synthetic")
# The folders a build writes are each named for the release, with one of `BESIDE` after
# its id. Every build writes the first two. The last is there where a build wrote what is
# shown beside a release and is no part of one.
EVERY_BUILD_WRITES = ("", BUILD_FOLDER)

THE_STORE = f"""\
The store of releases is named by the environment, and is never printed:
  {FOLDER_VARIABLE}    a folder on this machine, or
  {S3_VARIABLES[0]}  the address of an object store, with
  {S3_VARIABLES[1]}, {S3_VARIABLES[2]} and {S3_VARIABLES[3]}
Name one and not the other: with both named, the step does not start. It is
not the store of publishers' files, and no key of that store opens it."""
SAYS_WHICH = "Its first line says which kind of store it was given: a folder, or an object store."
COULD_NOT_START = (
    "It could not start or could not finish: an argument is wrong, a folder could not be "
    "read, or the store did not answer. The reason is said in words"
)

STEPS = (
    Step(
        KEEP,
        "Keep a release that was built, in the store of releases",
        f"""\
Run it once a release is built and checked. A hosted run builds on a machine
that is thrown away, so what it built is kept in a bucket, where the build of
an image can take it from.

A release that is kept is served nowhere for being kept. To approve it is to
commit its lock, which the run shows: {APPROVED}/ID.json.

FOLDER is the folder the build wrote under. It holds the folder of the
release, the folder of its build beside it, named for it with {BUILD_FOLDER}
after, and the folder of what is shown beside the release, with {BESIDE[-1]}
after, where the build wrote one. Each file is kept under releases/, then the
folder it is in, then its own name.

The release is opened first, as the service opens it: held to its manifest
and to the hashes of its build. One that would not be served is not kept.
What stands beside it is kept as the build wrote it: `burro-release check`
holds it to its rules, and is run before this.

A release is never written over. Before anything is kept, every file is
looked for in the store. A file that is kept there already must be the same
bytes, and is left as it is. If one differs nothing is kept, and the step
ends: build again under a new id.

Reaches no publisher. Reaches the store of releases. Reads no publisher's file
and needs no key of the store they are kept in.

{THE_STORE}
{SAYS_WHICH}

Then it prints one line: how many files the release holds, how many of them
this run added, and how many were kept already.""",
        ("data/releases --release lon-2026-10-02-01",),
        {
            0: "Every file of the release is kept",
            1: "Another file is kept under the name of one of them. Nothing was kept",
            2: COULD_NOT_START,
        },
    ),
    Step(
        TAKE,
        "Take the release a committed lock names, to the folder an image is built from",
        f"""\
Run it before the image of the service is built. It fills the folder the
image carries, and nothing else puts a release of London there.

A release of London is taken only where its lock is committed: the file
{APPROVED}/ID.json, which is there because the founder approved the release.
Every file the lock names is copied out of the store of releases and held to
the hash and the size the lock gives. If one differs, or is not there,
nothing is left in the folder, and the step ends. No file is taken that the
lock does not name. What was taken is then opened as the service opens it: a
release it would refuse is not left in the folder either.

With no release named, and no lock committed, it takes the made-up city, as
it is committed under {MADE_UP}, and reaches no store. With no release named
where a lock is committed it stops, and asks which release is meant: name a
release of London, or the made-up city by its own id.

Reaches no publisher. Reaches the store of releases, for a release of London,
and writes nothing to it. For the made-up city it reaches no network.

{THE_STORE}
{SAYS_WHICH}

Writes the folder of the release under --out, and beside it what the release
is served with. --out must be new, or empty: an image carries what is served
and nothing else. It is refused inside the repository, but for data/releases/
and scratch/, which git ignores.

Then it prints one line: the release, how many files it holds, and the hash
of what its lock says. `tools/release_lock.py read` gives the same hash of
the lock, and so does the run that built the release.""",
        (
            "--release lon-2026-10-02-01 --out data/releases/served",
            "--out data/releases/served",
        ),
        {
            0: "The release is in the folder, and every file of it is as its lock says",
            1: "No lock names the release, or a file is not as the lock says. The folder "
            "holds nothing",
            2: COULD_NOT_START,
        },
    ),
)


class Stop(Exception):
    """The step cannot start, or cannot finish. The message is safe to print."""


def _store(environment: Mapping[str, str], step: str) -> Kept:
    """The store of releases the environment names. A line says which kind it is."""
    try:
        store = kept_from_environment(environment)
    except StoreError as error:
        raise Stop(str(error)) from None
    print(f"step={step} kind={store.kind}", flush=True)
    return store


def files_of(folder: Path, release: str) -> dict[str, Path]:
    """Every file a build wrote under a folder, by the name a lock gives it."""
    found: dict[str, Path] = {}
    for suffix in BESIDE:
        within = folder / f"{release}{suffix}"
        if not within.is_dir():
            if suffix not in EVERY_BUILD_WRITES:
                continue
            raise Stop(f"the folder holds no {within.name}, which every build writes")
        for entry in sorted(within.iterdir()):
            if entry.name == IGNORED and entry.is_file() and not entry.is_symlink():
                continue
            if entry.is_symlink() or not entry.is_file():
                raise Stop(f"{within.name} holds what is no file, and a build writes files alone")
            found[f"{within.name}/{entry.name}"] = entry
    return found


def _opened(folder: Path, release: str) -> None:
    """Open a release as the service does, held to the hashes of its build. Raises `Stop`."""
    try:
        read_served(folder / release)
    except UnreadableRelease as error:
        raise Stop(f"the release would not be served: {error}") from None
    except ReleaseError as error:
        raise Stop(f"the release would not be served: {error.file} [{error.rule}]") from None


def _keep(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    release: str = args.release
    if not RELEASE.fullmatch(release):
        raise Stop("--release is not the id of a release of London, as lon-2026-10-02-01")
    files = files_of(args.folder, release)
    _opened(args.folder, release)
    store = _store(environment, KEEP)
    try:
        kept: set[str] = set()
        differing = 0
        for name, path in files.items():
            try:
                if store.holds(name, path):
                    kept.add(name)
            except Differs:
                differing += 1
        if differing:
            print(public(KEEP, "refused", release=release, differs=differing))
            print(
                "error: another file is kept under the name of a file of this release. A "
                "release is never written over, so nothing was kept. Build again under a new id",
                file=sys.stderr,
            )
            return 1
        added = sum(store.put(name, path) for name, path in files.items() if name not in kept)
    except StoreError as error:
        raise Stop(str(error)) from None
    size = sum(path.stat().st_size for path in files.values())
    print(
        public(
            KEEP,
            "ok",
            release=release,
            files=len(files),
            bytes=size,
            new=added,
            same=len(files) - added,
        )
    )
    return 0


def _to_write(args: argparse.Namespace) -> Path:
    out: Path = args.out
    if not may_be_written(out, args.root):
        raise Stop(f"--out {NOT_IGNORED}")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Stop(
            "--out holds something already. An image carries what is served and nothing "
            "else: name a folder that is new, or empty"
        )
    return out


def _take_the_made_up_city(args: argparse.Namespace, release: str | None) -> int:
    """Copy the made-up city from where it is committed. It reaches no store."""
    folder: Path = args.made_up
    found = sorted(path for path in folder.iterdir() if path.is_dir()) if folder.is_dir() else []
    if release is not None:
        found = [path for path in found if path.name == release]
    if len(found) != 1:
        print(public(TAKE, "missing", **({"release": release} if release else {})))
        print(
            "error: the made-up city is not where it is committed, or another id was named "
            f"than the one it is committed under. It is looked for under {folder}",
            file=sys.stderr,
        )
        return 1
    source = found[0]
    try:
        opened = read_release(source)
    except UnreadableRelease as error:
        raise Stop(f"the made-up city would not be served: {error}") from None
    if not opened.manifest.synthetic:
        raise Stop("what is committed as the made-up city does not say that it is made up")
    out = _to_write(args)
    target = out / source.name
    target.mkdir(parents=True)
    names = sorted(path.name for path in source.iterdir() if path.name != IGNORED)
    for name in names:
        shutil.copyfile(source / name, target / name)
    size = sum((target / name).stat().st_size for name in names)
    print(public(TAKE, "ok", release=source.name, files=len(names), bytes=size))
    return 0


def _take(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    release: str | None = args.release
    if release is not None and not RELEASE_ID.fullmatch(release):
        raise Stop("--release is not the id of a release, as lon-2026-10-02-01")
    named = approved(args.approved)
    if release is None and named:
        print(public(TAKE, "refused"))
        raise Stop(
            f"{len(named)} of the releases of London are approved, and none was named. Name "
            "the release to take with --release, or the made-up city by its own id"
        )
    if release is None or release.startswith(SYNTHETIC_PREFIX):
        return _take_the_made_up_city(args, release)
    if release not in named:
        print(public(TAKE, "missing", release=release))
        print(
            f"error: no lock names {release}. A release is served only once its lock is "
            f"committed, as {APPROVED}/{release}.json, and only the founder commits one",
            file=sys.stderr,
        )
        return 1
    try:
        lock = read_lock(args.approved / f"{release}.json")
    except LockRefused as error:
        print(public(TAKE, "unreadable", release=release))
        print(f"error: {error}", file=sys.stderr)
        return 1
    out = _to_write(args)
    store = _store(environment, TAKE)
    try:
        for file in lock.files:
            store.get(file.name, file.sha256, file.bytes, out / file.name)
            if hash_file(out / file.name) != (file.sha256, file.bytes):
                raise NotTheFile("a file that was taken is not the file its lock names")
        _opened(out, release)
    except (NotTheFile, StoreError, Stop) as error:
        # Nothing half taken is left for an image to be built from.
        shutil.rmtree(out, ignore_errors=True)
        if not isinstance(error, NotTheFile):
            raise Stop(str(error)) from None
        print(public(TAKE, "differs", release=release, differing=1))
        print(
            "error: a file that is kept is not the file the lock names, so nothing was taken. "
            "What is kept under the id of a release never changes: build again under a new "
            "id, and approve that",
            file=sys.stderr,
        )
        return 1
    size = sum(file.bytes for file in lock.files)
    print(
        public(TAKE, "ok", release=release, files=len(lock.files), bytes=size, sha256=lock.digest())
    )
    return 0


def build(prog: str = PROG) -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The steps kept owns, as the command line takes them: the whole, and each step of it."""
    whole = argparse.ArgumentParser(
        prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = whole.add_subparsers(dest="command", required=True)
    step = {step.name: add_step(commands, step, prog) for step in STEPS}
    step[KEEP].add_argument(
        "folder",
        type=Path,
        metavar="FOLDER",
        help="the folder the build wrote under, which holds the folder of the release",
    )
    step[KEEP].add_argument(
        "--release",
        required=True,
        metavar="ID",
        help="the release that is kept, as lon-2026-10-02-01",
    )
    step[TAKE].add_argument(
        "--release",
        metavar="ID",
        help="the release that is taken, as lon-2026-10-02-01. Without it the made-up city "
        "is taken, where no lock is committed",
    )
    step[TAKE].add_argument(
        "--out",
        required=True,
        type=Path,
        metavar="FOLDER",
        help="the folder the release is written under, which must be new or empty",
    )
    step[TAKE].add_argument(
        "--approved",
        type=Path,
        default=Path(APPROVED),
        metavar="FOLDER",
        help=f"the folder of the locks that are committed (default: {APPROVED})",
    )
    step[TAKE].add_argument(
        "--made-up",
        type=Path,
        default=MADE_UP,
        metavar="FOLDER",
        help=f"the folder the made-up city is committed under (default: {MADE_UP})",
    )
    step[TAKE].add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="the top of the repository, which --out is held to (default: here)",
    )
    return whole, step


def parsed(argv: Sequence[str] | None = None, prog: str = PROG) -> argparse.Namespace:
    """The arguments of a step. Stops with the step's usage if they are not ones it takes."""
    return build(prog)[0].parse_args(argv)


def main(argv: Sequence[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    args = parsed(argv)
    environment = os.environ if environment is None else environment
    try:
        if args.command == KEEP:
            return _keep(args, environment)
        return _take(args, environment)
    except Stop as stop:
        print(f"error: {stop}", file=sys.stderr)
    except OSError as error:
        print(f"error: cannot read or write a file: {error.strerror}", file=sys.stderr)
    return 2
