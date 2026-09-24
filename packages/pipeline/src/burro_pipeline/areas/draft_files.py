"""The curated files of a draft, made from the draft of names and the draft of areas.

Section 5 of the areas design names the files that are the source of truth.
This writes them as a draft: what a method made and nobody has checked. A
person's decisions at the review desk turn them into the gazetteer.

| File | One row is | How a row says it is a draft |
|---|---|---|
| `areas.csv` | An area that stands | `review_state` is `drafted`, or `named_by_rule` |
| `oa_to_area.csv` | An output area | `basis` is `auto`, and nobody is in `decided_by` |
| `aliases.csv` | A name offered beside an area's first | The last column |
| `name_evidence.csv` | One record that writes one name | Nobody is in `chosen_by` |
| `relations.csv` | Two areas that a name ties together | The last column |
| `snapshots.json` | A publisher's file that was read | The member `state` |

Every table has one column more than the design gives it, the last: `state`,
which holds the same words in every row. A row cut out of its file still says
what it is. The review desk refuses a column it does not know, so
`for_the_desk` writes the same rows without it.

Three tables say a little more, in columns that stand before `state`:

| File | Column | Says |
|---|---|---|
| `areas.csv`, `aliases.csv` | `no_receipt` | Whether the name, its points or its seed rest |
| | | on a file that has no receipt |
| `areas.csv` | `boroughs` | Every borough the area lies in, with its output areas in each |
| | `borough_is_a_tie` | Whether two boroughs hold as many of its output areas as each |
| | | other. The main borough is then the one whose code sorts first |
| | `publishers_writing` | Every publisher that writes the name, wherever its record lies |
| `name_evidence.csv` | `match` | How the label writes the name: `same`, or `part` for a |
| | | label of several names. `same` takes no account of the |
| | | publisher's own word for the kind of thing it lists |
| | `letter_for_letter` | Whether the label is the name, letter for letter |
| | `share` | The share of the record that lies in the area |
| | `metres_outside` | How far the record lies from the area, where it lies outside |

**What the desk may offer as a spelling.** The desk offers every form that a
row of evidence writes, for a person to choose as the name. Section 6 of the
design gives the order of spelling: as OS Open Names writes it, else as the
town centres do. A ward is not in it, and a ward's label ends with the
publisher's word for a ward. So the desk is handed no row of a ward. The
curated file keeps every row, and the flags and the layers read that.

**A name that stands by the rule.** The founder decided that one official
publisher is enough for a name: `draft_decided.py` holds the rule. The name of
an area that the rule fits, and that the draft has no mark on, is put to nobody.
Its row of `areas.csv` says `named_by_rule`, which no person's reading has made
it: `name_checked` is what a person's answer makes a name. The desk is handed
the row, and makes no item of it.

Four files more are for a person's eyes, and are no part of the design:

| File | Holds |
|---|---|
| `named_by_the_rule.csv` | Every area whose name the rule fits, with who writes it and |
| | the record that puts it inside. Those that stand by the rule alone come first |
| `area_names.csv` | Every name offered for every area, with who writes it. For an area |
| | whose own name lies outside it, the names nearest to it |
| `names_to_look_at.csv` | Every mark a person should settle, the gravest first, with why |
| | in words and the item of the review desk it is on. `draft_marks.py` makes it |
| `seeds.csv`, `listed.csv` | Where each area's seed stands, and what the method could not mend |
| `largest_areas.csv` | The ten areas that hold most output areas, with the other names that |
| | lie in each. An area is large where the files hold no other name, and the desk cannot |
| | make it smaller: it can move a cell, and cannot make an area of another name |

**The borough of an area** is the borough that holds most of its output areas.
The design asks for the borough with most of its homes, and the licence gate
does not give homes for this use.

**A slug** is the name in lower case with hyphens. Two areas of one name have
the borough added. An area with no name has no slug.

What is written is made from publishers' files. It goes to a folder that git
does not track. Nothing here reads a clock.
"""

import csv
import io
import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass

