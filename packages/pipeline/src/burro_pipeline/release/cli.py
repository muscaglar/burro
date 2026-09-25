"""Command line for data releases: `burro-release build-synthetic|check`.

`build-synthetic` writes the made-up release, and with `--census-out` the
made-up count beside it, in a folder of its own. `check` with `--census` holds
the folder of a census to the release it was made for. `--income-out` and
`--income` do the same for the estimate of household income, which is shown on
an area's page as the census is and is no part of a release either.

`check` says whether a folder is a release that may be served. A made-up
release is held to every rule of the contract. A release that is not made up
is held to them too, and then to what it was built with, which stands in the
folder beside it: the hashes of the build must be as they were written, and
every fact the release would show must have a row of evidence behind it that
holds the same figure. It asks the licence registry again about every source,
and works each percentile and each tag out again with core's own code. Given
the folder of receipts that were committed, it holds the receipts in the
evidence to them.
"""

import argparse
import sys
from pathlib import Path

from burro_core.census import Census, CensusError
from burro_core.ids import GrittyVariant
from burro_core.income import Income, IncomeError
from burro_core.release import EVIDENCE, LOCK, InMemoryRelease, ReleaseError
from pydantic import ValidationError

from burro_pipeline.derive.measures import TAGGED, behind
from burro_pipeline.evidence.lock import LockError, read_lock, read_receipts
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER
from burro_pipeline.evidence.record import in_words as record_in_words
from burro_pipeline.evidence.served import Finding, counted, unevidenced
from burro_pipeline.evidence.store import Evidence
from burro_pipeline.registry import RegistryError, load
from burro_pipeline.release.income import UnreadableIncome, read_income, write_income
from burro_pipeline.release.income import in_words as income_in_words
from burro_pipeline.release.read import UnreadableRelease, beside, in_words, read_served
from burro_pipeline.release.residents import UnreadableCensus, read_census, write_census
from burro_pipeline.release.residents import in_words as census_in_words
from burro_pipeline.release.synthetic import (
    BUILT_AT,
    GRITTY,
    RELEASE_IDS,
    SEED,
    build_synthetic,
)
from burro_pipeline.release.synthetic.count import made_up_census
from burro_pipeline.release.synthetic.estimate import made_up_income
from burro_pipeline.release.write import write_release

EVIDENCED = ", with evidence behind every fact"


class Unevidenced(Exception):
    """A fact of a release has no evidence behind it. Says how many, by rule, and never which."""


def _summary(release: InMemoryRelease) -> str:
    """What a release holds, and what it says of itself: made up or real, and whether finished."""
    manifest, counts = release.manifest, release.manifest.counts
    return (
        f"{manifest.release_id}: {counts.neighbourhoods} areas ({counts.rankable} rankable), "
        f"{len(release.metrics)} measures, "
        f"{counts.destinations} destinations, {counts.places} places, {counts.stations} stations, "
        f"{'synthetic' if manifest.synthetic else 'real'}"
        f"{', a preview' if manifest.preview else ''}"
        f"{'' if manifest.synthetic else EVIDENCED}"
    )


def _census_summary(census: Census) -> str:
    """What a census holds. It gives no figure of any area."""
    return (
        f"{census.release_id}-residents: {len(census.tables)} tables, {len(census.areas)} areas, "
        f"{'made up' if census.synthetic else 'real'}"
    )


def _findings(
    release: InMemoryRelease, folder: Path, registry: Path | None, receipts: Path | None
) -> tuple[Finding, ...]:
    """Every fact of a release that is not made up and has no evidence behind it."""
    built = beside(folder)
    try:
        evidence = Evidence.model_validate_json((built / EVIDENCE).read_bytes())
    except ValidationError as error:
        raise Unevidenced(f"{EVIDENCE} is not valid evidence: {record_in_words(error)}") from None
    committed = None
    if receipts is not None:
        if not receipts.is_dir():
            raise Unevidenced(f"--receipts names no folder: {receipts.name}")
        committed = {receipt.file_id: receipt for receipt in read_receipts(receipts)}
    return unevidenced(
        release,
        evidence,
        read_lock(built / LOCK),
        load(registry),
        behind(),
        TAGGED.derivation_id,
        committed,
    )


