"""What moved between two builds: what differs between two releases, each with its evidence.

A person approves a fresh build by committing its lock. Before they do, this says what
the build changed of what is served: the areas, measures and vibes that came or went,
how far the figures of each measure moved, how many areas changed band on each vibe,
which publishers' files behind the build are other files than before, and the first ten
areas of a few searches, before and after.

Each release is read as it is served, through `read_served`, so that what is compared is
what a person would be shown. Every band and every rank is core's own. Nothing is worked
out again but the difference.

What is found names areas, by the id and the name each bears in its release. So it is
written only to a folder a person names, and is never printed: what a step prints is
counts. It reads files and changes none.
"""

import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from burro_core.ids import FeatureId, TagId
from burro_core.release import LOCK, InMemoryRelease, Neighbourhood
from pydantic import ValidationError

from burro_pipeline.evidence import InputKind, Lock, LockedInput, Receipt
from burro_pipeline.fetch.cli import paired
from burro_pipeline.fetch.sources import FetchList
from burro_pipeline.release.read import beside, read_served
from burro_pipeline.upkeep import searches as ranked
from burro_pipeline.upkeep.searches import Search

# How many areas are listed as those that moved most.
MOST = 10


class NoLock(Exception):
    """A release that is not made up has no lock beside it that can be read."""


class OtherCity(Exception):
    """The two releases are not of one city, so nothing of one is an area of the other."""


@dataclass(frozen=True)
class Build:
    """A release as it is served, with the lock of its build. A made-up release has none."""

    release: InMemoryRelease
    lock: Lock | None

    @property
    def id(self) -> str:
        return self.release.manifest.release_id


def with_its_lock(release: InMemoryRelease, folder: Path) -> Build:
    """A release that was read from a folder as it is served, with the lock beside it.
    Raises `NoLock`."""
    if release.manifest.synthetic:
        return Build(release, None)
    try:
        return Build(release, Lock.model_validate_json((beside(folder) / LOCK).read_bytes()))
    except (OSError, ValidationError):
        raise NoLock from None


def open_build(folder: Path) -> Build:
    """The release in a folder, as it is served, and the lock beside it.

    Raises `ReleaseError` for a release that would not be served, and `NoLock`.
    """
    return with_its_lock(read_served(folder), folder)


def _apart(was: float, now: float) -> float:
    """How far two figures stand apart, as a person who subtracts by hand finds it."""
    return float(abs(Decimal(repr(now)) - Decimal(repr(was))))


def _place(area: Neighbourhood) -> dict[str, str]:
    return {"id": area.area_id, "name": area.name, "borough": area.borough}


@dataclass(frozen=True)
class _Pair:
    """Two builds, and the areas both hold, in the order of their ids."""

    before: InMemoryRelease
    after: InMemoryRelease

    @property
    def both(self) -> list[Neighbourhood]:
        held = {area.area_id for area in self.before.neighbourhoods}
        found = [area for area in self.after.neighbourhoods if area.area_id in held]
        return sorted(found, key=lambda area: area.area_id)


def _came_and_went(
    before: Mapping[str, dict[str, Any]], after: Mapping[str, dict[str, Any]]
) -> dict[str, Any]:
    return {
        "same": len(before.keys() & after.keys()),
        "came": [after[key] for key in sorted(after.keys() - before.keys())],
        "went": [before[key] for key in sorted(before.keys() - after.keys())],
    }


def _areas(pair: _Pair) -> dict[str, Any]:
    """The areas that came or went, and those that bear another name or another outline."""
    was = {area.area_id: area for area in pair.before.neighbourhoods}
    found = _came_and_went(
        {key: _place(area) for key, area in was.items()},
        {area.area_id: _place(area) for area in pair.after.neighbourhoods},
    )
    renamed = [
        {**_place(area), "was": was[area.area_id].name, "was_in": was[area.area_id].borough}
        for area in pair.both
        if (area.name, area.borough) != (was[area.area_id].name, was[area.area_id].borough)
    ]
    redrawn = [
        _place(area)
        for area in pair.both
        if pair.before.geometry(area.area_id) != pair.after.geometry(area.area_id)
    ]
    return {**found, "renamed": renamed, "redrawn": redrawn}


