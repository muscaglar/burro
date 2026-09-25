"""Which areas of the census of 2021 are the areas they were in 2011.

Some publishers give a figure for each MSOA of the census of 2011. An area of
a build is an MSOA of 2021. The Office for National Statistics publishes a
lookup between the two: each row pairs an area of 2011 with an area of 2021,
and gives the pair a mark.

| Mark | What the publisher's record says of it | What is made of it here |
|---|---|---|
| `U` | No change: "direct comparisons can be made" | The area of 2021 is the area of 2011 |
| `S` | An area of 2011 split into two or more of 2021 | Understood, and not carried |
| `M` | Areas of 2011 merged into one of 2021 | Never carried |
| `X` | The two do not fit | Never carried |

A figure that was published for an area of 2011 is given to an area of 2021
only under a mark that `CARRIED` names, and `CARRIED` names the mark of no
change alone. That is what the licence registry asks of the lookup: a figure
published for an area that was split, merged or drawn again is given to no
area of 2021, whole or in part. Nothing is ever shared out, by homes, by land
or by any other guess.

A split is understood all the same. An area of 2021 that was split from one
area of 2011 lies wholly inside it, so `taken_from` can name that area, where
it is asked to. Whether the figure of an area of 2011 may stand for each part
it was split into is the founder's to decide, and no build does it: to decide
it is to add the mark to `CARRIED`, to say so in the definition of every
measure that reads this, and to change the entry of the lookup in the licence
registry, in one change that a person reads. An area that was merged has two
figures and none of its own, and is never carried.

What is claimed here, and where each claim is from:

| What | Where it is from |
|---|---|
| The names of the columns | The file, as `describe` gave them on 2026-09-24 |
| That the mark's column is `CHNGIND` | The file. The record writes it `CHGIND` |
| What each mark means | The item's record, as the licence registry quotes it |
| That an unchanged area keeps its code | Held to the file: a row that breaks it stops the step |
| That the lookup is V2, as at December 2022 | The item's record. The file states neither |

What is read of a row: the four columns of `READ`. No name of an area or of
an authority is read. A row of an authority that is none of the build's is
passed over once its authority has been read, because the registry entry asks
that the rows of London's boroughs alone are read.

What the reader holds the file to: every column that is read is there, a code
is a code, a mark is one of the four the record names, a pair stands once,
every row of an authority of the build is of an area of the build, every area
of the build stands in a row, an area marked as unchanged has the code it had
and stands in no other row, an area of 2011 marked as split stands in two rows
or more, and the areas of 2011 marked as merged into one are two or more. A
file that breaks one stops the build.
"""

import re
from collections import Counter
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property

from burro_pipeline.cells.spine import Spine
from burro_pipeline.evidence.lock import LockError
from burro_pipeline.inputs import Inputs, Opened
from burro_pipeline.registry.model import Use

SOURCE = "ons-msoa11-msoa21-lad22-lookup"
EDITION = "V2"
PUBLISHER = "Office for National Statistics"
# The columns that are read, by their names in the file. It holds nine.
OF_2011, MARK, OF_2021, AUTHORITY = "MSOA11CD", "CHNGIND", "MSOA21CD", "LAD22CD"
READ = (OF_2011, MARK, OF_2021, AUTHORITY)
# The columns that are never read: three names, a name in Welsh and the number of a row.
NEVER_READ = ("MSOA11NM", "MSOA21NM", "LAD22NM", "LAD22NMW", "ObjectId")
# The shape of the code of an MSOA, and of a local authority, of England or of Wales.
AN_AREA = re.compile(r"[EW]02[0-9]{6}")
AN_AUTHORITY = re.compile(r"[EW]0[6-9][0-9]{6}")


class Mark(StrEnum):
    """What the publisher says became of an area of 2011, as the file writes it."""

    UNCHANGED = "U"
    SPLIT = "S"
    MERGED = "M"
    NO_FIT = "X"


# The marks a figure of an area of 2011 is given to an area of 2021 under. Do not add one
# but in a change that a person reads, with the registry entry of the lookup.
CARRIED = frozenset({Mark.UNCHANGED})


@dataclass(frozen=True, order=True)
class Pair:
    """One row of the lookup that is read: an area of 2021, an area of 2011 and their mark."""

    of_2021: str
    of_2011: str
    mark: Mark


