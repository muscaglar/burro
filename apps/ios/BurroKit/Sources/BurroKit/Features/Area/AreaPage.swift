import Foundation

// How an area's profile is laid out on its screen: which facts go under which
// heading, and in what order. It mirrors apps/web/src/lib/area/profile.ts.
//
// Nothing here writes a word about a place, and nothing is filled in. A
// feature with no figure has no fact, and the screen says so in its own
// words. What the API serves with no fact behind it, such as whether a
// station is step-free, has no source and no date, and is not laid out at all.

/// Everything an area's screen shows that is of the release: the facts, in
/// the order they are shown, and the names of the areas next to it.
///
/// It holds nothing of a search: no rank, no fit, no journey, no budget. So
/// it is also what the shortlist keeps.
public struct AreaPage: Hashable, Sendable {
    /// A feature or a tag of the release, with the fact the area has for it, if it has one.
    public struct Row: Hashable, Sendable, Identifiable {
        /// The API's name for the feature or the tag. It names the row when there is no figure.
        public let label: String
        public let fact: Fact?
        /// `feature` or `tag`.
        public let kind: FactKind
        /// The id of the feature or the tag, as the release lists it.
        public let key: String

        public var id: String { "\(kind.rawValue)/\(key)" }

        public init(label: String, fact: Fact?, kind: FactKind, key: String) {
            self.label = label
            self.fact = fact
            self.kind = kind
            self.key = key
        }
    }

    /// The features that are about one thing.
    public struct Group: Hashable, Sendable, Identifiable {
        /// What they are about. `nil` when the release's list of features is not in hand.
        public let dimension: Dimension?
        public let rows: [Row]

        public var id: String { dimension?.rawValue ?? "" }

        public init(dimension: Dimension?, rows: [Row]) {
            self.dimension = dimension
            self.rows = rows
        }
    }

    public let area: AreaRef
    public let rankable: Bool
    /// The release the facts are of.
    public let releaseId: String
    public let synthetic: Bool
    /// The fact that names the area and its borough. It carries their source.
    public let named: Fact?
    public let neighbours: [AreaRef]
    /// The nearest first, then the rest by how long the walk is.
    public let stations: [Fact]
    public let rent: [Fact]
    public let buy: [Fact]
    public let measured: [Group]
    public let tags: [Row]

    public init(
        area: AreaRef, rankable: Bool, releaseId: String, synthetic: Bool, named: Fact?,
        neighbours: [AreaRef], stations: [Fact], rent: [Fact], buy: [Fact], measured: [Group], tags: [Row]
    ) {
        self.area = area
        self.rankable = rankable
        self.releaseId = releaseId
        self.synthetic = synthetic
        self.named = named
        self.neighbours = neighbours
        self.stations = stations
        self.rent = rent
        self.buy = buy
        self.measured = measured
        self.tags = tags
    }

    /// The order the groups are shown in. Recorded crime is last: it is off unless asked for.
    public static let dimensions: [Dimension] = [
        .stationAccess, .greenWater, .airNoise, .venuesCulture, .schools, .homes, .crime,
    ]

    /// The kinds of home that go with each tenure, in the order a form lists
    /// them. No route says which suit which (web.md section 13, gap 8).
    public static let rented: [Segment] = [.room, .studio, .bed1, .bed2, .bed3, .bed4plus]
    public static let bought: [Segment] = [.flat, .terraced, .semiDetached, .detached]

