"""The evidence of a name: one row for each record that writes it, for a page to cite.

Section 6 of the areas design gives the row. It is here as `Row`, with the
design's fourteen columns and four more that a draft needs: how the record's
label writes the name, how far off the record lies, who publishes it, and
whether its file has a receipt.

| Column | Here |
|---|---|
| `area_id`, `name` | The area the name is put forward for, and the name as its key writes it |
| `role` | `primary`, `alias` or `wide` |
| `source_id`, `record_id` | The registry id, and the publisher's own id of the record |
| `as_written`, `field` | The record's label in full, exactly as the file holds it, and its column |
| `locates` | What the record gives. Below |
| `data_date`, `retrieved_on` | From the file's receipt. Empty where the file has none |
| `snapshot_sha256` | The hash of the file the record was read from |
| `checked` | True: every row is made by reading the record in the file |
| `chosen_by`, `chosen_on` | Empty. A person chooses, at the review desk |

**`locates`, before a border is drawn.** No area has ground yet, so a row says
what its record gives and not whether that lies in the area. A point is
`point_inside`: a seed is a point of the place. An outline that holds the
place's point is `polygon_overlap`. An outline that does not is `label_only`
until a border shows that it overlaps.

**Who writes a name.** A record counts as writing a name when its label is the
name, or is several names of which one is the name. A label that holds the name
among other words is kept in the fuller file and left out of the design's, so
that nobody counts it as a second publisher.

**An id for every place.** The design gives an area `lon-n0001` onwards, never
reused. A person may turn any name into an area, so every place has an id,
whatever it is put forward as. Ids are given in the order of the records the
places are known by, and an id that was given before is kept: `ids` takes what
an earlier draft gave.
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from burro_core.ids import AREA_ID_PATTERN, SLUG_PATTERN

from burro_pipeline.areas import names_places
from burro_pipeline.areas.names_candidates import POINT, Candidate, Match, Place, Written
from burro_pipeline.areas.seeds import Key, Seed, Tier
from burro_pipeline.cells.spine import slug_of

PRIMARY, ALIAS, WIDE = "primary", "alias", "wide"
POINT_INSIDE, POLYGON_OVERLAP, LABEL_ONLY = "point_inside", "polygon_overlap", "label_only"
ROLE = {Tier.AREA: PRIMARY, Tier.SAME_GROUND: ALIAS, Tier.INSIDE: ALIAS, Tier.WIDE: WIDE}
DESIGN = (
    *("area_id", "name", "role", "source_id", "record_id", "as_written", "field"),
    *("locates", "data_date", "retrieved_on", "snapshot_sha256", "checked"),
    *("chosen_by", "chosen_on"),
)
FULLER = (*DESIGN, "match", "metres", "publisher", "has_receipt")
ID = "lon-n{:04d}"
NUMBER = re.compile(r"lon-n(\d{4,})")


@dataclass(frozen=True)
class Row:
    """One record that writes or holds one name, for one area."""

    area_id: str
    name: str
    role: str
    record: Candidate
    # The record's label, or for a second name of a record, that name.
    as_written: str
    field: str
    locates: str
    match: Match
    metres: float

    @property
    def writes(self) -> bool:
        """Whether the row is one of the design's: the record writes the name."""
        return self.match in (Match.SAME, Match.PART)

    def fuller(self) -> dict[str, str]:
        file = self.record.file
        return {
            "area_id": self.area_id,
            "name": self.name,
            "role": self.role,
            "source_id": self.record.source_id,
            "record_id": self.record.record_id,
            "as_written": self.as_written,
            "field": self.field,
            "locates": self.locates,
            "data_date": file.data_date,
            "retrieved_on": file.retrieved_on,
            "snapshot_sha256": file.sha256,
            "checked": "true",
            "chosen_by": "",
            "chosen_on": "",
            "match": self.match.value,
            "metres": f"{self.metres:.0f}",
            "publisher": file.publisher,
            "has_receipt": "true" if file.has_receipt else "false",
        }

    def design(self) -> dict[str, str]:
        written = self.fuller()
        return {column: written[column] for column in DESIGN}


