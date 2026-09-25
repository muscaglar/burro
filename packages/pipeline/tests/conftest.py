"""The generated tests draw a fixed sample in `make ci`, and run in full with `-m full`.

The whole suite has to stay within the limit `AGENTS.md` states. A test that
tries every area of the city has two forms: the sample, which always runs, and the whole, which is
marked `full` and is skipped unless it is asked for: `make test ARGS="-m full"`.

What many tests read and none changes is made once in each process: `once.py` says how.
"""

from collections.abc import Iterator

import pytest

from . import once

FULL = "full"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", f"{FULL}: a generated test in full, which make ci samples")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if FULL in str(config.getoption("-m", default="")):
        return
    skip = pytest.mark.skip(reason='the whole of a generated test: run it with ARGS="-m full"')
    for item in items:
        if FULL in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session", autouse=True)
def what_is_made_once(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Where a thing is made once for the run, and the check that no test wrote to one."""
    once.FOLDERS.append(tmp_path_factory)
    try:
        yield
    finally:
        once.FOLDERS.clear()
    written_to = once.changed()
    assert not written_to, f"a test wrote to what is made once for every test: {written_to}"
