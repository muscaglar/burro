"""The layers made from files, on made-up files shaped like the publishers'.

Every file here is made up. The town is Quillhaven and Tallowgate, in squares
of 100 metres in the North Sea. The files have the publishers' own layouts: a
zip that holds a GeoPackage of several layers, tables with no header, a file
with no receipt.
"""

import csv
import json
import time
from pathlib import Path
from typing import Any

import pytest
from burro_pipeline.areas import (
    context,
    context_files,
    context_names,
    context_read,
    flags_files,
)
from burro_pipeline.areas.context_files import Made
from burro_pipeline.cells import shapes
from burro_pipeline.evidence.lock import LockError

from ..cells import support as cells
from ..cells.support import held
from .context_support import (
    ALDERWICK,
    BRACKENHYTHE,
    CENTRE_FIELDS,
    EAST,
    NAMES,
    NAMES_COLUMNS,
    NORTH,
    a_draft,
    above,
    contents,
    geopackage,
    inputs_of,
    name_row,
    open_names,
    zipped,
)

LONDON = (EAST - 500.0, NORTH - 500.0, EAST + 1_100.0, NORTH + 700.0)


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Made]:
    folder = tmp_path_factory.mktemp("layers")
    made = context_files.build(inputs_of(folder, contents()), folder / "out", draft=True)
    return folder / "out", made


def layer(out: Path, group: str, name: str, folder: str = "layers") -> dict[str, Any]:
    return json.loads((out / folder / group / f"{name}.geojson").read_text(encoding="utf-8"))


def named(found: dict[str, Any]) -> list[str]:
    return [feature["properties"]["name"] for feature in found["features"]]


def test_every_layer_the_gate_gives_is_written_for_every_borough(built: tuple[Path, Made]):
    out, _ = built

    written = sorted(path.relative_to(out).as_posix() for path in out.rglob("*.geojson"))

    assert written == [
        "layers/all/boroughs.geojson",
        *(f"layers/quillhaven/{name}.geojson" for name in ("centres", "names", "roads", "wards")),
        *(f"layers/tallowgate/{name}.geojson" for name in ("centres", "names", "roads", "wards")),
        "not_yet_drawn/quillhaven/water.geojson",
        "not_yet_drawn/tallowgate/water.geojson",
    ]


def test_the_boroughs_are_those_of_london_under_the_names_the_lookup_writes(
    built: tuple[Path, Made],
):
    found = layer(built[0], "all", "boroughs")

    assert [feature["id"] for feature in found["features"]] == ["E09000901", "E09000902"]
    assert named(found) == ["Quillhaven", "Tallowgate"]
    assert found["desk"]["source_ids"] == [
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "ons-output-areas-2021",
    ]


def test_a_ward_keeps_its_name_as_written_and_a_ward_outside_london_is_not_read(
    built: tuple[Path, Made],
):
    found = layer(built[0], "quillhaven", "wards")

    assert named(found) == ["Quillhaven West Ward", "Quillhaven East Ward", "Tallowgate Ward"]
    assert [feature["id"] for feature in found["features"]] == [
        "E05999001",
        "E05999002",
        "E05999003",
    ]


def test_a_town_centre_carries_its_name_and_its_class_as_written(built: tuple[Path, Made]):
    found = layer(built[0], "tallowgate", "centres")

    assert [feature["properties"] for feature in found["features"]] == [
        {"class": "District", "name": "Quillhaven Market"},
        {"class": "Major", "name": "Tallowgate Cross"},
    ]


def test_the_links_of_one_road_are_one_line_and_a_local_road_is_left_out(
    built: tuple[Path, Made],
):
    found = layer(built[0], "quillhaven", "roads")

    assert [(each["id"], each["properties"]) for each in found["features"]] == [
        ("syn-link-0001", {"class": "A Road", "name": "Tallowgate Row"}),
        ("syn-link-0003", {"class": "B Road", "name": "B9992"}),
    ]
    assert found["features"][0]["geometry"]["type"] == "LineString"


