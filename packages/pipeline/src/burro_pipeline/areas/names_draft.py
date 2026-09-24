"""A draft of the names and the seeds, read from the files and written for a person to decide.

`read` opens every file through the licence gate. `make` joins the records
into places, weighs them, thins the seeds and marks what to look at. `write`
puts it all in a folder that is no part of the repository: what is made from a
publisher's file is never committed.

| File | One row is |
|---|---|
| `candidates.csv` | One record of one file that names a place |
| `places.csv` | One place: its records joined, its points, what it is put forward as |
| `seeds.csv` | One name put forward as an area, and where its seed stands |
| `name_records.csv` | One record beside one name, with how it writes the name |
| `hard_look.csv` | One reason to look hard at one name |
| `stations.csv` | One railway station. It is no candidate: a mark is checked against it |
| `ids.csv` | The id of each place, to hand to the next draft |
| `decided.csv` | One name a person decided at the review desk, and what the method had made it |
| `draft/areas.csv`, `draft/aliases.csv` | As section 5 of the design, for the review desk |
| `draft/name_evidence.csv` | The same |
| `draft/flags_names.csv` | `queue`, `item`, `flag`, for the desk's queue of names |
| `counts.json` | Every count of the draft |

A cell that begins `=`, `+`, `-` or `@` and is no number gains a leading
apostrophe, as the desk's own files do, so that no sheet reads a name as a sum.
"""

import csv
import io
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from burro_pipeline.areas import (
    names_candidates,
    names_centres,
    names_evidence,
    names_files,
    names_ground,
    names_look,
    names_places,
    names_wards,
    seeds,
    seeds_roads,
)
from burro_pipeline.areas.names_candidates import Candidates, Place
from burro_pipeline.areas.names_centres import Centre
from burro_pipeline.areas.names_evidence import Row
from burro_pipeline.areas.names_files import File
from burro_pipeline.areas.names_ground import London
from burro_pipeline.areas.names_look import Look, Mark
from burro_pipeline.areas.names_places import Names
from burro_pipeline.areas.names_wards import Outlined
from burro_pipeline.areas.seeds import Draft, Key, Rules, Seed, Tier
from burro_pipeline.areas.seeds_roads import Roads
from burro_pipeline.cells import shapes, spine
from burro_pipeline.inputs import Inputs

DRAFT = "draft"
STARTS_A_SUM = ("=", "+", "-", "@")
DRAFTED = "drafted"
NAMES_QUEUE = "names"
# The flags of the desk's queue of names, and the mark each is.
FLAGS = {Mark.ONE_PUBLISHER: "one_publisher", Mark.SAME_NAME_ELSEWHERE: "same_name_elsewhere"}
# The kind of alias a second name of a record is: another name of the same ground.
SECOND_NAME_IS = Tier.SAME_GROUND.value
# The answer of the review desk that says a name is no name to keep.
NOT_KEPT = "drop"
# What a person may say of a name at the review desk, and what the draft makes of each.
ANSWERS: Mapping[str, Tier | None] = {**{tier.value: tier for tier in Tier}, NOT_KEPT: None}


@dataclass(frozen=True)
class Read:
    """Everything that was read, from every file the gate gives for names."""

    london: London
    names: Names
    centres: tuple[Centre, ...]
    wards: tuple[Outlined, ...]
    boroughs: tuple[Outlined, ...]
    roads: Roads
    # Every file that was read, by its source.
    files: Mapping[str, File]


@dataclass(frozen=True)
class Drafted:
    """A draft of the names and seeds, with all that stands behind it."""

    candidates: Candidates
    seeds: Draft
    area_ids: Mapping[Key, str]
    slugs: Mapping[Key, str]
    rows: tuple[Row, ...]
    looks: tuple[Look, ...]
    borough_names: Mapping[str, str]
    files: Mapping[str, File]
    lookup: File
    # What a person decided at the review desk, by the id of the place: an answer of the desk.
    decided: Mapping[str, str] = field(default_factory=dict[str, str])

    @property
    def by_key(self) -> dict[Key, Seed]:
        return {seed.key: seed for seed in self.seeds.seeds}


