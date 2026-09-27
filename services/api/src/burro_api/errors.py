"""Errors: one envelope, fixed messages, and handlers that never echo what was sent.

A validation error is the likeliest place for a prompt to leak: pydantic's
`input`, `ctx` and `msg` can each repeat the value that failed. So an error
response is built from where the problem is and what kind it is, and from
nothing else. Even a field name is kept only if it is one of ours, because the
name of a field that should not be there is itself something the sender wrote.
"""

from collections.abc import Iterator, Mapping, Sequence
from typing import cast

from burro_core.ids import SpecProblemKind
from burro_core.spec import SpecProblem
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from burro_api.accounts.wire import BODIES as OF_ACCOUNTS
from burro_api.wire import (
    BODIES,
    ErrorBody,
    ErrorCode,
    ErrorEnvelope,
    FieldProblem,
    Meta,
    Problem,
)

STATUS: Mapping[ErrorCode, int] = {
    ErrorCode.MALFORMED_JSON: 400,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.AREA_NOT_FOUND: 404,
    ErrorCode.SHARE_NOT_FOUND: 404,
    ErrorCode.CENSUS_NOT_AVAILABLE: 404,
    ErrorCode.INCOME_NOT_AVAILABLE: 404,
    ErrorCode.METHOD_NOT_ALLOWED: 405,
    ErrorCode.RELEASE_CHANGED: 410,
    ErrorCode.BODY_TOO_LARGE: 413,
    ErrorCode.UNSUPPORTED_MEDIA_TYPE: 415,
    ErrorCode.INTERNAL_ERROR: 500,
    # The routes of accounts.
    ErrorCode.NOT_SIGNED_IN: 401,
    ErrorCode.NOT_THE_WEBSITE: 403,
    ErrorCode.SIGN_IN_AGAIN: 403,
    ErrorCode.SEARCH_NOT_FOUND: 404,
    ErrorCode.SESSION_NOT_FOUND: 404,
    ErrorCode.OTHER_BROWSER: 409,
    ErrorCode.AGE_NOT_CONFIRMED: 409,
    ErrorCode.TOO_MANY_SEARCHES: 409,
    ErrorCode.LINK_EXPIRED: 410,
    ErrorCode.LINK_USED: 410,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.SIGN_IN_BUSY: 429,
    ErrorCode.SIGN_IN_UNAVAILABLE: 503,
}
UNPROCESSABLE = 422

