"""What is logged of accounts: what happened and how it ended, and nothing of whom.

No line holds an address, a token, a session, an account, the address of a client or a
spec. The test looks for each one that was used, and then for anything in the shape of
one, in every line, in every record in full, and in everything the service wrote out.

A test that only looked for them would pass if nothing were logged. So it also holds
what should be there: every word of the two closed lists that a person can bring about.
"""

import json
import re
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from burro_api import logs
from burro_api.accounts.events import Event, Outcome
from burro_api.accounts.sender import SendFailed
from burro_api.logs import configure_logging

from ..support import CANARY, SCHOOL, Seen, commute, searching, watching, wire
from .support import (
    ADDRESS,
    LIMITS_KEY,
    SAFARI,
    SECRET,
    Browser,
    On,
    Post,
    code,
    data,
    turned_on,
)

EMAIL = f"marmalade.{CANARY}@example.org"
OTHER = "pumpernickel.vole@example.org"
ACCOUNT_LINE = {"at", "level", "event", "request_id", "happened", "outcome"}
REQUEST_LINE = {
    "at",
    "level",
    "event",
    "request_id",
    "method",
    "route",
    "status",
    "latency_ms",
    "release_id",
    "engine_version",
    "synthetic",
    "preview",
    "error_code",
}
# Anything in the shape of what must never be written. An id of a request is made by
# the service for each request and names nobody, so it is taken out before the search.
IN_THE_SHAPE_OF = {
    "an address": re.compile(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "the address of a client": re.compile(
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|[0-9a-f]*::?[0-9a-f:]+/\d+"
    ),
    "a token, a session or an id": re.compile(r"[A-Za-z0-9_-]{22,}"),
    "a hash": re.compile(r"[0-9A-Fa-f]{20,}"),
    "a place or an area": re.compile(r"(?:syn|lon)-[a-z][0-9]"),
    "a cookie": re.compile(r"burro_(?:session|link)", re.IGNORECASE),
}


@contextmanager
def heard(on: On) -> Generator[Seen]:
    """The service with accounts on, as it logs when it runs, with every line kept."""
    configure_logging()
    with watching(on.deps) as seen:
        on.client = seen.client
        yield seen


def ours(seen: Seen) -> list[dict[str, Any]]:
    """Every line the service wrote, without the id of its request and the time it was written.

    A line of a library is cut down to where it came from, and holds nothing that was sent.
    """
    made_anew = ("request_id", "at")
    return [
        {name: value for name, value in line.items() if name not in made_anew}
        for line in seen.lines()
        if line["event"] != "library"
    ]


def happened(seen: Seen) -> list[tuple[str, str]]:
    return [(line["happened"], line["outcome"]) for line in seen.events("account")]


def a_whole_life(on: On, post: Post) -> set[str]:
    """Everything that can happen to an account, and every secret that was used in it."""
    used: set[str] = {SECRET, LIMITS_KEY, ADDRESS, "198.51.100.66", "2001:db8:1:2::7"}
    desk = Browser(on)
    phone = Browser(on, agent=SAFARI, address="2001:db8:1:2::7")
    stranger = Browser(on, address="198.51.100.66")
    spec = wire(searching(commutes=(commute(SCHOOL, 25),)))

    def keep(*browsers: Browser) -> None:
        for browser in browsers:
            used.update(browser.cookies.values())
        used.update(link.rpartition("=")[2] for _, link in post.sent)

    # What is no address, a link that is asked for, and one that a sender will not send.
    assert code(desk.post("/v1/auth/link", {"email": f"{CANARY} at example"}))[0] == 422
    first = desk.ask_for_link(EMAIL)
    keep(desk)
    # A letter is sent once the answer is given, so the answer is the one every address
    # is given. Whoever asks in the minute after is told that none can be sent.
    post.fails = SendFailed(reached=False)
    assert desk.post("/v1/auth/link", {"email": OTHER}).status_code == 202
    assert desk.post("/v1/auth/link", {"email": OTHER}).status_code == 503
    on.later(minutes=1)
    post.fails = SendFailed(reached=True)
    assert desk.post("/v1/auth/link", {"email": OTHER}).status_code == 202
    post.fails = None
    # Whose it is, in the browser that asked and in another, and what is no link at all.
    assert data(desk.post("/v1/auth/link/whose", {"token": first}))["email"] == EMAIL
    assert data(phone.post("/v1/auth/link/whose", {"token": first}))["same_browser"] is False
    assert code(stranger.post("/v1/auth/link/whose", {"token": "t" * 43}))[0] == 422
    assert code(phone.post("/v1/auth/session", {"token": first, "adult": True}))[0] == 409
    assert code(desk.post("/v1/auth/session", {"token": first}))[0] == 409
    # Signing in, and the link used again.
    assert desk.post("/v1/auth/session", {"token": first, "adult": True}).status_code == 200
    keep(desk)
    assert code(desk.post("/v1/auth/session", {"token": first}))[0] == 410
    # A second browser, by a link that is opened in it and one that runs out.
    late = phone.ask_for_link(EMAIL)
    on.later(minutes=16)
    assert code(phone.post("/v1/auth/session", {"token": late}))[0] == 410
    phone.sign_in(EMAIL)
    keep(desk, phone)
    # What a person who has signed in does.
    assert desk.put("/v1/me/preferences", {"keep_recent": "on"}).status_code == 200
    kept = data(desk.post("/v1/me/searches", {"spec": spec}))
    assert desk.post("/v1/me/recent", {"spec": spec}).status_code == 200
    for path in ("/v1/me", "/v1/me/searches", "/v1/me/recent", "/v1/me/sessions"):
        assert desk.get(path).status_code == 200
    exported = data(desk.get("/v1/me/export"))
    used.update(each["session_id"] for each in exported["sessions"])
    used.update([kept["search_id"], kept["name"]])
    assert code(desk.delete("/v1/me/searches", {"search_id": "a" * 22}))[0] == 404
    assert desk.delete("/v1/me/searches", {"search_id": kept["search_id"]}).status_code == 200
    # Who is not the website, who is not signed in, and what no route takes.
    assert code(stranger.ask("GET", "/v1/me", without=("x-burro-website",)))[0] == 403
    assert code(stranger.get("/v1/me"))[0] == 401
    assert code(desk.get(f"/v1/me?email={EMAIL}"))[0] == 422
    # One client asks too often.
    for number in range(11):
        stranger.post("/v1/auth/link", {"email": f"q{number}.{CANARY}@example.org"})
    # Signing out of one, and of every one. Then the account is deleted.
    other = exported["sessions"][0]["session_id"]
    assert phone.delete("/v1/auth/session").status_code == 200
    desk.sign_in(EMAIL)
    keep(desk)
    assert desk.delete("/v1/me/sessions", {"session_id": other}).status_code in (200, 404)
    assert desk.delete("/v1/me").status_code == 200
    used.update(row[0] for row in on.rows("SELECT id FROM accounts"))
    used.update(
        each for row in on.rows("SELECT token_hash, binding_hash FROM login_tokens") for each in row
    )
    return {each for each in used if each}


def test_no_line_holds_an_address_a_token_a_session_an_account_a_client_or_a_spec(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    post = Post()
    on = turned_on(tmp_path, post=post)
    ids_before = {row[0] for row in on.rows("SELECT id FROM accounts")}

    with heard(on) as seen:
        used = a_whole_life(on, post)
        lines, records = ours(seen), [repr(record.__dict__) for record in seen.records]
    out, err = capsys.readouterr()

    assert len(used) > 25 and not ids_before
    written = "\n".join([json.dumps(lines), *records, out, err])
    # Not one of those that were used...
    for secret in sorted(used):
        assert secret not in written, secret[:6]
    assert CANARY not in written.casefold() and "example.org" not in written
    # ...and nothing in the shape of one, in any line the service wrote.
    said = json.dumps(lines)
    for what, shape in IN_THE_SHAPE_OF.items():
        assert shape.search(said) is None, (what, shape.search(said))
    assert len(seen.events("request")) > 40 and len(seen.events("account")) > 20


def test_every_word_of_the_two_lists_that_a_person_can_bring_about_is_said(tmp_path: Path):
    post = Post()
    on = turned_on(tmp_path, post=post)

    with heard(on) as seen:
        a_whole_life(on, post)
        said = happened(seen)

    assert {event for event, _ in said} == {event.value for event in Event}
    assert {outcome for _, outcome in said} == {outcome.value for outcome in Outcome}
    assert set(said) == {
        ("link_requested", "ok"),
        ("link_requested", "refused"),
        ("link_requested", "unavailable"),
        ("link_sent", "ok"),
        ("link_send_failed", "unavailable"),
        ("link_send_failed", "refused"),
        ("link_rejected", "refused"),
        ("link_rejected", "used"),
        ("link_rejected", "expired"),
        ("link_used", "ok"),
        ("session_created", "ok"),
        ("session_revoked", "ok"),
        ("rate_limited", "limited"),
        ("account_deleted", "ok"),
    }


def test_a_line_of_accounts_holds_what_happened_and_how_it_ended_and_no_more(tmp_path: Path):
    post = Post()
    on = turned_on(tmp_path, post=post)

    with heard(on) as seen:
        a_whole_life(on, post)
        lines = seen.lines()

    assert {line["event"] for line in lines} - {"library"} == {"request", "account"}
    for line in seen.events("account"):
        assert set(line) == ACCOUNT_LINE and line["level"] == "info"
        assert line["happened"] in {event.value for event in Event}
        assert line["outcome"] in {outcome.value for outcome in Outcome}
    routes = set[str]()
    for line in seen.events("request"):
        assert set(line) <= REQUEST_LINE
        routes.add(line["route"])
    # The template of the route, and never what was asked for.
    assert routes == {
        "/v1/auth/link",
        "/v1/auth/link/whose",
        "/v1/auth/session",
        "/v1/me",
        "/v1/me/export",
        "/v1/me/preferences",
        "/v1/me/recent",
        "/v1/me/searches",
        "/v1/me/sessions",
    }
    # A line of accounts is of the request that brought it about.
    requests = {line["request_id"] for line in seen.events("request")}
    assert {line["request_id"] for line in seen.events("account")} <= requests


def test_the_log_gained_two_fields_and_each_is_a_word_of_a_closed_list():
    assert {"happened", "outcome"} <= logs.LOGGABLE
    for never in (
        "email",
        "address",
        "token",
        "session",
        "session_id",
        "account",
        "account_id",
        "client",
        "ip",
        "cookie",
        "origin",
        "user_agent",
        "browser",
        "search_id",
        "spec",
    ):
        assert never not in logs.LOGGABLE, never
        with pytest.raises(ValueError, match=f"not loggable: {never}"):
            logs.event("account", **{never: EMAIL})
    assert [event.value for event in Event] == [
        "link_requested",
        "link_sent",
        "link_send_failed",
        "link_used",
        "link_rejected",
        "session_created",
        "session_revoked",
        "rate_limited",
        "account_deleted",
    ]
    assert [outcome.value for outcome in Outcome] == [
        "ok",
        "refused",
        "expired",
        "used",
        "limited",
        "unavailable",
    ]


def test_what_is_refused_at_the_gate_is_logged_as_any_refusal_is(tmp_path: Path):
    on = turned_on(tmp_path)

    with heard(on) as seen:
        stranger = Browser(on)
        stranger.ask("POST", "/v1/auth/link", {"email": EMAIL}, without=("x-burro-website",))
        stranger.ask(
            "POST", "/v1/auth/link", {"email": EMAIL}, changed={"origin": "https://x.example"}
        )
        lines = ours(seen)

    # The line of the request, with the code of the refusal. Nothing says who was refused.
    assert [(line["route"], line["status"], line["error_code"]) for line in lines] == [
        ("/v1/auth/link", 403, "not_the_website"),
        ("/v1/auth/link", 403, "not_the_website"),
    ]
    assert lines[0] == lines[1] or {
        name for name in lines[0] if lines[0][name] != lines[1][name]
    } == {"latency_ms"}


def test_a_failure_in_accounts_is_logged_by_its_type_and_answered_in_fixed_words(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    class Broken(Post):
        def send(self, to: str, link: str) -> None:
            raise RuntimeError(f"could not send {link} to {to}")

    on = turned_on(tmp_path, post=Broken())

    with heard(on) as seen:
        answered = Browser(on).post("/v1/auth/link", {"email": EMAIL})
        after = Browser(on, address="198.51.100.66").post("/v1/auth/link", {"email": OTHER})
        lines, records = seen.lines(), [repr(record.__dict__) for record in seen.records]
    out, err = capsys.readouterr()

    # The answer was given before the letter was tried, so it is the one every address
    # is given. Whoever asks next is told, in fixed words.
    assert answered.status_code == 202 and code(after) == (503, "sign_in_unavailable")
    assert after.json()["error"] == {
        "code": "sign_in_unavailable",
        "message": "Burro cannot send sign-in emails at the moment, so please try again later.",
        "fields": [],
    }
    for each in (answered, after):
        assert each.headers["cache-control"] == "no-store"
        assert each.headers["x-content-type-options"] == "nosniff"
    [failure] = [line for line in lines if line["event"] == "failure"]
    assert (failure["exception"], failure["route"]) == ("RuntimeError", "/v1/auth/link")
    assert any(frame.endswith(":send") for frame in failure["frames"])
    assert ("link_send_failed", "unavailable") in happened(seen)
    # The link that was never sent opens nothing.
    assert [used is not None for (used,) in on.rows("SELECT used_at FROM login_tokens")] == [True]
    written = "\n".join([json.dumps(lines), *records, out, err, answered.text, after.text])
    assert CANARY not in written.casefold() and "sign-in/confirm" not in written


def test_what_is_kept_of_what_happened_is_of_the_two_lists_and_of_an_account(tmp_path: Path):
    post = Post()
    on = turned_on(tmp_path, post=post)
    Browser(on).sign_in(OTHER)

    with heard(on):
        a_whole_life(on, post)

    kept = on.rows(
        "SELECT a.email, e.event, e.outcome FROM audit_events e "
        "JOIN accounts a ON a.id = e.account_id ORDER BY e.id"
    )
    # The account that was deleted took what happened to it along. What is left is of
    # the account that is left, and every row is of an account.
    assert kept == [(OTHER, "link_used", "ok"), (OTHER, "session_created", "ok")]
    assert on.rows("SELECT count(*) FROM audit_events WHERE account_id IS NULL") == [(0,)]
