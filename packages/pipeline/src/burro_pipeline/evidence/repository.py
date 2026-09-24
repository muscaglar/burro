"""What git holds of the code a build runs: the commit, and whether the files are that commit.

A lock names the code by its commit. A commit that a person types may name
nothing, and a working copy with changes is not the code its commit names. So
`seal` reads both from the repository it is run in.

The repository is looked for as git looks for it: in the folder given, and in
every folder above it. So a step run in a folder of a working copy reads that
working copy, whole. What stands nearest is what is read, and nothing above it
is tried in its place.

It reads git's own files and runs no program, because no module of the
pipeline may run one. What it reads:

- `HEAD`, and the branch it names, for the commit that is checked out
- that commit, for the tree it holds
- the index, for the files git tracks
- every tracked file, to hash it.

A working copy is the commit, and nothing more, when two things hold. Every
tracked file hashes to what the index says of it. And the tree the index
describes is the tree of the commit, so nothing is staged.

A file git does not track is not looked at: which of them git ignores is
git's to say, and nothing here reads its rules. A file that git changes on
its way in, as a setting for line endings does, reads as changed.

What cannot be read is refused and never guessed: a repository whose hashes
are not SHA-1, branches kept as a table, an index that is split or sparse, a
repository inside this one.
"""

import hashlib
import os
import re
import stat
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

SHA1 = re.compile(r"[0-9a-f]{40}")
# A branch as HEAD names it. It is joined to a folder, so it may hold no way out of one.
REF = re.compile(r"refs/[A-Za-z0-9._/@{}+-]+")
# How far a name that stands for another name is followed.
FOLLOWED = 5
# A commit is a few hundred bytes. One over this size is not read: it is no commit.
LARGEST_OBJECT = 1 << 24
# How long a chain of changes to an object in a pack may be. Git's own limit is 50.
LONGEST_CHAIN = 64
PIECE = 1 << 16

FILE, RUNS, LINK, REPOSITORY, FOLDER = 0o100644, 0o100755, 0o120000, 0o160000, 0o40000
KINDS = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}
BY_OFFSET, BY_NAME = 6, 7
# Parts of an index that say its entries are not all of the files.
NOT_WHOLE = {b"link": "the index is split in two", b"sdir": "the index is sparse"}


class NotRead(Exception):
    """The repository could not be read. Says why, and holds no path and no name."""


@dataclass(frozen=True)
class Tracked:
    """One file as the index holds it."""

    path: bytes
    mode: int
    oid: bytes
    # 0 but in a merge that has not been settled.
    stage: int


# A folder of the index: each name in it is a file, or a folder in its turn.
type Folder = dict[bytes, Tracked | Folder]


@dataclass(frozen=True)
class CheckedOut:
    """The commit a working copy is at, and how far the working copy is from it."""

    commit: str
    # How many tracked files are not what the index says of them.
    changed: int
    # Whether the index holds what the commit does not: something is staged.
    staged: bool

    @property
    def clean(self) -> bool:
        return not self.changed and not self.staged

    def in_words(self) -> str:
        """What differs, as counts. Never the name of a file."""
        said: list[str] = []
        if self.changed == 1:
            said.append("1 tracked file is not as git last took it")
        elif self.changed:
            said.append(f"{self.changed} tracked files are not as git last took them")
        if self.staged:
            said.append("what is staged is not what is committed")
        return "; ".join(said)


def top_of(folder: Path) -> Path | None:
    """The top of the working copy a folder is in, or nothing if it is in none.

    It is the folder itself, or the nearest folder above it, that holds `.git`.
    Whether what is there can be read is found when it is read.
    """
    try:
        start = folder.resolve()
    except (OSError, RuntimeError):
        raise NotRead("the folder given leads nowhere") from None
    return next((above for above in (start, *start.parents) if (above / ".git").exists()), None)


def _top(folder: Path) -> Path:
    found = top_of(folder)
    if found is None:
        raise NotRead("the folder is in no working copy")
    return found


