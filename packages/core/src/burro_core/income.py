"""Household income on an area's page: the records, the words, and the one judge of the file.

The statistics office estimates, from a model, what the households of a small
area have as income in a year. It is a figure about who lives somewhere, so
Burro shows it on the page of an area and does nothing else with it. It is
kept apart from the release by structure, as the census is, and not by care:

- It stands in a folder of its own beside the release, and is no file of one.
- `Release` cannot return it. Ranking, facts, comparison, likeness, the
  portrait and the reader are handed a release, so none can be handed it.
- Nothing in core imports this module, and this module imports nothing of core
  but the shape of a record and the form of an id. A test holds both.
- It is no `FeatureId`, no `TagId` and no cost, so no spec and no edit can
  name it, and no sentence of an explanation can cite it.

What is served of it is one area's own figure, as its publisher gives it: the
estimate, the two limits the publisher puts round it, the year it is of, and
the publisher's own words for what it is. Nothing stands beside it: no other
area, no figure of the whole city, no rank, no colour, and no word of Burro's
about what the figure means. The publisher asks that areas are compared only
with the limits in mind, and Burro compares none.

The estimate is a mean and never a median, and is of the area, never of a
household or a person. It is of one year: no change over time is shown.
"""

import hashlib
import json
from collections.abc import Iterator, Mapping, Sequence
from typing import Annotated, Any

from pydantic import Field, StrictBool, ValidationError

from burro_core._record import Record
from burro_core.ids import (
    DATE_PATTERN,
    MONTH_PATTERN,
    SYNTHETIC_PREFIX,
    SYNTHETIC_SOURCE_ID,
    AreaId,
    ReleaseId,
    SourceId,
)

# The folder beside a release that holds the figure: the release's name with this after it.
INCOME_FOLDER = "-income"
MANIFEST = "manifest.json"
INCOME = "income.json"

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


class IncomeError(Exception):
    """A file of income broke a rule. Names the file, the row and the rule, and never a value."""

    def __init__(self, file: str, rule: str, row: str = "") -> None:
        self.file = file
        self.rule = rule
        self.row = row
        super().__init__(f"{file}: {row}: {rule}" if row else f"{file}: {rule}")


