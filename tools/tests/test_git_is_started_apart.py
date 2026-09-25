"""Git, where a test starts it, keeps to the repository it is run in.

Some tests start git, and so does some of the code they test. `conftest.py` at the root
sets the environment that each is started in. Here git is started plainly, as any test
may start it, on a machine that is made up: a person's own settings are planted in a
folder of the test, and git is looked at for any sign that it read one, or wrote one.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

GIT = shutil.which("git")
pytestmark = pytest.mark.skipif(GIT is None, reason="git is needed to see what it reads")

# A string found nowhere else. If git read a setting that was planted, this shows.
CANARY = "zqx-planted-4471"
# What a person may have set, each of which would change what a test makes.
SETTINGS = f"""[user]
\tname = {CANARY}
[commit]
\tgpgsign = true
[gc]
\tauto = 1
\tautoDetach = true
[maintenance]
\tauto = true
"""
# What git is told, as it lists it: a name is listed in small letters.
TOLD = {
    "gc.auto": "0",
    "gc.autodetach": "false",
    "maintenance.auto": "false",
    "maintenance.autodetach": "false",
    "core.excludesfile": os.devnull,
    "core.attributesfile": os.devnull,
}
LOOKS = {
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_ATTR_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
}
A_MADE_UP_PERSON = {
    "GIT_AUTHOR_NAME": "A made-up person",
    "GIT_AUTHOR_EMAIL": "made-up@example.org",
    "GIT_COMMITTER_NAME": "A made-up person",
    "GIT_COMMITTER_EMAIL": "made-up@example.org",
}


def git(folder: Path, *words: str, **more: str) -> subprocess.CompletedProcess[str]:
    """Start git as a test starts it: by its name, in the environment of the test."""
    return subprocess.run(
        ["git", *words],
        cwd=folder,
        capture_output=True,
        text=True,
        check=False,
        env=os.environ | more,
    )


@pytest.fixture
def planted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[Path, bytes]:
    """A person's own folder, with every file of settings git looks for in one."""
    home = tmp_path / "home"
    files = {
        home / ".gitconfig": SETTINGS,
        home / ".config" / "git" / "config": SETTINGS,
        home / ".config" / "git" / "ignore": "planted*\n",
        home / ".config" / "git" / "attributes": "* text eol=crlf\n",
    }
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    return {path: path.read_bytes() for path in files}


@pytest.fixture
def repository(tmp_path: Path, planted: dict[Path, bytes]) -> Path:
    folder = tmp_path / "repository"
    folder.mkdir()
    assert git(folder, "init", "--quiet").returncode == 0
    return folder


def test_git_reads_the_settings_of_the_repository_and_what_it_is_told_and_no_other(
    repository: Path,
):
    listed = git(repository, "config", "--list", "--show-origin")
    assert listed.returncode == 0
    found = [line.split("\t", 1) for line in listed.stdout.splitlines()]
    assert {origin for origin, _ in found if origin.startswith("file:")} == {"file:.git/config"}
    told = [setting for origin, setting in found if not origin.startswith("file:")]
    assert sorted(told) == sorted(f"{name}={value}" for name, value in TOLD.items())
    assert CANARY not in listed.stdout


def test_nothing_the_run_was_started_with_for_git_is_handed_on():
    """Not another repository or its index, as when the tests are run from a hook of git."""
    told = {f"GIT_CONFIG_{part}_{at}" for at in range(len(TOLD)) for part in ("KEY", "VALUE")}
    handed_on = {name: held for name, held in os.environ.items() if name.startswith("GIT_")}
    assert {name for name in handed_on if name not in told} == {*LOOKS, "GIT_CONFIG_COUNT"}
    assert {name: handed_on[name] for name in LOOKS} == LOOKS


def test_git_passes_over_nothing_that_the_person_has_it_pass_over(repository: Path):
    (repository / "planted.txt").write_text("made up\n", encoding="utf-8")
    assert git(repository, "status", "--porcelain").stdout == "?? planted.txt\n"


def test_git_treats_a_file_as_the_repository_says_and_not_as_the_person_does(repository: Path):
    (repository / "made-up.txt").write_bytes(b"one\ntwo\n")
    assert git(repository, "add", "--all").returncode == 0
    (repository / "made-up.txt").unlink()
    assert git(repository, "checkout", "--", "made-up.txt").returncode == 0
    assert (repository / "made-up.txt").read_bytes() == b"one\ntwo\n"


# Whoever may write anywhere may write where the null device is, so nothing is tried as them.
@pytest.mark.skipif(os.geteuid() == 0, reason="the one who runs the tests may write anywhere")
def test_git_writes_no_setting_of_the_person(repository: Path, planted: dict[Path, bytes]):
    """A setting of the person's is written to the file of the person, and git is given none."""
    assert git(repository, "config", "--global", "user.name", CANARY).returncode != 0
    home = Path(os.environ["HOME"])
    assert {path: path.read_bytes() for path in home.rglob("*") if path.is_file()} == planted


def test_a_commit_is_not_signed_and_starts_no_upkeep_of_the_repository(
    repository: Path, tmp_path: Path
):
    """After a commit git looks the repository over, unless it is told not to: in a process
    it lets go of, which holds a lock in the repository for as long as it looks."""
    (repository / "made-up.txt").write_text("made up\n", encoding="utf-8")
    assert git(repository, "add", "--all").returncode == 0
    said = tmp_path / "what-git-did"
    done = git(
        repository, "commit", "--quiet", "--message", "One", **A_MADE_UP_PERSON, GIT_TRACE=str(said)
    )
    assert (done.returncode, done.stdout) == (0, "")
    did = said.read_text(encoding="utf-8").splitlines()
    assert any("trace: built-in: git commit" in line for line in did)
    assert [line for line in did if "run_command:" in line] == []
    assert not list((repository / ".git").rglob("*.lock"))
    assert git(repository, "log", "--format=%an %G?").stdout == "A made-up person N\n"
