"""A made-up timetable in TransXChange, for the tests of its reader. It describes no real place.

It is the Amber line of the small town of `support.py`, one way: from Pellam
Cross through Tallowgate to Wexmoor. A train takes 5 minutes to Tallowgate,
stands there a minute, and takes 15 more to Wexmoor. Every stop bears the id
of a station of the synthetic release, and stands so many metres east and
north of a corner of the National Grid that no town is near.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field

from .support import CANARY, KINDLEWHARF, PELLAM, TALLOWGATE, WEXMOOR, WHERE

# Where Pellam Cross is put, in metres on the grid, so that no point is below nought.
CORNER = (10_000, 20_000)
WEEKDAYS = "<MondayToFriday/>"


def where(stop: str) -> tuple[float, float]:
    # A stop the town does not hold is put at its corner: a test of a broken file names one.
    east, north = WHERE.get(stop, (0, 0))
    return (float(CORNER[0] + east), float(CORNER[1] + north))


@dataclass(frozen=True)
class Link:
    """One stretch of a pattern, as the file writes it."""

    start: str
    end: str
    run: str
    # What the file says a train does at each end, and how long it stands there.
    at_start: str = "pickUpAndSetDown"
    at_end: str = "pickUpAndSetDown"
    wait_at_start: str = ""
    wait_at_end: str = ""


@dataclass(frozen=True)
class Journey:
    """One journey, as the file writes it."""

    code: str
    leaves: str
    # The days of the week it states, as the file writes them, or none. Or the whole of
    # what it states of the days it runs on, where a test writes more than days of the week.
    days: str = ""
    profile: str = ""
    pattern: str = "JP1"
    # Whatever else stands in it, as the file writes it.
    more: str = ""


AMBER = (
    Link(PELLAM, TALLOWGATE, "PT5M", at_start="pickUp", wait_at_end="PT1M"),
    Link(TALLOWGATE, WEXMOOR, "PT15M", at_end="setDown"),
)
MORNING = (Journey("VJ1", "07:00:00"), Journey("VJ2", "07:10:00"), Journey("VJ3", "07:20:00"))


@dataclass(frozen=True)
class Written:
    """A timetable to be written as a file. Each part may be changed to break it."""

    line: str = "Amber line"
    mode: str = "underground"
    runs: tuple[str, str] = ("2026-09-01", "2026-12-18")
    days: str = WEEKDAYS
    stops: Sequence[str] = (PELLAM, TALLOWGATE, WEXMOOR, KINDLEWHARF)
    patterns: dict[str, Sequence[Link]] = field(default_factory=lambda: {"JP1": AMBER})
    journeys: Sequence[Journey] = MORNING
    root: str = "TransXChange"
    # Whatever else stands before the root and after the service, as the file writes it.
    before: str = ""
    after_the_service: str = ""

    def _end(self, which: str, stop: str, does: str, wait: str) -> str:
        waits = f"<WaitTime>{wait}</WaitTime>" if wait else ""
        shown = f"<DynamicDestinationDisplay>{CANARY}</DynamicDestinationDisplay>"
        return (
            f"<{which}>{shown}<Activity>{does}</Activity>"
            f"<StopPointRef>{stop}</StopPointRef>{waits}</{which}>"
        )

    def _section(self, name: str, links: Sequence[Link]) -> str:
        written = "".join(
            f'<JourneyPatternTimingLink id="{name}-{place}">'
            + self._end("From", link.start, link.at_start, link.wait_at_start)
            + self._end("To", link.end, link.at_end, link.wait_at_end)
            + f"<RunTime>{link.run}</RunTime></JourneyPatternTimingLink>"
            for place, link in enumerate(links)
        )
        return f'<JourneyPatternSection id="S-{name}">{written}</JourneyPatternSection>'

    def _stop(self, stop: str) -> str:
        east, north = where(stop)
        return (
            f"<StopPoint><AtcoCode>{stop}</AtcoCode>"
            f"<Descriptor><CommonName>{CANARY}</CommonName></Descriptor>"
            f"<Place><Location><Easting>{east:.0f}</Easting>"
            f"<Northing>{north:.0f}</Northing></Location></Place></StopPoint>"
        )

    def _journey(self, journey: Journey) -> str:
        regular = f"<RegularDayType><DaysOfWeek>{journey.days}</DaysOfWeek></RegularDayType>"
        stated = journey.profile or (regular if journey.days else "")
        days = f"<OperatingProfile>{stated}</OperatingProfile>" if stated else ""
        return (
            f"<VehicleJourney>{days}<VehicleJourneyCode>{journey.code}</VehicleJourneyCode>"
            f"<JourneyPatternRef>{journey.pattern}</JourneyPatternRef>{journey.more}"
            f"<DepartureTime>{journey.leaves}</DepartureTime></VehicleJourney>"
        )

    def file(self) -> bytes:
        patterns = "".join(
            f'<JourneyPattern id="{name}"><JourneyPatternSectionRefs>S-{name}'
            "</JourneyPatternSectionRefs></JourneyPattern>"
            for name in self.patterns
        )
        return (
            f'<?xml version="1.0" encoding="utf-8"?>{self.before}'
            f'<{self.root} xmlns="http://www.transxchange.org.uk/">'
            f"<StopPoints>{''.join(self._stop(stop) for stop in self.stops)}</StopPoints>"
            f"<Routes><Route><Description>{CANARY}</Description></Route></Routes>"
            "<JourneyPatternSections>"
            f"{''.join(self._section(name, links) for name, links in self.patterns.items())}"
            "</JourneyPatternSections>"
            f"<Services><Service><Lines><Line><LineName>{self.line}</LineName></Line></Lines>"
            f"<OperatingPeriod><StartDate>{self.runs[0]}</StartDate>"
            f"<EndDate>{self.runs[1]}</EndDate></OperatingPeriod>"
            "<OperatingProfile><RegularDayType><DaysOfWeek>"
            f"{self.days}</DaysOfWeek></RegularDayType></OperatingProfile>"
            f"<Mode>{self.mode}</Mode>"
            f"<StandardService><Origin>{CANARY}</Origin>{patterns}</StandardService>"
            f"</Service>{self.after_the_service}</Services>"
            f"<VehicleJourneys>{''.join(self._journey(one) for one in self.journeys)}"
            f"</VehicleJourneys></{self.root}>"
        ).encode()
