"""The draft as it is written: the evidence of each name, the ids, and the files for the desk.

Every name here is made up. `names_support.py` draws the town.
"""

import csv
import io
import json
import re
from pathlib import Path

import pytest
from burro_core.ids import AREA_ID_PATTERN, SLUG_PATTERN
from burro_pipeline.areas import names_cli, names_draft, names_evidence
from burro_pipeline.areas.names_candidates import Match
from burro_pipeline.areas.names_evidence import Row
from burro_pipeline.areas.seeds import Rules, Tier
from burro_pipeline.fetch.store import FOLDER_VARIABLE

from ..cells.support import CANARY
from ..cells.support import held as every_file
from .names_support import CENTRES, LINE, NAMES, RULES, drafted, given, held, seed, sha256_of

# The columns of the three files of names, as the review desk reads them.
DESK = {
    "draft/areas.csv": (
        *("area_id", "slug", "name", "primary_borough"),
        *("seed_record", "review_state", "superseded_by"),
    ),
    "draft/aliases.csv": ("alias", "area_id", "kind", "source_id", "record_id"),
    "draft/name_evidence.csv": (
        *("area_id", "name", "role", "source_id", "record_id", "as_written", "field"),
        *("locates", "data_date", "retrieved_on", "snapshot_sha256", "checked"),
        *("chosen_by", "chosen_on"),
    ),
    "draft/flags_names.csv": ("queue", "item", "flag"),
}
# What whoever gives output areas to areas reads a seed by, and whoever flags a border.
SEED_COLUMNS = {"seed_id", "area_id", "easting", "northing", "weight", "name"}
# Words that would say who lives somewhere. No column of a draft is named for one.
ABOUT_RESIDENTS = re.compile(
    r"resident|people|population|person|age|ethnic|religio|income|depriv|price|rent|tenure"
)


def tables() -> dict[str, list[dict[str, str]]]:
    found: dict[str, list[dict[str, str]]] = {}
    for name, content in names_draft.written(drafted()).items():
        if name.endswith(".csv"):
            found[name] = list(csv.DictReader(io.StringIO(content.decode("utf-8"), newline="")))
    return found


# The evidence of a name


def test_every_area_name_rests_on_a_checked_source():
    """Every area has a row that puts its name on the map, and one that says who writes it.

    The design asks for two publishers. Where there is one, the name is marked
    and the founder decides: it is never passed in silence.
    """
    marked = {look.key for look in drafted().looks if look.mark.value == "one_publisher"}
    by_area: dict[str, list[Row]] = {}
    for row in drafted().rows:
        if row.role == names_evidence.PRIMARY and row.writes:
            by_area.setdefault(row.area_id, []).append(row)
    for area in drafted().seeds.areas:
        rows = by_area[drafted().area_ids[area.key]]
        assert any(row.locates == names_evidence.POINT_INSIDE for row in rows) or any(
            row.locates == names_evidence.POLYGON_OVERLAP for row in rows
        )
        publishers = {row.record.publisher for row in rows}
        assert (len(publishers) < 2) == (area.key in marked)
        assert all(row.fuller()["checked"] == "true" for row in rows)


def test_a_row_holds_the_name_exactly_as_the_record_writes_it():
    written = {
        (record.source_id, record.record_id): record.as_written
        for record in drafted().candidates.records
    }
    for row in drafted().rows:
        if row.field == "NAME2":
            continue
        assert written[(row.record.source_id, row.record.record_id)] == row.as_written


def test_a_row_says_the_file_it_was_found_in_and_the_day_that_file_was_fetched():
    (own,) = (row for row in drafted().rows if row.name == "Alderwick" and row.field == "NAME1")
    found = own.fuller()
    assert found["source_id"] == NAMES and found["record_id"] == "osgb9000000000000001"
    assert found["snapshot_sha256"] == sha256_of("names")
    assert (found["data_date"], found["retrieved_on"]) == ("2021-12", "2026-09-23")
    assert (found["role"], found["locates"], found["checked"]) == (
        "primary",
        "point_inside",
        "true",
    )
    assert (found["chosen_by"], found["chosen_on"]) == ("", "")
    assert (found["publisher"], found["has_receipt"]) == ("Ordnance Survey", "true")


def test_a_row_from_the_file_with_no_receipt_says_so_and_puts_nothing_in_its_place():
    rows = [row.fuller() for row in drafted().rows if row.record.source_id == CENTRES]
    assert rows
    for row in rows:
        assert row["has_receipt"] == "false"
        assert (row["data_date"], row["retrieved_on"]) == ("", "")
        assert row["snapshot_sha256"] == sha256_of("centres")


