"""A test is run on a hosted runner as it is run anywhere.

A hosted runner tells every step that it is a runner, which run it is, and where its own
files are. What a step writes to one of those is shown on the page of the run, or handed
to the next step. Some tools here write to one where one is named, so a test that started
such a tool with what it was handed wrote to the runner's own file. `conftest.py` at the
root takes what a runner sets out of the environment before any test runs.

Here the tests are started as a step of a hosted run starts them: with each of those set,
to a file or a folder that stands outside the folder of any test. They are written to a
folder of their own with a copy of that `conftest.py`, and run there by pytest in a
process of its own, once for all of them. A file of the runner is named and is not there,
so that a tool that only opens it to write leaves it behind.
"""

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# Where a step could write something the website shows, as tools/public_log.py lists them.
FILES = ("GITHUB_STEP_SUMMARY", "GITHUB_OUTPUT", "GITHUB_ENV", "GITHUB_PATH", "GITHUB_STATE")
# The folders a runner names, each by what a runner calls it: its own, and the repository's.
FOLDERS = {"RUNNER_TEMP": "_temp", "GITHUB_WORKSPACE": "work"}
# What a runner says of itself and of the run, and what it keeps for the actions it runs.
SAID = {
    "CI": "true",
    "GITHUB_ACTIONS": "true",
    "GITHUB_RUN_ID": "1234567890",
    "GITHUB_REF": "refs/heads/made-up",
    "RUNNER_OS": "Linux",
    "RUNNER_DEBUG": "1",
    "ACTIONS_RUNTIME_TOKEN": "made-up-token-0123456789",
}
# What a failure says of itself, which is longer than any line pytest cuts to fit a page.
AT_LENGTH = "it is said in full, " * 40 + "to the end"

TESTS = f'''
import os
import subprocess
import sys
from pathlib import Path

import pytest
import release_lock

TOOL = str(Path(release_lock.__file__).resolve())
RELEASE = "lon-2026-09-23-01"
FILES = {FILES!r}
# A step at its worst: it writes to every file that it is told a runner reads.
WORST = (
    "import os\\n"
    f"for name in {{FILES!r}}:\\n"
    "    if name in os.environ:\\n"
    "        open(os.environ[name], 'a').write('made-up row')\\n"
)


def set_by_a_runner(environment):
    begins = ("GITHUB_", "RUNNER_", "ACTIONS_")
    return sorted(name for name in environment if name == "CI" or name.startswith(begins))


def test_nothing_a_runner_sets_is_in_the_environment():
    assert set_by_a_runner(os.environ) == []


def test_runs_a_tool_in_its_own_process(tmp_path, capsys):
    """No build is in the folder, so each command ends with 1, once it has opened what it
    writes to."""
    assert release_lock.main(["hash", "a", str(tmp_path), RELEASE]) == 1
    assert release_lock.main(["show", str(tmp_path), RELEASE]) == 1
    assert capsys.readouterr().out.count("status=unreadable") == 2


def test_starts_a_tool_as_a_program(tmp_path):
    for words in (["hash", "a", str(tmp_path), RELEASE], ["show", str(tmp_path), RELEASE]):
        plainly = subprocess.run([sys.executable, TOOL, *words], capture_output=True, check=False)
        handed_on = subprocess.run(
            [sys.executable, TOOL, *words],
            capture_output=True,
            check=False,
            env=os.environ | {{"COPY_A": "made up"}},
        )
        assert (plainly.returncode, handed_on.returncode) == (1, 1)


def test_starts_a_step_at_its_worst():
    ran = subprocess.run([sys.executable, "-c", WORST], capture_output=True, check=False)
    assert (ran.returncode, ran.stderr) == (0, b"")


def test_names_a_file_under_its_own_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "outputs"))
    assert release_lock.main(["hash", "a", str(tmp_path / "build"), RELEASE]) == 1
    assert (tmp_path / "outputs").read_bytes() == b""
    ran = subprocess.run([sys.executable, "-c", WORST], capture_output=True, check=False)
    assert ran.returncode == 0
    assert (tmp_path / "outputs").read_text(encoding="utf-8") == "made-up row"


def test_fails_and_says_why_at_length():
    pytest.fail({AT_LENGTH!r})
'''


