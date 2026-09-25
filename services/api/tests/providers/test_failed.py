"""When a call to a model fails, nothing of the failure is written down.

A provider's error often holds what was sent to it: the sentence a person
typed, and sometimes the key. So on the way from a failed call to the rules
the error reaches no log. There is one place where a model is asked, `answer`
of route 1, and every failure is caught there, whatever its kind. What is
written is the type of the error and where in the code it happened, and how
the call is counted. Never its words, what it holds or what it prints as.

Each way of failing is driven through the service as it starts, with a marker
in the sentence and a made-up key set. Both are then looked for in every
record of every logger with the root logger at its lowest level, in all that
was printed, in every answer and in what is kept of each call.

No test here reaches a provider. A function, or the far end of a pair of
sockets, answers in its place.
"""

import json
import logging
import socket
import threading
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache, partial
from typing import Any

import pytest
from burro_api import logs
from burro_api.app import create_app, deps_from
from burro_api.deps import Deps
from burro_api.logs import JsonFormatter, configure_logging
from burro_api.providers.base import Deadline, Request, Response, Send, over_https
from burro_api.providers.choose import Choice, choose, told_of
from burro_api.providers.interface import ModelReply
from burro_api.providers.terms import TERMS, Provider
from burro_api.settings import Settings
from fastapi.testclient import TestClient

from ..support import LOOP
from .cases import CASES, all_of, listening

GEMINI = CASES[0]
# Two made-up words in mixed case, found nowhere else.
MARK = "Orrinthwaite Pelmadew"
# Not plain, so that the rules leave words unread and a model is asked. It holds what a
# person might well type of themselves.
TEXT = f"Honestly, 30 minutes to Cindermoor Works. I work nights at {MARK} and I am unwell"
# A made-up key in the form a provider gives one. It is put together from its parts, so
# that no file holds anything of that form, and it opens nothing.
KEY = "".join(("AI", "za", "Sy", "Zqx", "Keyed", "8143", "_Opens-Nothing_", "MadeUp", "00"))
# What is looked for, in small letters: each word of the marker, and the heart of the key.
NEVER = (*MARK.casefold().split(), "zqxkeyed8143", "unwell")
ON = {
    "BURRO_MODEL_PROVIDER": "gemini",
    "GEMINI_API_KEY": KEY,
    "BURRO_MODEL_TERMS_ACCEPTED": "gemini",
}
# How long an answer is waited for, where the test is of an answer that never comes. The
# others are given the time the service gives, so that none is late by chance.
SOON = {"BURRO_MODEL_TIMEOUT_S": "0.2"}
LET_GO = threading.Event()
# All that each stand-in was sent, which no stand-in but a test's may keep.
SENT: list[bytes] = []
# How the loggers of the test client are named. It is the caller, and no part of the service.
THE_CALLER = ("httpx", "httpcore")


class Unforeseen(Exception):
    """An error of a kind nobody named, as a library that is added one day may raise."""


class Stranger(BaseException):
    """An error that is no `Exception` at all, which a handler for `Exception` lets by."""


def all_that_was_sent(request: Request) -> str:
    """What a provider's error could say: the whole of what it was sent, and the key."""
    return f"could not read {request.body.decode()} sent with {request.key.for_header()}"


def raising(kind: type[BaseException]) -> Send:
    """A sender that raises `kind`, whose words and arguments hold all that was sent."""

    def send(request: Request, timeout_s: float) -> Response:
        said = all_that_was_sent(request)
        SENT.append(said.encode())
        raise kind(said, request.body, request.key.for_header(), {"sent": said})

    return send


def late(request: Request, timeout_s: float) -> Response:
    """A sender that is still at it when the person has been answered, and then fails."""
    SENT.append(all_that_was_sent(request).encode())
    LET_GO.wait(5)
    raise Unforeseen(all_that_was_sent(request))


class FarEnd:
    """The far end of a connection: a thread that plays the provider, on a pair of sockets.

    It reads the whole of the one request it is sent, as it went on the wire. Then it
    answers with all of it in the body, or says nothing.
    """

    def __init__(self, status: int | None, around: bytes = b"%s") -> None:
        self.status = status
        self.around = around
        self._ends: list[socket.socket] = []

    def _whole_request(self, link: socket.socket) -> bytes:
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
        return head + b"\r\n\r\n" + body

    def _answer(self, link: socket.socket, wire: bytes) -> None:
        if self.status is None:
            # It says nothing, until the caller has given up.
            LET_GO.wait(5)
            return
        # All it was sent, in the body of its answer: the sentence, and the header with the key.
        body = self.around % wire
        head = f"HTTP/1.1 {self.status} Whatever\r\nContent-Type: application/json\r\n"
        link.sendall(head.encode() + f"Content-Length: {len(body)}\r\n\r\n".encode() + body)

    def connect(self, host: str, deadline: Deadline) -> socket.socket:
        ours, theirs = socket.socketpair()
        self._ends.append(theirs)

        def serve() -> None:
            try:
                wire = self._whole_request(theirs)
                SENT.append(wire)
                self._answer(theirs, wire)
            except OSError:
                pass
            finally:
                theirs.close()

        threading.Thread(target=serve, daemon=True).start()
        return ours

    def close(self) -> None:
        for end in self._ends:
            end.close()


