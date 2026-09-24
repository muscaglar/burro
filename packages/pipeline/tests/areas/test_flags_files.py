"""The files a flag is read from and written to, on a made-up draft.

Every file here is made up. The town is Quillhaven and Tallowgate, in squares
of 100 metres in the North Sea, and the draft names two areas in it.
"""

import csv
import json
from pathlib import Path

import pytest
from burro_pipeline.areas import flags, flags_build, flags_files
from burro_pipeline.areas.flags_files import Unfit

from ..cells.support import held, registry
from .context_support import (
    ALDERWICK,
    BRACKENHYTHE,
    SEEDS,
    a_draft,
    contents,
    evidence,
    inputs_of,
    table,
)
from .flags_support import area_id

RECEIPTED = {"os-open-names", "os-boundary-line", "ons-output-areas-2021"}


# Reading


def test_a_row_gives_its_margin_and_its_second_choice_from_its_evidence(tmp_path: Path):
    given = flags_files.read_given(a_draft(tmp_path))

    first, second = sorted(given)[:2]
    assert (given[first].area, given[first].margin, given[first].second) == (
        ALDERWICK,
        0.0,
        BRACKENHYTHE,
    )
    assert given[second].margin == 3.0
    assert len(given) == 12


def test_a_row_that_says_nothing_of_its_margin_has_none(tmp_path: Path):
    rows = [{"oa21cd": "E00999001", "area_id": ALDERWICK, "evidence": "ward=Quillhaven West Ward"}]

    given = flags_files.read_given(a_draft(tmp_path, **{"oa_to_area.csv": rows}))

    assert given["E00999001"].margin is None and given["E00999001"].second == ""


@pytest.mark.parametrize(
    "evidence_said", ["margin=about ten", "margin=-4", "margin=nan", "margin", "margin=inf"]
)
def test_a_margin_that_is_no_number_of_hundredths_is_refused(tmp_path: Path, evidence_said: str):
    rows = [{"oa21cd": "E00999001", "area_id": ALDERWICK, "evidence": evidence_said}]

    with pytest.raises(Unfit):
        flags_files.read_given(a_draft(tmp_path, **{"oa_to_area.csv": rows}))


def test_an_output_area_in_two_areas_is_refused(tmp_path: Path):
    rows = [{"oa21cd": "E00999001", "area_id": area} for area in (ALDERWICK, BRACKENHYTHE)]

    with pytest.raises(Unfit, match="twice"):
        flags_files.read_given(a_draft(tmp_path, **{"oa_to_area.csv": rows}))


def test_a_file_that_lacks_a_column_is_refused_and_no_value_of_it_is_repeated(tmp_path: Path):
    table(tmp_path, "oa_to_area.csv", ("oa21cd", "area_id"), [{"oa21cd": "E00999001"}])

    with pytest.raises(Unfit) as refused:
        flags_files.read_given(tmp_path)

    assert "E00999001" not in str(refused.value)


def test_two_sources_of_one_publisher_are_one_publisher(tmp_path: Path):
    named = flags_files.read_named(a_draft(tmp_path), registry(), RECEIPTED)

    assert named[ALDERWICK].publishers == ("Ordnance Survey",)
    assert named[BRACKENHYTHE].publishers == ("Greater London Authority", "Ordnance Survey")


def test_a_name_one_official_publisher_writes_at_a_point_inside_is_said_to_fit_the_rule(
    tmp_path: Path,
):
    """The founder decided that one official publisher is enough for such a name. The
    flags read it from the rows of evidence, which say where each record lies."""
    rows = [
        evidence(ALDERWICK, "Alderwick", "os-open-names", locates="point_inside"),
        # A point that lies outside the area, and an outline that lies over it.
        evidence(BRACKENHYTHE, "Brackenhythe", "os-open-names", locates="label_only"),
        evidence(
            BRACKENHYTHE, "Brackenhythe", "gla-town-centre-boundaries", locates="polygon_overlap"
        ),
    ]
    named = flags_files.read_named(
        a_draft(tmp_path, **{"name_evidence.csv": rows}), registry(), RECEIPTED
    )
    assert named[ALDERWICK].by_the_rule
    assert not named[BRACKENHYTHE].by_the_rule


