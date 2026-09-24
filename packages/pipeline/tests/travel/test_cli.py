"""The step `travel` of the command line: what it takes, what it prints and what it refuses."""

import json
from pathlib import Path

import public_log
import pytest
from burro_pipeline.release.read import read_release
from burro_pipeline.travel import cli, engine, feed
from burro_pipeline.travel.engine import Settings
from burro_pipeline.travel.made_up import RELEASE_ID, town
from public_log import is_public

from .conftest import Routed, run

REPOSITORY = Path(__file__).parents[4]
NARROW = Settings(departures=6)


def test_the_step_routes_the_made_up_town_and_prints_one_public_line(routed: Routed):
    assert (routed.code, routed.err) == (0, "")
    (line,) = routed.out.splitlines()
    assert is_public(line)
    said = dict(pair.split("=") for pair in line.split())
    assert said | {"sha256": "", "manifest_sha256": ""} == {
        "step": "travel",
        "status": "ok",
        "release": RELEASE_ID,
        "stops": "16",
        "routes": "4",
        "trips": "756",
        "running": "502",
        "calls": "2654",
        "origins": "72",
        "destinations": "40",
        "departures": "120",
        "shards": "4",
        "areas": "24",
        "pairs": "960",
        "beyond": said["beyond"],
        "sha256": "",
        "manifest_sha256": "",
    }
    assert 0 < int(said["beyond"]) < 4 * 960


def test_what_it_writes_is_a_release_that_may_be_served(routed: Routed):
    release = read_release(routed.folder)

    assert release.manifest.synthetic and not release.manifest.preview
    assert release.manifest.release_id == RELEASE_ID
    assert release.travel_table.source_ids == ("synthetic",)
    # The day that was modelled is the date a journey carries.
    assert release.travel_table.as_of == "2026-09-22"
    assert release.travel_table.cutoff_minutes.model_dump() == {"pt": 120, "cycle": 60, "walk": 60}


def test_the_journeys_are_not_the_ones_the_city_was_first_drawn_with(routed: Routed):
    """They are worked out from the timetable, and everything else of the release is as it was."""
    release, first = read_release(routed.folder), town().release

    assert release.travel_table != first.travel_table
    assert release.travel_table.area_ids == first.travel_table.area_ids
    assert release.travel_table.destination_ids == first.travel_table.destination_ids
    assert (release.places, release.features, release.costs, release.station_rows) == (
        first.places,
        first.features,
        first.costs,
        first.station_rows,
    )


def test_no_time_is_under_two_minutes_and_none_is_left_not_computed(routed: Routed):
    travel = json.loads((routed.folder / "travel.json").read_text(encoding="utf-8"))
    cells = [
        cell
        for matrix in ("pt_typical", "pt_just_missed", "cycle", "walk")
        for row in travel[matrix]
        for cell in row
    ]

    assert len(cells) == 4 * 24 * 40
    assert None not in cells
    assert min(cell for cell in cells if cell != -1) >= 2
    # By public transport nobody does worse than on foot: they may walk all the way.
    for by_pt, on_foot in zip(travel["pt_typical"], travel["walk"], strict=True):
        assert all(w == -1 or 2 <= p <= w for p, w in zip(by_pt, on_foot, strict=True))


@pytest.mark.full
def test_the_same_town_routed_twice_gives_the_same_journeys():
    made = town()

    first, second = cli.journeys_of(made, NARROW), cli.journeys_of(made, NARROW)

    assert first == second


@pytest.mark.full
def test_the_number_of_shards_changes_nothing():
    made = town()

    assert cli.journeys_of(made, NARROW, shards=1) == cli.journeys_of(made, NARROW, shards=5)


@pytest.mark.full
def test_the_step_run_twice_writes_the_same_bytes(routed: Routed, tmp_path: Path):
    code, out, _ = run("--made-up", "--out", str(tmp_path))

    assert (code, out) == (0, routed.out)
    for file in sorted(routed.folder.iterdir()):
        assert (tmp_path / RELEASE_ID / file.name).read_bytes() == file.read_bytes(), file.name


def test_without_made_up_the_step_stops_and_names_the_rule(tmp_path: Path):
    code, out, err = run("--out", str(tmp_path))

    assert code == 2
    assert out == "step=travel status=refused engine_is_installed=1\n"
    assert is_public(out.strip())
    assert err == (
        "error: the engine that routes a real timetable is not installed [engine_is_installed]\n"
    )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("inside", ["data/fixtures/synthetic", "packages", "."])
def test_it_writes_nowhere_that_git_would_take_in(inside: str, monkeypatch: pytest.MonkeyPatch):
    if not (REPOSITORY / ".git").exists():
        pytest.skip("the tests are not in a working copy, so git would take nothing in")
    monkeypatch.chdir(REPOSITORY)

    code, out, err = run("--made-up", "--out", inside)

    assert (code, out) == (2, "step=travel status=refused\n")
    assert "is inside the repository" in err and "never committed" in err


@pytest.mark.parametrize(
    "arguments", [["--release-id", "lon-2026-10-02-01"], ["--built-at", "yesterday"]]
)
def test_a_release_that_is_not_made_up_or_a_time_that_is_no_time_is_refused(
    arguments: list[str], tmp_path: Path
):
    code, out, err = run("--made-up", "--out", str(tmp_path), *arguments)

    assert (code, out) == (2, "step=travel status=refused\n")
    assert err.startswith("error: ") and err.count("\n") == 1
    assert list(tmp_path.iterdir()) == []


def test_the_step_takes_no_word_that_could_name_a_place():
    """It works out every pair. Nothing it is given says which place anyone asked for."""
    options = cli.build()[1]["travel"]._actions  # pyright: ignore[reportPrivateUsage]

    assert sorted(option.dest for option in options if option.dest != "help") == [
        "built_at",
        "made_up",
        "out",
        "release_id",
        "seed",
    ]


def test_every_rule_the_step_may_name_is_on_the_public_list_and_no_other():
    assert set(feed.MEANING) | set(engine.MEANING) == public_log.TRAVEL_RULES
    assert not public_log.TRAVEL_RULES & (public_log.COUNTS | public_log.RULES)
    for rule in public_log.TRAVEL_RULES:
        assert is_public(f"step=travel status=refused {rule}=1")
