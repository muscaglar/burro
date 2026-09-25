"""The record of a decision: its one line, the file it is kept in, and which line stands.

A decision is one line of JSON, appended to `<data>/decisions/<queue>/<reviewer>.jsonl`.
The lines of a queue that may never be published are kept apart, in
`<data>/decisions-private/`, so that a copy of `decisions/` takes none of them.
A line is never changed and never removed: an undo is a line too. What the page
shows and what a build reads are both worked out from the lines by the functions
here. They read no clock, and they keep nothing between calls.

A line is on disk before `append` returns. A fault while a line is written can
leave half a line at the end of a file. Half a line is counted as broken, it is
never applied, and the next line starts on a line of its own.

Lines are put in order by their number, `n`, and never by their time, `at`. So a
clock that goes backwards changes no answer, and a file whose lines were shuffled
gives the same answers as before.

Standard library only. Needs a Mac or Linux, for the lock on a file.
See docs/design/desk.md, sections 3 and 8.
"""

import fcntl
import json
import os
import re
import statistics
import threading
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final, NoReturn, cast

type Json = bool | int | float | str | list[Json] | dict[str, Json] | None

# The version of the files the desk reads and writes.
DESK: Final = 1

# The fields of a line, in the order they are written.
FIELDS: Final = (
    *("n", "at", "reviewer", "queue", "question", "item", "rev", "part"),
    *("answer", "note", "second", "settles", "undoes", "detail", "seconds", "synthetic"),
)
# Answers that every queue has, beside the codes of its own question.
SKIP, MOVE, UNDO = "skip", "move", "undo"
# The answer of a line the desk writes where a rule that the founder adopted leaves an
# item as drafted. It is none of the question's answers: it says that nobody is asked,
# and decides nothing. No request may give it.
RULE: Final = "rule"
# The queue in which the founder adopts a rule, the answer that adopts one, and the keys
# of a preset that say which rule an item is, which queue it settles, what it gives an
# item, and which rule fits an item.
OF_RULES, ADOPT = "rules", "yes"
GIVES, FITS, PROPOSED = "gives", "fits", "proposed"
# The rule an item leans on, where the rule that fits it leans on others: such a rule
# settles the item only where both are adopted. On a rule, every rule it leans on.
LEANS_ON = "leans_on"

# A label, never a name: the files may be published.
REVIEWER: Final = re.compile(r"r[1-9][0-9]?")
FOUNDER: Final = "r1"
QUEUE: Final = re.compile(r"[a-z][a-z0-9_]{0,31}")
REV: Final = re.compile(r"[0-9a-f]{12}")
AT: Final = "%Y-%m-%dT%H:%M:%SZ"
NOTE_LIMIT: Final = 500
# What a note may not hold, by the category Unicode gives a character: a control, a mark
# that is not seen, and the end of a line or of a paragraph. A note can reach a published
# table, where one would part a row in two or turn the words round.
NOT_PLAIN: Final = frozenset({"Cc", "Cf", "Zl", "Zp"})
SECONDS_LIMIT: Final = 900
ID_LIMIT: Final = 200

# How the answers of two reviewers meet, by queue. `ALONE`: only the founder's count.
# `TOGETHER`: answers that differ are a dispute, and nothing is applied until the
# founder settles it. `EACH`: every reviewer's answer is a row of its own, as a rating is.
ALONE, TOGETHER, EACH = "alone", "together", "each"
RULES: Final[Mapping[str, str]] = {
    "names": ALONE,
    "borders": TOGETHER,
    "whole": TOGETHER,
    "claims": TOGETHER,
    "sentences": TOGETHER,
}

# The answers by which a reviewer says they cannot judge. Such an answer decides nothing:
# where another reviewer did decide, theirs stands, and the two are not in dispute.
NOT_KNOWN: Final = frozenset({"unknown", "cannot_say", "cannot_tell"})

# The answers by which a reviewer calls an item wrong. It changes nothing in a build:
# it is listed for a person to look at again.
CALLED_WRONG: Final = frozenset({"wrong", "looks_wrong"})

# Who is asked to work a queue: the founder alone, or any reviewer.
OPEN_TO_ALL, OPEN_TO_FOUNDER = "all", "founder"
# The queue in which a reviewer says how well they know each borough, the answers in the
# order their boroughs are offered in, and where a borough nobody marked comes.
KNOW: Final = "know"
KNOWN: Final = ("well", "a_little", "", "not")
# The queues that are put in that order: names, and those decided on the ground, where
# a person who knows it decides well and fast. Each is filled borough by borough, so a
# borough is finished before the next begins. Figures are read in the order of their
# file, for all of London.
BY_KNOWN: Final = frozenset({"names", "borders", "whole", "ratings"})

# Where lines are kept. A queue whose question says `public: false` holds what a person
# knows of a place, or judges of words about one: its lines are in a tree of their own.
PUBLIC_TREE, PRIVATE_TREE = "decisions", "decisions-private"

# The states of an item, for one reviewer.
OPEN, DONE, SKIPPED, STALE, DISPUTED = "open", "done", "skipped", "stale", "disputed"

# Pace is worked out over this many lines, and over this long.
PACE_LINES: Final = 50
PACE_WINDOW: Final = timedelta(hours=1)

