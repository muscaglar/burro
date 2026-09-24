"""What a person reads beside an item: every doubt of the draft, in words, on its own item.

Nothing here is real. `draft_support.py` makes the whole draft of the made-up
town, and `flags_support.py` draws the town the borders are flagged on.

The lines of a name are read on the draft in which every name is put to a person.
A name that stands by the rule on one official publisher is no item, and has no
line: `test_draft_decided.py` holds that.
"""

import dataclasses
import re

import pytest
from burro_pipeline.areas import context_shapes, draft_lines, draft_marks
from burro_pipeline.areas.draft_lines import Line
from burro_pipeline.areas.flags import Area, Cell, Draft, Rules, Side, flags_of
from burro_pipeline.areas.flags_order import doubts
from burro_pipeline.areas.names_candidates import Match
from burro_pipeline.areas.seeds import Weight

from . import names_support
from . import names_support as town
from .context_support import above, along
from .draft_support import Made, made_with_every_name_read

# Words that would say who lives somewhere. No label of a line holds one: the desk holds
# every label beside a map to the same rule.
ABOUT_RESIDENTS = re.compile(
    r"\b(residents?|population|people|households?|aged|ethnic\w*|religio\w+|born|incomes?"
    r"|depriv\w+|crimes?|prices?|rents?|tenure|students?|famil\w+|wealthy|affluent)\b"
)
OS_NAMES, TOWN_CENTRES, WARDS = (
    "Ordnance Survey, OS Open Names",
    "Greater London Authority, Town Centre Boundaries",
    "Ordnance Survey, OS Boundary-Line",
)


@pytest.fixture(scope="module")
def draft() -> Made:
    return made_with_every_name_read()


def lines(draft: Made, queue: str, item: str) -> list[tuple[str, str]]:
    return [
        (row["label"], row["value"])
        for row in draft.rows("desk/draft/lines.csv")
        if (row["queue"], row["item"]) == (queue, item)
    ]


# The lines of a name


def test_every_record_that_writes_a_name_is_a_line_under_its_publisher_in_words(draft: Made):
    found = dict(lines(draft, "names", "n:lon-n0001"))
    assert found[OS_NAMES] == ("Alderwick. A point inside this area. Record osgb9000000000000001.")
    assert found[TOWN_CENTRES] == (
        "Alderwick. An outline. 100% of it lies in this area. Record TCB90000001."
    )
    # A ward is no spelling to choose, so the desk is handed no row of it. It is still said.
    assert found[WARDS] == (
        "Alderwick Ward. It is not the name letter for letter. An outline. 100% of it lies "
        "in this area. Record E05998001."
    )
    sources = {
        row["source_id"]
        for row in draft.rows("desk/draft/lines.csv")
        if row["label"] in (OS_NAMES, TOWN_CENTRES, WARDS)
    }
    assert sources == {town.NAMES, town.CENTRES, town.LINE}


def test_a_record_that_lies_outside_the_area_says_so_and_how_far_off(draft: Made):
    """The desk's own words for it were "a label, with no place". The record has a place."""
    found = dict(lines(draft, "names", "a:lon-n0006:cindermoor"))
    assert found[TOWN_CENTRES] == (
        "Grapnel Dock/ Cindermoor. The label is several names, of which this is one. "
        "Its record lies outside this area, 200 m from its edge. Record TCB90000004."
    )
    assert not [
        row
        for row in draft.rows("desk/draft/lines.csv")
        if "no place" in row["value"] or "label_only" in row["value"]
    ]


@pytest.mark.parametrize(
    ("locates", "share", "metres", "said"),
    [
        ("point_inside", "1.00", "", "A point inside this area."),
        ("point_inside", "0.50", "", "A point on the line between this area and the next."),
        ("polygon_overlap", "0.62", "", "An outline. 62% of it lies in this area."),
        ("label_only", "0.00", "430", "Its record lies outside this area, 430 m from its edge."),
        ("label_only", "0.00", "1430", "Its record lies outside this area, 1,430 m from its edge."),
        ("label_only", "0.00", "0", "Its record lies outside this area, at its edge."),
        ("label_only", "0.003", "0", "Its record lies outside this area, at its edge."),
        (
            "label_only",
            "0.04",
            "0",
            "An outline that lies outside this area but for 4% of it, which is too little to "
            "say that it lies here.",
        ),
    ],
)
def test_where_a_record_lies_is_said_in_words(locates: str, share: str, metres: str, said: str):
    row = {"locates": locates, "share": share, "metres_outside": metres}
    assert draft_lines.where(row) == said