    /// Lays out what route 6 answered.
    ///
    /// - Parameters:
    ///   - release: The release the answer is of, and whether it is made up.
    ///   - features: The features of the release, from route 11. Every one has
    ///     a row, so that one with no figure is seen to have none. With none
    ///     in hand, the figures the area has are listed as they came.
    ///   - tags: The tags of the release, from route 11.
    public init(_ data: AreaData, release: Meta, features: [Metric], tags: [Tag]) {
        func fact(_ kind: FactKind, _ key: String) -> Fact? {
            data.facts.first { $0.kind == kind && $0.key == key }
        }
        func cost(_ tenure: Tenure, _ segments: [Segment]) -> [Fact] {
            segments.compactMap { fact(.cost, "\(tenure.rawValue).\($0.rawValue)") }
        }

        area = AreaRef(data.area)
        rankable = data.area.rankable
        releaseId = release.releaseId
        synthetic = release.synthetic || data.facts.contains { $0.synthetic }
        named = data.facts.first { $0.kind == .area }
        neighbours = data.neighbours.map(AreaRef.init)

        let walk = Dictionary(
            data.stations.map { ($0.stationId, $0.walkMinutes) }, uniquingKeysWith: { first, _ in first })
        stations = data.facts.filter { $0.kind == .station }.sorted { one, other in
            let nearest = (one.template == .station, other.template == .station)
            if nearest.0 != nearest.1 { return nearest.0 }
            let minutes = (walk[one.key] ?? Int.max, walk[other.key] ?? Int.max)
            if minutes.0 != minutes.1 { return minutes.0 < minutes.1 }
            return one.key < other.key
        }
        rent = cost(.rent, Self.rented)
        buy = cost(.buy, Self.bought)

        if features.isEmpty {
            let rows = data.facts.filter { $0.kind == .feature }
                .map { Row(label: $0.label, fact: $0, kind: .feature, key: $0.key) }
            measured = rows.isEmpty ? [] : [Group(dimension: nil, rows: rows)]
        } else {
            measured = Self.dimensions.compactMap { dimension in
                let rows = features.filter { $0.dimension == dimension }.map { metric in
                    Row(
                        label: metric.label, fact: fact(.feature, metric.featureId.rawValue),
                        kind: .feature, key: metric.featureId.rawValue)
                }
                return rows.isEmpty ? nil : Group(dimension: dimension, rows: rows)
            }
        }
        if tags.isEmpty {
            self.tags = data.facts.filter { $0.kind == .tag }
                .map { Row(label: $0.label, fact: $0, kind: .tag, key: $0.key) }
        } else {
            self.tags = tags.map { tag in
                Row(label: tag.label, fact: fact(.tag, tag.tagId.rawValue), kind: .tag, key: tag.tagId.rawValue)
            }
        }
    }

    /// The name and the borough are the fact's, where there is one: it carries their source.
    public var name: String { named?.slots["name"] ?? area.name }
    public var borough: String { named?.slots["borough"] ?? area.borough }

    /// Every fact the screen lays out, in the order it does, for the list of sources at its foot.
    public var facts: [Fact] {
        var facts: [Fact] = named.map { [$0] } ?? []
        facts += stations
        facts += rent
        facts += buy
        for group in measured { facts += group.rows.compactMap(\.fact) }
        facts += tags.compactMap(\.fact)
        return facts
    }

    /// Every source the screen names, once each, in the order of their names.
    public var sources: [FactSource] {
        SourceLines.sources(of: facts)
    }
}

// MARK: - The rows of each part

extension AreaPage {
    public var stationRows: [FactRow] {
        stations.compactMap { FactRow($0) }
    }

    /// The kind of home names the row. "Rent" would name six of them alike.
    public var rentRows: [FactRow] {
        rent.compactMap { FactRow($0, named: $0.slots["segment"]) }
    }

    public var buyRows: [FactRow] {
        buy.compactMap { FactRow($0, named: $0.slots["segment"]) }
    }

    public var tagRows: [FactRow] {
        tags.compactMap { Self.row($0, noFigure: AreaCopy.Tags.noFigure) }
    }

    public func rows(of group: Group) -> [FactRow] {
        group.rows.compactMap { Self.row($0, noFigure: AreaCopy.Measured.noFigure) }
    }

    private static func row(_ row: Row, noFigure: String) -> FactRow? {
        guard let fact = row.fact else {
            return row.label.isEmpty ? nil : FactRow(noFigure: row.label, says: noFigure, id: row.id)
        }
        return FactRow(fact)
    }

    /// Every piece of text the screen shows that came from the API, for a
    /// test to hold to what the API sent.
    public var said: [String] {
        var rows: [FactRow] = stationRows
        rows += rentRows
        rows += buyRows
        for group in measured { rows += self.rows(of: group) }
        rows += tagRows

        var said: [String] = [name, borough]
        said += neighbours.map(\.name)
        if let named { said += SourceLines.of([named]).map(\.name) }
        for row in rows {
            said.append(row.name)
            said += row.columns.map(\.value)
            said += row.sources.map(\.name)
        }
        said += sources.map(\.name)
        return said
    }
}
