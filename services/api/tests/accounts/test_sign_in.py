"""Signing in, by a link sent by email: every rule of it, from asking to the session.

Every address here is made up, and no letter is sent: a stand-in keeps each one.
"""

import hashlib
import hmac
import json
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from typing import Any

import anyio
import pytest
from burro_api.accounts import store as layer
from burro_api.accounts.sender import SendFailed
from burro_api.accounts.service import open_accounts

from ..support import CANARY, FixedClock
from .support import (
    AFTER_THE_HASH,
    SAFARI,
    SECRET,
    SITE,
    Browser,
    On,
    Post,
    code,
    data,
    settings,
    turned_on,
)

EMAIL = "marmalade.quokka@example.org"
OTHER = "pumpernickel.vole@example.org"
LINK_ASKED = {"lasts_minutes": 15}


def sha256(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def attributes(given: str) -> tuple[str, str, set[str]]:
    """The name of a cookie, its value, and what is said of it, in lower case."""
    first, *rest = (part.strip() for part in given.split(";"))
    name, _, value = first.partition("=")
    return name, value, {said.lower() for said in rest}


# Asking for a link.


def test_asking_for_a_link_sends_one_to_the_address_made_regular(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)

    answered = browser.post("/v1/auth/link", {"email": "  Marmalade.Quokka@Example.ORG "})

    assert answered.status_code == 202 and data(answered) == LINK_ASKED
    [(to, link)] = on.post.sent
    assert to == EMAIL
    # The token stands after the `#`, which a browser sends to no server.
    assert re.fullmatch(re.escape(f"{SITE}{AFTER_THE_HASH}") + r"[A-Za-z0-9_-]{43}", link)
    assert "?" not in link


def test_what_is_kept_of_a_link_is_the_hash_of_its_token_and_never_the_token(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)

    token = browser.ask_for_link(EMAIL)

    [row] = on.rows(
        "SELECT token_hash, email, made_at, ends_at, used_at, binding_hash FROM login_tokens"
    )
    [binding] = browser.cookies.values()
    assert row == (
        sha256(token),
        EMAIL,
        "2026-09-23T12:00:00Z",
        # It ends after a quarter of an hour.
        "2026-09-23T12:15:00Z",
        None,
        sha256(binding),
    )
    written = on.written()
    assert token.encode() not in written and binding.encode() not in written


def test_asking_binds_the_link_to_the_browser_that_asked(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)

    browser.ask_for_link(EMAIL)

    [given] = browser.given
    name, value, said = attributes(given)
    assert name == "__Host-burro_link" and re.fullmatch(r"[A-Za-z0-9_-]{43}", value)
    # It lasts as long as the link, and no script of a page can read it.
    assert said == {"max-age=900", "path=/", "secure", "httponly", "samesite=lax"}


@pytest.mark.parametrize(
    "typed",
    ["", " ", "marmalade", "marmalade@", "@example.org", "a b@example.org", f"{CANARY}@x"],
)
def test_what_is_not_an_address_is_said_to_be_none_and_is_never_repeated(
    tmp_path: Path, typed: str
):
    on = turned_on(tmp_path)

    answered = Browser(on).post("/v1/auth/link", {"email": typed})

    assert code(answered) == (422, "invalid_email")
    assert answered.json()["error"]["message"] == (
        "That does not look like an email address, so please check it and try again."
    )
    assert CANARY not in answered.text and not on.post.sent


@pytest.mark.parametrize(
    "sent",
    [
        {},
        {"email": None},
        {"email": 7},
        {"email": ["a@example.org"]},
        {"email": "a" * 255},
        {"email": EMAIL, "adult": True},
        {"address": EMAIL},
    ],
)
def test_a_body_that_is_not_what_the_route_takes_is_refused(tmp_path: Path, sent: Any):
    on = turned_on(tmp_path)

    answered = Browser(on).post("/v1/auth/link", sent)

    assert answered.status_code == 422 and not on.post.sent
    assert answered.json()["error"]["code"] in ("invalid_email", "invalid_request")
    assert EMAIL not in answered.text


# A known address and an unknown one.


def known_and_unknown(on: On) -> None:
    """Give the first address an account, and the second none."""
    Browser(on, address="203.0.113.200").sign_in(EMAIL)
    on.later(hours=2)
    assert on.rows("SELECT email FROM accounts") == [(EMAIL,)]


def test_a_known_address_and_an_unknown_one_are_answered_the_same(tmp_path: Path):
    on = turned_on(tmp_path)
    known_and_unknown(on)

    def answer(email: str) -> tuple[int, str, dict[str, str]]:
        browser = Browser(on)
        answered = browser.post("/v1/auth/link", {"email": email})
        [given] = browser.given
        name, value, said = attributes(given)
        headers = {
            name: said
            for name, said in answered.headers.items()
            if name not in ("x-request-id", "set-cookie")
        }
        # The cookie is the same but for its value, which is random for everybody.
        headers["set-cookie"] = f"{name} {len(value)} {sorted(said)}"
        return answered.status_code, answered.text, headers

    assert answer(EMAIL) == answer(OTHER)
    assert [to for to, _ in on.post.sent[-2:]] == [EMAIL, OTHER]


class Listening:
    """Stands between the layer and the file, and keeps every statement that is run."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self.run: list[str] = []

    def execute(self, statement: str, *values: Any) -> Any:
        self.run.append(statement)
        return self._connection.execute(statement, *values)

    def close(self) -> None:
        self._connection.close()


def test_a_known_address_and_an_unknown_one_are_given_the_same_work(tmp_path: Path):
    on = turned_on(tmp_path)
    known_and_unknown(on)
    store: Any = on.accounts._store  # pyright: ignore[reportPrivateUsage]
    listening = Listening(store._connection)
    store._connection = listening

    def work(email: str) -> list[str]:
        listening.run.clear()
        assert Browser(on).post("/v1/auth/link", {"email": email}).status_code == 202
        return list(listening.run)

    known, unknown = work(EMAIL), work(OTHER)

    # The same statements in the same order, and none of them looks for an account.
    assert known == unknown and len(known) >= 5
    assert not [statement for statement in known if " accounts " in f"{statement} "]


# How far apart the two middle times may be, as a share of the shorter, to be alike.
ALIKE = 0.2
ROUNDS = 120
TIMES_OVER = 3


class Measured:
    """How long asking for a link takes, for a known address and for an unknown one.

    Each round asks for both, in an order that turns about, so that what else the
    machine is doing falls on both alike. What is compared is the middle time of each,
    which a few slow rounds do not move.
    """

    def __init__(self, on: On) -> None:
        self.on = on
        self.found: list[tuple[float, float]] = []

    def _took(self, email: str, number: int) -> float:
        # A client of its own, so that no limit on a client is what is measured.
        browser = Browser(self.on, address=f"198.51.{number // 250}.{number % 250 + 1}")
        began = time.perf_counter()
        answered = browser.post("/v1/auth/link", {"email": email})
        ended = time.perf_counter()
        assert answered.status_code == 202
        return ended - began

    def once(self, rounds: int) -> tuple[float, float]:
        known: list[float] = []
        unknown: list[float] = []
        for number in range(rounds):
            # Three hours on, so that no address is over its limit of a quarter of an
            # hour or of a day, and each is sent a letter every time.
            self.on.later(hours=3)
            first, second = (EMAIL, OTHER) if number % 2 else (OTHER, EMAIL)
            times = {
                first: self._took(first, 2 * number),
                second: self._took(second, 2 * number + 1),
            }
            known.append(times[EMAIL])
            unknown.append(times[OTHER])
        return statistics.median(known), statistics.median(unknown)

    def alike(self, rounds: int = ROUNDS, times_over: int = TIMES_OVER) -> bool:
        """Whether the two are answered in like time, in any of so many measurements.

        A busy machine can spoil a measurement. It cannot make two times alike that
        are not, so one measurement that holds is enough, and one that does not is
        made again.
        """
        self.once(10)
        for _ in range(times_over):
            known, unknown = self.once(rounds)
            self.found.append((known, unknown))
            if abs(known - unknown) <= ALIKE * min(known, unknown):
                return True
        return False


def test_a_known_address_and_an_unknown_one_are_answered_in_like_time(tmp_path: Path):
    on = turned_on(tmp_path, links_per_hour=10_000)
    known_and_unknown(on)
    measured = Measured(on)

    assert measured.alike(), measured.found

    sent = [to for to, _ in on.post.sent]
    assert sent.count(EMAIL) - 1 == sent.count(OTHER) >= ROUNDS


def test_the_measurement_tells_two_times_apart_that_are_not_alike(tmp_path: Path):
    # A measurement that could not fail would hold nothing. So the same one is made of
    # a service that takes longer over the address it knows, and it must say so.
    class Slow(Post):
        longer = 0.0

        def send(self, to: str, link: str) -> None:
            if to == EMAIL:
                time.sleep(self.longer)
            super().send(to, link)

    slow = Slow()
    on = turned_on(tmp_path, post=slow, links_per_hour=10_000)
    known_and_unknown(on)
    measured = Measured(on)
    # As long again as an answer takes on this machine, as busy as it now is, and four
    # thousandths of a second at the least: so the two are apart however slow it runs.
    slow.longer = max(0.004, *measured.once(10))

    assert not measured.alike(rounds=40), measured.found
    assert all(known > unknown for known, unknown in measured.found)


# An address that is sent a letter, and one that is over its limit and is sent none.


class Noting(Post):
    """A stand-in for whoever sends, which notes when it is handed a letter."""

    def __init__(self, takes: float = 0.0) -> None:
        super().__init__()
        self.happened: list[str] = []
        self.takes = takes

    def send(self, to: str, link: str) -> None:
        self.happened.append("the letter is sent")
        time.sleep(self.takes)
        super().send(to, link)


def asked_of_the_service_itself(on: On, post: Noting, email: str, address: str) -> float:
    """Ask for a link with no test client between, and note what happens in its order.

    The test client gives an answer back once everything that follows it is done. The
    service is asked as a server asks it, so that the moment the answer is given is seen.
    It gives back how long the answer took, from the asking to the last of it.
    """
    browser = Browser(on, address=address)
    sent = [{"type": "http.request", "body": json.dumps({"email": email}).encode()}]
    headers = [(name.encode(), said.encode()) for name, said in browser.headers("POST").items()]
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/v1/auth/link",
        "raw_path": b"/v1/auth/link",
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("203.0.113.1", 50_000),
        "server": ("burro.example", 443),
    }
    took: list[float] = []

    async def asked() -> None:
        began = time.perf_counter()

        async def receive() -> dict[str, Any]:
            return sent.pop(0) if sent else {"type": "http.disconnect"}

        async def send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                post.happened.append(f"answered {message['status']}")
            elif not message.get("more_body", False):
                took.append(time.perf_counter() - began)
                post.happened.append("the answer is given whole")

        await on.client.app(scope, receive, send)  # pyright: ignore[reportArgumentType]

    anyio.run(asked)
    return took[0]


def test_a_letter_is_sent_once_the_answer_has_been_given(tmp_path: Path):
    post = Noting()
    on = turned_on(tmp_path, post=post)

    asked_of_the_service_itself(on, post, EMAIL, "198.51.100.1")

    # So an answer never waits on whoever sends, and says nothing by how long it takes.
    assert post.happened == ["answered 202", "the answer is given whole", "the letter is sent"]
    assert [to for to, _ in post.sent] == [EMAIL]


def test_an_address_over_its_limit_is_answered_as_soon_as_one_that_is_sent_a_letter(
    tmp_path: Path,
):
    # Whoever sends takes a tenth of a second.
    post = Noting(takes=0.1)
    on = turned_on(tmp_path, post=post)

    for number in range(5):
        asked_of_the_service_itself(on, post, EMAIL, f"198.51.100.{number + 1}")

    # Three were sent a letter, and two were over the limit and were sent none. Each answer
    # was given whole before whoever sends was handed anything, so not one waited for a
    # letter, and none says which it was by how long it took. It is held by the order of
    # what happened and by no clock: a machine that is busy answers late, whoever asks.
    given = ["answered 202", "the answer is given whole"]
    assert post.happened == [*[*given, "the letter is sent"] * 3, *given * 2]
    assert len(post.sent) == 3


def test_an_address_over_its_limit_is_given_the_same_work_as_any_other(tmp_path: Path):
    on = turned_on(tmp_path)
    store: Any = on.accounts._store  # pyright: ignore[reportPrivateUsage]
    listening = Listening(store._connection)
    store._connection = listening

    def work(number: int) -> list[str]:
        listening.run.clear()
        browser = Browser(on, address=f"198.51.100.{number + 1}")
        assert browser.post("/v1/auth/link", {"email": EMAIL}).status_code == 202
        return list(listening.run)

    sent, _, _, over = (work(number) for number in range(4))

    # The fourth is over the limit. It writes what the first wrote, and then takes it
    # out again: so the file is written to as it is for any address, and keeps nothing.
    assert len(on.post.sent) == 3 and layer.ADD_LINK in sent and layer.FORGET_LINK not in sent
    assert [statement for statement in over if statement != layer.FORGET_LINK] == sent
    assert over.count(layer.FORGET_LINK) == 1
    assert over.index(layer.FORGET_LINK) == over.index(layer.ADD_LINK) + 1
    assert len(on.rows("SELECT * FROM login_tokens")) == 3


def test_what_is_written_for_an_address_over_its_limit_is_in_no_byte_that_is_left(
    tmp_path: Path,
):
    on = turned_on(tmp_path)
    for number in range(3):
        Browser(on, address=f"198.51.100.{number + 1}").ask_for_link(EMAIL)
    store: Any = on.accounts._store  # pyright: ignore[reportPrivateUsage]
    written: list[tuple[Any, ...]] = []

    class Keeping(Listening):
        def execute(self, statement: str, *values: Any) -> Any:
            if statement == layer.ADD_LINK:
                written.extend(values)
            return super().execute(statement, *values)

    store._connection = Keeping(store._connection)
    browser = Browser(on, address="198.51.100.9")

    assert browser.post("/v1/auth/link", {"email": EMAIL}).status_code == 202

    # The link that was written and taken out again: the hash of its token, and the hash
    # of what binds it, are in no row and in no byte.
    [(token_hash, _, _, _, _, binding_hash)] = written
    assert sha256(browser.cookies["__Host-burro_link"]) == binding_hash
    left = on.written()
    assert token_hash.encode() not in left and binding_hash.encode() not in left
    assert len(on.rows("SELECT * FROM login_tokens")) == 3


# Whose link it is.


def test_a_page_is_told_whose_link_it_is_and_asking_uses_nothing_up(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)
    before = on.held()

    asked = [browser.post("/v1/auth/link/whose", {"token": token}) for _ in range(5)]

    for answered in asked:
        assert data(answered) == {"email": EMAIL, "same_browser": True, "new_account": True}
        assert "set-cookie" not in answered.headers
    # Not a row is other than it was, so a program that opens links uses nothing up.
    assert on.held() == before
    assert data(browser.post("/v1/auth/session", {"token": token, "adult": True}))


def test_a_page_is_told_whether_signing_in_would_make_an_account(tmp_path: Path):
    on = turned_on(tmp_path)
    Browser(on).sign_in(EMAIL)
    on.later(minutes=1)
    browser = Browser(on)

    again = browser.ask_for_link(EMAIL)

    found = data(browser.post("/v1/auth/link/whose", {"token": again}))
    assert found == {"email": EMAIL, "same_browser": True, "new_account": False}


@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
@pytest.mark.parametrize(
    "path", ["/v1/auth/link/whose", "/v1/auth/session", "/v1/auth/link", "/sign-in/confirm"]
)
def test_a_get_uses_no_token_up(tmp_path: Path, method: str, path: str):
    on = turned_on(tmp_path)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)
    before = on.held()

    # As a program that opens every link of a mailbox might ask, with the token
    # wherever it could be put.
    for asked in (path, f"{path}?t={token}", f"{path}?token={token}", f"{path}/{token}"):
        answered = browser.ask(method, asked, changed={"authorization": f"Bearer {token}"})
        assert answered.status_code in (200, 204, 404, 405, 422), asked
        assert token not in answered.text

    assert on.held() == before
    assert data(browser.post("/v1/auth/session", {"token": token, "adult": True}))


# Making the session.


def test_the_first_sign_in_makes_the_account_once_the_person_says_they_are_an_adult(
    tmp_path: Path,
):
    on = turned_on(tmp_path)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)

    for unsaid in ({"token": token}, {"token": token, "adult": False}):
        refused = browser.post("/v1/auth/session", unsaid)
        assert code(refused) == (409, "age_not_confirmed")
        assert "set-cookie" not in refused.headers
    # The link is not used up by being refused, so the person may tick and press again.
    assert not on.rows("SELECT * FROM accounts") and not on.rows("SELECT * FROM sessions")
    assert on.rows("SELECT used_at FROM login_tokens") == [(None,)]

    signed = browser.post("/v1/auth/session", {"token": token, "adult": True})

    assert data(signed) == {"email": EMAIL, "new_account": True}
    [(email, made_at, adult_at)] = on.rows("SELECT email, made_at, adult_at FROM accounts")
    assert (email, made_at, adult_at) == (EMAIL, "2026-09-23T12:00:00Z", "2026-09-23T12:00:00Z")


def test_a_person_who_has_an_account_is_not_asked_their_age_again(tmp_path: Path):
    on = turned_on(tmp_path)
    Browser(on).sign_in(EMAIL)
    on.later(minutes=1)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)

    signed = browser.post("/v1/auth/session", {"token": token})

    assert data(signed) == {"email": EMAIL, "new_account": False}
    assert len(on.rows("SELECT * FROM accounts")) == 1
    # When they said so is when they first said so.
    assert on.rows("SELECT adult_at FROM accounts") == [("2026-09-23T12:00:00Z",)]


def test_signing_in_gives_the_session_and_takes_back_what_bound_the_link(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)

    browser.sign_in(EMAIL)

    given = {name: (value, said) for name, value, said in map(attributes, browser.given)}
    session, said = given["__Host-burro_session"]
    assert re.fullmatch(r"[A-Za-z0-9_-]{43}", session)
    # Thirty days, the website's own, and no script of a page can read it.
    assert said == {"max-age=2592000", "path=/", "secure", "httponly", "samesite=lax"}
    assert not [each for each in said if each.startswith("domain")]
    taken_back, said_of_it = given["__Host-burro_link"]
    assert taken_back in ("", '""') and "max-age=0" in said_of_it
    assert list(browser.cookies) == ["__Host-burro_session"]
    # What is kept of the session is its hash, and never the session.
    assert on.rows("SELECT token_hash FROM sessions") == [(sha256(session),)]
    assert session.encode() not in on.written()


def test_a_link_works_once(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)
    assert browser.post("/v1/auth/session", {"token": token, "adult": True}).status_code == 200

    pressed = {"token": token, "adult": True, "other_browser": True}
    for again in (browser, Browser(on)):
        whose = again.post("/v1/auth/link/whose", {"token": token})
        signed = again.post("/v1/auth/session", pressed)
        for refused in (whose, signed):
            assert code(refused) == (410, "link_used")
            assert "set-cookie" not in refused.headers
    assert len(on.rows("SELECT * FROM sessions")) == 1


@pytest.mark.parametrize(("minutes", "works"), [(14, True), (15, False), (16, False), (600, False)])
def test_a_link_ends_after_a_quarter_of_an_hour(tmp_path: Path, minutes: int, works: bool):
    on = turned_on(tmp_path)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)

    on.later(minutes=minutes, seconds=59 if works else 0)
    whose = browser.post("/v1/auth/link/whose", {"token": token})
    signed = browser.post("/v1/auth/session", {"token": token, "adult": True})

    if works:
        assert whose.status_code == 200 and signed.status_code == 200
    else:
        assert code(whose) == code(signed) == (410, "link_expired")
        assert not on.rows("SELECT * FROM sessions")


def test_using_a_link_ends_every_other_that_was_asked_for_the_same_address(tmp_path: Path):
    on = turned_on(tmp_path)
    browser, elsewhere = Browser(on), Browser(on, address="203.0.113.9")
    first = browser.ask_for_link(EMAIL)
    second = browser.ask_for_link(EMAIL)
    theirs = elsewhere.ask_for_link(OTHER)

    assert browser.post("/v1/auth/session", {"token": second, "adult": True}).status_code == 200

    assert code(browser.post("/v1/auth/session", {"token": first})) == (410, "link_used")
    # A link of another address is nobody's but its own.
    assert data(elsewhere.post("/v1/auth/session", {"token": theirs, "adult": True}))


@pytest.mark.parametrize(
    "sent",
    [
        "t" * 43,
        "t" * 42,
        "t" * 44,
        "",
        " ",
        "not a token",
        "../../etc/passwd",
        "' OR 1=1 --",
        "t" * 128,
        "t" * 42 + "\N{LATIN SMALL LETTER E WITH ACUTE}",
        f"{CANARY}" * 3,
    ],
)
def test_what_is_no_link_of_burros_is_said_to_be_none(tmp_path: Path, sent: str):
    on = turned_on(tmp_path)
    browser = Browser(on)
    browser.ask_for_link(EMAIL)

    for path, more in (("/v1/auth/link/whose", {}), ("/v1/auth/session", {"adult": True})):
        refused = browser.post(path, {"token": sent} | more)
        if sent == "":
            assert code(refused) == (422, "invalid_request")
        else:
            assert code(refused) == (422, "link_not_valid")
        assert CANARY not in refused.text and EMAIL not in refused.text
    assert not on.rows("SELECT * FROM sessions")


def test_half_of_a_pair_is_no_token_and_breaks_nothing(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)
    # What no text holds, and what cannot be written down to be hashed.
    sent = b'{"token": "' + b"t" * 42 + b'\\ud800"}'

    for path in ("/v1/auth/link/whose", "/v1/auth/session"):
        refused = on.client.post(path, headers=browser.headers("POST"), content=sent)
        # Refused as what is no text, or as what is no link. Never a failure of Burro's.
        assert refused.status_code == 422
        assert refused.json()["error"]["code"] in ("invalid_request", "link_not_valid")


def test_of_two_that_use_one_link_at_once_one_signs_in(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)
    sent = {"token": token, "adult": True, "other_browser": True}
    many = [Browser(on, address=f"198.51.100.{number}") for number in range(1, 17)]

    def press(each: Browser) -> int:
        return each.post("/v1/auth/session", sent).status_code

    with ThreadPoolExecutor(max_workers=16) as pool:
        answered = list(pool.map(press, many))

    assert sorted(answered) == [200] + [410] * 15
    assert len(on.rows("SELECT * FROM sessions")) == 1
    assert len(on.rows("SELECT * FROM accounts")) == 1


def test_a_token_a_session_and_the_secret_are_each_compared_in_constant_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    compared: list[tuple[bytes, bytes]] = []
    compare_digest = hmac.compare_digest

    def heard(one: bytes, other: bytes) -> bool:
        compared.append((one, other))
        return compare_digest(one, other)

    monkeypatch.setattr(hmac, "compare_digest", heard)
    on = turned_on(tmp_path)
    browser = Browser(on)

    token = browser.ask_for_link(EMAIL)
    binding = browser.cookies["__Host-burro_link"]
    browser.post("/v1/auth/session", {"token": token, "adult": True})
    session = browser.cookies["__Host-burro_session"]
    assert browser.get("/v1/me").status_code == 200

    pairs = {(one, other) for one, other in compared}
    for kept in (sha256(token), sha256(binding), sha256(session)):
        # What was kept, against the hash of what was shown: the same, and compared so.
        assert (kept.encode(), kept.encode()) in pairs, kept[:6]
    secret = hashlib.sha256(SECRET.encode()).digest()
    assert (secret, secret) in pairs
    # And nothing is compared that is not a hash: no token, no session, no secret.
    for one, other in compared:
        assert len(one) == len(other) and len(one) in (32, 64)


# The browser that asked, and another.


def test_a_link_opened_in_another_browser_is_not_taken_without_being_asked(tmp_path: Path):
    on = turned_on(tmp_path)
    token = Browser(on).ask_for_link(EMAIL)
    phone = Browser(on, agent=SAFARI)

    whose = data(phone.post("/v1/auth/link/whose", {"token": token}))
    refused = phone.post("/v1/auth/session", {"token": token, "adult": True})

    # The page is told, so that it says so plainly and shows the address again.
    assert whose == {"email": EMAIL, "same_browser": False, "new_account": True}
    assert code(refused) == (409, "other_browser")
    assert "set-cookie" not in refused.headers and not phone.cookies
    assert not on.rows("SELECT * FROM sessions") and not on.rows("SELECT * FROM accounts")
    # And the link is not used up, so that the person may be asked and go on.
    asked = {"token": token, "adult": True, "other_browser": True}
    assert data(phone.post("/v1/auth/session", asked)) == {"email": EMAIL, "new_account": True}


def test_a_link_that_somebody_else_sent_signs_nobody_in_unseen(tmp_path: Path):
    on = turned_on(tmp_path)
    theirs = "somebody.else@example.org"
    sent = Browser(on, address="198.51.100.66").ask_for_link(theirs)
    # The person it was passed to opens it, in a browser that asked for no link.
    mine = Browser(on)

    whose = data(mine.post("/v1/auth/link/whose", {"token": sent}))
    pressed = mine.post("/v1/auth/session", {"token": sent, "adult": True})

    # They are shown whose account it is, which is not theirs, and are asked twice.
    assert whose["email"] == theirs and whose["same_browser"] is False
    assert code(pressed) == (409, "other_browser")
    assert not mine.cookies and not on.rows("SELECT * FROM sessions")


@pytest.mark.parametrize(
    "held",
    ["b" * 43, "", "short", "b" * 44, f"{CANARY}", "b" * 42 + "=", "../" * 14 + "b"],
)
def test_what_a_browser_holds_binds_a_link_only_where_it_is_what_was_given(
    tmp_path: Path, held: str
):
    on = turned_on(tmp_path)
    token = Browser(on).ask_for_link(EMAIL)
    other = Browser(on)
    other.cookies["__Host-burro_link"] = held

    whose = data(other.post("/v1/auth/link/whose", {"token": token}))

    assert whose["same_browser"] is False
    assert code(other.post("/v1/auth/session", {"token": token, "adult": True})) == (
        409,
        "other_browser",
    )


def test_a_cookie_under_the_plain_name_binds_nothing(tmp_path: Path):
    # A host beside the website can give a browser a cookie under a plain name. It
    # cannot give one under the name that a browser takes from the host itself.
    on = turned_on(tmp_path)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)
    [binding] = browser.cookies.values()
    beside = Browser(on)
    beside.cookies["burro_link"] = binding

    assert data(beside.post("/v1/auth/link/whose", {"token": token}))["same_browser"] is False


def test_the_links_of_one_browser_are_all_bound_to_what_it_now_holds(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)
    first = browser.ask_for_link(EMAIL)
    earlier = dict(browser.cookies)

    second = browser.ask_for_link(EMAIL)

    # The browser holds one cookie, which is the newer. Both links are bound to it, so
    # the letter that came first still opens in the browser that asked for it.
    assert browser.cookies != earlier and len(browser.cookies) == 1
    for token in (first, second):
        assert data(browser.post("/v1/auth/link/whose", {"token": token}))["same_browser"]
    # What it held before binds nothing now.
    stale = Browser(on)
    stale.cookies.update(earlier)
    assert not data(stale.post("/v1/auth/link/whose", {"token": first}))["same_browser"]


def test_a_refusal_leaves_the_links_of_a_browser_bound_to_what_it_holds(tmp_path: Path):
    post = Post()
    on = turned_on(tmp_path, post=post, links_per_hour=3)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)
    held = dict(browser.cookies)

    # Somebody else's letter could not be sent, so for a minute nobody is sent one.
    post.fails = SendFailed(reached=False)
    elsewhere = Browser(on, address="198.51.100.66")
    assert elsewhere.post("/v1/auth/link", {"email": "z@example.org"}).status_code == 202
    post.fails = None

    # Refused four ways, none of which gives the browser anything new to hold.
    assert code(browser.post("/v1/auth/link", {"email": OTHER})) == (503, "sign_in_unavailable")
    on.later(minutes=1)
    assert code(browser.post("/v1/auth/link", {"email": "nobody"})) == (422, "invalid_email")
    assert browser.post("/v1/auth/link", {"email": OTHER}).status_code == 202
    held_now = dict(browser.cookies)
    assert code(browser.post("/v1/auth/link", {"email": "q@example.org"})) == (429, "sign_in_busy")
    for _ in range(8):
        browser.post("/v1/auth/link", {"email": "nobody"})
    assert code(browser.post("/v1/auth/link", {"email": OTHER})) == (429, "rate_limited")

    # So the link it asked for first still opens in it, with nothing more to confirm.
    assert held != held_now == browser.cookies
    assert data(browser.post("/v1/auth/link/whose", {"token": token}))["same_browser"] is True
    assert data(browser.post("/v1/auth/session", {"token": token, "adult": True}))


def test_a_browser_binds_no_link_but_its_own(tmp_path: Path):
    on = turned_on(tmp_path)
    mine, theirs = Browser(on), Browser(on, address="198.51.100.66")
    token = mine.ask_for_link(EMAIL)

    # Another browser asks, again and again, holding what it likes.
    theirs.cookies["__Host-burro_link"] = "b" * 43
    for _ in range(3):
        theirs.ask_for_link(OTHER)

    assert data(mine.post("/v1/auth/link/whose", {"token": token}))["same_browser"] is True
    assert data(theirs.post("/v1/auth/link/whose", {"token": token}))["same_browser"] is False


# A new session is always made.


def test_a_session_is_never_taken_from_the_client(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)
    token = browser.ask_for_link(EMAIL)
    chosen = "s" * 43
    # As somebody might who had put a session of their choosing into the browser.
    browser.cookies["__Host-burro_session"] = chosen

    browser.post("/v1/auth/session", {"token": token, "adult": True})

    made = browser.cookies["__Host-burro_session"]
    assert made != chosen and re.fullmatch(r"[A-Za-z0-9_-]{43}", made)
    assert on.rows("SELECT token_hash FROM sessions") == [(sha256(made),)]
    stranger = Browser(on)
    stranger.cookies["__Host-burro_session"] = chosen
    assert code(stranger.get("/v1/me")) == (401, "not_signed_in")


def test_signing_in_again_makes_a_new_session_and_revokes_the_one_the_browser_had(
    tmp_path: Path,
):
    on = turned_on(tmp_path)
    browser = Browser(on)
    browser.sign_in(EMAIL)
    first = browser.cookies["__Host-burro_session"]
    on.later(minutes=1)

    browser.sign_in(EMAIL)

    second = browser.cookies["__Host-burro_session"]
    assert second != first
    held = dict(on.rows("SELECT token_hash, revoked_at FROM sessions"))
    assert held == {sha256(first): "2026-09-23T12:01:00Z", sha256(second): None}
    old = Browser(on)
    old.cookies["__Host-burro_session"] = first
    assert code(old.get("/v1/me")) == (401, "not_signed_in")


# The limits.


def test_three_links_to_an_address_in_a_quarter_of_an_hour_and_no_more(tmp_path: Path):
    on = turned_on(tmp_path)
    clients = [Browser(on, address=f"198.51.100.{number}") for number in range(1, 7)]

    answered = [each.post("/v1/auth/link", {"email": EMAIL}) for each in clients[:5]]

    # Every answer is the one every address is given, and three letters were sent.
    assert [(each.status_code, data(each)) for each in answered] == [(202, LINK_ASKED)] * 5
    assert all(len(each.headers.get_list("set-cookie")) == 1 for each in answered)
    assert [to for to, _ in on.post.sent] == [EMAIL] * 3
    assert len(on.rows("SELECT * FROM login_tokens")) == 3
    # Another address is not this one.
    assert clients[5].post("/v1/auth/link", {"email": OTHER}).status_code == 202
    assert on.post.sent[-1][0] == OTHER

    on.later(minutes=15)
    assert clients[5].post("/v1/auth/link", {"email": EMAIL}).status_code == 202
    assert [to for to, _ in on.post.sent].count(EMAIL) == 4


def test_ten_links_to_an_address_in_a_day_and_no_more(tmp_path: Path):
    on = turned_on(tmp_path)

    for number in range(14):
        on.later(minutes=20)
        browser = Browser(on, address=f"198.51.100.{number + 1}")
        assert browser.post("/v1/auth/link", {"email": EMAIL}).status_code == 202

    assert len(on.post.sent) == 10
    on.later(hours=20)
    assert Browser(on).post("/v1/auth/link", {"email": EMAIL}).status_code == 202
    assert len(on.post.sent) == 11


def test_ten_requests_from_one_client_in_a_quarter_of_an_hour_and_no_more(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)

    answered = [
        browser.post("/v1/auth/link", {"email": f"p{number}@example.org"}) for number in range(12)
    ]

    assert [each.status_code for each in answered] == [202] * 10 + [429] * 2
    assert answered[-1].json()["error"] == {
        "code": "rate_limited",
        "message": (
            "Burro has been asked to sign in too many times from here, so please wait a "
            "quarter of an hour and then try again."
        ),
        "fields": [],
    }
    assert len(on.post.sent) == 10
    on.later(minutes=15)
    assert browser.post("/v1/auth/link", {"email": "q@example.org"}).status_code == 202


def test_what_is_not_an_address_is_counted_against_the_client_that_sent_it(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)

    answered = [browser.post("/v1/auth/link", {"email": "nobody"}) for _ in range(12)]

    assert [each.status_code for each in answered] == [422] * 10 + [429] * 2


def test_the_whole_service_sends_so_many_links_in_an_hour_and_no_more(tmp_path: Path):
    on = turned_on(tmp_path, links_per_hour=5)

    def ask(number: int) -> int:
        browser = Browser(on, address=f"198.51.100.{number + 1}")
        return browser.post("/v1/auth/link", {"email": f"p{number}@example.org"}).status_code

    assert [ask(number) for number in range(7)] == [202] * 5 + [429] * 2
    refused = Browser(on).post("/v1/auth/link", {"email": "q@example.org"})
    assert code(refused) == (429, "sign_in_busy")
    assert len(on.post.sent) == 5

    on.later(minutes=61)
    assert ask(8) == 202


def test_an_address_over_its_limit_fills_the_hour_as_any_other(tmp_path: Path):
    def one_short_of_full(folder: Path, lately: int) -> On:
        """The hour one short of full, and then a link is asked for the address."""
        folder.mkdir()
        on = turned_on(folder, links_per_hour=6)
        for number in range(lately):
            browser = Browser(on, address=f"198.51.100.{number + 1}")
            assert browser.post("/v1/auth/link", {"email": EMAIL}).status_code == 202
        for number in range(5 - lately):
            browser = Browser(on, address=f"198.51.100.{number + 11}")
            email = f"p{number}@example.org"
            assert browser.post("/v1/auth/link", {"email": email}).status_code == 202
        assert Browser(on).post("/v1/auth/link", {"email": EMAIL}).status_code == 202
        return on

    def asked_next(on: On) -> tuple[int, str] | int:
        asking = Browser(on, address="198.51.100.66")
        answered = asking.post("/v1/auth/link", {"email": OTHER})
        return answered.status_code if answered.status_code == 202 else code(answered)

    sent = one_short_of_full(tmp_path / "sent", lately=0)
    over = one_short_of_full(tmp_path / "over", lately=3)

    # The address was sent a letter in the one, and was over its limit and sent none in
    # the other. Whoever asks next is answered the same, or the answer would say which.
    assert len(sent.post.sent) == 6 and len(over.post.sent) == 5
    assert asked_next(sent) == (429, "sign_in_busy")
    assert asked_next(over) == (429, "sign_in_busy")
    # What filled the hour and left no row is let go of with the hour, as a row is.
    for on in (sent, over):
        on.later(minutes=61)
        assert asked_next(on) == 202


def test_a_cap_of_nought_sends_no_link_at_all(tmp_path: Path):
    on = turned_on(tmp_path, links_per_hour=0)

    refused = Browser(on).post("/v1/auth/link", {"email": EMAIL})

    assert code(refused) == (429, "sign_in_busy") and not on.post.sent


def test_a_client_may_show_so_many_links_in_a_quarter_of_an_hour_and_no_more(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)

    shown = [
        browser.post(path, {"token": "t" * 43})
        for _ in range(16)
        for path in ("/v1/auth/link/whose", "/v1/auth/session")
    ]

    assert [each.status_code for each in shown] == [422] * 30 + [429] * 2
    assert code(shown[-1]) == (429, "rate_limited")


# The sender.


def test_with_no_sender_named_signing_in_answers_that_it_cannot(tmp_path: Path):
    on = turned_on(tmp_path, with_sender=False)
    browser = Browser(on)

    refused = browser.post("/v1/auth/link", {"email": EMAIL})

    assert code(refused) == (503, "sign_in_unavailable")
    assert refused.json()["error"]["message"] == (
        "Burro cannot send sign-in emails at the moment, so please try again later."
    )
    assert "set-cookie" not in refused.headers and not on.rows("SELECT * FROM login_tokens")
    # The rest of accounts answers as it does.
    assert data(browser.get("/v1/auth/session")) == {"signed_in": False, "email": None}


def test_a_sender_that_cannot_be_reached_is_said_to_whoever_asks_next(tmp_path: Path):
    post = Post()
    on = turned_on(tmp_path, post=post)
    post.fails = SendFailed(reached=False)
    browser = Browser(on)

    answered = browser.post("/v1/auth/link", {"email": EMAIL})

    # The answer was given before the letter was tried, so it is the one every address
    # is given. The link was made and was never sent, so it is ended. It is still counted.
    assert answered.status_code == 202 and data(answered) == LINK_ASKED
    assert on.rows("SELECT used_at FROM login_tokens") == [("2026-09-23T12:00:00Z",)]

    # For a minute nobody is sent a link, whatever their address and whoever they are,
    # and nothing is made of what they ask.
    post.fails = None
    held = dict(browser.cookies)
    for asking, email in ((browser, EMAIL), (Browser(on, address="198.51.100.66"), OTHER)):
        on.later(seconds=29)
        refused = asking.post("/v1/auth/link", {"email": email})
        assert code(refused) == (503, "sign_in_unavailable")
        assert "set-cookie" not in refused.headers
    assert len(on.rows("SELECT * FROM login_tokens")) == 1 and not post.sent
    assert browser.cookies == held

    on.later(seconds=2)
    assert browser.post("/v1/auth/link", {"email": EMAIL}).status_code == 202
    assert [to for to, _ in post.sent] == [EMAIL]


def test_a_letter_the_sender_will_not_take_is_answered_as_any_other(tmp_path: Path):
    post = Post()
    on = turned_on(tmp_path, post=post)
    post.fails = SendFailed(reached=True)
    browser = Browser(on)

    answered = browser.post("/v1/auth/link", {"email": EMAIL})

    # It may be the address that the sender will not take, so the answer does not say.
    assert answered.status_code == 202 and data(answered) == LINK_ASKED
    assert len(browser.given) == 1
    assert on.rows("SELECT used_at FROM login_tokens") == [("2026-09-23T12:00:00Z",)]
    # And nobody who asks after is told of it: another address is sent its letter.
    post.fails = None
    after = Browser(on, address="198.51.100.66").post("/v1/auth/link", {"email": OTHER})
    assert after.status_code == 202 and [to for to, _ in post.sent] == [OTHER]


# What is kept, and for how long.


def test_a_link_is_let_go_of_after_a_day_whoever_asked_for_it(tmp_path: Path):
    on = turned_on(tmp_path)
    Browser(on).ask_for_link("never.came.back@example.org")
    assert b"never.came.back" in on.written()

    on.later(hours=24, seconds=1)
    Browser(on).ask_for_link(OTHER)

    # A day on, the address of somebody who never signed in goes as the next link is
    # asked for: it is in no row, and in no byte of the file.
    assert on.rows("SELECT email FROM login_tokens") == [(OTHER,)]
    assert b"never.came.back" not in on.written()


def test_a_link_within_the_day_is_still_counted(tmp_path: Path):
    on = turned_on(tmp_path)
    for number in range(3):
        Browser(on, address=f"198.51.100.{number + 1}").ask_for_link(EMAIL)

    on.later(hours=23)
    Browser(on).ask_for_link(OTHER)

    assert len(on.rows("SELECT * FROM login_tokens WHERE email = ?", EMAIL)) == 3


def test_links_that_are_too_old_are_let_go_of_as_the_service_starts(tmp_path: Path):
    on = turned_on(tmp_path)
    Browser(on).ask_for_link(EMAIL)
    on.accounts.close()
    assert len(on.rows("SELECT * FROM login_tokens")) == 1

    # The service starts again, a day and more on.
    later = FixedClock(on.clock.at + timedelta(days=1, seconds=1))
    opened = open_accounts(settings(tmp_path), "0.0.0.0", (SITE,), later.now)  # noqa: S104

    assert not on.rows("SELECT * FROM login_tokens")
    assert EMAIL.encode() not in on.written()
    opened.close()


def test_an_address_that_never_signed_in_goes_as_somebody_who_is_signed_in_comes_back(
    tmp_path: Path,
):
    on = turned_on(tmp_path)
    mine = Browser(on)
    mine.sign_in(EMAIL)
    Browser(on, address="198.51.100.5").ask_for_link("never.came.back@example.org")

    # Nobody asks for a link. Somebody who is signed in uses Burro, a day and more on.
    on.later(days=1, seconds=1)
    assert data(mine.get("/v1/auth/session"))["signed_in"] is True

    assert not on.rows("SELECT * FROM login_tokens")
    assert b"never.came.back" not in on.written()


def test_what_is_too_old_of_every_kind_is_let_go_of_as_a_link_is_asked_for(tmp_path: Path):
    on = turned_on(tmp_path)
    left = Browser(on)
    left.sign_in(EMAIL)
    left.delete("/v1/auth/session")
    assert on.rows("SELECT count(*) FROM audit_events") == [(3,)]

    # Nobody signs in. Somebody asks for a link, and never opens it.
    on.later(days=90, seconds=1)
    Browser(on, address="198.51.100.5").ask_for_link(OTHER)

    assert on.rows("SELECT email FROM login_tokens") == [(OTHER,)]
    assert on.rows("SELECT count(*) FROM sessions") == [(0,)]
    assert on.rows("SELECT count(*) FROM audit_events") == [(0,)]
    # The account itself is never let go of by its age.
    assert on.rows("SELECT email FROM accounts") == [(EMAIL,)]


def test_what_is_too_old_of_every_kind_is_let_go_of_as_the_service_starts(tmp_path: Path):
    on = turned_on(tmp_path)
    left = Browser(on)
    left.sign_in(EMAIL)
    left.delete("/v1/auth/session")
    on.accounts.close()

    # The file is not opened meanwhile, as where accounts are turned off for a while.
    later = FixedClock(on.clock.at + timedelta(days=90, seconds=1))
    opened = open_accounts(settings(tmp_path), "0.0.0.0", (SITE,), later.now)  # noqa: S104

    assert on.rows("SELECT count(*) FROM login_tokens") == [(0,)]
    assert on.rows("SELECT count(*) FROM sessions") == [(0,)]
    assert on.rows("SELECT count(*) FROM audit_events") == [(0,)]
    assert on.rows("SELECT email FROM accounts") == [(EMAIL,)]
    opened.close()
