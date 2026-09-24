"""Every mark of a draft, by the item the review desk makes of the name it is on.

Two parts of the draft mark a name. The draft of names marks what it sees
before a border is drawn: a name that may say who lives there, a second name
of one record, a name that is also a borough's. The naming of the areas marks
what it sees once the borders are drawn: an area no name lies in, a name whose
record lies next door. A person decides with one item in view, so every mark
is given the item it belongs to, and is written in one list.

| Made here | Holds |
|---|---|
| `items_of` | The item the desk makes of each place: `n:` and an area, or `a:`, an area |
| | and the name as a slug |
| `flags_of` | The flags of the desk's queue of names, by item |
| `looks_of` | Every mark a person should settle, the gravest first: `names_to_look_at.csv` |

**A name that may say who lives there** is flagged for the founder, as section
6 of the areas design asks. The desk has a flag for it. The name is kept as
its publisher writes it, and nothing here changes or drops it.

**A name with a mark to settle is flagged.** The desk shows such a mark as a
line of the item, and goes from one flagged item to the next by a key. A name
whose only doubt was a mark was passed by that key. So every item that the
list of marks names with a grave mark carries the flag `look_hard`.

**The gravest first.** A name that may describe residents, then what the
naming found, then the other grave marks of the draft of names in its own
order. A mark that most names carry is left out of the list: one publisher,
and a file with no receipt, are each one decision and are said once.

**One publisher is a doubt only where the rule does not fit.** The founder
decided that a name an official publisher writes for a populated place, at a
point inside the area, is a name: `draft_decided.py`. The draft of names marks
every name that fewer than two publishers write, before a border is drawn. Once
the borders are drawn the flag is raised only on a name the rule does not fit.

A mark is never a verdict. It changes no name, no tier and no seed.
"""

import re
from collections.abc import Collection, Mapping, Sequence

from burro_pipeline.areas import draft_names
from burro_pipeline.areas.draft_names import Name, Naming
from burro_pipeline.areas.names_draft import Drafted
from burro_pipeline.areas.names_look import Look, Mark

NAMES_QUEUE = "names"
# The flags of the desk's queue of names, and the mark of the draft of names each is.
DESK_FLAGS: Mapping[Mark, str] = {
    Mark.ONE_PUBLISHER: "one_publisher",
    Mark.SAME_NAME_ELSEWHERE: "same_name_elsewhere",
    Mark.MAY_DESCRIBE_RESIDENTS: "describes_residents",
}
# The flag of an item that carries a mark to settle before the name ships.
LOOK_HARD = "look_hard"
# The marks of the naming that a person should settle before the name ships. A name that
# was put under another area before the borders were drawn lies where its record puts it,
# and asks nothing of anybody.
GRAVE_OF_THE_NAMING = frozenset(
    {
        draft_names.UNNAMED,
        draft_names.NOT_ITS_SEED,
        draft_names.SEED_LIES_ELSEWHERE,
        draft_names.HEAVIER_NAME_INSIDE,
        draft_names.BY_AN_OUTLINE_ALONE,
    }
)
# Every mark that is listed, the gravest first.
GRAVEST_FIRST: tuple[str, ...] = (
    Mark.MAY_DESCRIBE_RESIDENTS.value,
    draft_names.UNNAMED,
    draft_names.NOT_ITS_SEED,
    draft_names.SEED_LIES_ELSEWHERE,
    draft_names.HEAVIER_NAME_INSIDE,
    draft_names.BY_AN_OUTLINE_ALONE,
    Mark.SAME_NAME_ELSEWHERE.value,
    Mark.TWO_NAMES_ONE_PLACE.value,
    Mark.JOINED_BEYOND_1KM.value,
    Mark.MAY_BE_A_BUILT_THING.value,
    Mark.ALSO_A_BOROUGH.value,
    Mark.ALSO_A_STATION.value,
    Mark.ALSO_A_WARD.value,
    Mark.AS_MANY_POINTS.value,
    draft_names.ON_THE_LINE,
    draft_names.WAS_PUT_UNDER_ANOTHER,
)
COLUMNS = ("area_id", "name", "place_id", "mark", "why", "grave", "item", "from")
# Which part of the draft made a mark.
OF_THE_NAMES, OF_THE_NAMING = "names", "naming"


def desk_slug(name: str) -> str:
    """A name as the review desk makes the id of an item from it."""
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")


