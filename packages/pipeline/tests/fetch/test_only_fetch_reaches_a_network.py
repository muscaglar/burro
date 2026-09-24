"""Fetch is the only step of a build that may reach a network.

Two modules may open a connection: the downloader, which asks a publisher, and
the object store. Every other module of the pipeline and of core is read here,
and fails the test if it so much as names a library that can reach a network,
run another program, or load a module by a name worked out at run time.

The run blocks sockets as well, so every test but those marked for the
loopback stand-in proves the same of the code it drives.
"""

import ast
import http.client
import socket
import sys
from functools import cache
from pathlib import Path

import burro_core
import burro_pipeline
import pytest
from burro_pipeline.fetch.offline import NetworkRefused, sockets_refused

from .support import ONLY_LOOPBACK

PACKAGES = (Path(burro_pipeline.__file__).parent, Path(burro_core.__file__).parent)
MODULES = sorted(path for package in PACKAGES for path in package.rglob("*.py"))
FETCH = Path(burro_pipeline.__file__).parent / "fetch"

# The only modules that may open a connection.
MAY_REACH_A_NETWORK = {FETCH / "download.py", FETCH / "s3.py"}
# The guard itself names `socket`, to put a refusal in its place.
THE_GUARD = FETCH / "offline.py"

REACHES_A_NETWORK = {
    "socket",
    "socketserver",
    "ssl",
    "select",
    "selectors",
    "asyncio",
    "http",
    "urllib.request",
    "urllib.robotparser",
    "ftplib",
    "imaplib",
    "poplib",
    "smtplib",
    "xmlrpc",
    "webbrowser",
    "wsgiref",
    "multiprocessing",
}
RUNS_A_PROGRAM = {"subprocess", "pty", "ctypes"}
LOADS_BY_NAME = {"importlib", "runpy", "pkgutil", "zipimport"}
# Every package the pipeline and core may import that is not part of Python. One that is
# added may be able to reach a network by itself, so it is added here by a person, with
# a reason in the change. Rule 12 of AGENTS.md.
# `shapely` joins and measures outlines, and `pyproj` turns the National Grid to longitude and
# latitude. Both are named in section 13 of the pipeline design, and one module imports them:
# `cells/shapes.py`. Neither is asked to reach a network: the coordinate library's own
# fetching of grid files is turned off there, and a test holds it off.
# `pyarrow` reads the one publisher's file that is laid out as Parquet and packed with zstd,
# which Python cannot unpack by itself. One module imports it: `derive/culture_file.py`. It
# is handed a file that is open and never an address, and it is asked for the reader of
# Parquet alone: the parts of it that open a file by its address are never named.
PACKAGES_ALLOWED = {"burro_core", "burro_pipeline", "pydantic", "pyarrow", "pyproj", "shapely"}
# The one module that names the Parquet library, and the parts of the library it may name.
READS_PARQUET = Path(burro_pipeline.__file__).parent / "derive" / "culture_file.py"
OF_THE_PARQUET_LIBRARY = {"pyarrow", "pyarrow.parquet"}
NEVER_CALLED = {"__import__", "eval", "exec", "compile", "breakpoint"}


@cache
def parsed(path: Path) -> ast.Module:
    """A module as Python reads it. Three tests read each module, and it is parsed once."""
    return ast.parse(path.read_text(encoding="utf-8"))


def imported(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(parsed(path)):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"{path.name} imports by full name"
            found.add(node.module or "")
            found |= {f"{node.module}.{alias.name}" for alias in node.names}
    return found


def within(names: set[str], families: set[str]) -> set[str]:
    return {
        name
        for name in names
        for family in families
        if name == family or name.startswith(f"{family}.")
    }


def label(path: Path) -> str:
    return path.relative_to(path.parents[[p.name for p in path.parents].index("src")]).as_posix()


def test_there_is_something_to_check():
    assert set(MODULES) >= MAY_REACH_A_NETWORK
    assert THE_GUARD in MODULES
    assert len(MODULES) > 30


@pytest.mark.parametrize("path", MODULES, ids=label)
def test_no_other_module_names_a_library_that_reaches_a_network(path: Path):
    names = imported(path)
    allowed = (
        REACHES_A_NETWORK
        if path in MAY_REACH_A_NETWORK
        else {"socket"}
        if path == THE_GUARD
        else set[str]()
    )
    found = within(names, REACHES_A_NETWORK) - within(names, allowed)
    assert not found, f"{label(path)} names {sorted(found)}: only fetch may reach a network"


@pytest.mark.parametrize("path", MODULES, ids=label)
def test_no_module_runs_a_program_or_loads_a_module_by_name(path: Path):
    names = imported(path)
    found = within(names, RUNS_A_PROGRAM | LOADS_BY_NAME)
    assert not found, f"{label(path)} names {sorted(found)}"
    tree = parsed(path)
    called = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} & NEVER_CALLED
    assert not called, f"{label(path)} names {sorted(called)}"
    through_os = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "os"
        and (
            node.attr.startswith(("spawn", "exec", "posix_spawn"))
            or node.attr in ("system", "popen", "fork")
        )
    }
    assert not through_os, f"{label(path)} runs a program through os.{sorted(through_os)[0]}"


