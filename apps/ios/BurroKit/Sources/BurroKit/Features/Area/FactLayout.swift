import Foundation

// A fact from an area's profile has no sentence of its own, so its slots are
// laid out in fixed columns, chosen by its template. It mirrors the website's
// `FactRow`, and docs/design/web.md section 4.
//
// Each value is a slot of the fact as the API formatted it. A money slot gets
// its pound sign and nothing else is added. A column whose slot the fact does
// not hold is left out: nothing is filled in.

/// One column of a row: what it is, and the value as the API wrote it.
public struct FactColumn: Hashable, Sendable, Identifiable {
    public let name: String
    public let value: String

    public var id: String { name }
}

/// One row of an area's screen: a fact laid out, or the words that say there is none.
public struct FactRow: Hashable, Sendable, Identifiable {
    /// Tells one row of a screen from the next. It is held in memory and goes nowhere.
    public let id: String
    public let name: String
    public let columns: [FactColumn]
    /// What is said under the columns: the caveat that goes with recorded
    /// crime, that a vibe cannot place the area, that a price has no range,
    /// and the API's own line that a recipe is a judgement.
    public let caveats: [String]
    /// The source and the date of the figure. Empty when there is no figure.
    public let sources: [SourceLine]
    /// What is said in place of a figure, when the area has none.
    public let noFigure: String?

    /// The row of a fact. `nil` for a fact this build has no columns for,
    /// which is then not drawn.
    public init?(_ fact: Fact, named given: String? = nil) {
        guard let columns = FactLayout.columns(of: fact), let name = FactLayout.name(of: fact, given: given)
        else { return nil }
        id = "\(fact.kind.rawValue)/\(fact.key)"
        self.name = name
        // A column that only repeats the row's name says nothing new.
        self.columns = columns.filter { $0.value != name }
        caveats = FactLayout.caveats(of: fact)
        sources = SourceLines.of([fact])
        noFigure = nil
    }

    /// A row for something the area has no figure for. It says so, and gives
    /// no figure and no source.
    public init(noFigure name: String, says: String, id: String) {
        self.id = id
        self.name = name
        columns = []
        caveats = []
        sources = []
        noFigure = says
    }

    /// The line under the row: its source and its date.
    public var sourceWords: String? {
        guard !sources.isEmpty else { return nil }
        return "\(AreaCopy.Source.source): " + sources.map(\.words).joined(separator: " ")
    }
}

