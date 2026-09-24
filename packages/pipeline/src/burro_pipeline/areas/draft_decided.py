"""What the founder has decided of a name, and what the decision settles.

The design asked that a name rest on two publishers. Two in three names of the
first draft of London rest on one, and the design left the rule to the founder.
On 2026-09-24 the founder decided it: decision record 0022.

| | |
|---|---|
| The rule | A name that an official publisher writes for a populated place, at a |
| | point inside the area, is a name. It needs no second publisher |
| An official publisher | One whose file is a public body's own list of populated |
| | places, each with a point: `OFFICIAL_PLACES`. Today that is OS Open Names |
| Writes the name | The record's label is the name, letter for letter |
| At a point inside the area | The record's point lies in the area as drawn. An outline |
| | that lies over the area is no point, and a label that lies outside is none |

**What the rule fits.** The name of an area, and another name of the same
ground or of a smaller place inside it. A wide name lies over several areas,
so no point puts it inside one: the rule says nothing of it.

**What the rule settles.** The flag that one publisher writes a name is raised
only where the rule does not fit the name. And the name of an area stands by the
rule alone, and is put to nobody, where the rule fits it and the draft has no
mark on it: `stands`. A mark is a doubt the decision did not settle, so a name
with one is still read by a person. So is a name a person has decided before.

| Still read by a person | Why |
|---|---|
| A name with any mark the draft lists | The decision is about who writes a name, and |
| | a mark is about something else: a name that may say who lives there, a name that |
| | stands in two places, a point on the line between two areas |
| An area in which a heavier name lies, or the seed of another area | The mark is |
| | listed on the other name, and bears on this one |
| A name placed by an outline alone, or with no record inside | The rule does not fit |
| Another name, whatever writes it | The decision is about the name of an area |
| A name a person answered at the desk | What a person said of it stands |

**The border says that nobody read the name.** Nothing asks about a name that
stands, and every area is looked at in Borders under its name. So the border of
such an area says first that nobody has read its name, and what it stands on.

**A name still says how many publishers write it.** The rule takes away no
record. Every row of evidence stands, every area says who writes its name, and
what a page may say of a name is the publishers that write it.

With `read_every_name` the rule still lifts the flag, and every name is still
put to a person: nothing stands by the rule alone.

Nothing here reads a file, and nothing here knows a place.
"""

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.areas import draft_marks, draft_names, names_places
from burro_pipeline.areas.draft_names import Naming

# The decision, by the code the desk and the tables know it by, and where it is recorded.
CODE = "one_official_publisher"
RECORD = "0022"
DECIDED_ON = "2026-09-24"
SAYS = (
    "A name that an official publisher writes for a populated place, at a point inside the "
    "area, is a name. It needs no second publisher."
)
# How the decision is named where a line speaks of it.
NAMED = f"the founder's decision of {DECIDED_ON} that one official publisher is enough"
# The sources that are an official publisher's own list of populated places, each with a
# point. A source is added here when the registry approves one for the gazetteer.
OFFICIAL_PLACES = frozenset({names_places.SOURCE})
# What `areas.csv` says of an area whose name stands by the rule alone.
NAMED_BY_RULE = "named_by_rule"
# The marks of the naming that are listed on another name and bear on the area's own.
BEAR_ON_THE_AREA = frozenset({draft_names.HEAVIER_NAME_INSIDE, draft_names.SEED_LIES_ELSEWHERE})
# The seconds the design gives to a name at the desk, which nobody has timed.
SECONDS_A_NAME = 45.0
COLUMNS = (
    *("area_id", "name", "primary_borough", "publishers_writing", "source_id", "record_id"),
    *("as_written", "asked_at_the_desk", "why"),
)
# Why a name the rule fits is still put to a person.
HAS_A_MARK, WAS_DECIDED, EVERY_NAME = (
    "the draft has a mark on it",
    "a person answered it at the desk",
    "every name is read",
)


def fits(rows: Sequence[Mapping[str, str]]) -> Mapping[str, str] | None:
    """The record by which the rule fits a name, of the rows of evidence of the name as
    it is offered for one area. None where the rule does not fit it."""
    found = [
        row
        for row in rows
        if row["source_id"] in OFFICIAL_PLACES
        and row["locates"] == draft_names.POINT_INSIDE
        and row["letter_for_letter"] == "true"
    ]
    return min(found, key=lambda row: (row["source_id"], row["record_id"])) if found else None


@dataclass(frozen=True)
class Decided:
    """What the decision settles of one draft."""

    # The items of the desk's queue of names that the rule fits.
    fitted: frozenset[str]
    # The areas whose name stands by the rule alone: they are put to nobody.
    stands: frozenset[str]
    # Why each area the rule fits is still put to a person, by its id.
    asked: Mapping[str, str]
    # The record by which the rule fits the name of each area.
    by: Mapping[str, Mapping[str, str]]

    @property
    def left_out(self) -> frozenset[str]:
        """The items of the queue of names that the desk is not handed."""
        return frozenset(f"n:{area}" for area in self.stands)

    @property
    def hours(self) -> float:
        """The hours the names that stand would have taken, at the design's pace."""
        return len(self.stands) * SECONDS_A_NAME / 3600


