"""What the tests of schools share: a made-up register, laid out as the publisher's.

Nothing here is real. The file has the publisher's own layout: a zip that holds
one CSV named for its day, written as Windows-1252, with the 135 columns of the
register of 2026-09-24 in their order. What it holds is made up: a few schools
in the North Sea, where the made-up town of the tests of cells stands. No
school has a name. A canary stands in every column that is never read, and the
name of every school holds a letter that is no UTF-8 as the file writes it.

    northing
    450000+   a hundred schools, far from the town
    400100    three that do not count: one closed, one that charges fees, one secondary
    400000    A and B on one point . . . . . C . . . . . D, past the edge of London
              700000                      701000      702000

The town is twelve output areas in three areas. The centre of each is put
where a figure can be worked out by hand.

    Quillhaven 001   homes 110, 120, 130, 140   2, 2, 0 and 3 schools within 800 metres
    Quillhaven 002   homes 150, 160, 170, 180   1, 2, 1 and 0
    Tallowgate 001   homes 190, 200, 210, 220   none within 800 metres
"""

import csv
import hashlib
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.derive import schools_file
from burro_pipeline.evidence.receipt import How, Period, Receipt
from burro_pipeline.evidence.record import file_id_of
from burro_pipeline.fetch.store import FolderStore
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry import Registry
from burro_pipeline.registry.model import Use

from ..cells.support import FILES, contents, receipt_of, registry, zip_of
from .water_support import OAS, QUILLHAVEN_1, QUILLHAVEN_2, TALLOWGATE, centres_at, on

__all__ = ["OAS", "QUILLHAVEN_1", "QUILLHAVEN_2", "TALLOWGATE", "on"]

# A string found nowhere else. It stands in every column that is never read.
CANARY = "Zzyzx Parva"
# What stands for the name of a school. Its last letter is one byte in the file, and no UTF-8.
NAMELESS = "Made up \N{LATIN SMALL LETTER E WITH ACUTE}"
DAY = "2026-09-24"
ZIP_NAME, MEMBER = "extract.zip", "edubasealldata20260924.csv"
# The columns of the register of 2026-09-24, in its own order.
HELD = (
    "URN",
    "LA (code)",
    "LA (name)",
    "EstablishmentNumber",
    "EstablishmentName",
    "TypeOfEstablishment (code)",
    "TypeOfEstablishment (name)",
    "EstablishmentTypeGroup (code)",
    "EstablishmentTypeGroup (name)",
    "EstablishmentStatus (code)",
    "EstablishmentStatus (name)",
    "ReasonEstablishmentOpened (code)",
    "ReasonEstablishmentOpened (name)",
    "OpenDate",
    "ReasonEstablishmentClosed (code)",
    "ReasonEstablishmentClosed (name)",
    "CloseDate",
    "PhaseOfEducation (code)",
    "PhaseOfEducation (name)",
    "StatutoryLowAge",
    "StatutoryHighAge",
    "Boarders (code)",
    "Boarders (name)",
    "NurseryProvision (name)",
    "OfficialSixthForm (code)",
    "OfficialSixthForm (name)",
    "Gender (code)",
    "Gender (name)",
    "ReligiousCharacter (code)",
    "ReligiousCharacter (name)",
    "ReligiousEthos (name)",
    "Diocese (code)",
    "Diocese (name)",
    "AdmissionsPolicy (code)",
    "AdmissionsPolicy (name)",
    "SchoolCapacity",
    "SpecialClasses (code)",
    "SpecialClasses (name)",
    "CensusDate",
    "NumberOfPupils",
    "NumberOfBoys",
    "NumberOfGirls",
    "PercentageFSM",
    "TrustSchoolFlag (code)",
    "TrustSchoolFlag (name)",
    "Trusts (code)",
    "Trusts (name)",
    "SchoolSponsorFlag (name)",
    "SchoolSponsors (name)",
    "FederationFlag (name)",
    "Federations (code)",
    "Federations (name)",
    "UKPRN",
    "FEHEIdentifier",
    "FurtherEducationType (name)",
    "LastChangedDate",
    "Street",
    "Locality",
    "Address3",
    "Town",
    "County (name)",
    "Postcode",
    "SchoolWebsite",
    "TelephoneNum",
    "HeadTitle (name)",
    "HeadFirstName",
    "HeadLastName",
    "HeadPreferredJobTitle",
    "BSOInspectorateName (name)",
    "InspectorateReport",
    "DateOfLastInspectionVisit",
    "NextInspectionVisit",
    "TeenMoth (name)",
    "TeenMothPlaces",
    "CCF (name)",
    "SENPRU (name)",
    "EBD (name)",
    "PlacesPRU",
    "FTProv (name)",
    "EdByOther (name)",
    "Section41Approved (name)",
    *(f"SEN{number} (name)" for number in range(1, 14)),
    "TypeOfResourcedProvision (name)",
    "ResourcedProvisionOnRoll",
    "ResourcedProvisionCapacity",
    "SenUnitOnRoll",
    "SenUnitCapacity",
    "GOR (code)",
    "GOR (name)",
    "DistrictAdministrative (code)",
    "DistrictAdministrative (name)",
    "AdministrativeWard (code)",
    "AdministrativeWard (name)",
    "ParliamentaryConstituency (code)",
    "ParliamentaryConstituency (name)",
    "UrbanRural (code)",
    "UrbanRural (name)",
    "GSSLACode (name)",
    "Easting",
    "Northing",
    "MSOA (name)",
    "LSOA (name)",
    "InspectorateName (name)",
    "SENStat",
    "SENNoStat",
    "BoardingEstablishment (name)",
    "PropsName",
    "PreviousLA (code)",
    "PreviousLA (name)",
    "PreviousEstablishmentNumber",
    "Country (name)",
    "UPRN",
    "SiteName",
    "QABName (code)",
    "QABName (name)",
    "EstablishmentAccredited (code)",
    "EstablishmentAccredited (name)",
    "QABReport",
    "CHNumber",
    "MSOA (code)",
    "LSOA (code)",
    "FSM",
    "AccreditationExpiryDate",
)

