"""Places of worship nearby: the churches, mosques, synagogues, temples and gurdwaras in reach.

A person reaches a community through what is there. So a wish to live near a
mosque, a synagogue or a gurdwara is answered by where those buildings are,
and never by a count of who lives anywhere. This module counts the buildings.

The buildings come from one file of Overture Maps Places, which
`culture_file.py` reads: what each record says it is and where it stands, and
no name. Which category is which kind of building is in `worship_kinds.py`.
How buildings are counted within reach of homes is in `places_counted.py`,
which asks `culture_reach.py` as cultural venues do.

Seven figures are worked out for every area, each a count of buildings within
800 metres of home, in a straight line, as the mean over the area's homes:

| Figure | Its id |
|---|---|
| Places of worship, of any kind and of none named | `worship_places` |
| Churches | `worship_churches` |
| Mosques | `worship_mosques` |
| Synagogues | `worship_synagogues` |
| Hindu temples | `worship_hindu_temples` |
| Gurdwaras | `worship_gurdwaras` |
| Buddhist temples | `worship_buddhist_temples` |

**Three things this measure never does.** A test holds it to each.

1. **It is never turned into an estimate of who lives there.** A figure is a
   count of buildings. No figure is a share, a rate or a figure for each so
   many homes, and no file about who lives anywhere is opened. How many homes
   an area has changes no count of what is within reach of one of them.
2. **It is never added up into a score.** No kind is weighed against another,
   no figure says how many kinds are within reach, and no figure is part of a
   vibe. The one sum is the plain number of places of worship, each building
   counted once.
3. **It is never offered with a direction of fewer.** The one wish a figure
   answers is for a building nearby. No row says less, fewer, further or away.

**A record of which the file names no kind** counts toward places of worship
and toward none of the six. Where it stands within 25 metres of a building of
a kind, it is taken to be that building again and adds nothing. So the places
of worship of an output area are the buildings of the six kinds and the
buildings of no kind named, added up, each counted once.

**One building with many records counts once**, where they stand within 25
metres of the most westerly of them, as `places_counted.py` has it. Records of
one building that stand further apart count again, and `close_together` counts
the buildings of each kind that stand within 50 metres of another of the same
kind, for a person to look at.

**One building that is filed under two kinds** counts once under each, and so
twice among places of worship.

**The figures of the real file have been worked out, and none is put
forward.** Core holds no feature for any of the seven, so the measure is not
among those of a build, and no release carries it. `Proposed` says what the
rows of the catalogue would say. On the part of release 2026-09-23.0, places
of worship and churches are mostly a map of how built up an area is. The
five other kinds are not: there are few of each, and most areas read nought.
Nearly every record of each kind comes from one of the publisher's sources.
No register has been held against the file, and no person has looked at a
sample of the records.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_core.ids import FeatureId, FeatureKind

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_file, places_counted
from burro_pipeline.derive.culture_file import Record
from burro_pipeline.derive.culture_reach import (
    DECIMALS,
    METRES,
    Ground,
    ground_of,
    kept,
    within,
)
from burro_pipeline.derive.culture_venues import (
    AS_AT_THE_CENSUS,
    AT_THE_EDGE,
    OF_THE_RELEASE,
    ONE_VENUE,
)
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.places_counted import (
    METHOD,
    UNIT,
    Building,
    Held,
    Nearby,
    Proposed,
    as_buildings,
    close_together,
    in_order,
    nearby,
    proposed,
    rows_of,
)
from burro_pipeline.derive.worship_kinds import (
    KINDS,
    NAMED,
    WORDS,
    Kind,
    LeftOut,
    kind_of,
    said_beside,
)
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs

SOURCE = culture_file.SOURCE
PUBLISHER = culture_file.PUBLISHER
KEYED_BY = culture_file.KEYED_BY
CENSUS = 2021
# What the rows of evidence call each figure. Core has a feature for none of them.
KEY = "worship_places"
KEY_OF: dict[Kind, str] = {
    Kind.CHURCH: "worship_churches",
    Kind.MOSQUE: "worship_mosques",
    Kind.SYNAGOGUE: "worship_synagogues",
    Kind.HINDU_TEMPLE: "worship_hindu_temples",
    Kind.GURDWARA: "worship_gurdwaras",
    Kind.BUDDHIST_TEMPLE: "worship_buddhist_temples",
}
KEYS = (KEY, *KEY_OF.values())
_WITHIN = f"within {METRES} m of home, in a straight line"
LABEL = f"Places of worship {_WITHIN}"
LABEL_OF: dict[Kind, str] = {
    kind: f"{WORDS[kind][1][0].upper()}{WORDS[kind][1][1:]} {_WITHIN}" for kind in NAMED
}
# The wish, as a person is offered it. It asks for a building nearby and for nothing else.
OFFER = "A place of worship nearby"
OFFER_OF: dict[Kind, str] = {kind: f"A {WORDS[kind][0]} nearby" for kind in NAMED}
# What the publisher's category of each kind is, in the words of a sentence.
FILED_AS: dict[Kind, str] = {
    Kind.CHURCH: "a Christian place of worship",
    Kind.MOSQUE: "a Muslim place of worship",
    Kind.SYNAGOGUE: "a Jewish place of worship",
    Kind.HINDU_TEMPLE: "a Hindu place of worship",
    Kind.GURDWARA: "a Sikh place of worship",
    Kind.BUDDHIST_TEMPLE: "a Buddhist place of worship",
}

_COUNTED = (
    "records that release {release} of Overture Maps Places, of the {publisher}, as at {as_at}, "
    "gives a category of {filed_as}, leaving out a record that its file says has closed for "
    "good, and counting records of one kind within {one} metres of the first of them as one "
    "building"
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
    "given to {decimals} decimal place with a half taken upward: it is a count of buildings "
    "and of nothing else, it is measured across whatever lies between and not along any "
    "street, and a building the file does not hold is not counted."
)
DEFINITION = (
    f"The number of {{many}}, from the {_COUNTED}, {_WHERE}, as the mean over the area's homes "
    f"at the census of {{census}}, {_NOUGHT}, and {_HOW}"
)

# What the product shows beside a figure. Each line has a name, so that a figure takes a
# line by what it says and never by where it stands.
BUILDINGS = "It counts buildings and says nothing of who lives near them."
ON_THE_FILE = (
    "It counts what the file lists, so a building that has closed is counted unless the file "
    "says it has closed for good, which it says of almost none, and a building the file does "
    "not hold is not counted."
)
GATHERED = (
    "The file is gathered from what organisations and others have put on the web and not from "
    "a register, so nothing says that it holds every place of worship, and nobody has measured "
    "whether it holds the buildings of one kind as fully as those of another."
)
MEETS_ELSEWHERE = (
    "A group that meets to worship in a hall, a school, a shop front or a house is not "
    "counted, because the file lists such a place as what it is filed as."
)
BY_CATEGORY = (
    "A building is what the category of its record says it is, and nothing is decided from a "
    "name, so a building that is filed under the wrong kind is counted under it."
)
NO_KIND = (
    "A place of worship of which the file names no kind counts toward places of worship and "
    "toward no kind, so the count of a kind may be short of what is there."
)
OTHER_KINDS = (
    "The file has no category for a Jain temple, a Baha'i centre, a Zoroastrian temple or a "
    "Quaker meeting house, so none can be counted by its kind."
)
A_CHURCH = (
    "A church here is any building the file files as a Christian place of worship, so a "
    "chapel, a cathedral and a meeting house each count as one, and they are not told apart."
)
ONE_BUILDING = (
    f"Records of one kind that stand within {ONE_VENUE} metres of the first of them count as "
    "one building, so a building whose records stand further apart counts more than once, "
    "and two of one kind side by side count as one."
)
FILED_TWICE = (
    "A building that the file lists under two kinds counts once under each, and so twice "
    "among places of worship."
)
NOUGHT = (
    "Nought is given only where the file holds something of any kind within reach, and even "
    "there it means that the file lists no such building, which is not the same as there "
    "being none."
)
HOW_SURE = (
    "Nothing is left out for how sure the publisher is that a place exists, so a record it is "
    "not sure of counts as one it is sure of."
)
A_STRAIGHT_LINE = (
    "It is a straight line from where the homes of each small census area are taken to stand, "
    "and not a walk, so a railway, a river or a main road in between puts a building further "
    "off than it is counted."
)
WHAT_GOES_ON = (
    "It cannot say when a building is open, what is held there, how large it is or whether it "
    "has room."
)
CANNOT_SEE = (
    BUILDINGS,
    OF_THE_RELEASE,
    ON_THE_FILE,
    GATHERED,
    MEETS_ELSEWHERE,
    BY_CATEGORY,
    NO_KIND,
    OTHER_KINDS,
    ONE_BUILDING,
    FILED_TWICE,
    HOW_SURE,
    A_STRAIGHT_LINE,
    WHAT_GOES_ON,
    NOUGHT,
    AT_THE_EDGE,
    AS_AT_THE_CENSUS,
)
# What is said of the count of churches alone.
CANNOT_SEE_OF: dict[Kind, tuple[str, ...]] = {
    kind: (*CANNOT_SEE, A_CHURCH) if kind is Kind.CHURCH else CANNOT_SEE for kind in NAMED
}
# What keeps the measure out of a release, and whose each is to settle.
WAITS_ON = (
    "Core holds no feature for a place of worship, so no build can carry a figure. A feature "
    "for each, weighed on request only and in no vibe, brings the figures in.",
    "Whether the file holds the buildings of one kind as fully as those of another has not "
    "been measured, because no register is held against it, and until it has no figure of a "
    "kind is put forward to be ranked on. Nearly every record of each kind comes from one of "
    "the publisher's sources.",
    "Which category is which kind was decided from the publisher's table of categories and "
    "has not been held to a sample of records by a person.",
    "Whether a shrine, a monastery, a convent and a retreat are counted is a choice, and it is "
    "the founder's to settle.",
    "Whether 25 metres is the right distance for records to be one building is the founder's "
    "to settle. On the real file about one church in seven, and one gurdwara in seven, stands "
    "within 50 metres of another of its kind, and fewer of every other kind.",
)


@dataclass(frozen=True)
class Worship:
    """The measure for every area of the spine, with what stands behind it."""

    # The places of worship of each area, by its id. An area with no figure is here too.
    worked: Mapping[str, Worked]
    rows: tuple[EvidenceRow, ...]
    # The buildings of each of the six kinds.
    of_kind: Mapping[Kind, Mapping[str, Worked]]
    rows_of_kind: Mapping[Kind, tuple[EvidenceRow, ...]]
    # What the rows of the catalogue would say: the places of worship, then each kind.
    proposed: tuple[Proposed, ...]
    # The receipt of every file a figure was worked out from.
    files: tuple[Receipt, ...]
    # What the file holds, record by record, and the buildings those records are.
    held: Held
    buildings: tuple[Building, ...]
    # How many records were taken to be a building that was counted already, by kind.
    records_of_one_building: Mapping[Kind, int]
    # How many buildings of each kind stand within 50 metres of another of the same kind:
    # where one building may have been counted more than once. It changes no figure.
    close_together: Mapping[Kind, int]
    # How many records that are filed as something else name a place of worship beside it.
    said_beside: Mapping[Kind, int]
    nearby: Nearby
    geography: Geography


def is_the_file(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the file this measure reads."""
    return culture_file.is_the_file(name)


