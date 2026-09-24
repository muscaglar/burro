"""A draft folder, and the items each queue is filled with from it.

A draft folder is what the areas build, the pipeline and the research run hand to the
desk: docs/design/desk.md, section 8. The made-up city and London take this one path.
Every queue is a pure function of the folder: the same files give the same items, in
the same order, and nothing here reads a clock or a network.

Each queue puts first the items where a decision saves most. `ORDER` says how, in one
line for each. A file of items begins with every flagged item.

Standard library only.
"""

import csv
import hashlib
import json
import math
import re
import statistics
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Final, cast

from desk.fill import gate, layers
from desk.fill.layers import Collection, Unfit, canonical

type Row = dict[str, str]
type Item = dict[str, Any]

DESK: Final = 1
QUESTIONS: Final = Path(__file__).resolve().parents[1] / "questions.json"

# The tables of a draft folder, each with the columns it must have. `areas.csv`,
# `oa_to_area.csv`, `aliases.csv` and `name_evidence.csv` are the four files of section 5
# of docs/design/london-data-areas.md, as drafted.
TABLES: Final[Mapping[str, tuple[str, ...]]] = {
    "areas.csv": (
        *("area_id", "slug", "name", "primary_borough"),
        *("seed_record", "review_state", "superseded_by"),
    ),
    "oa_to_area.csv": (
        *("oa21cd", "area_id", "basis", "evidence"),
        *("decided_by", "decided_on", "reason"),
    ),
    "aliases.csv": ("alias", "area_id", "kind", "source_id", "record_id"),
    "name_evidence.csv": (
        *("area_id", "name", "role", "source_id", "record_id", "as_written", "field"),
        *("locates", "data_date", "retrieved_on", "snapshot_sha256", "checked"),
        *("chosen_by", "chosen_on"),
    ),
    "flags.csv": ("queue", "item", "flag"),
    "kinds.csv": ("record_id", "source_id", "kind", "name", "category", "upstream"),
    "figures.csv": ("area_id", "feature_id", "value", "unit", "source_id", "vintage", "flag"),
    "figures_before.csv": ("area_id", "feature_id", "value"),
    "commons.csv": ("name", "record_id", "match", "kind", "way_in"),
    "rubrics.csv": ("vibe", "rubric"),
    # The map of areas to articles: docs/design/london-data-researcher.md, section 4, step 1.
    "area_sources.csv": ("area_id", "source_id", "qid", "page_id", "title", "role"),
    # What a draft says beside an item, in words: every doubt it has. A line with no
    # source is the draft's own work.
    "lines.csv": ("queue", "item", "label", "value", "source_id"),
    # The order a draft would have a person look in: each area by its id under `borders`,
    # and each borough by its group under `whole`, the most at stake first, from 1.
    "order.csv": ("queue", "item", "rank"),
    # A rule that would settle items with no person reading each: what it says, what could
    # go wrong, and what it gives an item it fits. `gives` is `proposed` for the answer
    # the draft proposes, an answer of the queue, or nothing, for a border that is left
    # as drafted. A rule settles only what no rule before it settles. `leans_on` names
    # the rules a rule leans on, with a space between them: it settles an item only where
    # the one of them that the item names is adopted too.
    "rules.csv": ("rule", "queue", "gives", "says", "goes_wrong", "leans_on"),
    "rules_items.csv": ("rule", "queue", "item", "leans_on"),
    # What a draft has the desk mark on the map of an item, a row for each mark. `kind`
    # says what `what` is: `cell` for the code of a cell of the item that is in doubt,
    # `side` for two codes, the cell of the item and the cell beside it, where a border
    # follows no line, `seed` for the area whose seed stands close, and `centre` for the
    # name of a town centre, as its file writes it. `flag` is the flag the mark is of.
    "marks.csv": ("queue", "item", "flag", "kind", "what"),
}
SAID: Final = "lines.csv"
PLACED: Final = "order.csv"
MARKED: Final = "marks.csv"
# The kinds of mark, each with the key of an item's marks that holds it, and the queues
# whose maps are marked.
CELL, SIDE, SEED, CENTRE = "cell", "side", "seed", "centre"
KINDS: Final[Mapping[str, str]] = {
    CELL: "cells",
    SIDE: "sides",
    SEED: "seeds",
    CENTRE: "centres",
}
MAY_BE_MARKED: Final = ("borders",)
# The rules a draft puts to the founder, and the items each would settle. None is adopted
# until the founder says yes at the desk.
RULES_PUT, RULED = "rules.csv", "rules_items.csv"
# Columns a table may have beside its own. `label` is the measure in words.
MAY_HAVE: Final[Mapping[str, tuple[str, ...]]] = {"figures.csv": ("label",)}
# The files of lines, each with the keys a line must have.
LINES: Final[Mapping[str, tuple[str, ...]]] = {
    "sentences.jsonl": ("page_id", "revision_id", "title", "section", "sentence", "text"),
    "claim_sentences.jsonl": ("page_id", "revision_id", "title", "section", "sentence", "text"),
    "claims.jsonl": (
        *("claim_id", "area_id", "kind", "quote", "thing", "source_id", "title", "url"),
        *("page_id", "revision_id", "section", "has_reference", "review"),
    ),
}
# The source of a file that has no column for one, and the use each file is read under.
# A sample of venues is read under `scoring`, which the design asks the registry's owner
# to confirm. A table with no entry is Burro's own work, and is asked about nowhere.
WIKIPEDIA: Final = "wikimedia-wikipedia-excerpts"
GREENSPACE: Final = "os-open-greenspace"
OWN: Final = "burro"
SOURCE_OF: Final[Mapping[str, str]] = {
    "sentences.jsonl": WIKIPEDIA,
    "claim_sentences.jsonl": WIKIPEDIA,
    "commons.csv": GREENSPACE,
}
USE_OF: Final[Mapping[str, str]] = {
    SAID: gate.GAZETTEER,
    "aliases.csv": gate.GAZETTEER,
    "name_evidence.csv": gate.GAZETTEER,
    "area_sources.csv": gate.GAZETTEER,
    "kinds.csv": gate.SCORING,
    "figures.csv": gate.SCORING,
    "commons.csv": gate.SCORING,
    "claims.jsonl": gate.PROFILE_TEXT,
    "sentences.jsonl": gate.PROFILE_TEXT,
    "claim_sentences.jsonl": gate.PROFILE_TEXT,
}

# The queues, in the order of the work, each with the files it cannot be filled without,
# the files it reads if they are there, and whether it reads the layers.
QUEUES: Final[Mapping[str, tuple[tuple[str, ...], tuple[str, ...], bool]]] = {
    "rules": (
        (RULES_PUT, RULED),
        ("areas.csv", "name_evidence.csv", "aliases.csv", "oa_to_area.csv", "flags.csv", SAID),
        False,
    ),
    "know": (("areas.csv",), (), True),
    "kinds": (("kinds.csv",), (), False),
    "commons": (("commons.csv",), (), False),
    "figures": (("figures.csv", "areas.csv"), ("figures_before.csv",), True),
    "sentences": (("sentences.jsonl",), (), False),
    "names": (
        ("areas.csv", "name_evidence.csv"),
        ("aliases.csv", "flags.csv", SAID, PLACED, RULES_PUT, RULED),
        True,
    ),
    "borders": (
        ("areas.csv", "oa_to_area.csv"),
        ("flags.csv", SAID, PLACED, RULES_PUT, RULED, MARKED),
        True,
    ),
    "whole": (("areas.csv", "oa_to_area.csv"), ("flags.csv", SAID, PLACED), True),
    "ratings": (("areas.csv", "rubrics.csv"), (), True),
    "articles": (("area_sources.csv", "areas.csv"), ("flags.csv",), False),
    "claims": (("claims.jsonl",), ("areas.csv", "flags.csv", "claim_sentences.jsonl"), False),
}
# How each queue is put in order. A line a person can read. A queue that is read a part
# at a time, so that a part is finished, puts its flagged items first within the part.
ORDER: Final[Mapping[str, str]] = {
    "rules": "As the draft puts them: a rule settles only what no rule before it settles.",
    "claims": "Area by area, so that an area is finished and can ship. Flagged first in each.",
    "borders": "Borough by borough, the most at stake first. In each: flagged first, then "
    "the most at stake, the most flags, the least margin.",
    "names": "Borough by borough, the most at stake first. In each: names proposed as "
    "areas, then other names, and in both flagged first, then the most at stake.",
    "whole": "Flagged first. Then the most at stake, then the most flagged areas.",
    "sentences": "Article by article, in the order the sentences are read.",
    "ratings": "Area by area, so that the map stays still while every vibe is rated.",
    "articles": "Area by area: the area's own article, then those of its other names and "
    "its things. Flagged first in each.",
    "figures": "A figure with no evidence, then one that moved, then one far from its "
    "neighbours, then a zero where cover is thin.",
    "kinds": "The kinds the first look found in doubt, then each kind's doubtful records.",
    "know": "By name.",
    "commons": "A place with no match, then one with no name or no way in, then the rest.",
}

# The pace of the design, section 1: the seconds each takes, and whether that is for an
# item or for a group of items. A sentence is read an article at a time. Nobody has
# timed any of them, and the pace of a rule is a guess of the desk's own.
ITEM, GROUP = "item", "group"
PACE: Final[Mapping[str, tuple[int, str]]] = {
    "rules": (2 * 60, ITEM),
    "know": (5, ITEM),
    "kinds": (6, ITEM),
    "commons": (60, ITEM),
    "figures": (15, ITEM),
    "sentences": (12 * 60, GROUP),
    "names": (45, ITEM),
    "borders": (8 * 60, ITEM),
    "whole": (15 * 60, ITEM),
    "ratings": (10, ITEM),
    "articles": (20, ITEM),
    "claims": (25, ITEM),
}

