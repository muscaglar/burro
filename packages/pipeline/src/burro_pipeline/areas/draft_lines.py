"""What a person reads beside an item of the review desk: every doubt of the draft, in words.

The draft writes a plain sentence for every doubt it has. This writes them as
lines, by queue and item, in `lines.csv`:

    queue, item, label, value, source_id

The desk reads the file when it fills its queues. It keeps the first line of
its own for an item, and shows these under it, in the order of the file. A
line for an item the desk does not make stops its fill, so that no doubt is
lost without a word.

**The lines of a name.**

| Line | Says |
|---|---|
| The publisher and the product, in words | What the record writes, letter for letter. Whether |
| | that is the name. Where the record lies: a point inside, an outline and how much of it |
| | lies in the area, or outside and how far off. The record's id |
| `Look hard` | A mark to settle before the name ships, with why. It comes first: what |
| | is known of an item scrolls at the desk |
| `Publishers` | How many publishers write the name, and which. Where one writes it, |
| | whether the rule on one official publisher fits the name: `draft_decided.py` |
| `Kind of place` | The kind its publisher gives the place, in the publisher's own word |
| `Road records` | How many road records give the place as their settlement, where the |
| | place is known by a record that a road could give |
| `Points` | The points of a name put forward as an area, what a point is, in one line, |
| | and what gave each. A town centre and a ward are named as their files write them. A |
| | town centre that does not write the name is said to be of another name |
| `Size` | How many output areas the area of a name put forward as an area holds. It |
| | says nothing of any other area |
| `Other names` | The other names the draft puts in the area of a name put forward as an |
| | area, by what each is offered as: another name for the same ground, a smaller place |
| | inside, a wider name. Each is an item of its own, further down the queue |
| `Note` | A mark that asks less: a seed that stands far from its place, a class that was read |
| `No receipt` | The file with no receipt, and which of the name, its points and its seed |
| | rest on it |
| `Grown from`, `Nearest name` | For an area whose own name lies outside it: the name it |
| | was grown from and the names nearest to it, each with its record and how far off |
| `To change it` | The two rows a person writes in the file of decisions to give the area |
| | another name that lies in it. The desk cannot do it |

**A name that stands by the rule has no line.** The name of an area that the
rule on one official publisher fits, and that the draft has no mark on, is put
to nobody. The desk makes no item of it, and refuses a line of an item it does
not make. Its border is an item as before.

**The lines of a border.**

| Line | Says |
|---|---|
| `Name` | That nobody has read the name of the area, where it stands by the rule on one |
| | official publisher, and what it stands on. It comes first |
| `Flagged` | Why, for every flag of the draft about the border: what the flag found |
| `No receipt` | The file with no receipt that its name or its seed rests on |
| `In doubt` | How many output areas are in doubt, once, with the rule in words, and how |
| | many are under each reason. Every one is then a line |
| The code of an output area | Its margin and second choice, its ward, its borough where that |
| | is not the area's own, and the streets that run in it. The desk rings on its map every |
| | output area that a line is labelled with |

**One count of the output areas in doubt.** An output area is in doubt where
its margin is under 10%, whether or not it lies on the border, or where a flag
about the border points at it with some doubt. The line says how many there
are, and then how many are under each reason. The desk once counted apart the
cells on a border with a margin under 10%, which is fewer, and the two numbers
stood side by side with no word of why they differed.

**A margin** is by how much the second choice is further than the first, in
hundredths. Under a hundred it is said as written: "margin 6%". From a hundred
it is said in words: "which is 3.4 times as far". The draft writes no margin
over 999, so that one is said as "over 10 times as far".

**What the desk marks on its map** is in `marks.csv`, a row for each mark:

    queue, item, flag, kind, what

| `kind` | `what` | The desk draws |
|---|---|---|
| `cell` | The code of an output area in doubt | A ring whose look says the doubt |
| `side` | Two codes: the cell of this area, and the cell beside it | The stretch of the |
| | | border between the two, where a border follows no line |
| `seed` | The id of an area | A mark on the seed of that area, which stands close |
| `centre` | The name of a town centre, as its file writes it | That name |

A street is named from OS Open Roads, with local roads kept. What the roads of
an output area give as their settlement is left out where that is a wide name:
it says nothing of where a border runs.

**A distance says what it is from and what it is to.** A record that lies
outside an area is so far from the area's edge. A town centre's outline is so
far from the place's point. A seed is so far along the roads from another.

Every name in a line is one a publisher's record writes. Every number was
worked out by the draft. A label holds no word about who lives anywhere.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.areas import (
    draft_decided,
    draft_marks,
    draft_names,
    names_centres,
    names_places,
    names_wards,
)
from burro_pipeline.areas.draft_decided import Decided
from burro_pipeline.areas.draft_names import Naming, Offered
from burro_pipeline.areas.flags import (
    ABOUT_THE_NAME,
    BORDERS,
    SEEDS_CLOSE,
    TWO_BOROUGHS,
    TWO_PIECES,
    Draft,
    Flag,
)
from burro_pipeline.areas.flags import MARGIN as MARGIN_FLAG
from burro_pipeline.areas.flags import NO_RECEIPT as RESTS_ON_NO_RECEIPT
from burro_pipeline.areas.names_candidates import CARRIES, WRITES
from burro_pipeline.areas.names_draft import Drafted
from burro_pipeline.areas.names_look import Mark
from burro_pipeline.areas.seeds import Seed

NAMES = "names"
COLUMNS = ("queue", "item", "label", "value", "source_id")
POINTS, LOOK_HARD, NOTE, NO_RECEIPT = "Points", "Look hard", "Note", "No receipt"
GROWN_FROM, NEAREST, TO_CHANGE_IT = "Grown from", "Nearest name", "To change it"
KIND, ROADS_NAMING, SIZE = "Kind of place", "Road records", "Size"
PUBLISHERS = "Publishers"
OTHER_NAMES = "Other names"
# What another name is offered as, in the order and the words the line lists them in.
OFFERED_AS: Mapping[str, str] = {
    draft_names.SAME_GROUND: "Another name for the same ground",
    draft_names.INSIDE: "A smaller place inside",
    draft_names.WIDE: "A wider name, over this area and others",
}
FLAGGED, IN_DOUBT = "Flagged", "In doubt"
# The line of a border that says nobody has read the name of its area.
NAME_UNREAD = "Name"
# The table of what the desk marks on its map, and the kinds of mark.
MARK_COLUMNS = ("queue", "item", "flag", "kind", "what")
CELL, SIDE, SEED_MARK, CENTRE = "cell", "side", "seed", "centre"
MARK_KINDS = (CELL, SIDE, SEED_MARK, CENTRE)
# A margin under this many hundredths puts an output area in doubt: `flags.Rules`.
CLOSE = 10
# From this margin the second choice is said to be so many times as far, and the most
# a margin is written as: `assign.MOST_MARGIN`.
AS_FAR, MOST = 100, 999
# The rule by which an output area is in doubt, in words.
IN_DOUBT_WHERE = (
    f"An output area is in doubt where its margin is under {CLOSE}%, which is where its "
    "second choice is under a tenth further than its first, or where a flag about the "
    "border points at it."
)
# Why an output area is in doubt, in the order the line counts them: the flag, then the
# words for one output area and for several.
REASONS: tuple[tuple[str, str, str], ...] = (
    (MARGIN_FLAG, f"has a margin under {CLOSE}%", f"have a margin under {CLOSE}%"),
    (TWO_BOROUGHS, "lies outside the main borough", "lie outside the main borough"),
    (
        SEEDS_CLOSE,
        "lies on the border with an area whose seed is close",
        "lie on the border with an area whose seed is close",
    ),
    (TWO_PIECES, "is cut off from the largest piece", "are cut off from the largest piece"),
)
# The order of the lines of a name. A line of evidence is labelled with its publisher,
# and comes where `EVIDENCE_COMES` says. What a person weighs comes after it.
FIRST_TO_LAST = (
    *(LOOK_HARD, GROWN_FROM, NEAREST, "", PUBLISHERS, KIND, ROADS_NAMING, POINTS, SIZE),
    *(OTHER_NAMES, TO_CHANGE_IT, NOTE, NO_RECEIPT),
)
EVIDENCE_COMES = FIRST_TO_LAST.index("")
# The marks of the draft of names that ask less than a grave one, and are still said.
NOTED = frozenset(
    {Mark.SEED_FAR_FROM_PLACE, Mark.SEED_ON_A_LABEL_THAT_HOLDS_IT, Mark.CLASS_WAS_READ}
)
# The least share of an outline that is said as a share: under it, a hundredth rounds to none.
SLIVER = 0.005
# How many streets of an output area are named, those that run furthest in it first.
MOST_STREETS = 4
# How well a record places a name, the best first.
BEST = (draft_names.POINT_INSIDE, draft_names.POLYGON_OVERLAP, draft_names.LABEL_ONLY)
# What a point is, in one line, where points are shown.
WHAT_A_POINT_IS = (
    "A point is a weight the draft gives for a kind of record of the name, and a name with "
    "the points asked is put forward as an area."
)
# The name a record writes, by its source and its id.
Written = Mapping[tuple[str, str], str]
# The keys of what a row of `oa_to_area.csv` says placed its output area.
MARGIN, SECOND, ROADS, WARD = "margin", "second", "roads", "ward"


@dataclass(frozen=True)
class Line:
    """One line of one item."""

    queue: str
    item: str
    label: str
    value: str
    source_id: str = ""

    def row(self) -> dict[str, str]:
        return {
            "queue": self.queue,
            "item": self.item,
            "label": self.label,
            "value": self.value,
            "source_id": self.source_id,
        }


def in_words(publisher: str, product: str) -> str:
    """A source as a person reads it: who publishes it, and what it is called."""
    return f"{publisher.split(' (')[0].strip()}, {product.split(' (')[0].strip()}"


def _percent(share: float) -> str:
    return f"{round(share * 100)}%"


def _metres(metres: float) -> str:
    """A length in whole metres, as every line of a name writes one."""
    return f"{round(metres):,} m"


# Names


def item_of(offered: Offered, wide: Mapping[str, Sequence[str]]) -> str:
    """The item the desk makes of one name offered for one area."""
    if offered.role == draft_names.PRIMARY:
        return f"n:{offered.area_id}"
    first = min(wide.get(offered.name.place_id, [offered.area_id]))
    area = first if offered.kind == draft_names.WIDE else offered.area_id
    return f"a:{area}:{draft_marks.desk_slug(offered.as_offered)}"


def where(row: Mapping[str, str]) -> str:
    """Where a record lies, in words: inside the area, over it, or outside and how far off."""
    share = float(row["share"] or 0)
    if row["locates"] == draft_names.POINT_INSIDE and share < 1:
        return "A point on the line between this area and the next."
    if row["locates"] == draft_names.POINT_INSIDE:
        return "A point inside this area."
    if row["locates"] == draft_names.POLYGON_OVERLAP:
        return f"An outline. {_percent(share)} of it lies in this area."
    if share >= SLIVER:
        return (
            f"An outline that lies outside this area but for {_percent(share)} of it, "
            "which is too little to say that it lies here."
        )
    if row["metres_outside"] and float(row["metres_outside"]) >= 1:
        far = _metres(float(row["metres_outside"]))
        return f"Its record lies outside this area, {far} from its edge."
    return "Its record lies outside this area, at its edge."


def written(row: Mapping[str, str]) -> str:
    """What a record writes, and whether that is the name letter for letter."""
    if row["letter_for_letter"] == "true":
        return f"{row['as_written']}."
    if row["match"] == "part":
        return f"{row['as_written']}. The label is several names, of which this is one."
    return f"{row['as_written']}. It is not the name letter for letter."


def evidence_line(queue: str, item: str, row: Mapping[str, str], words: Mapping[str, str]) -> Line:
    record = f" Record {row['record_id']}." if row["record_id"] else ""
    return Line(
        queue,
        item,
        words.get(row["source_id"], row["source_id"]),
        f"{written(row)} {where(row)}{record}",
        row["source_id"],
    )


def centre_is_its_own(seed: Seed) -> bool:
    """Whether the town centre that gave a place points writes or holds its name."""
    return seed.place.centre is not None or any(
        other.candidate.source_id == names_centres.SOURCE
        and other.candidate.record_id == seed.weight.centre_record
        and other.match in CARRIES
        for other in seed.place.others
    )


def _called(written: Written, source: str, record: str) -> str:
    """The name a record writes, in quotes, where the draft holds the record."""
    name = written.get((source, record), "")
    return f' "{name}"' if name else ""


def _the_centre(seed: Seed, written: Written) -> str:
    """The town centre that gave a place its points: whose it is, what its file calls it,
    and how far its outline lies from the place's point."""
    weight = seed.weight
    called = _called(written, names_centres.SOURCE, weight.centre_record).strip()
    own = centre_is_its_own(seed)
    whose = "Its own town centre" if own else "A town centre of another name"
    named = f"{whose}, {called}" if called else whose
    if weight.centre_metres is None:
        far = ""
    elif round(weight.centre_metres) == 0:
        far = " Its outline holds the place's point."
    else:
        far = f" Its outline is {_metres(weight.centre_metres)} from the place's point."
    return f"{named}: {weight.centre}.{far} Record {weight.centre_record}."


