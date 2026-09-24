"""The kinds of cultural venue: which of the publisher's categories is which, and which is none.

Overture Maps gives every place a category from a tree of its own. A place
has its most particular category as `taxonomy.primary`, the path to it from
the top of the tree as `taxonomy.hierarchy`, and other categories that fit it
as `taxonomy.alternates`. This module is the table that says what each
category is to Burro. It reads no file and holds no name of any place.

Six kinds are counted: a museum, a gallery, a theatre, a cinema, a music
venue and a library. **The most particular category of a record decides, and
nothing else does.** No rule is made from a name: a name is not read.

1. A category is a kind where the table below says so. The table is the whole
   of what counts.
2. A record whose most particular category is a parent of the kinds is left
   out. `performing_arts_venue` says a stage of some sort and not which, so a
   record that says no more is no theatre and no music venue. The top of the
   branch, `arts_and_entertainment`, says less still.
3. Every other category of the arts and of entertainment is left out by its
   name, with the reason. An orchestra is a group of players and no place. A
   karaoke venue is a bar. A casino and a stadium are none of the six.
4. A record that also gives a category of a place of learning is left out. A
   stage school is filed under theatre, and says of itself that it teaches.
5. A category of the arts and of entertainment, or under a library, that is
   not on the table stops the build, so that a person says what a new category
   is. It is never counted and never dropped by a guess.

What is left out is counted, by the reason and by the category, so that a
person can see what each rule costs.

**Where the table comes from.** The publisher's own table of categories for
release 2026-09-23.0, at `docs.overturemaps.org/taxonomy/2026-09-23.0/taxonomy.csv`,
read on 2026-09-24 through a reader that extracts the text of a page. An
extraction is not the page. The reader was asked for the branch of the arts
twice, in different words, and gave the same rows both times: every category
of a kind, and everything beside one, is from those rows. It was asked for the
branch of education once, and the categories of a place of learning are from
that one answer. The table was read as far as its branch for health care, and
the branches after it were not read: no category of theirs is here. No person
has seen the table.

**The table has been held to a file.** In the part of release 2026-09-23.0
round London, 84 categories are the most particular of a record of the arts,
of entertainment or of a library. 25 are a kind, and every one of those was on
the table as it was first read. 11 more were on it as left out, and one as a
parent. The other 47 had not been met. One is the top of the branch, which is
now a parent. 46 are now left out by name, in `ELSEWHERE`, with seven more
that the part holds only as the parent of another. So a record of the arts
and of entertainment is counted, or is left out by the name of its category,
or stops the build. Four categories that are a kind, and five that are left
out, are on the table and in no record of the part.
`test_culture_on_the_real_files.py` holds the table to the part.

**What the choices are, and whose.** Which category is which kind is a choice,
and each is written beside its category. They are the founder's to change:

- An art museum is a museum, and an art gallery is a gallery, as the
  publisher files them.
- Opera and ballet is a music venue, because the publisher files it under
  one. A jazz and blues venue is one too.
- A comedy club, a cabaret, an amphitheatre and an auditorium are none of the
  six. Nor is a cultural centre, which the publisher files apart from the arts.
- A cinema out of doors is not counted: a drive-in, and a screen in the open.
- A planetarium, an observatory, an aquarium and a zoo are none of the six,
  though a person may call each a museum of a sort. Nor is a dance club.
"""

from enum import StrEnum


class Kind(StrEnum):
    """The six kinds of venue that are counted, in the order a figure lists them."""

    MUSEUM = "museum"
    GALLERY = "gallery"
    THEATRE = "theatre"
    CINEMA = "cinema"
    MUSIC_VENUE = "music_venue"
    LIBRARY = "library"


class LeftOut(StrEnum):
    """Why a record is not counted. Each is counted."""

    # Its most particular category is no category of culture. It is most of any file.
    NOT_CULTURE = "not_culture"
    # The file gives it no category at all.
    NO_CATEGORY = "no_category"
    # Its most particular category is a parent of the kinds, and says no kind.
    PARENT_ALONE = "parent_alone"
    # Its category is of the arts or of entertainment, and is none of the six.
    NOT_A_KIND = "not_a_kind"
    # It is a kind by its category, and also gives a category of a place of learning.
    ALSO_TEACHES = "also_teaches"
    # The file says that it has closed.
    CLOSED = "closed"
    # It has no point, or a point that is no point on the earth.
    NO_POINT = "no_point"


KINDS = tuple(Kind)
# What a kind is called in a sentence, one and many.
WORDS: dict[Kind, tuple[str, str]] = {
    Kind.MUSEUM: ("museum", "museums"),
    Kind.GALLERY: ("gallery", "galleries"),
    Kind.THEATRE: ("theatre", "theatres"),
    Kind.CINEMA: ("cinema", "cinemas"),
    Kind.MUSIC_VENUE: ("music venue", "music venues"),
    Kind.LIBRARY: ("library", "libraries"),
}

