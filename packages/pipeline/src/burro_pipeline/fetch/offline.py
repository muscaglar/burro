"""Refuse every socket, for the steps of a build that must not reach a network.

Fetch is the only step that may. Every other step reads files that were
fetched before it started, so inside `sockets_refused()` making a socket of
any kind raises, and so does looking up a name. It is what the test run does
to every test, done by the code itself where it matters.
"""

import socket
from collections.abc import Generator
from contextlib import contextmanager
from typing import NoReturn

LOOKUPS = ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getnameinfo")


class NetworkRefused(RuntimeError):
    """A step that must not reach a network tried to."""


def _refuse(*_: object, **__: object) -> NoReturn:
    raise NetworkRefused("this step may not reach a network: only fetch does")


class _Refused(socket.socket):
    # Refused in `__new__`, so that nothing of a socket is made before the refusal.
    def __new__(
        cls,
        family: socket.AddressFamily | int = -1,
        type: socket.SocketKind | int = -1,
        proto: int = -1,
        fileno: int | None = None,
    ) -> "_Refused":
        _refuse()


@contextmanager
def sockets_refused() -> Generator[None]:
    """Inside, no socket can be made and no name looked up. After, all is as it was."""
    before = {name: getattr(socket, name) for name in ("socket", *LOOKUPS)}
    socket.socket = _Refused
    for name in LOOKUPS:
        setattr(socket, name, _refuse)
    try:
        yield
    finally:
        for name, was in before.items():
            setattr(socket, name, was)