# The same words for every request. Nothing here is built from what was sent.
#
# A person reads a message where a page or an answer should stand. So what a person
# can meet says what Burro could not do, and what to try where there is something to
# try, and names no spec, route, release or contract. What only a caller that is
# written wrongly can meet says what is wrong with what it sent: the first three, and
# the method. `fields` says where, for whoever writes the caller.
MESSAGES: Mapping[ErrorCode, str] = {
    ErrorCode.MALFORMED_JSON: "The body is not valid JSON.",
    ErrorCode.BODY_TOO_LARGE: "The body is larger than 16 KiB.",
    ErrorCode.UNSUPPORTED_MEDIA_TYPE: "The body must be sent as application/json.",
    ErrorCode.INTERNAL_ERROR: "Something went wrong on the server.",
    ErrorCode.NOT_FOUND: "Burro has nothing at this address.",
    ErrorCode.METHOD_NOT_ALLOWED: "The route does not take this method.",
    ErrorCode.INVALID_REQUEST: (
        "Burro could not read what the page sent, so try loading the page again."
    ),
    ErrorCode.INVALID_TEXT: "The text must be 1 to 600 characters.",
    ErrorCode.INVALID_SPEC: "Burro could not read this search, so try starting it again.",
    ErrorCode.INVALID_OPERATIONS: "Burro could not make that change to your search.",
    ErrorCode.INVALID_COMPARE: "A comparison takes 2 to 4 different areas.",
    ErrorCode.INVALID_QUERY: "The search text must be 2 to 80 characters.",
    ErrorCode.UNKNOWN_PLACE: "This search names a place that Burro does not have.",
    ErrorCode.UNKNOWN_AREA: "This search names an area that Burro does not have.",
    ErrorCode.AREA_NOT_FOUND: "Burro has no area by that name.",
    ErrorCode.SHARE_NOT_FOUND: "There is no such shared search.",
    ErrorCode.RELEASE_CHANGED: "The data has changed and this shared search cannot be shown.",
    ErrorCode.CENSUS_NOT_AVAILABLE: "Burro has no census figures to show at the moment.",
    ErrorCode.INCOME_NOT_AVAILABLE: (
        "Burro has no figure for household income to show at the moment."
    ),
    # The routes of accounts. The first is met only by a caller that is not the website.
    ErrorCode.NOT_THE_WEBSITE: "Burro only answers this when its own website asks.",
    ErrorCode.NOT_SIGNED_IN: "You are not signed in, so please sign in and try again.",
    ErrorCode.SIGN_IN_AGAIN: (
        "Please sign in again before you delete your account. Burro asks for this so that "
        "nobody else can delete it from a browser you left signed in."
    ),
    ErrorCode.RATE_LIMITED: (
        "Burro has been asked to sign in too many times from here, so please wait a "
        "quarter of an hour and then try again."
    ),
    ErrorCode.SIGN_IN_BUSY: (
        "Burro has sent as many sign-in emails as it may for now, so please try again in an hour."
    ),
    ErrorCode.SIGN_IN_UNAVAILABLE: (
        "Burro cannot send sign-in emails at the moment, so please try again later."
    ),
    ErrorCode.INVALID_EMAIL: (
        "That does not look like an email address, so please check it and try again."
    ),
    ErrorCode.LINK_NOT_VALID: (
        "Burro does not recognise this sign-in link. It may be incomplete, so please ask "
        "for a new one."
    ),
    ErrorCode.LINK_EXPIRED: (
        "This sign-in link has run out, because a link only works for 15 minutes. Please "
        "ask for a new one."
    ),
    ErrorCode.LINK_USED: (
        "This sign-in link no longer works, because it has been used or a newer one has. "
        "Each link works once, so please ask for a new one."
    ),
    ErrorCode.OTHER_BROWSER: (
        "This link was asked for in a different browser, so Burro needs you to confirm "
        "that you want to sign in here."
    ),
    ErrorCode.AGE_NOT_CONFIRMED: (
        "Burro can only make an account for you once you have confirmed that you are 18 or over."
    ),
    ErrorCode.TOO_MANY_SEARCHES: (
        "You have saved 100 searches, which is the most Burro holds for one account. Remove "
        "one and you can save this one."
    ),
    ErrorCode.SEARCH_NOT_FOUND: "Burro could not find that search among the ones you have saved.",
    ErrorCode.SESSION_NOT_FOUND: "Burro could not find that sign-in, so it may have ended already.",
}

# Which part of the body an error is about decides the code.
_CODE_FOR_FIELD: Mapping[str, ErrorCode] = {
    "text": ErrorCode.INVALID_TEXT,
    "spec": ErrorCode.INVALID_SPEC,
    "operations": ErrorCode.INVALID_OPERATIONS,
    "area_ids": ErrorCode.INVALID_COMPARE,
    "q": ErrorCode.INVALID_QUERY,
    "email": ErrorCode.INVALID_EMAIL,
}

# pydantic's error types, which are its own words and never the sender's.
_PROBLEM_FOR_TYPE: Mapping[str, Problem] = {
    "missing": Problem.MISSING,
    "extra_forbidden": Problem.UNKNOWN_FIELD,
    "enum": Problem.NOT_ALLOWED,
    "literal_error": Problem.NOT_ALLOWED,
    "string_pattern_mismatch": Problem.BAD_FORMAT,
    "greater_than": Problem.OUT_OF_RANGE,
    "greater_than_equal": Problem.OUT_OF_RANGE,
    "less_than": Problem.OUT_OF_RANGE,
    "less_than_equal": Problem.OUT_OF_RANGE,
    "too_long": Problem.OUT_OF_RANGE,
    "too_short": Problem.OUT_OF_RANGE,
    "string_too_long": Problem.OUT_OF_RANGE,
    "string_too_short": Problem.OUT_OF_RANGE,
    "finite_number": Problem.OUT_OF_RANGE,
}
_JSON_INVALID = "json_invalid"
_PATH_PARAMETERS = frozenset({"id_or_slug", "share_id"})


class ApiError(Exception):
    """A refusal a route chose. Holds a code and paths, never a value."""

    def __init__(self, code: ErrorCode, fields: tuple[FieldProblem, ...] = ()) -> None:
        self.code = code
        self.fields = fields
        super().__init__(code.value)


