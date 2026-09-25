"""Make the whole draft of London's areas from the store, in one command.

    python -m burro_pipeline draft --out FOLDER
    python -m burro_pipeline.areas.draft_run --out FOLDER

It runs the parts of the areas in the order the design gives them, each as its
own module makes it, and joins them. It is the step `draft` of the one command
line, which `cli.py` beside this joins it to, and takes the same arguments
under either name.

| Step | What is made | By | Written to |
|---|---|---|---|
| 1 | Candidates, places and seeds | `names_draft` | `made/names/` |
| 2 | Every output area given to an area, and each area's outline | `assign_run` | `made/areas/` |
| 3 | A name for each area, and the curated files | `draft_names`, `draft_files` | The folder |
| 4 | The files as the review desk reads them | `draft_files` | `desk/draft/` |
| | The files as the flags and the layers read them | `draft_files` | `made/draft/` |
| 5 | The flags, and the order to look at the areas in | `flags_build` | `made/flags/` |
| 6 | The layers a reviewer sees behind a border | `context_files` | `made/context/` |
| 7 | A picture of London, and one of each borough | `draft_picture` | `pictures/` |

It is a draft: what a method made and nobody has checked. A file that has no
receipt is read for a draft alone, from a store that is a folder, and
everything that rests on it says so. No file of London is read so today: the
town centres were, until they had their receipt. From an object store no such
file is read at all, so a hosted run reads none.

**Made again from what was decided.** The review desk cannot take the ground
from under an area: an answer that turns a name put forward as an area into
another name, or into no name, is set aside there. So the names are read
first, and the draft is made again before any border is looked at:

    --decided FILE   the answers about names, as the desk's `out/names.csv` holds them
    --kept FILE      the areas that stay however small, one `area_id` to a row
    --ids FILE       the `ids.csv` of the draft the answers were given on

**One official publisher is enough for a name.** The founder decided so on
2026-09-24: decision record 0022, and `draft_decided.py`. A name that an official
publisher writes for a populated place, at a point inside the area, is a name.
The name of an area that the rule fits, and that the draft has no mark on, stands
by the rule alone and is put to nobody: `named_by_the_rule.csv` lists each. With
`--read-every-name` none does, and every name is put to a person as before.

Of `--decided` only the founder's answers about a name put forward as an area
are read: a row whose `item` begins `n:` and whose `reviewer` is `r1`. An
answer about another name is applied by the desk itself. A person may also
write the file by hand, with the columns `area_id` and `answer`, to make an
area of a place the draft put forward as another name: the desk cannot.

Every file is asked for under `gazetteer`, by the module that reads it. A
source the gate refuses is not read. Nothing about who lives anywhere is read,
and nothing from OpenStreetMap. No name and no border is supplied by whoever
runs this, or by a model.

It reaches no publisher, and no socket can be made while a file is read. It
reaches the store, to copy files out, and writes nothing to it. The store is
named by the environment and is never printed: a folder, or an object store.
An object store is reached over a network, so every file that has a receipt is
copied out of it before any is read. The same files give the same bytes:
nothing here reads a clock.

What it prints may be read by anyone: one line of counts. What it writes names
places, so it goes to the folder `--out` names, which must be outside what git
tracks.
"""

import argparse
import csv
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, cast

from burro_pipeline.areas import (
    assign,
    assign_run,
    assign_write,
    context,
    context_files,
    context_shapes,
    draft_decided,
    draft_files,
    draft_lines,
    draft_names,
    draft_picture,
    draft_rules,
    draft_shapes,
    flags,
    flags_build,
    flags_files,
    flags_order,
    names_draft,
)
from burro_pipeline.areas.assign import Draft
from burro_pipeline.areas.assign_files import Ground, Reading
from burro_pipeline.areas.assign_outline import Outlines
from burro_pipeline.areas.draft_picture import Label, Picture, Shape
from burro_pipeline.areas.names_candidates import Candidate
from burro_pipeline.areas.names_draft import Drafted, Read
from burro_pipeline.areas.seeds import Rules, Tier
from burro_pipeline.cells import shapes
from burro_pipeline.evidence.cli import public
from burro_pipeline.evidence.lock import LockError, read_receipts
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.fetch.store import FolderStore, StoreError, store_from_environment
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import RegistryError, find, load