def _the_ward(seed: Seed, written: Written) -> str:
    """The ward that gave a place its point, as its file calls it. A ward whose label
    only holds the name is no record of the name, and the desk is shown none: so the
    line says why the ward is not listed."""
    weight = seed.weight
    called = _called(written, names_wards.SOURCE, weight.ward_record)
    writes = any(
        other.candidate.source_id == names_wards.SOURCE
        and other.candidate.record_id == weight.ward_record
        and other.match in WRITES
        for other in seed.place.others
    )
    if writes:
        return f"The ward{called} carries it: {weight.ward}. Record {weight.ward_record}."
    return (
        f"The ward{called} carries it among other words: {weight.ward}. Its label is no "
        f"record of the name, so it is not listed above. Record {weight.ward_record}."
    )


def points_of(seed: Seed, asked: int, written: Written | None = None) -> str:
    """The points of a place, what a point is, and what gave each, as one line.

    `written` is the name each record writes, by its source and its id: a town centre
    and a ward are named as their files write them, and never by an id alone.
    """
    weight = seed.weight
    parts: list[str] = []
    if weight.place:
        parts.append(f"A populated place: {weight.place}.")
    if weight.roads:
        parts.append(f"{seed.place.roads} roads give it as their settlement: {weight.roads}.")
    if weight.centre:
        parts.append(_the_centre(seed, written or {}))
    if weight.ward:
        parts.append(_the_ward(seed, written or {}))
    asks = f"{weight.total} points, where {asked} are asked."
    return " ".join([asks, WHAT_A_POINT_IS, *parts])


