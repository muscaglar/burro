"""A test that binds a port of its own choosing, or writes a path of its own, is refused.

The tests run side by side, in several processes. Two that bind one port, or write one
path, fail only when they meet, which is in some runs and not in others. So the rule is
held by `conftest.py` at the root and not by luck: such a test fails every time it runs,
alone or beside others, and is told what it did.

Each test here is about a careless test or a careful one. They are written to a folder
of their own with a copy of that `conftest.py`, and run there by pytest in a process of
its own, once for all of them.
"""

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# A port no test is given by asking for 0 on a machine that keeps to the usual range.
PORT = 1_717

TESTS = """
import os
import socket
import sqlite3
import tempfile
import threading
from pathlib import Path

import pytest

PORT = 1_717
FIXED = Path(tempfile.gettempdir()) / "burro-a-path-of-its-own.txt"
pytestmark = pytest.mark.allow_hosts(["127.0.0.1"])


def test_binds_a_port_of_its_own():
    with socket.socket() as held:
        held.bind(("127.0.0.1", PORT))


def test_asks_for_any_port():
    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        assert held.getsockname()[1] != 0


def test_binds_again_the_port_it_was_given():
    with socket.socket() as first:
        first.bind(("127.0.0.1", 0))
        given = first.getsockname()[1]
    with socket.socket() as again:
        again.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        again.bind(("127.0.0.1", given))


def test_writes_a_path_of_its_own():
    FIXED.write_text("left behind", encoding="utf-8")


def test_writes_beside_itself():
    Path("left-in-the-folder-it-ran-in.txt").write_text("left behind", encoding="utf-8")


def test_makes_a_folder_of_its_own():
    (Path(tempfile.gettempdir()) / "burro-a-folder-of-its-own").mkdir(exist_ok=True)


def test_writes_a_path_of_its_own_and_hides_the_failure():
    try:
        FIXED.write_text("left behind", encoding="utf-8")
    except Exception:
        pass


def test_writes_a_path_of_its_own_and_hides_whatever_is_raised():
    try:
        FIXED.write_text("left behind", encoding="utf-8")
    except BaseException:
        pass


def test_writes_a_path_of_its_own_in_a_thread():
    def write():
        FIXED.write_text("left behind", encoding="utf-8")

    thread = threading.Thread(target=write)
    thread.start()
    thread.join()


@pytest.fixture(scope="module")
def made_once():
    FIXED.write_text("left behind", encoding="utf-8")


def test_is_given_what_wrote_a_path_of_its_own(made_once):
    pass


def test_writes_where_pytest_says(tmp_path, tmp_path_factory):
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "c.txt").write_text("kept to itself", encoding="utf-8")
    with (tmp_path / "d.bin").open("ab") as file:
        file.write(b"kept to itself")
    (tmp_path_factory.mktemp("more") / "e.txt").write_text("kept to itself", encoding="utf-8")
    sqlite3.connect(tmp_path / "f.sqlite").close()


def test_writes_what_the_system_names(monkeypatch, tmp_path):
    with tempfile.TemporaryDirectory() as folder:
        (Path(folder) / "a.txt").write_text("kept to itself", encoding="utf-8")
        (Path(folder).resolve() / "b.txt").write_text("kept to itself", encoding="utf-8")
        (Path(folder) / "c").mkdir()
    with tempfile.TemporaryFile() as file:
        file.write(b"kept to itself")
    with tempfile.NamedTemporaryFile() as file:
        file.write(b"kept to itself")
    number, name = tempfile.mkstemp()
    os.close(number)
    Path(name).write_text("kept to itself", encoding="utf-8")
    Path(name).unlink()
    with open(os.devnull, "w", encoding="utf-8") as file:
        file.write("kept to itself")
    monkeypatch.chdir(tmp_path)
    Path("beside-itself.txt").write_text("kept to itself", encoding="utf-8")


def test_is_the_first_to_import_a_module():
    import imported_late.module

    assert imported_late.module.SAID == "kept to itself"
    assert Path(imported_late.module.__cached__).is_file()


def test_reads_what_is_anywhere():
    assert Path(__file__).read_text(encoding="utf-8")
    with open(__file__, "rb") as file:
        assert file.read(1)
    assert os.listdir(tempfile.gettempdir()) is not None
"""


