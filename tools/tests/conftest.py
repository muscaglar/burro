"""What the tests of the tools share: logging that is left as it was found.

The service sets logging up for the whole process when it starts, and so does whatever
starts it as the service does. A test that does must not leave the next test writing to a
stream that is gone, or hearing less than it says it hears.
"""

import logging
from collections.abc import Iterator

import pytest


def _loggers() -> list[logging.Logger]:
    named = logging.Logger.manager.loggerDict.values()
    return [each for each in named if isinstance(each, logging.Logger)]


@pytest.fixture
def logging_as_it_was() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    levels = {each.name: each.level for each in _loggers()}
    try:
        yield
    finally:
        root.handlers[:] = handlers
        root.setLevel(level)
        for each in _loggers():
            # One made since then goes back to what a new one has: no level of its own.
            each.setLevel(levels.get(each.name, logging.NOTSET))
