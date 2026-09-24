#!/usr/bin/env python3
"""Writes what the app takes from the rest of the repository.

    python3 scripts/generate.py            write the files
    python3 scripts/generate.py --check    write nothing; fail if a file is out of date

Three things come of it:

    BurroKit/Sources/BurroKit/API/Generated/APIModels.swift       every API record and code
    BurroKit/Sources/BurroKit/API/Generated/APIRoutes.swift       every route, and `BurroAPI`
    BurroKit/Sources/BurroKit/Design/Generated/TokenValues.swift  every colour and space
    BurroKit/Tests/BurroKitTests/Recorded/                        the recorded answers, copied

The contract, contracts/openapi.json, is the only source of the first two.
apps/web/src/styles/tokens.css is the only source of the third, and
apps/web/test/recorded/ of the fourth. Nothing in the app writes one by hand.

It fails on a schema it does not understand. It never guesses.
Standard library only, and Python 3.9.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

IOS = Path(__file__).resolve().parent.parent
REPO = IOS.parent.parent
CONTRACT = REPO / "contracts" / "openapi.json"
TOKENS = REPO / "apps" / "web" / "src" / "styles" / "tokens.css"
RECORDED = REPO / "apps" / "web" / "test" / "recorded"

KIT = IOS / "BurroKit"
MODELS_OUT = KIT / "Sources" / "BurroKit" / "API" / "Generated" / "APIModels.swift"
ROUTES_OUT = KIT / "Sources" / "BurroKit" / "API" / "Generated" / "APIRoutes.swift"
TOKENS_OUT = KIT / "Sources" / "BurroKit" / "Design" / "Generated" / "TokenValues.swift"
RECORDED_OUT = KIT / "Tests" / "BurroKitTests" / "Recorded"

Schema = dict[str, Any]


class Unsupported(Exception):
    """The contract holds something this script has no rule for."""


def banner(source: str, digest: str) -> str:
    return (
        f"// Generated from {source} by apps/ios/scripts/generate.py.\n"
        "// Never edited by hand: change the source and run `make generate`.\n"
        f"// source-sha256: {digest}\n"
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- Names -----------------------------------------------------------------

# Words Swift keeps for itself. A name that is one of them is written in backticks.
RESERVED = frozenset(
    [
        "associatedtype",
        "class",
        "deinit",
        "enum",
        "extension",
        "fileprivate",
        "func",
        "import",
        "init",
        "inout",
        "internal",
        "let",
        "open",
        "operator",
        "private",
        "precedencegroup",
        "protocol",
        "public",
        "rethrows",
        "static",
        "struct",
        "subscript",
        "typealias",
        "var",
        "break",
        "case",
        "catch",
        "continue",
        "default",
        "defer",
        "do",
        "else",
        "fallthrough",
        "for",
        "guard",
        "if",
        "in",
        "repeat",
        "return",
        "throw",
        "switch",
        "where",
        "while",
        "Any",
        "as",
        "false",
        "is",
        "nil",
        "self",
        "Self",
        "super",
        "throws",
        "true",
        "try",
    ]
)

# A value that would read as something else in Swift. `.none` on an optional is `nil`.
RENAMED_CASES = {"none": "nothing", "some": "something"}

# The name given to a value this build does not know.
UNLISTED = "unlisted"


def camel(name: str) -> str:
    parts = [part for part in re.split(r"[_\-\s]+", name) if part]
    if not parts:
        raise Unsupported(f"a name with no letters in it: {name!r}")
    head = parts[0][:1].lower() + parts[0][1:]
    tail = "".join(part[:1].upper() + part[1:] for part in parts[1:])
    joined = head + tail
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", joined):
        raise Unsupported(f"a name Swift cannot hold: {name!r}")
    return joined


def quoted(name: str) -> str:
    return f"`{name}`" if name in RESERVED else name


def case_name(value: str) -> str:
    name = RENAMED_CASES.get(value, camel(value))
    if name == UNLISTED:
        raise Unsupported(
            f"a value named {value!r} would be taken for one this build does not know"
        )
    return name


def swift_string(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def doc(text: str | None, indent: str = "") -> str:
    if not text:
        return ""
    return "".join(f"{indent}/// {line}".rstrip() + "\n" for line in text.strip().splitlines())


# --- Types -----------------------------------------------------------------

# The one union in the contract, with a name for each of its alternatives.
UNIONS = {
    ("Geometry", "coordinates"): ("GeometryCoordinates", ["polygon", "multiPolygon"]),
}

LONLAT = [
    {"maximum": 180.0, "minimum": -180.0, "type": "number"},
    {"maximum": 90.0, "minimum": -90.0, "type": "number"},
]

PLAIN = {"string": "String", "integer": "Int", "number": "Double", "boolean": "Bool"}

# Keys that say what a value may be, and change nothing about its type.
LIMITS = frozenset(
    [
        "title",
        "description",
        "default",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "pattern",
        "const",
    ]
)


def ref_name(schema: Schema) -> str:
    return schema["$ref"].rsplit("/", 1)[-1]


def is_envelope(name: str, schema: Schema) -> bool:
    return name.startswith("Envelope_") and set(schema.get("properties", {})) == {"meta", "data"}


class Types:
    def __init__(self, schemas: dict[str, Schema]):
        self.schemas = schemas
        self.unions: dict[str, tuple[list[str], list[str]]] = {}

    def of(self, schema: Schema, owner: str, field: str) -> tuple[str, bool]:
        """The Swift type of a schema, and whether the contract lets it be null."""
        if "$ref" in schema:
            extra = set(schema) - {"$ref"} - LIMITS
            if extra:
                raise Unsupported(f"{owner}.{field}: a reference with {sorted(extra)} beside it")
            return ref_name(schema), False
        if "anyOf" in schema:
            options = [one for one in schema["anyOf"] if one.get("type") != "null"]
            nullable = len(options) != len(schema["anyOf"])
            if len(options) == 1:
                return self.of(options[0], owner, field)[0], nullable
            if (owner, field) not in UNIONS:
                raise Unsupported(f"{owner}.{field}: a choice of types with no name given to it")
            name, cases = UNIONS[(owner, field)]
            if len(cases) != len(options):
                raise Unsupported(f"{owner}.{field}: {len(options)} types and {len(cases)} names")
            self.unions[name] = (cases, [self.of(one, owner, field)[0] for one in options])
            return name, nullable
        extra = (
            set(schema) - LIMITS - {"type", "items", "prefixItems", "additionalProperties", "enum"}
        )
        if extra:
            raise Unsupported(f"{owner}.{field}: {sorted(extra)} is not understood")
        if "enum" in schema:
            raise Unsupported(f"{owner}.{field}: a list of values written in place, with no name")
        kind = schema.get("type")
        if kind in PLAIN:
            return PLAIN[kind], False
        if kind == "array":
            if "prefixItems" in schema:
                if (
                    schema["prefixItems"] != LONLAT
                    or schema.get("minItems") != 2
                    or schema.get("maxItems") != 2
                ):
                    raise Unsupported(
                        f"{owner}.{field}: a fixed list that is not a longitude and a latitude"
                    )
                return "LonLat", False
            inner, nullable = self.of(schema["items"], owner, field)
            if nullable:
                raise Unsupported(f"{owner}.{field}: a list that may hold null")
            return f"[{inner}]", False
        if kind == "object" and isinstance(schema.get("additionalProperties"), dict):
            inner, nullable = self.of(schema["additionalProperties"], owner, field)
            if nullable or "properties" in schema:
                raise Unsupported(f"{owner}.{field}: a record of this shape")
            return f"[String: {inner}]", False
        raise Unsupported(f"{owner}.{field}: type {kind!r}")

    def literal(self, value: Any, schema: Schema, owner: str, field: str) -> str:
        """A default of the contract, written as Swift."""
        if "$ref" in schema:
            target = self.schemas[ref_name(schema)]
            if "enum" in target:
                if value not in target["enum"]:
                    raise Unsupported(f"{owner}.{field}: a default that is not one of its values")
                return "." + case_name(value)
            if target.get("type") == "object" and isinstance(value, dict):
                fields = properties_of(ref_name(schema), target)
                if set(value) != {name for name, _ in fields}:
                    raise Unsupported(f"{owner}.{field}: a default that does not fill every field")
                inside = ", ".join(
                    f"{camel(name)}: {self.literal(value[name], one, ref_name(schema), name)}"
                    for name, one in fields
                )
                return f"{ref_name(schema)}({inside})"
            raise Unsupported(f"{owner}.{field}: a default of this kind")
        kind = schema.get("type")
        if kind == "boolean" and isinstance(value, bool):
            return "true" if value else "false"
        if kind == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return str(value)
        if kind == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return repr(float(value))
        if kind == "string" and isinstance(value, str):
            return swift_string(value)
        raise Unsupported(f"{owner}.{field}: a default of this kind")


def properties_of(name: str, schema: Schema) -> list[tuple[str, Schema]]:
    """The fields of a record: the required ones in the contract's order, then the rest by name."""
    found = schema.get("properties", {})
    required = [field for field in schema.get("required", [])]
    missing = [field for field in required if field not in found]
    if missing:
        raise Unsupported(f"{name}: requires {missing}, which it does not describe")
    rest = sorted(field for field in found if field not in required)
    return [(field, found[field]) for field in required + rest]