def test_a_name_put_forward_as_an_area_says_its_points_and_what_gave_each(draft: Made):
    assert dict(lines(draft, "names", "n:lon-n0001"))["Points"] == (
        "9 points, where 6 are asked. A point is a weight the draft gives for a kind of "
        "record of the name, and a name with the points asked is put forward as an area. "
        "A populated place: 3. 60 roads give it as their settlement: 2. "
        'Its own town centre, "Alderwick": 3. Its outline holds the place\'s point. '
        'Record TCB90000001. The ward "Alderwick Ward" carries it: 1. Record E05998001.'
    )
    others = [row for row in draft.rows("desk/draft/lines.csv") if row["item"].startswith("a:")]
    assert others and "Points" not in {row["label"] for row in others}


def test_where_points_are_shown_the_line_says_in_one_sentence_what_a_point_is(draft: Made):
    points = [row for row in draft.rows("desk/draft/lines.csv") if row["label"] == "Points"]
    assert points
    for row in points:
        first, second, _ = row["value"].split(". ", 2)
        assert first.endswith("are asked")
        assert f"{second}." == draft_lines.WHAT_A_POINT_IS
    assert draft_lines.WHAT_A_POINT_IS.count(".") == 1, "one line"


def test_a_town_centre_of_another_name_that_gives_points_is_named_as_its_file_writes_it(
    draft: Made,
):
    """A town centre gives points to a place whose name it does not write. The line said
    so, and named the centre by its id alone: a person could not tell which it was."""
    said = dict(lines(draft, "names", "n:lon-n0010"))["Points"]
    assert (
        'A town centre of another name, "Pellam Cross": 3. Its outline is 200 m from the '
        "place's point. Record TCB90000003."
    ) in said
    centres = {
        row["record_id"]: row["as_written"]
        for row in draft.rows("made/names/candidates.csv")
        if row["source_id"] == town.CENTRES
    }
    assert centres["TCB90000003"] == "Pellam Cross"
    for row in draft.rows("desk/draft/lines.csv"):
        if row["label"] == "Points" and "town centre" in row["value"]:
            record = re.search(r"Record (TCB\w+)\.", row["value"])
            assert record and f'"{centres[record[1]]}"' in row["value"], row["item"]


def test_the_ward_that_carries_a_name_is_named_and_is_the_ward_the_item_lists(draft: Made):
    rows = draft.rows("desk/draft/lines.csv")
    listed: dict[str, set[str]] = {}
    for row in rows:
        if row["label"] == WARDS:
            listed.setdefault(row["item"], set()).add(row["value"].split("Record ")[-1][:-1])
    carried = [row for row in rows if row["label"] == "Points" and " carries it" in row["value"]]
    assert carried
    for row in carried:
        record = re.search(r'The ward "[^"]+" carries it[^.]*: 1\. Record (\w+)\.', row["value"])
        assert record, row["value"]
        assert not listed.get(row["item"]) or record[1] in listed[row["item"]], row["item"]


def test_a_ward_that_only_holds_the_name_among_other_words_says_why_it_is_not_listed():
    place = names_support.seed("Cindermoor").place
    (writes,) = place.written_by(town.LINE)
    holds = dataclasses.replace(
        writes,
        candidate=dataclasses.replace(
            writes.candidate, record_id="E05998099", as_written="Cindermoor Park Ward"
        ),
        match=Match.HELD,
    )
    seed = dataclasses.replace(
        names_support.seed("Cindermoor"),
        place=dataclasses.replace(place, others=(holds,)),
        weight=Weight(place=3, ward=1, ward_record="E05998099"),
    )
    written = {(town.LINE, "E05998099"): "Cindermoor Park Ward"}
    assert draft_lines.points_of(seed, 4, written).endswith(
        'The ward "Cindermoor Park Ward" carries it among other words: 1. Its label is no '
        "record of the name, so it is not listed above. Record E05998099."
    )