Place = tuple[float, float]


@dataclass(frozen=True)
class MadeUpSchool:
    """One made-up row of the register, as far as a test says what it holds."""

    status: str = "Open"
    kind: str = "Community school"
    phase: str = "Primary"
    region: str = "London"
    # The two parts of its point, as the file writes them.
    east: str = ""
    north: str = ""
    # Its number, where a test needs one that is not its place in the file.
    urn: str | None = None


def at(east: int, north: int, **what: str) -> MadeUpSchool:
    return MadeUpSchool(east=str(east), north=str(north), **what)


A = at(700_000, 400_000)
# A second school on the same point, as an infant and a junior school on one site are.
B = at(700_000, 400_000, kind="Academy converter")
C = at(701_000, 400_000, kind="Voluntary aided school")
# Past the edge of London: the register gives it to another region.
D = at(702_000, 400_000, kind="Free schools", phase="All-through", region="East of England")
COUNTED = (A, B, C, D)
CLOSED = at(700_000, 400_100, status="Closed")
NOT_YET_OPEN = at(700_000, 400_100, status="Proposed to open", kind="Free schools")
CHARGES_FEES = at(700_000, 400_100, kind="Other independent school", phase="Not applicable")
SECONDARY = at(700_000, 400_100, phase="Secondary")
NURSERY = at(700_000, 400_100, kind="Local authority nursery school", phase="Nursery")
# A special school that the register gives no point, written as nought.
SPECIAL = MadeUpSchool(kind="Community special school", phase="Not applicable", east="0", north="0")
DO_NOT_COUNT = (CLOSED, NOT_YET_OPEN, CHARGES_FEES, SECONDARY, NURSERY, SPECIAL)
# A hundred schools that count, far from the town and in another region.
FAR_AWAY = tuple(
    at(700_000 + 1_000 * (number % 10), 450_000 + 1_000 * (number // 10), region="North East")
    for number in range(100)
)
REGISTER = (*COUNTED, *DO_NOT_COUNT, *FAR_AWAY)

# Where the centre of each output area stands, in the order of their codes.
PLACED: tuple[Place, ...] = (
    # Quillhaven 001: on the two schools, 800 metres from them exactly, half a metre
    # further, and half way between them and the third.
    (700_000, 400_000),
    (700_000, 400_800),
    (700_000, 400_800.5),
    (700_500, 400_000),
    # Quillhaven 002: on the third school, between it and the one past the edge, near
    # the one past the edge alone, and far from all four.
    (701_000, 400_000),
    (701_400, 400_000),
    (702_000, 400_600),
    (701_000, 403_000),
    # Tallowgate 001: far from every school.
    (705_000, 400_000),
    (705_000, 401_000),
    (706_000, 400_000),
    (706_000, 401_000),
)


def row_of(school: MadeUpSchool, number: int) -> dict[str, str]:
    """One row, with a canary in every column the measure never reads."""
    row = dict.fromkeys(HELD, CANARY)
    row |= {
        "URN": school.urn if school.urn is not None else str(900_000 + number),
        "EstablishmentName": NAMELESS,
        "EstablishmentStatus (name)": school.status,
        "TypeOfEstablishment (name)": school.kind,
        "PhaseOfEducation (name)": school.phase,
        "GOR (name)": school.region,
        "Easting": school.east,
        "Northing": school.north,
    }
    return row


def register_csv(
    schools: Sequence[MadeUpSchool] = REGISTER,
    *,
    columns: Sequence[str] = HELD,
    rows: Sequence[Mapping[str, str]] | None = None,
) -> bytes:
    """The register as the publisher writes it: Windows-1252, quoted, each line ended CRLF.

    The first line of the real file has a quote round every name. How its rows
    are quoted was not read, so every cell is quoted here: a reader of tables
    takes both.
    """
    text = io.StringIO(newline="")
    table = csv.writer(text, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    table.writerow(columns)
    made = [row_of(school, number) for number, school in enumerate(schools, start=1)]
    for row in made if rows is None else rows:
        table.writerow([row[name] for name in columns if name in row])
    return text.getvalue().encode("cp1252")


def zipped(
    register: bytes | None = None,
    *,
    member: str = MEMBER,
    beside: Mapping[str, bytes] | None = None,
) -> bytes:
    """The zip as the publisher gives it: the one file, under the name of its day.

    `beside` are files a test puts in the zip beside it, which the publisher does not.
    """
    held = {member: register_csv() if register is None else register}
    return zip_of(held | dict(beside or {}))


def with_one(school: MadeUpSchool) -> bytes:
    """The register of the town, and one school more."""
    return zipped(register_csv((*REGISTER, school)))


def register_receipt(content: bytes, name: str = ZIP_NAME, day: str = DAY) -> Receipt:
    sha256 = hashlib.sha256(content).hexdigest()
    return Receipt(
        file_id=file_id_of(sha256),
        source_id=schools_file.SOURCE,
        use=Use.SCORING,
        publisher_file=name,
        url=f"https://files.made-up.example/{sha256[:8]}",
        sha256=sha256,
        bytes=len(content),
        retrieved_at=f"{day}T00:00:00Z",
        how=How.BY_HAND,
        edition=day,
        data_period=Period(as_at=day),
    )


def inputs_of(
    folder: Path,
    packed: bytes | None = None,
    placed: Mapping[str, Place] | None = None,
    *,
    day: str = DAY,
    given: Registry | None = None,
) -> Inputs:
    """The made-up files of a build in a store of their own, with a receipt for each."""
    packed = zipped() if packed is None else packed
    files = contents() | {"centres": centres_at(on(*PLACED) if placed is None else placed)}
    every = [
        *(
            (receipt_of(*FILES[which][:3], content, FILES[which][3]), content)
            for which, content in files.items()
        ),
        (register_receipt(packed, day=day), packed),
    ]
    store = FolderStore(folder / "store")
    for receipt, content in every:
        path = folder / "given" / receipt.file_id / receipt.publisher_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        store.put(receipt.source_id, receipt.publisher_file, path)
    return Inputs(given or registry(), [receipt for receipt, _ in every], store, folder / "work")
