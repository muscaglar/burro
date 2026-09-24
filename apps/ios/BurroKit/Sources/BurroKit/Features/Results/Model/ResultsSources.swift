import Foundation

// Where a fact came from and when, and a fact laid out in columns: both read
// off the fact, for a screen to show.
//
// Nothing here writes a word about a place. Every value is a slot of a fact
// as the API formatted it. A money slot gets its pound sign and nothing else
// is added. Only a date is written out for a person to read.

extension Results {
    /// The source and the date behind a line: what ends every sentence and every figure.
    struct SourceLine: Hashable, Sendable, Identifiable {
        let sourceId: String
        let name: String
        /// The date as the API sent it.
        let asOf: String
        /// The date as a person reads it.
        let date: String
        let synthetic: Bool

        var id: String { "\(sourceId) \(asOf)" }

        /// The line in full, as it is read out.
        var words: String {
            let line = "\(ResultsCopy.Source.source): \(name). \(ResultsCopy.Source.dataFrom) \(date)."
            return synthetic ? "\(line) \(ResultsCopy.Source.madeUp)" : line
        }
    }

    /// One line for each source and date, however many facts share them.
    static func sourceLines(of facts: [Fact]) -> [SourceLine] {
        var lines: [SourceLine] = []
        for fact in facts {
            for source in fact.sources {
                let line = SourceLine(
                    sourceId: source.sourceId, name: source.name, asOf: fact.asOf,
                    date: readableDate(fact.asOf), synthetic: fact.synthetic)
                if let at = lines.firstIndex(where: { $0.id == line.id }) {
                    lines[at] = line
                } else {
                    lines.append(line)
                }
            }
        }
        return lines
    }

    private static let months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    /// A date or a timestamp, written as a day, a month and a year, and a
    /// month, written as a month and a year. Anything else is returned as it
    /// came: a year, or a period, is the release's own words.
    static func readableDate(_ value: String) -> String {
        let text = Array(value.utf8)
        func digits(_ from: Int, _ count: Int) -> Int? {
            guard from + count <= text.count else { return nil }
            var number = 0
            for byte in text[from..<from + count] {
                guard byte >= 0x30, byte <= 0x39 else { return nil }
                number = number * 10 + Int(byte - 0x30)
            }
            return number
        }
        func dash(_ at: Int) -> Bool { at < text.count && text[at] == 0x2d }

        guard let year = digits(0, 4), dash(4), let month = digits(5, 2), (1...12).contains(month) else {
            return value
        }
        let named = months[month - 1]
        if text.count == 7 { return "\(named) \(year)" }
        guard dash(7), let day = digits(8, 2), (1...daysIn(month, of: year)).contains(day) else {
            return value
        }
        let isDate = text.count == 10
        let isTimestamp = text.count >= 20 && text[10] == 0x54 && text[text.count - 1] == 0x5a
        guard isDate || isTimestamp else { return value }
        return "\(day) \(named) \(year)"
    }

    private static func daysIn(_ month: Int, of year: Int) -> Int {
        switch month {
        case 4, 6, 9, 11: return 30
        case 2: return (year % 4 == 0 && year % 100 != 0) || year % 400 == 0 ? 29 : 28
        default: return 31
        }
    }

    // MARK: - A fact in columns

    /// One column of a fact: what it is called, and its value as the API wrote it.
    struct Column: Hashable, Sendable, Identifiable {
        let name: String
        let value: String

        var id: String { name }
    }

    private static func pounds(_ value: String?) -> String? {
        value.map { "\(ResultsCopy.Cost.pound)\($0)" }
    }

    /// The columns of a fact, in order, chosen by its template. A column
    /// whose slot the fact does not hold is left out: nothing is filled in.
    static func columns(of fact: Fact) -> [Column] {
        let slots = fact.slots
        let names = ResultsCopy.Columns.self
        let pairs: [(String, String?)]
        switch fact.template {
        case .feature, .featureCrime:
            pairs = [(names.value, slots["value"]), (names.standing, slots["standing"])]
        case .tag:
            pairs = [(names.standing, slots["standing"])]
        case .costRent, .costBuy:
            var range: String?
            if let lower = pounds(slots["lower"]), let upper = pounds(slots["upper"]) {
                range = "\(lower) \(names.to) \(upper)"
            }
            pairs = [
                (names.segment, slots["segment"]), (names.range, range),
                (names.median, pounds(slots["median"])), (names.asOf, slots["as_of"]),
                (names.confidence, slots["confidence"]),
            ]
        case .budgetUnder, .budgetOver:
            pairs = [
                (names.upper, pounds(slots["upper"])), (names.amount, pounds(slots["amount"])),
                (fact.template == .budgetUnder ? names.under : names.over, pounds(slots["margin"])),
            ]
        case .travelPt:
            pairs = [
                (names.place, slots["place"]), (names.mode, slots["mode"]),
                (names.typical, slots["typical"]), (names.missed, slots["missed"]),
            ]
        case .travelOther:
            pairs = [
                (names.place, slots["place"]), (names.mode, slots["mode"]), (names.minutes, slots["minutes"]),
            ]
        case .travelBeyond:
            pairs = [
                (names.place, slots["place"]), (names.mode, slots["mode"]), (names.moreThan, slots["cutoff"]),
            ]
        case .station, .stationNearby:
            pairs = [(names.station, slots["name"]), (names.walk, slots["walk"]), (names.lines, slots["lines"])]
        case .area, .missing:
            pairs = [(names.name, slots["name"]), (names.borough, slots["borough"])]
        case .unlisted:
            // A kind of fact this build does not know is not laid out by guesswork.
            pairs = []
        }
        return pairs.compactMap { name, value in
            guard let value, !value.isEmpty else { return nil }
            return Column(name: name, value: value)
        }
    }

    /// One fact with no sentence of its own, laid out: its name, its columns, and its source.
    struct FactShown: Hashable, Sendable {
        let name: String
        let columns: [Column]
        /// The caveat that goes under a figure of recorded crime.
        let caveat: String?
        let sources: [SourceLine]
    }

    /// A fact as a row. It is named by the fact's own label, but for a
    /// station: which station is the nearest is said by the template alone.
    static func row(of fact: Fact, named given: String? = nil) -> FactShown {
        let ofAStation = fact.template == .station || fact.template == .stationNearby
        let kind = ResultsCopy.kind(of: fact.template) ?? fact.label
        let name = given ?? (ofAStation ? kind : (fact.label.isEmpty ? kind : fact.label))
        return FactShown(
            name: name,
            // A column that only repeats the row's name says nothing new.
            columns: columns(of: fact).filter { $0.value != name },
            caveat: fact.template == .featureCrime ? ResultsCopy.crimeCaveat : nil,
            sources: sourceLines(of: [fact]))
    }
}
