"""Recorded anti-social behaviour: records a year for each 1,000 homes, for each area.

The figure comes from the police's own file of street-level crime, as recorded
criminal damage and arson does. `derive/incident_criminal_damage.py` holds the
counting, and says what is read, what is counted and what a moved point does.
This module says what differs.

What is counted: a record of the kind `Anti-social behaviour`, as the file
names it. The file says nothing more of the kind. The publisher's pages say it
is an incident that was reported and recorded, and no page was read to write
this, so no sentence of the measure says more than the name of the kind.

Core names the measure "Recorded anti-social behaviour", which is what the
file counts, and counts it for each 1,000 homes, as the figure is. So a build
whose lists hold the police's file carries it.
"""

from burro_core.ids import FeatureId

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import incident_criminal_damage
from burro_pipeline.derive.incident_criminal_damage import (
    NOT_SEEN,
    Counted,
    Incidents,
    Recorded,
    records,
)
from burro_pipeline.evidence.method import Method
from burro_pipeline.inputs import Inputs, Opened

FEATURE = FeatureId.INCIDENT_ANTISOCIAL
SOURCE = incident_criminal_damage.SOURCE
# What the rows of a crime file are keyed by.
KEYED_BY = incident_criminal_damage.KEYED_BY
# The arithmetic: what a methods page prints beside the measure.
METHODS: tuple[Method, ...] = incident_criminal_damage.METHODS

ANTISOCIAL = Recorded(
    feature=FEATURE,
    kind="Anti-social behaviour",
    label="Recorded anti-social behaviour",
    counts="Records of anti-social behaviour, ",
    cannot_see=(
        "It counts what the police recorded as anti-social behaviour, so it follows who calls "
        "the police as well as what happens.",
    ),
)

# What the product shows beside the figure.
CANNOT_SEE = (*ANTISOCIAL.cannot_see, *NOT_SEEN)


def is_the_zip(name: str) -> bool:
    """Whether a publisher's name for a file is the name of a zip the form made."""
    return incident_criminal_damage.is_the_zip(name)


def read(opened: Opened) -> Counted:
    """The records of the kind in the latest 36 months of the zip, at each point."""
    return incident_criminal_damage.read(opened, ANTISOCIAL)


def build(inputs: Inputs, found: Spine) -> Incidents:
    """The figure of every area and its evidence, from the files of the build."""
    return records(inputs, found, ANTISOCIAL)
