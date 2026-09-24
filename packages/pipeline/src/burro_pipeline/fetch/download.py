"""One download: the only code in a build that asks a publisher for anything.

It sends one GET over https and keeps the bytes as they arrive. It follows a
redirect only on the same host, or to a host the list of sources names for
that file. It refuses a file over a stated size, a connection to an address
that is not public, and a publisher that is too slow. It refuses an address
that holds a letter outside ASCII, which a request cannot be written with. It
reads no proxy, no cookie and no login from the machine it runs on.

A file may also be asked for a piece at a time, by `InPieces`: each piece is
one GET that names the bytes it wants, and is held to the same rules. A piece
is kept only if the publisher says it is the bytes that were asked for, of a
file of the size the first piece gave. A publisher that answers with the whole
file is not read. Where the publisher marks the version of the file, each
later piece is asked of that version, so that the pieces are of one file.

A refusal is a reason from a fixed list, with at most a status or a host name
beside it. It never repeats an address, a header or anything the network said,
because a build's log is public.
"""

import hashlib
import http.client
import ipaddress
import re
import secrets
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass
from email.message import Message
from enum import StrEnum
from pathlib import Path
from urllib.parse import SplitResult, unquote, urljoin, urlsplit

PIECE = 1024 * 1024
HOST = re.compile(
    r"(?=.{1,253}$)[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*"
)
NOT_IN_AN_ADDRESS = re.compile(r"[\x00-\x20\x7f-\x9f\\]")
CONTACT = re.compile(r"[!-~]{3,200}")
REDIRECTS = frozenset({301, 302, 303, 307, 308})
# What a publisher answers a piece with, and what it answers when the file is no longer the
# version that was asked of.
A_PIECE, NOT_THAT_VERSION = 206, 412
# What a publisher says a piece is: its first and its last byte, and the size of the whole.
SAID_OF_A_PIECE = re.compile(r"bytes (\d{1,18})-(\d{1,18})/(\d{1,18})")
# A mark a publisher gives a version of a file, where it is one that tells two versions apart.
A_MARK = re.compile(r'"[\x21\x23-\x7e]{1,200}"')
PORTS = {"https": 443, "http": 80}
# Names that stand for the machine itself or its own network. Refused without a lookup.
LOCAL_NAMES = ("localhost", ".localhost", ".local", ".internal", ".home.arpa")


class Reason(StrEnum):
    NOT_HTTPS = "the address is not https"
    BAD_ADDRESS = "the address could not be read, or holds a login"
    NOT_ASCII = "the address holds a letter outside ASCII"
    NOT_PUBLIC = "the address is not a public one"
    NO_CONNECTION = "the publisher could not be reached"
    NOT_SECURE = "the secure connection failed"
    TIMED_OUT = "the publisher was too slow"
    BAD_ANSWER = "the answer could not be read"
    STATUS = "status"
    REDIRECT_ELSEWHERE = "redirect to another host"
    TOO_MANY_REDIRECTS = "too many redirects"
    TOO_LARGE = "the file is over the size stated for it"
    CUT_SHORT = "the file stopped before its end"
    NOT_WRITTEN = "the file could not be written"
    NOT_IN_PIECES = "the publisher did not give the piece that was asked for"
    CHANGED = "the file changed while pieces of it were taken"
    NOT_LAID_OUT = "the file is not laid out so that part of it can be taken"


