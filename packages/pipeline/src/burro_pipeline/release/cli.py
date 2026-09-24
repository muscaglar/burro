"""Command line for data releases: `burro-release build-synthetic|check`."""

import argparse
import sys
from pathlib import Path

from burro_core.release import InMemoryRelease, ReleaseError
from pydantic import ValidationError

from burro_pipeline.release.read import UnreadableRelease, in_words, read_release
from burro_pipeline.release.synthetic import BUILT_AT, RELEASE_ID, SEED, build_synthetic
from burro_pipeline.release.write import write_release


def _summary(release: InMemoryRelease) -> str:
    manifest, counts = release.manifest, release.manifest.counts
    return (
        f"{manifest.release_id}: {counts.neighbourhoods} areas ({counts.rankable} rankable), "
        f"{counts.destinations} destinations, {counts.places} places, {counts.stations} stations, "
        f"{'synthetic' if manifest.synthetic else 'real'}"
    )


def parser() -> argparse.ArgumentParser:
    """The command, as it takes its arguments. A test holds the workflows to it."""
    whole = argparse.ArgumentParser(prog="burro-release", description=__doc__)
    commands = whole.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-synthetic", help="write the synthetic release")
    build.add_argument(
        "--out", type=Path, required=True, help="where releases are kept; it gets its own folder"
    )
    build.add_argument("--seed", type=int, default=SEED)
    build.add_argument("--release-id", default=RELEASE_ID)
    build.add_argument(
        "--built-at", default=BUILT_AT, help="a timestamp, never read from the clock"
    )
    check = commands.add_parser("check", help="fail if a folder is not a valid release")
    check.add_argument("folder", type=Path)
    return whole


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)

    try:
        if args.command == "check":
            release = read_release(args.folder)
        else:
            built = build_synthetic(args.seed, args.release_id, args.built_at)
            release = write_release(built, args.out)
    except UnreadableRelease as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except ReleaseError as error:
        print(f"error: {in_words(error, args.out / args.release_id)}", file=sys.stderr)
        return 2
    except ValidationError:
        # A release id or a timestamp that is not in the form the contract gives.
        print(
            "error: --release-id or --built-at is not in the form a release needs", file=sys.stderr
        )
        return 2
    except OSError as error:
        print(f"error: cannot write to {args.out}: {error.strerror}", file=sys.stderr)
        return 2
    print(_summary(release))
    return 0


if __name__ == "__main__":
    sys.exit(main())