@pytest.mark.parametrize("path", MODULES, ids=label)
def test_every_package_that_is_not_part_of_python_is_one_a_person_allowed(path: Path):
    tops = {name.split(".")[0] for name in imported(path) if name}
    outside = tops - set(sys.stdlib_module_names) - PACKAGES_ALLOWED
    assert not outside, f"{label(path)} imports {sorted(outside)}: see PACKAGES_ALLOWED"


def test_one_module_names_the_parquet_library_and_only_its_reader():
    """The library can open a file on an object store by its address. It is never asked to."""
    naming = {
        path: {name for name in imported(path) if name.split(".")[0] == "pyarrow"}
        for path in MODULES
    }
    assert {path for path, names in naming.items() if names} == {READS_PARQUET}
    assert naming[READS_PARQUET] == OF_THE_PARQUET_LIBRARY


def test_the_parquet_library_is_handed_a_file_that_is_open_and_never_an_address():
    """Handed words in place of a file, the library opens what they name, and may reach for it.

    So the one module that names the library asks it for two things and no other: to read a
    file, and to read a footer. Each is handed a file that is open, by its name in the
    module, or bytes that are held. Nothing else of the library is named but its types.
    """
    tree = parsed(READS_PARQUET)
    short = {"pq": "pyarrow.parquet", "pa": "pyarrow"}
    asked = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id in short
    ]
    assert {(node.value.id, node.attr) for node in asked if isinstance(node.value, ast.Name)} == {
        ("pq", "ParquetFile"),
        ("pq", "read_metadata"),
        ("pa", "types"),
        ("pa", "ArrowException"),
    }
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "pq"
    ]
    assert len(calls) == 3
    for call in calls:
        assert {word.arg for word in call.keywords} <= {"metadata", "pre_buffer"}
        (handed,) = call.args
        assert ast.unparse(handed) in ("file", "view", "io.BytesIO(view.footer_alone())")
    opened = [
        ast.unparse(item.context_expr)
        for node in ast.walk(tree)
        if isinstance(node, ast.With)
        for item in node.items
    ]
    assert "opened.path.open('rb')" in opened
    assert "TakenFile(opened.path, taken.runs, taken.of_bytes)" in opened


def test_the_downloader_reads_no_proxy_cookie_or_login_from_the_machine():
    """`urllib.request` would read proxies and logins from the environment. It is not used."""
    names = imported(FETCH / "download.py") | imported(FETCH / "s3.py")
    assert not within(names, {"urllib.request", "http.cookiejar", "netrc", "getpass", "os"})


@ONLY_LOOPBACK
def test_inside_the_guard_no_socket_can_be_made_and_no_name_looked_up():
    """The run would let this test reach the loopback address. The guard does not."""
    with sockets_refused():
        with pytest.raises(NetworkRefused):
            socket.socket()
        with pytest.raises(NetworkRefused):
            socket.create_connection(("127.0.0.1", 9), timeout=0.01)
        with pytest.raises(NetworkRefused):
            socket.socketpair()
        with pytest.raises(NetworkRefused):
            socket.getaddrinfo("made-up.example", 443)
        with pytest.raises(NetworkRefused):
            socket.gethostbyname("made-up.example")
        with pytest.raises(NetworkRefused):
            http.client.HTTPConnection("127.0.0.1", 9, timeout=0.01).connect()


def test_the_guard_puts_back_what_it_found():
    before = socket.socket, socket.getaddrinfo
    with sockets_refused():
        with sockets_refused():
            assert socket.socket is not before[0]
        assert socket.socket is not before[0]
        assert socket.getaddrinfo is not before[1]
    assert (socket.socket, socket.getaddrinfo) == before


def test_the_guard_puts_back_what_it_found_after_a_failure():
    before = socket.socket
    with pytest.raises(ValueError, match="made up"), sockets_refused():
        raise ValueError("made up")
    assert socket.socket is before
