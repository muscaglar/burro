"""Which areas kept the outline they had in 2011, from a made-up lookup.

Every row here is made up. The town is the made-up town of the tests of cells:
three areas, each an MSOA of 2021. `areas_of_2011_support.py` says how the file
is laid out, and what each area is said to have been in 2011.
"""

from collections.abc import Sequence
from pathlib import Path

import pytest
from burro_pipeline.cells import spine
from burro_pipeline.derive import areas_of_2011 as lookup
from burro_pipeline.derive.areas_of_2011 import CARRIED, Changes, Mark, Pair
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.fetch.sources import load_list
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Status, Use

from ..cells.support import CANARY, contents, held, inputs_of, registry
from .areas_of_2011_support import (
    AS_THEY_WERE,
    COLUMNS,
    ELSEWHERE,
    JOINED,
    QUILLHAVEN,
    SPLIT,
    TALLOWGATE,
    TOWN,
    Row,
    lookup_csv,
    with_the_lookup,
)

ONE, TWO, THREE = "E02999001", "E02999002", "E02999003"
LISTED = load_list("m11-outdoor-space").files


def inputs_with(folder: Path, content: bytes | None = None, **changes: Registry) -> Inputs:
    return with_the_lookup(inputs_of(folder, contents(), **changes), folder, content)


def built(folder: Path, rows: Sequence[Row] = TOWN) -> Changes:
    inputs = inputs_with(folder, lookup_csv(rows))
    return lookup.build(inputs, spine.build(inputs))


def refused(folder: Path, content: bytes) -> LockError:
    """The refusal of a lookup, which repeats nothing the lookup holds."""
    inputs = inputs_with(folder, content)
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        lookup.build(inputs, found)
    assert stopped.value.rule == "input_is_as_described"
    assert CANARY not in str(stopped.value)
    assert str(folder) not in str(stopped.value)
    return stopped.value


# What is read


def test_the_rows_of_the_authorities_of_the_build_are_read_and_no_other(tmp_path: Path):
    found = built(tmp_path)
    assert found.pairs == (
        Pair(ONE, "E02999001", Mark.UNCHANGED),
        Pair(TWO, "E02999002", Mark.UNCHANGED),
        Pair(THREE, "E02999803", Mark.MERGED),
        Pair(THREE, "E02999804", Mark.MERGED),
    )
    assert found.rows == len(TOWN)
    assert set(found.of_2021) == {ONE, TWO, THREE}


def test_the_mark_of_each_area_is_the_mark_of_its_rows(tmp_path: Path):
    assert built(tmp_path).marks == {
        ONE: Mark.UNCHANGED,
        TWO: Mark.UNCHANGED,
        THREE: Mark.MERGED,
    }
    assert built(tmp_path / "split", SPLIT).marks == {
        ONE: Mark.SPLIT,
        TWO: Mark.SPLIT,
        THREE: Mark.MERGED,
    }


def test_no_name_is_read(tmp_path: Path):
    """Every name of the made-up file is a canary, and so is nothing that is read."""
    assert set(lookup.READ) | set(lookup.NEVER_READ) == set(COLUMNS)
    assert not set(lookup.READ) & set(lookup.NEVER_READ)
    found = built(tmp_path)
    assert CANARY not in repr(found)


def test_the_file_is_read_with_its_mark_at_the_start_and_without(tmp_path: Path):
    plain = lookup_csv().removeprefix(b"\xef\xbb\xbf")
    assert plain != lookup_csv()
    inputs = inputs_with(tmp_path, plain)
    assert lookup.build(inputs, spine.build(inputs)).pairs == built(tmp_path / "marked").pairs


def test_the_columns_may_stand_in_another_order(tmp_path: Path):
    turned = lookup_csv(columns=tuple(reversed(COLUMNS)))
    inputs = inputs_with(tmp_path, turned)
    assert lookup.build(inputs, spine.build(inputs)).pairs == built(tmp_path / "plain").pairs


# Which area of 2011 an area of 2021 is given the figure of


def test_an_area_that_did_not_change_is_given_the_area_it_was(tmp_path: Path):
    found = built(tmp_path)
    assert (found.taken_from(ONE), found.taken_from(TWO)) == ("E02999001", "E02999002")


def test_a_figure_is_carried_under_the_mark_of_no_change_and_no_other():
    """The licence registry asks it of the lookup. To carry a split is the founder's to decide."""
    assert frozenset({Mark.UNCHANGED}) == CARRIED


def test_an_area_that_was_split_from_another_is_given_none(tmp_path: Path):
    found = built(tmp_path, SPLIT)
    assert (found.taken_from(ONE), found.taken_from(TWO)) == (None, None)