# --- Records and codes -----------------------------------------------------


def enum_of(name: str, schema: Schema) -> str:
    if schema.get("type") != "string":
        raise Unsupported(f"{name}: a list of values that are not text")
    values: list[str] = schema["enum"]
    cases = [(case_name(value), value) for value in values]
    if len({case for case, _ in cases}) != len(cases):
        raise Unsupported(f"{name}: two values come to one name")
    out = [doc(schema.get("description"))]
    out.append(
        f"public enum {name}: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {{\n"
    )
    for case, _ in cases:
        out.append(f"    case {quoted(case)}\n")
    out.append("    /// A value this build does not know. It is kept, and sent back, as it came.\n")
    out.append(f"    case {UNLISTED}(String)\n\n")
    listed = ", ".join(f".{case}" for case, _ in cases)
    out.append("    /// Every value the contract lists.\n")
    out.append(f"    public static let allCases: [{name}] = [{listed}]\n\n")
    out.append("    public init(rawValue: String) {\n        switch rawValue {\n")
    for case, value in cases:
        out.append(f"        case {swift_string(value)}: self = .{case}\n")
    out.append(f"        default: self = .{UNLISTED}(rawValue)\n        }}\n    }}\n\n")
    out.append("    public var rawValue: String {\n        switch self {\n")
    for case, value in cases:
        out.append(f"        case .{case}: return {swift_string(value)}\n")
    out.append(f"        case .{UNLISTED}(let value): return value\n        }}\n    }}\n")
    out.append("}\n")
    return "".join(out)


