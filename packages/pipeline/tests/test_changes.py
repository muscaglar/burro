"""The file of changes: what a person decided at the panel, as a build reads it.

Every line, id and reason here is made up. No line names a real place.
"""

import json
from typing import Any

import pytest
from burro_pipeline import changes
from burro_pipeline.changes import Change, ChangesError, What

WAS = {"school_primary_nearby": 40, "play_space_proximity": 35, "park_proximity": 25}
NOW = {"school_primary_nearby": 20, "play_space_proximity": 47, "park_proximity": 33}
# A reason no other test writes. If a refusal repeats what a line holds, it shows.
CANARY = "Zzyzx Parva canary reason"


def a_line(n: int = 1, **changed: Any) -> dict[str, Any]:
    held: dict[str, Any] = {
        "n": n,
        "on": "2026-09-25",
        "by": "r1",
        "what": "recipe",
        "of": "family_amenities",
        "was": WAS,
        "now": NOW,
        "why": "A park says more of a family's week than the count of schools.",
        "takes_back": None,
    }
    return {**held, **changed}


def taken_back(n: int, line: int, of: str = "family_amenities") -> dict[str, Any]:
    return a_line(n, what="take_back", of=of, was=None, now=None, takes_back=line, why="No.")


def a_file(*lines: dict[str, Any]) -> bytes:
    return "".join(json.dumps(line) + "\n" for line in lines).encode()


def refused(data: bytes) -> ChangesError:
    with pytest.raises(ChangesError) as caught:
        changes.read(data)
    return caught.value


def test_a_line_is_read_back_as_it_was_written():
    one = Change.model_validate(a_line())
    written = changes.line(one)
    assert written.endswith(b"\n") and written.count(b"\n") == 1
    assert changes.read(written) == (one,)
    assert list(json.loads(written)) == list(changes.FIELDS)


def test_a_file_with_no_line_holds_no_change():
    assert changes.read(b"") == ()
    assert changes.standing(()) == ()


def test_the_last_line_that_no_later_line_takes_back_stands():
    later = {**NOW, "school_primary_nearby": 30, "play_space_proximity": 37}
    held = changes.read(a_file(a_line(1), a_line(2, was=NOW, now=later)))
    assert [(one.n, one.now) for one in changes.standing(held)] == [(2, later)]
    held = changes.read(a_file(a_line(1), a_line(2, was=NOW, now=later), taken_back(3, 2)))
    assert [(one.n, one.now) for one in changes.standing(held)] == [(1, NOW)]


def test_a_change_that_was_taken_back_changes_nothing():
    held = changes.read(a_file(a_line(1), taken_back(2, 1)))
    assert changes.standing(held) == ()


def test_to_take_a_taking_back_back_puts_the_line_in_place_again():
    held = changes.read(a_file(a_line(1), taken_back(2, 1), taken_back(3, 2)))
    assert [one.n for one in changes.standing(held)] == [1]


def test_each_thing_has_a_line_of_its_own_that_stands():
    name = {"label": "Leafy", "low_end": None, "high_end": None}
    held = changes.read(
        a_file(
            a_line(1),
            a_line(2, what="name", of="leafy", was=name, now={**name, "label": "Green"}),
            a_line(3, what="flag", of="figure/syn-n0004/air_no2", was=None, now=None),
        )
    )
    assert [(one.what, one.of) for one in changes.standing(held)] == [
        (What.RECIPE, "family_amenities"),
        (What.NAME, "leafy"),
        (What.FLAG, "figure/syn-n0004/air_no2"),
    ]


@pytest.mark.parametrize(
    ("line", "rule"),
    [
        (a_line(why=""), "line_gives_its_reason"),
        (a_line(why="x" * 501), "line_gives_its_reason"),
        (a_line(why="two\nlines"), "line_gives_its_reason"),
        (a_line(on="2026-09-25T10:00:00Z"), "line_says_the_day"),
        (a_line(on="2026-02-30"), "line_says_the_day"),
        (a_line(by="founder"), "reviewer_is_a_label"),
        (a_line(by="r0"), "reviewer_is_a_label"),
        (a_line(what="rename"), "line_is_a_line"),
        (a_line(extra=1), "line_is_a_line"),
        (a_line(of="no_such_vibe"), "change_names_what_it_changes"),
        (a_line(what="label", of="leafy"), "change_names_what_it_changes"),
        (a_line(what="flag", of="figure/syn-n0004", was=None, now=None), "flag_names_a_thing"),
        (a_line(what="flag", of="price/syn-n0004/flat", was=None, now=None), "flag_names_a_thing"),
        (a_line(what="flag", of="figure/syn-n0004/air_no2", now=41.5), "flag_holds_no_figure"),
        (
            a_line(what="leave_out", of="band/syn-n0004/leafy", was=None, now=None),
            "only_a_figure_is_left_out",
        ),
        (a_line(now={**NOW, "school_primary_nearby": "20"}), "change_is_of_its_kind"),
        (a_line(now=[20, 47, 33]), "change_is_of_its_kind"),
        (a_line(takes_back=1), "only_a_taking_back_names_a_line"),
    ],
)
def test_a_line_that_is_not_as_the_design_gives_it_is_refused(line: dict[str, Any], rule: str):
    found = refused(a_file(line))
    assert (found.line, found.rule) == (1, rule)


