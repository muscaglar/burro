"""Describe gives the days a timetable says it runs on, and nothing else of it.

Every file here is made up. A timetable is laid out as TransXChange lays one
out: its stops, its routes and its operators stand before its services, and its
journeys after them. Each holds a canary wherever a name stands: a stop, a
line, an operator, a description. It must be in nothing describe gives back.
No socket is opened: the run blocks them, and describe refuses them too.

The layout was written from the schema, before a timetable of any publisher was
read. Describe was then run on the timetables of Transport for London as they
were stored on 2026-09-24: 826 files in six zips inside one, each with one
service that states both days and a mode.
"""

import io
import json
import zipfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pytest
from burro_pipeline.fetch.describe import DescribeError, as_text, describe
from burro_pipeline.fetch.kinds import DEEPEST

from .support import CANARY_ROW, made_up_zip

NAMESPACE = "http://www.transxchange.org.uk/"
# One service: the day it runs from, the day it runs to, and its mode, each as it is written.
Service = tuple[str | None, str | None, str | None]
ONE: Service = ("<StartDate>2026-09-19</StartDate>", "<EndDate>2026-10-23</EndDate>", "bus")
JOURNEYS = f"<VehicleJourneys><VehicleJourney>{CANARY_ROW}</VehicleJourney></VehicleJourneys>"


def service(runs_from: str | None, runs_to: str | None, mode: str | None) -> str:
    period = f"<OperatingPeriod>{runs_from or ''}{runs_to or ''}</OperatingPeriod>"
    return (
        f"<Service><ServiceCode>{CANARY_ROW}</ServiceCode>"
        f"<Lines><Line><LineName>{CANARY_ROW}</LineName></Line></Lines>"
        f"{period}<RegisteredOperatorRef>{CANARY_ROW}</RegisteredOperatorRef>"
        f"{'' if mode is None else f'<Mode>{mode}</Mode>'}"
        f"<Description>{CANARY_ROW}</Description></Service>"
    )


def timetable(
    services: Sequence[Service] = (ONE,), *, after: str = JOURNEYS, namespace: str = NAMESPACE
) -> bytes:
    """A made-up timetable: what stands before its services, its services, and what is after."""
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<TransXChange xmlns="{namespace}" CreationDateTime="2020-01-02T03:04:05" '
        f'FileName="{CANARY_ROW}.xml" SchemaVersion="2.1">'
        f"<StopPoints><StopPoint><CommonName>{CANARY_ROW}</CommonName>"
        # A day that is no day of a service, in a place that is not read.
        "<StartDate>1999-01-01</StartDate></StopPoint></StopPoints>"
        f"<Operators><Operator><OperatorShortName>{CANARY_ROW}</OperatorShortName>"
        "<Mode>coach</Mode></Operator></Operators>"
        f"<Services>{''.join(service(*one) for one in services)}</Services>"
        f"{after}</TransXChange>"
    ).encode()


def shape(path: Path, inside: bool = False) -> dict[str, Any]:
    found = describe(path, inside=inside)
    assert CANARY_ROW not in as_text(found)
    assert CANARY_ROW.lower() not in json.dumps(found).lower()
    return cast(dict[str, Any], found)


def of(tmp_path: Path, content: bytes) -> dict[str, Any]:
    path = tmp_path / "made-up.xml"
    path.write_bytes(content)
    return shape(path)


def zipped(members: dict[str, bytes]) -> bytes:
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), content)
    return packed.getvalue()


# The days


def test_a_timetable_gives_the_days_its_service_runs_from_and_to_and_its_mode(tmp_path: Path):
    content = timetable()
    assert of(tmp_path, content) == {
        "kind": "xml",
        "bytes": len(content),
        "root": "TransXChange",
        "services": 1,
        "runs_from": "2026-09-19",
        "runs_to": "2026-10-23",
        "modes": {"bus": 1},
    }