class Field:
    def __init__(self, types: Types, owner: str, name: str, schema: Schema, required: bool):
        self.json = name
        self.name = camel(name)
        base, nullable = types.of(schema, owner, name)
        self.base = base
        self.required = required
        self.nullable = nullable
        self.default: str | None = None
        if "default" in schema and schema["default"] is not None:
            self.default = types.literal(schema["default"], schema, owner, name)
        if required and "default" in schema:
            raise Unsupported(f"{owner}.{name}: required, and given a default")
        self.description = schema.get("description")
        self.fixed: str | None = None
        if "const" in schema:
            self.fixed = types.literal(schema["const"], {"type": schema.get("type")}, owner, name)

    @property
    def optional(self) -> bool:
        """True when the Swift value may be nil."""
        return self.nullable or (not self.required and self.default is None)

    @property
    def type(self) -> str:
        return f"{self.base}?" if self.optional else self.base

    @property
    def parameter(self) -> str:
        if self.fixed is not None:
            return f"{quoted(self.name)}: {self.type} = {self.fixed}"
        if self.default is not None:
            return f"{quoted(self.name)}: {self.type} = {self.default}"
        if self.optional and not self.required:
            return f"{quoted(self.name)}: {self.type} = nil"
        return f"{quoted(self.name)}: {self.type}"

    @property
    def decode(self) -> str:
        key = f".{self.name}"
        name = quoted(self.name)
        if_present = f"try container.decodeIfPresent({self.base}.self, forKey: {key})"
        if self.optional:
            return f"{name} = {if_present}"
        if self.default is not None:
            return f"{name} = {if_present} ?? {self.default}"
        return f"{name} = try container.decode({self.base}.self, forKey: {key})"

    @property
    def encode(self) -> str:
        key = f".{self.name}"
        # A field the contract requires is always written, as `null` when it holds nothing.
        if self.optional and not self.required:
            return f"try container.encodeIfPresent({quoted(self.name)}, forKey: {key})"
        return f"try container.encode({quoted(self.name)}, forKey: {key})"