def test_the_names_are_places_stations_water_and_woods_and_never_a_postcode_or_a_road(
    built: tuple[Path, Made],
):
    found = layer(built[0], "quillhaven", "names")

    assert [feature["properties"] for feature in found["features"]] == [
        {"kind": "Railway Station", "name": "Quillhaven Halt"},
        {"kind": "Inland Water", "name": "Tallowgate Water"},
        {"kind": "Woodland Or Forest", "name": "Quillhaven Copse"},
        {"kind": "Suburban Area", "name": "Quillhaven"},
    ]


def test_the_tidal_water_is_kept_apart_until_the_desk_draws_such_a_layer(
    built: tuple[Path, Made],
):
    found = layer(built[0], "quillhaven", "water", "not_yet_drawn")

    assert found["desk"]["source_ids"] == ["ons-output-areas-2021", "os-boundary-line"]
    assert [feature["properties"] for feature in found["features"]] == [{"name": ""}]


def test_a_layer_made_from_a_file_with_no_receipt_says_so(built: tuple[Path, Made]):
    said = json.loads((built[0] / "layers.json").read_text(encoding="utf-8"))

    by_name = {each["layer"]: each for each in said["layers"]}
    assert by_name["centres"]["rests_on_a_file_with_no_receipt"] == ["gla-town-centre-boundaries"]
    assert by_name["wards"]["rests_on_a_file_with_no_receipt"] == []
    assert [each["has_receipt"] for each in said["read"]].count(False) == 1


def test_what_was_made_says_how_large_each_layer_is_and_what_the_gate_refused(
    built: tuple[Path, Made],
):
    out, made = built
    said = json.loads((out / "layers.json").read_text(encoding="utf-8"))

    assert said == json.loads(json.dumps(context_files.said(made)))
    for each in said["layers"]:
        assert each["the_gate_gave_it"]
        # With no draft, the layers that are the draft itself are not made, and say why.
        assert each["made"] == (each["layer"] not in context_files.OF_THE_DRAFT)
        assert bool(each["why_not"]) == (not each["made"])
        assert each["bytes"] == sum(
            (out / file["path"]).stat().st_size
            for file in said["files"]
            if file["layer"] == each["layer"]
        )
    assert [each["what"] for each in said["not_given"]] == ["parks", "rivers", "stations"]
    assert all(each["the_gate_said"] and each["in_its_place"] for each in said["not_given"])


def test_the_boroughs_are_listed_for_the_desk_to_ask(built: tuple[Path, Made]):
    with (built[0] / "boroughs.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    assert [(row["queue"], row["item"], row["group"], row["name"]) for row in rows] == [
        ("know", "quillhaven", "all", "Quillhaven"),
        ("know", "tallowgate", "all", "Tallowgate"),
    ]
    assert [row["output_areas"] for row in rows] == ["8", "4"]


def test_a_build_that_is_no_draft_makes_no_layer_from_a_file_with_no_receipt(tmp_path: Path):
    made = context_files.build(inputs_of(tmp_path, contents()), tmp_path / "out", draft=False)

    assert "input_has_one_receipt" in made.not_made["centres"]
    assert set(made.not_made) == {"centres", *context_files.OF_THE_DRAFT}
    assert not list((tmp_path / "out").rglob("centres.geojson"))
    assert list((tmp_path / "out").rglob("wards.geojson"))


def test_the_made_up_files_are_the_same_bytes_whenever_they_are_made(
    monkeypatch: pytest.MonkeyPatch,
):
    """A zip holds the time each member was written, to two seconds, unless it is given one.

    Two builds that fell either side of such a second read other files, and what they
    wrote of them differed: the test below failed in some runs only.
    """
    first = contents()
    a_day_on = time.time() + 86_400

    monkeypatch.setattr(time, "time", lambda: a_day_on)

    assert contents() == first


