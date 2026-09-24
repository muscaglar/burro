"""The census figures of an area's page: the records, the words, and the one judge of the file.

A census says who lived somewhere on one day. Burro shows it on the page of an
area and does nothing else with it. So it is kept apart from the release by
structure, and not by care:

- It stands in a folder of its own beside the release, and is no file of one.
- `Release` cannot return it. Ranking, facts, likeness, the portrait and the
  reader are handed a release, so none of them can be handed a census.
- Nothing in core imports this module, and this module imports nothing of core
  but the shape of a record and the form of an id. A test holds both.

The figures are counts that a publisher gives for small areas, added up over an
area. What is served of one is a share in whole per cents, the count beside it,
and the share of the whole city for the same thing. Nothing else stands beside
a figure: no other area, no rank, no word of Burro's about what the figure means.

A share under 1 in 100 is said in words, and its count is never given: the
publisher changes small counts on purpose, so a small count is no fact about
people. A table is left out where too few were counted for a share to be steady.
"""

import hashlib
import json
from collections.abc import Iterator, Mapping, Sequence
from enum import StrEnum
from typing import Annotated, Any

from pydantic import Field, StrictBool, ValidationError

from burro_core._record import Record
from burro_core.ids import (
    DATE_PATTERN,
    SLUG_PATTERN,
    SYNTHETIC_PREFIX,
    SYNTHETIC_SOURCE_ID,
    AreaId,
    ReleaseId,
    SourceId,
)

# The folder beside a release that holds the census: the release's name with this after it.
RESIDENTS_FOLDER = "-residents"
MANIFEST = "manifest.json"
CENSUS = "census.json"

# A table is left out for an area where fewer than this were counted in it, people or
# households. With the rule on a share under 1 in 100 it means that no count under 10 is
# ever given. The publisher's guidance names no figure: this one is Burro's, and a first guess.
FLOOR = 1_000
# A count is given only where it is at least this share of those counted.
ONE_IN = 100
# What the base of a table is rounded to before it is said, with "about" before it.
BASE_ROUNDED_TO = 100
# How deep a row may stand under its group.
DEEPEST = 2

FEWER = "fewer than 1 in 100"
NEARLY_ALL = "over 99%"

_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


class CensusError(Exception):
    """A census broke a rule. Names the file, the row and the rule, and never a value."""

    def __init__(self, file: str, rule: str, row: str = "") -> None:
        self.file = file
        self.rule = rule
        self.row = row
        super().__init__(f"{file}: {row}: {rule}" if row else f"{file}: {rule}")


class CensusKind(StrEnum):
    """What a table counts. It is no `FeatureId` and no `TagId`: no spec or edit can name it."""

    AGE = "age"
    HOUSEHOLDS = "households"
    COUNTRY_OF_BIRTH = "country_of_birth"
    ETHNIC_GROUP = "ethnic_group"
    RELIGION = "religion"


# Shown on an area's page, and never ranked on, filtered on or compared on. Age and the
# make-up of households are not among them: a measure built from either is a feature of
# the catalogue, with an id and a source of its own, and is no part of this file.
SHOWN_AND_NEVER_RANKED_ON = frozenset(
    {CensusKind.COUNTRY_OF_BIRTH, CensusKind.ETHNIC_GROUP, CensusKind.RELIGION}
)


class Unit(StrEnum):
    PEOPLE = "people"
    HOUSEHOLDS = "households"


class CensusLeftOut(StrEnum):
    """Why an area has no figure for a table. Nothing is filled in for either."""

    TOO_FEW = "too_few"
    NOT_HELD = "not_held"