Text = Annotated[str, Field(min_length=1)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
# Whole pounds, written as a whole number: a figure in words or with a fraction is refused.
Pounds = Annotated[int, Field(ge=1, strict=True)]


class IncomeSource(Record):
    """Where the figures came from. The same fields as a source of a release."""

    source_id: SourceId
    name: Text
    publisher: Text
    licence: Text
    attribution: Text
    url: str
    retrieved_on: str = Field(pattern=DATE_PATTERN)


class IncomeManifest(Record):
    """What the folder holds, and which release it was made for."""

    release_id: ReleaseId
    synthetic: StrictBool
    income_sha256: Sha256
    income_bytes: int = Field(ge=0)
    source: IncomeSource


class AreaIncome(Record):
    """The publisher's figure for one area, in whole pounds a year, or that it gives none.

    An area that is not one of the publisher's own areas has no figure: nothing
    is added up, averaged or shared out to make one.
    """

    area_id: AreaId
    estimate: Pounds | None
    lower: Pounds | None
    upper: Pounds | None


class Income(Record):
    """The figure of every area of one release, of one kind of income, for one year."""

    release_id: ReleaseId
    synthetic: StrictBool
    # The first and the last month of the year the figures are of.
    start: str = Field(pattern=MONTH_PATTERN)
    end: str = Field(pattern=MONTH_PATTERN)
    source: IncomeSource
    areas: tuple[AreaIncome, ...]

    def of(self, area_id: str) -> AreaIncome | None:
        return next((area for area in self.areas if area.area_id == area_id), None)


class Words(Record):
    """The fixed words of the block. `{start}`, `{end}` and `{retrieved}` are filled in."""

    heading: Text
    intro: Text
    # The publisher's own name for the kind of income, and its own words for what that is.
    kind: Text
    definition: Text
    year_line: Text
    modelled: Text
    limits: Text
    # The two limits as they are printed, one after the other.
    between: Text
    notes: tuple[Text, ...]
    none_given: Text
    source_line: Text
    licence_line: Text
    open_source: Text


# The words for the statistics office's estimates. What is in quotation marks is the
# publisher's own, from the workbook and from its page of quality and methodology.
ONS = Words(
    heading="Household income, as the Office for National Statistics estimates it",
    intro=(
        "The statistics office's estimate of what the households of this area had as income "
        "in a year. It comes from a model, and is shown here and nowhere else. Burro never "
        "ranks, filters or compares areas by it."
    ),
    kind="Total annual household income",
    definition=(
        "The statistics office's definition: \"Total annual household income is the sum of "
        "the gross income of every member of the household plus any income from benefits such "
        'as Working Families Tax Credit."'
    ),
    year_line="Financial year ending {end}: {start} to {end}.",
    modelled=(
        "This is an estimate from a model, and no count of what anybody has. The statistics "
        'office calls these "model-based small area income estimates".'
    ),
    limits="Lower and upper confidence limits",
    between="{lower} to {upper}",
    notes=(
        "It is an average for the area: a mean, and not a median. It is not what any one "
        "household or person here has.",
        'The statistics office says: "A confidence interval gives an indication of the degree '
        "of uncertainty of an estimate and helps to decide how precise a sample estimate is. "
        'It specifies a range of values likely to contain the unknown population value."',
        "It is of one year. The statistics office asks for caution in reading any change over "
        "time, and Burro shows none.",
        "Nothing stands beside the figure: no other area, and no figure for the whole city. "
        "Burro says nothing about what it means.",
    ),
    none_given="The statistics office gives no estimate for this area.",
    source_line="Source: Office for National Statistics. Retrieved {retrieved}.",
    licence_line=(
        "Contains public sector information licensed under the Open Government Licence v3.0."
    ),
    open_source="The statistics office's page for these estimates",
)

# A made-up figure names no real publisher and no real year's events. Its words are as
# long as the real ones, so that a page laid out on it is laid out for the real one.
MADE_UP = Words(
    heading="A made-up estimate of household income",
    intro=(
        "A made-up estimate of what the households of this area had as income in a year. It "
        "is shown here and nowhere else. Burro never ranks, filters or compares areas by it."
    ),
    kind="Total annual household income, made up",
    definition=(
        'The definition a publisher would give: "The income of every member of a household '
        'in a year, added up, before tax."'
    ),
    year_line="A made-up year ending {end}: {start} to {end}.",
    modelled=(
        "This figure is made up. A real one is an estimate from a model, and no count of what "
        "anybody has, and says so here."
    ),
    limits="Lower and upper limits, made up",
    between="{lower} to {upper}",
    notes=(
        "It is an average for the area: a mean, and not a median. It is not what any one "
        "household or person here has.",
        "A real estimate quotes here what its publisher says of the limits round it.",
        "It is of one year. Burro shows no change over time.",
        "Nothing stands beside the figure: no other area, and no figure for the whole city. "
        "Burro says nothing about what it means.",
    ),
    none_given="The made-up estimates hold none for this area.",
    source_line="Source: made up by Burro for testing. Made on {retrieved}.",
    licence_line="Synthetic data generated by Burro for testing. It describes no real place.",
    open_source="The publisher's page for these estimates",
)

# Words that Burro would be choosing, and so never uses of the figure. None says that an
# area has much or little, or stands above or below another.
NEVER_SAID = frozenset(
    {
        "affluent",
        "rich",
        "poor",
        "wealthy",
        "deprived",
        "high",
        "low",
        "higher",
        "lower than",
        "above",
        "below",
        "more than",
        "less than",
        "typical",
        "well off",
    }
)


def words_of(synthetic: bool) -> Words:
    return MADE_UP if synthetic else ONS


def month_in_words(month: str) -> str:
    """`2023-03` as `March 2023`."""
    year, number = (int(part) for part in month.split("-"))
    return f"{_MONTHS[number - 1]} {year}"


def day_in_words(date: str) -> str:
    """`2026-09-24` as `24 September 2026`."""
    year, month, day = (int(part) for part in date.split("-"))
    return f"{day} {_MONTHS[month - 1]} {year}"


def pounds(amount: int) -> str:
    """`52300` as `£52,300`."""
    return f"£{amount:,}"


# ---------------------------------------------------------------------------
# What is served.
# ---------------------------------------------------------------------------


class IncomeOffer(Record):
    """What the closed block of an area's page says. It holds no figure and names no area."""

    available: StrictBool
    heading: str
    intro: str


NO_INCOME = IncomeOffer(available=False, heading="", intro="")


class IncomeShown(Record):
    """The figure of one area, as its page shows it. Every word but a button's is here.

    A figure is said in words, as it is to be printed: `£52,300`. `limits`
    holds both limits as they are printed, `£46,100 to £59,300`, so that no
    client joins two figures. Where the publisher gives none for the area,
    `estimate` and the limits are `None` and `none_given` says so.
    """

    area_id: AreaId
    heading: str
    kind: str
    definition: str
    estimate: str | None
    limits_label: str
    lower: str | None
    upper: str | None
    limits: str | None
    none_given: str | None
    year_line: str
    modelled: str
    notes: tuple[str, ...]
    source_line: str
    licence_line: str
    source_url: str
    open_source: str


def offer(income: Income | None) -> IncomeOffer:
    """What an area's page says before the figure is asked for."""
    if income is None:
        return NO_INCOME
    words = words_of(income.synthetic)
    return IncomeOffer(available=True, heading=words.heading, intro=words.intro)


def shown(income: Income, area_id: str) -> IncomeShown | None:
    """What the page of one area shows, or `None` where the file does not name the area."""
    area = income.of(area_id)
    if area is None:
        return None
    words = words_of(income.synthetic)
    given = area.estimate is not None
    limits = (
        words.between.format(lower=pounds(area.lower), upper=pounds(area.upper))
        if area.lower is not None and area.upper is not None
        else None
    )
    return IncomeShown(
        area_id=area.area_id,
        heading=words.heading,
        kind=words.kind,
        definition=words.definition,
        estimate=pounds(area.estimate) if area.estimate is not None else None,
        limits_label=words.limits,
        lower=pounds(area.lower) if area.lower is not None else None,
        upper=pounds(area.upper) if area.upper is not None else None,
        limits=limits,
        none_given=None if given else words.none_given,
        year_line=words.year_line.format(
            start=month_in_words(income.start), end=month_in_words(income.end)
        ),
        modelled=words.modelled,
        notes=words.notes,
        source_line=words.source_line.format(retrieved=day_in_words(income.source.retrieved_on)),
        licence_line=words.licence_line,
        source_url=income.source.url,
        open_source=words.open_source,
    )


# ---------------------------------------------------------------------------
# The one judge of the file.
# ---------------------------------------------------------------------------

Finding = tuple[str, str]


def income_is_of_the_release(
    income: Income, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    if income.release_id != release_id:
        yield INCOME, "release_id"
    if income.synthetic is not synthetic:
        yield INCOME, "synthetic"


def made_up_is_said(
    income: Income, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    """A made-up figure cites the reserved source and no other, and a real one never cites it."""
    if (income.source.source_id == SYNTHETIC_SOURCE_ID) is not income.synthetic:
        yield INCOME, "source"
    if bool(income.source.url) is income.synthetic:
        # A made-up estimate has no page to open, and a real one always has.
        yield INCOME, "source.url"
    for position, area in enumerate(income.areas):
        if area.area_id.startswith(SYNTHETIC_PREFIX) is not income.synthetic:
            yield INCOME, f"areas[{position}]"


def areas_are_the_releases(
    income: Income, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    """Every area of the release once, in the order of its id, and no other."""
    if [area.area_id for area in income.areas] != sorted(set(area_ids)):
        yield INCOME, "areas"


def _between(area: AreaIncome) -> bool:
    """Whether an area's estimate stands with both its limits, and between them."""
    if area.lower is None or area.estimate is None or area.upper is None:
        return False
    return area.lower <= area.estimate <= area.upper


def limits_hold_the_estimate(
    income: Income, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    """An estimate stands with both its limits and between them, or none of the three is given."""
    for position, area in enumerate(income.areas):
        nothing = area.lower is None and area.estimate is None and area.upper is None
        if not nothing and not _between(area):
            yield INCOME, f"areas[{position}]"


def year_is_a_year(
    income: Income, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Iterator[Finding]:
    """The figures are of twelve months, from the first to the last."""
    first, last = (
        tuple(int(part) for part in month.split("-")) for month in (income.start, income.end)
    )
    if (last[0] - first[0]) * 12 + last[1] - first[1] != 11:
        yield INCOME, "end"


RULES = (
    income_is_of_the_release,
    made_up_is_said,
    areas_are_the_releases,
    limits_hold_the_estimate,
    year_is_a_year,
)


def _refuse_constant(_: str) -> Any:
    raise ValueError("NaN and Infinity are not JSON")


def _parsed(name: str, content: bytes) -> object:
    try:
        return json.loads(content.decode("utf-8"), parse_constant=_refuse_constant)
    except ValueError:
        raise IncomeError(name, "json_is_valid") from None


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
        raise IncomeError(name, "shape_is_valid", _row(loc)) from None


def parse_income(
    document: object, release_id: str, synthetic: bool, area_ids: Sequence[str]
) -> Income:
    """The parsed content of `income.json`, held to every rule. The only parser."""
    income = _shaped(INCOME, Income, document)
    for rule in RULES:
        for file, row in rule(income, release_id, synthetic, area_ids):
            raise IncomeError(file, rule.__name__, row)
    return income


def open_income(
    folder_name: str,
    files: Mapping[str, bytes],
    release_id: str,
    synthetic: bool,
    area_ids: Sequence[str],
) -> Income:
    """Check the bytes of the folder, and hold it to the release it stands beside.

    It reads no file itself: the caller passes the bytes, by file name. The
    release is given as its id, whether it is made up, and the ids of its
    areas, and as nothing more: the figure is never handed a release.
    """
    if folder_name != f"{release_id}{INCOME_FOLDER}":
        raise IncomeError(MANIFEST, "folder_is_named_for_the_release")
    for name in (MANIFEST, INCOME):
        if name not in files:
            raise IncomeError(name, "files_match_manifest")
    for name in sorted(set(files) - {MANIFEST, INCOME}):
        raise IncomeError(name, "files_match_manifest")

    manifest = _shaped(MANIFEST, IncomeManifest, _parsed(MANIFEST, files[MANIFEST]))
    if manifest.release_id != release_id or manifest.synthetic is not synthetic:
        raise IncomeError(MANIFEST, income_is_of_the_release.__name__)
    content = files[INCOME]
    if (
        len(content) != manifest.income_bytes
        or hashlib.sha256(content).hexdigest() != manifest.income_sha256
    ):
        raise IncomeError(INCOME, "files_match_manifest")
    income = parse_income(_parsed(INCOME, content), release_id, synthetic, area_ids)
    if manifest.source != income.source:
        raise IncomeError(MANIFEST, "source_is_stated", "source")
    return income