# The categories that are a kind, as the publisher writes them. Each stands in the
# publisher's tree under the kind's own category.
IS: dict[str, Kind] = {
    # arts_and_entertainment > museum, and everything under it.
    "museum": Kind.MUSEUM,
    "art_museum": Kind.MUSEUM,
    "asian_art_museum": Kind.MUSEUM,
    "cartooning_museum": Kind.MUSEUM,
    "contemporary_art_museum": Kind.MUSEUM,
    "costume_museum": Kind.MUSEUM,
    "decorative_arts_museum": Kind.MUSEUM,
    "design_museum": Kind.MUSEUM,
    "modern_art_museum": Kind.MUSEUM,
    "photography_museum": Kind.MUSEUM,
    "textile_museum": Kind.MUSEUM,
    "aviation_museum": Kind.MUSEUM,
    "childrens_museum": Kind.MUSEUM,
    "history_museum": Kind.MUSEUM,
    "civilization_museum": Kind.MUSEUM,
    "community_museum": Kind.MUSEUM,
    "military_museum": Kind.MUSEUM,
    "national_museum": Kind.MUSEUM,
    "science_museum": Kind.MUSEUM,
    "computer_museum": Kind.MUSEUM,
    "sports_museum": Kind.MUSEUM,
    "state_museum": Kind.MUSEUM,
    # arts_and_entertainment > arts_and_crafts_space > art_gallery.
    "art_gallery": Kind.GALLERY,
    # arts_and_entertainment > performing_arts_venue > theatre_venue.
    "theatre_venue": Kind.THEATRE,
    # arts_and_entertainment > movie_theater.
    "movie_theater": Kind.CINEMA,
    # arts_and_entertainment > performing_arts_venue > music_venue, and two under it.
    "music_venue": Kind.MUSIC_VENUE,
    "jazz_and_blues_venue": Kind.MUSIC_VENUE,
    "opera_and_ballet": Kind.MUSIC_VENUE,
    # education > library.
    "library": Kind.LIBRARY,
}

# The categories that stand under a parent of the kinds and are none of the six, each with
# why. The publisher's tree puts each beside a kind or under one.
BESIDE_A_KIND: dict[str, str] = {
    # Under theatre_venue.
    "dinner_theater": "a place to eat that puts on a show",
    # Under music_venue.
    "band_orchestra_symphony": "a group of players, and no place",
    "choir": "a group of singers, and no place",
    "karaoke_venue": "a bar where the guests sing",
    # Under movie_theater.
    "drive_in_theater": "a screen out of doors, watched from a car",
    "outdoor_movie_space": "a screen out of doors",
    # Under performing_arts_venue, beside the theatre and the music venue.
    "amphitheater": "a stage out of doors, and none of the six kinds",
    "cabaret": "none of the six kinds",
    "comedy_club": "none of the six kinds",
    # Under arts_and_crafts_space, beside the gallery.
    "artist_studio": "a place of work, which may not be open to anyone",
    "glass_blowing_venue": "a workshop",
    "paint_and_sip_venue": "a class with a drink",
    "paint_your_own_pottery_venue": "a workshop",
    "sculpture_park": "a park, which the measures of parks count",
    "sculpture_statue": "one work of art, and no venue",
    "street_art": "one work of art, and no venue",
}

_A_FAIR = "a place of rides or of shows that come and go, and none of the six kinds"
_ANIMALS = "a place to see animals, and none of the six kinds"
_A_HALL = "a hall for hire, which says nothing of what is on"
_A_FESTIVAL = "a ground for a festival, and no venue the year round"
_A_GAME = "a place to play or to bet, and none of the six kinds"
_AT_NIGHT = "a place to go at night, and none of the six kinds"
_OF_SCIENCE = "a place of science, and none of the six kinds"
_A_CLUB = "a club for its members"
_ADVICE = "a service, and no venue"
_SPORT = "a ground for sport, and none of the six kinds"
# The categories of the arts and of entertainment that stand under no parent of a kind,
# each with why it is none of the six. Every one is in a path of the part of release
# 2026-09-23.0 round London, and none was on the table before the table was held to it.
ELSEWHERE: dict[str, str] = {
    "amusement_attraction": _A_FAIR,
    "amusement_park": _A_FAIR,
    "circus_venue": _A_FAIR,
    "haunted_house": _A_FAIR,
    "animal_attraction": _ANIMALS,
    "aquarium": _ANIMALS,
    "wildlife_sanctuary": _ANIMALS,
    "zoo": _ANIMALS,
    "petting_zoo": _ANIMALS,
    "event_venue": _A_HALL,
    "auditorium": _A_HALL,
    "exhibition_and_trade_fair_venue": _A_HALL,
    "festival_venue": _A_FESTIVAL,
    "fairgrounds": _A_FESTIVAL,
    "film_festival_venue": _A_FESTIVAL,
    "music_festival_venue": _A_FESTIVAL,
    "gaming_venue": _A_GAME,
    "arcade": _A_GAME,
    "betting_center": _A_GAME,
    "bingo_hall": _A_GAME,
    "casino": _A_GAME,
    "escape_room": _A_GAME,
    "lottery_vendor": _A_GAME,
    "nightlife_venue": _AT_NIGHT,
    "adult_entertainment_venue": _AT_NIGHT,
    "erotic_massage_venue": _AT_NIGHT,
    "strip_club": _AT_NIGHT,
    "dance_club": _AT_NIGHT,
    "salsa_club": _AT_NIGHT,
    "rural_attraction": "a place in the country, and none of the six kinds",
    "country_dance_hall": "a hall for dancing, and none of the six kinds",
    "science_attraction": _OF_SCIENCE,
    "makerspace": "a workshop",
    "observatory": _OF_SCIENCE,
    "planetarium": _OF_SCIENCE,
    "social_club": _A_CLUB,
    "country_club": _A_CLUB,
    "fraternal_organization": _A_CLUB,
    "veterans_organization": _A_CLUB,
    "spiritual_advising": _ADVICE,
    "astrological_advising": _ADVICE,
    "psychic_advising": _ADVICE,
    "stadium_arena": _SPORT,
    "stadium": _SPORT,
    "basketball_stadium": _SPORT,
    "cricket_ground": _SPORT,
    "football_stadium": _SPORT,
    "hockey_arena": _SPORT,
    "rugby_stadium": _SPORT,
    "soccer_stadium": _SPORT,
    "tennis_stadium": _SPORT,
    "track_stadium": _SPORT,
    "ticket_office_or_booth": "a place that sells tickets, and no venue",
}
# Every category that is left out by its name, with why.
IS_NOT: dict[str, str] = {**BESIDE_A_KIND, **ELSEWHERE}