def test_a_distance_says_from_what_to_what_and_one_thing_has_one_distance(draft: Made):
    """The draft gave three distances for what read as one thing: from a place to its
    town centre. One was to the centre's outline, in metres and again in kilometres, and
    one was to where the seed stands."""
    found = lines(draft, "names", "n:lon-n0009")
    said = dict(found)
    assert (
        "Look hard",
        'The town centre "Wexmoor" is taken for the same place. Its outline is 1,150 m from '
        "the place's point, inside the box that is drawn round the place.",
    ) in found
    assert "Its outline is 1,150 m from the place's point." in said["Points"]
    assert said["Note"] == (
        "Its seed stands where its town centre is taken to stand, 1,200 m from the point "
        "that Ordnance Survey gives the place."
    )
    # No distance of a name is said without what it is from and what it is to.
    for row in draft.rows("desk/draft/lines.csv"):
        # The sides of a box are no distance between two things.
        if row["queue"] == "names" and not row["value"].startswith("Its box is"):
            assert not re.search(r"\d m off\b|\d km off\b", row["value"]), row["value"]
            for metres in re.finditer(r"[\d,.]+ k?m\b", row["value"]):
                after = row["value"][metres.end() :].lstrip(", ")
                assert after.startswith(("from ", "along the roads from ", "away, ")), row


def test_a_name_says_the_kind_of_place_its_publisher_gives(draft: Made):
    """Whether a name is a suburb, a village or a town centre is what a person weighs."""
    rows = [row for row in draft.rows("desk/draft/lines.csv") if row["queue"] == "names"]
    kinds = {row["item"]: row for row in rows if row["label"] == "Kind of place"}
    assert set(kinds) == {row["item"] for row in rows}, "every name says its kind, once"
    assert len(kinds) == sum(row["label"] == "Kind of place" for row in rows)
    said = {item: (row["value"], row["source_id"]) for item, row in kinds.items()}
    assert said["n:lon-n0001"] == ("Other Settlement.", "os-open-names")
    assert said["n:lon-n0006"] == ("Village.", "os-open-names")
    # A name that only a town centre holds is of the kind the town centres give it.
    assert said["a:lon-n0009:grapnel-dock-cindermoor"] == ("Local Centre.", town.CENTRES)
    written = {row["kind"] for row in draft.rows("made/names/places.csv")}
    assert {value.removesuffix(".") for value, _ in said.values()} <= written


def test_a_name_says_how_many_road_records_give_it_as_their_settlement(draft: Made):
    said = dict(lines(draft, "names", "n:lon-n0001"))["Road records"]
    assert said == "60 road records give it as their settlement."
    # Fewer than the 50 that give points are still said: a person weighs them.
    every = [row for row in draft.rows("desk/draft/lines.csv") if row["label"] == "Road records"]
    assert {row["source_id"] for row in every} == {"os-open-names"}
    assert "No road record gives it as its settlement." in {row["value"] for row in every}
    # A name only a town centre holds has no record that a road could give.
    assert "Road records" not in dict(lines(draft, "names", "a:lon-n0009:grapnel-dock-cindermoor"))


def test_a_name_put_forward_as_an_area_says_how_large_the_area_is(draft: Made):
    held: dict[str, int] = {}
    for row in draft.rows("oa_to_area.csv"):
        held[row["area_id"]] = held.get(row["area_id"], 0) + 1
    for area, count in held.items():
        assert dict(lines(draft, "names", f"n:{area}"))["Size"] == f"{count} output areas."
    others = [row for row in draft.rows("desk/draft/lines.csv") if row["item"].startswith("a:")]
    assert others and "Size" not in {row["label"] for row in others}


def test_the_size_of_an_area_says_nothing_of_any_other_area():
    """The desk asks a name again when a line of it has changed. A line that held what
    half of the areas hold would change on every name whenever one area changed."""
    assert draft_lines.size_of("n:lon-n0001", 49) == Line(
        "names", "n:lon-n0001", "Size", "49 output areas."
    )
    assert draft_lines.size_of("n:lon-n0001", 1).value == "1 output area."


def test_what_a_person_weighs_is_read_after_the_evidence_and_before_what_asks_less(
    draft: Made,
):
    labels = [label for label, _ in lines(draft, "names", "n:lon-n0001")]
    assert labels[-6:] == [
        *("Kind of place", "Road records", "Points", "Size", "Other names", "No receipt")
    ]


def test_every_mark_to_settle_is_a_line_of_the_item_it_is_on(draft: Made):
    listed = draft.rows("names_to_look_at.csv")
    assert listed
    for row in listed:
        label = "Look hard" if row["grave"] == "true" else "Note"
        assert (label, row["why"]) in lines(draft, "names", row["item"]), row
    found = lines(draft, "names", "n:lon-n0009")
    assert (
        "Note",
        "Its seed stands where its town centre is taken to stand, 1,200 m from the point "
        "that Ordnance Survey gives the place.",
    ) in found


