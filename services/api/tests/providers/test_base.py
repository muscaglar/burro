"""The function that sends, with a real connection and no network.

The two ends of a socket pair stand for Burro and for the provider, and a
thread plays the provider. So what is tested is what is written to the wire
and how what comes back is read, by the standard library's own parser. What
cannot be tested here is the handshake with a real certificate.
"""

import socket
import ssl
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread

import pytest
from burro_api.providers import base
from burro_api.providers.base import (
    MAX_BYTES,
    Deadline,
    Key,
    Request,
    Response,
    allowed,
    over_https,
    refused,
    verifying,
)
from burro_api.providers.interface import ModelError, ModelFailure, ModelTimeout

from .cases import KEY_TEXT, KEYED, TYPED, assert_bare, key, listening

BODY = b'{"request": "ten minutes from ' + TYPED.encode() + b'"}'
ANSWER = b'{"answer": "' + TYPED.encode() + b'"}'

Play = Callable[[socket.socket], None]


def request(**changes: object) -> Request:
    sent: dict[str, object] = {
        "host": "api.provider.example",
        "path": "/v1/answers",
        "key_header": "x-api-key",
        "key": key(),
        "headers": {"x-version": "2026-09-23"},
        "body": BODY,
    } | changes
    return Request(**sent)  # type: ignore[arg-type]


def _read_request(link: socket.socket) -> bytes:
    """All of one request: its head, and as much body as its head says."""
    got = b""
    while b"\r\n\r\n" not in got:
        got += link.recv(65536)
    head, _, body = got.partition(b"\r\n\r\n")
    [length] = [
        int(line.split(b":")[1])
        for line in head.split(b"\r\n")
        if line.lower().startswith(b"content-length:")
    ]
    while len(body) < length:
        body += link.recv(65536)
    return got


class Provider:
    """The far end of the connection. It keeps each request it was sent."""

    def __init__(self, play: Play) -> None:
        self.play = play
        self.received: list[bytes] = []
        self.connections = 0
        self.hosts: list[str] = []
        self._threads: list[Thread] = []
        self._ends: list[socket.socket] = []
        self.done = Event()

    def connect(self, host: str, deadline: Deadline) -> socket.socket:
        self.connections += 1
        self.hosts.append(host)
        ours, theirs = socket.socketpair()
        self._ends.append(theirs)

        def serve() -> None:
            try:
                self.received.append(_read_request(theirs))
                self.play(theirs)
            except OSError:
                pass
            finally:
                theirs.close()
                self.done.set()

        thread = Thread(target=serve, daemon=True)
        self._threads.append(thread)
        thread.start()
        return ours

    def close(self) -> None:
        self.done.set()
        for end in self._ends:
            end.close()
        for thread in self._threads:
            thread.join(2)


@contextmanager
def provider(play: Play) -> Generator[Provider]:
    playing = Provider(play)
    try:
        yield playing
    finally:
        playing.close()


def says(raw: bytes) -> Play:
    return lambda link: link.sendall(raw)


def answer(status: int = 200, body: bytes = ANSWER, extra: str = "") -> bytes:
    head = f"HTTP/1.1 {status} Whatever\r\nContent-Type: application/json\r\n{extra}"
    return head.encode() + f"Content-Length: {len(body)}\r\n\r\n".encode() + body


def failing(sent: Request, play: Play, timeout_s: float = 2.0) -> ModelFailure:
    with provider(play) as far, pytest.raises(ModelFailure) as failed:
        over_https(sent, timeout_s, connect=far.connect)
    return failed.value


def test_one_post_is_written_and_the_answer_is_its_status_and_its_body():
    with provider(says(answer())) as far:
        got = over_https(request(), 2.0, connect=far.connect)

    assert (got.status, got.body) == (200, ANSWER)
    [wire] = far.received
    head, _, body = wire.partition(b"\r\n\r\n")
    assert head.decode("ascii").split("\r\n") == [
        "POST /v1/answers HTTP/1.1",
        "Host: api.provider.example",
        "Content-Type: application/json",
        f"Content-Length: {len(BODY)}",
        "Accept: application/json",
        "Accept-Encoding: identity",
        "Connection: close",
        "User-Agent: burro",
        "x-version: 2026-09-23",
        f"x-api-key: {KEY_TEXT}",
    ]
    assert body == BODY
    assert far.hosts == ["api.provider.example"]


