"""From a timetable to a search: the whole of the step, and what it leaves no record of.

The step routes the made-up town and writes a release. The API is then started
on the folder, as `burro-api serve` starts it, and asked to search. So this
test stands on both sides of the release folder, which is where the pipeline
and the API meet. It is the one module of the pipeline's tests that imports
the API, and no module of the pipeline does.

A place a person names is where they work. It is in the body of a request and
nowhere else. The step is never told of one: it works out every pair before
anyone asks. The release holds every pair, so nothing in it says which was
asked for. The service writes a line for each request, and the line of a
search to one place is the line of a search to any other.

Every name here is made up. The service is driven through the test client,
and not over a socket.
"""

import hashlib
import io
import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from burro_api import logs
from burro_api.app import create_app, deps_from
from burro_api.deps import Deps
from burro_api.settings import Settings
from burro_core import default_spec
from burro_core.ids import Mode, Provenance, PtBasis, Strictness, Tenure
from burro_core.release import TravelStatus
from burro_core.spec import Commute
from burro_pipeline.release.read import read_release
from fastapi.testclient import TestClient

from .conftest import Routed

WORKS, WORKS_NAME = "syn-p0021", "Cindermoor Works"
UNIVERSITY, UNIVERSITY_NAME = "syn-p0026", "Wexmoor University"
# Found nowhere else. It stands where a person would type the name of a place.
CANARY = "Zqxcanary Parva"
Body = dict[str, Any]


@dataclass
class Served:
    client: TestClient
    written: io.StringIO
    deps: Deps
    folder: Path

    def lines(self) -> list[Body]:
        return [json.loads(line) for line in self.written.getvalue().splitlines()]

    def everything_kept(self) -> str:
        """Every line the service wrote and every record it kept of a call."""
        records = self.deps.calls.records(self.deps.clock.now())
        return self.written.getvalue() + repr(records)


@pytest.fixture
def served(routed: Routed) -> Iterator[Served]:
    """The service, started on the release the step wrote. Logging is left as it was found.

    The service sets logging up for the whole process when it starts: the
    handlers and the level of the root, and the level of its own logger.
    """
    root, own = logging.getLogger(), logging.getLogger(logs.LOGGER)
    handlers, level, own_level = root.handlers[:], root.level, own.level
    written = io.StringIO()
    logs.configure_logging(written)
    deps = deps_from(Settings.from_env({"BURRO_RELEASE_DIR": str(routed.folder)}))
    try:
        yield Served(TestClient(create_app(deps)), written, deps, routed.folder)
    finally:
        root.handlers[:] = handlers
        root.setLevel(level)
        own.setLevel(own_level)


def search(place_id: str, minutes: int, mode: str = "pt", firm: bool = True) -> Body:
    """A search for anywhere within so many minutes of a place, as a client sends it."""
    journey = Commute(
        place_id=place_id,
        mode=Mode(mode),
        max_minutes=minutes,
        strictness=Strictness.HARD if firm else Strictness.SOFT,
        provenance=Provenance.STATED,
    )
    return default_spec(Tenure.RENT).replace(commutes=(journey,)).model_dump(mode="json")


def ranked(served: Served, spec: Body) -> Body:
    answer = served.client.post("/v1/rank", json={"spec": spec, "limit": 100})
    assert answer.status_code == 200, answer.json()
    return answer.json()["data"]


def hashes(folder: Path) -> dict[str, str]:
    return {
        file.name: hashlib.sha256(file.read_bytes()).hexdigest()
        for file in sorted(folder.iterdir())
    }