def _steps(
    areas: Sequence[Neighbourhood],
    was: Callable[[str], float | None],
    now: Callable[[str], float | None],
) -> dict[str, Any]:
    """How the figures of the areas of two builds differ: how many changed, which way, by
    how much in the middle and at most, and how many gained or lost a figure."""
    apart: list[tuple[float, str, float, float]] = []
    gained = lost = up = 0
    for area in areas:
        old, new = was(area.area_id), now(area.area_id)
        if old is None or new is None:
            gained += old is None and new is not None
            lost += old is not None and new is None
        elif old != new:
            apart.append((_apart(old, new), area.area_id, old, new))
            up += new > old
    named = {area.area_id: area for area in areas}
    most = sorted(apart, key=lambda one: (-one[0], one[1]))[:MOST]
    return {
        "areas": len(areas),
        "changed": len(apart),
        "up": up,
        "down": len(apart) - up,
        "gained": gained,
        "lost": lost,
        "middle": statistics.median_low([one[0] for one in apart]) if apart else None,
        "most": max(one[0] for one in apart) if apart else None,
        "moved_most": [
            {**_place(named[area_id]), "was": old, "now": new, "by": by}
            for by, area_id, old, new in most
        ],
    }


def _has_moved(found: Mapping[str, Any]) -> bool:
    return bool(found["changed"] or found["gained"] or found["lost"])


def _measures(pair: _Pair) -> dict[str, Any]:
    """The measures that came or went, and of each that both carry, how its figures moved."""
    was = {metric.feature_id: metric for metric in pair.before.metrics}
    now = {metric.feature_id: metric for metric in pair.after.metrics}

    def said(of: Mapping[FeatureId, Any], release: InMemoryRelease) -> dict[str, dict[str, Any]]:
        figures: dict[FeatureId, int] = {}
        for row in release.features:
            figures[row.feature_id] = figures.get(row.feature_id, 0) + (row.value is not None)
        return {
            key.value: {
                "id": key.value,
                "label": one.label,
                "unit": one.unit,
                # How many areas of the release have a figure of it.
                "with_a_figure": figures.get(key, 0),
            }
            for key, one in of.items()
        }

    def value_in(release: InMemoryRelease, feature_id: FeatureId) -> Callable[[str], float | None]:
        def of(area_id: str) -> float | None:
            row = release.feature(area_id, feature_id)
            return None if row is None else row.value

        return of

    moved: list[dict[str, Any]] = []
    for feature_id in sorted(was.keys() & now.keys(), key=lambda key: key.value):
        steps = _steps(
            pair.both, value_in(pair.before, feature_id), value_in(pair.after, feature_id)
        )
        dated = (was[feature_id].vintage, now[feature_id].vintage)
        if _has_moved(steps) or dated[0] != dated[1]:
            about = {
                "id": feature_id.value,
                "label": now[feature_id].label,
                "unit": now[feature_id].unit,
                "dated": {"was": dated[0], "now": dated[1]},
            }
            moved.append(about | steps)
    carried = _came_and_went(said(was, pair.before), said(now, pair.after))
    return {**carried, "moved": moved}


def _costs(pair: _Pair) -> list[dict[str, Any]]:
    """What a home of each kind sells for, where it moved: the median of each area."""
    kinds = sorted(
        {(cost.tenure, cost.segment) for cost in (*pair.before.costs, *pair.after.costs)}
    )

    moved: list[dict[str, Any]] = []
    for tenure, segment in kinds:

        def value_in(
            release: InMemoryRelease, tenure: Any = tenure, segment: Any = segment
        ) -> Callable[[str], float | None]:
            def of(area_id: str) -> float | None:
                cost = release.cost(area_id, tenure, segment)
                return None if cost is None else float(cost.median)

            return of

        steps = _steps(pair.both, value_in(pair.before), value_in(pair.after))
        if _has_moved(steps):
            moved.append({"tenure": tenure.value, "segment": segment.value, "unit": "£"} | steps)
    return moved


