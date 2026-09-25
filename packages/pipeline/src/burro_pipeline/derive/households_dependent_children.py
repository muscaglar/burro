"""Households with dependent children, as a share of all households, at Census 2021.

It is a figure about who lived in an area, and its name says so. The founder
decided on 24 September 2026 that the household make-up of residents may feed
a vibe and a ranking (ADR 0006 as amended that day). A person may ask for more
of what it counts, and never for fewer.

What is counted: the households of an MSOA in the four categories of the table
of household composition that hold dependent children, added up, over all its
households. The four are the households of a married couple or civil
partners, of a cohabiting couple, of a lone parent, and of any other kind,
each with dependent children. What a dependent child is, is the census's own
to say, and this module does not repeat it.

The four are read only to be added up. The table splits households by whether
a couple is married, and names lone parents. No figure is made from one of the
four alone, and none may be: marriage and civil partnership is a protected
characteristic, and nothing was decided about it. `derive/census_msoa.py` holds
the reading and the arithmetic, and says what no page states of the file.

The statistics office says data about household relationships might not always
look consistent with legal partnership status. That bears on which of the four
a household is counted in, and not on their sum.

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

FEATURE = FeatureId.HOUSEHOLDS_DEPENDENT_CHILDREN
KEY = FEATURE.value
SOURCE = census_msoa.SOURCE
METHODS = census_msoa.METHODS
CANNOT_SEE = (
    f"It counts households as they were {SINCE}",
    "It is a share of households, so it cannot see how many children there are, how old they "
    "are, or whether they go to school nearby.",
)
# The four categories that hold dependent children. They are added up, and never read apart.
WITH_CHILDREN = (
    "couple_married_children",
    "couple_cohabiting_children",
    "lone_parent_children",
    "other_kinds_children",
)
MEASURE = Of(
    key=KEY,
    table=HOUSEHOLDS,
    counted=WITH_CHILDREN,
    label="Households with dependent children as a share of all households, Census 2021",
    short_label="More households with children",
    said="Households with dependent children, of every kind of family added together",
    cannot_see=CANNOT_SEE,
)


def is_the_table(name: str) -> bool:
    """Whether a publisher's name for a file is the name of the table this measure reads."""
    return HOUSEHOLDS.is_the_table(name)


def build(inputs: Inputs, found: Spine) -> Share:
    """The figure of every area and its evidence, from the files of the build."""
    return census_msoa.build(MEASURE, inputs, found)
