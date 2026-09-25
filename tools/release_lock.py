"""The lock of a release: the release by its id, and every file of it by its hash.

A release of London is built in a hosted run and kept in a bucket. Nothing of
it is committed: it holds real figures of real places. What is committed is
its lock, which holds ids, hashes, counts and dates, and no figure and no name
of a place. To approve a release is to commit its lock, in data/approved/,
named for the release. An image carries a release that is not made up only
where its lock is committed and every byte it holds of the release is as the
lock says.

    python tools/release_lock.py hash a FOLDER RELEASE     one build, as copy a or b
    python tools/release_lock.py compare FOLDER RELEASE    this build beside the other's lock
    python tools/release_lock.py show FOLDER RELEASE       put the lock on the run's summary
    python tools/release_lock.py carried FOLDER RELEASE    hold what an image carries to its lock
    python tools/release_lock.py read FILE                 say what a lock names

FOLDER is where a build wrote, or where a release was taken to: it holds the
folder of the release, and beside it the folder of its build and the folder of
household income. `compare` reads the lock of the other build from COPY_A,
which is the output of the job that made it.

A lock is the same lock however it is written down: what is compared is what
it says. `read` gives the hash of what a lock says, so that a lock that was
pasted can be held to the one a run showed.

Every line this prints is one tools/public_log.py would show. What it writes
to the run's summary and to a job's output is a lock and what a lock says, and
every value of a lock is held to a shape before it is written: an id, a hash,
a whole number, a time, the id of a measure in core's catalogue, the name of a
rule, the name of a file that a build is known to write. Nothing else is
copied from a file of a build.

A hosted run starts three of these with no public log before them, because
they write to the run's outputs and its summary. So whatever goes wrong, a
command ends on one line of that kind, with a code that is not nought, and it
never prints a traceback: one could hold a name or a figure of the release it
read, or a path of the machine. A fault nobody foresaw is said as
`status=failed why=17`, the number a line of fetch gives a fault of its own.
What it would have printed is counted, as `withheld`, and never shown.

Standard library only. See docs/data-builds.md.
"""

import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
import traceback
from collections.abc import Generator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn, TextIO, cast

from public_log import BESIDE_FILES, FEATURES, RELEASE_FILES, RULES

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
# Where the lock of an approved release is committed, from the top of the repository.
APPROVED = PurePosixPath("data/approved")
# The folders a build writes: the release, and what stands beside it. Each is named for
# the release, with this after its id. A public line names a folder by the word beside it.
RELEASE, BUILD, INCOME = "", "-build", "-income"
BESIDE: Mapping[str, str] = {RELEASE: "release", BUILD: "build", INCOME: "income"}
MANIFEST, CATALOGUE, RECORD = "manifest.json", "catalogue.json", "build.json"
# What a release that is not made up is served with: the service holds it to each.
SERVED_WITH = (
    (RELEASE, MANIFEST),
    (BUILD, "hashes.json"),
    (BUILD, "evidence.json"),
    (BUILD, "lock.json"),
)
# What a Mac leaves in a folder it has shown. The release reader leaves it out too.
IGNORED = ".DS_Store"
MADE_UP = "syn-"
PIECE = 1024 * 1024

RELEASE_ID = re.compile(r"(?:syn|lon)-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}")
LONDON = re.compile(r"lon-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}")
COMMIT = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
SHA256 = re.compile(r"[0-9a-f]{64}")

# What a lock holds, and nothing else.
KEYS = (
    *("schema_version", "release_id", "built_at", "commit", "development", "preview"),
    *("holds", "left_out", "files"),
)
# What a lock counts of a release. The manifest of a release names the first an area.
HOLDS = ("areas", "rankable", "measures", "vibes", "destinations", "places", "stations")
IN_THE_MANIFEST = {
    "areas": "neighbourhoods",
    "rankable": "rankable",
    "destinations": "destinations",
    "places": "places",
    "stations": "stations",
}

