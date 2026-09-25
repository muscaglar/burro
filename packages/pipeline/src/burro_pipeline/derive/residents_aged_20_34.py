"""Residents aged 20 to 34, as a share of all residents, at Census 2021.

It is a figure about who lived in an area, and its name says so. The founder
decided on 24 September 2026 that the age of residents may feed a vibe and a
ranking (ADR 0006 as amended that day). A person may ask for more of what it
counts, and never for fewer.

What is counted: the usual residents of an MSOA in three bands of the table of
age by five-year age bands, 20 to 24, 25 to 29 and 30 to 34, added up, over
all its usual residents. `derive/census_msoa.py` holds the reading and the
arithmetic, and says what no page states of the file.

It is the measure the lockdown bears on most. The census counts a student at
the term-time address. The statistics office says the pandemic may have
affected where some people were usually resident on Census Day, names students
and some urban areas, and reports an analysis by the Greater London Authority
that found many young adults left London during lockdown and returned in the
spring and summer of 2021. Census Day was 21 March 2021. So the share may read
lower than it would in another year, and nothing in the table says where. No
page ties this to who rents a home, and this module does not.

Core holds the measure, under the name this module gives it, and a build
carries it. Core holds the rules that come with it: it is asked for towards
more and never towards fewer, it stands in no scale, and no likeness is
counted on it.
"""

from burro_core.ids import FeatureId

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import census_msoa
from burro_pipeline.derive.census_msoa import AGE, Of, Share
from burro_pipeline.inputs import Inputs

FEATURE = FeatureId.RESIDENTS_AGED_20_34
KEY = FEATURE.value
SOURCE = census_msoa.SOURCE
METHODS = census_msoa.METHODS
CANNOT_SEE = (
    "It counts who was living in the area on 21 March 2021, during a lockdown that the "
    "statistics office says may have changed where students and people in some urban areas "
    "were living, so the share may read lower than it would in another year.",
    "It cannot see who has moved in or out since, and it cannot tell a student from someone "
    "in work.",
)
MEASURE = Of(
    key=KEY,
    table=AGE,
    counted=("aged_20_24", "aged_25_29", "aged_30_34"),
    label="Residents aged 20 to 34 as a share of all residents, Census 2021",
    short_label="More young adults",
    said="Usual residents aged 20 to 34",
    cannot_see=CANNOT_SEE,
)


def is_the_table(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the table this measure reads."""
    return AGE.is_the_table(name)


def build(inputs: Inputs, found: Spine) -> Share:
    """The figure of every area and its evidence, from the files of the build."""
    return census_msoa.build(MEASURE, inputs, found)
