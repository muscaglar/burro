"""The files a draft is written as, each the same bytes for the same draft.

| File | One row is | Read by |
|---|---|---|
| `oa_to_area.csv` | An output area and its area: the design's curated file | The desk, a build |
| `oa_evidence.csv` | An output area, and the seeds it was weighed against | Whoever asks why |
| `areas_drawn.csv` | An area, measured: its size, its boroughs, its pieces | The flags |
| `absorbed.csv` | A seed that stands for no area of its own | The names, for an alias |
| `listed.csv` | An area the method could not put right | The flags |
| `cells.csv` | An output area as the ground holds it | The flags |
| `sides.csv` | Two output areas and the metres of side they share | The flags |
| `outlines.geojson` | An area's outline, in longitude and latitude | A map |
| `counts.json` | What was counted, and the numbers the method turned on | A person |

`oa_to_area.csv` holds the seven columns of the design. A row the method wrote
has `basis` `auto`, and says nothing of who decided or when: a person has not.
Its `evidence` is `key=value` pairs parted by `;`, with the keys the review
desk knows and no other: `margin`, `second`, `roads`, `ward`. A name that
holds `;` or `=` is left out of it.

What is written is made from publishers' files. It goes to a folder that git
does not track, and never into a tracked one.

Nothing here reads a clock. Rows are in the order of their codes, a line ends
with a line feed, and a number is written one way.
"""

import csv
import io
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from burro_pipeline.areas.assign import ROADS, WARD, Draft, Given
from burro_pipeline.areas.assign_files import Ground
from burro_pipeline.areas.assign_outline import Outlines, feature_collection
from burro_pipeline.areas.grow import MILLIMETRES_IN_A_METRE
from burro_pipeline.release.write import canonical_json

OA_TO_AREA = "oa_to_area.csv"
OA_EVIDENCE = "oa_evidence.csv"
AREAS_DRAWN = "areas_drawn.csv"
ABSORBED = "absorbed.csv"
LISTED = "listed.csv"
CELLS = "cells.csv"
SIDES = "sides.csv"
OUTLINES = "outlines.geojson"
COUNTS = "counts.json"
AUTO = "auto"
# The characters that part one pair of `evidence` from the next, and a key from its value.
PARTS = (";", "=", "\n", "\r")
# How many seeds a row of `oa_evidence.csv` has columns for.
SHOWN = 3


def table(columns: Sequence[str], rows: Iterable[Sequence[object]]) -> bytes:
    """A table as it is written: a header, a row a line, each line ended with a line feed."""
    text = io.StringIO(newline="")
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        if len(row) != len(columns):
            raise ValueError("a row holds as many values as the table has columns")
        writer.writerow(["" if value is None else value for value in row])
    return text.getvalue().encode("utf-8")


def metres(millimetres: int | None) -> str:
    """A distance in metres, to the whole metre. Nothing where there is none."""
    return "" if millimetres is None else str(round(millimetres / MILLIMETRES_IN_A_METRE))


def evidence_of(given: Given, ward: str, roads: str = "") -> str:
    """What placed an output area, as the desk reads it: `margin=7;second=lon-n0012;ward=...`."""
    pairs: list[tuple[str, str]] = []
    if given.margin is not None:
        pairs.append(("margin", str(given.margin)))
    if given.second:
        pairs.append(("second", given.second))
    if roads:
        pairs.append((ROADS, roads))
    if ward:
        pairs.append((WARD, ward))
    return ";".join(
        f"{key}={value}" for key, value in pairs if not any(part in value for part in PARTS)
    )


def _ward_of(ground: Ground, oa: str) -> str:
    return ground.wards[oa].name if oa in ground.wards else ""


def _roads_of(ground: Ground, oa: str) -> str:
    return ground.settlements[oa].name if oa in ground.settlements else ""


def oa_to_area(draft: Draft, ground: Ground) -> bytes:
    columns = ("oa21cd", "area_id", "basis", "evidence", "decided_by", "decided_on", "reason")
    return table(
        columns,
        (
            (
                oa,
                given.area,
                AUTO,
                evidence_of(given, _ward_of(ground, oa), _roads_of(ground, oa)),
                "",
                "",
                "",
            )
            for oa, given in sorted(draft.given.items())
        ),
    )


def oa_evidence(draft: Draft) -> bytes:
    columns = ["oa21cd", "area_id", "how", "margin", "second"]
    for number in range(1, SHOWN + 1):
        columns += [f"seed_{number}", f"metres_{number}", f"weighed_{number}", f"why_{number}"]
    rows: list[list[object]] = []
    for oa, given in sorted(draft.given.items()):
        row: list[object] = [oa, given.area, given.how, given.margin, given.second]
        for number in range(SHOWN):
            if number < len(given.choices):
                choice = given.choices[number]
                why = [*choice.favoured_by, *(["across_a_borough"] if choice.across else [])]
                row += [
                    choice.seed,
                    metres(choice.far),
                    str(round(choice.weighed / MILLIMETRES_IN_A_METRE)),
                    " ".join(why),
                ]
            else:
                row += ["", "", "", ""]
        rows.append(row)
    return table(columns, rows)


