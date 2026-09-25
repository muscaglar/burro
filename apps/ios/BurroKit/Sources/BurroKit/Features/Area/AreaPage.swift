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
    /// A feature of the release, with the fact the area has for it, if it has one.
    public struct Row: Hashable, Sendable, Identifiable {
        /// The API's name for the feature. It names the row when there is no figure.
        public let label: String
        public let fact: Fact?
        /// `feature`.
        public let kind: FactKind
        /// The id of the feature, as the release lists it.
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

    /// One list of the portrait. Which vibe stands in which list, and in
    /// what order, is the API's to say.
    public enum VibeList: String, Codable, Hashable, Sendable, CaseIterable {
        case scales
        case more
        case less
        case others
        case unplaced
    }

    /// One vibe of the portrait: the list the API put it in, how a screen
    /// draws it, and the fact that holds its band, where it is in hand.
    public struct Vibe: Hashable, Sendable, Identifiable {
        public let list: VibeList
        public let shown: VibeShown
        public let fact: Fact?

        public var id: String { shown.id }

        public init(list: VibeList, shown: VibeShown, fact: Fact?) {
            self.list = list
            self.shown = shown
            self.fact = fact
        }
    }

    public let area: AreaRef
    public let rankable: Bool
    /// The release the facts are of.
    public let releaseId: String
    public let synthetic: Bool
    /// True when the release the facts are of is a preview.
    public let preview: Bool
    /// The fact that names the area and its borough. It carries their source.
    public let named: Fact?
    public let neighbours: [AreaRef]
    /// The nearest first, then the rest by how long the walk is.
    public let stations: [Fact]
    public let rent: [Fact]
    public let buy: [Fact]
    public let measured: [Group]
    /// Where the area sits on each vibe, in the order the API lists them.
    public let vibes: [Vibe]

    public init(
        area: AreaRef, rankable: Bool, releaseId: String, synthetic: Bool, preview: Bool, named: Fact?,
        neighbours: [AreaRef], stations: [Fact], rent: [Fact], buy: [Fact], measured: [Group],
        vibes: [Vibe]
    ) {
        self.area = area
        self.rankable = rankable
        self.releaseId = releaseId
        self.synthetic = synthetic
        self.preview = preview
        self.named = named
        self.neighbours = neighbours
        self.stations = stations
        self.rent = rent
        self.buy = buy
        self.measured = measured
        self.vibes = vibes
    }

    /// The order the groups are shown in. What is there comes first, and who lived there
    /// after it. Recorded crime is last: it is off unless asked for.
    public static let dimensions: [Dimension] = [
        .stationAccess, .greenWater, .airNoise, .venuesCulture, .services, .brands, .schools, .homes,
        .residents, .crime,
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
    ///   - tags: The vibes of the release, from route 11. A vibe the release
    ///     does not name is left out: nothing can be said of it.
    ///   - recipes: What the release holds of each recipe, from route 11.
    ///   - guides: What each vibe that is a rough guide says of itself, from
    ///     route 11. It is said under the band of such a vibe.
    public init(
        _ data: AreaData, release: Meta, features: [Metric], tags: [Tag], recipes: [RecipeHeld] = [],
        guides: [RoughGuide] = []
    ) {
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
        preview = release.preview
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
        vibes = Self.lists(of: data.portrait).flatMap { list, marks in
            marks.compactMap { mark -> Vibe? in
                guard let tag = tags.first(where: { $0.tagId == mark.tagId }),
                    let fact = data.facts.first(where: { $0.factId == mark.factId })
                else { return nil }
                // A vibe the API lists as one it cannot place the area on has no band to give.
                let placed = list == .unplaced ? nil : Placed(fact)
                let held = recipes.first { $0.tagId == mark.tagId }
                return Vibe(
                    list: list,
                    shown: Vibes.shown(tag, placed: placed, fact: fact, held: held, guides: guides),
                    fact: fact)
            }
        }
    }

    /// The lists of a portrait, in the order the screen draws them.
    static func lists(of portrait: Portrait) -> [(VibeList, [PortraitMark])] {
        [
            (.scales, portrait.scales), (.more, portrait.more), (.less, portrait.less),
            (.others, portrait.others), (.unplaced, portrait.unplaced),
        ]
    }

    /// The vibes of one list, in the order the API gave them.
    public func vibes(in list: VibeList) -> [Vibe] {
        vibes.filter { $0.list == list }
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
        facts += vibes.compactMap(\.fact)
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

    /// What the publisher of the rents advises, in the API's words, where a rent of the
    /// area is of a wider place. It is said once, over the rows it is said of, however
    /// many kinds of home there are.
    public var rentCaution: String? {
        rent.lazy.compactMap { $0.slots["caution"] }.first { !$0.isEmpty }
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

        /// The name of each source of some lines, and the credit of each that brings one.
        func cited(_ lines: [SourceLine]) -> [String] {
            lines.map(\.name) + lines.compactMap(\.credit)
        }

        var said: [String] = [name, borough]
        if let rentCaution { said.append(rentCaution) }
        said += neighbours.map(\.name)
        if let named { said += cited(SourceLines.of([named])) }
        for vibe in vibes {
            said.append(vibe.shown.name)
            // The two ends are drawn beside the line of five, which an area that cannot be placed has none of.
            if vibe.shown.placed != nil { said += [vibe.shown.low, vibe.shown.high] }
            // What a band rests on is the API's own clause, where the fact holds one.
            if let partly = vibe.fact?.slots["partly"], vibe.shown.restsOn == partly { said.append(partly) }
            said += cited(vibe.shown.sources)
        }
        for row in rows {
            said.append(row.name)
            said += row.columns.map(\.value)
            said += cited(row.sources)
        }
        said += sources.map(\.name)
        return said
    }
}