@dataclass(frozen=True)
class Ran:
    # How each test ended, by its name: PASSED, FAILED or ERROR.
    ended: dict[str, str]
    printed: str
    folder: Path

    def said_of(self, name: str) -> str:
        """What was printed of one test that did not pass."""
        # A heading is drawn to the width of the page, so a long name has one line a side.
        parts = re.split(r"^_+ (?:ERROR at \w+ of )?(\w+) _+$", self.printed, flags=re.M)
        found = zip(parts[1::2], parts[2::2], strict=True)
        return "".join(text for test, text in found if test == name)


def run(folder: Path, *words: str) -> subprocess.CompletedProcess[str]:
    """Run pytest in a folder of its own, under the `conftest.py` of this repository."""
    shutil.copy(ROOT / "conftest.py", folder / "conftest.py")
    (folder / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    command = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-rA", *words]
    socket_block = ["--disable-socket", "--allow-unix-socket"]
    return subprocess.run(
        [*command, *socket_block],
        cwd=folder,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


@pytest.fixture(scope="module")
def ran(tmp_path_factory: pytest.TempPathFactory) -> Ran:
    folder = tmp_path_factory.mktemp("kept")
    (folder / "test_them.py").write_text(TESTS, encoding="utf-8")
    # A package that nothing has imported: Python has made no folder for its bytecode.
    (folder / "imported_late").mkdir()
    (folder / "imported_late" / "__init__.py").write_text("", encoding="utf-8")
    (folder / "imported_late" / "module.py").write_text(
        'SAID = "kept to itself"\n', encoding="utf-8"
    )
    done = run(folder)
    ended: dict[str, str] = {}
    for how, name in re.findall(r"^(PASSED|FAILED|ERROR) test_them\.py::(\w+)", done.stdout, re.M):
        # A test that passes and then fails as it is cleared away is printed as both.
        if ended.get(name, "PASSED") == "PASSED":
            ended[name] = how
    assert ended, done.stdout + done.stderr
    return Ran(ended, done.stdout, folder)


def test_a_test_that_binds_a_port_of_its_own_choosing_fails_and_is_told_the_port(ran: Ran):
    assert ran.ended["test_binds_a_port_of_its_own"] == "FAILED"
    said = ran.said_of("test_binds_a_port_of_its_own")
    assert f"port {PORT}" in said and "port 0" in said


def test_a_test_that_asks_for_any_port_passes(ran: Ran):
    assert ran.ended["test_asks_for_any_port"] == "PASSED"


def test_a_test_may_bind_again_the_port_it_was_given(ran: Ran):
    """As a test does that stops a server and starts it again where it was."""
    assert ran.ended["test_binds_again_the_port_it_was_given"] == "PASSED"


def test_a_test_that_writes_a_path_of_its_own_fails_and_is_told_the_path(ran: Ran):
    assert ran.ended["test_writes_a_path_of_its_own"] == "FAILED"
    said = ran.said_of("test_writes_a_path_of_its_own")
    assert "burro-a-path-of-its-own.txt" in said and "tmp_path" in said


def test_a_test_that_writes_in_the_folder_it_ran_in_fails(ran: Ran):
    assert ran.ended["test_writes_beside_itself"] == "FAILED"
    assert not (ran.folder / "left-in-the-folder-it-ran-in.txt").exists()


def test_a_test_that_makes_a_folder_of_its_own_fails(ran: Ran):
    assert ran.ended["test_makes_a_folder_of_its_own"] == "FAILED"
    assert "burro-a-folder-of-its-own" in ran.said_of("test_makes_a_folder_of_its_own")


def test_nothing_is_written_at_a_path_a_test_chose(ran: Ran):
    import tempfile

    assert ran.ended
    assert not (Path(tempfile.gettempdir()) / "burro-a-path-of-its-own.txt").exists()
    assert not (Path(tempfile.gettempdir()) / "burro-a-folder-of-its-own").exists()


def test_a_test_that_hides_the_failure_fails_all_the_same(ran: Ran):
    assert ran.ended["test_writes_a_path_of_its_own_and_hides_the_failure"] == "FAILED"
    name = "test_writes_a_path_of_its_own_and_hides_whatever_is_raised"
    assert ran.ended[name] == "ERROR"
    assert "burro-a-path-of-its-own.txt" in ran.said_of(name)


def test_what_a_test_did_is_said_once(ran: Ran):
    """Where it happened, with the line. Not again as the test is cleared away."""
    for name in ("test_binds_a_port_of_its_own", "test_writes_a_path_of_its_own"):
        said = re.findall(rf"^(?:FAILED|ERROR) test_them\.py::{name}\b", ran.printed, re.M)
        assert len(said) == 1


def test_a_write_made_in_a_thread_fails_the_test_that_started_it(ran: Ran):
    name = "test_writes_a_path_of_its_own_in_a_thread"
    assert ran.ended[name] in ("FAILED", "ERROR")
    assert "burro-a-path-of-its-own.txt" in ran.said_of(name)


def test_a_write_made_once_for_many_tests_fails_the_test_it_was_made_for(ran: Ran):
    name = "test_is_given_what_wrote_a_path_of_its_own"
    assert ran.ended[name] in ("FAILED", "ERROR")
    assert "burro-a-path-of-its-own.txt" in ran.said_of(name)


def test_a_test_that_writes_where_pytest_says_passes(ran: Ran):
    assert ran.ended["test_writes_where_pytest_says"] == "PASSED"


def test_a_test_that_writes_what_the_system_names_passes(ran: Ran):
    """A name the system makes up is no path of the test's own: no two are the same."""
    assert ran.ended["test_writes_what_the_system_names"] == "PASSED"


def test_a_test_may_read_anything(ran: Ran):
    assert ran.ended["test_reads_what_is_anywhere"] == "PASSED"


def test_a_test_may_be_the_first_to_import_a_module(ran: Ran):
    """Python keeps what it compiled beside the module, in a folder it makes when it first
    imports one. In a working copy that is new, that is inside whichever test imports it."""
    assert ran.ended["test_is_the_first_to_import_a_module"] == "PASSED"
    assert (ran.folder / "imported_late" / "__pycache__").is_dir()


def test_every_test_of_the_made_up_file_was_run(ran: Ran):
    assert sorted(ran.ended) == sorted(re.findall(r"^def (test_\w+)", TESTS, re.M))


CARELESS = """
import socket
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.allow_hosts(["127.0.0.1"])


def test_binds_a_port_of_its_own():
    with socket.socket() as held:
        held.bind(("127.0.0.1", 1_717))


def test_writes_a_path_of_its_own():
    (Path(tempfile.gettempdir()) / "burro-a-path-of-its-own.txt").write_text("a", encoding="utf-8")
"""


def test_careless_tests_fail_every_time_whether_or_not_they_meet(tmp_path: Path):
    """Side by side and one after another: it is never a matter of when each ran."""
    for name in ("test_one.py", "test_two.py"):
        (tmp_path / name).write_text(CARELESS, encoding="utf-8")

    for words in (["-n", "2", "--dist", "loadfile"], ["-p", "no:xdist"]):
        done = run(tmp_path, *words)

        failed = re.findall(r"^FAILED (test_\w+\.py::\w+)", done.stdout, re.M)
        assert sorted(failed) == [
            "test_one.py::test_binds_a_port_of_its_own",
            "test_one.py::test_writes_a_path_of_its_own",
            "test_two.py::test_binds_a_port_of_its_own",
            "test_two.py::test_writes_a_path_of_its_own",
        ], done.stdout + done.stderr
