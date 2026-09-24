"""How an adapter reaches its provider: one HTTPS POST, made with the standard library.

`over_https` is the one function that sends. It answers with a status and a
body, or raises one of the three failures. It follows no redirect, reads no
more than `MAX_BYTES`, gives the whole call one deadline, checks the
provider's certificate, and tries once. It writes no log line and keeps
nothing of what it sent or received.

`Adapter` is what the four providers share. A provider's module says what to
send and how to read the answer, and no more.

Every failure is `ModelTimeout`, `ModelCapped` or `ModelError`, with no
message, no cause and no context. What goes wrong underneath can hold the
request, the key or the answer: a JSON error holds the whole document, and a
header error holds the header. So the work is done where nothing is raised,
and the failure is raised afterwards from a frame that holds none of it.
"""

import http.client
import io
import json
import re
import socket
import ssl
import time
from collections.abc import Buffer, Callable, Mapping
from concurrent.futures import Future
from dataclasses import dataclass, field
from functools import cache
from threading import Lock, Thread
from typing import ClassVar, cast

from burro_api.providers.interface import (
    ModelCapped,
    ModelError,
    ModelFailure,
    ModelReply,
    ModelTimeout,
)

PORT = 443
OK = 200
# The most that is read of an answer. A reading of one sentence is a few
# thousand characters, so an answer beyond this is not an answer.
MAX_BYTES = 256 * 1024
# A status that means the same whoever sends it (RFC 9110).
TIMED_OUT = frozenset({408, 504})
CAPPED = frozenset({402, 429})
# An answer that will not mend itself: a request the provider will not take,
# a key that is no longer one, a model that is gone. The next person's
# sentence would be sent and refused in the same way.
STUCK = frozenset({400, 401, 403, 404})
# After this many such answers in a row the provider is left alone for a
# while, and the rules read in its place. One call is then let through, to
# see whether it has mended. Nothing is ever sent twice, so this is no retry.
PATIENCE = 3
REST_S = 300.0

# A model's name goes into an address or a body. Lower-case letters, digits,
# dots and hyphens: nothing that could begin a path, a query or a header.
MODEL = re.compile(r"[a-z0-9][a-z0-9.-]{0,63}")
# A name that ends so is moved to a new model by its provider with no notice,
# and what was measured on the old one no longer holds.
MOVING = "-latest"

_KEY = re.compile(r"[\x21-\x7e]{1,512}")
_HOST = re.compile(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?")
# A path is made of parts that are names: none is empty, and none is dots alone.
_PATH = re.compile(r"(?:/(?!\.{1,2}(?:/|$))[A-Za-z0-9._:-]{1,128}){1,8}")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9-]{0,63}")
_VALUE = re.compile(r"[\x21-\x7e](?:[\x20-\x7e]{0,1022}[\x21-\x7e])?")
# The headers this module writes itself, and those that say how a body is
# framed or where a request goes on to. An adapter may write none of them.
_OURS = frozenset(
    {
        "host",
        "content-type",
        "content-length",
        "accept",
        "accept-encoding",
        "connection",
        "user-agent",
        "transfer-encoding",
        "te",
        "trailer",
        "upgrade",
        "expect",
        "keep-alive",
        "proxy-authorization",
        "proxy-connection",
    }
)
_REFERENCE = re.compile(r"#/(\$defs|definitions)/([^/]+)")


class Unfit(Exception):
    """What was to be sent, or what came back, is not of the shape it must be.

    It carries no message, and it never leaves this package: it becomes `ModelError`.
    """


class Key:
    """A provider's key. It shows in no `repr`, no `str` and no copy.

    It is checked when it is made, so that no key can ever begin a second
    header. The one way out is `for_header`, which the sender calls as it
    writes the request.
    """

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        if _KEY.fullmatch(value) is None:
            # Never the value. A key that is malformed is still a key.
            raise ValueError("not a key")
        self._value = value

    def __repr__(self) -> str:
        return "Key(hidden)"

    def __reduce__(self) -> str:
        raise TypeError("a key is never copied")

    def __getstate__(self) -> object:
        # What a tool that writes objects out asks for when it does not pickle.
        raise TypeError("a key is never copied")

    def for_header(self, scheme: str = "") -> str:
        return f"{scheme}{self._value}"


@dataclass(frozen=True)
class Request:
    """One POST. The host and the path are constants of an adapter, never a setting."""

    host: str
    path: str
    # The name of the header that carries the key, and what stands before it.
    key_header: str
    key: Key
    key_scheme: str = ""
    headers: Mapping[str, str] = field(default_factory=dict[str, str])
    # What the person typed is in here.
    body: bytes = field(default=b"", repr=False)
    # The statuses whose body is read. The body of any other is left unread,
    # because the body of an error can repeat the request.
    wants: frozenset[int] = frozenset({OK})