def core_holds_it() -> bool:
    """Whether core has a feature under any id the rows are written under."""
    return bool(set(KEYS) & {feature.value for feature in FeatureId})


def as_places(records: Sequence[Building]) -> tuple[tuple[Building, ...], dict[Kind, int]]:
    """The buildings that some records are, and how many records were a building again.

    The records of each of the six kinds are made into buildings first. A
    record of no kind named that stands within 25 metres of one of those is
    that building again. The rest of them are made into buildings among
    themselves.
    """
    kinds = [kind.value for kind in NAMED]
    named, again = as_buildings([one for one in records if one.kind in kinds], kinds)
    bare = sorted((one for one in records if one.kind == Kind.NO_KIND_NAMED), key=in_order)
    held = kept((each.longitude, each.latitude, 0, 1) for each in named)
    apart = [
        one for one in bare if not within(held, (one.longitude, one.latitude), ONE_VENUE, 1)[0]
    ]
    unnamed, among = as_buildings(apart, [Kind.NO_KIND_NAMED.value])
    found = Counter({Kind(kind): count for kind, count in again.items()})
    found[Kind.NO_KIND_NAMED] += len(bare) - len(apart) + sum(among.values())
    return (
        tuple(sorted((*named, *unnamed), key=in_order)),
        {kind: found[kind] for kind in KINDS if found[kind]},
    )


