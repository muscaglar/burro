"""The draft of the made-up city: unmistakably made up, the same every time, and whole.

docs/adr/0010 and rule 13 of AGENTS.md. It is made from the synthetic release alone.
"""

import json
import shutil
from collections import Counter
from pathlib import Path

import pytest
from desk.fill import draft, gate, layers, synthetic
from desk.fill.layers import Unfit

from .conftest import RELEASE, ROOT

# The files compile reads, which it holds to these columns in this order.
CURATED = ("areas.csv", "oa_to_area.csv", "aliases.csv", "name_evidence.csv")
# Words a made-up name may hold beside a name of the release.
PLAIN = (
    *("Made-up", "Theatre", "Stage", "School", "Community", "Hall", "Scout", "Group"),
    *("Hospital", "Gym", "Library", "Tap", "Cafe", "Parade", "Waterside", "Forest", "Heath"),
    *("Common", "Playing", "Field", "Road", "to", "ward", "East", "South"),
)


def files_of(folder: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(folder)): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def test_the_same_release_gives_the_same_draft_byte_for_byte(drafted: Path, tmp_path: Path):
    synthetic.make(RELEASE, tmp_path)
    again = files_of(tmp_path)
    assert again == files_of(drafted) and len(again) == 41


def test_the_draft_is_made_from_a_made_up_release_and_from_no_other(tmp_path: Path):
    real = tmp_path / "lon-2026-10-02-01"
    shutil.copytree(synthetic.release_in(RELEASE), real)
    manifest = json.loads((real / "manifest.json").read_text(encoding="utf-8"))
    (real / "manifest.json").write_text(
        json.dumps({**manifest, "synthetic": False}), encoding="utf-8"
    )
    with pytest.raises(Unfit, match="is not made up"):
        synthetic.make(real, tmp_path / "draft")
    assert not (tmp_path / "draft").exists()
    with pytest.raises(Unfit, match="No synthetic release"):
        synthetic.make(tmp_path / "nowhere", tmp_path / "draft")


def test_the_four_curated_files_have_the_columns_of_the_areas_design(drafted: Path):
    for name in CURATED:
        first = (drafted / name).read_text(encoding="utf-8").splitlines()[0]
        assert tuple(first.split(",")) == draft.TABLES[name], name


def test_every_cell_is_in_exactly_one_area(drafted: Path):
    rows = draft.read_table(drafted, "oa_to_area.csv")
    codes = [row["oa21cd"] for row in rows]
    drawn = draft.Draft.open(drafted, synthetic=True)
    assert len(codes) == len(set(codes)) == 1115 and set(codes) == set(drawn.cells)
    areas = {row["area_id"] for row in draft.read_table(drafted, "areas.csv")}
    assert {row["area_id"] for row in rows} == areas and len(areas) == 24
    assert all(row["basis"] == "auto" and not row["decided_by"] for row in rows)


def test_every_area_is_in_one_piece(drafted: Path):
    for group in ("quillhaven", "east-quillhaven", "south-quillhaven"):
        path = drafted / "layers" / group / "areas.geojson"
        for area in layers.read(path, synthetic=True)["features"]:
            assert area["geometry"]["type"] == "Polygon", area["id"]
            assert len(area["geometry"]["coordinates"]) == 1, area["id"]


def test_a_stray_part_of_an_area_joins_the_area_it_shares_most_sides_with():
    cells = {(0, 0): "a", (1, 0): "a", (2, 0): "b", (3, 0): "a", (3, 1): "b", (4, 0): "c"}
    synthetic._repair(cells)  # pyright: ignore[reportPrivateUsage]
    assert cells == {(0, 0): "a", (1, 0): "a", (2, 0): "b", (3, 0): "b", (3, 1): "b", (4, 0): "c"}


def test_the_outline_of_some_squares_is_drawn_once_round_them():
    bend = synthetic.outline([(0, 0), (1, 0), (0, 1)])
    assert bend["type"] == "Polygon" and len(bend["coordinates"]) == 1
    step = synthetic.STEP
    assert bend["coordinates"][0] == [
        [0.0, 0.0],
        [2 * step, 0.0],
        [2 * step, step],
        [step, step],
        [step, 2 * step],
        [0.0, 2 * step],
        [0.0, 0.0],
    ]
    apart = synthetic.outline([(0, 0), (5, 5)])
    assert apart["type"] == "MultiPolygon" and len(apart["coordinates"]) == 2
    ring = [(i, j) for i in range(3) for j in range(3) if (i, j) != (1, 1)]
    holed = synthetic.outline(ring)
    assert holed["type"] == "Polygon" and len(holed["coordinates"]) == 2
    corners = synthetic.outline([(0, 0), (1, 1)])
    assert corners["type"] == "MultiPolygon", "squares that meet at a corner are two shapes"


def test_a_shape_near_a_circle_is_more_compact_than_a_long_one():
    block = [(i, j) for i in range(3) for j in range(3)]
    strip = [(i, 0) for i in range(9)]
    assert synthetic.compactness(block) > synthetic.compactness(strip)


def test_no_two_areas_beside_each_other_are_one_colour(drafted: Path):
    held = draft.Draft.open(drafted, synthetic=True)
    colour = {
        cell["properties"]["area"]: cell["properties"]["colour"] for cell in held.cells.values()
    }
    assert len(colour) == 24 and all(0 <= each < layers.COLOURS for each in colour.values())
    for area_id, others in held.neighbours.items():
        assert others and all(colour[other] != colour[area_id] for other in others), area_id