@pytest.mark.parametrize(
    ("place_id", "mode", "minutes"),
    [
        (WORKS, "pt", 40),
        (WORKS, "pt", 120),
        (WORKS, "cycle", 20),
        (UNIVERSITY, "pt", 25),
        (UNIVERSITY, "walk", 45),
    ],
)
def test_a_search_leaves_out_the_areas_the_timetable_puts_beyond_the_limit(
    served: Served, place_id: str, mode: str, minutes: int
):
    release = read_release(served.folder)
    place = release.place(place_id)
    assert place is not None
    times = {
        area.area_id: release.travel(
            area.area_id, place.destination_id, Mode(mode), PtBasis.TYPICAL
        )
        for area in release.neighbourhoods
        if area.rankable
    }
    too_far = {
        area_id
        for area_id, time in times.items()
        if time.status is TravelStatus.BEYOND_CUTOFF or (time.minutes or 0) > minutes
    }

    found = ranked(served, search(place_id, minutes, mode))

    left_out = {area["area_id"] for area in found["filtered"]}
    assert left_out == too_far
    assert {area["reason"] for area in found["filtered"]} <= {"commute_cap"}
    # An area of which too little is known is listed apart, whatever its journey.
    apart = {area["area_id"] for area in found["unranked"] if area["reason"] != "not_rankable"}
    assert {area["area_id"] for area in found["ranked"]} == set(times) - too_far - apart
    assert not apart & too_far
    # Some are left out and some are not, or the search would show nothing of the step.
    assert (0 < len(too_far) < len(times)) or minutes == 120
    for area in found["ranked"]:
        (leg,) = area["legs"]
        assert leg["minutes"] == times[area["area_id"]].minutes
        assert leg["minutes"] <= minutes


def test_the_time_a_result_shows_is_a_fact_with_the_day_that_was_modelled(served: Served):
    answer = served.client.post("/v1/explanations", json={"spec": search(WORKS, 40), "limit": 3})
    facts = [fact for fact in answer.json()["data"]["facts"] if fact["kind"] == "travel"]
    release = read_release(served.folder)
    place = release.place(WORKS)
    assert place is not None and facts

    for fact in facts:
        held = release.travel(fact["area_id"], place.destination_id, Mode.PT, PtBasis.TYPICAL)
        assert fact["slots"]["typical"] == str(held.minutes)
        assert fact["as_of"] == "2026-09-22"
        assert [source["source_id"] for source in fact["sources"]] == ["synthetic"]
        assert fact["synthetic"] is True


def test_every_answer_says_the_release_is_made_up(served: Served):
    answers = [
        served.client.get("/v1/meta"),
        served.client.post("/v1/rank", json={"spec": search(WORKS, 40)}),
        served.client.post("/v1/rank", json={"spec": search("syn-p9999", 40)}),
    ]

    assert [answer.status_code for answer in answers] == [200, 200, 422]
    for answer in answers:
        assert answer.headers["X-Burro-Synthetic"] == "true"
        assert answer.json()["meta"]["synthetic"] is True
        assert answer.json()["meta"]["release_id"] == "syn-2026-09-24-07"


# What no record may hold


def test_the_step_is_never_told_of_a_place_and_prints_none(routed: Routed):
    release = read_release(routed.folder)
    named = [
        *(place.place_id for place in release.places),
        *(place.name for place in release.places),
        *(end.destination_id for end in release.destinations),
        *(area.area_id for area in release.neighbourhoods),
        *(area.name for area in release.neighbourhoods),
    ]

    said = routed.out + routed.err

    assert not [name for name in named if name in said]


def test_the_release_holds_every_pair_so_nothing_in_it_says_which_was_asked_for(routed: Routed):
    release = read_release(routed.folder)
    table = release.travel_table

    assert len(table.area_ids) == len(release.neighbourhoods) == 24
    assert len(table.destination_ids) == len(release.destinations) == 40
    assert {place.destination_id for place in release.places} == set(table.destination_ids)
    for matrix in (table.pt_typical, table.pt_just_missed, table.cycle, table.walk):
        assert all(len(row) == 40 and None not in row for row in matrix)


def test_a_search_changes_nothing_of_the_release(served: Served):
    before = hashes(served.folder)

    for place_id in (WORKS, UNIVERSITY):
        ranked(served, search(place_id, 40))
    served.client.post("/v1/interpret", json={"text": f"30 minutes to {WORKS_NAME}"})
    served.client.post("/v1/shares", json={"spec": search(WORKS, 40)})

    assert hashes(served.folder) == before
    assert sorted(path.name for path in served.folder.parent.iterdir()) == [served.folder.name]