def definition_of(many: str, filed_as: str, held: Held) -> str:
    """The sentence a methods page prints: what is counted, from whom, as at when, and what not."""
    return DEFINITION.format(
        many=many,
        filed_as=filed_as,
        release=held.file.edition,
        publisher=PUBLISHER,
        as_at=held.as_at,
        one=ONE_VENUE,
        metres=METRES,
        census=CENSUS,
        decimals=DECIMALS,
    )


def proposed_of(files: Sequence[Receipt], held: Held) -> tuple[Proposed, ...]:
    """What the seven rows of the catalogue would say.

    Each is weighed on request only, so that no vibe may hold it, and more is
    its one direction. None is put forward to be ranked on: no register has
    been held against the file.
    """

    def row(key: str, label: str, offer: str, many: str, filed_as: str) -> Proposed:
        return proposed(
            key,
            label,
            offer,
            definition_of(many, filed_as, held),
            files,
            held.as_at,
            kind=FeatureKind.ON_REQUEST,
            in_a_vibe=False,
        )

    return (
        row(KEY, LABEL, OFFER, "places of worship", "a place of worship"),
        *(
            row(KEY_OF[kind], LABEL_OF[kind], OFFER_OF[kind], WORDS[kind][1], FILED_AS[kind])
            for kind in NAMED
        ),
    )


