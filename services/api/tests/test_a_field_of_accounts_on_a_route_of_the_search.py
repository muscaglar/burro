"""A route of the search says nothing of a field of accounts that it says of no other name.

An error says where a problem is by the names of our own fields, and keeps no
other: the name of a field that should not be there is something the sender
wrote. The names were read from every body there is, those of accounts among
them. So a body of route 1 that held "email" was refused with that name in its
path, and as an address that does not look like one, where the service that
had no accounts gave an empty path and said that it could not read what was
sent. With accounts off no answer of any route differs from what it was, and
with them on a route of the search knows no more of them.

A route of accounts keeps the names of its own fields, as it did.
"""

from pathlib import Path
from typing import Any, cast

import pytest
from burro_api.accounts.wire import BODIES as OF_ACCOUNTS
from burro_api.deps import Deps
from burro_api.errors import KNOWN_NAMES, MESSAGES
from burro_api.wire import BODIES, ErrorCode
from pydantic import BaseModel

from .accounts.support import Browser, turned_on
from .support import client_for, make_deps, searching, wire

# A body of each route of the search that takes one, which the route would answer.
SENT: dict[str, dict[str, Any]] = {
    "/v1/interpret": {"text": "leafy"},
    "/v1/rank": {"spec": wire(searching())},
    "/v1/explanations": {"spec": wire(searching())},
    "/v1/compare": {"area_ids": ["syn-n0001", "syn-n0002"], "spec": wire(searching())},
    "/v1/places/search": {"q": "Pellam"},
    "/v1/shares": {"spec": wire(searching())},
}


def names_of(bodies: tuple[type[BaseModel], ...]) -> set[str]:
    """Every name of a field that a schema of some bodies holds, however deep it lies."""

    def within(schema: object) -> set[str]:
        if isinstance(schema, dict):
            held = cast(dict[str, object], schema)
            own = set(cast(dict[str, object], held.get("properties", {})))
            return own.union(*(within(part) for part in held.values()))
        if isinstance(schema, list):
            return set[str]().union(*(within(part) for part in cast(list[object], schema)))
        return set()

    return set[str]().union(*(within(body.model_json_schema()) for body in bodies))


# The names that a body of accounts holds and no body of the search does.
OF_ACCOUNTS_ALONE = sorted(names_of(OF_ACCOUNTS) - names_of(BODIES))
NOT_READ = {
    "code": "invalid_request",
    "message": MESSAGES[ErrorCode.INVALID_REQUEST],
    "fields": [{"path": "", "problem": "unknown_field"}],
}


def on(folder: Path) -> Deps:
    return turned_on(folder).deps


def off(folder: Path) -> Deps:
    return make_deps()


def test_the_names_of_accounts_are_some_and_a_route_of_the_search_knows_none():
    assert {"email", "token", "search_id", "session_id"} <= set(OF_ACCOUNTS_ALONE)
    assert not KNOWN_NAMES & set(OF_ACCOUNTS_ALONE)


@pytest.mark.parametrize("accounts", [off, on], ids=["accounts off", "accounts on"])
@pytest.mark.parametrize("name", OF_ACCOUNTS_ALONE)
@pytest.mark.parametrize("path", SENT)
def test_a_route_of_the_search_says_of_a_field_of_accounts_what_it_says_of_any_other_name(
    tmp_path: Path, path: str, name: str, accounts: Any
):
    client = client_for(accounts(tmp_path))
    assert client.post(path, json=SENT[path]).is_success

    of_accounts = client.post(path, json=SENT[path] | {name: "x"})
    of_nobody = client.post(path, json=SENT[path] | {"zzz": "x"})

    assert of_accounts.status_code == of_nobody.status_code == 422
    assert of_accounts.json()["error"] == of_nobody.json()["error"] == NOT_READ


def test_a_route_of_accounts_keeps_the_names_of_its_own_fields(tmp_path: Path):
    browser = Browser(turned_on(tmp_path))

    no_address = browser.post("/v1/auth/link", {"email": 5})
    no_token = browser.post("/v1/auth/session", {"token": 5, "zzz": "x"})

    assert no_address.status_code == no_token.status_code == 422
    assert no_address.json()["error"]["code"] == "invalid_email"
    assert no_address.json()["error"]["fields"] == [{"path": "email", "problem": "wrong_type"}]
    assert no_token.json()["error"]["fields"] == [
        {"path": "token", "problem": "wrong_type"},
        {"path": "", "problem": "unknown_field"},
    ]
