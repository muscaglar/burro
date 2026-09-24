"""The step `preview`, on a build that takes a file which states its own edition.

A publisher that replaces a file under one address leaves the file itself to
say which file it is. The store may then hold two editions of one file of the
list. These hold the whole of a build to the rule of which it takes:

    told nothing       the newest, by the day the file states
    told an edition    that one
    in the lock        the file of the list, and the edition that was taken
    built twice        the same bytes

The town is Quillhaven and Tallowgate, which do not exist. The register is of
a made-up authority, and its businesses have a made-up name. No measure reads
it: it is the file of no borough of the town, and a measure of the register
rests on the file of every authority. So the measures of the register are held
out of the builds made here. What is held here is which file a build takes,
and what it says of it.
"""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.assemble import cli as assemble
from burro_pipeline.assemble.cli import of_the_list
from burro_pipeline.derive import food_register
from burro_pipeline.evidence.lock import Lock, LockError
from burro_pipeline.fetch.sources import load_list
from public_log import is_public

from ..cells.support import held
from .support import REGISTER, RELEASE, Made, files, list_of, made, register_of

Printed = pytest.CaptureFixture[str]
OLDER, NEWER = "2026-09-16", "2026-09-17"
# The files of the made-up build, and the register beside them.
FILES = len(files()) + 1
# A string found nowhere else. If a line repeats what it was handed, this shows up in it.
CANARY = "Zzyzx Parva"


@pytest.fixture(autouse=True)
def no_measure_of_the_register(monkeypatch: pytest.MonkeyPatch) -> None:
    """The builds made here carry no measure of the register, whose file here is of no borough.

    A release that carried one would be held to the file of every authority the
    lock names, and the made-up file of these tests is one that no measure reads.
    """
    held = "Held out of a build whose register holds a file of no borough of its town."
    monkeypatch.setattr(
        assemble,
        "MEASURES",
        tuple(
            replace(measure, held_back=(held,))
            if measure.source == food_register.SOURCE
            else measure
            for measure in assemble.MEASURES
        ),
    )


def with_the_register(folder: Path, *days: str, receipt: bool = True) -> Made:
    """The made-up build, with a register in its list and an edition of it for each day."""
    first, *later = [register_of(day, rows=2 + n) for n, day in enumerate(days or (OLDER,))]
    found = made(
        folder, changed={REGISTER: first}, without_a_receipt=() if receipt else (REGISTER,)
    )
    for file in later:
        found.keep(file)
    return found


def lines_of(capsys: Printed) -> tuple[list[str], str]:
    out = capsys.readouterr()
    assert all(is_public(line) for line in out.out.splitlines())
    assert CANARY not in out.out + out.err
    return out.out.splitlines(), out.err


def sealing(said: list[str]) -> str:
    """The line of the last build that says what was sealed."""
    return [line for line in said if line.startswith("step=seal ")][-1]


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def taken(found: Made, out: Path | None = None) -> dict[str, str | None]:
    """What the lock of a build says it took of each file that states its own edition."""
    beside = found.beside if out is None else out / found.beside.name
    lock = Lock.model_validate_json((beside / "lock.json").read_bytes())
    return {one.item: one.edition for one in lock.inputs if one.item is not None}


def test_a_build_takes_a_file_that_states_its_own_edition_and_its_lock_says_which(
    tmp_path: Path, capsys: Printed
):
    found = with_the_register(tmp_path)
    assert found.run() == 0
    said, words = lines_of(capsys)
    assert said[0].startswith(
        f"step=seal status=ok release={RELEASE} inputs={FILES} missing=0 "
        "own_edition=1 named=0 passed_over=0 development=1 lock_sha256="
    )
    assert taken(found) == {REGISTER: f"extract of {OLDER}"}
    # One edition has a receipt, so there was nothing to choose, and nothing is noted.
    assert REGISTER not in words
    record = read(found.beside / "build.json")
    assert record["files_of_the_list_with_no_receipt"] == []
    assert register_of(OLDER).receipt().file_id in record["files_sealed"]


def test_built_twice_from_the_same_store_it_writes_the_same_bytes(tmp_path: Path, capsys: Printed):
    found = with_the_register(tmp_path, OLDER, NEWER)
    assert found.run() == 0
    assert found.run(out=tmp_path / "again") == 0
    assert held(tmp_path / "again") == held(found.out)