HOW_MANY = ("No publisher writes it", "One publisher writes it", "Two publishers write it")
# What the line says where one publisher writes a name, by whether the rule fits the name.
ENOUGH = (
    "That is enough for a name: it writes the name for a populated place at a point inside "
    "this area."
)
NOT_ENOUGH = (
    "The rule that one official publisher is enough does not fit it: no such publisher "
    "writes it for a populated place at a point inside this area."
)
OF_A_WIDE_NAME = (
    "The rule that one official publisher is enough says nothing of a wide name: no point "
    "puts it inside one area."
)


def publishers_of(item: str, offered: Offered, fitted: bool) -> Line:
    """How many publishers write a name, and which. A name still says so, whatever the
    rule on one official publisher makes of it."""
    named = sorted({each.record.publisher for each in offered.records if each.record.writes})
    count = (
        HOW_MANY[len(named)] if len(named) < len(HOW_MANY) else f"{len(named)} publishers write it"
    )
    said = f"{count}: {', '.join(named)}." if named else f"{count}."
    if len(named) == 1 and offered.kind == draft_names.WIDE:
        said = f"{said} {OF_A_WIDE_NAME}"
    elif len(named) == 1:
        said = f"{said} {ENOUGH if fitted else NOT_ENOUGH}"
    return Line(NAMES, item, PUBLISHERS, said)