def test_a_second_publisher_has_a_row_of_its_own_under_the_same_name():
    found = {
        (row.record.source_id, row.as_written, row.match, row.locates)
        for row in drafted().rows
        if row.name == "Alderwick"
    }
    assert found == {
        (NAMES, "Alderwick", Match.SAME, "point_inside"),
        (CENTRES, "Alderwick", Match.SAME, "polygon_overlap"),
        (LINE, "Alderwick Ward", Match.SAME, "polygon_overlap"),
    }


def test_a_label_that_only_holds_a_name_is_kept_out_of_the_designs_rows():
    """So that nobody counts it as a second publisher of the name."""
    held_in = [row for row in drafted().rows if row.name == "Kindlewharf" and not row.writes]
    assert [(row.as_written, row.match) for row in held_in] == [
        ("Kindlewharf High Street", Match.HELD)
    ]
    design = tables()["draft/name_evidence.csv"]
    assert "Kindlewharf High Street" not in {
        row["as_written"] for row in design if row["name"] == "Kindlewharf"
    }
    fuller = tables()["name_records.csv"]
    assert "held" in {row["match"] for row in fuller if row["name"] == "Kindlewharf"}


def test_an_outline_that_does_not_hold_the_place_locates_nothing_yet():
    (row,) = (
        row
        for row in drafted().rows
        if row.name == "Cindermoor" and row.record.source_id == CENTRES
    )
    assert (row.match, row.locates, row.metres) == (Match.PART, "label_only", 450.0)


def test_a_name_that_is_no_area_has_its_rows_under_the_area_it_is_a_name_of():
    rows = [row for row in drafted().rows if row.name == "Foxholt"]
    assert {row.area_id for row in rows} == {drafted().area_ids[seed("Alderwick").key]}
    assert {row.role for row in rows} == {"alias"}
    wide = [row for row in drafted().rows if row.name == "Quillhaven"]
    assert {row.role for row in wide} == {"wide"} and len({row.area_id for row in wide}) == 5


def test_a_second_name_of_a_record_is_another_name_of_the_same_ground():
    (row,) = (row for row in drafted().rows if row.name == "Lantern Yard")
    assert (row.role, row.field, row.as_written) == ("alias", "NAME2", "Lantern Yard")
    assert row.area_id == drafted().area_ids[seed("Kindlewharf").key]
    aliases = tables()["draft/aliases.csv"]
    assert {"alias": "Lantern Yard", "kind": "same_ground"}.items() <= next(
        row for row in aliases if row["alias"] == "Lantern Yard"
    ).items()


# Ids and slugs


def test_every_place_has_an_id_and_the_populated_places_come_first():
    ids = drafted().area_ids
    assert len(set(ids.values())) == len(ids) == 14
    assert all(re.fullmatch(AREA_ID_PATTERN, each) for each in ids.values())
    assert ids[seed("Alderwick").key] == "lon-n0001"
    assert ids[seed("Osierholm").key] == "lon-n0014"


def test_an_id_that_an_earlier_draft_gave_is_kept_and_a_new_place_is_given_the_next():
    places = list(drafted().candidates.places)
    earlier = names_evidence.ids(places[:3] + places[5:])
    assert sorted(earlier.values()) == [f"lon-n{number:04d}" for number in range(1, 13)]
    again = names_evidence.ids(places, earlier)
    assert all(again[key] == earlier[key] for key in earlier)
    assert {again[each.key.key] for each in places[3:5]} == {"lon-n0013", "lon-n0014"}
    # A place that the next draft no longer holds keeps its id, and nobody else is given it.
    fewer = names_evidence.ids(places[1:], again)
    assert again[places[0].key.key] not in fewer.values()


def test_an_id_is_never_given_twice(tmp_path: Path):
    places = list(drafted().candidates.places)
    twice = {places[0].key.key: "lon-n0001", places[1].key.key: "lon-n0001"}
    with pytest.raises(ValueError, match="given twice"):
        names_evidence.ids(places, twice)
    names_draft.write(tmp_path, drafted())
    assert names_draft.read_ids(tmp_path / "ids.csv") == dict(drafted().area_ids)


def test_a_slug_is_the_name_in_lower_case_and_the_borough_is_added_where_two_share_a_name():
    found = names_draft.make(held(), RULES, points=3, publishers=1)
    slugs = {(each.name, each.place.key.kind): found.slugs[each.key] for each in found.seeds.areas}
    assert slugs[("Alderwick", "Other Settlement")] == "alderwick"
    assert slugs[("Farrowmere", "Suburban Area")] == "farrowmere-quillhaven"
    assert slugs[("Farrowmere", "Village")] == "farrowmere-tallowgate"
    assert len(set(slugs.values())) == len(slugs)
    assert all(re.fullmatch(SLUG_PATTERN, slug) for slug in slugs.values())


