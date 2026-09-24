"""The files a flag is read from, and the files the flags are written to.

**Read.** Three of the curated files of section 5 of the areas design, as a
draft writes them: `areas.csv`, `oa_to_area.csv` and `name_evidence.csv`. And
`seeds.csv`, which says where each area's seed stands.

| File | Read for |
|---|---|
| `areas.csv` | Each area's id and name. An area another took the place of is left out |
| `oa_to_area.csv` | Each output area's area, and from `evidence` its margin and second choice |
| `name_evidence.csv` | Who writes each name: the publisher of each checked `primary` row. |
| | And whether an official publisher writes it for a populated place at a point inside |
| | the area, where the file says where each record lies |
| `seeds.csv` | `area_id`, `easting`, `northing`: where the seed stands, on the National Grid |

`seeds.csv` may hold a column `no_receipt`. Where it says `true`, the seed or
the weight of its name rests on a file with no receipt, whether or not a row of
evidence names that file. It may hold a column `name`: the name the seed's own
record writes. An area may bear another name than the one it was grown from,
so a seed is never called by the name of its area.

A draft may hold `listed.csv`, with `area_id` and `what`: what its own method
found wrong with an area and could not put right. It is read where it is there.

An area of `areas.csv` that holds no output area in `oa_to_area.csv` is no
area of the draft: the draft made its name part of another area. It is left
out, and counted.

A publisher is who the licence registry says publishes a source. Two sources
of one publisher are one publisher.

**Written.** To a folder that is no part of the repository: what is made from
a publisher's file is never committed.

| File | Holds |
|---|---|
| `flags.csv` | `queue`, `item`, `flag`: every flag, as the review desk reads them |
| `flags_desk.csv` | The flags the desk is handed: of a border, those about the border |
| `flagged.csv` | Every flag with why, in words, and the output areas it points at |
| `order.csv` | Every area and borough in the order to look at them, and how sure the method was |
| `cells_in_doubt.csv` | Every output area a flag points at, with its margin and second choice |
| `rules.json` | Each rule in one line with its number, the words for the desk, and the counts |

A cell of a table that begins `=`, `+`, `-` or `@` gains a leading apostrophe,
as the desk's own files do, so that no sheet reads a name as a sum.
"""

import csv
import json
import math
from collections import Counter
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.areas import flags
from burro_pipeline.areas.draft_decided import OFFICIAL_PLACES
from burro_pipeline.areas.flags import BORDERS, Draft, Flag, Point, Rules
from burro_pipeline.areas.flags_ground import Given, Named
from burro_pipeline.areas.flags_order import Placed, doubts
from burro_pipeline.registry import Registry, RegistryError

AREAS, GIVEN, EVIDENCE, SEEDS = "areas.csv", "oa_to_area.csv", "name_evidence.csv", "seeds.csv"
LISTED = "listed.csv"
# The flags as the desk is handed them.
DESK = "flags_desk.csv"
COLUMNS: Mapping[str, tuple[str, ...]] = {
    AREAS: ("area_id", "name", "superseded_by"),
    GIVEN: ("oa21cd", "area_id", "evidence"),
    EVIDENCE: ("area_id", "role", "source_id", "checked"),
    SEEDS: ("area_id", "easting", "northing"),
    LISTED: ("area_id", "what"),
}
PRIMARY = "primary"
# What a row of evidence says of a record that is a point inside the area.
POINT_INSIDE = "point_inside"
NO_RECEIPT = "no_receipt"
NAME = "name"
# What is said of a seed that rests on a file with no receipt, where no row names the file.
UNNAMED = "a file the draft does not name"
YES = frozenset({"true", "yes", "1"})
MARGIN, SECOND = "margin", "second"
# How much of what is at stake lies in the first so many areas of the order. The design
# gives the founder time for 120.
FIRST = (50, 100, 120, 150, 200, 300)
# What a sheet would read as the start of a sum.
STARTS_A_SUM = ("=", "+", "-", "@")


class Unfit(Exception):
    """A file of the draft that is not as the design gives it. The words name no value."""


