"""What the tests of accounts share: a service with accounts on, and a browser before it.

Every address, secret and name here is made up. An address of a client is one that is
set aside for writing about, and is nobody's.
"""

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any

import httpx2
from burro_api.accounts.sender import SendFailed
from burro_api.accounts.service import CLIENT, REQUESTED, WEBSITE, Accounts, open_accounts
from burro_api.accounts.settings import AccountsSettings, KeepRecent
from burro_api.deps import Deps
from fastapi.testclient import TestClient
from pydantic import SecretStr

from ..support import CANARY, FixedClock, client_for, make_deps

SITE = "https://burro.example"
AT_HOME = "http://127.0.0.1:3381"
# Each holds the canary, so that a secret that is written anywhere is found.
SECRET = f"the-secret-of-the-website-{CANARY}-0123456789"
LIMITS_KEY = f"the-key-of-the-limits-{CANARY}-0123456789abc"
ADDRESS = "203.0.113.7"
FIREFOX = "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"
SAFARI = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1"
)
JSON = "application/json"
AFTER_THE_HASH = "/sign-in/confirm#t="


class Post:
    """Stands in for whoever sends. It keeps each letter it is handed, and sends none."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        # What the next letters fail with, where they are to fail.
        self.fails: SendFailed | None = None

    def send(self, to: str, link: str) -> None:
        if self.fails is not None:
            raise self.fails
        self.sent.append((to, link))

    def token(self, to: str | None = None) -> str:
        """The token of the last link that was sent, to anybody or to one address."""
        links = [link for address, link in self.sent if to is None or address == to]
        assert links, "no link was sent"
        site, found, token = links[-1].partition(AFTER_THE_HASH)
        assert found and site in (SITE, AT_HOME)
        return token


def settings(folder: Path, **changes: Any) -> AccountsSettings:
    made: dict[str, Any] = {
        "database": folder / "accounts.db",
        "site": SITE,
        "development": False,
        "website_secret": SecretStr(SECRET),
        "limits_key": SecretStr(LIMITS_KEY),
        "sender": None,
        "sender_key": None,
        "sender_from": None,
        "links_per_hour": 200,
        "keep_recent": KeepRecent.ASKED,
    }
    return AccountsSettings.model_validate(made | changes)


@dataclass
class On:
    """A service with accounts turned on, and all that a test may look at behind it."""

    deps: Deps
    accounts: Accounts
    post: Post
    clock: FixedClock
    database: Path
    client: TestClient = field(init=False)

    def __post_init__(self) -> None:
        self.client = client_for(self.deps)

    def later(self, **time: float) -> None:
        self.clock.at += timedelta(**time)

    def rows(self, statement: str, *values: object) -> list[tuple[Any, ...]]:
        """What the file holds, read beside the service and never through it."""
        probe = sqlite3.connect(self.database)
        try:
            return probe.execute(statement, values).fetchall()
        finally:
            probe.close()

    def written(self) -> bytes:
        """Every byte of the file, and of what is written beside it."""
        beside = sorted(self.database.parent.glob(f"{self.database.name}*"))
        return b"".join(path.read_bytes() for path in beside)

    def held(self) -> dict[str, list[tuple[Any, ...]]]:
        """Every row of every table, as the file holds them."""
        return {
            table: self.rows(statement)
            for table, statement in {
                "accounts": "SELECT * FROM accounts ORDER BY id",
                "login_tokens": "SELECT * FROM login_tokens ORDER BY token_hash",
                "sessions": "SELECT * FROM sessions ORDER BY token_hash",
                "saved_searches": "SELECT * FROM saved_searches ORDER BY id",
                "recent_searches": "SELECT * FROM recent_searches ORDER BY id",
                "preferences": "SELECT * FROM preferences ORDER BY account_id, key",
                "audit_events": "SELECT * FROM audit_events ORDER BY id",
            }.items()
        }


def turned_on(
    folder: Path, post: Post | None = None, with_sender: bool = True, **changes: Any
) -> On:
    clock = FixedClock()
    found = settings(folder, **changes)
    post = post or Post()
    host = "127.0.0.1" if found.development else "0.0.0.0"  # noqa: S104
    origins = (found.site,)
    accounts = open_accounts(found, host, origins, clock.now, sender=post if with_sender else None)
    if not with_sender:
        # Opened with no sender named, as the settings say.
        assert found.sender is None
    deps = make_deps(accounts=accounts, clock=clock, allowed_origins=origins)
    return On(deps=deps, accounts=accounts, post=post, clock=clock, database=found.database)


# The headers a test changes. One that is not in plain letters is given as its bytes.
Changed = Mapping[str, str | bytes]


class Browser:
    """A browser, and the website that stands between it and the service.

    It sends what a page of the website sends, with what the website adds: its secret,
    and the address of the client. It keeps the cookies it is given, as a browser does,
    and sends them back. A test takes out or changes whatever it means to try.
    """

    def __init__(
        self, on: On, address: str = ADDRESS, agent: str = FIREFOX, site: str = SITE
    ) -> None:
        self.on = on
        self.address = address
        self.agent = agent
        self.site = site
        self.cookies: dict[str, str] = {}
        # Each `Set-Cookie` of the last answer, as it was written.
        self.given: list[str] = []

    def headers(self, method: str) -> dict[str, str]:
        sent = {WEBSITE: SECRET, CLIENT: self.address, "user-agent": self.agent}
        if method != "GET":
            sent |= {"origin": self.site, REQUESTED: "1", "content-type": JSON}
        if self.cookies:
            sent["cookie"] = "; ".join(f"{name}={value}" for name, value in self.cookies.items())
        return sent

    def ask(
        self,
        method: str,
        path: str,
        body: Any = None,
        without: tuple[str, ...] = (),
        changed: Changed | None = None,
    ) -> httpx2.Response:
        """Ask as a page would, but for the headers a test takes out or changes."""
        headers: dict[str, str | bytes] = {**self.headers(method), **(changed or {})}
        for name in without:
            headers.pop(name, None)
        content = b"" if body is None else json.dumps(body).encode()
        # The test client keeps cookies of its own. What is sent here is what is held here.
        self.on.client.cookies.clear()
        written = [
            (name.encode(), value if isinstance(value, bytes) else value.encode())
            for name, value in headers.items()
        ]
        answered = self.on.client.request(method, path, headers=written, content=content)
        self._keep(answered)
        return answered

    def _keep(self, answered: httpx2.Response) -> None:
        self.given = answered.headers.get_list("set-cookie")
        for written in self.given:
            read: SimpleCookie = SimpleCookie()
            read.load(written)
            for name, morsel in read.items():
                if morsel["max-age"] == "0" or not morsel.value:
                    self.cookies.pop(name, None)
                else:
                    self.cookies[name] = morsel.value

    def get(self, path: str, changed: Changed | None = None) -> httpx2.Response:
        return self.ask("GET", path, changed=changed)

    def post(self, path: str, body: Any = None, changed: Changed | None = None) -> httpx2.Response:
        return self.ask("POST", path, {} if body is None else body, changed=changed)

    def delete(self, path: str, body: Any = None) -> httpx2.Response:
        return self.ask("DELETE", path, body)

    def put(self, path: str, body: Any) -> httpx2.Response:
        return self.ask("PUT", path, body)

    def ask_for_link(self, email: str) -> str:
        """Ask for a link, and give back the token of the link that was sent."""
        answered = self.post("/v1/auth/link", {"email": email})
        assert answered.status_code == 202, answered.text
        return self.on.post.token()

    def sign_in(self, email: str, adult: bool = True) -> httpx2.Response:
        """Sign in as a person would: ask for a link, look whose it is, and press."""
        token = self.ask_for_link(email)
        whose = self.post("/v1/auth/link/whose", {"token": token})
        assert whose.status_code == 200, whose.text
        signed = self.post("/v1/auth/session", {"token": token, "adult": adult})
        assert signed.status_code == 200, signed.text
        return signed


def data(answered: httpx2.Response) -> Any:
    assert answered.status_code in (200, 202), answered.text
    return answered.json()["data"]


def code(answered: httpx2.Response) -> tuple[int, str]:
    """The status of a refusal and its code, which is all that tells one from another."""
    return answered.status_code, answered.json()["error"]["code"]