type Lock = dict[str, Any]


class Unreadable(Exception):
    """A build or a lock is not in the form this file writes and reads.

    The message is a fixed sentence. It never repeats what a file holds.
    """


def _hash(path: Path) -> tuple[str, int]:
    found, size = hashlib.sha256(), 0
    with path.open("rb") as file:
        while piece := file.read(PIECE):
            found.update(piece)
            size += len(piece)
    return found.hexdigest(), size


def _is_a_count(value: object) -> bool:
    return type(value) is int and value >= 0


def _is_a_time(value: object) -> bool:
    """Whether a value is a time in UTC that the calendar has, written as a release writes one."""
    if not (isinstance(value, str) and TIME.fullmatch(value)):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return False
    return True


def _named(name: object, release: str) -> tuple[str, str] | None:
    """The folder and the file a lock's name stands for, where it is a file of the release."""
    if not isinstance(name, str):
        return None
    folder, _, file = name.partition("/")
    suffix = folder.removeprefix(release)
    if folder.startswith(release) and suffix in BESIDE and file in RELEASE_FILES | BESIDE_FILES:
        return suffix, file
    return None


def _checked_files(listed: object, release: str) -> list[dict[str, Any]]:
    if not isinstance(listed, list) or not listed:
        raise Unreadable("a lock names the files of its release, each by its hash")
    found: list[dict[str, Any]] = []
    for entry in cast(list[object], listed):
        if not isinstance(entry, dict) or set(cast(dict[str, Any], entry)) != {
            "name",
            "sha256",
            "bytes",
        }:
            raise Unreadable("a file of a lock is its name, its hash and its size")
        file = cast(dict[str, Any], entry)
        sha256 = file["sha256"]
        if (
            _named(file["name"], release) is None
            or not (isinstance(sha256, str) and SHA256.fullmatch(sha256))
            or not _is_a_count(file["bytes"])
        ):
            raise Unreadable("a file of a lock is not a file a build writes, or has no hash")
        found.append({"name": file["name"], "sha256": sha256, "bytes": file["bytes"]})
    names = [file["name"] for file in found]
    if names != sorted(set(names)):
        raise Unreadable("a lock names each file once, in the order of their names")
    if not {f"{release}{suffix}/{file}" for suffix, file in SERVED_WITH} <= set(names):
        raise Unreadable("a lock names the manifest of its release and what it is served with")
    return found


def _checked_left_out(listed: object) -> list[dict[str, str]]:
    if not isinstance(listed, list):
        raise Unreadable("a lock says which measures were left out, and by which rule")
    found: list[dict[str, str]] = []
    for entry in cast(list[object], listed):
        if not isinstance(entry, dict) or set(cast(dict[str, Any], entry)) != {"feature", "rule"}:
            raise Unreadable("a measure that was left out is its id and the name of a rule")
        gone = cast(dict[str, Any], entry)
        feature, rule = gone["feature"], gone["rule"]
        if not (isinstance(feature, str) and feature in FEATURES):
            raise Unreadable("a measure is named by its id in the catalogue")
        if not (isinstance(rule, str) and rule in RULES):
            raise Unreadable("a rule is named as the build names it")
        found.append({"feature": feature, "rule": rule})
    if found != sorted(found, key=lambda gone: (gone["feature"], gone["rule"])):
        raise Unreadable("the measures that were left out stand in the order of their ids")
    return found


