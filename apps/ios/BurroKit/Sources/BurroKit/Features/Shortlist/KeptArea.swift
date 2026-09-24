import Foundation

// What the shortlist keeps of a saved area: its ids and names, the date it
// was saved, the release it came from, and its facts as they were.
//
// Every record here has fixed keys, and none of them can hold anything of a
// search. A fact is kept only if it is of the release alone. A journey, a
// budget and a gap in a score are each of a search: a journey names the place
// a person must reach. They are refused here, by kind, and so is a kind this
// build does not know. A fact's id is not kept. Nor is a rank, a fit, a spec
// or anything typed: no record has a key for one.

/// A source of a fact, as it is kept.
public struct KeptSource: Codable, Hashable, Sendable {
    public let sourceId: String
    public let name: String

    enum CodingKeys: String, CodingKey {
        case sourceId = "source_id"
        case name
    }
}

/// One fact of the release, as it was when the area was saved.
public struct KeptFact: Codable, Hashable, Sendable {
    /// The kinds of fact that are of the release alone. Nothing else is kept.
    public static let kinds: Set<FactKind> = [.area, .feature, .tag, .cost, .station]
    /// The templates that state them.
    public static let templates: Set<TemplateId> = [
        .area, .feature, .featureCrime, .tag, .costRent, .costBuy, .station, .stationNearby,
    ]

    public let kind: FactKind
    public let key: String
    public let label: String
    public let template: TemplateId
    /// The values as the API formatted them.
    public let slots: [String: String]
    public let sources: [KeptSource]
    public let asOf: String
    public let synthetic: Bool

    enum CodingKeys: String, CodingKey {
        case kind
        case key
        case label
        case template
        case slots
        case sources
        case asOf = "as_of"
        case synthetic
    }

    /// What is kept of a fact. `nil` for a fact that is of a search, or of a
    /// kind this build does not know.
    public init?(_ fact: Fact) {
        guard Self.kinds.contains(fact.kind), Self.templates.contains(fact.template) else { return nil }
        kind = fact.kind
        key = fact.key
        label = fact.label
        template = fact.template
        slots = fact.slots
        sources = fact.sources.map { KeptSource(sourceId: $0.sourceId, name: $0.name) }
        asOf = fact.asOf
        synthetic = fact.synthetic
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        kind = try container.decode(FactKind.self, forKey: .kind)
        template = try container.decode(TemplateId.self, forKey: .template)
        // A file that holds anything else was not written by this app.
        guard Self.kinds.contains(kind), Self.templates.contains(template) else {
            throw DecodingError.dataCorruptedError(
                forKey: .kind, in: container, debugDescription: "Not a fact the shortlist keeps.")
        }
        key = try container.decode(String.self, forKey: .key)
        label = try container.decode(String.self, forKey: .label)
        slots = try container.decode([String: String].self, forKey: .slots)
        sources = try container.decode([KeptSource].self, forKey: .sources)
        asOf = try container.decode(String.self, forKey: .asOf)
        synthetic = try container.decode(Bool.self, forKey: .synthetic)
    }

    /// The fact, for the screen to lay out as it lays out any fact. What a
    /// screen never shows of a fact was not kept, and is empty here.
    public func fact(of areaId: String) -> Fact {
        Fact(
            factId: "\(areaId)/\(kind.rawValue)/\(key)", areaId: areaId, kind: kind, key: key, label: label,
            template: template, slots: slots, numbers: [], names: [],
            sources: sources.map { FactSource(sourceId: $0.sourceId, name: $0.name) },
            asOf: asOf, synthetic: synthetic)
    }
}

/// An area next to a saved one: its ids and its names.
public struct KeptNeighbour: Codable, Hashable, Sendable {
    public let areaId: String
    public let slug: String
    public let name: String
    public let borough: String

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case slug
        case name
        case borough
    }

    public init(_ area: AreaRef) {
        areaId = area.areaId
        slug = area.slug
        name = area.name
        borough = area.borough
    }

    public var area: AreaRef {
        AreaRef(areaId: areaId, slug: slug, name: name, borough: borough)
    }
}

/// One row of a saved area's screen: where it goes, and the fact it holds, if it holds one.
public struct KeptRow: Codable, Hashable, Sendable {
    /// The part of the screen a row belongs to.
    public enum Part: String, Codable, Hashable, Sendable, CaseIterable {
        case named
        case station
        case rent
        case buy
        case measured
        case tag
    }

    public let part: Part
    /// What a measured row is about. `nil` for every other part.
    public let dimension: Dimension?
    /// The id of the feature, the tag, the kind of home or the station, as the release lists it.
    public let key: String
    /// The API's name for the feature or the tag. It names a row that has no figure.
    public let label: String
    /// `nil` when the area had no figure.
    public let fact: KeptFact?

    enum CodingKeys: String, CodingKey {
        case part
        case dimension
        case key
        case label
        case fact
    }
}

/// One saved area, as the phone keeps it.
public struct KeptArea: Codable, Hashable, Sendable, Identifiable {
    public let areaId: String
    public let slug: String
    public let name: String
    public let borough: String
    public let savedOn: Date
    /// The release the facts are of.
    public let releaseId: String
    /// True when the release was made up, so that the screen can say so with no connection.
    public let synthetic: Bool
    public let rankable: Bool
    public let neighbours: [KeptNeighbour]
    /// The rows of the area's screen, in the order it shows them.
    public let rows: [KeptRow]