def read(inputs: Inputs, *, draft: bool) -> Read:
    """Every file, through the gate. `draft` lets the one file with no receipt be read."""
    london = names_ground.read(inputs)
    open_names = names_files.with_receipt(inputs, names_places.SOURCE)
    centres = names_files.either(inputs, names_centres.SOURCE, draft=draft)
    line = names_files.with_receipt(inputs, names_wards.SOURCE)
    roads = names_files.with_receipt(inputs, seeds_roads.SOURCE)
    return Read(
        london=london,
        names=names_places.read(open_names, london.ground.box),
        centres=names_centres.read(centres),
        wards=names_wards.read_wards(line),
        boroughs=names_wards.read_boroughs(line),
        roads=seeds_roads.read(roads, london.ground.box),
        files={
            file.source_id: file
            for file in (open_names, centres, line, roads, london.lookup, london.boundaries)
        },
    )


def make(
    held: Read,
    rules: Rules | None = None,
    *,
    ids: Mapping[Key, str] | None = None,
    points: int | None = None,
    publishers: int | None = None,
    decided: Mapping[str, str] | None = None,
) -> Drafted:
    """The draft, from what was read. With `points` and `publishers`, by that rule alone.

    `decided` is what a person said at the review desk of a name, by the id of
    the place: an answer of the desk's queue of names. It raises `ValueError`
    for an id the draft does not hold, and for an answer that is none of the
    desk's.
    """
    found = names_candidates.join(
        held.london, held.names, held.centres, held.wards, held.boroughs, held.files
    )
    area_ids = names_evidence.ids(found.places, ids)
    by_id = {area_id: key for key, area_id in area_ids.items()}
    decided = dict(sorted((decided or {}).items()))
    if not set(decided) <= set(by_id):
        raise ValueError("a decision is about a place the draft does not hold")
    if not set(decided.values()) <= set(ANSWERS):
        raise ValueError(f"an answer is none of: {', '.join(ANSWERS)}")
    drafted = seeds.draft(
        found.places,
        held.centres,
        held.roads,
        rules,
        points=points,
        publishers=publishers,
        decided={by_id[area_id]: ANSWERS[answer] for area_id, answer in decided.items()},
    )
    rows = [row for seed in drafted.seeds for row in names_evidence.rows_of(seed, area_ids)]
    is_ward = {ward.record_id for ward in held.wards}
    of_line = [record for record in found.records if record.source_id == names_wards.SOURCE]
    wards = [record for record in of_line if record.record_id in is_ward]
    boroughs = [record for record in of_line if record.record_id not in is_ward]
    return Drafted(
        candidates=found,
        seeds=drafted,
        area_ids=area_ids,
        slugs=names_evidence.slugs(drafted.areas, held.london.borough_names),
        rows=tuple(rows),
        looks=names_look.marks(
            drafted.seeds,
            found.stations,
            wards,
            boroughs,
            held.london.borough_names,
            held.files,
        ),
        borough_names=held.london.borough_names,
        files=held.files,
        lookup=held.london.lookup,
        decided=decided,
    )


# Writing


def _is_a_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def _safe(value: object) -> str:
    """A cell as it is written. A number is left as it is: a longitude west of the meridian
    begins with a minus sign, and is no sum."""
    text = "" if value is None else str(value)
    return f"'{text}" if text.startswith(STARTS_A_SUM) and not _is_a_number(text) else text


def table(columns: Sequence[str], rows: Iterable[Mapping[str, object]]) -> bytes:
    """A table as it is written: its columns in order, and lines that end with a line feed."""
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=list(columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: _safe(row.get(column, "")) for column in columns})
    return text.getvalue().encode("utf-8")


def _whole(value: float) -> str:
    return f"{value:.0f}"


def _on_the_globe(at: tuple[float, float]) -> dict[str, str]:
    longitude, latitude = shapes.longitude_and_latitude(*at)
    return {"longitude": f"{longitude:.6f}", "latitude": f"{latitude:.6f}"}


def _file(file: File) -> dict[str, str]:
    return {
        "file_id": file.file_id,
        "snapshot_sha256": file.sha256,
        "edition": file.edition,
        "data_date": file.data_date,
        "retrieved_on": file.retrieved_on,
        "has_receipt": "true" if file.has_receipt else "false",
    }


CANDIDATES = (
    *("source_id", "publisher", "record_id", "as_written", "field", "kind", "gives"),
    *("easting", "northing", "longitude", "latitude", "oa21cd", "lad22cd", "borough"),
    *("file_id", "snapshot_sha256", "edition", "data_date", "retrieved_on", "has_receipt"),
    "area_id",
)