def struct_of(types: Types, name: str, schema: Schema) -> str:
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise Unsupported(f"{name}: a record that may hold fields the contract does not name")
    extra = set(schema) - {
        "type",
        "additionalProperties",
        "properties",
        "required",
        "title",
        "description",
    }
    if extra:
        raise Unsupported(f"{name}: {sorted(extra)} is not understood")
    required = set(schema.get("required", []))
    fields = [
        Field(types, name, field, one, field in required)
        for field, one in properties_of(name, schema)
    ]
    if len({field.name for field in fields}) != len(fields):
        raise Unsupported(f"{name}: two fields come to one name")

    out = [doc(schema.get("description"))]
    out.append(f"public struct {name}: Hashable, Sendable, Codable {{\n")
    for field in fields:
        out.append(doc(field.description, "    "))
        out.append(f"    public let {quoted(field.name)}: {field.type}\n")
    out.append("\n")
    if len(fields) > 3:
        parameters = ",\n        ".join(field.parameter for field in fields)
        out.append(f"    public init(\n        {parameters}\n    ) {{\n")
    else:
        parameters = ", ".join(field.parameter for field in fields)
        out.append(f"    public init({parameters}) {{\n")
    for field in fields:
        out.append(f"        self.{field.name} = {quoted(field.name)}\n")
    out.append("    }\n\n")
    out.append("    enum CodingKeys: String, CodingKey {\n")
    for field in fields:
        if field.name == field.json:
            out.append(f"        case {quoted(field.name)}\n")
        else:
            out.append(f"        case {quoted(field.name)} = {swift_string(field.json)}\n")
    out.append("    }\n\n")
    out.append("    public init(from decoder: any Decoder) throws {\n")
    out.append("        let container = try decoder.container(keyedBy: CodingKeys.self)\n")
    for field in fields:
        out.append(f"        {field.decode}\n")
    out.append("    }\n\n")
    out.append("    public func encode(to encoder: any Encoder) throws {\n")
    out.append("        var container = encoder.container(keyedBy: CodingKeys.self)\n")
    for field in fields:
        out.append(f"        {field.encode}\n")
    out.append("    }\n")
    out.append("}\n")
    return "".join(out)