def checked(document: object) -> Lock:
    """The lock a document is, with every value held to its shape. Raises `Unreadable`."""
    if not isinstance(document, dict) or set(cast(dict[str, Any], document)) != set(KEYS):
        raise Unreadable("a lock holds what a lock holds, and nothing else")
    lock = cast(dict[str, Any], document)
    release = lock["release_id"]
    if lock["schema_version"] != SCHEMA_VERSION or type(lock["schema_version"]) is not int:
        raise Unreadable("the lock is of a version this file does not read")
    if not (isinstance(release, str) and LONDON.fullmatch(release)):
        raise Unreadable("a lock is of a release that is not made up, named by its id")
    if not (isinstance(lock["commit"], str) and COMMIT.fullmatch(lock["commit"])):
        raise Unreadable("a lock names the code by its commit, in full")
    if not _is_a_time(lock["built_at"]):
        raise Unreadable("a lock says when its release is said to be built, in UTC")
    if not all(isinstance(lock[key], bool) for key in ("development", "preview")):
        raise Unreadable("a lock says whether its release is a preview, and how it was built")
    holds = lock["holds"]
    if (
        not isinstance(holds, dict)
        or set(cast(dict[str, Any], holds)) != set(HOLDS)
        or not all(_is_a_count(value) for value in cast(dict[str, Any], holds).values())
    ):
        raise Unreadable("a lock counts what its release holds, in whole numbers")
    return {
        "schema_version": SCHEMA_VERSION,
        "release_id": release,
        "built_at": lock["built_at"],
        "commit": lock["commit"],
        "development": lock["development"],
        "preview": lock["preview"],
        "holds": {name: cast(dict[str, Any], holds)[name] for name in HOLDS},
        "left_out": _checked_left_out(lock["left_out"]),
        "files": _checked_files(lock["files"], release),
    }


def written(lock: Lock) -> str:
    """A lock as it is committed: one value to a line, so that a change to one reads as one."""
    return json.dumps(checked(lock), indent=2, ensure_ascii=True) + "\n"


