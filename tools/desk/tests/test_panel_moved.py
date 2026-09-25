"""The screen "What moved": the release the panel shows, held against one other.

The panel shows the committed synthetic release. The other release is the same city
with the air of one area lower and one measure gone, made in memory and never written.
What moved between them is worked out by the step `moved` of the pipeline, and the panel
answers with what that found. Every name and id is made up, and the panel is asked with
no port: `test_panel_server.py` asks every route it reads through the desk's own.
"""

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import TAGS
from burro_core.ids import City, FeatureId, TagId
from burro_pipeline.upkeep import moved
from desk import cli, fill, records, server
from desk.panel import look, routes

RELEASE = cli.FIXTURE / "syn-2026-09-23-01"
HIGHER, GONE = "syn-n0004", FeatureId.WATER_ACCESS


@pytest.fixture(scope="module")
def panel() -> routes.Panel:
    return routes.open_panel(RELEASE)


@pytest.fixture(scope="module")
def desk(tmp_path_factory: pytest.TempPathFactory, panel: routes.Panel) -> server.Desk:
    data = tmp_path_factory.mktemp("moved") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    return server.open_desk(data, cli.PAGE, cli.QUESTIONS, "r1", log=lambda _: None, panel=panel)


def before_it(held: look.Held) -> look.Held:
    """The release as it stood before: the air of one area stood lower by 2.5, and the
    release carried no measure of water."""
    release = held.release
    air = release.feature(HIGHER, FeatureId.AIR_NO2)
    assert air is not None and air.value is not None
    lower = float(f"{air.value - 2.5:.1f}")
    was = dataclasses.replace(
        release,
        metrics=tuple(one for one in release.metrics if one.feature_id is not GONE),
        features=tuple(
            row.replace(value=lower)
            if (row.area_id, row.feature_id) == (HIGHER, FeatureId.AIR_NO2)
            else row
            for row in release.features
            if row.feature_id is not GONE
        ),
    )
    return dataclasses.replace(held, release=was)


@pytest.fixture(scope="module")
def held_against(panel: routes.Panel) -> routes.Panel:
    """The panel, with the release it shows held against the release as it stood before."""
    found = routes.moved_since(before_it(panel.held), panel.held, panel.searches, cli.ROOT)
    return dataclasses.replace(panel, moved=found)


def answered(panel: routes.Panel, desk: server.Desk) -> dict[str, Any]:
    return panel.answer(desk, "moved", None, None)


def test_with_no_other_release_named_the_screen_says_how_to_name_one(
    panel: routes.Panel, desk: server.Desk
):
    assert answered(panel, desk) == {"moved": None, "says": routes.NO_OTHER}
    assert "make desk RELEASE=FOLDER BEFORE=FOLDER" in routes.NO_OTHER


def test_the_route_is_one_the_desk_reads_and_it_takes_no_word():
    assert "moved" in server.PANEL_READS
    assert server.route("/api/panel/moved") == ("/api/panel/moved", [])
    assert server.ROUTES["/api/panel/moved"] == server.GET
    assert server.route("/api/panel/moved/syn-2026-09-23-01") is None


def test_what_moved_is_what_the_step_of_the_pipeline_finds(
    held_against: routes.Panel, desk: server.Desk
):
    answer = answered(held_against, desk)
    found = answer["moved"]
    assert found == moved.compare(
        moved.Build(before_it(held_against.held).release, None),
        moved.Build(held_against.held.release, None),
        searches=held_against.searches,
    )
    assert answer["counts"] == moved.counted(found)
    # What is answered is plain values: it is sent to the page as it is.
    assert json.loads(json.dumps(found)) == found
    # A vibe that is a rough guide says so beside its name on this screen too. The step
    # writes no word of it: the desk reads it from the release that is shown.
    assert answer["rough"] == {"village_feel": look.rough_of(TAGS[TagId.VILLAGE_FEEL])}
    assert "Rough guide" not in json.dumps(found)


def test_it_says_the_measure_that_came_and_the_area_whose_figure_moved(
    held_against: routes.Panel, desk: server.Desk
):
    found = answered(held_against, desk)["moved"]
    assert [one["id"] for one in found["measures"]["came"]] == [GONE.value]
    (air,) = [one for one in found["measures"]["moved"] if one["id"] == "air_no2"]
    assert (air["changed"], air["up"], air["gained"], air["lost"]) == (1, 1, 0, 0)
    assert (air["middle"], air["most"]) == (2.5, 2.5)
    (most,) = air["moved_most"]
    assert (most["id"], most["name"], most["borough"]) == (HIGHER, "Dulcimer Green", "Quillhaven")
    assert (most["was"], most["now"], most["by"]) == (17.2, 19.7, 2.5)
    # The made-up city has no lock, so no file is compared.
    assert found["files"]["compared"] is False
    assert [one["id"] for one in found["searches"]] == [
        "the_founders_sentence",
        "a_family_buying_a_house",
        "nights_out_well_connected",
    ]


def test_the_sentence_a_search_was_read_from_is_not_in_what_is_answered(
    held_against: routes.Panel, desk: server.Desk
):
    said = json.dumps(answered(held_against, desk), ensure_ascii=False)
    for search in held_against.searches:
        assert len(search.says) > 20 and search.says not in said


def test_a_release_held_against_itself_has_moved_nothing(panel: routes.Panel, desk: server.Desk):
    found = routes.moved_since(panel.held, panel.held, panel.searches, cli.ROOT)
    counts = answered(dataclasses.replace(panel, moved=found), desk)["counts"]
    assert {name: count for name, count in counts.items() if count} == {
        "areas": 24,
        "measures": len(panel.held.release.metrics),
        "vibes": len(panel.held.release.vibes),
        "searches": 3,
    }


def test_the_made_up_city_is_never_held_against_a_release_of_another_city(
    panel: routes.Panel,
):
    release = panel.held.release
    real = dataclasses.replace(release, manifest=release.manifest.replace(city=City.LON))
    other = dataclasses.replace(panel.held, release=real)
    with pytest.raises(look.NotServed) as refused:
        routes.moved_since(other, panel.held, panel.searches, cli.ROOT)
    assert "not of one city" in str(refused.value)


# The command line


def test_the_desk_is_told_the_other_release_as_it_starts(desk: server.Desk):
    shown, said = cli.panel_for(RELEASE, desk.data, RELEASE)
    assert isinstance(shown, routes.Panel) and shown.moved is not None
    assert "The panel shows the release in " in said
    assert said.count("syn-2026-09-23-01") == 2 and " It is held against the release in " in said
    assert moved.counted(shown.moved)["measures_moved"] == 0
    parsed = cli.parser().parse_args(["serve", "--release", "a", "--before", "b"])
    assert (parsed.release, parsed.before) == (Path("a"), Path("b"))
    # With none named, the desk says nothing of another release.
    assert "held against" not in cli.panel_for(RELEASE, desk.data)[1]


def test_another_release_that_cannot_be_served_stops_the_desk_in_words(
    tmp_path: Path, desk: server.Desk
):
    (tmp_path / "syn-2026-09-23-09").mkdir()
    with pytest.raises(records.Unfit) as refused:
        cli.panel_for(RELEASE, desk.data, tmp_path / "syn-2026-09-23-09")
    assert str(refused.value).startswith("The release cannot be shown.")


def test_make_desk_hands_the_other_release_to_the_desk():
    recipe = (cli.ROOT / "Makefile").read_text(encoding="utf-8")
    assert "$(if $(BEFORE),--before $(BEFORE))" in recipe
    assert "BEFORE=FOLDER" in recipe