def _income_summary(income: Income) -> str:
    """What the folder of income holds. It gives no figure of any area."""
    given = sum(area.estimate is not None for area in income.areas)
    return (
        f"{income.release_id}-income: {len(income.areas)} areas, {given} with an estimate, "
        f"{'made up' if income.synthetic else 'real'}"
    )


def _checked(folder: Path, registry: Path | None, receipts: Path | None) -> InMemoryRelease:
    """The release in a folder, if it may be served."""
    release = read_served(folder)
    if release.manifest.synthetic:
        return release
    findings = _findings(release, folder, registry, receipts)
    if findings:
        facts = "1 fact" if len(findings) == 1 else f"{len(findings)} facts"
        rules = ", ".join(f"{count} [{rule}]" for rule, count in counted(findings).items())
        to_do = "Run `python -m burro_pipeline check` with --list FILE to have each written down"
        raise Unevidenced(f"{facts} may not be served: {rules}. {to_do}")
    return release


def parser() -> argparse.ArgumentParser:
    """The command, as it takes its arguments. A test holds the workflows to it."""
    whole = argparse.ArgumentParser(prog="burro-release", description=__doc__)
    commands = whole.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-synthetic", help="write the synthetic release")
    build.add_argument(
        "--out", type=Path, required=True, help="where releases are kept; it gets its own folder"
    )
    build.add_argument("--seed", type=int, default=SEED)
    build.add_argument(
        "--gritty",
        choices=[variant.value for variant in GrittyVariant],
        default=GRITTY.value,
        help="which of the two ways gritty was built the release carries",
    )
    build.add_argument("--release-id", help="by default, the id kept for that way of gritty")
    build.add_argument(
        "--built-at", default=BUILT_AT, help="a timestamp, never read from the clock"
    )
    build.add_argument(
        "--census-out",
        type=Path,
        metavar="FOLDER",
        help="where the made-up count is kept; it gets a folder of its own, named for the "
        "release. It is never a folder of releases. Left out, no count is written",
    )
    build.add_argument(
        "--income-out",
        type=Path,
        metavar="FOLDER",
        help="where the made-up estimate of household income is kept; it gets a folder of its "
        "own, named for the release. It is never a folder of releases. Left out, none is "
        "written",
    )
    check = commands.add_parser(
        "check", help="fail if a folder is not a release that may be served"
    )
    check.add_argument("folder", type=Path)
    check.add_argument(
        "--registry",
        type=Path,
        help="the licence registry, a file or a folder (default: this repository's). It is "
        "not read for a made-up release",
    )
    check.add_argument(
        "--receipts",
        type=Path,
        metavar="FOLDER",
        help=f"the folder of receipts that were committed, as {RECEIPTS_FOLDER}. With it "
        "every receipt in the evidence is held to the one committed for its file. It is not "
        "read for a made-up release",
    )
    check.add_argument(
        "--census",
        type=Path,
        metavar="FOLDER",
        help="the folder of the census that was made for the release. With it the census is "
        "held to every rule of its own, and to the release",
    )
    check.add_argument(
        "--income",
        type=Path,
        metavar="FOLDER",
        help="the folder of household income that was made for the release. With it the "
        "figures are held to every rule of their own, and to the release",
    )
    return whole


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command != "check" and args.release_id is None:
        args.release_id = RELEASE_IDS[GrittyVariant(args.gritty)]

    census: Census | None = None
    income: Income | None = None
    try:
        if args.command == "check":
            release = _checked(args.folder, args.registry, args.receipts)
            if args.census is not None:
                census = read_census(args.census, release)
            if args.income is not None:
                income = read_income(args.income, release)
        else:
            built = build_synthetic(args.seed, args.release_id, args.built_at, args.gritty)
            release = write_release(built, args.out)
            if args.census_out is not None:
                census = write_census(made_up_census(release, args.seed), release, args.census_out)
            if args.income_out is not None:
                income = write_income(made_up_income(release, args.seed), release, args.income_out)
    except Unevidenced as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except (
        UnreadableRelease,
        UnreadableCensus,
        UnreadableIncome,
        LockError,
        RegistryError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except CensusError as error:
        print(f"error: {census_in_words(error, args.census_out or args.out)}", file=sys.stderr)
        return 2
    except IncomeError as error:
        print(f"error: {income_in_words(error, args.income_out or args.out)}", file=sys.stderr)
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
    if census is not None:
        print(_census_summary(census))
    if income is not None:
        print(_income_summary(income))
    return 0


if __name__ == "__main__":
    sys.exit(main())