def test_the_same_files_give_the_same_layers_byte_for_byte(tmp_path: Path):
    for run in ("one", "two"):
        context_files.build(
            inputs_of(tmp_path / run, contents()), tmp_path / run / "out", draft=True
        )

    assert held(tmp_path / "one" / "out") == held(tmp_path / "two" / "out")


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    before = held(tmp_path / "store")

    context_files.build(inputs, tmp_path / "out", draft=True)

    assert held(tmp_path / "store") == before


def test_no_layer_holds_a_word_from_a_column_that_is_not_read(built: tuple[Path, Made]):
    """The made-up files hold one string in columns no layer reads."""
    for path in built[0].rglob("*"):
        if path.is_file():
            assert "Zzyzx" not in path.read_text(encoding="utf-8")


# The draft itself


@pytest.fixture(scope="module")
def drawn(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Made]:
    folder = tmp_path_factory.mktemp("drawn")
    drafted = a_draft(folder / "draft")
    inputs = inputs_of(folder, contents())
    return folder / "out", context_files.build(inputs, folder / "out", draft=True, drafted=drafted)


def test_every_cell_of_a_draft_is_drawn_in_the_colour_of_its_area(drawn: tuple[Path, Made]):
    found = layer(drawn[0], "quillhaven", "cells")

    assert len(found["features"]) == 12
    assert {
        (each["properties"]["area"], each["properties"]["colour"], each["properties"]["borough"])
        for each in found["features"]
    } == {(ALDERWICK, 0, "Quillhaven"), (BRACKENHYTHE, 1, "Tallowgate")}
    assert found["desk"]["source_ids"] == [
        "ons-oa21-lsoa21-msoa21-lad22-lookup",
        "ons-output-areas-2021",
    ]


def test_an_area_of_a_draft_is_outlined_under_its_name_and_its_seed_is_a_point(
    drawn: tuple[Path, Made],
):
    areas = layer(drawn[0], "tallowgate", "areas")
    seeds = layer(drawn[0], "tallowgate", "seeds")

    assert [(each["id"], each["properties"]) for each in areas["features"]] == [
        (ALDERWICK, {"name": "Alderwick"}),
        (BRACKENHYTHE, {"name": "Brackenhythe"}),
    ]
    assert [each["properties"] for each in seeds["features"]] == [
        {"area": ALDERWICK, "name": "Alderwick"},
        {"area": BRACKENHYTHE, "name": "Brackenhythe"},
    ]
    assert {each["geometry"]["type"] for each in seeds["features"]} == {"Point"}


def test_a_seed_is_drawn_under_the_name_its_own_record_writes_and_never_its_areas(
    tmp_path: Path,
):
    """An area may bear another name than the one it was grown from: its seed lies outside
    it. The dot then stands where the seed's record puts it, so it bears the seed's name.
    A seed the draft gives no name is drawn with none."""
    seeds = [
        {"area_id": ALDERWICK, "name": "Foxholt", "easting": 700_150, "northing": 400_100},
        {"area_id": BRACKENHYTHE, "easting": 700_500, "northing": 400_100},
    ]
    drafted = a_draft(tmp_path / "draft", **{"seeds.csv": seeds})
    inputs = inputs_of(tmp_path, contents())

    context_files.build(inputs, tmp_path / "out", draft=True, drafted=drafted)

    areas = layer(tmp_path / "out", "quillhaven", "areas")
    seeds_drawn = layer(tmp_path / "out", "quillhaven", "seeds")
    assert {each["id"]: each["properties"]["name"] for each in areas["features"]}[
        ALDERWICK
    ] == "Alderwick"
    assert [each["properties"] for each in seeds_drawn["features"]] == [
        {"area": ALDERWICK, "name": "Foxholt"},
        {"area": BRACKENHYTHE, "name": ""},
    ]


