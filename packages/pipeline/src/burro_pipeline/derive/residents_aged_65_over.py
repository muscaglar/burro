"""Residents aged 65 and over, as a share of all residents, at Census 2021.

It is a figure about who lived in an area, and its name says so. The founder
decided on 24 September 2026 that the age of residents may feed a vibe and a
ranking (ADR 0006 as amended that day). A person may ask for more of what it
counts, and never for fewer.

What is counted: the usual residents of an MSOA in the five oldest bands of the
table of age by five-year age bands, from 65 to 69 up to 85 and over, added up,
over all its usual residents. `derive/census_msoa.py` holds the reading and
the arithmetic, and says what no page states of the file.

The statistics office says, on its page for the table of age by single year,
that its estimates for single years of age from 90 are less reliable than for
other ages. That table is not read. This measure reads bands of five years and
adds five of them up, the last of which is 85 and over, so that bears on it
little.

Core holds no such measure. `FeatureId` is the list of what may be ranked or
shown, and core lets no word for who lives somewhere stand in a name. So this
module makes no row of the catalogue and is not among the measures of a build.
"""

from burro_pipeline.cells.spine import Spine
from burro_pipeline.derive import census_msoa
from burro_pipeline.derive.census_msoa import AGE, SINCE, Of, Share
from burro_pipeline.inputs import Inputs

KEY = "residents_aged_65_over"
SOURCE = census_msoa.SOURCE
METHODS = census_msoa.METHODS
CANNOT_SEE = (
    f"It counts who was living in the area {SINCE}",
    "It is a share of everyone counted, so it cannot tell an area with many older residents "
    "from one with few younger ones.",
)
MEASURE = Of(
    key=KEY,
    table=AGE,
    counted=("aged_65_69", "aged_70_74", "aged_75_79", "aged_80_84", "aged_85_over"),
    label="Residents aged 65 and over as a share of all residents, Census 2021",
    short_label="More residents aged 65 and over",
    said="Usual residents aged 65 and over",
    cannot_see=CANNOT_SEE,
)


def is_the_table(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the table this measure reads."""
    return AGE.is_the_table(name)


def core_holds_it() -> bool:
    """Whether core has a feature under the id the rows are written under."""
    return census_msoa.core_holds(KEY)


def build(inputs: Inputs, found: Spine) -> Share:
    """The figure of every area and its evidence, from the files of the build."""
    return census_msoa.build(MEASURE, inputs, found)
