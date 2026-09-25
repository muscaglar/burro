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
        case .vibe:
            pairs =
                [
                    (names.band, slots["band"]),
                    (names.ends, between(slots["low_end"], slots["high_end"])),
                    (names.compared, slots["compared"]),
                    (names.partsDated, slots["span"]),
                ] + restsOnPart(slots)
        case .vibeRange:
            pairs =
                [
                    (names.bands, between(slots["spread_low"], slots["spread_high"])),
                    (names.ends, between(slots["low_end"], slots["high_end"])),
                    (names.partsDated, slots["span"]),
                ] + restsOnPart(slots)
        case .vibeUnknown:
            pairs = [(names.partsKnown, slots["known"]), (names.parts, slots["parts"])]
        case .costBuyMedian:
            pairs = [
                (names.segment, slots["segment"]), (names.middleOfAll, pounds(slots["median"])),
                (names.soldIn, slots["period"]),
            ]
        case .costBuySold:
            pairs = [
                (names.segment, slots["segment"]), (names.middleOfAll, pounds(slots["median"])),
                (names.soldIn, slots["period"]), (names.sales, slots["sales"]),
            ]
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
        case .budgetUnderMedian, .budgetOverMedian:
            // The budget is held against the one number there is, and the row names it.
            pairs = [
                (names.middleOfAll, pounds(slots["median"])), (names.amount, pounds(slots["amount"])),
                (fact.template == .budgetUnderMedian ? names.under : names.over, pounds(slots["margin"])),
            ]
        case .travelPt, .travelPtOver:
            pairs =
                [
                    (names.place, slots["place"]), (names.mode, slots["mode"]),
                    (names.typical, slots["typical"]), (names.missed, slots["missed"]),
                ] + againstTheLimit(fact)
        case .travelOther, .travelOtherOver:
            pairs =
                [
                    (names.place, slots["place"]), (names.mode, slots["mode"]),
                    (names.minutes, slots["minutes"]),
                ] + againstTheLimit(fact)
        case .travelEstimated:
            // No time is held. The fact says where an estimate stands against the limit, and
            // that it is one, and gives no minutes of its own.
            pairs = [
                (names.place, slots["place"]), (names.mode, slots["mode"]), (names.limit, slots["limit"]),
                (names.estimate, slots["verdict"]), (names.howKnown, slots["estimated"]),
            ]
        case .travelBeyond:
            pairs = [
                (names.place, slots["place"]), (names.mode, slots["mode"]), (names.moreThan, slots["cutoff"]),
            ]
        case .station, .stationNearby:
            pairs = [(names.station, slots["name"]), (names.walk, slots["walk"]), (names.lines, slots["lines"])]
        case .area, .missing:
            pairs = [(names.name, slots["name"]), (names.borough, slots["borough"])]
        case .missingJourney:
            pairs = [(names.name, slots["name"]), (names.place, slots["place"])]
        case .likeness, .likenessSame:
            // A likeness is of two areas, and is said on an area's own page.
            pairs = []
        case .unlisted:
            // A kind of fact this build does not know is not laid out by guesswork.
            pairs = []
        }
        return pairs.compactMap { name, value in
            guard let value, !value.isEmpty else { return nil }
            return Column(name: name, value: value)
        }
    }

    /// From one slot to another, where the fact holds both.
    private static func between(_ from: String?, _ to: String?) -> String? {
        guard let from, !from.isEmpty, let to, !to.isEmpty else { return nil }
        return "\(from) \(ResultsCopy.Columns.to) \(to)"
    }

    /// How many parts of its recipe a band rests on, where that is not all of
    /// them. Both counts, and what those parts carry of the recipe, are the
    /// API's: nothing is added up here.
    private static func restsOnPart(_ slots: [String: String]) -> [(String, String?)] {
        guard let known = slots["known"], let parts = slots["parts"], known != parts else { return [] }
        let names = ResultsCopy.Columns.self
        return [(names.partsKnown, known), (names.parts, parts), (names.share, slots["share"])]
    }

    /// Where a journey stands against the limit the person set, where the fact holds one.
    private static func againstTheLimit(_ fact: Fact) -> [(String, String?)] {
        let names = ResultsCopy.Columns.self
        let over = fact.template == .travelPtOver || fact.template == .travelOtherOver
        return [
            (names.limit, fact.slots["limit"]),
            (over ? names.overLimit : names.underLimit, fact.slots["margin"]),
        ]
    }

    /// One fact with no sentence of its own, laid out: its name, its columns, and its source.
    struct FactShown: Hashable, Sendable {
        let name: String
        let columns: [Column]
        /// What is said under the columns: the caveat that goes with recorded
        /// crime, that a vibe cannot place the area, that a price has no
        /// range, and the API's own line that a recipe is a judgement.
        let caveats: [String]
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
            caveats: FactLayout.caveats(of: fact),
            sources: sourceLines(of: [fact]))
    }
}
