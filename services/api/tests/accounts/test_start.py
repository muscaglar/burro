"""Starting the service with accounts: what is opened, what is needed, and what is said.

With accounts off nothing of them is opened or made. With them on, what they need is
needed as the service starts, and what is missing is named and never shown.
"""

import json
import os
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import uvicorn
from burro_api.app import create_app, deps_from
from burro_api.cli import main
from burro_api.logs import configure_logging
from burro_api.settings import Settings
from fastapi.testclient import TestClient

from ..support import CANARY
from .support import AT_HOME, LIMITS_KEY, SECRET, SITE
from .test_off import NOTHING_HERE, routes

JSON = {"content-type": "application/json"}


def env(folder: Path, **changes: str) -> dict[str, str]:
    """What is set to turn accounts on, on a machine of one's own."""
    return {
        "BURRO_ACCOUNTS": "on",
        "BURRO_ACCOUNTS_DB": str(folder / "accounts.db"),
        "BURRO_ACCOUNTS_SITE": AT_HOME,
        "BURRO_ALLOWED_ORIGINS": AT_HOME,
        "BURRO_WEBSITE_SECRET": SECRET,
        "BURRO_ACCOUNTS_LIMITS_KEY": LIMITS_KEY,
        "BURRO_ACCOUNTS_DEVELOPMENT": "yes",
        "BURRO_ACCOUNTS_SENDER": "console",
    } | changes


