"""Every test leaves logging as it found it, and a generated test is sampled in `make ci`.

One event loop serves the requests of every test.

The service sets logging up for the whole process when it starts. A test that
starts it must not leave the next test writing JSON to a stream that is gone.

The whole suite has to stay within the limit `AGENTS.md` states, and a
generated test that puts every sign of doubt beside every thing in every order
does not fit in that.
So each has two forms: the sample, which always runs and is the same
sentences every time, and the whole, which is marked `full` and is skipped
unless it is asked for: `make test ARGS="-m full"`.
"""

from collections.abc import Iterator

import pytest
from anyio.from_thread import start_blocking_portal
from burro_api.providers.terms import TERMS

from .support import LOOP, logging_put_back

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
def one_loop() -> Iterator[None]:
    """One event loop for every request of every test, started once and stopped at the end.

    A test client that is not entered starts a loop for each request it makes, and the
    tests make some two thousand. A client that a test enters still starts its own.
    """
    with start_blocking_portal() as portal:
        LOOP.append(portal)
        try:
            yield
        finally:
            LOOP.clear()


@pytest.fixture(autouse=True)
def nothing_chosen(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test finds a provider, a key or accepted terms in the shell it runs in.

    The service reads them from the environment when it starts. A test that
    wants one set says so itself.
    """
    chosen_by = ("BURRO_MODEL_PROVIDER", "BURRO_MODEL_TERMS_ACCEPTED", "BURRO_MODEL_ID")
    for name in (*chosen_by, *(terms.key_variable for terms in TERMS.values())):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def logging_as_it_was() -> Iterator[None]:
    with logging_put_back():
        yield
