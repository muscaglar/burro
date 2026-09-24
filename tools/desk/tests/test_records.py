"""The record of a decision: what is written, what is read back, and which line stands.

Every name, id and note here is made up. No socket is opened.
"""

import json
import random
import stat
import threading
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from desk import records
from desk.records import (
    DISPUTED,
    DONE,
    FIELDS,
    OPEN,
    SKIPPED,
    STALE,
    Broken,
    Item,
    Items,
    Line,
    Question,
    Read,
    Unfit,
    append,
    live,
    next_item,
    pace,
    parse,
    path_of,
    progress,
    read,
    read_bytes,
    read_items,
    read_questions,
    read_queue,
    standing,
    state_of,
    verdict,
)

REV, OLD_REV = "9f2c41d07ab3", "000000000000"
# Some readers take it for the end of a line. A file of lines must not.
LINE_SEPARATOR = chr(0x2028)
START = datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC)
# The example of docs/design/desk.md, section 3, as it is written there.
EXAMPLE = (
    '{"n":412,"at":"2026-10-06T21:14:09Z","reviewer":"r1","queue":"names",'
    '"question":"names@1","item":"n:syn-n0004","rev":"9f2c41d07ab3","part":"",'
    '"answer":"area","note":"","second":false,"settles":false,"undoes":null,'
    '"detail":{"of":[],"pick":"Dulcimer Green"},"seconds":31,"synthetic":true}'
)


def ticking(start: datetime = START, step: int = 30) -> Iterator[datetime]:
    at = start
    while True:
        yield at
        at += timedelta(seconds=step)


def line(n: int, item: str = "syn-n0001", answer: str = "right", **changed: Any) -> Line:
    """A line of the queue `borders`, as `r1` would write it."""
    held: dict[str, Any] = {
        "n": n,
        "at": (START + timedelta(seconds=30 * n)).strftime(records.AT),
        "reviewer": "r1",
        "queue": "borders",
        "question": "borders@1",
        "item": item,
        "rev": REV,
        "part": "",
        "answer": answer,
        "note": "",
        "second": False,
        "settles": False,
        "undoes": None,
        "detail": {},
        "seconds": 20,
        "synthetic": True,
    }
    return Line(**{**held, **changed})


def undo(n: int, of: Line) -> Line:
    return replace(of, n=n, answer="undo", undoes=of.n, note="", seconds=0)


def move(n: int, item: str, cell: str, to: str, **changed: Any) -> Line:
    detail = {"from": item, "to": to}
    return line(n, item, "move", part=cell, detail=detail, **changed)


def as_file(*lines: Line) -> bytes:
    return b"".join(each.canonical().encode() + b"\n" for each in lines)


def item(name: str, flags: tuple[str, ...] = (), rev: str = REV) -> Item:
    return Item(name, rev, "quillhaven", flags, None, {"id": name, "rev": rev})


def items(*held: Item, queue: str = "borders") -> Items:
    return Items(queue, f"{queue}@1", True, held, {each.id: each for each in held})


def question(queue: str = "borders", answers: tuple[str, ...] = ("right", "wrong")) -> Question:
    return Question(queue, f"{queue}@1", queue.title(), answers, frozenset(), {"id": queue})


BORDERS = question()
A, B, C = item("syn-n0001"), item("syn-n0002"), item("syn-n0003")


def stands(**lines_of: list[Line]) -> dict[str, records.Standing]:
    return {reviewer: standing(lines) for reviewer, lines in lines_of.items()}


def write(path: Path, **changed: Any) -> Line:
    held: dict[str, Any] = {
        "reviewer": "r1",
        "queue": "borders",
        "question": "borders@1",
        "item": "syn-n0001",
        "rev": REV,
        "answer": "right",
        "synthetic": True,
        "clock": lambda: START,
    }
    return append(path, **{**held, **changed})


@pytest.fixture
def file(tmp_path: Path) -> Path:
    return path_of(tmp_path, "borders", "r1")


# A line


def test_a_line_is_written_as_the_design_writes_it():
    assert parse(EXAMPLE.encode()).canonical() == EXAMPLE


def test_a_line_is_one_line_with_its_fields_in_a_fixed_order():
    odd = f"two\nlines, and a {LINE_SEPARATOR} too"
    written = line(1, note="Thrushcombe Lane.", detail={"to": "b", "from": odd})
    text = written.canonical()
    assert len(text.encode().split(b"\n")) == 1
    assert parse(text.encode()).detail["from"] == odd
    assert tuple(json.loads(text)) == FIELDS
    assert list(json.loads(text)["detail"]) == ["from", "to"]


def test_a_line_read_back_is_the_line_that_was_written():
    written = line(3, note="Thrushcombe Lane is the edge. Café on the corner.", second=True)
    assert parse(written.canonical().encode()) == written


@pytest.mark.parametrize(
    "changed",
    [
        {"n": "1"},
        {"n": 0},
        {"n": True},
        {"seconds": -1},
        {"seconds": 901},
        {"seconds": 1.5},
        {"second": 0},
        {"synthetic": "true"},
        {"at": "2026-10-06 21:14:09"},
        {"at": "2026-13-06T21:14:09Z"},
        {"reviewer": "founder"},
        {"reviewer": "r0"},
        {"reviewer": "r100"},
        {"queue": "../names"},
        {"rev": "9F2C41D07AB3"},
        {"rev": "9f2c"},
        {"item": ""},
        {"item": "x" * 201},
        {"answer": ""},
        {"note": "x" * 501},
        {"detail": []},
        {"undoes": 1},
        {"answer": "undo"},
        {"answer": "undo", "undoes": 2, "n": 2},
        {"answer": "move"},
        {"part": "syn-oa0001"},
        {"settles": True, "reviewer": "r2"},
    ],
)
def test_a_line_that_is_not_as_the_design_gives_it_is_broken(changed: dict[str, Any]):
    held = {**line(1).as_dict(), **changed}
    with pytest.raises(Broken):
        parse(json.dumps(held).encode())


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"not json",
        b"[]",
        b'"a line"',
        b'{"n":1}',
        b"\xff\xfe",
        EXAMPLE.encode()[:-40],
        EXAMPLE.encode().replace(b'"seconds":31', b'"seconds":NaN'),
        EXAMPLE.encode().replace(b'"synthetic":true', b'"synthetic":true,"name":"x"'),
    ],
)
def test_what_is_not_a_line_is_broken(raw: bytes):
    with pytest.raises(Broken):
        parse(raw)


@pytest.mark.parametrize(
    "note",
    [
        "two\nlines",
        "a return\r",
        "a tab\there",
        "an escape \x1b[31m red",
        "a nul \x00",
        "turned round \u202e",
        "joined \u200d",
        f"a line parted {LINE_SEPARATOR} here",
        "a paragraph parted \u2029 here",
    ],
)
def test_a_note_with_a_control_character_is_refused(note: str, file: Path):
    # A note may reach a published table. It is one line of plain text.
    with pytest.raises(Broken):
        parse(json.dumps({**line(1).as_dict(), "note": note}).encode())
    with pytest.raises(Broken):
        write(file, note=note)
    assert not file.exists()


def test_a_note_in_plain_words_of_any_language_is_kept(file: Path):
    note = "Café on the corner of Łódź Street, by the 東 gate."
    assert write(file, note=note).note == note


