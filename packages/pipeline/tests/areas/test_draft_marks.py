"""Every mark of a draft reaches the person who decides, on the item it belongs to.

Every name here is made up. `names_support.py` draws the town, and the ground
is two output areas given to one area.
"""

import json
from dataclasses import replace
from pathlib import Path

from burro_pipeline.areas import draft_files, draft_marks
from burro_pipeline.areas.draft_names import INSIDE, POINT, Name, Naming, Record, name_areas
from burro_pipeline.areas.names_draft import Drafted
from burro_pipeline.areas.names_look import Look, Mark

from . import names_support as town
from .draft_support import made

SAYS_WHO = 'It holds the word "students", which is a word for a group of people.'
QUESTIONS = Path(__file__).resolve().parents[4] / "tools" / "desk" / "questions.json"


def point(oa: str, name: str, record_id: str) -> Record:
    return Record(
        source_id="os-open-names",
        record_id=record_id,
        publisher="Ordnance Survey",
        field="NAME1",
        as_written=name,
        gives=POINT,
        match="same",
        writes=True,
        lies_on={oa: 1.0},
    )


def two_names() -> tuple[Drafted, Naming, list[Name]]:
    """Alderwick is an area, and Foxholt is a smaller place inside it."""
    drafted = town.drafted()
    area = drafted.area_ids[town.seed("Alderwick").key]
    other = drafted.area_ids[town.seed("Foxholt").key]
    names = [
        Name(area, "Alderwick", "area", 9, (point("a1", "Alderwick", "osgb-1"),)),
        Name(other, "Foxholt", INSIDE, 6, (point("a2", "Foxholt", "osgb-2"),), of=(area,)),
    ]
    return drafted, name_areas(names, {"a1": area, "a2": area}, {area: area}), names


def looked(drafted: Drafted, *looks: Look) -> Drafted:
    return replace(drafted, looks=looks)


def look(name: str, mark: Mark, why: str = "Why.", *, elsewhere: bool = False) -> Look:
    return Look(town.seed(name).key, name, mark, why, elsewhere=elsewhere)


def test_a_name_that_may_say_who_lives_there_is_flagged_for_the_founder_at_the_desk():
    """Section 6 of the areas design: each such name is put to the founder."""
    drafted, naming, _ = two_names()
    marked = looked(
        drafted,
        look("Foxholt", Mark.MAY_DESCRIBE_RESIDENTS, SAYS_WHO),
        look("Alderwick", Mark.MAY_DESCRIBE_RESIDENTS, SAYS_WHO),
    )
    assert draft_marks.flags_of(marked, naming) == [
        {"queue": "names", "item": "a:lon-n0001:foxholt", "flag": "describes_residents"},
        {"queue": "names", "item": "a:lon-n0001:foxholt", "flag": "look_hard"},
        {"queue": "names", "item": "n:lon-n0001", "flag": "describes_residents"},
        {"queue": "names", "item": "n:lon-n0001", "flag": "look_hard"},
    ]


def test_a_name_with_a_mark_to_settle_is_flagged_so_that_the_desk_stops_at_it():
    """The desk shows a mark to settle as a line, "Look hard". The key that goes to the
    next flagged name passed every name whose only doubt was such a mark."""
    drafted, naming, names = two_names()
    marked = looked(
        drafted,
        look("Alderwick", Mark.ALSO_A_BOROUGH, "A borough has the same name."),
        # A station of the same name that stands where the place does is no mark to settle.
        look("Foxholt", Mark.ALSO_A_STATION),
    )
    assert draft_marks.flags_of(marked, naming) == [
        {"queue": "names", "item": "n:lon-n0001", "flag": "look_hard"}
    ]
    listed = draft_marks.looks_of(marked, naming, names)
    assert [(row["item"], row["grave"]) for row in listed] == [("n:lon-n0001", "true")]


def test_every_name_with_a_line_to_look_hard_at_is_flagged_and_no_other_is_for_it():
    draft = made()
    hard = {
        row["item"]
        for row in draft.rows("desk/draft/lines.csv")
        if (row["queue"], row["label"]) == ("names", "Look hard")
    }
    flagged = {
        row["item"]
        for row in draft.rows("desk/draft/flags.csv")
        if (row["queue"], row["flag"]) == ("names", "look_hard")
    }
    assert hard and flagged == hard
    # One whose only doubt is such a mark was flagged by nothing before.
    others = {
        row["item"]
        for row in draft.rows("desk/draft/flags.csv")
        if row["queue"] == "names" and row["flag"] != "look_hard"
    }
    assert "n:lon-n0009" in hard - others


def test_the_desk_has_words_for_every_flag_of_a_name_that_this_part_raises():
    asked = json.loads(QUESTIONS.read_bytes())["queues"]
    words = next(queue["flags"] for queue in asked if queue["id"] == "names")
    raised = {*draft_marks.DESK_FLAGS.values(), draft_marks.LOOK_HARD}
    assert raised <= set(words)
    assert words[draft_marks.LOOK_HARD] == "the draft has a mark on it to settle"