def test_a_split_is_understood_and_is_carried_only_where_it_is_asked_for(tmp_path: Path):
    """A part of a split lies wholly inside the area it was split from, so that area can be
    named. No build asks for it: it is here so that to carry a split is one line."""
    found = built(tmp_path, SPLIT)
    asked = {Mark.UNCHANGED, Mark.SPLIT}
    assert (found.taken_from(ONE, asked), found.taken_from(TWO, asked)) == (
        "E02999801",
        "E02999801",
    )


@pytest.mark.parametrize("carried", [CARRIED, {Mark.UNCHANGED, Mark.SPLIT}, set(Mark)])
def test_an_area_that_was_made_by_joining_two_is_given_none_whatever_is_asked(
    tmp_path: Path, carried: set[Mark]
):
    """It has two figures and none of its own. Nothing is added up and nothing is chosen."""
    assert built(tmp_path).taken_from(THREE, carried) is None


def test_an_area_the_lookup_does_not_hold_is_given_none(tmp_path: Path):
    assert built(tmp_path).taken_from("E02999999", set(Mark)) is None


def test_an_area_whose_areas_do_not_fit_is_given_none_under_any_mark_but_its_own(
    tmp_path: Path,
):
    rows: list[Row] = [
        ("E02999001", "X", ONE, QUILLHAVEN),
        ("E02999002", "X", ONE, QUILLHAVEN),
        ("E02999002", "X", TWO, QUILLHAVEN),
        *JOINED,
    ]
    found = built(tmp_path, rows)
    assert found.marks[ONE] is found.marks[TWO] is Mark.NO_FIT
    assert found.taken_from(ONE, set(Mark)) is None
    assert found.taken_from(TWO, {Mark.UNCHANGED, Mark.SPLIT, Mark.MERGED}) is None


# What stops the build


@pytest.mark.parametrize("missing", lookup.READ)
def test_a_file_that_lacks_a_column_stops_the_build(tmp_path: Path, missing: str):
    less = tuple(name for name in COLUMNS if name != missing)
    assert "a column is missing" in str(refused(tmp_path, lookup_csv(columns=less)))


def test_the_mark_is_asked_for_by_the_name_the_file_gives_it(tmp_path: Path):
    """The publisher's record writes the column `CHGIND`. The file writes it `CHNGIND`."""
    assert lookup.MARK == "CHNGIND"
    as_the_record_has_it = lookup_csv().replace(b"CHNGIND", b"CHGIND", 1)
    assert "a column is missing" in str(refused(tmp_path, as_the_record_has_it))


@pytest.mark.parametrize("mark", ["", "u", "N", "UU", CANARY])
def test_a_mark_the_publisher_does_not_name_stops_the_build(tmp_path: Path, mark: str):
    rows: list[Row] = [("E02999001", mark, ONE, QUILLHAVEN), *TOWN[1:]]
    assert "a mark is none the publisher names" in str(refused(tmp_path, lookup_csv(rows)))


@pytest.mark.parametrize(
    "row",
    [
        ("E0299900", "U", ONE, QUILLHAVEN),
        ("E01999001", "U", ONE, QUILLHAVEN),
        ("E02999001", "U", CANARY, QUILLHAVEN),
        ("E02999001", "U", ONE, "E0900090"),
        ("E02999001", "U", ONE, CANARY),
    ],
)
def test_a_code_that_is_no_code_stops_the_build(tmp_path: Path, row: Row):
    rows: list[Row] = [row, *TOWN[1:]]
    assert "a code is not a code" in str(refused(tmp_path, lookup_csv(rows)))


def test_a_code_that_is_no_code_stops_the_build_in_a_row_that_is_passed_over(tmp_path: Path):
    """The authority of every row is read, so a file whose columns have moved is seen."""
    rows: list[Row] = [*TOWN, ("E02999902", "U", "E02999902", CANARY)]
    assert "a code is not a code" in str(refused(tmp_path, lookup_csv(rows)))


def test_a_pair_of_areas_that_is_there_twice_stops_the_build(tmp_path: Path):
    rows: list[Row] = [*TOWN, JOINED[0]]
    assert "a pair of areas is there twice" in str(refused(tmp_path, lookup_csv(rows)))


@pytest.mark.parametrize(
    "rows",
    [
        # Its code is not the code it had.
        [("E02999801", "U", ONE, QUILLHAVEN), AS_THEY_WERE[1], *JOINED],
        # It stands in a second row, as a part of another area.
        [*AS_THEY_WERE, ("E02999001", "S", THREE, TALLOWGATE), ("E02999001", "S", TWO, QUILLHAVEN)],
        # Another area of 2011 is said to be a part of it.
        [*AS_THEY_WERE, *JOINED, ("E02999803", "M", ONE, QUILLHAVEN)],
    ],
)
def test_an_area_marked_as_unchanged_that_is_not_the_area_it_was_stops_the_build(
    tmp_path: Path, rows: Sequence[Row]
):
    error = refused(tmp_path, lookup_csv(rows))
    assert "an area marked as unchanged is not the area it was" in str(error)