class InPlaceOfTheAdapter:
    """A client that raises where an adapter would have answered, with all it was handed.

    An adapter lets no error of its own out but the four it names. Whatever is
    put in its place one day may, and the route is the edge for that too.
    """

    def __init__(self, kind: type[BaseException]) -> None:
        self.kind = kind

    def complete(self, **sent: Any) -> ModelReply:
        # An adapter is handed the key when it is made, and a client is handed none.
        SENT.append(f"{sent['user']} {KEY}".encode())
        raise self.kind(f"could not read {sent['user']} sent with {KEY}", sent, KEY)


@dataclass(frozen=True)
class Failing:
    """One way for a call to fail: who answers in the provider's place, and how it is counted."""

    name: str
    counted: str
    # The type that is written of it, where a line is written for the failure at all.
    written_as: str | None
    send: Callable[[], Send] | None = None
    far: Callable[[], FarEnd] | None = None
    client: Callable[[], Any] | None = None
    # Whether the person is answered before the provider has done anything at all.
    never_comes: bool = False

    def __str__(self) -> str:
        return self.name


def _raises(name: str, kind: type[BaseException], counted: str, written_as: str | None) -> Failing:
    return Failing(name, counted, written_as, send=lambda: raising(kind))


def _answers(status: int, counted: str, written_as: str | None) -> Failing:
    return Failing(f"answers {status}", counted, written_as, far=lambda: FarEnd(status))


FAILINGS = (
    # It raises an error whose words and arguments hold the whole of what was sent, and the key.
    _raises("raises, and says all that was sent", RuntimeError, "error", "ModelError"),
    _raises("the connection is reset", ConnectionResetError, "error", "ModelError"),
    # It times out: it says so, it says nothing at all, or it is still at it afterwards.
    _raises("times out, and says all that was sent", TimeoutError, "timeout", None),
    Failing("never answers", "timeout", None, far=lambda: FarEnd(None), never_comes=True),
    Failing("is late, and then fails", "timeout", None, send=lambda: late, never_comes=True),
    # It answers with an error, and a body that holds all it was sent.
    _answers(400, "error", "ModelError"),
    _answers(401, "error", "ModelError"),
    _answers(403, "error", "ModelError"),
    _answers(429, "capped", None),
    _answers(500, "error", "ModelError"),
    # It answers 200 with a body that is no JSON.
    Failing(
        "answers 200 with what is no JSON",
        "error",
        "ModelError",
        far=lambda: FarEnd(200, b"<html>%s</html>"),
    ),
    # It raises an error of a kind nobody named.
    _raises("raises a kind nobody named", Unforeseen, "error", "ModelError"),
    _raises("raises what is no exception", Stranger, "error", "Stranger"),
    Failing(
        "a kind nobody named, in the adapter's place",
        "error",
        "Unforeseen",
        client=lambda: InPlaceOfTheAdapter(Unforeseen),
    ),
    Failing(
        "what is no exception, in the adapter's place",
        "error",
        "Stranger",
        client=lambda: InPlaceOfTheAdapter(Stranger),
    ),
    Failing(
        "an exit, in the adapter's place",
        "error",
        "SystemExit",
        client=lambda: InPlaceOfTheAdapter(SystemExit),
    ),
)


def _the_service(failing: Failing) -> tuple[Deps, FarEnd | None]:
    """What the service depends on as it starts, with `failing` where the provider would be."""
    env = ON | (SOON if failing.never_comes else {})
    settings = Settings.from_env(env)
    if failing.client is not None:
        told = told_of(TERMS[Provider.GEMINI], with_settings=False)
        return deps_from(settings, Choice(failing.client(), GEMINI.model, told)), None
    if failing.far is not None:
        far = failing.far()
        return deps_from(settings, choose(env, send=partial(over_https, connect=far.connect))), far
    assert failing.send is not None
    return deps_from(settings, choose(env, send=failing.send())), None


@dataclass
class Found:
    """All that one failure left behind."""

    failing: Failing
    answer: Any
    records: list[logging.LogRecord]
    lines: list[dict[str, Any]]
    kept: list[str]
    printed: str
    # All that whoever stood in the provider's place was sent.
    sent: list[bytes]

    def everything(self) -> str:
        """Every record in full, every line, all that was printed or kept, and the answer."""
        answered = f"{self.answer.status_code} {dict(self.answer.headers)!r} {self.answer.text}"
        written = [all_of(record) for record in self.records]
        return "\n".join((answered, *written, json.dumps(self.lines), *self.kept, self.printed))


def _asked(deps: Deps) -> Any:
    client = TestClient(create_app(deps), raise_server_exceptions=True)
    if LOOP:
        client.portal = LOOP[0]
    return client.post("/v1/interpret", json={"text": TEXT})


@cache
def ruled() -> dict[str, Any]:
    """What the service answers to the same sentence where no model is set."""
    return _asked(deps_from(Settings.from_env({}))).json()["data"]


