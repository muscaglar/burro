import Foundation

/// JSON as plain values, for a test to compare what was sent with what was meant.
///
/// A number is held as the number it is worth, so two values are the same
/// when they say the same thing, however each was written. `true` is never 1.
indirect enum JSON: Codable, Hashable, Sendable {
    case null
    case bool(Bool)
    case number(Double)
    case string(String)
    case array([JSON])
    case object([String: JSON])

    init(from decoder: any Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode(Double.self) {
            self = .number(value)
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode([JSON].self) {
            self = .array(value)
        } else {
            self = .object(try container.decode([String: JSON].self))
        }
    }

    func encode(to encoder: any Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .null: try container.encodeNil()
        case .bool(let value): try container.encode(value)
        case .number(let value): try container.encode(value)
        case .string(let value): try container.encode(value)
        case .array(let value): try container.encode(value)
        case .object(let value): try container.encode(value)
        }
    }

    static func read(_ data: Data) throws -> JSON {
        try JSONDecoder().decode(JSON.self, from: data)
    }

    /// What a value is written as.
    static func written(_ value: some Encodable) throws -> JSON {
        try read(JSONEncoder().encode(value))
    }

    var data: Data {
        get throws { try JSONEncoder().encode(self) }
    }

    subscript(key: String) -> JSON? {
        get {
            if case .object(let fields) = self { return fields[key] }
            return nil
        }
        set {
            guard case .object(var fields) = self else { return }
            fields[key] = newValue
            self = .object(fields)
        }
    }

    var string: String? {
        if case .string(let value) = self { return value }
        return nil
    }

    var int: Int? {
        if case .number(let value) = self { return Int(exactly: value) }
        return nil
    }

    var bool: Bool? {
        if case .bool(let value) = self { return value }
        return nil
    }

    var isNull: Bool { self == .null }
}