def areas_drawn(draft: Draft, ground: Ground, outlines: Outlines) -> bytes:
    columns = (
        "area_id",
        "output_areas",
        "hectares",
        "primary_borough",
        "boroughs",
        "pieces",
        "pieces_of_outline",
        "points_of_outline",
        "banks",
        "seed_inside",
        "seed_easting",
        "seed_northing",
        "inside_longitude",
        "inside_latitude",
        "beside",
    )
    seeds = {seed.seed_id: seed for seed in ground.seeds}
    rows: list[list[object]] = []
    for area, drawn in sorted(draft.drawn.items()):
        outline = outlines.of[area]
        rows.append(
            [
                area,
                len(drawn.cells),
                f"{drawn.hectares:.4f}",
                drawn.primary_borough,
                " ".join(f"{code}:{count}" for code, count in sorted(drawn.boroughs.items())),
                len(drawn.pieces),
                outline.pieces,
                outline.points,
                " ".join(bank or "not_drawn" for bank in drawn.banks),
                "yes" if drawn.seed_inside else "no",
                f"{seeds[area].point[0]:.1f}",
                f"{seeds[area].point[1]:.1f}",
                f"{outline.inside[0]:.6f}",
                f"{outline.inside[1]:.6f}",
                " ".join(f"{other}:{round(far)}" for other, far in sorted(drawn.beside.items())),
            ]
        )
    return table(columns, rows)


def absorbed(draft: Draft, ground: Ground) -> bytes:
    columns = (
        *("seed_id", "into", "why", "metres", "lies_in", "output_areas", "weight"),
        *("easting", "northing"),
    )
    seeds = {seed.seed_id: seed for seed in ground.seeds}
    return table(
        columns,
        (
            (
                each.seed,
                each.into,
                each.why,
                metres(each.far),
                each.lies_in,
                each.held,
                f"{seeds[each.seed].weight:g}",
                f"{seeds[each.seed].point[0]:.1f}",
                f"{seeds[each.seed].point[1]:.1f}",
            )
            for each in draft.absorbed
        ),
    )


def listed(draft: Draft) -> bytes:
    return table(
        ("area_id", "what", "output_areas"),
        ((each.area, each.what, " ".join(each.cells)) for each in draft.listed),
    )


def cells(draft: Draft, ground: Ground) -> bytes:
    columns = (
        "oa21cd",
        "area_id",
        "borough",
        "ward",
        "ward_share",
        "roads_name",
        "roads_naming_it",
        "roads",
        "bank",
        "hectares",
        "metres_round",
        "easting",
        "northing",
        "metres_to_node",
    )
    rows: list[list[object]] = []
    for cell in ground.cells:
        ward = ground.wards.get(cell.oa)
        named = ground.settlements.get(cell.oa)
        rows.append(
            [
                cell.oa,
                draft.given[cell.oa].area,
                cell.borough,
                ward.code if ward else "",
                f"{ward.share:.4f}" if ward else "",
                named.key if named else "",
                named.roads if named else "",
                named.of if named else "",
                cell.bank or "not_drawn",
                f"{cell.hectares:.4f}",
                f"{ground.around[cell.oa]:.1f}",
                f"{cell.centre[0]:.1f}",
                f"{cell.centre[1]:.1f}",
                metres(cell.to_node) if cell.node else "",
            ]
        )
    return table(columns, rows)


def sides(ground: Ground) -> bytes:
    return table(
        ("a", "b", "metres"),
        (
            (one, other, f"{far:.1f}")
            for one, others in sorted(ground.beside.items())
            for other, far in sorted(others.items())
            if one < other
        ),
    )


def counts(draft: Draft, ground: Ground, outlines: Outlines) -> bytes:
    sizes = sorted(len(each.cells) for each in draft.drawn.values())
    land = sorted(each.hectares for each in draft.drawn.values())
    written = canonical_json(feature_collection(outlines))
    rules = draft.rules
    document: dict[str, object] = {
        "rules": {
            "nearest": rules.nearest,
            "too_close": rules.too_close,
            "smallest": rules.smallest,
            "kept": sorted(rules.kept),
            "cut": dict(sorted(rules.cut.items())),
            "across_a_borough": rules.across_a_borough,
        },
        "ground": dict(ground.counted),
        "draft": draft.counts(),
        "seeds_outside_london": len(ground.outside),
        "sizes": {
            "output_areas_least": sizes[0],
            "output_areas_median": sizes[len(sizes) // 2],
            "output_areas_most": sizes[-1],
            "hectares_least": round(land[0], 1),
            "hectares_median": round(land[len(land) // 2], 1),
            "hectares_most": round(land[-1], 1),
        },
        "outlines": {
            "bytes": len(written),
            "points": sum(each.points for each in outlines.of.values()),
            "in_more_than_one_piece": sum(each.pieces > 1 for each in outlines.of.values()),
            "fit_together": outlines.fit_together,
        },
        "inputs": list(ground.inputs),
    }
    return canonical_json(document)


def files_of(draft: Draft, ground: Ground, outlines: Outlines) -> dict[str, bytes]:
    """Every file of a draft, by its name."""
    return {
        OA_TO_AREA: oa_to_area(draft, ground),
        OA_EVIDENCE: oa_evidence(draft),
        AREAS_DRAWN: areas_drawn(draft, ground, outlines),
        ABSORBED: absorbed(draft, ground),
        LISTED: listed(draft),
        CELLS: cells(draft, ground),
        SIDES: sides(ground),
        OUTLINES: canonical_json(feature_collection(outlines)),
        COUNTS: counts(draft, ground, outlines),
    }


def write(files: Mapping[str, bytes], folder: Path) -> None:
    """Write the files of a draft to a folder, each whole or not at all."""
    folder.mkdir(parents=True, exist_ok=True)
    for name in sorted(files):
        part = folder / f".part-{name}"
        part.write_bytes(files[name])
        part.replace(folder / name)