# The queues whose answer is about the ground: a border, a borough, an outline to rate.
# Their revision is made from the cells and what placed them, and not from a name, so
# that a name respelt reopens no answer about the ground.
DECIDED_ON_THE_GROUND: Final = ("borders", "whole", "ratings")

# Names: the tiers of docs/design/london-data-areas.md, section 2, in words.
PRIMARY, ALIAS, WIDE = "primary", "alias", "wide"
# What a draft says of an area whose name stands by a rule the founder has decided
# already, as `review_state`. Its name is put to nobody, and its border is asked about.
NAMED_BY_RULE: Final = "named_by_rule"
# The answer that keeps a name proposed as an area.
AREA: Final = "area"
# Rules: the queues whose items a rule may settle, what a rule gives an item in place of
# an answer of the queue, and how many of the items it would settle are shown.
MAY_BE_RULED: Final = ("names", "borders")
PROPOSED, AS_DRAFTED = "proposed", ""
FITS: Final = "fits"
# The rule that an item leans on, where the rule that fits it leans on others. On the
# item of a rule, every rule it leans on.
LEANS_ON: Final = "leans_on"
# The items of a rule that are shown with it, by their ids, for the page to open each.
DRAWN: Final = "drawn"
# The label of what a draft says the founder has decided already of a rule. It is shown
# under what the rule would settle, which it explains: the rest of what a draft says of a
# rule is shown before the items that are drawn.
ALREADY_DECIDED: Final = "Already decided"
MOST_DRAWN: Final = 10
# What an area holds that the desk cannot take from under it: the cells drafted to it,
# or another name that is given to it. An answer that turns the name of such an area
# down is saved, and the step that makes a build's files sets it aside.
HOLDS, CELLS, OTHER_NAMES = "holds", "cells", "names"
TIERS: Final[Mapping[str, str]] = {
    "same_ground": "Another name for",
    "inside": "A smaller place inside",
    "wide": "A wider name, over",
}
LOCATES: Final[Mapping[str, str]] = {
    "point_inside": "a point inside",
    "polygon_overlap": "a shape that overlaps",
    "label_only": "a label, with no place",
    "none": "no place given",
}
MOST_PICKS: Final = 5
MOST_WIDE: Final = 5
# How many lines of evidence the desk makes for an item by itself. A draft may say more
# in `lines.csv`: what is known of an item scrolls.
MOST_LINES: Final = 6
# What stands before the name of an area that lies beside the one a figure is of.
BESIDE: Final = "Beside it"
UNDER: Final = 10
# From this margin, in hundredths, the second choice is said to be so many times as far.
# The most a draft writes a margin as: it does not say how much further.
AS_FAR, MOST_MARGIN = 100, 999

# Figures: the four rules, in the order their items are put in. Each is one line in
# questions.json. The first and the last are what the pipeline's own reports say of a
# figure, read from the column `flag` and never worked out again here.
NO_EVIDENCE, MOVED, FAR, ZERO = (
    "no_evidence",
    "moved_between_releases",
    "far_from_neighbours",
    "zero_thin_cover",
)
RULES: Final = (NO_EVIDENCE, MOVED, FAR, ZERO)
# What the coverage report says where no row of evidence stands behind a figure, and the
# findings of `check` that say the same of a fact.
SAYS_NO_EVIDENCE: Final = frozenset(
    {"no_record", "fact_has_a_row", "row_has_a_value", "source_has_a_file", "input_is_locked"}
)
# The state the coverage report gives a figure that covers less than the whole area.
SAYS_THIN: Final = "partial"
# "Moved by a fifth or more": docs/research/data/overture-places.md.
A_FIFTH: Final = 0.2
# A figure is compared with its neighbours only where this many have one.
ENOUGH_NEIGHBOURS: Final = 2
ENOUGH_AREAS: Final = 8

# Kinds: what the first look at Overture Places found, docs/research/data/overture-places.md.
# "Half the records under theatre are stage schools by their names. Half the community
# halls are scout groups from one feed." "Counts of hospitals, universities and stations
# are not believable", because one institution has many records.
GIVES_AWAY: Final[Mapping[str, tuple[str, ...]]] = {
    "theatre": ("school", "schools"),
    "community_hall": ("scout", "scouts"),
}
MANY_RECORDS: Final = ("hospital", "university", "station")
IN_DOUBT: Final = (*GIVES_AWAY, *MANY_RECORDS)
ANOTHER_KIND, REPEATS, TWO_KINDS = "name_says_another_kind", "one_of_many_records", "in_two_kinds"
# To say how often a kind holds what it says to within ten points in a hundred, nineteen
# times in twenty, whatever the share turns out to be: 1.96 squared, times a half squared,
# over a tenth squared. A kind with fewer records needs fewer.
WITHIN, SURE = 0.10, 1.96
WORST_CASE: Final = SURE**2 * 0.25 / WITHIN**2

NO_MATCH, NO_NAME, NO_WAY_IN = "no_match", "no_name", "no_way_in"
# Names: a name that may say who lives there. The areas design puts each to the founder.
DESCRIBES_RESIDENTS: Final = "describes_residents"
# Articles: whose article a row of the map says it is, in words, in the order they are
# read. The answer that keeps a row is the one the map proposes.
ROLES: Final[Mapping[str, str]] = {
    "own": "The article about the area itself",
    "alias": "The article about another name of the area",
    "thing": "The article about a thing in the area",
}
ITS_ARTICLE: Final = "its_article"
YES: Final = frozenset({"yes", "true", "1"})
PENDING: Final = "pending"

# What a row of `oa_to_area.csv` may say placed a cell, as `key=value` parted by `;`:
# the margin in hundredths, the second choice, and the names that the roads, the ward,
# the MSOA and the town centre give. It is all that stands beside a border: rule 8 of
# AGENTS.md, and section 6 of the design. A key that is not here is refused, so no
# figure about who lives somewhere can ride in as evidence.
EVIDENCE: Final[Mapping[str, str]] = {
    "margin": "margin {}%",
    "second": "second choice {}",
    "roads": "its roads say {}",
    "ward": "its ward is {}",
    "msoa": "its MSOA is named {}",
    "centre": "its town centre is {}",
}
# The table of cells is Burro's own work, and the margin and the second choice are worked
# out by Burro. A name in the evidence is its publisher's: the source each comes from,
# which the licence gate is asked about before the name is shown beside a border.
EVIDENCE_SOURCE: Final[Mapping[str, str]] = {
    "roads": "os-open-roads",
    "ward": "os-boundary-line",
    "msoa": "hoc-library-msoa-names",
    "centre": "gla-town-centre-boundaries",
}

# Rule 8 of AGENTS.md, and section 6 of the design: what may never stand beside a name, a
# border or a vibe. Each is looked for as a whole word. A rubric, the label of a line and
# a name in the evidence of a cell are held to it. The name of a place is not: a place
# may be named for a word on the list, and the founder reads every name.
DRAWS_A_MAP: Final = ("names", "borders", "whole", "ratings", "know")
ABOUT_RESIDENTS: Final = (
    *("residents?", "population", "people", "households?", "aged", "ethnic\\w*", "religio\\w+"),
    *("born", "incomes?", "depriv\\w+", "crimes?", "burglar\\w+", "prices?", "rents?", "census"),
    *("tenure", "students?", "famil\\w+", "professionals?", "retired", "pensioners?"),
    *("migrants?", "immigra\\w+", "wealthy", "affluent"),
)
_ABOUT_RESIDENTS: Final = re.compile(rf"\b(?:{'|'.join(ABOUT_RESIDENTS)})\b")


def about_residents(text: str) -> bool:
    """Whether words hold a word about who lives somewhere, a price or a crime."""
    return _ABOUT_RESIDENTS.search(text.casefold()) is not None


def sample_size(records: int) -> int:
    """How many of a kind's records a person reads, to be right to within ten in a hundred."""
    if records <= 0:
        return 0
    return min(records, math.ceil(WORST_CASE / (1 + (WORST_CASE - 1) / records)))