from burro_pipeline.areas import (
    assign_write,
    draft_decided,
    draft_marks,
    draft_names,
    names_draft,
    names_places,
    names_wards,
)
from burro_pipeline.areas.assign import Draft
from burro_pipeline.areas.assign_files import Ground
from burro_pipeline.areas.draft_decided import Decided
from burro_pipeline.areas.draft_names import Located, Name, Naming, Offered, Record
from burro_pipeline.areas.names_candidates import OUTLINE, POINT, Candidate, Match, Written
from burro_pipeline.areas.names_draft import Drafted, table
from burro_pipeline.areas.names_evidence import DESIGN
from burro_pipeline.areas.names_files import File
from burro_pipeline.cells.spine import slug_of
from burro_pipeline.evidence.receipt import Receipt

STATE = "draft, made by method, checked by nobody"
STATE_COLUMN = "state"
DRAFTED = "drafted"

AREAS, GIVEN, ALIASES = "areas.csv", "oa_to_area.csv", "aliases.csv"
EVIDENCE, RELATIONS, SNAPSHOTS = "name_evidence.csv", "relations.csv", "snapshots.json"
AREA_NAMES, TO_LOOK_AT, SEEDS, LISTED = (
    "area_names.csv",
    "names_to_look_at.csv",
    "seeds.csv",
    "listed.csv",
)
LARGEST = "largest_areas.csv"
# Every area whose name the rule on one official publisher fits, for a person to skim.
NAMED_BY_THE_RULE = "named_by_the_rule.csv"
LARGEST_COLUMNS = (
    *("rank", "area_id", "name", "primary_borough", "output_areas", "hectares"),
    *("times_the_median", "other_names_inside", "places_inside"),
)
# How many of the largest areas are listed for the founder.
LARGEST_LISTED = 10
FLAGS = "flags_names.csv"
COLUMNS: Mapping[str, tuple[str, ...]] = {
    AREAS: (
        *("area_id", "slug", "name", "primary_borough"),
        *("seed_record", "review_state", "superseded_by"),
    ),
    GIVEN: ("oa21cd", "area_id", "basis", "evidence", "decided_by", "decided_on", "reason"),
    ALIASES: ("alias", "area_id", "kind", "source_id", "record_id"),
    EVIDENCE: DESIGN,
    RELATIONS: ("area_id", "other_area_id", "kind", "source_id", "record_id"),
}
# The tables of the design, which the review desk reads.
OF_THE_DESIGN = (AREAS, GIVEN, ALIASES, EVIDENCE, RELATIONS)
# What a curated file says beside the columns of the design, before it says its state.
NO_RECEIPT = "no_receipt"
MATCH, LETTER_FOR_LETTER, SHARE, METRES_OUTSIDE = (
    "match",
    "letter_for_letter",
    "share",
    "metres_outside",
)
BOROUGHS, TIE = "boroughs", "borough_is_a_tie"
WRITING = "publishers_writing"
MORE: Mapping[str, tuple[str, ...]] = {
    AREAS: (NO_RECEIPT, BOROUGHS, TIE, WRITING),
    ALIASES: (NO_RECEIPT,),
    EVIDENCE: (MATCH, LETTER_FOR_LETTER, SHARE, METRES_OUTSIDE),
}
NAMES_COLUMNS = (
    *("area_id", "offered", "name", "kind", "why", "proposed_as", "points"),
    *("publishers_writing", "locates", "source_id", "record_id", "place_id"),
    *("lies_in", "metres", "primary_borough", "marks"),
)
LOOK_COLUMNS = draft_marks.COLUMNS
SEED_COLUMNS = ("area_id", "seed_id", "name", "easting", "northing", "weight", "no_receipt")
FIRST, OTHER, NEAREST = "first", "other", "nearest"
# The kinds of `relations.csv`.
SAME_NAME, NAME_LIES_OVER, GROWN_FROM_A_NAME_IN = (
    "same_name",
    "name_lies_over",
    "grown_from_a_name_in",
)
# How many of the nearest names are offered beside an area whose own name lies outside it.
NEAREST_OFFERED = 3
# The sources whose label is no spelling of a name: section 6 of the design gives the
# order of spelling, and a ward is not in it.
NO_SPELLING_FROM = frozenset({names_wards.SOURCE})
# How well a record places a name, the best first.
BEST = (draft_names.POINT_INSIDE, draft_names.POLYGON_OVERLAP, draft_names.LABEL_ONLY)