def test_every_grave_mark_is_listed_with_its_item_and_a_name_for_residents_comes_first():
    drafted, naming, names = two_names()
    marked = looked(
        drafted,
        look("Alderwick", Mark.ALSO_A_BOROUGH, "A borough has the same name."),
        look("Foxholt", Mark.MAY_BE_A_BUILT_THING, "Its box is the smallest."),
        look("Foxholt", Mark.MAY_DESCRIBE_RESIDENTS, SAYS_WHO),
        look("Foxholt", Mark.ALSO_A_STATION, "A station 3 km away.", elsewhere=True),
    )
    rows = draft_marks.looks_of(marked, naming, names)
    assert [(row["item"], row["mark"]) for row in rows] == [
        ("a:lon-n0001:foxholt", "may_describe_residents"),
        ("a:lon-n0001:foxholt", "may_be_a_built_thing"),
        ("n:lon-n0001", "also_a_borough"),
        ("a:lon-n0001:foxholt", "also_a_station"),
    ]
    assert {row["grave"] for row in rows} == {"true"}
    assert {row["area_id"] for row in rows} == {"lon-n0001"}
    assert rows[0]["why"] == SAYS_WHO and rows[0]["name"] == "Foxholt"


def test_a_mark_that_most_names_carry_or_that_is_what_one_would_expect_is_not_listed():
    drafted, naming, names = two_names()
    marked = looked(
        drafted,
        look("Alderwick", Mark.ONE_PUBLISHER),
        look("Alderwick", Mark.NO_RECEIPT),
        # A station of the same name that stands where the place does.
        look("Alderwick", Mark.ALSO_A_STATION),
        look("Alderwick", Mark.ALSO_A_WARD),
    )
    assert draft_marks.looks_of(marked, naming, names) == []
    # One publisher is still a flag at the desk: it is one decision, and is said once.
    assert draft_marks.flags_of(marked, naming) == [
        {"queue": "names", "item": "n:lon-n0001", "flag": "one_publisher"}
    ]


def test_a_mark_on_a_name_that_is_offered_nowhere_asks_nothing_of_anybody():
    drafted, naming, names = two_names()
    marked = looked(drafted, look("Eskerfold", Mark.MAY_DESCRIBE_RESIDENTS, SAYS_WHO))
    assert draft_marks.looks_of(marked, naming, names) == []
    assert draft_marks.flags_of(marked, naming) == []


def test_what_the_naming_found_is_listed_beside_what_the_names_found():
    drafted = town.drafted()
    area = drafted.area_ids[town.seed("Alderwick").key]
    # The name the area was grown from lies outside it, and no other name lies in it.
    names = [Name(area, "Alderwick", "area", 9, (point("b1", "Alderwick", "osgb-1"),))]
    naming = name_areas(names, {"a1": area, "b1": "lon-n0900"}, {area: area})
    rows = draft_marks.looks_of(looked(drafted), naming, names)
    first = rows[0]
    assert (first["area_id"], first["mark"], first["item"], first["from"]) == (
        area,
        "unnamed",
        f"n:{area}",
        "naming",
    )
    assert first["grave"] == "true"


def test_an_area_with_no_name_is_flagged_so_that_the_desk_puts_it_first():
    """The desk has no word for an area with no name. It has one for a name few write."""
    drafted = town.drafted()
    first = sorted(drafted.area_ids.values())[0]
    nothing = Naming(first={first: None}, others={first: ()}, marks=())
    assert draft_marks.flags_of(looked(drafted), nothing) == [
        {"queue": "names", "item": f"n:{first}", "flag": "one_publisher"}
    ]


# The whole draft of the made-up town


def test_the_list_of_marks_of_a_whole_draft_names_an_item_of_the_desk_in_every_row():
    draft = made()
    rows = draft.rows(draft_files.TO_LOOK_AT)
    assert draft.columns(draft_files.TO_LOOK_AT) == draft_marks.COLUMNS
    items = {f"n:{row['area_id']}" for row in draft.rows("areas.csv")}
    items |= {
        f"a:{row['area_id']}:{draft_marks.desk_slug(row['alias'])}"
        for row in draft.rows("aliases.csv")
    }
    assert rows and {row["item"] for row in rows} <= items
    # Every grave mark of the draft of names is in the list, under the name it is on.
    grave = {
        (row["area_id"], row["mark"], row["why"])
        for row in draft.rows("made/names/hard_look.csv")
        if row["grave"] == "true"
    }
    listed = {(row["place_id"], row["mark"], row["why"]) for row in rows if row["from"] == "names"}
    assert listed and listed <= grave
    offered = {
        row["place_id"] for row in draft.rows("area_names.csv") if row["offered"] != "nearest"
    }
    assert {each for each in grave if each[0] in offered} == listed


def test_the_note_beside_a_draft_says_where_every_mark_is_written():
    about = (made().out / "about.txt").read_text(encoding="utf-8")
    assert "names_to_look_at.csv" in about and "made/names/hard_look.csv" in about
