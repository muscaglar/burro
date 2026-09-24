"""The kinds of place of worship: which of the publisher's categories is which, and which is none.

Overture Maps gives every place a category from a tree of its own. A place
has its most particular category as `taxonomy.primary`, and the path to it
from the top of the tree as `taxonomy.hierarchy`. This module is the table
that says what each category of a place of worship is to Burro. It reads no
file and holds no name of any place.

**A kind is a kind of building.** The table says that a building is a church,
a mosque, a synagogue, a Hindu temple, a gurdwara or a Buddhist temple. It
says nothing of who goes there and nothing of who lives near it.

**The most particular category of a record decides, and nothing else does.**
No rule is made from a name: a name is not read.

1. The publisher's tree holds one branch for places of worship,
   `cultural_and_historic > place_of_worship`, and six branches under it. Each
   of the six is a kind, with everything that stands under it: a Baptist
   church and a Greek Orthodox church are each a church.
2. A record whose most particular category is `place_of_worship`, and no
   more, is a place of worship of which the file names no kind. It counts
   toward the places of worship within reach, and toward none of the six.
3. Three branches of religion stand beside places of worship in the
   publisher's tree: a landmark, such as a shrine or a site of pilgrimage, an
   organisation, such as a convent or a seminary, and a retreat. The publisher
   files each apart from a place of worship, and so none is counted. Each is
   counted as left out, by its category.
4. Three more stand beside them under `cultural_and_historic`: a historic
   site, a memorial and a cultural centre. None is a place of worship, and
   each is left out by the name of its category.
5. A category anywhere under `cultural_and_historic` that the table does not
   hold stops the build, so that a person says what a new category is. It is
   never counted and never dropped by a guess. That holds of a branch that is
   left out as of a branch that is counted: a new category may be a kind of
   place of worship that the publisher has filed beside the others.
6. What else a record says of itself, beside its most particular category,
   decides nothing. A community centre that also gives a category of a place
   of worship is a community centre. Such records are counted, so that a
   person can see how many the rule passes by.

**What the tree does not hold.** As far as it was read, it has no category of
a place of worship for any belief but the six. A building of another belief
is filed under `place_of_worship` alone, or under a shrine, or under
something else, and the table cannot tell which. So the table cannot count
such a building by its kind, and `CANNOT_NAME` says so.

**Where the table comes from.** The publisher's own table of categories for
release 2026-09-23.0, at `docs.overturemaps.org/taxonomy/2026-09-23.0/taxonomy.csv`,
read on 2026-09-24 through a reader that extracts the text of a page. An
extraction is not the page. The reader was asked for the branches of
worship twice, in different words, and gave the same 73 rows both times:
every category here is from those rows. It said both times that no other
category of the table, as far as it read, holds the word church, mosque,
synagogue, temple, gurdwara, chapel or worship. It read the table as far as
its branch for health care, and the branches after it were not read. No
person has seen the table.

**The table has been held to a file.** In the part of release 2026-09-23.0
round London, 24 categories under `cultural_and_historic` are the most
particular of a record. 13 are counted, and each was on the table as it was
first read. One was on it as left out, `religious_organization`. The other
ten had not been met: nine of a historic site or of a memorial, and the
cultural centre. Each is now left out by name, in `NO_WORSHIP`, with
`memorial_site`, which the part holds only as the parent of another. So a
record under `cultural_and_historic` is counted, or is left out by the name
of its category, or stops the build. 42 categories that are counted, and 17
that are left out, are on the table and in no record of the part: the part
tells apart five denominations of church and no branch of any other kind, and
holds no shrine, no monastery, no convent and no retreat under a category of
its own. `test_community_on_the_real_files.py` holds the table to the part.

**What the choices are, and whose.** Each is the founder's to change:

- A church is every building the publisher files as a Christian place of
  worship: a chapel, a cathedral, a meeting house and a Kingdom Hall among
  them. The denominations under it are read and are not told apart.
- A shrine, a monastery, a convent, an ashram and a Zen centre are not
  counted, because the publisher files each apart from a place of worship.
"""

from enum import StrEnum

from burro_pipeline.derive.culture_kinds import NotOnTheTable


class Kind(StrEnum):
    """The kinds of building that are counted, in the order a figure lists them."""

    CHURCH = "church"
    MOSQUE = "mosque"
    SYNAGOGUE = "synagogue"
    HINDU_TEMPLE = "hindu_temple"
    GURDWARA = "gurdwara"
    BUDDHIST_TEMPLE = "buddhist_temple"
    # A place of worship of which the file names no kind. It counts toward the total alone.
    NO_KIND_NAMED = "no_kind_named"


