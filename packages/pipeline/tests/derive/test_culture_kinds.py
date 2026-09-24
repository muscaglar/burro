"""Which of the publisher's categories is which kind of venue, and which is none.

Nothing is read here: the table is held to itself, and to the rules it is
written by. Every record is made up.
"""

import inspect
import re

import pytest
from burro_pipeline.derive import culture_kinds
from burro_pipeline.derive.culture_kinds import (
    ELSEWHERE,
    IS,
    IS_NOT,
    KINDS,
    PARENTS,
    READ_UNDER,
    TEACHES,
    WORDS,
    Kind,
    LeftOut,
    NotOnTheTable,
    kind_of,
)

ARTS = "arts_and_entertainment"
STAGE = (ARTS, "performing_arts_venue")
# A category as the publisher writes one: small letters, digits and `_`.
WRITTEN = re.compile(r"[a-z][a-z0-9_]*")
# Words for who goes somewhere or who lives somewhere. No category of culture holds one.
OF_PEOPLE = ("worship", "church", "mosque", "temple", "synagogue", "gurdwara", "religio")


def test_six_kinds_are_counted_and_each_has_a_category_of_its_own():
    assert [kind.value for kind in KINDS] == [
        "museum",
        "gallery",
        "theatre",
        "cinema",
        "music_venue",
        "library",
    ]
    assert set(IS.values()) == set(KINDS) == set(WORDS)


def test_a_category_is_on_the_table_once():
    assert not set(IS) & set(IS_NOT)
    assert not set(IS) & PARENTS and not set(IS_NOT) & PARENTS
    assert not (set(IS) | set(IS_NOT) | PARENTS) & TEACHES


def test_every_category_is_written_as_the_publisher_writes_one():
    for category in (*IS, *IS_NOT, *PARENTS, *READ_UNDER, *TEACHES):
        assert WRITTEN.fullmatch(category), category


def test_every_category_that_is_left_out_says_why_in_plain_words():
    for why in IS_NOT.values():
        assert why and why[0].islower() and not why.endswith(".") and "!" not in why


def test_no_category_of_the_table_is_about_who_goes_there():
    """Rank places, never residents: a place of worship is no part of culture nearby."""
    for category in (*IS, *IS_NOT, *PARENTS, *READ_UNDER):
        assert not any(word in category for word in OF_PEOPLE), category


@pytest.mark.parametrize(
    ("primary", "hierarchy", "kind"),
    [
        ("museum", (ARTS, "museum"), Kind.MUSEUM),
        ("art_museum", (ARTS, "museum", "art_museum"), Kind.MUSEUM),
        ("design_museum", (ARTS, "museum", "art_museum", "design_museum"), Kind.MUSEUM),
        ("art_gallery", (ARTS, "arts_and_crafts_space", "art_gallery"), Kind.GALLERY),
        ("theatre_venue", (*STAGE, "theatre_venue"), Kind.THEATRE),
        ("movie_theater", (ARTS, "movie_theater"), Kind.CINEMA),
        ("music_venue", (*STAGE, "music_venue"), Kind.MUSIC_VENUE),
        ("opera_and_ballet", (*STAGE, "music_venue", "opera_and_ballet"), Kind.MUSIC_VENUE),
        ("library", ("education", "library"), Kind.LIBRARY),
    ],
)
def test_the_most_particular_category_of_a_record_decides_its_kind(
    primary: str, hierarchy: tuple[str, ...], kind: Kind
):
    assert kind_of(primary, hierarchy, ()) is kind


@pytest.mark.parametrize("parent", sorted(PARENTS))
def test_a_record_whose_only_category_is_a_parent_is_left_out(parent: str):
    assert kind_of(parent, (ARTS, parent), ()) is LeftOut.PARENT_ALONE


@pytest.mark.parametrize(
    ("primary", "hierarchy"),
    [
        ("choir", (*STAGE, "music_venue", "choir")),
        ("band_orchestra_symphony", (*STAGE, "music_venue", "band_orchestra_symphony")),
        ("karaoke_venue", (*STAGE, "music_venue", "karaoke_venue")),
        ("dinner_theater", (*STAGE, "theatre_venue", "dinner_theater")),
        ("drive_in_theater", (ARTS, "movie_theater", "drive_in_theater")),
        ("comedy_club", (*STAGE, "comedy_club")),
        ("artist_studio", (ARTS, "arts_and_crafts_space", "artist_studio")),
    ],
)
def test_a_category_is_not_a_kind_because_its_parent_is(primary: str, hierarchy: tuple[str, ...]):
    """A choir stands under music venue in the publisher's tree, and is no venue."""
    assert kind_of(primary, hierarchy, ()) is LeftOut.NOT_A_KIND