STEP = "areas-draft"
MADE, DESK, PICTURES = "made", "desk", "pictures"
NAMES, AREAS, FLAGS, CONTEXT = "names", "areas", "flags", "context"
# The answer of the review desk that says a name is the name of an area.
AREA = "area"
# The folder of a draft as the review desk reads one, inside its folder of data.
DESK_DRAFT = "draft"
# What a person reads beside each item. The desk reads it when it fills its queues.
LINES = "lines.csv"
# What the desk marks on the map of each border: the doubt of each cell, the stretch that
# follows no line, the seed that stands close, the town centre a flag names.
MARKS = "marks.csv"
# The order to look at the areas and the boroughs in, as the desk reads it.
ORDER, ORDER_COLUMNS = "order.csv", ("queue", "item", "rank")
# The rules put to the founder, and the items each would settle. None is applied.
RULES_PUT, WOULD_SETTLE = "rules_put_to_the_founder.csv", "rules_would_settle.csv"
# The same, as the desk reads them, to put each rule to the founder as an item.
DESK_RULES, DESK_RULED = "rules.csv", "rules_items.csv"
LONDON = "london"
# A name that fewer publishers write than this rests on one publisher, or on none.
TWO = 2
# Two areas this near each other, in metres, are given two colours in a picture, whether
# or not they share a side: the tidal water is nowhere wider where a picture is looked at.
SIDE_BY_SIDE = 400.0


ABOUT = """\
A draft of the areas of London: what a method made, and nobody has checked.

Everything here is made from publishers' files. None of it is committed, and none of it
is published. Every name is one a publisher's file holds. No name and no border was
supplied by a person or by a model. What rests on a file that has no receipt says so in
its own row: the column no_receipt of areas.csv and of aliases.csv, the empty dates of
name_evidence.csv, and a line of the item at the review desk.

The order of the work. The review desk cannot take the ground from under an area, so:
  1. Read the names at the desk, and no border yet.
  2. Make the draft again from the answers, under the same ids:
       --decided <the desk's out/names.csv>  --ids made/names/ids.csv
     A name that was turned down is then no area, and its ground goes to its neighbours.
  3. Fill the queues again, and only then look at the borders.

The curated files, as section 5 of the areas design names them. Each row ends `state`:
  areas.csv            every area that stands, with the name offered first
  oa_to_area.csv       every output area, and the area it is given to
  aliases.csv          every other name offered for an area
  name_evidence.csv    every record that writes a name, and whether it lies in the area
  relations.csv        two areas that a name ties together
  snapshots.json       every publisher's file that was read

For a person's eyes:
  area_names.csv        every name offered for every area, with who writes it
  names_to_look_at.csv  every mark to settle before a name ships, the gravest first: a name
                        that may say who lives there, then what the naming found, then the
                        rest. Each row names the item of the review desk it is on
  made/names/hard_look.csv  every mark of every name, the grave and the rest, as the draft
                        of names wrote them before a border was drawn
  largest_areas.csv     the ten areas that hold most output areas, and the other names that
                        lie in each. Where none does, the desk cannot make the area smaller
  named_by_the_rule.csv every area whose name an official publisher writes for a populated
                        place at a point inside it. The founder decided that such a name is
                        a name. Those the draft has no mark on stand by the rule alone, come
                        first, and are not asked about at the desk. To turn one down, write
                        its area_id and an answer in a file of decisions, by hand
  rules_put_to_the_founder.csv  rules that would save hours, each with what it would
                        settle and what could go wrong. None is adopted: the founder decides
  rules_would_settle.csv  every item each of those rules would settle, to skim
  pictures/             london.svg, and one picture of each borough. No basemap
  counts.json           everything that was counted
  made/flags/order.csv  every area and borough in the order to look at them
  made/                 what each part of the method wrote, as it wrote it

For the review desk:
  desk/draft/           the draft as the desk reads one: copy it to <data>/draft, and
                        fill the queues from it. No step comes between
  desk/draft/lines.csv  what a person reads beside each item: every doubt of the draft, in
                        words. The desk reads it when it fills its queues
  desk/draft/marks.csv  what the desk marks on the map of a border: the doubt of each
                        cell, a stretch that follows no line, a seed that stands close
  desk/draft/order.csv  the order the desk offers names and borders in: borough by borough,
                        the most at stake first
  desk/draft/rules.csv  the rules put to the founder, and in rules_items.csv the items each
                        would settle. The desk asks of each rule whether it is adopted
"""


