"""The made-up town is routed once for the tests that read what the step wrote."""

import io
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path

import pytest
from burro_pipeline import cli
from burro_pipeline.travel.made_up import RELEASE_ID


@dataclass(frozen=True)
class Routed:
    """What one run of the step left: the folder of the release, and what it printed."""

    folder: Path
    out: str
    err: str
    code: int


def run(*arguments: str) -> tuple[int, str, str]:
    """Run the step as the command line does. Gives its exit code and what it printed."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(["travel", *arguments])
    return code, out.getvalue(), err.getvalue()


@pytest.fixture(scope="session")
def routed(tmp_path_factory: pytest.TempPathFactory) -> Routed:
    releases = tmp_path_factory.mktemp("routed")
    code, out, err = run("--made-up", "--out", str(releases))
    return Routed(releases / RELEASE_ID, out, err, code)
