"""What many tests read and none changes is made once in each process, and held to what it was.

A test that made a whole build to read one file of it made what the test before it had
made. So a thing of that kind is made once, in a folder of its own that pytest gives this
process, by the first test that asks for it. A test that only reads it is handed the
folder. A test that changes what it is given is handed a copy.

No test may change what the next one reads. So what each folder holds is noted when it
is made, and held to that when the run ends: `conftest.py` fails the run if a test wrote
to one, and names the folder.
"""

import hashlib
from pathlib import Path

import pytest

# The maker of folders that pytest gives this process. `conftest.py` puts it here for as
# long as the tests run, as the API's puts its one event loop in the support of its tests.
FOLDERS: list[pytest.TempPathFactory] = []
# What each folder held when it was made, by the folder.
_HELD: dict[Path, str] = {}


def folder_for(what: str) -> Path:
    """A new and empty folder of this process, for one thing that is made once."""
    assert FOLDERS, "a thing is made once only while the tests run"
    return FOLDERS[0].mktemp(what)


def holding(folder: Path) -> str:
    """One hash of every file under a folder: its path, and what it holds."""
    found = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            found.update(path.relative_to(folder).as_posix().encode() + b"\0")
            found.update(hashlib.sha256(path.read_bytes()).digest())
    return found.hexdigest()


def made(folder: Path) -> Path:
    """Note what a folder holds now that it is made. It is held to that when the run ends."""
    _HELD[folder] = holding(folder)
    return folder


def changed() -> list[str]:
    """The folders that no longer hold what they held when they were made."""
    return [folder.name for folder, held in _HELD.items() if holding(folder) != held]