def test_an_area_lists_the_other_names_the_draft_puts_in_it_by_what_each_is_offered_as(
    draft: Made,
):
    """A person who reads the name of an area could not see what else the draft calls
    ground inside it: each other name was an item of its own, further down the queue."""
    said = dict(lines(draft, "names", "n:lon-n0006"))["Other names"]
    assert said == (
        "The draft puts 3 other names in this area. A smaller place inside: Cindermoor, "
        "Osierholm. A wider name, over this area and others: Quillhaven."
    )
    assert dict(lines(draft, "names", "n:lon-n0008"))["Other names"] == (
        "The draft puts 3 other names in this area. Another name for the same ground: "
        "Lantern Yard. A smaller place inside: Kindlewharf High Street. A wider name, over "
        "this area and others: Quillhaven."
    )
    offered: dict[str, set[str]] = {}
    for row in draft.rows("desk/draft/aliases.csv"):
        offered.setdefault(f"n:{row['area_id']}", set()).add(row["alias"])
    areas = {f"n:{row['area_id']}" for row in draft.rows("desk/draft/areas.csv")}
    for item in areas:
        said = dict(lines(draft, "names", item))["Other names"]
        for name in offered.get(item, set()):
            assert name in said, (item, name)
        if not offered.get(item):
            assert said == "The draft puts no other name in this area."
    others = [row for row in draft.rows("desk/draft/lines.csv") if row["item"].startswith("a:")]
    assert "Other names" not in {row["label"] for row in others}


def test_a_mark_to_settle_is_read_before_the_evidence_and_what_asks_less_after_it(draft: Made):
    """What is known of an item scrolls at the desk. What must not be missed comes first."""
    labels = [label for label, _ in lines(draft, "names", "n:lon-n0009")]
    assert labels == [
        *("Look hard", OS_NAMES, TOWN_CENTRES),
        *("Publishers", "Kind of place", "Road records", "Points", "Size", "Other names"),
        *("Note", "No receipt"),
    ]


def test_a_name_says_how_many_publishers_write_it_and_whether_one_is_enough(draft: Made):
    """The founder decided that one official publisher is enough for a name it writes
    for a populated place at a point inside the area. A name still says who writes it."""

    def said(item: str) -> str:
        return dict(lines(draft, "names", item))["Publishers"]

    assert said("n:lon-n0009") == (
        "Two publishers write it: Greater London Authority, Ordnance Survey."
    )
    assert said("n:lon-n0010") == (
        "One publisher writes it: Ordnance Survey. That is enough for a name: it writes the "
        "name for a populated place at a point inside this area."
    )
    # A town centre is an outline, and is no populated place.
    assert said("a:lon-n0006:osierholm") == (
        "One publisher writes it: Greater London Authority. The rule that one official "
        "publisher is enough does not fit it: no such publisher writes it for a populated "
        "place at a point inside this area."
    )
    assert said("a:lon-n0001:quillhaven") == (
        "One publisher writes it: Ordnance Survey. The rule that one official publisher is "
        "enough says nothing of a wide name: no point puts it inside one area."
    )
    every = {row["item"] for row in draft.rows("desk/draft/lines.csv") if row["queue"] == "names"}
    told = {
        row["item"]
        for row in draft.rows("desk/draft/lines.csv")
        if (row["queue"], row["label"]) == ("names", "Publishers")
    }
    assert told == every


def test_what_rests_on_the_file_with_no_receipt_says_so_on_its_own_item(draft: Made):
    rests = {row["area_id"] for row in draft.rows("areas.csv") if row["no_receipt"] == "true"}
    assert rests
    for area in rests:
        (said,) = [
            value for label, value in lines(draft, "names", f"n:{area}") if label == "No receipt"
        ]
        assert town.CENTRES in said and "no receipt" in said
    assert "No receipt" not in dict(lines(draft, "names", "a:lon-n0010:eskerfold"))


def test_what_rests_on_the_file_with_no_receipt_says_which_of_the_three_it_is(draft: Made):
    """It said "its name, its points or its seed", and a person could not tell which."""

    def said(item: str) -> str:
        return dict(lines(draft, "names", item))["No receipt"]

    ends = f"on {town.CENTRES}, a file that has no receipt."
    # The town centre writes the name, gives points, and the seed stands on it.
    assert said("n:lon-n0001") == f"Its name, its points and its seed rest {ends}"
    # A town centre of another name gives points, and nothing more.
    assert said("n:lon-n0010") == f"Its points rest {ends}"
    # The town centre names it beside another name, and its seed stands there. The
    # centre is below district class, and gives it no point.
    assert said("a:lon-n0006:cindermoor") == f"Its name and its seed rest {ends}"
    for row in draft.rows("desk/draft/lines.csv"):
        if row["queue"] == "names" and row["label"] == "No receipt":
            assert " or " not in row["value"], row["value"]