# The keys of an item, as docs/design/desk.md section 8 gives them. An item with any
# other key is refused, so that nothing reaches the page that the design does not name.
ITEM_KEYS: Final = frozenset(
    {
        *("id", "rev", "group", "title", "lines", "text"),
        *("map", "picks", "flags", "fill", "preset"),
    }
)
HEADER_KEYS: Final = frozenset(
    {"desk", "queue", "question", "synthetic", "made_on", "made_from", "count"}
)


class Broken(ValueError):
    """A line that cannot be read as a decision. The words never repeat the line."""


class Unfit(ValueError):
    """A file of items or of questions that is not as the design gives it."""


class Differ(OSError):
    """The kept copy holds what the file of decisions does not. Neither is written over."""


def rule_of(queue: str) -> str:
    return RULES.get(queue, EACH)


def number_of(reviewer: str) -> int:
    """The order of reviewers: r1, r2, and so on. r10 comes after r9."""
    return int(reviewer[1:])


# A line


@dataclass(frozen=True, slots=True)
class Line:
    """One decision, as written. docs/design/desk.md section 3 says what each field holds."""

    n: int
    at: str
    reviewer: str
    queue: str
    question: str
    item: str
    rev: str
    part: str
    answer: str
    note: str
    second: bool
    settles: bool
    undoes: int | None
    detail: Mapping[str, Json]
    seconds: int
    synthetic: bool

    def as_dict(self) -> dict[str, Json]:
        held: dict[str, Json] = {name: getattr(self, name) for name in FIELDS}
        held["detail"] = _sorted(dict(self.detail))
        return held

    def canonical(self) -> str:
        """The line as it is written: one line, fields in a fixed order, no spaces."""
        return json.dumps(
            self.as_dict(), ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )

    @property
    def day(self) -> str:
        return self.at[:10]

    @property
    def decides(self) -> bool:
        """True when the line answers the question of its item."""
        return not self.part and self.answer not in (SKIP, UNDO, MOVE)


def by_rule(line: Line) -> str:
    """The rule that settled the item of a line, or nothing where a person answered it.

    The desk writes such a line when the founder adopts a rule, and names the rule in
    its detail. Only the desk can: a request may send no detail but what the item holds.
    The founder's own answer to a rule names the rule too, and is a person's answer.
    """
    rule = line.detail.get(RULE)
    return rule if isinstance(rule, str) and line.queue != OF_RULES else ""