def slug(name: str) -> str:
    """A name in lower case with hyphens, as the areas design gives a slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")


def in_words(code: str) -> str:
    return code.replace("_", " ")


def revision(item: Mapping[str, Any]) -> str:
    """The first 12 hex digits of the SHA-256 of an item without `rev`, keys sorted."""
    bare = {key: value for key, value in item.items() if key != "rev"}
    return hashlib.sha256(canonical(bare).encode("utf-8")).hexdigest()[:12]


def _draw(*parts: str) -> str:
    """A fixed shuffle: the same records are drawn for the same data."""
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def plain(value: float) -> str:
    """A number as a person writes it: no exponent, and no zeros after the point."""
    return format(value, ".12g") if abs(value) < 1e12 else format(value, ".0f")


def _number(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


# Reading and writing a draft


def write_table(folder: Path, name: str, rows: Iterable[Mapping[str, object]]) -> None:
    """Write one table of a draft, with its columns in the order the design gives them."""
    columns = (*TABLES[name], *MAY_HAVE.get(name, ()))
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / name).open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def write_lines(folder: Path, name: str, rows: Iterable[Mapping[str, object]]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    text = "".join(canonical(row) + "\n" for row in rows)
    (folder / name).write_text(text, encoding="utf-8")


def read_table(folder: Path, name: str) -> list[Row]:
    """The rows of one table. Raises `Unfit`, which names the file and never a value."""
    try:
        with (folder / name).open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file, strict=True)
            columns = tuple(reader.fieldnames or ())
            rows = [dict(row) for row in reader]
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise Unfit(f"{name} cannot be read as a table") from error
    known = {*TABLES[name], *MAY_HAVE.get(name, ())}
    if not set(TABLES[name]) <= set(columns) or not set(columns) <= known:
        raise Unfit(f"{name} does not have the columns of the design: {', '.join(TABLES[name])}")
    if any(None in row or None in row.values() for row in rows):
        raise Unfit(f"{name} holds a row that is longer or shorter than its first line")
    return rows


def read_lines(folder: Path, name: str) -> list[dict[str, Any]]:
    """The lines of one file of JSON lines. Raises `Unfit`."""
    try:
        raw = (folder / name).read_text(encoding="utf-8")
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    except (OSError, ValueError) as error:
        raise Unfit(f"{name} cannot be read as lines of JSON") from error
    for row in rows:
        if not isinstance(row, dict) or not set(LINES[name]) <= set(cast(dict[str, Any], row)):
            raise Unfit(f"{name} holds a line without the keys: {', '.join(LINES[name])}")
    return cast(list[dict[str, Any]], rows)


@dataclass(frozen=True)
class Draft:
    """One draft folder, read once. What is worked out from it is kept for every queue."""

    folder: Path
    synthetic: bool
    drawn: Mapping[tuple[str, str], Collection] = field(default_factory=dict[Any, Any])
    # The licence registry, which says who publishes a source. None is this repository's.
    registry: Path | None = None

    @classmethod
    def open(cls, folder: Path, *, synthetic: bool, registry: Path | None = None) -> "Draft":
        drawn = layers.read_all(folder / "layers", synthetic=synthetic)
        return cls(folder, synthetic, drawn, registry)

    def has(self, name: str) -> bool:
        return (self.folder / name).is_file()

    def table(self, name: str) -> list[Row]:
        """The rows of a table, read once. A table the draft does not hold has no rows."""
        if name not in self._tables:
            self._tables[name] = read_table(self.folder, name) if self.has(name) else []
        return self._tables[name]

    def lines(self, name: str) -> list[dict[str, Any]]:
        if name not in self._lines:
            self._lines[name] = read_lines(self.folder, name) if self.has(name) else []
        return self._lines[name]

    def digest(self, name: str) -> str:
        if name not in self._digests:
            self._digests[name] = hashlib.sha256((self.folder / name).read_bytes()).hexdigest()
        return self._digests[name]

    @cached_property
    def _tables(self) -> dict[str, list[Row]]:
        return {}

    @cached_property
    def _lines(self) -> dict[str, list[dict[str, Any]]]:
        return {}

    @cached_property
    def _digests(self) -> dict[str, str]:
        return {}

    def in_words(self, source_id: str) -> str:
        """A source as a person reads it: its publisher, and what it is called."""
        if source_id not in self._words:
            self._words[source_id] = gate.in_words(
                source_id, synthetic=self.synthetic, registry=self.registry
            )
        return self._words[source_id]

    @cached_property
    def _words(self) -> dict[str, str]:
        return {}

    def sources_of(self, name: str) -> list[str]:
        """The sources a file of the draft names, or the one the design gives it."""
        if name == SAID:
            # A line with no source is the draft's own work, and is asked about nowhere.
            return sorted({row["source_id"] for row in self.table(name)} - {""})
        if name in TABLES and "source_id" in TABLES[name]:
            return sorted({row["source_id"] for row in self.table(name)})
        if name == "claims.jsonl":
            return sorted({str(row["source_id"]) for row in self.lines(name)})
        if self.synthetic:
            return [gate.MADE_UP]
        return [SOURCE_OF.get(name, OWN)]

    # Areas

    @cached_property
    def areas(self) -> dict[str, Row]:
        """Every area that stands, by id. An area that another took the place of is left out."""
        return {
            row["area_id"]: row
            for row in self.table("areas.csv")
            if row["area_id"] and not row["superseded_by"]
        }

    def named(self, area_id: str) -> str:
        return self.areas[area_id]["name"] if area_id in self.areas else area_id

    def group_of(self, area_id: str) -> str:
        return slug(self.areas[area_id]["primary_borough"]) or layers.ALL

    @cached_property
    def boroughs(self) -> dict[str, str]:
        """Every borough, by the name of its group."""
        names = {row["primary_borough"] for row in self.areas.values() if row["primary_borough"]}
        return {slug(name): name for name in sorted(names)}

    def flags(self, queue: str, item: str) -> list[str]:
        return self._flags.get((queue, item), [])

    @cached_property
    def said(self) -> dict[str, dict[str, list[dict[str, str]]]]:
        """What the draft says beside each item, by queue and then by item, in the order
        of its file. Raises `Unfit` for a line of no queue, or with no label or no words."""
        held: dict[str, dict[str, list[dict[str, str]]]] = {}
        for row in self.table(SAID):
            if row["queue"] not in QUEUES:
                raise Unfit(f"{SAID} names a queue the desk does not have")
            if not (row["item"] and row["label"].strip() and row["value"].strip()):
                raise Unfit(f"{SAID} holds a line with no label or no words, or of no item")
            lines = held.setdefault(row["queue"], {}).setdefault(row["item"], [])
            lines.append(_line(row["label"], row["value"], row["source_id"]))
        return held

    @cached_property
    def places(self) -> dict[str, dict[str, int]]:
        """The place a draft gives each item of a queue, from 1: the most at stake first.
        Raises `Unfit` for a place that is no number, and for an item placed twice."""
        held: dict[str, dict[str, int]] = {}
        for row in self.table(PLACED):
            if row["queue"] not in QUEUES:
                raise Unfit(f"{PLACED} names a queue the desk does not have")
            if not (row["rank"].isascii() and row["rank"].isdigit() and int(row["rank"]) > 0):
                raise Unfit(f"{PLACED} gives a place that is no whole number from 1")
            if row["item"] in held.setdefault(row["queue"], {}):
                raise Unfit(f"{PLACED} places an item twice")
            held[row["queue"]][row["item"]] = int(row["rank"])
        return held

    @cached_property
    def marks(self) -> dict[str, dict[str, dict[str, Any]]]:
        """What the draft has the desk mark on the map of each item, by queue and then by
        item: the cells in doubt with the flags each is under, the sides that follow no
        line, the seeds that stand close, and the town centres a flag names.

        Raises `Unfit`, which names the file and never a value, for a mark of a queue
        whose maps are not marked, of no kind the design gives, on a cell of another
        area, on a side that is not between the item and another area, on the seed of
        no other area, or on a town centre with no name.
        """
        held: dict[str, dict[str, dict[str, Any]]] = {}
        for row in self.table(MARKED):
            queue, item, kind, what = row["queue"], row["item"], row["kind"], row["what"]
            if queue not in MAY_BE_MARKED or not row["flag"]:
                raise Unfit(f"{MARKED} names a queue that marks no map, or a mark of no flag")
            if kind not in KINDS:
                raise Unfit(f"{MARKED} holds a kind of mark that is none of: {', '.join(KINDS)}")
            marks = held.setdefault(queue, {}).setdefault(
                item, {"cells": {}, "sides": [], "seeds": [], "centres": []}
            )
            if kind == CELL:
                if self._area_of(what) != item:
                    raise Unfit(f"{MARKED} marks a cell of another area than the item's")
                flags = marks["cells"].setdefault(what, [])
                flags += [row["flag"]] if row["flag"] not in flags else []
                continue
            if kind == SIDE:
                pair = what.split()
                own = len(pair) == 2 and self._area_of(pair[0]) == item
                if not own or self._area_of(pair[1]) in ("", item):
                    raise Unfit(
                        f"{MARKED} marks a side that is not between a cell of the item "
                        "and a cell of another area"
                    )
            if kind == SEED and (what == item or what not in self.areas):
                raise Unfit(f"{MARKED} marks the seed of no other area of the draft")
            if kind == CENTRE and not what.strip():
                raise Unfit(f"{MARKED} marks a town centre with no name")
            mark: Any = what.split() if kind == SIDE else what
            if mark not in marks[KINDS[kind]]:
                marks[KINDS[kind]].append(mark)
        return held

    def _area_of(self, cell: str) -> str:
        """The area a cell is given to. Nothing for a cell the draft does not hold."""
        row = self.membership.get(cell) if self.has("oa_to_area.csv") else None
        return row["area_id"] if row else ""

    def marked(self, queue: str, item: str) -> dict[str, Any]:
        """The marks of an item, as its map holds them: only the kinds it has any of."""
        marks = self.marks.get(queue, {}).get(item, {})
        return {kind: held for kind, held in marks.items() if held}

    def place_of(self, queue: str, item: str) -> float:
        """Where the draft would have an item looked at. What it does not place comes
        after all that it does."""
        return self.places.get(queue, {}).get(item, math.inf)

    def place_of_borough(self, group: str) -> tuple[float, str]:
        """Where a borough comes: the most at stake first, and then by name. Every item
        of a borough is read before the next borough begins."""
        return self.place_of("whole", group), group

    @cached_property
    def rules(self) -> dict[str, Row]:
        """Every rule the draft puts to the founder, by its code, in the order it puts
        them. Raises `Unfit` for a rule that is not as the design gives one."""
        held: dict[str, Row] = {}
        asked = answers_of()
        for row in self.table(RULES_PUT):
            if not (row["rule"] and row["says"].strip() and row["goes_wrong"].strip()):
                raise Unfit(
                    f"{RULES_PUT} puts a rule with no words, or without what could go wrong"
                )
            if row["rule"] in held or not re.fullmatch(r"[a-z][a-z0-9_]*", row["rule"]):
                raise Unfit(f"{RULES_PUT} puts a rule twice, or one whose code is no code")
            if row["queue"] not in MAY_BE_RULED:
                raise Unfit(f"{RULES_PUT} puts a rule to a queue that no rule may settle")
            if row["queue"] == "borders" and row["gives"] != AS_DRAFTED:
                raise Unfit(
                    f"{RULES_PUT} gives an answer to a border. A rule may only leave one as "
                    "drafted: whether a border is right is for a person to say"
                )
            if row["queue"] != "borders" and row["gives"] not in (PROPOSED, *asked[row["queue"]]):
                raise Unfit(f"{RULES_PUT} gives an answer that is none of the queue's")
            for other in row[LEANS_ON].split():
                # A rule leans on a rule that stands by itself, and was put before it.
                stands = other in held and not held[other][LEANS_ON]
                if not stands or held[other]["queue"] != row["queue"]:
                    raise Unfit(
                        f"{RULES_PUT} has a rule lean on one that is not put before it for "
                        "the same queue, or that leans on another"
                    )
            held[row["rule"]] = row
        return held

    def leans_on(self, rule: str) -> tuple[str, ...]:
        """The rules a rule leans on, in the order the draft names them."""
        return tuple(dict.fromkeys(self.rules[rule][LEANS_ON].split()))

    @cached_property
    def ruled(self) -> dict[str, dict[str, str]]:
        """The rule that would settle each item, by queue and then by item. Raises `Unfit`
        for an item given to two rules, and for a rule the draft does not put."""
        held: dict[str, dict[str, str]] = {}
        for row in self.table(RULED):
            if row["rule"] not in self.rules:
                raise Unfit(f"{RULED} names a rule that {RULES_PUT} does not hold")
            if row["queue"] != self.rules[row["rule"]]["queue"]:
                raise Unfit(f"{RULED} gives a rule an item of another queue than its own")
            if row["item"] in held.setdefault(row["queue"], {}):
                raise Unfit(f"{RULED} gives an item to two rules")
            held[row["queue"]][row["item"]] = row["rule"]
        return held

    @cached_property
    def leaning(self) -> dict[str, dict[str, str]]:
        """The rule each item leans on, by queue and then by item, for the items of a rule
        that leans on others. Raises `Unfit` for an item of such a rule that names none
        of the rules it leans on, and for an item of any other rule that names one."""
        held: dict[str, dict[str, str]] = {}
        for row in self.table(RULED):
            may = self.leans_on(row["rule"]) if row["rule"] in self.rules else ()
            if (row[LEANS_ON] or may) and row[LEANS_ON] not in may:
                raise Unfit(
                    f"{RULED} holds an item that leans on a rule its own rule does not lean "
                    "on, or that names none where its rule leans on others"
                )
            if row[LEANS_ON]:
                held.setdefault(row["queue"], {})[row["item"]] = row[LEANS_ON]
        return held

    def fits(self, queue: str, item: str) -> dict[str, str]:
        """The rule that would settle an item, as the item's preset holds it, and the
        rule the item leans on where that rule leans on others."""
        rule = self.ruled.get(queue, {}).get(item)
        other = self.leaning.get(queue, {}).get(item)
        return {} if not rule else {FITS: rule, LEANS_ON: other} if other else {FITS: rule}

    def made(self, queue: str) -> list[Item]:
        """The items of a queue, made once: the rules show items of other queues."""
        if queue not in self._made:
            self._made[queue] = MAKERS[queue](self)
        return self._made[queue]

    @cached_property
    def _made(self) -> dict[str, list[Item]]:
        return {}

    def laid(
        self, queue: str, item: str, own: Sequence[Mapping[str, str]]
    ) -> Sequence[Mapping[str, str]]:
        """The lines of an item: the desk's first line, and under it what the draft says.
        Where the draft says nothing of the item, the desk's own lines."""
        theirs = self.said.get(queue, {}).get(item)
        return own if not theirs else [*own[:1], *theirs]

    @cached_property
    def _flags(self) -> dict[tuple[str, str], list[str]]:
        held: dict[tuple[str, str], list[str]] = {}
        for row in self.table("flags.csv"):
            flags = held.setdefault((row["queue"], row["item"]), [])
            if row["flag"] and row["flag"] not in flags:
                flags.append(row["flag"])
        return held

    # Cells

    @cached_property
    def cells(self) -> dict[str, Mapping[str, Any]]:
        """Every cell that is drawn, once, whichever boroughs it is drawn for."""
        held: dict[str, Mapping[str, Any]] = {}
        for (_, layer), collection in sorted(self.drawn.items()):
            if layer == "cells":
                for feature in collection["features"]:
                    held.setdefault(feature["id"], feature)
        return held

    @cached_property
    def membership(self) -> dict[str, Row]:
        """The row of every cell, by its code. A cell has one row, and names an area."""
        rows = self.table("oa_to_area.csv")
        held = {row["oa21cd"]: row for row in rows}
        if len(held) != len(rows) or "" in held:
            raise Unfit("oa_to_area.csv holds a cell twice, or a row with no cell")
        if any(row["area_id"] not in self.areas for row in rows):
            raise Unfit("oa_to_area.csv names an area that areas.csv does not hold")
        for row in rows:
            # Every row is held to it, and not only the rows of the cells that are shown.
            evidence_of(row)
        for code, cell in self.cells.items():
            drawn_in = cell["properties"].get("area", "")
            if drawn_in != (held[code]["area_id"] if code in held else ""):
                raise Unfit(
                    "The cells that are drawn and oa_to_area.csv do not agree. "
                    "Make the layers again, from the same draft"
                )
        return held

    @cached_property
    def cells_of(self) -> dict[str, list[str]]:
        """The cells of each area, in the order of their codes."""
        held: dict[str, list[str]] = {area_id: [] for area_id in self.areas}
        for code in sorted(self.membership):
            held[self.membership[code]["area_id"]].append(code)
        return held

    @cached_property
    def beside(self) -> dict[str, set[str]]:
        return layers.touching(self.cells.values())

    @cached_property
    def neighbours(self) -> dict[str, list[str]]:
        """The areas each area shares a side of a cell with."""
        held: dict[str, set[str]] = {area_id: set() for area_id in self.areas}
        for code, others in self.beside.items():
            if code in self.membership:
                here = self.membership[code]["area_id"]
                there = {
                    self.membership[other]["area_id"]
                    for other in others
                    if other in self.membership
                }
                held[here].update(there - {here})
        return {area_id: sorted(others) for area_id, others in held.items()}

    def border_cells(self, area_id: str) -> list[str]:
        """The cells of an area that have a cell of another area beside them."""
        return [
            code
            for code in self.cells_of[area_id]
            if any(
                other in self.membership and self.membership[other]["area_id"] != area_id
                for other in self.beside.get(code, ())
            )
        ]

    # Maps

    def map_of(
        self,
        group: str,
        focus: object,
        around: Iterable[Mapping[str, Any]],
        marks: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """What the page draws for an item, or nothing where the draft has no layer for it.

        `focus` is what the item is about: the id of an area or of a borough, a list of
        such ids, or an area with the point a record puts a name at. The boroughs are
        drawn behind every borough's own layers, and the page takes them from `all`.
        `marks` is what the draft has the desk mark on the map, where it marks anything.
        """
        drawn = {layer for (held_in, layer) in self.drawn if held_in in (group, layers.ALL)}
        box = layers.bounds(around, margin=0.2)
        if not drawn or box is None:
            return None
        return {
            "bbox": box,
            "focus": focus,
            "layers": [layer for layer in layers.LAYERS if layer in drawn],
            **({"marks": dict(marks)} if marks else {}),
        }

    @cached_property
    def placed(self) -> dict[str, list[float]]:
        """Where each record puts its name, by the record's id.

        A draft may draw no layer of records, and draw a publisher's record of a name as
        a point of the layer of names, under the record's own id. It is found there too.
        A point of the layer of records stands before one of the layer of names.
        """
        return {
            feature["id"]: list(feature["geometry"]["coordinates"][:2])
            for among in ("names", "records")
            for (_, layer), collection in sorted(self.drawn.items())
            if layer == among
            for feature in collection["features"]
        }

    def about(self, area_id: str, rows: Iterable[Row]) -> dict[str, Any]:
        """An area, and the first point that a record of the name gives."""
        at = next(
            (self.placed[row["record_id"]] for row in rows if row["record_id"] in self.placed), None
        )
        return {"area": area_id} if at is None else {"area": area_id, "at": at}

    def shapes_of(self, area_id: str) -> list[Mapping[str, Any]]:
        """What an area is drawn from: its outline where there is one, or else its cells."""
        outline = self.drawn.get((self.group_of(area_id), "areas"))
        found = [
            each for each in (outline or {"features": []})["features"] if each["id"] == area_id
        ]
        return found or [self.cells[code] for code in self.cells_of_drawn(area_id)]

    def cells_of_drawn(self, area_id: str) -> list[str]:
        if not self.has("oa_to_area.csv"):
            return []
        return [code for code in self.cells_of.get(area_id, []) if code in self.cells]


# Items


def _line(label: str, value: str, source_id: str = "") -> dict[str, str]:
    return {"label": label, "value": value, "source_id": source_id}


def _item(
    draft: Draft,
    name: str,
    group: str,
    title: str,
    *,
    queue: str = "",
    lines: Sequence[Mapping[str, str]] = (),
    more: Sequence[Mapping[str, str]] = (),
    text: Mapping[str, str] | None = None,
    drawn: Mapping[str, Any] | None = None,
    picks: Sequence[str] | None = None,
    flags: Sequence[str] = (),
    fill: Mapping[str, str] | None = None,
    preset: Mapping[str, Any] | None = None,
    ground: Mapping[str, Any] | None = None,
) -> Item:
    """An item, with the fields of the design and no other. A made-up item says that it is.

    `ground` is what an answer about the ground was given on: the cells, and what placed
    each. Where it is given the revision is made from it, with the item's id and flags,
    and from no name and no word that is shown.

    `queue` names the queue of an item that a draft may say more of, in `lines.csv`.
    `more` is what the desk says under that, whatever the draft says.
    """
    said = draft.laid(queue, name, lines) if queue else lines
    item: Item = {
        "id": name,
        "group": group or layers.ALL,
        "title": f"{title} (made up)" if draft.synthetic else title,
        "lines": [dict(line) for line in (*said, *more)],
        "text": None if text is None else dict(text),
        "map": None if drawn is None else dict(drawn),
        "picks": None if picks is None else list(picks),
        "flags": list(flags),
        "fill": dict(fill or {}),
        "preset": dict(preset or {}),
    }
    about = {"id": name, "flags": list(flags), "fill": item["fill"], "ground": ground}
    item["rev"] = revision(item if ground is None else about)
    return item


def _area_title(draft: Draft, area_id: str) -> str:
    borough = draft.areas[area_id]["primary_borough"]
    return f"{draft.named(area_id)}, {borough}" if borough else draft.named(area_id)


# Names


def _evidence_line(draft: Draft, row: Row) -> dict[str, str]:
    """A record, under the name of its publisher. The page names the source after it."""
    where = LOCATES.get(row["locates"], row["locates"] or LOCATES["none"])
    record = f" Record {row['record_id']}." if row["record_id"] else ""
    said = f"{row['as_written']}. It gives {where}.{record}"
    return _line(draft.in_words(row["source_id"]), said, row["source_id"])


def _as_written(draft: Draft, rows: Iterable[Row]) -> list[dict[str, str]]:
    """A line for each publisher's way of writing a name. A name over several areas has a
    record for each, and is said once."""
    said: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (row["source_id"], row["as_written"], row["locates"])
        said.setdefault(key, _evidence_line(draft, row))
    return list(said.values())


def _spellings(chosen: str, rows: Iterable[Row]) -> list[str]:
    """The spelling the draft chose, then every other form that a source wrote."""
    others = sorted({row["as_written"] for row in rows if row["as_written"]} - {chosen})
    return [chosen, *others][:MOST_PICKS]


def _stands(draft: Draft, area_id: str) -> bool:
    """Whether the name of an area stands by a rule the founder has decided already, and
    is put to nobody. The draft says so of the area. A name with any flag is asked about
    whatever the draft says: a flag is a doubt, and a name that may say who lives there
    is put to the founder by the desk's own list of words."""
    area = draft.areas[area_id]
    flagged = _flags_of_a_name(draft, f"n:{area_id}", area["name"])
    return area["review_state"] == NAMED_BY_RULE and not flagged


def stands(draft: Draft) -> list[str]:
    """The areas whose name stands by a rule the founder has decided already, by id.
    The desk makes no item of the name of any of them."""
    return sorted(area_id for area_id in draft.areas if _stands(draft, area_id))


def names(draft: Draft) -> list[Item]:
    evidence: dict[tuple[str, str], list[Row]] = {}
    for row in draft.table("name_evidence.csv"):
        evidence.setdefault((row["area_id"], row["name"]), []).append(row)
    items: list[tuple[tuple[Any, ...], Item]] = []
    given = {row["area_id"] for row in draft.table("aliases.csv")}
    for area_id, area in draft.areas.items():
        if _stands(draft, area_id):
            continue
        rows = [row for row in evidence.get((area_id, area["name"]), []) if row["role"] == PRIMARY]
        name = f"n:{area_id}"
        flags = _flags_of_a_name(draft, name, area["name"])
        holds = _holds(draft, area_id, given)
        fits = draft.fits("names", name)
        item = _item(
            draft,
            name,
            draft.group_of(area_id),
            _area_title(draft, area_id),
            queue="names",
            lines=[_line("Proposed as", "An area"), *_as_written(draft, rows)],
            more=_a_rule_fits(draft, fits, AREA),
            drawn=draft.map_of(
                draft.group_of(area_id), draft.about(area_id, rows), draft.shapes_of(area_id)
            ),
            picks=_spellings(area["name"], rows),
            flags=flags,
            preset={"of": [], "pick": area["name"], "proposed": AREA, **holds, **fits},
        )
        at = (not flags, draft.place_of("borders", area_id), area["name"], name)
        items.append(((*draft.place_of_borough(item["group"]), 0, *at), item))
    for alias, kind, area_ids in _aliases(draft):
        live = [area_id for area_id in area_ids if area_id in draft.areas][:MOST_WIDE]
        if not live:
            continue
        rows = [row for area_id in live for row in evidence.get((area_id, alias), [])]
        rows = [row for row in rows if row["role"] != PRIMARY]
        name = f"a:{live[0]}:{slug(alias)}"
        flags = _flags_of_a_name(draft, name, alias)
        over = ", ".join(draft.named(area_id) for area_id in live)
        shapes = [shape for area_id in live for shape in draft.shapes_of(area_id)]
        borough = draft.areas[live[0]]["primary_borough"]
        fits = draft.fits("names", name)
        proposed = {"proposed": kind} if kind in TIERS else {}
        item = _item(
            draft,
            name,
            draft.group_of(live[0]),
            f"{alias}, {borough}" if borough else alias,
            queue="names",
            lines=[
                _line("Proposed as", f"{TIERS.get(kind, in_words(kind))} {over}"),
                *_as_written(draft, rows),
            ],
            more=_a_rule_fits(draft, fits, proposed.get("proposed", "")),
            drawn=draft.map_of(draft.group_of(live[0]), draft.about(live[0], rows), shapes),
            picks=_spellings(alias, rows),
            flags=flags,
            # The answer the draft proposes, where it is one of the question's.
            preset={"of": live, "pick": alias, **proposed, **fits},
        )
        at = (not flags, draft.place_of("borders", live[0]), alias, name)
        items.append(((*draft.place_of_borough(item["group"]), 1, *at), item))
    return [item for _, item in sorted(items, key=lambda pair: pair[0])]


def _would_be(draft: Draft, rule: Row, proposed: str) -> str:
    """What a rule would make of an item, in words. Raises `Unfit` where the rule gives
    what the draft proposes, and the draft proposes nothing for the item."""
    if rule["gives"] == AS_DRAFTED:
        return "left as drafted, and offered to nobody"
    gives = proposed if rule["gives"] == PROPOSED else rule["gives"]
    if not gives:
        raise Unfit(f"{RULES_PUT} gives what the draft proposes to an item with nothing proposed")
    label = labels_of()[rule["queue"]][gives]
    return f"accepted as proposed: {label}" if rule["gives"] == PROPOSED else f"given: {label}"


def _a_rule_fits(draft: Draft, fits: Mapping[str, str], proposed: str) -> list[dict[str, str]]:
    """The line that says which rule would settle an item, and what the item would be.
    Where the rule leans on another, the line names that rule: both are to be adopted."""
    if not fits:
        return []
    rule = draft.rules[fits[FITS]]
    would_be = _would_be(draft, rule, proposed)
    title = in_words(rule["rule"]).capitalize()
    if LEANS_ON in fits:
        other = in_words(fits[LEANS_ON]).capitalize()
        said = f"{title}. It leans on the rule {other}. If you adopt both in Rules, this is"
        return [_line("A rule fits", f"{said} {would_be}.")]
    return [_line("A rule fits", f"{title}. If you adopt it in Rules, this is {would_be}.")]


def _holds(draft: Draft, area_id: str, given: set[str]) -> dict[str, str]:
    """What an area holds that the desk cannot take from under it, for the page to say
    before a name is turned down. Nothing where it holds nothing."""
    if draft.has("oa_to_area.csv") and draft.cells_of.get(area_id):
        return {HOLDS: CELLS}
    return {HOLDS: OTHER_NAMES} if area_id in given else {}


def _flags_of_a_name(draft: Draft, item: str, name: str) -> list[str]:
    """The flags the draft gives a name, and one more where the name holds a word about
    who lives somewhere. Such a name is kept only where its publisher writes it as the
    name of the place, and each is put to the founder: areas design, section 6."""
    flags = list(draft.flags("names", item))
    if about_residents(name) and DESCRIBES_RESIDENTS not in flags:
        flags.append(DESCRIBES_RESIDENTS)
    return flags


def _aliases(draft: Draft) -> list[tuple[str, str, list[str]]]:
    """Each other name, its kind and the areas it is proposed for. A wide name is one
    item over all its areas. Any other name is an item for each area it is placed in:
    a name that stands inside two areas is asked about in each."""
    held: dict[tuple[str, str, str], list[str]] = {}
    for row in draft.table("aliases.csv"):
        where = "" if row["kind"] == WIDE else row["area_id"]
        areas = held.setdefault((row["alias"], row["kind"], where), [])
        if row["area_id"] not in areas:
            areas.append(row["area_id"])
    return [(alias, kind, areas) for (alias, kind, _), areas in held.items()]


# Borders, and whole boroughs


def evidence_of(row: Row) -> dict[str, str]:
    """What a row of `oa_to_area.csv` says placed the cell: `margin=7;second=lon-n0012`."""
    parts = [part for part in row["evidence"].split(";") if part.strip()]
    pairs = [part.split("=", 1) for part in parts]
    if any(len(pair) != 2 or pair[0].strip() not in EVIDENCE for pair in pairs):
        raise Unfit(f"oa_to_area.csv gives evidence that is not one of: {', '.join(EVIDENCE)}")
    return {key.strip(): value.strip() for key, value in pairs}


def _margin(row: Row) -> float:
    found = _number(evidence_of(row).get("margin", ""))
    return math.inf if found is None else found


def placed_by(said: Mapping[str, str]) -> str:
    """What placed a cell, in words. A margin is by how much the second choice is further
    than the first: under a hundred it is said as written, and from a hundred as so many
    times as far, because "margin 240%" says little to a person."""
    if not said:
        return "No evidence is given"
    margin = _number(said.get("margin", ""))
    if margin is None or margin < AS_FAR:
        return ", ".join(EVIDENCE[key].format(value) for key, value in said.items())
    if margin >= MOST_MARGIN:
        times = "over 10 times as far"
    else:
        times = "twice as far" if margin == AS_FAR else f"{1 + margin / 100:.1f} times as far"
    second = said.get("second", "")
    far = f"second choice {second}, which is {times}" if second else f"its second choice is {times}"
    rest = [
        EVIDENCE[key].format(value)
        for key, value in said.items()
        if key not in ("margin", "second")
    ]
    return ", ".join([far, *rest])


def _placed_by(draft: Draft, row: Row) -> str:
    said = evidence_of(row)
    return placed_by(
        {key: draft.named(value) if key == "second" else value for key, value in said.items()}
    )


def borders(draft: Draft) -> list[Item]:
    items: list[tuple[tuple[Any, ...], Item]] = []
    for area_id in draft.areas:
        cells = draft.cells_of[area_id]
        if not cells:
            continue
        edge = sorted(
            draft.border_cells(area_id), key=lambda code: (_margin(draft.membership[code]), code)
        )
        # How many cells are in doubt is for the draft to say, once, with its rule. The
        # desk once counted the cells on a border with a margin under 10% here, and the
        # draft every cell with one: two counts stood side by side and differed.
        count = f"{len(cells)} cells, {len(edge)} on a border"
        flags = draft.flags("borders", area_id)
        fits = draft.fits("borders", area_id)
        item = _item(
            draft,
            area_id,
            draft.group_of(area_id),
            _area_title(draft, area_id),
            queue="borders",
            lines=[
                _line("Cells", count),
                *(
                    _line(code, _placed_by(draft, draft.membership[code]))
                    for code in edge[:MOST_LINES]
                ),
            ],
            drawn=draft.map_of(
                draft.group_of(area_id),
                area_id,
                [draft.cells[c] for c in cells if c in draft.cells],
                draft.marked("borders", area_id),
            ),
            more=_a_rule_fits(draft, fits, ""),
            flags=flags,
            preset=fits,
            ground={code: draft.membership[code]["evidence"] for code in cells},
        )
        least = _margin(draft.membership[edge[0]]) if edge else math.inf
        at = (not flags, draft.place_of("borders", area_id), -len(flags), least)
        key = (*draft.place_of_borough(item["group"]), *at, draft.named(area_id), area_id)
        items.append((key, item))
    return [item for _, item in sorted(items, key=lambda pair: pair[0])]


def whole(draft: Draft) -> list[Item]:
    items: list[tuple[tuple[Any, ...], Item]] = []
    for group, borough in draft.boroughs.items():
        inside = [area_id for area_id in draft.areas if draft.group_of(area_id) == group]
        flagged = [area_id for area_id in inside if draft.flags("borders", area_id)]
        flags = list(draft.flags("whole", group))
        for area_id in flagged:
            flags += [flag for flag in draft.flags("borders", area_id) if flag not in flags]
        cells = [code for area_id in inside for code in draft.cells_of[area_id]]
        if not cells:
            continue
        lines = [_line("Areas", f"{len(inside)} areas, {len(flagged)} flagged, {len(cells)} cells")]
        if flagged:
            shown = ", ".join(draft.named(area_id) for area_id in flagged[:MOST_LINES])
            lines.append(
                _line("Flagged", shown + (" and more" if len(flagged) > MOST_LINES else ""))
            )
        item = _item(
            draft,
            group,
            group,
            borough,
            queue="whole",
            lines=lines,
            drawn=draft.map_of(group, inside, [draft.cells[c] for c in cells if c in draft.cells]),
            flags=flags,
            ground={code: draft.membership[code]["area_id"] for code in cells},
        )
        items.append(((not flags, draft.place_of("whole", group), -len(flagged), borough), item))
    return [item for _, item in sorted(items, key=lambda pair: pair[0])]


def _borough_id(draft: Draft, borough: str) -> str:
    """The id of a borough's outline, which is what the page puts in the middle."""
    outlines = draft.drawn.get((layers.ALL, "boroughs"), {"features": []})["features"]
    return next((each["id"] for each in outlines if each["properties"].get("name") == borough), "")


def know(draft: Draft) -> list[Item]:
    outlines = draft.drawn.get((layers.ALL, "boroughs"), {"features": []})["features"]
    return [
        _item(
            draft,
            group,
            layers.ALL,
            borough,
            drawn=draft.map_of(layers.ALL, _borough_id(draft, borough), outlines),
        )
        for group, borough in draft.boroughs.items()
    ]


# Ratings


def ratings(draft: Draft) -> list[Item]:
    rubrics = [row for row in draft.table("rubrics.csv") if row["vibe"] and row["rubric"]]
    areas = sorted(draft.areas, key=lambda area_id: (draft.group_of(area_id), draft.named(area_id)))
    return [
        _item(
            draft,
            f"{area_id}:{row['vibe']}",
            draft.group_of(area_id),
            _area_title(draft, area_id),
            lines=[_line("Rate", in_words(row["vibe"]))],
            drawn=draft.map_of(draft.group_of(area_id), area_id, draft.shapes_of(area_id)),
            fill={"rubric": row["rubric"]},
            preset={"area_id": area_id, "vibe": row["vibe"]},
            ground={"cells": draft.cells_of_drawn(area_id), "vibe": row["vibe"]},
        )
        for area_id in areas
        for row in rubrics
    ]


# Claims, and the sentences of the golden set


def _prefix(draft: Draft) -> str:
    return "syn" if draft.synthetic else "lon"


def _pages(rows: Iterable[Mapping[str, Any]]) -> dict[tuple[Any, Any], list[Mapping[str, Any]]]:
    """The sentences of each revision of each page, in the order they are read."""
    pages: dict[tuple[Any, Any], list[Mapping[str, Any]]] = {}
    for row in rows:
        pages.setdefault((row["page_id"], row["revision_id"]), []).append(row)
    for sentences in pages.values():
        sentences.sort(key=lambda row: int(row["sentence"]))
    return pages


def _each_side(sentences: Sequence[Mapping[str, Any]], first: int, last: int) -> tuple[str, str]:
    before = str(sentences[first - 1]["text"]) if first > 0 else ""
    after = str(sentences[last + 1]["text"]) if last + 1 < len(sentences) else ""
    return before, after


def _around(quote: str, sentences: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    """The sentence each side of a quotation of one sentence or two, where the page is held."""
    for first, row in enumerate(sentences):
        text = str(row["text"])
        if text and quote.startswith(text):
            last, rest = first, quote[len(text) :].strip()
            if rest and first + 1 < len(sentences) and rest == str(sentences[first + 1]["text"]):
                last = first + 1
            elif rest:
                continue
            return _each_side(sentences, first, last)
    return "", ""


def claims(draft: Draft) -> list[Item]:
    pages = _pages([*draft.lines("claim_sentences.jsonl"), *draft.lines("sentences.jsonl")])
    items: list[tuple[tuple[Any, ...], Item]] = []
    for row in draft.lines("claims.jsonl"):
        review = cast(Mapping[str, Any], row["review"])
        if review.get("status") != PENDING:
            continue
        name, area_id, quote = str(row["claim_id"]), str(row["area_id"]), str(row["quote"])
        flags = list(draft.flags("claims", name))
        if row["has_reference"] is not True and "no_reference" not in flags:
            flags.append("no_reference")
        before, after = _around(quote, pages.get((row["page_id"], row["revision_id"]), []))
        source = str(row["source_id"])
        address = str(row["url"]) or ("None. The page is made up" if draft.synthetic else "None")
        lines = [
            _line("Area", draft.named(area_id)),
            _line("Kind", in_words(str(row["kind"]))),
            _line("Article", str(row["title"]), source),
            _line("Heading", str(row["section"]) or "The opening", source),
            _line("Address", address, source),
        ]
        if row["thing"]:
            lines.insert(2, _line("Names", str(row["thing"]), source))
        item = _item(
            draft,
            name,
            slug(str(row["title"])),
            f"{draft.named(area_id)}: {in_words(str(row['kind']))}",
            lines=lines,
            text={"before": before, "body": quote, "after": after},
            flags=flags,
        )
        items.append(((draft.named(area_id), area_id, not flags, name), item))
    return [item for _, item in sorted(items, key=lambda pair: pair[0])]


def sentences(draft: Draft) -> list[Item]:
    pages = _pages(draft.lines("sentences.jsonl"))
    items: list[Item] = []
    for (page_id, revision_id), rows in sorted(
        pages.items(), key=lambda page: (str(page[1][0]["title"]), str(page[0]))
    ):
        for at, row in enumerate(rows):
            before, after = _each_side(rows, at, at)
            number = int(row["sentence"])
            items.append(
                _item(
                    draft,
                    f"{_prefix(draft)}-page-{page_id}:{number}",
                    slug(str(row["title"])),
                    f"{row['title']}, sentence {number}",
                    lines=[_line("Heading", str(row["section"]) or "The opening")],
                    text={"before": before, "body": str(row["text"]), "after": after},
                    preset={"page_id": page_id, "revision_id": revision_id, "sentence": number},
                )
            )
    return items


# The map of areas to articles


def articles(draft: Draft) -> list[Item]:
    """One item for each row of the map. It is read before any page is fetched, so an
    item shows the title of an article and no word of it."""
    items: list[tuple[tuple[Any, ...], Item]] = []
    for row in draft.table("area_sources.csv"):
        area_id, role = row["area_id"], row["role"]
        if area_id not in draft.areas or not row["qid"] or role not in ROLES:
            raise Unfit(
                "area_sources.csv names an area that areas.csv does not hold, no item, "
                f"or a role that is not one of: {', '.join(ROLES)}"
            )
        name = f"{area_id}:{row['qid']}"
        flags = draft.flags("articles", name)
        source = row["source_id"]
        item = _item(
            draft,
            name,
            draft.group_of(area_id),
            f"{draft.named(area_id)}: {row['title'] or 'No title'}",
            lines=[
                _line("Area", _area_title(draft, area_id)),
                _line("Article", row["title"] or "No title", source),
                _line("Proposed as", ROLES[role]),
                _line("Item", row["qid"], source),
                _line("Page", row["page_id"] or "None", source),
            ],
            flags=flags,
            preset={
                "area_id": area_id,
                "qid": row["qid"],
                "page_id": row["page_id"],
                "role": role,
                "proposed": ITS_ARTICLE,
            },
        )
        at = list(ROLES).index(role)
        items.append(((item["group"], draft.named(area_id), area_id, not flags, at, name), item))
    return [item for _, item in sorted(items, key=lambda pair: pair[0])]


# Figures


def _spread(values: Sequence[float]) -> float | None:
    """What the middle half of all areas spans: from a low area to a high one."""
    if len(values) < ENOUGH_AREAS:
        return None
    low, _, high = statistics.quantiles(values, n=4, method="inclusive")
    return high - low


def _is_far(value: float, beside: Sequence[float], spread: float | None) -> bool:
    if spread is None or spread <= 0 or len(beside) < ENOUGH_NEIGHBOURS:
        return False
    return value > max(beside) + spread or value < min(beside) - spread


def _has_moved(value: float, before: float | None) -> bool:
    if before is None or value == before:
        return False
    return before == 0 or abs(value - before) / abs(before) >= A_FIFTH


def _shown(value: str, unit: str) -> str:
    if not value:
        return "No figure"
    if unit == "count":
        # A count is said by its number, as the product says it: its name says what is counted.
        return value
    return f"{value}{unit}" if unit == "%" else f"{value} {unit}".strip()


def figures(draft: Draft) -> list[Item]:
    rows = [row for row in draft.table("figures.csv") if row["area_id"] in draft.areas]
    held = {(row["area_id"], row["feature_id"]): row for row in rows}
    before = {
        (row["area_id"], row["feature_id"]): _number(row["value"])
        for row in draft.table("figures_before.csv")
    }
    values: dict[str, list[float]] = {}
    for row in rows:
        number = _number(row["value"])
        if number is not None:
            values.setdefault(row["feature_id"], []).append(number)
    spread = {feature_id: _spread(found) for feature_id, found in values.items()}
    beside = draft.neighbours if draft.has("oa_to_area.csv") else {}
    items: list[tuple[tuple[Any, ...], Item]] = []
    for (area_id, feature_id), row in held.items():
        value, said = _number(row["value"]), set(row["flag"].split())
        near = [
            held[other, feature_id]
            for other in beside.get(area_id, [])
            if (other, feature_id) in held
        ]
        numbers = [number for other in near if (number := _number(other["value"])) is not None]
        was = before.get((area_id, feature_id))
        found = {
            NO_EVIDENCE: bool(said & SAYS_NO_EVIDENCE),
            MOVED: value is not None and _has_moved(value, was),
            FAR: value is not None and _is_far(value, numbers, spread.get(feature_id)),
            ZERO: value == 0 and SAYS_THIN in said,
        }
        flags = [rule for rule in RULES if found[rule]]
        if not flags:
            continue
        source = row["source_id"]
        lines = [_line("Figure", _shown(row["value"], row["unit"]), source)]
        if found[MOVED]:
            lines.append(
                _line(
                    "The release before",
                    _shown("" if was is None else plain(was), row["unit"]),
                    source,
                )
            )
        lines += [
            _line("Source", draft.in_words(source), source),
            _line("Date of the data", row["vintage"], source),
        ]
        # A name alone does not say why it is there: it is an area beside this one.
        lines += [
            _line(
                f"{BESIDE}: {draft.named(other['area_id'])}",
                _shown(other["value"], other["unit"]),
                source,
            )
            for other in near[:MOST_LINES]
        ]
        label = row.get("label") or in_words(feature_id)
        item = _item(
            draft,
            f"{area_id}:{feature_id}",
            draft.group_of(area_id),
            f"{label}, {draft.named(area_id)}",
            lines=lines,
            flags=flags,
            preset={"area_id": area_id, "feature_id": feature_id},
        )
        first = RULES.index(flags[0])
        items.append(((first, draft.named(area_id), area_id, feature_id), item))
    return [item for _, item in sorted(items, key=lambda pair: pair[0])]


# Kinds of venue


def _words(name: str) -> set[str]:
    return set(re.findall(r"[a-z]+", name.casefold()))


def kinds(draft: Draft) -> list[Item]:
    rows = [row for row in draft.table("kinds.csv") if row["record_id"] and row["kind"]]
    by_kind: dict[str, list[Row]] = {}
    for row in rows:
        by_kind.setdefault(row["kind"], []).append(row)
    under = Counter(row["record_id"] for row in rows)
    chosen: list[tuple[tuple[Any, ...], Item]] = []
    for kind, records in by_kind.items():
        named = Counter(row["name"].casefold() for row in records)
        drawn = sorted(records, key=lambda row: _draw(kind, row["record_id"]))
        sample = drawn[: sample_size(len(records))]
        doubts = {row["record_id"]: _doubts(row, named, under) for row in sample}
        share = sum(bool(found) for found in doubts.values()) / len(sample)
        rank = IN_DOUBT.index(kind) if kind in IN_DOUBT else len(IN_DOUBT)
        for at, row in enumerate(sample):
            flags = doubts[row["record_id"]]
            twice = under[row["record_id"]] > 1
            item = _item(
                draft,
                f"{row['record_id']}:{kind}" if twice else row["record_id"],
                slug(kind),
                row["name"] or "No name",
                lines=[
                    _line("Category as written", row["category"] or "None", row["source_id"]),
                    _line("Given by", row["upstream"] or "Not said", row["source_id"]),
                    _line("Sample", f"{len(sample)} of {len(records)} records of this kind"),
                ],
                flags=flags,
                fill={"kind": in_words(kind)},
                preset={"kind": kind, "source_id": row["source_id"]},
            )
            chosen.append(((rank, -share, kind, not flags, at), item))
    return [item for _, item in sorted(chosen, key=lambda pair: pair[0])]


def _doubts(row: Row, named: Mapping[str, int], under: Mapping[str, int]) -> list[str]:
    """Why a record may not be what its kind says, by what the first look found."""
    found: list[str] = []
    if _words(row["name"]) & set(GIVES_AWAY.get(row["kind"], ())):
        found.append(ANOTHER_KIND)
    if named[row["name"].casefold()] > 1:
        found.append(REPEATS)
    if under[row["record_id"]] > 1:
        found.append(TWO_KINDS)
    return found


# Commons


def commons(draft: Draft) -> list[Item]:
    places: dict[str, list[Row]] = {}
    for row in draft.table("commons.csv"):
        if row["name"]:
            places.setdefault(row["name"], []).extend([row] if row["record_id"] else [])
    items: list[tuple[tuple[Any, ...], Item]] = []
    for name, matches in places.items():
        flags: list[str] = []
        if not matches:
            flags.append(NO_MATCH)
        elif not matches[0]["match"]:
            flags.append(NO_NAME)
        if matches and matches[0]["way_in"].casefold() not in YES:
            flags.append(NO_WAY_IN)
        source = draft.sources_of("commons.csv")[0]
        lines = [
            _line(
                row["match"] or "No name in the file",
                f"{row['kind'] or 'No kind'}. "
                f"{'A way in' if row['way_in'].casefold() in YES else 'No way in'}. "
                f"Record {row['record_id']}.",
                source,
            )
            for row in matches[:MOST_LINES]
        ]
        item = _item(
            draft,
            f"c:{slug(name)}",
            layers.ALL,
            name,
            lines=lines or [_line("Matches", "None in the file", source)],
            flags=flags,
            preset={"record_id": matches[0]["record_id"]} if matches else {},
        )
        worst = 0 if NO_MATCH in flags else 1 if flags else 2
        items.append(((worst, name), item))
    return [item for _, item in sorted(items, key=lambda pair: pair[0])]


# Rules


def _long(seconds: int) -> str:
    if seconds < 90:
        return f"{seconds} s"
    return f"{round(seconds / 60)} min" if seconds < 90 * 60 else f"{seconds / 3600:.1f} h"


def _waits(count: int) -> str:
    """That some of the names a rule would turn down are areas with ground, in words."""
    one = count == 1
    return (
        f"{count} of these {'is an area that has' if one else 'are areas that have'} ground. "
        f"{'Its answer is' if one else 'Their answers are'} saved, and set aside until the "
        "draft is made again from the answers."
    )


def _leans(draft: Draft, code: str, settles: Sequence[Item]) -> list[dict[str, str]]:
    """The line of a rule that leans on others: that it settles nothing by itself, and
    how many of its items lean on each. Nothing for a rule that stands by itself."""
    others = draft.leans_on(code)
    if not others:
        return []
    counted = Counter(str(item["preset"].get(LEANS_ON, "")) for item in settles)
    each = [f"{counted[other]} on {in_words(other).capitalize()}" for other in others]
    fits = f"the {len(settles)} item{'' if len(settles) == 1 else 's'} it fits"
    return [
        _line(
            "Leans on",
            "This rule settles an item only where the rule the item leans on is adopted "
            f"too. Of {fits}, those that lean on each rule: {', '.join(each)}.",
        )
    ]


def rules(draft: Draft) -> list[Item]:
    """One item for each rule the draft puts to the founder, in the order it puts them.

    An item shows the rule in words, how many items it would settle, what could go
    wrong, and ten of those items drawn by a fixed shuffle, so that the founder sees what
    it would wave through. Its preset holds a digest of every item it would settle, as
    each stands: a yes is given to one list, and to no other. So a rule is open again
    when an item it would settle is added, is taken away or has changed.

    Its preset holds the ids of the ten that are drawn, in the order of their lines, so
    that the page can open each. What the draft says of a rule in `lines.csv` is shown
    before them. A rule that leans on others says which, and its preset names them.
    """
    items: list[Item] = []
    titles = titles_of()
    for code, rule in draft.rules.items():
        queue = rule["queue"]
        held = {item["id"]: item for item in draft.made(queue)} if not missing(draft, queue) else {}
        mine = [name for name, by in draft.ruled.get(queue, {}).items() if by == code]
        if set(mine) - set(held):
            raise Unfit(f"{RULED} names an item that {queue} does not hold")
        settles = [held[name] for name in held if name in set(mine)]
        each, _ = PACE[queue]
        count = f"{len(settles)} of the {len(held)} items of {titles[queue]}"
        said = draft.said.get("rules", {}).get(code, [])
        lines = [
            _line("The rule", rule["says"]),
            _line(
                "Would settle",
                f"{count}. {_long(each * len(settles))} at the pace of the design, which "
                "nobody has timed.",
            ),
            *(line for line in said if line["label"] == ALREADY_DECIDED),
            *_leans(draft, code, settles),
            _line("What could go wrong", rule["goes_wrong"]),
        ]
        waits = [
            item
            for item in settles
            if item["preset"].get(HOLDS) and rule["gives"] not in (PROPOSED, AS_DRAFTED, AREA)
        ]
        if waits:
            lines.append(_line("Waits for a new draft", _waits(len(waits))))
        lines += [line for line in said if line["label"] != ALREADY_DECIDED]
        drawn = sorted(settles, key=lambda item: _draw(code, str(item["id"])))[:MOST_DRAWN]
        for at, item in enumerate(drawn, start=1):
            proposed = str(item["preset"].get("proposed", ""))
            would_be = _would_be(draft, rule, proposed)
            title = str(item["title"]).removesuffix(" (made up)")
            lines.append(
                _line(
                    f"Drawn at random, {at} of {len(drawn)}",
                    f"{title}. {would_be[0].upper()}{would_be[1:]}.",
                )
            )
        for item in settles:
            _would_be(draft, rule, str(item["preset"].get("proposed", "")))
        leans = {LEANS_ON: list(draft.leans_on(code))} if draft.leans_on(code) else {}
        items.append(
            _item(
                draft,
                code,
                queue,
                in_words(code).capitalize(),
                lines=lines,
                preset={
                    "rule": code,
                    "queue": queue,
                    "gives": rule["gives"],
                    "settles": revision(
                        {"settles": [[each["id"], each["rev"]] for each in settles]}
                    ),
                    DRAWN: [str(item["id"]) for item in drawn],
                    **leans,
                },
            )
        )
    return items


MAKERS: Final[Mapping[str, Callable[[Draft], list[Item]]]] = {
    "rules": rules,
    "know": know,
    "kinds": kinds,
    "commons": commons,
    "figures": figures,
    "sentences": sentences,
    "names": names,
    "borders": borders,
    "whole": whole,
    "ratings": ratings,
    "articles": articles,
    "claims": claims,
}


# A file of items


@dataclass(frozen=True)
class Asked:
    """What the desk asks of a queue today, as `questions.json` holds it."""

    # The queue and the version of its question, as a line records it: `names@1`.
    version: str
    # The flags the page has words for.
    flags: frozenset[str]


def _asked(path: Path = QUESTIONS) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], json.loads(path.read_text(encoding="utf-8"))["queues"])


