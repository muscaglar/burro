"""Community centres and cultural centres nearby: the buildings of each within reach of home.

The file of places has a category for a community centre and one for a
cultural centre. This module counts the buildings of each, as
`worship_nearby.py` counts places of worship and by the same rules: the most
particular category of a record decides, no name is read, one building with
many records counts once, and a figure is a count of buildings within 800
metres of home, in a straight line.

Two figures are worked out for every area:

| Figure | Its id | The publisher's category |
|---|---|---|
| Community centres | `community_centres` | `community_center` |
| Cultural centres | `cultural_centres` | `cultural_center` |

The publisher files the first under `community_and_government`, in its branch
`social_or_community_service`, and the second under `cultural_and_historic`.

**A cultural centre is counted as a cultural centre, and of no named
culture.** The file's category says that a building is a cultural centre and
does not say whose. A name would say, and no name is read. So the figure
cannot tell one cultural centre from another, and it is never a count of the
centres of any one community.

**The two are not added up.** A community centre is a hall that anyone may
hire or walk in to. A cultural centre is of one culture or of the arts. They
are two figures, and no figure is both: `nearby` is asked for none.

**What the measure never does** is what `worship_nearby.py` never does: a
figure is never an estimate of who lives anywhere, never part of a score of
how much of a community an area has, and never offered with a direction of
fewer.

What is left out, though it stands beside a centre in the publisher's tree:
a civic centre, which is a building of a council, a social club, which is for
its members, and a youth organisation, which is a body and no place. So is
everything else the publisher files under `community_and_government`: an
office of government, a service, a utility, a charity.

**A scout hall is not counted.** The publisher has a category of its own for
one, `scout_hall`, beside the community centre, and this release files more
records under it than under the community centre. A first look at an earlier
release found that half the records under a community hall were scout groups
from one feed. A scout hall that is filed as a community centre is still
counted here as one, because no name is read.

**Where the table comes from.** The publisher's own table of categories for
release 2026-09-23.0, read on 2026-09-24 through a reader that extracts the
text of a page. It was asked for these branches twice, in different words.
Both answers gave the two categories that are counted, each under the parent
written above, and the categories that are named as left out. One answer
alone gave a category of its own for a scout hall, and the rest of the branch
of social and community services. No person has seen the table.

**The table has been held to a file.** In the part of release 2026-09-23.0
round London, 48 categories under `community_and_government` are the most
particular of a record. One is counted, the community centre. Two were on
the table as left out. The other 45 had not been met. Two of them are
parents of the community centre and say no kind. 43 are now left out by
name, in `ELSEWHERE`, with three more that the part holds only as the parent
of another. So a record under `community_and_government` is counted, or is
left out by the name of its category, or stops the build. The cultural centre
stands under another top, which the table of places of worship holds to the
file. `test_community_on_the_real_files.py` holds this table to the part.

**The figures of the real file have been worked out, and neither is put
forward.** Core holds no feature for either, so the measure is not among
those of a build. On the part of release 2026-09-23.0 each count is partly a
map of the centre. No person has looked at a sample of the records.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from burro_core.ids import FeatureId, FeatureKind

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import culture_file, places_counted
from burro_pipeline.derive.culture_file import Record
from burro_pipeline.derive.culture_kinds import NotOnTheTable
from burro_pipeline.derive.culture_reach import DECIMALS, METRES, ground_of
from burro_pipeline.derive.culture_venues import (
    AS_AT_THE_CENSUS,
    AT_THE_EDGE,
    OF_THE_RELEASE,
    ONE_VENUE,
)
from burro_pipeline.derive.methods import Worked
from burro_pipeline.derive.places_counted import (
    Building,
    Held,
    Nearby,
    Proposed,
    as_buildings,
    close_together,
    nearby,
    proposed,
    rows_of,
)
from burro_pipeline.evidence.receipt import Geography, Receipt
from burro_pipeline.evidence.row import EvidenceRow
from burro_pipeline.inputs import Inputs


class Kind(StrEnum):
    """The two kinds of centre that are counted, in the order a figure lists them."""

    COMMUNITY_CENTRE = "community_centre"
    CULTURAL_CENTRE = "cultural_centre"


class LeftOut(StrEnum):
    """Why a record is not counted. Each is counted."""

    # Its most particular category is no centre. It is most of any file.
    NOT_A_CENTRE = "not_a_centre"
    # The file gives it no category at all.
    NO_CATEGORY = "no_category"
    # Its category stands beside a centre in the publisher's tree, and is none.
    BESIDE = "beside"
    # Its most particular category is a parent of the community centre, and says no kind.
    PARENT_ALONE = "parent_alone"


KINDS = tuple(Kind)
WORDS: dict[Kind, tuple[str, str]] = {
    Kind.COMMUNITY_CENTRE: ("community centre", "community centres"),
    Kind.CULTURAL_CENTRE: ("cultural centre", "cultural centres"),
}
# The categories that are counted, as the publisher writes them.
IS: dict[str, Kind] = {
    "community_center": Kind.COMMUNITY_CENTRE,
    "cultural_center": Kind.CULTURAL_CENTRE,
}
# The categories that stand beside a centre and are none, each with why.
BESIDE_A_CENTRE: dict[str, str] = {
    "civic_center": "a building of a council",
    "social_club": "a club for its members",
    "country_club": "a club for its members",
    "fraternal_organization": "a club for its members",
    "veterans_organization": "a club for its members",
    "youth_organization": "a body, and no place",
}
_A_BODY = "a body, and no place"
_AN_OFFICE = "an office of government"
_A_SERVICE = "a service, and no hall"
_A_UTILITY = "a utility"
_OF_SAFETY = "a service of public safety"
_IN_THE_OPEN = "a thing in the street, and no hall"
# What else the publisher files under `community_and_government`, each with why it is no
# centre. Every one is in a path of the part of release 2026-09-23.0 round London, and none
# was on the table before the table was held to it.
ELSEWHERE: dict[str, str] = {
    "civic_organization": _A_BODY,
    "charity_organization": _A_BODY,
    "labor_union": _A_BODY,
    "non_governmental_association": _A_BODY,
    "political_organization": _A_BODY,
    "political_party_office": "an office of a party",
    "government_office": _AN_OFFICE,
    "chambers_of_commerce": _A_BODY,
    "courthouse": _AN_OFFICE,
    "embassy": _AN_OFFICE,
    "government_department": _AN_OFFICE,
    "department_of_motor_vehicles": _AN_OFFICE,
    "health_department": _AN_OFFICE,
    "immigration_and_naturalization_office": _AN_OFFICE,
    "pension_office": _AN_OFFICE,
    "registry_office": _AN_OFFICE,
    "social_security_service": _AN_OFFICE,
    "tax_office": _AN_OFFICE,
    "town_hall": _AN_OFFICE,
    "military_site": "a site of the armed forces",
    "public_facility": _IN_THE_OPEN,
    "public_fountain": _IN_THE_OPEN,
    "public_plaza": _IN_THE_OPEN,
    "public_restroom": _IN_THE_OPEN,
    "public_safety_service": _OF_SAFETY,
    "fire_station": _OF_SAFETY,
    "jail_or_prison": _OF_SAFETY,
    "police_station": _OF_SAFETY,
    "public_utility": _A_UTILITY,
    "electric_utility_provider": _A_UTILITY,
    "garbage_collection_service": _A_UTILITY,
    "natural_gas_utility_provider": _A_UTILITY,
    "septic_service": _A_UTILITY,
    "water_utility_provider": _A_UTILITY,
    "child_protection_service": _A_SERVICE,
    "disability_services_and_support_organization": _A_SERVICE,
    "food_bank": _A_SERVICE,
    "foster_care_service": _A_SERVICE,
    "gay_and_lesbian_services_organization": _A_SERVICE,
    "homeless_shelter": _A_SERVICE,
    "housing_authority": _A_SERVICE,
    "scout_hall": "a hall of a scout group, which the publisher files apart from a centre",
    "senior_citizen_service": _A_SERVICE,
    "social_and_human_service": _A_SERVICE,
    "social_welfare_center": _A_SERVICE,
    "volunteer_association": _A_BODY,
}
# Every category that is left out by its name, with why.
IS_NOT: dict[str, str] = {**BESIDE_A_CENTRE, **ELSEWHERE}
# The top of the branch that holds the community centre, as the publisher writes it, and
# the category between the two. A record whose most particular category is one of these
# says no kind, and is left out.
TOP = "community_and_government"
PARENTS = frozenset({TOP, "social_or_community_service"})

SOURCE = culture_file.SOURCE
PUBLISHER = culture_file.PUBLISHER
KEYED_BY = culture_file.KEYED_BY
CENSUS = 2021
KEY_OF: dict[Kind, str] = {
    Kind.COMMUNITY_CENTRE: "community_centres",
    Kind.CULTURAL_CENTRE: "cultural_centres",
}
KEYS = tuple(KEY_OF.values())
_WITHIN = f"within {METRES} m of home, in a straight line"
LABEL_OF: dict[Kind, str] = {
    Kind.COMMUNITY_CENTRE: f"Community centres {_WITHIN}",
    Kind.CULTURAL_CENTRE: f"Cultural centres {_WITHIN}",
}
OFFER_OF: dict[Kind, str] = {kind: f"A {WORDS[kind][0]} nearby" for kind in KINDS}
# What a person may ask of each. A community centre is a place to meet, and may be one kind
# of several in a vibe of places to meet. A cultural centre is weighed on request only.
ASKED_AS: dict[Kind, FeatureKind] = {
    Kind.COMMUNITY_CENTRE: FeatureKind.AMENITY,
    Kind.CULTURAL_CENTRE: FeatureKind.ON_REQUEST,
}

DEFINITION = (
    "The number of {many}, from the records that release {release} of Overture Maps Places, of "
    "the {publisher}, as at {as_at}, gives a category of a {one_of}, leaving out a record that "
    "its file says has closed for good, and counting records of one kind within {one} metres "
    "of the first of them as one building, within {metres} metres in a straight line of the "
    "point the statistics office gives as the centre of each census output area, as the mean "
    "over the area's homes at the census of {census}, with nought read as a count only where "
    "the file holds a record of any kind within the same distance, and given to {decimals} "
    "decimal place with a half taken upward: it is a count of buildings and of nothing else, "
    "it is measured across whatever lies between and not along any street, and a building the "
    "file does not hold is not counted."
)

BUILDINGS = "It counts buildings and says nothing of who lives near them."
ON_THE_FILE = (
    "It counts what the file lists, so a centre that has closed is counted unless the file "
    "says it has closed for good, which it says of almost none, and a centre the file does not "
    "hold is not counted."
)
GATHERED = (
    "The file is gathered from what organisations and others have put on the web and not from "
    "a register, so nothing says that it holds every centre."
)
BY_CATEGORY = (
    "A building is what the category of its record says it is, and nothing is decided from a "
    "name, so a scout hut or a church hall that is filed as a community centre is counted as "
    "one."
)
WHOSE = (
    "It cannot say whose a cultural centre is: the file says that a building is a cultural "
    "centre and not of which culture, and no name is read."
)
ONE_BUILDING = (
    f"Records of one kind that stand within {ONE_VENUE} metres of the first of them count as "
    "one building, so a building whose records stand further apart counts more than once, "
    "and two of one kind side by side count as one."
)
NOUGHT = (
    "Nought is given only where the file holds something of any kind within reach, and even "
    "there it means that the file lists no such centre, which is not the same as there being "
    "none."
)
A_STRAIGHT_LINE = (
    "It is a straight line from where the homes of each small census area are taken to stand, "
    "and not a walk, so a railway, a river or a main road in between puts a building further "
    "off than it is counted."
)
WHAT_GOES_ON = (
    "It cannot say what is on, when a centre is open, what it costs to hire or whether a "
    "group that meets there has room."
)
CANNOT_SEE = (
    BUILDINGS,
    OF_THE_RELEASE,
    ON_THE_FILE,
    GATHERED,
    BY_CATEGORY,
    ONE_BUILDING,
    A_STRAIGHT_LINE,
    WHAT_GOES_ON,
    NOUGHT,
    AT_THE_EDGE,
    AS_AT_THE_CENSUS,
)
CANNOT_SEE_OF: dict[Kind, tuple[str, ...]] = {
    Kind.COMMUNITY_CENTRE: CANNOT_SEE,
    Kind.CULTURAL_CENTRE: (*CANNOT_SEE, WHOSE),
}
WAITS_ON = (
    "Core holds no feature for a community centre or for a cultural centre, so no build can "
    "carry a figure.",
    "A first look at an earlier release found that half the records under a community hall "
    "were scout groups from one feed. This release has a category of its own for a scout hall, "
    "which is left out, and how many scout halls are still filed as a community centre cannot "
    "be asked of a file that holds no name.",
    "Which category is which kind was decided from the publisher's table of categories and "
    "has not been held to a sample of records by a person.",
)


def kind_of(primary: str | None, hierarchy: tuple[str, ...]) -> Kind | LeftOut:
    """What a record is, by its most particular category: a kind, or why it is none.

    Raises `NotOnTheTable` for a category that the table does not hold and
    that stands under `community_and_government`, or under one that is counted.
    """
    if primary is None or primary == "":
        return LeftOut.NO_CATEGORY
    kind = IS.get(primary)
    if kind is not None:
        return kind
    if primary in PARENTS:
        return LeftOut.PARENT_ALONE
    if primary in IS_NOT:
        return LeftOut.BESIDE
    if (set(IS) | {TOP}) & set(hierarchy):
        raise NotOnTheTable
    return LeftOut.NOT_A_CENTRE


@dataclass(frozen=True)
class Centres:
    """The measure for every area of the spine, with what stands behind it."""

    of_kind: Mapping[Kind, Mapping[str, Worked]]
    rows_of_kind: Mapping[Kind, tuple[EvidenceRow, ...]]
    # What the rows of the catalogue would say, in the order of the kinds.
    proposed: tuple[Proposed, ...]
    files: tuple[Receipt, ...]
    held: Held
    buildings: tuple[Building, ...]
    records_of_one_building: Mapping[Kind, int]
    # How many centres of each kind stand within 50 metres of another of the same kind:
    # where one centre may have been counted more than once. It changes no figure.
    close_together: Mapping[Kind, int]
    nearby: Nearby
    geography: Geography


def core_holds_it() -> bool:
    """Whether core has a feature under any id the rows are written under."""
    return bool(set(KEYS) & {feature.value for feature in FeatureId})


def definition_of(kind: Kind, held: Held) -> str:
    """The sentence a methods page prints: what is counted, from whom, as at when, and what not."""
    return DEFINITION.format(
        many=WORDS[kind][1],
        one_of=WORDS[kind][0],
        release=held.file.edition,
        publisher=PUBLISHER,
        as_at=held.as_at,
        one=ONE_VENUE,
        metres=METRES,
        census=CENSUS,
        decimals=DECIMALS,
    )


def proposed_of(files: Sequence[Receipt], held: Held) -> tuple[Proposed, ...]:
    """What the two rows of the catalogue would say. Neither is put forward to be ranked on."""
    return tuple(
        proposed(
            KEY_OF[kind],
            LABEL_OF[kind],
            OFFER_OF[kind],
            definition_of(kind, held),
            files,
            held.as_at,
            kind=ASKED_AS[kind],
            in_a_vibe=ASKED_AS[kind] is not FeatureKind.ON_REQUEST,
        )
        for kind in KINDS
    )


def read(inputs: Inputs, *, edition: str | None = None) -> Held:
    """What the file of places holds of centres. The gate is asked before the file is opened."""

    def decide(record: Record) -> Kind | LeftOut:
        return kind_of(record.primary, record.hierarchy)

    return places_counted.read(
        culture_file.opened_of(inputs, edition=edition),
        decide,
        KINDS,
        (LeftOut.NOT_A_CENTRE, LeftOut.NO_CATEGORY),
    )


def build(inputs: Inputs, found: Spine, *, edition: str | None = None) -> Centres:
    """The figures of every area and their evidence, from the files of the build.

    The gate is asked about the places and about the centres of the output
    areas before either is read. `found` is the spine of the same build.
    """
    held = read(inputs, edition=edition)
    ground = ground_of(inputs, found)
    handed = {one.file_id: one.receipt for one in inputs.opened}
    if not set(found.inputs) <= set(handed):
        raise ValueError("the spine is made from files of this build")
    kinds = [kind.value for kind in KINDS]
    buildings, again = as_buildings(held.records, kinds)
    counted = nearby(buildings, held.every, kinds, ground, found, added_up=False)
    close = close_together(buildings, kinds)
    behind = sorted({held.file.file_id, ground.placed.file_id, *found.inputs})
    files = tuple(handed[file_id] for file_id in behind)
    of_kind = {kind: counted.of_kind[kind.value] for kind in KINDS}
    return Centres(
        of_kind=of_kind,
        rows_of_kind={kind: rows_of(KEY_OF[kind], of_kind[kind], files) for kind in KINDS},
        proposed=proposed_of(files, held),
        files=files,
        held=held,
        buildings=buildings,
        records_of_one_building={Kind(kind): count for kind, count in again.items()},
        close_together={Kind(kind): count for kind, count in close.items()},
        nearby=counted,
        geography=KEYED_BY,
    )