def union_of(name: str, cases: list[str], kinds: list[str]) -> str:
    # `Types.of` refuses a union with more names than shapes, or fewer.
    shapes = [(case, kinds[index]) for index, case in enumerate(cases)]
    out = ["/// One of several shapes. Each is tried in the contract's order.\n"]
    out.append(f"public enum {name}: Hashable, Sendable, Codable {{\n")
    for case, kind in shapes:
        out.append(f"    case {quoted(case)}({kind})\n")
    out.append("\n    public init(from decoder: any Decoder) throws {\n")
    out.append("        let container = try decoder.singleValueContainer()\n")
    for case, kind in shapes:
        out.append(f"        if let value = try? container.decode({kind}.self) {{\n")
        out.append(f"            self = .{case}(value)\n            return\n        }}\n")
    out.append(
        "        throw DecodingError.dataCorruptedError(\n"
        f'            in: container, debugDescription: "No shape of {name} fits.")\n'
    )
    out.append("    }\n\n")
    out.append("    public func encode(to encoder: any Encoder) throws {\n")
    out.append("        var container = encoder.singleValueContainer()\n        switch self {\n")
    for case in cases:
        out.append(f"        case .{case}(let value): try container.encode(value)\n")
    out.append("        }\n    }\n}\n")
    return "".join(out)


PREAMBLE = """
import Foundation

/// What these files were generated from, for the test that says when they are stale.
public enum GeneratedFrom {
    /// The SHA-256 of `contracts/openapi.json` when the models were written.
    public static let contractSHA256 = "%(digest)s"
    /// The title and the version the contract gives itself.
    public static let contractTitle = %(title)s
    public static let contractVersion = %(version)s
}

/// A position as GeoJSON writes it: longitude, then latitude, in WGS84.
public struct LonLat: Hashable, Sendable, Codable {
    public let longitude: Double
    public let latitude: Double

    public init(longitude: Double, latitude: Double) {
        self.longitude = longitude
        self.latitude = latitude
    }

    public init(from decoder: any Decoder) throws {
        var container = try decoder.unkeyedContainer()
        longitude = try container.decode(Double.self)
        latitude = try container.decode(Double.self)
        guard container.isAtEnd else {
            throw DecodingError.dataCorruptedError(
                in: container, debugDescription: "A position holds two numbers.")
        }
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.unkeyedContainer()
        try container.encode(longitude)
        try container.encode(latitude)
    }
}

/// What every answer that went well is wrapped in: `meta`, and the `data` of the route.
public struct Envelope<Payload: Decodable & Sendable>: Decodable, Sendable {
    public let meta: Meta
    public let data: Payload
}
"""


def models(contract: Schema, digest: str) -> str:
    schemas: dict[str, Schema] = contract["components"]["schemas"]
    types = Types(schemas)
    parts: list[str] = []
    for name in sorted(schemas):
        schema = schemas[name]
        if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", name):
            raise Unsupported(f"a schema named {name!r}")
        if is_envelope(name, schema):
            if ref_name(schema["properties"]["meta"]) != "Meta":
                raise Unsupported(f"{name}: an envelope whose meta is not Meta")
            continue
        if "_" in name:
            raise Unsupported(f"{name}: a generic record that is not an envelope")
        parts.append(enum_of(name, schema) if "enum" in schema else struct_of(types, name, schema))
    for name in sorted(types.unions):
        cases, kinds = types.unions[name]
        parts.append(union_of(name, cases, kinds))
    info = contract["info"]
    head = banner("contracts/openapi.json", digest) + PREAMBLE % {
        "digest": digest,
        "title": swift_string(info["title"]),
        "version": swift_string(info["version"]),
    }
    return head + "\n" + "\n".join(parts)


# --- Routes ----------------------------------------------------------------


