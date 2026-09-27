"""Accounts are off until they are turned on, and off is what the service was before them.

With nothing set no route of accounts exists: each is asked for here, by every method
it takes, and is answered as any address is that Burro has nothing at. The contract
lists them all the same, because a client is made from it.
"""

from typing import Any

import pytest
from burro_api.routes import accounts
from fastapi import FastAPI
from fastapi.routing import APIRoute

from ..support import client_for, make_deps, watching

JSON = {"content-type": "application/json"}
NOTHING_HERE: dict[str, Any] = {
    "code": "not_found",
    "message": "Burro has nothing at this address.",
    "fields": [],
}


def routes() -> list[tuple[str, str]]:
    """Every route of accounts as it is declared: a method and a path."""
    declared = [route for route in accounts.router.routes if isinstance(route, APIRoute)]
    return sorted((method, route.path) for route in declared for method in route.methods or ())


def test_the_routes_of_accounts_are_under_two_paths_and_no_other():
    assert len(routes()) == 17
    assert {path.split("/")[2] for _, path in routes()} == {"auth", "me"}


@pytest.mark.parametrize(("method", "path"), routes())
def test_with_accounts_off_no_route_of_accounts_exists(method: str, path: str):
    client = client_for(make_deps())

    answered = client.request(method, path, headers=JSON, content=b"{}")

    assert answered.status_code == 404
    assert answered.json()["error"] == NOTHING_HERE


@pytest.mark.parametrize(("method", "path"), routes())
def test_with_accounts_off_a_route_of_accounts_is_logged_as_no_route(method: str, path: str):
    with watching() as seen:
        seen.send(method, path, headers=JSON, content=b"{}")

    [line] = seen.events("request")
    assert (line["route"], line["status"], line["error_code"]) == ("unmatched", 404, "not_found")


def test_the_contract_lists_the_routes_of_accounts_though_none_is_served():
    app = client_for(make_deps()).app
    assert isinstance(app, FastAPI)

    document: dict[str, Any] = app.openapi()

    listed = {(method.upper(), path) for path, item in document["paths"].items() for method in item}
    assert set(routes()) <= listed