@dataclass(frozen=True)
class Changes:
    """What the lookup says of the areas of a build."""

    # The rows of the authorities of the build, in the order of their codes.
    pairs: tuple[Pair, ...]
    # How many rows the file holds, of any authority.
    rows: int
    file_id: str

    @cached_property
    def of_2021(self) -> Mapping[str, tuple[Pair, ...]]:
        """The rows each area of 2021 stands in, by its code."""
        found: dict[str, list[Pair]] = {}
        for pair in self.pairs:
            found.setdefault(pair.of_2021, []).append(pair)
        return {code: tuple(pairs) for code, pairs in found.items()}

    @cached_property
    def marks(self) -> Mapping[str, Mark]:
        """The mark of each area of 2021. An area of two marks is one whose areas do not fit."""
        found: dict[str, Mark] = {}
        for code, pairs in self.of_2021.items():
            given = {pair.mark for pair in pairs}
            found[code] = given.pop() if len(given) == 1 else Mark.NO_FIT
        return found

    def taken_from(self, of_2021: str, carried: Collection[Mark] = CARRIED) -> str | None:
        """The area of 2011 whose figure an area of 2021 is given, or none.

        It is given one only where it stands in one row, under a mark that
        `carried` names. So an area that was merged is given none, whatever is
        named: it stands in a row for each area it was made of.
        """
        pairs = self.of_2021.get(of_2021, ())
        if len(pairs) != 1 or pairs[0].mark not in carried:
            return None
        return pairs[0].of_2011


def _refused(opened: Opened, words: str) -> LockError:
    return LockError("input_is_as_described", opened.file_id, words)


def _held_to_its_marks(opened: Opened, pairs: Collection[Pair]) -> None:
    """Stop where a mark is not what the rows of its areas are."""
    in_2011 = Counter(pair.of_2011 for pair in pairs)
    in_2021 = Counter(pair.of_2021 for pair in pairs)
    for pair in pairs:
        alone = in_2011[pair.of_2011] == 1 and in_2021[pair.of_2021] == 1
        if pair.mark is Mark.UNCHANGED and not (alone and pair.of_2011 == pair.of_2021):
            raise _refused(opened, "an area marked as unchanged is not the area it was")
        if pair.mark is Mark.SPLIT and in_2011[pair.of_2011] < 2:
            raise _refused(opened, "an area marked as split is split into one")
        if pair.mark is Mark.MERGED and in_2021[pair.of_2021] < 2:
            raise _refused(opened, "an area marked as merged is made of one")


def read(opened: Opened, authorities: Collection[str]) -> Changes:
    """The rows of the lookup that are of the authorities named, each held to what it says.

    `authorities` are the codes of the local authorities of the build. A row
    of any other is counted and passed over.
    """
    pairs: list[Pair] = []
    rows = 0
    with opened.text() as text:
        for row in opened.rows(text, READ):
            rows += 1
            if not AN_AUTHORITY.fullmatch(row[AUTHORITY]):
                raise _refused(opened, "a code is not a code")
            if row[AUTHORITY] not in authorities:
                continue
            if not (AN_AREA.fullmatch(row[OF_2011]) and AN_AREA.fullmatch(row[OF_2021])):
                raise _refused(opened, "a code is not a code")
            if row[MARK] not in Mark:
                raise _refused(opened, "a mark is none the publisher names")
            pairs.append(Pair(row[OF_2021], row[OF_2011], Mark(row[MARK])))
    if not pairs:
        raise _refused(opened, "it holds no row of the build")
    if len({(pair.of_2021, pair.of_2011) for pair in pairs}) != len(pairs):
        raise _refused(opened, "a pair of areas is there twice")
    _held_to_its_marks(opened, pairs)
    return Changes(pairs=tuple(sorted(pairs)), rows=rows, file_id=opened.file_id)


def build(inputs: Inputs, found: Spine) -> Changes:
    """What the lookup says of every area of the build, from the build's files.

    The gate is asked about the lookup before it is read, for the use a
    figure is put to. `found` is the spine of the same build: the lookup is
    held to it, so that every area of the build stands in a row, and no row of
    an authority of the build is of an area the build does not hold.
    """
    opened = inputs.open(SOURCE, Use.SCORING, edition=EDITION)
    changes = read(opened, {area.borough_code for area in found.areas})
    ours = {area.code for area in found.areas}
    if set(changes.of_2021) - ours:
        raise _refused(opened, "a row is of an area that is no area of the build")
    if ours - set(changes.of_2021):
        raise _refused(opened, "an area of the build has no row")
    return changes