def test_every_line_is_of_an_item_the_desk_makes_and_no_label_is_about_who_lives_anywhere(
    draft: Made,
):
    rows = draft.rows("desk/draft/lines.csv")
    assert draft.columns("desk/draft/lines.csv") == draft_lines.COLUMNS
    items = {f"n:{row['area_id']}" for row in draft.rows("areas.csv")}
    items |= {
        f"a:{row['area_id']}:{draft_marks.desk_slug(row['alias'])}"
        for row in draft.rows("aliases.csv")
    }
    assert {row["item"] for row in rows if row["queue"] == "names"} <= items
    assert {row["item"] for row in rows if row["queue"] == "borders"} <= {
        row["area_id"] for row in draft.rows("areas.csv")
    }
    for row in rows:
        assert row["label"] and row["value"], row
        assert not ABOUT_RESIDENTS.search(row["label"].casefold()), row["label"]


# The lines of a border


def test_a_border_says_in_words_what_every_flag_found_whether_or_not_the_desk_has_words(
    draft: Made,
):
    flagged = [
        row
        for row in draft.rows("made/flags/flagged.csv")
        if row["queue"] == "borders" and row["about"] == "border"
    ]
    assert {row["flag"] for row in flagged} > {"two_boroughs"}
    for row in flagged:
        assert ("Flagged", row["why"]) in lines(draft, "borders", row["item"]), row
    # Two boroughs are named, and how many output areas lie in the second.
    assert (
        "Flagged",
        "It lies in Tallowgate and Quillhaven. 4 of its 9 output areas are outside "
        "Tallowgate: 44.4% of its output areas.",
    ) in lines(draft, "borders", "lon-n0009")


def test_every_output_area_in_doubt_is_a_line_so_that_the_desk_rings_it(draft: Made):
    in_doubt: dict[str, set[str]] = {}
    for row in draft.rows("made/flags/cells_in_doubt.csv"):
        in_doubt.setdefault(row["area_id"], set()).add(row["oa21cd"])
    assert in_doubt
    for area, cells in in_doubt.items():
        found = dict(lines(draft, "borders", area))
        assert cells <= set(found), area
        assert found["In doubt"].startswith(f"{len(cells)} output area")
    assert dict(lines(draft, "borders", "lon-n0006"))["E00998035"] == (
        "margin 6%, second choice Thrushcombe, in Quillhaven, not the main borough, "
        "its ward is Brackenhythe & Cindermoor"
    )


def test_a_margin_of_a_hundred_or_more_is_said_in_words_and_not_as_a_percentage(draft: Made):
    """A margin is by how much the second choice is further than the first. The desk
    showed "margin 240%", and up to 999%, with no word of what that means."""
    assert dict(lines(draft, "borders", "lon-n0009"))["E00998005"] == (
        "second choice Kindlewharf, which is 3.4 times as far, in Quillhaven, not the main borough"
    )
    for row in draft.rows("desk/draft/lines.csv"):
        if row["queue"] == "borders":
            shown = [int(found) for found in re.findall(r"margin (\d+)%", row["value"])]
            assert all(margin < 100 for margin in shown), row["value"]


@pytest.mark.parametrize(
    ("margin", "said"),
    [
        ("0", "margin 0%, second choice Foxholt"),
        ("99", "margin 99%, second choice Foxholt"),
        ("100", "second choice Foxholt, which is twice as far"),
        ("150", "second choice Foxholt, which is 2.5 times as far"),
        ("998", "second choice Foxholt, which is 11.0 times as far"),
        # The most a margin is written as: the draft does not say how much further.
        ("999", "second choice Foxholt, which is over 10 times as far"),
    ],
)
def test_how_far_the_second_choice_is_reads_the_same_at_every_margin(margin: str, said: str):
    found = ground()
    line = draft_lines.cell_line(
        "a1",
        "lon-n0001",
        found,
        "E09000901",
        {"margin": margin, "second": "lon-n0002"},
        {"lon-n0002": "Foxholt"},
        frozenset(),
        (),
    )
    assert line.value == said