def test_the_place_that_was_asked_for_is_in_no_line_and_no_record(served: Served):
    release = read_release(served.folder)
    place = release.place(WORKS)
    assert place is not None
    spec = search(WORKS, 40)

    read = served.client.post("/v1/interpret", json={"text": f"at most 30 minutes to {WORKS_NAME}"})
    ranked(served, spec)
    served.client.post("/v1/explanations", json={"spec": spec})
    served.client.post("/v1/compare", json={"spec": spec, "area_ids": ["syn-n0003", "syn-n0001"]})
    served.client.post("/v1/places/search", json={"q": WORKS_NAME})
    served.client.post("/v1/shares", json={"spec": spec, "exact_destinations": True})

    assert read.json()["data"]["spec"]["commutes"][0]["place_id"] == WORKS
    kept = served.everything_kept().casefold()
    assert len(served.lines()) >= 6
    for word in (WORKS, WORKS_NAME, "cindermoor", place.destination_id, "syn-p", "syn-d", "syn-n"):
        assert word.casefold() not in kept


def test_the_line_of_a_search_to_one_place_is_the_line_of_a_search_to_any_other(served: Served):
    for place_id, minutes in ((WORKS, 40), (UNIVERSITY, 25), (WORKS, 90)):
        ranked(served, search(place_id, minutes))

    first, second, third = (
        {key: value for key, value in line.items() if key not in ("at", "request_id", "latency_ms")}
        for line in served.lines()
    )

    assert first == second == third
    assert first == {
        "engine_version": first["engine_version"],
        "event": "request",
        "level": "info",
        "method": "POST",
        "preview": False,
        "release_id": "syn-2026-09-24-07",
        "route": "/v1/rank",
        "status": 200,
        "synthetic": True,
    }


def test_a_place_is_named_in_the_body_of_a_request_and_never_in_its_address(served: Served):
    """No route that searches can be asked with `GET`, so no place can stand in an address."""
    for route in ("rank", "interpret", "explanations", "compare", "places/search"):
        asked = served.client.get(f"/v1/{route}?place_id={WORKS}&q={CANARY}")
        assert asked.status_code == 405, route
        assert WORKS not in asked.text and CANARY not in asked.text

    kept = served.everything_kept()
    assert WORKS not in kept and CANARY not in kept and "place_id" not in kept


# A place that is not in the table


def test_a_place_the_release_does_not_hold_is_refused_and_not_repeated(served: Served):
    answer = served.client.post("/v1/rank", json={"spec": search("syn-p9999", 40)})

    assert answer.status_code == 422
    assert answer.json()["error"] == {
        "code": "unknown_place",
        "message": "The spec names a place this release does not have.",
        "fields": [{"path": "spec.commutes[0].place_id", "problem": "unknown_place"}],
    }
    assert "syn-p9999" not in answer.text
    assert "syn-p9999" not in served.everything_kept()


def test_a_name_that_is_the_name_of_no_place_finds_nothing_and_is_asked_about(served: Served):
    found = served.client.post("/v1/places/search", json={"q": CANARY})
    read = served.client.post("/v1/interpret", json={"text": f"30 minutes to {CANARY}"})

    assert found.json()["data"] == {"places": []}
    data = read.json()["data"]
    # No journey is made to a place that was guessed at. The person is asked, with no offers.
    assert (data["status"], data["spec"]["commutes"], data["places"]) == ("clarify", [], [])
    assert data["clarify"] == [{"group": "commute_ops", "index": 0, "options": []}]
    assert CANARY.casefold() not in (read.text + found.text).casefold()
    assert CANARY.casefold() not in served.everything_kept().casefold()


def test_a_limit_past_what_was_routed_is_refused(served: Served):
    """The release routed to 60 minutes on foot. A limit of 90 could not be tested."""
    answer = served.client.post("/v1/rank", json={"spec": search(WORKS, 90, "walk")})

    assert answer.status_code == 422
    assert answer.json()["error"]["code"] == "invalid_spec"
