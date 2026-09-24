"""Say whether two builds of one release gave the same bytes.

A build runs twice, on two machines. Each hashes what it built, and a third
job compares the two. A release's manifest lists the hash of every other file,
so two builds with one manifest are the same byte for byte.

    COPY=a python tools/same_manifest.py hash FOLDER     FOLDER holds one release
    COPY_A=... COPY_B=... python tools/same_manifest.py compare

Nothing crosses from one job to the next but names of files and hashes, as a
job's output. No file of a release is ever uploaded to be compared.

Standard library only. See docs/data-builds.md.
"""

import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
from collections.abc import Generator, Sequence
from pathlib import Path
from typing import Any, TextIO, cast

from public_log import RELEASE_FILES, RELEASE_ID, SHA256

MANIFEST = "manifest.json"
FILE_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._-]*")
# What a Mac leaves in a folder it has shown. The release reader leaves it out too.
IGNORED = ".DS_Store"
PIECE = 1024 * 1024


class _Unreadable(Exception):
    """The manifest, or a job's output, is not in the form this file writes and reads."""


def _hash(path: Path) -> tuple[str, int]:
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as file:
        while piece := file.read(PIECE):
            digest.update(piece)
            size += len(piece)
    return digest.hexdigest(), size


def _listed(manifest: bytes) -> dict[str, tuple[str, int]]:
    """The files a manifest lists, each with its hash and its size."""
    try:
        document = json.loads(manifest)
        entries = cast(list[dict[str, Any]], document["files"])
        found = {
            str(entry["name"]): (str(entry["sha256"]), int(entry["bytes"])) for entry in entries
        }
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise _Unreadable from error
    names_are_plain = all(FILE_NAME.fullmatch(name) and name != MANIFEST for name in found)
    if not found or len(found) != len(entries) or not names_are_plain:
        raise _Unreadable
    return found


def _shown(names: Sequence[str]) -> list[str]:
    """The names that are names of release files. Any other is counted and never shown."""
    return [name for name in names if name in RELEASE_FILES]


def hash_release(folder: Path, copy: str, out: TextIO, outputs: TextIO) -> int:
    """Check one build against its own manifest, and write its hashes as the job's output."""

    def fail(status: str, *more: str) -> int:
        print(" ".join([f"step=manifest status={status}", *more]), file=out)
        return 1

    if copy not in ("a", "b"):
        return fail("refused")
    releases = sorted(path for path in folder.iterdir() if path.is_dir()) if folder.is_dir() else []
    if len(releases) != 1:
        return fail("missing", f"copy={copy}")
    release = releases[0]
    try:
        manifest = (release / MANIFEST).read_bytes()
        listed = _listed(manifest)
    except (OSError, _Unreadable):
        return fail("unreadable", f"copy={copy}")

    wrong: list[str] = []
    for name, expected in sorted(listed.items()):
        path = release / name
        if not path.is_file() or path.is_symlink() or _hash(path) != expected:
            wrong.append(name)
    unlisted = [
        path.name for path in release.iterdir() if path.name not in {*listed, MANIFEST, IGNORED}
    ]
    for name in _shown(wrong):
        fail("failed", f"copy={copy}", f"file={name}")
    if hidden := len(wrong) - len(_shown(wrong)):
        fail("failed", f"copy={copy}", f"wrong={hidden}")
    if unlisted:
        fail("failed", f"copy={copy}", f"unlisted={len(unlisted)}")
    if wrong or unlisted:
        return 1

    of_manifest = hashlib.sha256(manifest).hexdigest()
    named = [f"release={release.name}"] if RELEASE_ID.fullmatch(release.name) else []
    size = sum(size for _, size in listed.values())
    counts = [f"files={len(listed)}", f"bytes={size}", f"manifest_sha256={of_manifest}"]
    print(" ".join(["step=manifest status=ok", f"copy={copy}", *named, *counts]), file=out)
    hashes = {"manifest": of_manifest, "files": {name: sha for name, (sha, _) in listed.items()}}
    print(f"{copy}={json.dumps(hashes, sort_keys=True, separators=(',', ':'))}", file=outputs)
    return 0


def _read(output: str) -> tuple[str, dict[str, str]]:
    """The hashes one build gave, as `hash_release` wrote them."""
    try:
        document = json.loads(output)
        manifest, files = document["manifest"], cast(dict[str, Any], document["files"])
        hashes = [manifest, *files.values()]
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise _Unreadable from error
    if not files or not all(isinstance(sha, str) and SHA256.fullmatch(sha) for sha in hashes):
        raise _Unreadable
    return manifest, cast(dict[str, str], files)


def compare(a: str, b: str, out: TextIO, summary: TextIO) -> int:
    """Compare what two builds gave. Writes one paragraph for the run's summary page."""
    try:
        (manifest_a, files_a), (manifest_b, files_b) = _read(a), _read(b)
    except _Unreadable:
        print("step=compare status=missing", file=out)
        print("A build gave no manifest, so the two could not be compared.", file=summary)
        return 1

    names = sorted({*files_a, *files_b})
    differing = [name for name in names if files_a.get(name) != files_b.get(name)]
    if not differing and manifest_a != manifest_b:
        differing = [MANIFEST]
    if not differing:
        counts = f"files={len(names)} differing=0 manifest_sha256={manifest_a}"
        print(f"step=compare status=ok {counts}", file=out)
        print(f"Built twice, and the two builds give one manifest: `{manifest_a}`.", file=summary)
        return 0

    shown = [name for name in differing if name in {*RELEASE_FILES, MANIFEST}]
    for name in shown:
        print(f"step=compare status=differs file={name}", file=out)
    print(f"step=compare status=differs files={len(names)} differing={len(differing)}", file=out)
    others = len(differing) - len(shown)
    listed = ", ".join([*shown, *([f"{others} more"] if others else [])])
    print(
        f"The two builds differ in {len(differing)} of {len(names)} files: {listed}.", file=summary
    )
    return 1


@contextlib.contextmanager
def _runners_file(variable: str) -> Generator[TextIO]:
    """A file the runner reads after the step. Away from a runner, what is written is dropped."""
    with Path(os.environ.get(variable) or os.devnull).open("a", encoding="utf-8") as file:
        yield file


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="same_manifest", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("hash").add_argument("folder", type=Path)
    commands.add_parser("compare")
    args = parser.parse_args(argv)
    if args.command == "hash":
        with _runners_file("GITHUB_OUTPUT") as outputs:
            return hash_release(args.folder, os.environ.get("COPY", ""), sys.stdout, outputs)
    with _runners_file("GITHUB_STEP_SUMMARY") as summary:
        a, b = os.environ.get("COPY_A", ""), os.environ.get("COPY_B", "")
        return compare(a, b, sys.stdout, summary)


if __name__ == "__main__":
    sys.exit(main())