def kind_of(item: str, seed: Seed) -> Line | None:
    """The kind of place, in the word of the publisher whose record the place is known by."""
    kind = seed.place.key.kind
    return Line(NAMES, item, KIND, f"{kind}.", seed.place.key.source_id) if kind else None


def roads_of(item: str, seed: Seed) -> Line | None:
    """How many road records give a place as their settlement. None where the place is
    known by no record that a road could give: a town centre has none."""
    if seed.place.record is None:
        return None
    count = seed.place.roads
    if count == 0:
        said = "No road record gives it as its settlement."
    else:
        said = f"{count} road record{' gives' if count == 1 else 's give'} it as their settlement."
    return Line(NAMES, item, ROADS_NAMING, said, names_places.SOURCE)


def other_names(item: str, offered: Sequence[Offered]) -> Line:
    """The other names the draft puts in an area, by what each is offered as. A person
    who reads the name of an area sees what else the draft calls ground inside it."""
    others = [each for each in offered if each.role != draft_names.PRIMARY]
    if not others:
        return Line(NAMES, item, OTHER_NAMES, "The draft puts no other name in this area.")
    said: list[str] = []
    for kind, words in OFFERED_AS.items():
        named = sorted({each.as_offered for each in others if each.kind == kind})
        if named:
            said.append(f"{words}: {', '.join(named)}.")
    rest = sorted({each.as_offered for each in others if each.kind not in OFFERED_AS})
    if rest:
        said.append(f"Offered as nothing the desk has an answer for: {', '.join(rest)}.")
    count = len({each.as_offered for each in others})
    names = "1 other name" if count == 1 else f"{count} other names"
    return Line(NAMES, item, OTHER_NAMES, f"The draft puts {names} in this area. {' '.join(said)}")