@pytest.mark.parametrize(
    ("primary", "hierarchy"),
    [
        ("casino", (ARTS, "gaming_venue", "casino")),
        ("cricket_ground", (ARTS, "stadium_arena", "stadium", "cricket_ground")),
        ("dance_club", (ARTS, "nightlife_venue", "dance_club")),
        ("planetarium", (ARTS, "science_attraction", "planetarium")),
        ("auditorium", (ARTS, "event_venue", "auditorium")),
        ("social_club", (ARTS, "social_club")),
        ("gaming_venue", (ARTS, "gaming_venue")),
    ],
)
def test_a_category_of_entertainment_that_is_none_of_the_six_is_left_out_by_its_name(
    primary: str, hierarchy: tuple[str, ...]
):
    """So what is passed by is counted by its category, and a person can see what it is."""
    assert primary in ELSEWHERE and ELSEWHERE[primary] == IS_NOT[primary]
    assert kind_of(primary, hierarchy, ()) is LeftOut.NOT_A_KIND


def test_a_record_that_says_no_more_than_the_arts_and_entertainment_is_left_out():
    assert ARTS in PARENTS and ARTS in READ_UNDER
    assert kind_of(ARTS, (ARTS,), ()) is LeftOut.PARENT_ALONE


def test_a_new_category_anywhere_in_the_arts_and_entertainment_stops_the_build():
    """Not under a parent of a kind alone: a kind that the publisher files elsewhere in the
    branch would else be counted nowhere, and nothing would say so."""
    for path in ((ARTS,), (ARTS, "gaming_venue"), (ARTS, "zzyzx_parva_attraction")):
        with pytest.raises(NotOnTheTable):
            kind_of("zzyzx_parva_hall", (*path, "zzyzx_parva_hall"), ())


def test_a_record_that_also_says_it_teaches_is_left_out():
    """A stage school filed under theatre. Its category says so, and its name is not read."""
    theatre = (*STAGE, "theatre_venue")
    assert kind_of("theatre_venue", theatre, ("drama_school",)) is LeftOut.ALSO_TEACHES
    assert kind_of("music_venue", (*STAGE, "music_venue"), ("music_school",)) is (
        LeftOut.ALSO_TEACHES
    )
    assert kind_of("art_gallery", (ARTS, "art_gallery"), ("art_school", "cafe")) is (
        LeftOut.ALSO_TEACHES
    )


def test_a_record_that_gives_another_category_beside_its_kind_is_still_its_kind():
    assert kind_of("theatre_venue", (*STAGE, "theatre_venue"), ("bar", "cafe")) is Kind.THEATRE
    assert kind_of("museum", (ARTS, "museum"), ("library",)) is Kind.MUSEUM


def test_a_kind_given_beside_another_category_does_not_make_a_record_that_kind():
    """A school that also calls itself a theatre is a school: the most particular decides."""
    school = ("education", "place_of_learning", "specialty_school", "drama_school")
    assert kind_of("drama_school", school, ("theatre_venue",)) is LeftOut.NOT_CULTURE
    assert kind_of("restaurant", ("food_and_drink", "restaurant"), ("music_venue",)) is (
        LeftOut.NOT_CULTURE
    )


def test_a_record_with_no_category_is_left_out_and_is_no_kind():
    assert kind_of(None, (), ()) is LeftOut.NO_CATEGORY
    assert kind_of("", (), ("museum",)) is LeftOut.NO_CATEGORY


@pytest.mark.parametrize("parent", sorted(READ_UNDER))
def test_a_category_of_culture_that_the_table_does_not_hold_stops_the_build(parent: str):
    """It is never counted by a guess and never dropped by one: a person says what it is."""
    with pytest.raises(NotOnTheTable) as stopped:
        kind_of("zzyzx_parva_venue", (ARTS, parent, "zzyzx_parva_venue"), ())
    assert "zzyzx" not in str(stopped.value)


def test_a_category_of_anything_else_is_no_culture_and_stops_nothing():
    assert kind_of("zzyzx_parva_shop", ("shopping", "zzyzx_parva_shop"), ()) is LeftOut.NOT_CULTURE
    worship = ("cultural_and_historic", "place_of_worship")
    assert kind_of("place_of_worship", worship, ()) is LeftOut.NOT_CULTURE
    assert kind_of("cultural_center", ("cultural_and_historic", "cultural_center"), ()) is (
        LeftOut.NOT_CULTURE
    )


def test_every_kind_stands_under_a_branch_that_is_read():
    """So a category that arrives under the same parent as a kind is never passed by."""
    own = {"museum", "movie_theater", "library"}
    assert own <= READ_UNDER and PARENTS <= READ_UNDER
    assert own <= set(IS)


def test_nothing_of_a_name_is_handed_to_the_rule():
    assert list(inspect.signature(kind_of).parameters) == ["primary", "hierarchy", "alternates"]
    assert "name" not in {name.lower() for name in vars(culture_kinds) if name.isupper()}