def test_the_key_is_in_its_header_and_never_in_the_address():
    sent = request(key_header="Authorization", key_scheme="Bearer ")

    with provider(says(answer())) as far:
        over_https(sent, 2.0, connect=far.connect)

    [wire] = far.received
    lines = wire.partition(b"\r\n\r\n")[0].decode("ascii").split("\r\n")
    assert KEYED not in lines[0]
    assert [line for line in lines if KEYED in line] == [f"Authorization: Bearer {KEY_TEXT}"]


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_a_redirect_is_answered_as_its_status_and_never_followed(status: int):
    elsewhere = "Location: https://elsewhere.example/v1/answers\r\n"

    with provider(says(answer(status, b"moved", elsewhere))) as far:
        got = over_https(request(), 2.0, connect=far.connect)

    assert (got.status, got.body) == (status, b"")
    # One connection, to the host in code, and one request on it.
    assert (far.connections, far.hosts) == (1, ["api.provider.example"])
    assert len(far.received) == 1
    assert type(refused(got.status)) is type(ModelError)
    assert refused(got.status) is ModelError


@pytest.mark.parametrize("status", [400, 401, 402, 404, 429, 500, 503, 529])
def test_the_body_of_an_error_is_left_unread(status: int):
    echo = b'{"error": {"message": "could not read ' + BODY + b'"}}'

    with provider(says(answer(status, echo))) as far:
        got = over_https(request(), 2.0, connect=far.connect)

    assert (got.status, got.body) == (status, b"")


def test_the_body_of_an_error_is_read_where_the_adapter_asks_for_it():
    with provider(says(answer(400, b'{"error": {}}'))) as far:
        got = over_https(request(wants=frozenset({200, 400})), 2.0, connect=far.connect)

    assert (got.status, got.body) == (400, b'{"error": {}}')


def test_an_answer_in_chunks_is_read_whole():
    chunked = (
        b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n"
        b"5\r\n" + ANSWER[:5] + b"\r\n" + f"{len(ANSWER) - 5:x}".encode() + b"\r\n" + ANSWER[5:]
    ) + b"\r\n0\r\n\r\n"

    with provider(says(chunked)) as far:
        got = over_https(request(), 2.0, connect=far.connect)

    assert got.body == ANSWER


def test_a_body_of_the_greatest_size_is_read_and_one_byte_more_is_refused():
    most = b"x" * MAX_BYTES

    with provider(says(answer(200, most))) as far:
        assert over_https(request(), 2.0, connect=far.connect).body == most

    assert type(failing(request(), says(answer(200, most + b"x")))) is ModelError


def _endless(link: socket.socket) -> None:
    link.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    for _ in range(64):
        link.sendall(b"x" * 65536)


def _endless_chunks(link: socket.socket) -> None:
    link.sendall(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n")
    for _ in range(64):
        link.sendall(b"10000\r\n" + b"x" * 65536 + b"\r\n")


def _understated(link: socket.socket) -> None:
    link.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 12\r\n\r\n" + b"x" * (2 * MAX_BYTES))


@pytest.mark.parametrize("play", [_endless, _endless_chunks], ids=["to the end", "in chunks"])
def test_a_body_with_no_stated_length_is_read_to_the_limit_and_refused(play: Play):
    failure = failing(request(), play)

    assert type(failure) is ModelError
    assert_bare(failure)


def test_a_body_that_is_longer_than_it_says_is_read_as_long_as_it_says():
    with provider(_understated) as far:
        got = over_https(request(), 2.0, connect=far.connect)

    assert got.body == b"x" * 12


@pytest.mark.parametrize("length", ["-1", "abc", "1e3", str(MAX_BYTES + 1), "9" * 40])
def test_a_stated_length_that_is_too_long_or_no_number_is_refused_unread(length: str):
    raw = f"HTTP/1.1 200 OK\r\nContent-Length: {length}\r\n\r\n".encode() + ANSWER

    assert type(failing(request(), says(raw))) is ModelError


def _silent(link: socket.socket) -> None:
    # Says nothing, until the caller gives up and closes its end.
    link.recv(1)


def _trickle(link: socket.socket) -> None:
    # As one provider does under load: the status, then an empty line now and then.
    link.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
    for _ in range(200):
        time.sleep(0.02)
        link.sendall(b"\n")


def _slow_head(link: socket.socket) -> None:
    for byte in b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}":
        time.sleep(0.05)
        link.sendall(bytes([byte]))