@dataclass(frozen=True)
class Response:
    status: int
    # A model's answer can repeat what the person typed.
    body: bytes = field(default=b"", repr=False)


class Deadline:
    """The one clock of a call. Every step is given what is left of it."""

    def __init__(self, seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._at = clock() + seconds

    def left(self) -> float:
        left = self._at - self._clock()
        # Written so that a time that is no number has run out too.
        if not left > 0:
            raise TimeoutError
        return left


Send = Callable[[Request, float], Response]
Connect = Callable[[str, Deadline], socket.socket]
Outcome = ModelReply | type[ModelFailure]


@cache
def verifying() -> ssl.SSLContext:
    """The provider's certificate is checked against the host's own, and its name against the host.

    Made by hand. The standard library's ready-made context also reads
    `SSLKEYLOGFILE`, and then writes the secrets of every call to a file:
    whoever held that file and a copy of the traffic could read the key and
    the words. A context of this kind asks for a certificate and checks the
    name on it without being told to.

    `SSL_CERT_FILE` and `SSL_CERT_DIR` are still honoured, because that is
    how whoever runs a host names its certificates, and whoever can set them
    can read the key as well. Whether to go on honouring them is the
    founder's to decide: `docs/design/models.md`.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    # As the ready-made context is set.
    context.verify_flags |= ssl.VERIFY_X509_STRICT | ssl.VERIFY_X509_PARTIAL_CHAIN
    context.load_default_certs()
    return context


_Where = tuple[str, int] | tuple[str, int, int, int] | tuple[int, bytes]
_Found = tuple[socket.AddressFamily, socket.SocketKind, int, str, _Where]


def _addresses(host: str, deadline: Deadline) -> list[_Found]:
    # Looking a name up is the one step the standard library sets no limit
    # on, so it is done on a thread of its own, which is left if it is late.
    looking = Future[list[_Found]]()

    def look() -> None:
        try:
            looking.set_result(socket.getaddrinfo(host, PORT, type=socket.SOCK_STREAM))
        except BaseException as error:
            looking.set_exception(error)

    Thread(target=look, daemon=True).start()
    return looking.result(timeout=deadline.left())


def tls(host: str, deadline: Deadline) -> socket.socket:
    """A connection to `host` on port 443, with the certificate checked. There is no other kind."""
    found = _addresses(host, deadline)
    for tried, (family, kind, proto, _, where) in enumerate(found):
        plain = socket.socket(family, kind, proto)
        try:
            # Each address is given its share of what is left, so that one
            # which does not answer leaves time for the next.
            plain.settimeout(deadline.left() / (len(found) - tried))
            plain.connect(where)
            plain.settimeout(deadline.left())
            return verifying().wrap_socket(plain, server_hostname=host)
        except OSError:
            plain.close()
    # A timeout if the time is spent, and an error if no address would answer.
    deadline.left()
    raise OSError


class _Reads(io.RawIOBase):
    """Reads from a socket, and gives each read only the time that is left.

    A timeout on each read alone is no limit: a provider under load may send
    an empty line every few seconds for ten minutes, and each is a read that
    worked.
    """

    def __init__(self, link: socket.socket, deadline: Deadline) -> None:
        super().__init__()
        self._link = link
        self._deadline = deadline

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Buffer, /) -> int:
        self._link.settimeout(self._deadline.left())
        return self._link.recv_into(buffer)


class _Link:
    """All that `HTTPResponse` asks of a socket: something to read from."""

    def __init__(self, link: socket.socket, deadline: Deadline) -> None:
        self._link = link
        self._deadline = deadline

    def makefile(self, mode: str = "rb", *_: object, **__: object) -> io.BufferedReader:
        return io.BufferedReader(_Reads(self._link, self._deadline))


def _written(request: Request) -> bytes:
    """The request as it goes on the wire. The key is in one header and nowhere else."""
    if _HOST.fullmatch(request.host) is None or _PATH.fullmatch(request.path) is None:
        raise Unfit
    sent = dict(request.headers)
    named = [request.key_header, *sent]
    if len({name.lower() for name in named}) != len(named) or _OURS & {n.lower() for n in named}:
        raise Unfit
    carried = request.key.for_header(request.key_scheme)
    if not all(_NAME.fullmatch(name) for name in named):
        raise Unfit
    if not all(_VALUE.fullmatch(value) for value in (*sent.values(), carried)):
        raise Unfit
    lines = [
        f"POST {request.path} HTTP/1.1",
        f"Host: {request.host}",
        "Content-Type: application/json",
        f"Content-Length: {len(request.body)}",
        "Accept: application/json",
        # So that what is read is what was sent, and its size is its size.
        "Accept-Encoding: identity",
        "Connection: close",
        "User-Agent: burro",
        *(f"{name}: {value}" for name, value in sent.items()),
        f"{request.key_header}: {carried}",
    ]
    return "\r\n".join(lines).encode("ascii") + b"\r\n\r\n" + request.body


def _length(said: str | None) -> int | None:
    """How long the body says it is, if it says. A length over the limit is refused unread."""
    if said is None:
        return None
    if not (said.isascii() and said.isdigit()) or len(said) > 9 or int(said) > MAX_BYTES:
        raise Unfit
    return int(said)


def _answered(
    link: socket.socket, wire: bytes, wants: frozenset[int], deadline: Deadline
) -> Response:
    link.settimeout(deadline.left())
    link.sendall(wire)
    answer = http.client.HTTPResponse(cast(socket.socket, _Link(link, deadline)), method="POST")
    try:
        answer.begin()
        if answer.status not in wants:
            # A redirect is among them. Where it points is never read.
            return Response(answer.status)
        stated = _length(answer.getheader("Content-Length"))
        body = answer.read(MAX_BYTES + 1)
        # Too long, or cut off before the length it gave.
        if len(body) > MAX_BYTES or (stated is not None and len(body) != stated):
            raise Unfit
        return Response(answer.status, body)
    finally:
        answer.close()


def _exchanged(
    request: Request, timeout_s: float, connect: Connect
) -> Response | type[ModelFailure]:
    """The answer, or which failure it was. It never raises for anything that went wrong."""
    try:
        deadline = Deadline(timeout_s)
        deadline.left()
        # Made before anything is connected to, so that a request that is
        # not fit to send reaches nobody.
        wire = _written(request)
        link = connect(request.host, deadline)
        try:
            return _answered(link, wire, request.wants, deadline)
        finally:
            link.close()
    except TimeoutError:
        return ModelTimeout
    except Exception:
        return ModelError


def over_https(request: Request, timeout_s: float, *, connect: Connect = tls) -> Response:
    """Send `request` once and answer with the status and the body.

    `timeout_s` is for the whole call: the name, the connection, the
    handshake, the sending and every read. A redirect is answered as its
    status and never followed, because it could carry the key to another
    host. A body longer than `MAX_BYTES` is refused. There is no retry.
    """
    outcome = _exchanged(request, timeout_s, connect)
    # Let go of, so that a failure leaves from a frame that holds no request.
    del request
    if isinstance(outcome, Response):
        return outcome
    raise outcome()


def refused(status: int) -> type[ModelFailure] | None:
    """Which failure a status is, or `None` for the one status that is an answer.

    Read the same way for every provider. A redirect, and a success that is
    not 200, are errors like any other.
    """
    if status == OK:
        return None
    if status in TIMED_OUT:
        return ModelTimeout
    if status in CAPPED:
        return ModelCapped
    return ModelError


def allowed(model: str) -> bool:
    """Whether `model` may go into an address or a body."""
    return MODEL.fullmatch(model) is not None and not model.endswith(MOVING)


def record(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise Unfit
    return cast(dict[str, object], value)


def listed(value: object) -> list[object]:
    if not isinstance(value, list):
        raise Unfit
    return cast(list[object], value)


def words(value: object) -> str:
    if not isinstance(value, str):
        raise Unfit
    return value


def count(value: object) -> int:
    """A count of tokens. A number that is missing is an error, and never nought."""
    # `True` is an `int` to Python, and is no count.
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise Unfit
    return value


def count_if_given(value: object) -> int:
    """A count that its provider leaves out when it is nought, as its own examples show."""
    return 0 if value is None else count(value)


def parsed(body: bytes) -> dict[str, object]:
    """The body as a JSON object. Blank lines before it are no part of it."""
    if len(body) > MAX_BYTES:
        raise Unfit
    return record(json.loads(body))


def inlined(schema: Mapping[str, object]) -> dict[str, object]:
    """`schema` with every reference written out in full, and no definitions.

    What is left is made of `type`, `properties`, `required`,
    `additionalProperties`, `enum` and `items`, which every provider's
    documents list. It accepts what the schema accepted and nothing else. A
    reference that leads out of the schema, or back to itself, is refused.
    """
    defined = {
        name: record(schema.get(name, {})) for name in ("$defs", "definitions") if name in schema
    }

    def written(node: object, within: tuple[str, ...]) -> object:
        if isinstance(node, list):
            return [written(item, within) for item in cast(list[object], node)]
        if not isinstance(node, dict):
            return node
        held = cast(dict[str, object], node)
        rest = {key: written(value, within) for key, value in held.items() if key != "$ref"}
        if "$ref" not in held:
            return rest
        found = _REFERENCE.fullmatch(words(held["$ref"]))
        if found is None or found[0] in within or found[2] not in defined.get(found[1], {}):
            raise Unfit
        return record(written(defined[found[1]][found[2]], (*within, found[0]))) | rest

    top = {key: value for key, value in schema.items() if key not in defined}
    return record(written(top, ()))


def _one_of_three(failure: ModelFailure) -> type[ModelFailure]:
    if isinstance(failure, ModelTimeout):
        return ModelTimeout
    return ModelCapped if isinstance(failure, ModelCapped) else ModelError


class Adapter:
    """What the four adapters share: send once, read the status, read the answer.

    A provider's class says what to send (`body`, `path`, `headers`) and how
    to read what comes back (`read`). Everything else is the same for all
    four, so that none is held to less than another.

    Nothing of a call is kept. What is kept is a count of the answers in a
    row that would not mend themselves, so that a provider which refuses
    every call is not sent every person's sentence to refuse.
    """

    HOST: ClassVar[str]
    # The models whose own documents say they take the request as it is sent
    # here, the setting for thinking above all. A model of the same family
    # that is not here may refuse every call, so it is refused when the
    # service starts and not once a person has typed. A key that was set
    # where the model's name belongs is no such name either, and so is never
    # sent or logged. To add a model, read its page and add it with its test.
    FITS: ClassVar[frozenset[str]]
    KEY_HEADER: ClassVar[str]
    KEY_SCHEME: ClassVar[str] = ""
    HEADERS: ClassVar[Mapping[str, str]] = {}
    WANTS: ClassVar[frozenset[int]] = frozenset({OK})

    def __init__(
        self, key: Key, send: Send = over_https, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._key = key
        self._send = send
        self._clock = clock
        # How many answers in a row would not mend themselves, and until when
        # the provider is left alone. A count and a time: nothing of a call.
        self._lock = Lock()
        self._stuck = 0
        self._until: float | None = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"

    @classmethod
    def takes(cls, model: str) -> bool:
        """Whether `model` is one whose request was read, and may go in an address."""
        return allowed(model) and model in cls.FITS

    @property
    def resting(self) -> bool:
        """Whether the provider has refused so often that it is not being asked for now."""
        with self._lock:
            return self._until is not None and self._clock() < self._until

    def _heard(self, stuck: bool) -> None:
        with self._lock:
            self._stuck = self._stuck + 1 if stuck else 0
            self._until = self._clock() + REST_S if self._stuck >= PATIENCE else None

    def path(self, model: str) -> str:
        raise NotImplementedError

    def body(
        self, system: str, user: str, schema: dict[str, object], model: str, max_tokens: int
    ) -> dict[str, object]:
        raise NotImplementedError

    def read(self, answer: dict[str, object]) -> Outcome:
        raise NotImplementedError

    def failure(self, response: Response) -> type[ModelFailure] | None:
        """Which failure the status is. Decided on the status alone, unless a provider says more."""
        return refused(response.status)

    def complete(
        self,
        *,
        system: str,
        user: str,
        schema: Mapping[str, object],
        model: str,
        max_tokens: int,
        timeout_s: float,
    ) -> ModelReply:
        outcome = self._asked(system, user, schema, model, max_tokens, timeout_s)
        # What was sent is let go of before anything is raised, so that a
        # failure leaves from a frame that holds none of it. The settings go
        # too: a value in the wrong variable could be a key.
        del system, user, schema, model, max_tokens, timeout_s
        if isinstance(outcome, ModelReply):
            return outcome
        raise outcome()

    def _asked(
        self,
        system: str,
        user: str,
        schema: Mapping[str, object],
        model: str,
        max_tokens: int,
        timeout_s: float,
    ) -> Outcome:
        """The reply, or which failure it was. It never raises for anything that went wrong."""
        try:
            if not self.takes(model) or max_tokens < 1 or not timeout_s > 0:
                return ModelError
            if self.resting:
                # Nothing is made and nothing is sent.
                return ModelError
            sent = self.body(system, user, inlined(schema), model, max_tokens)
            request = Request(
                host=self.HOST,
                path=self.path(model),
                key_header=self.KEY_HEADER,
                key=self._key,
                key_scheme=self.KEY_SCHEME,
                headers=self.HEADERS,
                body=json.dumps(sent, ensure_ascii=False).encode(),
                wants=self.WANTS,
            )
            response = self._send(request, timeout_s)
            failed = self.failure(response)
            self._heard(response.status in STUCK and failed is ModelError)
            if failed is not None:
                return failed
            outcome = self.read(parsed(response.body))
            if isinstance(outcome, ModelReply):
                # An answer is a JSON object, whatever else it turns out to be.
                record(json.loads(outcome.output))
            return outcome
        except ModelFailure as failure:
            return _one_of_three(failure)
        except TimeoutError:
            return ModelTimeout
        except Exception:
            return ModelError
