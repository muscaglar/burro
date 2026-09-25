"""What the tests of kept share: the made-up build, and the steps run as a person runs them.

Nothing here is real. The build is the made-up build of the tests of assemble:
two boroughs that do not exist, drawn in the North Sea, under the ids of a
release of London, because only such a release has a lock.
"""

import io
import shutil
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import release_lock
from burro_pipeline.kept import cli
from burro_pipeline.kept.store import FOLDER_VARIABLE

from ..assemble.support import RELEASE, built_once

OTHER = "lon-2026-09-23-02"
MADE_UP = "syn-2026-09-23-01"


def built(folder: Path) -> Path:
    """What the made-up build wrote, in a folder of the test's own. Gives that folder.

    The build is made once, and each test is handed a copy of what it wrote: the same
    bytes wherever it is built, which a test of the build holds. So a test may change
    what it is given, and the next is given what was built.
    """
    return shutil.copytree(built_once().out, folder / "out")


def approve(folder: Path, out: Path, release: str = RELEASE) -> Path:
    """The folder of locks that are committed, with the lock of one build in it."""
    folder.mkdir(parents=True, exist_ok=True)
    lock = release_lock.written(release_lock.lock_of(out, release))
    (folder / f"{release}.json").write_text(lock, encoding="utf-8")
    return folder


def run(arguments: list[str], environment: dict[str, str]) -> tuple[int, list[str], str]:
    """Run a step. Gives its exit code, the lines it printed, and its words."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        status = cli.main(arguments, environment)
    return status, out.getvalue().splitlines(), err.getvalue()


def keep(out: Path, store: Path, release: str = RELEASE) -> tuple[int, list[str], str]:
    return run(["keep", str(out), "--release", release], {FOLDER_VARIABLE: str(store)})


def take(to: Path, store: Path, locks: Path, *more: str) -> tuple[int, list[str], str]:
    """Take a release to a folder that is in no repository, as a test's own folder is."""
    top = to.parent / "no-repository"
    top.mkdir(exist_ok=True)
    arguments = ["take", "--out", str(to), "--approved", str(locks), "--root", str(top), *more]
    return run(arguments, {FOLDER_VARIABLE: str(store)})