def test_what_is_wrong_with_a_line_is_said_without_the_line():
    with pytest.raises(Broken) as refusal:
        parse(json.dumps({**line(1).as_dict(), "note": "Zzyzx Parva " * 50}).encode())
    assert "Zzyzx" not in str(refusal.value)


def test_a_reviewer_is_a_label_and_never_a_name(tmp_path: Path):
    with pytest.raises(ValueError, match="labels"):
        path_of(tmp_path, "names", "a-name")
    with pytest.raises(ValueError, match="labels"):
        path_of(tmp_path, "../names", "r1")


# Writing


def test_a_line_is_on_disk_before_append_returns(file: Path, monkeypatch: pytest.MonkeyPatch):
    seen: list[bytes] = []
    real = records._sync  # pyright: ignore[reportPrivateUsage]

    def watched(descriptor: int) -> None:
        seen.append(file.read_bytes())
        real(descriptor)

    monkeypatch.setattr(records, "_sync", watched)
    written = write(file)
    assert seen == [written.canonical().encode() + b"\n"]
    assert file.read_bytes() == seen[0]


def test_lines_are_numbered_from_one_in_the_order_they_are_written(file: Path):
    assert [write(file, item=f"syn-n000{at}").n for at in (1, 2, 3)] == [1, 2, 3]
    assert [each.item for each in read(file).lines] == ["syn-n0001", "syn-n0002", "syn-n0003"]


def test_a_line_holds_the_time_it_was_written_to_the_second_in_utc(file: Path):
    late = datetime(2026, 10, 6, 23, 59, 59, 900000, tzinfo=UTC) + timedelta(hours=1)
    east = late.astimezone(tz=None).astimezone(UTC)
    assert write(file, clock=lambda: east).at == "2026-10-07T00:59:59Z"


def test_a_line_is_never_changed_or_removed(file: Path):
    before = b""
    first = write(file)
    for step in range(6):
        if step % 2:
            write(file, answer="undo", undoes=first.n)
        else:
            write(file, answer="wrong", note="The brook is the edge.")
        after = file.read_bytes()
        assert after.startswith(before) and len(after) > len(before)
        before = after


def test_a_line_that_could_not_be_read_back_is_not_written(file: Path):
    write(file)
    before = file.read_bytes()
    for changed in ({"note": "x" * 501}, {"reviewer": "r2"}, {"note": "\ud800"}, {"rev": "new"}):
        with pytest.raises(Broken):
            write(file, **changed)
    assert file.read_bytes() == before


def test_a_line_that_is_refused_leaves_no_file_behind(file: Path, tmp_path: Path):
    for changed in ({"note": "x" * 501}, {"note": "\ud800"}, {"answer": "undo", "undoes": 0}):
        with pytest.raises(Broken):
            write(file, **changed)
    assert list(tmp_path.iterdir()) == []


def test_a_file_that_ends_in_half_a_line_loses_only_that_line(file: Path):
    first, second = write(file), write(file, item="syn-n0002")
    half = line(3, "syn-n0003").canonical().encode()[:70]
    with file.open("ab") as torn:
        torn.write(half)

    held = read(file)
    assert held.lines == (first, second)
    assert (held.broken, held.torn) == (1, True)

    third = write(file, item="syn-n0004")
    assert third.n == 4
    assert file.read_bytes().count(half + b"\n") == 1, "the half line is kept as it was"
    assert read(file) == Read((first, second, third), broken=1, torn=False, count=4)


