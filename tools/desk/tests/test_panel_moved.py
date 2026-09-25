"""The screen "What moved": the release the panel shows, held against one other.

The panel shows the committed synthetic release. The other release is the same city
with the air of one area lower and one measure gone, made in memory and never written.
What moved between them is worked out by the step `moved` of the pipeline, and the panel
answers with what that found. Every name and id is made up, and the panel is asked with
no port: `test_panel_server.py` asks every route it reads through the desk's own.

The other release may be a build of another catalogue, which is when a person most needs
the screen. It is then the same city written again as a build under the catalogue before
would have written it, in a folder of the test's own.
"""

import dataclasses
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from burro_core.catalogue import CATALOGUE_VERSION, FEATURES, TAGS
from burro_core.ids import City, FeatureId, TagId
from burro_pipeline.upkeep import moved
from burro_pipeline.upkeep.searches import NOT_IN_IT
from desk import cli, fill, records, server
from desk.panel import look, routes

RELEASE = cli.FIXTURE / "syn-2026-09-23-01"
HIGHER, GONE = "syn-n0004", FeatureId.WATER_ACCESS
NODE = shutil.which("node")


@pytest.fixture(scope="module")
def panel() -> routes.Panel:
    return routes.open_panel(RELEASE)


@pytest.fixture(scope="module")
def desk(tmp_path_factory: pytest.TempPathFactory, panel: routes.Panel) -> server.Desk:
    data = tmp_path_factory.mktemp("moved") / "desk-synthetic"
    fill.fill(cli.FIXTURE, data, synthetic=True)
    return server.open_desk(data, cli.PAGE, cli.QUESTIONS, "r1", log=lambda _: None, panel=panel)


def before_it(held: look.Held) -> moved.Build:
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
    return moved.Build(was, None)


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
        before_it(held_against.held),
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
    itself = moved.Build(panel.held.release, None)
    found = routes.moved_since(itself, panel.held, panel.searches, cli.ROOT)
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
    with pytest.raises(look.NotServed) as refused:
        routes.moved_since(moved.Build(real, None), panel.held, panel.searches, cli.ROOT)
    assert "not of one city" in str(refused.value)


# Held against a build of another catalogue

OLDER = CATALOGUE_VERSION - 1
# What the catalogue before did not hold, and what it labelled otherwise.
CAME, RELABELLED = FeatureId.HIGHSTREET_CONSERVED, FeatureId.AIR_NO2
WAS_LABELLED = "Nitrogen dioxide, as it was labelled then"
# The recipe Village feel had, of which the catalogue before placed no area.
VILLAGE_WAS = (
    ("independents_nearby", 25),
    ("centre_small", 20),
    ("centre_compact", 20),
    ("homes_pre1919", 20),
    ("conservation_cover", 15),
)


def _written(document: object) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()


def of_the_catalogue_before(to: Path, more: Any = None) -> Path:
    """The city that is shown, written again as a build under the catalogue before would
    have written it: a measure fewer, a recipe of other parts that placed no area, a label
    that was another, and no word of how sure a vibe is."""
    folder = to / RELEASE.name
    shutil.copytree(RELEASE, folder)
    found = {path.name: json.loads(path.read_bytes()) for path in sorted(folder.glob("*.json"))}
    manifest, catalogue = found.pop("manifest.json"), found["catalogue.json"]
    manifest["catalogue_version"] = catalogue["catalogue_version"] = OLDER
    catalogue["metrics"] = [one for one in catalogue["metrics"] if one["feature_id"] != CAME]
    rows = found["features.json"]["rows"]
    found["features.json"]["rows"] = [row for row in rows if row["feature_id"] != CAME]
    for vibe in catalogue["vibes"]:
        del vibe["sureness"]
        if vibe["tag_id"] == "village_feel":
            vibe["terms"] = [
                {"feature_id": part, "hundredths": share, "reading": "high"}
                for part, share in VILLAGE_WAS
            ]
            vibe["strip"] = True
    for row in found["tags.json"]["rows"]:
        if row["tag_id"] == "village_feel":
            row.update(raw=None, score=None, band=None, spread_low=None, spread_high=None)
    next(one for one in catalogue["metrics"] if one["feature_id"] == RELABELLED).update(
        label=WAS_LABELLED
    )
    if more is not None:
        more(found)
    for name, document in found.items():
        (folder / name).write_bytes(_written(document))
    for entry in manifest["files"]:
        content = (folder / entry["name"]).read_bytes()
        entry.update(sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))
    (folder / "manifest.json").write_bytes(_written(manifest))
    return folder