def _rows(folder: Path, name: str) -> list[dict[str, str]]:
    try:
        with (folder / name).open(encoding="utf-8-sig", newline="") as file:
            table = csv.DictReader(file, strict=True)
            columns = set(table.fieldnames or ())
            rows = [dict(row) for row in table]
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise Unfit(f"{name} cannot be read as a table") from error
    if not set(COLUMNS[name]) <= columns:
        raise Unfit(f"{name} does not have the columns: {', '.join(COLUMNS[name])}")
    if any(None in row or None in row.values() for row in rows):
        raise Unfit(f"{name} holds a row that is longer or shorter than its first line")
    return rows


def _said(evidence: str) -> dict[str, str]:
    """What a row says placed its output area: `margin=7;second=lon-n0012`."""
    parts = [part.split("=", 1) for part in evidence.split(";") if part.strip()]
    if any(len(part) != 2 for part in parts):
        raise Unfit(f"{GIVEN} gives evidence that is not a list of key=value")
    return {key.strip(): value.strip() for key, value in parts}


def _margin(text: str) -> float | None:
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        value = math.nan
    if not math.isfinite(value) or value < 0:
        raise Unfit(f"{GIVEN} gives a margin that is not a number of hundredths")
    return value


def read_given(folder: Path) -> dict[str, Given]:
    """The area of every output area, with its margin and second choice where the draft says."""
    found: dict[str, Given] = {}
    for row in _rows(folder, GIVEN):
        said = _said(row["evidence"])
        if not row["oa21cd"] or not row["area_id"] or row["oa21cd"] in found:
            raise Unfit(f"{GIVEN} holds an output area twice, or a row with no area")
        found[row["oa21cd"]] = Given(
            row["area_id"], _margin(said.get(MARGIN, "")), said.get(SECOND, "")
        )
    return dict(sorted(found.items()))


@dataclass(frozen=True)
class Seed:
    """Where an area's seed stands, and whether it rests on a file with no receipt."""

    at: Point
    no_receipt: bool = False
    # The name the seed's own record writes. Empty where the draft does not say.
    name: str = ""


def read_seeds(folder: Path) -> dict[str, Seed]:
    """Where each area's seed stands. Nothing where the draft holds no file of seeds."""
    if not (folder / SEEDS).is_file():
        return {}
    found: dict[str, Seed] = {}
    for row in _rows(folder, SEEDS):
        try:
            at = float(row["easting"]), float(row["northing"])
        except ValueError:
            at = math.nan, math.nan
        if not row["area_id"] or row["area_id"] in found or not all(map(math.isfinite, at)):
            raise Unfit(f"{SEEDS} holds an area twice, or a seed at no place")
        found[row["area_id"]] = Seed(
            at, row.get(NO_RECEIPT, "").strip().casefold() in YES, row.get(NAME, "")
        )
    return found


def read_listed(folder: Path) -> dict[str, tuple[str, ...]]:
    """What the draft lists as wrong with each area. Nothing where it holds no such file."""
    if not (folder / LISTED).is_file():
        return {}
    found: dict[str, set[str]] = {}
    for row in _rows(folder, LISTED):
        if row["area_id"] and row["what"]:
            found.setdefault(row["area_id"], set()).add(row["what"])
    return {area_id: tuple(sorted(what)) for area_id, what in sorted(found.items())}


def read_boroughs(folder: Path) -> dict[str, str]:
    """The borough the draft names for each area that stands, as the draft writes it."""
    return {
        row["area_id"]: row.get("primary_borough", "")
        for row in _rows(folder, AREAS)
        if row["area_id"] and not row["superseded_by"]
    }


def publisher_of(registry: Registry, source_id: str) -> str:
    """Who publishes a source, as the registry writes it, less what stands in brackets."""
    try:
        return registry.get(source_id).publisher.split(" (")[0].strip()
    except RegistryError:
        raise Unfit(f"{EVIDENCE} names a source the licence registry does not hold") from None