def read(inputs: Inputs, *, edition: str | None = None) -> tuple[Held, dict[Kind, int]]:
    """What the file of places holds of places of worship. The gate is asked first.

    It gives back, beside the records, how many records that are filed as
    something else name a place of worship beside it, by kind.
    """
    beside: Counter[Kind] = Counter()

    def decide(record: Record) -> Kind | LeftOut:
        found = kind_of(record.primary, record.hierarchy)
        named = said_beside(record.alternates) if found is LeftOut.NOT_WORSHIP else None
        if named is not None:
            beside[named] += 1
        return found

    held = places_counted.read(
        culture_file.opened_of(inputs, edition=edition),
        decide,
        KINDS,
        (LeftOut.NOT_WORSHIP, LeftOut.NO_CATEGORY),
    )
    return held, {kind: beside[kind] for kind in KINDS if beside[kind]}


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Worship:
    """The figures of every area and their evidence, from the files of the build.

    The gate is asked about the places and about the centres before either is
    read. `found` is the spine of the same build: a row of evidence names its
    files beside the places and the centres, so they must be files this build
    opened. `edition` is the release of the places, as its receipt gives it.
    """
    held, beside = read(inputs, edition=edition)
    ground: Ground = ground_of(inputs, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    buildings, again = as_places(held.records)
    kinds = [kind.value for kind in KINDS]
    counted = nearby(buildings, held.every, kinds, ground, found, added_up=True)
    if counted.of_all is None:
        raise ValueError("the places of worship of an area are its buildings of every kind")
    close = close_together(buildings, kinds)
    behind = sorted({held.file.file_id, ground.placed.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    of_kind = {kind: counted.of_kind[kind.value] for kind in NAMED}
    return Worship(
        worked=counted.of_all,
        rows=rows_of(KEY, counted.of_all, files),
        of_kind=of_kind,
        rows_of_kind={kind: rows_of(KEY_OF[kind], of_kind[kind], files) for kind in NAMED},
        proposed=proposed_of(files, held),
        files=files,
        held=held,
        buildings=buildings,
        records_of_one_building=again,
        close_together={Kind(kind): count for kind, count in close.items()},
        said_beside=beside,
        nearby=counted,
        geography=KEYED_BY,
    )


__all__ = ["METHOD", "UNIT", "Worship", "as_places", "build", "read"]