def test_the_seeds_of_a_draft_say_that_they_rest_on_a_file_with_no_receipt(
    drawn: tuple[Path, Made],
):
    assert drawn[1].unreceipted["seeds"] == ["gla-town-centre-boundaries"]
    assert drawn[1].not_made == {}


def test_a_draft_that_leaves_an_output_area_in_no_area_is_not_drawn(tmp_path: Path):
    drafted = a_draft(
        tmp_path / "draft", **{"oa_to_area.csv": [{"oa21cd": "E00999001", "area_id": ALDERWICK}]}
    )

    with pytest.raises(flags_files.Unfit, match="every output area once"):
        context_files.build(
            inputs_of(tmp_path, contents()), tmp_path / "out", draft=True, drafted=drafted
        )


def test_an_area_that_runs_into_the_next_borough_is_drawn_whole_under_its_own(tmp_path: Path):
    """The desk shows an area under the borough its draft names for it."""
    units = sorted(cells.LONDON, key=lambda unit: unit.oa)
    across = next(unit.oa for unit in units if unit.borough_name == "Tallowgate")
    given = [
        {
            "oa21cd": unit.oa,
            "area_id": ALDERWICK
            if unit.borough_name == "Quillhaven" or unit.oa == across
            else BRACKENHYTHE,
        }
        for unit in units
    ]
    areas = [
        {"area_id": ALDERWICK, "name": "Alderwick", "primary_borough": "Quillhaven"},
        {"area_id": BRACKENHYTHE, "name": "Brackenhythe", "primary_borough": "Tallowgate"},
    ]
    drafted = a_draft(tmp_path / "draft", **{"oa_to_area.csv": given, "areas.csv": areas})
    inputs = inputs_of(tmp_path, contents())
    made = Made(answers={})
    london = context_files.read_london(inputs, made)
    drawn = context.areas_drawn(
        london.outlines,
        {row["oa21cd"]: row["area_id"] for row in given},
        {ALDERWICK: "Alderwick", BRACKENHYTHE: "Brackenhythe"},
    )

    grounds = context_files.grounds_of(london, drafted, drawn)

    # Quillhaven is eight squares of a hectare. Its group holds the ninth, in Tallowgate.
    assert shapes.hectares(london.boroughs["E09000901"]) == pytest.approx(8.0)
    assert shapes.hectares(grounds["E09000901"]) == pytest.approx(9.0)
    # Tallowgate's group holds all of Tallowgate, the square that went to Alderwick too.
    assert shapes.hectares(grounds["E09000902"]) == pytest.approx(
        shapes.hectares(london.boroughs["E09000902"])
    )


def test_two_areas_side_by_side_are_never_one_colour():
    ring = {name: [other for other in "abcde" if other != name] for name in "abcde"}
    assert sorted(context.colours_of(ring).values()) == [0, 1, 2, 3, 4]

    # With more areas beside one than there are colours, the colour fewest have is given.
    crowd = {
        f"n{at:02d}": [f"n{other:02d}" for other in range(14) if other != at] for at in range(14)
    }
    given = context.colours_of(crowd)
    assert set(given.values()) == set(range(context.COLOURS))
    assert (given["n12"], given["n13"]) == (0, 1)


# The reader of names


def names_zip(tmp_path: Path, content: bytes) -> Path:
    path = tmp_path / "opname_csv_gb.zip"
    path.write_bytes(content)
    return path


def test_a_name_outside_the_ground_is_left_out(tmp_path: Path):
    found = context_names.read(names_zip(tmp_path, open_names()), "f-000000000000", LONDON)

    assert [each.name for each in found] == [
        "Quillhaven Halt",
        "Tallowgate Water",
        "Quillhaven Copse",
        "Quillhaven",
    ]
    assert "Made-up Halt" in {row["NAME1"] for row in NAMES}


