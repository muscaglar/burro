"""The step `draft`: the whole draft of the areas, as a step of the one command line.

A hosted run makes the draft from the store, so that no draft is handed to it
from a machine of a person's own. Nothing here is real, and nothing reaches a
network: the store that stands in for a bucket has a folder behind it.
"""

from pathlib import Path

import pytest
from burro_pipeline import cli
from burro_pipeline.areas import cli as areas
from burro_pipeline.areas import draft_run
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.fetch.store import FOLDER_VARIABLE
from burro_pipeline.registry.model import Use
from public_log import is_public

from ..cells.support import receipt_of
from ..test_inputs import Reached, in_place_of_the_environment
from . import names_support as town
from .draft_support import given, receipts_folder
from .test_draft_run import every_file

Printed = pytest.CaptureFixture[str]
A_BUCKET = {
    "BURRO_STORE_ENDPOINT": "https://made-up.example",
    "BURRO_STORE_BUCKET": "made-up-bucket",
    "BURRO_STORE_KEY_ID": "made-up-key-id",
    "BURRO_STORE_SECRET": "made-up-secret",
}


def every_receipt(folder: Path, every: bool = True) -> tuple[list[Receipt], Path]:
    """The receipts of the made-up town, and the store it is in.

    One file of the town has no receipt, and a draft from a folder reads it
    all the same. With `every` it has one here, as every file of London has.
    """
    found = given(folder)
    receipts = list(found.receipts)
    if every:
        for which in sorted(town.WITHOUT_A_RECEIPT):
            source_id, name, edition = town.FILES[which]
            content = town.contents()[which]
            receipts.append(receipt_of(source_id, Use.GAZETTEER, name, content, edition or "V1"))
    return receipts, found.store


def arguments(folder: Path, out: Path, *more: str, every: bool = True) -> tuple[list[str], Path]:
    """What is typed after the name of the step, and the store the made-up town is in."""
    receipts, store = every_receipt(folder, every)
    held = receipts_folder(folder / "receipts", receipts)
    return ["--out", str(out), "--receipts", str(held), *more], store


def test_the_draft_is_a_step_of_the_one_command_line():
    assert [step.name for step in areas.STEPS] == ["draft"]
    assert cli.STEPS["draft"] is areas.STEPS[0]
    assert list(cli.STEPS).index("draft") < list(cli.STEPS).index("preview")


def test_the_step_makes_what_the_command_of_its_own_makes(tmp_path: Path, capsys: Printed):
    typed, store = arguments(tmp_path / "a", tmp_path / "a" / "out")
    assert draft_run.main(typed, {FOLDER_VARIABLE: str(store)}) == 0
    as_before = capsys.readouterr().out
    typed, store = arguments(tmp_path / "b", tmp_path / "b" / "out")
    assert areas.main(["draft", *typed], {FOLDER_VARIABLE: str(store)}) == 0
    assert capsys.readouterr().out == as_before
    assert every_file(tmp_path / "a" / "out") == every_file(tmp_path / "b" / "out")


def test_the_step_takes_every_argument_the_command_takes():
    of_the_step = {action.dest for action in cli.parser_of("draft")._actions}  # pyright: ignore[reportPrivateUsage]
    of_the_command = {action.dest for action in draft_run.parser()._actions}  # pyright: ignore[reportPrivateUsage]
    assert of_the_step == of_the_command


def from_a_bucket(
    folder: Path, out: Path, patch: pytest.MonkeyPatch, *more: str, every: bool = True
) -> tuple[int, Reached]:
    typed, behind = arguments(folder, out, *more, every=every)
    store = Reached(behind)
    patch.setattr(draft_run, "store_from_environment", in_place_of_the_environment(store))
    return areas.main(["draft", *typed], A_BUCKET), store


def test_a_draft_from_a_bucket_copies_every_file_out_before_it_reads_any(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    status, store = from_a_bucket(tmp_path, tmp_path / "out", monkeypatch)
    said = capsys.readouterr().out.splitlines()
    assert status == 0
    receipts, _ = every_receipt(tmp_path / "again")
    # Every file that has a receipt was asked for once, and none while a file was read.
    assert sorted(store.asked) == sorted(receipt.sha256 for receipt in receipts)
    size = sum(receipt.bytes for receipt in receipts)
    assert (
        said[0] == f"step=store status=ok kind=object_store files={len(store.asked)} bytes={size}"
    )
    assert is_public(said[0]) and said[1].startswith("step=areas-draft status=ok ")


def test_a_file_that_has_no_receipt_is_not_read_from_a_bucket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    """A draft from a folder may read such a file, for a draft alone. A hosted run reads none."""
    status, _ = from_a_bucket(tmp_path, tmp_path / "out", monkeypatch, every=False)
    printed = capsys.readouterr()
    assert status == 2
    assert printed.out.splitlines()[-1] == "step=areas-draft status=refused file_is_in_the_vault=1"
    assert not (tmp_path / "out" / "areas.csv").exists()


def test_a_draft_from_a_bucket_is_the_bytes_of_a_draft_from_a_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    typed, store = arguments(tmp_path / "a", tmp_path / "a" / "out")
    assert areas.main(["draft", *typed], {FOLDER_VARIABLE: str(store)}) == 0
    assert from_a_bucket(tmp_path / "b", tmp_path / "b" / "out", monkeypatch)[0] == 0
    assert every_file(tmp_path / "a" / "out") == every_file(tmp_path / "b" / "out")


def test_the_copies_a_draft_leaves_are_the_copies_a_build_finds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    """A hosted run makes the draft and then builds. Each file is copied out once."""
    work = tmp_path / "copies"
    status, store = from_a_bucket(tmp_path, tmp_path / "out", monkeypatch, "--work", str(work))
    assert status == 0
    asked = len(store.asked)
    status, store = from_a_bucket(
        tmp_path / "again", tmp_path / "out-again", monkeypatch, "--work", str(work)
    )
    assert status == 0 and asked > 0 and store.asked == []


def test_a_file_the_bucket_does_not_hold_stops_the_draft_before_anything_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Printed
):
    typed, behind = arguments(tmp_path, tmp_path / "out")
    gone = sorted(path for path in (behind / "raw").rglob("*") if path.is_file())[0]
    gone.rename(tmp_path / "set-aside")
    monkeypatch.setattr(
        draft_run, "store_from_environment", in_place_of_the_environment(Reached(behind))
    )
    assert areas.main(["draft", *typed], A_BUCKET) == 2
    printed = capsys.readouterr()
    assert printed.out == "step=areas-draft status=refused file_is_in_the_vault=1\n"
    # A hosted run shows why: the line is one the public log lets through.
    assert is_public(printed.out.strip())
    assert not (tmp_path / "out").exists()


def test_with_no_store_named_the_step_says_how_either_is_named(tmp_path: Path, capsys: Printed):
    typed, _ = arguments(tmp_path, tmp_path / "out")
    assert areas.main(["draft", *typed], {}) == 2
    words = capsys.readouterr().err
    assert "BURRO_STORE_FOLDER" in words and "BURRO_STORE_ENDPOINT" in words