@dataclass(frozen=True)
class Ran:
    # How each test ended, by its name: PASSED, FAILED or ERROR.
    ended: dict[str, str]
    printed: str
    # The folder that holds all that the runner named, and what it held before the tests ran.
    runner: Path
    before: list[str]

    def holds(self) -> list[str]:
        return sorted(str(path.relative_to(self.runner)) for path in self.runner.rglob("*"))


@pytest.fixture(scope="module")
def ran(tmp_path_factory: pytest.TempPathFactory) -> Ran:
    folder = tmp_path_factory.mktemp("on-a-runner")
    tests, own, runner = folder / "tests", folder / "own", folder / "runner"
    tests.mkdir()
    (tests / "test_them.py").write_text(TESTS, encoding="utf-8")
    (tests / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    shutil.copy(ROOT / "conftest.py", tests / "conftest.py")
    # What a runner makes before a step: the folders it names, and the folder of its files.
    named = {name: runner / folder for name, folder in FOLDERS.items()}
    named |= {name: runner / "_temp" / "_runner_file_commands" / name.lower() for name in FILES}
    for name in FOLDERS:
        named[name].mkdir(parents=True)
    (runner / "_temp" / "_runner_file_commands").mkdir()
    before = sorted(str(path.relative_to(runner)) for path in runner.rglob("*"))
    told = SAID | {name: str(path) for name, path in named.items()}
    command = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-rA"]
    done = subprocess.run(
        [*command, "--basetemp", str(own), "--disable-socket", "--allow-unix-socket"],
        cwd=tests,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        # The page is no wider than a failure is long, whatever started these tests.
        env=os.environ | told | {"PYTHONPATH": str(ROOT / "tools"), "COLUMNS": "80"},
    )
    found = re.findall(r"^(PASSED|FAILED|ERROR) test_them\.py::(\w+)", done.stdout, re.M)
    ended: dict[str, str] = {}
    for how, name in found:
        # A test that passes and then fails as it is cleared away is printed as both.
        if ended.get(name, "PASSED") == "PASSED":
            ended[name] = how
    assert ended, done.stdout + done.stderr
    return Ran(ended, done.stdout, runner, before)


def test_what_a_runner_sets_is_taken_out_before_any_test_runs(ran: Ran):
    assert ran.ended["test_nothing_a_runner_sets_is_in_the_environment"] == "PASSED"


@pytest.mark.parametrize(
    "started",
    [
        "test_runs_a_tool_in_its_own_process",
        "test_starts_a_tool_as_a_program",
        "test_starts_a_step_at_its_worst",
    ],
)
def test_a_tool_that_a_test_starts_is_told_of_no_file_of_the_runner(ran: Ran, started: str):
    assert ran.ended[started] == "PASSED", ran.printed


def test_no_file_of_the_runner_is_made_or_written_and_nothing_is_left_in_its_folders(ran: Ran):
    """No file that was named was there, so one that was only opened to write would be."""
    assert ran.ended
    assert ran.before == ["_temp", "_temp/_runner_file_commands", "work"]
    assert ran.holds() == ran.before


def test_a_test_may_name_a_file_under_its_own_folder_for_a_tool_to_write_to(ran: Ran):
    """It is how a test tries what a tool does on a runner. The tool goes where it is told."""
    assert ran.ended["test_names_a_file_under_its_own_folder"] == "PASSED", ran.printed


def test_on_a_runner_what_a_failure_said_is_still_summed_up_in_full(ran: Ran):
    """pytest cuts the line of a failure to the width of the page, but where it reads that
    it is on a runner. A hosted run says those lines again where anyone can read them."""
    name = "test_fails_and_says_why_at_length"
    assert ran.ended[name] == "FAILED"
    [line] = re.findall(rf"^FAILED test_them\.py::{name} - (.*)$", ran.printed, re.M)
    assert line == f"Failed: {AT_LENGTH}"


def test_every_test_of_the_made_up_file_was_run(ran: Ran):
    assert sorted(ran.ended) == sorted(re.findall(r"^def (test_\w+)", TESTS, re.M))