def routes(contract: Schema, digest: str) -> str:
    schemas: dict[str, Schema] = contract["components"]["schemas"]
    found = []
    for path in sorted(contract["paths"]):
        for method, operation in sorted(contract["paths"][path].items()):
            if method not in ("get", "post"):
                raise Unsupported(f"{method.upper()} {path}: a method the client has no rule for")
            answer = operation["responses"]["200"]["content"]["application/json"]["schema"]
            wrapped = schemas[ref_name(answer)]
            enveloped = is_envelope(ref_name(answer), wrapped)
            payload = ref_name(wrapped["properties"]["data"]) if enveloped else ref_name(answer)
            body = (
                operation.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema")
            )
            parameters = operation.get("parameters", [])
            if len(parameters) > 1 or any(
                one["in"] != "path"
                or one["schema"] != {"title": one["schema"].get("title"), "type": "string"}
                for one in parameters
            ):
                raise Unsupported(f"{method.upper()} {path}: parameters the client has no rule for")
            if body is not None and parameters:
                raise Unsupported(f"{method.upper()} {path}: a body and a parameter")
            if (method == "post") != (body is not None):
                raise Unsupported(f"{method.upper()} {path}: a POST has a body and a GET has none")
            found.append(
                {
                    "id": operation["operationId"],
                    "case": camel(operation["operationId"]),
                    "method": method,
                    "path": path,
                    "description": operation.get("description", ""),
                    "payload": payload,
                    "enveloped": enveloped,
                    "body": None if body is None else ref_name(body),
                    "parameter": parameters[0]["name"] if parameters else None,
                    "failures": sorted(
                        int(code) for code in operation["responses"] if code != "200"
                    ),
                }
            )
    found.sort(key=lambda one: one["id"])

    out = [banner("contracts/openapi.json", digest), "\nimport Foundation\n\n"]
    out.append("public enum HTTPMethod: String, Hashable, Sendable {\n")
    out.append('    case get = "GET"\n    case post = "POST"\n}\n\n')
    out.append("/// Every route of the contract, named by its operation id.\n")
    out.append("public enum APIRoute: String, Hashable, Sendable, CaseIterable {\n")
    for one in found:
        out.append(f"    case {quoted(one['case'])} = {swift_string(one['id'])}\n")
    out.append("\n    public var method: HTTPMethod {\n        switch self {\n")
    for one in found:
        out.append(f"        case .{one['case']}: return .{one['method']}\n")
    out.append("        }\n    }\n\n")
    out.append("    /// The path as the contract writes it, with its parameter unfilled.\n")
    out.append("    public var template: String {\n        switch self {\n")
    for one in found:
        out.append(f"        case .{one['case']}: return {swift_string(one['path'])}\n")
    out.append("        }\n    }\n\n")
    out.append("    /// The name of the one value in the path, for the routes that have one.\n")
    out.append("    public var parameter: String? {\n        switch self {\n")
    for one in found:
        value = "nil" if one["parameter"] is None else swift_string(one["parameter"])
        out.append(f"        case .{one['case']}: return {value}\n")
    out.append("        }\n    }\n\n")
    out.append("    /// False for the one answer that comes with no `meta` around it.\n")
    out.append("    public var enveloped: Bool {\n        switch self {\n")
    for one in found:
        out.append(
            f"        case .{one['case']}: return {'true' if one['enveloped'] else 'false'}\n"
        )
    out.append("        }\n    }\n\n")
    out.append("    /// The statuses the contract says the route can fail with.\n")
    out.append("    public var failures: [Int] {\n        switch self {\n")
    for one in found:
        out.append(f"        case .{one['case']}: return {one['failures']}\n")
    out.append("        }\n    }\n}\n\n")

    def signature(one: dict[str, Any]) -> str:
        answer = (
            f"Answer<{one['payload']}>"
            if one["enveloped"]
            else f"Result<{one['payload']}, Failure>"
        )
        if one["body"] is not None:
            return f"func {one['case']}(_ body: {one['body']}) async -> {answer}"
        if one["parameter"] is not None:
            return f"func {one['case']}(_ {camel(one['parameter'])}: String) async -> {answer}"
        return f"func {one['case']}() async -> {answer}"

    out.append("/// The API: one method a route, named by its operation id.\n")
    out.append("///\n/// No method throws. ")
    out.append("Each answers with `meta` and `data`, or with a failure that says why.\n")
    out.append("public protocol BurroAPI: Sendable {\n")
    for one in found:
        out.append(doc(f"`{one['method'].upper()} {one['path']}`. {one['description']}", "    "))
        out.append(f"    {signature(one)}\n")
    out.append("}\n\n")
    out.append(
        "/// What a client has to be able to do. Every method of `BurroAPI` is made of it.\n"
    )
    out.append("public protocol RouteSending: Sendable {\n")
    out.append("    /// Sends one request and reads the envelope of the answer.\n")
    out.append("    func send<Payload: Decodable & Sendable>(\n")
    out.append("        _ route: APIRoute, parameter: String?, body: (any Encodable & Sendable)?\n")
    out.append("    ) async -> Answer<Payload>\n")
    out.append("    /// Sends one request to a route whose answer has no `meta` around it.\n")
    out.append("    func sendPlain<Payload: Decodable & Sendable>(_ route: APIRoute) async")
    out.append(" -> Result<Payload, Failure>\n")
    out.append("}\n\n")
    out.append("extension BurroAPI where Self: RouteSending {\n")
    for index, one in enumerate(found):
        if index:
            out.append("\n")
        out.append(f"    public {signature(one)} {{\n")
        if not one["enveloped"]:
            out.append(f"        await sendPlain(.{one['case']})\n")
        elif one["body"] is not None:
            out.append(f"        await send(.{one['case']}, parameter: nil, body: body)\n")
        elif one["parameter"] is not None:
            parameter = camel(one["parameter"])
            out.append(f"        await send(.{one['case']}, parameter: {parameter}, body: nil)\n")
        else:
            out.append(f"        await send(.{one['case']}, parameter: nil, body: nil)\n")
        out.append("    }\n")
    out.append("}\n")
    return "".join(out)