@pytest.fixture
def opened(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every file that is opened as a database, by whatever opens it."""
    found: list[str] = []
    connect = sqlite3.connect

    def heard(database: Any, *args: Any, **kwargs: Any) -> sqlite3.Connection:
        found.append(str(database))
        return connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", heard)
    return found


def runs_nothing(app: object, **how: object) -> None:
    """Stands in for the server, and returns as one that was stopped does."""


# Off.


def test_with_accounts_off_no_file_is_opened_and_nothing_of_them_is_made(
    tmp_path: Path, opened: list[str]
):
    # Everything that turns accounts on is set, but the one setting that does.
    set_ = {name: value for name, value in env(tmp_path).items() if name != "BURRO_ACCOUNTS"}

    for how in (set_, set_ | {"BURRO_ACCOUNTS": "off"}, {}):
        deps = deps_from(Settings.from_env(how))
        client = TestClient(create_app(deps))
        for method, path in routes():
            answered = client.request(method, path, headers=JSON, content=b"{}")
            assert (answered.status_code, answered.json()["error"]) == (404, NOTHING_HERE)
        assert deps.accounts is None

    assert opened == [] and list(tmp_path.iterdir()) == []


def test_with_accounts_off_the_service_is_what_it_was(tmp_path: Path):
    # Answering the same website, with accounts and without.
    off = TestClient(create_app(deps_from(Settings.from_env({"BURRO_ALLOWED_ORIGINS": AT_HOME}))))
    on = TestClient(create_app(deps_from(Settings.from_env(env(tmp_path)))))
    found = off.get("/v1/meta").json()
    sent = {"spec": found["data"]["defaults"]["rent"]}

    def answered(client: TestClient) -> list[tuple[int, dict[str, str], str]]:
        asked = [
            client.get("/v1/meta"),
            client.get("/v1/areas"),
            client.post("/v1/rank", json=sent),
            client.post("/v1/explanations", json=sent),
            client.post("/v1/interpret", json={"text": "leafy, 30 minutes to Cindermoor Works"}),
            client.get("/v1/nothing-here"),
            client.get("/v1/areas", headers={"origin": AT_HOME}),
            client.options(
                "/v1/rank", headers={"origin": AT_HOME, "access-control-request-method": "POST"}
            ),
        ]
        return [
            (
                each.status_code,
                {n: v for n, v in each.headers.items() if n not in ("x-request-id", "vary")},
                each.text,
            )
            for each in asked
        ]

    # Every route of the search answers the same, to the byte and to the header.
    assert answered(off) == answered(on)
    for _, headers, _ in answered(on):
        assert "x-content-type-options" not in headers and "set-cookie" not in headers


def test_starting_the_service_with_nothing_set_opens_no_file_of_accounts(tmp_path: Path):
    # In a process of its own, so that nothing a test has done stands in the way: every
    # file that is opened as a database is heard of, whoever opens it.
    code = (
        "import sys\n"
        "opened = []\n"
        "sys.addaudithook(lambda event, args: opened.append(args) "
        "if event == 'sqlite3.connect' else None)\n"
        "from burro_api.app import create_app, deps_from\n"
        "from burro_api.providers.choose import choose\n"
        "from burro_api.settings import Settings\n"
        "deps = deps_from(Settings.from_env({}), choose({}))\n"
        "app = create_app(deps)\n"
        "sys.exit(repr((opened, deps.accounts)))\n"
    )

    done = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        cwd=tmp_path,
        env={"PATH": ""},
    )

    assert done.stderr.strip() == "([], None)"
    assert list(tmp_path.iterdir()) == []


# On.


def test_with_accounts_on_the_file_is_opened_once_and_is_its_owners_alone(
    tmp_path: Path, opened: list[str]
):
    deps = deps_from(Settings.from_env(env(tmp_path)))

    assert deps.accounts is not None
    assert opened == [str(tmp_path / "accounts.db")]
    assert stat.S_IMODE((tmp_path / "accounts.db").stat().st_mode) == 0o600
    client = TestClient(create_app(deps))
    # Every route of accounts is served, and no more is opened however much is asked.
    for method, path in routes():
        answered = client.request(method, path, headers={"x-burro-website": SECRET} | JSON)
        assert answered.status_code != 404, (method, path)
    assert len(opened) == 1
    deps.accounts.close()


def test_the_contract_is_the_same_with_accounts_on_as_with_them_off(tmp_path: Path):
    on = deps_from(Settings.from_env(env(tmp_path)))
    off = deps_from(Settings.from_env({}))

    assert create_app(on).openapi() == create_app(off).openapi()
    assert on.accounts is not None
    on.accounts.close()


def test_the_command_line_names_what_accounts_need_and_never_what_was_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(uvicorn, "run", runs_nothing)
    wrong = env(
        tmp_path,
        BURRO_WEBSITE_SECRET=f"short-{CANARY}",
        BURRO_ACCOUNTS_SENDER=f"nobody-{CANARY}",
    )
    del wrong["BURRO_ACCOUNTS_DB"]
    for name, value in wrong.items():
        monkeypatch.setenv(name, value)

    assert main(["serve"]) == 2

    out, err = capsys.readouterr()
    assert out == "" and CANARY not in err
    assert err.splitlines() == [
        "error: accounts are on, and need these settings: "
        "BURRO_ACCOUNTS_DB, BURRO_ACCOUNTS_SENDER, BURRO_WEBSITE_SECRET"
    ]
    assert list(tmp_path.iterdir()) == []


def test_the_command_line_says_that_the_file_of_accounts_cannot_be_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(uvicorn, "run", runs_nothing)
    nowhere = tmp_path / f"not-here-{CANARY}" / "accounts.db"
    for name, value in env(tmp_path, BURRO_ACCOUNTS_DB=str(nowhere)).items():
        monkeypatch.setenv(name, value)

    assert main(["serve"]) == 2

    out, err = capsys.readouterr()
    assert out == "" and CANARY not in err
    assert err.splitlines() == ["error: the file of accounts could not be used [no_folder]"]


@pytest.mark.skipif(os.geteuid() == 0, reason="the one who runs the tests may write anywhere")
def test_the_command_line_says_that_the_file_of_accounts_may_not_be_written_to(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(uvicorn, "run", runs_nothing)
    # As on a volume that was just made: the folder is there, and is not the service's.
    folder = tmp_path / f"somebody-elses-{CANARY}"
    folder.mkdir()
    folder.chmod(0o555)
    for name, value in env(tmp_path, BURRO_ACCOUNTS_DB=str(folder / "accounts.db")).items():
        monkeypatch.setenv(name, value)

    try:
        assert main(["serve"]) == 2
    finally:
        folder.chmod(0o755)

    # It says that it is of accounts, and why, and names no path.
    out, err = capsys.readouterr()
    assert out == "" and CANARY not in err
    assert err.splitlines() == ["error: the file of accounts could not be used [not_permitted]"]
    assert list(folder.iterdir()) == []


def test_the_service_says_as_it_starts_that_accounts_are_on_and_nothing_of_how(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(uvicorn, "run", runs_nothing)
    for name, value in env(tmp_path).items():
        monkeypatch.setenv(name, value)
    configure_logging()

    assert main(["serve"]) == 0

    out, err = capsys.readouterr()
    lines = [json.loads(row) for row in out.splitlines()]
    assert [line["event"] for line in lines] == ["starting", "accounts_on"]
    assert set(lines[1]) == {"at", "level", "event"}
    written = out + err
    assert CANARY not in written and str(tmp_path) not in written and "127.0.0.1" not in written


def test_out_of_development_the_service_does_not_start_with_what_development_allows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    monkeypatch.setattr(uvicorn, "run", runs_nothing)
    # As it is deployed: it listens to every address, behind the host's own proxy.
    deployed = env(tmp_path, BURRO_HOST="0.0.0.0")  # noqa: S104
    for name, value in deployed.items():
        monkeypatch.setenv(name, value)

    assert main(["serve"]) == 2

    _, err = capsys.readouterr()
    assert err.splitlines() == [
        "error: accounts are on, and need these settings: BURRO_ACCOUNTS_DEVELOPMENT, BURRO_HOST"
    ]
    assert list(tmp_path.iterdir()) == []


def test_as_it_is_deployed_accounts_are_on_with_a_website_over_tls_and_no_sender_yet(
    tmp_path: Path,
):
    deployed = {
        "BURRO_ACCOUNTS": "on",
        "BURRO_ACCOUNTS_DB": str(tmp_path / "accounts.db"),
        "BURRO_ACCOUNTS_SITE": SITE,
        "BURRO_ALLOWED_ORIGINS": SITE,
        "BURRO_WEBSITE_SECRET": SECRET,
        "BURRO_ACCOUNTS_LIMITS_KEY": LIMITS_KEY,
        "BURRO_HOST": "0.0.0.0",  # noqa: S104
    }

    deps = deps_from(Settings.from_env(deployed))

    assert deps.accounts is not None and deps.accounts.cookies.secure
    assert deps.accounts.cookies.session == "__Host-burro_session"
    client = TestClient(create_app(deps))
    asked = client.post(
        "/v1/auth/link",
        headers={
            "x-burro-website": SECRET,
            "x-burro-client-address": "203.0.113.7",
            "origin": SITE,
            "x-burro-request": "1",
            "content-type": "application/json",
        },
        content=b'{"email": "marmalade.quokka@example.org"}',
    )
    assert (asked.status_code, asked.json()["error"]["code"]) == (503, "sign_in_unavailable")
    deps.accounts.close()