def labels_of(path: Path = QUESTIONS) -> dict[str, dict[str, str]]:
    """The label of every answer of every queue, by queue and then by code."""
    return {
        queue["id"]: {answer["code"]: answer["label"] for answer in queue["answers"]}
        for queue in _asked(path)
    }


def answers_of(path: Path = QUESTIONS) -> dict[str, tuple[str, ...]]:
    return {queue: tuple(labels) for queue, labels in labels_of(path).items()}


def titles_of(path: Path = QUESTIONS) -> dict[str, str]:
    return {queue["id"]: str(queue["title"]) for queue in _asked(path)}


def questions(path: Path = QUESTIONS) -> dict[str, Asked]:
    held = json.loads(path.read_text(encoding="utf-8"))
    return {
        queue["id"]: Asked(f"{queue['id']}@{queue['version']}", frozenset(queue["flags"]))
        for queue in held["queues"]
    }


def files_of(draft: Draft, queue: str) -> list[str]:
    """The files of the draft that a queue is made from, its layers among them."""
    needs, reads, draws = QUEUES[queue]
    tables = [name for name in (*needs, *reads) if draft.has(name)]
    drawn = (
        [f"layers/{group}/{layer}.geojson" for group, layer in sorted(draft.drawn)] if draws else []
    )
    return [*tables, *drawn]