def size_of(item: str, held: int) -> Line:
    """How large an area is, in output areas. It says nothing of any other area: the desk
    asks a name again when a line of it has changed."""
    return Line(NAMES, item, SIZE, f"{held} output area{'' if held == 1 else 's'}.")


def _marks(looks: Sequence[Mapping[str, str]]) -> dict[str, list[Line]]:
    """The lines of every mark that is listed, by item, in the order of the list."""
    found: dict[str, list[Line]] = {}
    for row in looks:
        if row["item"]:
            label = LOOK_HARD if row["grave"] == "true" else NOTE
            found.setdefault(row["item"], []).append(Line(NAMES, row["item"], label, row["why"]))
    return found


def _more_marks(
    drafted: Drafted, item: Mapping[str, str], wanted: frozenset[Mark], label: str
) -> dict[str, list[Line]]:
    found: dict[str, list[Line]] = {}
    for look in drafted.looks:
        place_id = drafted.area_ids[look.key]
        if look.mark in wanted and not look.grave and place_id in item:
            line = Line(NAMES, item[place_id], label, look.why, look.source_id)
            if line not in found.setdefault(item[place_id], []):
                found[item[place_id]].append(line)
    return found


def names(
    rows: Mapping[str, Sequence[Mapping[str, str]]],
    drafted: Drafted,
    naming: Naming,
    words: Mapping[str, str],
    held: Mapping[str, int] | None = None,
    decided: Decided = draft_decided.NOTHING,
) -> list[Line]:
    """The lines of every item of the queue of names, in the order of the items.

    `rows` holds the curated rows of a draft: the evidence, the marks to look
    at and the names offered. `words` says each source as a person reads it.
    `held` is how many output areas each area holds. `decided` is what the rule on
    one official publisher settles: a name that stands by it is no item, and has no line.
    """
    evidence: dict[tuple[str, str], list[Mapping[str, str]]] = {}
    for row in rows["name_evidence.csv"]:
        evidence.setdefault((row["area_id"], row["name"]), []).append(row)
    # A wide name is one item over all its areas: each record is said once, where it lies.
    best: dict[tuple[str, str, str], Mapping[str, str]] = {}
    wide: dict[str, list[str]] = {}
    for area in sorted(naming.first):
        for offered in naming.offered(area):
            if offered.kind == draft_names.WIDE:
                wide.setdefault(offered.name.place_id, []).append(area)
    by_item = draft_marks.items_of(drafted, naming)
    seeds = {drafted.area_ids[seed.key]: seed for seed in drafted.seeds.seeds}
    written = {
        (each.source_id, each.record_id): each.as_written for each in drafted.candidates.records
    }
    marks = _marks(rows["names_to_look_at.csv"])
    noted = _more_marks(drafted, by_item, NOTED, NOTE)
    unreceipted = _more_marks(drafted, by_item, frozenset({Mark.NO_RECEIPT}), NO_RECEIPT)
    near: dict[str, list[Mapping[str, str]]] = {}
    for row in rows["area_names.csv"]:
        if row["offered"] == "nearest":
            near.setdefault(row["area_id"], []).append(row)

    found: dict[str, list[Line]] = {}
    for area in sorted(naming.first):
        if naming.first[area] is None:
            found.setdefault(f"n:{area}", [])
        for offered in naming.offered(area):
            item = item_of(offered, wide)
            found.setdefault(item, [])
            for row in evidence.get((area, offered.as_offered), []):
                key = (item, row["source_id"], row["record_id"])
                if key not in best or BEST.index(row["locates"]) < BEST.index(best[key]["locates"]):
                    best[key] = row
    for (item, _, _), row in best.items():
        found[item].append(evidence_line(NAMES, item, row, words))
    sizes = held or {}
    weighed: set[str] = set()
    for area in sorted(naming.first):
        if area in sizes:
            found.setdefault(f"n:{area}", []).append(size_of(f"n:{area}", sizes[area]))
        found.setdefault(f"n:{area}", []).append(other_names(f"n:{area}", naming.offered(area)))
        for offered in naming.offered(area):
            seed = seeds.get(offered.name.place_id)
            item = item_of(offered, wide)
            if seed is not None and item not in weighed and item in found:
                # A wide name is one item over all its areas: it is weighed once.
                weighed.add(item)
                found[item].append(publishers_of(item, offered, item in decided.fitted))
                found[item] += [
                    line for line in (kind_of(item, seed), roads_of(item, seed)) if line
                ]
            if offered.role == draft_names.PRIMARY and seed is not None:
                said = points_of(seed, drafted.seeds.points, written)
                found[f"n:{area}"].append(Line(NAMES, f"n:{area}", POINTS, said))
    for area, rows_near in sorted(near.items()):
        item = f"n:{area}"
        for row in rows_near:
            grown = row["place_id"] == area
            lies = f" It lies in {row['lies_in']}." if row["lies_in"] else ""
            found.setdefault(item, []).append(
                Line(
                    NAMES,
                    item,
                    GROWN_FROM if grown else NEAREST,
                    f"{row['name']}. {_metres(float(row['metres']))} from the edge of this "
                    f"area.{lies} "
                    f"Record {row['record_id']}.",
                    row["source_id"],
                )
            )
    for more in (marks, noted, unreceipted):
        for item, lines in more.items():
            found.setdefault(item, []).extend(lines)
    for row in rows["names_to_look_at.csv"]:
        if row["mark"] in (draft_names.HEAVIER_NAME_INSIDE, draft_names.NOT_ITS_SEED):
            item = f"n:{row['area_id']}"
            found.setdefault(item, []).append(Line(NAMES, item, TO_CHANGE_IT, by_hand(row)))
    return [
        line
        for item in sorted(found)
        if item not in decided.left_out
        for line in sorted(found[item], key=_read_first)
    ]