# The top of the branch that holds every kind but the library, as the publisher writes it.
ARTS = "arts_and_entertainment"
# The categories that stand above the kinds and say no kind. A record whose most
# particular category is one of these is left out.
PARENTS = frozenset({ARTS, "performing_arts_venue", "arts_and_crafts_space"})
# The categories whose branch of the tree is read. A record with one of these in its path
# is a record of culture: its most particular category is on this table, or the build stops.
# The whole of the arts and of entertainment is read, so the four under it say nothing more.
# They are kept so that a kind is seen to stand under a branch that is read.
READ_UNDER = frozenset(
    {ARTS, "museum", "movie_theater", "performing_arts_venue", "arts_and_crafts_space", "library"}
)

# The categories of a place of learning: everything the publisher's tree holds under
# `education > place_of_learning`. A record that is a kind by its most particular category,
# and gives one of these beside it, says of itself that it teaches.
TEACHES = frozenset(
    {
        "place_of_learning",
        "academy",
        "civil_examinations_academy",
        "adult_education_center",
        "class_venue",
        "tasting_class",
        "cheese_tasting_class",
        "wine_tasting_class",
        "college_university",
        "architecture_school",
        "business_school",
        "engineering_school",
        "law_school",
        "medical_sciences_school",
        "dentistry_school",
        "pharmacy_school",
        "veterinary_school",
        "science_school",
        "school",
        "charter_school",
        "elementary_school",
        "high_school",
        "kindergarten",
        "middle_school",
        "montessori_school",
        "preschool",
        "private_school",
        "public_school",
        "religious_school",
        "waldorf_school",
        "specialty_school",
        "art_school",
        "bartending_school",
        "cheerleading",
        "childbirth_education",
        "circus_school",
        "computer_coaching",
        "cooking_school",
        "cosmetology_school",
        "cpr_class",
        "drama_school",
        "driving_school",
        "dui_school",
        "firearm_training",
        "first_aid_class",
        "flight_school",
        "food_safety_training",
        "language_school",
        "massage_school",
        "medical_school",
        "music_school",
        "nursing_school",
        "parenting_class",
        "photography_class",
        "speech_training",
        "sports_school",
        "traffic_school",
        "vocational_and_technical_school",
    }
)


class NotOnTheTable(Exception):
    """A category stands under a parent that is read, and the table does not know it."""


def kind_of(
    primary: str | None, hierarchy: tuple[str, ...], alternates: tuple[str, ...]
) -> Kind | LeftOut:
    """What a record is, by its most particular category: a kind, or why it is none.

    `hierarchy` is the path from the top of the publisher's tree to the most
    particular category, and `alternates` the other categories the file gives
    the record. Raises `NotOnTheTable` for a category of culture that the
    table does not hold.
    """
    if primary is None or primary == "":
        return LeftOut.NO_CATEGORY
    if primary in PARENTS:
        return LeftOut.PARENT_ALONE
    if primary in IS_NOT:
        return LeftOut.NOT_A_KIND
    kind = IS.get(primary)
    if kind is None:
        if READ_UNDER & set(hierarchy):
            raise NotOnTheTable
        return LeftOut.NOT_CULTURE
    if TEACHES & set(alternates):
        return LeftOut.ALSO_TEACHES
    return kind