Shares = Callable[[Candidate], Mapping[str, float]]
# The output areas a point lies in or on the edge of.
Holding = Callable[[tuple[float, float]], Sequence[str]]
Nearest = Callable[[str], Sequence[tuple[float, str]]]
# How far a record lies from an area, in metres: the source, the record, the area.
Outside = Callable[[str, str, str], float]


# From the two drafts to plain values


def _record(written: Written, shares: Shares, holding: Holding | None = None) -> Record:
    candidate = written.candidate
    if candidate.gives == POINT:
        # A point on the line between output areas lies on each of them, in equal parts.
        cells = sorted(holding(candidate.at)) if holding is not None else []
        lies_on = dict.fromkeys(cells or [candidate.cell], 1 / max(1, len(cells)))
    else:
        lies_on = dict(shares(candidate))
    return Record(
        source_id=candidate.source_id,
        record_id=candidate.record_id,
        publisher=candidate.publisher,
        field=candidate.field,
        as_written=candidate.as_written,
        gives=POINT if candidate.gives == POINT else OUTLINE,
        match=written.match.value,
        writes=written.writes,
        lies_on=lies_on,
    )


def names_of(drafted: Drafted, shares: Shares, holding: Holding | None = None) -> list[Name]:
    """Every place of the draft of names, as the naming takes one.

    `holding` gives the output areas a point lies in or on the edge of. Without
    it a point lies in the one output area the draft of names gave it to.
    """
    found: list[Name] = []
    for seed in drafted.seeds.seeds:
        place = seed.place
        own = Written(place.key, Match.SAME, 0.0)
        second = place.record.second_name if place.record is not None else ""
        found.append(
            Name(
                place_id=drafted.area_ids[seed.key],
                name=seed.name,
                proposed=seed.tier.value,
                points=seed.weight.total,
                records=tuple(_record(each, shares, holding) for each in (own, *place.others)),
                of=tuple(drafted.area_ids[key] for key in seed.of),
                second_name=second,
                second_field=names_places.SECOND_NAME if second else "",
            )
        )
    return sorted(found, key=lambda name: name.place_id)


def stands_as(found: Draft) -> dict[str, str]:
    """The area every seed stands as at the end: its own, or the one it became part of."""
    held = {area: area for area in found.drawn}
    return held | {each.seed: each.into for each in found.absorbed}


def area_of(found: Draft) -> dict[str, str]:
    return {oa: given.area for oa, given in sorted(found.given.items())}


# The curated files


@dataclass(frozen=True)
class Curated:
    """Every row of the curated files, and of the files for a person's eyes."""

    rows: Mapping[str, tuple[Mapping[str, str], ...]]
    # `oa_to_area.csv` as the draft of the areas writes it.
    given: bytes
    snapshots: tuple[Mapping[str, object], ...]
    counts: Mapping[str, object]
    # What the decision on one official publisher settles of the draft.
    decided: Decided = draft_decided.NOTHING


def slugs_of(names: Mapping[str, str], boroughs: Mapping[str, str]) -> dict[str, str]:
    """A slug for every area that has a name, and no slug twice."""
    wanted: dict[str, list[str]] = {}
    for area in sorted(names):
        if slug_of(names[area]):
            wanted.setdefault(slug_of(names[area]), []).append(area)
    found: dict[str, str] = {}
    taken: set[str] = set()
    for plain, same in sorted(wanted.items()):
        for area in same:
            longer = slug_of(f"{names[area]} {boroughs.get(area, '')}")
            slug, number = (plain if len(same) == 1 else longer), 1
            while slug in taken:
                number += 1
                slug = f"{longer}-{number}"
            taken.add(slug)
            found[area] = slug
    return found


def _best(records: Iterable[Located]) -> Located | None:
    """The record that places a name best in an area, of those that write the name."""
    writing = [each for each in records if each.record.writes]
    return min(writing, key=lambda each: BEST.index(each.locates)) if writing else None