def _read_first(line: Line) -> int:
    """Where a line of a name comes. What is known of an item scrolls, so what a person
    must not miss is first: a mark to settle, then the names nearest an area with none."""
    return FIRST_TO_LAST.index(line.label) if line.label in FIRST_TO_LAST else EVIDENCE_COMES


def by_hand(row: Mapping[str, str]) -> str:
    """How a person gives an area the name of a place that lies in it: the desk cannot."""
    if row["mark"] == draft_names.NOT_ITS_SEED:
        return (
            "The name it was grown from lies outside it. To keep that name, move the border "
            "to take in its record. To make the name offered here the seed, write in the file "
            f"of decisions: {row['place_id']},area and {row['area_id']},inside."
        )
    return (
        f"To make {row['name']} the name of an area of its own, write in the file of "
        f"decisions: {row['place_id']},area. To give this area that name in place of its "
        f"own, write also: {row['area_id']},inside. Then make the draft again."
    )


# Borders


def _said(evidence: str) -> dict[str, str]:
    parts = [part.split("=", 1) for part in evidence.split(";") if part.strip()]
    return {key.strip(): value.strip() for key, value in parts if value.strip()}


def cell_line(
    oa: str,
    area: str,
    draft: Draft,
    main: str,
    said: Mapping[str, str],
    area_names: Mapping[str, str],
    wide: frozenset[str],
    streets: Sequence[str],
) -> Line:
    """One output area in doubt, in words a person who knows the ground can place."""
    cell = draft.cells[oa]
    parts: list[str] = [*_second_choice(said, area_names)]
    if cell.borough != main:
        parts.append(f"in {draft.boroughs.get(cell.borough, cell.borough)}, not the main borough")
    if said.get(WARD):
        parts.append(f"its ward is {said[WARD]}")
    if said.get(ROADS) and said[ROADS].casefold() not in wide:
        parts.append(f"its roads say {said[ROADS]}")
    if streets:
        parts.append("streets: " + ", ".join(streets))
    return Line(BORDERS, area, oa, ", ".join(parts) if parts else "No evidence is given")