def missing(draft: Draft, queue: str) -> list[str]:
    return [name for name in QUEUES[queue][0] if not draft.has(name)]


def ask(draft: Draft, queue: str, registry: Path | None = None) -> None:
    """Ask the licence gate about every source a queue would show. Raises `gate.Refused`."""
    needs, reads, _ = QUEUES[queue]
    for name in (*needs, *reads):
        if draft.has(name) and name in USE_OF:
            gate.ask(
                draft.sources_of(name), USE_OF[name], synthetic=draft.synthetic, registry=registry
            )
    if "oa_to_area.csv" in needs and not draft.synthetic:
        # A name in the evidence of a cell is shown beside a border, and is written to
        # the table that is committed. The made-up city names no publisher there.
        named = {key for row in draft.table("oa_to_area.csv") for key in evidence_of(row)}
        sources = sorted({EVIDENCE_SOURCE[key] for key in named if key in EVIDENCE_SOURCE})
        gate.ask(sources, gate.GAZETTEER, synthetic=False, registry=registry)


def hold_to_rule_8(draft: Draft) -> None:
    """Refuse a draft that would put words about who lives somewhere beside a border or a
    vibe. Raises `Unfit`, which names the file and the row and never a value."""
    for at, row in enumerate(draft.table("rubrics.csv"), start=1):
        if about_residents(row["rubric"]):
            raise Unfit(
                f"rubrics.csv, row {at}: the rubric asks about who lives somewhere, a price "
                "or a crime. A rubric is in words about streets, buildings and places"
            )
    for at, row in enumerate(draft.table("oa_to_area.csv"), start=1):
        said = evidence_of(row)
        if any(about_residents(said[key]) for key in EVIDENCE_SOURCE if key in said):
            raise Unfit(
                f"oa_to_area.csv, row {at}: the evidence holds words about who lives "
                "somewhere, a price or a crime. Nothing of the kind stands beside a border"
            )