def ground() -> Draft:
    """One area of two output areas beside another of one."""
    cells = {
        "a1": Cell("a1", "lon-n0001", "E09000901", margin=2.0, second="lon-n0002"),
        "a2": Cell("a2", "lon-n0001", "E09000902", margin=40.0, second="lon-n0002"),
        "b1": Cell("b1", "lon-n0002", "E09000902", margin=50.0, second="lon-n0001"),
    }
    areas = {
        "lon-n0001": Area("lon-n0001", "Alderwick", publishers=("a", "b")),
        "lon-n0002": Area("lon-n0002", "Foxholt", publishers=("a", "b")),
    }
    sides = (Side("a1", "a2", 100.0), Side("a2", "b1", 100.0))
    return Draft(areas, cells, sides, {"E09000901": "Quillhaven", "E09000902": "Tallowgate"})


def border_lines(**more: object) -> list[Line]:
    found, rules = ground(), Rules()
    flags = flags_of(found, rules)
    return draft_lines.borders(
        found,
        flags,
        doubts(found, flags, rules),
        {
            "a1": "margin=2;second=lon-n0002;roads=Quillhaven;ward=Alderwick",
            "a2": "margin=40;second=lon-n0002;roads=Foxholt",
        },
        {"lon-n0001": "Alderwick", "lon-n0002": "Foxholt"},
        {"lon-n0001": "E09000901", "lon-n0002": "E09000902"},
        **more,  # type: ignore[arg-type]
    )


def test_an_output_area_in_doubt_names_the_streets_that_run_in_it():
    found = border_lines(streets={"a1": ("Made-up Road", "Harrier Lane", "A9001", "b", "c")})
    (a1,) = [line for line in found if line.label == "a1"]
    assert a1.value == (
        "margin 2%, second choice Foxholt, its ward is Alderwick, its roads say Quillhaven, "
        "streets: Made-up Road, Harrier Lane, A9001, b"
    )


def test_what_the_roads_give_as_their_settlement_is_left_out_where_it_is_a_wide_name():
    """The name of the whole city says nothing of where a border runs."""
    found = border_lines(wide=frozenset({"quillhaven"}))
    (a1,) = [line for line in found if line.label == "a1"]
    assert a1.value == "margin 2%, second choice Foxholt, its ward is Alderwick"
    (a2,) = [line for line in found if line.label == "a2"]
    assert "its roads say Foxholt" in a2.value and "in Tallowgate, not the main borough" in a2.value


def test_the_most_in_doubt_come_first_and_the_line_says_how_many_there_are():
    found = [line for line in border_lines() if line.item == "lon-n0001"]
    labels = [line.label for line in found]
    # What was flagged comes first, then how many are in doubt, then each of them.
    assert labels[:2] == ["Flagged", "Flagged"]
    assert [label for label in labels if label != "Flagged"] == ["In doubt", "a1", "a2"]
    assert dict((line.label, line.value) for line in found)["In doubt"] == (
        "2 output areas are in doubt. An output area is in doubt where its margin is under "
        "10%, which is where its second choice is under a tenth further than its first, or "
        "where a flag about the border points at it. 1 has a margin under 10%. 1 lies "
        "outside the main borough."
    )


def test_the_cells_in_doubt_are_counted_once_and_every_one_is_under_a_reason():
    """The desk counted the cells on a border with a margin under 10%, and the draft every
    cell with one. The two differed, and cells between two seeds were under neither."""
    cells = {
        "a1": Cell("a1", "lon-n0001", "E09000901", margin=2.0, second="lon-n0002"),
        "a2": Cell("a2", "lon-n0001", "E09000901", margin=3.0, second="lon-n0002"),
        "a3": Cell("a3", "lon-n0001", "E09000901", margin=60.0, second="lon-n0002"),
        "b1": Cell("b1", "lon-n0002", "E09000901", margin=50.0, second="lon-n0001"),
    }
    areas = {
        "lon-n0001": Area("lon-n0001", "Alderwick", seed=(0.0, 0.0), publishers=("a", "b")),
        "lon-n0002": Area("lon-n0002", "Foxholt", seed=(300.0, 0.0), publishers=("a", "b")),
    }
    # a2 lies in the middle of its area, and a3 on the border with the other.
    sides = (Side("a1", "a2", 100.0), Side("a2", "a3", 100.0), Side("a3", "b1", 100.0))
    found, rules = Draft(areas, cells, sides, {"E09000901": "Quillhaven"}), Rules()
    flags = flags_of(found, rules)
    said = draft_lines.borders(
        found, flags, doubts(found, flags, rules), {}, {}, {"lon-n0001": "E09000901"}
    )
    first = dict((line.label, line.value) for line in said if line.item == "lon-n0001")
    assert first["In doubt"].startswith("3 output areas are in doubt. An output area is")
    assert first["In doubt"].endswith(
        "2 have a margin under 10%. 1 lies on the border with an area whose seed is close."
    )
    assert {"a1", "a2", "a3"} <= set(first)