@pytest.mark.parametrize("play", [_silent, _trickle, _slow_head], ids=["silent", "trickle", "slow"])
def test_the_whole_call_has_one_deadline_however_the_time_is_spent(play: Play):
    took = [0.0]
    with provider(play) as far, pytest.raises(ModelFailure) as failed:
        began = time.monotonic()
        try:
            over_https(request(), 0.2, connect=far.connect)
        finally:
            took[0] = time.monotonic() - began

    failure = failed.value
    assert type(failure) is ModelTimeout
    # Each read that worked was given only what was left, and none was given more. The
    # deadline is a fifth of a second: long enough for several reads of each kind, and
    # short, because three tests wait it out on a real clock.
    assert 0.15 < took[0] < 1.0
    assert_bare(failure)


def test_an_answer_that_comes_in_time_is_read_though_it_comes_in_pieces():
    def play(link: socket.socket) -> None:
        for piece in (answer()[:20], answer()[20:40], answer()[40:]):
            time.sleep(0.02)
            link.sendall(piece)

    with provider(play) as far:
        assert over_https(request(), 2.0, connect=far.connect).body == ANSWER


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (TimeoutError(f"timed out reaching {KEY_TEXT}"), ModelTimeout),
        (ConnectionRefusedError(f"refused {KEY_TEXT}"), ModelError),
        (socket.gaierror(8, f"no such name {KEY_TEXT}"), ModelError),
        (ssl.SSLCertVerificationError(1, f"certificate verify failed {KEY_TEXT}"), ModelError),
        (ssl.SSLError(1, f"handshake failure {KEY_TEXT}"), ModelError),
        (RuntimeError(f"anything else {KEY_TEXT}"), ModelError),
    ],
    ids=range(6),
)
def test_a_connection_that_cannot_be_made_is_one_of_the_three(
    raised: Exception, expected: type[ModelFailure]
):
    def connect(host: str, deadline: Deadline) -> socket.socket:
        raise raised

    with pytest.raises(ModelFailure) as failed:
        over_https(request(), 2.0, connect=connect)

    assert type(failed.value) is expected
    assert_bare(failed.value)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\r\n\r\n",
        b"not http at all " + TYPED.encode(),
        b"HTTP/1.1 two hundred OK\r\n\r\n",
        b"HTTP/1.1 99999 OK\r\n\r\n",
        b"HTTP/1.1 200 OK\r\nContent-Length: 50\r\n\r\n{}",
        b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\nzz\r\n{}\r\n0\r\n\r\n",
        b"HTTP/1.1 200 OK\r\n" + b"x-filler: " + b"y" * 70_000 + b"\r\n\r\n{}",
        b"HTTP/1.1 200 OK\r\n" + b"".join(b"x-%d: y\r\n" % n for n in range(200)) + b"\r\n{}",
    ],
    ids=range(9),
)
def test_what_is_not_an_answer_over_http_is_an_error(raw: bytes):
    failure = failing(request(), says(raw))

    assert type(failure) is ModelError
    assert_bare(failure)


