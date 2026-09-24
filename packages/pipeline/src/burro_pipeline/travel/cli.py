"""The step of the command line that travel owns.

    python -m burro_pipeline travel --made-up --out FOLDER

What it prints may be read by anyone: one line of `key=value` pairs, the step,
its status, counts and hashes. Why it stopped is said in words on standard
error. Neither holds a stop, a place, an area or a time: a journey is between
an area and a place a person may name, so no pair is ever printed, and the
step is never told which place anyone asked for. It works out every pair.
"""

import argparse
import dataclasses
import hashlib
import io
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from burro_core.release import BEYOND_CUTOFF_CELL, MANIFEST, ReleaseError, TravelTable
from pydantic import ValidationError

from burro_pipeline.command import PROG, Step, add_step, may_be_written
from burro_pipeline.evidence.cli import public
from burro_pipeline.fetch.offline import sockets_refused
from burro_pipeline.release.synthetic.build import BUILT_AT, SEED, SOURCES
from burro_pipeline.release.write import write_release
from burro_pipeline.travel.engine import RoutingError, Settings
from burro_pipeline.travel.feed import Counted, FeedError, read_feed
from burro_pipeline.travel.made_up import RELEASE_ID, Town, town
from burro_pipeline.travel.plain import PlainRouter
from burro_pipeline.travel.roll_up import table_of
from burro_pipeline.travel.route import digest, join, route, same_twice, shard_of

STEP = "travel"
SHARDS = 4
# What is written here is made up, so it is never of a release of London.
MADE_UP_ID = re.compile(r"syn-\d{4}-\d{2}-\d{2}-\d{2}")
NOT_IGNORED = (
    "--out is inside the repository, where git would take in what the step writes. The "
    "release it writes is built on demand and never committed. Name a folder under "
    "data/releases/ or scratch/, or one outside the repository"
)

STEPS = (
    Step(
        STEP,
        "Work out the journeys of a release from a timetable and the streets",
        f"""\
Today it routes the made-up town alone, and says so: give it --made-up. The
town is the city of the synthetic release, written as a timetable in the open
format that transit feeds use, a grid of streets and three home points to an
area. It describes no real place.

What it does, in order. It reads the timetable and checks it as it reads:
every stop has a point, every trip has its times in order, and the calendar
covers the day that is modelled. It routes from every home point to every
place journeys end at, for every departure minute from 07:00 to 08:59, by
public transport, by bike and on foot. It does so in {SHARDS} shards and joins
them, and routes the first shard again to see that the same is found twice.
It takes the time that half of the departure minutes do at least as well as,
and the time that nine in ten do. It gives each area the time of its home
points, by the weighted lower median. It writes the release.

The router it uses is for tests. It is plain and slow, and routes no real
place. A real timetable is routed by an engine that needs Java and runs on a
hosted runner, which is not installed by this package: without --made-up the
step stops and says so. docs/design/london-data-travel.md says what the first
run of that engine must settle.

Reads nothing: no file, no store and no publisher. Reaches no network, and no
socket is open while it routes.

Writes a release to a folder of its own under the folder --out names. It is
made up, and is still never committed: --out is refused inside the
repository, but for data/releases/ and scratch/, which git ignores.

Prints one line of counts and hashes. `sha256` is of the fine matrices, from
every home point to every place, one byte a journey.""",
        ("--made-up --out scratch/releases",),
        {
            0: "The release was written",
            2: "The timetable may not be routed on, the engine is not installed, or the "
            "release could not be written. The line names the rule",
        },
    ),
)


class Refused(Exception):
    """The step could not start or could not write. Says why, and nothing of a journey."""


@dataclasses.dataclass(frozen=True)
class Journeys:
    """What the step worked out: the journeys as a release holds them, and what stands behind."""

    table: TravelTable
    # The hash of the fine matrices, from every home point to every place.
    fine: str
    # What the timetable held.
    counted: Counted


