"""Rules that would save the founder's hours, and what each would settle. None is adopted.

A person reads every name before it ships, and looks at every flagged border.
Most names show records that agree and nothing in dispute. A rule could
settle those, and leave the person the names that need one. Whether to adopt
a rule is the founder's decision, and changes what the design promises. So
this adopts none. It counts what each rule would settle on the draft, and
lists the items, for the founder to skim before deciding.

| Rule | Settles |
|---|---|
| `two_publishers_write_it` | A name put forward as an area that Ordnance Survey writes at a |
| | point inside it and the town centres write letter for letter over it |
| `a_ward_of_its_name` | One that Ordnance Survey writes at a point inside, with a ward of |
| | its name over the area |
| `many_roads_name_it` | One that Ordnance Survey writes at a point inside, and that 50 road |
| | records or more give as their settlement |
| `a_smaller_place_by_its_own_point` | Another name that Ordnance Survey writes as a |
| | suburban area, a village or a hamlet, at a point inside the area it is offered for |
| `a_mark_that_asks_nothing` | Another name that the fourth rule would settle but for a |
| | mark that says only that a station of its name stands elsewhere, or that it was put |
| | under another area before the borders were drawn |
| `named_for_a_built_thing` | A name of the kind Other Settlement that no road, no ward and |
| | no town centre writes, and that holds a word for a street or a building |
| `a_label_of_two_names` | A name only a town centre holds, whose label is two names or |
| | holds a part in brackets |
| `a_few_cells_across_a_borough_line` | A border flagged only for lying in two boroughs, |
| | with under 5 output areas and under a tenth of them outside its main borough |

A rule settles only what no rule before it settles, so the counts add up. A
name with any mark to settle is left to the person, but for the marks the
fifth rule names. So is the name of an area in which a heavier name lies, or
the seed of another area: the mark is listed on the other name, and bears on
this one. Nothing here reads a file: it is handed the draft.

**A rule that leans on another.** The fifth rule lets a name through to the rule
its records fit. It has no test of its own for whether the records agree. So it
settles a name only where that other rule is adopted too, and every item under
it says which rule that is. The desk holds it to that: the founder who adopts
the fifth rule and not the fourth has let no name through on its point alone.

**What the founder has decided already.** On 2026-09-24 the founder decided
that one official publisher is enough for a name: `draft_decided.py` holds the
rule, and decision record 0022 the reasons. The first three rules here each
ask that Ordnance Survey write the name at a point inside the area, and then
ask for more. So the decision fits every name they fit. A name that stands by
the decision is no item of the desk, and no rule settles it: it is counted
under the rule that would have, as already decided, so that the founder is not
asked twice. Every rule says on its own screen what the decision has settled of
it. The eight rules stay the founder's to adopt, each at the desk.

The fifth rule leant on the first three while they settled names. A mark on the
name of an area is a doubt the decision did not settle, so such a name is read
by a person. The fifth rule now lets through another name alone, and leans on
the fourth.

What is written names places, so it goes where the draft goes. `RULES` holds
each rule in words, with what could go wrong, and names no place.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.areas import (
    draft_decided,
    draft_lines,
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
    TWO_BOROUGHS,
    Draft,
    Flag,
    main_borough,
)
from burro_pipeline.areas.names_candidates import WORD, parts
from burro_pipeline.areas.names_draft import Drafted
from burro_pipeline.areas.names_look import Mark
from burro_pipeline.areas.seeds import Put, Seed

NAMES = "names"
# The queue of the desk that holds the rules, and the line of a rule's item that names
# the table of what it would settle.
OF_RULES, EVERY_ITEM = "rules", "Every item"
COLUMNS = (
    *("rule", "queue", "would_settle", "hours", "says", "what_could_go_wrong", "leans_on"),
    *("already_decided", "what_the_decision_settled"),
)
# The line of a rule's item that says what the founder has decided already.
ALREADY_DECIDED = "Already decided"
ITEM_COLUMNS = ("rule", "queue", "item", "name", "would_be", "leans_on")
# The design's pace, which nobody has timed: 45 seconds a name, 8 minutes a border.
SECONDS: Mapping[str, float] = {NAMES: 45.0, BORDERS: 480.0}
# What a rule would make of an item.
ACCEPTED, NOT_KEPT, NOT_FLAGGED = "accepted as proposed", "not kept", "not offered as flagged"
# The same as the review desk reads it: the answer the draft proposes for the item, the
# answer of the desk that keeps no name, or none of the desk's answers, where a border
# is left as drafted and is no longer offered.
GIVES: Mapping[str, str] = {ACCEPTED: "proposed", NOT_KEPT: "drop", NOT_FLAGGED: ""}
DESK_COLUMNS = ("rule", "queue", "gives", "says", "goes_wrong", "leans_on")
DESK_ITEM_COLUMNS = ("rule", "queue", "item", "leans_on")
ROADS_NEEDED = 50
SMALLER_PLACES = frozenset({"Suburban Area", "Village", "Hamlet"})
OTHER_SETTLEMENT = "Other Settlement"
BUILT = frozenset(
    {"wharf", "square", "mews", "quay", "close", "parade", "yard", "estate", "terrace", "place"}
)
# The marks that the fifth rule says ask nothing of a person.
ASKS_NOTHING = frozenset({Mark.ALSO_A_STATION.value, draft_names.WAS_PUT_UNDER_ANOTHER})
FEW_CELLS, SMALL_SHARE = 5, 0.1


@dataclass(frozen=True)
class Rule:
    """One rule put to the founder: what it says, and what could go wrong."""

    code: str
    queue: str
    says: str
    goes_wrong: str
    would_be: str = ACCEPTED
    # The rules this one leans on, by code. It settles an item only where the one of
    # them that the item names is adopted too.
    leans_on: tuple[str, ...] = ()
    # What the founder's decision on one official publisher says of the rule, in words.
    decided: str = ""


# The rules by which the records of a name agree, in the order they are tried.
AGREE = (
    "two_publishers_write_it",
    "a_ward_of_its_name",
    "many_roads_name_it",
    "a_smaller_place_by_its_own_point",
)
# The rule by which the records of another name agree. It is the one rule that a mark
# which asks nothing lets a name through to: the name of an area with a mark is read.
OF_ANOTHER_NAME = AGREE[-1]
# What the decision says of a rule that asks more than the decision does.
ASKS_MORE = (
    "This rule fits only a name that Ordnance Survey writes for a populated place at a "
    "point inside the area, with no mark on it. The decision names every such name, "
    "whatever else writes it."
)


def in_words(code: str) -> str:
    """A rule as the desk names it on its screen."""
    return code.replace("_", " ").capitalize()


RULES: tuple[Rule, ...] = (
    Rule(
        "two_publishers_write_it",
        NAMES,
        "A name put forward as an area is accepted when Ordnance Survey writes it for a "
        "populated place at a point inside the area, the Greater London Authority writes the "
        "same name letter for letter for a town centre whose outline overlaps the area, and "
        "the draft has put no mark on it.",
        "The outlines of the town centre file are based on "
        "Ordnance Survey mapping, so the two publishers may not be independent. A town "
        "centre's name is the name of a shopping street: the area grown round it may be "
        "wider than what people call by that name. Where every name is put to a person, a "
        "yes takes a list to skim in place of a screen for each.",
        decided=ASKS_MORE,
    ),
    Rule(
        "a_ward_of_its_name",
        NAMES,
        "A name put forward as an area is accepted when Ordnance Survey writes it at a point "
        "inside the area, a ward of that name overlaps the area, and the draft has put no "
        "mark on it.",
        "Both records are published by Ordnance Survey. The founder has decided that one "
        "official publisher is enough, so that stands against the rule no longer. A ward's "
        "name is chosen at an electoral review and may have been coined for the ward, or "
        "taken from the same map.",
        decided=f"{ASKS_MORE} It was the one rule that said it waited on the decision.",
    ),
    Rule(
        "many_roads_name_it",
        NAMES,
        "A name put forward as an area is accepted when Ordnance Survey writes it at a point "
        f"inside the area, {ROADS_NEEDED} or more road records give it as their settlement, "
        "and the draft has put no mark on it.",
        "A name that many roads give is a post town, and may cover more ground than one "
        "area. The draft treats a name as wide only where it is a city with a large box.",
        decided=ASKS_MORE,
    ),
    Rule(
        "a_smaller_place_by_its_own_point",
        NAMES,
        "Another name is accepted as a smaller place inside the area its own point lies in, "
        "when Ordnance Survey writes it as a Suburban Area, Village or Hamlet at a point "
        "inside, and the draft has put no mark on it.",
        "Another name has no border and is not ranked, so a wrong one costs little. But it "
        "is tied to its area by id when it is decided. If the border moves later, the name "
        "stays with the old area unless the build places it again from its point.",
        decided="The decision is about the name of an area, and this rule is about another "
        "name. So it settles no name of this rule. It settles what stood against each: that "
        "one publisher writes a name this rule fits is no flag on it.",
    ),
    Rule(
        "a_mark_that_asks_nothing",
        NAMES,
        "A mark that says only that a station of the same name stands over 1 km away, or "
        "that the name was put under another area before the borders were drawn, does not "
        "hold another name back from the rule its records fit: "
        f"{in_words(OF_ANOTHER_NAME)}. This rule settles a name only where that rule is "
        "adopted too. It settles no name put forward as an area.",
        "A station of the name 1 km off may mean that the record stands in the wrong place. "
        "This rule would let the name through with nothing said of it.",
        leans_on=(OF_ANOTHER_NAME,),
        decided="The decision says nothing of a mark, so it settles no name of this rule. "
        "This rule once let through the name of an area too, by leaning on the three rules "
        "that the decision has overtaken. A mark on the name of an area is a doubt the "
        "decision did not settle, so such a name is now read by a person.",
    ),
    Rule(
        "named_for_a_built_thing",
        NAMES,
        "A name that Ordnance Survey writes as Other Settlement, that no road record gives "
        "as its settlement, that no ward and no town centre writes, and that holds a word "
        "for a street or a building (" + ", ".join(sorted(BUILT)) + ") is never an area, and "
        "as another name it is not kept.",
        "The list of words is blunt. A new district that people do call by its "
        "development's name would be lost as a name to search by. Where such a name is an "
        "area today, the draft is made again without it and its neighbours' borders move.",
        NOT_KEPT,
        decided="The decision keeps no name that this rule would turn down. Each holds a "
        "word for a street or a building, which the draft marks, and a name with a mark is "
        "still put to a person.",
    ),
    Rule(
        "a_label_of_two_names",
        NAMES,
        "A town centre's label that holds two names, or a part in brackets, is not kept as a "
        "name. Each name it holds is kept only where a record writes that name alone.",
        "An area whose only name is such a label would be left with no name, until the draft "
        "offers the parts of the label, which it does not do today.",
        NOT_KEPT,
        decided="The decision fits no name of this rule: a town centre alone writes each, "
        "as an outline and not for a populated place.",
    ),
    Rule(
        "a_few_cells_across_a_borough_line",
        BORDERS,
        "An area flagged only because it lies in two boroughs, with under "
        f"{FEW_CELLS} output areas and under a tenth of its output areas outside its main "
        "borough, is not offered as a flagged border.",
        "One to four output areas stay in an area of another borough, checked by nobody. "
        "The area's page would name two boroughs on the strength of them, and council tax "
        "and school admissions follow the borough. Giving them to the neighbour by rule "
        "instead would split any place that truly lies across the line.",
        NOT_FLAGGED,
        decided="The decision is about names. It settles no border, and every border is "
        "offered as before: that of an area whose name stands by the decision too.",
    ),
)


BY_CODE: Mapping[str, Rule] = {rule.code: rule for rule in RULES}


@dataclass(frozen=True)
class Settled:
    """One item that one rule would settle."""

    rule: str
    queue: str
    item: str
    name: str
    would_be: str
    # The rule the item leans on, where its own rule leans on others.
    leans_on: str = ""
    # Whether the founder's decision on one official publisher has settled it already.
    # It is then no item of the desk, and the rule settles nothing of it.
    already: bool = False

    def row(self) -> dict[str, str]:
        return {
            "rule": self.rule,
            "queue": self.queue,
            "item": self.item,
            "name": self.name,
            "would_be": self.would_be,
            "leans_on": self.leans_on,
        }


def _a_point_inside(rows: Sequence[Mapping[str, str]]) -> bool:
    return any(
        row["source_id"] == names_places.SOURCE
        and row["locates"] == draft_names.POINT_INSIDE
        and row["letter_for_letter"] == "true"
        for row in rows
    )


def _over_it(rows: Sequence[Mapping[str, str]], source: str, *, exactly: bool) -> bool:
    return any(
        row["source_id"] == source
        and row["locates"] == draft_names.POLYGON_OVERLAP
        and (row["letter_for_letter"] == "true" if exactly else row["match"] == "same")
        for row in rows
    )


def _of_two_names(seed: Seed) -> bool:
    """Whether a name is one that only a town centre holds, in a label of several names."""
    alone = seed.place.record is None and seed.put is Put.CENTRE
    return alone and (bool(parts(seed.name)) or "(" in seed.name)


def _built(seed: Seed, rows: Sequence[Mapping[str, str]]) -> bool:
    return (
        seed.place.key.kind == OTHER_SETTLEMENT
        and seed.place.roads == 0
        and {row["source_id"] for row in rows} <= {names_places.SOURCE}
        and not seed.weight.ward
        and bool(set(WORD.findall(seed.name.casefold())) & BUILT)
    )


def _agrees(offered: Offered, seed: Seed, held: Sequence[Mapping[str, str]]) -> Rule | None:
    """The first of the rules by which the records of a name agree. None where none does."""
    if not _a_point_inside(held):
        return None
    if offered.role != draft_names.PRIMARY:
        smaller = offered.kind == draft_names.INSIDE and seed.place.key.kind in SMALLER_PLACES
        return BY_CODE["a_smaller_place_by_its_own_point"] if smaller else None
    if _over_it(held, names_centres.SOURCE, exactly=True):
        return BY_CODE["two_publishers_write_it"]
    if _over_it(held, names_wards.SOURCE, exactly=False):
        return BY_CODE["a_ward_of_its_name"]
    if seed.place.roads >= ROADS_NEEDED:
        return BY_CODE["many_roads_name_it"]
    return None


def rule_for(agrees: Rule | None, marked: set[str]) -> tuple[Rule | None, str]:
    """The rule that would settle a name whose records agree, and the rule it leans on.

    `agrees` is the rule by which the records agree, and `marked` every mark on the
    name. With no mark the rule settles it. Another name with only marks that ask
    nothing is settled by the rule that says so, which leans on the rule by which the
    records agree. With any other mark the name is left to the person, and so is the
    name of an area with any mark at all.
    """
    if agrees is None or not marked <= ASKS_NOTHING:
        return None, ""
    if not marked:
        return agrees, ""
    if agrees.code != OF_ANOTHER_NAME:
        return None, ""
    return BY_CODE["a_mark_that_asks_nothing"], agrees.code


def of_names(
    rows: Mapping[str, Sequence[Mapping[str, str]]],
    drafted: Drafted,
    naming: Naming,
    decided: Decided = draft_decided.NOTHING,
) -> list[Settled]:
    """What each rule about a name would settle, each item under the first rule that does.

    `decided` is what the founder's decision on one official publisher settles. A name
    that stands by it is listed under the rule that would have settled it, as already
    decided: no rule settles it, and the desk makes no item of it.
    """
    evidence: dict[tuple[str, str], list[Mapping[str, str]]] = {}
    for row in rows["name_evidence.csv"]:
        evidence.setdefault((row["area_id"], row["name"]), []).append(row)
    marks: dict[str, set[str]] = {}
    for row in rows["names_to_look_at.csv"]:
        marks.setdefault(row["item"], set()).add(row["mark"])
        if row["mark"] in draft_decided.BEAR_ON_THE_AREA:
            # It is listed on another name, and says that the area may be better named
            # for that one. So no rule settles the area's own name.
            marks.setdefault(f"n:{row['area_id']}", set()).add(row["mark"])
    seeds = {drafted.area_ids[seed.key]: seed for seed in drafted.seeds.seeds}
    wide: dict[str, list[str]] = {}
    for area in sorted(naming.first):
        for offered in naming.offered(area):
            if offered.kind == draft_names.WIDE:
                wide.setdefault(offered.name.place_id, []).append(area)
    found: dict[str, Settled] = {}
    for area in sorted(naming.first):
        for offered in naming.offered(area):
            item = draft_lines.item_of(offered, wide)
            seed = seeds[offered.name.place_id]
            if item in found or offered.why == draft_names.SECOND_NAME:
                continue
            held = evidence.get((area, offered.as_offered), [])
            rule, leans_on = rule_for(_agrees(offered, seed, held), marks.get(item, set()))
            if _built(seed, held):
                rule, leans_on = BY_CODE["named_for_a_built_thing"], ""
            elif _of_two_names(seed):
                rule, leans_on = BY_CODE["a_label_of_two_names"], ""
            if rule is not None:
                found[item] = Settled(
                    rule.code,
                    NAMES,
                    item,
                    offered.as_offered,
                    rule.would_be,
                    leans_on,
                    already=item in decided.left_out,
                )
    order = {rule.code: at for at, rule in enumerate(RULES)}
    return sorted(found.values(), key=lambda each: (order[each.rule], each.item))


def of_borders(draft: Draft, flags: Sequence[Flag]) -> list[Settled]:
    """The borders the eighth rule would no longer offer as flagged.

    Every flag about the border counts: the desk shows each of them.
    """
    raised: dict[str, set[str]] = {}
    for flag in flags:
        if flag.queue == BORDERS and flag.code not in ABOUT_THE_NAME:
            raised.setdefault(flag.area, set()).add(flag.code)
    found: list[Settled] = []
    rule = BY_CODE["a_few_cells_across_a_borough_line"]
    for area, codes in sorted(raised.items()):
        if codes != {TWO_BOROUGHS}:
            continue
        cells = draft.cells_of[area]
        main = main_borough(draft, area)
        outside = [oa for oa in cells if draft.cells[oa].borough != main]
        if len(outside) < FEW_CELLS and len(outside) < SMALL_SHARE * len(cells):
            name = draft.areas[area].name
            found.append(Settled(rule.code, BORDERS, area, name, rule.would_be))
    return found


def to_decide(drafted: Drafted) -> dict[str, int]:
    """What each decision the founder is asked for turns on, counted over the names that
    are put forward as areas, before any is taken in for being too small.

    Each is a question of the design, and none is answered here. The counts
    say how much of the draft hangs on the answer.
    """
    areas = drafted.seeds.areas
    asked = drafted.seeds.points
    of_areas = {seed.key for seed in areas}
    marked: dict[Mark, set[tuple[str, str, str]]] = {}
    smallest_box: set[tuple[str, str, str]] = set()
    for look in drafted.looks:
        if look.key in of_areas:
            marked.setdefault(look.mark, set()).add(look.key)
            if look.mark is Mark.MAY_BE_A_BUILT_THING and look.why.startswith("Its box"):
                smallest_box.add(look.key)
    by_another = [
        seed for seed in areas if seed.weight.centre and not draft_lines.centre_is_its_own(seed)
    ]
    return {
        "names_put_forward_as_areas": len(areas),
        "of_them_one_publisher_writes": sum(seed.one_publisher for seed in areas),
        "of_them_with_points_from_a_town_centre_of_another_name": len(by_another),
        "of_them_reaching_the_points_asked_only_through_such_a_centre": sum(
            seed.weight.total - seed.weight.centre < asked for seed in by_another
        ),
        "of_them_known_by_a_record_in_the_smallest_box": len(smallest_box),
        "of_them_holding_a_word_for_a_built_thing_in_a_larger_box": len(
            marked.get(Mark.MAY_BE_A_BUILT_THING, set()) - smallest_box
        ),
        "of_them_with_a_seed_moved_to_a_label_that_only_holds_the_name": len(
            marked.get(Mark.SEED_ON_A_LABEL_THAT_HOLDS_IT, set())
        ),
        "of_them_resting_on_a_file_with_no_receipt": len(marked.get(Mark.NO_RECEIPT, set())),
    }


def for_the_desk(settled: Sequence[Settled]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Every rule, and every item each would settle, as the review desk reads them.

    The desk puts each rule to the founder, with what could go wrong beside it and
    some of the items drawn at random. Nothing is settled until the founder says yes.
    """
    rules = [
        {
            "rule": rule.code,
            "queue": rule.queue,
            "gives": GIVES[rule.would_be],
            "says": rule.says,
            "goes_wrong": rule.goes_wrong,
            "leans_on": " ".join(rule.leans_on),
        }
        for rule in RULES
    ]
    items = [
        {"rule": each.rule, "queue": each.queue, "item": each.item, "leans_on": each.leans_on}
        for each in left(settled)
    ]
    return rules, items