def test_a_line_that_is_no_json_is_refused_by_its_number():
    found = refused(a_file(a_line(1)) + b"{not json\n")
    assert (found.line, found.rule) == (2, "line_is_a_line")


def test_lines_are_numbered_from_one_with_none_left_out():
    assert refused(a_file(a_line(1), a_line(3))).rule == "lines_are_numbered_in_order"
    assert refused(a_file(a_line(2))).rule == "lines_are_numbered_in_order"


def test_a_file_is_of_one_reviewer():
    found = refused(a_file(a_line(1), a_line(2, by="r2")))
    assert (found.line, found.rule) == (2, "file_is_of_one_reviewer")


def test_a_taking_back_names_a_line_written_before_it_of_the_same_thing():
    assert refused(a_file(a_line(1), taken_back(2, 2))).rule == "taking_back_names_a_line"
    assert refused(a_file(a_line(1), taken_back(2, 5))).rule == "taking_back_names_a_line"
    assert refused(a_file(a_line(1), taken_back(2, 1, of="leafy"))).rule == (
        "taking_back_names_a_line"
    )


def test_a_refusal_never_repeats_what_a_line_holds():
    found = refused(a_file(a_line(why=CANARY, by="Zzyzx")))
    assert "Zzyzx" not in str(found)
    assert str(found) == "line 1 of the file of changes is refused [reviewer_is_a_label]"


def test_a_file_that_ends_in_half_a_line_is_refused():
    # A build applies a file whole or not at all: half a line is a change nobody can read.
    found = refused(a_file(a_line(1))[:-10])
    assert (found.line, found.rule) == (1, "line_is_a_line")


# A file that was written by hand


@pytest.mark.parametrize(
    "by",
    [
        "founder",
        "Ada Quillfeather",
        "ada@example.org",
        "R1",
        "r0",
        "r01",
        "r100",
        "",
        " r1",
        "r1\n",
    ],
)
def test_a_reviewer_is_named_by_the_label_of_the_desk_and_never_by_a_name_or_an_address(by: str):
    found = refused(a_file(a_line(by=by)))
    assert (found.line, found.rule) == (1, "reviewer_is_a_label")
    assert by.strip() == "" or by.strip() not in str(found)


@pytest.mark.parametrize(
    "by", ["\N{FULLWIDTH LATIN SMALL LETTER R}1", "r\N{ARABIC-INDIC DIGIT ONE}"]
)
def test_a_label_is_written_in_the_letters_and_digits_the_desk_writes(by: str):
    assert refused(a_file(a_line(by=by))).rule == "reviewer_is_a_label"


@pytest.mark.parametrize(
    "row",
    [
        # A field that is written twice says one thing to a reader and another to a build.
        b'{"n":1,"on":"2026-09-25","by":"Ada Quillfeather","by":"r1","what":"flag",'
        b'"of":"name/syn-n0004","was":null,"now":null,"why":"A made-up reason.","takes_back":null}',
        b'{"n":1,"on":"2026-09-25","by":"r1","what":"flag","of":"name/syn-n0004","was":41.5,'
        b'"was":null,"now":null,"why":"A made-up reason.","takes_back":null}',
    ],
)
def test_a_line_that_writes_a_field_twice_is_no_line(row: bytes):
    found = refused(row + b"\n")
    assert (found.line, found.rule) == (1, "line_is_a_line")
    assert "Quillfeather" not in str(found)
    # Nor is one inside what a line holds.
    inside = a_file(a_line()).replace(
        b'"park_proximity": 25', b'"park_proximity": 9, "park_proximity": 25'
    )
    assert refused(inside).rule == "line_is_a_line"


@pytest.mark.parametrize(
    "now",
    [
        {**NOW, "ethnic_group": 10},
        {**NOW, "religion": 10},
        {**NOW, "country_of_birth": 10},
        {**NOW, "household_income": 10},
        {**NOW, "no_such_part": 10},
        {**NOW, "air_no2": 10},
        {**NOW, "school_primary_nearby": {"hundredths": 20, "reading": "low"}},
        {**NOW, "school_primary_nearby": 20.0},
        {**NOW, "school_primary_nearby": True},
        {**NOW, "reading": "low"},
    ],
)
def test_a_recipe_holds_the_parts_it_held_each_with_a_whole_number(now: dict[str, Any]):
    found = refused(a_file(a_line(now=now)))
    assert (found.line, found.rule) == (1, "change_is_of_its_kind")