@pytest.mark.parametrize(
    "changes",
    [
        {"host": "api.provider.example:8443"},
        {"host": "api.provider.example/x"},
        {"host": "user@api.provider.example"},
        {"host": "API.provider.example"},
        {"host": ""},
        {"host": "api.provider.example\r\nx-injected: 1"},
        {"path": "v1/answers"},
        {"path": "/v1/answers?key=abc"},
        {"path": "/v1/answers#x"},
        {"path": "/v1/ answers"},
        {"path": "/v1/answers\r\nx-injected: 1"},
        {"path": "/v1/%2e%2e/answers"},
        {"path": "//elsewhere.example/v1"},
        {"path": ""},
        {"key_header": "x-api-key\r\nx-injected"},
        {"key_header": "x api key"},
        {"key_header": ""},
        {"key_header": "Host"},
        {"key_header": "Content-Length"},
        {"key_scheme": "Bearer\r\nx-injected: "},
        {"key_scheme": " "},
        {"headers": {"x-version": "1\r\nx-injected: 1"}},
        {"headers": {"x-version\r\nx-injected": "1"}},
        {"headers": {"x-version": ""}},
        {"headers": {"x-version": "café"}},
        {"headers": {"X-API-KEY": "another"}},
        {"headers": {"content-length": "0"}},
        {"headers": {"Transfer-Encoding": "chunked"}},
        {"headers": {"Host": "elsewhere.example"}},
    ],
    ids=range(29),
)
def test_a_request_that_is_not_fit_to_send_reaches_nobody(changes: dict[str, object]):
    reached: list[str] = []

    def connect(host: str, deadline: Deadline) -> socket.socket:
        reached.append(host)
        raise AssertionError("it was sent")

    with pytest.raises(ModelError) as failed:
        over_https(request(**changes), 2.0, connect=connect)

    assert reached == []
    assert_bare(failed.value)


@pytest.mark.parametrize("seconds", [0, -1, float("nan"), float("-inf")])
def test_a_call_with_no_time_to_run_is_never_made(seconds: float):
    reached: list[str] = []

    def connect(host: str, deadline: Deadline) -> socket.socket:
        reached.append(host)
        raise AssertionError("it was sent")

    with pytest.raises(ModelFailure):
        over_https(request(), seconds, connect=connect)

    assert reached == []


def test_nothing_is_logged_and_nothing_is_printed(capsys: pytest.CaptureFixture[str]):
    with listening() as records:
        with provider(says(answer())) as far:
            over_https(request(), 2.0, connect=far.connect)
        failing(request(), says(answer(200, b"x" * (MAX_BYTES + 1))))
        failing(request(), _silent, timeout_s=0.05)
        failing(request(path="no slash"), says(answer()))

    printed = capsys.readouterr()
    assert records == []
    assert (printed.out, printed.err) == ("", "")


def test_nothing_of_a_call_is_kept_once_it_is_over():
    before = {name: repr(value) for name, value in vars(base).items()}

    with provider(says(answer())) as far:
        over_https(request(), 2.0, connect=far.connect)

    after = {name: repr(value) for name, value in vars(base).items()}
    assert after == before
    assert TYPED not in repr(after) and KEYED not in repr(after)


def test_the_certificate_is_checked_and_so_is_the_name_on_it():
    context = verifying()

    assert context.verify_mode is ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert context.minimum_version >= ssl.TLSVersion.TLSv1_2
    assert context.protocol is ssl.PROTOCOL_TLS_CLIENT
    # As strict as the context the standard library makes ready.
    assert context.verify_flags & ssl.VERIFY_X509_STRICT
    ready = ssl.create_default_context().verify_flags
    assert context.verify_flags & ready == ready


@pytest.fixture
def fresh_context() -> Generator[None]:
    """The context is made once and kept. A test that changes what it is made from makes it anew."""
    verifying.cache_clear()
    yield
    verifying.cache_clear()


@pytest.mark.usefixtures("fresh_context")
def test_the_secrets_of_a_call_are_written_nowhere_whatever_the_environment_asks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    # With this set, the context the standard library makes ready writes the
    # secrets of every call to the file. Whoever held it, and a copy of the
    # traffic, could read the key and the words.
    wanted = tmp_path / "keys.log"
    monkeypatch.setenv("SSLKEYLOGFILE", str(wanted))
    assert ssl.create_default_context().keylog_filename == str(wanted)
    wanted.unlink(missing_ok=True)

    context = verifying()

    assert context.keylog_filename is None
    assert not wanted.exists()
    assert context.verify_mode is ssl.CERT_REQUIRED and context.check_hostname is True


def test_the_context_is_made_by_hand_and_names_no_file_for_secrets():
    source = Path(base.__file__).read_text(encoding="utf-8")

    assert "create_default_context" not in source.replace("`ssl.create_default_context`", "")
    assert "keylog_filename" not in source and "environ" not in source