# --- Tokens ----------------------------------------------------------------

COLOUR = re.compile(r"^\s*--([a-z0-9-]+):\s*#([0-9a-fA-F]{6})\s*;", re.MULTILINE)
PIXELS = re.compile(r"^\s*--([a-z0-9-]+):\s*(\d+)px\s*;", re.MULTILINE)
MILLISECONDS = re.compile(r"^\s*--([a-z0-9-]+):\s*(\d+)ms\s*;", re.MULTILINE)


def blocks_of(css: str) -> tuple[str, str, str]:
    """The light values, the dark ones, and what holds when motion is welcome."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    dark = re.search(
        r"@media \(prefers-color-scheme: dark\)\s*\{\s*:root\s*\{(.*?)\}\s*\}", css, re.DOTALL
    )
    motion = re.search(
        r"@media \(prefers-reduced-motion: no-preference\)\s*\{\s*:root\s*\{(.*?)\}\s*\}",
        css,
        re.DOTALL,
    )
    light = re.search(r"^:root\s*\{(.*?)\}", css, re.DOTALL | re.MULTILINE)
    if not (light and dark and motion):
        raise Unsupported("tokens.css: the light, the dark or the motion block was not found")
    return light.group(1), dark.group(1), motion.group(1)


def tokens(css: str, digest: str) -> str:
    light_block, dark_block, motion_block = blocks_of(css)
    light = dict(COLOUR.findall(light_block))
    dark = dict(COLOUR.findall(dark_block))
    if set(light) != set(dark) or not light:
        raise Unsupported("tokens.css: a colour with no light value, or none for the dark")
    sizes = dict(PIXELS.findall(light_block))
    still = dict(MILLISECONDS.findall(light_block))
    moving = dict(MILLISECONDS.findall(motion_block))
    if set(still) != set(moving) or any(value != "0" for value in still.values()):
        raise Unsupported("tokens.css: motion that is not nought until it is welcome")

    out = [banner("apps/web/src/styles/tokens.css", digest), "\n"]
    out.append("/// Every colour, space and time of the website's tokens, as it names them.\n")
    out.append("///\n/// `Tokens` gives each its Swift name. Use that, and not this.\n")
    out.append("public enum TokenValues {\n")
    out.append(
        "    /// Each colour by its name in `tokens.css`: light, then dark, as `0xRRGGBB`.\n"
    )
    out.append("    public static let colours: [String: (light: UInt32, dark: UInt32)] = [\n")
    for name in sorted(light):
        out.append(
            f"        {swift_string(name)}: (0x{light[name].lower()}, 0x{dark[name].lower()}),\n"
        )
    out.append("    ]\n\n")
    out.append("    /// Each length by its name in `tokens.css`, in points.\n")
    out.append("    public static let lengths: [String: Double] = [\n")
    for name in sorted(sizes):
        out.append(f"        {swift_string(name)}: {int(sizes[name])},\n")
    out.append("    ]\n\n")
    out.append("    /// How long a change takes where motion is welcome, in seconds.")
    out.append(" Where it is not, none.\n")
    out.append("    public static let durations: [String: Double] = [\n")
    for name in sorted(moving):
        out.append(f"        {swift_string(name)}: {int(moving[name]) / 1000!r},\n")
    out.append("    ]\n\n")
    for name in sorted(light):
        out.append(
            f"    public static let {camel(name)} = TokenColor(light: 0x{light[name].lower()}, "
            f"dark: 0x{dark[name].lower()})\n"
        )
    out.append("\n")
    for name in sorted(sizes):
        out.append(f"    public static let {camel(name)}: Double = {int(sizes[name])}\n")
    out.append("}\n")
    return "".join(out)


# --- Recorded answers ------------------------------------------------------


def recorded() -> dict[Path, bytes]:
    """Every recorded answer, by where its copy goes."""
    found = sorted(path for path in RECORDED.rglob("*.json"))
    if not found:
        raise Unsupported("apps/web/test/recorded holds no recording")
    return {RECORDED_OUT / path.relative_to(RECORDED): path.read_bytes() for path in found}


# --- Writing and checking --------------------------------------------------


def wanted() -> dict[Path, bytes]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    files: dict[Path, bytes] = {
        MODELS_OUT: models(contract, sha256(CONTRACT)).encode("utf-8"),
        ROUTES_OUT: routes(contract, sha256(CONTRACT)).encode("utf-8"),
        TOKENS_OUT: tokens(TOKENS.read_text(encoding="utf-8"), sha256(TOKENS)).encode("utf-8"),
    }
    files.update(recorded())
    return files


def strays(files: dict[Path, bytes]) -> list[Path]:
    """Files in a folder this script owns that it would not write."""
    owned = [MODELS_OUT.parent, TOKENS_OUT.parent, RECORDED_OUT]
    found = [
        path for folder in owned if folder.exists() for path in folder.rglob("*") if path.is_file()
    ]
    return sorted(path for path in found if path not in files and path.name != ".DS_Store")


def main(arguments: list[str]) -> int:
    unknown = [argument for argument in arguments if argument != "--check"]
    if unknown:
        sys.stderr.write(__doc__ or "")
        return 2
    check = "--check" in arguments
    try:
        files = wanted()
    except Unsupported as problem:
        sys.stderr.write(f"generate.py has no rule for this: {problem}\n")
        return 1

    stale = [
        path for path, content in files.items() if not path.exists() or path.read_bytes() != content
    ]
    extra = strays(files)
    if check:
        for path in stale:
            sys.stderr.write(f"{path.relative_to(IOS)} is out of date. Run `make generate`.\n")
        for path in extra:
            sys.stderr.write(f"{path.relative_to(IOS)} should not be there. Run `make generate`.\n")
        if not stale and not extra:
            sys.stdout.write(f"{len(files)} generated files match their sources\n")
        return 1 if stale or extra else 0

    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(files[path])
    for path in extra:
        path.unlink()
    left = len(files) - len(stale)
    sys.stdout.write(f"Wrote {len(stale)} files, removed {len(extra)}, left {left} as they were\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