def candidates_of(drafted: Drafted) -> list[dict[str, str]]:
    """Every record that names a place, as a row. A second name of a record is a row too."""
    found: list[dict[str, str]] = []
    joined: dict[tuple[str, str], str] = {}
    for place in drafted.candidates.places:
        area_id = drafted.area_ids[place.key.key]
        joined[(place.key.source_id, place.key.record_id)] = area_id
        for other in place.written_by(names_centres.SOURCE):
            if other.match is names_candidates.Match.SAME:
                joined[(other.candidate.source_id, other.candidate.record_id)] = area_id
    second = {
        place.key.record_id: place.record.second_name
        for place in drafted.candidates.places
        if place.record is not None and place.record.second_name
    }
    for record in drafted.candidates.records:
        row = {
            "source_id": record.source_id,
            "publisher": record.publisher,
            "record_id": record.record_id,
            "as_written": record.as_written,
            "field": record.field,
            "kind": record.kind,
            "gives": record.gives,
            "easting": _whole(record.at[0]),
            "northing": _whole(record.at[1]),
            **_on_the_globe(record.at),
            "oa21cd": record.cell,
            "lad22cd": record.borough,
            "borough": drafted.borough_names.get(record.borough, ""),
            **_file(record.file),
            "area_id": joined.get((record.source_id, record.record_id), ""),
        }
        found.append(row)
        if record.source_id == names_places.SOURCE and record.record_id in second:
            found.append(
                row | {"as_written": second[record.record_id], "field": names_places.SECOND_NAME}
            )
    for code, name in sorted(drafted.borough_names.items()):
        found.append(
            {
                "source_id": drafted.lookup.source_id,
                "publisher": drafted.lookup.publisher,
                "record_id": code,
                "as_written": name,
                "field": spine.BOROUGH_NAME,
                "kind": names_candidates.BOROUGH,
                "gives": "output_areas",
                "lad22cd": code,
                "borough": name,
                **_file(drafted.lookup),
            }
        )
    return found


PLACES = (
    *("area_id", "name", "tier", "why", "of", "of_names", "slug"),
    *("source_id", "record_id", "kind", "lad22cd", "borough"),
    *("points", "points_place", "points_roads", "points_centre", "points_ward"),
    *("road_records", "centre_record", "centre_metres", "ward_record"),
    *("publishers_with_points", "publishers_writing", "one_publisher"),
    *("put", "own_centre", "easting", "northing", "longitude", "latitude"),
    *("place_easting", "place_northing", "metres", "along_roads", "tie"),
    *("rests_on", "no_receipt", "marks"),
)
SEEDS = (
    *("seed_id", "area_id", "name", "slug", "easting", "northing", "longitude", "latitude"),
    *("weight", "publishers_with_points", "publishers_writing", "one_publisher"),
    *("put", "own_centre", "lad22cd", "borough", "no_receipt", "marks"),
)


def rests_on_no_receipt(seed: Seed, files: Mapping[str, File]) -> bool:
    """Whether a name, its points or its seed rest on a file that has no receipt."""
    return any(not files[source].has_receipt for source in names_look.rests_on(seed))