@pytest.fixture(scope="module")
def between_catalogues(tmp_path_factory: pytest.TempPathFactory) -> routes.Panel:
    """The panel, as the desk opens it where the other release is of the catalogue before."""
    older = of_the_catalogue_before(tmp_path_factory.mktemp("older"))
    return routes.open_panel(RELEASE, before=older)


def test_the_release_that_is_shown_is_held_against_a_build_of_another_catalogue(
    between_catalogues: routes.Panel, desk: server.Desk
):
    answer = answered(between_catalogues, desk)
    found = answer["moved"]
    assert (found["catalogue"]["before"], found["catalogue"]["after"]) == (
        OLDER,
        CATALOGUE_VERSION,
    )
    assert found["before"]["catalogue_version"] == OLDER
    assert [one["id"] for one in found["measures"]["came"]] == [CAME.value]
    assert answer["counts"] == moved.counted(found)
    assert json.loads(json.dumps(found)) == found
    # The release that is shown is read as it is served, as every screen of the panel is.
    assert between_catalogues.held.release.manifest.catalogue_version == CATALOGUE_VERSION


def test_it_says_what_came_and_went_of_the_catalogue_itself(
    between_catalogues: routes.Panel, desk: server.Desk
):
    answer = answered(between_catalogues, desk)
    catalogue = answer["moved"]["catalogue"]
    assert catalogue["measures"] == [
        {
            "id": RELABELLED.value,
            "label": FEATURES[RELABELLED].label,
            "names": [{"what": "label", "was": WAS_LABELLED, "now": FEATURES[RELABELLED].label}],
        }
    ]
    (village,) = catalogue["vibes"]
    assert (village["id"], village["rough"]) == ("village_feel", {"was": False, "now": True})
    assert [(one["id"], one["share"]) for one in village["parts_came"]] == [
        ("highstreet_conserved", 45),
        ("homes_density", 30),
    ]
    assert [one["id"] for one in village["parts_went"]] == [
        "independents_nearby",
        "centre_small",
        "centre_compact",
    ]
    assert [(one["id"], one["was"], one["now"]) for one in village["shares"]] == [
        ("homes_pre1919", 20, 15),
        ("conservation_cover", 15, 10),
    ]
    # The vibe placed no area before, and is a rough guide where it is shown.
    (bands,) = [one for one in answer["moved"]["vibes"]["moved"] if one["id"] == "village_feel"]
    assert bands["gained"] > 0 and (bands["changed"], bands["lost"]) == (0, 0)
    assert answer["rough"] == {"village_feel": look.rough_of(TAGS[TagId.VILLAGE_FEEL])}
    assert answer["counts"]["rough_came"] == 1 and answer["counts"]["parts_went"] == 3


def test_a_search_is_ranked_on_each_release_by_what_that_release_holds(
    between_catalogues: routes.Panel, desk: server.Desk
):
    searches = {one["id"]: one for one in answered(between_catalogues, desk)["moved"]["searches"]}
    asked = searches["nights_out_well_connected"]
    gone = NOT_IN_IT.format(label="Village feel")
    assert gone in asked["before"]["notes"] and gone not in asked["after"]["notes"]
    assert asked["same"] is False
    for other in ("the_founders_sentence", "a_family_buying_a_house"):
        assert searches[other]["same"] is True, other


def test_what_the_panel_answers_is_what_the_step_of_the_pipeline_finds_between_the_two(
    between_catalogues: routes.Panel, desk: server.Desk, tmp_path: Path
):
    older = of_the_catalogue_before(tmp_path)
    assert answered(between_catalogues, desk)["moved"] == moved.compare(
        moved.open_build(older),
        moved.open_build(RELEASE),
        searches=between_catalogues.searches,
    )