@dataclass(frozen=True)
class Settings:
    """The rules of every part of the method. Each part's own module says what each means."""

    of_seeds: Rules = field(default_factory=Rules)
    of_areas: assign.Rules = field(default_factory=assign.Rules)
    of_reading: Reading = field(default_factory=Reading)
    of_naming: draft_names.Rules = field(default_factory=draft_names.Rules)
    of_flags: flags.Rules = field(default_factory=flags.Rules)
    # The points an area needs, and the publishers they must come from. With neither, the
    # design's 6 from two is moved until the count of areas lands in range.
    points: int | None = None
    publishers: int | None = None
    # What a person decided of a name at the review desk, by the id of the place.
    decided: Mapping[str, str] = field(default_factory=dict[str, str])
    # Whether every name is put to a person, though the rule on one official publisher
    # fits it and the draft has no mark on it.
    read_every_name: bool = False


class Refused(Exception):
    """The run could not start. Says why, and never what a file holds."""


# What was decided at the review desk

ITEM, REVIEWER, ANSWER, AREA_ID = "item", "reviewer", "answer", "area_id"
# The founder, as the desk writes a reviewer. The desk takes names from the founder alone.
FOUNDER = "r1"
# What begins the item of a name put forward as an area.
OF_AN_AREA = "n:"
# The answers by which a person says they cannot judge. Such an answer decides nothing.
DECIDES_NOTHING = frozenset({"unknown", "cannot_say", "cannot_tell", "skip"})


