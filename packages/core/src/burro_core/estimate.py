"""A journey estimated from distance, where a release holds no journey time.

No build of London holds a journey time yet: none has read a timetable. So a
journey by public transport is estimated from how far the place is, in a
straight line, from where the homes of an area are taken to stand. It is an
estimate, and it is said to be one wherever it is shown (decision record 0027).

It is said as one of three bands against the limit the person gave, and never
as a number of minutes: the estimate is too rough to be read as a time. A
journey time that a release holds takes its place. Nothing is estimated for an
area of which the release does not say where its homes stand, by bike or on
foot, or to a place the release does not hold.

It is a pure function of the release and of the limit, so the same search
gives the same answer.
"""

import math
from collections.abc import Mapping
from types import MappingProxyType

from burro_core._record import Record
from burro_core.ids import FeatureId, JourneyBand, Mode
from burro_core.release import Place, Point, Release

# How an estimate is made. Each number is a first guess, for the founder to adjust: none
# was fitted to a journey that was timed. Change one here and nowhere else, and bump
# `ENGINE_VERSION` with it.
#
# A fixed part, in minutes: the walk to a stop, the wait, and the walk at the far end.
FIXED_MINUTES = 12.0
# And a part for each kilometre in a straight line between the homes and the place.
MINUTES_A_KM = 3.0
# Where the homes of the area are near a station of the Underground or the DLR, each
# kilometre takes less.
MINUTES_A_KM_NEAR_THE_UNDERGROUND = 2.5
# How near that is, in metres in a straight line.
NEAR_THE_UNDERGROUND_M = 800
# Likely within: the estimate is at least this many minutes under the limit.
WITHIN_BY = 5
# Likely beyond: the estimate is more than this many minutes over the limit. What lies
# between the two is borderline.
BEYOND_BY = 10
# What a band is worth to the fit where the limit is flexible. A journey that is likely
# within its limit is worth all of it, one that is likely beyond it nothing, and one that
# is borderline a half, which is what a journey exactly at its limit is worth.
WORTH: Mapping[JourneyBand, float] = MappingProxyType(
    {JourneyBand.LIKELY_WITHIN: 1.0, JourneyBand.BORDERLINE: 0.5, JourneyBand.LIKELY_BEYOND: 0.0}
)
# What is said wherever an estimate is shown. Every surface says it, word for word.
ESTIMATED = "Estimated from distance, not from a timetable."
# How each band is said before "the 40 minutes you set".
SAID: Mapping[JourneyBand, str] = MappingProxyType(
    {
        JourneyBand.LIKELY_WITHIN: "likely within",
        JourneyBand.BORDERLINE: "borderline for",
        JourneyBand.LIKELY_BEYOND: "likely beyond",
    }
)
# And how each is said where it stands alone, in a table or beside a journey.
VERDICT: Mapping[JourneyBand, str] = MappingProxyType(
    {
        JourneyBand.LIKELY_WITHIN: "Likely within your limit",
        JourneyBand.BORDERLINE: "Borderline for your limit",
        JourneyBand.LIKELY_BEYOND: "Likely beyond your limit",
    }
)
# The earth's mean radius, in kilometres.
_EARTH_KM = 6371.0088


class HowEstimated(Record):
    """The numbers an estimate is made with, for a page of methods to print."""

    fixed_minutes: float
    minutes_a_km: float
    minutes_a_km_near_the_underground: float
    near_the_underground_m: int
    within_by: int
    beyond_by: int
    # The line that stands wherever an estimate is shown.
    said: str


HOW = HowEstimated(
    fixed_minutes=FIXED_MINUTES,
    minutes_a_km=MINUTES_A_KM,
    minutes_a_km_near_the_underground=MINUTES_A_KM_NEAR_THE_UNDERGROUND,
    near_the_underground_m=NEAR_THE_UNDERGROUND_M,
    within_by=WITHIN_BY,
    beyond_by=BEYOND_BY,
    said=ESTIMATED,
)


def kilometres(one: Point, other: Point) -> float:
    """How far two points are from each other over the ground, in a straight line.

    Each is a longitude and a latitude.
    """
    east, north = math.radians(one[0]), math.radians(one[1])
    to_east, to_north = math.radians(other[0]), math.radians(other[1])
    half = (
        math.sin((to_north - north) / 2) ** 2
        + math.cos(north) * math.cos(to_north) * math.sin((to_east - east) / 2) ** 2
    )
    return 2 * _EARTH_KM * math.asin(math.sqrt(min(half, 1.0)))


def _near_the_underground(release: Release, area_id: str) -> bool:
    """Whether the homes of an area are known to stand near the Underground or the DLR.

    Where the release holds no figure for the area, they are not known to,
    and the estimate is made as for any other area.
    """
    row = release.feature(area_id, FeatureId.UNDERGROUND_PROXIMITY)
    return row is not None and row.value is not None and row.value <= NEAR_THE_UNDERGROUND_M


def estimated_minutes(release: Release, area_id: str, place: Place) -> float | None:
    """How long a journey by public transport is estimated to take, or `None`.

    It is for working a band out and for nothing else: no surface gives it.
    `None` where the release does not say where the homes of the area stand.
    """
    area = release.neighbourhood(area_id)
    if area is None or area.homes_at is None:
        return None
    rate = (
        MINUTES_A_KM_NEAR_THE_UNDERGROUND
        if _near_the_underground(release, area_id)
        else MINUTES_A_KM
    )
    return FIXED_MINUTES + rate * kilometres(area.homes_at, place.centroid)


def band_against(minutes: float, limit: int) -> JourneyBand:
    """Where an estimate stands against the limit a person gave."""
    if minutes <= limit - WITHIN_BY:
        return JourneyBand.LIKELY_WITHIN
    if minutes > limit + BEYOND_BY:
        return JourneyBand.LIKELY_BEYOND
    return JourneyBand.BORDERLINE


def estimate(
    release: Release, area_id: str, place_id: str, mode: Mode, limit: int
) -> JourneyBand | None:
    """The band of a journey that the release holds no time for, or `None`.

    `None` where nothing can be estimated: by bike or on foot, to a place the
    release does not hold, or from an area of which it does not say where
    the homes stand. The caller asks only where the release holds no time.
    """
    place = release.place(place_id)
    if mode is not Mode.PT or place is None:
        return None
    minutes = estimated_minutes(release, area_id, place)
    return None if minutes is None else band_against(minutes, limit)


def estimates_journeys(release: Release) -> bool:
    """Whether a journey of this release may be estimated: it names a place, and says of
    an area where its homes stand."""
    return bool(release.places) and any(
        area.homes_at is not None for area in release.neighbourhoods
    )