def items_of(drafted: Drafted, naming: Naming) -> dict[str, str]:
    """The item the desk makes of each place that is offered, by the id of the place.

    The desk names the item of an area `n:` and its id. It names the item of
    another name `a:`, the area it is offered for and the name as a slug, and
    makes one item of a wide name, under the first of its areas.
    """
    item: dict[str, str] = {}
    wide: dict[str, list[str]] = {}
    for area in sorted(naming.first):
        for offered in naming.offered(area):
            if offered.why == draft_names.SECOND_NAME:
                continue
            if offered.role == draft_names.PRIMARY:
                item[offered.name.place_id] = f"n:{area}"
            elif offered.kind == draft_names.WIDE:
                wide.setdefault(offered.name.place_id, []).append(area)
            else:
                item[offered.name.place_id] = f"a:{area}:{desk_slug(offered.as_offered)}"
    by_key = {drafted.area_ids[seed.key]: seed for seed in drafted.seeds.seeds}
    for place_id, areas in wide.items():
        item[place_id] = f"a:{min(areas)}:{desk_slug(by_key[place_id].name)}"
    return item


def flags_of(
    drafted: Drafted, naming: Naming, fitted: Collection[str] = ()
) -> list[dict[str, str]]:
    """The flags of the desk's queue of names, by the item the desk makes of each name.

    `fitted` holds the items that the rule on one official publisher fits. That one
    publisher writes such a name is no doubt, so it is no flag.

    An area with no name is flagged as one that fewer than two publishers write: none
    does. The desk puts a flagged item first, so an area with no name is not left among
    the names that nothing is known against.
    """
    item = items_of(drafted, naming)
    found = {
        (item[drafted.area_ids[look.key]], DESK_FLAGS[look.mark])
        for look in drafted.looks
        if look.mark in DESK_FLAGS and drafted.area_ids[look.key] in item
    }
    found -= {(name, DESK_FLAGS[Mark.ONE_PUBLISHER]) for name in fitted}
    found |= {(f"n:{area}", DESK_FLAGS[Mark.ONE_PUBLISHER]) for area in naming.unnamed}
    found |= {(name, LOOK_HARD) for name in to_settle(drafted, naming)}
    return [{"queue": NAMES_QUEUE, "item": name, "flag": flag} for name, flag in sorted(found)]


def to_settle(drafted: Drafted, naming: Naming) -> set[str]:
    """The items that carry a mark to settle before the name ships: every item that
    `looks_of` lists with a grave mark."""
    item = items_of(drafted, naming)
    found = {
        item.get(mark.place_id, "") if mark.place_id else f"n:{mark.area_id}"
        for mark in naming.marks
        if mark.mark in GRAVE_OF_THE_NAMING
    }
    found |= {item.get(drafted.area_ids[look.key], "") for look in grave_looks(drafted)}
    return found - {""}


def grave_looks(drafted: Drafted) -> list[Look]:
    """The marks of the draft of names that a person should settle, each said once."""
    return [look for look in drafted.looks if look.grave]


def _place(order: Mapping[str, int], row: Mapping[str, str]) -> tuple[int, str, str, str]:
    return (order[row["mark"]], row["area_id"], row["name"], row["why"])


def looks_of(drafted: Drafted, naming: Naming, names: Sequence[Name]) -> list[dict[str, str]]:
    """Every mark a person should look at, the gravest first, each with the item it is on.

    A mark of the draft of names is listed under the area its name is offered
    for. One on a name that is offered nowhere has no item, and is left out:
    nobody is asked about that name.
    """
    by_id = {name.place_id: name for name in names}
    item = items_of(drafted, naming)
    found: list[dict[str, str]] = []
    for mark in naming.marks:
        found.append(
            {
                "area_id": mark.area_id,
                "name": by_id[mark.place_id].name if mark.place_id in by_id else "",
                "place_id": mark.place_id,
                "mark": mark.mark,
                "why": mark.why,
                "grave": "true" if mark.mark in GRAVE_OF_THE_NAMING else "false",
                "item": item.get(mark.place_id, "") if mark.place_id else f"n:{mark.area_id}",
                "from": OF_THE_NAMING,
            }
        )
    for look in grave_looks(drafted):
        place_id = drafted.area_ids[look.key]
        if place_id not in item:
            continue
        found.append(
            {
                "area_id": naming.placed.get(place_id, ""),
                "name": look.name,
                "place_id": place_id,
                "mark": look.mark.value,
                "why": look.why,
                "grave": "true",
                "item": item[place_id],
                "from": OF_THE_NAMES,
            }
        )
    order = {mark: at for at, mark in enumerate(GRAVEST_FIRST)}
    unique = {(row["item"], row["mark"], row["why"]): row for row in found}
    return sorted(unique.values(), key=lambda row: _place(order, row))