class LeftOut(StrEnum):
    """Why a record is not counted. Each is counted."""

    # Its most particular category is no category of a place of worship. It is most of a file.
    NOT_WORSHIP = "not_worship"
    # The file gives it no category at all.
    NO_CATEGORY = "no_category"
    # It stands in a branch the publisher files beside places of worship.
    BESIDE = "beside"


# The six kinds that a figure names, in the order a figure lists them.
NAMED = tuple(kind for kind in Kind if kind is not Kind.NO_KIND_NAMED)
KINDS = tuple(Kind)
# What a kind is called in a sentence, one and many.
WORDS: dict[Kind, tuple[str, str]] = {
    Kind.CHURCH: ("church", "churches"),
    Kind.MOSQUE: ("mosque", "mosques"),
    Kind.SYNAGOGUE: ("synagogue", "synagogues"),
    Kind.HINDU_TEMPLE: ("Hindu temple", "Hindu temples"),
    Kind.GURDWARA: ("gurdwara", "gurdwaras"),
    Kind.BUDDHIST_TEMPLE: ("Buddhist temple", "Buddhist temples"),
    Kind.NO_KIND_NAMED: ("place of worship", "places of worship"),
}

# The category every place of worship stands under, as the publisher writes it.
PLACE_OF_WORSHIP = "place_of_worship"
# The category at the head of each kind's branch. Each stands directly under
# `cultural_and_historic > place_of_worship`.
HEAD: dict[Kind, str] = {
    Kind.CHURCH: "christian_place_of_worship",
    Kind.MOSQUE: "muslim_place_of_worship",
    Kind.SYNAGOGUE: "jewish_place_of_worship",
    Kind.HINDU_TEMPLE: "hindu_place_of_worship",
    Kind.GURDWARA: "sikh_place_of_worship",
    Kind.BUDDHIST_TEMPLE: "buddhist_place_of_worship",
}
# What stands under each head, however deep, as the publisher writes it.
UNDER: dict[Kind, tuple[str, ...]] = {
    Kind.CHURCH: (
        "church_of_the_east_place_of_worship",
        "eastern_orthodox_place_of_worship",
        "antiochan_orthodox_place_of_worship",
        "bulgarian_orthodox_place_of_worship",
        "georgian_orthodox_place_of_worship",
        "greek_orthodox_place_of_worship",
        "romanian_orthodox_place_of_worship",
        "russian_orthodox_place_of_worship",
        "serbian_orthodox_place_of_worship",
        "oriental_orthodox_place_of_worship",
        "armenian_apostolic_place_of_worship",
        "coptic_orthodox_place_of_worship",
        "eritrean_orthodox_tewahedo_place_of_worship",
        "ethiopian_orthodox_tewahedo_place_of_worship",
        "malankara_orthodox_syrian_place_of_worship",
        "syriac_orthodox_place_of_worship",
        "protestant_place_of_worship",
        "adventist_place_of_worship",
        "anabaptist_place_of_worship",
        "anglican_or_episcopal_place_of_worship",
        "baptist_place_of_worship",
        "lutheran_place_of_worship",
        "methodist_place_of_worship",
        "pentecostal_place_of_worship",
        "reformed_or_calvinist_place_of_worship",
        "restorationist_place_of_worship",
        "jehovahs_witness_place_of_worship",
        "mormon_place_of_worship",
        "roman_catholic_place_of_worship",
        "eastern_catholic_place_of_worship",
        "western_catholic_place_of_worship",
    ),
    Kind.MOSQUE: (
        "ibadi_muslim_place_of_worship",
        "shia_muslim_place_of_worship",
        "sunni_muslim_place_of_worship",
    ),
    Kind.SYNAGOGUE: (
        "conservative_jewish_place_of_worship",
        "orthodox_jewish_place_of_worship",
        "reconstructionist_jewish_place_of_worship",
        "reform_jewish_place_of_worship",
    ),
    Kind.HINDU_TEMPLE: (
        "shaiva_hindu_place_of_worship",
        "shakta_hindu_place_of_worship",
        "smarta_hindu_place_of_worship",
        "vaishnava_hindu_place_of_worship",
    ),
    Kind.GURDWARA: (),
    Kind.BUDDHIST_TEMPLE: (
        "mahayana_buddhist_place_of_worship",
        "nichiren_buddhist_place_of_worship",
        "pure_land_buddhist_place_of_worship",
        "zen_buddhist_place_of_worship",
        "theravada_buddhist_place_of_worship",
        "vajrayana_buddhist_place_of_worship",
    ),
}
# The categories that are counted, each with its kind.
IS: dict[str, Kind] = {
    PLACE_OF_WORSHIP: Kind.NO_KIND_NAMED,
    **{HEAD[kind]: kind for kind in NAMED},
    **{category: kind for kind in NAMED for category in UNDER[kind]},
}

