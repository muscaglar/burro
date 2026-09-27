"""The iPhone app's generator has a rule for the contract as it stands, and guesses nothing.

`apps/ios/scripts/generate.py` writes the app's models and routes from
`contracts/openapi.json`. It needs python3 and nothing else, so what it makes of a
contract is held here, where no Mac is needed. Whether the files it wrote are in step
is the app's own check: `make -C apps/ios generate-check`.

Three things were found when the routes of accounts came into the contract, and each is
held by a contract that is made up for it:

1. A route may answer 202 where all goes well. The generator looked for 200 alone.
2. A route of accounts is asked by the website, and by the app not at all. It is listed
   apart, and is given no method of the client.
3. A record of accounts may bear a name the app's own code has already: `SearchState`.
   What only a route of accounts takes or gives is written under one name of its own.
"""

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "the_apps_generator", ROOT / "apps" / "ios" / "scripts" / "generate.py"
)
assert _SPEC is not None and _SPEC.loader is not None
generate = importlib.util.module_from_spec(_SPEC)
sys.modules["the_apps_generator"] = generate
_SPEC.loader.exec_module(generate)

Contract = dict[str, Any]


def ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/components/schemas/{name}"}


def record(**fields: Any) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": fields,
        "required": list(fields),
    }


def answers(status: str, name: str, *failures: str) -> dict[str, Any]:
    found: dict[str, Any] = {status: {"content": {"application/json": {"schema": ref(name)}}}}
    for failure in failures:
        found[failure] = {"content": {"application/json": {"schema": ref("ErrorEnvelope")}}}
    return found


def asked(
    operation_id: str,
    status: str = "200",
    gives: str = "Envelope_Thing_",
    takes: str | None = None,
    marked: list[str] | None = None,
) -> dict[str, Any]:
    """One route, as the contract writes it."""
    found: dict[str, Any] = {
        "operationId": operation_id,
        "description": f"What {operation_id} does.",
        "responses": answers(status, gives, "422"),
    }
    if takes is not None:
        found["requestBody"] = {"content": {"application/json": {"schema": ref(takes)}}}
    if marked is not None:
        found["tags"] = marked
    return found


def made_up() -> Contract:
    """A contract of two routes that the app asks, and nothing of accounts."""
    return {
        "info": {"title": "A made-up contract", "version": "3"},
        "paths": {
            "/v1/things": {
                "get": asked("list_things"),
                "post": asked("make_thing", takes="ThingBody"),
            },
        },
        "components": {
            "schemas": {
                "Meta": record(synthetic={"type": "boolean"}),
                "ErrorEnvelope": record(meta=ref("Meta"), message={"type": "string"}),
                "Kind": {"type": "string", "enum": ["plain", "fancy"]},
                "Thing": record(name={"type": "string"}, kind=ref("Kind")),
                "ThingBody": record(name={"type": "string"}),
                "Envelope_Thing_": record(meta=ref("Meta"), data=ref("Thing")),
            }
        },
    }


def with_accounts() -> Contract:
    """The same, with three routes of accounts. One record of theirs is named as the app's is."""
    contract = made_up()
    contract["paths"]["/v1/auth/link"] = {
        "post": asked("ask_for_link", "202", "Envelope_LinkAsked_", "LinkBody", ["accounts"])
    }
    contract["paths"]["/v1/me/searches"] = {
        "get": asked("list_searches", gives="Envelope_KeptSearch_", marked=["accounts"]),
        "delete": asked(
            "forget_search", gives="Envelope_KeptSearch_", takes="ForgetBody", marked=["accounts"]
        ),
    }
    contract["components"]["schemas"] |= {
        "LinkBody": record(email={"type": "string"}),
        "LinkAsked": record(lasts_minutes={"type": "integer"}),
        "ForgetBody": record(search_id={"type": "string"}),
        "SearchState": {"type": "string", "enum": ["ok", "release_changed"]},
        # It names a record that the app's routes give too, which stays where it was.
        "KeptSearch": record(state=ref("SearchState"), thing=ref("Thing")),
        "Envelope_LinkAsked_": record(meta=ref("Meta"), data=ref("LinkAsked")),
        "Envelope_KeptSearch_": record(meta=ref("Meta"), data=ref("KeptSearch")),
    }
    return contract


def routes(contract: Contract) -> str:
    return generate.routes(contract, "0" * 64)


def models(contract: Contract) -> str:
    return generate.models(contract, "0" * 64)