NOTHING = Decided(frozenset(), frozenset(), {}, {})


def decide(
    naming: Naming,
    evidence: Sequence[Mapping[str, str]],
    looks: Sequence[Mapping[str, str]],
    *,
    answered: Collection[str] = (),
    read_every_name: bool = False,
) -> Decided:
    """What the decision settles: the names the rule fits, and the areas that stand by it.

    `evidence` holds the rows of `name_evidence.csv` and `looks` those of
    `names_to_look_at.csv`. `answered` holds the places a person has answered at the desk.
    """
    rows: dict[tuple[str, str], list[Mapping[str, str]]] = {}
    for row in evidence:
        rows.setdefault((row["area_id"], row["name"]), []).append(row)
    marked = {row["item"] for row in looks if row["item"]}
    marked |= {f"n:{row['area_id']}" for row in looks if row["mark"] in BEAR_ON_THE_AREA}
    fitted: set[str] = set()
    stands: set[str] = set()
    asked: dict[str, str] = {}
    by: dict[str, Mapping[str, str]] = {}
    for area in sorted(naming.first):
        for offered in naming.offered(area):
            if offered.kind == draft_names.WIDE:
                continue
            record = fits(rows.get((area, offered.as_offered), []))
            if record is None:
                continue
            if offered.role != draft_names.PRIMARY:
                fitted.add(f"a:{area}:{draft_marks.desk_slug(offered.as_offered)}")
                continue
            fitted.add(f"n:{area}")
            by[area] = record
            if f"n:{area}" in marked:
                asked[area] = HAS_A_MARK
            elif offered.name.place_id in answered or area in answered:
                asked[area] = WAS_DECIDED
            elif read_every_name:
                asked[area] = EVERY_NAME
            else:
                stands.add(area)
    return Decided(frozenset(fitted), frozenset(stands), asked, by)


def unread(decided: Decided, words: Mapping[str, str]) -> dict[str, tuple[str, str]]:
    """What the border of each area whose name stands says of the name, by area: the
    words, and the source of the record the name stands on. Nothing asks about such a
    name, and its border is looked at under it. `words` says each source as a person
    reads it."""
    return {
        area: (
            "Nobody has read the name of this area. It stands by the rule that one official "
            "publisher is enough: it is written for a populated place at a point inside the "
            f"area, by {words.get(decided.by[area]['source_id'], decided.by[area]['source_id'])}"
            ". If the name looks wrong, say so in a note: a name that stands is turned down "
            "by hand.",
            decided.by[area]["source_id"],
        )
        for area in sorted(decided.stands)
    }


def listed(
    decided: Decided, areas: Sequence[Mapping[str, str]], writing: Mapping[str, str]
) -> list[dict[str, str]]:
    """Every area the rule fits, for a person to skim: the name, who writes it, the
    record that puts it inside, and whether it is still put to a person.

    `areas` holds the rows of `areas.csv`, and `writing` the publishers that write the
    name of each area.
    """
    found: list[dict[str, str]] = []
    for row in areas:
        record = decided.by.get(row["area_id"])
        if record is None:
            continue
        found.append(
            {
                "area_id": row["area_id"],
                "name": row["name"],
                "primary_borough": row["primary_borough"],
                "publishers_writing": writing.get(row["area_id"], ""),
                "source_id": record["source_id"],
                "record_id": record["record_id"],
                "as_written": record["as_written"],
                "asked_at_the_desk": "false" if row["area_id"] in decided.stands else "true",
                "why": decided.asked.get(row["area_id"], ""),
            }
        )
    return sorted(found, key=lambda each: (each["asked_at_the_desk"], each["area_id"]))


def counts_of(decided: Decided, areas: int, one_publisher: Collection[str]) -> dict[str, object]:
    """What the decision settled, in numbers. `one_publisher` holds the areas whose name
    fewer than two publishers write."""
    only = set(one_publisher)
    named = set(decided.by)
    return {
        "decided_on": DECIDED_ON,
        "record": RECORD,
        "areas": areas,
        "areas_the_rule_fits": len(named),
        "areas_the_rule_does_not_fit": areas - len(named),
        "of_them_one_publisher_writes": len(named & only),
        "areas_named_by_the_rule_alone": len(decided.stands),
        "of_them_one_publisher_writes_the_name": len(decided.stands & only),
        "areas_the_rule_fits_that_are_still_asked_at_the_desk": len(decided.asked),
        "items_that_leave_the_queue_of_names": len(decided.left_out),
        "hours_they_would_have_taken": round(decided.hours, 1),
        "names_the_rule_fits": len(decided.fitted),
    }
