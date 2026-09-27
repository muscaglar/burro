"""An answer is said to stand only where the service that is asked would give the same one.

Four routes give an answer that a browser may keep, and each is tagged. A
browser asks each time whether what it holds still stands, and is answered 304
with no body where its tag is the one the service gives. The tag was the id of
the release, and the made-up city keeps its id however often it is built again
and whatever engine reads it. So the service that was published and the one
that was built after it gave one tag to two answers: of the page of one area,
two hundred sentences differ between them, and a browser that had been to the
first was told by the second that what it held still stood. A person who came
back read the words that had been taken away.

The tag now names the release and eight characters of what made the answer: the
release as it was loaded, with the hash of every file of it, the engine and the
contract. Every release here is made up.
"""

import dataclasses
import re
from collections.abc import Iterator
from typing import Any

import pytest
from burro_api import deps as held_by_the_service
from burro_api.deps import Deps
from burro_api.providers.terms import TERMS, Provider
from burro_core.release import InMemoryRelease

from .support import (
    FakeModelClient,
    client_for,
    make_deps,
    model_output,
    reader_asking,
    release,
    told_of,
)

KEPT = ("/v1/areas", "/v1/areas/geometry", "/v1/areas/syn-n0001", "/v1/meta")
A_TAG = re.compile(r'"syn-2026-09-23-01\.[0-9a-f]{8}"')
# What the service that was published gave: the id of the release, and for route 11 the id
# and what people were told.
AS_PUBLISHED = ('"syn-2026-09-23-01"', '"syn-2026-09-23-01.0abc8435"')


def tags(deps: Deps) -> dict[str, str]:
    client = client_for(deps)
    return {path: client.get(path).headers["etag"] for path in KEPT}


def built_again(**changed: Any) -> InMemoryRelease:
    """The made-up release under its own id, with something of its manifest changed."""
    found = release()
    return dataclasses.replace(found, manifest=found.manifest.replace(**changed))


@pytest.fixture
def another_engine(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(held_by_the_service, "ENGINE_VERSION", "9.9.9")
    yield


def test_a_tag_names_the_release_and_eight_characters_of_what_made_the_answer():
    found = tags(make_deps())

    assert all(A_TAG.fullmatch(tag) for tag in found.values()), found
    # The routes that are of the release alone share a tag, and route 11 has its own:
    # it says who reads what is typed as well.
    assert len({found[path] for path in KEPT[:3]}) == 1
    assert found["/v1/meta"] != found["/v1/areas"]


def test_the_same_service_gives_the_same_tag_each_time_it_is_started():
    assert tags(make_deps()) == tags(make_deps())


@pytest.mark.parametrize("held", AS_PUBLISHED)
def test_a_browser_that_holds_what_the_published_service_gave_is_answered_in_full(held: str):
    client = client_for(make_deps())

    for path in KEPT:
        answered = client.get(path, headers={"if-none-match": held})

        assert answered.status_code == 200, path
        assert answered.json()["meta"]["synthetic"] is True
        assert answered.headers["etag"] != held


def test_a_browser_that_holds_the_tag_it_was_given_is_told_that_it_still_stands():
    client = client_for(make_deps())

    for path in KEPT:
        given = client.get(path).headers["etag"]
        answered = client.get(path, headers={"if-none-match": given})

        assert (answered.status_code, answered.content) == (304, b""), path
        assert answered.headers["etag"] == given


def test_an_answer_of_another_engine_is_never_said_to_stand(
    request: pytest.FixtureRequest,
):
    before = tags(make_deps())
    request.getfixturevalue("another_engine")
    after = tags(make_deps())
    client = client_for(make_deps())

    for path in KEPT:
        assert before[path] != after[path], path
        answered = client.get(path, headers={"if-none-match": before[path]})
        assert answered.status_code == 200
        assert answered.json()["meta"]["engine_version"] == "9.9.9"


@pytest.mark.parametrize(
    "changed",
    [
        {"built_at": "2026-09-27T00:00:00Z"},
        {"seed": 20260927},
        {"changes_sha256": "0" * 64},
    ],
    ids=["built on another day", "from another seed", "with a file of changes"],
)
def test_a_release_that_is_built_again_under_its_id_is_never_said_to_stand(
    changed: dict[str, Any],
):
    before = tags(make_deps())
    again = make_deps(release=built_again(**changed))
    after = tags(again)
    client = client_for(again)

    for path in KEPT:
        assert A_TAG.fullmatch(after[path]) and before[path] != after[path], path
        assert client.get(path, headers={"if-none-match": before[path]}).status_code == 200
        assert client.get(path, headers={"if-none-match": after[path]}).status_code == 304


def test_a_file_of_the_release_that_holds_other_bytes_gives_another_tag():
    found = release()
    first, *rest = found.manifest.files
    other = first.replace(sha256="f" * 64)

    after = tags(make_deps(release=built_again(files=(other, *rest))))

    assert all(after[path] != tag for path, tag in tags(make_deps()).items())


def test_route_11_is_never_said_to_stand_where_people_are_told_of_another_reader():
    reads = reader_asking(FakeModelClient(model_output()))
    told = told_of(TERMS[Provider.GEMINI], with_settings=False)
    by_rules, by_a_model = make_deps(), make_deps(interpreter=reads, told=told)

    before, after = tags(by_rules), tags(by_a_model)

    assert before["/v1/meta"] != after["/v1/meta"]
    # What is of the release alone stands, whoever reads what is typed.
    assert [before[path] for path in KEPT[:3]] == [after[path] for path in KEPT[:3]]
    held = {"if-none-match": before["/v1/meta"]}
    assert client_for(by_a_model).get("/v1/meta", headers=held).status_code == 200


def test_a_tag_holds_nothing_of_the_engine_or_of_the_release_but_its_id():
    # Eight characters of a checksum: no version, no date and no hash is read from it.
    for tag in tags(make_deps()).values():
        assert (
            "1.19" not in tag
            and "2026-09-27" not in tag
            and len(tag) == len('"syn-2026-09-23-01.00000000"')
        )
