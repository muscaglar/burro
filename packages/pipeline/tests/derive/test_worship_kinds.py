"""Which of the publisher's categories is which kind of place of worship, and which is none.

Nothing is read here: the table is held to itself, and to the rules it is
written by. Every record is made up.
"""

import inspect
import re

import pytest
from burro_pipeline.derive import worship_kinds
from burro_pipeline.derive.culture_kinds import NotOnTheTable
from burro_pipeline.derive.worship_kinds import (
    BESIDE,
    CANNOT_NAME,
    HEAD,
    IS,
    IS_NOT,
    KINDS,
    NAMED,
    NO_WORSHIP,
    OF_RELIGION,
    PLACE_OF_WORSHIP,
    READ_UNDER,
    UNDER,
    WORDS,
    Kind,
    LeftOut,
    kind_of,
    said_beside,
)

from .community_support import (
    ANGLICAN,
    BUDDHIST_TEMPLE,
    CHURCH,
    COMMUNITY_CENTRE,
    GREEK_ORTHODOX,
    GURDWARA,
    HINDU_TEMPLE,
    MONASTERY,
    MOSQUE,
    OLD,
    REFORM,
    RETREAT,
    SHRINE,
    SUNNI,
    SYNAGOGUE,
    WORSHIP,
    ZEN,
)

# A category as the publisher writes one: small letters, digits and `_`.
WRITTEN = re.compile(r"[a-z][a-z0-9_]*")


def test_six_kinds_of_building_are_named_and_a_seventh_is_of_no_kind_named():
    assert [kind.value for kind in NAMED] == [
        "church",
        "mosque",
        "synagogue",
        "hindu_temple",
        "gurdwara",
        "buddhist_temple",
    ]
    assert list(KINDS) == [*NAMED, Kind.NO_KIND_NAMED]
    assert set(WORDS) == set(KINDS) and set(HEAD) == set(UNDER) == set(NAMED)


def test_a_kind_is_called_by_the_word_for_the_building():
    """A word for a building, one and many, and never a word for those who go there."""
    assert [WORDS[kind] for kind in NAMED] == [
        ("church", "churches"),
        ("mosque", "mosques"),
        ("synagogue", "synagogues"),
        ("Hindu temple", "Hindu temples"),
        ("gurdwara", "gurdwaras"),
        ("Buddhist temple", "Buddhist temples"),
    ]
    assert WORDS[Kind.NO_KIND_NAMED] == ("place of worship", "places of worship")


def test_the_table_holds_the_rows_that_two_readings_of_the_publishers_table_gave():
    """55 categories under a place of worship, itself among them, and 18 of religion beside
    it. The file gave 11 more under the same top, and none is a place of worship."""
    assert len(IS) == 55 and len(OF_RELIGION) == 18 and len(NO_WORSHIP) == 11
    assert IS_NOT == {**OF_RELIGION, **NO_WORSHIP} and len(IS_NOT) == 29
    assert {kind: 1 + len(UNDER[kind]) for kind in NAMED} == {
        Kind.CHURCH: 32,
        Kind.MOSQUE: 4,
        Kind.SYNAGOGUE: 5,
        Kind.HINDU_TEMPLE: 5,
        Kind.GURDWARA: 1,
        Kind.BUDDHIST_TEMPLE: 7,
    }
    assert IS[PLACE_OF_WORSHIP] is Kind.NO_KIND_NAMED


def test_a_category_is_on_the_table_once():
    every = [PLACE_OF_WORSHIP, *HEAD.values(), *(one for kind in NAMED for one in UNDER[kind])]
    assert len(every) == len(set(every)) == len(IS)
    assert not set(IS) & set(IS_NOT) and not set(OF_RELIGION) & set(NO_WORSHIP)
    assert set(OF_RELIGION) >= BESIDE


def test_every_category_is_written_as_the_publisher_writes_one():
    for category in (*IS, *IS_NOT, *BESIDE):
        assert WRITTEN.fullmatch(category), category


def test_every_category_that_is_counted_says_that_it_is_a_place_of_worship():
    """The publisher ends each with the same words, so a category of another branch is not
    on the table by a slip."""
    assert all(category.endswith(PLACE_OF_WORSHIP) for category in IS)
    assert not any(category.endswith(PLACE_OF_WORSHIP) for category in IS_NOT)


def test_every_category_that_is_left_out_says_why_in_plain_words():
    for why in IS_NOT.values():
        assert why and why[0].islower() and not why.endswith(".") and "!" not in why