def _property_names(schema: object) -> Iterator[str]:
    if isinstance(schema, dict):
        document = cast(dict[str, object], schema)
        properties = document.get("properties")
        if isinstance(properties, dict):
            yield from cast(dict[str, object], properties)
        for value in document.values():
            yield from _property_names(value)
    elif isinstance(schema, list):
        for item in cast(list[object], schema):
            yield from _property_names(item)


def _names_of(bodies: Sequence[type[BaseModel]]) -> frozenset[str]:
    """Every field name that some requests may hold, read from the request bodies themselves."""
    names = set(_PATH_PARAMETERS)
    for body in bodies:
        names.update(_property_names(body.model_json_schema()))
    return frozenset(names)


# What a request of the search may hold, and what a request of accounts may. A route of
# the search is asked by anybody, with accounts on or off, and the name of a field of
# accounts is to it what any other name is that the sender wrote.
KNOWN_NAMES = _names_of(BODIES)
KNOWN_TO_ACCOUNTS = KNOWN_NAMES | _names_of(OF_ACCOUNTS)


def path_of(loc: Sequence[object], names: frozenset[str] = KNOWN_NAMES) -> str:
    """`("body", "spec", "commutes", 0, "max_minutes")` as `spec.commutes[0].max_minutes`.

    The first part says where the value was and is dropped. A part that is not
    a position or one of our field names is dropped too: it is a key the
    sender chose, or the name pydantic gives to a branch of a union. `names`
    are the field names of the routes the request was for.
    """
    path = ""
    for part in loc[1:]:
        if isinstance(part, int) and not isinstance(part, bool):
            path += f"[{part}]"
        elif isinstance(part, str) and part in names:
            path += f".{part}" if path else part
    return path


def _problem_for(kind: str) -> Problem:
    if kind in _PROBLEM_FOR_TYPE:
        return _PROBLEM_FOR_TYPE[kind]
    wrong_type = kind.endswith(("_type", "_parsing")) or kind.startswith("model_")
    return Problem.WRONG_TYPE if wrong_type else Problem.INVALID


def from_validation(
    errors: Sequence[Mapping[str, object]], names: frozenset[str] = KNOWN_NAMES
) -> tuple[ErrorCode, tuple[FieldProblem, ...]]:
    """The code and the fields for a body that failed validation.

    Reads `loc` and `type` only. `input`, `ctx` and `msg` are never touched.
    `names` are the field names of the routes the request was for: a part of
    the body that is none of them decides no code, and is in no path.
    """
    located = [
        (cast(Sequence[object], error.get("loc", ())), str(error.get("type", "")))
        for error in errors
    ]
    if any(kind == _JSON_INVALID for _, kind in located):
        return ErrorCode.MALFORMED_JSON, ()
    fields = tuple(
        FieldProblem(path=path_of(loc, names), problem=_problem_for(kind)) for loc, kind in located
    )
    # The part of the body the first error is in decides the code.
    first = located[0][0] if located else ()
    part = first[1] if len(first) > 1 else None
    code = _CODE_FOR_FIELD.get(part) if isinstance(part, str) and part in names else None
    return code or ErrorCode.INVALID_REQUEST, fields


def spec_refused(problems: Sequence[SpecProblem]) -> ApiError:
    """What `check_spec` found, as the error a route answers with."""
    kinds = {problem.problem for problem in problems}
    if SpecProblemKind.UNKNOWN_PLACE in kinds:
        code = ErrorCode.UNKNOWN_PLACE
    elif SpecProblemKind.UNKNOWN_AREA in kinds:
        code = ErrorCode.UNKNOWN_AREA
    else:
        code = ErrorCode.INVALID_SPEC
    return ApiError(
        code,
        tuple(
            FieldProblem(path=f"spec.{problem.path}", problem=Problem(problem.problem.value))
            for problem in problems
        ),
    )


def error_response(
    meta: Meta, code: ErrorCode, fields: tuple[FieldProblem, ...] = ()
) -> JSONResponse:
    body = ErrorEnvelope(
        meta=meta, error=ErrorBody(code=code, message=MESSAGES[code], fields=fields)
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=STATUS.get(code, UNPROCESSABLE))