def _file_of(drafted: Drafted, source_id: str) -> File:
    return drafted.files[source_id]


def _truth(value: bool) -> str:
    return "true" if value else "false"


def is_a_tie(boroughs: Mapping[str, int]) -> bool:
    """Whether two boroughs hold as many of an area's output areas as each other, and most."""
    most = sorted(boroughs.values(), reverse=True)[:2]
    return len(most) == 2 and most[0] == most[1]


def _evidence(
    drafted: Drafted, offered: Offered, outside: Outside | None = None
) -> list[dict[str, str]]:
    """The rows of evidence of one name offered for one area: every record that writes it."""
    found: list[dict[str, str]] = []
    for each in offered.records:
        if not each.record.writes:
            continue
        file = _file_of(drafted, each.record.source_id)
        lies_outside = each.locates == draft_names.LABEL_ONLY and outside is not None
        metres = (
            outside(each.record.source_id, each.record.record_id, offered.area_id)
            if lies_outside and outside is not None
            else None
        )
        found.append(
            {
                MATCH: each.record.match,
                LETTER_FOR_LETTER: _truth(each.record.as_written == offered.as_offered),
                SHARE: f"{each.share:.2f}",
                METRES_OUTSIDE: "" if metres is None else f"{metres:.0f}",
            }
            | {
                "area_id": offered.area_id,
                "name": offered.as_offered,
                "role": offered.role,
                "source_id": each.record.source_id,
                "record_id": each.record.record_id,
                "as_written": each.record.as_written,
                "field": each.record.field,
                "locates": each.locates,
                "data_date": file.data_date,
                "retrieved_on": file.retrieved_on,
                "snapshot_sha256": file.sha256,
                "checked": "true",
                "chosen_by": "",
                "chosen_on": "",
            }
        )
    return found


def writing(offered: Offered | None) -> str:
    """Every publisher that writes a name as it is offered, wherever its record lies."""
    records = () if offered is None else offered.records
    return ";".join(sorted({each.record.publisher for each in records if each.record.writes}))


def _offered_row(
    offered: Offered, which: str, borough: str, marks: Sequence[str]
) -> dict[str, str]:
    best = _best(offered.records)
    second = offered.why == draft_names.SECOND_NAME
    return {
        "area_id": offered.area_id,
        "offered": which,
        "name": offered.as_offered,
        "kind": offered.kind,
        "why": offered.why,
        "proposed_as": offered.name.proposed,
        "points": "" if second else str(offered.name.points),
        "publishers_writing": writing(offered),
        "locates": "" if best is None else best.locates,
        "source_id": offered.records[0].record.source_id,
        "record_id": offered.records[0].record.record_id,
        "place_id": offered.name.place_id,
        "lies_in": offered.records[0].lies_in,
        "metres": "",
        "primary_borough": borough,
        "marks": ";".join(marks),
    }


def _relations(
    naming: Naming, by_id: Mapping[str, Name], rules: draft_names.Rules, given: Mapping[str, str]
) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    first = {area: offered for area, offered in naming.first.items() if offered is not None}
    same: dict[str, list[str]] = {}
    for area, offered in sorted(first.items()):
        same.setdefault(draft_names.fold(offered.as_offered), []).append(area)
    for areas in same.values():
        for area in areas:
            for other in areas:
                if other != area:
                    key = first[other].name.key
                    found.append(
                        {
                            "area_id": area,
                            "other_area_id": other,
                            "kind": SAME_NAME,
                            "source_id": key.source_id,
                            "record_id": key.record_id,
                        }
                    )
    for area, offered in sorted(first.items()):
        for each in offered.records:
            if not each.record.writes or each.record.gives != OUTLINE:
                continue
            shares = draft_names.shares_of(each.record, given)
            for other in sorted(shares):
                if other != area and shares[other] >= rules.ties:
                    found.append(
                        {
                            "area_id": area,
                            "other_area_id": other,
                            "kind": NAME_LIES_OVER,
                            "source_id": each.record.source_id,
                            "record_id": each.record.record_id,
                        }
                    )
    for area in sorted(naming.first):
        seed = by_id.get(area)
        lies_in = naming.placed.get(area, "")
        if seed is not None and lies_in and lies_in != area:
            found.append(
                {
                    "area_id": area,
                    "other_area_id": lies_in,
                    "kind": GROWN_FROM_A_NAME_IN,
                    "source_id": seed.key.source_id,
                    "record_id": seed.key.record_id,
                }
            )
    unique = {tuple(row.values()): row for row in found}
    return [unique[key] for key in sorted(unique)]