def fits_the_rule(row: Mapping[str, str]) -> bool:
    """Whether a row of evidence is an official publisher's record of a populated place
    that writes the name, letter for letter, at a point inside the area. A file that
    does not say where a record lies says it of none."""
    return (
        row["source_id"] in OFFICIAL_PLACES
        and row.get("locates") == POINT_INSIDE
        and bool(row.get("name"))
        and row.get("as_written") == row.get("name")
    )


def read_named(folder: Path, registry: Registry, receipted: Collection[str]) -> dict[str, Named]:
    """Every area that stands, with who writes its name and where its seed is.

    `receipted` is every source that has a receipt. A source of a checked row
    that is not among them is one the area rests on with no receipt.
    """
    seeds = read_seeds(folder)
    wrong = read_listed(folder)
    behind: dict[str, list[str]] = {}
    every: set[str] = set()
    by_the_rule: set[str] = set()
    for row in _rows(folder, EVIDENCE):
        every.add(row["source_id"])
        if row["role"] == PRIMARY and row["checked"].strip().casefold() in YES:
            behind.setdefault(row["area_id"], []).append(row["source_id"])
            if fits_the_rule(row):
                by_the_rule.add(row["area_id"])
    # Every source the draft names that has no receipt. A seed that rests on a file with
    # no receipt rests on one of these.
    none_for = {source for source in every if source and source not in receipted}
    found: dict[str, Named] = {}
    for row in _rows(folder, AREAS):
        if not row["area_id"] or row["superseded_by"]:
            continue
        if row["area_id"] in found:
            raise Unfit(f"{AREAS} holds an area twice")
        sources = sorted(set(behind.get(row["area_id"], ())))
        seed = seeds.get(row["area_id"])
        rests_on = {source for source in sources if source not in receipted}
        if seed is not None and seed.no_receipt:
            rests_on |= none_for or {UNNAMED}
        found[row["area_id"]] = Named(
            name=row["name"],
            seed=None if seed is None else seed.at,
            seed_name="" if seed is None else seed.name,
            publishers=tuple(sorted({publisher_of(registry, source) for source in sources})),
            by_the_rule=row["area_id"] in by_the_rule,
            unreceipted=tuple(sorted(rests_on)),
            listed=wrong.get(row["area_id"], ()),
        )
    return dict(sorted(found.items()))


# Writing


def _safe(value: object) -> str:
    text = "" if value is None else str(value)
    return f"'{text}" if text.startswith(STARTS_A_SUM) else text