Text = Annotated[str, Field(min_length=1)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Count = Annotated[int, Field(ge=0)]
TableCode = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$")]


class CensusSource(Record):
    """Where the figures came from. The same fields as a source of a release."""

    source_id: SourceId
    name: Text
    publisher: Text
    licence: Text
    attribution: Text
    url: str
    retrieved_on: str = Field(pattern=DATE_PATTERN)


class CensusManifest(Record):
    """What the folder of a census holds, and which release it was made for."""

    release_id: ReleaseId
    synthetic: StrictBool
    census_sha256: Sha256
    census_bytes: int = Field(ge=0)
    sources: Annotated[tuple[CensusSource, ...], Field(min_length=1)]


class Row(Record):
    """One row of a table, as the publisher heads it. Said once for the table."""

    code: str = Field(pattern=SLUG_PATTERN)
    # The publisher's heading whole, for a screen reader, and the part of it that is printed.
    heading: Text
    label: Text
    depth: int = Field(ge=0, le=DEEPEST)


class Table(Record):
    """One table of the census: what it counts, in whose words, and from where."""

    table_code: TableCode
    kind: CensusKind
    title: Text
    variable: Text
    universe: Text
    unit: Unit
    # The publisher's own sentence. It is quoted, and never reworded.
    definition: Text
    source_id: SourceId
    # The publisher's page for the table. Empty for a made-up table, which has none.
    url: str
    rows: Annotated[tuple[Row, ...], Field(min_length=1)]


class Counted(Record):
    """The figures of one table for one area, or for the whole city.

    `counts` is in the order of the table's rows. A count that is under 1 in
    100 of `base` is not held: it is `None`, and what is served says so in
    words. Where the table is left out, `base` is `None`, `counts` is empty
    and `reason` says why.
    """

    table_code: TableCode
    base: Count | None
    counts: tuple[Count | None, ...]
    reason: CensusLeftOut | None


class AreaCensus(Record):
    area_id: AreaId
    # How many of the publisher's small areas were added up.
    output_areas: int = Field(ge=0)
    tables: tuple[Counted, ...]


class Whole(Record):
    """The whole city, which is all that stands beside an area's figure."""

    name: Text
    tables: tuple[Counted, ...]


class Census(Record):
    """The census of one release: every table, the whole city, and every area."""

    release_id: ReleaseId
    synthetic: StrictBool
    # The day the census was taken.
    taken_on: str = Field(pattern=DATE_PATTERN)
    # When the publisher's files were fetched.
    retrieved_on: str = Field(pattern=DATE_PATTERN)
    sources: Annotated[tuple[CensusSource, ...], Field(min_length=1)]
    tables: Annotated[tuple[Table, ...], Field(min_length=1)]
    whole: Whole
    areas: tuple[AreaCensus, ...]

    def area(self, area_id: str) -> AreaCensus | None:
        return next((area for area in self.areas if area.area_id == area_id), None)


# ---------------------------------------------------------------------------
# The words. Every word of the panel but a button's is here, and is served.
# None says what a figure means: no "main", no "most", no adjective.
# ---------------------------------------------------------------------------


class Words(Record):
    """The fixed words of the panel. `{name}`, `{city}`, `{day}` and the rest are filled in."""

    heading: Text
    intro: Text
    date_line: Text
    notes: tuple[Text, ...]
    caption: Text
    definition: Text
    too_few: Text
    not_held: Text
    shown_only: Text
    counted: Mapping[Unit, Text]
    source_line: Text
    derivation_line: Text
    licence_line: Text
    # The publisher's own sentence about the day, said under the tables it bears on.
    of_the_day: Text
    open_source: Text
    # What the publisher's small areas are called: one of them, and more than one.
    small_area: tuple[Text, Text]


CENSUS_2021 = Words(
    heading="Census 2021: who lived here",
    intro=(
        "Official figures for the people who lived here on {day}: age, households, country "
        "of birth, ethnic group and religion. Burro never ranks, filters or compares areas "
        "by ethnic group, religion or country of birth."
    ),
    date_line="Census 2021, taken on {day}. Published by the Office for National Statistics.",
    notes=(
        "The census was taken during a lockdown. Some people were not living where they "
        "usually do.",
        "An area can change. These figures are of that day, and not of today.",
        "{name} is drawn by Burro from {areas}. The figures are the statistics office's "
        "counts, added up by Burro. No official table has this boundary, so none will "
        "match exactly.",
        "The statistics office changes small counts slightly so that nobody can be picked "
        "out. Shares are whole numbers and may not add up to 100%. Where fewer than 1 in "
        "100 were counted, the table says so and gives no count.",
        "Beside each figure is the figure for {city}, and nothing else. Burro says nothing "
        "about what a figure means.",
    ),
    caption=(
        "{title}. Census 2021, {day}. Share of {universe} in {name}, with the number "
        "counted, beside the share in {city}. About {base} {unit} counted in {name}."
    ),
    definition='The statistics office\'s definition: "{definition}"',
    too_few="{title}. Too few {unit} lived in {name} on census day for Burro to give shares.",
    not_held="{title}. The census figures Burro holds have none for {name}.",
    shown_only="Shown here and nowhere else. Burro never ranks, filters or compares on it.",
    counted={Unit.PEOPLE: "Counted", Unit.HOUSEHOLDS: "Counted"},
    source_line=(
        "Source: Office for National Statistics. Census 2021, tables {codes}, for output "
        "areas. Retrieved {retrieved}."
    ),
    derivation_line=(
        "Added up by Burro over the {areas} of {name}. The shares are Burro's arithmetic on "
        "the office's counts."
    ),
    licence_line=(
        "Contains public sector information licensed under the Open Government Licence v3.0."
    ),
    of_the_day=(
        'The statistics office says: "The coronavirus pandemic may have affected some '
        "people's choice of usual residence on Census Day.\""
    ),
    open_source="The statistics office's page for this table",
    small_area=("census output area", "census output areas"),
)

# A made-up count names no real census, no real day's events and no real group. Its words
# are as long as the real ones, so that a page laid out on it is laid out for the real one.
MADE_UP = Words(
    heading="A made-up count: who lived here",
    intro=(
        "Made-up figures for the people who lived here on {day}: age, households, and three "
        "tables of made-up groups. Burro never ranks, filters or compares areas by who "
        "lives in them."
    ),
    date_line="A made-up count, dated {day}. Nothing here was counted, and nobody published it.",
    notes=(
        "A real count says here what was unusual about the day it was taken.",
        "An area can change. These figures are of that day, and not of today.",
        "{name} is drawn by Burro from {areas}. The figures are made-up counts, added up by Burro.",
        "Shares are whole numbers and may not add up to 100%. Where fewer than 1 in 100 "
        "were counted, the table says so and gives no count.",
        "Beside each figure is the figure for {city}, and nothing else. Burro says nothing "
        "about what a figure means.",
    ),
    caption=(
        "{title}. A made-up count, {day}. Share of {universe} in {name}, with the number "
        "counted, beside the share in {city}. About {base} {unit} counted in {name}."
    ),
    definition='The definition a publisher would give: "{definition}"',
    too_few="{title}. Too few {unit} lived in {name} on the day for Burro to give shares.",
    not_held="{title}. The made-up count holds no figures for {name}.",
    shown_only="Shown here and nowhere else. Burro never ranks, filters or compares on it.",
    counted={Unit.PEOPLE: "Counted", Unit.HOUSEHOLDS: "Counted"},
    source_line="Source: made up by Burro for testing. Tables {codes}. Made on {retrieved}.",
    derivation_line=(
        "Added up by Burro over the {areas} of {name}. The shares are Burro's arithmetic on "
        "made-up counts."
    ),
    licence_line="Synthetic data generated by Burro for testing. It describes no real place.",
    of_the_day="A real count quotes here what its publisher says of the day it was taken.",
    open_source="The publisher's page for this table",
    small_area=("made-up small area", "made-up small areas"),
)

# The tables whose figures depend most on where people were living on the day: the
# publisher's sentence about the day is said under these.
BEARS_ON = frozenset({CensusKind.AGE, CensusKind.HOUSEHOLDS})

# Words that Burro would be choosing, and so never uses of a figure. A publisher's own
# heading may hold one, and is printed as it is published.
NEVER_SAID = frozenset(
    {
        "diverse",
        "diversity",
        "mixed",
        "multicultural",
        "vibrant",
        "main",
        "largest",
        "biggest",
        "majority",
        "minority",
        "dominant",
        "predominantly",
        "mostly",
        "typical",
        "average",
        "high",
        "low",
        "higher",
        "lower",
        "above",
        "below",
        "more",
        "less",
    }
)


def words_of(synthetic: bool) -> Words:
    return MADE_UP if synthetic else CENSUS_2021


def day_in_words(date: str) -> str:
    """`2021-03-21` as `21 March 2021`."""
    year, month, day = (int(part) for part in date.split("-"))
    return f"{day} {_MONTHS[month - 1]} {year}"


# ---------------------------------------------------------------------------
# What is served.
# ---------------------------------------------------------------------------


class CensusOffer(Record):
    """What the closed block of an area's page says. It holds no figure and names no area."""

    available: StrictBool
    heading: str
    intro: str


NO_CENSUS = CensusOffer(available=False, heading="", intro="")


class CensusPanelRow(Record):
    """One row as it is printed: the area's figure, and the whole city's beside it.

    `share` and `city_share` are words. `percent` and `city_percent` are the
    same shares as whole numbers, for the picture alone, and are `None`
    where the share is under 1 in 100. `count` is as it is printed, and is
    `None` where the share is under 1 in 100: a small count is never given.
    """

    code: str
    heading: str
    label: str
    depth: int
    share: str
    percent: int | None
    count: str | None
    city_share: str
    city_percent: int | None


class CensusColumns(Record):
    """The heading of each column, in the order they are printed."""

    label: str
    share: str
    count: str
    city: str


class CensusPanelTable(Record):
    table_code: str
    kind: CensusKind
    title: str
    # The title, the census, its day, the area and how many were counted. Every table
    # carries all of it, so that a picture of one table says what it is and when.
    caption: str
    definition: str
    # Said of a table that is shown and never ranked on. `None` for the others.
    shown_only: str | None
    # The publisher's own sentence about the day, under a table it bears on.
    note: str | None
    columns: CensusColumns
    # Why the table is left out for this area, and the sentence that says so.
    reason: CensusLeftOut | None
    left_out: str | None
    # In the publisher's order. Empty where the table is left out.
    rows: tuple[CensusPanelRow, ...]
    source_id: str
    # The publisher's page for the table, and what a link to it says. Empty where there is none.
    source_url: str
    source_label: str


class CensusPanel(Record):
    """The census of one area, as its page shows it. Every word but a button's is here."""

    area_id: AreaId
    heading: str
    date_line: str
    notes: tuple[str, ...]
    city: str
    output_areas: int
    tables: tuple[CensusPanelTable, ...]
    source_line: str
    derivation_line: str
    licence_line: str


def offer(census: Census | None) -> CensusOffer:
    """What an area's page says before the figures are asked for."""
    if census is None:
        return NO_CENSUS
    words = words_of(census.synthetic)
    day = day_in_words(census.taken_on)
    return CensusOffer(available=True, heading=words.heading, intro=words.intro.format(day=day))


def percent_of(count: int, base: int) -> int:
    """A share as a whole per cent. It reads 100 only where every one that was counted is in it."""
    whole = round(100 * count / base)
    return min(whole, ONE_IN - 1) if count < base else ONE_IN


def is_small(count: int, base: int) -> bool:
    """Whether a count is under 1 in 100 of those counted."""
    return count * ONE_IN < base


def share_in_words(count: int | None, base: int) -> tuple[str, int | None]:
    """A share as it is printed, and as a whole number for the picture."""
    if count is None:
        return FEWER, None
    percent = percent_of(count, base)
    nearly = count < base and round(100 * count / base) >= ONE_IN
    return (NEARLY_ALL if nearly else f"{percent}%"), percent


def base_in_words(base: int) -> str:
    rounded = round(base / BASE_ROUNDED_TO) * BASE_ROUNDED_TO
    return f"{rounded:,}"


def _rows(table: Table, here: Counted, city: Counted | None) -> tuple[CensusPanelRow, ...]:
    assert here.base is not None
    found: list[CensusPanelRow] = []
    for position, row in enumerate(table.rows):
        count = here.counts[position]
        share, percent = share_in_words(count, here.base)
        # The whole city has a figure for every table it holds. Where it holds none for
        # this table, nothing stands beside the area's figure, and nothing is filled in.
        city_share, city_percent = (
            share_in_words(city.counts[position], city.base)
            if city is not None and city.base is not None
            else ("", None)
        )
        found.append(
            CensusPanelRow(
                code=row.code,
                heading=row.heading,
                label=row.label,
                depth=row.depth,
                share=share,
                percent=percent,
                count=None if count is None else f"{count:,}",
                city_share=city_share,
                city_percent=city_percent,
            )
        )
    return tuple(found)


def panel(census: Census, area_id: str, name: str) -> CensusPanel | None:
    """The census of one area, as it is served. `None` where the census does not name the area.

    `name` is the release's name for the area. The rows of a table are in the
    order the census holds them, which is the publisher's. Nothing here puts
    one row before another by its figure.
    """
    area = census.area(area_id)
    if area is None:
        return None
    words = words_of(census.synthetic)
    day = day_in_words(census.taken_on)
    city = census.whole.name
    of_city = {counted.table_code: counted for counted in census.whole.tables}
    of_area = {counted.table_code: counted for counted in area.tables}
    one, many = words.small_area
    # How many small areas were added up, said so that one reads as one.
    areas = f"{area.output_areas:,} {one if area.output_areas == 1 else many}"
    said = {"name": name, "city": city, "day": day, "areas": areas}

    tables: list[CensusPanelTable] = []
    for table in census.tables:
        here = of_area[table.table_code]
        given = {
            **said,
            "title": table.title,
            "universe": table.universe,
            "unit": table.unit.value,
        }
        if here.reason is not None or here.base is None:
            sentence = words.too_few if here.reason is CensusLeftOut.TOO_FEW else words.not_held
            caption, left_out = table.title, sentence.format(**given)
            rows: tuple[CensusPanelRow, ...] = ()
        else:
            caption = words.caption.format(**given, base=base_in_words(here.base))
            left_out = None
            rows = _rows(table, here, of_city.get(table.table_code))
        tables.append(
            CensusPanelTable(
                table_code=table.table_code,
                kind=table.kind,
                title=table.title,
                caption=caption,
                definition=words.definition.format(definition=table.definition),
                shown_only=(words.shown_only if table.kind in SHOWN_AND_NEVER_RANKED_ON else None),
                note=words.of_the_day if table.kind in BEARS_ON and rows else None,
                columns=CensusColumns(
                    label=table.variable, share=name, count=words.counted[table.unit], city=city
                ),
                reason=here.reason,
                left_out=left_out,
                rows=rows,
                source_id=table.source_id,
                source_url=table.url,
                source_label=words.open_source if table.url else "",
            )
        )

    codes = [table.table_code for table in census.tables]
    listed = ", ".join(codes[:-1]) + (" and " if len(codes) > 1 else "") + codes[-1]
    return CensusPanel(
        area_id=area.area_id,
        heading=words.heading,
        date_line=words.date_line.format(**said),
        notes=tuple(note.format(**said) for note in words.notes),
        city=city,
        output_areas=area.output_areas,
        tables=tuple(tables),
        source_line=words.source_line.format(
            codes=listed, retrieved=day_in_words(census.retrieved_on)
        ),
        derivation_line=words.derivation_line.format(**said),
        licence_line=words.licence_line,
    )


# ---------------------------------------------------------------------------
# The one judge of a census.
# ---------------------------------------------------------------------------

Finding = tuple[str, str]


def census_is_of_the_release(
    census: Census, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    if census.release_id != release_id:
        yield CENSUS, "release_id"
    if census.synthetic is not synthetic:
        yield CENSUS, "synthetic"


def made_up_is_said(
    census: Census, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    """A made-up count cites the reserved source and no other, and a real one never cites it."""
    for position, source in enumerate(census.sources):
        if (source.source_id == SYNTHETIC_SOURCE_ID) is not census.synthetic:
            yield CENSUS, f"sources[{position}]"
    for position, area in enumerate(census.areas):
        if area.area_id.startswith(SYNTHETIC_PREFIX) is not census.synthetic:
            yield CENSUS, f"areas[{position}]"
    for position, table in enumerate(census.tables):
        if bool(table.url) is census.synthetic:
            # A made-up table has no page to open, and a real one always has.
            yield CENSUS, f"tables[{position}].url"


def tables_are_in_order(
    census: Census, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    """Each kind of table once, and every row of a table under a code of its own."""
    kinds = [table.kind for table in census.tables]
    codes = [table.table_code for table in census.tables]
    if len(set(kinds)) != len(kinds) or len(set(codes)) != len(codes):
        yield CENSUS, "tables"
    cited = {source.source_id for source in census.sources}
    for position, table in enumerate(census.tables):
        rows = [row.code for row in table.rows]
        if len(set(rows)) != len(rows):
            yield CENSUS, f"tables[{position}].rows"
        if table.source_id not in cited:
            yield CENSUS, f"tables[{position}].source_id"
        # A row stands one step under the row before it at most, and the first under none.
        above = -1
        for place, row in enumerate(table.rows):
            if row.depth > above + 1:
                yield CENSUS, f"tables[{position}].rows[{place}]"
            above = row.depth


def areas_are_the_releases(
    census: Census, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    """Every area of the release once, in the order of its id, and no other."""
    if [area.area_id for area in census.areas] != sorted(set(area_ids)):
        yield CENSUS, "areas"


def _counted(census: Census) -> Iterator[tuple[str, Counted]]:
    for position, counted in enumerate(census.whole.tables):
        yield f"whole.tables[{position}]", counted
    for place, area in enumerate(census.areas):
        for position, counted in enumerate(area.tables):
            yield f"areas[{place}].tables[{position}]", counted


def rows_are_complete(
    census: Census, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    """Every area, and the whole city, has each table once, with a count for every row of it."""
    codes = [table.table_code for table in census.tables]
    width = {table.table_code: len(table.rows) for table in census.tables}
    for where, held in (
        ("whole", census.whole.tables),
        *((f"areas[{place}]", area.tables) for place, area in enumerate(census.areas)),
    ):
        if [counted.table_code for counted in held] != codes:
            yield CENSUS, f"{where}.tables"
    for where, counted in _counted(census):
        left_out = counted.reason is not None
        if (
            left_out is not (counted.base is None)
            or left_out is not (not counted.counts)
            or (not left_out and len(counted.counts) != width.get(counted.table_code))
        ):
            yield CENSUS, where


def too_few_are_left_out(
    census: Census, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    for where, counted in _counted(census):
        if counted.base is not None and counted.base < FLOOR:
            yield CENSUS, f"{where}.base"


def small_counts_are_withheld(
    census: Census, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    """No count under 1 in 100 of those counted is held, and none is more than were counted."""
    for where, counted in _counted(census):
        if counted.base is None:
            continue
        for position, count in enumerate(counted.counts):
            if count is not None and (is_small(count, counted.base) or count > counted.base):
                yield CENSUS, f"{where}.counts[{position}]"


RULES = (
    census_is_of_the_release,
    made_up_is_said,
    tables_are_in_order,
    areas_are_the_releases,
    rows_are_complete,
    too_few_are_left_out,
    small_counts_are_withheld,
)


def _refuse_constant(_: str) -> Any:
    raise ValueError("NaN and Infinity are not JSON")


def _parsed(name: str, content: bytes) -> object:
    try:
        return json.loads(content.decode("utf-8"), parse_constant=_refuse_constant)
    except ValueError:
        raise CensusError(name, "json_is_valid") from None


def _row(loc: tuple[int | str, ...]) -> str:
    parts = ""
    for part in loc:
        parts += f"[{part}]" if isinstance(part, int) else f".{part}"
    return parts.lstrip(".")


def _shaped[R: Record](name: str, shape: type[R], document: object) -> R:
    try:
        return shape.model_validate(document)
    except ValidationError as error:
        # Only where. The message and the input can repeat a value.
        first = error.errors(include_url=False, include_context=False, include_input=False)[0]
        loc = first["loc"]
        if first["type"] == "extra_forbidden":
            loc = loc[:-1]
        raise CensusError(name, "shape_is_valid", _row(loc)) from None


def parse_census(
    document: object, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Census:
    """The parsed content of `census.json` as a census, held to every rule. The only parser."""
    census = _shaped(CENSUS, Census, document)
    for rule in RULES:
        for file, row in rule(census, release_id, synthetic, area_ids):
            raise CensusError(file, rule.__name__, row)
    return census


def open_census(
    folder_name: str,
    files: Mapping[str, bytes],
    release_id: str,
    synthetic: bool,
    area_ids: Sequence[str],
) -> Census:
    """Check the bytes of the folder of a census, and hold it to the release it stands beside.

    It reads no file itself: the caller passes the bytes, by file name. The
    release is given as its id, whether it is made up, and the ids of its
    areas, and as nothing more: a census is never handed a release.
    """
    if folder_name != f"{release_id}{RESIDENTS_FOLDER}":
        raise CensusError(MANIFEST, "folder_is_named_for_the_release")
    for name in (MANIFEST, CENSUS):
        if name not in files:
            raise CensusError(name, "files_match_manifest")
    for name in sorted(set(files) - {MANIFEST, CENSUS}):
        raise CensusError(name, "files_match_manifest")

    manifest = _shaped(MANIFEST, CensusManifest, _parsed(MANIFEST, files[MANIFEST]))
    if manifest.release_id != release_id or manifest.synthetic is not synthetic:
        raise CensusError(MANIFEST, census_is_of_the_release.__name__)
    content = files[CENSUS]
    if (
        len(content) != manifest.census_bytes
        or hashlib.sha256(content).hexdigest() != manifest.census_sha256
    ):
        raise CensusError(CENSUS, "files_match_manifest")
    census = parse_census(_parsed(CENSUS, content), release_id, synthetic, area_ids)
    if manifest.sources != census.sources:
        raise CensusError(MANIFEST, "sources_are_stated", "sources")
    return census