def _on_one_line(lock: Lock) -> str:
    """A lock in the one form a release file is written in, which is the form that is hashed."""
    return json.dumps(
        checked(lock), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def digest(lock: Lock) -> str:
    """The hash of what a lock says, however it was written down.

    It is the hash of the lock in the one form a release file is written in,
    with the end of the line that such a file ends with.
    """
    return hashlib.sha256(f"{_on_one_line(lock)}\n".encode()).hexdigest()


def read(path: Path) -> Lock:
    """The lock in a file. Raises `Unreadable`, which repeats nothing the file holds."""
    try:
        return checked(json.loads(path.read_bytes()))
    except (OSError, ValueError):
        raise Unreadable("the file could not be read as a lock") from None


def _document(path: Path) -> dict[str, Any]:
    try:
        found = json.loads(path.read_bytes())
    except (OSError, ValueError):
        raise Unreadable("a file of the build could not be read") from None
    if not isinstance(found, dict):
        raise Unreadable("a file of the build is not in the form a build writes")
    return cast(dict[str, Any], found)


def _held_in(folder: Path) -> tuple[dict[str, tuple[str, int]], int]:
    """Every file of one folder of a build by its name, with its hash and its size.

    Beside them, how many things the folder holds that no build writes there:
    a folder, a link, a file under a name that is not on the list.
    """
    found: dict[str, tuple[str, int]] = {}
    strays = 0
    try:
        for entry in sorted(folder.iterdir()):
            if entry.name == IGNORED and entry.is_file() and not entry.is_symlink():
                continue
            if (
                entry.is_symlink()
                or not entry.is_file()
                or entry.name not in RELEASE_FILES | BESIDE_FILES
            ):
                strays += 1
            else:
                found[entry.name] = _hash(entry)
    except OSError:
        raise Unreadable("a folder of the build could not be read") from None
    return found, strays


def _files_of(out: Path, release: str) -> list[dict[str, Any]]:
    """Every file a build wrote, by its name in a lock. The folder of income may be absent."""
    found: list[dict[str, Any]] = []
    for suffix in BESIDE:
        folder = out / f"{release}{suffix}"
        if not folder.is_dir():
            if suffix == INCOME:
                continue
            raise Unreadable("the build lacks a folder that every build writes")
        held, strays = _held_in(folder)
        if strays:
            raise Unreadable("a folder of the build holds what no build writes there")
        found += [
            {"name": f"{release}{suffix}/{name}", "sha256": sha256, "bytes": size}
            for name, (sha256, size) in held.items()
        ]
    return sorted(found, key=lambda file: file["name"])


def lock_of(out: Path, release: str) -> Lock:
    """The lock of the build that was written under `out`. Raises `Unreadable`.

    It is read from what the build wrote: the hash of every file, the counts
    of the manifest, the measures and the vibes of the catalogue, and from the
    record of the build its commit and what was left out. Of what was left
    out only the id of the measure and the name of the rule are read.
    """
    if not LONDON.fullmatch(release):
        raise Unreadable("a lock is of a release that is not made up, named by its id")
    files = _files_of(out, release)
    manifest = _document(out / release / MANIFEST)
    catalogue = _document(out / release / CATALOGUE)
    record = _document(out / f"{release}{BUILD}" / RECORD)
    if manifest.get("synthetic") is not False:
        raise Unreadable("the release says it is made up, and a made-up release has no lock")
    if {manifest.get("release_id"), record.get("release_id")} != {release}:
        raise Unreadable("the build is of another release than its folder is named for")
    try:
        counts = cast(dict[str, Any], manifest["counts"])
        gone = cast(list[dict[str, Any]], record["measures_left_out"])
        return checked(
            {
                "schema_version": SCHEMA_VERSION,
                "release_id": release,
                "built_at": manifest["built_at"],
                "commit": record["commit"],
                "development": record["development"],
                "preview": manifest["preview"],
                "holds": {name: counts[there] for name, there in IN_THE_MANIFEST.items()}
                | {"measures": len(catalogue["metrics"]), "vibes": len(catalogue["vibes"])},
                "left_out": sorted(
                    ({"feature": one["feature_id"], "rule": one["rule"]} for one in gone),
                    key=lambda one: (str(one["feature"]), str(one["rule"])),
                ),
                "files": files,
            }
        )
    except (KeyError, TypeError, AttributeError):
        raise Unreadable("a file of the build is not in the form a build writes") from None


def _counted(lock: Lock) -> str:
    size = sum(file["bytes"] for file in lock["files"])
    return f"files={len(lock['files'])} bytes={size}"


def _held(lock: Lock) -> str:
    holds = lock["holds"]
    return f"areas={holds['areas']} measures={holds['measures']} vibes={holds['vibes']}"


def hash_build(
    out: Path, release: str, copy: str, printed: TextIO, outputs: TextIO, to: Path | None = None
) -> int:
    """Hash one build, and write its lock as the output of the job, named for the copy.

    With `to`, the lock is written to that file as well, as it is committed.
    """
    if copy not in ("a", "b") or not LONDON.fullmatch(release):
        print("step=lock status=refused", file=printed)
        return 1
    try:
        lock = lock_of(out, release)
        if to is not None:
            to.parent.mkdir(parents=True, exist_ok=True)
            to.write_text(written(lock), encoding="utf-8")
    except (Unreadable, OSError):
        print(f"step=lock status=unreadable copy={copy}", file=printed)
        return 1
    print(
        f"step=lock status=ok copy={copy} release={release} {_counted(lock)} "
        f"{_held(lock)} sha256={digest(lock)}",
        file=printed,
    )
    print(f"{copy}={_on_one_line(lock)}", file=outputs)
    return 0


def _differing(ours: Lock, theirs: Lock) -> tuple[list[str], int]:
    """The files two locks say differently of, and how many other things they differ in."""
    a = {file["name"]: (file["sha256"], file["bytes"]) for file in ours["files"]}
    b = {file["name"]: (file["sha256"], file["bytes"]) for file in theirs["files"]}
    files = [name for name in sorted({*a, *b}) if a.get(name) != b.get(name)]
    wrong = sum(ours[key] != theirs[key] for key in KEYS if key != "files")
    return files, wrong


def _say_each(step: str, release: str, names: Sequence[str], more: str, printed: TextIO) -> None:
    """One line for each file that differs, by the folder it is in and its name."""
    for name in names:
        found = _named(name, release)
        if found is not None:
            print(
                f"step={step} status=differs{more} folder={BESIDE[found[0]]} file={found[1]}",
                file=printed,
            )


def compare(out: Path, release: str, other: str, printed: TextIO) -> int:
    """Hold this build to the lock of the other. Returns 0 only where every byte is the same."""
    try:
        theirs = checked(json.loads(other))
    except (Unreadable, ValueError):
        print("step=compare status=missing", file=printed)
        return 1
    try:
        ours = lock_of(out, release)
    except Unreadable:
        print("step=compare status=unreadable", file=printed)
        return 1
    files, wrong = _differing(ours, theirs)
    names = {file["name"] for lock in (ours, theirs) for file in lock["files"]}
    if not files and not wrong:
        counts = f"files={len(names)} differing=0 sha256={digest(ours)}"
        print(f"step=compare status=ok {counts}", file=printed)
        return 0
    # A lock of another release names no file of this one, so such a file is counted.
    _say_each("compare", release, files, "", printed)
    more = f" wrong={wrong}" if wrong else ""
    print(
        f"step=compare status=differs files={len(names)} differing={len(files)}{more}",
        file=printed,
    )
    return 1


def summary_of(lock: Lock) -> str:
    """What the run's summary says of a release that was built twice and kept."""
    release, holds = lock["release_id"], lock["holds"]
    kind = [
        "a preview" if lock["preview"] else "not a preview",
        "a development build" if lock["development"] else "built from locked packages",
    ]
    gone = [f"| `{one['feature']}` | `{one['rule']}` |" for one in lock["left_out"]]
    left_out = (
        ["", "| Left out | By the rule |", "|---|---|", *gone]
        if gone
        else ["", "No measure was left out."]
    )
    return "\n".join(
        [
            f"## The lock of `{release}`",
            "",
            "Built twice, and the two builds are the same, byte for byte. The release is kept.",
            "It is served nowhere until its lock is on the default branch.",
            "",
            "| | |",
            "|---|---|",
            f"| The release | `{release}`, {' and '.join(kind)} |",
            f"| Built from | `{lock['commit']}` |",
            f"| It holds | {holds['areas']} areas, of which {holds['rankable']} can be ranked. "
            f"{holds['measures']} measures. {holds['vibes']} vibes. "
            f"{holds['destinations']} destinations, {holds['places']} places and "
            f"{holds['stations']} stations |",
            f"| Its files | {len(lock['files'])}, each named below by its hash |",
            f"| The hash of what the lock says | `{digest(lock)}` |",
            *left_out,
            "",
            f"To approve it, save what stands below as `{APPROVED.as_posix()}/{release}.json`, "
            "and bring it into the default branch. docs/data-builds.md says what to read first.",
            "",
            "```json",
            written(lock).rstrip("\n"),
            "```",
            "",
        ]
    )


def show(out: Path, release: str, printed: TextIO, summary: TextIO) -> int:
    """Put the lock of a build on the run's summary, as it is to be committed."""
    try:
        lock = lock_of(out, release)
    except Unreadable:
        print("step=lock status=unreadable", file=printed)
        return 1
    print(summary_of(lock), file=summary)
    print(
        f"step=lock status=ok release={release} files={len(lock['files'])} sha256={digest(lock)}",
        file=printed,
    )
    return 0


def _strays(folder: Path, expected: set[str]) -> int:
    """How many things stand in a folder beside the folders that are expected there."""
    try:
        return sum(entry.name not in {*expected, IGNORED} for entry in folder.iterdir())
    except OSError:
        raise Unreadable("the folder could not be read") from None


def _found(folder: Path, release: str, suffixes: Sequence[str]) -> tuple[list[dict[str, Any]], int]:
    """What a folder holds of a release, as a lock names it, and what it holds beside that."""
    found: list[dict[str, Any]] = []
    strays = 0
    for suffix in suffixes:
        within = folder / f"{release}{suffix}"
        if within.is_dir():
            held, more = _held_in(within)
            strays += more
            found += [
                {"name": f"{release}{suffix}/{name}", "sha256": sha256, "bytes": size}
                for name, (sha256, size) in held.items()
            ]
    return found, strays


def _said(
    release: str, expected: Sequence[dict[str, Any]], folder: Path, of: str, printed: TextIO
) -> int:
    """Hold what a folder holds to what is expected of it, file by file, and say so."""
    suffixes = sorted({suffix for file in expected if (suffix := _suffix(file, release)) in BESIDE})
    found, wrong = _found(folder, release, suffixes)
    a = {file["name"]: (file["sha256"], file["bytes"]) for file in expected}
    b = {file["name"]: (file["sha256"], file["bytes"]) for file in found}
    files = [name for name in sorted({*a, *b}) if a.get(name) != b.get(name)]
    if not files and not wrong:
        size = sum(file["bytes"] for file in expected)
        print(
            f"step=take status=ok release={release} files={len(expected)} bytes={size}{of}",
            file=printed,
        )
        return 0
    _say_each("take", release, files, f" release={release}", printed)
    more = f" wrong={wrong}" if wrong else ""
    print(
        f"step=take status=differs release={release} files={len(expected)} "
        f"differing={len(files)}{more}",
        file=printed,
    )
    return 1


def _suffix(file: Mapping[str, Any], release: str) -> str:
    return str(file["name"]).partition("/")[0].removeprefix(release)


def _made_up(folder: Path, release: str, printed: TextIO) -> int:
    """Hold the made-up city to its own manifest, which is committed with it."""
    try:
        if strays := _strays(folder, {release}):
            print(f"step=take status=refused release={release} unlisted={strays}", file=printed)
            return 1
        manifest = _document(folder / release / MANIFEST)
        listed = cast(list[dict[str, Any]], manifest["files"])
        expected = [
            {
                "name": f"{release}/{entry['name']}",
                "sha256": str(entry["sha256"]),
                "bytes": int(entry["bytes"]),
            }
            for entry in listed
        ]
        sha256, size = _hash(folder / release / MANIFEST)
    except (Unreadable, KeyError, TypeError, ValueError, OSError):
        print(f"step=take status=unreadable release={release}", file=printed)
        return 1
    if manifest.get("synthetic") is not True or manifest.get("release_id") != release:
        # A release that is not made up is carried by its lock, and under its own id.
        print(f"step=take status=refused release={release}", file=printed)
        return 1
    expected.append({"name": f"{release}/{MANIFEST}", "sha256": sha256, "bytes": size})
    return _said(release, expected, folder, "", printed)


def carried(folder: Path, release: str, approved: Path, printed: TextIO) -> int:
    """Say whether an image may carry what a folder holds. Returns 0 only where it may.

    The made-up city is carried as it is committed: it is held to its own
    manifest. Any other release is carried only where a lock named for it is
    in `approved`, the folder holds every file the lock names with the hash
    and the size it gives, and the folder holds nothing else.
    """
    if not RELEASE_ID.fullmatch(release):
        print("step=take status=refused", file=printed)
        return 1
    if release.startswith(MADE_UP):
        return _made_up(folder, release, printed)
    path = approved / f"{release}.json"
    if not path.is_file():
        print(f"step=take status=missing release={release}", file=printed)
        return 1
    try:
        lock = read(path)
        if lock["release_id"] != release:
            raise Unreadable("the lock is named for another release than it names")
        expected = {f"{release}{_suffix(file, release)}" for file in lock["files"]}
        strays = _strays(folder, expected)
    except Unreadable:
        print(f"step=take status=unreadable release={release}", file=printed)
        return 1
    if strays:
        print(f"step=take status=refused release={release} unlisted={strays}", file=printed)
        return 1
    return _said(release, lock["files"], folder, f" sha256={digest(lock)}", printed)


def said_of(path: Path, printed: TextIO) -> int:
    """Say what a lock names, and the hash of what it says."""
    try:
        lock = read(path)
    except Unreadable:
        print("step=lock status=unreadable", file=printed)
        return 1
    if path.stem != lock["release_id"]:
        print("step=lock status=refused", file=printed)
        return 1
    print(
        f"step=lock status=ok release={lock['release_id']} {_counted(lock)} {_held(lock)} "
        f"sha256={digest(lock)}",
        file=printed,
    )
    return 0


@contextlib.contextmanager
def _runners_file(variable: str) -> Generator[TextIO]:
    """A file the runner reads after the step. Away from a runner, what is written is dropped."""
    with Path(os.environ.get(variable) or os.devnull).open("a", encoding="utf-8") as file:
        yield file


# The step each command is, on the lines it prints.
STEP_OF: Mapping[str, str] = {
    "hash": "lock",
    "compare": "compare",
    "show": "lock",
    "carried": "take",
    "read": "lock",
}
# Why a command stopped on a fault of its own, as the number a line gives for it: the one
# a line of fetch gives a fault of its own, which `python -m burro_pipeline why` says in
# words. This file imports no package, so a test holds the two together.
FAULT = 17
# What a command ends with then. 1 is of what it was asked about, and 2 of how it was asked.
FAULTED = 3


class _NotTaken(Exception):
    """The words of a command are not ones this tool takes."""


class _Parser(argparse.ArgumentParser):
    """A parser that repeats nothing it was handed: a word of a command may be a path of
    the machine, or what somebody typed."""

    def error(self, message: str) -> NoReturn:
        raise _NotTaken


def _withheld(fault: BaseException) -> int:
    """How many lines a fault would have printed. None of them is kept."""
    try:
        return sum(len(part.splitlines()) for part in traceback.format_exception(fault))
    except Exception:
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run one command, and end on a line whatever goes wrong.

    No public log stands between this tool and the log of a run. So a fault nobody
    foresaw is caught here, whatever it is, and a run that is stopped as well: what it
    would have printed is counted and not shown, and the line says the step, that it
    failed, and why as a number. It holds nothing of what was read.
    """
    words = list(sys.argv[1:] if argv is None else argv)
    step = STEP_OF.get(words[0] if words else "", "lock")
    try:
        return _run(words)
    except _NotTaken:
        print(f"step={step} status=refused", flush=True)
        return 2
    except SystemExit:
        # The tool was asked how it is run, and has said so.
        raise
    except BaseException as fault:
        # Where the line itself cannot be printed, nothing is: a fault of that would be
        # printed with the fault before it.
        with contextlib.suppress(BaseException):
            print(f"step={step} status=failed why={FAULT} withheld={_withheld(fault)}", flush=True)
        return FAULTED


def _run(argv: Sequence[str]) -> int:
    parser = _Parser(prog="release_lock", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("hash")
    one.add_argument("copy")
    one.add_argument("--out", type=Path, metavar="FILE")
    for command in (one, *(commands.add_parser(name) for name in ("compare", "show", "carried"))):
        command.add_argument("folder", type=Path)
        command.add_argument("release")
    commands.choices["carried"].add_argument("--approved", type=Path, default=ROOT / APPROVED)
    commands.add_parser("read").add_argument("file", type=Path)
    args = parser.parse_args(argv)
    if args.command == "hash":
        with _runners_file("GITHUB_OUTPUT") as outputs:
            return hash_build(args.folder, args.release, args.copy, sys.stdout, outputs, args.out)
    if args.command == "compare":
        return compare(args.folder, args.release, os.environ.get("COPY_A", ""), sys.stdout)
    if args.command == "show":
        with _runners_file("GITHUB_STEP_SUMMARY") as summary:
            return show(args.folder, args.release, sys.stdout, summary)
    if args.command == "carried":
        return carried(args.folder, args.release, args.approved, sys.stdout)
    return said_of(args.file, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
