import Foundation

// Where a fact came from and when: read off the fact, for a screen to show.
// It mirrors apps/web/src/lib/facts.ts and format.ts.
//
// Nothing here writes a word about a place. It finds what the API sent.

/// One source and one date, as the line under a figure gives them.
public struct SourceLine: Hashable, Sendable, Identifiable {
    public let sourceId: String
    public let name: String
    public let asOf: String
    public let synthetic: Bool

    public var id: String { "\(sourceId) \(asOf)" }

    /// The line as it is read: the source, the date, and that it is made up when it is.
    public var words: String {
        let from = "\(name). \(AreaCopy.Source.dataFrom) \(ReadableDate.words(asOf))."
        return synthetic ? "\(from) \(AreaCopy.Source.madeUp)" : from
    }
}

public enum SourceLines {
    /// One line for each source and date, however many facts share them.
    public static func of(_ facts: [Fact]) -> [SourceLine] {
        var order: [String] = []
        var lines: [String: SourceLine] = [:]
        for fact in facts {
            for source in fact.sources {
                let line = SourceLine(
                    sourceId: source.sourceId, name: source.name, asOf: fact.asOf, synthetic: fact.synthetic)
                if lines[line.id] == nil { order.append(line.id) }
                lines[line.id] = line
            }
        }
        return order.compactMap { lines[$0] }
    }

    /// Every source the facts name, once each, in the order of their names.
    public static func sources(of facts: [Fact]) -> [FactSource] {
        var found: [String: FactSource] = [:]
        for fact in facts {
            for source in fact.sources { found[source.sourceId] = source }
        }
        let british = Locale(identifier: "en_GB")
        return found.values.sorted { one, other in
            let byName = one.name.compare(other.name, options: [.caseInsensitive], locale: british)
            if byName != .orderedSame { return byName == .orderedAscending }
            return one.sourceId < other.sourceId
        }
    }

    /// Everything the line under a figure says, as one piece of text.
    public static func words(for facts: [Fact]) -> String? {
        let lines = of(facts)
        guard !lines.isEmpty else { return nil }
        return "\(AreaCopy.Source.source): " + lines.map(\.words).joined(separator: " ")
    }
}

/// How a date the API sent is written for a person to read.
///
/// Only dates are written out here. A figure about a place arrives already
/// formatted, in a fact's slots, and is shown as it came.
public enum ReadableDate {
    private static let months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    /// A date or a timestamp, as "23 September 2026", and a month, as "August
    /// 2026". Anything else is returned as it came: a year, or a period, is
    /// the release's own words.
    public static func words(_ value: String) -> String {
        let text = Array(value.utf8)
        if text.count == 7, let (year, month) = yearAndMonth(text) {
            return "\(months[month - 1]) \(year)"
        }
        let isDate = text.count == 10
        let isTimestamp = text.count >= 20 && text[10] == UInt8(ascii: "T") && text.last == UInt8(ascii: "Z")
        guard isDate || (isTimestamp && isTime(Array(text[11...]))),
            let (year, month) = yearAndMonth(Array(text[..<7])),
            text[7] == UInt8(ascii: "-"),
            let day = number(text[8..<10]), isDay(day, month: month, year: year)
        else { return value }
        return "\(day) \(months[month - 1]) \(year)"
    }

    private static func yearAndMonth(_ text: [UInt8]) -> (Int, Int)? {
        guard text.count == 7, text[4] == UInt8(ascii: "-"),
            let year = number(text[0..<4]), let month = number(text[5..<7]), (1...12).contains(month)
        else { return nil }
        return (year, month)
    }

    /// `hh:mm:ss`, a fraction of a second if there is one, and `Z`.
    private static func isTime(_ text: [UInt8]) -> Bool {
        guard text.count >= 9, text[2] == UInt8(ascii: ":"), text[5] == UInt8(ascii: ":"),
            let hour = number(text[0..<2]), let minute = number(text[3..<5]), let second = number(text[6..<8]),
            hour < 24, minute < 60, second < 60
        else { return false }
        let rest = text[8..<(text.count - 1)]
        if rest.isEmpty { return true }
        guard rest.first == UInt8(ascii: "."), rest.count > 1 else { return false }
        return rest.dropFirst().allSatisfy(isDigit)
    }

    private static func isDay(_ day: Int, month: Int, year: Int) -> Bool {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "UTC") ?? .gmt
        let parts = DateComponents(calendar: calendar, year: year, month: month, day: day)
        return day >= 1 && parts.isValidDate(in: calendar)
    }

    private static func isDigit(_ byte: UInt8) -> Bool {
        byte >= UInt8(ascii: "0") && byte <= UInt8(ascii: "9")
    }

    private static func number(_ text: ArraySlice<UInt8>) -> Int? {
        guard !text.isEmpty, text.allSatisfy(isDigit) else { return nil }
        return text.reduce(0) { $0 * 10 + Int($1 - UInt8(ascii: "0")) }
    }
}