def _vibes(pair: _Pair) -> dict[str, Any]:
    """The vibes that came or went, and of each that both carry, how many areas changed
    band and by how many bands. An area is said by its band, never by its score."""
    was = {vibe.tag_id: vibe for vibe in pair.before.vibes}
    now = {vibe.tag_id: vibe for vibe in pair.after.vibes}

    def said(of: Mapping[TagId, Any]) -> dict[str, dict[str, Any]]:
        return {key.value: {"id": key.value, "label": one.label} for key, one in of.items()}

    moved: list[dict[str, Any]] = []
    for tag_id in sorted(was.keys() & now.keys(), key=lambda key: key.value):
        by: dict[int, int] = {}
        gained = lost = 0
        apart: list[tuple[int, str, int, int]] = []
        for area in pair.both:
            old, new = pair.before.tag(area.area_id, tag_id), pair.after.tag(area.area_id, tag_id)
            before = None if old is None else old.band
            after = None if new is None else new.band
            if before is None or after is None:
                gained += before is None and after is not None
                lost += before is not None and after is None
            elif before != after:
                by[after - before] = by.get(after - before, 0) + 1
                apart.append((abs(after - before), area.area_id, before, after))
        recipe = was[tag_id] != now[tag_id]
        if not (by or gained or lost or recipe):
            continue
        named = {area.area_id: area for area in pair.both}
        moved.append(
            {
                "id": tag_id.value,
                "label": now[tag_id].label,
                "areas": len(pair.both),
                "changed": sum(by.values()),
                "up": sum(count for step, count in by.items() if step > 0),
                "down": sum(count for step, count in by.items() if step < 0),
                "gained": gained,
                "lost": lost,
                "by_bands": [{"by": step, "areas": by[step]} for step in sorted(by)],
                # Whether the release carries another recipe, name or line of the vibe.
                "recipe_changed": recipe,
                "moved_most": [
                    {**_place(named[area_id]), "was": old, "now": new}
                    for _, area_id, old, new in sorted(apart, key=lambda one: (-one[0], one[1]))[
                        :MOST
                    ]
                ],
            }
        )
    return {**_came_and_went(said(was), said(now)), "moved": moved}


# The files behind a build

Known = tuple[Receipt | None, str | None, str | None]


def _named(lock: Lock | None, of: Mapping[str, Known]) -> dict[str, dict[str, Any]]:
    """Every input of a lock, by what tells it from the other inputs: for a publisher's
    file its source, its list and its item, and for anything else its name."""
    found: dict[str, dict[str, Any]] = {}
    for locked in () if lock is None else lock.inputs:
        if locked.kind is not InputKind.PUBLISHER_FILE:
            found[f"{locked.kind}:{locked.name}"] = {"name": locked.name, "sha256": locked.sha256}
            continue
        found[_key(locked, of)] = _file(locked, _known(locked, of))
    return found


def _known(locked: LockedInput, of: Mapping[str, Known]) -> Known:
    """The receipt of an input, and the list and the item it is of, where they are known."""
    return of.get(locked.name, (None, None, locked.item))


def _key(locked: LockedInput, of: Mapping[str, Known]) -> str:
    _, build, item = _known(locked, of)
    # A file that no list is known to name is known by itself alone.
    return f"{locked.source_id}:{build or ''}:{item or locked.name}"


def _file(locked: LockedInput, known: Known) -> dict[str, Any]:
    receipt, build, item = known
    period = None if receipt is None else receipt.data_period
    return {
        "source": locked.source_id,
        "list": build,
        "item": item,
        "file_id": locked.name,
        "sha256": locked.sha256,
        "edition": locked.edition if receipt is None else receipt.edition,
        "period": None if period is None else period.as_at or f"{period.start} to {period.end}",
        "retrieved_on": None if receipt is None else receipt.retrieved_on,
    }