def checked_out(folder: Path) -> CheckedOut:
    """The commit the working copy around `folder` is at, and whether its files are that commit."""
    root = _top(folder)
    try:
        own, shared = _folders(root)
        commit = _commit_at(own, shared)
        tracked = _index(own / "index")
        of_the_commit = _tree_of_commit(_stores(shared), commit)
        changed = sum(not _is_as_tracked(root, file) for file in tracked)
        staged = any(file.stage for file in tracked) or _tree(tracked) != of_the_commit
    except OSError:
        raise NotRead("a file of the repository could not be read") from None
    except (struct.error, zlib.error, IndexError, ValueError):
        raise NotRead("a file of the repository is not as git writes it") from None
    return CheckedOut(commit, changed, staged)


def held(folder: Path, oid: str) -> tuple[str, bytes]:
    """An object of the repository by its hash: what kind it is, and what it holds."""
    root = _top(folder)
    try:
        return _object(_stores(_folders(root)[1]), oid, LONGEST_CHAIN)
    except OSError:
        raise NotRead("a file of the repository could not be read") from None
    except (struct.error, zlib.error, IndexError, ValueError):
        raise NotRead("a file of the repository is not as git writes it") from None


# Where git keeps things.


def _folders(root: Path) -> tuple[Path, Path]:
    """The folder git keeps for this working copy, and the one it shares with any other."""
    own = root / ".git"
    if own.is_file():
        # A second working copy of a repository: its folder is kept inside the first one's.
        said = own.read_text(encoding="utf-8").strip()
        if not said.startswith("gitdir: "):
            raise NotRead("the working copy does not say where its repository is")
        own = root / said.removeprefix("gitdir: ")
    shared = own / "commondir"
    return own, (own / shared.read_text(encoding="utf-8").strip() if shared.is_file() else own)


def _stores(shared: Path) -> list[Path]:
    """Every folder of objects: the repository's own, and any it borrows from."""
    stores = [shared / "objects"]
    borrowed = stores[0] / "info" / "alternates"
    if borrowed.is_file():
        lines = borrowed.read_text(encoding="utf-8").splitlines()
        stores += [stores[0] / line for line in lines if line and not line.startswith("#")]
    return stores


# The commit that is checked out.


def _commit_at(own: Path, shared: Path) -> str:
    said = (own / "HEAD").read_text(encoding="utf-8").strip()
    for _ in range(FOLLOWED):
        if SHA1.fullmatch(said):
            return said
        name = said.removeprefix("ref: ")
        if not said.startswith("ref: ") or not REF.fullmatch(name) or ".." in name:
            break
        said = _named(own, shared, name)
    if re.fullmatch(r"[0-9a-f]{64}", said):
        raise NotRead("its hashes are not SHA-1")
    raise NotRead("HEAD names no commit that can be read")


def _named(own: Path, shared: Path, name: str) -> str:
    """What a branch names: a commit, or another name."""
    for folder in (own, shared):
        if (folder / name).is_file():
            return (folder / name).read_text(encoding="utf-8").strip()
    packed = shared / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            commit, _, found = line.partition(" ")
            if found == name:
                return commit
    if (shared / "reftable").exists():
        raise NotRead("its branches are kept as a table")
    raise NotRead("the branch that is checked out has no commit")


# An object, loose or in a pack.


def _tree_of_commit(stores: list[Path], commit: str) -> bytes:
    kind, body = _object(stores, commit, LONGEST_CHAIN)
    first = body.split(b"\n", 1)[0].decode("ascii", "replace")
    if kind != "commit" or not first.startswith("tree ") or not SHA1.fullmatch(first[5:]):
        raise NotRead("HEAD names something that is no commit")
    return bytes.fromhex(first[5:])


