"""What every test shares: how often Python looks for what to throw away, how git is
started, and two refusals.

The tests make millions of small records and let them go. Python stops to look for
records that nothing holds any more each time a few hundred have been made. Here that
frees next to nothing, and costs the tests a second or two of the time they may take.
So while the tests run it looks less often, in every process that runs them.

The tests run side by side, in several processes. Two that bind one port, or write one
path, fail only when they meet, which is in some runs and not in others. So a test that
binds a port of its own choosing, or opens a path of its own to write, is refused every
time it runs. See docs/adr/0020. What a program started by a test does is not seen.

Some tests start git, and so does some of the code they test. After a commit git looks the
repository over, in a process it lets go of, and holds a lock in the repository while it
looks. A test that copied the repository meanwhile found the lock listed and then gone, in
some runs and not in others. So git is started apart, by whatever starts it: it does no
upkeep of its own, and it reads no settings but those of the repository it is run in.

No code under test is changed by this, but that `bind` is asked through a function here.
"""

import gc
import os
import socket
import sys
import tempfile
from collections.abc import Generator, Iterator, MutableMapping
from typing import Any, cast

import pytest

gc.set_threshold(200_000, 20, 20)

# What git is told each time it is started, for that command alone: to collect nothing and
# keep nothing up of its own accord, and to let go of no process. The last two are the
# person's own files of what git passes over and of how it treats a file, which are read
# wherever they usually are unless another is named.
_GIT_IS_TOLD = {
    "gc.auto": "0",
    "gc.autoDetach": "false",
    "maintenance.auto": "false",
    "maintenance.autoDetach": "false",
    "core.excludesFile": os.devnull,
    "core.attributesFile": os.devnull,
}
# Where git looks for the settings of the machine and of the person: nowhere. It can write
# to neither, and it asks nobody for a password.
_GIT_LOOKS = {
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_ATTR_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
}


def _start_git_apart(environment: MutableMapping[str, str]) -> None:
    """Make the environment one in which git keeps to the repository it is run in.

    What the run was started with for git is dropped: another repository, its index, and
    settings of the machine that are handed down this way. What git is told is said in the
    environment, so that no file of settings is written, of a repository or of the machine.
    """
    for name in [name for name in environment if name.startswith("GIT_")]:
        del environment[name]
    environment.update(_GIT_LOOKS)
    environment["GIT_CONFIG_COUNT"] = str(len(_GIT_IS_TOLD))
    for at, (name, told) in enumerate(_GIT_IS_TOLD.items()):
        environment[f"GIT_CONFIG_KEY_{at}"] = name
        environment[f"GIT_CONFIG_VALUE_{at}"] = told


_start_git_apart(os.environ)

# What a flag of `os.open` holds when the file is opened to be written.
_TO_WRITE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
# Worked out once, and never inside the watcher: `tempfile` holds a lock while it opens.
# A path is held as text throughout: the watcher hears of every file that is opened, tens
# of thousands in a run, and asks the system about a path only when it is about to refuse.
_TEMPORARY = os.path.abspath(tempfile.gettempdir())  # noqa: PTH100
_DEVICES = os.path.dirname(os.path.abspath(os.devnull)) + os.sep  # noqa: PTH100, PTH120
# Python keeps what it compiled beside a module, in a folder it makes the first time it
# imports one. In a working copy that is new, that is inside whichever test imports it.
_BYTECODE = f"{os.sep}__pycache__{os.sep}"


class _Kept:
    """What is known of the test that is running, in this process."""

    # The test that is running, if one is. Nothing is refused between tests.
    test: str | None = None
    # The folder pytest gives this process, as written and as the system resolves it.
    own: tuple[str, ...] = ()
    # Every name the system made up when asked for a temporary file or folder.
    named: set[str] = set()  # noqa: RUF012
    # Every port the system chose when asked for any.
    given: set[int] = set()  # noqa: RUF012
    # What the test that is running did that it may not.
    strayed: list[str] = []  # noqa: RUF012