def _table(path: Path, what: str) -> tuple[set[str], list[dict[str, str]]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            rows = csv.DictReader(file, strict=True)
            columns = set(rows.fieldnames or ())
            held = [dict(row) for row in rows]
    except (OSError, UnicodeDecodeError, csv.Error):
        raise Refused(f"the file of {what} could not be read as a table") from None
    if any(None in row or None in row.values() for row in held):
        raise Refused(f"the file of {what} holds a row that is longer or shorter than its header")
    return columns, held


def read_decided(path: Path) -> dict[str, str]:
    """What a person decided of each name put forward as an area, by the id of the place.

    The file is the desk's own table of answers, or one written by hand. It
    raises `Refused`, which names no place and no answer that was given.
    """
    columns, rows = _table(path, "decisions")
    found: dict[str, str] = {}
    if {ITEM, REVIEWER, ANSWER} <= columns:
        pairs = [
            (row[ITEM].removeprefix(OF_AN_AREA), row[ANSWER])
            for row in rows
            if row[ITEM].startswith(OF_AN_AREA) and row[REVIEWER] == FOUNDER
        ]
    elif {AREA_ID, ANSWER} <= columns and ITEM not in columns:
        pairs = [(row[AREA_ID], row[ANSWER]) for row in rows]
    else:
        raise Refused(
            f"the file of decisions lacks its columns: {ITEM}, {REVIEWER} and {ANSWER} as "
            f"the desk writes them, or {AREA_ID} and {ANSWER} as a person does"
        )
    for area_id, answer in pairs:
        if answer in DECIDES_NOTHING:
            continue
        if answer not in names_draft.ANSWERS:
            raise Refused(f"an answer is none of: {', '.join(names_draft.ANSWERS)}")
        if not area_id or area_id in found:
            raise Refused("the file of decisions holds a place twice, or a row with no place")
        found[area_id] = answer
    return found


def read_kept(path: Path) -> frozenset[str]:
    """The areas that stay however small they are: the design's short kept list."""
    columns, rows = _table(path, "areas that are kept")
    if AREA_ID not in columns:
        raise Refused(f"the file of areas that are kept lacks the column {AREA_ID}")
    return frozenset(row[AREA_ID] for row in rows if row[AREA_ID])


# Naming


def whole_of(found: Draft, ground: Ground) -> dict[str, shapes.Shape]:
    """The ground of every area as one outline, on the National Grid."""
    return {
        area: shapes.joined([ground.outlines[oa] for oa in drawn.cells])
        for area, drawn in sorted(found.drawn.items())
    }


def named(
    held: Read,
    drafted: Drafted,
    found: Draft,
    ground: Ground,
    inputs: Inputs,
    whole: Mapping[str, shapes.Shape],
    rules: draft_names.Rules | None = None,
    *,
    read_every_name: bool = False,
) -> tuple[draft_files.Curated, draft_names.Naming]:
    """The curated files of the two drafts, with a name offered for each area."""
    kept: dict[tuple[str, str], Mapping[str, float]] = {}

    def shares(candidate: Candidate) -> Mapping[str, float]:
        key = (candidate.source_id, candidate.record_id)
        if key not in kept:
            kept[key] = draft_shapes.shares_on(candidate.shape, held.london.ground)
        return kept[key]

    names = draft_files.names_of(drafted, shares, held.london.ground.holding)
    naming = draft_names.name_areas(
        names, draft_files.area_of(found), draft_files.stands_as(found), rules
    )
    points = {drafted.area_ids[seed.key]: seed.place.at for seed in drafted.seeds.seeds}

    def nearest(area: str) -> Sequence[tuple[float, str]]:
        return draft_shapes.nearest_to(whole[area], points, len(points))

    records = {(each.source_id, each.record_id): each for each in drafted.candidates.records}

    def outside(source_id: str, record_id: str, area: str) -> float:
        return records[source_id, record_id].metres_from_shape(whole[area])

    receipts = [opened.receipt for opened in inputs.opened]
    curated = draft_files.curated(
        drafted,
        found,
        ground,
        naming,
        names,
        receipts,
        nearest,
        rules,
        outside,
        read_every_name=read_every_name,
    )
    return curated, naming


# The lines of the desk


def lines_of(
    inputs: Inputs,
    drafted: Drafted,
    curated: draft_files.Curated,
    naming: draft_names.Naming,
    read: flags_build.Read,
    flagged: flags_build.Flagged,
    rules: flags.Rules,
) -> list[draft_lines.Line]:
    """Every line the draft hands the desk, for the names and then for the borders."""
    words = {
        source: draft_lines.in_words(
            inputs.registry.get(source).publisher, inputs.registry.get(source).name
        )
        for source in sorted(drafted.files)
    }
    doubts = flags_order.doubts(flagged.draft, flagged.flags, rules)
    in_doubt = {oa: read.outlines[oa] for cells in doubts.values() for oa in cells}
    named_links = [link for link in read.links if link.name or link.number]
    streets = draft_lines.streets_of(
        [link.name or link.number for link in named_links],
        context_shapes.metres_in([link.shape for link in named_links], in_doubt),
    )
    given = {
        row["oa21cd"]: row["evidence"]
        for row in csv.DictReader(curated.given.decode("utf-8").splitlines())
    }
    held = {area: len(cells) for area, cells in flagged.draft.cells_of.items()}
    return [
        *draft_lines.names(curated.rows, drafted, naming, words, held, curated.decided),
        *draft_lines.borders(
            flagged.draft,
            flagged.flags,
            doubts,
            given,
            {row["area_id"]: row["name"] for row in curated.rows[draft_files.AREAS]},
            {area: flags.main_borough(flagged.draft, area) for area in flagged.draft.areas},
            wide=frozenset(
                seed.name.casefold() for seed in drafted.seeds.seeds if seed.tier is Tier.WIDE
            ),
            streets=streets,
            unread=draft_decided.unread(curated.decided, words),
        ),
    ]


# The flags of the desk


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def desk_flags(of_the_borders: Path, of_the_names: Path) -> bytes:
    """`flags.csv` as the review desk reads it: of the borders, and of the names."""
    rows = [*_rows(of_the_borders), *_rows(of_the_names)]
    unique = {(row["queue"], row["item"], row["flag"]): row for row in rows}
    return names_draft.table(("queue", "item", "flag"), [unique[key] for key in sorted(unique)])


# Pictures


def _json(path: Path) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], json.loads(path.read_bytes()))