def _object(stores: list[Path], oid: str, chain: int) -> tuple[str, bytes]:
    """An object by its hash: what kind it is, and what it holds."""
    if chain < 0:
        raise NotRead("an object is kept as too long a chain of changes")
    for store in stores:
        loose = store / oid[:2] / oid[2:]
        if loose.is_file():
            with loose.open("rb") as file:
                kind, _, body = _inflated(file).partition(b"\0")
            return kind.split(b" ")[0].decode("ascii"), body
    for store in stores:
        for index in sorted((store / "pack").glob("*.idx")):
            offset = _offset_in(index.read_bytes(), bytes.fromhex(oid))
            if offset is not None:
                with index.with_suffix(".pack").open("rb") as pack:
                    return _packed(pack, offset, stores, chain)
    raise NotRead("the commit that is checked out is not in the repository")


def _inflated(file: BinaryIO) -> bytes:
    """What is compressed at the place a file is read from, and no more than an object may be."""
    inflate, found = zlib.decompressobj(), bytearray()
    while not inflate.eof:
        piece = file.read(PIECE)
        if not piece:
            raise NotRead("an object stops before its end")
        found += inflate.decompress(piece, LARGEST_OBJECT + 1 - len(found))
        if len(found) > LARGEST_OBJECT or inflate.unconsumed_tail:
            raise NotRead("an object is too large to be a commit")
    return bytes(found)


def _offset_in(index: bytes, oid: bytes) -> int | None:
    """Where a pack holds an object, from the pack's index. Nothing if it does not hold it."""
    if index[:8] != b"\xfftOc\x00\x00\x00\x02":
        raise NotRead("a pack has an index of a version that is not read")
    counts = struct.unpack_from(">256I", index, 8)
    names = 8 + 256 * 4
    low, high, total = (counts[oid[0] - 1] if oid[0] else 0), counts[oid[0]], counts[255]
    while low < high:
        middle = (low + high) // 2
        found = index[names + 20 * middle : names + 20 * middle + 20]
        if found == oid:
            offsets = names + 24 * total
            (offset,) = struct.unpack_from(">I", index, offsets + 4 * middle)
            if offset & 0x80000000:
                at = offsets + 4 * total + 8 * (offset & 0x7FFFFFFF)
                (offset,) = struct.unpack_from(">Q", index, at)
            return offset
        low, high = (middle + 1, high) if found < oid else (low, middle)
    return None


def _packed(pack: BinaryIO, offset: int, stores: list[Path], chain: int) -> tuple[str, bytes]:
    """An object at a place in a pack. It may be kept whole, or as changes to another."""
    pack.seek(offset)
    head = pack.read(64)
    kind, at = (head[0] >> 4) & 7, 1
    while head[at - 1] & 0x80:
        at += 1
    if kind in KINDS:
        pack.seek(offset + at)
        return KINDS[kind], _inflated(pack)
    if kind == BY_OFFSET:
        back = head[at] & 0x7F
        while head[at] & 0x80:
            at += 1
            back = ((back + 1) << 7) | (head[at] & 0x7F)
        at += 1
        pack.seek(offset + at)
        changes = _inflated(pack)
        of, whole = _packed(pack, offset - back, stores, chain - 1)
    elif kind == BY_NAME:
        pack.seek(offset + at + 20)
        changes = _inflated(pack)
        of, whole = _object(stores, head[at : at + 20].hex(), chain - 1)
    else:
        raise NotRead("a pack holds an object of a kind that is not read")
    return of, _changed(whole, changes)


def _number(changes: bytes, at: int) -> tuple[int, int]:
    """A size as the changes to an object write it, and where the next thing starts."""
    found = shift = 0
    while True:
        byte = changes[at]
        found |= (byte & 0x7F) << shift
        at, shift = at + 1, shift + 7
        if not byte & 0x80:
            return found, at


def _changed(whole: bytes, changes: bytes) -> bytes:
    """An object, from the one it was kept as changes to."""
    before, at = _number(changes, 0)
    after, at = _number(changes, at)
    if before != len(whole) or after > LARGEST_OBJECT:
        raise NotRead("an object is not the size its changes give")
    made = bytearray()
    while at < len(changes):
        order = changes[at]
        at += 1
        if order & 0x80:
            start = size = 0
            for bit in range(4):
                if order & (1 << bit):
                    start |= changes[at] << (8 * bit)
                    at += 1
            for bit in range(3):
                if order & (0x10 << bit):
                    size |= changes[at] << (8 * bit)
                    at += 1
            size = size or 0x10000
            if start + size > len(whole):
                raise NotRead("an object is not the size its changes give")
            made += whole[start : start + size]
        elif order:
            made += changes[at : at + order]
            at += order
        else:
            raise NotRead("an object is kept as changes that are not read")
    if len(made) != after:
        raise NotRead("an object is not the size its changes give")
    return bytes(made)