@pytest.mark.parametrize(
    ("hierarchy", "kind"),
    [
        (CHURCH, Kind.CHURCH),
        (ANGLICAN, Kind.CHURCH),
        (GREEK_ORTHODOX, Kind.CHURCH),
        (MOSQUE, Kind.MOSQUE),
        (SUNNI, Kind.MOSQUE),
        (SYNAGOGUE, Kind.SYNAGOGUE),
        (REFORM, Kind.SYNAGOGUE),
        (HINDU_TEMPLE, Kind.HINDU_TEMPLE),
        (GURDWARA, Kind.GURDWARA),
        (BUDDHIST_TEMPLE, Kind.BUDDHIST_TEMPLE),
        (ZEN, Kind.BUDDHIST_TEMPLE),
    ],
)
def test_the_most_particular_category_of_a_record_decides_its_kind(
    hierarchy: tuple[str, ...], kind: Kind
):
    assert kind_of(hierarchy[-1], hierarchy) is kind


def test_a_record_whose_only_category_is_a_place_of_worship_is_of_no_kind_named():
    """It counts toward the places of worship, and toward none of the six."""
    assert kind_of(PLACE_OF_WORSHIP, WORSHIP) is Kind.NO_KIND_NAMED
    assert Kind.NO_KIND_NAMED not in NAMED


@pytest.mark.parametrize("hierarchy", [SHRINE, MONASTERY, RETREAT])
def test_what_the_publisher_files_beside_a_place_of_worship_is_left_out(
    hierarchy: tuple[str, ...],
):
    assert kind_of(hierarchy[-1], hierarchy) is LeftOut.BESIDE
    assert kind_of(hierarchy[1], hierarchy[:2]) is LeftOut.BESIDE


def test_a_category_under_a_place_of_worship_that_the_table_does_not_hold_stops_the_build():
    """It is never counted by a guess and never dropped by one: a person says what it is."""
    for under in (WORSHIP, CHURCH, MOSQUE):
        with pytest.raises(NotOnTheTable) as stopped:
            kind_of("zzyzx_parva_place_of_worship", (*under, "zzyzx_parva_place_of_worship"))
        assert "zzyzx" not in str(stopped.value)


def test_a_new_category_in_a_branch_that_is_left_out_stops_the_build_too():
    """A new category beside the places of worship may be a kind of one that the publisher
    has filed there. It is left out by its name once a person has said what it is."""
    for under in (SHRINE, MONASTERY, RETREAT, (OLD, "historic_site"), (OLD,)):
        with pytest.raises(NotOnTheTable):
            kind_of("zzyzx_parva_site", (*under, "zzyzx_parva_site"))
    assert READ_UNDER == OLD


@pytest.mark.parametrize(
    "hierarchy",
    [
        (OLD, "historic_site"),
        (OLD, "historic_site", "castle"),
        (OLD, "memorial_site", "cemetery"),
        (OLD, "memorial_site", "monument"),
        (OLD, "cultural_center"),
    ],
)
def test_what_else_stands_under_the_same_top_is_left_out_by_its_name(
    hierarchy: tuple[str, ...],
):
    assert hierarchy[-1] in NO_WORSHIP
    assert kind_of(hierarchy[-1], hierarchy) is LeftOut.BESIDE


def test_a_category_of_anything_else_is_no_place_of_worship_and_stops_nothing():
    assert kind_of("cafe", ("food_and_drink", "cafe")) is LeftOut.NOT_WORSHIP
    assert kind_of("community_center", COMMUNITY_CENTRE) is LeftOut.NOT_WORSHIP
    assert kind_of("religious_school", ("education", "religious_school")) is LeftOut.NOT_WORSHIP


def test_a_record_with_no_category_is_left_out_and_is_no_kind():
    assert kind_of(None, ()) is LeftOut.NO_CATEGORY
    assert kind_of("", ()) is LeftOut.NO_CATEGORY


def test_what_a_record_says_beside_its_category_is_counted_and_decides_nothing():
    """A community centre that also says it is a mosque is a community centre."""
    assert list(inspect.signature(kind_of).parameters) == ["primary", "hierarchy"]
    assert said_beside(("muslim_place_of_worship",)) is Kind.MOSQUE
    assert said_beside(("cafe", "sunni_muslim_place_of_worship")) is Kind.MOSQUE
    assert said_beside(("place_of_worship", "sikh_place_of_worship")) is Kind.GURDWARA
    assert said_beside(("cafe", "shrine")) is None and said_beside(()) is None


def test_nothing_of_a_name_is_handed_to_the_rule():
    assert "name" not in set(inspect.signature(kind_of).parameters)
    assert "name" not in {name.lower() for name in vars(worship_kinds) if name.isupper()}


def test_the_table_says_which_buildings_it_cannot_name():
    """The publisher's tree has a category for six kinds. A building of another is not told."""
    assert len(CANNOT_NAME) == len(set(CANNOT_NAME)) >= 4
    assert all(one.startswith("a ") for one in CANNOT_NAME)
    assert not any(word in " ".join(IS) for word in ("jain", "bahai", "zoroastrian", "quaker"))