def part(text: str, begins: str) -> str:
    """One declaration of what was made, from the line that begins it to the brace that ends it.

    `begins` is the whole of how its line begins, with the spaces it stands in from.
    """
    at = text.index("\n" + begins) + 1
    indent = len(begins) - len(begins.lstrip())
    # A part that was cut out of what was made ends at a brace, with no line after it.
    end = (text + "\n").index("\n" + " " * indent + "}\n", at)
    return text[at:end]


def theirs_of(text: str) -> str:
    """The list of the routes of accounts, as it stands inside their name."""
    return part(text, "    public enum Route: ")


def values_of(text: str, name: str) -> dict[str, str]:
    """What one `var` of a list of routes answers, by the case it answers for."""
    begins = re.search(rf"^ *public var {name}: ", text, re.MULTILINE)
    assert begins is not None, name
    return dict(re.findall(r"case \.(\w+): return (.+)", part(text, begins[0])))


# The contract as it stands


def test_the_generator_has_a_rule_for_the_contract_as_it_stands():
    contract = json.loads(generate.CONTRACT.read_text(encoding="utf-8"))

    files = generate.wanted()

    assert {generate.MODELS_OUT, generate.ROUTES_OUT} <= set(files)
    every = {
        operation["operationId"]
        for methods in contract["paths"].values()
        for operation in methods.values()
    }
    written = files[generate.ROUTES_OUT].decode("utf-8")
    assert len(every) > 10
    assert [name for name in sorted(every) if f'= "{name}"' not in written] == []


def test_every_route_of_the_contract_as_it_stands_is_the_apps_to_ask_or_is_of_accounts():
    contract = json.loads(generate.CONTRACT.read_text(encoding="utf-8"))
    written = generate.routes(contract, "0" * 64)
    theirs = {
        operation["operationId"]
        for methods in contract["paths"].values()
        for operation in methods.values()
        if operation.get("tags") == ["accounts"]
    }
    ours = {
        operation["operationId"]
        for methods in contract["paths"].values()
        for operation in methods.values()
        if "tags" not in operation
    }

    asked_by_the_app: set[str] = set(
        re.findall(r'= "(\w+)"', part(written, "public enum APIRoute: "))
    )
    listed_apart: set[str] = set(re.findall(r'= "(\w+)"', theirs_of(written)))

    assert theirs, "the contract holds the routes of accounts"
    assert (asked_by_the_app, listed_apart) == (ours, theirs)


# What a route answers where all goes well


@pytest.mark.parametrize("status", ["200", "201", "202"])
def test_the_answer_of_a_route_is_what_it_gives_where_all_goes_well_whatever_its_number(
    status: str,
):
    contract = made_up()
    contract["paths"]["/v1/things"]["post"] = asked("make_thing", status, takes="ThingBody")

    written = routes(contract)

    assert "func makeThing(_ body: ThingBody) async -> Answer<Thing>" in written
    # What it fails with is every other answer, and never the one that went well.
    assert values_of(written, "failures")["makeThing"] == "[422]"


def test_a_route_of_accounts_says_which_number_it_answers_with():
    listed = theirs_of(routes(with_accounts()))

    assert values_of(listed, "answers") == {
        "askForLink": "202",
        "forgetSearch": "200",
        "listSearches": "200",
    }
    assert values_of(listed, "failures")["askForLink"] == "[422]"


@pytest.mark.parametrize("given", [[], ["200", "202"], ["204"]])
def test_a_route_with_no_one_answer_that_went_well_is_refused_and_nothing_is_guessed(
    given: list[str],
):
    contract = made_up()
    found: dict[str, Any] = {}
    for status in given:
        found |= answers(status, "Envelope_Thing_")
    # An answer of 204 holds nothing, so there is no record to read of it.
    if given == ["204"]:
        found = {"204": {"description": "Nothing."}}
    contract["paths"]["/v1/things"]["get"]["responses"] = found | answers("422", "ErrorEnvelope")

    with pytest.raises(generate.Unsupported, match="GET /v1/things"):
        routes(contract)


# The routes of accounts


def test_a_route_of_accounts_is_listed_apart_and_the_client_is_given_no_method_for_it():
    before, after = routes(made_up()), routes(with_accounts())

    listed = theirs_of(after)
    assert re.findall(r'case (\w+) = "(\w+)"', listed) == [
        ("askForLink", "ask_for_link"),
        ("forgetSearch", "forget_search"),
        ("listSearches", "list_searches"),
    ]
    assert values_of(listed, "method") == {
        "askForLink": ".post",
        "forgetSearch": ".delete",
        "listSearches": ".get",
    }
    assert values_of(listed, "template")["forgetSearch"] == '"/v1/me/searches"'
    # What each takes and gives is said, for whoever gives the app accounts.
    assert "        /// It takes `ForgetBody` and gives `KeptSearch`.\n" in listed
    assert "        /// It takes nothing and gives `KeptSearch`.\n" in listed
    # What the app asks, and every method of its client, is as it was with no accounts.
    for begins in (
        "public enum APIRoute: ",
        "public protocol BurroAPI: ",
        "public protocol RouteSending: ",
        "extension BurroAPI where Self: RouteSending ",
    ):
        assert part(after, begins) == part(before, begins)
    assert "Accounts" not in before and "askForLink" not in part(after, "public enum APIRoute: ")