    public var id: String { areaId }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case slug
        case name
        case borough
        case savedOn = "saved_on"
        case releaseId = "release_id"
        case synthetic
        case rankable
        case neighbours
        case rows
    }

    /// What is kept of an area's screen. Anything of a search is left behind.
    public init(_ page: AreaPage, savedOn: Date) {
        func rows(_ part: KeptRow.Part, _ facts: [Fact]) -> [KeptRow] {
            facts.compactMap { fact in
                KeptFact(fact).map {
                    KeptRow(part: part, dimension: nil, key: fact.key, label: fact.label, fact: $0)
                }
            }
        }
        func row(_ part: KeptRow.Part, _ dimension: Dimension?, _ row: AreaPage.Row) -> KeptRow? {
            // A fact that may not be kept is left out whole: it is not turned into "no figure".
            if let fact = row.fact {
                return KeptFact(fact).map {
                    KeptRow(part: part, dimension: dimension, key: row.key, label: row.label, fact: $0)
                }
            }
            return KeptRow(part: part, dimension: dimension, key: row.key, label: row.label, fact: nil)
        }

        areaId = page.area.areaId
        slug = page.area.slug
        name = page.name
        borough = page.borough
        self.savedOn = savedOn
        releaseId = page.releaseId
        synthetic = page.synthetic
        rankable = page.rankable
        neighbours = page.neighbours.map(KeptNeighbour.init)
        var kept: [KeptRow] = rows(.named, page.named.map { [$0] } ?? [])
        kept += rows(.station, page.stations)
        kept += rows(.rent, page.rent)
        kept += rows(.buy, page.buy)
        for group in page.measured {
            kept += group.rows.compactMap { row(.measured, group.dimension, $0) }
        }
        kept += page.tags.compactMap { row(.tag, nil, $0) }
        self.rows = kept
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        slug = try container.decode(String.self, forKey: .slug)
        name = try container.decode(String.self, forKey: .name)
        borough = try container.decode(String.self, forKey: .borough)
        let written = try container.decode(String.self, forKey: .savedOn)
        guard let date = Self.date(written) else {
            throw DecodingError.dataCorruptedError(
                forKey: .savedOn, in: container, debugDescription: "Not a date.")
        }
        savedOn = date
        releaseId = try container.decode(String.self, forKey: .releaseId)
        synthetic = try container.decode(Bool.self, forKey: .synthetic)
        rankable = try container.decode(Bool.self, forKey: .rankable)
        neighbours = try container.decode([KeptNeighbour].self, forKey: .neighbours)
        rows = try container.decode([KeptRow].self, forKey: .rows)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(slug, forKey: .slug)
        try container.encode(name, forKey: .name)
        try container.encode(borough, forKey: .borough)
        // The date is written one way, whatever writes the file.
        try container.encode(Self.written(savedOn), forKey: .savedOn)
        try container.encode(releaseId, forKey: .releaseId)
        try container.encode(synthetic, forKey: .synthetic)
        try container.encode(rankable, forKey: .rankable)
        try container.encode(neighbours, forKey: .neighbours)
        try container.encode(rows, forKey: .rows)
    }

    public var area: AreaRef {
        AreaRef(areaId: areaId, slug: slug, name: name, borough: borough)
    }

    /// The screen of the area, as it was when it was saved.
    public var page: AreaPage {
        func facts(_ part: KeptRow.Part) -> [Fact] {
            rows.filter { $0.part == part }.compactMap { $0.fact?.fact(of: areaId) }
        }
        func row(_ kept: KeptRow, _ kind: FactKind) -> AreaPage.Row {
            AreaPage.Row(label: kept.label, fact: kept.fact?.fact(of: areaId), kind: kind, key: kept.key)
        }
        var groups: [AreaPage.Group] = []
        for kept in rows where kept.part == .measured {
            let next = row(kept, .feature)
            if let last = groups.last, last.dimension == kept.dimension {
                groups[groups.count - 1] = AreaPage.Group(dimension: last.dimension, rows: last.rows + [next])
            } else {
                groups.append(AreaPage.Group(dimension: kept.dimension, rows: [next]))
            }
        }
        return AreaPage(
            area: area, rankable: rankable, releaseId: releaseId, synthetic: synthetic,
            named: facts(.named).first, neighbours: neighbours.map(\.area),
            stations: facts(.station), rent: facts(.rent), buy: facts(.buy), measured: groups,
            tags: rows.filter { $0.part == .tag }.map { row($0, .tag) })
    }

    // MARK: - The date

    private static func written(_ date: Date) -> String {
        date.formatted(Date.ISO8601FormatStyle())
    }

    private static func date(_ written: String) -> Date? {
        try? Date.ISO8601FormatStyle().parse(written)
    }
}

/// Everything the phone keeps of the shortlist's facts: the areas, and the order the person put them in.
public struct KeptShortlist: Codable, Hashable, Sendable {
    /// The shape of the file. A file of another shape is read as an empty one.
    public static let version = 1

    public let version: Int
    /// The ids of the saved areas, in the order the person put them in.
    public let order: [String]
    public let areas: [KeptArea]

    enum CodingKeys: String, CodingKey {
        case version
        case order
        case areas
    }

    public init(order: [String], areas: [KeptArea]) {
        version = Self.version
        self.order = order
        self.areas = areas
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        version = try container.decode(Int.self, forKey: .version)
        guard version == Self.version else {
            throw DecodingError.dataCorruptedError(
                forKey: .version, in: container, debugDescription: "Not a shortlist this build reads.")
        }
        order = try container.decode([String].self, forKey: .order)
        areas = try container.decode([KeptArea].self, forKey: .areas)
    }

    public static let empty = KeptShortlist(order: [], areas: [])
}