def test_a_table_whose_rows_are_not_as_long_as_the_header_stops_the_step(tmp_path: Path):
    header = ",".join(NAMES_COLUMNS).encode()
    short = zipped(
        {"Doc/OS_Open_Names_Header.csv": header, "Data/TA00.csv": b"syn0000000009,,Quillhaven"}
    )

    with pytest.raises(LockError, match="input_is_as_described"):
        context_names.read(names_zip(tmp_path, short), "f-000000000000", LONDON)


def test_a_file_of_names_that_lacks_a_column_that_is_read_stops_the_step(tmp_path: Path):
    lacking = open_names(columns=[name for name in NAMES_COLUMNS if name != "LOCAL_TYPE"])

    with pytest.raises(LockError, match="input_is_as_described"):
        context_names.read(names_zip(tmp_path, lacking), "f-000000000000", LONDON)


def test_a_file_of_names_with_no_header_stops_the_step(tmp_path: Path):
    with pytest.raises(LockError, match="input_is_as_described"):
        context_names.read(names_zip(tmp_path, b"not a zip"), "f-000000000000", LONDON)


def test_a_name_is_kept_exactly_as_the_file_writes_it(tmp_path: Path):
    odd = name_row(
        "syn0000000008", "  quillhaven  HALT ", "transportNetwork", "Railway Station", 1, 1
    )

    found = context_names.read(names_zip(tmp_path, open_names([odd])), "f-000000000000", LONDON)

    assert [each.name for each in found] == ["  quillhaven  HALT "]


# The publishers' files


def test_a_file_with_no_receipt_is_read_for_a_draft_alone_and_says_that_it_has_none(
    tmp_path: Path,
):
    inputs = inputs_of(tmp_path, contents())

    taken = context_read.take(inputs, "gla-town-centre-boundaries", draft=True)

    assert not taken.has_receipt and taken.edition == ""
    assert [centre.name for centre in context_read.centres(taken)] == [
        "Quillhaven Market",
        "Tallowgate Cross",
    ]
    with pytest.raises(LockError, match="input_has_one_receipt"):
        context_read.take(inputs, "gla-town-centre-boundaries")


def test_a_file_that_has_a_receipt_is_read_through_it_draft_or_not(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())

    taken = context_read.take(inputs, "os-boundary-line", draft=True)

    assert taken.has_receipt and taken.edition == "2026-05"


def test_the_gate_is_asked_before_a_file_with_no_receipt_is_looked_for(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())

    for refused in ("os-open-rivers", "osm-geofabrik-greater-london", "no-such-source"):
        with pytest.raises(LockError, match="gate_refuses"):
            context_read.take(inputs, refused, draft=True)


def test_only_the_links_whose_box_meets_the_ground_are_read(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())

    found = context_read.links(context_read.take(inputs, "os-open-roads"), LONDON)

    assert [link.record_id for link in found] == [f"syn-link-000{n}" for n in (1, 2, 3, 4)]
    assert (found[2].of_class, found[2].kind, found[2].name, found[2].number) == (
        "B Road",
        "B Road",
        "",
        "B9992",
    )


def test_a_town_centre_counts_where_its_class_is_of_district_rank_or_above(tmp_path: Path):
    rows = (
        (("SYN00000001", "Quillhaven Market", "District Centre", 0.0, 0.0), above(0, 0)),
        (("SYN00000002", "Tallowgate Cross", "Local Centre", 0.0, 0.0), above(0, 1)),
        (("SYN00000003", "Quillhaven Cross", "Metropolitan", 0.0, 0.0), above(0, 2)),
    )
    files = contents() | {
        "centres": geopackage({"town_centres": ("geom", CENTRE_FIELDS, rows)}, indexed=False)
    }
    inputs = inputs_of(tmp_path, files)
    taken = context_read.take(inputs, "gla-town-centre-boundaries", draft=True)

    found = context_read.centres(taken)

    assert [(centre.rank, centre.counts) for centre in found] == [
        ("District Centre", True),
        ("Local Centre", False),
        ("Metropolitan", True),
    ]