def places_of(drafted: Drafted) -> list[dict[str, str]]:
    """Every place, with its points and what it is put forward as."""
    by_key = drafted.by_key
    marked: dict[Key, list[str]] = {}
    for look in drafted.looks:
        if look.mark.value not in marked.setdefault(look.key, []):
            marked[look.key].append(look.mark.value)
    found: list[dict[str, str]] = []
    for seed in sorted(drafted.seeds.seeds, key=lambda each: drafted.area_ids[each.key]):
        weight, key = seed.weight, seed.place.key
        found.append(
            {
                "area_id": drafted.area_ids[seed.key],
                "seed_id": key.record_id,
                "name": seed.name,
                "tier": seed.tier.value,
                "why": seed.why.value,
                "of": ";".join(drafted.area_ids[each] for each in seed.of),
                "of_names": ";".join(by_key[each].name for each in seed.of),
                "slug": drafted.slugs.get(seed.key, ""),
                "source_id": key.source_id,
                "record_id": key.record_id,
                "kind": key.kind,
                "lad22cd": key.borough,
                "borough": drafted.borough_names.get(key.borough, ""),
                "points": str(weight.total),
                "weight": str(weight.total),
                "points_place": str(weight.place),
                "points_roads": str(weight.roads),
                "points_centre": str(weight.centre),
                "points_ward": str(weight.ward),
                "road_records": str(seed.place.roads),
                "centre_record": weight.centre_record,
                "centre_metres": ""
                if weight.centre_metres is None
                else _whole(weight.centre_metres),
                "ward_record": weight.ward_record,
                "publishers_with_points": ";".join(weight.publishers),
                "publishers_writing": ";".join(seed.place.publishers),
                "one_publisher": "true" if seed.one_publisher else "false",
                "put": seed.put.value,
                "own_centre": seed.own_centre,
                "easting": _whole(seed.at[0]),
                "northing": _whole(seed.at[1]),
                **_on_the_globe(seed.at),
                "place_easting": _whole(seed.place.at[0]),
                "place_northing": _whole(seed.place.at[1]),
                "metres": "" if seed.metres is None else _whole(seed.metres),
                "along_roads": "true" if seed.along_roads else "false",
                "tie": "true" if seed.tie else "false",
                "rests_on": ";".join(names_look.rests_on(seed)),
                "no_receipt": "true" if rests_on_no_receipt(seed, drafted.files) else "false",
                "marks": ";".join(marked.get(seed.key, [])),
            }
        )
    return found


def _item(drafted: Drafted, seed: Seed) -> str:
    """The id of a name's item at the review desk.

    The desk names the item of another name by the first area it is given to, in the
    order of the rows of `aliases.csv`, which is the order of the ids.
    """
    if seed.tier is Tier.AREA:
        return f"n:{drafted.area_ids[seed.key]}"
    first = min((drafted.area_ids[key] for key in seed.of), default="")
    return f"a:{first}:{spine.slug_of(seed.name)}"


def desk_of(drafted: Drafted) -> dict[str, list[dict[str, str]]]:
    """The three files of names as the review desk reads them, and the flags of its queue."""
    by_key = drafted.by_key
    areas = [
        {
            "area_id": drafted.area_ids[seed.key],
            "slug": drafted.slugs[seed.key],
            "name": seed.name,
            "primary_borough": drafted.borough_names.get(seed.place.key.borough, ""),
            "seed_record": seed.place.key.record_id,
            "review_state": DRAFTED,
            "superseded_by": "",
        }
        for seed in sorted(drafted.seeds.areas, key=lambda each: drafted.area_ids[each.key])
    ]
    aliases: list[dict[str, str]] = []
    for seed in drafted.seeds.seeds:
        second = seed.place.record.second_name if seed.place.record is not None else ""
        record = {"source_id": seed.place.key.source_id, "record_id": seed.place.key.record_id}
        under = [seed.key] if seed.tier is Tier.AREA else list(seed.of)
        for key in under:
            if seed.tier is not Tier.AREA:
                aliases.append(
                    {"alias": seed.name, "area_id": drafted.area_ids[key], "kind": seed.tier.value}
                    | record
                )
            if second:
                aliases.append(
                    {"alias": second, "area_id": drafted.area_ids[key], "kind": SECOND_NAME_IS}
                    | record
                )
    flags = [
        {"queue": NAMES_QUEUE, "item": _item(drafted, by_key[look.key]), "flag": FLAGS[look.mark]}
        for look in drafted.looks
        if look.mark in FLAGS and (by_key[look.key].tier is Tier.AREA or by_key[look.key].of)
    ]
    unique = {(flag["item"], flag["flag"]): flag for flag in flags}
    return {
        "areas.csv": areas,
        "aliases.csv": sorted(aliases, key=lambda row: (row["area_id"], row["alias"], row["kind"])),
        "name_evidence.csv": [row.design() for row in drafted.rows if row.writes],
        "flags_names.csv": [unique[key] for key in sorted(unique)],
    }


DESK = {
    "areas.csv": (
        *("area_id", "slug", "name", "primary_borough"),
        *("seed_record", "review_state", "superseded_by"),
    ),
    "aliases.csv": ("alias", "area_id", "kind", "source_id", "record_id"),
    "name_evidence.csv": names_evidence.DESIGN,
    "flags_names.csv": ("queue", "item", "flag"),
}
LOOKS = ("area_id", "name", "tier", "borough", "mark", "grave", "why", "source_id", "record_id")
DECIDED = ("area_id", "name", "answer", "was", "source_id", "record_id")
STATIONS = ("source_id", "record_id", "as_written", "easting", "northing", "oa21cd", "lad22cd")
IDS = ("area_id", "source_id", "record_id", "field")