def test_a_method_is_named_once_it_is_one_a_route_bears():
    before, after = routes(made_up()), routes(with_accounts())

    assert re.findall(r"    case (\w+) = ", part(before, "public enum HTTPMethod: ")) == [
        "get",
        "post",
    ]
    assert re.findall(r'    case (\w+) = "(\w+)"', part(after, "public enum HTTPMethod: ")) == [
        ("get", "GET"),
        ("post", "POST"),
        ("delete", "DELETE"),
    ]


def test_a_route_the_app_asks_is_still_held_to_a_get_and_a_post():
    contract = made_up()
    contract["paths"]["/v1/things"]["delete"] = asked("forget_thing", takes="ThingBody")

    with pytest.raises(generate.Unsupported, match="DELETE /v1/things"):
        routes(contract)


@pytest.mark.parametrize("marked", [["admin"], ["accounts", "admin"], ["Accounts"]])
def test_a_mark_the_generator_has_no_rule_for_is_refused(marked: list[str]):
    contract = made_up()
    contract["paths"]["/v1/things"]["get"]["tags"] = marked

    with pytest.raises(generate.Unsupported, match="GET /v1/things"):
        routes(contract)
    with pytest.raises(generate.Unsupported, match="GET /v1/things"):
        models(contract)


# The records of accounts


def test_what_only_a_route_of_accounts_takes_or_gives_is_written_under_one_name():
    before, after = models(made_up()), models(with_accounts())

    theirs = part(after, "public enum Accounts ")
    for name in ("LinkBody", "LinkAsked", "ForgetBody", "KeptSearch"):
        assert f"    public struct {name}: " in theirs
        assert f"\npublic struct {name}: " not in after
    # The app's own code has a `SearchState`. This one is `Accounts.SearchState`.
    assert "    public enum SearchState: " in theirs
    assert "\npublic enum SearchState: " not in after
    assert "        public let state: SearchState\n" in theirs
    # What a route of the app's gives too stays where it was, as it was.
    for begins in ("public struct Thing: ", "public enum Kind: ", "public struct ThingBody: "):
        assert part(after, begins) == part(before, begins)
        assert begins not in theirs.replace("    public", "public") or begins in before
    assert "        public let thing: Thing\n" in theirs
    assert "Accounts" not in before


def test_every_line_under_the_name_of_accounts_stands_further_in():
    theirs = part(models(with_accounts()), "public enum Accounts ")

    lines = theirs.splitlines()[1:]
    assert len(lines) > 40
    assert [line for line in lines if line.strip() and not line.startswith("    ")] == []


def test_a_body_of_accounts_is_made_by_whoever_sends_it_as_a_body_of_the_apps_is():
    theirs = part(models(with_accounts()), "public enum Accounts ")

    # A body leaves out what it has nothing to say in, and a record of the API's writes it.
    assert "public init(email: String)" in part(theirs, "    public struct LinkBody: ")


def test_the_name_of_accounts_is_written_wherever_a_route_of_theirs_is():
    # The list of the routes stands inside the name, so the name is there for it to stand in,
    # though every record a route of accounts names is one the app's routes name too.
    contract = made_up()
    contract["paths"]["/v1/me/thing"] = {"get": asked("my_thing", marked=["accounts"])}

    assert "\npublic enum Accounts {\n}\n" in models(contract)
    assert "\nextension Accounts {\n" in routes(contract)


def test_a_route_of_accounts_with_something_in_its_path_is_refused():
    contract = with_accounts()
    contract["paths"]["/v1/me/searches"]["get"]["parameters"] = [
        {"name": "search_id", "in": "path", "schema": {"title": "Search Id", "type": "string"}}
    ]

    with pytest.raises(generate.Unsupported, match="GET /v1/me/searches"):
        routes(contract)


def test_a_contract_with_nothing_of_accounts_makes_what_it_made_before():
    contract = made_up()
    other = copy.deepcopy(contract)
    other["paths"]["/v1/things"]["get"]["tags"] = []

    assert routes(other) == routes(contract)
    assert models(other) == models(contract)
    assert "Accounts" not in routes(contract) + models(contract)
