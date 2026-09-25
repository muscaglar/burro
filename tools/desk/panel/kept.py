"""The file of changes on the disk: where it is, how a line is added, and what it holds.

Each reviewer has a file of their own, `decisions/changes/<reviewer>.jsonl` in the
desk's folder of data. It lies with the decisions, so that the second copy the desk
keeps of every decision holds it too. It is no queue, and no line of it is a line of
a queue: `burro_pipeline.changes` says what a line holds, and is the one reader of it.

A line is on the disk, and in the kept copy, before `add` returns. A file is read
whole each time it is asked for: it holds tens of lines, and never thousands.

See docs/design/panel.md, section 3.
"""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from burro_pipeline import changes
from burro_pipeline.changes import Change, ChangesError, What

from desk import records

# The folder of the files of changes, beside the folders of the queues. No queue may bear
# the name.
FOLDER: Final = "changes"
DAY: Final = "%Y-%m-%d"


class Unreadable(Exception):
    """A file of changes that cannot be read whole. It names the file, the line and the rule."""

    def __init__(self, reviewer: str, error: ChangesError) -> None:
        super().__init__(
            f"{records.PUBLIC_TREE}/{FOLDER}/{reviewer}.jsonl cannot be read: line {error.line} "
            f"breaks the rule {error.rule}. Mend the line by hand, or move the file away"
        )
        self.reviewer, self.line, self.rule = reviewer, error.line, error.rule


def path_of(data: Path, reviewer: str) -> Path:
    """Where one reviewer's file of changes is kept."""
    return records.path_of(data, FOLDER, reviewer)


def read(data: Path, reviewer: str) -> tuple[Change, ...]:
    """One reviewer's lines, in the order they were written. Raises `Unreadable`."""
    try:
        return changes.read(path_of(data, reviewer).read_bytes())
    except FileNotFoundError:
        return ()
    except ChangesError as error:
        raise Unreadable(reviewer, error) from None


def read_all(data: Path) -> dict[str, tuple[Change, ...]]:
    """Every reviewer's lines, by reviewer, the founder first. Raises `Unreadable`."""
    folder = path_of(data, records.FOUNDER).parent
    found = sorted(
        (
            path.stem
            for path in (folder.glob("r*.jsonl") if folder.is_dir() else ())
            if records.REVIEWER.fullmatch(path.stem) and path.is_file() and not path.is_symlink()
        ),
        key=records.number_of,
    )
    return {reviewer: read(data, reviewer) for reviewer in found}


def add(
    data: Path,
    reviewer: str,
    what: What,
    of: str,
    *,
    why: str,
    was: Any = None,
    now: Any = None,
    takes_back: int | None = None,
    clock: Callable[[], datetime] = records.now,
    keep: Path | None = None,
) -> Change:
    """Write one line at the end of a reviewer's file, and return it once it is on the disk.

    Raises `ChangesError`, and writes nothing, for a line that a build could not read.
    Raises `Unreadable`, and writes nothing, where the file cannot be read as it stands.
    """
    day = clock().astimezone(UTC).strftime(DAY)
    draft = Change(
        n=1, on=day, by=reviewer, what=what, of=of, was=was, now=now, why=why, takes_back=takes_back
    )
    # Checked before the disk is touched: a line that is refused leaves no file behind.
    rule = changes.broken(draft)
    if rule is not None:
        raise ChangesError(0, rule)
    written: list[Change] = []

    def make(held: bytes) -> bytes:
        try:
            before = changes.read(held)
        except ChangesError as error:
            raise Unreadable(reviewer, error) from None
        line = draft.model_copy(update={"n": len(before) + 1})
        added = changes.line(line)
        # The file is read as a build reads it, with the line in it, before it is written.
        changes.read(held + added)
        written.append(line)
        return added

    path = path_of(data, reviewer)
    records.add_to(path, make)
    if keep is not None:
        records.keep_up(path, keep / path.relative_to(data))
    return written[0]


def as_shown(change: Change) -> dict[str, Any]:
    """A line as the page is given it."""
    return {name: getattr(change, name) for name in changes.FIELDS} | {"what": change.what.value}


def stands_for(lines: Mapping[str, tuple[Change, ...]], reviewer: str) -> tuple[Change, ...]:
    """The lines of one reviewer that stand."""
    return changes.standing(lines.get(reviewer, ()))
