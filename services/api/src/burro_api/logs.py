"""Logging: one JSON line per event, holding only what is on the list.

Raw prompt text and destination strings are never written to a log (ADR 0005).
That is kept by construction and not by care: a line is built from an event
name and named fields, the names come from `LOGGABLE`, and no message is ever
formatted. What a library logs is cut down to where it came from, because its
message may repeat what it was given.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO, cast

LOGGER = "burro_api"

# Everything a log line may hold (contract, section 10.1). A field that is not
# here cannot be logged, so adding one is a reviewed change to this list.
LOGGABLE = frozenset(
    {
        "request_id",
        "method",
        # The route template, such as `/v1/shares/{share_id}`. Never the path.
        "route",
        "status",
        "latency_ms",
        "release_id",
        "engine_version",
        "synthetic",
        # Nothing worked out from a spec is on the list, and no hash of one of
        # any kind: a spec is a small space, and a hash of it can be matched
        # to a workplace by trying specs (ADR 0011).
        "endpoint",
        "interpreter",
        "model",
        "interpret_status",
        "call_status",
        "degraded",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        # How many edits in each group, and how many rejections for each reason.
        "edits",
        "rejections",
        "unmet",
        "assumptions",
        "error_code",
        "exception",
        "causes",
        "frames",
    }
)

Value = str | int | float | bool | tuple[str, ...] | dict[str, int]

_FIELDS = "burro_fields"
_MAX_FRAMES = 30

_log = logging.getLogger(LOGGER)


def _write(level: int, name: str, fields: dict[str, Value]) -> None:
    unlisted = sorted(set(fields) - LOGGABLE)
    if unlisted:
        # The names are ours, so they can be shown. The values are not.
        raise ValueError(f"not loggable: {', '.join(unlisted)}")
    _log.log(level, name, extra={_FIELDS: fields})


def event(name: str, **fields: Value) -> None:
    """Write one line. `name` is fixed text, and every field is on the list."""
    _write(logging.INFO, name, fields)


def _frames(error: BaseException) -> tuple[str, ...]:
    """Where it happened: file, line and function of each frame. Never a value.

    The traceback is walked by hand. The standard formatter would do, but it
    can be asked to print local variables, and this cannot.
    """
    found: list[str] = []
    step = error.__traceback__
    while step is not None:
        code = step.tb_frame.f_code
        file = Path(code.co_filename)
        found.append(f"{file.parent.name}/{file.name}:{step.tb_lineno}:{code.co_name}")
        step = step.tb_next
    # The innermost frames say the most.
    return tuple(found[-_MAX_FRAMES:])


def _causes(error: BaseException) -> tuple[str, ...]:
    """The types of what led to it. A type is code; a message may be what a person typed."""
    found: list[str] = []
    seen = {id(error)}
    cause = error.__cause__ or error.__context__
    while cause is not None and id(cause) not in seen and len(found) < _MAX_FRAMES:
        seen.add(id(cause))
        found.append(type(cause).__name__)
        cause = cause.__cause__ or cause.__context__
    return tuple(found)


def log_failure(error: BaseException, **fields: Value) -> None:
    """The only way an exception is logged: its type and its frames.

    It never calls `str(error)`, because an exception's message can repeat the
    input that caused it. This is also the one place to attach an error
    tracker, with request bodies off.
    """
    found: dict[str, Value] = {
        "exception": type(error).__name__,
        "causes": _causes(error),
        "frames": _frames(error),
    }
    # At the level of an error, so that whoever watches the log for errors sees it.
    _write(logging.ERROR, "failure", found | fields)


def _at(created: float) -> str:
    return datetime.fromtimestamp(created, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class JsonFormatter(logging.Formatter):
    """One JSON object per line. It never formats a message and never prints a traceback."""

    def format(self, record: logging.LogRecord) -> str:
        line: dict[str, object] = {"at": _at(record.created), "level": record.levelname.lower()}
        fields = getattr(record, _FIELDS, None)
        if record.name == LOGGER and isinstance(fields, dict):
            line["event"] = record.msg
            line.update(cast(dict[str, object], fields))
        else:
            # A library's record. Its message and arguments may hold anything
            # it was handed, so only where it came from is kept.
            line["event"] = "library"
            line["logger"] = record.name
            line["where"] = f"{record.module}:{record.lineno}:{record.funcName}"
            # Some libraries log the exception itself. Its type is code, and
            # the number the operating system gave is a number.
            error = record.exc_info[1] if record.exc_info else record.msg
            if isinstance(error, BaseException):
                line["exception"] = type(error).__name__
            if isinstance(error, OSError) and error.errno is not None:
                line["errno"] = error.errno
        return json.dumps(line, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class _OursOrWarning(logging.Filter):
    """Lets through our own lines, and a library's only from `WARNING` up.

    A filter on the handler, so it holds whatever level a library sets on its
    own logger. An SDK told to log at debug level writes request bodies.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == LOGGER or record.levelno >= logging.WARNING


def configure_logging(stream: TextIO | None = None) -> logging.Handler:
    """Replace every handler with one that writes JSON lines to standard output."""
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(_OursOrWarning())
    root = logging.getLogger()
    for old in list(root.handlers):
        root.removeHandler(old)
    root.addHandler(handler)
    root.setLevel(logging.WARNING)
    _log.setLevel(logging.INFO)
    return handler