def counts_of(drafted: Drafted) -> dict[str, object]:
    """Every count of the draft. It holds numbers and the publishers' own labels, and no name."""
    held, places = drafted.seeds, drafted.candidates.places
    areas = held.areas
    records = drafted.candidates.records

    def places_by(what: str) -> dict[str, int]:
        found = Counter(
            (seed.place.key.source_id if what == "source" else seed.tier.value)
            for seed in held.seeds
        )
        return dict(sorted(found.items()))

    def with_points(seed: Seed) -> int:
        return len(seed.weight.publishers)

    marked: dict[str, set[Key]] = {}
    for look in drafted.looks:
        marked.setdefault(look.mark.value, set()).add(look.key)
    of_areas = {seed.key for seed in areas}
    # The populated places that may be seeds: every one but a wide name.
    settled = [
        seed for seed in held.seeds if seed.place.record is not None and seed.tier is not Tier.WIDE
    ]
    return {
        "rule": {
            "points": held.points,
            "publishers": held.publishers,
            "in_range": held.in_range,
            "least": held.rules.least,
            "most": held.rules.most,
        },
        "tried": [
            {"points": each.points, "publishers": each.publishers, "areas": each.areas}
            for each in held.tried
        ],
        "candidates_by_source": dict(sorted(Counter(r.source_id for r in records).items())),
        "candidates_by_publisher": dict(sorted(Counter(r.publisher for r in records).items())),
        "candidates_by_source_and_kind": {
            f"{source}|{kind}": count
            for (source, kind), count in sorted(
                Counter((r.source_id, r.kind) for r in records).items()
            )
        },
        "distinct_names": len({names_candidates.fold(r.as_written) for r in records}),
        "distinct_names_less_the_word_for_the_kind": len(
            {
                names_candidates.fold(
                    names_candidates.core(
                        r.as_written, names_candidates.ENDINGS.get(r.source_id, ())
                    )
                )
                for r in records
            }
        ),
        "populated_places_by_what_gave_points": {
            "roads": sum(1 for seed in settled if seed.weight.roads),
            "town_centre": sum(1 for seed in settled if seed.weight.centre),
            "ward": sum(1 for seed in settled if seed.weight.ward),
        },
        "borough_names_in_the_lookup": len(drafted.borough_names),
        "stations": len(drafted.candidates.stations),
        "outside_london": dict(drafted.candidates.outside),
        "places": len(places),
        "places_by_source_of_key": places_by("source"),
        "places_joined_under_two_publishers": sum(len(p.publishers) > 1 for p in places),
        "town_centres_joined_to_a_populated_place": sum(
            1
            for place in places
            for other in place.written_by(names_centres.SOURCE)
            if other.match is names_candidates.Match.SAME
        ),
        "joined_beyond_1km": len(marked.get(Mark.JOINED_BEYOND_1KM.value, ())),
        "places_by_points": dict(
            sorted(Counter(str(seed.weight.total) for seed in held.seeds).items())
        ),
        "places_by_tier": places_by("tier"),
        "places_by_tier_and_why": {
            f"{tier}|{why}": count
            for (tier, why), count in sorted(
                Counter((s.tier.value, s.why.value) for s in held.seeds).items()
            )
        },
        "areas": len(areas),
        "areas_by_kind": dict(sorted(Counter(s.place.key.kind for s in areas).items())),
        "areas_by_points": dict(sorted(Counter(str(s.weight.total) for s in areas).items())),
        "areas_put_on_a_town_centre": sum(s.put is seeds.Put.CENTRE for s in areas),
        "areas_whose_name_one_publisher_writes": sum(s.one_publisher for s in areas),
        "areas_whose_name_two_publishers_write": sum(not s.one_publisher for s in areas),
        "areas_with_points_from_one_publisher": sum(with_points(s) < seeds.TWO for s in areas),
        "areas_with_points_from_two_publishers": sum(with_points(s) >= seeds.TWO for s in areas),
        "areas_resting_on_a_file_with_no_receipt": sum(
            rests_on_no_receipt(s, drafted.files) for s in areas
        ),
        "places_whose_name_one_publisher_writes": sum(s.one_publisher for s in held.seeds),
        "evidence_rows": len(drafted.rows),
        "evidence_rows_of_the_design": sum(row.writes for row in drafted.rows),
        "marks": {mark: len(keys) for mark, keys in sorted(marked.items())},
        "marks_on_areas": {mark: len(keys & of_areas) for mark, keys in sorted(marked.items())},
        "places_marked": len({look.key for look in drafted.looks}),
        "decided_at_the_desk": dict(sorted(Counter(drafted.decided.values()).items())),
        "areas_marked_for_more_than_one_publisher_or_receipt": len(
            {
                look.key
                for look in drafted.looks
                if look.key in of_areas and look.mark not in (Mark.ONE_PUBLISHER, Mark.NO_RECEIPT)
            }
        ),
        "files": {
            source: {"file_id": file.file_id, "has_receipt": file.has_receipt}
            for source, file in sorted(drafted.files.items())
        },
    }