def test_of_several_services_the_earliest_and_the_latest_day_are_given(tmp_path: Path):
    services: list[Service] = [
        ("<StartDate>2026-09-19</StartDate>", "<EndDate>2026-10-23</EndDate>", "bus"),
        ("<StartDate>2026-08-01</StartDate>", "<EndDate>2026-09-30</EndDate>", "tram"),
        ("<StartDate>2026-09-21</StartDate>", "<EndDate>2026-12-31</EndDate>", "bus"),
    ]
    found = of(tmp_path, timetable(services))
    assert (found["services"], found["runs_from"], found["runs_to"]) == (
        3,
        "2026-08-01",
        "2026-12-31",
    )
    assert found["modes"] == {"bus": 2, "tram": 1}
    assert "no_day_from" not in found and "no_day_to" not in found


def test_a_service_that_states_no_day_it_runs_to_is_counted_and_adds_nothing(tmp_path: Path):
    """A timetable may run until it is replaced. No day stands in for the one it does not state."""
    services: list[Service] = [ONE, ("<StartDate>2026-09-01</StartDate>", None, "bus")]
    found = of(tmp_path, timetable(services))
    assert (found["runs_from"], found["runs_to"], found["no_day_to"]) == (
        "2026-09-01",
        "2026-10-23",
        1,
    )


def test_a_timetable_with_no_service_gives_no_day(tmp_path: Path):
    content = timetable(())
    assert of(tmp_path, content) == {
        "kind": "xml",
        "bytes": len(content),
        "root": "TransXChange",
        "services": 0,
    }


@pytest.mark.parametrize(
    "written",
    [
        f"<StartDate>{CANARY_ROW}</StartDate>",
        "<StartDate>2026-13-40</StartDate>",
        "<StartDate>2026-09-19T00:00:00</StartDate>",
        "<StartDate>19/09/2026</StartDate>",
        "<StartDate></StartDate>",
        "<StartDate/>",
        f"<StartDate><Day>2026-09-19</Day>{CANARY_ROW}</StartDate>",
        f"<StartDate>2026-09-19{CANARY_ROW * 40}</StartDate>",
        "<StartDate>2026-09-19</StartDate><StartDate>2026-09-20</StartDate>",
        None,
    ],
)
def test_what_stands_in_the_place_of_a_day_and_is_no_day_is_not_given(
    tmp_path: Path, written: str | None
):
    found = of(tmp_path, timetable([(written, "<EndDate>2026-10-23</EndDate>", "bus")]))
    assert "runs_from" not in found
    assert (found["services"], found["no_day_from"], found["runs_to"]) == (1, 1, "2026-10-23")


@pytest.mark.parametrize("mode", [CANARY_ROW, "Bus", "bus 25", "", f"<Kind>{CANARY_ROW}</Kind>"])
def test_a_mode_that_is_no_word_of_small_letters_is_not_given(tmp_path: Path, mode: str):
    found = of(tmp_path, timetable([(ONE[0], ONE[1], mode)]))
    assert "modes" not in found
    assert (found["runs_from"], found["runs_to"]) == ("2026-09-19", "2026-10-23")


def test_a_day_that_is_not_of_a_service_is_never_taken(tmp_path: Path):
    """The made-up stops hold a day of 1999, and the operators a mode. Neither is a service's."""
    found = of(tmp_path, timetable())
    assert "1999" not in as_text(found)
    assert found["modes"] == {"bus": 1}


# How far the file is read


def test_nothing_is_read_after_the_services(tmp_path: Path):
    """The journeys are most of a timetable. What is there is not well formed, and is not met."""
    found = of(tmp_path, timetable(after=f"<VehicleJourneys><{CANARY_ROW}"))
    assert (found["runs_from"], found["runs_to"]) == ("2026-09-19", "2026-10-23")


def test_a_timetable_is_known_by_its_root_whatever_namespace_it_is_written_in(tmp_path: Path):
    found = of(tmp_path, timetable(namespace="https://files.example/made-up"))
    assert (found["root"], found["runs_from"]) == ("TransXChange", "2026-09-19")