@pytest.mark.parametrize(
    "row",
    [
        # A label that holds the name among other words does not write it.
        evidence(ALDERWICK, "Alderwick", "os-open-names", locates="point_inside")
        | {"as_written": "Alderwick Wharf"},
        evidence(ALDERWICK, "Alderwick", "os-open-names", locates="point_inside", checked="false"),
        evidence(ALDERWICK, "Alderwick", "os-open-names", locates="point_inside", role="alias"),
        evidence(ALDERWICK, "Alderwick", "os-boundary-line", locates="point_inside"),
        # A file that does not say where a record lies says it of none.
        evidence(ALDERWICK, "Alderwick", "os-open-names"),
    ],
)
def test_the_rule_fits_no_name_whose_record_is_not_as_the_rule_asks(
    tmp_path: Path, row: dict[str, str]
):
    folder = a_draft(tmp_path, **{"name_evidence.csv": [row]})
    assert not flags_files.read_named(folder, registry(), RECEIPTED)[ALDERWICK].by_the_rule


def test_a_row_that_was_not_checked_or_is_of_another_name_adds_no_publisher(tmp_path: Path):
    named = flags_files.read_named(a_draft(tmp_path), registry(), RECEIPTED)

    assert "Office for National Statistics" not in named[BRACKENHYTHE].publishers


def test_an_area_rests_on_a_source_with_no_receipt_where_a_checked_row_names_one(tmp_path: Path):
    named = flags_files.read_named(a_draft(tmp_path), registry(), RECEIPTED)

    assert named[ALDERWICK].unreceipted == ()
    assert named[BRACKENHYTHE].unreceipted == ("gla-town-centre-boundaries",)


def test_an_area_that_another_took_the_place_of_is_left_out(tmp_path: Path):
    named = flags_files.read_named(a_draft(tmp_path), registry(), RECEIPTED)

    assert sorted(named) == [ALDERWICK, BRACKENHYTHE]


def test_a_source_the_registry_does_not_hold_is_refused(tmp_path: Path):
    rows = [evidence(ALDERWICK, "Alderwick", "made-up-gazetteer")]

    with pytest.raises(Unfit, match="licence registry"):
        flags_files.read_named(a_draft(tmp_path, **{"name_evidence.csv": rows}), registry(), ())


def test_what_the_draft_lists_as_wrong_with_an_area_is_read_where_it_is_there(tmp_path: Path):
    drafted = a_draft(tmp_path)
    assert flags_files.read_named(drafted, registry(), RECEIPTED)[ALDERWICK].listed == ()
    listed = [
        {"area_id": ALDERWICK, "what": "seed_outside", "output_areas": ""},
        {"area_id": ALDERWICK, "what": "both_banks", "output_areas": ""},
    ]
    table(drafted, "listed.csv", ("area_id", "what", "output_areas"), listed)

    named = flags_files.read_named(drafted, registry(), RECEIPTED)

    assert named[ALDERWICK].listed == ("both_banks", "seed_outside")
    assert named[BRACKENHYTHE].listed == ()


def test_a_draft_with_no_file_of_seeds_gives_no_area_a_seed(tmp_path: Path):
    drafted = a_draft(tmp_path)
    (drafted / "seeds.csv").unlink()

    named = flags_files.read_named(drafted, registry(), RECEIPTED)

    assert named[ALDERWICK].seed is None


def test_a_seed_is_where_the_file_of_seeds_puts_it(tmp_path: Path):
    named = flags_files.read_named(a_draft(tmp_path), registry(), RECEIPTED)

    assert named[ALDERWICK].seed == (700_150.0, 400_100.0)


def test_a_seed_that_rests_on_a_file_with_no_receipt_marks_its_area(tmp_path: Path):
    """A seed may be put on a town centre whose name is not the area's: no row says so."""
    seeds = [
        {"area_id": ALDERWICK, "easting": 700_150, "northing": 400_100, "no_receipt": "true"},
        {"area_id": BRACKENHYTHE, "easting": 700_500, "northing": 400_100, "no_receipt": "false"},
    ]
    drafted = a_draft(tmp_path)
    table(drafted, "seeds.csv", (*SEEDS, "no_receipt"), seeds)

    named = flags_files.read_named(drafted, registry(), RECEIPTED)

    assert named[ALDERWICK].unreceipted == ("gla-town-centre-boundaries",)
    assert named[ALDERWICK].publishers == ("Ordnance Survey",)