def decided_of(drafted: Drafted) -> list[dict[str, str]]:
    """Every name a person decided, with what the method had put it forward as."""
    by_id = {area_id: key for key, area_id in drafted.area_ids.items()}
    named = {place.key.key: place.name for place in drafted.candidates.places}
    return [
        {
            "area_id": area_id,
            "name": named[by_id[area_id]],
            "answer": answer,
            "was": drafted.seeds.before[by_id[area_id]].value,
            "source_id": by_id[area_id][0],
            "record_id": by_id[area_id][1],
        }
        for area_id, answer in sorted(drafted.decided.items())
    ]


def written(drafted: Drafted) -> dict[str, bytes]:
    """Every file of the draft, by its name in the folder, as the bytes that are written."""
    by_key = drafted.by_key
    places = places_of(drafted)
    desk = desk_of(drafted)
    looks = [
        {
            "area_id": drafted.area_ids[look.key],
            "name": look.name,
            "tier": by_key[look.key].tier.value,
            "borough": drafted.borough_names.get(by_key[look.key].place.key.borough, ""),
            "mark": look.mark.value,
            "grave": "true" if look.grave else "false",
            "why": look.why,
            "source_id": look.source_id,
            "record_id": look.record_id,
        }
        for look in drafted.looks
    ]
    stations = [
        {
            "source_id": station.source_id,
            "record_id": station.record_id,
            "as_written": station.as_written,
            "easting": _whole(station.at[0]),
            "northing": _whole(station.at[1]),
            "oa21cd": station.cell,
            "lad22cd": station.borough,
        }
        for station in drafted.candidates.stations
    ]
    ids = [
        {"area_id": area_id, "source_id": key[0], "record_id": key[1], "field": key[2]}
        for key, area_id in sorted(drafted.area_ids.items(), key=lambda pair: pair[1])
    ]
    found = {
        "candidates.csv": table(CANDIDATES, candidates_of(drafted)),
        "places.csv": table(PLACES, places),
        "seeds.csv": table(SEEDS, [row for row in places if row["tier"] == Tier.AREA.value]),
        "name_records.csv": table(names_evidence.FULLER, [row.fuller() for row in drafted.rows]),
        "hard_look.csv": table(LOOKS, looks),
        "stations.csv": table(STATIONS, stations),
        "ids.csv": table(IDS, ids),
        "decided.csv": table(DECIDED, decided_of(drafted)),
        "counts.json": (json.dumps(counts_of(drafted), indent=1, sort_keys=True) + "\n").encode(),
    }
    for name, rows in desk.items():
        found[f"{DRAFT}/{name}"] = table(DESK[name], rows)
    found[f"{DRAFT}/seeds.csv"] = found["seeds.csv"]
    return found


def write(out: Path, drafted: Drafted) -> dict[str, object]:
    """Write the draft to a folder, and give its counts."""
    for name, content in written(drafted).items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return counts_of(drafted)


def read_ids(path: Path) -> dict[Key, str]:
    """The ids an earlier draft gave, from its `ids.csv`."""
    with path.open(encoding="utf-8", newline="") as file:
        return {
            (row["source_id"], row["record_id"], row["field"]): row["area_id"]
            for row in csv.DictReader(file)
        }


def places_with(drafted: Drafted, mark: Mark) -> list[Place]:
    """The places that carry one mark."""
    by_key = drafted.by_key
    keys = sorted({look.key for look in drafted.looks if look.mark is mark})
    return [by_key[key].place for key in keys]