def _sorted(value: Json) -> Json:
    if isinstance(value, dict):
        return {key: _sorted(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted(each) for each in value]
    return value


def plain(text: str) -> bool:
    """True when a text is one line of plain words, in whatever language."""
    return not any(unicodedata.category(each) in NOT_PLAIN for each in text)


def _refuse(_: str) -> NoReturn:
    raise ValueError


def _load(raw: bytes) -> object:
    """What a line of JSON holds. NaN and the infinities are not JSON, and are refused."""
    return cast(object, json.loads(raw.decode("utf-8"), parse_constant=_refuse))


def _check(line: Line) -> None:
    """Refuse a line that is not as section 3 gives it. It is run before a line is written too."""
    whole = (line.n, line.seconds, *(() if line.undoes is None else (line.undoes,)))
    words = (line.at, line.reviewer, line.queue, line.question, line.item, line.rev)
    flags = (line.second, line.settles, line.synthetic)
    if not (
        all(type(each) is int for each in whole)
        and all(type(each) is str for each in (*words, line.part, line.answer, line.note))
        and all(type(each) is bool for each in flags)
        and isinstance(cast(object, line.detail), dict)
    ):
        raise Broken("a field is of the wrong kind")
    if line.n < 1 or not 0 <= line.seconds <= SECONDS_LIMIT:
        raise Broken("a number is out of range")
    try:
        datetime.strptime(line.at, AT)
    except ValueError as error:
        raise Broken("the time is not a time") from error
    if not (REVIEWER.fullmatch(line.reviewer) and QUEUE.fullmatch(line.queue)):
        raise Broken("the reviewer or the queue is not a label")
    if not (REV.fullmatch(line.rev) and line.question and line.answer):
        raise Broken("the question, the answer or the revision is missing")
    if not 0 < len(line.item) <= ID_LIMIT or len(line.part) > ID_LIMIT:
        raise Broken("the item or the part is too long, or missing")
    if len(line.note) > NOTE_LIMIT:
        raise Broken("the note is too long")
    if not plain(line.note):
        raise Broken("the note is not one line of plain text")
    if (line.answer == UNDO) != (line.undoes is not None):
        raise Broken("only an undo names a line it takes back")
    if line.undoes is not None and not 1 <= line.undoes < line.n:
        raise Broken("an undo takes back a line written before it")
    if (line.answer == MOVE) != bool(line.part) and line.answer != UNDO:
        raise Broken("a move names a part, and nothing else does")
    if line.settles and line.reviewer != FOUNDER:
        raise Broken("only the founder settles a dispute")
    try:
        line.canonical().encode("utf-8")
    except (ValueError, TypeError) as error:
        raise Broken("the line cannot be written as JSON") from error


def parse(raw: bytes) -> Line:
    """The decision one line of a file holds. Raises `Broken` for anything else."""
    try:
        held = _load(raw)
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        raise Broken("not a line of JSON") from error
    if not isinstance(held, dict):
        raise Broken("not an object")
    fields = cast(dict[str, object], held)
    if set(fields) != set(FIELDS):
        raise Broken("the fields are not those of a line")
    # What each field holds is checked next: a file can hold anything.
    line = Line(**cast(dict[str, Any], fields))
    _check(line)
    return line


# A file of lines


@dataclass(frozen=True, slots=True)
class Read:
    """What a file of decisions holds."""

    # The lines that can be read, in the order of their numbers.
    lines: tuple[Line, ...] = ()
    # How many lines on disk cannot be read. They are kept, and never applied.
    broken: int = 0
    # True when the file ends in half a line: a fault stopped the last write.
    torn: bool = False
    # How many lines the file holds, read or not.
    count: int = 0
    # How many half lines were written again whole. They are not counted as broken:
    # a fault cut the line short, the page sent the answer again, and nothing was lost.
    mended: int = 0

    @property
    def last_number(self) -> int:
        return max(self.count, max((line.n for line in self.lines), default=0))


def read_bytes(data: bytes) -> Read:
    """Read a file's bytes. Pure: the same bytes give the same lines."""
    torn = bool(data) and not data.endswith(b"\n")
    rows = data.split(b"\n")
    if not torn:
        rows = rows[:-1]
    found: dict[int, list[Line]] = {}
    broken = mended = 0
    # The item of a half line that waits to be written again whole.
    cut_short: str | None = None
    for row in rows:
        if not row.strip():
            continue
        try:
            line = parse(row)
        except Broken:
            broken += 1
            cut_short = _item_of_half(row)
            continue
        if cut_short is not None and line.item == cut_short:
            broken, mended = broken - 1, mended + 1
        cut_short = None
        found.setdefault(line.n, []).append(line)
    lines: list[Line] = []
    for n in sorted(found):
        first, *rest = found[n]
        if all(each == first for each in rest):
            # The same line twice over, as when a file was joined to a copy of itself.
            lines.append(first)
        else:
            # Two lines with one number: nobody can say which came first.
            broken += len(found[n])
    return Read(tuple(lines), broken, torn, len(rows), mended)


# The item of a line, where a line was cut short after it was written.
_ITEM: Final = re.compile(rb'"item":("(?:[^"\\]|\\.)*"),')


def _item_of_half(row: bytes) -> str | None:
    """The item of a line that a fault cut short, or None: where the row is whole, and so
    is broken in another way, or was cut before its item was written."""
    try:
        json.loads(row)
    except ValueError:
        found = _ITEM.search(row)
    else:
        return None
    try:
        return None if found is None else cast(str, json.loads(found[1]))
    except ValueError:
        return None


def read(path: Path) -> Read:
    try:
        return read_bytes(path.read_bytes())
    except FileNotFoundError:
        return Read()


def tree_of(private: bool) -> str:
    return PRIVATE_TREE if private else PUBLIC_TREE


def _stands_as(held: os.stat_result) -> tuple[int, int, int]:
    """What says whether a file is as it was: its size, its time of change and its place
    on the disk. A line added changes the first, and a file copied in the last."""
    return held.st_size, held.st_mtime_ns, held.st_ino


class Files:
    """What each file of decisions held when it was last read.

    Every request once read each file whole, and checked every line of it, so an answer
    slowed as the file grew. A file is now read again only when its size, its time of
    change or its place on the disk differs. So a second desk on the folder, a file sent
    back by another reviewer and a file taken away are still seen. Nothing is kept from
    one run to the next: what is held is made from the disk each time the desk starts.
    """

    def __init__(self) -> None:
        self._held: dict[Path, tuple[tuple[int, int, int], Read]] = {}
        self._lock = threading.Lock()

    def read(self, path: Path) -> Read:
        try:
            now = _stands_as(path.stat())
        except FileNotFoundError:
            with self._lock:
                self._held.pop(path, None)
            return Read()
        found = self.known(path, now)
        if found is None:
            try:
                found = read_bytes(path.read_bytes())
            except FileNotFoundError:
                return Read()
            self.keep(path, now, found)
        return found

    def known(self, path: Path, now: tuple[int, int, int]) -> Read | None:
        """What is held of a file, if the file stands as it did when that was read."""
        with self._lock:
            held = self._held.get(path)
        return held[1] if held is not None and held[0] == now else None

    def keep(self, path: Path, now: tuple[int, int, int], held: Read) -> None:
        with self._lock:
            self._held[path] = (now, held)

    def forget(self, path: Path) -> None:
        with self._lock:
            self._held.pop(path, None)


def path_of(data: Path, queue: str, reviewer: str, *, private: bool = False) -> Path:
    """Where one reviewer's lines for one queue are kept."""
    if not (QUEUE.fullmatch(queue) and REVIEWER.fullmatch(reviewer)):
        raise ValueError("a queue and a reviewer are labels")
    return data / tree_of(private) / queue / f"{reviewer}.jsonl"


def read_queue(
    data: Path, queue: str, *, private: bool = False, files: Files | None = None
) -> dict[str, Read]:
    """Every reviewer's lines for one queue, by reviewer. A line filed under another's name
    or another queue is counted as broken."""
    found: dict[str, Read] = {}
    folder = path_of(data, queue, FOUNDER, private=private).parent
    for path in sorted(folder.glob("r*.jsonl")) if folder.is_dir() else ():
        if not REVIEWER.fullmatch(path.stem) or path.is_symlink() or not path.is_file():
            continue
        held = read(path) if files is None else files.read(path)
        own = tuple(
            line for line in held.lines if line.reviewer == path.stem and line.queue == queue
        )
        strays = len(held.lines) - len(own)
        found[path.stem] = Read(own, held.broken + strays, held.torn, held.count, held.mended)
    return found


def misplaced(data: Path, questions: Mapping[str, "Question"]) -> list[str]:
    """The folders of lines that are in the wrong tree: a private queue's among those that
    may be published, or the other way. They are never read from there, so they are said."""
    found: list[str] = []
    for queue, question in questions.items():
        wrong = path_of(data, queue, FOUNDER, private=question.public).parent
        if wrong.is_dir() and any(wrong.glob("r*.jsonl")):
            found.append(f"{wrong.parent.name}/{queue}")
    return sorted(found)


def _write_all(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        view = view[os.write(descriptor, view) :]


def _sync(descriptor: int) -> None:
    """Wait until the bytes are on the disk itself, and not only with the system."""
    full = getattr(fcntl, "F_FULLFSYNC", None)
    if isinstance(full, int):
        try:
            fcntl.fcntl(descriptor, full)
        except OSError:
            # Not every kind of disk takes the stronger call.
            os.fsync(descriptor)
    else:
        os.fsync(descriptor)


def _sync_folder(folder: Path) -> None:
    descriptor = os.open(folder, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def now() -> datetime:
    return datetime.now(UTC)


def append(
    path: Path,
    *,
    reviewer: str,
    queue: str,
    question: str,
    item: str,
    rev: str,
    answer: str,
    synthetic: bool,
    part: str = "",
    note: str = "",
    second: bool = False,
    settles: bool = False,
    undoes: int | None = None,
    detail: Mapping[str, Json] | None = None,
    seconds: int = 0,
    clock: Callable[[], datetime] = now,
    files: Files | None = None,
) -> Line:
    """Write one line at the end of a file, and return it once it is on disk.

    The file is locked while it is read and written, so two desks on one folder
    never give two lines one number. Raises `Broken` and writes nothing if the
    line is not one that could be read back.

    With `files`, the file is not read where it stands as it did when it was last read,
    and what is held of it afterwards is what it now holds.
    """
    if path.stem != reviewer or path.parent.name != queue:
        raise Broken("a line is kept in its own reviewer's file, under its own queue")
    draft = Line(
        # Its number is known once the file is locked. Until then, one that any undo may have.
        n=(undoes or 0) + 1,
        at=clock().astimezone(UTC).strftime(AT),
        reviewer=reviewer,
        queue=queue,
        question=question,
        item=item,
        rev=rev,
        part=part,
        answer=answer,
        note=note,
        second=second,
        settles=settles,
        undoes=undoes,
        detail=dict(detail or {}),
        seconds=seconds,
        synthetic=synthetic,
    )
    # Checked before the disk is touched: a line that is refused leaves no file behind.
    _check(draft)
    folder = path.parent
    if not folder.is_dir():
        folder.mkdir(parents=True, mode=0o700, exist_ok=True)
        # `mkdir` gives the mode to the last folder alone. The tree is the owner's too.
        folder.parent.chmod(0o700)
        _sync_folder(folder.parent)
    is_new = not path.exists()
    descriptor = os.open(path, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        # Under the lock no other desk writes. So what is held is the file itself,
        # where the file stands as it did when that was read.
        known = None if files is None else files.known(path, _stands_as(os.fstat(descriptor)))
        if known is None:
            with open(descriptor, "rb", closefd=False) as file:
                held = read_bytes(file.read())
        else:
            held = known
        line = replace(draft, n=held.last_number + 1)
        _check(line)
        # Half a line is left as it is, and ended, so that this line stands by itself.
        start = b"\n" if held.torn else b""
        if files is not None:
            # If the write fails, what is held is of before it. It is read again.
            files.forget(path)
        _write_all(descriptor, start + line.canonical().encode("utf-8") + b"\n")
        _sync(descriptor)
        if files is not None and not held.torn and not held.broken:
            # A file with a line that cannot be read is read whole each time it grows:
            # whether half a line was mended is known only from the rows themselves.
            after = Read((*held.lines, line), 0, False, held.count + 1, held.mended)
            files.keep(path, _stands_as(os.fstat(descriptor)), after)
    finally:
        os.close(descriptor)
    if is_new:
        _sync_folder(folder)
    return line


def add_to(path: Path, make: Callable[[bytes], bytes]) -> bytes:
    """Add to the end of a file what `make` gives for what the file holds, and return it
    once it is on the disk.

    The file is locked while it is read and written, so two desks on one folder never
    write over each other. `make` is handed the bytes of the file, and what it raises is
    raised here, with nothing written. It is for a file of lines that are not decisions
    of a queue, and are kept as they are: the panel's file of changes.
    """
    folder = path.parent
    if not folder.is_dir():
        folder.mkdir(parents=True, mode=0o700, exist_ok=True)
        folder.parent.chmod(0o700)
        _sync_folder(folder.parent)
    is_new = not path.exists()
    descriptor = os.open(path, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        with open(descriptor, "rb", closefd=False) as file:
            held = file.read()
        added = make(held)
        _write_all(descriptor, added)
        _sync(descriptor)
    finally:
        os.close(descriptor)
    if is_new:
        _sync_folder(folder)
    return added


# The kept copy. The lines are under `data/raw/`, which git ignores, so one `git clean`
# would take forty hours of decisions. Each line is written to a second folder too,
# outside the repository, before the desk answers.

# How much of the end of the kept copy is held against the file each time a line is
# added. The two are compared in full when the desk starts.
TAIL: Final = 256


def keep_up(file: Path, copy: Path) -> int:
    """Write to the kept copy what it lacks of a file of decisions, and wait until it is on
    the disk. Returns how many lines were written. Raises `Differ`, and writes nothing, if
    the copy holds more than the file, or ends otherwise: then the file has lost lines,
    and the copy is the only place they are.

    It reads the end of each and not the whole, so that a long file costs no more than a
    short one. `compare` reads the whole, and is run when the desk starts.
    """
    folder = copy.parent
    if not folder.is_dir():
        folder.mkdir(parents=True, mode=0o700, exist_ok=True)
        folder.parent.chmod(0o700)
    descriptor = os.open(copy, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        has = os.fstat(descriptor).st_size
        try:
            with file.open("rb") as held:
                held.seek(max(0, has - TAIL))
                end, lacks = held.read(min(has, TAIL)), held.read()
        except FileNotFoundError:
            end, lacks = b"", b""
        if len(end) < min(has, TAIL) or end != os.pread(descriptor, len(end), has - len(end)):
            raise Differ("the kept copy holds what the file does not")
        if lacks:
            _write_all(descriptor, lacks)
            _sync(descriptor)
    finally:
        os.close(descriptor)
    return lacks.count(b"\n")


@dataclass(frozen=True, slots=True)
class Compared:
    """How the kept copy stands beside the folder of decisions, file by file. Each file is
    named by its path from the folder, which holds a queue and a label and no word of a line."""

    # The copy lacks lines the folder holds. It is brought up when the desk starts.
    behind: tuple[str, ...] = ()
    # The copy holds lines the folder lacks: the folder has lost them.
    ahead: tuple[str, ...] = ()
    # Neither begins with the other.
    differ: tuple[str, ...] = ()


def _lines_under(folder: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for tree in (PUBLIC_TREE, PRIVATE_TREE):
        for path in sorted((folder / tree).glob("*/r*.jsonl")):
            if path.is_file() and not path.is_symlink():
                found[str(path.relative_to(folder))] = path
    return found


def compare(data: Path, keep: Path) -> Compared:
    """Compare every file of decisions with its kept copy, byte for byte."""
    mine, kept = _lines_under(data), _lines_under(keep)
    behind: list[str] = []
    ahead: list[str] = []
    differ: list[str] = []
    for name in sorted({*mine, *kept}):
        held = mine[name].read_bytes() if name in mine else b""
        has = kept[name].read_bytes() if name in kept else b""
        if held == has:
            continue
        (behind if held.startswith(has) else ahead if has.startswith(held) else differ).append(name)
    return Compared(tuple(behind), tuple(ahead), tuple(differ))


# Which line stands


def _by_number(line: Line) -> int:
    return line.n


def live(lines: Iterable[Line]) -> list[Line]:
    """The lines that no later line undoes, in the order they were written, undos left out.

    An undo that is itself undone takes nothing back: the line it named stands again.
    """
    ordered = sorted(lines, key=_by_number)
    known = {line.n for line in ordered}
    undone: set[int] = set()
    for line in reversed(ordered):
        if line.answer == UNDO and line.n not in undone and line.undoes in known:
            undone.add(line.undoes)
    return [line for line in ordered if line.n not in undone and line.answer != UNDO]


@dataclass(frozen=True, slots=True)
class Standing:
    """What stands of one reviewer's lines in one queue."""

    # By item: the answer that stands. A skip is an answer here.
    answers: Mapping[str, Line]
    # By item, then by part: the move that stands.
    moves: Mapping[str, Mapping[str, Line]]
    # The line an undo would take back, if there is one. It is never a line that a rule
    # wrote: those are taken back together, when the rule is.
    last: Line | None


NOTHING: Final = Standing({}, {}, None)


def standing(lines: Iterable[Line]) -> Standing:
    """For each item and part: the last line that no later line undoes."""
    answers: dict[str, Line] = {}
    moves: dict[str, dict[str, Line]] = {}
    last: Line | None = None
    for line in live(lines):
        last = last if by_rule(line) else line
        if line.part:
            moves.setdefault(line.item, {})[line.part] = line
        else:
            answers[line.item] = line
    return Standing(answers, moves, last)


# Items and questions


@dataclass(frozen=True, slots=True)
class Item:
    id: str
    rev: str
    group: str
    flags: tuple[str, ...]
    picks: tuple[str, ...] | None
    # The item as its file holds it, which is what the page is given.
    held: Mapping[str, Json]


@dataclass(frozen=True, slots=True)
class Items:
    queue: str
    question: str
    synthetic: bool
    items: tuple[Item, ...]
    by_id: Mapping[str, Item]


@dataclass(frozen=True, slots=True)
class Question:
    queue: str
    # The queue and the version of its question, as a line holds it: `names@1`.
    version: str
    title: str
    answers: tuple[str, ...]
    adds: frozenset[str]
    # The question as its file holds it, which is what the page is given.
    held: Mapping[str, Json]
    # Whether its lines may be published. A file of questions must say.
    public: bool = True
    # The queues whose decisions this one is made from: it waits on what is left of them.
    after: tuple[str, ...] = ()
    # Whether a reviewer other than the founder is asked to work it.
    open_to_all: bool = True
    # The key of an item's preset that says which part it is of, where one answer may be
    # given to every item of a part at once: a rater who does not know an area says so
    # once, and not once for each vibe. None where there is no such answer.
    covers: str | None = None

    @property
    def private(self) -> bool:
        return not self.public


def _object(raw: bytes, what: str) -> dict[str, Json]:
    try:
        held = _load(raw)
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        raise Unfit(f"{what} is not JSON") from error
    if not isinstance(held, dict):
        raise Unfit(f"{what} is not an object")
    return cast(dict[str, Json], held)


def _words(value: Json, what: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(each, str) for each in value):
        raise Unfit(f"{what} is not a list of words")
    return tuple(cast(list[str], value))


def _item(held: dict[str, Json], what: str) -> Item:
    if frozenset(held) != ITEM_KEYS:
        raise Unfit(f"{what} does not have the keys of an item, and no others")
    name, rev, group = held["id"], held["rev"], held["group"]
    if not (isinstance(name, str) and 0 < len(name) <= ID_LIMIT):
        raise Unfit(f"{what} has no id, or one that is too long")
    if not (isinstance(rev, str) and REV.fullmatch(rev) and isinstance(group, str) and group):
        raise Unfit(f"{what} has no revision of 12 hex digits, or no group")
    if not isinstance(held["preset"], dict) or not isinstance(held["fill"], dict):
        raise Unfit(f"{what} holds a preset or a fill that is not an object")
    picks = None if held["picks"] is None else _words(held["picks"], f"picks of {what}")
    return Item(name, rev, group, _words(held["flags"], f"flags of {what}"), picks, held)


def read_items(path: Path) -> Items:
    """The items of one queue. Raises `Unfit`, which names the file and the line, not a value."""
    rows = [row for row in path.read_bytes().split(b"\n") if row.strip()]
    if not rows:
        raise Unfit(f"{path.name} is empty")
    header = _object(rows[0], f"line 1 of {path.name}")
    if frozenset(header) != HEADER_KEYS or header["desk"] != DESK:
        raise Unfit(f"line 1 of {path.name} is not the first line of a file of items")
    queue, question, synthetic = header["queue"], header["question"], header["synthetic"]
    if queue != path.stem or not isinstance(queue, str) or not QUEUE.fullmatch(queue):
        raise Unfit(f"{path.name} does not hold the queue it is named for")
    if not isinstance(question, str) or not isinstance(synthetic, bool):
        raise Unfit(f"line 1 of {path.name} does not say which question, or which city")
    items = [
        _item(_object(row, f"line {at} of {path.name}"), f"line {at} of {path.name}")
        for at, row in enumerate(rows[1:], start=2)
    ]
    by_id = {item.id: item for item in items}
    if len(by_id) != len(items) or header["count"] != len(items):
        raise Unfit(f"{path.name} holds an item twice, or not as many as it says")
    return Items(queue, question, synthetic, tuple(items), by_id)


def _question(held: dict[str, Json], what: str) -> Question:
    queue, title = held.get("id"), held.get("title")
    answers, adds = held.get("answers"), held.get("adds")
    if not (isinstance(queue, str) and QUEUE.fullmatch(queue) and isinstance(title, str)):
        raise Unfit(f"{what} has no id or no title")
    if not isinstance(answers, list) or not 0 < len(answers) <= 9:
        raise Unfit(f"{what} does not have from one to nine answers")
    codes: list[str] = []
    for answer in answers:
        code = answer.get("code") if isinstance(answer, dict) else None
        if not isinstance(code, str) or not code or code in (SKIP, MOVE, UNDO, RULE, *codes):
            raise Unfit(f"{what} has an answer with no code, or a code used twice")
        codes.append(code)
    version = held.get("question", f"{queue}@{held.get('version', 1)}")
    if not isinstance(version, str) or not version.startswith(f"{queue}@"):
        raise Unfit(f"{what} does not say which version of the question it is")
    added = frozenset(_words([] if adds is None else adds, f"adds of {what}"))
    public = held.get("public")
    if type(public) is not bool:
        # Left unsaid, a private line could be taken for one that may be published.
        raise Unfit(f"{what} does not say whether its lines may be published")
    after = _words(held.get("after", []), f"after of {what}")
    open_to = held.get("open_to", OPEN_TO_ALL)
    if open_to not in (OPEN_TO_ALL, OPEN_TO_FOUNDER) or queue in after:
        raise Unfit(f"{what} does not say who works it, or waits on itself")
    whole = (queue, version, title, tuple(codes), added, held, public, after)
    return Question(*whole, open_to == OPEN_TO_ALL, _covers(held.get("covers"), codes, what))


def _covers(held: Json, codes: Sequence[str], what: str) -> str | None:
    """The key by which an answer covers a part, or None. Raises `Unfit`."""
    if held is None:
        return None
    by, code, label = (
        (held.get(key) for key in ("by", "code", "label"))
        if isinstance(held, dict)
        else (None, None, None)
    )
    if not (isinstance(by, str) and by and code in codes and isinstance(label, str) and label):
        raise Unfit(f"{what} covers a part with an answer it does not have, or names no part")
    return by


def read_questions(path: Path) -> dict[str, Question]:
    """The question of every queue, in the order the file gives them."""
    listed = _object(path.read_bytes(), path.name).get("queues")
    if not isinstance(listed, list) or not listed:
        raise Unfit(f"{path.name} lists no queue")
    found: dict[str, Question] = {}
    for at, each in enumerate(cast(list[object], listed), start=1):
        if not isinstance(each, dict):
            raise Unfit(f"queue {at} of {path.name} is not an object")
        question = _question(cast(dict[str, Json], each), f"queue {at} of {path.name}")
        if question.queue in found:
            raise Unfit(f"{path.name} holds a queue twice")
        found[question.queue] = question
    return found


# What stands between reviewers


def fresh(line: Line, item: Item, question: Question) -> bool:
    """False when the item or the question has changed since the line was written."""
    return line.rev == item.rev and line.question == question.version


@dataclass(frozen=True, slots=True)
class Verdict:
    """What the reviewers' answers to one item come to."""

    # `open`, `done` or `disputed`.
    state: str
    # The line whose answer is applied, when the state is `done`.
    applied: Line | None
    # Every reviewer whose answer is the one applied, in order.
    by: tuple[str, ...]
    # Each reviewer's answer that stands, skips and stale lines left out.
    answers: Mapping[str, Line]


def verdict(item: Item, question: Question, stands: Mapping[str, Standing]) -> Verdict:
    """What is decided of an item. Where answers differ nothing is, until the founder settles."""
    rule = rule_of(question.queue)
    answers: dict[str, Line] = {}
    for reviewer in sorted(stands, key=number_of):
        line = stands[reviewer].answers.get(item.id)
        if line is None or line.answer in (SKIP, RULE) or not fresh(line, item, question):
            continue
        if rule == ALONE and reviewer != FOUNDER:
            continue
        answers[reviewer] = line
    if not answers:
        return Verdict(OPEN, None, (), answers)
    # Only those who decided are counted, where anybody did. So a founder who does not
    # know the ground throws away no work of the reviewer who does, and an area is
    # never said to be checked by a person who said they could not check it.
    decided = {name: line for name, line in answers.items() if line.answer not in NOT_KNOWN}
    counted = decided or answers
    founder = counted.get(FOUNDER)
    first = founder or next(iter(counted.values()))
    agree = tuple(name for name, line in counted.items() if line.answer == first.answer)
    if len(agree) < len(counted) and not (founder and founder.settles):
        return Verdict(DISPUTED, None, (), answers)
    return Verdict(DONE, first, agree, answers)


def state_of(reviewer: str, item: Item, question: Question, stands: Mapping[str, Standing]) -> str:
    """The state of an item for one reviewer. Another's answer shows only once your own stands."""
    mine = stands.get(reviewer, NOTHING).answers.get(item.id)
    if mine is None:
        return OPEN
    if not fresh(mine, item, question):
        return STALE
    if mine.answer == SKIP:
        return SKIPPED
    if rule_of(question.queue) == TOGETHER and verdict(item, question, stands).state == DISPUTED:
        return DISPUTED
    return DONE


# An answer that a build will set aside. The desk cannot take the ground from under an
# area, nor an area from under the names given to it. So an answer that turns the name
# of such an area down is saved, and the step that makes a build's files sets it aside
# until the draft is made again from the answers. A question says which answers turn a
# name down, under `set_aside`, and an item says what its area holds, in its preset.
SET_ASIDE, HOLDS = "set_aside", "holds"


def waits_for_a_draft(item: Item, question: Question, line: Line | None) -> bool:
    """Whether an answer to an item is one that a build will set aside for now."""
    held, preset = question.held.get(SET_ASIDE), item.held.get("preset")
    if line is None or not isinstance(held, dict) or not isinstance(preset, dict):
        return False
    answers = held.get("answers")
    return bool(preset.get(HOLDS)) and isinstance(answers, list) and line.answer in answers


def set_aside(
    reviewer: str,
    items: Items,
    question: Question,
    stands: Mapping[str, Standing],
    *,
    own: bool = False,
) -> int:
    """How many of a reviewer's answers that stand will be set aside for now. With `own`,
    only those the reviewer gave: what a rule settled is counted with the rule's."""
    mine = stands.get(reviewer, NOTHING).answers
    return sum(
        1
        for item in items.items
        if state_of(reviewer, item, question, stands) == DONE
        and waits_for_a_draft(item, question, mine.get(item.id))
        and not (own and by_rule(mine[item.id]))
    )


def moves_of(
    reviewer: str, item: Item, question: Question, stands: Mapping[str, Standing]
) -> list[Line]:
    """A reviewer's moves on an item that stand, in the order of their parts."""
    held = stands.get(reviewer, NOTHING).moves.get(item.id, {})
    return [held[part] for part in sorted(held) if fresh(held[part], item, question)]


# Progress


@dataclass(frozen=True, slots=True)
class Progress:
    """How far one reviewer is through one queue. Worked out from the lines alone."""

    total: int
    done: int
    # Of those done: how many the reviewer called wrong, and how many they could not judge.
    wrong: int
    not_known: int
    skipped: int
    stale: int
    disputed: int
    # Of those done: how many a rule settled that the founder adopted, and no person read.
    by_rule: int
    # Items that carry a flag, and how many of those are not yet done.
    flagged: int
    flagged_left: int
    # Items whose answer asks for a second reviewer.
    second: int
    # The median time on screen of the last 50 answers, or None before the first.
    median_seconds: int | None
    # Answers written in the hour up to the newest line. Not the hour up to now.
    last_hour: int

    @property
    def left(self) -> int:
        return self.total - self.done

    def as_dict(self) -> dict[str, Json]:
        return {
            "total": self.total,
            "done": self.done,
            "wrong": self.wrong,
            "not_known": self.not_known,
            "skipped": self.skipped,
            "stale": self.stale,
            "disputed": self.disputed,
            "by_rule": self.by_rule,
            "flagged": self.flagged,
            "flagged_left": self.flagged_left,
            "second": self.second,
            "median_seconds": self.median_seconds,
            "last_hour": self.last_hour,
        }


def pace(lines: Sequence[Line]) -> tuple[int | None, int]:
    """The median seconds of the last 50 answers, and the answers of the last hour.

    The hour ends at the newest time any line holds, so it is the last hour of work.
    If the clock went backwards, a line written later may hold an earlier time: the
    count is then short, and never below nothing.
    """
    answers = [line for line in sorted(lines, key=_by_number) if line.decides and not by_rule(line)]
    if not answers:
        return None, 0
    median = round(statistics.median(line.seconds for line in answers[-PACE_LINES:]))
    # A time is written in one way, to the second and in UTC, so the later of two
    # times is the later of their words. Only the newest is read as a time.
    newest = max(line.at for line in answers)
    edge = (datetime.strptime(newest, AT) - PACE_WINDOW).strftime(AT)
    return median, sum(1 for line in answers if line.at > edge)


def progress(
    reviewer: str, items: Items, question: Question, reads: Mapping[str, Read]
) -> Progress:
    stands = {name: standing(held.lines) for name, held in reads.items()}
    mine = stands.get(reviewer, NOTHING)
    states = {item.id: state_of(reviewer, item, question, stands) for item in items.items}
    count = Counter(states.values())
    flagged = [item for item in items.items if item.flags]
    median, last_hour = pace(reads[reviewer].lines if reviewer in reads else ())
    said = Counter(mine.answers[name].answer for name, state in states.items() if state == DONE)
    return Progress(
        total=len(items.items),
        done=count.get(DONE, 0),
        wrong=sum(said[answer] for answer in CALLED_WRONG),
        not_known=sum(said[answer] for answer in NOT_KNOWN),
        skipped=count.get(SKIPPED, 0),
        stale=count.get(STALE, 0),
        disputed=count.get(DISPUTED, 0),
        by_rule=sum(
            1 for name, state in states.items() if state == DONE and by_rule(mine.answers[name])
        ),
        flagged=len(flagged),
        flagged_left=sum(1 for item in flagged if states[item.id] != DONE),
        second=sum(
            1
            for item in items.items
            if states[item.id] in (DONE, DISPUTED, SKIPPED) and mine.answers[item.id].second
        ),
        median_seconds=median,
        last_hour=last_hour,
    )


def known_by(stands: Standing) -> dict[str, str]:
    """How well a reviewer says they know each borough, by the borough's group."""
    return {name: line.answer for name, line in stands.answers.items() if line.answer in KNOWN}


def order_for(
    reviewer: str,
    items: Items,
    stands: Mapping[str, Standing],
    known: Mapping[str, str] | None = None,
) -> list[Item]:
    """The order a reviewer is shown items in. What the founder marked for a second
    reviewer comes first for everyone else. Then the boroughs the reviewer knows well,
    those they know a little, those they did not mark, and those they do not know. Within
    each, the order of the file."""
    marked = known or {}
    asked = (
        set[str]()
        if reviewer == FOUNDER
        else {name for name, line in stands.get(FOUNDER, NOTHING).answers.items() if line.second}
    )

    def place(item: Item) -> tuple[bool, int]:
        how = marked.get(item.group, marked.get(item.id, ""))
        return item.id not in asked, KNOWN.index(how if how in KNOWN else "")

    return sorted(items.items, key=place)


def next_item(
    reviewer: str,
    items: Items,
    question: Question,
    stands: Mapping[str, Standing],
    after: str | None = None,
    known: Mapping[str, str] | None = None,
) -> str | None:
    """The next item to show: the first that is open after this one, going round to the
    start. When none is open, the first that was skipped. None when all are done."""
    ordered = order_for(reviewer, items, stands, known)
    at = next((index for index, item in enumerate(ordered) if item.id == after), -1)
    around = ordered[at + 1 :] + ordered[: at + 1]
    states = {item.id: state_of(reviewer, item, question, stands) for item in around}
    for wanted in ((OPEN, STALE), (SKIPPED,)):
        for item in around:
            if item.id != after and states[item.id] in wanted:
                return item.id
    return after if after is not None and states.get(after, DONE) != DONE else None