public enum FactLayout {
    /// The columns of a fact, left to right, chosen by its template. `nil` for
    /// a template an area's page does not lay out.
    public static func columns(of fact: Fact) -> [FactColumn]? {
        let slots = fact.slots
        let found: [(String, String?)]
        switch fact.template {
        case .feature, .featureCrime:
            found = [(AreaCopy.Column.value, slots["value"]), (AreaCopy.Column.standing, slots["standing"])]
        case .vibe:
            found =
                [
                    (AreaCopy.Column.band, slots["band"]),
                    (AreaCopy.Column.ends, between(slots["low_end"], slots["high_end"])),
                    (AreaCopy.Column.compared, slots["compared"]),
                    (AreaCopy.Column.partsDated, slots["span"]),
                ] + restsOnPart(slots)
        case .vibeRange:
            found =
                [
                    (AreaCopy.Column.bands, between(slots["spread_low"], slots["spread_high"])),
                    (AreaCopy.Column.ends, between(slots["low_end"], slots["high_end"])),
                    (AreaCopy.Column.partsDated, slots["span"]),
                ] + restsOnPart(slots)
        case .vibeUnknown:
            found = [(AreaCopy.Column.partsKnown, slots["known"]), (AreaCopy.Column.parts, slots["parts"])]
        case .costBuyMedian:
            // One number, as a publisher gives it. No range stands beside it, and no word
            // for how sure it is: the row says under its columns what is not known of it.
            found = [
                (AreaCopy.Column.segment, slots["segment"]),
                (AreaCopy.Column.middleOfAll, pounds(slots["median"])),
                (AreaCopy.Column.soldIn, slots["period"]),
            ]
        case .costBuySold:
            // One number, counted from the sales of three years. It says how many it rests on.
            found = [
                (AreaCopy.Column.segment, slots["segment"]),
                (AreaCopy.Column.middleOfAll, pounds(slots["median"])),
                (AreaCopy.Column.soldIn, slots["period"]),
                (AreaCopy.Column.sales, slots["sales"]),
            ]
        case .costRent, .costBuy:
            found = [
                (AreaCopy.Column.segment, slots["segment"]),
                (AreaCopy.Column.range, range(slots["lower"], slots["upper"])),
                (AreaCopy.Column.median, pounds(slots["median"])),
                (AreaCopy.Column.asOf, slots["as_of"]),
                (AreaCopy.Column.confidence, slots["confidence"]),
            ]
        case .station, .stationNearby:
            found = [
                (AreaCopy.Column.station, slots["name"]),
                (AreaCopy.Column.walk, slots["walk"]),
                (AreaCopy.Column.lines, slots["lines"]),
            ]
        case .area:
            found = [(AreaCopy.Column.name, slots["name"]), (AreaCopy.Column.borough, slots["borough"])]
        case .budgetUnder, .budgetOver, .budgetUnderMedian, .budgetOverMedian, .travelPt, .travelPtOver,
            .travelOther, .travelOtherOver, .travelBeyond, .travelEstimated, .missing, .missingJourney,
            .likeness, .likenessSame, .unlisted:
            // These are of a search, or of another area. This page lays neither out in columns.
            return nil
        }
        return found.compactMap { name, value in
            guard let value, !value.isEmpty else { return nil }
            return FactColumn(name: name, value: value)
        }
    }

    /// What names the row: the name it was given, or the fact's own label.
    /// Which station is the nearest is said by the template, and by nothing
    /// else in the fact.
    public static func name(of fact: Fact, given: String? = nil) -> String? {
        if let given, !given.isEmpty { return given }
        let kind = AreaCopy.kind(fact.template)
        if fact.template == .station || fact.template == .stationNearby { return kind }
        return fact.label.isEmpty ? kind : fact.label
    }

    /// How many parts of its recipe a band rests on, where that is not all of
    /// them. Both counts, and what those parts carry of the recipe, are the
    /// API's: nothing is added up here.
    static func restsOnPart(_ slots: [String: String]) -> [(String, String?)] {
        guard let known = slots["known"], let parts = slots["parts"], known != parts else { return [] }
        return [
            (AreaCopy.Column.partsKnown, known),
            (AreaCopy.Column.parts, parts),
            (AreaCopy.Column.share, slots["share"]),
        ]
    }

    /// What is said under the columns of a fact, each line in fixed words or the API's own.
    static func caveats(of fact: Fact) -> [String] {
        var said: [String] = []
        switch fact.template {
        case .featureCrime: said.append(AreaCopy.crimeCaveat)
        case .vibeUnknown: said.append(VibeCopy.cannotPlace)
        case .costBuyMedian: said.append(AreaCopy.oneNumber)
        default: break
        }
        // What a middle price means, in the API's words: about half of what sold went for less.
        if fact.kind == .cost, let half = fact.slots["half_sold"], !half.isEmpty {
            said.append(half)
        }
        // What every sentence about a vibe ends in, as the API holds it.
        if fact.kind == .tag, let judgement = fact.slots["judgement"], !judgement.isEmpty {
            said.append(judgement)
        }
        return said
    }

    /// From one slot to another, where the fact holds both.
    static func between(_ from: String?, _ to: String?) -> String? {
        guard let from, !from.isEmpty, let to, !to.isEmpty else { return nil }
        return "\(from) \(AreaCopy.Column.to) \(to)"
    }

    static func pounds(_ value: String?) -> String? {
        guard let value, !value.isEmpty else { return nil }
        return "£\(value)"
    }

    static func range(_ lower: String?, _ upper: String?) -> String? {
        between(pounds(lower), pounds(upper))
    }
}
