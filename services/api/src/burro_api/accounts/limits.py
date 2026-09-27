"""How many times one client may ask, counted in memory under a keyed hash.

The address of a client is what the website says it is, in one header. The website is
believed because it has shown its secret, and nothing else that names an address is
read: not what a proxy adds on the way, and not the other end of the connection, which
is the website's own machine.

An address is counted under a hash made with a key. It is held in the memory of the
process and written nowhere: not to the file of accounts, and not to a line of the log.
The key is what keeps a guess at an address from being confirmed by whoever could read
that memory.

These are the limits on signing in. They are no limit on a search, which knows nobody
(ADR 0032).
"""

import hashlib
import hmac
import ipaddress
from collections import deque
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from threading import Lock

# What every address is counted as that cannot be read, or was not given. So what
# cannot be read is limited the more, and never the less. It is for development, where
# no host stands before the website: anywhere else the service refuses a request that
# does not say whose it is.
UNKNOWN = "unknown"
# A client that is given addresses of the newer kind is given a network of them.
NETWORK_BITS = 64
SHORTEST_KEY = 32
# How many clients are held at once. One that is let go of is counted afresh.
KEEP = 100_000


class NotOne(Exception):
    """More than one address was given. The website gives one, so it was not the website's."""


def _regular(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str:
    if isinstance(address, ipaddress.IPv4Address):
        return str(address)
    if address.ipv4_mapped is not None:
        # An address of the older kind, written as one of the newer.
        return str(address.ipv4_mapped)
    # The number alone, so that what names a link of the machine is left behind.
    return str(ipaddress.IPv6Network((int(address), NETWORK_BITS), strict=False))


def client_of(given: Sequence[str]) -> str:
    """The client, from what the header of its address held: one address, made regular.

    `given` is every value the header was sent with. The website takes out what a
    client sent under that name and puts in one of its own, so two values, or a list
    in one, say that what arrived is not what the website alone wrote.
    """
    if len(given) > 1 or any("," in value for value in given):
        raise NotOne
    try:
        return _regular(ipaddress.ip_address(given[0].strip())) if given else UNKNOWN
    except ValueError:
        return UNKNOWN


class Limiter:
    """Lets in so many calls from one client within a time, and no more.

    The time runs from each call, so there is no moment at which every count starts
    again. A call that is turned away is not counted. The clock is handed to it, so
    that a test moves time and waits for nothing.
    """

    def __init__(
        self,
        key: bytes,
        most: int,
        within: timedelta,
        now: Callable[[], datetime],
        keep: int = KEEP,
    ) -> None:
        if len(key) < SHORTEST_KEY:
            # Never the key. One that is too short is still a key.
            raise ValueError("the key is too short")
        # The key is let go of here. What is held is what hashes under it, which shows
        # the key in no `repr` and hands it to nobody.
        self._keyed = hmac.new(key, digestmod=hashlib.sha256)
        self._most = most
        self._within = within
        self._now = now
        self._keep = keep
        self._lock = Lock()
        # When each client that is held was let in, the oldest first. A client is held
        # by the hash of its address under the key, and by nothing else.
        self._let_in: dict[bytes, deque[datetime]] = {}

    def __repr__(self) -> str:
        return "Limiter()"

    def _name(self, client: str) -> bytes:
        named = self._keyed.copy()
        named.update(client.encode())
        return named.digest()

    def _make_room(self, since: datetime) -> None:
        """Let go of every client whose calls are all too old, and then of the oldest."""
        old = [name for name, times in self._let_in.items() if not times or times[-1] <= since]
        for name in old:
            del self._let_in[name]
        while len(self._let_in) >= self._keep:
            # A dict keeps the order things were put in.
            del self._let_in[next(iter(self._let_in))]

    def lets_in(self, client: str) -> bool:
        """Whether a call may be made now. One that may is counted, and one that may not is not."""
        name = self._name(client)
        now = self._now()
        since = now - self._within
        with self._lock:
            times = self._let_in.get(name)
            if times is None:
                if len(self._let_in) >= self._keep:
                    self._make_room(since)
                times = self._let_in.setdefault(name, deque())
            # A clock that is put back leaves what was counted as it was.
            while times and times[0] <= since:
                times.popleft()
            if len(times) >= self._most:
                return False
            times.append(now)
            return True

    def held(self) -> int:
        """How many clients are held."""
        with self._lock:
            return len(self._let_in)

    def names(self) -> frozenset[bytes]:
        """What each client is held by. A test reads it, and the service never does."""
        with self._lock:
            return frozenset(self._let_in)