def _second_choice(said: Mapping[str, str], area_names: Mapping[str, str]) -> list[str]:
    """The margin of an output area and its second choice, in words a person can read.

    A margin is by how much the second choice is further than the first. Under a
    hundred it is said as written. From a hundred it is said as so many times as far:
    "margin 240%" says little, and "3.4 times as far" says it.
    """
    second = said.get(SECOND, "")
    named = f"second choice {area_names.get(second) or second}" if second else ""
    try:
        margin = float(said[MARGIN]) if MARGIN in said else None
    except ValueError:
        margin = None
    if margin is None:
        return [named] if named else []
    if margin < AS_FAR:
        return [f"margin {said[MARGIN]}%", *([named] if named else [])]
    if margin >= MOST:
        times = "over 10 times as far"
    elif margin == AS_FAR:
        times = "twice as far"
    else:
        times = f"{1 + margin / 100:.1f} times as far"
    return [f"{named}, which is {times}" if named else f"its second choice is {times}"]


def reasons_of(
    draft: Draft, flags: Sequence[Flag], doubts: Mapping[str, Mapping[str, float]]
) -> dict[str, dict[str, list[str]]]:
    """Why each output area in doubt is in doubt: for each area, and each of its output
    areas in doubt, the flags it is under, in the order of `REASONS`.

    An output area with a margin under 10% is under the flag for margins whether or not
    so many are that the area is flagged for it.
    """
    pointed: dict[tuple[str, str], set[str]] = {}
    for flag in flags:
        if flag.queue == BORDERS and flag.code not in ABOUT_THE_NAME:
            for oa, doubt in zip(flag.cells, flag.doubt, strict=True):
                if doubt > 0:
                    pointed.setdefault((flag.area, oa), set()).add(flag.code)
    order = [code for code, _, _ in REASONS]
    found: dict[str, dict[str, list[str]]] = {}
    for area, cells in sorted(doubts.items()):
        for oa in sorted(cells):
            under = set(pointed.get((area, oa), set()))
            margin = draft.cells[oa].margin
            if margin is not None and 0 <= margin < CLOSE:
                under.add(MARGIN_FLAG)
            ranked = sorted(under, key=lambda code: (order.index(code), code))
            found.setdefault(area, {})[oa] = ranked
    return found


def in_doubt(cells: Mapping[str, Sequence[str]]) -> str:
    """How many output areas of an area are in doubt, once, with the rule in words, and
    how many are under each reason. An output area may be under more than one."""
    count = f"{len(cells)} output area{' is' if len(cells) == 1 else 's are'} in doubt."
    said: list[str] = []
    for code, one, several in REASONS:
        under = sum(code in reasons for reasons in cells.values())
        if under:
            said.append(f"{under} {one if under == 1 else several}.")
    return " ".join([count, IN_DOUBT_WHERE, *said])