def test_a_street_is_named_by_how_far_it_runs_in_an_output_area():
    """A road of no name is called by its number, and one with neither is left out."""
    squares = {"west": above(0, 0), "east": above(0, 1)}
    roads = [
        ("Harrier Lane", along((0.0, 0.5), (1.5, 0.5))),
        ("", along((0.2, 0.0), (0.2, 1.0))),
        ("A9001", along((0.6, 0.2), (0.6, 0.6))),
        ("Harrier Lane", along((1.5, 0.5), (2.0, 0.5))),
        ("Osier Way", along((1.0, 0.0), (1.0, 1.0))),
    ]
    metres = context_shapes.metres_in([shape for _, shape in roads], squares)
    found = draft_lines.streets_of([name for name, _ in roads], metres)
    # A road along the edge of two output areas runs in both: a border may run down it.
    assert found["west"] == ("Harrier Lane", "Osier Way", "A9001")
    assert found["east"] == ("Harrier Lane", "Osier Way")


def test_a_flag_about_the_name_is_no_line_of_a_border():
    found = Draft(
        {"lon-n0001": Area("lon-n0001", "Alderwick", publishers=("a",))},
        {"a1": Cell("a1", "lon-n0001", "E09000901")},
        (),
    )
    flags = flags_of(found, Rules())
    assert {flag.code for flag in flags} == {"one_publisher"}
    assert draft_lines.borders(found, flags, {}, {}, {}, {}) == []


def test_a_border_says_that_its_name_or_its_seed_rests_on_a_file_with_no_receipt():
    """A build may not rest on such a file, so whoever looks at the border is told."""
    found = Draft(
        {
            "lon-n0001": Area(
                "lon-n0001", "Alderwick", publishers=("a", "b"), unreceipted=("made-up-centres",)
            )
        },
        {"a1": Cell("a1", "lon-n0001", "E09000901")},
        (),
    )
    flags = flags_of(found, Rules())
    assert {flag.code for flag in flags} == {"no_receipt"}
    assert draft_lines.borders(found, flags, {}, {}, {}, {}) == [
        Line(
            "borders",
            "lon-n0001",
            "No receipt",
            "Its name or its seed rests on a file that has no receipt: made-up-centres.",
        )
    ]


def test_every_border_that_rests_on_the_file_with_no_receipt_says_so(draft: Made):
    rests = {row["area_id"] for row in draft.rows("areas.csv") if row["no_receipt"] == "true"}
    said = {
        row["item"]
        for row in draft.rows("desk/draft/lines.csv")
        if row["queue"] == "borders" and row["label"] == "No receipt"
    }
    assert rests and said == rests


# What the desk marks on its map


def marks_of(found: Draft) -> list[tuple[str, str, str, str]]:
    rules = Rules()
    flags = flags_of(found, rules)
    rows = draft_lines.marks(found, flags, doubts(found, flags, rules))
    assert {row["queue"] for row in rows} <= {"borders"}
    return [(row["item"], row["flag"], row["kind"], row["what"]) for row in rows]


def test_every_cell_in_doubt_is_marked_with_each_doubt_it_is_under():
    """The desk rings a cell in doubt. The ring says by its look what the doubt is, so
    the draft says of each cell which doubts it is under."""
    cells = [row for row in marks_of(ground()) if row[2] == "cell"]
    assert [row for row in cells if row[0] == "lon-n0001"] == [
        ("lon-n0001", "margin_under_10", "cell", "a1"),
        ("lon-n0001", "two_boroughs", "cell", "a2"),
    ]
    # A cell with a margin well over 10% in its area's main borough is under no doubt.
    assert not [row for row in cells if row[0] == "lon-n0002"]