_A_LANDMARK = "a landmark, which the publisher files apart from a place of worship"
_A_BODY = "an organisation or a house of an order, which the publisher files apart"
_A_RETREAT = "a retreat, which the publisher files apart from a place of worship"
# The categories of religion that the publisher files beside places of worship, each with
# why it is not counted. Each stands under `cultural_and_historic`.
OF_RELIGION: dict[str, str] = {
    "religious_landmark": _A_LANDMARK,
    "pilgrimage_site": _A_LANDMARK,
    "buddhist_pilgrimage_site": _A_LANDMARK,
    "christian_pilgrimage_site": _A_LANDMARK,
    "hindu_pilgrimage_site": _A_LANDMARK,
    "muslim_pilgrimage_site": _A_LANDMARK,
    "shrine": _A_LANDMARK,
    "catholic_shrine": _A_LANDMARK,
    "shinto_shrine": _A_LANDMARK,
    "sufi_shrine": _A_LANDMARK,
    "religious_organization": _A_BODY,
    "convent": _A_BODY,
    "monastery": _A_BODY,
    "seminary": _A_BODY,
    "religious_retreat_or_center": _A_RETREAT,
    "christian_retreat_center": _A_RETREAT,
    "hindu_ashram": _A_RETREAT,
    "zen_center": _A_RETREAT,
}
# The heads of the three branches of religion that stand beside places of worship.
BESIDE = frozenset({"religious_landmark", "religious_organization", "religious_retreat_or_center"})
_A_HISTORIC_SITE = "a historic site, which is no place of worship"
_A_MEMORIAL = "a memorial, which is no place of worship"
# What else the publisher files under `cultural_and_historic`, each with why it is not
# counted. Every one is in a path of the part of release 2026-09-23.0 round London, and none
# was on the table before the table was held to it.
NO_WORSHIP: dict[str, str] = {
    "historic_site": _A_HISTORIC_SITE,
    "castle": _A_HISTORIC_SITE,
    "fort": _A_HISTORIC_SITE,
    "historic_mission": _A_HISTORIC_SITE,
    "lighthouse": _A_HISTORIC_SITE,
    "palace": _A_HISTORIC_SITE,
    "ruin": _A_HISTORIC_SITE,
    "memorial_site": _A_MEMORIAL,
    "cemetery": _A_MEMORIAL,
    "monument": _A_MEMORIAL,
    "cultural_center": "a cultural centre, which the measure of centres counts",
}
# Every category that is left out by its name, with why.
IS_NOT: dict[str, str] = {**OF_RELIGION, **NO_WORSHIP}
# The top of the branch that holds every place of worship, as the publisher writes it. The
# whole of it is read: a category under it is on this table, or the build stops.
READ_UNDER = "cultural_and_historic"
# What the publisher's tree has no category of a place of worship for. A building of one of
# these cannot be counted by its kind, and the words beside a figure say so.
CANNOT_NAME = (
    "a Jain temple",
    "a Baha'i centre",
    "a Zoroastrian temple",
    "a Quaker meeting house as apart from a church",
    "a Shinto shrine as a place of worship",
)


def kind_of(primary: str | None, hierarchy: tuple[str, ...]) -> Kind | LeftOut:
    """What a record is, by its most particular category: a kind, or why it is none.

    `hierarchy` is the path from the top of the publisher's tree to the most
    particular category. Raises `NotOnTheTable` for a category under
    `cultural_and_historic` that the table does not hold.
    """
    if primary is None or primary == "":
        return LeftOut.NO_CATEGORY
    kind = IS.get(primary)
    if kind is not None:
        return kind
    if primary in IS_NOT:
        return LeftOut.BESIDE
    if READ_UNDER in hierarchy or PLACE_OF_WORSHIP in hierarchy:
        raise NotOnTheTable
    return LeftOut.NOT_WORSHIP


def said_beside(alternates: tuple[str, ...]) -> Kind | None:
    """The kind a record names beside its most particular category, where it names one.

    It decides nothing. It is counted, so that a person can see how many
    records say they are a place of worship and are filed as something else:
    a hall or a centre where people also meet to worship.
    """
    named = sorted({IS[one] for one in alternates if one in IS}, key=KINDS.index)
    return named[0] if named else None