def left(settled: Sequence[Settled]) -> list[Settled]:
    """What is left for the rules to settle: every item the founder has not decided already."""
    return [each for each in settled if not each.already]


def _counted(settled: Sequence[Settled], *, already: bool) -> dict[str, int]:
    counted: dict[str, int] = {}
    for each in settled:
        if each.already == already:
            counted[each.rule] = counted.get(each.rule, 0) + 1
    return counted


def already_decided(rule: Rule, fitted: int, already: int, stands: int) -> str:
    """What the founder's decision on one official publisher has settled of one rule, in
    words for the rule's own screen, so that the founder is not asked twice.

    `fitted` is how many items the rule fits, `already` how many of them stand by the
    decision, and `stands` how many names stand by it in all.
    """
    said = [f"By {draft_decided.NAMED}, decision record {draft_decided.RECORD}.", rule.decided]
    if rule.queue != NAMES or not stands:
        return " ".join(said)
    if already == 0:
        said.append(f"None of the {stands} names that stand by the decision is of this rule.")
        return " ".join(said)
    names = "name" if fitted == 1 else "names"
    stand = "stands" if already == 1 else "stand"
    said.append(
        f"Of the {fitted} {names} this rule fits, {already} {stand} by the decision and "
        f"{'is' if already == 1 else 'are'} not asked about."
    )
    if fitted == already:
        said.append(
            "Nothing is left for this rule to settle. Either answer takes it off the queue, "
            "and changes nothing."
        )
    else:
        said.append(f"{fitted - already} are left for this rule to settle.")
    return " ".join(said)