# The files


def test_the_files_of_names_have_the_columns_the_review_desk_reads():
    found = names_draft.written(drafted())
    for name, columns in DESK.items():
        header = found[name].decode("utf-8").splitlines()[0]
        assert tuple(header.split(",")) == columns, name


def test_the_seeds_have_the_columns_the_other_builders_read_and_hold_the_areas_alone():
    seeds = tables()["seeds.csv"]
    assert set(seeds[0]) >= SEED_COLUMNS
    assert sorted(row["name"] for row in seeds) == sorted(
        each.name for each in drafted().seeds.areas
    )
    assert len({row["seed_id"] for row in seeds}) == len({row["area_id"] for row in seeds}) == 5
    assert tables()["draft/seeds.csv"] == seeds
    alderwick = next(row for row in seeds if row["name"] == "Alderwick")
    assert (alderwick["easting"], alderwick["northing"], alderwick["weight"]) == (
        "700750",
        "400750",
        "9",
    )


def test_every_name_that_is_no_area_names_an_area_that_the_draft_holds():
    found = tables()
    areas = {row["area_id"] for row in found["draft/areas.csv"]}
    assert len(areas) == len(found["draft/areas.csv"]) == 5
    assert {row["area_id"] for row in found["draft/aliases.csv"]} <= areas
    assert {row["area_id"] for row in found["draft/name_evidence.csv"]} <= areas
    assert {row["kind"] for row in found["draft/aliases.csv"]} <= {"same_ground", "inside", "wide"}
    assert {row["review_state"] for row in found["draft/areas.csv"]} == {"drafted"}
    wide = [row for row in found["draft/aliases.csv"] if row["kind"] == "wide"]
    assert len(wide) == 5 and {row["alias"] for row in wide} == {"Quillhaven"}


def test_every_candidate_is_written_with_its_publisher_its_kind_its_place_and_its_file():
    found = tables()["candidates.csv"]
    # Ten places of London, six town centres, four wards and two boroughs of Boundary-Line,
    # a second name of one record, and two boroughs as the lookup names them.
    assert len(found) == 10 + 6 + 4 + 2 + 1 + 2
    for row in found:
        assert row["as_written"] and row["publisher"] and row["kind"] and row["file_id"]
        assert row["source_id"] and row["record_id"] and row["field"] and row["lad22cd"]
        if row["gives"] != "output_areas":
            assert row["easting"] and row["oa21cd"] and row["longitude"] and row["latitude"]
    by_publisher = {row["publisher"] for row in found}
    assert by_publisher == {
        "Ordnance Survey",
        "Greater London Authority",
        "Office for National Statistics",
    }
    assert {row["has_receipt"] for row in found if row["source_id"] == CENTRES} == {"false"}


def test_the_flags_of_the_desk_name_the_item_of_each_name():
    flags = tables()["draft/flags_names.csv"]
    assert {row["queue"] for row in flags} == {"names"}
    assert {row["flag"] for row in flags} == {"one_publisher", "same_name_elsewhere"}
    ids = drafted().area_ids
    area, alias = ids[seed("Thrushcombe").key], ids[seed("Alderwick").key]
    items = {(row["item"], row["flag"]) for row in flags}
    assert (f"n:{area}", "one_publisher") in items
    assert (f"a:{alias}:foxholt", "one_publisher") in items
    assert (f"n:{ids[seed('Alderwick').key]}", "one_publisher") not in items
    # A wide name is one item, named for the first of its areas in the order of their ids.
    first = min(ids[key] for key in seed("Quillhaven").of)
    assert (f"a:{first}:quillhaven", "one_publisher") in items
    assert first == min(
        row["area_id"] for row in tables()["draft/aliases.csv"] if row["alias"] == "Quillhaven"
    )


def test_a_hard_look_says_why_in_words_and_whether_it_is_grave():
    looks = tables()["hard_look.csv"]
    assert {row["grave"] for row in looks} == {"true", "false"}
    assert all(row["why"].endswith(".") and row["area_id"] and row["name"] for row in looks)
    grave = {row["mark"] for row in looks if row["grave"] == "true"}
    assert {"one_publisher", "no_receipt"}.isdisjoint(grave)


def test_nothing_that_a_reader_must_not_read_is_in_any_file():
    for name, content in names_draft.written(drafted()).items():
        assert CANARY.encode() not in content, name
        assert b"QV1 1XX" not in content, name


