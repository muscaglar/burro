"""A made-up zip of the police's crime files, for the tests of recorded incidents.

Nothing here is real. The zip is laid out as the form at data.police.uk lays
one out: a folder for each month, and in it a file for each force and each
kind of data. The names of the columns are the publisher's. Every record is
made up, and stands at a point of the made-up town of `tests/cells/support.py`,
which is in open sea. A canary stands in every column and every file that is
never read.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from burro_pipeline.cells.shapes import longitude_and_latitude
from burro_pipeline.derive import street_crime_files
from burro_pipeline.derive.street_crime_files import FORCES, HELD, SOURCE
from burro_pipeline.evidence.receipt import Period
from burro_pipeline.inputs import Inputs
from burro_pipeline.registry.model import Use

from ..cells.support import CANARY, EAST, NORTH, SIDE, contents, inputs_of, receipt_of, zip_of

NAME = "made-up.zip"
DAMAGE, ANTISOCIAL, OTHER = "Criminal damage and arson", "Anti-social behaviour", "Burglary"
ONE, TWO, THREE = "lon-ne02999001", "lon-ne02999002", "lon-ne02999003"
# The homes of each area of the made-up town, at its made-up census.
HOMES = {ONE: 500, TWO: 660, THREE: 820}
# The 36 months of the made-up zip, as the real one names its months.
MONTHS = tuple(f"{2023 + (7 + n) // 12}-{(7 + n) % 12 + 1:02d}" for n in range(36))
# The middle of one square of each area, and a point in the sea beside the town.
IN_ONE, IN_TWO, IN_THREE, AT_SEA = (0, 1), (2, 0), (4, 1), (20, 20)


def at(square: tuple[int, int]) -> tuple[str, str]:
    """The middle of a square of the town, as the file writes a point."""
    column, row = square
    longitude, latitude = longitude_and_latitude(
        EAST + column * SIDE + SIDE / 2, NORTH + row * SIDE + SIDE / 2
    )
    return f"{longitude:.6f}", f"{latitude:.6f}"


@dataclass(frozen=True)
class Record:
    """One made-up record: its kind, and the square it stands in, or none."""

    kind: str
    square: tuple[int, int] | None
    # The month the row itself states. It is the month of its file unless a test says other.
    month: str | None = None


# What every month of the larger force holds, unless a test says other: four records of
# criminal damage in the first area and two in the second, six of anti-social behaviour in
# the third, and one of a kind that no measure counts.
EVERY_MONTH: tuple[Record, ...] = (
    *(Record(DAMAGE, IN_ONE) for _ in range(4)),
    *(Record(DAMAGE, IN_TWO) for _ in range(2)),
    *(Record(ANTISOCIAL, IN_THREE) for _ in range(6)),
    Record(OTHER, IN_ONE),
)


def crime_csv(month: str, records: Sequence[Record]) -> str:
    lines = [",".join(HELD)]
    for record in records:
        longitude, latitude = at(record.square) if record.square is not None else ("", "")
        row = {
            "Crime ID": CANARY,
            "Month": record.month or month,
            "Reported by": CANARY,
            "Falls within": CANARY,
            "Longitude": longitude,
            "Latitude": latitude,
            "Location": CANARY,
            "LSOA code": CANARY,
            "LSOA name": CANARY,
            "Crime type": record.kind,
            "Last outcome category": CANARY,
            "Context": CANARY,
        }
        lines.append(",".join(row[name] for name in HELD))
    return "\n".join(lines) + "\n"


def members(
    changed: Mapping[str, Sequence[Record]] | None = None,
    months: Sequence[str] = MONTHS,
    forces: Sequence[str] = FORCES,
) -> dict[str, str | bytes]:
    """The members of a made-up zip. `changed` gives the records of a month of the larger force."""
    found: dict[str, str | bytes] = {}
    for month in months:
        for force in forces:
            held = (changed or {}).get(month, EVERY_MONTH) if force == FORCES[-1] else ()
            found[f"{month}/{month}-{force}-street.csv"] = crime_csv(month, held)
            # Two kinds of file that are never read. Every cell of each is the canary.
            found[f"{month}/{month}-{force}-outcomes.csv"] = f"Crime ID\n{CANARY}\n"
            found[f"{month}/{month}-{force}-stop-and-search.csv"] = f"Type\n{CANARY}\n"
    return found


def inputs_with(
    folder: Path, held: Mapping[str, str | bytes] | None = None, period: Period | None = None
) -> Inputs:
    """The made-up build with a made-up zip of crime files in its store."""
    content = zip_of(members() if held is None else held)
    inputs = inputs_of(folder, contents())
    given = folder / "given" / NAME
    given.write_bytes(content)
    inputs.store.put(SOURCE, NAME, given)
    receipt = receipt_of(SOURCE, Use.SCORING, NAME, content, street_crime_files.EDITION)
    stated = period or Period(start=MONTHS[0], end=MONTHS[-1])
    inputs.receipts = [*inputs.receipts, receipt.model_copy(update={"data_period": stated})]
    return inputs