def made_from(draft: Draft, queue: str) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for name in files_of(draft, queue):
        digest = draft.digest(name)
        if name.startswith("layers/"):
            group, layer = name.removeprefix("layers/").removesuffix(".geojson").split("/")
            sources = draft.drawn[group, layer]["desk"]["source_ids"]
        else:
            sources = draft.sources_of(name) or [gate.MADE_UP if draft.synthetic else OWN]
            if name == SAID and any(not row["source_id"] for row in draft.table(name)):
                sources = sorted({*sources, gate.MADE_UP if draft.synthetic else OWN})
        found += [{"source_id": source, "file": name, "sha256": digest} for source in sources]
    return found


def fill(draft: Draft, queue: str, made_on: str, asked: Asked) -> str:
    """The file of one queue, as text: its first line, then an item to a line."""
    items = draft.made(queue)
    if len({item["id"] for item in items}) != len(items):
        raise Unfit(f"The draft gives the queue {queue} an item twice")
    if set(draft.said.get(queue, ())) - {item["id"] for item in items}:
        # A doubt that reaches no item would be lost without a word.
        raise Unfit(f"{SAID} holds a line of an item that {queue} does not hold")
    for at, item in enumerate(items if queue in DRAWS_A_MAP else (), start=1):
        # The last look. What a draft may hold was held to the rule where it was read.
        shown = [*(line["label"] for line in item["lines"]), *item["fill"].values()]
        if about_residents(" ".join(shown)):
            raise Unfit(
                f"Item {at} of {queue} would show words about who lives somewhere, a price "
                "or a crime, beside a map"
            )
    if any(set(item["flags"]) - asked.flags for item in items):
        raise Unfit(
            f"The draft flags an item of {queue} with a flag the page has no words for. "
            "Give the flag its words in questions.json, or take it out of flags.csv"
        )
    if set(draft.marks.get(queue, ())) - {item["id"] for item in items}:
        raise Unfit(f"{MARKED} marks an item that {queue} does not hold")
    marked_for = {
        row["flag"] for row in draft.table(MARKED) if row["queue"] == queue and row["flag"]
    }
    if marked_for - asked.flags:
        raise Unfit(f"{MARKED} holds a mark of a flag the page has no words for")
    header = {
        "desk": DESK,
        "queue": queue,
        "question": asked.version,
        "synthetic": draft.synthetic,
        "made_on": made_on,
        "made_from": made_from(draft, queue),
        "count": len(items),
    }
    return "".join(canonical(row) + "\n" for row in (header, *items))
