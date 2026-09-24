"""What the tests of places of worship and of centres share: the buildings of a made-up town.

Nothing here is real. The town is the one `culture_support.py` draws, in the
North Sea, and every building is made up. The file is written as the
publisher of places lays out its own, and every name in it is the canary.

The centres of the town's output areas stand 1,000 metres apart in three rows,
so that what is within reach of one home is within reach of little else, and
every count can be made by hand:

    Quillhaven 001   Q1  a church 100 metres east, a mosque 100 metres north and a
                         synagogue 100 metres west. A place of worship of no kind named,
                         200 metres north. Two community centres and a cultural centre
                     Q2  a gurdwara, 500 metres east, half way to Q3
                     Q3  the same gurdwara, 500 metres west
                     Q4  a Hindu temple 790 metres north. A Buddhist temple 810 metres
                         north is out of reach
    Quillhaven 002   R1  a church. R2, R3 and R4 have nothing within reach
    Tallowgate 001   T1  two mosques 100 metres apart and an Anglican church, and a
                         community centre. T2, T3 and T4 have nothing

Beside Q1 stand seven records that add no place of worship: a record of no
kind named that stands 10 metres from the church and is the church again, a
shrine, a monastery, a retreat, a church that has closed, a cafe, and a
community centre that also says it is a mosque. Three records stand there that
are beside a centre and are none: a civic centre, a social club and a youth
organisation. A bookshop stands by every centre, so that the file is seen to
hold something within reach of every home.
"""

import re

from .culture_support import (
    BY_EVERY_CENTRE,
    CAFE,
    Q1,
    Q2,
    Q4,
    R1,
    T1,
    beside,
    place,
)

OLD = "cultural_and_historic"
WORSHIP = (OLD, "place_of_worship")
CHURCH = (*WORSHIP, "christian_place_of_worship")
ANGLICAN = (*CHURCH, "protestant_place_of_worship", "anglican_or_episcopal_place_of_worship")
GREEK_ORTHODOX = (
    *CHURCH,
    "eastern_orthodox_place_of_worship",
    "greek_orthodox_place_of_worship",
)
MOSQUE = (*WORSHIP, "muslim_place_of_worship")
SUNNI = (*MOSQUE, "sunni_muslim_place_of_worship")
SYNAGOGUE = (*WORSHIP, "jewish_place_of_worship")
REFORM = (*SYNAGOGUE, "reform_jewish_place_of_worship")
HINDU_TEMPLE = (*WORSHIP, "hindu_place_of_worship")
GURDWARA = (*WORSHIP, "sikh_place_of_worship")
BUDDHIST_TEMPLE = (*WORSHIP, "buddhist_place_of_worship")
ZEN = (*BUDDHIST_TEMPLE, "mahayana_buddhist_place_of_worship", "zen_buddhist_place_of_worship")
SHRINE = (OLD, "religious_landmark", "shrine")
MONASTERY = (OLD, "religious_organization", "monastery")
RETREAT = (OLD, "religious_retreat_or_center", "zen_center")
SERVICE = ("community_and_government", "social_or_community_service")
COMMUNITY_CENTRE = (*SERVICE, "community_center")
YOUTH = (*SERVICE, "youth_organization")
CIVIC_CENTRE = ("community_and_government", "civic_organization", "civic_center")
SOCIAL_CLUB = ("arts_and_entertainment", "social_club")
CULTURAL_CENTRE = (OLD, "cultural_center")

# What stands in the town unless a test says otherwise. Every building is put against a
# centre, so that each count can be made by hand.
IN_THE_TOWN = (
    *BY_EVERY_CENTRE,
    # A church, a mosque and a synagogue stand 100 metres from the first centre.
    place(beside(Q1, 100), CHURCH),
    place(beside(Q1, 0, 100), SUNNI),
    place(beside(Q1, -100), REFORM),
    # A place of worship of which the file names no kind, 200 metres north.
    place(beside(Q1, 0, 200), WORSHIP),
    # And one that stands 10 metres from the church, and is the church again.
    place(beside(Q1, 110), WORSHIP),
    # A gurdwara stands half way between the second centre and the third.
    place(beside(Q2, 500), GURDWARA),
    # A Hindu temple stands 790 metres north of the fourth centre, and a Buddhist temple 810.
    place(beside(Q4, 0, 790), HINDU_TEMPLE),
    place(beside(Q4, 0, 810), ZEN),
    # What is no place of worship that is counted stands beside the first centre too.
    place(beside(Q1, 10, 10), SHRINE),
    place(beside(Q1, 20, 20), MONASTERY),
    place(beside(Q1, 30, 30), RETREAT),
    place(beside(Q1, 40, 40), CHURCH, status="permanently_closed"),
    place(beside(Q1, 50, 50), CAFE),
    place(beside(Q1, 60, 60), COMMUNITY_CENTRE, alternates=("muslim_place_of_worship",)),
    # Another community centre and a cultural centre, and what stands beside a centre.
    place(beside(Q1, -60, -60), COMMUNITY_CENTRE),
    place(beside(Q1, -70, 70), CULTURAL_CENTRE),
    place(beside(Q1, -80, 80), CIVIC_CENTRE),
    place(beside(Q1, -90, 90), SOCIAL_CLUB),
    place(beside(Q1, 90, -90), YOUTH),
    # The second area has one church, beside its first centre.
    place(beside(R1, 0, 50), GREEK_ORTHODOX),
    # Two mosques, an Anglican church and a community centre beside the first centre of
    # Tallowgate, and nothing else.
    place(beside(T1, 50), MOSQUE),
    place(beside(T1, -50), SUNNI),
    place(beside(T1, 0, 50), ANGLICAN),
    place(beside(T1, 0, -50), COMMUNITY_CENTRE),
)

# Words for who lives somewhere, as core's test of its catalogue lists them. None may stand
# in anything a person can rank on, so none may stand in a row this measure puts forward.
OF_RESIDENTS = re.compile(
    r"\b(?:residents?|people|population|households?|famil(?:y|ies)|students?|tenure|tenants?|"
    r"owners?|ages?|aged|young|old|elderly|child(?:ren)?|kids?|ethnic\w*|rac(?:e|ial)|"
    r"religio\w*|faith|born|birth|languages?|gender|sex\w*|disab\w*|health|incomes?|"
    r"depriv\w*|poor|rich|wealth\w*|class|migrants?|immigra\w*|nationalit\w*)\b",
    re.IGNORECASE,
)
# Words for those who go to a building, or for how much of a community a place has.
OF_THOSE_WHO_GO = re.compile(
    r"\b(?:worshippers?|congregations?|believers?|followers?|members?|communit(?:y|ies)|"
    r"christians|muslims|jews|hindus|sikhs|buddhists|diverse|diversity|multicultural|"
    r"majority|minority|share of|per cent|percent|estimate[sd]?)\b",
    re.IGNORECASE,
)
# Words that would offer a figure with a direction of fewer.
OF_FEWER = re.compile(
    r"\b(?:fewer|less|least|avoid\w*|away|far|further|without|free of|no (?:church|mosque|"
    r"synagogue|temple|gurdwara)\w*|not many|not too many)\b",
    re.IGNORECASE,
)
# A name that would say a figure is a score, a share or a mix.
OF_A_SCORE = ("score", "index", "share", "rate", "ratio", "mix", "variety", "diversity", "weight")