def test_after_a_newer_file_arrives_the_build_takes_the_newer_and_says_so(
    tmp_path: Path, capsys: Printed
):
    found = with_the_register(tmp_path)
    assert found.run() == 0
    before = taken(found)
    found.keep(register_of(NEWER, rows=3))
    assert found.run(out=tmp_path / "after") == 0
    said, words = lines_of(capsys)
    assert before == {REGISTER: f"extract of {OLDER}"}
    assert taken(found, tmp_path / "after") == {REGISTER: f"extract of {NEWER}"}
    assert f" inputs={FILES} missing=0 own_edition=1 named=0 passed_over=1 " in sealing(said)
    assert (
        f"note: {REGISTER} has 2 editions with a receipt. This build takes the newest, and "
        f"its lock says which. To take another, give --edition {REGISTER}=EDITION"
    ) in words.splitlines()
    lock = Lock.model_validate_json(
        (tmp_path / "after" / f"{RELEASE}-build" / "lock.json").read_bytes()
    )
    assert not lock.holds(register_of(OLDER).receipt().file_id)


def test_told_to_take_the_older_it_builds_what_it_built_before_the_newer_arrived(
    tmp_path: Path, capsys: Printed
):
    found = with_the_register(tmp_path)
    assert found.run() == 0
    found.keep(register_of(NEWER, rows=3))
    told = ("--edition", f"{REGISTER}=extract of {OLDER}")
    assert found.run(*told, out=tmp_path / "told") == 0
    assert held(tmp_path / "told") == held(found.out)
    said, words = lines_of(capsys)
    assert " own_edition=1 named=1 passed_over=1 " in sealing(said)
    assert "This build takes the one that was named" in words


@pytest.mark.parametrize(
    ("days", "told", "rule"),
    [
        ((OLDER, OLDER), "", "listed_file_has_one_receipt"),
        ((OLDER, NEWER), f"{REGISTER}=extract of 2026-09-18", "named_edition_has_a_receipt"),
        ((OLDER,), f"{REGISTER}={CANARY}", "named_edition_has_a_receipt"),
        ((OLDER,), "grid=2024", "named_edition_has_a_receipt"),
    ],
    ids=["one edition twice", "an edition with no receipt", "no edition", "no such file"],
)
def test_what_stops_a_build_stops_it_before_anything_is_written(
    days: tuple[str, ...], told: str, rule: str, tmp_path: Path, capsys: Printed
):
    found = with_the_register(tmp_path, *days)
    assert found.run(*(("--edition", told) if told else ())) == 2
    said, words = lines_of(capsys)
    assert len(said) == 1 and said[0].startswith(f"step=assemble status=refused {rule}=1")
    assert f"[{rule}]" in words and "2026-09-18" not in words
    assert not found.out.exists()


def test_a_file_that_states_its_own_edition_and_has_no_receipt_is_left_out_and_said(
    tmp_path: Path, capsys: Printed
):
    found = with_the_register(tmp_path, receipt=False)
    assert found.run() == 0
    said, words = lines_of(capsys)
    assert f" inputs={FILES - 1} missing=1 development=1 " in said[0]
    assert f"{REGISTER} of the list has no receipt" in words
    assert taken(found) == {}
    record = read(found.beside / "build.json")
    assert [one["item"] for one in record["files_of_the_list_with_no_receipt"]] == [REGISTER]


def test_the_receipts_of_a_list_are_the_editions_taken_and_no_other(tmp_path: Path):
    every = [*files().values(), register_of(OLDER)]
    (tmp_path / "made-up.toml").write_text(list_of(every), encoding="utf-8")
    listed = load_list(tmp_path / "made-up.toml").files
    older, newer = register_of(OLDER).receipt(), register_of(NEWER, rows=3).receipt()
    receipts = [file.receipt() for file in files().values()]
    found, with_one, without = of_the_list([newer, *receipts, older], listed)
    assert [receipt.file_id for receipt in found] == [
        *(receipt.file_id for receipt in receipts),
        newer.file_id,
    ]
    assert ([file.item for file in with_one], without) == ([file.item for file in listed], [])
    told = {REGISTER: older.edition}
    found, _, _ = of_the_list([newer, *receipts, older], listed, told)
    assert found[-1] == older and newer not in found
    with pytest.raises(LockError) as refused:
        of_the_list([*receipts, older, register_of(OLDER, rows=5).receipt()], listed)
    assert refused.value.rule == "listed_file_has_one_receipt"