# The index: the files git tracks.


def _index(path: Path) -> list[Tracked]:
    if not path.is_file():
        raise NotRead("the repository has no index")
    held = path.read_bytes()
    sign, version, count = struct.unpack_from(">4sII", held, 0)
    if sign != b"DIRC" or version not in (2, 3, 4):
        raise NotRead("the index is of a version that is not read")
    tracked: list[Tracked] = []
    at, before = 12, b""
    for _ in range(count):
        mode, oid = struct.unpack_from(">I", held, at + 24)[0], held[at + 40 : at + 60]
        (flags,) = struct.unpack_from(">H", held, at + 60)
        name = at + 62 + (2 if version >= 3 and flags & 0x4000 else 0)
        if version == 4:
            # A path is written as what to cut from the end of the last one, and what to add.
            cut = held[name] & 0x7F
            while held[name] & 0x80:
                name += 1
                cut = ((cut + 1) << 7) | (held[name] & 0x7F)
            end = held.index(b"\0", name + 1)
            before = before[: len(before) - cut] + held[name + 1 : end]
            at = end + 1
        else:
            end = held.index(b"\0", name)
            before = held[name:end]
            at += (end - at + 8) // 8 * 8
        tracked.append(Tracked(before, mode, oid, (flags >> 12) & 3))
    # What follows the entries is in parts, each with a name of four letters and a size.
    while at + 8 <= len(held) - 20:
        part, size = struct.unpack_from(">4sI", held, at)
        if part in NOT_WHOLE:
            raise NotRead(NOT_WHOLE[part])
        at += 8 + size
    return tracked


def _hash(kind: bytes, held: bytes) -> bytes:
    """The name git gives an object. It names, and keeps nothing safe."""
    return hashlib.sha1(kind + b" %d\0" % len(held) + held, usedforsecurity=False).digest()


def _tree(tracked: list[Tracked]) -> bytes:
    """The tree that the index describes, by its hash: what a commit of it would hold."""
    top: Folder = {}
    for file in tracked:
        *folders, name = file.path.split(b"/")
        into = top
        for folder in folders:
            inside = into.setdefault(folder, {})
            if isinstance(inside, Tracked):
                raise NotRead("the index holds a file and a folder of one name")
            into = inside
        into[name] = file

    def written(folder: Folder) -> bytes:
        # Git sorts a folder as if its name ended in a slash.
        rows = [
            (name + b"/", FOLDER, name, written(held))
            if isinstance(held, dict)
            else (name, held.mode, name, held.oid)
            for name, held in folder.items()
        ]
        rows.sort(key=lambda row: row[0])
        return _hash(b"tree", b"".join(b"%o %b\0%b" % row[1:] for row in rows))

    return written(top)


def _is_as_tracked(root: Path, file: Tracked) -> bool:
    """Whether a file in the working copy is what the index says of it."""
    if file.mode == REPOSITORY:
        raise NotRead("the repository holds another repository")
    path = root / os.fsdecode(file.path)
    try:
        found = path.lstat()
    except OSError:
        return False
    if file.mode == LINK:
        if not stat.S_ISLNK(found.st_mode):
            return False
        # Where a link leads, letter for letter. A path would be tidied, and hash otherwise.
        return _hash(b"blob", os.fsencode(os.readlink(path))) == file.oid  # noqa: PTH115
    if not stat.S_ISREG(found.st_mode) or bool(found.st_mode & 0o100) != (file.mode == RUNS):
        return False
    return _hash(b"blob", path.read_bytes()) == file.oid