@pytest.mark.usefixtures("fresh_context")
def test_the_hosts_own_list_of_certificates_is_the_one_that_is_trusted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    # Whoever runs a host names its certificates with these two, and they
    # are honoured: a list that holds nothing trusts nobody. Whether to go
    # on honouring them is the founder's to decide, and this test changes
    # with that decision. No proxy is read either way.
    empty = tmp_path / "none.pem"
    empty.write_text("", encoding="ascii")
    (tmp_path / "certs").mkdir()
    monkeypatch.setenv("SSL_CERT_FILE", str(empty))
    monkeypatch.setenv("SSL_CERT_DIR", str(tmp_path / "certs"))

    context = verifying()

    assert context.cert_store_stats()["x509_ca"] == 0
    assert context.verify_mode is ssl.CERT_REQUIRED and context.check_hostname is True


def test_a_connection_is_made_to_port_443_with_the_name_checked(monkeypatch: pytest.MonkeyPatch):
    made: list[object] = []
    ours, theirs = socket.socketpair()

    class Plain:
        def __init__(self, family: int, kind: int, proto: int) -> None:
            made.append(("socket", family, kind))

        def settimeout(self, seconds: float) -> None:
            made.append(("timeout", 0 < seconds <= 2.0))

        def connect(self, where: object) -> None:
            made.append(("connect", where))

        def close(self) -> None:
            made.append("close")

    class Context:
        def wrap_socket(self, plain: object, server_hostname: str) -> socket.socket:
            made.append(("wrap", server_hostname))
            return ours

    found = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 443))]

    def look(host: str, port: int, **_: object) -> list[object]:
        made.append((host, port))
        return list(found)

    monkeypatch.setattr(socket, "getaddrinfo", look)
    monkeypatch.setattr(socket, "socket", Plain)
    monkeypatch.setattr(base, "verifying", Context)
    try:
        assert base.tls("api.provider.example", Deadline(2.0)) is ours
    finally:
        ours.close()
        theirs.close()

    assert made == [
        ("api.provider.example", 443),
        ("socket", socket.AF_INET, socket.SOCK_STREAM),
        ("timeout", True),
        ("connect", ("192.0.2.1", 443)),
        ("timeout", True),
        ("wrap", "api.provider.example"),
    ]


