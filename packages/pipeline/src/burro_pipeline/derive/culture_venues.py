"""Culture nearby: the museums, galleries, theatres, cinemas, music venues and libraries in reach.

The venues come from one file of Overture Maps Places, which `culture_file.py`
reads: the kind and the point of each record, and nothing else of it. Which
category is which kind is in `culture_kinds.py`. Where homes are, how far a
venue may be, and what is done at the edge of London are in
`culture_reach.py`, which every measure of venues asks.

**A figure is about what is within reach of an area's homes, and not about
what lies inside its outline.** A theatre on a border serves both sides.

Three figures are worked out for every area:

| Figure | What it is | Its id |
|---|---|---|
| The count | Venues within 800 metres of home, as the mean over homes | `culture_venues` |
| The rate | Venues for each 1,000 homes within the same reach | `culture_venues_per_homes` |
| The kinds | How many of the six kinds are within 800 metres of home | `culture_kinds_nearby` |

Core holds the first two.

The count is shown and never ranked on. A wish for culture, and the vibe that
holds it, are ranked on the rate, as a wish for places to eat is. Core has no
feature for the kinds, so no release carries them.

**One venue with many records counts once.** The file may hold several records
of one institution: a museum, and again its wings and its rooms. Records of
one kind that stand within 25 metres of the first of them are one venue. The
records are taken from west to east, so the same file gives the same venues.
What this cannot do is said in `ONE_VENUE_WORDS`: an institution whose records
stand further apart counts more than once, and two venues of one kind within
25 metres of each other count as one. No name is read, so no record is
matched to another by its name. 25 metres is a choice and not a finding, and
no record is left out for how sure its publisher is of it: each is for a
person to look at again.

**When nought is a count.** The file is gathered from what businesses and
their visitors have put on the web, and nothing says that it holds every
place. A first look found that it holds less the further a place is from the
centre. So nought is read as a count only where the file is seen to hold
something: an output area with no venue within reach has a count of nought
where the file holds a record of any kind within the same reach, and has no
count where it holds none. An output area with no count adds nothing, and the
coverage of its area falls by its homes. Whether one record of any kind is
enough to show that the file would hold a venue is not settled.

**The edge of London.** The part of the file that is fetched reaches 2,000
metres beyond the homes of London, so a venue outside London within reach of
a home is in it. The homes outside London are in no file of the build. So the
edge is done as `culture_reach.py` does it for every measure of venues: an
output area with homes outside London within its reach has no count.

**What has not been looked at.** `culture_check.py` holds each figure against
how built up and how central an area is. On the part of release 2026-09-23.0
the count is mostly a map of the centre, the rate less so, and neither passes
the rule of the check. So the count is shown, and the rate is what is ranked
on. No person has looked at a sample of the records, and the figures have not
been held against a register.

Two records stand behind a figure. The row of evidence names the file of
places, the centres, the lookup and the homes, and the method. The row of the
catalogue holds the name, the unit, the day of the release and the sentence a
methods page prints.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_core.catalogue import RANKED_AS
from burro_core.facts import fact_id
from burro_core.ids import Dimension, FactKind, FeatureId, NativeResolution, Polarity
from burro_core.release import Metric

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_file, culture_reach
from burro_pipeline.derive.catalogue_row import catalogue_row
from burro_pipeline.derive.culture_file import Places, Venue, in_order
from burro_pipeline.derive.culture_kinds import KINDS, WORDS, Kind
from burro_pipeline.derive.culture_reach import (
    CODE,
    DECIMALS,
    METRES,
    PER,
    Reach,
    at_the_edge,
    figures,
    first_of_each,
    for_each_at,
    ground_of,
    rates,
    reach_of,
    within_at,
)
from burro_pipeline.derive.methods import Worked, row_of
from burro_pipeline.evidence.method import Kind as MadeBy
from burro_pipeline.evidence.method import Method
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.CULTURE_VENUES
FEATURE_OF_THE_RATE = FeatureId.CULTURE_VENUES_PER_HOMES
# What the rows of evidence call each figure. The first two are core's ids. Core has none
# for the third.
KEY = str(FEATURE)
KEY_OF_THE_RATE = str(FEATURE_OF_THE_RATE)
KEY_OF_THE_KINDS = "culture_kinds_nearby"
SOURCE = culture_file.SOURCE
PUBLISHER = culture_file.PUBLISHER
KEYED_BY = culture_file.KEYED_BY
CENSUS = 2021
# Records of one kind within this many metres of the first of them are one venue.
ONE_VENUE = 25
# How many records of any kind the file must hold within reach for nought to be a count.
SEEN = 1
# The slot every record of the file adds to, after one for each kind.
EVERY = len(KINDS)
UNIT, UNIT_OF_THE_RATE, UNIT_OF_THE_KINDS = "count", "per 1,000 homes", "kinds"
NAMED = "Museums, galleries, theatres, cinemas, music venues and libraries"
LABEL = f"{NAMED} within {METRES} m of home, in a straight line"
LABEL_OF_THE_RATE = f"{NAMED} for each {PER:,} homes within {METRES} m, in a straight line"
LABEL_OF_THE_KINDS = (
    f"Kinds of cultural venue within {METRES} m of home, in a straight line, of {len(KINDS)}"
)


def kinds_within_at(metres: int) -> Method:
    """The record of the third figure: how many kinds of venue are within reach."""
    return Method(
        derivation_id=f"kinds_within_{metres}m_at_homes@1",
        sentence=f"The number of kinds of place of which at least one stands within {metres} "
        "metres, in a straight line, of the point where the homes of each census output area are "
        f"taken to stand, as the mean over the area's homes at the census, {at_the_edge(metres)}",
        kind=MadeBy.MEASURED,
        parameters={"metres": metres, "enough_in_100": 50},
        code=CODE,
    )


METHOD, METHOD_OF_THE_RATE = within_at(METRES), for_each_at(METRES)
METHOD_OF_THE_KINDS = kinds_within_at(METRES)
METHODS: tuple[Method, ...] = (METHOD, METHOD_OF_THE_RATE, METHOD_OF_THE_KINDS)

# What is said in every sentence of a methods page: what is counted, from whom, and what not.
_COUNTED = (
    "records that release {release} of Overture Maps Places, of the {publisher}, as at {as_at}, "
    "gives a category of {kinds}, leaving out a record that its file says has closed for good "
    "and a record that also gives a category of a place of learning, and counting records of "
    "one kind within {one_venue} metres of the first of them as one venue"
)
_WHERE = (
    "within {metres} metres in a straight line of the point the statistics office gives as the "
    "centre of each census output area"
)
_NOUGHT = (
    "with nought read as a count only where the file holds a record of any kind within the "
    "same distance"
)
_HOW = (
    "given to {decimals} decimal place with a half taken upward: it is measured across whatever "
    "lies between and not along any street, a venue the file does not hold is not counted, and "
    "a venue that has closed and is still listed as open, or as nothing, is."
)
DEFINITION = (
    f"The number of venues, from the {_COUNTED}, {_WHERE}, as the mean over the area's homes at "
    f"the census of {{census}}, {_NOUGHT}, and {_HOW}"
)
DEFINITION_OF_THE_RATE = (
    f"The number of venues, from the {_COUNTED}, {_WHERE}, for each {{per}} homes at the census "
    f"of {{census}} within the same distance of the same point, each added up over the area's "
    f"homes before one is divided by the other, {_NOUGHT}, and {_HOW}"
)
DEFINITION_OF_THE_KINDS = (
    f"The number of kinds of venue, of {{six}}, of which at least one stands {_WHERE}, from the "
    f"{_COUNTED}, as the mean over the area's homes at the census of {{census}}, {_NOUGHT}, and "
    f"{_HOW}"
)

# What the product shows beside a figure. Each line has a name, so that a figure takes a
# line by what it says and never by where it stands.
ON_THE_FILE = (
    "It counts what the file lists, so a venue that has closed is counted unless the file says "
    "it has closed for good, which it says of almost none, and a venue the file does not hold "
    "is not counted."
)
GATHERED = (
    "The file is gathered from what businesses and others have put on the web and not from a "
    "register, so nothing says that it holds every venue, and a first look found that it holds "
    "less the further a place is from the centre."
)
BY_CATEGORY = (
    "A venue is what the category of its record says it is, and nothing is decided from a name, "
    "so a stage school that is filed as a theatre is counted as one unless its record also "
    "says that it teaches."
)
ONE_VENUE_WORDS = (
    f"Records of one kind that stand within {ONE_VENUE} metres of the first of them count as "
    "one venue, so an institution whose records stand further apart counts more than once, and "
    "two venues of one kind side by side count as one."
)
HOW_SURE = (
    "Nothing is left out for how sure the publisher is that a place exists, so a record it is "
    "not sure of counts as one it is sure of."
)
A_STRAIGHT_LINE = (
    "It is a straight line from where the homes of each small census area are taken to stand, "
    "and not a walk, so a railway, a river or a main road in between puts a venue further off "
    "than it is counted."
)
WHAT_IS_ON = (
    "It cannot say what is on, what it costs, when a venue is open, how large it is or how "
    "well it is thought of: a village hall that shows a film counts as a cinema where it is "
    "filed as one."
)
NOUGHT = (
    "Nought is given only where the file holds something of any kind within reach, and even "
    "there it means that the file lists no venue, which is not the same as there being none."
)
AT_THE_EDGE = (
    "Near the edge of London the homes of a small census area are left out of the figure where "
    "homes outside London are within reach of them, because the homes outside London are not "
    "counted, so the figure of an area at the edge rests on the homes further in."
)
AS_AT_THE_CENSUS = (
    "Homes are weighed as they stood at the last census, so where many homes have been built "
    "since, or stand empty, the figure leans to where homes were and not to where they are."
)
# The file states no period. The founder stated one on 2026-09-24, with this beside it.
OF_THE_RELEASE = (
    "The day it is as at is the day its publisher released the file, and not the day of each "
    "record: many records of the file were last changed years before it."
)
CANNOT_SEE = (
    OF_THE_RELEASE,
    ON_THE_FILE,
    GATHERED,
    BY_CATEGORY,
    ONE_VENUE_WORDS,
    HOW_SURE,
    A_STRAIGHT_LINE,
    WHAT_IS_ON,
    NOUGHT,
    AT_THE_EDGE,
    AS_AT_THE_CENSUS,
)
# What is said of the second figure alone, for each 1,000 homes within the same reach.
OF_THE_RATE = (
    "It divides the venues the file lists now by the homes of the last census, so where many "
    "homes have been built since it reads too high.",
    "It reads highest where few homes are, so an area of offices or of shops leads it.",
)
CANNOT_SEE_OF_THE_RATE = (*CANNOT_SEE, *OF_THE_RATE)
# What is said of the third figure alone: how many kinds are within reach.
OF_THE_KINDS = (
    "It says how many kinds of venue are within reach and not how many venues, so one small "
    "library counts as much as ten theatres.",
)
CANNOT_SEE_OF_THE_KINDS = (
    *(line for line in CANNOT_SEE if line != ONE_VENUE_WORDS),
    *OF_THE_KINDS,
)


@dataclass(frozen=True)
class Proposed:
    """What a row of the catalogue says of a figure, as it is measured.

    It is the row of no release: `Culture.metric` and
    `Culture.metric_of_the_rate` are. Core holds the count and the rate as
    they are said here, and has no feature for the kinds.
    """

    key: str
    label: str
    dimension: Dimension
    unit: str
    polarity: Polarity
    native_resolution: NativeResolution
    source_ids: tuple[str, ...]
    vintage: str
    rankable: bool
    definition: str


@dataclass(frozen=True)
class Culture:
    """The measure for every area of the spine, with what stands behind it."""

    # The count of each area, by its id. An area with no figure is here too, with its state.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # The venues for each 1,000 homes within the same reach.
    rate: Mapping[str, Worked]
    rows_of_the_rate: tuple[EvidenceRow, ...]
    # How many of the six kinds are within reach.
    kinds: Mapping[str, Worked]
    rows_of_the_kinds: tuple[EvidenceRow, ...]
    # What the rows of the catalogue say: the count, the rate and the kinds.
    proposed: tuple[Proposed, Proposed, Proposed]
    # The rows of the catalogue a release carries: the count, which is shown, and the rate,
    # which is ranked on.
    metric: Metric
    metric_of_the_rate: Metric
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    # What the file holds, record by record, and the venues those records are.
    places: Places
    venues: tuple[Venue, ...]
    # How many records were taken to be a venue that was counted already, by kind.
    records_of_one_venue: Mapping[Kind, int]
    reach: Reach
    # The venues within reach of each output area that has a count.
    counted: Mapping[str, float]
    # The output areas with no count because the file holds nothing at all within reach.
    nothing_seen: tuple[str, ...]
    geography: Geography


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return culture_file.is_the_file(name)


def core_holds_it() -> bool:
    """Whether core has a feature under the id the rows of the count are written under."""
    return KEY in {feature.value for feature in FeatureId}


def as_venues(records: Sequence[Venue]) -> tuple[tuple[Venue, ...], dict[Kind, int]]:
    """The venues that some records are, and how many records were a venue again, by kind.

    Records of one kind within `ONE_VENUE` metres of the first of them are one
    venue, which stands where the first stands and keeps every source that
    gave a record of it. The records are taken in the order of where they
    stand, so the order of a file changes nothing.
    """
    venues: list[Venue] = []
    again: Counter[Kind] = Counter()
    for kind in KINDS:
        of_kind = sorted((record for record in records if record.kind is kind), key=in_order)
        firsts = first_of_each([(one.longitude, one.latitude) for one in of_kind], ONE_VENUE)
        sources: dict[int, set[str]] = {}
        for place, first in enumerate(firsts):
            sources.setdefault(first, set()).update(of_kind[place].datasets)
            again[kind] += first != place
        venues += [
            Venue(
                of_kind[first].longitude,
                of_kind[first].latitude,
                kind,
                tuple(sorted(sources[first])),
                of_kind[first].confidence,
            )
            for first in sorted(sources)
        ]
    return tuple(sorted(venues, key=in_order)), {kind: again[kind] for kind in KINDS if again[kind]}


def _in_words() -> str:
    one = [f"a {WORDS[kind][0]}" for kind in KINDS]
    return f"{', '.join(one[:-1])} or {one[-1]}"


def definition_of(sentence: str, places: Places) -> str:
    """The sentence a methods page prints: what is counted, from whom, as at when, and what not."""
    return sentence.format(
        release=places.file.edition,
        publisher=PUBLISHER,
        as_at=places.as_at,
        kinds=_in_words(),
        one_venue=ONE_VENUE,
        metres=METRES,
        per=f"{PER:,}",
        six=len(KINDS),
        census=CENSUS,
        decimals=DECIMALS,
    )


def metrics_of(files: Sequence[Receipt], places: Places) -> tuple[Metric, Metric]:
    """The rows of the catalogue a release carries: of the count, and of the rate.

    Core decides which way is more. The name and the unit are the ones each
    figure supports, and core says the same. The count is shown, and no area
    is ranked on it: a wish for culture is ranked on the rate.
    """

    def row(feature: FeatureId, label: str, unit: str, method: Method, sentence: str) -> Metric:
        made = catalogue_row(
            feature,
            method=method,
            label=label,
            native_resolution=NativeResolution.POINT,
            source_ids={receipt.source_id for receipt in files},
            vintage=places.as_at,
            rankable=feature not in RANKED_AS,
            definition=definition_of(sentence, places),
        )
        # The unit is the one the figure supports, whatever core says of the measure.
        return made.replace(unit=unit)

    return (
        row(FEATURE, LABEL, UNIT, METHOD, DEFINITION),
        row(
            FEATURE_OF_THE_RATE,
            LABEL_OF_THE_RATE,
            UNIT_OF_THE_RATE,
            METHOD_OF_THE_RATE,
            DEFINITION_OF_THE_RATE,
        ),
    )


def proposed_of(files: Sequence[Receipt], places: Places) -> tuple[Proposed, Proposed, Proposed]:
    """What the three rows of the catalogue say.

    More is more culture nearby, as core has it. The rate alone is ranked on:
    the count is shown beside it, and core has no feature for the kinds.
    """
    sources = tuple(sorted({receipt.source_id for receipt in files}))

    def row(key: str, label: str, unit: str, sentence: str) -> Proposed:
        return Proposed(
            key=key,
            label=label,
            dimension=Dimension.VENUES_CULTURE,
            unit=unit,
            polarity=Polarity.MORE,
            native_resolution=NativeResolution.POINT,
            source_ids=sources,
            vintage=places.as_at,
            rankable=key == KEY_OF_THE_RATE,
            definition=definition_of(sentence, places),
        )

    return (
        row(KEY, LABEL, UNIT, DEFINITION),
        row(KEY_OF_THE_RATE, LABEL_OF_THE_RATE, UNIT_OF_THE_RATE, DEFINITION_OF_THE_RATE),
        row(KEY_OF_THE_KINDS, LABEL_OF_THE_KINDS, UNIT_OF_THE_KINDS, DEFINITION_OF_THE_KINDS),
    )


def _rows(
    key: str, worked: Mapping[str, Worked], method: Method, files: Sequence[Receipt]
) -> tuple[EvidenceRow, ...]:
    return tuple(
        row_of(fact_id(area, FactKind.FEATURE, key), worked[area], method, files)
        for area in sorted(worked)
    )


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Culture:
    """The figures of every area and their evidence, from the files of the build.

    The gate is asked about the places and about the centres before either is
    read. `found` is the spine of the same build: a row of evidence names its
    files beside the places and the centres, so they must be files this build
    opened. `edition` is the release of the places, as its receipt gives it.
    """
    places = culture_file.build(inputs, edition=edition)
    ground = ground_of(inputs, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    venues, again = as_venues(places.venues)
    points = [
        *((one.longitude, one.latitude, KINDS.index(one.kind), 1) for one in venues),
        *((longitude, latitude, EVERY, 1) for longitude, latitude in places.every),
    ]
    reach = reach_of(points, EVERY + 1, ground, found)
    of_kinds = range(EVERY)
    seen = {oa for oa, held in reach.within.items() if held[EVERY] >= SEEN}
    counted = {oa: count for oa, count in reach.of(of_kinds).items() if oa in seen}
    how_many = {oa: count for oa, count in reach.how_many_of(of_kinds).items() if oa in seen}
    behind = sorted({places.file.file_id, ground.placed.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    worked, rate = figures(counted, found), rates(counted, reach, found)
    kinds = figures(how_many, found)
    metric, metric_of_the_rate = metrics_of(files, places)
    return Culture(
        worked=worked,
        rows=_rows(KEY, worked, METHOD, files),
        rate=rate,
        rows_of_the_rate=_rows(KEY_OF_THE_RATE, rate, METHOD_OF_THE_RATE, files),
        kinds=kinds,
        rows_of_the_kinds=_rows(KEY_OF_THE_KINDS, kinds, METHOD_OF_THE_KINDS, files),
        proposed=proposed_of(files, places),
        metric=metric,
        metric_of_the_rate=metric_of_the_rate,
        files=files,
        places=places,
        venues=venues,
        records_of_one_venue=again,
        reach=reach,
        counted=counted,
        nothing_seen=tuple(sorted(set(reach.within) - seen)),
        geography=KEYED_BY,
    )


__all__ = ["Culture", "Proposed", "as_venues", "build", "culture_reach"]