def _of_the_call(thread: threading.Thread) -> bool:
    """Whether a thread is one a call to a model runs on, or one that plays the provider."""
    return thread.name.endswith(("(run)", "(serve)", "(look)"))


def _driven(failing: Failing, capfd: pytest.CaptureFixture[str]) -> Found:
    LET_GO.clear()
    SENT.clear()
    before = set(threading.enumerate())
    far: FarEnd | None = None
    try:
        # Logging as the service sets it up, so that what it would print is printed.
        configure_logging()
        with listening() as records:
            deps, far = _the_service(failing)
            answer = _asked(deps)
            # What was still running is let go of, and is waited for: what it
            # raises once nobody is waiting for it must be written nowhere either.
            LET_GO.set()
            for thread in set(threading.enumerate()) - before:
                if _of_the_call(thread):
                    thread.join(5)
            kept = [record.model_dump_json() for record in deps.calls.records(deps.clock.now())]
            lines = [json.loads(JsonFormatter().format(record)) for record in records]
            written = list(records)
        out, err = capfd.readouterr()
        return Found(failing, answer, written, lines, kept, out + err, list(SENT))
    finally:
        LET_GO.set()
        if far is not None:
            far.close()


# Each failure is driven once, by the first test that asks for it. The tests of a file
# run in one process and in their order, so every test of it reads what that one found.
_FOUND: dict[str, Found] = {}


@pytest.fixture(params=FAILINGS, ids=str)
def found(request: pytest.FixtureRequest, capfd: pytest.CaptureFixture[str]) -> Found:
    failing: Failing = request.param
    if failing.name not in _FOUND:
        _FOUND[failing.name] = _driven(failing, capfd)
    return _FOUND[failing.name]


def test_the_person_is_answered_by_the_rules_whatever_the_provider_does(found: Found):
    # Never a 5xx, and never the framework's own page for an error nobody foresaw.
    assert found.answer.status_code == 200
    assert found.answer.headers["content-type"] == "application/json"
    data = found.answer.json()["data"]
    assert (data["interpreter"], data["degraded"]) == ("rule", True)
    # What the rules answer where no model is set, but for saying that they stood in.
    assert data == ruled() | {"degraded": True}
    assert data["suggestions"] != []


def test_the_sentence_and_the_key_are_in_nothing_that_is_written_printed_or_answered(found: Found):
    everything = found.everything().casefold()

    assert not [word for word in NEVER if word in everything]
    assert KEY.casefold() not in everything
    # The service did write its lines, and they were looked through.
    assert {"interpret", "request"} <= {line["event"] for line in found.lines}
    assert '"event":"interpret"' in found.printed


def test_the_provider_was_sent_the_sentence_and_the_key_so_there_was_something_to_give_away(
    found: Found,
):
    # Once, and as it was typed. A test that found nothing because nothing was sent
    # would say nothing of the service.
    [sent] = found.sent
    assert MARK.encode() in sent and KEY.encode() in sent


def test_what_is_written_of_a_failure_is_its_type_and_how_the_call_is_counted(found: Found):
    failing = found.failing
    [read] = [line for line in found.lines if line["event"] == "interpret"]
    failures = [line for line in found.lines if line["event"] == "failure"]

    assert read["call_status"] == failing.counted
    assert isinstance(read["latency_ms"], int)
    assert [line["exception"] for line in failures] == (
        [] if failing.written_as is None else [failing.written_as]
    )
    for line in failures:
        # The type, the types of what led to it, and where in the code it happened.
        assert set(line) == {"at", "event", "level", "exception", "causes", "frames", "request_id"}
        assert all(isinstance(cause, str) and cause.isidentifier() for cause in line["causes"])
        for frame in line["frames"]:
            file, number, function = frame.rsplit(":", 2)
            assert file.endswith(".py") and number.isdigit(), frame
            assert function.strip("<>").isidentifier(), frame
    # Every line is an event and fields from the list, and no record holds a message
    # that was put together from anything.
    for record in found.records:
        if record.name == logs.LOGGER:
            assert record.args in ((), None) and record.exc_info is None
            assert set(getattr(record, "burro_fields", {})) <= logs.LOGGABLE


def test_the_frameworks_own_handler_is_never_reached_from_the_path_of_a_model(found: Found):
    # The route caught it. Had it fallen to the edge, the line would name the route and
    # the answer would be a 500. Had it fallen past the edge, the server would have
    # written it, and the test client would have raised it here.
    assert found.answer.status_code == 200
    assert not [line for line in found.lines if line["event"] == "failure" and "route" in line]
    [asked] = [line for line in found.lines if line["event"] == "request"]
    assert (asked["status"], asked.get("error_code")) == (200, None)
    # Nor did the server or the framework write a line of its own. The test client is
    # the caller, and what it logs of the request it made is not the service's.
    library = [line for line in found.lines if line["event"] == "library"]
    assert not [line for line in library if not line["logger"].startswith(THE_CALLER)]


def test_no_logger_but_the_services_own_writes_on_the_path_of_a_model(found: Found):
    wrote = {record.name for record in found.records if not record.name.startswith(THE_CALLER)}

    assert wrote == {logs.LOGGER}