def lines_for_the_desk(
    listed_in: str,
    settled: Sequence[Settled] = (),
    decided: Decided = draft_decided.NOTHING,
    stand_in: str = "",
) -> list[draft_lines.Line]:
    """What the desk says on the item of every rule beside the rule itself: what the
    founder has decided already, and where every item the rule would settle is listed.
    The desk shows ten of them, drawn at random.

    `stand_in` names the file that lists every name that stands by the decision.
    """
    open_, already = _counted(settled, already=False), _counted(settled, already=True)
    found: list[draft_lines.Line] = []
    for rule in RULES:
        fitted = open_.get(rule.code, 0) + already.get(rule.code, 0)
        said = already_decided(rule, fitted, already.get(rule.code, 0), len(decided.stands))
        if already.get(rule.code) and stand_in:
            said += (
                f" Each is listed in the file {stand_in} of the folder the draft was written to."
            )
        found.append(draft_lines.Line(OF_RULES, rule.code, ALREADY_DECIDED, said))
        found.append(
            draft_lines.Line(
                OF_RULES,
                rule.code,
                EVERY_ITEM,
                "The draft lists every item this rule would settle, by name, in the file "
                f"{listed_in} of the folder the draft was written to.",
            )
        )
    return found


def put_to_the_founder(
    settled: Sequence[Settled], decided: Decided = draft_decided.NOTHING
) -> list[dict[str, str]]:
    """Every rule in words, with how many items it would settle and the hours those are,
    and what the founder's decision on one official publisher has settled of it already."""
    counted, already = _counted(settled, already=False), _counted(settled, already=True)
    return [
        {
            "rule": rule.code,
            "queue": rule.queue,
            "would_settle": str(counted.get(rule.code, 0)),
            "hours": f"{counted.get(rule.code, 0) * SECONDS[rule.queue] / 3600:.1f}",
            "says": rule.says,
            "what_could_go_wrong": rule.goes_wrong,
            "leans_on": " ".join(rule.leans_on),
            "already_decided": str(already.get(rule.code, 0)),
            "what_the_decision_settled": already_decided(
                rule,
                counted.get(rule.code, 0) + already.get(rule.code, 0),
                already.get(rule.code, 0),
                len(decided.stands),
            ),
        }
        for rule in RULES
    ]