# The whole step, on made-up files


@pytest.fixture(scope="module")
def flagged(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, flags_build.Flagged]:
    folder = tmp_path_factory.mktemp("flags")
    inputs = inputs_of(folder, contents())
    read = flags_build.read_ground(inputs, draft=True)
    found = flags_build.flag(inputs, read, a_draft(folder / "draft"), folder / "out")
    return folder / "out", found


def rows_of(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_the_flags_are_written_as_the_desk_reads_them(flagged: tuple[Path, flags_build.Flagged]):
    rows = rows_of(flagged[0] / "flags.csv")

    assert set(rows[0]) == {"queue", "item", "flag"}
    assert ("borders", ALDERWICK, "one_publisher") in {
        (row["queue"], row["item"], row["flag"]) for row in rows
    }
    assert ("borders", BRACKENHYTHE, "no_receipt") in {
        (row["queue"], row["item"], row["flag"]) for row in rows
    }


def test_only_borders_are_flagged_unless_names_are_asked_for_too(
    flagged: tuple[Path, flags_build.Flagged], tmp_path: Path
):
    """The draft of names flags the names. A flag written twice would be read twice."""
    assert {row["queue"] for row in rows_of(flagged[0] / "flags.csv")} == {"borders"}

    inputs = inputs_of(tmp_path, contents())
    read = flags_build.read_ground(inputs, draft=True)
    drafted = a_draft(tmp_path / "draft")
    flags_build.flag(inputs, read, drafted, tmp_path / "out", queues=("borders", "names"))

    assert ("names", f"n:{BRACKENHYTHE}", "no_receipt") in {
        (row["queue"], row["item"], row["flag"]) for row in rows_of(tmp_path / "out/flags.csv")
    }


def test_the_desk_is_handed_every_flag_about_the_border_and_none_about_the_name(
    flagged: tuple[Path, flags_build.Flagged],
):
    handed = rows_of(flagged[0] / "flags_desk.csv")
    every = rows_of(flagged[0] / "flags.csv")

    assert handed and len(handed) < len(every)
    assert handed == [row for row in every if row["flag"] not in flags.ABOUT_THE_NAME]
    assert {row["flag"] for row in handed} <= set(flags.WORDS[flags.BORDERS])
    assert {row["flag"] for row in handed} - {
        *("margin_under_10", "least_compact", "two_boroughs", "two_centres"),
    }, "a flag the desk once had no words for is handed to it"


def test_every_flag_is_written_with_why_and_the_cells_it_points_at(
    flagged: tuple[Path, flags_build.Flagged],
):
    rows = rows_of(flagged[0] / "flagged.csv")

    assert len(rows) == len(flagged[1].flags)
    for row in rows:
        assert row["why"].endswith(".") and row["name"] in ("Alderwick", "Brackenhythe")
        assert int(row["cells_pointed_at"]) == len(row["cells"].split())
        assert row["about"] == ("name" if row["flag"] in flags.ABOUT_THE_NAME else "border")
        assert row["of_the_whole_area"] in ("true", "false")


def test_the_order_holds_every_area_and_every_borough_with_how_sure_the_method_was(
    flagged: tuple[Path, flags_build.Flagged],
):
    rows = rows_of(flagged[0] / "order.csv")

    assert [(row["queue"], row["rank"]) for row in rows] == [
        ("borders", "1"),
        ("borders", "2"),
        ("whole", "1"),
        ("whole", "2"),
    ]
    assert {row["item"] for row in rows} == {ALDERWICK, BRACKENHYTHE, "quillhaven", "tallowgate"}
    assert {row["weighed_by"] for row in rows} == {"output areas"}
    assert all(0 <= float(row["sure"]) <= 1 for row in rows)


def test_homes_are_not_read_while_the_gate_does_not_give_them_for_the_gazetteer(
    flagged: tuple[Path, flags_build.Flagged],
):
    """The table of homes is registered for scoring. When it is given this use, this fails."""
    said = json.loads((flagged[0] / "rules.json").read_text(encoding="utf-8"))

    assert said["weighed_by"] == "output areas"
    assert "not registered for gazetteer" in said["notes"]["ons-census-2021-housing-tables"]


def test_the_rules_are_written_each_in_one_line_with_the_counts(
    flagged: tuple[Path, flags_build.Flagged],
):
    said = json.loads((flagged[0] / "rules.json").read_text(encoding="utf-8"))

    assert [rule["flag"] for rule in said["rules"]] == list(flags.Rules().lines())
    assert all(rule["rule"].endswith(".") for rule in said["rules"])
    assert said["counts"]["areas"] == 2 and said["counts"]["output_areas"] == 12
    assert said["numbers"]["margin_percent"] == 10.0
    assert (
        said["counts"]["areas_flagged_about_the_border"]
        + said["counts"]["areas_flagged_about_the_name_alone"]
        == said["counts"]["areas_flagged"]
    )
    assert said["notes"]["no_receipt"].endswith("gla-town-centre-boundaries.")


def test_a_cell_in_doubt_is_written_with_its_margin_and_its_second_choice(
    flagged: tuple[Path, flags_build.Flagged],
):
    rows = rows_of(flagged[0] / "cells_in_doubt.csv")

    assert rows and all(0 < float(row["doubt"]) <= 1 for row in rows)
    closest = next(row for row in rows if row["margin"] == "0")
    assert (closest["doubt"], closest["second"]) == ("1", BRACKENHYTHE)


def test_a_name_that_begins_as_a_sum_would_is_written_so_that_no_sheet_reads_it_as_one(
    tmp_path: Path,
):
    inputs = inputs_of(tmp_path, contents())
    read = flags_build.read_ground(inputs, draft=True)
    areas = [
        {"area_id": ALDERWICK, "name": "=Alderwick"},
        {"area_id": BRACKENHYTHE, "name": "Brackenhythe"},
    ]
    drafted = a_draft(tmp_path / "draft", **{"areas.csv": areas})

    flags_build.flag(inputs, read, drafted, tmp_path / "out")

    names = {row["name"] for row in rows_of(tmp_path / "out" / "flagged.csv")}
    assert "'=Alderwick" in names and "=Alderwick" not in names


def test_the_same_draft_gives_the_same_files_byte_for_byte(tmp_path: Path):
    for run in ("one", "two"):
        inputs = inputs_of(tmp_path / run, contents())
        read = flags_build.read_ground(inputs, draft=True)
        flags_build.flag(inputs, read, a_draft(tmp_path / run / "draft"), tmp_path / run / "out")

    assert held(tmp_path / "one" / "out") == held(tmp_path / "two" / "out")


def test_a_name_that_holds_no_output_area_is_left_out_and_counted(tmp_path: Path):
    """A seed too small to stand becomes part of another area. Its name is no area."""
    inputs = inputs_of(tmp_path, contents())
    read = flags_build.read_ground(inputs, draft=True)
    areas = [
        {"area_id": ALDERWICK, "name": "Alderwick"},
        {"area_id": BRACKENHYTHE, "name": "Brackenhythe"},
        {"area_id": area_id("E"), "name": "Eskerfold"},
    ]
    drafted = a_draft(tmp_path / "draft", **{"areas.csv": areas})

    found = flags_build.flag(inputs, read, drafted, tmp_path / "out")

    assert sorted(found.draft.areas) == [ALDERWICK, BRACKENHYTHE]
    assert {flag.area for flag in found.flags} <= {ALDERWICK, BRACKENHYTHE}
    said = json.loads((tmp_path / "out" / "rules.json").read_text(encoding="utf-8"))
    assert said["notes"]["names_with_no_output_area"].startswith("1 names of areas.csv")


def test_a_draft_that_leaves_an_output_area_in_no_area_is_not_flagged(tmp_path: Path):
    inputs = inputs_of(tmp_path, contents())
    read = flags_build.read_ground(inputs, draft=True)
    rows = [{"oa21cd": "E00999001", "area_id": ALDERWICK}]
    drafted = a_draft(tmp_path / "draft", **{"oa_to_area.csv": rows})

    with pytest.raises(ValueError, match="in one area"):
        flags_build.flag(inputs, read, drafted, tmp_path / "out")

    assert not (tmp_path / "out").exists()