def _write(path: Path, columns: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        table = csv.DictWriter(file, fieldnames=columns, lineterminator="\n")
        table.writeheader()
        for row in rows:
            table.writerow({column: _safe(row.get(column, "")) for column in columns})


def _number(value: float | None, places: int = 3) -> str:
    return (
        "" if value is None else format(round(value, places), f".{places}f").rstrip("0").rstrip(".")
    )


def counts(found: Sequence[Flag]) -> dict[str, dict[str, int]]:
    """How many items each rule flags, by queue."""
    counted: dict[str, Counter[str]] = {}
    for flag in found:
        counted.setdefault(flag.queue, Counter())[flag.code] += 1
    return {queue: dict(sorted(codes.items())) for queue, codes in sorted(counted.items())}


def write(
    out: Path,
    draft: Draft,
    found: Sequence[Flag],
    areas: Sequence[Placed],
    boroughs: Sequence[Placed],
    *,
    rules: Rules | None = None,
    notes: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Write the flags, the order and the rules, and give back what `rules.json` holds."""
    rules = rules or Rules()
    asked = [{"queue": flag.queue, "item": flag.item, "flag": flag.code} for flag in found]
    _write(out / "flags.csv", ("queue", "item", "flag"), asked)
    # The desk puts a flagged border before one that is not. A flag about the name is on
    # most areas, and is raised where names are read, so it is left out of this file.
    _write(
        out / DESK,
        ("queue", "item", "flag"),
        (
            row
            for row in asked
            if row["queue"] != BORDERS or row["flag"] not in flags.ABOUT_THE_NAME
        ),
    )
    _write(
        out / "flagged.csv",
        (
            *("queue", "item", "area_id", "name", "flag", "about", "why"),
            *("of_the_whole_area", "cells_pointed_at", "cells"),
        ),
        (
            {
                "queue": flag.queue,
                "item": flag.item,
                "area_id": flag.area,
                "name": draft.areas[flag.area].name,
                "flag": flag.code,
                "about": "name" if flag.code in flags.ABOUT_THE_NAME else "border",
                "why": flag.why,
                "of_the_whole_area": "true" if flag.whole else "false",
                "cells_pointed_at": len(flag.cells),
                "cells": " ".join(flag.cells),
            }
            for flag in found
        ),
    )
    _write(
        out / "order.csv",
        (
            *("queue", "rank", "item", "name", "flags", "at_stake", "held", "weighed_by"),
            *("sure", "why"),
        ),
        (
            {
                "queue": placed.queue,
                "rank": placed.rank,
                "item": placed.item,
                "name": draft.areas[placed.item].name if placed.queue == BORDERS else "",
                "flags": " ".join(placed.flags),
                "at_stake": _number(placed.at_stake, 1),
                "held": _number(placed.held, 1),
                "weighed_by": placed.weighed_by,
                "sure": _number(placed.sure),
                "why": " ".join(placed.why),
            }
            for placed in (*areas, *boroughs)
        ),
    )
    pointed = doubts(draft, found, rules)
    why: dict[tuple[str, str], list[str]] = {}
    for flag in found:
        if flag.queue == BORDERS:
            for oa in flag.cells:
                why.setdefault((flag.area, oa), []).append(flag.code)
    _write(
        out / "cells_in_doubt.csv",
        ("oa21cd", "area_id", "doubt", "margin", "second", "flags"),
        (
            {
                "oa21cd": oa,
                "area_id": area_id,
                "doubt": _number(doubt),
                "margin": _number(draft.cells[oa].margin),
                "second": draft.cells[oa].second,
                "flags": " ".join(why.get((area_id, oa), ())),
            }
            for area_id, cells in sorted(pointed.items())
            for oa, doubt in sorted(cells.items())
        ),
    )
    lines = rules.lines()
    flagged = [placed for placed in areas if placed.flags]
    border = [placed for placed in areas if placed.about_the_border]
    at_stake = math.fsum(placed.at_stake for placed in areas)
    said: dict[str, object] = {
        "rules": [
            {
                "flag": code,
                "rule": line,
                "queues": [queue for queue, words in flags.WORDS.items() if code in words],
                "words_for_the_desk": {
                    queue: words[code] for queue, words in flags.WORDS.items() if code in words
                },
            }
            for code, line in lines.items()
        ],
        "not_worked_out": flags.not_worked_out(draft),
        "weighed_by": draft.weighed_by,
        "counts": {
            "areas": len(areas),
            "output_areas": len(draft.cells),
            "areas_flagged": len(flagged),
            "areas_flagged_about_the_border": len(border),
            "areas_flagged_about_the_name_alone": len(flagged) - len(border),
            "areas_with_no_flag": len(areas) - len(flagged),
            "flags_by_queue_and_rule": counts(found),
            "areas_by_number_of_flags_about_the_border": dict(
                sorted(Counter(len(placed.about_the_border) for placed in areas).items())
            ),
            "output_areas_in_doubt": sum(len(cells) for cells in pointed.values()),
            "at_stake": round(at_stake, 1),
            "share_of_what_is_at_stake_in_the_first": {
                str(first): round(
                    math.fsum(placed.at_stake for placed in areas[:first]) / at_stake, 3
                )
                for first in FIRST
                if at_stake > 0 and first <= len(areas)
            },
            "areas_the_method_was_sure_of_under_half": sum(
                placed.sure is not None and placed.sure < 0.5 for placed in areas
            ),
        },
        "order": "An area in two pieces or on both banks first. Then the most at stake "
        "first. What is at stake is every output area in doubt, "
        f"counted in {draft.weighed_by} and by how unsure the method was of it, and a tenth "
        "of the area for each flag of the whole area.",
        "numbers": {name: getattr(rules, name) for name in sorted(vars(rules))},
        "notes": dict(sorted((notes or {}).items())),
    }
    (out / "rules.json").write_text(
        json.dumps(said, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8"
    )
    return said