def newer_than_the_code(found: dict[str, Any]) -> None:
    found["catalogue.json"]["vibes"][0]["said_since"] = "what a later catalogue says"


def no_band(found: dict[str, Any]) -> None:
    placed = next(row for row in found["tags.json"]["rows"] if row["band"] is not None)
    placed.update(band=None, spread_low=None, spread_high=None)


@pytest.mark.parametrize(
    ("more", "rule"), [(newer_than_the_code, "shape_is_valid"), (no_band, "bands_match_raw")]
)
def test_another_release_that_cannot_be_read_stops_the_desk_and_the_words_say_why(
    tmp_path: Path, desk: server.Desk, more: Any, rule: str
):
    older = of_the_catalogue_before(tmp_path, more)
    with pytest.raises(look.NotServed) as refused:
        routes.open_panel(RELEASE, before=older)
    assert f"[{rule}]" in str(refused.value) and "said_since" not in str(refused.value)
    with pytest.raises(records.Unfit) as unfit:
        cli.panel_for(RELEASE, desk.data, older)
    assert str(unfit.value).startswith("The release cannot be shown.")


def test_the_release_that_is_shown_is_still_one_that_is_served(tmp_path: Path):
    """The panel shows every figure of it, and adjusts its recipes by core's own. So a
    build of another catalogue is held against, and is never the one that is shown."""
    older = of_the_catalogue_before(tmp_path)
    with pytest.raises(look.NotServed) as refused:
        routes.open_panel(older, before=RELEASE)
    assert "[versions_match]" in str(refused.value)


# The page draws what the desk answers

DRAWN = """
import { textOf, viewWhatMoved } from './tools/desk/page/panel-logic.mjs';
let sent = '';
process.stdin.setEncoding('utf8');
for await (const chunk of process.stdin) sent += chunk;
process.stdout.write(textOf(viewWhatMoved(JSON.parse(sent))));
"""


@pytest.mark.skipif(NODE is None, reason="Node is not on the PATH")
def test_the_page_draws_what_the_desk_answers_of_two_catalogues(
    between_catalogues: routes.Panel, desk: server.Desk
):
    """The panel's own page, handed what the desk answers, with no port and no browser."""
    answer = answered(between_catalogues, desk)
    assert NODE is not None
    ran = subprocess.run(
        [NODE, "--input-type=module", "-e", DRAWN],
        input=json.dumps(answer),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        cwd=cli.ROOT,
    )
    assert ran.returncode == 0, ran.stderr[-2000:]
    rough = look.rough_of(TAGS[TagId.VILLAGE_FEEL])
    assert isinstance(rough, dict)
    for words in (
        f"The catalogue: version {OLDER} before, and version {CATALOGUE_VERSION} after",
        "Measures: 1 came, and 0 went. Vibes: 0 came, and 0 went. Each is named below.",
        f"{FEATURES[RELABELLED].label} {RELABELLED.value} Its label {WAS_LABELLED} "
        f"{FEATURES[RELABELLED].label}",
        "Village feel: its recipe",
        f"{rough['label']}. {rough['why']}",
        "Village feel became a rough guide.",
        # A part that came had no share, and one that went has none: its cell is empty.
        f"{FEATURES[CAME].label} {CAME.value}  45 Came, read from its high end",
        f"{FEATURES[FeatureId.HOMES_DENSITY].label} homes_density  30 Came, read from its low end",
        f"{FEATURES[FeatureId.CENTRE_SMALL].label} centre_small 20  Went, read from its high end",
        f"{FEATURES[FeatureId.HOMES_PRE1919].label} homes_pre1919 20 15 Its share changed",
        f"Before: {NOT_IN_IT.format(label='Village feel')}",
    ):
        assert words in ran.stdout, words
    assert f"After: {NOT_IN_IT.format(label='Village feel')}" not in ran.stdout


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
