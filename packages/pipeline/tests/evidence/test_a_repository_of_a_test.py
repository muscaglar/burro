"""A repository that a test makes, and the copy of it that a test is handed.

Git holds a lock in a repository while it writes there, and takes it away when it is done.
After a commit it looked the repository over in a process it let go of, so a lock was made
and taken away once git had answered. A copy that listed the lock and then found it gone
fell over it, in some runs and not in others.

So git is started to do no upkeep of its own, and a copy passes over a lock. To hold the
second, a file is taken away here as soon as the folder that holds it has been listed,
which is what that copy met, and is met every time.
"""

import os
import shutil
from collections.abc import Iterator
from contextlib import AbstractContextManager, nullcontext
from pathlib import Path

import pytest

from .conftest import copy_of
from .support import GIT, git

pytestmark = pytest.mark.skipif(GIT is None, reason="git is needed to make a repository to copy")

Entries = Iterator["os.DirEntry[str]"]


def copied_as_it_goes(repository: Path, to: Path, gone: Path, patch: pytest.MonkeyPatch) -> Path:
    """Copy a repository in which a file is there when its folder is listed, and gone after."""
    listing = os.scandir

    def listed(folder: "str | os.PathLike[str]") -> AbstractContextManager[Entries]:
        with listing(folder) as found:
            entries = list(found)
        if Path(folder) == gone.parent:
            gone.unlink()
        return nullcontext(iter(entries))

    assert gone.is_file()
    with patch.context() as while_it_is_copied:
        while_it_is_copied.setattr(os, "scandir", listed)
        copy = copy_of(repository, to)
    assert not gone.exists()
    return copy


def test_nothing_writes_in_a_repository_once_git_has_answered(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A commit starts no other program, and leaves no lock behind it."""
    said = tmp_path / "what-git-did"
    monkeypatch.setenv("GIT_TRACE", str(said))
    (repository / "README.md").write_text("changed\n", encoding="utf-8")
    git(repository, "commit", "--quiet", "--all", "--message", "Change one file")
    did = said.read_text(encoding="utf-8").splitlines()
    assert any("trace: built-in: git commit" in line for line in did)
    assert [line for line in did if "run_command:" in line] == []
    assert not list((repository / ".git").rglob("*.lock"))
    assert git(repository, "log", "-1", "--format=%an %G?") == "A made-up person N"


@pytest.mark.parametrize("name", ["objects/maintenance.lock", "index.lock", "HEAD.lock"])
def test_a_lock_git_takes_away_while_a_repository_is_copied_is_not_missed(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
):
    lock = repository / ".git" / name
    lock.touch()
    copy = copied_as_it_goes(repository, tmp_path / "copy", lock, monkeypatch)
    assert not (copy / ".git" / name).exists()
    # The copy is the repository: the same commit, and every file as git took it.
    assert git(copy, "rev-parse", "HEAD") == git(repository, "rev-parse", "HEAD")
    assert git(copy, "status", "--porcelain") == ""


def test_a_lock_git_still_holds_is_left_out_of_a_copy(repository: Path, tmp_path: Path):
    """Git refuses to write where a lock is held, so a copy that held one could not be changed."""
    (repository / ".git" / "index.lock").touch()
    copy = copy_of(repository, tmp_path / "copy")
    assert not (copy / ".git" / "index.lock").exists()
    (copy / "README.md").write_text("changed\n", encoding="utf-8")
    git(copy, "commit", "--quiet", "--all", "--message", "Change one file")
    assert git(copy, "status", "--porcelain") == ""


@pytest.mark.parametrize("name", ["a/first.py", "a/held.lock", ".git/index", ".git/HEAD"])
def test_a_file_of_the_repository_that_is_gone_by_the_time_it_is_read_is_an_error(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
):
    """Only a lock of git's own is passed over. A file that ends as a lock does is a file."""
    (repository / name).touch()
    with pytest.raises(shutil.Error) as caught:
        copied_as_it_goes(repository, tmp_path / "copy", repository / name, monkeypatch)
    assert [Path(source) for source, _, _ in caught.value.args[0]] == [repository / name]
