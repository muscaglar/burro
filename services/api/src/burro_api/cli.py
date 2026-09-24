"""Command line for the API: `burro-api serve|openapi`."""

import argparse
import json
import os
import sys
from pathlib import Path

import uvicorn
from burro_core.release import ReleaseError
from fastapi import FastAPI
from pydantic import ValidationError

from burro_api import logs
from burro_api.app import create_app, deps_from
from burro_api.settings import Settings


def openapi_document(app: FastAPI) -> str:
    """The OpenAPI document as it is committed: sorted, indented, one trailing newline."""
    return json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _refusal(folder: Path, error: ReleaseError) -> str:
    """Why a release was refused, in one line: the folder, the file, the row and the rule.

    Never a value from a file. `burro-release check` says the same in more words.
    """
    where = ", at ".join(part for part in (error.file, error.row) if part)
    return f"{folder}: {where} [{error.rule}]" if where else f"{folder} [{error.rule}]"


def _serve(settings: Settings) -> int:
    logs.configure_logging()
    deps = deps_from(settings)
    manifest = deps.release.manifest
    logs.event(
        "starting",
        release_id=manifest.release_id,
        synthetic=manifest.synthetic,
        interpreter=deps.interpreter.name.value,
        model=deps.model_id,
    )
    try:
        uvicorn.run(
            create_app(deps),
            host=settings.host,
            port=settings.port,
            # The server's own access log writes the path, and a path can hold
            # a share id. The app writes its own line, from the route template.
            access_log=False,
            # Logging is already set up, as JSON. The server must not set it up again.
            log_config=None,
            log_level="warning",
            server_header=False,
        )
    except SystemExit:
        # How the server says it could not start. The log line before this one
        # holds the type of the error and its number.
        print(f"error: could not listen on {settings.host}:{settings.port}", file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="burro-api", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="run the service; settings come from the environment")
    export = commands.add_parser("openapi", help="write the OpenAPI document")
    export.add_argument("--out", type=Path, required=True, help="the file to write")
    args = parser.parse_args(argv)

    folder = Path()
    try:
        serving = args.command == "serve"
        # The OpenAPI document does not depend on the release, so it is written
        # from the fixture, whatever the environment says.
        settings = Settings.from_env(os.environ if serving else {})
        folder = settings.release_dir
        if serving:
            return _serve(settings)
        document = openapi_document(create_app(deps_from(settings)))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(document, encoding="utf-8")
        print(f"wrote {args.out}")
    except ValidationError:
        print("error: a setting in the environment is not in the form it needs", file=sys.stderr)
        return 2
    except ReleaseError as error:
        print(f"error: the release could not be loaded: {_refusal(folder, error)}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"error: {error.strerror}", file=sys.stderr)
        return 2
    return 0
