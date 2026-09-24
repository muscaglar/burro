"""What the tests of evidence share that a test asks for by name: a repository to read.

It is made with git itself, once, and copied for each test that changes it.
Every file in it is made up.
"""

import shutil
from pathlib import Path

import pytest

from .support import CANARY, git

FILES = {
    "README.md": "Made up for a test.\n",
    "a.b": "a file that sorts before the folder a\n",
    "a/first.py": "FIRST = 1\n",
    "a/deeper/second.py": "SECOND = 2\n",
    "a0": "a file that sorts after the folder a\n",
    f"data/{CANARY}.csv": f"name\n{CANARY}\n",
    "data/café.csv": "name\nmade up\n",
}


def write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")


@pytest.fixture(scope="session")
def made(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A repository of made-up files, with everything committed. It is made once."""
    root = tmp_path_factory.mktemp("made") / "repository"
    root.mkdir()
    git(root, "init", "--quiet", "--initial-branch", "main")
    write(root, FILES)
    (root / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (root / "run.sh").chmod(0o755)
    (root / "latest").symlink_to("a/first.py")
    git(root, "add", "--all")
    git(root, "commit", "--quiet", "--message", "Make up some files")
    return root


@pytest.fixture
def repository(made: Path, tmp_path: Path) -> Path:
    """A copy of that repository, for one test to change."""
    return shutil.copytree(made, tmp_path / "repository", symlinks=True)
