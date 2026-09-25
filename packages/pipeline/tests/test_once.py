"""What is made once for every test is held to what it was when it was made.

A test that wrote to it would change what the next test reads, and which test is next
depends on the order the tests run in. So the run fails, and names the folder.
"""

import io
import shutil
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from . import once
from .assemble.support import RELEASE, built_once, made_once
from .kept.support import built


@pytest.fixture
def noted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A folder that is noted as made once, in a record of this test's own."""
    monkeypatch.setattr(once, "_HELD", {})
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "made.txt").write_text("as it was made", encoding="utf-8")
    return once.made(tmp_path)


def test_a_folder_that_no_test_wrote_to_is_not_named(noted: Path):
    assert (noted / "a" / "made.txt").read_text(encoding="utf-8") == "as it was made"
    assert once.changed() == []


@pytest.mark.parametrize("name", ["a/made.txt", "a/more.txt", "more.txt"])
def test_a_folder_that_a_test_wrote_to_is_named(noted: Path, name: str):
    (noted / name).write_text("as a test left it", encoding="utf-8")
    assert once.changed() == [noted.name]


def test_a_folder_that_a_test_took_a_file_from_is_named(noted: Path):
    (noted / "a" / "made.txt").unlink()
    assert once.changed() == [noted.name]


def test_a_file_that_was_moved_is_not_taken_for_the_file_it_was(noted: Path):
    (noted / "a" / "made.txt").rename(noted / "a" / "moved.txt")
    assert once.changed() == [noted.name]


def test_what_is_made_once_is_made_under_the_folder_pytest_gives(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
):
    given = tmp_path_factory.getbasetemp()
    assert built_once().folder.is_relative_to(given)
    assert built_once().out.is_relative_to(given)
    assert made_once(tmp_path / "build").folder.is_relative_to(given)
    # What a build writes from the files that are made once, it writes to the test's own.
    assert made_once(tmp_path / "build").out.is_relative_to(tmp_path)


def test_a_test_that_changes_its_copy_of_the_build_changes_nothing_the_next_is_handed(
    tmp_path: Path,
):
    mine = built(tmp_path / "mine")
    as_built = once.holding(mine)
    (mine / RELEASE / "manifest.json").write_bytes(b"changed by a test")
    shutil.rmtree(mine / f"{RELEASE}-build")
    assert once.holding(mine) != as_built

    assert once.holding(built(tmp_path / "next")) == as_built
    assert once.holding(built_once().out) == as_built
    assert once.changed() == []


def test_a_test_that_changes_what_it_built_changes_nothing_the_next_builds_from(tmp_path: Path):
    mine = made_once(tmp_path / "mine")
    files = once.holding(mine.folder)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert mine.run() == 0
    as_built = once.holding(mine.out)
    (mine.release / "manifest.json").write_bytes(b"changed by a test")
    shutil.rmtree(mine.beside)
    assert once.holding(mine.out) != as_built

    following = made_once(tmp_path / "next")
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert following.run() == 0
    assert once.holding(following.out) == as_built
    assert once.holding(following.folder) == files
    assert once.changed() == []