def ids(places: Sequence[Place], held: Mapping[Key, str] | None = None) -> dict[Key, str]:
    """An id for every place. One that an earlier draft gave is kept, and none is given twice."""
    held = dict(held or {})
    if len(set(held.values())) != len(held) or not all(
        re.fullmatch(AREA_ID_PATTERN, each) and NUMBER.fullmatch(each) for each in held.values()
    ):
        raise ValueError("an id of an earlier draft is given twice, or is no id of an area")
    last = max(
        (int(match[1]) for each in held.values() if (match := NUMBER.fullmatch(each))), default=0
    )
    found: dict[Key, str] = {}
    # The populated places first, then the names only a town centre holds, each by its id.
    for place in sorted(places, key=lambda each: (each.record is None, each.key.key)):
        if place.key.key in held:
            found[place.key.key] = held[place.key.key]
        else:
            last += 1
            found[place.key.key] = ID.format(last)
    return found


def slugs(areas: Sequence[Seed], borough_names: Mapping[str, str]) -> dict[Key, str]:
    """A slug for every area, and no slug twice.

    Where two areas share a name the borough is added, as the design says. Two
    of one name in one borough are told apart by a number, in the order of their
    records.
    """
    wanted: dict[str, list[Seed]] = {}
    for seed in sorted(areas, key=lambda each: each.key):
        wanted.setdefault(slug_of(seed.name), []).append(seed)
    found: dict[Key, str] = {}
    taken: set[str] = set()
    for plain, same in sorted(wanted.items()):
        for seed in same:
            borough = borough_names.get(seed.place.key.borough, "")
            slug = plain if len(same) == 1 else slug_of(f"{seed.name} {borough}")
            number = 1
            while not slug or slug in taken:
                number += 1
                slug = f"{slug_of(f'{seed.name} {borough}') or 'area'}-{number}"
            if not re.fullmatch(SLUG_PATTERN, slug):
                raise ValueError("a name makes no slug")
            taken.add(slug)
            found[seed.key] = slug
    return found


def _locates(record: Candidate, metres: float) -> str:
    if record.gives == POINT:
        return POINT_INSIDE
    return POLYGON_OVERLAP if metres == 0 else LABEL_ONLY


def _row(area_id: str, seed: Seed, role: str, written: Written, name: str | None = None) -> Row:
    return Row(
        area_id=area_id,
        name=name or seed.name,
        role=role,
        record=written.candidate,
        as_written=written.candidate.as_written,
        field=written.candidate.field,
        locates=_locates(written.candidate, written.metres),
        match=written.match,
        metres=written.metres,
    )


def rows_of(seed: Seed, area_ids: Mapping[Key, str]) -> list[Row]:
    """Every row behind one name: its own record first, then every other, the nearest first.

    A name put forward as an area has its rows under its own id. A name put
    forward as a name of other areas has them under the id of each.
    """
    own = Written(seed.place.key, Match.SAME, 0.0)
    records = [own, *seed.place.others]
    role = ROLE[seed.tier]
    under = [area_ids[seed.key]] if seed.tier is Tier.AREA else [area_ids[key] for key in seed.of]
    found = [_row(area_id, seed, role, written) for area_id in under for written in records]
    second = seed.place.record.second_name if seed.place.record is not None else ""
    if second:
        # A second name of the same record is another name of the same ground.
        for area_id in under:
            found.append(
                Row(
                    area_id=area_id,
                    name=second,
                    role=ALIAS if role == PRIMARY else role,
                    record=seed.place.key,
                    as_written=second,
                    field=names_places.SECOND_NAME,
                    locates=POINT_INSIDE,
                    match=Match.SAME,
                    metres=0.0,
                )
            )
    return found