def snapshots_of(drafted: Drafted, receipts: Sequence[Receipt]) -> tuple[dict[str, object], ...]:
    """Every publisher's file the draft was read from, as `snapshots.json` holds one.

    A file with no receipt has no address, no day and no edition: nothing is
    put in their place, and the row says that it has no receipt.
    """
    found: dict[str, dict[str, object]] = {}
    for receipt in receipts:
        found[receipt.sha256] = {
            "source_id": receipt.source_id,
            "url": receipt.url,
            "retrieved_on": receipt.retrieved_on,
            "sha256": receipt.sha256,
            "bytes": receipt.bytes,
            "version": receipt.edition,
            "has_receipt": True,
            STATE_COLUMN: STATE,
        }
    for file in drafted.files.values():
        if not file.has_receipt:
            found[file.sha256] = {
                "source_id": file.source_id,
                "url": "",
                "retrieved_on": "",
                "sha256": file.sha256,
                "bytes": file.path.stat().st_size,
                "version": "",
                "has_receipt": False,
                STATE_COLUMN: STATE,
            }
    return tuple(
        sorted(found.values(), key=lambda row: (str(row["source_id"]), str(row["sha256"])))
    )


def curated(
    drafted: Drafted,
    found: Draft,
    ground: Ground,
    naming: Naming,
    names: Sequence[Name],
    receipts: Sequence[Receipt],
    nearest: Nearest,
    rules: draft_names.Rules | None = None,
    outside: Outside | None = None,
    *,
    read_every_name: bool = False,
) -> Curated:
    """Every row of the curated files, from the two drafts and the naming of the areas.

    With `read_every_name` no name stands by the rule on one official publisher alone:
    every name is put to a person, as the design first had it.
    """
    rules = rules or draft_names.Rules()
    rests = {
        drafted.area_ids[seed.key]: _truth(names_draft.rests_on_no_receipt(seed, drafted.files))
        for seed in drafted.seeds.seeds
    }
    by_id = {name.place_id: name for name in names}
    given = area_of(found)
    borough = {
        area: ground.boroughs.get(drawn.primary_borough, "")
        for area, drawn in sorted(found.drawn.items())
    }
    first_name = {
        area: offered.as_offered for area, offered in naming.first.items() if offered is not None
    }
    slugs = slugs_of(first_name, borough)
    marked: dict[tuple[str, str], list[str]] = {}
    for mark in naming.marks:
        marked.setdefault((mark.area_id, mark.place_id), []).append(mark.mark)

    areas: list[dict[str, str]] = []
    aliases: list[dict[str, str]] = []
    evidence: list[dict[str, str]] = []
    offered_rows: list[dict[str, str]] = []
    for area in sorted(found.drawn):
        seed = by_id.get(area)
        first = naming.first[area]
        # An area rests on what its seed rests on, and on what the name offered first does.
        behind = {area} | ({first.name.place_id} if first is not None else set[str]())
        areas.append(
            {
                "area_id": area,
                "slug": slugs.get(area, ""),
                "name": first_name.get(area, ""),
                "primary_borough": borough[area],
                "seed_record": "" if seed is None else seed.key.record_id,
                "review_state": DRAFTED,
                "superseded_by": "",
                NO_RECEIPT: _truth(any(rests.get(each) == "true" for each in behind)),
                BOROUGHS: "; ".join(
                    f"{ground.boroughs.get(code, code)}: {count}"
                    for code, count in sorted(
                        found.drawn[area].boroughs.items(), key=lambda pair: (-pair[1], pair[0])
                    )
                ),
                TIE: _truth(is_a_tie(found.drawn[area].boroughs)),
                WRITING: writing(first),
            }
        )
        if first is None:
            offered_rows.append(
                dict.fromkeys(NAMES_COLUMNS, "")
                | {
                    "area_id": area,
                    "offered": FIRST,
                    "why": draft_names.UNNAMED,
                    "primary_borough": borough[area],
                    "marks": ";".join(marked.get((area, ""), [])),
                }
            )
        for offered in naming.offered(area):
            which = FIRST if offered.role == draft_names.PRIMARY else OTHER
            marks = marked.get((area, offered.name.place_id), [])
            second = offered.why == draft_names.SECOND_NAME
            offered_rows.append(
                _offered_row(offered, which, borough[area], [] if second else marks)
            )
            evidence += _evidence(drafted, offered, outside)
            if which == OTHER:
                aliases.append(
                    {
                        "alias": offered.as_offered,
                        "area_id": area,
                        "kind": offered.kind,
                        "source_id": offered.name.key.source_id,
                        "record_id": offered.name.key.record_id,
                        NO_RECEIPT: rests.get(offered.name.place_id, ""),
                    }
                )
        if first is None or first.why != draft_names.SEED:
            here = {offered.name.place_id for offered in naming.offered(area)}
            near_by = [
                (metres, place_id)
                for metres, place_id in nearest(area)
                if place_id not in here and by_id[place_id].proposed != draft_names.WIDE
            ]
            for metres, place_id in near_by[:NEAREST_OFFERED]:
                near = by_id[place_id]
                offered_rows.append(
                    dict.fromkeys(NAMES_COLUMNS, "")
                    | {
                        "area_id": area,
                        "offered": NEAREST,
                        "name": near.name,
                        "proposed_as": near.proposed,
                        "points": str(near.points),
                        "publishers_writing": ";".join(near.publishers),
                        "source_id": near.key.source_id,
                        "record_id": near.key.record_id,
                        "place_id": place_id,
                        "lies_in": naming.placed.get(place_id, ""),
                        "metres": f"{metres:.0f}",
                        "primary_borough": borough[area],
                    }
                )

    looks = draft_marks.looks_of(drafted, naming, names)
    decided = draft_decided.decide(
        naming, evidence, looks, answered=set(drafted.decided), read_every_name=read_every_name
    )
    for row in areas:
        if row["area_id"] in decided.stands:
            row["review_state"] = draft_decided.NAMED_BY_RULE
    of_seeds = {row["area_id"]: row for row in _seed_rows(drafted)}
    seeds = [of_seeds[area] for area in sorted(found.drawn) if area in of_seeds]
    listed = [
        {"area_id": each.area, "what": each.what, "output_areas": " ".join(each.cells)}
        for each in found.listed
    ]
    relations = _relations(naming, by_id, rules, given)
    largest = largest_of(found, areas, aliases)
    rows: dict[str, tuple[Mapping[str, str], ...]] = {
        AREAS: tuple(areas),
        ALIASES: tuple(sorted(aliases, key=lambda r: (r["area_id"], r["alias"], r["kind"]))),
        EVIDENCE: tuple(evidence),
        RELATIONS: tuple(relations),
        AREA_NAMES: tuple(offered_rows),
        TO_LOOK_AT: tuple(looks),
        SEEDS: tuple(seeds),
        LISTED: tuple(listed),
        LARGEST: tuple(largest),
        FLAGS: tuple(draft_marks.flags_of(drafted, naming, decided.fitted)),
        NAMED_BY_THE_RULE: tuple(
            draft_decided.listed(decided, areas, {row["area_id"]: row[WRITING] for row in areas})
        ),
    }
    return Curated(
        rows=rows,
        given=assign_write.oa_to_area(found, ground),
        snapshots=snapshots_of(drafted, receipts),
        counts=counts_of(rows, naming, names, len(drafted.seeds.areas)),
        decided=decided,
    )