def _layer(
    folder: Path, group: str, layer: str, drawn_as: str, of: Sequence[str] | None = None
) -> list[Shape]:
    """One layer of one group, as shapes to draw. Nothing where the group has no such layer.

    With `of`, only the features of those areas.
    """
    path = folder / group / f"{layer}.geojson"
    if not path.is_file():
        return []
    return [
        Shape(drawn_as, each["geometry"])
        for each in draft_picture.features_of(_json(path))
        if of is None or str(each["properties"].get("area", "")) in of
    ]


def pictures(
    found: Draft, outlines: Outlines, made: Path, whole: Mapping[str, shapes.Shape]
) -> dict[str, str]:
    """A picture of London and one of each borough, by the name of its file."""
    colours = context.colours_of(draft_shapes.near_each_other(whole, SIDE_BY_SIDE))
    layers, water = made / CONTEXT / "layers", made / CONTEXT / "not_yet_drawn"
    boroughs = {
        str(each["id"]): each
        for each in draft_picture.features_of(_json(layers / context.ALL / "boroughs.geojson"))
    }
    lines = [Shape(draft_picture.LINE, each["geometry"]) for each in boroughs.values()]
    areas = {
        area: Shape(draft_picture.AREA, outlines.of[area].geometry, colours[area], area)
        for area in sorted(outlines.of)
    }
    river = {
        group.name: _layer(water, group.name, "water", draft_picture.WATER_FILL)
        for group in sorted(water.iterdir() if water.is_dir() else ())
    }
    # Each borough's group holds the water near it, so one stretch is in several groups.
    every_river = list(
        {
            json.dumps(each.geometry, sort_keys=True): each
            for group in sorted(river)
            for each in river[group]
        }.values()
    )
    found_pictures = {
        f"{LONDON}.svg": draft_picture.svg(
            Picture(
                f"A draft of London's areas, made by method and checked by nobody. "
                f"{len(areas)} areas.",
                [*areas.values(), *every_river, *lines],
            )
        )
    }
    for code, borough in sorted(boroughs.items()):
        group = context.group_of(str(borough["properties"]["name"]))
        shown = sorted(area for area, drawn in found.drawn.items() if code in drawn.boroughs)
        if not shown:
            continue
        seeds = _layer(layers, group, "seeds", draft_picture.DOTS, shown)
        found_pictures[f"borough-{group}.svg"] = draft_picture.svg(
            Picture(
                f"{borough['properties']['name']}: a draft, made by method and checked by "
                f"nobody. {len(shown)} areas lie in it, in whole or in part.",
                [
                    *(areas[area] for area in shown),
                    *river.get(group, []),
                    *_layer(layers, group, "roads", draft_picture.ROADS),
                    *_layer(layers, group, "centres", draft_picture.CENTRES),
                    Shape(draft_picture.LINE, borough["geometry"]),
                    *seeds,
                ],
                labels=[
                    Label(area.removeprefix("lon-n").lstrip("0") or "0", outlines.of[area].inside)
                    for area in shown
                ],
                fit_to=[areas[area].geometry for area in shown],
            )
        )
    return found_pictures


# The run


