"""Who is heard: the website, which shows its secret, and nobody else.

And what is heard of a client: the one address the website gave, and nothing a client
wrote itself.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from burro_api.accounts.service import CLIENT, REQUESTED, WEBSITE

from ..support import CANARY
from .support import AT_HOME, JSON, SECRET, SITE, Browser, On, code, data, turned_on
from .test_off import routes

NOT_THE_WEBSITE = (403, "not_the_website")
EMAIL = "marmalade.quokka@example.org"
each_route = pytest.mark.parametrize(("method", "path"), routes())
changing = [(method, path) for method, path in routes() if method != "GET"]


@pytest.fixture(scope="module")
def on(tmp_path_factory: pytest.TempPathFactory) -> Iterator[On]:
    """One service for every test here whose request is refused, and so changes nothing.

    Hundreds of requests are tried that are each refused before anything is made of
    them. A test that counts, or that changes what is kept, has a service of its own.
    """
    made = turned_on(tmp_path_factory.mktemp("heard"))
    yield made
    made.accounts.close()


@pytest.fixture(scope="module")
def signed(on: On) -> Browser:
    """A browser that is signed in to that service, and is never signed out."""
    browser = Browser(on)
    browser.sign_in(EMAIL)
    return browser


# The secret of the website.


@each_route
def test_a_request_without_the_websites_secret_is_refused(signed: Browser, method: str, path: str):
    before = signed.on.held()

    # Signed in, and from a page of the website: all that is missing is the secret.
    answered = signed.ask(method, path, {}, without=(WEBSITE,))

    assert signed.on.held() == before

    assert code(answered) == NOT_THE_WEBSITE
    assert answered.json()["error"] == {
        "code": "not_the_website",
        "message": "Burro only answers this when its own website asks.",
        "fields": [],
    }


@each_route
@pytest.mark.parametrize(
    "shown",
    [
        "",
        " ",
        "wrong",
        SECRET[:-1],
        SECRET + "x",
        SECRET.upper(),
        f" {SECRET}",
        f"Bearer {SECRET}",
        f"{SECRET},{SECRET}",
        "\N{LATIN SMALL LETTER E WITH ACUTE}" * 40,
    ],
)
def test_a_secret_that_is_not_the_websites_is_refused(
    signed: Browser, method: str, path: str, shown: str
):
    answered = signed.ask(method, path, {}, changed={WEBSITE: shown.encode()})

    assert code(answered) == NOT_THE_WEBSITE
    assert CANARY not in answered.text


def test_the_secret_is_read_from_its_own_header_and_no_other(on: On):
    browser = Browser(on)
    elsewhere = {
        "authorization": f"Bearer {SECRET}",
        "x-api-key": SECRET,
        "cookie": f"x-burro-website={SECRET}",
        "x-burro-secret": SECRET,
    }

    for name, shown in elsewhere.items():
        answered = browser.ask("GET", "/v1/auth/session", without=(WEBSITE,), changed={name: shown})
        assert code(answered) == NOT_THE_WEBSITE, name


def test_a_secret_that_is_shown_twice_is_not_the_websites(on: On):
    twice = [(WEBSITE, SECRET), (WEBSITE, SECRET), (CLIENT, "203.0.113.7")]

    answered = on.client.get("/v1/auth/session", headers=twice)

    assert code(answered) == NOT_THE_WEBSITE


@pytest.mark.parametrize(("method", "path"), changing)
def test_what_a_stranger_sends_is_refused_before_it_is_read(on: On, method: str, path: str):
    headers = {"content-type": JSON, "origin": SITE, REQUESTED: "1"}
    # Not JSON at all, and with the canary in it. Read, it would be answered 400.
    sent = f'{{"email": "{CANARY}'.encode()
    before = len(on.post.sent)

    answered = on.client.request(method, path, headers=headers, content=sent)

    assert code(answered) == NOT_THE_WEBSITE
    assert CANARY not in answered.text and len(on.post.sent) == before


def test_an_origin_that_is_sent_twice_is_no_origin_of_a_page(on: On):
    twice = [
        (WEBSITE, SECRET),
        ("origin", SITE),
        ("origin", "https://elsewhere.example"),
        (REQUESTED, "1"),
        ("content-type", JSON),
    ]

    for headers in (twice, [twice[0], twice[2], twice[1], *twice[3:]]):
        answered = on.client.post("/v1/auth/link", headers=headers, content=b"{}")
        assert code(answered) == NOT_THE_WEBSITE


def test_the_website_is_answered(on: On):
    browser = Browser(on)

    assert data(browser.get("/v1/auth/session")) == {"signed_in": False, "email": None}


# What changes anything.


@pytest.mark.parametrize(("method", "path"), changing)
@pytest.mark.parametrize(
    "origin",
    [
        None,
        "",
        "null",
        "https://elsewhere.example",
        "https://burro.example.elsewhere.example",
        "https://burro.example:443",
        "https://burro.example/",
        "https://BURRO.example",
        "http://burro.example",
        "https://www.burro.example",
        f"{SITE} {SITE}",
        f"{SITE},{SITE}",
        "*",
    ],
)
def test_what_changes_anything_comes_from_a_page_of_the_website(
    signed: Browser, method: str, path: str, origin: str | None
):
    if origin is None:
        answered = signed.ask(method, path, {}, without=("origin",))
    else:
        answered = signed.ask(method, path, {}, changed={"origin": origin})

    assert code(answered) == NOT_THE_WEBSITE
    assert "access-control-allow-origin" not in answered.headers


@pytest.mark.parametrize(("method", "path"), changing)
@pytest.mark.parametrize("said", [None, "", "0", "2", "true", "yes", "1 ", "11", "1, 1"])
def test_what_changes_anything_says_that_a_page_of_burro_asked(
    signed: Browser, method: str, path: str, said: str | None
):
    if said is None:
        answered = signed.ask(method, path, {}, without=(REQUESTED,))
    else:
        answered = signed.ask(method, path, {}, changed={REQUESTED: said})

    # A form on another site can send no header of its own, so it cannot say so.
    assert code(answered) == NOT_THE_WEBSITE


@pytest.mark.parametrize(("method", "path"), changing)
@pytest.mark.parametrize(
    "kind",
    [
        None,
        "",
        "text/plain",
        "application/x-www-form-urlencoded",
        "multipart/form-data; boundary=x",
        "application/jsonp",
        "text/json",
    ],
)
def test_what_changes_anything_is_sent_as_json_and_as_nothing_a_form_can_send(
    signed: Browser, method: str, path: str, kind: str | None
):
    if kind is None:
        answered = signed.ask(method, path, {}, without=("content-type",))
    else:
        answered = signed.ask(method, path, {}, changed={"content-type": kind})

    assert code(answered) == (415, "unsupported_media_type")


def test_asking_for_a_link_needs_all_three_though_there_is_no_cookie_yet(tmp_path: Path):
    on = turned_on(tmp_path)
    browser = Browser(on)
    sent = {"email": EMAIL}

    assert not browser.cookies
    for missing in ("origin", REQUESTED, "content-type"):
        refused = browser.ask("POST", "/v1/auth/link", sent, without=(missing,))
        assert refused.status_code in (403, 415), missing
    assert not on.post.sent and not on.rows("SELECT * FROM login_tokens")

    assert browser.post("/v1/auth/link", sent).status_code == 202
    assert len(on.post.sent) == 1


@pytest.mark.parametrize("path", sorted({path for method, path in routes() if method == "GET"}))
def test_a_get_needs_the_website_and_no_more_and_changes_nothing(signed: Browser, path: str):
    before = signed.on.held()

    answered = signed.ask("GET", path, without=("origin", REQUESTED, "content-type"))

    assert answered.status_code == 200
    # Not a row of the file is other than it was.
    assert signed.on.held() == before and len(before["sessions"]) == 1


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/v1/auth/link"),
        ("GET", "/v1/auth/link/whose"),
        ("GET", "/v1/me/preferences"),
        ("HEAD", "/v1/me"),
        ("PATCH", "/v1/me"),
        ("POST", "/v1/me"),
        ("PUT", "/v1/me/searches"),
    ],
)
def test_a_route_takes_the_methods_it_is_declared_with_and_no_other(
    signed: Browser, method: str, path: str
):
    answered = signed.ask(method, path, None if method in ("GET", "HEAD") else {})

    assert answered.status_code == 405
    if method != "HEAD":
        assert answered.json()["error"]["code"] == "method_not_allowed"


@each_route
@pytest.mark.parametrize("query", ["t=token", "token=x", "x", "search_id=abc", f"q={CANARY}"])
def test_no_route_takes_a_query(signed: Browser, method: str, path: str, query: str):
    answered = signed.ask(method, f"{path}?{query}", {})

    # A link and an id are sent in a body. In an address they would reach a log.
    assert code(answered) == (422, "invalid_request")
    assert CANARY not in answered.text


# The address of a client.


def test_a_client_is_counted_by_the_address_the_website_gave(tmp_path: Path):
    on = turned_on(tmp_path)
    one, other = Browser(on, address="203.0.113.7"), Browser(on, address="203.0.113.8")

    asked = [one.post("/v1/auth/link", {"email": f"p{n}@example.org"}) for n in range(11)]

    assert [each.status_code for each in asked] == [202] * 10 + [429]
    assert code(asked[-1]) == (429, "rate_limited")
    # Another client is not the first, and is answered.
    assert other.post("/v1/auth/link", {"email": "q@example.org"}).status_code == 202


@pytest.mark.parametrize(
    "header", ["x-forwarded-for", "forwarded", "x-real-ip", "cf-connecting-ip", "true-client-ip"]
)
def test_an_address_that_a_client_wrote_is_not_believed(tmp_path: Path, header: str):
    on = turned_on(tmp_path)
    browser = Browser(on)

    # Each says it comes from somewhere new, in every header a proxy might read.
    asked = [
        browser.post(
            "/v1/auth/link",
            {"email": f"p{n}@example.org"},
            {header: f"for=198.51.100.{n}" if header == "forwarded" else f"198.51.100.{n}"},
        )
        for n in range(11)
    ]

    assert [each.status_code for each in asked] == [202] * 10 + [429]


def test_the_header_of_an_address_is_believed_from_the_website_alone(tmp_path: Path):
    on = turned_on(tmp_path)
    headers = {CLIENT: "203.0.113.7", "content-type": JSON, "origin": SITE, REQUESTED: "1"}

    # A stranger says it is the client, many times over. It is refused, and not counted.
    for number in range(40):
        sent = f'{{"email": "s{number}@example.org"}}'.encode()
        refused = on.client.post("/v1/auth/link", headers=headers, content=sent)
        assert code(refused) == NOT_THE_WEBSITE

    # So the client that the stranger named has still every one of its own.
    browser = Browser(on, address="203.0.113.7")
    asked = [browser.post("/v1/auth/link", {"email": f"p{n}@example.org"}) for n in range(10)]
    assert [each.status_code for each in asked] == [202] * 10


@pytest.mark.parametrize(
    "given",
    [
        [(CLIENT, "203.0.113.7"), (CLIENT, "198.51.100.9")],
        [(CLIENT, "203.0.113.7, 198.51.100.9")],
        [(CLIENT, "198.51.100.9,203.0.113.7")],
    ],
)
def test_two_addresses_say_that_the_website_did_not_write_them_alone(
    on: On, given: list[tuple[str, str]]
):
    # The website takes out what a client sent and puts in one. Two are not its work.
    answered = on.client.get("/v1/auth/session", headers=[(WEBSITE, SECRET), *given])

    assert code(answered) == NOT_THE_WEBSITE


UNREAD = ["", " ", "nonsense", "203.0.113", "unknown", "203.0.113.7:443", "[2001:db8::1]"]


@each_route
@pytest.mark.parametrize("given", [None, *UNREAD])
def test_a_request_that_does_not_say_whose_it_is_is_not_the_websites(
    signed: Browser, method: str, path: str, given: str | None
):
    before = signed.on.held()

    # Signed in, from a page of the website, and with its secret: all that is missing
    # is the one address of the client, which the website gives with whatever it passes on.
    if given is None:
        answered = signed.ask(method, path, {}, without=(CLIENT,))
    else:
        answered = signed.ask(method, path, {}, changed={CLIENT: given})

    assert code(answered) == NOT_THE_WEBSITE
    assert signed.on.held() == before


def test_no_client_is_counted_with_the_unknown_but_in_development(tmp_path: Path):
    on = turned_on(tmp_path)
    nobody = Browser(on)

    # Were they counted as one client, whoever asked ten times without an address
    # would stop everybody whose address could not be read from signing in.
    asked = [
        nobody.ask("POST", "/v1/auth/link", {"email": f"p{n}@example.org"}, without=(CLIENT,))
        for n in range(12)
    ]

    assert [code(each) for each in asked] == [NOT_THE_WEBSITE] * 12
    assert not on.post.sent and not on.rows("SELECT * FROM login_tokens")
    # And none of it was counted against anybody.
    assert Browser(on).post("/v1/auth/link", {"email": EMAIL}).status_code == 202


def test_in_development_clients_whose_address_cannot_be_read_are_counted_as_one(tmp_path: Path):
    # On a machine of one's own no host stands before the website to say who asks.
    on = turned_on(tmp_path, development=True, site=AT_HOME)
    unread = [
        Browser(on, address=given, site=AT_HOME)
        for given in ("", "nonsense", "203.0.113", "unknown")
    ]
    unread.append(Browser(on, site=AT_HOME))

    asked = [
        browser.ask(
            "POST",
            "/v1/auth/link",
            {"email": f"p{n}@example.org"},
            without=(CLIENT,) if browser is unread[-1] else (),
        )
        for n in range(3)
        for browser in unread
    ]

    # Fifteen between them, of which ten are let in: so what cannot be read is limited
    # the more, and never the less.
    assert [each.status_code for each in asked] == [202] * 10 + [429] * 5


# Every answer.


@each_route
def test_every_answer_is_never_kept_and_is_what_it_says_it_is(
    tmp_path: Path, method: str, path: str
):
    on = turned_on(tmp_path)
    browser = Browser(on)
    browser.sign_in(EMAIL)
    sent = [
        browser.ask(method, path, {}),
        browser.ask(method, path, {}, without=(WEBSITE,)),
        browser.ask(method, f"{path}?x=1", {}),
        browser.ask(method, path, {}, changed={"content-type": "text/plain"}),
        on.client.request(method, path, headers=browser.headers(method), content=b"x" * 20_000),
    ]

    for answered in sent:
        assert answered.headers["cache-control"] == "no-store", answered.status_code
        assert answered.headers["x-content-type-options"] == "nosniff", answered.status_code
        assert answered.headers["content-type"] == JSON
        # Every answer says whether the data is made up, as every answer of Burro does.
        assert answered.headers["x-burro-synthetic"] == "true"
        assert answered.json()["meta"]["synthetic"] is True
        assert "access-control-allow-credentials" not in answered.headers
        assert "location" not in answered.headers and answered.status_code not in range(300, 400)


def test_an_answer_of_the_search_is_as_it_was(on: On):
    found = on.client.get("/v1/meta")
    ranked = on.client.post("/v1/rank", json={"spec": found.json()["data"]["defaults"]["rent"]})

    # With accounts on as with them off: no answer of the search is marked as one of
    # accounts is, and none asks who is there.
    for answered in (found, ranked):
        assert answered.status_code == 200
        assert "x-content-type-options" not in answered.headers
        assert "set-cookie" not in answered.headers
    assert found.headers["cache-control"] == "no-cache"


@each_route
def test_no_browser_is_let_send_a_cookie_or_the_header_of_a_page_across_origins(
    on: On, method: str, path: str
):
    asking = {
        "origin": SITE,
        "access-control-request-method": method,
        "access-control-request-headers": f"content-type, {REQUESTED}",
    }

    answered = on.client.options(path, headers=asking)

    # What a browser is told it may send is what it was always told: no header of a
    # page of Burro, no method that takes anything away, and never a cookie.
    assert answered.headers["access-control-allow-headers"] == "Content-Type"
    assert answered.headers["access-control-allow-methods"] == "GET, POST"
    assert "access-control-allow-credentials" not in answered.headers
