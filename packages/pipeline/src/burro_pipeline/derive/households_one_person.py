"""Households of one person, as a share of all households, at Census 2021.

It is a figure about who lived in an area, and its name says so. The founder
decided on 24 September 2026 that the household make-up of residents may feed
a vibe and a ranking (ADR 0006 as amended that day). A person may ask for more
of what it counts, and never for fewer.

What is counted: the households of an MSOA that the table of household
composition gives as a one-person household, over all its households. The
table splits them into those aged 66 and over and the rest. The split is not
read: the measure is the one the founder was asked about, and a split by age
inside it is a finer cut that nobody has decided on. So the figure cannot tell
a young person who lives alone from an old one. `derive/census_msoa.py` holds
the reading and the arithmetic, and says what no page states of the file.

Core holds the measure, under the name this module gives it, and a build
carries it. Core holds the rules that come with it: it is asked for towards
more and never towards fewer, it stands in no scale, and no likeness is
counted on it.
"""

from burro_core.ids import FeatureId

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import census_msoa
from burro_pipeline.derive.census_msoa import HOUSEHOLDS, SINCE, Of, Share
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.HOUSEHOLDS_ONE_PERSON
KEY = FEATURE.value
SOURCE = census_msoa.SOURCE
METHODS = census_msoa.METHODS
CANNOT_SEE = (
    f"It counts households as they were {SINCE}",
    "It cannot tell a young person who lives alone from an old one, and it says nothing of "
    "how many people live in the other households.",
)
MEASURE = Of(
    key=KEY,
    table=HOUSEHOLDS,
    counted=("one_person",),
    label="Households of one person as a share of all households, Census 2021",
    short_label="More households of one person",
    said="Households of one person",
    cannot_see=CANNOT_SEE,
)


def is_the_table(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the table this measure reads."""
    return HOUSEHOLDS.is_the_table(name)


def build(inputs: Inputs, found: Spine) -> Share:
    """The figure of every area and its evidence, from the files of the build."""
    return census_msoa.build(MEASURE, inputs, found)