class _Addresses:
    """Stands in for the network: some addresses answer, some refuse, some say nothing."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, *behave: str) -> None:
        self.tried: list[tuple[str, float]] = []
        self.ours, self.theirs = socket.socketpair()
        outer = self

        class Plain:
            def __init__(self, family: int, kind: int, proto: int) -> None:
                self.given = 0.0

            def settimeout(self, seconds: float) -> None:
                self.given = seconds

            def connect(self, where: tuple[str, int]) -> None:
                outer.tried.append((where[0], self.given))
                how = behave[int(where[0].rsplit(".", 1)[1]) - 1]
                if how == "silent":
                    time.sleep(self.given)
                    raise TimeoutError
                if how == "refuses":
                    raise ConnectionRefusedError

            def close(self) -> None:
                pass

        class Context:
            def wrap_socket(self, plain: object, server_hostname: str) -> socket.socket:
                return outer.ours

        found = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (f"192.0.2.{n + 1}", 443))
            for n in range(len(behave))
        ]

        def look(host: str, port: int, **_: object) -> list[object]:
            return list(found)

        monkeypatch.setattr(socket, "getaddrinfo", look)
        monkeypatch.setattr(socket, "socket", Plain)
        monkeypatch.setattr(base, "verifying", Context)

    def close(self) -> None:
        self.ours.close()
        self.theirs.close()


def test_an_address_that_does_not_answer_leaves_time_for_the_next(
    monkeypatch: pytest.MonkeyPatch,
):
    network = _Addresses(monkeypatch, "silent", "refuses", "answers")
    try:
        assert base.tls("api.provider.example", Deadline(0.3)) is network.ours
    finally:
        network.close()

    [first, second, third] = network.tried
    assert [where for where, _ in network.tried] == ["192.0.2.1", "192.0.2.2", "192.0.2.3"]
    # A third of the time for the first of three, half of what is left for the second.
    assert first[1] == pytest.approx(0.1, abs=0.02)
    assert second[1] == pytest.approx(0.1, abs=0.02)
    assert third[1] == pytest.approx(0.2, abs=0.03)


@pytest.mark.parametrize(
    ("behave", "expected"),
    [
        (("silent", "silent"), TimeoutError),
        (("refuses", "refuses"), OSError),
        (("refuses", "silent"), TimeoutError),
        ((), OSError),
    ],
    ids=["silent", "refused", "both", "no address"],
)
def test_when_no_address_answers_it_is_a_timeout_only_if_the_time_is_spent(
    monkeypatch: pytest.MonkeyPatch, behave: tuple[str, ...], expected: type[OSError]
):
    network = _Addresses(monkeypatch, *behave)
    began = time.monotonic()
    try:
        with pytest.raises(OSError) as failed:
            base.tls("api.provider.example", Deadline(0.1))
    finally:
        network.close()

    assert type(failed.value) is expected
    assert time.monotonic() - began < 0.6


def test_looking_a_name_up_is_inside_the_deadline_too(monkeypatch: pytest.MonkeyPatch):
    release = Event()

    def slow(host: str, port: int, **_: object) -> list[object]:
        release.wait(3)
        return []

    monkeypatch.setattr(socket, "getaddrinfo", slow)
    began = time.monotonic()
    try:
        with pytest.raises(ModelTimeout):
            over_https(request(), 0.1)
    finally:
        release.set()

    assert time.monotonic() - began < 1.0


def test_a_name_that_cannot_be_found_is_an_error(monkeypatch: pytest.MonkeyPatch):
    def missing(host: str, port: int, **_: object) -> list[object]:
        raise socket.gaierror(8, f"nodename nor servname provided for {host}")

    monkeypatch.setattr(socket, "getaddrinfo", missing)

    with pytest.raises(ModelError) as failed:
        over_https(request(), 1.0)

    assert_bare(failed.value)


def test_a_deadline_gives_what_is_left_and_then_nothing():
    now = [100.0]
    deadline = Deadline(2.0, clock=lambda: now[0])

    assert deadline.left() == 2.0
    now[0] = 101.5
    assert deadline.left() == 0.5
    now[0] = 102.0
    with pytest.raises(TimeoutError):
        deadline.left()


@pytest.mark.parametrize(
    "value",
    ["", " ", "with space", "with\ttab", "line\nbreak", "line\r\nx-injected: 1", "café", "k" * 513],
)
def test_a_key_that_could_not_go_in_a_header_is_refused_without_being_shown(value: str):
    with pytest.raises(ValueError, match=r"^not a key$") as refused_key:
        Key(value)

    assert refused_key.value.args == ("not a key",)


def test_a_key_shows_in_no_repr_no_str_and_no_copy():
    import copy
    import pickle

    held = key()

    assert KEYED not in f"{held!r} {held!s} {held} {[held]} {held:}"
    assert not hasattr(held, "__dict__")
    for copied in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            copied(held)
    assert held.for_header("Bearer ") == f"Bearer {KEY_TEXT}"


def test_a_key_cannot_be_read_out_by_a_tool_that_writes_objects_down():
    import dataclasses
    import json

    held = key()

    # The ways a serialiser asks an object for what it holds.
    for asked in (
        lambda: held.__getstate__(),
        lambda: held.__reduce__(),
        lambda: held.__reduce_ex__(2),
        lambda: held.__reduce_ex__(5),
        lambda: json.dumps(held),
        lambda: vars(held),
        lambda: dataclasses.asdict(request(key=held)),
    ):
        with pytest.raises(TypeError) as refused_to:
            asked()
        assert KEYED not in repr(refused_to.value.args)


def test_a_request_and_an_answer_show_nothing_of_what_they_hold():
    shown = f"{request()!r} {request()!s} {Response(200, ANSWER)!r} {Response(200, ANSWER)!s}"

    assert TYPED not in shown and KEYED not in shown


@pytest.mark.parametrize(
    "name",
    [
        "gemini-3.5-flash-lite",
        "gpt-6-luna",
        "gpt-5.4-nano-2026-03-17",
        "deepseek-flash",
        "claude-haiku-4-5-20251001",
        "claude-sonnet-5",
        "o4-mini",
        "a",
        "g" * 64,
    ],
)
def test_the_names_the_providers_give_their_models_are_allowed(name: str):
    assert allowed(name)