def _files(
    before: Lock | None,
    after: Lock | None,
    receipts: Sequence[Receipt],
    lists: Sequence[FetchList],
) -> dict[str, Any]:
    """The inputs of two builds that differ, from their locks. A receipt says which file of
    which list an input is, and which edition: with none, a file is known by its id."""
    of: dict[str, Known] = {}
    for receipt, named in zip(receipts, paired(receipts, lists), strict=True):
        build = min(named) if named else None
        of[receipt.file_id] = (receipt, build, named[build] if build is not None else None)
    was, now = _named(before, of), _named(after, of)
    changed = [
        {"was": was[key], "now": now[key]}
        for key in sorted(was.keys() & now.keys())
        if was[key]["sha256"] != now[key]["sha256"]
    ]
    return {
        "compared": before is not None and after is not None,
        "same": len(was.keys() & now.keys()) - len(changed),
        "changed": changed,
        "came": [now[key] for key in sorted(now.keys() - was.keys())],
        "went": [was[key] for key in sorted(was.keys() - now.keys())],
    }


# The areas that moved most, of all


def _moved_most(pair: _Pair, vibes: Mapping[str, Any], measures: Mapping[str, Any]) -> list[Any]:
    """The areas whose bands changed most between the builds: by how many bands in all,
    then by how many vibes, then by how many of their figures changed."""
    bands: dict[str, list[int]] = {}
    for tag_id in (TagId(one["id"]) for one in vibes["moved"]):
        for area in pair.both:
            old, new = pair.before.tag(area.area_id, tag_id), pair.after.tag(area.area_id, tag_id)
            before = None if old is None else old.band
            after = None if new is None else new.band
            if before != after:
                step = 1 if before is None or after is None else abs(after - before)
                bands.setdefault(area.area_id, []).append(step)
    figures: dict[str, int] = {}
    for feature_id in (FeatureId(one["id"]) for one in measures["moved"]):
        for area in pair.both:
            old = pair.before.feature(area.area_id, feature_id)
            new = pair.after.feature(area.area_id, feature_id)
            if (None if old is None else old.value) != (None if new is None else new.value):
                figures[area.area_id] = figures.get(area.area_id, 0) + 1
    counted = sorted(
        (
            -sum(bands.get(area.area_id, [])),
            -len(bands.get(area.area_id, [])),
            -figures.get(area.area_id, 0),
            area.area_id,
        )
        for area in pair.both
        if area.area_id in bands or area.area_id in figures
    )
    named = {area.area_id: area for area in pair.both}
    return [
        {**_place(named[area_id]), "bands": -steps, "vibes": -many, "figures": -changed}
        for steps, many, changed, area_id in counted[:MOST]
    ]


def _searched(pair: _Pair, searches: Sequence[Search]) -> list[dict[str, Any]]:
    """The first ten areas of each search, before and after, and how the two differ."""
    found = ranked.searched(searches, pair.before, pair.after)
    for one in found:
        was = [area["id"] for area in one["before"]["first"]]
        now = [area["id"] for area in one["after"]["first"]]
        kept = [area for area in now if area in was]
        one["kept"] = len(kept)
        one["came"] = len(now) - len(kept)
        one["went"] = len(was) - len(kept)
        # Of the areas that stayed among the first ten, how many stand at another place.
        one["reordered"] = sum(was.index(area) != now.index(area) for area in kept)
    return found


def _said(build: Build) -> dict[str, Any]:
    manifest, lock = build.release.manifest, build.lock
    return {
        "release_id": manifest.release_id,
        "built_at": manifest.built_at,
        "commit": None if lock is None else lock.commit,
        "synthetic": manifest.synthetic,
        "preview": manifest.preview,
        "catalogue_version": manifest.catalogue_version,
        "areas": len(build.release.neighbourhoods),
        "measures": len(build.release.metrics),
        "vibes": len(build.release.vibes),
    }