def largest_of(
    found: Draft, areas: Sequence[Mapping[str, str]], aliases: Sequence[Mapping[str, str]]
) -> list[dict[str, str]]:
    """The areas that hold most output areas, the largest first, with what lies in each.

    An area is counted in output areas: the licence gate does not give homes
    for this use. Another name that lies in an area is what it could be split
    by. Where there is none, no file holds a name to make a second area of.
    """
    inside: dict[str, list[str]] = {}
    for row in aliases:
        if row["kind"] == draft_names.INSIDE:
            inside.setdefault(row["area_id"], []).append(row["alias"])
    sizes = sorted(len(drawn.cells) for drawn in found.drawn.values())
    median = sizes[len(sizes) // 2] if sizes else 0
    ranked = sorted(
        areas, key=lambda row: (-len(found.drawn[row["area_id"]].cells), row["area_id"])
    )
    return [
        {
            "rank": str(rank),
            "area_id": row["area_id"],
            "name": row["name"],
            "primary_borough": row["primary_borough"],
            "output_areas": str(len(found.drawn[row["area_id"]].cells)),
            "hectares": f"{found.drawn[row['area_id']].hectares:.1f}",
            "times_the_median": f"{len(found.drawn[row['area_id']].cells) / median:.1f}"
            if median
            else "",
            "other_names_inside": str(len(inside.get(row["area_id"], []))),
            "places_inside": "; ".join(sorted(inside.get(row["area_id"], []))),
        }
        for rank, row in enumerate(ranked[:LARGEST_LISTED], start=1)
    ]


def _seed_rows(drafted: Drafted) -> list[dict[str, str]]:
    """Where the seed of each name put forward as an area stands, as the flags read it."""
    return [
        {
            "area_id": row["area_id"],
            "seed_id": row["seed_id"],
            "name": row["name"],
            "easting": row["easting"],
            "northing": row["northing"],
            "weight": row["weight"],
            "no_receipt": row["no_receipt"],
        }
        for row in names_draft.places_of(drafted)
        if row["tier"] == draft_names.AREA
    ]


def counts_of(
    rows: Mapping[str, Sequence[Mapping[str, str]]],
    naming: Naming,
    names: Sequence[Name],
    seeds: int,
) -> dict[str, object]:
    """What the naming counted. It holds numbers, and no name."""
    first = [offered for offered in naming.first.values() if offered is not None]
    others = [each for found in naming.others.values() for each in found]
    marks: dict[str, int] = {}
    for mark in naming.marks:
        marks[mark.mark] = marks.get(mark.mark, 0) + 1
    kinds: dict[str, int] = {}
    for each in others:
        kinds[each.kind] = kinds.get(each.kind, 0) + 1
    relations: dict[str, int] = {}
    for row in rows[RELATIONS]:
        relations[row["kind"]] = relations.get(row["kind"], 0) + 1
    publishers = [
        len({r.record.publisher for r in each.records if r.record.writes}) for each in first
    ]
    # A label may write a name with the publisher's word for a ward or a centre after it,
    # or among other names. Who writes it letter for letter is counted apart.
    exactly = [
        len(
            {
                r.record.publisher
                for r in each.records
                if r.record.writes and r.record.as_written == each.as_offered
            }
        )
        for each in first
    ]
    return {
        "places": len(names),
        "seeds": seeds,
        "areas": len(naming.first),
        "areas_with_a_name": len(first),
        "areas_with_no_name": len(naming.unnamed),
        "areas_named_for_their_seed": sum(each.why == draft_names.SEED for each in first),
        "areas_named_for_another_name": sum(each.why != draft_names.SEED for each in first),
        "areas_whose_name_two_publishers_write": sum(count >= 2 for count in publishers),
        "areas_whose_name_one_publisher_writes": sum(count < 2 for count in publishers),
        "areas_whose_name_two_publishers_write_letter_for_letter": sum(
            count >= 2 for count in exactly
        ),
        "areas_that_rest_on_a_file_with_no_receipt": sum(
            row[NO_RECEIPT] == "true" for row in rows[AREAS]
        ),
        "areas_whose_name_a_point_places": sum(
            any(r.locates == draft_names.POINT_INSIDE for r in each.records if r.record.writes)
            for each in first
        ),
        "other_names": len(others),
        "other_names_by_kind": dict(sorted(kinds.items())),
        "other_names_that_were_seeds": sum(
            each.why in (draft_names.SEED_OF_NO_AREA, draft_names.SEED_OUTSIDE) for each in others
        ),
        "places_offered_nowhere": len(names) - len(naming.placed),
        "rows_of_evidence": len(rows[EVIDENCE]),
        "relations": len(rows[RELATIONS]),
        "relations_by_kind": dict(sorted(relations.items())),
        "marks": dict(sorted(marks.items())),
        "areas_whose_main_borough_is_a_tie": sum(row[TIE] == "true" for row in rows[AREAS]),
        "marks_to_look_at": len(rows[TO_LOOK_AT]),
        "names_with_a_grave_mark": len(
            {row["item"] for row in rows[TO_LOOK_AT] if row["grave"] == "true"}
        ),
        "names_that_may_say_who_lives_there": sum(
            row["flag"] == draft_marks.DESK_FLAGS[draft_marks.Mark.MAY_DESCRIBE_RESIDENTS]
            for row in rows[FLAGS]
        ),
        "flags_for_the_desk": len(rows[FLAGS]),
    }


# Writing


def _with_state(columns: Sequence[str], rows: Iterable[Mapping[str, str]]) -> bytes:
    return table((*columns, STATE_COLUMN), ({**row, STATE_COLUMN: STATE} for row in rows))


def columns_of(name: str) -> tuple[str, ...]:
    """The columns of a curated file as a draft writes it, less the last, which is its state."""
    return (*COLUMNS[name], *MORE.get(name, ()))


def _given_rows(given: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(given.decode("utf-8"), newline="")))