def journeys_of(made: Town, settings: Settings, shards: int = SHARDS) -> Journeys:
    """The journeys of the made-up town, from its timetable, its streets and its homes."""
    feed = read_feed(io.BytesIO(made.feed), made.day)
    engine = PlainRouter(feed, made.streets)
    origins = [home.point for home in made.homes]
    parts = [
        route(engine, shard_of(origins, shard, shards), made.destinations, settings)
        for shard in range(1, shards + 1)
    ]
    same_twice(engine, shard_of(origins, 1, shards), made.destinations, settings, parts[0])
    fine = join(parts)
    areas = [area.area_id for area in made.release.neighbourhoods]
    table = table_of(fine, made.homes, areas, settings, SOURCES, made.day.isoformat())
    return Journeys(table, digest(fine, settings), feed.counted)


def _beyond(table: TravelTable) -> int:
    matrices = (table.pt_typical, table.pt_just_missed, table.cycle, table.walk)
    return sum(cell == BEYOND_CUTOFF_CELL for matrix in matrices for row in matrix for cell in row)


def _travel(args: argparse.Namespace) -> int:
    if not args.made_up:
        raise RoutingError("engine_is_installed")
    out: Path = args.out
    # The step is run at the top of the repository.
    if not may_be_written(out, Path()):
        raise Refused(NOT_IGNORED)
    if not MADE_UP_ID.fullmatch(args.release_id):
        raise Refused("--release-id is not the id of a made-up release, as syn-2026-09-24-07")
    settings = Settings()
    try:
        made = town(args.seed, args.release_id, args.built_at)
    except ValidationError:
        raise Refused("--built-at is not a time in the form a release needs") from None
    with sockets_refused():
        found = journeys_of(made, settings)
    table, feed = found.table, found.counted
    written = write_release(dataclasses.replace(made.release, travel_table=table), out)
    manifest = (out / written.manifest.release_id / MANIFEST).read_bytes()
    print(
        public(
            STEP,
            "ok",
            release=written.manifest.release_id,
            stops=feed.stops,
            routes=feed.routes,
            trips=feed.trips,
            running=feed.running,
            calls=feed.calls,
            origins=len(made.homes),
            destinations=len(made.destinations),
            departures=settings.departures,
            shards=SHARDS,
            areas=len(table.area_ids),
            pairs=len(table.area_ids) * len(table.destination_ids),
            beyond=_beyond(table),
            sha256=found.fine,
            manifest_sha256=hashlib.sha256(manifest).hexdigest(),
        )
    )
    return 0


def build(prog: str = PROG) -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The step travel owns, as the command line takes it: the whole, and the step."""
    whole = argparse.ArgumentParser(
        prog=prog, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = whole.add_subparsers(dest="command", required=True)
    step = {step.name: add_step(commands, step, prog) for step in STEPS}
    travel = step[STEP]
    travel.add_argument(
        "--made-up",
        action="store_true",
        help="route the made-up town, with the router that is for tests. Without it the step "
        "stops: no engine for a real timetable is installed",
    )
    travel.add_argument(
        "--out",
        required=True,
        type=Path,
        metavar="FOLDER",
        help="where releases are kept. The release gets a folder of its own there",
    )
    travel.add_argument(
        "--release-id",
        default=RELEASE_ID,
        metavar="ID",
        help=f"the release that is written (default: {RELEASE_ID})",
    )
    travel.add_argument(
        "--built-at",
        default=BUILT_AT,
        metavar="TIME",
        help="when the release is said to be built. It is never read from the clock "
        f"(default: {BUILT_AT})",
    )
    travel.add_argument(
        "--seed",
        type=int,
        default=SEED,
        help=f"what the made-up town is drawn from (default: {SEED})",
    )
    return whole, step


def parsed(argv: Sequence[str] | None = None, prog: str = PROG) -> argparse.Namespace:
    """The arguments of the step. Stops with the step's usage if they are not ones it takes."""
    return build(prog)[0].parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parsed(argv)
    try:
        return _travel(args)
    except (FeedError, RoutingError) as error:
        print(public(STEP, "refused", **{error.rule: 1}))
        print(f"error: {error}", file=sys.stderr)
    except Refused as error:
        print(public(STEP, "refused"))
        print(f"error: {error}", file=sys.stderr)
    except ReleaseError as error:
        print(public(STEP, "refused"))
        print(f"error: the release is not one that may be written [{error.rule}]", file=sys.stderr)
    except OSError as error:
        print(public(STEP, "unreadable"))
        print(f"error: cannot write a file: {error.strerror}", file=sys.stderr)
    return 2