def _write(folder: Path, files: Mapping[str, bytes]) -> None:
    for name in sorted(files):
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(files[name])


def make(
    inputs: Inputs, out: Path, *, ids: Path | None = None, settings: Settings | None = None
) -> dict[str, object]:
    """Make the whole draft in a folder, and give what was counted."""
    settings = settings or Settings()
    made = out / MADE
    held = names_draft.read(inputs, draft=True)
    drafted = names_draft.make(
        held,
        settings.of_seeds,
        ids=names_draft.read_ids(ids) if ids is not None else None,
        points=settings.points,
        publishers=settings.publishers,
        decided=settings.decided,
    )
    listed = settings.of_areas.kept
    if not listed <= set(drafted.area_ids.values()):
        raise ValueError("the list of areas that are kept holds a place the draft does not hold")
    # A name that a person made an area stays an area, however small its ground.
    made_areas = {place for place, said in settings.decided.items() if said == AREA}
    of_areas = replace(settings.of_areas, kept=listed | made_areas)
    of_names = names_draft.write(made / NAMES, drafted)

    seeds = assign_run.read_seeds(made / NAMES / "seeds.csv")
    found, ground, outlines = assign_run.drafted(inputs, seeds, of_areas, settings.of_reading)
    assign_write.write(assign_write.files_of(found, ground, outlines), made / AREAS)

    whole = whole_of(found, ground)
    curated, naming = named(
        held,
        drafted,
        found,
        ground,
        inputs,
        whole,
        settings.of_naming,
        read_every_name=settings.read_every_name,
    )
    _write(out, draft_files.written(curated))
    desk = out / DESK / DESK_DRAFT
    _write(desk, draft_files.for_the_desk(curated))
    # The flags and the layers read every row of evidence. The desk is handed fewer.
    whole_draft = made / DESK_DRAFT
    _write(whole_draft, draft_files.for_the_flags(curated))

    read = flags_build.read_ground(inputs, draft=True)
    flagged = flags_build.flag(inputs, read, whole_draft, made / FLAGS, rules=settings.of_flags)
    (desk / "flags.csv").write_bytes(
        desk_flags(made / FLAGS / flags_files.DESK, desk / draft_files.FLAGS)
    )
    (desk / ORDER).write_bytes(
        names_draft.table(
            ORDER_COLUMNS,
            [
                {"queue": placed.queue, "item": placed.item, "rank": str(placed.rank)}
                for placed in (*flagged.areas, *flagged.boroughs)
            ],
        )
    )
    # Rules that would save hours are counted and listed, and never applied. A name that
    # stands by what the founder has decided already is no item, and no rule settles it.
    would = [
        *draft_rules.of_names(curated.rows, drafted, naming, curated.decided),
        *draft_rules.of_borders(flagged.draft, flagged.flags),
    ]
    lines = [
        *lines_of(inputs, drafted, curated, naming, read, flagged, settings.of_flags),
        *draft_rules.lines_for_the_desk(
            WOULD_SETTLE, would, curated.decided, draft_files.NAMED_BY_THE_RULE
        ),
    ]
    (desk / LINES).write_bytes(
        names_draft.table(draft_lines.COLUMNS, [line.row() for line in lines])
    )
    doubts = flags_order.doubts(flagged.draft, flagged.flags, settings.of_flags)
    (desk / MARKS).write_bytes(
        names_draft.table(
            draft_lines.MARK_COLUMNS, draft_lines.marks(flagged.draft, flagged.flags, doubts)
        )
    )
    put = draft_rules.put_to_the_founder(would, curated.decided)
    rules, ruled = draft_rules.for_the_desk(would)
    _write(
        desk,
        {
            DESK_RULES: names_draft.table(draft_rules.DESK_COLUMNS, rules),
            DESK_RULED: names_draft.table(draft_rules.DESK_ITEM_COLUMNS, ruled),
        },
    )
    _write(
        out,
        {
            RULES_PUT: names_draft.table(draft_rules.COLUMNS, put),
            WOULD_SETTLE: names_draft.table(
                draft_rules.ITEM_COLUMNS, [each.row() for each in draft_rules.left(would)]
            ),
        },
    )

    for folder in ("layers", "not_yet_drawn"):
        shutil.rmtree(made / CONTEXT / folder, ignore_errors=True)
    layers = context_files.build(inputs, made / CONTEXT, draft=True, drafted=whole_draft)
    shutil.rmtree(desk / "layers", ignore_errors=True)
    shutil.copytree(made / CONTEXT / "layers", desk / "layers")

    drawn = pictures(found, outlines, made, whole)
    _write(out / PICTURES, {name: text.encode("utf-8") for name, text in drawn.items()})

    counted_flags = cast(Mapping[str, Any], flagged.said["counts"])
    unnamed = [row for row in curated.rows[draft_files.AREAS] if not row["name"]]
    no_receipt = sorted(file.source_id for file in drafted.files.values() if not file.has_receipt)
    counted: dict[str, object] = {
        "state": draft_files.STATE,
        "names": of_names,
        "areas": json.loads(assign_write.counts(found, ground, outlines)),
        "naming": curated.counts,
        "flags": counted_flags,
        "layers": len(layers.written),
        "pictures": len(drawn),
        "rules_put_to_the_founder": {row["rule"]: int(row["would_settle"]) for row in put},
        "rules_already_decided": {row["rule"]: int(row["already_decided"]) for row in put},
        draft_decided.CODE: draft_decided.counts_of(
            curated.decided,
            len(curated.rows[draft_files.AREAS]),
            [
                row["area_id"]
                for row in curated.rows[draft_files.AREAS]
                if len([each for each in row[draft_files.WRITING].split(";") if each]) < TWO
            ],
        ),
        "for_the_founder_to_decide": draft_rules.to_decide(drafted),
        "lines_for_the_desk": {
            queue: sum(line.queue == queue for line in lines)
            for queue in sorted({line.queue for line in lines})
        },
        "files_read": sorted(opened.file_id for opened in inputs.opened),
        "decided_at_the_desk": of_names["decided_at_the_desk"],
        "areas_kept_however_small": len(of_areas.kept),
        "files_with_no_receipt": no_receipt,
    }
    _write(
        out,
        {
            "counts.json": (
                json.dumps(counted, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
            ).encode("utf-8"),
            "about.txt": ABOUT.encode("utf-8"),
        },
    )
    return {
        "output_areas": len(found.given),
        "candidates": len(drafted.candidates.records),
        "places": len(drafted.candidates.places),
        "seeds": len(drafted.seeds.areas),
        "areas": len(found.drawn),
        "areas_with_no_name": len(unnamed),
        "other_names": len(curated.rows[draft_files.ALIASES]),
        "evidence_rows": len(curated.rows[draft_files.EVIDENCE]),
        "relations": len(curated.rows[draft_files.RELATIONS]),
        "areas_flagged_about_the_border": counted_flags["areas_flagged_about_the_border"],
        "layers": len(layers.written),
        "pictures": len(drawn),
        "no_receipt": len(no_receipt),
    }


def parser() -> argparse.ArgumentParser:
    given = argparse.ArgumentParser(
        prog="python -m burro_pipeline.areas.draft_run",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    arguments(given)
    return given


def arguments(given: argparse.ArgumentParser) -> None:
    """Add the arguments a run takes to a parser: this command's own, or the step's."""
    given.add_argument(
        "--out",
        required=True,
        type=Path,
        metavar="FOLDER",
        help="the folder the draft is written to, outside what git tracks. It is new, or empty",
    )
    given.add_argument(
        "--again",
        action="store_true",
        help="write over the files of an earlier draft in the folder --out names",
    )
    given.add_argument(
        "--ids",
        type=Path,
        metavar="FILE",
        help="the ids.csv of an earlier draft, so that every place keeps its id",
    )
    given.add_argument(
        "--points",
        type=int,
        metavar="N",
        help="the points an area needs. Without it, the design's 6 is moved until the count "
        "of areas lands in range",
    )
    given.add_argument(
        "--publishers",
        type=int,
        metavar="N",
        help="the publishers an area's points must come from. Given with --points",
    )
    given.add_argument(
        "--decided",
        type=Path,
        metavar="FILE",
        help="the answers about names that were given at the review desk, as its out/names.csv "
        "holds them. A name that was turned down is then no area",
    )
    given.add_argument(
        "--kept",
        type=Path,
        metavar="FILE",
        help="the areas that stay however small they are, one area_id to a row",
    )
    given.add_argument(
        "--read-every-name",
        action="store_true",
        help="put every name to a person at the desk, though an official publisher writes it "
        "for a populated place at a point inside the area and the draft has no mark on it",
    )
    given.add_argument(
        "--receipts",
        type=Path,
        default=Path(RECEIPTS_FOLDER),
        metavar="FOLDER",
        help=f"the folder of receipts (default: {RECEIPTS_FOLDER})",
    )
    given.add_argument(
        "--registry", type=Path, metavar="FOLDER", help="the licence registry (default: this one)"
    )
    given.add_argument(
        "--work",
        type=Path,
        metavar="FOLDER",
        help="where the copies of the files are put while they are read, and left. Without it "
        "they are put in a folder that is removed when the run ends",
    )


def _run(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    out: Path = args.out
    if assign_run.tracked(out):
        raise Refused("the folder to write to is one git tracks. Name one outside the repository")
    if out.exists() and any(out.iterdir()) and not args.again:
        raise Refused(f"the folder {out.name} holds something already. Name a folder that is new")
    if (args.points is None) != (args.publishers is None):
        raise Refused("--points and --publishers are given together, or not at all")
    if not args.receipts.is_dir():
        raise Refused("the folder of receipts is not there. Name it with --receipts")
    if args.ids is not None and not args.ids.is_file():
        raise Refused("the file of ids is not there")
    decided = read_decided(args.decided) if args.decided is not None else {}
    kept = read_kept(args.kept) if args.kept is not None else frozenset[str]()
    try:
        store = store_from_environment(environment)
    except StoreError as error:
        raise Refused(str(error)) from None
    with tempfile.TemporaryDirectory(prefix="burro-draft-") as scratch:
        inputs = Inputs(
            registry=load(args.registry or find()),
            receipts=read_receipts(args.receipts),
            store=store,
            work=args.work or Path(scratch),
        )
        if store.kind != FolderStore.kind:
            # A file is read with no socket open, and this store is reached over a network.
            copied, size = inputs.copy_out()
            said = public("store", "ok", kind=store.kind, files=copied, bytes=size)
            sys.stdout.write(f"{said}\n")
            sys.stdout.flush()
        with sockets_refused():
            settings = Settings(
                of_areas=assign.Rules(kept=kept),
                points=args.points,
                publishers=args.publishers,
                decided=decided,
                read_every_name=args.read_every_name,
            )
            counted = make(inputs, out, ids=args.ids, settings=settings)
    sys.stdout.write(public(STEP, "ok", **counted) + "\n")
    return 0


def main(argv: Sequence[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    return run(parser().parse_args(argv), os.environ if environment is None else environment)


def run(args: argparse.Namespace, environment: Mapping[str, str]) -> int:
    """Make the draft the arguments ask for, and say in one line how it ended."""
    try:
        return _run(args, environment)
    except LockError as error:
        sys.stdout.write(public(STEP, "refused", **{error.rule: 1}) + "\n")
        sys.stderr.write(f"error: {error}\n")
    except (Refused, RegistryError, ValueError, flags_files.Unfit) as error:
        sys.stdout.write(public(STEP, "unreadable") + "\n")
        sys.stderr.write(f"error: {error}\n")
    except OSError as error:
        sys.stdout.write(public(STEP, "unreadable") + "\n")
        sys.stderr.write(f"error: cannot read or write a file: {error.strerror}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
