"""A session and its cookie: how long it lasts, how it ends, and what is kept of it."""

import hashlib
import re
from pathlib import Path

import pytest
from burro_api.accounts.service import family
from burro_api.accounts.wire import Browser as Family

from ..support import CANARY
from .support import AT_HOME, FIREFOX, SAFARI, Browser, On, code, data, turned_on

EMAIL = "marmalade.quokka@example.org"
OTHER = "pumpernickel.vole@example.org"
SESSION = "__Host-burro_session"
NOT_SIGNED_IN = (401, "not_signed_in")
CHROME = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)
EDGE = f"{CHROME} Edg/140.0.0.0"


def sha256(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def signed_in(on: On, email: str = EMAIL, **how: str) -> Browser:
    browser = Browser(on, **how)
    browser.sign_in(email)
    return browser


def holding(on: On, session: str) -> Browser:
    """A browser that holds a session it was not given."""
    browser = Browser(on)
    browser.cookies[SESSION] = session
    return browser


def ends_at(on: On) -> list[str]:
    return [ends for (ends,) in on.rows("SELECT ends_at FROM sessions ORDER BY made_at")]


# Who is signed in.


def test_a_browser_is_told_whether_it_is_signed_in_and_as_whom(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)
    assert data(browser.get("/v1/auth/session")) == {"signed_in": False, "email": None}
    assert code(browser.get("/v1/me")) == NOT_SIGNED_IN

    browser.sign_in(EMAIL)

    assert data(browser.get("/v1/auth/session")) == {"signed_in": True, "email": EMAIL}
    assert data(browser.get("/v1/me")) == {
        "email": EMAIL,
        "made_at": "2026-09-23T12:00:00Z",
        "preferences": {"keep_recent": "off"},
        "fresh": True,
    }


@pytest.mark.parametrize(
    "held",
    [
        "s" * 43,
        "",
        "s" * 42,
        "s" * 44,
        "deleted",
        "null",
        f"{CANARY}",
        "' OR 1=1 --",
        "s" * 42 + "\N{LATIN SMALL LETTER E WITH ACUTE}",
    ],
)
def test_a_session_that_burro_did_not_make_opens_nothing(tmp_path: Path, held: str):
    on = turned_on(tmp_path)
    signed_in(on)

    stranger = holding(on, held.encode().decode("latin-1"))

    assert data(stranger.get("/v1/auth/session")) == {"signed_in": False, "email": None}
    for path in ("/v1/me", "/v1/me/searches", "/v1/me/sessions", "/v1/me/export"):
        refused = stranger.get(path)
        assert code(refused) == NOT_SIGNED_IN
        assert CANARY not in refused.text and EMAIL not in refused.text


def test_a_session_is_found_by_its_own_cookie_and_no_other(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    session = browser.cookies[SESSION]

    for name in ("burro_session", "__Secure-burro_session", "session", "__Host-burro_link"):
        beside = Browser(on)
        beside.cookies[name] = session
        assert code(beside.get("/v1/me")) == NOT_SIGNED_IN, name
    header = Browser(on)
    assert code(header.get("/v1/me", {"authorization": f"Bearer {session}"})) == NOT_SIGNED_IN


def test_the_hash_of_a_session_opens_nothing(tmp_path: Path):
    # Whoever reads the file of accounts reads hashes, and can use none of them.
    on = turned_on(tmp_path)
    signed_in(on)
    [(kept,)] = on.rows("SELECT token_hash FROM sessions")
    [(named,)] = on.rows("SELECT public_id FROM sessions")

    for held in (kept, kept[:43], named):
        assert code(holding(on, held).get("/v1/me")) == NOT_SIGNED_IN


# How long it lasts.


def test_a_session_lasts_thirty_days(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    assert ends_at(on) == ["2026-10-23T12:00:00Z"]
    session = browser.cookies[SESSION]

    on.later(days=29, hours=23)
    # Not used in all that time, so never put forward.
    assert on.rows("SELECT seen_at FROM sessions") == [("2026-09-23T12:00:00Z",)]
    on.later(hours=1)

    assert code(holding(on, session).get("/v1/me")) == NOT_SIGNED_IN


def test_a_session_is_put_forward_when_it_is_used_once_a_day_at_the_most(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)

    for hours in (1, 5, 17):
        on.later(hours=hours)
        assert browser.get("/v1/me").status_code == 200
        # Within the day it is used as it is, and nothing is written.
        assert ends_at(on) == ["2026-10-23T12:00:00Z"] and not browser.given

    on.later(hours=1)
    answered = browser.get("/v1/me")

    # A day on, to the second. It is put forward to thirty days from now, and the
    # cookie is given again to last as long.
    assert answered.status_code == 200
    assert ends_at(on) == ["2026-10-24T12:00:00Z"]
    assert on.rows("SELECT seen_at FROM sessions") == [("2026-09-24T12:00:00Z",)]
    [given] = browser.given
    assert given.startswith(f"{SESSION}={browser.cookies[SESSION]};")
    assert "Max-Age=2592000" in given and "Secure" in given and "HttpOnly" in given


def test_the_route_that_says_who_is_signed_in_puts_a_session_forward_too(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    on.later(days=2)

    assert data(browser.get("/v1/auth/session"))["signed_in"] is True

    assert ends_at(on) == ["2026-10-25T12:00:00Z"] and len(browser.given) == 1


def test_a_session_never_lasts_past_ninety_days_from_when_it_was_made(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)

    # Used every week, and put forward every time.
    for _ in range(12):
        on.later(days=7)
        assert browser.get("/v1/me").status_code == 200

    # Eighty-four days on. What is left is six days, and not thirty.
    assert ends_at(on) == ["2026-12-22T12:00:00Z"]
    [given] = browser.given
    assert f"Max-Age={6 * 24 * 60 * 60}" in given
    on.later(days=5, hours=23)
    assert browser.get("/v1/me").status_code == 200
    on.later(hours=1)
    assert code(browser.get("/v1/me")) == NOT_SIGNED_IN
    assert ends_at(on) == ["2026-12-22T12:00:00Z"]


# Signing out.


def test_signing_out_revokes_the_session_at_the_service(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    session = browser.cookies[SESSION]
    on.later(minutes=5)

    answered = browser.delete("/v1/auth/session")

    assert data(answered) == {"signed_in": False, "email": None}
    assert not browser.cookies
    [given] = browser.given
    assert given.startswith(f'{SESSION}="";') and "Max-Age=0" in given
    assert on.rows("SELECT revoked_at FROM sessions") == [("2026-09-23T12:05:00Z",)]
    # A cookie that was kept opens nothing after.
    kept = holding(on, session)
    assert code(kept.get("/v1/me")) == NOT_SIGNED_IN
    assert data(kept.get("/v1/auth/session")) == {"signed_in": False, "email": None}


def test_signing_out_with_no_session_is_answered_and_leaves_a_browser_with_none(tmp_path: Path):
    on = turned_on(tmp_path)
    nobody = holding(on, "s" * 43)

    answered = nobody.delete("/v1/auth/session")

    assert data(answered) == {"signed_in": False, "email": None}
    assert not nobody.cookies and "Max-Age=0" in nobody.given[0]


def test_where_a_person_is_signed_in_is_listed_and_the_browser_that_asks_is_marked(
    tmp_path: Path,
):
    on = turned_on(tmp_path)
    desk = signed_in(on, agent=FIREFOX)
    on.later(minutes=1)
    phone = signed_in(on, agent=SAFARI, address="203.0.113.9")
    signed_in(on, OTHER, address="203.0.113.10")

    found = data(phone.get("/v1/me/sessions"))

    assert found["signed_in"] is True
    assert [
        (each["browser"], each["current"], each["made_at"], each["ends_at"], each["revoked"])
        for each in found["sessions"]
    ] == [
        ("safari", True, "2026-09-23T12:01:00Z", "2026-10-23T12:01:00Z", False),
        ("firefox", False, "2026-09-23T12:00:00Z", "2026-10-23T12:00:00Z", False),
    ]
    # What names a session is no session, and nothing of one.
    for each in found["sessions"]:
        assert re.fullmatch(r"[A-Za-z0-9_-]{22}", each["session_id"])
        assert set(each) == {
            "session_id",
            "browser",
            "made_at",
            "seen_at",
            "ends_at",
            "current",
            "revoked",
        }
    sessions = {desk.cookies[SESSION], phone.cookies[SESSION]}
    served = phone.get("/v1/me/sessions").text
    assert not [each for each in sessions if each in served or sha256(each) in served]


def test_a_person_signs_out_of_one_browser_and_stays_signed_in_with_the_rest(tmp_path: Path):
    on = turned_on(tmp_path)
    desk = signed_in(on, agent=FIREFOX)
    on.later(minutes=1)
    phone = signed_in(on, agent=SAFARI)
    [there, elsewhere] = data(phone.get("/v1/me/sessions"))["sessions"]
    assert there["current"] and not elsewhere["current"]

    left = data(phone.delete("/v1/me/sessions", {"session_id": elsewhere["session_id"]}))

    assert left["signed_in"] is True and [e["browser"] for e in left["sessions"]] == ["safari"]
    assert phone.cookies and code(desk.get("/v1/me")) == NOT_SIGNED_IN
    assert phone.get("/v1/me").status_code == 200


def test_signing_out_everywhere_revokes_every_session_of_the_account_and_no_other(
    tmp_path: Path,
):
    on = turned_on(tmp_path)
    desk, phone = signed_in(on, agent=FIREFOX), signed_in(on, agent=SAFARI)
    theirs = signed_in(on, OTHER, address="203.0.113.10")
    on.later(minutes=1)

    left = data(phone.delete("/v1/me/sessions", {"everywhere": True}))

    assert left == {"sessions": [], "signed_in": False}
    assert not phone.cookies and "Max-Age=0" in phone.given[0]
    for browser in (desk, phone):
        assert code(holding(on, browser.cookies.get(SESSION, "s" * 43)).get("/v1/me")) == (
            NOT_SIGNED_IN
        )
    assert code(desk.get("/v1/me")) == NOT_SIGNED_IN
    assert data(theirs.get("/v1/me"))["email"] == OTHER
    revoked = dict(
        on.rows(
            "SELECT a.email, count(s.revoked_at) FROM sessions s "
            "JOIN accounts a ON a.id = s.account_id GROUP BY a.email"
        )
    )
    assert revoked == {EMAIL: 2, OTHER: 0}


@pytest.mark.parametrize(
    "sent",
    [
        {},
        {"everywhere": False},
        {"session_id": None},
        {"session_id": "a" * 22, "everywhere": True},
    ],
)
def test_signing_out_names_one_session_or_every_one_and_never_both_or_neither(
    tmp_path: Path, sent: dict[str, object]
):
    on = turned_on(tmp_path)
    browser = signed_in(on)

    refused = browser.delete("/v1/me/sessions", sent)

    assert code(refused) == (422, "invalid_request")
    assert browser.get("/v1/me").status_code == 200


def test_a_session_of_somebody_elses_is_not_found_and_is_not_ended(tmp_path: Path):
    on = turned_on(tmp_path)
    mine, theirs = signed_in(on), signed_in(on, OTHER, address="203.0.113.10")
    [there] = data(theirs.get("/v1/me/sessions"))["sessions"]

    refused = mine.delete("/v1/me/sessions", {"session_id": there["session_id"]})

    assert code(refused) == (404, "session_not_found")
    assert theirs.get("/v1/me").status_code == 200
    assert on.rows("SELECT count(*) FROM sessions WHERE revoked_at IS NOT NULL") == [(0,)]


def test_sessions_that_ended_long_ago_are_let_go_of_as_a_person_signs_in(tmp_path: Path):
    on = turned_on(tmp_path)
    old = signed_in(on)
    old.delete("/v1/auth/session")

    on.later(days=31)
    signed_in(on, OTHER, address="203.0.113.10")

    # Revoked a month and more ago, so it is held no longer.
    assert [
        email
        for (email,) in on.rows(
            "SELECT a.email FROM sessions s JOIN accounts a ON a.id = s.account_id"
        )
    ] == [OTHER]


def test_a_session_that_ended_long_ago_is_let_go_of_as_somebody_else_comes_back(tmp_path: Path):
    on = turned_on(tmp_path)
    stays = signed_in(on, OTHER, address="203.0.113.10")
    left = signed_in(on)
    whose = "SELECT a.email, s.public_id FROM sessions s JOIN accounts a ON a.id = s.account_id"
    named = dict(on.rows(whose))[EMAIL]
    left.delete("/v1/auth/session")

    # Nobody signs in and nobody asks for a link. The one who stays uses Burro each day.
    for _ in range(31):
        on.later(days=1)
        assert data(stays.get("/v1/auth/session"))["signed_in"] is True

    # Revoked a month and more ago, so it is held no longer: in no row, and in no byte.
    assert [email for email, _ in on.rows(whose)] == [OTHER]
    assert named.encode() not in on.written()


def test_what_happened_long_ago_is_let_go_of_as_somebody_else_comes_back(tmp_path: Path):
    on = turned_on(tmp_path)
    left = signed_in(on)
    left.delete("/v1/auth/session")
    on.later(days=70)
    stays = signed_in(on, OTHER, address="203.0.113.10")
    whose = "SELECT DISTINCT a.email FROM audit_events e JOIN accounts a ON a.id = e.account_id"
    assert sorted(on.rows(whose)) == [(EMAIL,), (OTHER,)]

    # Nothing more happens to any account. The one who stays uses Burro each day.
    for _ in range(21):
        on.later(days=1)
        assert data(stays.get("/v1/auth/session"))["signed_in"] is True

    # Ninety days and more on, what happened to the account of the one who left is held no longer.
    assert on.rows(whose) == [(OTHER,)]


# What is kept of a browser.


@pytest.mark.parametrize(
    ("agent", "kept"),
    [
        (FIREFOX, Family.FIREFOX),
        (SAFARI, Family.SAFARI),
        (CHROME, Family.CHROME),
        (EDGE, Family.EDGE),
        ("curl/8.7.1", Family.OTHER),
        ("", Family.OTHER),
        (f"{CANARY}/1.0", Family.OTHER),
    ],
)
def test_what_is_kept_of_a_browser_is_its_family_and_nothing_else(agent: str, kept: Family):
    assert family(agent) is kept


def test_what_a_browser_says_it_is_is_written_nowhere(tmp_path: Path):
    on = turned_on(tmp_path)

    signed_in(on, agent=f"{FIREFOX} {CANARY}/7.4")

    assert on.rows("SELECT browser FROM sessions") == [("firefox",)]
    assert CANARY.encode() not in on.written() and b"Gecko" not in on.written()


# In development.


def test_in_development_the_cookies_bear_their_plain_names_and_are_not_secure(tmp_path: Path):
    on = turned_on(tmp_path, site=AT_HOME, development=True)
    browser = Browser(on, site=AT_HOME)

    browser.ask_for_link(EMAIL)
    [bound] = browser.given
    token = on.post.token()
    browser.post("/v1/auth/session", {"token": token, "adult": True})

    # A browser need take neither the prefix nor `Secure` from a page in the clear.
    assert bound.startswith("burro_link=") and "Secure" not in bound and "HttpOnly" in bound
    assert list(browser.cookies) == ["burro_session"]
    [given] = [each for each in browser.given if each.startswith("burro_session=")]
    assert "Secure" not in given and "HttpOnly" in given and "SameSite=lax" in given
    assert on.post.sent[0][1].startswith(f"{AT_HOME}/sign-in/confirm#t=")
    assert data(browser.get("/v1/me"))["email"] == EMAIL


def test_out_of_development_a_cookie_under_a_plain_name_opens_nothing(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = signed_in(on)
    plain = Browser(on)
    plain.cookies["burro_session"] = browser.cookies[SESSION]

    assert code(plain.get("/v1/me")) == NOT_SIGNED_IN