def test_an_area_marked_as_split_into_one_stops_the_build(tmp_path: Path):
    rows: list[Row] = [("E02999801", "S", ONE, QUILLHAVEN), AS_THEY_WERE[1], *JOINED]
    assert "an area marked as split is split into one" in str(refused(tmp_path, lookup_csv(rows)))


def test_an_area_marked_as_merged_that_is_made_of_one_stops_the_build(tmp_path: Path):
    rows: list[Row] = [*AS_THEY_WERE, JOINED[0]]
    assert "an area marked as merged is made of one" in str(refused(tmp_path, lookup_csv(rows)))


def test_an_area_of_the_build_with_no_row_stops_the_build(tmp_path: Path):
    """Every area of 2021 stands in the lookup. One that does not is no area the lookup is of."""
    assert "an area of the build has no row" in str(refused(tmp_path, lookup_csv(AS_THEY_WERE)))


def test_a_row_of_an_area_the_build_does_not_hold_stops_the_build(tmp_path: Path):
    rows: list[Row] = [*TOWN, ("E02999004", "U", "E02999004", TALLOWGATE)]
    error = refused(tmp_path, lookup_csv(rows))
    assert "a row is of an area that is no area of the build" in str(error)


def test_a_file_with_no_row_of_the_build_stops_the_build(tmp_path: Path):
    assert "it holds no row of the build" in str(refused(tmp_path, lookup_csv(ELSEWHERE)))


def test_a_file_that_is_no_text_stops_the_build(tmp_path: Path):
    assert "could not be read as text" in str(refused(tmp_path, b"\xff\xfe\x00 made up"))


# The gate


def without_scoring() -> Registry:
    """The repository's registry, with the lookup registered for cells alone, as it once was."""
    sources = [
        source.model_copy(update={"uses": (Use.CELLS,)}) if source.id == lookup.SOURCE else source
        for source in registry()
    ]
    return Registry(tuple(sources))


def test_the_gate_is_asked_before_the_lookup_is_read(tmp_path: Path):
    inputs = inputs_with(tmp_path, registry=without_scoring())
    found = spine.build(inputs)
    with pytest.raises(LockError) as stopped:
        lookup.build(inputs, found)
    assert stopped.value.rule == "gate_refuses"
    assert all(one.receipt.source_id != lookup.SOURCE for one in inputs.opened)


def test_a_build_with_no_receipt_of_the_lookup_is_refused_by_the_name_of_the_rule(
    tmp_path: Path,
):
    """A build that does not name the list holds no receipt of it, and leaves out what reads it."""
    inputs = inputs_of(tmp_path, contents())
    with pytest.raises(LockError) as stopped:
        lookup.build(inputs, spine.build(inputs))
    assert stopped.value.rule == "input_has_one_receipt"


def test_nothing_is_written_to_the_store(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    before = held(tmp_path / "store")
    lookup.build(inputs, spine.build(inputs))
    assert held(tmp_path / "store") == before


# The registry, and the list


def test_the_lookup_is_registered_for_cells_and_for_scoring_and_nothing_else():
    """In scoring it says which areas kept their outline. No figure is worked out from it."""
    source = registry().get(lookup.SOURCE)
    assert source.status is Status.APPROVED
    assert source.uses == (Use.CELLS, Use.SCORING)
    assert source.dimension == "geography"
    assert source.url in source.evidence_urls
    assert "https://www.ons.gov.uk/methodology/geography/licences" in source.evidence_urls
    assert (source.verified_how, source.licence) == ("primary_source", "OGL-3.0")
    said = " ".join(source.conditions)
    for words in (
        "Never use it to share a figure out",
        "is given to no area of 2021, whole or in part",
        "No figure is worked out from it",
        "Read the rows of London's boroughs only",
    ):
        assert words in said, words
    assert "ADR 0016" in source.notes


def test_the_list_names_the_lookup_and_states_what_was_read_of_it():
    """The file states no edition and no period, so both are its record's, and the notes say
    where each was read."""
    (listed,) = (one for one in LISTED if one.source_id == lookup.SOURCE)
    source = registry().get(lookup.SOURCE)
    assert listed.use is Use.CELLS
    assert str(listed.page) == source.url
    assert any(str(listed.url).startswith(prefix) for prefix in source.file_urls)
    assert listed.unsure == () and listed.ready_for_a_receipt
    assert (listed.edition, listed.data_period.as_at if listed.data_period else None) == (
        lookup.EDITION,
        "2022-12",
    )
    for name in COLUMNS:
        assert name in listed.notes, name
    for words in (
        "The edition: the file states none",
        "The period: the file states no day and no month",
        f"writes the third CHGIND: the file writes it {lookup.MARK}",
    ):
        assert words in listed.notes, words