def compare(
    before: Build,
    after: Build,
    *,
    receipts: Sequence[Receipt] = (),
    lists: Sequence[FetchList] = (),
    searches: Sequence[Search] = (),
) -> dict[str, Any]:
    """What differs between two builds, as plain values that may be written as JSON.
    Raises `OtherCity` where the two are not of one city: the made-up city and a real one
    are never held against each other."""
    if before.release.manifest.city is not after.release.manifest.city:
        raise OtherCity
    pair = _Pair(before.release, after.release)
    measures, vibes = _measures(pair), _vibes(pair)
    return {
        "before": _said(before),
        "after": _said(after),
        "areas": _areas(pair) | {"moved_most": _moved_most(pair, vibes, measures)},
        "measures": measures,
        "vibes": vibes,
        "costs": _costs(pair),
        "files": _files(before.lock, after.lock, receipts, lists),
        "searches": _searched(pair, searches),
    }


def counted(found: Mapping[str, Any]) -> dict[str, int]:
    """What moved, in counts: what the step prints of the whole."""
    areas, measures, vibes, files = (found[key] for key in ("areas", "measures", "vibes", "files"))
    return {
        "areas": found["after"]["areas"],
        "areas_came": len(areas["came"]),
        "areas_went": len(areas["went"]),
        "areas_renamed": len(areas["renamed"]),
        "areas_redrawn": len(areas["redrawn"]),
        "measures": found["after"]["measures"],
        "measures_came": len(measures["came"]),
        "measures_went": len(measures["went"]),
        "measures_moved": len(measures["moved"]),
        "vibes": found["after"]["vibes"],
        "vibes_came": len(vibes["came"]),
        "vibes_went": len(vibes["went"]),
        "vibes_moved": len(vibes["moved"]),
        "costs_moved": len(found["costs"]),
        "files_changed": len(files["changed"]),
        "files_came": len(files["came"]),
        "files_went": len(files["went"]),
        "searches": len(found["searches"]),
        "searches_moved": sum(not one["same"] for one in found["searches"]),
    }


def _by_source(files: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    found: dict[str, dict[str, int]] = {}
    each: Iterable[tuple[str, Any]] = (
        *(("changed", one["now"]) for one in files["changed"]),
        *(("came", one) for one in files["came"]),
        *(("went", one) for one in files["went"]),
    )
    for how, one in each:
        source = one.get("source")
        if source is not None:
            counts = found.setdefault(source, {"changed": 0, "came": 0, "went": 0})
            counts[how] += 1
    return found


def lines(found: Mapping[str, Any]) -> list[str]:
    """What the step prints: a line for each measure, vibe, source and search that moved,
    and one for the whole. Each holds ids of the catalogue and the registry, and counts."""
    said: list[str] = []
    measures, vibes = found["measures"], found["vibes"]
    for how in ("came", "went"):
        said += [f"step=moved feature={one['id']} {how}=1" for one in measures[how]]
    for one in measures["moved"]:
        counts = " ".join(f"{key}={one[key]}" for key in ("areas", "changed", "gained", "lost"))
        said.append(f"step=moved feature={one['id']} {counts}")
    for how in ("came", "went"):
        said += [f"step=moved vibe={one['id']} {how}=1" for one in vibes[how]]
    for one in vibes["moved"]:
        counts = " ".join(
            f"{key}={one[key]}" for key in ("areas", "changed", "up", "down", "gained", "lost")
        )
        said.append(f"step=moved vibe={one['id']} {counts}")
    for source, counts in sorted(_by_source(found["files"]).items()):
        said.append(
            f"step=moved source={source} " + " ".join(f"{k}={v}" for k, v in counts.items())
        )
    for number, one in enumerate(found["searches"], start=1):
        counts = " ".join(f"{key}={one[key]}" for key in ("kept", "came", "went", "reordered"))
        said.append(f"step=moved search={number} {counts}")
    whole = " ".join(f"{key}={count}" for key, count in counted(found).items())
    said.append(
        f"step=moved status=ok before={found['before']['release_id']} "
        f"after={found['after']['release_id']} {whole}"
    )
    return said