def test_a_fault_while_writing_loses_at_most_the_line_being_written(
    file: Path, monkeypatch: pytest.MonkeyPatch
):
    first = write(file)
    real = records._write_all  # pyright: ignore[reportPrivateUsage]

    def fails_half_way(descriptor: int, data: bytes) -> None:
        real(descriptor, data[: len(data) // 2])
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(records, "_write_all", fails_half_way)
    with pytest.raises(OSError, match="No space"):
        write(file, item="syn-n0002")
    monkeypatch.setattr(records, "_write_all", real)

    assert read(file).lines == (first,)
    assert (read(file).broken, read(file).mended) == (1, 0)
    again = write(file, item="syn-n0002")
    assert read(file).lines == (first, again)
    # The page sent the answer again, and it is whole. So nothing was lost, and the
    # half line is no longer a warning that a person learns to pass over.
    assert (read(file).broken, read(file).mended) == (0, 1)


def test_half_a_line_is_mended_only_by_a_whole_line_for_the_same_item(file: Path):
    first = write(file)
    half = line(2, "syn-n0002", note="The lane.").canonical().encode()
    cut_after_the_item = half[: half.index(b'"rev"')]
    cut_before_the_item = half[: half.index(b'"item"')]
    for cut, other, mended in (
        (cut_after_the_item, "syn-n0002", 1),
        (cut_after_the_item, "syn-n0003", 0),
        (cut_before_the_item, "syn-n0002", 0),
    ):
        file.write_bytes(first.canonical().encode() + b"\n" + cut)
        again = write(file, item=other)
        held = read(file)
        assert held.lines == (first, again)
        assert (held.broken, held.mended, held.count) == (1 - mended, mended, 3), (cut, other)


def test_a_line_that_is_whole_and_wrong_is_never_said_to_be_mended(file: Path):
    first = write(file)
    wrong = json.dumps({**line(2, "syn-n0002").as_dict(), "seconds": -1}).encode()
    file.write_bytes(first.canonical().encode() + b"\n" + wrong + b"\n")
    again = write(file, item="syn-n0002")
    held = read(file)
    assert held.lines == (first, again)
    assert (held.broken, held.mended) == (1, 0)


def test_a_file_of_decisions_is_open_to_its_owner_alone(file: Path):
    write(file)
    assert stat.S_IMODE(file.stat().st_mode) == 0o600
    assert stat.S_IMODE(file.parent.stat().st_mode) == 0o700


def test_a_line_is_not_written_through_a_link(file: Path, tmp_path: Path):
    elsewhere = tmp_path / "elsewhere.jsonl"
    elsewhere.write_bytes(b"")
    file.parent.mkdir(parents=True)
    file.symlink_to(elsewhere)
    with pytest.raises(OSError):
        write(file)
    assert elsewhere.read_bytes() == b""


def test_a_line_is_kept_in_its_own_reviewers_file_under_its_own_queue(tmp_path: Path):
    with pytest.raises(Broken):
        write(path_of(tmp_path, "borders", "r2"))
    with pytest.raises(Broken):
        write(path_of(tmp_path, "names", "r1"))
    assert not (tmp_path / "decisions").exists()


def test_two_desks_on_one_folder_never_give_two_lines_one_number(file: Path):
    def work(at: int) -> None:
        for step in range(10):
            write(file, item=f"syn-n{at}{step:03d}")

    threads = [threading.Thread(target=work, args=(at,)) for at in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    held = read(file)
    assert [each.n for each in held.lines] == list(range(1, 41))
    assert held.broken == 0


def test_a_file_that_is_not_there_holds_nothing(file: Path):
    assert read(file) == Read()


def test_the_lines_of_a_private_queue_are_kept_in_a_tree_of_their_own(tmp_path: Path):
    # A copy of `decisions/` made by hand must never take a private line with it.
    public, private = (
        path_of(tmp_path, "names", "r1"),
        path_of(tmp_path, "know", "r1", private=True),
    )
    assert public == tmp_path / "decisions" / "names" / "r1.jsonl"
    assert private == tmp_path / "decisions-private" / "know" / "r1.jsonl"
    written = write(private, queue="know", question="know@1", item="quillhaven", answer="well")
    assert read_queue(tmp_path, "know", private=True) == {"r1": Read((written,), count=1)}
    assert read_queue(tmp_path, "know") == {}
    assert not (tmp_path / "decisions").exists()
    assert stat.S_IMODE(private.stat().st_mode) == 0o600
    assert stat.S_IMODE(private.parent.stat().st_mode) == 0o700


def test_lines_found_in_the_wrong_tree_are_said_and_never_passed_over(tmp_path: Path):
    asked = {
        "names": question("names", ("area",)),
        "know": replace(question("know", ("well",)), public=False),
    }
    assert records.misplaced(tmp_path, asked) == []
    write(path_of(tmp_path, "know", "r1"), queue="know", question="know@1", answer="well")
    write(path_of(tmp_path, "names", "r1", private=True), queue="names", question="names@1")
    assert records.misplaced(tmp_path, asked) == [
        "decisions-private/names",
        "decisions/know",
    ]


# What is held of a file between two requests


def counting(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """How many bytes were read as lines, each time a file was read whole."""
    read: list[int] = []
    real = records.read_bytes

    def counted(data: bytes) -> Read:
        read.append(len(data))
        return real(data)

    monkeypatch.setattr(records, "read_bytes", counted)
    return read


def test_a_file_is_read_again_only_when_it_has_changed(file: Path, monkeypatch: pytest.MonkeyPatch):
    first = write(file)
    files, read_whole = records.Files(), counting(monkeypatch)
    held = files.read(file)
    assert held.lines == (first,) and len(read_whole) == 1
    assert files.read(file) is held and files.read(file) is held
    assert len(read_whole) == 1, "it is not read again while it stands as it was"
    second = write(file, item="syn-n0002")
    assert files.read(file).lines == (first, second)
    assert len(read_whole) == 3, "once by the desk that wrote, and once here"


def test_a_line_written_through_what_is_held_costs_no_reading_of_the_file(
    file: Path, monkeypatch: pytest.MonkeyPatch
):
    files = records.Files()
    written = [write(file, item=f"syn-n{at:04d}", files=files) for at in range(1, 4)]
    read_whole = counting(monkeypatch)
    written.append(write(file, item="syn-n0004", files=files))
    assert files.read(file).lines == tuple(written)
    assert [line.n for line in written] == [1, 2, 3, 4]
    assert read_whole == [], "neither to find its number, nor to read it back"
    assert read(file).lines == tuple(written), "and the disk holds what is held of it"


def test_a_line_written_by_another_desk_is_seen(file: Path):
    mine, theirs = records.Files(), records.Files()
    first = write(file, files=mine)
    second = write(file, item="syn-n0002", files=theirs)
    third = write(file, item="syn-n0003", files=mine)
    assert (first.n, second.n, third.n) == (1, 2, 3), "no two lines have one number"
    assert mine.read(file).lines == theirs.read(file).lines == (first, second, third)


def test_a_file_copied_in_or_taken_away_is_seen(file: Path, tmp_path: Path):
    files = records.Files()
    first = write(file, files=files)
    other = tmp_path / "sent-back" / "borders" / "r1.jsonl"
    theirs = [write(other, item=f"syn-n{at:04d}") for at in (7, 8)]
    other.replace(file)
    assert files.read(file).lines == tuple(theirs) != (first,)
    file.unlink()
    assert files.read(file) == Read()
    again = write(file, files=files)
    assert again.n == 1 and files.read(file).lines == (again,)


def test_half_a_line_is_never_held_as_if_it_were_whole(file: Path):
    files = records.Files()
    first = write(file, files=files)
    whole = line(2, "syn-n0002").canonical().encode()
    with file.open("ab") as torn:
        torn.write(whole[: whole.index(b'"rev"')])
    assert (files.read(file).broken, files.read(file).torn) == (1, True)
    again = write(file, item="syn-n0002", files=files)
    assert again.n == 3
    assert files.read(file) == read(file) == Read((first, again), count=3, mended=1)


def test_pace_is_worked_out_without_reading_the_time_of_every_line(
    monkeypatch: pytest.MonkeyPatch,
):
    held = [line(at, f"syn-n{at:04d}") for at in range(1, 400)]
    parsed: list[str] = []

    class Counted(datetime):
        @classmethod
        def strptime(cls, text: str, how: str) -> datetime:
            parsed.append(text)
            return datetime.strptime(text, how)

    monkeypatch.setattr(records, "datetime", Counted)
    assert pace(held) == (20, 120)
    assert len(parsed) <= 1


# The kept copy


def test_the_kept_copy_is_brought_up_to_the_file(file: Path, tmp_path: Path):
    copy = tmp_path / "kept" / "decisions" / "borders" / "r1.jsonl"
    write(file)
    assert records.keep_up(file, copy) == 1
    assert copy.read_bytes() == file.read_bytes()
    assert stat.S_IMODE(copy.stat().st_mode) == 0o600
    assert stat.S_IMODE(copy.parent.stat().st_mode) == 0o700
    write(file, item="syn-n0002")
    write(file, item="syn-n0003")
    assert records.keep_up(file, copy) == 2
    assert copy.read_bytes() == file.read_bytes()
    assert records.keep_up(file, copy) == 0, "asked again, it writes nothing"


def test_the_kept_copy_is_on_disk_before_it_is_said_to_be_kept(
    file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    synced: list[bytes] = []
    copy = tmp_path / "kept" / "decisions" / "borders" / "r1.jsonl"
    write(file)

    def sync(descriptor: int) -> None:
        synced.append(copy.read_bytes())

    monkeypatch.setattr(records, "_sync", sync)
    records.keep_up(file, copy)
    assert synced == [file.read_bytes()]


def test_a_kept_copy_that_holds_more_than_the_file_is_never_written_over(
    file: Path, tmp_path: Path
):
    # As when `git clean` took the folder of decisions, and the desk was started again.
    copy = tmp_path / "kept" / "decisions" / "borders" / "r1.jsonl"
    write(file)
    write(file, item="syn-n0002")
    records.keep_up(file, copy)
    kept = copy.read_bytes()
    file.unlink()
    write(file, item="syn-n0009")
    with pytest.raises(records.Differ):
        records.keep_up(file, copy)
    assert copy.read_bytes() == kept


def test_the_two_copies_are_compared_file_by_file(tmp_path: Path):
    data, kept = tmp_path / "data", tmp_path / "kept"
    same, behind = path_of(data, "names", "r1"), path_of(data, "borders", "r1")
    ahead = path_of(data, "know", "r1", private=True)
    differs = path_of(data, "kinds", "r1")
    for file, queue in ((same, "names"), (behind, "borders"), (ahead, "know"), (differs, "kinds")):
        write(file, queue=queue, question=f"{queue}@1")
        records.keep_up(file, kept / file.relative_to(data))
    write(behind, item="syn-n0002")
    ahead.unlink()
    differs.write_bytes(differs.read_bytes().replace(b"right", b"wrong"))
    only = path_of(kept, "commons", "r1")
    write(only, queue="commons", question="commons@1")
    found = records.compare(data, kept)
    assert found.behind == ("decisions/borders/r1.jsonl",)
    assert found.ahead == ("decisions-private/know/r1.jsonl", "decisions/commons/r1.jsonl")
    assert found.differ == ("decisions/kinds/r1.jsonl",)
    assert records.compare(data, tmp_path / "nothing-kept-yet") == records.Compared(
        behind=tuple(sorted(str(each.relative_to(data)) for each in (same, behind, differs)))
    )


def test_a_line_filed_under_another_reviewer_is_set_aside(tmp_path: Path):
    mine, theirs = line(1), line(2, reviewer="r2")
    file = path_of(tmp_path, "borders", "r1")
    file.parent.mkdir(parents=True)
    file.write_bytes(as_file(mine, theirs))
    (file.parent / "notes.txt").write_text("not a file of lines")
    (file.parent / "r1-copy.jsonl").write_bytes(as_file(mine))
    assert read_queue(tmp_path, "borders") == {"r1": Read((mine,), broken=1, count=2)}


# Which line stands


def test_the_last_answer_to_an_item_stands():
    held = standing([line(1, answer="right"), line(2, "syn-n0002"), line(3, answer="wrong")])
    assert held.answers["syn-n0001"].answer == "wrong"
    assert held.answers["syn-n0002"].answer == "right"


def test_an_undo_is_a_line_and_the_answer_before_it_stands_again():
    first, second = line(1, answer="right"), line(2, answer="wrong", note="The brook.")
    held = standing([first, second, undo(3, second)])
    assert held.answers["syn-n0001"] == first
    assert held.last == first


def test_an_undo_of_the_only_answer_leaves_the_item_open():
    only = line(1)
    assert standing([only, undo(2, only)]).answers == {}
    assert state_of("r1", A, BORDERS, stands(r1=[only, undo(2, only)])) == OPEN


def test_an_undo_of_an_undo_puts_the_answer_back():
    first = line(1)
    taken_back = undo(2, first)
    put_back = undo(3, taken_back)
    assert standing([first, taken_back]).answers == {}
    assert standing([first, taken_back, put_back]).answers == {"syn-n0001": first}
    and_again = undo(4, put_back)
    assert standing([first, taken_back, put_back, and_again]).answers == {}


def test_an_undo_takes_back_a_move_and_leaves_the_others():
    one, two = (
        move(1, "syn-n0001", "syn-oa0001", "syn-n0002"),
        move(2, "syn-n0001", "syn-oa0002", "syn-n0002"),
    )
    held = standing([one, two, undo(3, two)])
    assert held.moves == {"syn-n0001": {"syn-oa0001": one}}


def test_a_decision_made_twice_counts_once():
    twice = [line(1, answer="right"), line(2, answer="right")]
    assert list(standing(twice).answers) == ["syn-n0001"]
    assert progress("r1", items(A, B), BORDERS, {"r1": Read(tuple(twice))}).done == 1


def test_the_same_line_twice_in_a_file_is_read_once():
    first, second = line(1), line(2, "syn-n0002")
    joined = read_bytes(as_file(first, second) + as_file(first, second))
    assert joined.lines == (first, second)
    assert joined.broken == 0


def test_two_lines_with_one_number_are_both_set_aside():
    held = read_bytes(as_file(line(1, answer="right"), line(1, answer="wrong"), line(2)))
    assert held.lines == (line(2),)
    assert held.broken == 2


def test_lines_in_any_order_give_the_same_answers():
    first = line(1, answer="right")
    written = [
        first,
        move(2, "syn-n0002", "syn-oa0001", "syn-n0003"),
        line(3, "syn-n0002", answer="wrong", note="The brook is the edge."),
        undo(4, first),
        line(5, answer="wrong", note="The lane."),
        line(6, "syn-n0003", answer="skip"),
    ]
    rows = as_file(*written).splitlines(keepends=True)
    expected = standing(read_bytes(b"".join(rows)).lines)
    shuffled = random.Random(7)  # noqa: S311 a fixed order, for a test
    for _ in range(20):
        shuffled.shuffle(rows)
        assert standing(read_bytes(b"".join(rows)).lines) == expected


def test_a_clock_that_goes_backwards_changes_no_answer(file: Path):
    clock = iter([START, START - timedelta(hours=3), START - timedelta(days=400)])
    for answer in ("right", "wrong", "unknown"):
        write(file, answer=answer, note="The brook.", clock=lambda: next(clock))
    held = read(file)
    assert [each.at for each in held.lines] == sorted(
        (each.at for each in held.lines), reverse=True
    )
    assert standing(held.lines).answers["syn-n0001"].answer == "unknown"
    assert standing(held.lines).last == held.lines[-1]


def test_a_skip_stands_as_not_decided():
    held = stands(r1=[line(1, answer="skip")])
    assert state_of("r1", A, BORDERS, held) == SKIPPED
    assert verdict(A, BORDERS, held).state == OPEN


def test_a_line_for_an_older_revision_is_stale_and_kept():
    old = line(1, rev=OLD_REV)
    held = stands(r1=[old])
    assert state_of("r1", A, BORDERS, held) == STALE
    assert verdict(A, BORDERS, held).applied is None
    assert held["r1"].answers["syn-n0001"] == old, "the old answer can still be shown"


def test_a_line_for_an_older_question_is_stale():
    held = stands(r1=[line(1, question="borders@0")])
    assert state_of("r1", A, BORDERS, held) == STALE


def test_a_stale_move_is_not_shown_as_standing():
    held = stands(r1=[move(1, "syn-n0001", "syn-oa0001", "syn-n0002", rev=OLD_REV)])
    assert records.moves_of("r1", A, BORDERS, held) == []


# Two reviewers


def test_two_reviewers_who_agree_are_done():
    held = stands(r1=[line(1)], r2=[line(1, reviewer="r2")])
    found = verdict(A, BORDERS, held)
    assert (found.state, found.by) == (DONE, ("r1", "r2"))
    assert found.applied == line(1)


def test_two_reviewers_who_disagree_are_in_dispute_and_nothing_is_applied():
    held = stands(r1=[line(1, answer="right")], r2=[line(1, reviewer="r2", answer="wrong")])
    found = verdict(A, BORDERS, held)
    assert (found.state, found.applied, found.by) == (DISPUTED, None, ())
    assert state_of("r1", A, BORDERS, held) == DISPUTED
    assert state_of("r2", A, BORDERS, held) == DISPUTED


def test_the_founder_settles_a_dispute():
    theirs = line(1, reviewer="r2", answer="wrong", note="The lane.")
    settled = line(2, answer="right", settles=True, note="Walked it. The brook.")
    held = stands(r1=[line(1, answer="right"), settled], r2=[theirs])
    found = verdict(A, BORDERS, held)
    assert (found.state, found.applied, found.by) == (DONE, settled, ("r1",))
    assert state_of("r2", A, BORDERS, held) == DONE


def test_nobody_but_the_founder_settles_a_dispute():
    with pytest.raises(Broken):
        parse(json.dumps({**line(1).as_dict(), "reviewer": "r2", "settles": True}).encode())


def test_a_dispute_comes_back_when_the_founder_takes_the_settling_back():
    first = line(1, answer="right")
    settled = line(2, answer="right", settles=True)
    theirs = [line(1, reviewer="r2", answer="wrong", note="The lane.")]
    held = stands(r1=[first, settled, undo(3, settled)], r2=theirs)
    assert verdict(A, BORDERS, held).state == DISPUTED


@pytest.mark.parametrize("answer", ["unknown", "cannot_say", "cannot_tell"])
def test_the_founder_not_knowing_is_no_dispute(answer: str):
    # The founder meets ground they do not know. The reviewer who knows it decides.
    mine = line(1, answer=answer)
    theirs = line(1, reviewer="r2", answer="right", note="Walked it.")
    held = stands(r1=[mine], r2=[theirs])
    found = verdict(A, BORDERS, held)
    assert (found.state, found.applied, found.by) == (DONE, theirs, ("r2",))
    assert dict(found.answers) == {"r1": mine, "r2": theirs}, "both answers are still shown"
    assert state_of("r1", A, BORDERS, held) == DONE
    assert state_of("r2", A, BORDERS, held) == DONE


def test_a_reviewer_not_knowing_leaves_the_founders_answer_to_stand():
    mine = line(1, answer="wrong", note="The lane.")
    held = stands(r1=[mine], r2=[line(1, reviewer="r2", answer="unknown")])
    found = verdict(A, BORDERS, held)
    assert (found.state, found.applied, found.by) == (DONE, mine, ("r1",))


def test_where_nobody_knows_nothing_is_checked_and_nothing_is_in_dispute():
    mine = line(1, answer="unknown")
    held = stands(r1=[mine], r2=[line(1, reviewer="r2", answer="unknown")])
    found = verdict(A, BORDERS, held)
    assert (found.state, found.applied, found.by) == (DONE, mine, ("r1", "r2"))


def test_two_who_decide_and_differ_are_in_dispute_whoever_else_does_not_know():
    held = stands(
        r1=[line(1, answer="unknown")],
        r2=[line(1, reviewer="r2", answer="right")],
        r3=[line(1, reviewer="r3", answer="wrong", note="The lane.")],
    )
    assert verdict(A, BORDERS, held).state == DISPUTED


def test_a_founder_who_settles_by_not_knowing_leaves_it_to_the_one_who_decided():
    theirs = line(1, reviewer="r2", answer="right")
    settled = line(2, answer="unknown", settles=True)
    held = stands(r1=[line(1, answer="wrong", note="The lane."), settled], r2=[theirs])
    found = verdict(A, BORDERS, held)
    assert (found.state, found.applied, found.by) == (DONE, theirs, ("r2",))


def test_a_skip_by_one_reviewer_is_no_dispute():
    held = stands(r1=[line(1, answer="right")], r2=[line(1, reviewer="r2", answer="skip")])
    assert verdict(A, BORDERS, held).state == DONE


def test_a_stale_answer_by_one_reviewer_is_no_dispute():
    held = stands(r1=[line(1)], r2=[line(1, reviewer="r2", answer="wrong", rev=OLD_REV)])
    assert verdict(A, BORDERS, held).state == DONE


def test_another_reviewers_answer_does_not_show_until_mine_stands():
    held = stands(r1=[line(1, answer="right")], r2=[])
    assert state_of("r2", A, BORDERS, held) == OPEN


def test_names_are_decided_by_the_founder_alone():
    names = question("names", ("area", "drop"))
    mine = line(1, queue="names", question="names@1", answer="area")
    theirs = line(1, queue="names", question="names@1", answer="drop", reviewer="r2")
    held = stands(r1=[mine], r2=[theirs])
    assert verdict(A, names, held).applied == mine
    assert state_of("r2", A, names, held) == DONE
    assert verdict(A, names, stands(r2=[theirs])).state == OPEN


def test_ratings_are_never_in_dispute():
    ratings = question("ratings", ("1", "2", "3", "4", "5", "cannot_say"))
    held = stands(
        r1=[line(1, queue="ratings", question="ratings@1", answer="2")],
        r7=[line(1, queue="ratings", question="ratings@1", answer="5", reviewer="r7")],
    )
    assert state_of("r1", A, ratings, held) == DONE
    assert state_of("r7", A, ratings, held) == DONE


def test_reviewers_come_in_the_order_of_their_numbers():
    lines_of = {f"r{at}": [line(1, reviewer=f"r{at}")] for at in (10, 2, 9)}
    assert verdict(A, BORDERS, stands(**lines_of)).by == ("r2", "r9", "r10")


# Progress


def test_progress_counts_each_item_once_and_in_one_state():
    held = {
        "r1": Read(
            (
                line(1, "syn-n0001", answer="right"),
                line(2, "syn-n0002", answer="skip"),
                line(3, "syn-n0003", rev=OLD_REV),
                line(4, "syn-n0004", answer="wrong", note="The lane.", second=True),
                line(5, "syn-n0001", answer="right"),
            )
        ),
        "r2": Read((line(1, "syn-n0004", reviewer="r2", answer="right"),)),
    }
    queue = items(
        A, B, C, item("syn-n0004", ("two_boroughs",)), item("syn-n0005", ("two_centres",))
    )
    found = progress("r1", queue, BORDERS, held)
    assert (found.total, found.done, found.skipped, found.stale, found.disputed) == (5, 1, 1, 1, 1)
    assert (found.flagged, found.flagged_left, found.second, found.left) == (2, 2, 1, 4)


def test_progress_says_how_many_answers_decide_nothing():
    # "120 done" must not say that work is finished which a build will never see.
    held = {
        "r1": Read(
            (
                line(1, "syn-n0001", answer="right"),
                line(2, "syn-n0002", answer="wrong", note="The lane."),
                line(3, "syn-n0003", answer="unknown"),
                line(4, "syn-n0004", answer="unknown"),
                line(5, "syn-n0005", answer="skip"),
            )
        )
    }
    queue = items(A, B, C, item("syn-n0004"), item("syn-n0005"))
    asked = question(answers=("right", "wrong", "unknown"))
    found = progress("r1", queue, asked, held)
    assert (found.done, found.wrong, found.not_known, found.skipped) == (4, 1, 2, 1)
    assert found.as_dict() | {"median_seconds": 0, "last_hour": 0} == {
        "total": 5,
        "done": 4,
        "wrong": 1,
        "not_known": 2,
        "skipped": 1,
        "stale": 0,
        "disputed": 0,
        "by_rule": 0,
        "flagged": 0,
        "flagged_left": 0,
        "second": 0,
        "median_seconds": 0,
        "last_hour": 0,
    }


# An item settled by a rule


def ruled(n: int, item_id: str, answer: str, rule: str = "a_made_up_rule", **more: Any) -> Line:
    """A line the desk writes when the founder adopts a rule: it names the rule."""
    about = {"queue": "names", "question": "names@1", "seconds": 0, **more}
    return line(n, item_id, answer, detail={"rule": rule}, **about)


def test_a_line_says_which_rule_settled_it_and_a_line_of_a_person_names_none():
    assert records.by_rule(ruled(1, "n:syn-n0001", "area")) == "a_made_up_rule"
    assert records.by_rule(line(1)) == ""
    assert records.by_rule(line(1, detail={"rule": ""})) == ""
    assert records.by_rule(line(1, detail={"rule": 7})) == ""
    # The founder's own answer to a rule names the rule, and is a person's answer.
    adopted = line(1, "a_made_up_rule", "yes", queue="rules", detail={"rule": "a_made_up_rule"})
    assert records.by_rule(adopted) == ""
    assert standing([adopted]).last == adopted


def test_an_item_settled_by_a_rule_is_done_and_is_counted_apart():
    # "120 done" must not say that a person read what a rule waved through.
    queue = items(name("n:syn-n0001"), name("n:syn-n0002"), name("n:syn-n0003"), queue="names")
    held = {
        "r1": Read(
            (
                named(1, "n:syn-n0001", "area", seconds=30),
                ruled(2, "n:syn-n0002", "area"),
                ruled(3, "n:syn-n0003", "drop"),
            )
        )
    }
    found = progress("r1", queue, NAMES, held)
    assert (found.total, found.done, found.by_rule, found.left) == (3, 3, 2, 0)
    assert found.as_dict()["by_rule"] == 2
    assert state_of("r1", queue.items[1], NAMES, stands(r1=list(held["r1"].lines))) == DONE


def test_a_line_a_rule_wrote_is_left_out_of_the_pace():
    answered = [named(at, f"n:syn-n{at:04d}", "area", seconds=40) for at in range(1, 4)]
    by_rule = [ruled(at, f"n:syn-n{at:04d}", "area") for at in range(4, 60)]
    assert pace([*answered, *by_rule]) == (40, 3)


def test_a_border_left_as_drafted_by_a_rule_decides_nothing_between_reviewers():
    # The rule says only that nobody is asked. What a reviewer says of the border stands.
    left = line(1, "syn-n0001", records.RULE, detail={"rule": "a_made_up_rule"}, seconds=0)
    right = line(1, "syn-n0001", "right", reviewer="r2")
    alone = verdict(A, BORDERS, stands(r1=[left]))
    assert (alone.state, alone.applied, alone.answers) == (OPEN, None, {})
    both = verdict(A, BORDERS, stands(r1=[left], r2=[right]))
    assert (both.state, both.applied, both.by) == (DONE, right, ("r2",))
    assert state_of("r1", A, BORDERS, stands(r1=[left], r2=[right])) == DONE
    assert state_of("r1", A, BORDERS, stands(r1=[left])) == DONE, "it is offered to nobody"


def test_an_undo_never_takes_back_a_line_that_a_rule_wrote():
    # The key for undo takes back what the last key wrote. A rule's lines are taken back
    # together, when its yes is.
    mine = named(1, "n:syn-n0001", "area")
    held = standing([mine, ruled(2, "n:syn-n0002", "area"), ruled(3, "n:syn-n0003", "area")])
    assert held.last == mine
    assert set(held.answers) == {"n:syn-n0001", "n:syn-n0002", "n:syn-n0003"}
    assert standing([ruled(1, "n:syn-n0002", "area")]).last is None


def test_the_answer_a_rule_gives_a_border_is_no_answer_of_any_question(tmp_path: Path):
    path = tmp_path / "questions.json"
    asked = {**QUESTIONS["queues"][0], "answers": [{"code": "rule", "label": "By rule"}]}
    path.write_text(json.dumps({"queues": [asked]}))
    with pytest.raises(Unfit, match="an answer with no code, or a code used twice"):
        read_questions(path)


# An answer that a build will set aside

TURNS_DOWN: list[records.Json] = ["same_ground", "inside", "wide", "drop"]
NAMES = Question(
    "names",
    "names@1",
    "Names",
    ("area", "same_ground", "inside", "wide", "drop"),
    frozenset({"pick"}),
    {"id": "names", "set_aside": {"answers": TURNS_DOWN}},
)


def name(item_id: str, **preset: records.Json) -> Item:
    return Item(item_id, REV, "quillhaven", (), None, {"id": item_id, "preset": preset})


def named(n: int, item_id: str, answer: str, **changed: Any) -> Line:
    return line(n, item_id, answer, queue="names", question="names@1", **changed)


def test_an_answer_that_turns_down_an_area_with_ground_is_counted_as_set_aside():
    # The desk saves it, and the step that makes a build's files sets it aside until the
    # draft is made again. So it is counted apart, and the page can say so.
    queue = items(
        name("n:syn-n0001", holds="cells"),
        name("n:syn-n0002", holds="cells"),
        name("n:syn-n0003", holds="names"),
        name("n:syn-n0004"),
        name("a:syn-n0001:pellam"),
        queue="names",
    )
    held = stands(
        r1=[
            named(1, "n:syn-n0001", "drop"),
            named(2, "n:syn-n0002", "area"),
            named(3, "n:syn-n0003", "inside"),
            named(4, "n:syn-n0004", "drop"),
            named(5, "a:syn-n0001:pellam", "drop"),
        ]
    )
    assert records.set_aside("r1", queue, NAMES, held) == 2
    assert records.set_aside("r2", queue, NAMES, held) == 0
    # What a rule turned down waits too, and is counted with the rule's where asked.
    more = stands(r1=[*held["r1"].answers.values(), ruled(6, "n:syn-n0002", "drop")])
    assert records.set_aside("r1", queue, NAMES, more) == 3
    assert records.set_aside("r1", queue, NAMES, more, own=True) == 2
    assert [
        records.waits_for_a_draft(each, NAMES, held["r1"].answers[each.id]) for each in queue.items
    ] == [True, False, True, False, False]


def test_an_answer_that_was_skipped_taken_back_or_is_stale_is_not_set_aside():
    queue = items(
        name("n:syn-n0001", holds="cells"),
        name("n:syn-n0002", holds="cells"),
        name("n:syn-n0003", holds="cells"),
        queue="names",
    )
    dropped = named(1, "n:syn-n0001", "drop")
    held = stands(
        r1=[
            dropped,
            undo(2, dropped),
            named(3, "n:syn-n0002", "skip"),
            named(4, "n:syn-n0003", "drop", rev=OLD_REV),
        ]
    )
    assert records.set_aside("r1", queue, NAMES, held) == 0


def test_a_queue_with_no_such_answers_sets_nothing_aside():
    held = stands(r1=[line(1, "syn-n0001", "wrong", note="The lane.")])
    assert records.set_aside("r1", items(A, B), BORDERS, held) == 0


def test_progress_with_no_line_is_all_to_do():
    found = progress("r1", items(A, B), BORDERS, {})
    assert (found.total, found.done, found.median_seconds, found.last_hour) == (2, 0, None, 0)


def test_pace_is_the_median_of_the_last_fifty_answers():
    slow = [line(at, f"syn-n{at:04d}", seconds=600) for at in range(1, 11)]
    quick = [line(at, f"syn-n{at:04d}", seconds=10 + at % 3) for at in range(11, 61)]
    assert pace(slow + quick)[0] == 11
    assert pace(slow)[0] == 600


def test_pace_leaves_out_skips_moves_and_undos():
    answered = line(1, seconds=40)
    others = [
        line(2, "syn-n0002", answer="skip", seconds=2),
        move(3, "syn-n0003", "syn-oa0001", "syn-n0002", seconds=1),
        undo(4, answered),
    ]
    assert pace([answered, *others]) == (40, 1)


def test_pace_over_the_last_hour_is_counted_from_the_newest_line():
    day_before = [line(at, f"syn-n{at:04d}", at="2026-10-05T20:00:00Z") for at in range(1, 6)]
    tonight = [line(at, f"syn-n{at:04d}", at=f"2026-10-06T21:{at:02d}:00Z") for at in range(6, 9)]
    assert pace(day_before + tonight)[1] == 3
    assert pace(day_before)[1] == 5


def test_pace_is_never_below_nothing_when_the_clock_goes_backwards():
    before = [line(at, f"syn-n{at:04d}", at=f"2026-10-06T21:{at:02d}:00Z") for at in range(1, 4)]
    after = [line(at, f"syn-n{at:04d}", at=f"2026-10-06T17:{at:02d}:00Z") for at in range(4, 9)]
    median, last_hour = pace(before + after)
    assert median == 20
    assert 0 <= last_hour <= 8


def test_progress_is_worked_out_from_the_lines_alone(monkeypatch: pytest.MonkeyPatch):
    def no_clock() -> datetime:
        raise AssertionError("progress read the clock")

    monkeypatch.setattr(records, "now", no_clock)
    held = {"r1": Read((line(1), line(2, "syn-n0002")))}
    assert progress("r1", items(A, B, C), BORDERS, held).as_dict() == {
        "total": 3,
        "done": 2,
        "wrong": 0,
        "not_known": 0,
        "skipped": 0,
        "stale": 0,
        "disputed": 0,
        "by_rule": 0,
        "flagged": 0,
        "flagged_left": 0,
        "second": 0,
        "median_seconds": 20,
        "last_hour": 2,
    }


# What is shown next


def test_the_next_item_is_the_first_open_one_after_this():
    held = stands(r1=[line(1, "syn-n0001"), line(2, "syn-n0002")])
    assert next_item("r1", items(A, B, C), BORDERS, held, after="syn-n0002") == "syn-n0003"
    assert next_item("r1", items(A, B, C), BORDERS, held) == "syn-n0003"


def test_the_next_item_goes_round_to_the_start():
    held = stands(r1=[line(1, "syn-n0003")])
    assert next_item("r1", items(A, B, C), BORDERS, held, after="syn-n0003") == "syn-n0001"


def test_a_skipped_item_comes_back_after_the_rest():
    held = stands(r1=[line(1, "syn-n0001", answer="skip")])
    queue = items(A, B, C)
    assert next_item("r1", queue, BORDERS, held, after="syn-n0001") == "syn-n0002"
    held = stands(
        r1=[line(1, "syn-n0001", answer="skip"), line(2, "syn-n0002"), line(3, "syn-n0003")]
    )
    assert next_item("r1", queue, BORDERS, held, after="syn-n0003") == "syn-n0001"
    assert next_item("r1", queue, BORDERS, held, after="syn-n0001") == "syn-n0001"


def test_the_next_item_is_none_when_all_are_done():
    held = stands(r1=[line(1, "syn-n0001"), line(2, "syn-n0002")])
    assert next_item("r1", items(A, B), BORDERS, held, after="syn-n0002") is None


def test_what_the_founder_marked_comes_first_for_the_second_reviewer():
    held = stands(r1=[line(1, "syn-n0003", second=True)], r2=[])
    assert next_item("r2", items(A, B, C), BORDERS, held) == "syn-n0003"
    assert next_item("r2", items(A, B, C), BORDERS, held, after="syn-n0003") == "syn-n0001"
    assert next_item("r1", items(A, B, C), BORDERS, held) == "syn-n0001"


def test_the_boroughs_a_reviewer_knows_well_come_first():
    held = [
        Item("syn-n0001", REV, "quillhaven", (), None, {}),
        Item("syn-n0002", REV, "marrowmere", (), None, {}),
        Item("syn-n0003", REV, "thrushcombe", (), None, {}),
        Item("syn-n0004", REV, "quillhaven", (), None, {}),
        Item("syn-n0005", REV, "osierholm", (), None, {}),
    ]
    queue = items(*held)
    known = {"quillhaven": "not", "marrowmere": "a_little", "osierholm": "well"}
    ordered = records.order_for("r1", queue, {}, known)
    assert [each.id for each in ordered] == [
        *("syn-n0005", "syn-n0002", "syn-n0003", "syn-n0001", "syn-n0004"),
    ], "well, a little, not marked, not known: and the order of the file within each"
    assert next_item("r1", queue, BORDERS, {}, known=known) == "syn-n0005"
    assert [each.id for each in records.order_for("r1", queue, {})] == [e.id for e in held]


def test_what_the_founder_marked_still_comes_first_for_a_reviewer_who_knows_another_borough():
    held = [
        Item("syn-n0001", REV, "quillhaven", (), None, {}),
        Item("syn-n0002", REV, "marrowmere", (), None, {}),
    ]
    marked = stands(r1=[line(1, "syn-n0001", second=True)], r2=[])
    ordered = records.order_for("r2", items(*held), marked, {"marrowmere": "well"})
    assert [each.id for each in ordered] == ["syn-n0001", "syn-n0002"]


def test_names_and_the_ground_are_offered_by_the_boroughs_a_reviewer_knows():
    # Names ran by borough in the order of the alphabet, for all of London. A person
    # decides a name well, and fast, where they know the ground.
    assert frozenset({"names", "borders", "whole", "ratings"}) == records.BY_KNOWN


def test_a_borough_is_finished_before_the_next_begins_whatever_is_known():
    held = [
        Item("n:syn-n0001", REV, "quillhaven", (), None, {}),
        Item("a:syn-n0001:pellam", REV, "quillhaven", (), None, {}),
        Item("n:syn-n0002", REV, "marrowmere", (), None, {}),
        Item("a:syn-n0002:osier", REV, "marrowmere", (), None, {}),
        Item("n:syn-n0003", REV, "osierholm", (), None, {}),
    ]
    ordered = records.order_for("r1", items(*held, queue="names"), {}, {"marrowmere": "well"})
    assert [each.group for each in ordered] == [
        *("marrowmere", "marrowmere", "quillhaven", "quillhaven", "osierholm"),
    ]
    assert [each.id for each in ordered][:2] == ["n:syn-n0002", "a:syn-n0002:osier"]


def test_a_whole_borough_is_placed_by_how_well_it_is_known():
    held = [
        Item("quillhaven", REV, "quillhaven", (), None, {}),
        Item("osierholm", REV, "o", (), None, {}),
    ]
    ordered = records.order_for("r1", items(*held, queue="whole"), {}, {"osierholm": "well"})
    assert [each.id for each in ordered] == ["osierholm", "quillhaven"]


def test_a_question_may_have_an_answer_that_covers_every_item_of_a_part(tmp_path: Path):
    path = tmp_path / "questions.json"
    names = QUESTIONS["queues"][0]
    covers = {"by": "area_id", "code": "drop", "label": "I do not know this area"}
    path.write_text(json.dumps({"queues": [{**names, "covers": covers}]}))
    assert read_questions(path)["names"].covers == "area_id"
    path.write_text(json.dumps({"queues": [names]}))
    assert read_questions(path)["names"].covers is None
    for wrong in ({"code": "nothing"}, {"by": ""}, {"by": 7}, {"label": ""}):
        path.write_text(json.dumps({"queues": [{**names, "covers": {**covers, **wrong}}]}))
        with pytest.raises(Unfit, match="covers"):
            read_questions(path)


def test_a_question_says_what_it_waits_on_and_who_works_it(tmp_path: Path):
    path = tmp_path / "questions.json"
    names = QUESTIONS["queues"][0]
    borders = {**names, "id": "borders", "after": ["names"], "open_to": "all"}
    path.write_text(json.dumps({"queues": [{**names, "open_to": "founder"}, borders]}))
    found = read_questions(path)
    assert (found["names"].after, found["names"].open_to_all) == ((), False)
    assert (found["borders"].after, found["borders"].open_to_all) == (("names",), True)
    for wrong in ({"open_to": "r2"}, {"after": "names"}, {"after": ["borders"]}, {"after": [1]}):
        path.write_text(json.dumps({"queues": [{**borders, **wrong}]}))
        with pytest.raises(Unfit):
            read_questions(path)


def test_live_lines_are_in_the_order_they_were_written():
    written = [line(3, "syn-n0003"), line(1), line(2, "syn-n0002")]
    assert [each.n for each in live(written)] == [1, 2, 3]


# Items and questions, as files

HEADER: dict[str, Any] = {
    "desk": 1,
    "queue": "names",
    "question": "names@1",
    "synthetic": True,
    "made_on": "2026-09-23",
    "made_from": [{"source_id": "synthetic", "file": "neighbourhoods.json", "sha256": "0" * 64}],
    "count": 1,
}
ITEM: dict[str, Any] = {
    "id": "n:syn-n0004",
    "rev": REV,
    "group": "quillhaven",
    "title": "Dulcimer Green, Quillhaven",
    "lines": [{"label": "As written", "value": "Dulcimer Green", "source_id": "synthetic"}],
    "text": None,
    "map": {"bbox": [-0.02, 0.03, -0.01, 0.05], "focus": "syn-n0004", "layers": ["cells"]},
    "picks": ["Dulcimer Green", "Dulcimer"],
    "flags": ["one_publisher"],
    "fill": {},
    "preset": {"of": [], "pick": "Dulcimer Green"},
}
QUESTIONS: dict[str, Any] = {
    "queues": [
        {
            "id": "names",
            "title": "Names",
            "text": "Is this the name of an area?",
            "rule": "Copy no name and no border from a map or a website.",
            "view": "map",
            "adds": ["pick"],
            "public": True,
            "answers": [
                {"code": "area", "label": "An area"},
                {"code": "drop", "label": "Not kept"},
            ],
        }
    ],
    "flags": {"one_publisher": "one publisher"},
}


def items_file(folder: Path, *rows: dict[str, Any], header: dict[str, Any] | None = None) -> Path:
    path = folder / "names.jsonl"
    held = [{**HEADER, "count": len(rows), **(header or {})}, *rows]
    path.write_text("".join(json.dumps(row) + "\n" for row in held), encoding="utf-8")
    return path


def test_a_file_of_items_is_read_in_its_own_order(tmp_path: Path):
    second: dict[str, Any] = {**ITEM, "id": "a:syn-n0004:dulcimer", "picks": None}
    found = read_items(items_file(tmp_path, ITEM, second))
    assert (found.queue, found.question, found.synthetic) == ("names", "names@1", True)
    assert [each.id for each in found.items] == ["n:syn-n0004", "a:syn-n0004:dulcimer"]
    assert found.by_id["n:syn-n0004"].picks == ("Dulcimer Green", "Dulcimer")
    assert found.by_id["n:syn-n0004"].held == ITEM


@pytest.mark.parametrize(
    ("rows", "header"),
    [
        ([{**ITEM, "residents": 4100}], {}),
        ([{key: value for key, value in ITEM.items() if key != "flags"}], {}),
        ([ITEM, ITEM], {}),
        ([ITEM], {"count": 2}),
        ([ITEM], {"desk": 2}),
        ([ITEM], {"queue": "borders"}),
        ([ITEM], {"synthetic": "yes"}),
        ([{**ITEM, "rev": "not-a-hash"}], {}),
        ([{**ITEM, "id": ""}], {}),
        ([{**ITEM, "picks": "Dulcimer"}], {}),
        ([{**ITEM, "preset": None}], {}),
    ],
)
def test_a_file_of_items_that_is_not_as_the_design_gives_it_is_refused(
    tmp_path: Path, rows: list[dict[str, Any]], header: dict[str, Any]
):
    with pytest.raises(Unfit) as refusal:
        read_items(items_file(tmp_path, *rows, header=header))
    assert "Dulcimer" not in str(refusal.value)


def test_the_questions_are_read_in_the_order_of_their_file(tmp_path: Path):
    path = tmp_path / "questions.json"
    borders = {**QUESTIONS["queues"][0], "id": "borders", "adds": ["move"], "version": 2}
    path.write_text(json.dumps({**QUESTIONS, "queues": [*QUESTIONS["queues"], borders]}))
    found = read_questions(path)
    assert list(found) == ["names", "borders"]
    assert (found["names"].version, found["names"].answers) == ("names@1", ("area", "drop"))
    assert (found["borders"].version, found["borders"].adds) == ("borders@2", {"move"})
    assert found["names"].held == QUESTIONS["queues"][0]


def test_a_question_says_whether_its_lines_may_be_published(tmp_path: Path):
    path = tmp_path / "questions.json"
    asked = {"id": "know", "title": "Know", "answers": [{"code": "well", "label": "Well"}]}
    path.write_text(json.dumps({"queues": [{**asked, "public": False}]}), encoding="utf-8")
    assert read_questions(path)["know"].public is False
    path.write_text(json.dumps({"queues": [{**asked, "public": True}]}), encoding="utf-8")
    assert read_questions(path)["know"].public is True
    for unsaid in ({}, {"public": "no"}, {"public": 0}, {"public": None}):
        path.write_text(json.dumps({"queues": [{**asked, **unsaid}]}), encoding="utf-8")
        with pytest.raises(Unfit, match="whether its lines may be published"):
            read_questions(path)


@pytest.mark.parametrize(
    "changed",
    [
        {"id": "Names"},
        {"answers": []},
        {"answers": [{"code": str(at), "label": str(at)} for at in range(10)]},
        {"answers": [{"code": "area", "label": "An area"}, {"code": "area", "label": "Again"}]},
        {"answers": [{"code": "skip", "label": "Skip"}]},
        {"answers": [{"label": "No code"}]},
        {"question": "borders@1"},
        {"adds": "pick"},
    ],
)
def test_a_question_that_is_not_as_the_design_gives_it_is_refused(
    tmp_path: Path, changed: dict[str, Any]
):
    path = tmp_path / "questions.json"
    path.write_text(json.dumps({"queues": [{**QUESTIONS["queues"][0], **changed}]}))
    with pytest.raises(Unfit):
        read_questions(path)


def test_a_file_is_never_followed_out_of_the_folder_of_decisions(tmp_path: Path):
    outside = tmp_path / "outside.jsonl"
    outside.write_bytes(as_file(line(1)))
    folder = path_of(tmp_path, "borders", "r1").parent
    folder.mkdir(parents=True)
    (folder / "r1.jsonl").symlink_to(outside)
    assert read_queue(tmp_path, "borders") == {}