def written(held: Curated) -> dict[str, bytes]:
    """The curated files for a person's eyes, by name: every row says that it is a draft."""
    found = {
        name: _with_state(columns_of(name), held.rows[name])
        for name in OF_THE_DESIGN
        if name != GIVEN
    }
    found[GIVEN] = _with_state(COLUMNS[GIVEN], _given_rows(held.given))
    found[SNAPSHOTS] = (
        json.dumps(list(held.snapshots), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    found[AREA_NAMES] = table(NAMES_COLUMNS, held.rows[AREA_NAMES])
    found[TO_LOOK_AT] = table(LOOK_COLUMNS, held.rows[TO_LOOK_AT])
    found[LARGEST] = table(LARGEST_COLUMNS, held.rows[LARGEST])
    found[NAMED_BY_THE_RULE] = table(draft_decided.COLUMNS, held.rows[NAMED_BY_THE_RULE])
    return found


def for_the_flags(held: Curated) -> dict[str, bytes]:
    """The files of the draft as the flags and the layers read them: every row of evidence."""
    found = {name: table(COLUMNS[name], held.rows[name]) for name in (AREAS, EVIDENCE)}
    found[GIVEN] = held.given
    found[SEEDS] = table(SEED_COLUMNS, held.rows[SEEDS])
    found[LISTED] = table(("area_id", "what", "output_areas"), held.rows[LISTED])
    return found


def may_be_chosen(row: Mapping[str, str]) -> bool:
    """Whether the desk may offer what a row writes as the spelling of a name."""
    return row["source_id"] not in NO_SPELLING_FROM or row["as_written"] == row["name"]


def for_the_desk(held: Curated) -> dict[str, bytes]:
    """The files of the draft as the review desk reads them.

    The four tables the desk reads hold the columns of the design and no
    other. The rows of evidence are those whose form may be chosen as a
    spelling. `seeds.csv` says where each seed stands, and under which name.
    """
    found = {name: table(COLUMNS[name], held.rows[name]) for name in (AREAS, ALIASES)}
    found[EVIDENCE] = table(COLUMNS[EVIDENCE], filter(may_be_chosen, held.rows[EVIDENCE]))
    found[GIVEN] = held.given
    found[SEEDS] = table(SEED_COLUMNS, held.rows[SEEDS])
    found[LISTED] = table(("area_id", "what", "output_areas"), held.rows[LISTED])
    found[FLAGS] = table(("queue", "item", "flag"), held.rows[FLAGS])
    return found