def marks(
    draft: Draft, flags: Sequence[Flag], doubts: Mapping[str, Mapping[str, float]]
) -> list[dict[str, str]]:
    """What the desk marks on the map of each border, a row for each mark.

    Every output area in doubt, with each doubt it is under, so that its ring says by its
    look what the doubt is. Each stretch of a border that follows no line. The seed that
    stands close. Each town centre a flag names.
    """
    found: list[tuple[str, str, str, str]] = []
    for area, cells in reasons_of(draft, flags, doubts).items():
        found += [(area, code, CELL, oa) for oa, under in cells.items() for code in under]
    for flag in flags:
        if flag.queue != BORDERS or flag.code in ABOUT_THE_NAME:
            continue
        found += [(flag.area, flag.code, SIDE, f"{own} {other}") for own, other in flag.sides]
        found += [(flag.area, flag.code, SEED_MARK, seed) for seed in flag.seeds]
        found += [(flag.area, flag.code, CENTRE, centre) for centre in flag.centres]
    order = {kind: at for at, kind in enumerate(MARK_KINDS)}
    unique = sorted(set(found), key=lambda row: (row[0], row[1], order[row[2]], row[3]))
    return [
        {"queue": BORDERS, "item": item, "flag": flag, "kind": kind, "what": what}
        for item, flag, kind, what in unique
    ]


def borders(
    draft: Draft,
    flags: Sequence[Flag],
    doubts: Mapping[str, Mapping[str, float]],
    evidence: Mapping[str, str],
    area_names: Mapping[str, str],
    main_borough: Mapping[str, str],
    *,
    wide: frozenset[str] = frozenset(),
    streets: Mapping[str, Sequence[str]] | None = None,
    unread: Mapping[str, tuple[str, str]] | None = None,
) -> list[Line]:
    """The lines of every item of the queue of borders, in the order of the items.

    `doubts` gives, for each area, its output areas in doubt and how unsure the
    method was of each. `evidence` is what `oa_to_area.csv` says placed each
    output area. `wide` holds the wide names, in lower case. `streets` names
    the streets of an output area, those that run furthest in it first. `unread`
    holds, for each area whose name nobody has read, what its border says of the
    name and the source the name stands on.
    """
    raised: dict[str, list[Flag]] = {}
    rests: dict[str, list[Flag]] = {}
    for flag in flags:
        if flag.queue == BORDERS and flag.code not in ABOUT_THE_NAME:
            raised.setdefault(flag.area, []).append(flag)
        elif flag.queue == BORDERS and flag.code == RESTS_ON_NO_RECEIPT:
            rests.setdefault(flag.area, []).append(flag)
    found: list[Line] = []
    reasons = reasons_of(draft, flags, doubts)
    for area in sorted(draft.areas):
        if area in (unread or {}):
            found.append(Line(BORDERS, area, NAME_UNREAD, *(unread or {})[area]))
        for flag in raised.get(area, []):
            found.append(Line(BORDERS, area, FLAGGED, flag.why))
        # It is no flag of the border: it is on most areas, and is settled where names
        # are read. But a build may not rest on such a file, so it is said.
        for flag in rests.get(area, []):
            found.append(Line(BORDERS, area, NO_RECEIPT, flag.why))
        cells = doubts.get(area, {})
        if not cells:
            continue
        # Every one is listed, the most in doubt first: the desk rings what a line names.
        listed = sorted(cells, key=lambda oa: (-cells[oa], oa))
        found.append(Line(BORDERS, area, IN_DOUBT, in_doubt(reasons[area])))
        for oa in listed:
            found.append(
                cell_line(
                    oa,
                    area,
                    draft,
                    main_borough.get(area, ""),
                    _said(evidence.get(oa, "")),
                    area_names,
                    wide,
                    (streets or {}).get(oa, ())[:MOST_STREETS],
                )
            )
    return found


def streets_of(
    names: Sequence[str], metres: Mapping[str, Mapping[int, float]]
) -> dict[str, tuple[str, ...]]:
    """The streets of each output area by name, those that run furthest in it first.

    `names` is the name of each road, or its number where it has no name, in
    the order the roads were measured in. A road with neither is left out.
    """
    found: dict[str, tuple[str, ...]] = {}
    for oa, held in sorted(metres.items()):
        along: dict[str, float] = {}
        for at, length in held.items():
            if names[at]:
                along[names[at]] = along.get(names[at], 0.0) + length
        found[oa] = tuple(sorted(along, key=lambda name: (-along[name], name)))
    return found