@pytest.mark.parametrize(
    "content",
    [
        b'<?xml version="1.0"?><made-up><Services><Service><OperatingPeriod>'
        b"<StartDate>2026-09-19</StartDate></OperatingPeriod></Service></Services></made-up>",
        b'<?xml version="1.0"?><!DOCTYPE TransXChange [<!ENTITY more "more">]>'
        b"<TransXChange><Services/></TransXChange>",
        b"<TransXChange",
    ],
)
def test_xml_that_is_no_timetable_is_not_read(tmp_path: Path, content: bytes):
    path = tmp_path / "made-up.xml"
    path.write_bytes(content)
    assert shape(path) == {"kind": "not_read", "bytes": len(content), "looks_like": "xml"}


def test_a_timetable_that_breaks_off_before_its_services_end_says_so_and_no_more(
    tmp_path: Path,
):
    path = tmp_path / "made-up.xml"
    path.write_bytes(timetable().split(b"</Services>")[0])
    with pytest.raises(DescribeError) as refused:
        describe(path)
    assert str(refused.value).startswith("the timetable could not be read: the XML is not well")
    assert CANARY_ROW not in str(refused.value)
    assert refused.value.__cause__ is None
    assert refused.value.__context__ is None or refused.value.__suppress_context__


# A zip of zips


def test_a_timetable_in_a_zip_inside_a_zip_is_read_with_inside(tmp_path: Path):
    """Transport for London's zip holds a zip for each group of services, and each holds XML."""
    buses = zipped({"made-up-1.xml": timetable(), "made-up-2.xml": timetable(())})
    path = made_up_zip(tmp_path / "timetables.zip", {"MADE UP BUSES 01012026.zip": buses})
    found = shape(path, inside=True)
    (member,) = found["members"]
    assert (member["name"], member["bytes"]) == ("MADE UP BUSES 01012026.zip", len(buses))
    assert member["inside"]["kind"] == "zip"
    first, second = member["inside"]["members"]
    assert (first["name"], first["bytes"]) == ("made-up-1.xml", len(timetable()))
    assert first["inside"] == {
        "kind": "xml",
        "root": "TransXChange",
        "services": 1,
        "runs_from": "2026-09-19",
        "runs_to": "2026-10-23",
        "modes": {"bus": 1},
    }
    assert second["inside"] == {"kind": "xml", "root": "TransXChange", "services": 0}
    assert list(tmp_path.iterdir()) == [path]


def test_without_inside_a_zip_inside_a_zip_is_named_and_not_opened(tmp_path: Path):
    buses = zipped({"made-up-1.xml": timetable()})
    path = made_up_zip(tmp_path / "timetables.zip", {"MADE UP BUSES 01012026.zip": buses})
    (member,) = shape(path)["members"]
    assert set(member) == {"name", "bytes", "packed_bytes"}


def test_a_timetable_in_a_zip_that_cannot_be_read_says_so_of_that_one_alone(tmp_path: Path):
    broken = timetable().split(b"</Services>")[0]
    path = made_up_zip(tmp_path / "buses.zip", {"broken.xml": broken, "whole.xml": timetable()})
    first, second = shape(path, inside=True)["members"]
    assert first["inside"]["kind"] == "not_read"
    assert first["inside"]["why"].startswith("the timetable could not be read")
    assert second["inside"]["runs_from"] == "2026-09-19"


def test_zips_are_looked_into_no_deeper_than_fetch_looks(tmp_path: Path):
    """Fetch looks into a zip and three zips inside one another. Describe goes no deeper."""
    content = zipped({"made-up.xml": timetable()})
    for _ in range(DEEPEST):
        content = zipped({"deeper.zip": content})
    path = tmp_path / "deep.zip"
    path.write_bytes(content)
    found = shape(path, inside=True)
    for _ in range(DEEPEST - 1):
        (member,) = found["members"]
        found = member["inside"]
    (last,) = found["members"]
    assert last["name"] == "deeper.zip"
    assert "inside" not in last