def test_a_border_flagged_for_a_seed_close_to_another_marks_that_seed():
    cells = {
        "a1": Cell("a1", "lon-n0001", "E09000901", margin=60.0),
        "b1": Cell("b1", "lon-n0002", "E09000901", margin=50.0),
    }
    areas = {
        "lon-n0001": Area("lon-n0001", "Alderwick", seed=(0.0, 0.0), publishers=("a", "b")),
        "lon-n0002": Area("lon-n0002", "Foxholt", seed=(300.0, 0.0), publishers=("a", "b")),
    }
    found = Draft(areas, cells, (Side("a1", "b1", 100.0),), {"E09000901": "Quillhaven"})
    assert [row for row in marks_of(found) if row[1] == "seeds_close"] == [
        ("lon-n0001", "seeds_close", "cell", "a1"),
        ("lon-n0001", "seeds_close", "seed", "lon-n0002"),
        ("lon-n0002", "seeds_close", "cell", "b1"),
        ("lon-n0002", "seeds_close", "seed", "lon-n0001"),
    ]


def test_a_border_flagged_for_following_no_line_marks_each_stretch_that_follows_none():
    """The flag put no cell in doubt, so the desk ringed nothing, and nothing on its map
    said which stretch of the border was meant."""
    cells = {
        "a1": Cell("a1", "lon-n0001", "E09000901", ward="w1"),
        "a2": Cell("a2", "lon-n0001", "E09000901", ward="w1"),
        "b1": Cell("b1", "lon-n0002", "E09000901", ward="w1"),
        "b2": Cell("b2", "lon-n0002", "E09000901", ward="w2"),
    }
    areas = {
        "lon-n0001": Area("lon-n0001", "Alderwick", publishers=("a", "b")),
        "lon-n0002": Area("lon-n0002", "Foxholt", publishers=("a", "b")),
    }
    # The long side follows nothing. The short one runs along a ward line.
    sides = (Side("a1", "a2", 50.0), Side("a1", "b1", 900.0), Side("a2", "b2", 100.0))
    found = Draft(areas, cells, sides, {"E09000901": "Quillhaven"})
    assert [row for row in marks_of(found) if row[0] == "lon-n0001"] == [
        ("lon-n0001", "follows_nothing", "side", "a1 b1"),
    ]
    assert ("lon-n0002", "follows_nothing", "side", "b1 a1") in marks_of(found)


def test_a_border_flagged_for_two_town_centres_names_each_as_its_file_writes_it():
    found = Draft(
        {
            "lon-n0001": Area(
                "lon-n0001",
                "Alderwick",
                publishers=("a", "b"),
                centres=("Osierholm", "Pellam Cross"),
            )
        },
        {"a1": Cell("a1", "lon-n0001", "E09000901")},
        (),
        {"E09000901": "Quillhaven"},
    )
    assert marks_of(found) == [
        ("lon-n0001", "two_centres", "centre", "Osierholm"),
        ("lon-n0001", "two_centres", "centre", "Pellam Cross"),
    ]


def test_the_desk_is_handed_the_marks_of_every_border_and_each_is_of_a_flag_it_has_words_for(
    draft: Made,
):
    rows = draft.rows("desk/draft/marks.csv")
    assert draft.columns("desk/draft/marks.csv") == draft_lines.MARK_COLUMNS
    assert rows and {row["kind"] for row in rows} <= set(draft_lines.MARK_KINDS)
    areas = {row["area_id"] for row in draft.rows("desk/draft/areas.csv")}
    assert {row["item"] for row in rows} <= areas
    given = {row["oa21cd"]: row["area_id"] for row in draft.rows("desk/draft/oa_to_area.csv")}
    for row in rows:
        if row["kind"] == "cell":
            assert given[row["what"]] == row["item"]
        if row["kind"] == "side":
            own, other = row["what"].split()
            assert given[own] == row["item"] != given[other]
        if row["kind"] == "seed":
            assert row["what"] in areas - {row["item"]}
    # Every cell that a line is about is marked, and says what doubt it is under.
    lined = {
        (row["item"], row["label"])
        for row in draft.rows("desk/draft/lines.csv")
        if row["queue"] == "borders" and row["label"].startswith("E0")
    }
    assert lined == {(row["item"], row["what"]) for row in rows if row["kind"] == "cell"}
    # The border flagged for following no line has its stretches marked.
    stretches = {row["item"] for row in rows if row["flag"] == "follows_nothing"}
    flagged = {
        row["item"]
        for row in draft.rows("desk/draft/flags.csv")
        if (row["queue"], row["flag"]) == ("borders", "follows_nothing")
    }
    assert stretches == flagged and "lon-n0001" in stretches