def test_no_column_of_any_file_is_about_who_lives_somewhere():
    # The first line is read, so that a table with no row is held to it too.
    for name, content in names_draft.written(drafted()).items():
        if not name.endswith(".csv"):
            continue
        columns = next(csv.reader(io.StringIO(content.decode("utf-8"), newline="")))
        assert columns
        for column in columns:
            assert not ABOUT_RESIDENTS.search(column.replace("easting", "")), (name, column)


def test_the_counts_hold_numbers_and_labels_and_no_name_of_a_place():
    counts = names_draft.counts_of(drafted())
    text = json.dumps(counts)
    for each in drafted().seeds.seeds:
        assert f'"{each.name}"' not in text and each.name not in text.replace("Quillhaven", "")
    assert counts["areas"] == 5 and counts["places"] == 14
    assert counts["rule"] == {
        "points": 6,
        "publishers": 2,
        "in_range": True,
        "least": 5,
        "most": 6,
    }
    assert counts["candidates_by_source"] == {CENTRES: 6, LINE: 6, NAMES: 10}
    assert counts["areas_whose_name_one_publisher_writes"] == 3
    assert counts["files"] == {
        source: {"file_id": file.file_id, "has_receipt": source != CENTRES}
        for source, file in held().files.items()
    }


def test_a_number_below_nought_is_left_as_it_is_and_a_name_is_never_read_as_a_sum():
    written = names_draft.table(
        ("name", "longitude"), [{"name": "=Alderwick", "longitude": "-0.113509"}]
    )
    assert written == b"name,longitude\n'=Alderwick,-0.113509\n"


def test_the_same_files_give_the_same_bytes():
    assert names_draft.written(names_draft.make(held(), RULES)) == names_draft.written(drafted())


# The step


def run(folder: Path, *words: str) -> tuple[int, Path]:
    made = given(folder)
    receipts = folder / "receipts"
    for receipt in made.receipts:
        path = receipts / receipt.source_id / f"{receipt.file_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(receipt.model_dump_json(), encoding="utf-8")
    out = folder / "out"
    argv = ["--out", str(out), "--receipts", str(receipts), "--work", str(folder / "w"), *words]
    return names_cli.main(argv, {FOLDER_VARIABLE: str(made.store)}), out


def test_the_step_writes_nothing_to_the_store(tmp_path: Path):
    made = given(tmp_path / "before")
    before = every_file(made.store)
    code, _ = run(tmp_path / "run", "--draft")
    assert code == 0
    assert every_file(tmp_path / "run" / "store") == before


def test_the_step_writes_the_draft_and_prints_one_line_that_holds_no_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    code, out = run(tmp_path, "--draft", "--points", "6", "--publishers", "2")
    printed = capsys.readouterr()
    assert code == 0 and printed.err == ""
    assert re.fullmatch(r"step=names status=ok( [a-z_]+=[0-9]+)+\n", printed.out)
    assert printed.out.startswith(
        "step=names status=ok files=6 records=22 places=14 areas=5 points=6 publishers=2 "
        "in_range=0 "
    )
    assert printed.out.endswith(" no_receipt=1\n")
    assert {path.name for path in out.iterdir()} == {
        *("candidates.csv", "places.csv", "seeds.csv", "name_records.csv", "hard_look.csv"),
        *("stations.csv", "ids.csv", "decided.csv", "counts.json", "draft"),
    }
    assert (out / "seeds.csv").read_bytes() == names_draft.written(
        names_draft.make(held(), Rules(), points=6, publishers=2)
    )["seeds.csv"]


def test_without_draft_the_step_stops_at_the_file_with_no_receipt_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    code, out = run(tmp_path)
    printed = capsys.readouterr()
    assert code == 2 and not out.exists()
    assert printed.out == "step=names status=refused input_has_one_receipt=1\n"
    assert printed.err.startswith("error: ") and "input_has_one_receipt" in printed.err
    assert CENTRES in printed.err and "pass --draft" in printed.err


def test_the_step_does_not_write_over_a_folder_that_holds_something(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "kept.txt").write_text("kept", encoding="utf-8")
    code, out = run(tmp_path, "--draft")
    assert code == 2 and {path.name for path in out.iterdir()} == {"kept.txt"}
    assert "holds something already" in capsys.readouterr().err


def test_a_draft_names_no_area_that_is_not_put_forward_as_one():
    put_forward = {each.key for each in drafted().seeds.seeds if each.tier is Tier.AREA}
    assert {each.key for each in drafted().seeds.areas} == put_forward