def _within(path: str) -> bool:
    """Whether a path is the test's to write: under its own folder, or under a made-up name."""
    if path.startswith(_Kept.own):
        return True
    at = path
    while at not in _Kept.named:
        above: str = os.path.dirname(at)  # noqa: PTH120
        if above == at:
            return False
        at = above
    return True


def _may_be_written(path: str) -> bool:
    if path == _TEMPORARY or path.startswith(_DEVICES) or _BYTECODE in path + os.sep:
        # `TemporaryFile` opens the folder itself, and names the file as it does. With a
        # separator after it, the folder of bytecode is found as what is in it is.
        return True
    return _within(path) or _within(os.path.realpath(path))


def _refuse(what: str) -> None:
    said = f"{what} See docs/adr/0020."
    _Kept.strayed.append(said)
    pytest.fail(said)


def _watch(event: str, args: tuple[Any, ...]) -> None:
    """Hear of every file that is opened and every folder that is made, and refuse some."""
    if event in ("tempfile.mkstemp", "tempfile.mkdtemp"):
        _Kept.named.add(os.path.abspath(args[0]))  # noqa: PTH100
        _Kept.named.add(os.path.realpath(args[0]))
        return
    if _Kept.test is None or not _Kept.own or event not in ("open", "os.mkdir"):
        return
    if not isinstance(args[0], (str, bytes, os.PathLike)):
        # A file that is open already, by its number.
        return
    path = cast("str | bytes | os.PathLike[str]", args[0])
    if event == "open":
        mode, flags = args[1], args[2]
        to_write = flags & _TO_WRITE if isinstance(flags, int) else set(mode or "") & set("wax+")
        if not to_write:
            return
    elif len(args) > 2 and isinstance(args[2], int) and args[2] != -1:
        # A folder made beside one that is held open: where that one is, is not said.
        return
    where = os.path.abspath(os.fsdecode(path))  # noqa: PTH100
    if not _may_be_written(where):
        _refuse(
            f"A test writes only under the folder pytest gives it. This one wrote to {where}. "
            "Ask for `tmp_path`, or for a name from `tempfile`."
        )


_bind = socket.socket.bind


def _port_of(address: object) -> int | None:
    """The port of an address on a network. A socket of the machine's own has a path."""
    if isinstance(address, tuple):
        parts = cast("tuple[object, ...]", address)
        if len(parts) > 1 and isinstance(parts[1], int):
            return parts[1]
    return None


def _bound(self: socket.socket, address: Any) -> None:
    """Bind as asked, but not to a port the test chose. Remember each port the system chose."""
    port = _port_of(address)
    chosen = port is not None and port != 0 and port not in _Kept.given
    if chosen and _Kept.test is not None:
        _refuse(
            f"A test binds no port of its own choosing. This one asked for port {port}. "
            "Ask for port 0 and read which port was given."
        )
    _bind(self, address)
    if port == 0:
        _Kept.given.add(self.getsockname()[1])


socket.socket.bind = _bound
sys.addaudithook(_watch)


@pytest.fixture(scope="session", autouse=True)
def the_folder_of_this_process(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Where this process may write: the folder pytest gives it, and no other process."""
    folder = str(tmp_path_factory.getbasetemp())
    _Kept.own = tuple({folder + os.sep, os.path.realpath(folder) + os.sep})


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item) -> Generator[None, object, object]:
    _Kept.test = item.nodeid
    _Kept.strayed.clear()
    try:
        return (yield)
    finally:
        _Kept.test = None


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, object, object]:
    try:
        return (yield)
    except pytest.fail.Exception as failed:
        # The test failed of it where it happened, so it has been said.
        _Kept.strayed[:] = [each for each in _Kept.strayed if each != str(failed)]
        raise


@pytest.fixture(autouse=True)
def a_test_keeps_to_itself() -> Iterator[None]:
    """Fail the test for what it did, though it hid the failure or did it in a thread."""
    yield
    if _Kept.strayed:
        said = "\n".join(dict.fromkeys(_Kept.strayed))
        _Kept.strayed.clear()
        pytest.fail(said, pytrace=False)