class DownloadRefused(Exception):
    """A download that was not made, or not kept. Safe to print."""

    def __init__(self, reason: Reason, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail
        joined = " " if reason is Reason.STATUS else ": "
        super().__init__(f"{reason.value}{joined}{detail}" if detail else reason.value)


@dataclass(frozen=True)
class Limits:
    max_bytes: int
    connect_seconds: float = 30
    read_seconds: float = 120
    total_seconds: float = 3600
    max_redirects: int = 5


@dataclass(frozen=True)
class Downloaded:
    sha256: str
    bytes: int
    final_url: str
    file_name: str
    content_type: str


def user_agent(contact: str) -> str:
    """What fetch calls itself. Publishers ask for a name and a way to reach a person."""
    if not CONTACT.fullmatch(contact) or not ("@" in contact or contact.startswith("https://")):
        raise ValueError(
            "BURRO_FETCH_CONTACT must be an email address or an https page, with no spaces"
        )
    return f"Burro-fetch/1 ({contact})"


@dataclass(frozen=True)
class _Address:
    scheme: str
    host: str
    port: int
    target: str
    whole: str

    @property
    def origin(self) -> tuple[str, str, int]:
        return self.scheme, self.host, self.port


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _read(address: str) -> _Address:
    """Take an address apart, and refuse one that is not a plain web address."""
    if NOT_IN_AN_ADDRESS.search(address):
        raise DownloadRefused(Reason.BAD_ADDRESS)
    # A request is written in ASCII. How a letter outside it is to be sent is the
    # publisher's to say, so it is not guessed: the list gives the address as it is sent.
    if not address.isascii():
        raise DownloadRefused(Reason.NOT_ASCII)
    try:
        parts: SplitResult = urlsplit(address)
        port = parts.port
    except ValueError:
        raise DownloadRefused(Reason.BAD_ADDRESS) from None
    scheme = parts.scheme.lower()
    if scheme not in PORTS:
        raise DownloadRefused(Reason.NOT_HTTPS)
    host = (parts.hostname or "").lower().rstrip(".")
    if not host or parts.username is not None or parts.password is not None:
        raise DownloadRefused(Reason.BAD_ADDRESS)
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if not HOST.fullmatch(host):
            raise DownloadRefused(Reason.BAD_ADDRESS) from None
    target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
    return _Address(scheme, host, port or PORTS[scheme], target, address.split("#", 1)[0])


def _allowed(address: _Address, loopback_for_tests: bool) -> None:
    """Refuse plain http, and refuse an address that names this machine or a private network."""
    loopback = _is_loopback(address.host)
    if address.scheme != "https" and not (loopback_for_tests and loopback):
        raise DownloadRefused(Reason.NOT_HTTPS)
    if loopback and loopback_for_tests:
        return
    if address.host == LOCAL_NAMES[0] or address.host.endswith(LOCAL_NAMES[1:]):
        raise DownloadRefused(Reason.NOT_PUBLIC)
    try:
        if not ipaddress.ip_address(address.host).is_global:
            raise DownloadRefused(Reason.NOT_PUBLIC)
    except ValueError:
        pass


def may_be_asked(address: str) -> None:
    """Refuse an address that a download would refuse before it asked anything.

    Worked out from text alone: no name is looked up and no socket is opened.
    """
    _allowed(_read(address), loopback_for_tests=False)


def next_address(current: str, location: str, may_redirect_to: tuple[str, ...] = ()) -> str:
    """Where a redirect leads, if it may be followed. Worked out from text alone.

    The same scheme, host and port may always be followed. Another host may be
    followed only if the list of sources names it, and only over https.
    """
    here = _read(current)
    try:
        there = _read(urljoin(current, location))
    except DownloadRefused as refused:
        if refused.reason is Reason.NOT_ASCII:
            raise
        raise DownloadRefused(Reason.REDIRECT_ELSEWHERE) from None
    if there.origin == here.origin:
        return there.whole
    named = there.host in {host.lower() for host in may_redirect_to}
    if named and (there.scheme == "https" or (here.scheme == "http" and _is_loopback(there.host))):
        return there.whole
    raise DownloadRefused(Reason.REDIRECT_ELSEWHERE, there.host)


class _Connection(http.client.HTTPConnection):
    """A connection that checks who answered before it says anything.

    A name can be pointed at a private address after the list was reviewed. So
    the address of the machine that answered is checked, and only then is the
    secure connection made and the request sent.
    """

    def __init__(self, address: _Address, seconds: float, check: Callable[[str], None]) -> None:
        super().__init__(address.host, address.port, timeout=seconds, blocksize=PIECE)
        self._secure = address.scheme == "https"
        self._check = check

    def connect(self) -> None:
        super().connect()
        peer = self.sock.getpeername()[0]
        self._check(str(peer))
        if self._secure:
            context = ssl.create_default_context()
            self.sock = context.wrap_socket(self.sock, server_hostname=self.host)


def _file_name(headers: Message, address: _Address) -> str:
    """The publisher's own name for the file, from the answer, or else from the address."""
    named = headers.get_filename()
    if not named:
        named = unquote(address.target.split("?", 1)[0].rsplit("/", 1)[-1])
    named = re.split(r"[/\\]", named)[-1]
    named = "".join(sign for sign in named if sign.isprintable()).strip()
    return named[:200] or "file"


def _ask(
    address: _Address,
    agent: str,
    limits: Limits,
    loopback_for_tests: bool,
    more: tuple[tuple[str, str], ...] = (),
) -> tuple[_Connection, http.client.HTTPResponse]:
    def check(peer: str) -> None:
        found = ipaddress.ip_address(peer.split("%", 1)[0])
        if not (found.is_global or (loopback_for_tests and found.is_loopback)):
            raise DownloadRefused(Reason.NOT_PUBLIC)

    connection = _Connection(address, limits.connect_seconds, check)
    try:
        connection.connect()
        connection.sock.settimeout(limits.read_seconds)
        connection.putrequest("GET", address.target, skip_accept_encoding=True)
        connection.putheader("Accept-Encoding", "identity")
        connection.putheader("Accept", "*/*")
        connection.putheader("User-Agent", agent)
        connection.putheader("Connection", "close")
        for name, value in more:
            connection.putheader(name, value)
        connection.endheaders()
        return connection, connection.getresponse()
    except BaseException:
        connection.close()
        raise


def download(
    address: str,
    to: Path,
    limits: Limits,
    *,
    agent: str,
    may_redirect_to: tuple[str, ...] = (),
    loopback_for_tests: bool = False,
    clock: Callable[[], float] = time.monotonic,
) -> Downloaded:
    """Fetch one file to `to`. On any refusal nothing is left on disk."""
    started = clock()
    current = address
    part = to.with_name(f".part-{secrets.token_hex(8)}")
    try:
        for _ in range(limits.max_redirects + 1):
            here = _read(current)
            _allowed(here, loopback_for_tests)
            connection, answer = _ask(here, agent, limits, loopback_for_tests)
            try:
                if answer.status in REDIRECTS:
                    location = answer.getheader("Location")
                    if not location:
                        raise DownloadRefused(Reason.BAD_ANSWER)
                    current = next_address(current, location, may_redirect_to)
                    continue
                if answer.status != 200:
                    raise DownloadRefused(Reason.STATUS, str(answer.status))
                sha256, size = _keep(answer, part, limits, started, clock)
                part.replace(to)
                return Downloaded(
                    sha256=sha256,
                    bytes=size,
                    final_url=here.whole,
                    file_name=_file_name(answer.headers, here),
                    content_type=answer.headers.get_content_type(),
                )
            finally:
                connection.close()
        raise DownloadRefused(Reason.TOO_MANY_REDIRECTS)
    except DownloadRefused:
        raise
    except TimeoutError:
        raise DownloadRefused(Reason.TIMED_OUT) from None
    except ssl.SSLError:
        raise DownloadRefused(Reason.NOT_SECURE) from None
    except http.client.IncompleteRead:
        raise DownloadRefused(Reason.CUT_SHORT) from None
    except http.client.HTTPException:
        raise DownloadRefused(Reason.BAD_ANSWER) from None
    except OSError:
        raise DownloadRefused(Reason.NO_CONNECTION) from None
    finally:
        part.unlink(missing_ok=True)


def _keep(
    answer: http.client.HTTPResponse,
    part: Path,
    limits: Limits,
    started: float,
    clock: Callable[[], float],
) -> tuple[str, int]:
    """Write the body to disk as it arrives, hashing it, and stop at either limit."""
    stated = answer.getheader("Content-Length")
    if stated is not None and (not stated.isdigit() or int(stated) > limits.max_bytes):
        raise DownloadRefused(Reason.TOO_LARGE if stated.isdigit() else Reason.BAD_ANSWER)
    digest, size = hashlib.sha256(), 0
    try:
        file = part.open("xb")
    except OSError:
        raise DownloadRefused(Reason.NOT_WRITTEN) from None
    with file:
        # `read1` gives what has arrived and does not wait for a full piece, so a
        # publisher that sends a little at a time still meets the time limit.
        while piece := answer.read1(PIECE):
            size += len(piece)
            if size > limits.max_bytes:
                raise DownloadRefused(Reason.TOO_LARGE)
            if clock() - started > limits.total_seconds:
                raise DownloadRefused(Reason.TIMED_OUT)
            digest.update(piece)
            try:
                file.write(piece)
            except OSError:
                raise DownloadRefused(Reason.NOT_WRITTEN) from None
    if stated is not None and size != int(stated):
        raise DownloadRefused(Reason.CUT_SHORT)
    return digest.hexdigest(), size


class InPieces:
    """One file, asked for a piece at a time. What is said of `download` holds of each piece.

    The size of the whole file is what the publisher says of the first piece
    that arrives, and every later piece must say the same. The time limit and
    the size limit are of all the pieces together.
    """

    def __init__(
        self,
        address: str,
        limits: Limits,
        *,
        agent: str,
        may_redirect_to: tuple[str, ...] = (),
        loopback_for_tests: bool = False,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._address, self._limits, self._agent = address, limits, agent
        self._may_redirect_to, self._loopback = may_redirect_to, loopback_for_tests
        self._clock, self._started = clock, clock()
        self._whole: int | None = None
        self._ended_at: _Address | None = None
        self._name, self._mark = "", ""
        # How many bytes have arrived, of every piece.
        self.arrived = 0

    @property
    def of_bytes(self) -> int:
        """The size of the whole file, as the publisher gave it with the first piece."""
        if self._whole is None:
            raise DownloadRefused(Reason.BAD_ANSWER)
        return self._whole

    @property
    def final_url(self) -> str:
        """The address the pieces came from in the end."""
        if self._ended_at is None:
            raise DownloadRefused(Reason.BAD_ANSWER)
        return self._ended_at.whole

    @property
    def file_name(self) -> str:
        return self._name or "file"

    def end(self, count: int) -> bytes:
        """The last so many bytes of the file."""
        held = bytearray()
        self._piece(f"bytes=-{count}", None, count, held.extend)
        return bytes(held)

    def piece(self, first: int, count: int, keep: Callable[[bytes], object]) -> None:
        """So many bytes of the file from a first byte, handed to `keep` as they arrive."""
        if first < 0 or count < 1:
            raise DownloadRefused(Reason.NOT_IN_PIECES)
        self._piece(f"bytes={first}-{first + count - 1}", first, count, keep)

    def _piece(
        self, asked: str, first: int | None, count: int, keep: Callable[[bytes], object]
    ) -> None:
        try:
            self._one(asked, first, count, keep)
        except DownloadRefused:
            raise
        except TimeoutError:
            raise DownloadRefused(Reason.TIMED_OUT) from None
        except ssl.SSLError:
            raise DownloadRefused(Reason.NOT_SECURE) from None
        except http.client.IncompleteRead:
            raise DownloadRefused(Reason.CUT_SHORT) from None
        except http.client.HTTPException:
            raise DownloadRefused(Reason.BAD_ANSWER) from None
        except OSError:
            raise DownloadRefused(Reason.NO_CONNECTION) from None

    def _one(
        self, asked: str, first: int | None, count: int, keep: Callable[[bytes], object]
    ) -> None:
        if self.arrived + count > self._limits.max_bytes:
            raise DownloadRefused(Reason.TOO_LARGE)
        more = [("Range", asked)]
        if self._mark:
            more.append(("If-Match", self._mark))
        current = self._address
        for _ in range(self._limits.max_redirects + 1):
            here = _read(current)
            _allowed(here, self._loopback)
            connection, answer = _ask(here, self._agent, self._limits, self._loopback, tuple(more))
            try:
                if answer.status in REDIRECTS:
                    location = answer.getheader("Location")
                    if not location:
                        raise DownloadRefused(Reason.BAD_ANSWER)
                    current = next_address(current, location, self._may_redirect_to)
                    continue
                self._held(answer, here, first, count)
                self._kept(answer, count, keep)
                return
            finally:
                connection.close()
        raise DownloadRefused(Reason.TOO_MANY_REDIRECTS)

    def _held(
        self, answer: http.client.HTTPResponse, here: _Address, first: int | None, count: int
    ) -> None:
        """Refuse an answer that is not the piece asked for, of the file the first piece was of."""
        if answer.status == NOT_THAT_VERSION and self._mark:
            raise DownloadRefused(Reason.CHANGED)
        if answer.status == 200:
            # The publisher does not give a file in pieces. The whole file is not read.
            raise DownloadRefused(Reason.NOT_IN_PIECES)
        if answer.status != A_PIECE:
            raise DownloadRefused(Reason.STATUS, str(answer.status))
        said = SAID_OF_A_PIECE.fullmatch((answer.getheader("Content-Range") or "").strip())
        if said is None:
            raise DownloadRefused(Reason.NOT_IN_PIECES)
        start, last, whole = (int(part) for part in said.groups())
        if first is None:
            first = whole - count
        if (start, last) != (first, first + count - 1) or not 0 <= start <= last < whole:
            raise DownloadRefused(Reason.NOT_IN_PIECES)
        length = answer.getheader("Content-Length")
        if length is not None and length != str(count):
            raise DownloadRefused(Reason.NOT_IN_PIECES)
        if self._whole is None:
            self._whole, self._ended_at = whole, here
            self._name = _file_name(answer.headers, here)
            mark = (answer.getheader("ETag") or "").strip()
            self._mark = mark if A_MARK.fullmatch(mark) else ""
        elif whole != self._whole or self._ended_at is None or here.whole != self._ended_at.whole:
            raise DownloadRefused(Reason.CHANGED)

    def _kept(
        self, answer: http.client.HTTPResponse, count: int, keep: Callable[[bytes], object]
    ) -> None:
        """Hand the bytes of a piece over as they arrive, and stop at either limit."""
        size = 0
        while piece := answer.read1(PIECE):
            size += len(piece)
            if size > count:
                raise DownloadRefused(Reason.NOT_IN_PIECES)
            if self._clock() - self._started > self._limits.total_seconds:
                raise DownloadRefused(Reason.TIMED_OUT)
            try:
                keep(piece)
            except OSError:
                raise DownloadRefused(Reason.NOT_WRITTEN) from None
        if size != count:
            raise DownloadRefused(Reason.CUT_SHORT)
        self.arrived += size