def names_of(drafted: Path) -> list[str]:
    """Every name the draft holds that the release does not."""
    folder = drafted
    found = [row["alias"] for row in draft.read_table(folder, "aliases.csv")]
    found += [row["as_written"] for row in draft.read_table(folder, "name_evidence.csv")]
    found += [row["name"] for row in draft.read_table(folder, "kinds.csv")]
    found += [row["primary_borough"] for row in draft.read_table(folder, "areas.csv")]
    for row in draft.read_table(folder, "commons.csv"):
        found += [row["name"], row["match"]]
    for (_, layer), held in layers.read_all(folder / "layers", synthetic=True).items():
        if layer in ("wards", "centres", "roads", "names", "boroughs"):
            found += [feature["properties"]["name"] for feature in held["features"]]
    return [name for name in found if name]


def test_every_made_up_name_is_made_from_a_name_of_the_release(drafted: Path):
    # The pipeline holds the names of the release to a list of real places. A name made
    # here is a name of the release and plain words, so that list holds it too.
    release = synthetic.release_in(RELEASE)
    held = json.loads((release / "neighbourhoods.json").read_text(encoding="utf-8"))
    places = json.loads((release / "places.json").read_text(encoding="utf-8"))["places"]
    known = {word for area in held["neighbourhoods"] for word in area["name"].split()}
    known |= {
        word for area in held["neighbourhoods"] for word in (*area["aliases"], area["borough"])
    }
    known |= {word for place in places for word in place["name"].split()}
    names = names_of(drafted)
    assert len(names) > 400
    for name in names:
        words = [word for word in name.replace("-", " ").split() if not word.isdigit()]
        stray = [word for word in words if word not in known and word.title() not in known]
        planted = synthetic.OF_RESIDENTS[0].split()
        assert set(stray) <= {*PLAIN, *planted, "Made", "up", "green", "quay", "fields", "yard"}
        assert set(words) & known, name


def test_the_words_of_the_flag_for_one_publisher_are_true_of_every_name_it_is_planted_on(
    drafted: Path,
):
    """The made-up city plants the flag on a name that its one publisher writes at a point
    inside the area. So the words of the flag say that one publisher is not enough, and
    nothing of where a record lies: what the page says of an item is true of it."""
    flagged = {
        row["item"].removeprefix("n:")
        for row in draft.read_table(drafted, "flags.csv")
        if (row["queue"], row["flag"]) == ("names", "one_publisher")
    }
    inside = {
        row["area_id"]
        for row in draft.read_table(drafted, "name_evidence.csv")
        if row["role"] == "primary" and row["locates"] == "point_inside"
    }
    assert flagged & inside, "the made-up city flags a name whose record lies inside"
    asked = json.loads((ROOT / "tools" / "desk" / "questions.json").read_bytes())["queues"]
    words = [
        queue["flags"]["one_publisher"] for queue in asked if "one_publisher" in queue["flags"]
    ]
    assert len(words) == 3
    for said in words:
        assert "one is not enough" in said
        assert "point" not in said and "inside" not in said


def test_every_publisher_of_the_made_up_city_says_it_is_made_up(drafted: Path):
    rows = draft.read_table(drafted, "name_evidence.csv")
    assert Counter(row["source_id"] for row in rows) == {
        "synthetic-names": 27,
        "synthetic-items": 29,
        "synthetic-wards": 18,
        "synthetic-centres": 7,
    }
    assert all(row["record_id"].startswith("syn-r") and row["checked"] == "true" for row in rows)


def test_the_day_a_made_up_draft_is_made_on_is_the_day_of_its_release():
    assert synthetic.made_on(RELEASE) == "2026-09-23"


# The layers of the made-up city
GROUPS = ("all", "east-quillhaven", "quillhaven", "south-quillhaven")
BOROUGH = ("cells", "areas", "wards", "centres", "roads", "names", "seeds", "records")


def test_each_borough_has_every_layer_and_the_boroughs_are_in_all(drafted: Path):
    found = layers.found(drafted / "layers")
    assert tuple(found) == GROUPS
    assert found == {"all": ("boroughs",), **dict.fromkeys(GROUPS[1:], BOROUGH)}


def test_every_made_up_layer_is_made_from_made_up_sources_and_ids(drafted: Path):
    for (group, layer), held in layers.read_all(drafted / "layers", synthetic=True).items():
        assert all(gate.is_made_up(source) for source in held["desk"]["source_ids"]), layer
        assert all(feature["id"].startswith("syn-") for feature in held["features"]), group
        assert held["features"], f"{group}/{layer}"


def test_a_feature_holds_only_the_properties_of_the_design(drafted: Path):
    for (_, layer), held in layers.read_all(drafted / "layers", synthetic=True).items():
        for feature in held["features"]:
            assert set(feature["properties"]) == layers.LAYERS[layer][0], layer


def test_every_made_up_place_is_in_open_sea(drafted: Path):
    # The contract puts every synthetic coordinate in this box.
    for held in layers.read_all(drafted / "layers", synthetic=True).values():
        west, south, east, north = layers.bounds(held["features"]) or [0, 0, 0, 0]
        assert -0.20 <= west <= east <= 0.20 and -0.15 <= south <= north <= 0.15
