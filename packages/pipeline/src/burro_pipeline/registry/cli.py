"""Command line for the licence registry: `burro-registry check|list|attributions`."""

import argparse
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from burro_pipeline.registry.load import Registry, RegistryError, load
from burro_pipeline.registry.rules import Severity, check


def _check(registry: Registry, strict: bool) -> int:
    problems = check(registry, today=date.today())
    errors = [p for p in problems if p.severity is Severity.ERROR]
    warnings = [p for p in problems if p.severity is Severity.WARNING]
    for problem in errors + (warnings if strict else []):
        print(problem, file=sys.stderr)
    counts = Counter(source.status for source in registry)
    breakdown = ", ".join(f"{counts[status]} {status}" for status in sorted(counts))
    total = f"{len(registry.sources)} sources" + (f" ({breakdown})" if breakdown else "")
    failing = len(errors) + (len(warnings) if strict else 0)
    open_items = f"; {len(warnings)} to settle before launch (--strict lists them)"
    print(f"{total}; {failing} failing" + (open_items if warnings and not strict else ""))
    return 1 if failing else 0


def _list(registry: Registry) -> int:
    for source in sorted(registry, key=lambda s: (s.status, s.id)):
        print(f"{source.status:<9} {source.licence:<24} {source.id}")
    return 0


def _attributions(registry: Registry) -> int:
    for source, statement in registry.attributions():
        # What is said with the credit stands under it, as a page draws it.
        said = f"\n  {source.said_with_attribution}" if source.said_with_attribution else ""
        print(f"{source.name} ({source.publisher})\n  {statement}{said}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="burro-registry", description=__doc__)
    parser.add_argument(
        "--path", type=Path, help="registry file or folder (default: this repository's)"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check_parser = commands.add_parser("check", help="fail if any entry breaks a rule")
    check_parser.add_argument("--strict", action="store_true", help="warnings fail too")
    commands.add_parser("list", help="one line per source")
    commands.add_parser("attributions", help="statements the product must display")
    args = parser.parse_args(argv)

    try:
        registry = load(args.path, enforce=args.command == "attributions")
    except RegistryError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.command == "check":
        return _check(registry, args.strict)
    if args.command == "list":
        return _list(registry)
    return _attributions(registry)


if __name__ == "__main__":
    sys.exit(main())
