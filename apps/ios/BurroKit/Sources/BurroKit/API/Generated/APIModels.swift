// Generated from contracts/openapi.json by apps/ios/scripts/generate.py.
// Never edited by hand: change the source and run `make generate`.
// source-sha256: 7517d49e52c18b16277d656ade942ad20c34bb9cdb4a3a6c89a4860cb3eaa254

import Foundation

/// What these files were generated from, for the test that says when they are stale.
public enum GeneratedFrom {
    /// The SHA-256 of `contracts/openapi.json` when the models were written.
    public static let contractSHA256 = "7517d49e52c18b16277d656ade942ad20c34bb9cdb4a3a6c89a4860cb3eaa254"
    /// The title and the version the contract gives itself.
    public static let contractTitle = "Burro API"
    public static let contractVersion = "2"
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

public struct Applied: Hashable, Sendable, Codable {
    public let group: OpsGroup
    public let index: Int
    public let changed: Bool

    public init(group: OpsGroup, index: Int, changed: Bool) {
        self.group = group
        self.index = index
        self.changed = changed
    }

    enum CodingKeys: String, CodingKey {
        case group
        case index
        case changed
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        group = try container.decode(OpsGroup.self, forKey: .group)
        index = try container.decode(Int.self, forKey: .index)
        changed = try container.decode(Bool.self, forKey: .changed)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(group, forKey: .group)
        try container.encode(index, forKey: .index)
        try container.encode(changed, forKey: .changed)
    }
}

public enum AreaAction: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case exclude
    case only
    case clear
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [AreaAction] = [.exclude, .only, .clear]

    public init(rawValue: String) {
        switch rawValue {
        case "exclude": self = .exclude
        case "only": self = .only
        case "clear": self = .clear
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .exclude: return "exclude"
        case .only: return "only"
        case .clear: return "clear"
        case .unlisted(let value): return value
        }
    }
}

public struct AreaData: Hashable, Sendable, Codable {
    public let area: Neighbourhood
    public let features: [FeatureValue]
    public let tags: [TagValue]
    public let cost: [CostEstimate]
    public let stations: [StationAccess]
    public let neighbours: [AreaSummary]
    public let portrait: Portrait
    public let similar: [Similar]
    public let facts: [Fact]

    public init(
        area: Neighbourhood,
        features: [FeatureValue],
        tags: [TagValue],
        cost: [CostEstimate],
        stations: [StationAccess],
        neighbours: [AreaSummary],
        portrait: Portrait,
        similar: [Similar],
        facts: [Fact]
    ) {
        self.area = area
        self.features = features
        self.tags = tags
        self.cost = cost
        self.stations = stations
        self.neighbours = neighbours
        self.portrait = portrait
        self.similar = similar
        self.facts = facts
    }

    enum CodingKeys: String, CodingKey {
        case area
        case features
        case tags
        case cost
        case stations
        case neighbours
        case portrait
        case similar
        case facts
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        area = try container.decode(Neighbourhood.self, forKey: .area)
        features = try container.decode([FeatureValue].self, forKey: .features)
        tags = try container.decode([TagValue].self, forKey: .tags)
        cost = try container.decode([CostEstimate].self, forKey: .cost)
        stations = try container.decode([StationAccess].self, forKey: .stations)
        neighbours = try container.decode([AreaSummary].self, forKey: .neighbours)
        portrait = try container.decode(Portrait.self, forKey: .portrait)
        similar = try container.decode([Similar].self, forKey: .similar)
        facts = try container.decode([Fact].self, forKey: .facts)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(area, forKey: .area)
        try container.encode(features, forKey: .features)
        try container.encode(tags, forKey: .tags)
        try container.encode(cost, forKey: .cost)
        try container.encode(stations, forKey: .stations)
        try container.encode(neighbours, forKey: .neighbours)
        try container.encode(portrait, forKey: .portrait)
        try container.encode(similar, forKey: .similar)
        try container.encode(facts, forKey: .facts)
    }
}

public struct AreaEdit: Hashable, Sendable, Codable {
    public let action: AreaAction
    public let areaId: String
    public let provenance: EditProvenance

    public init(action: AreaAction, areaId: String, provenance: EditProvenance) {
        self.action = action
        self.areaId = areaId
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case action
        case areaId = "area_id"
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        action = try container.decode(AreaAction.self, forKey: .action)
        areaId = try container.decode(String.self, forKey: .areaId)
        provenance = try container.decode(EditProvenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(action, forKey: .action)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(provenance, forKey: .provenance)
    }
}

public struct AreaRule: Hashable, Sendable, Codable {
    public let areaId: String
    public let rule: AreaRuleKind
    public let provenance: Provenance

    public init(areaId: String, rule: AreaRuleKind, provenance: Provenance) {
        self.areaId = areaId
        self.rule = rule
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case rule
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        rule = try container.decode(AreaRuleKind.self, forKey: .rule)
        provenance = try container.decode(Provenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(rule, forKey: .rule)
        try container.encode(provenance, forKey: .provenance)
    }
}

public enum AreaRuleKind: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case exclude
    case only
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [AreaRuleKind] = [.exclude, .only]

    public init(rawValue: String) {
        switch rawValue {
        case "exclude": self = .exclude
        case "only": self = .only
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .exclude: return "exclude"
        case .only: return "only"
        case .unlisted(let value): return value
        }
    }
}

public struct AreaSummary: Hashable, Sendable, Codable {
    public let areaId: String
    public let slug: String
    public let name: String
    public let borough: String
    public let centroid: LonLat
    public let rankable: Bool
    public let named: Named?

    public init(
        areaId: String,
        slug: String,
        name: String,
        borough: String,
        centroid: LonLat,
        rankable: Bool,
        named: Named?
    ) {
        self.areaId = areaId
        self.slug = slug
        self.name = name
        self.borough = borough
        self.centroid = centroid
        self.rankable = rankable
        self.named = named
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case slug
        case name
        case borough
        case centroid
        case rankable
        case named
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        slug = try container.decode(String.self, forKey: .slug)
        name = try container.decode(String.self, forKey: .name)
        borough = try container.decode(String.self, forKey: .borough)
        centroid = try container.decode(LonLat.self, forKey: .centroid)
        rankable = try container.decode(Bool.self, forKey: .rankable)
        named = try container.decodeIfPresent(Named.self, forKey: .named)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(slug, forKey: .slug)
        try container.encode(name, forKey: .name)
        try container.encode(borough, forKey: .borough)
        try container.encode(centroid, forKey: .centroid)
        try container.encode(rankable, forKey: .rankable)
        try container.encode(named, forKey: .named)
    }
}

public struct AreasData: Hashable, Sendable, Codable {
    public let areas: [AreaSummary]
    public let bands: [VibeBands]

    public init(areas: [AreaSummary], bands: [VibeBands]) {
        self.areas = areas
        self.bands = bands
    }

    enum CodingKeys: String, CodingKey {
        case areas
        case bands
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areas = try container.decode([AreaSummary].self, forKey: .areas)
        bands = try container.decode([VibeBands].self, forKey: .bands)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areas, forKey: .areas)
        try container.encode(bands, forKey: .bands)
    }
}

/// What was chosen for an edit because the text did not say.
public struct Assumption: Hashable, Sendable, Codable {
    public let code: AssumptionCode
    public let group: OpsGroup
    public let index: Int
    public let word: String

    public init(
        code: AssumptionCode,
        group: OpsGroup,
        index: Int,
        word: String = ""
    ) {
        self.code = code
        self.group = group
        self.index = index
        self.word = word
    }

    enum CodingKeys: String, CodingKey {
        case code
        case group
        case index
        case word
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        code = try container.decode(AssumptionCode.self, forKey: .code)
        group = try container.decode(OpsGroup.self, forKey: .group)
        index = try container.decode(Int.self, forKey: .index)
        word = try container.decodeIfPresent(String.self, forKey: .word) ?? ""
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(code, forKey: .code)
        try container.encode(group, forKey: .group)
        try container.encode(index, forKey: .index)
        try container.encode(word, forKey: .word)
    }
}

public enum AssumptionCode: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case tenure
    case segment
    case strictness
    case mode
    case maxMinutes
    case direction
    case weight
    case word
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [AssumptionCode] = [.tenure, .segment, .strictness, .mode, .maxMinutes, .direction, .weight, .word]

    public init(rawValue: String) {
        switch rawValue {
        case "tenure": self = .tenure
        case "segment": self = .segment
        case "strictness": self = .strictness
        case "mode": self = .mode
        case "max_minutes": self = .maxMinutes
        case "direction": self = .direction
        case "weight": self = .weight
        case "word": self = .word
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .tenure: return "tenure"
        case .segment: return "segment"
        case .strictness: return "strictness"
        case .mode: return "mode"
        case .maxMinutes: return "max_minutes"
        case .direction: return "direction"
        case .weight: return "weight"
        case .word: return "word"
        case .unlisted(let value): return value
        }
    }
}

/// Where one area sits on one vibe: a band, one of five, and the bands it spans.
///
/// All three are `null` for an area that cannot be placed. It is never drawn
/// in the middle. The score a vibe is ranked on is not here, and is never shown.
public struct BandMark: Hashable, Sendable, Codable {
    public let areaId: String
    public let band: Int?
    public let spreadLow: Int?
    public let spreadHigh: Int?

    public init(
        areaId: String,
        band: Int?,
        spreadLow: Int?,
        spreadHigh: Int?
    ) {
        self.areaId = areaId
        self.band = band
        self.spreadLow = spreadLow
        self.spreadHigh = spreadHigh
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case band
        case spreadLow = "spread_low"
        case spreadHigh = "spread_high"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        band = try container.decodeIfPresent(Int.self, forKey: .band)
        spreadLow = try container.decodeIfPresent(Int.self, forKey: .spreadLow)
        spreadHigh = try container.decodeIfPresent(Int.self, forKey: .spreadHigh)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(band, forKey: .band)
        try container.encode(spreadLow, forKey: .spreadLow)
        try container.encode(spreadHigh, forKey: .spreadHigh)
    }
}

public struct Budget: Hashable, Sendable, Codable {
    public let amount: Int?
    public let segment: Segment
    public let strictness: Strictness
    public let weight: Double
    public let provenance: Provenance

    public init(
        amount: Int?,
        segment: Segment,
        strictness: Strictness,
        weight: Double,
        provenance: Provenance
    ) {
        self.amount = amount
        self.segment = segment
        self.strictness = strictness
        self.weight = weight
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case amount
        case segment
        case strictness
        case weight
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        amount = try container.decodeIfPresent(Int.self, forKey: .amount)
        segment = try container.decode(Segment.self, forKey: .segment)
        strictness = try container.decode(Strictness.self, forKey: .strictness)
        weight = try container.decode(Double.self, forKey: .weight)
        provenance = try container.decode(Provenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(amount, forKey: .amount)
        try container.encode(segment, forKey: .segment)
        try container.encode(strictness, forKey: .strictness)
        try container.encode(weight, forKey: .weight)
        try container.encode(provenance, forKey: .provenance)
    }
}

public enum BudgetAction: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case set
    case clear
    case nudge
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [BudgetAction] = [.set, .clear, .nudge]

    public init(rawValue: String) {
        switch rawValue {
        case "set": self = .set
        case "clear": self = .clear
        case "nudge": self = .nudge
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .set: return "set"
        case .clear: return "clear"
        case .nudge: return "nudge"
        case .unlisted(let value): return value
        }
    }
}

public struct BudgetEdit: Hashable, Sendable, Codable {
    public let action: BudgetAction
    public let tenure: TenureChoice
    public let amount: Int
    public let segment: SegmentChoice
    public let strictness: StrictnessChoice
    public let step: Step
    public let provenance: EditProvenance

    public init(
        action: BudgetAction,
        tenure: TenureChoice,
        amount: Int,
        segment: SegmentChoice,
        strictness: StrictnessChoice,
        step: Step,
        provenance: EditProvenance
    ) {
        self.action = action
        self.tenure = tenure
        self.amount = amount
        self.segment = segment
        self.strictness = strictness
        self.step = step
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case action
        case tenure
        case amount
        case segment
        case strictness
        case step
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        action = try container.decode(BudgetAction.self, forKey: .action)
        tenure = try container.decode(TenureChoice.self, forKey: .tenure)
        amount = try container.decode(Int.self, forKey: .amount)
        segment = try container.decode(SegmentChoice.self, forKey: .segment)
        strictness = try container.decode(StrictnessChoice.self, forKey: .strictness)
        step = try container.decode(Step.self, forKey: .step)
        provenance = try container.decode(EditProvenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(action, forKey: .action)
        try container.encode(tenure, forKey: .tenure)
        try container.encode(amount, forKey: .amount)
        try container.encode(segment, forKey: .segment)
        try container.encode(strictness, forKey: .strictness)
        try container.encode(step, forKey: .step)
        try container.encode(provenance, forKey: .provenance)
    }
}

public struct BudgetFit: Hashable, Sendable, Codable {
    public let upperQuartile: Int?
    public let margin: Int
    public let utility: Double
    public let confidence: Confidence
    public let asOf: String

    public init(
        upperQuartile: Int?,
        margin: Int,
        utility: Double,
        confidence: Confidence,
        asOf: String
    ) {
        self.upperQuartile = upperQuartile
        self.margin = margin
        self.utility = utility
        self.confidence = confidence
        self.asOf = asOf
    }

    enum CodingKeys: String, CodingKey {
        case upperQuartile = "upper_quartile"
        case margin
        case utility
        case confidence
        case asOf = "as_of"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        upperQuartile = try container.decodeIfPresent(Int.self, forKey: .upperQuartile)
        margin = try container.decode(Int.self, forKey: .margin)
        utility = try container.decode(Double.self, forKey: .utility)
        confidence = try container.decode(Confidence.self, forKey: .confidence)
        asOf = try container.decode(String.self, forKey: .asOf)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(upperQuartile, forKey: .upperQuartile)
        try container.encode(margin, forKey: .margin)
        try container.encode(utility, forKey: .utility)
        try container.encode(confidence, forKey: .confidence)
        try container.encode(asOf, forKey: .asOf)
    }
}

/// The heading of each column, in the order they are printed.
public struct CensusColumns: Hashable, Sendable, Codable {
    public let label: String
    public let share: String
    public let count: String
    public let city: String

    public init(
        label: String,
        share: String,
        count: String,
        city: String
    ) {
        self.label = label
        self.share = share
        self.count = count
        self.city = city
    }

    enum CodingKeys: String, CodingKey {
        case label
        case share
        case count
        case city
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        label = try container.decode(String.self, forKey: .label)
        share = try container.decode(String.self, forKey: .share)
        count = try container.decode(String.self, forKey: .count)
        city = try container.decode(String.self, forKey: .city)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(label, forKey: .label)
        try container.encode(share, forKey: .share)
        try container.encode(count, forKey: .count)
        try container.encode(city, forKey: .city)
    }
}

/// What a table counts. It is no `FeatureId` and no `TagId`: no spec or edit can name it.
public enum CensusKind: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case age
    case households
    case countryOfBirth
    case ethnicGroup
    case religion
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [CensusKind] = [.age, .households, .countryOfBirth, .ethnicGroup, .religion]

    public init(rawValue: String) {
        switch rawValue {
        case "age": self = .age
        case "households": self = .households
        case "country_of_birth": self = .countryOfBirth
        case "ethnic_group": self = .ethnicGroup
        case "religion": self = .religion
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .age: return "age"
        case .households: return "households"
        case .countryOfBirth: return "country_of_birth"
        case .ethnicGroup: return "ethnic_group"
        case .religion: return "religion"
        case .unlisted(let value): return value
        }
    }
}

/// Why an area has no figure for a table. Nothing is filled in for either.
public enum CensusLeftOut: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case tooFew
    case notHeld
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [CensusLeftOut] = [.tooFew, .notHeld]

    public init(rawValue: String) {
        switch rawValue {
        case "too_few": self = .tooFew
        case "not_held": self = .notHeld
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .tooFew: return "too_few"
        case .notHeld: return "not_held"
        case .unlisted(let value): return value
        }
    }
}

/// What the closed block of an area's page says. It holds no figure and names no area.
public struct CensusOffer: Hashable, Sendable, Codable {
    public let available: Bool
    public let heading: String
    public let intro: String

    public init(available: Bool, heading: String, intro: String) {
        self.available = available
        self.heading = heading
        self.intro = intro
    }

    enum CodingKeys: String, CodingKey {
        case available
        case heading
        case intro
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        available = try container.decode(Bool.self, forKey: .available)
        heading = try container.decode(String.self, forKey: .heading)
        intro = try container.decode(String.self, forKey: .intro)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(available, forKey: .available)
        try container.encode(heading, forKey: .heading)
        try container.encode(intro, forKey: .intro)
    }
}

/// The census of one area, as its page shows it. Every word but a button's is here.
public struct CensusPanel: Hashable, Sendable, Codable {
    public let areaId: String
    public let heading: String
    public let dateLine: String
    public let notes: [String]
    public let city: String
    public let outputAreas: Int
    public let tables: [CensusPanelTable]
    public let sourceLine: String
    public let derivationLine: String
    public let licenceLine: String

    public init(
        areaId: String,
        heading: String,
        dateLine: String,
        notes: [String],
        city: String,
        outputAreas: Int,
        tables: [CensusPanelTable],
        sourceLine: String,
        derivationLine: String,
        licenceLine: String
    ) {
        self.areaId = areaId
        self.heading = heading
        self.dateLine = dateLine
        self.notes = notes
        self.city = city
        self.outputAreas = outputAreas
        self.tables = tables
        self.sourceLine = sourceLine
        self.derivationLine = derivationLine
        self.licenceLine = licenceLine
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case heading
        case dateLine = "date_line"
        case notes
        case city
        case outputAreas = "output_areas"
        case tables
        case sourceLine = "source_line"
        case derivationLine = "derivation_line"
        case licenceLine = "licence_line"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        heading = try container.decode(String.self, forKey: .heading)
        dateLine = try container.decode(String.self, forKey: .dateLine)
        notes = try container.decode([String].self, forKey: .notes)
        city = try container.decode(String.self, forKey: .city)
        outputAreas = try container.decode(Int.self, forKey: .outputAreas)
        tables = try container.decode([CensusPanelTable].self, forKey: .tables)
        sourceLine = try container.decode(String.self, forKey: .sourceLine)
        derivationLine = try container.decode(String.self, forKey: .derivationLine)
        licenceLine = try container.decode(String.self, forKey: .licenceLine)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(heading, forKey: .heading)
        try container.encode(dateLine, forKey: .dateLine)
        try container.encode(notes, forKey: .notes)
        try container.encode(city, forKey: .city)
        try container.encode(outputAreas, forKey: .outputAreas)
        try container.encode(tables, forKey: .tables)
        try container.encode(sourceLine, forKey: .sourceLine)
        try container.encode(derivationLine, forKey: .derivationLine)
        try container.encode(licenceLine, forKey: .licenceLine)
    }
}

/// One row as it is printed: the area's figure, and the whole city's beside it.
///
/// `share` and `city_share` are words. `percent` and `city_percent` are the
/// same shares as whole numbers, for the picture alone, and are `None`
/// where the share is under 1 in 100. `count` is as it is printed, and is
/// `None` where the share is under 1 in 100: a small count is never given.
public struct CensusPanelRow: Hashable, Sendable, Codable {
    public let code: String
    public let heading: String
    public let label: String
    public let depth: Int
    public let share: String
    public let percent: Int?
    public let count: String?
    public let cityShare: String
    public let cityPercent: Int?

    public init(
        code: String,
        heading: String,
        label: String,
        depth: Int,
        share: String,
        percent: Int?,
        count: String?,
        cityShare: String,
        cityPercent: Int?
    ) {
        self.code = code
        self.heading = heading
        self.label = label
        self.depth = depth
        self.share = share
        self.percent = percent
        self.count = count
        self.cityShare = cityShare
        self.cityPercent = cityPercent
    }

    enum CodingKeys: String, CodingKey {
        case code
        case heading
        case label
        case depth
        case share
        case percent
        case count
        case cityShare = "city_share"
        case cityPercent = "city_percent"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        code = try container.decode(String.self, forKey: .code)
        heading = try container.decode(String.self, forKey: .heading)
        label = try container.decode(String.self, forKey: .label)
        depth = try container.decode(Int.self, forKey: .depth)
        share = try container.decode(String.self, forKey: .share)
        percent = try container.decodeIfPresent(Int.self, forKey: .percent)
        count = try container.decodeIfPresent(String.self, forKey: .count)
        cityShare = try container.decode(String.self, forKey: .cityShare)
        cityPercent = try container.decodeIfPresent(Int.self, forKey: .cityPercent)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(code, forKey: .code)
        try container.encode(heading, forKey: .heading)
        try container.encode(label, forKey: .label)
        try container.encode(depth, forKey: .depth)
        try container.encode(share, forKey: .share)
        try container.encode(percent, forKey: .percent)
        try container.encode(count, forKey: .count)
        try container.encode(cityShare, forKey: .cityShare)
        try container.encode(cityPercent, forKey: .cityPercent)
    }
}

public struct CensusPanelTable: Hashable, Sendable, Codable {
    public let tableCode: String
    public let kind: CensusKind
    public let title: String
    public let caption: String
    public let definition: String
    public let shownOnly: String?
    public let note: String?
    public let columns: CensusColumns
    public let reason: CensusLeftOut?
    public let leftOut: String?
    public let rows: [CensusPanelRow]
    public let sourceId: String
    public let sourceUrl: String
    public let sourceLabel: String

    public init(
        tableCode: String,
        kind: CensusKind,
        title: String,
        caption: String,
        definition: String,
        shownOnly: String?,
        note: String?,
        columns: CensusColumns,
        reason: CensusLeftOut?,
        leftOut: String?,
        rows: [CensusPanelRow],
        sourceId: String,
        sourceUrl: String,
        sourceLabel: String
    ) {
        self.tableCode = tableCode
        self.kind = kind
        self.title = title
        self.caption = caption
        self.definition = definition
        self.shownOnly = shownOnly
        self.note = note
        self.columns = columns
        self.reason = reason
        self.leftOut = leftOut
        self.rows = rows
        self.sourceId = sourceId
        self.sourceUrl = sourceUrl
        self.sourceLabel = sourceLabel
    }

    enum CodingKeys: String, CodingKey {
        case tableCode = "table_code"
        case kind
        case title
        case caption
        case definition
        case shownOnly = "shown_only"
        case note
        case columns
        case reason
        case leftOut = "left_out"
        case rows
        case sourceId = "source_id"
        case sourceUrl = "source_url"
        case sourceLabel = "source_label"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tableCode = try container.decode(String.self, forKey: .tableCode)
        kind = try container.decode(CensusKind.self, forKey: .kind)
        title = try container.decode(String.self, forKey: .title)
        caption = try container.decode(String.self, forKey: .caption)
        definition = try container.decode(String.self, forKey: .definition)
        shownOnly = try container.decodeIfPresent(String.self, forKey: .shownOnly)
        note = try container.decodeIfPresent(String.self, forKey: .note)
        columns = try container.decode(CensusColumns.self, forKey: .columns)
        reason = try container.decodeIfPresent(CensusLeftOut.self, forKey: .reason)
        leftOut = try container.decodeIfPresent(String.self, forKey: .leftOut)
        rows = try container.decode([CensusPanelRow].self, forKey: .rows)
        sourceId = try container.decode(String.self, forKey: .sourceId)
        sourceUrl = try container.decode(String.self, forKey: .sourceUrl)
        sourceLabel = try container.decode(String.self, forKey: .sourceLabel)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tableCode, forKey: .tableCode)
        try container.encode(kind, forKey: .kind)
        try container.encode(title, forKey: .title)
        try container.encode(caption, forKey: .caption)
        try container.encode(definition, forKey: .definition)
        try container.encode(shownOnly, forKey: .shownOnly)
        try container.encode(note, forKey: .note)
        try container.encode(columns, forKey: .columns)
        try container.encode(reason, forKey: .reason)
        try container.encode(leftOut, forKey: .leftOut)
        try container.encode(rows, forKey: .rows)
        try container.encode(sourceId, forKey: .sourceId)
        try container.encode(sourceUrl, forKey: .sourceUrl)
        try container.encode(sourceLabel, forKey: .sourceLabel)
    }
}

public struct CharacterMark: Hashable, Sendable, Codable {
    public let areaId: String
    public let band: Int?
    public let spreadLow: Int?
    public let spreadHigh: Int?
    public let factId: String

    public init(
        areaId: String,
        band: Int?,
        spreadLow: Int?,
        spreadHigh: Int?,
        factId: String
    ) {
        self.areaId = areaId
        self.band = band
        self.spreadLow = spreadLow
        self.spreadHigh = spreadHigh
        self.factId = factId
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case band
        case spreadLow = "spread_low"
        case spreadHigh = "spread_high"
        case factId = "fact_id"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        band = try container.decodeIfPresent(Int.self, forKey: .band)
        spreadLow = try container.decodeIfPresent(Int.self, forKey: .spreadLow)
        spreadHigh = try container.decodeIfPresent(Int.self, forKey: .spreadHigh)
        factId = try container.decode(String.self, forKey: .factId)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(band, forKey: .band)
        try container.encode(spreadLow, forKey: .spreadLow)
        try container.encode(spreadHigh, forKey: .spreadHigh)
        try container.encode(factId, forKey: .factId)
    }
}

public struct CharacterRow: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let marks: [CharacterMark]

    public init(tagId: TagId, marks: [CharacterMark]) {
        self.tagId = tagId
        self.marks = marks
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case marks
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        marks = try container.decode([CharacterMark].self, forKey: .marks)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(marks, forKey: .marks)
    }
}

public enum Choice: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case slowest
    case mean
    case typical
    case justMissed
    case nothing
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Choice] = [.slowest, .mean, .typical, .justMissed, .nothing]

    public init(rawValue: String) {
        switch rawValue {
        case "slowest": self = .slowest
        case "mean": self = .mean
        case "typical": self = .typical
        case "just_missed": self = .justMissed
        case "none": self = .nothing
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .slowest: return "slowest"
        case .mean: return "mean"
        case .typical: return "typical"
        case .justMissed: return "just_missed"
        case .nothing: return "none"
        case .unlisted(let value): return value
        }
    }
}

/// An edit whose place or area could not be settled, and what to offer instead.
public struct Clarify: Hashable, Sendable, Codable {
    public let group: OpsGroup
    public let index: Int
    public let options: [ClarifyOption]

    public init(group: OpsGroup, index: Int, options: [ClarifyOption]) {
        self.group = group
        self.index = index
        self.options = options
    }

    enum CodingKeys: String, CodingKey {
        case group
        case index
        case options
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        group = try container.decode(OpsGroup.self, forKey: .group)
        index = try container.decode(Int.self, forKey: .index)
        options = try container.decode([ClarifyOption].self, forKey: .options)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(group, forKey: .group)
        try container.encode(index, forKey: .index)
        try container.encode(options, forKey: .options)
    }
}

public struct ClarifyOption: Hashable, Sendable, Codable {
    public let id: String
    public let name: String
    public let kind: OptionKind

    public init(id: String, name: String, kind: OptionKind) {
        self.id = id
        self.name = name
        self.kind = kind
    }

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case kind
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        kind = try container.decode(OptionKind.self, forKey: .kind)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(name, forKey: .name)
        try container.encode(kind, forKey: .kind)
    }
}

public enum Combine: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case slowest
    case mean
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Combine] = [.slowest, .mean]

    public init(rawValue: String) {
        switch rawValue {
        case "slowest": self = .slowest
        case "mean": self = .mean
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .slowest: return "slowest"
        case .mean: return "mean"
        case .unlisted(let value): return value
        }
    }
}

public struct Commute: Hashable, Sendable, Codable {
    public let placeId: String
    public let mode: Mode
    public let maxMinutes: Int
    public let strictness: Strictness
    public let provenance: Provenance

    public init(
        placeId: String,
        mode: Mode,
        maxMinutes: Int,
        strictness: Strictness,
        provenance: Provenance
    ) {
        self.placeId = placeId
        self.mode = mode
        self.maxMinutes = maxMinutes
        self.strictness = strictness
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case placeId = "place_id"
        case mode
        case maxMinutes = "max_minutes"
        case strictness
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        placeId = try container.decode(String.self, forKey: .placeId)
        mode = try container.decode(Mode.self, forKey: .mode)
        maxMinutes = try container.decode(Int.self, forKey: .maxMinutes)
        strictness = try container.decode(Strictness.self, forKey: .strictness)
        provenance = try container.decode(Provenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(placeId, forKey: .placeId)
        try container.encode(mode, forKey: .mode)
        try container.encode(maxMinutes, forKey: .maxMinutes)
        try container.encode(strictness, forKey: .strictness)
        try container.encode(provenance, forKey: .provenance)
    }
}

public enum CommuteAction: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case add
    case update
    case remove
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [CommuteAction] = [.add, .update, .remove]

    public init(rawValue: String) {
        switch rawValue {
        case "add": self = .add
        case "update": self = .update
        case "remove": self = .remove
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .add: return "add"
        case .update: return "update"
        case .remove: return "remove"
        case .unlisted(let value): return value
        }
    }
}

public struct CommuteEdit: Hashable, Sendable, Codable {
    public let action: CommuteAction
    public let placeId: String
    public let mode: ModeChoice
    public let maxMinutes: Int
    public let strictness: StrictnessChoice
    public let step: Step
    public let provenance: EditProvenance

    public init(
        action: CommuteAction,
        placeId: String,
        mode: ModeChoice,
        maxMinutes: Int,
        strictness: StrictnessChoice,
        step: Step,
        provenance: EditProvenance
    ) {
        self.action = action
        self.placeId = placeId
        self.mode = mode
        self.maxMinutes = maxMinutes
        self.strictness = strictness
        self.step = step
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case action
        case placeId = "place_id"
        case mode
        case maxMinutes = "max_minutes"
        case strictness
        case step
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        action = try container.decode(CommuteAction.self, forKey: .action)
        placeId = try container.decode(String.self, forKey: .placeId)
        mode = try container.decode(ModeChoice.self, forKey: .mode)
        maxMinutes = try container.decode(Int.self, forKey: .maxMinutes)
        strictness = try container.decode(StrictnessChoice.self, forKey: .strictness)
        step = try container.decode(Step.self, forKey: .step)
        provenance = try container.decode(EditProvenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(action, forKey: .action)
        try container.encode(placeId, forKey: .placeId)
        try container.encode(mode, forKey: .mode)
        try container.encode(maxMinutes, forKey: .maxMinutes)
        try container.encode(strictness, forKey: .strictness)
        try container.encode(step, forKey: .step)
        try container.encode(provenance, forKey: .provenance)
    }
}

public struct CommuteLeg: Hashable, Sendable, Codable {
    public let placeId: String
    public let mode: Mode
    public let status: TravelStatus
    public let minutes: Int?
    public let minutesTypical: Int?
    public let minutesJustMissed: Int?
    public let utility: Double?
    public let estimate: JourneyBand?

    public init(
        placeId: String,
        mode: Mode,
        status: TravelStatus,
        minutes: Int?,
        minutesTypical: Int?,
        minutesJustMissed: Int?,
        utility: Double?,
        estimate: JourneyBand? = nil
    ) {
        self.placeId = placeId
        self.mode = mode
        self.status = status
        self.minutes = minutes
        self.minutesTypical = minutesTypical
        self.minutesJustMissed = minutesJustMissed
        self.utility = utility
        self.estimate = estimate
    }

    enum CodingKeys: String, CodingKey {
        case placeId = "place_id"
        case mode
        case status
        case minutes
        case minutesTypical = "minutes_typical"
        case minutesJustMissed = "minutes_just_missed"
        case utility
        case estimate
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        placeId = try container.decode(String.self, forKey: .placeId)
        mode = try container.decode(Mode.self, forKey: .mode)
        status = try container.decode(TravelStatus.self, forKey: .status)
        minutes = try container.decodeIfPresent(Int.self, forKey: .minutes)
        minutesTypical = try container.decodeIfPresent(Int.self, forKey: .minutesTypical)
        minutesJustMissed = try container.decodeIfPresent(Int.self, forKey: .minutesJustMissed)
        utility = try container.decodeIfPresent(Double.self, forKey: .utility)
        estimate = try container.decodeIfPresent(JourneyBand.self, forKey: .estimate)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(placeId, forKey: .placeId)
        try container.encode(mode, forKey: .mode)
        try container.encode(status, forKey: .status)
        try container.encode(minutes, forKey: .minutes)
        try container.encode(minutesTypical, forKey: .minutesTypical)
        try container.encode(minutesJustMissed, forKey: .minutesJustMissed)
        try container.encode(utility, forKey: .utility)
        try container.encode(estimate, forKey: .estimate)
    }
}

public struct CompareBody: Hashable, Sendable, Codable {
    public let areaIds: [String]
    public let spec: PreferenceSpec

    public init(areaIds: [String], spec: PreferenceSpec) {
        self.areaIds = areaIds
        self.spec = spec
    }

    enum CodingKeys: String, CodingKey {
        case areaIds = "area_ids"
        case spec
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaIds = try container.decode([String].self, forKey: .areaIds)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaIds, forKey: .areaIds)
        try container.encode(spec, forKey: .spec)
    }
}

public struct CompareCell: Hashable, Sendable, Codable {
    public let areaId: String
    public let value: Double?
    public let percentile: Double?
    public let utility: Double?
    public let contribution: Double?
    public let factId: String?
    public let estimate: JourneyBand?

    public init(
        areaId: String,
        value: Double?,
        percentile: Double?,
        utility: Double?,
        contribution: Double?,
        factId: String?,
        estimate: JourneyBand? = nil
    ) {
        self.areaId = areaId
        self.value = value
        self.percentile = percentile
        self.utility = utility
        self.contribution = contribution
        self.factId = factId
        self.estimate = estimate
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case value
        case percentile
        case utility
        case contribution
        case factId = "fact_id"
        case estimate
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        value = try container.decodeIfPresent(Double.self, forKey: .value)
        percentile = try container.decodeIfPresent(Double.self, forKey: .percentile)
        utility = try container.decodeIfPresent(Double.self, forKey: .utility)
        contribution = try container.decodeIfPresent(Double.self, forKey: .contribution)
        factId = try container.decodeIfPresent(String.self, forKey: .factId)
        estimate = try container.decodeIfPresent(JourneyBand.self, forKey: .estimate)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(value, forKey: .value)
        try container.encode(percentile, forKey: .percentile)
        try container.encode(utility, forKey: .utility)
        try container.encode(contribution, forKey: .contribution)
        try container.encode(factId, forKey: .factId)
        try container.encode(estimate, forKey: .estimate)
    }
}

public struct CompareData: Hashable, Sendable, Codable {
    public let areas: [ComparedArea]
    public let character: [CharacterRow]
    public let rows: [CompareRow]
    public let facts: [Fact]

    public init(
        areas: [ComparedArea],
        character: [CharacterRow],
        rows: [CompareRow],
        facts: [Fact]
    ) {
        self.areas = areas
        self.character = character
        self.rows = rows
        self.facts = facts
    }

    enum CodingKeys: String, CodingKey {
        case areas
        case character
        case rows
        case facts
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areas = try container.decode([ComparedArea].self, forKey: .areas)
        character = try container.decode([CharacterRow].self, forKey: .character)
        rows = try container.decode([CompareRow].self, forKey: .rows)
        facts = try container.decode([Fact].self, forKey: .facts)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areas, forKey: .areas)
        try container.encode(character, forKey: .character)
        try container.encode(rows, forKey: .rows)
        try container.encode(facts, forKey: .facts)
    }
}

/// One thing that counts, across the areas. The journeys have a row each.
///
/// Every cell of a journey's row is to the same place. The row is named as
/// core keys a journey, `commute.<place_id>.<mode>`, and carries the weight
/// of the journeys, which count as one thing between them.
public struct CompareRow: Hashable, Sendable, Codable {
    public let component: String
    public let label: String
    public let weight: Double
    public let place: NamedPlace?
    public let cells: [CompareCell]

    public init(
        component: String,
        label: String,
        weight: Double,
        place: NamedPlace?,
        cells: [CompareCell]
    ) {
        self.component = component
        self.label = label
        self.weight = weight
        self.place = place
        self.cells = cells
    }

    enum CodingKeys: String, CodingKey {
        case component
        case label
        case weight
        case place
        case cells
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        component = try container.decode(String.self, forKey: .component)
        label = try container.decode(String.self, forKey: .label)
        weight = try container.decode(Double.self, forKey: .weight)
        place = try container.decodeIfPresent(NamedPlace.self, forKey: .place)
        cells = try container.decode([CompareCell].self, forKey: .cells)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(component, forKey: .component)
        try container.encode(label, forKey: .label)
        try container.encode(weight, forKey: .weight)
        try container.encode(place, forKey: .place)
        try container.encode(cells, forKey: .cells)
    }
}

/// `ranked`, or the reason the area was filtered or left unranked.
///
/// One enum and not a union of three, so that a generated client gets one
/// type. A test holds it to `FilterReason` and `UnrankedReason`.
public enum CompareStatus: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case ranked
    case excluded
    case notSelected
    case overBudget
    case commuteCap
    case commuteLikelyBeyond
    case notRankable
    case insufficientData
    case characterUnknown
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [CompareStatus] = [.ranked, .excluded, .notSelected, .overBudget, .commuteCap, .commuteLikelyBeyond, .notRankable, .insufficientData, .characterUnknown]

    public init(rawValue: String) {
        switch rawValue {
        case "ranked": self = .ranked
        case "excluded": self = .excluded
        case "not_selected": self = .notSelected
        case "over_budget": self = .overBudget
        case "commute_cap": self = .commuteCap
        case "commute_likely_beyond": self = .commuteLikelyBeyond
        case "not_rankable": self = .notRankable
        case "insufficient_data": self = .insufficientData
        case "character_unknown": self = .characterUnknown
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .ranked: return "ranked"
        case .excluded: return "excluded"
        case .notSelected: return "not_selected"
        case .overBudget: return "over_budget"
        case .commuteCap: return "commute_cap"
        case .commuteLikelyBeyond: return "commute_likely_beyond"
        case .notRankable: return "not_rankable"
        case .insufficientData: return "insufficient_data"
        case .characterUnknown: return "character_unknown"
        case .unlisted(let value): return value
        }
    }
}

public struct ComparedArea: Hashable, Sendable, Codable {
    public let areaId: String
    public let name: String
    public let status: CompareStatus
    public let counted: Int
    public let present: Int

    public init(
        areaId: String,
        name: String,
        status: CompareStatus,
        counted: Int,
        present: Int
    ) {
        self.areaId = areaId
        self.name = name
        self.status = status
        self.counted = counted
        self.present = present
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case name
        case status
        case counted
        case present
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        name = try container.decode(String.self, forKey: .name)
        status = try container.decode(CompareStatus.self, forKey: .status)
        counted = try container.decode(Int.self, forKey: .counted)
        present = try container.decode(Int.self, forKey: .present)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(name, forKey: .name)
        try container.encode(status, forKey: .status)
        try container.encode(counted, forKey: .counted)
        try container.encode(present, forKey: .present)
    }
}

/// What a cost rests on. The first three are of a range Burro worked out.
public enum Confidence: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case high
    case medium
    case low
    case unstated
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Confidence] = [.high, .medium, .low, .unstated]

    public init(rawValue: String) {
        switch rawValue {
        case "high": self = .high
        case "medium": self = .medium
        case "low": self = .low
        case "unstated": self = .unstated
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .high: return "high"
        case .medium: return "medium"
        case .low: return "low"
        case .unstated: return "unstated"
        case .unlisted(let value): return value
        }
    }
}

public struct Contribution: Hashable, Sendable, Codable {
    public let component: String
    public let present: Bool
    public let weight: Double
    public let share: Double
    public let utility: Double?
    public let contribution: Double
    public let loss: Double
    public let factIds: [String]

    public init(
        component: String,
        present: Bool,
        weight: Double,
        share: Double,
        utility: Double?,
        contribution: Double,
        loss: Double,
        factIds: [String]
    ) {
        self.component = component
        self.present = present
        self.weight = weight
        self.share = share
        self.utility = utility
        self.contribution = contribution
        self.loss = loss
        self.factIds = factIds
    }

    enum CodingKeys: String, CodingKey {
        case component
        case present
        case weight
        case share
        case utility
        case contribution
        case loss
        case factIds = "fact_ids"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        component = try container.decode(String.self, forKey: .component)
        present = try container.decode(Bool.self, forKey: .present)
        weight = try container.decode(Double.self, forKey: .weight)
        share = try container.decode(Double.self, forKey: .share)
        utility = try container.decodeIfPresent(Double.self, forKey: .utility)
        contribution = try container.decode(Double.self, forKey: .contribution)
        loss = try container.decode(Double.self, forKey: .loss)
        factIds = try container.decode([String].self, forKey: .factIds)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(component, forKey: .component)
        try container.encode(present, forKey: .present)
        try container.encode(weight, forKey: .weight)
        try container.encode(share, forKey: .share)
        try container.encode(utility, forKey: .utility)
        try container.encode(contribution, forKey: .contribution)
        try container.encode(loss, forKey: .loss)
        try container.encode(factIds, forKey: .factIds)
    }
}

/// What a home of one kind costs in one area: a range, or one number where no range is known.
///
/// A row holds both quartiles or neither. A row with neither is a median of
/// what was paid for the homes that were sold, and is one of two things. A
/// publisher's own median is of the twelve months that end with `as_of`, and
/// what it rests on is `unstated`: the publisher gives no count of the sales.
/// A median worked out from the sales themselves says how many it rests on,
/// in `sales`, and the first month they were made in, in `since`. Nothing
/// stands in for the range of either.
///
/// A rent may be of a wider place than the area: no publisher gives one for
/// an area. It is then a range as its publisher gives it for the place, and
/// says the place in `of`, how many rents were recorded there in `rents`,
/// and the first month of them in `since`. Every area of the place that
/// takes its figure holds the same row.
public struct CostEstimate: Hashable, Sendable, Codable {
    public let areaId: String
    public let tenure: Tenure
    public let segment: Segment
    public let lowerQuartile: Int?
    public let median: Int
    public let upperQuartile: Int?
    public let confidence: Confidence
    public let asOf: String
    public let sourceIds: [String]
    public let of: CostOf?
    public let rents: Int?
    public let sales: Int?
    public let since: String?

    public init(
        areaId: String,
        tenure: Tenure,
        segment: Segment,
        lowerQuartile: Int?,
        median: Int,
        upperQuartile: Int?,
        confidence: Confidence,
        asOf: String,
        sourceIds: [String],
        of: CostOf? = nil,
        rents: Int? = nil,
        sales: Int? = nil,
        since: String? = nil
    ) {
        self.areaId = areaId
        self.tenure = tenure
        self.segment = segment
        self.lowerQuartile = lowerQuartile
        self.median = median
        self.upperQuartile = upperQuartile
        self.confidence = confidence
        self.asOf = asOf
        self.sourceIds = sourceIds
        self.of = of
        self.rents = rents
        self.sales = sales
        self.since = since
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case tenure
        case segment
        case lowerQuartile = "lower_quartile"
        case median
        case upperQuartile = "upper_quartile"
        case confidence
        case asOf = "as_of"
        case sourceIds = "source_ids"
        case of
        case rents
        case sales
        case since
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        tenure = try container.decode(Tenure.self, forKey: .tenure)
        segment = try container.decode(Segment.self, forKey: .segment)
        lowerQuartile = try container.decodeIfPresent(Int.self, forKey: .lowerQuartile)
        median = try container.decode(Int.self, forKey: .median)
        upperQuartile = try container.decodeIfPresent(Int.self, forKey: .upperQuartile)
        confidence = try container.decode(Confidence.self, forKey: .confidence)
        asOf = try container.decode(String.self, forKey: .asOf)
        sourceIds = try container.decode([String].self, forKey: .sourceIds)
        of = try container.decodeIfPresent(CostOf.self, forKey: .of)
        rents = try container.decodeIfPresent(Int.self, forKey: .rents)
        sales = try container.decodeIfPresent(Int.self, forKey: .sales)
        since = try container.decodeIfPresent(String.self, forKey: .since)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(tenure, forKey: .tenure)
        try container.encode(segment, forKey: .segment)
        try container.encode(lowerQuartile, forKey: .lowerQuartile)
        try container.encode(median, forKey: .median)
        try container.encode(upperQuartile, forKey: .upperQuartile)
        try container.encode(confidence, forKey: .confidence)
        try container.encode(asOf, forKey: .asOf)
        try container.encode(sourceIds, forKey: .sourceIds)
        try container.encode(of, forKey: .of)
        try container.encode(rents, forKey: .rents)
        try container.encode(sales, forKey: .sales)
        try container.encode(since, forKey: .since)
    }
}

/// The place a cost is of, where it is of a wider place than the area.
///
/// A postcode district the area lies in, by what stands before the space of
/// its postcodes, or the borough the area is in, by its name. A cost that is
/// of the area alone holds none.
public struct CostOf: Hashable, Sendable, Codable {
    public let kind: CostOfKind
    public let name: String

    public init(kind: CostOfKind, name: String) {
        self.kind = kind
        self.name = name
    }

    enum CodingKeys: String, CodingKey {
        case kind
        case name
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        kind = try container.decode(CostOfKind.self, forKey: .kind)
        name = try container.decode(String.self, forKey: .name)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(kind, forKey: .kind)
        try container.encode(name, forKey: .name)
    }
}

/// The kind of place a cost is of, where it is of a wider place than the area.
///
/// No publisher gives a rent for an area. One gives the rents that were
/// recorded in a postcode district and in a borough, and an area is given the
/// figure of the place it lies in.
public enum CostOfKind: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case postcodeDistrict
    case borough
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [CostOfKind] = [.postcodeDistrict, .borough]

    public init(rawValue: String) {
        switch rawValue {
        case "postcode_district": self = .postcodeDistrict
        case "borough": self = .borough
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .postcodeDistrict: return "postcode_district"
        case .borough: return "borough"
        case .unlisted(let value): return value
        }
    }
}

public struct Counts: Hashable, Sendable, Codable {
    public let neighbourhoods: Int
    public let rankable: Int
    public let destinations: Int
    public let places: Int
    public let stations: Int

    public init(
        neighbourhoods: Int,
        rankable: Int,
        destinations: Int,
        places: Int,
        stations: Int
    ) {
        self.neighbourhoods = neighbourhoods
        self.rankable = rankable
        self.destinations = destinations
        self.places = places
        self.stations = stations
    }

    enum CodingKeys: String, CodingKey {
        case neighbourhoods
        case rankable
        case destinations
        case places
        case stations
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        neighbourhoods = try container.decode(Int.self, forKey: .neighbourhoods)
        rankable = try container.decode(Int.self, forKey: .rankable)
        destinations = try container.decode(Int.self, forKey: .destinations)
        places = try container.decode(Int.self, forKey: .places)
        stations = try container.decode(Int.self, forKey: .stations)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(neighbourhoods, forKey: .neighbourhoods)
        try container.encode(rankable, forKey: .rankable)
        try container.encode(destinations, forKey: .destinations)
        try container.encode(places, forKey: .places)
        try container.encode(stations, forKey: .stations)
    }
}

/// The longest journey the release routed, by mode. Anything longer is `beyond_cutoff`.
public struct Cutoffs: Hashable, Sendable, Codable {
    public let pt: Int
    public let cycle: Int
    public let walk: Int

    public init(pt: Int, cycle: Int, walk: Int) {
        self.pt = pt
        self.cycle = cycle
        self.walk = walk
    }

    enum CodingKeys: String, CodingKey {
        case pt
        case cycle
        case walk
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        pt = try container.decode(Int.self, forKey: .pt)
        cycle = try container.decode(Int.self, forKey: .cycle)
        walk = try container.decode(Int.self, forKey: .walk)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(pt, forKey: .pt)
        try container.encode(cycle, forKey: .cycle)
        try container.encode(walk, forKey: .walk)
    }
}

public struct Defaults: Hashable, Sendable, Codable {
    public let rent: PreferenceSpec
    public let buy: PreferenceSpec

    public init(rent: PreferenceSpec, buy: PreferenceSpec) {
        self.rent = rent
        self.buy = buy
    }

    enum CodingKeys: String, CodingKey {
        case rent
        case buy
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        rent = try container.decode(PreferenceSpec.self, forKey: .rent)
        buy = try container.decode(PreferenceSpec.self, forKey: .buy)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(rent, forKey: .rent)
        try container.encode(buy, forKey: .buy)
    }
}

/// What a feature is a fact about.
public enum Describes: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case place
    case buildings
    case events
    case residents
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Describes] = [.place, .buildings, .events, .residents]

    public init(rawValue: String) {
        switch rawValue {
        case "place": self = .place
        case "buildings": self = .buildings
        case "events": self = .events
        case "residents": self = .residents
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .place: return "place"
        case .buildings: return "buildings"
        case .events: return "events"
        case .residents: return "residents"
        case .unlisted(let value): return value
        }
    }
}

public enum Dimension: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case crime
    case schools
    case greenWater
    case airNoise
    case venuesCulture
    case homes
    case stationAccess
    case services
    case brands
    case residents
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Dimension] = [.crime, .schools, .greenWater, .airNoise, .venuesCulture, .homes, .stationAccess, .services, .brands, .residents]

    public init(rawValue: String) {
        switch rawValue {
        case "crime": self = .crime
        case "schools": self = .schools
        case "green_water": self = .greenWater
        case "air_noise": self = .airNoise
        case "venues_culture": self = .venuesCulture
        case "homes": self = .homes
        case "station_access": self = .stationAccess
        case "services": self = .services
        case "brands": self = .brands
        case "residents": self = .residents
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .crime: return "crime"
        case .schools: return "schools"
        case .greenWater: return "green_water"
        case .airNoise: return "air_noise"
        case .venuesCulture: return "venues_culture"
        case .homes: return "homes"
        case .stationAccess: return "station_access"
        case .services: return "services"
        case .brands: return "brands"
        case .residents: return "residents"
        case .unlisted(let value): return value
        }
    }
}

public enum Direction: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case more
    case less
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Direction] = [.more, .less]

    public init(rawValue: String) {
        switch rawValue {
        case "more": self = .more
        case "less": self = .less
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .more: return "more"
        case .less: return "less"
        case .unlisted(let value): return value
        }
    }
}

public enum DirectionChoice: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case more
    case less
    case `default`
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [DirectionChoice] = [.more, .less, .default]

    public init(rawValue: String) {
        switch rawValue {
        case "more": self = .more
        case "less": self = .less
        case "default": self = .default
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .more: return "more"
        case .less: return "less"
        case .default: return "default"
        case .unlisted(let value): return value
        }
    }
}

public enum EditProvenance: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case stated
    case inferred
    case uiEdit
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [EditProvenance] = [.stated, .inferred, .uiEdit]

    public init(rawValue: String) {
        switch rawValue {
        case "stated": self = .stated
        case "inferred": self = .inferred
        case "ui_edit": self = .uiEdit
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .stated: return "stated"
        case .inferred: return "inferred"
        case .uiEdit: return "ui_edit"
        case .unlisted(let value): return value
        }
    }
}

public struct ErrorBody: Hashable, Sendable, Codable {
    public let code: ErrorCode
    public let message: String
    public let fields: [FieldProblem]

    public init(code: ErrorCode, message: String, fields: [FieldProblem]) {
        self.code = code
        self.message = message
        self.fields = fields
    }

    enum CodingKeys: String, CodingKey {
        case code
        case message
        case fields
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        code = try container.decode(ErrorCode.self, forKey: .code)
        message = try container.decode(String.self, forKey: .message)
        fields = try container.decode([FieldProblem].self, forKey: .fields)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(code, forKey: .code)
        try container.encode(message, forKey: .message)
        try container.encode(fields, forKey: .fields)
    }
}

public enum ErrorCode: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case malformedJson
    case bodyTooLarge
    case unsupportedMediaType
    case internalError
    case notFound
    case methodNotAllowed
    case invalidRequest
    case invalidText
    case invalidSpec
    case invalidOperations
    case invalidCompare
    case invalidQuery
    case unknownPlace
    case unknownArea
    case areaNotFound
    case shareNotFound
    case releaseChanged
    case censusNotAvailable
    case incomeNotAvailable
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [ErrorCode] = [.malformedJson, .bodyTooLarge, .unsupportedMediaType, .internalError, .notFound, .methodNotAllowed, .invalidRequest, .invalidText, .invalidSpec, .invalidOperations, .invalidCompare, .invalidQuery, .unknownPlace, .unknownArea, .areaNotFound, .shareNotFound, .releaseChanged, .censusNotAvailable, .incomeNotAvailable]

    public init(rawValue: String) {
        switch rawValue {
        case "malformed_json": self = .malformedJson
        case "body_too_large": self = .bodyTooLarge
        case "unsupported_media_type": self = .unsupportedMediaType
        case "internal_error": self = .internalError
        case "not_found": self = .notFound
        case "method_not_allowed": self = .methodNotAllowed
        case "invalid_request": self = .invalidRequest
        case "invalid_text": self = .invalidText
        case "invalid_spec": self = .invalidSpec
        case "invalid_operations": self = .invalidOperations
        case "invalid_compare": self = .invalidCompare
        case "invalid_query": self = .invalidQuery
        case "unknown_place": self = .unknownPlace
        case "unknown_area": self = .unknownArea
        case "area_not_found": self = .areaNotFound
        case "share_not_found": self = .shareNotFound
        case "release_changed": self = .releaseChanged
        case "census_not_available": self = .censusNotAvailable
        case "income_not_available": self = .incomeNotAvailable
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .malformedJson: return "malformed_json"
        case .bodyTooLarge: return "body_too_large"
        case .unsupportedMediaType: return "unsupported_media_type"
        case .internalError: return "internal_error"
        case .notFound: return "not_found"
        case .methodNotAllowed: return "method_not_allowed"
        case .invalidRequest: return "invalid_request"
        case .invalidText: return "invalid_text"
        case .invalidSpec: return "invalid_spec"
        case .invalidOperations: return "invalid_operations"
        case .invalidCompare: return "invalid_compare"
        case .invalidQuery: return "invalid_query"
        case .unknownPlace: return "unknown_place"
        case .unknownArea: return "unknown_area"
        case .areaNotFound: return "area_not_found"
        case .shareNotFound: return "share_not_found"
        case .releaseChanged: return "release_changed"
        case .censusNotAvailable: return "census_not_available"
        case .incomeNotAvailable: return "income_not_available"
        case .unlisted(let value): return value
        }
    }
}

public struct ErrorEnvelope: Hashable, Sendable, Codable {
    public let meta: Meta
    public let error: ErrorBody

    public init(meta: Meta, error: ErrorBody) {
        self.meta = meta
        self.error = error
    }

    enum CodingKeys: String, CodingKey {
        case meta
        case error
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        meta = try container.decode(Meta.self, forKey: .meta)
        error = try container.decode(ErrorBody.self, forKey: .error)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(meta, forKey: .meta)
        try container.encode(error, forKey: .error)
    }
}

public struct ExplainedSentence: Hashable, Sendable, Codable {
    public let text: String
    public let factIds: [String]
    public let origin: SentenceOrigin
    public let replaced: Bool

    public init(
        text: String,
        factIds: [String],
        origin: SentenceOrigin,
        replaced: Bool
    ) {
        self.text = text
        self.factIds = factIds
        self.origin = origin
        self.replaced = replaced
    }

    enum CodingKeys: String, CodingKey {
        case text
        case factIds = "fact_ids"
        case origin
        case replaced
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        text = try container.decode(String.self, forKey: .text)
        factIds = try container.decode([String].self, forKey: .factIds)
        origin = try container.decode(SentenceOrigin.self, forKey: .origin)
        replaced = try container.decode(Bool.self, forKey: .replaced)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(text, forKey: .text)
        try container.encode(factIds, forKey: .factIds)
        try container.encode(origin, forKey: .origin)
        try container.encode(replaced, forKey: .replaced)
    }
}

public struct Explanation: Hashable, Sendable, Codable {
    public let areaId: String
    public let orientation: ExplainedSentence
    public let reasons: [ExplainedSentence]
    public let tradeOff: ExplainedSentence?
    public let missing: [ExplainedSentence]

    public init(
        areaId: String,
        orientation: ExplainedSentence,
        reasons: [ExplainedSentence],
        tradeOff: ExplainedSentence?,
        missing: [ExplainedSentence]
    ) {
        self.areaId = areaId
        self.orientation = orientation
        self.reasons = reasons
        self.tradeOff = tradeOff
        self.missing = missing
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case orientation
        case reasons
        case tradeOff = "trade_off"
        case missing
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        orientation = try container.decode(ExplainedSentence.self, forKey: .orientation)
        reasons = try container.decode([ExplainedSentence].self, forKey: .reasons)
        tradeOff = try container.decodeIfPresent(ExplainedSentence.self, forKey: .tradeOff)
        missing = try container.decode([ExplainedSentence].self, forKey: .missing)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(orientation, forKey: .orientation)
        try container.encode(reasons, forKey: .reasons)
        try container.encode(tradeOff, forKey: .tradeOff)
        try container.encode(missing, forKey: .missing)
    }
}

public struct ExplanationsBody: Hashable, Sendable, Codable {
    public let spec: PreferenceSpec
    public let limit: Int

    public init(spec: PreferenceSpec, limit: Int = 3) {
        self.spec = spec
        self.limit = limit
    }

    enum CodingKeys: String, CodingKey {
        case spec
        case limit
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        limit = try container.decodeIfPresent(Int.self, forKey: .limit) ?? 3
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(spec, forKey: .spec)
        try container.encode(limit, forKey: .limit)
    }
}

public struct ExplanationsData: Hashable, Sendable, Codable {
    public let specHash: String
    public let explanations: [Explanation]
    public let facts: [Fact]

    public init(specHash: String, explanations: [Explanation], facts: [Fact]) {
        self.specHash = specHash
        self.explanations = explanations
        self.facts = facts
    }

    enum CodingKeys: String, CodingKey {
        case specHash = "spec_hash"
        case explanations
        case facts
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        specHash = try container.decode(String.self, forKey: .specHash)
        explanations = try container.decode([Explanation].self, forKey: .explanations)
        facts = try container.decode([Fact].self, forKey: .facts)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(specHash, forKey: .specHash)
        try container.encode(explanations, forKey: .explanations)
        try container.encode(facts, forKey: .facts)
    }
}

public struct Fact: Hashable, Sendable, Codable {
    public let factId: String
    public let areaId: String
    public let kind: FactKind
    public let key: String
    public let label: String
    public let template: TemplateId
    public let slots: [String: String]
    public let numbers: [String]
    public let names: [String]
    public let sources: [FactSource]
    public let asOf: String
    public let synthetic: Bool

    public init(
        factId: String,
        areaId: String,
        kind: FactKind,
        key: String,
        label: String,
        template: TemplateId,
        slots: [String: String],
        numbers: [String],
        names: [String],
        sources: [FactSource],
        asOf: String,
        synthetic: Bool
    ) {
        self.factId = factId
        self.areaId = areaId
        self.kind = kind
        self.key = key
        self.label = label
        self.template = template
        self.slots = slots
        self.numbers = numbers
        self.names = names
        self.sources = sources
        self.asOf = asOf
        self.synthetic = synthetic
    }

    enum CodingKeys: String, CodingKey {
        case factId = "fact_id"
        case areaId = "area_id"
        case kind
        case key
        case label
        case template
        case slots
        case numbers
        case names
        case sources
        case asOf = "as_of"
        case synthetic
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        factId = try container.decode(String.self, forKey: .factId)
        areaId = try container.decode(String.self, forKey: .areaId)
        kind = try container.decode(FactKind.self, forKey: .kind)
        key = try container.decode(String.self, forKey: .key)
        label = try container.decode(String.self, forKey: .label)
        template = try container.decode(TemplateId.self, forKey: .template)
        slots = try container.decode([String: String].self, forKey: .slots)
        numbers = try container.decode([String].self, forKey: .numbers)
        names = try container.decode([String].self, forKey: .names)
        sources = try container.decode([FactSource].self, forKey: .sources)
        asOf = try container.decode(String.self, forKey: .asOf)
        synthetic = try container.decode(Bool.self, forKey: .synthetic)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(factId, forKey: .factId)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(kind, forKey: .kind)
        try container.encode(key, forKey: .key)
        try container.encode(label, forKey: .label)
        try container.encode(template, forKey: .template)
        try container.encode(slots, forKey: .slots)
        try container.encode(numbers, forKey: .numbers)
        try container.encode(names, forKey: .names)
        try container.encode(sources, forKey: .sources)
        try container.encode(asOf, forKey: .asOf)
        try container.encode(synthetic, forKey: .synthetic)
    }
}

public enum FactKind: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case area
    case feature
    case tag
    case cost
    case budgetFit
    case travel
    case station
    case missing
    case likeness
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [FactKind] = [.area, .feature, .tag, .cost, .budgetFit, .travel, .station, .missing, .likeness]

    public init(rawValue: String) {
        switch rawValue {
        case "area": self = .area
        case "feature": self = .feature
        case "tag": self = .tag
        case "cost": self = .cost
        case "budget_fit": self = .budgetFit
        case "travel": self = .travel
        case "station": self = .station
        case "missing": self = .missing
        case "likeness": self = .likeness
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .area: return "area"
        case .feature: return "feature"
        case .tag: return "tag"
        case .cost: return "cost"
        case .budgetFit: return "budget_fit"
        case .travel: return "travel"
        case .station: return "station"
        case .missing: return "missing"
        case .likeness: return "likeness"
        case .unlisted(let value): return value
        }
    }
}

public struct FactSource: Hashable, Sendable, Codable {
    public let sourceId: String
    public let name: String
    public let publisher: String
    public let attribution: String?
    public let saidWithAttribution: String?

    public init(
        sourceId: String,
        name: String,
        publisher: String,
        attribution: String? = nil,
        saidWithAttribution: String? = nil
    ) {
        self.sourceId = sourceId
        self.name = name
        self.publisher = publisher
        self.attribution = attribution
        self.saidWithAttribution = saidWithAttribution
    }

    enum CodingKeys: String, CodingKey {
        case sourceId = "source_id"
        case name
        case publisher
        case attribution
        case saidWithAttribution = "said_with_attribution"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        sourceId = try container.decode(String.self, forKey: .sourceId)
        name = try container.decode(String.self, forKey: .name)
        publisher = try container.decode(String.self, forKey: .publisher)
        attribution = try container.decodeIfPresent(String.self, forKey: .attribution)
        saidWithAttribution = try container.decodeIfPresent(String.self, forKey: .saidWithAttribution)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(sourceId, forKey: .sourceId)
        try container.encode(name, forKey: .name)
        try container.encode(publisher, forKey: .publisher)
        try container.encode(attribution, forKey: .attribution)
        try container.encode(saidWithAttribution, forKey: .saidWithAttribution)
    }
}

/// The groups of the settings, in the order they are shown.
public enum Family: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case streetsHomes
    case paceFood
    case green
    case dailyLife
    case whoLivesThere
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Family] = [.streetsHomes, .paceFood, .green, .dailyLife, .whoLivesThere]

    public init(rawValue: String) {
        switch rawValue {
        case "streets_homes": self = .streetsHomes
        case "pace_food": self = .paceFood
        case "green": self = .green
        case "daily_life": self = .dailyLife
        case "who_lives_there": self = .whoLivesThere
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .streetsHomes: return "streets_homes"
        case .paceFood: return "pace_food"
        case .green: return "green"
        case .dailyLife: return "daily_life"
        case .whoLivesThere: return "who_lives_there"
        case .unlisted(let value): return value
        }
    }
}

public struct FamilyLabel: Hashable, Sendable, Codable {
    public let family: Family
    public let label: String

    public init(family: Family, label: String) {
        self.family = family
        self.label = label
    }

    enum CodingKeys: String, CodingKey {
        case family
        case label
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        family = try container.decode(Family.self, forKey: .family)
        label = try container.decode(String.self, forKey: .label)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(family, forKey: .family)
        try container.encode(label, forKey: .label)
    }
}

public enum FeatureId: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case crimeViolenceRobbery
    case crimeBurglaryTheft
    case schoolPrimaryNearby
    case schoolPrimaryAttainment
    case schoolSecondaryAttainment
    case universityProximity
    case greenCover
    case parkProximity
    case playSpaceProximity
    case waterAccess
    case airNo2
    case noiseExposure
    case venueFoodDrink
    case venueEvening
    case venueIndependent
    case cultureVenues
    case highstreetAccess
    case homesFlats
    case homesPre1919
    case homesDensity
    case conservationCover
    case stationWalk
    case stationLines
    case independentsNearby
    case centreSmall
    case centreCompact
    case listedBuildings
    case homesPost2000
    case roadMajorExposure
    case eveningClusterExposure
    case landIndustry
    case landStorage
    case landTransportOther
    case landGardens
    case landWoodland
    case parkLargeProximity
    case parkFacilities
    case groceryWalk
    case incidentCriminalDamage
    case incidentAntisocial
    case privateOutdoorSpace
    case cuisineVariety
    case gpWalk
    case pharmacyWalk
    case venueFoodDrinkPerHomes
    case priceMedian
    case cultureVenuesPerHomes
    case venueCafe
    case venueCafePerHomes
    case venueGym
    case venueGymPerHomes
    case venueEveningPerHomes
    case grocerPremiumNearby
    case grocerMidNearby
    case grocerValueNearby
    case gymPremiumNearby
    case gymMidNearby
    case gymValueNearby
    case coffeePremiumNearby
    case coffeeMidNearby
    case coffeeValueNearby
    case grocerPremiumDistance
    case grocerMidDistance
    case grocerValueDistance
    case gymPremiumDistance
    case gymMidDistance
    case gymValueDistance
    case coffeePremiumDistance
    case coffeeMidDistance
    case coffeeValueDistance
    case brandMix
    case brandWaitrose
    case brandMands
    case brandWholeFoods
    case brandSainsburys
    case brandTesco
    case brandCoop
    case brandMorrisons
    case brandAsda
    case brandAldi
    case brandLidl
    case brandIceland
    case brandEquinox
    case brandThirdSpace
    case brandBarrys
    case brandVirginActive
    case brandNuffield
    case brandGymbox
    case brandDavidLloyd
    case brandAnytimeFitness
    case brandPuregym
    case brandTheGymGroup
    case brandGails
    case brandOleAndSteen
    case brandPret
    case brandNero
    case brandStarbucks
    case brandCosta
    case brandBlankStreet
    case brandGreggs
    case undergroundProximity
    case overgroundProximity
    case railProximity
    case busStopsNearby
    case busRoutesNearby
    case residentsAged2034
    case residentsAged65Over
    case householdsDependentChildren
    case householdsOnePerson
    case homesHigherBands
    case priceRise5y
    case priceRise10y
    case highstreetConserved
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [FeatureId] = [.crimeViolenceRobbery, .crimeBurglaryTheft, .schoolPrimaryNearby, .schoolPrimaryAttainment, .schoolSecondaryAttainment, .universityProximity, .greenCover, .parkProximity, .playSpaceProximity, .waterAccess, .airNo2, .noiseExposure, .venueFoodDrink, .venueEvening, .venueIndependent, .cultureVenues, .highstreetAccess, .homesFlats, .homesPre1919, .homesDensity, .conservationCover, .stationWalk, .stationLines, .independentsNearby, .centreSmall, .centreCompact, .listedBuildings, .homesPost2000, .roadMajorExposure, .eveningClusterExposure, .landIndustry, .landStorage, .landTransportOther, .landGardens, .landWoodland, .parkLargeProximity, .parkFacilities, .groceryWalk, .incidentCriminalDamage, .incidentAntisocial, .privateOutdoorSpace, .cuisineVariety, .gpWalk, .pharmacyWalk, .venueFoodDrinkPerHomes, .priceMedian, .cultureVenuesPerHomes, .venueCafe, .venueCafePerHomes, .venueGym, .venueGymPerHomes, .venueEveningPerHomes, .grocerPremiumNearby, .grocerMidNearby, .grocerValueNearby, .gymPremiumNearby, .gymMidNearby, .gymValueNearby, .coffeePremiumNearby, .coffeeMidNearby, .coffeeValueNearby, .grocerPremiumDistance, .grocerMidDistance, .grocerValueDistance, .gymPremiumDistance, .gymMidDistance, .gymValueDistance, .coffeePremiumDistance, .coffeeMidDistance, .coffeeValueDistance, .brandMix, .brandWaitrose, .brandMands, .brandWholeFoods, .brandSainsburys, .brandTesco, .brandCoop, .brandMorrisons, .brandAsda, .brandAldi, .brandLidl, .brandIceland, .brandEquinox, .brandThirdSpace, .brandBarrys, .brandVirginActive, .brandNuffield, .brandGymbox, .brandDavidLloyd, .brandAnytimeFitness, .brandPuregym, .brandTheGymGroup, .brandGails, .brandOleAndSteen, .brandPret, .brandNero, .brandStarbucks, .brandCosta, .brandBlankStreet, .brandGreggs, .undergroundProximity, .overgroundProximity, .railProximity, .busStopsNearby, .busRoutesNearby, .residentsAged2034, .residentsAged65Over, .householdsDependentChildren, .householdsOnePerson, .homesHigherBands, .priceRise5y, .priceRise10y, .highstreetConserved]

    public init(rawValue: String) {
        switch rawValue {
        case "crime_violence_robbery": self = .crimeViolenceRobbery
        case "crime_burglary_theft": self = .crimeBurglaryTheft
        case "school_primary_nearby": self = .schoolPrimaryNearby
        case "school_primary_attainment": self = .schoolPrimaryAttainment
        case "school_secondary_attainment": self = .schoolSecondaryAttainment
        case "university_proximity": self = .universityProximity
        case "green_cover": self = .greenCover
        case "park_proximity": self = .parkProximity
        case "play_space_proximity": self = .playSpaceProximity
        case "water_access": self = .waterAccess
        case "air_no2": self = .airNo2
        case "noise_exposure": self = .noiseExposure
        case "venue_food_drink": self = .venueFoodDrink
        case "venue_evening": self = .venueEvening
        case "venue_independent": self = .venueIndependent
        case "culture_venues": self = .cultureVenues
        case "highstreet_access": self = .highstreetAccess
        case "homes_flats": self = .homesFlats
        case "homes_pre1919": self = .homesPre1919
        case "homes_density": self = .homesDensity
        case "conservation_cover": self = .conservationCover
        case "station_walk": self = .stationWalk
        case "station_lines": self = .stationLines
        case "independents_nearby": self = .independentsNearby
        case "centre_small": self = .centreSmall
        case "centre_compact": self = .centreCompact
        case "listed_buildings": self = .listedBuildings
        case "homes_post2000": self = .homesPost2000
        case "road_major_exposure": self = .roadMajorExposure
        case "evening_cluster_exposure": self = .eveningClusterExposure
        case "land_industry": self = .landIndustry
        case "land_storage": self = .landStorage
        case "land_transport_other": self = .landTransportOther
        case "land_gardens": self = .landGardens
        case "land_woodland": self = .landWoodland
        case "park_large_proximity": self = .parkLargeProximity
        case "park_facilities": self = .parkFacilities
        case "grocery_walk": self = .groceryWalk
        case "incident_criminal_damage": self = .incidentCriminalDamage
        case "incident_antisocial": self = .incidentAntisocial
        case "private_outdoor_space": self = .privateOutdoorSpace
        case "cuisine_variety": self = .cuisineVariety
        case "gp_walk": self = .gpWalk
        case "pharmacy_walk": self = .pharmacyWalk
        case "venue_food_drink_per_homes": self = .venueFoodDrinkPerHomes
        case "price_median": self = .priceMedian
        case "culture_venues_per_homes": self = .cultureVenuesPerHomes
        case "venue_cafe": self = .venueCafe
        case "venue_cafe_per_homes": self = .venueCafePerHomes
        case "venue_gym": self = .venueGym
        case "venue_gym_per_homes": self = .venueGymPerHomes
        case "venue_evening_per_homes": self = .venueEveningPerHomes
        case "grocer_premium_nearby": self = .grocerPremiumNearby
        case "grocer_mid_nearby": self = .grocerMidNearby
        case "grocer_value_nearby": self = .grocerValueNearby
        case "gym_premium_nearby": self = .gymPremiumNearby
        case "gym_mid_nearby": self = .gymMidNearby
        case "gym_value_nearby": self = .gymValueNearby
        case "coffee_premium_nearby": self = .coffeePremiumNearby
        case "coffee_mid_nearby": self = .coffeeMidNearby
        case "coffee_value_nearby": self = .coffeeValueNearby
        case "grocer_premium_distance": self = .grocerPremiumDistance
        case "grocer_mid_distance": self = .grocerMidDistance
        case "grocer_value_distance": self = .grocerValueDistance
        case "gym_premium_distance": self = .gymPremiumDistance
        case "gym_mid_distance": self = .gymMidDistance
        case "gym_value_distance": self = .gymValueDistance
        case "coffee_premium_distance": self = .coffeePremiumDistance
        case "coffee_mid_distance": self = .coffeeMidDistance
        case "coffee_value_distance": self = .coffeeValueDistance
        case "brand_mix": self = .brandMix
        case "brand_waitrose": self = .brandWaitrose
        case "brand_mands": self = .brandMands
        case "brand_whole_foods": self = .brandWholeFoods
        case "brand_sainsburys": self = .brandSainsburys
        case "brand_tesco": self = .brandTesco
        case "brand_coop": self = .brandCoop
        case "brand_morrisons": self = .brandMorrisons
        case "brand_asda": self = .brandAsda
        case "brand_aldi": self = .brandAldi
        case "brand_lidl": self = .brandLidl
        case "brand_iceland": self = .brandIceland
        case "brand_equinox": self = .brandEquinox
        case "brand_third_space": self = .brandThirdSpace
        case "brand_barrys": self = .brandBarrys
        case "brand_virgin_active": self = .brandVirginActive
        case "brand_nuffield": self = .brandNuffield
        case "brand_gymbox": self = .brandGymbox
        case "brand_david_lloyd": self = .brandDavidLloyd
        case "brand_anytime_fitness": self = .brandAnytimeFitness
        case "brand_puregym": self = .brandPuregym
        case "brand_the_gym_group": self = .brandTheGymGroup
        case "brand_gails": self = .brandGails
        case "brand_ole_and_steen": self = .brandOleAndSteen
        case "brand_pret": self = .brandPret
        case "brand_nero": self = .brandNero
        case "brand_starbucks": self = .brandStarbucks
        case "brand_costa": self = .brandCosta
        case "brand_blank_street": self = .brandBlankStreet
        case "brand_greggs": self = .brandGreggs
        case "underground_proximity": self = .undergroundProximity
        case "overground_proximity": self = .overgroundProximity
        case "rail_proximity": self = .railProximity
        case "bus_stops_nearby": self = .busStopsNearby
        case "bus_routes_nearby": self = .busRoutesNearby
        case "residents_aged_20_34": self = .residentsAged2034
        case "residents_aged_65_over": self = .residentsAged65Over
        case "households_dependent_children": self = .householdsDependentChildren
        case "households_one_person": self = .householdsOnePerson
        case "homes_higher_bands": self = .homesHigherBands
        case "price_rise_5y": self = .priceRise5y
        case "price_rise_10y": self = .priceRise10y
        case "highstreet_conserved": self = .highstreetConserved
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .crimeViolenceRobbery: return "crime_violence_robbery"
        case .crimeBurglaryTheft: return "crime_burglary_theft"
        case .schoolPrimaryNearby: return "school_primary_nearby"
        case .schoolPrimaryAttainment: return "school_primary_attainment"
        case .schoolSecondaryAttainment: return "school_secondary_attainment"
        case .universityProximity: return "university_proximity"
        case .greenCover: return "green_cover"
        case .parkProximity: return "park_proximity"
        case .playSpaceProximity: return "play_space_proximity"
        case .waterAccess: return "water_access"
        case .airNo2: return "air_no2"
        case .noiseExposure: return "noise_exposure"
        case .venueFoodDrink: return "venue_food_drink"
        case .venueEvening: return "venue_evening"
        case .venueIndependent: return "venue_independent"
        case .cultureVenues: return "culture_venues"
        case .highstreetAccess: return "highstreet_access"
        case .homesFlats: return "homes_flats"
        case .homesPre1919: return "homes_pre1919"
        case .homesDensity: return "homes_density"
        case .conservationCover: return "conservation_cover"
        case .stationWalk: return "station_walk"
        case .stationLines: return "station_lines"
        case .independentsNearby: return "independents_nearby"
        case .centreSmall: return "centre_small"
        case .centreCompact: return "centre_compact"
        case .listedBuildings: return "listed_buildings"
        case .homesPost2000: return "homes_post2000"
        case .roadMajorExposure: return "road_major_exposure"
        case .eveningClusterExposure: return "evening_cluster_exposure"
        case .landIndustry: return "land_industry"
        case .landStorage: return "land_storage"
        case .landTransportOther: return "land_transport_other"
        case .landGardens: return "land_gardens"
        case .landWoodland: return "land_woodland"
        case .parkLargeProximity: return "park_large_proximity"
        case .parkFacilities: return "park_facilities"
        case .groceryWalk: return "grocery_walk"
        case .incidentCriminalDamage: return "incident_criminal_damage"
        case .incidentAntisocial: return "incident_antisocial"
        case .privateOutdoorSpace: return "private_outdoor_space"
        case .cuisineVariety: return "cuisine_variety"
        case .gpWalk: return "gp_walk"
        case .pharmacyWalk: return "pharmacy_walk"
        case .venueFoodDrinkPerHomes: return "venue_food_drink_per_homes"
        case .priceMedian: return "price_median"
        case .cultureVenuesPerHomes: return "culture_venues_per_homes"
        case .venueCafe: return "venue_cafe"
        case .venueCafePerHomes: return "venue_cafe_per_homes"
        case .venueGym: return "venue_gym"
        case .venueGymPerHomes: return "venue_gym_per_homes"
        case .venueEveningPerHomes: return "venue_evening_per_homes"
        case .grocerPremiumNearby: return "grocer_premium_nearby"
        case .grocerMidNearby: return "grocer_mid_nearby"
        case .grocerValueNearby: return "grocer_value_nearby"
        case .gymPremiumNearby: return "gym_premium_nearby"
        case .gymMidNearby: return "gym_mid_nearby"
        case .gymValueNearby: return "gym_value_nearby"
        case .coffeePremiumNearby: return "coffee_premium_nearby"
        case .coffeeMidNearby: return "coffee_mid_nearby"
        case .coffeeValueNearby: return "coffee_value_nearby"
        case .grocerPremiumDistance: return "grocer_premium_distance"
        case .grocerMidDistance: return "grocer_mid_distance"
        case .grocerValueDistance: return "grocer_value_distance"
        case .gymPremiumDistance: return "gym_premium_distance"
        case .gymMidDistance: return "gym_mid_distance"
        case .gymValueDistance: return "gym_value_distance"
        case .coffeePremiumDistance: return "coffee_premium_distance"
        case .coffeeMidDistance: return "coffee_mid_distance"
        case .coffeeValueDistance: return "coffee_value_distance"
        case .brandMix: return "brand_mix"
        case .brandWaitrose: return "brand_waitrose"
        case .brandMands: return "brand_mands"
        case .brandWholeFoods: return "brand_whole_foods"
        case .brandSainsburys: return "brand_sainsburys"
        case .brandTesco: return "brand_tesco"
        case .brandCoop: return "brand_coop"
        case .brandMorrisons: return "brand_morrisons"
        case .brandAsda: return "brand_asda"
        case .brandAldi: return "brand_aldi"
        case .brandLidl: return "brand_lidl"
        case .brandIceland: return "brand_iceland"
        case .brandEquinox: return "brand_equinox"
        case .brandThirdSpace: return "brand_third_space"
        case .brandBarrys: return "brand_barrys"
        case .brandVirginActive: return "brand_virgin_active"
        case .brandNuffield: return "brand_nuffield"
        case .brandGymbox: return "brand_gymbox"
        case .brandDavidLloyd: return "brand_david_lloyd"
        case .brandAnytimeFitness: return "brand_anytime_fitness"
        case .brandPuregym: return "brand_puregym"
        case .brandTheGymGroup: return "brand_the_gym_group"
        case .brandGails: return "brand_gails"
        case .brandOleAndSteen: return "brand_ole_and_steen"
        case .brandPret: return "brand_pret"
        case .brandNero: return "brand_nero"
        case .brandStarbucks: return "brand_starbucks"
        case .brandCosta: return "brand_costa"
        case .brandBlankStreet: return "brand_blank_street"
        case .brandGreggs: return "brand_greggs"
        case .undergroundProximity: return "underground_proximity"
        case .overgroundProximity: return "overground_proximity"
        case .railProximity: return "rail_proximity"
        case .busStopsNearby: return "bus_stops_nearby"
        case .busRoutesNearby: return "bus_routes_nearby"
        case .residentsAged2034: return "residents_aged_20_34"
        case .residentsAged65Over: return "residents_aged_65_over"
        case .householdsDependentChildren: return "households_dependent_children"
        case .householdsOnePerson: return "households_one_person"
        case .homesHigherBands: return "homes_higher_bands"
        case .priceRise5y: return "price_rise_5y"
        case .priceRise10y: return "price_rise_10y"
        case .highstreetConserved: return "highstreet_conserved"
        case .unlisted(let value): return value
        }
    }
}

/// What a person may want of a feature, which decides where it may stand.
public enum FeatureKind: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case taste
    case amenity
    case nuisance
    case onRequest
    case residents
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [FeatureKind] = [.taste, .amenity, .nuisance, .onRequest, .residents]

    public init(rawValue: String) {
        switch rawValue {
        case "taste": self = .taste
        case "amenity": self = .amenity
        case "nuisance": self = .nuisance
        case "on_request": self = .onRequest
        case "residents": self = .residents
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .taste: return "taste"
        case .amenity: return "amenity"
        case .nuisance: return "nuisance"
        case .onRequest: return "on_request"
        case .residents: return "residents"
        case .unlisted(let value): return value
        }
    }
}

public struct FeatureValue: Hashable, Sendable, Codable {
    public let areaId: String
    public let featureId: FeatureId
    public let value: Double?
    public let percentile: Double?
    public let coverage: Double

    public init(
        areaId: String,
        featureId: FeatureId,
        value: Double?,
        percentile: Double?,
        coverage: Double
    ) {
        self.areaId = areaId
        self.featureId = featureId
        self.value = value
        self.percentile = percentile
        self.coverage = coverage
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case featureId = "feature_id"
        case value
        case percentile
        case coverage
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        featureId = try container.decode(FeatureId.self, forKey: .featureId)
        value = try container.decodeIfPresent(Double.self, forKey: .value)
        percentile = try container.decodeIfPresent(Double.self, forKey: .percentile)
        coverage = try container.decode(Double.self, forKey: .coverage)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(featureId, forKey: .featureId)
        try container.encode(value, forKey: .value)
        try container.encode(percentile, forKey: .percentile)
        try container.encode(coverage, forKey: .coverage)
    }
}

public struct FeatureWeight: Hashable, Sendable, Codable {
    public let featureId: FeatureId
    public let weight: Double
    public let direction: Direction
    public let provenance: Provenance

    public init(
        featureId: FeatureId,
        weight: Double,
        direction: Direction,
        provenance: Provenance
    ) {
        self.featureId = featureId
        self.weight = weight
        self.direction = direction
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case featureId = "feature_id"
        case weight
        case direction
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        featureId = try container.decode(FeatureId.self, forKey: .featureId)
        weight = try container.decode(Double.self, forKey: .weight)
        direction = try container.decode(Direction.self, forKey: .direction)
        provenance = try container.decode(Provenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(featureId, forKey: .featureId)
        try container.encode(weight, forKey: .weight)
        try container.encode(direction, forKey: .direction)
        try container.encode(provenance, forKey: .provenance)
    }
}

public struct FieldProblem: Hashable, Sendable, Codable {
    public let path: String
    public let problem: Problem

    public init(path: String, problem: Problem) {
        self.path = path
        self.problem = problem
    }

    enum CodingKeys: String, CodingKey {
        case path
        case problem
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        path = try container.decode(String.self, forKey: .path)
        problem = try container.decode(Problem.self, forKey: .problem)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(path, forKey: .path)
        try container.encode(problem, forKey: .problem)
    }
}

/// In the order the filters are applied. An area stops at the first that catches it.
public enum FilterReason: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case excluded
    case notSelected
    case overBudget
    case commuteCap
    case commuteLikelyBeyond
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [FilterReason] = [.excluded, .notSelected, .overBudget, .commuteCap, .commuteLikelyBeyond]

    public init(rawValue: String) {
        switch rawValue {
        case "excluded": self = .excluded
        case "not_selected": self = .notSelected
        case "over_budget": self = .overBudget
        case "commute_cap": self = .commuteCap
        case "commute_likely_beyond": self = .commuteLikelyBeyond
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .excluded: return "excluded"
        case .notSelected: return "not_selected"
        case .overBudget: return "over_budget"
        case .commuteCap: return "commute_cap"
        case .commuteLikelyBeyond: return "commute_likely_beyond"
        case .unlisted(let value): return value
        }
    }
}

public struct Filtered: Hashable, Sendable, Codable {
    public let areaId: String
    public let reason: FilterReason

    public init(areaId: String, reason: FilterReason) {
        self.areaId = areaId
        self.reason = reason
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case reason
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        reason = try container.decode(FilterReason.self, forKey: .reason)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(reason, forKey: .reason)
    }
}

public struct FoundPlace: Hashable, Sendable, Codable {
    public let placeId: String
    public let name: String
    public let kind: PlaceKind
    public let coarseName: String

    public init(
        placeId: String,
        name: String,
        kind: PlaceKind,
        coarseName: String
    ) {
        self.placeId = placeId
        self.name = name
        self.kind = kind
        self.coarseName = coarseName
    }

    enum CodingKeys: String, CodingKey {
        case placeId = "place_id"
        case name
        case kind
        case coarseName = "coarse_name"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        placeId = try container.decode(String.self, forKey: .placeId)
        name = try container.decode(String.self, forKey: .name)
        kind = try container.decode(PlaceKind.self, forKey: .kind)
        coarseName = try container.decode(String.self, forKey: .coarseName)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(placeId, forKey: .placeId)
        try container.encode(name, forKey: .name)
        try container.encode(kind, forKey: .kind)
        try container.encode(coarseName, forKey: .coarseName)
    }
}

public struct GeoFeature: Hashable, Sendable, Codable {
    public let type: String
    public let id: String
    public let properties: GeoProperties
    public let geometry: Geometry

    public init(
        type: String = "Feature",
        id: String,
        properties: GeoProperties,
        geometry: Geometry
    ) {
        self.type = type
        self.id = id
        self.properties = properties
        self.geometry = geometry
    }

    enum CodingKeys: String, CodingKey {
        case type
        case id
        case properties
        case geometry
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        type = try container.decode(String.self, forKey: .type)
        id = try container.decode(String.self, forKey: .id)
        properties = try container.decode(GeoProperties.self, forKey: .properties)
        geometry = try container.decode(Geometry.self, forKey: .geometry)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(type, forKey: .type)
        try container.encode(id, forKey: .id)
        try container.encode(properties, forKey: .properties)
        try container.encode(geometry, forKey: .geometry)
    }
}

public struct GeoProperties: Hashable, Sendable, Codable {
    public let areaId: String

    public init(areaId: String) {
        self.areaId = areaId
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
    }
}

/// A GeoJSON geometry object: a polygon or a multipolygon, in WGS84.
public struct Geometry: Hashable, Sendable, Codable {
    public let type: GeometryType
    public let coordinates: GeometryCoordinates

    public init(type: GeometryType, coordinates: GeometryCoordinates) {
        self.type = type
        self.coordinates = coordinates
    }

    enum CodingKeys: String, CodingKey {
        case type
        case coordinates
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        type = try container.decode(GeometryType.self, forKey: .type)
        coordinates = try container.decode(GeometryCoordinates.self, forKey: .coordinates)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(type, forKey: .type)
        try container.encode(coordinates, forKey: .coordinates)
    }
}

/// A GeoJSON `FeatureCollection`, as `geometry.json` holds it.
public struct GeometryData: Hashable, Sendable, Codable {
    public let type: String
    public let features: [GeoFeature]

    public init(type: String = "FeatureCollection", features: [GeoFeature]) {
        self.type = type
        self.features = features
    }

    enum CodingKeys: String, CodingKey {
        case type
        case features
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        type = try container.decode(String.self, forKey: .type)
        features = try container.decode([GeoFeature].self, forKey: .features)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(type, forKey: .type)
        try container.encode(features, forKey: .features)
    }
}

public enum GeometryType: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case polygon
    case multiPolygon
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [GeometryType] = [.polygon, .multiPolygon]

    public init(rawValue: String) {
        switch rawValue {
        case "Polygon": self = .polygon
        case "MultiPolygon": self = .multiPolygon
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .polygon: return "Polygon"
        case .multiPolygon: return "MultiPolygon"
        case .unlisted(let value): return value
        }
    }
}

/// Whether a release carries Gritty, the one vibe that counts recorded crime.
public enum GrittyVariant: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case a
    case b
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [GrittyVariant] = [.a, .b]

    public init(rawValue: String) {
        switch rawValue {
        case "a": self = .a
        case "b": self = .b
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .a: return "a"
        case .b: return "b"
        case .unlisted(let value): return value
        }
    }
}

public struct Health: Hashable, Sendable, Codable {
    public let ok: Bool

    public init(ok: Bool) {
        self.ok = ok
    }

    enum CodingKeys: String, CodingKey {
        case ok
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        ok = try container.decode(Bool.self, forKey: .ok)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(ok, forKey: .ok)
    }
}

/// What a release holds to answer a search with, apart from its measures and its vibes.
///
/// A first build holds neither. A client then says so where a person would
/// look for it, and offers no control that could only be turned away.
public struct Holds: Hashable, Sendable, Codable {
    public let journeys: Bool
    public let costs: Bool

    public init(journeys: Bool, costs: Bool) {
        self.journeys = journeys
        self.costs = costs
    }

    enum CodingKeys: String, CodingKey {
        case journeys
        case costs
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        journeys = try container.decode(Bool.self, forKey: .journeys)
        costs = try container.decode(Bool.self, forKey: .costs)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(journeys, forKey: .journeys)
        try container.encode(costs, forKey: .costs)
    }
}

/// The numbers an estimate is made with, for a page of methods to print.
public struct HowEstimated: Hashable, Sendable, Codable {
    public let fixedMinutes: Double
    public let minutesAKm: Double
    public let minutesAKmNearTheUnderground: Double
    public let nearTheUndergroundM: Int
    public let withinBy: Int
    public let beyondBy: Int
    public let said: String

    public init(
        fixedMinutes: Double,
        minutesAKm: Double,
        minutesAKmNearTheUnderground: Double,
        nearTheUndergroundM: Int,
        withinBy: Int,
        beyondBy: Int,
        said: String
    ) {
        self.fixedMinutes = fixedMinutes
        self.minutesAKm = minutesAKm
        self.minutesAKmNearTheUnderground = minutesAKmNearTheUnderground
        self.nearTheUndergroundM = nearTheUndergroundM
        self.withinBy = withinBy
        self.beyondBy = beyondBy
        self.said = said
    }

    enum CodingKeys: String, CodingKey {
        case fixedMinutes = "fixed_minutes"
        case minutesAKm = "minutes_a_km"
        case minutesAKmNearTheUnderground = "minutes_a_km_near_the_underground"
        case nearTheUndergroundM = "near_the_underground_m"
        case withinBy = "within_by"
        case beyondBy = "beyond_by"
        case said
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        fixedMinutes = try container.decode(Double.self, forKey: .fixedMinutes)
        minutesAKm = try container.decode(Double.self, forKey: .minutesAKm)
        minutesAKmNearTheUnderground = try container.decode(Double.self, forKey: .minutesAKmNearTheUnderground)
        nearTheUndergroundM = try container.decode(Int.self, forKey: .nearTheUndergroundM)
        withinBy = try container.decode(Int.self, forKey: .withinBy)
        beyondBy = try container.decode(Int.self, forKey: .beyondBy)
        said = try container.decode(String.self, forKey: .said)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(fixedMinutes, forKey: .fixedMinutes)
        try container.encode(minutesAKm, forKey: .minutesAKm)
        try container.encode(minutesAKmNearTheUnderground, forKey: .minutesAKmNearTheUnderground)
        try container.encode(nearTheUndergroundM, forKey: .nearTheUndergroundM)
        try container.encode(withinBy, forKey: .withinBy)
        try container.encode(beyondBy, forKey: .beyondBy)
        try container.encode(said, forKey: .said)
    }
}

/// What the closed block of an area's page says. It holds no figure and names no area.
public struct IncomeOffer: Hashable, Sendable, Codable {
    public let available: Bool
    public let heading: String
    public let intro: String

    public init(available: Bool, heading: String, intro: String) {
        self.available = available
        self.heading = heading
        self.intro = intro
    }

    enum CodingKeys: String, CodingKey {
        case available
        case heading
        case intro
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        available = try container.decode(Bool.self, forKey: .available)
        heading = try container.decode(String.self, forKey: .heading)
        intro = try container.decode(String.self, forKey: .intro)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(available, forKey: .available)
        try container.encode(heading, forKey: .heading)
        try container.encode(intro, forKey: .intro)
    }
}

/// The figure of one area, as its page shows it. Every word but a button's is here.
///
/// A figure is said in words, as it is to be printed: `£52,300`. `limits`
/// holds both limits as they are printed, `£46,100 to £59,300`, so that no
/// client joins two figures. Where the publisher gives none for the area,
/// `estimate` and the limits are `None` and `none_given` says so.
public struct IncomeShown: Hashable, Sendable, Codable {
    public let areaId: String
    public let heading: String
    public let kind: String
    public let definition: String
    public let estimate: String?
    public let limitsLabel: String
    public let lower: String?
    public let upper: String?
    public let limits: String?
    public let noneGiven: String?
    public let yearLine: String
    public let modelled: String
    public let notes: [String]
    public let sourceLine: String
    public let licenceLine: String
    public let sourceUrl: String
    public let openSource: String

    public init(
        areaId: String,
        heading: String,
        kind: String,
        definition: String,
        estimate: String?,
        limitsLabel: String,
        lower: String?,
        upper: String?,
        limits: String?,
        noneGiven: String?,
        yearLine: String,
        modelled: String,
        notes: [String],
        sourceLine: String,
        licenceLine: String,
        sourceUrl: String,
        openSource: String
    ) {
        self.areaId = areaId
        self.heading = heading
        self.kind = kind
        self.definition = definition
        self.estimate = estimate
        self.limitsLabel = limitsLabel
        self.lower = lower
        self.upper = upper
        self.limits = limits
        self.noneGiven = noneGiven
        self.yearLine = yearLine
        self.modelled = modelled
        self.notes = notes
        self.sourceLine = sourceLine
        self.licenceLine = licenceLine
        self.sourceUrl = sourceUrl
        self.openSource = openSource
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case heading
        case kind
        case definition
        case estimate
        case limitsLabel = "limits_label"
        case lower
        case upper
        case limits
        case noneGiven = "none_given"
        case yearLine = "year_line"
        case modelled
        case notes
        case sourceLine = "source_line"
        case licenceLine = "licence_line"
        case sourceUrl = "source_url"
        case openSource = "open_source"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        heading = try container.decode(String.self, forKey: .heading)
        kind = try container.decode(String.self, forKey: .kind)
        definition = try container.decode(String.self, forKey: .definition)
        estimate = try container.decodeIfPresent(String.self, forKey: .estimate)
        limitsLabel = try container.decode(String.self, forKey: .limitsLabel)
        lower = try container.decodeIfPresent(String.self, forKey: .lower)
        upper = try container.decodeIfPresent(String.self, forKey: .upper)
        limits = try container.decodeIfPresent(String.self, forKey: .limits)
        noneGiven = try container.decodeIfPresent(String.self, forKey: .noneGiven)
        yearLine = try container.decode(String.self, forKey: .yearLine)
        modelled = try container.decode(String.self, forKey: .modelled)
        notes = try container.decode([String].self, forKey: .notes)
        sourceLine = try container.decode(String.self, forKey: .sourceLine)
        licenceLine = try container.decode(String.self, forKey: .licenceLine)
        sourceUrl = try container.decode(String.self, forKey: .sourceUrl)
        openSource = try container.decode(String.self, forKey: .openSource)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(heading, forKey: .heading)
        try container.encode(kind, forKey: .kind)
        try container.encode(definition, forKey: .definition)
        try container.encode(estimate, forKey: .estimate)
        try container.encode(limitsLabel, forKey: .limitsLabel)
        try container.encode(lower, forKey: .lower)
        try container.encode(upper, forKey: .upper)
        try container.encode(limits, forKey: .limits)
        try container.encode(noneGiven, forKey: .noneGiven)
        try container.encode(yearLine, forKey: .yearLine)
        try container.encode(modelled, forKey: .modelled)
        try container.encode(notes, forKey: .notes)
        try container.encode(sourceLine, forKey: .sourceLine)
        try container.encode(licenceLine, forKey: .licenceLine)
        try container.encode(sourceUrl, forKey: .sourceUrl)
        try container.encode(openSource, forKey: .openSource)
    }
}

public struct InterpretBody: Hashable, Sendable, Codable {
    public let text: String
    public let askModel: Bool
    public let spec: PreferenceSpec?

    public init(text: String, askModel: Bool = true, spec: PreferenceSpec? = nil) {
        self.text = text
        self.askModel = askModel
        self.spec = spec
    }

    enum CodingKeys: String, CodingKey {
        case text
        case askModel = "ask_model"
        case spec
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        text = try container.decode(String.self, forKey: .text)
        askModel = try container.decodeIfPresent(Bool.self, forKey: .askModel) ?? true
        spec = try container.decodeIfPresent(PreferenceSpec.self, forKey: .spec)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(text, forKey: .text)
        try container.encode(askModel, forKey: .askModel)
        try container.encodeIfPresent(spec, forKey: .spec)
    }
}

public struct InterpretData: Hashable, Sendable, Codable {
    public let status: InterpretStatus
    public let operations: Operations
    public let spec: PreferenceSpec
    public let specHash: String
    public let applied: [Applied]
    public let rejected: [Rejected]
    public let assumptions: [Assumption]
    public let unmet: [UnmetCategory]
    public let clarify: [Clarify]
    public let notice: Notice
    public let noticeText: String
    public let interpreter: InterpreterName
    public let degraded: Bool
    public let modelRefused: Bool
    public let restsOn: [RestsOn]
    public let suggestions: [Suggestion]
    public let unread: [Span]
    public let notInRelease: [NotInRelease]
    public let unmetAt: [UnmetAt]
    public let modelPending: Bool
    public let places: [NamedPlace]

    public init(
        status: InterpretStatus,
        operations: Operations,
        spec: PreferenceSpec,
        specHash: String,
        applied: [Applied],
        rejected: [Rejected],
        assumptions: [Assumption],
        unmet: [UnmetCategory],
        clarify: [Clarify],
        notice: Notice,
        noticeText: String,
        interpreter: InterpreterName,
        degraded: Bool,
        modelRefused: Bool,
        restsOn: [RestsOn],
        suggestions: [Suggestion],
        unread: [Span],
        notInRelease: [NotInRelease],
        unmetAt: [UnmetAt],
        modelPending: Bool,
        places: [NamedPlace]
    ) {
        self.status = status
        self.operations = operations
        self.spec = spec
        self.specHash = specHash
        self.applied = applied
        self.rejected = rejected
        self.assumptions = assumptions
        self.unmet = unmet
        self.clarify = clarify
        self.notice = notice
        self.noticeText = noticeText
        self.interpreter = interpreter
        self.degraded = degraded
        self.modelRefused = modelRefused
        self.restsOn = restsOn
        self.suggestions = suggestions
        self.unread = unread
        self.notInRelease = notInRelease
        self.unmetAt = unmetAt
        self.modelPending = modelPending
        self.places = places
    }

    enum CodingKeys: String, CodingKey {
        case status
        case operations
        case spec
        case specHash = "spec_hash"
        case applied
        case rejected
        case assumptions
        case unmet
        case clarify
        case notice
        case noticeText = "notice_text"
        case interpreter
        case degraded
        case modelRefused = "model_refused"
        case restsOn = "rests_on"
        case suggestions
        case unread
        case notInRelease = "not_in_release"
        case unmetAt = "unmet_at"
        case modelPending = "model_pending"
        case places
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        status = try container.decode(InterpretStatus.self, forKey: .status)
        operations = try container.decode(Operations.self, forKey: .operations)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        specHash = try container.decode(String.self, forKey: .specHash)
        applied = try container.decode([Applied].self, forKey: .applied)
        rejected = try container.decode([Rejected].self, forKey: .rejected)
        assumptions = try container.decode([Assumption].self, forKey: .assumptions)
        unmet = try container.decode([UnmetCategory].self, forKey: .unmet)
        clarify = try container.decode([Clarify].self, forKey: .clarify)
        notice = try container.decode(Notice.self, forKey: .notice)
        noticeText = try container.decode(String.self, forKey: .noticeText)
        interpreter = try container.decode(InterpreterName.self, forKey: .interpreter)
        degraded = try container.decode(Bool.self, forKey: .degraded)
        modelRefused = try container.decode(Bool.self, forKey: .modelRefused)
        restsOn = try container.decode([RestsOn].self, forKey: .restsOn)
        suggestions = try container.decode([Suggestion].self, forKey: .suggestions)
        unread = try container.decode([Span].self, forKey: .unread)
        notInRelease = try container.decode([NotInRelease].self, forKey: .notInRelease)
        unmetAt = try container.decode([UnmetAt].self, forKey: .unmetAt)
        modelPending = try container.decode(Bool.self, forKey: .modelPending)
        places = try container.decode([NamedPlace].self, forKey: .places)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(status, forKey: .status)
        try container.encode(operations, forKey: .operations)
        try container.encode(spec, forKey: .spec)
        try container.encode(specHash, forKey: .specHash)
        try container.encode(applied, forKey: .applied)
        try container.encode(rejected, forKey: .rejected)
        try container.encode(assumptions, forKey: .assumptions)
        try container.encode(unmet, forKey: .unmet)
        try container.encode(clarify, forKey: .clarify)
        try container.encode(notice, forKey: .notice)
        try container.encode(noticeText, forKey: .noticeText)
        try container.encode(interpreter, forKey: .interpreter)
        try container.encode(degraded, forKey: .degraded)
        try container.encode(modelRefused, forKey: .modelRefused)
        try container.encode(restsOn, forKey: .restsOn)
        try container.encode(suggestions, forKey: .suggestions)
        try container.encode(unread, forKey: .unread)
        try container.encode(notInRelease, forKey: .notInRelease)
        try container.encode(unmetAt, forKey: .unmetAt)
        try container.encode(modelPending, forKey: .modelPending)
        try container.encode(places, forKey: .places)
    }
}

/// In the order that decides the status: the first that applies wins.
public enum InterpretStatus: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case offTopic
    case policyRedirect
    case clarify
    case suggest
    case ok
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [InterpretStatus] = [.offTopic, .policyRedirect, .clarify, .suggest, .ok]

    public init(rawValue: String) {
        switch rawValue {
        case "off_topic": self = .offTopic
        case "policy_redirect": self = .policyRedirect
        case "clarify": self = .clarify
        case "suggest": self = .suggest
        case "ok": self = .ok
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .offTopic: return "off_topic"
        case .policyRedirect: return "policy_redirect"
        case .clarify: return "clarify"
        case .suggest: return "suggest"
        case .ok: return "ok"
        case .unlisted(let value): return value
        }
    }
}

public enum InterpreterName: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case rule
    case model
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [InterpreterName] = [.rule, .model]

    public init(rawValue: String) {
        switch rawValue {
        case "rule": self = .rule
        case "model": self = .model
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .rule: return "rule"
        case .model: return "model"
        case .unlisted(let value): return value
        }
    }
}

/// Where an estimated journey stands against the limit a person gave. Never minutes.
public enum JourneyBand: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case likelyWithin
    case borderline
    case likelyBeyond
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [JourneyBand] = [.likelyWithin, .borderline, .likelyBeyond]

    public init(rawValue: String) {
        switch rawValue {
        case "likely_within": self = .likelyWithin
        case "borderline": self = .borderline
        case "likely_beyond": self = .likelyBeyond
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .likelyWithin: return "likely_within"
        case .borderline: return "borderline"
        case .likelyBeyond: return "likely_beyond"
        case .unlisted(let value): return value
        }
    }
}

public struct Meta: Hashable, Sendable, Codable {
    public let releaseId: String
    public let engineVersion: String
    public let synthetic: Bool
    public let preview: Bool

    public init(
        releaseId: String,
        engineVersion: String,
        synthetic: Bool,
        preview: Bool
    ) {
        self.releaseId = releaseId
        self.engineVersion = engineVersion
        self.synthetic = synthetic
        self.preview = preview
    }

    enum CodingKeys: String, CodingKey {
        case releaseId = "release_id"
        case engineVersion = "engine_version"
        case synthetic
        case preview
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        releaseId = try container.decode(String.self, forKey: .releaseId)
        engineVersion = try container.decode(String.self, forKey: .engineVersion)
        synthetic = try container.decode(Bool.self, forKey: .synthetic)
        preview = try container.decode(Bool.self, forKey: .preview)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(releaseId, forKey: .releaseId)
        try container.encode(engineVersion, forKey: .engineVersion)
        try container.encode(synthetic, forKey: .synthetic)
        try container.encode(preview, forKey: .preview)
    }
}

public struct MetaData: Hashable, Sendable, Codable {
    public let releaseId: String
    public let builtAt: String
    public let synthetic: Bool
    public let preview: Bool
    public let engineVersion: String
    public let catalogueVersion: Int
    public let counts: Counts
    public let holds: Holds
    public let attributions: [Source]
    public let features: [Metric]
    public let tags: [Tag]
    public let recipes: [RecipeHeld]
    public let families: [FamilyLabel]
    public let grittyVariant: GrittyVariant
    public let defaults: Defaults
    public let limits: ServedLimits
    public let reader: Reader
    public let census: CensusOffer
    public let income: IncomeOffer
    public let journeyEstimate: HowEstimated?
    public let rents: RentsSaid?
    public let roughGuides: [RoughGuide]

    public init(
        releaseId: String,
        builtAt: String,
        synthetic: Bool,
        preview: Bool,
        engineVersion: String,
        catalogueVersion: Int,
        counts: Counts,
        holds: Holds,
        attributions: [Source],
        features: [Metric],
        tags: [Tag],
        recipes: [RecipeHeld],
        families: [FamilyLabel],
        grittyVariant: GrittyVariant,
        defaults: Defaults,
        limits: ServedLimits,
        reader: Reader,
        census: CensusOffer,
        income: IncomeOffer,
        journeyEstimate: HowEstimated? = nil,
        rents: RentsSaid? = nil,
        roughGuides: [RoughGuide] = []
    ) {
        self.releaseId = releaseId
        self.builtAt = builtAt
        self.synthetic = synthetic
        self.preview = preview
        self.engineVersion = engineVersion
        self.catalogueVersion = catalogueVersion
        self.counts = counts
        self.holds = holds
        self.attributions = attributions
        self.features = features
        self.tags = tags
        self.recipes = recipes
        self.families = families
        self.grittyVariant = grittyVariant
        self.defaults = defaults
        self.limits = limits
        self.reader = reader
        self.census = census
        self.income = income
        self.journeyEstimate = journeyEstimate
        self.rents = rents
        self.roughGuides = roughGuides
    }

    enum CodingKeys: String, CodingKey {
        case releaseId = "release_id"
        case builtAt = "built_at"
        case synthetic
        case preview
        case engineVersion = "engine_version"
        case catalogueVersion = "catalogue_version"
        case counts
        case holds
        case attributions
        case features
        case tags
        case recipes
        case families
        case grittyVariant = "gritty_variant"
        case defaults
        case limits
        case reader
        case census
        case income
        case journeyEstimate = "journey_estimate"
        case rents
        case roughGuides = "rough_guides"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        releaseId = try container.decode(String.self, forKey: .releaseId)
        builtAt = try container.decode(String.self, forKey: .builtAt)
        synthetic = try container.decode(Bool.self, forKey: .synthetic)
        preview = try container.decode(Bool.self, forKey: .preview)
        engineVersion = try container.decode(String.self, forKey: .engineVersion)
        catalogueVersion = try container.decode(Int.self, forKey: .catalogueVersion)
        counts = try container.decode(Counts.self, forKey: .counts)
        holds = try container.decode(Holds.self, forKey: .holds)
        attributions = try container.decode([Source].self, forKey: .attributions)
        features = try container.decode([Metric].self, forKey: .features)
        tags = try container.decode([Tag].self, forKey: .tags)
        recipes = try container.decode([RecipeHeld].self, forKey: .recipes)
        families = try container.decode([FamilyLabel].self, forKey: .families)
        grittyVariant = try container.decode(GrittyVariant.self, forKey: .grittyVariant)
        defaults = try container.decode(Defaults.self, forKey: .defaults)
        limits = try container.decode(ServedLimits.self, forKey: .limits)
        reader = try container.decode(Reader.self, forKey: .reader)
        census = try container.decode(CensusOffer.self, forKey: .census)
        income = try container.decode(IncomeOffer.self, forKey: .income)
        journeyEstimate = try container.decodeIfPresent(HowEstimated.self, forKey: .journeyEstimate)
        rents = try container.decodeIfPresent(RentsSaid.self, forKey: .rents)
        roughGuides = try container.decodeIfPresent([RoughGuide].self, forKey: .roughGuides) ?? []
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(releaseId, forKey: .releaseId)
        try container.encode(builtAt, forKey: .builtAt)
        try container.encode(synthetic, forKey: .synthetic)
        try container.encode(preview, forKey: .preview)
        try container.encode(engineVersion, forKey: .engineVersion)
        try container.encode(catalogueVersion, forKey: .catalogueVersion)
        try container.encode(counts, forKey: .counts)
        try container.encode(holds, forKey: .holds)
        try container.encode(attributions, forKey: .attributions)
        try container.encode(features, forKey: .features)
        try container.encode(tags, forKey: .tags)
        try container.encode(recipes, forKey: .recipes)
        try container.encode(families, forKey: .families)
        try container.encode(grittyVariant, forKey: .grittyVariant)
        try container.encode(defaults, forKey: .defaults)
        try container.encode(limits, forKey: .limits)
        try container.encode(reader, forKey: .reader)
        try container.encode(census, forKey: .census)
        try container.encode(income, forKey: .income)
        try container.encode(journeyEstimate, forKey: .journeyEstimate)
        try container.encode(rents, forKey: .rents)
        try container.encode(roughGuides, forKey: .roughGuides)
    }
}

public enum Method: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case measured
    case modelled
    case averaged
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Method] = [.measured, .modelled, .averaged]

    public init(rawValue: String) {
        switch rawValue {
        case "measured": self = .measured
        case "modelled": self = .modelled
        case "averaged": self = .averaged
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .measured: return "measured"
        case .modelled: return "modelled"
        case .averaged: return "averaged"
        case .unlisted(let value): return value
        }
    }
}

/// A feature this release carries. Core decides what it is; the release says where from.
public struct Metric: Hashable, Sendable, Codable {
    public let featureId: FeatureId
    public let label: String
    public let shortLabel: String
    public let dimension: Dimension
    public let unit: String
    public let polarity: Polarity
    public let kind: FeatureKind
    public let describes: Describes
    public let family: Family?
    public let method: Method
    public let inLikeness: Bool
    public let nativeResolution: NativeResolution
    public let sourceIds: [String]
    public let vintage: String
    public let rankable: Bool
    public let definition: String

    public init(
        featureId: FeatureId,
        label: String,
        shortLabel: String,
        dimension: Dimension,
        unit: String,
        polarity: Polarity,
        kind: FeatureKind,
        describes: Describes,
        family: Family?,
        method: Method,
        inLikeness: Bool,
        nativeResolution: NativeResolution,
        sourceIds: [String],
        vintage: String,
        rankable: Bool,
        definition: String
    ) {
        self.featureId = featureId
        self.label = label
        self.shortLabel = shortLabel
        self.dimension = dimension
        self.unit = unit
        self.polarity = polarity
        self.kind = kind
        self.describes = describes
        self.family = family
        self.method = method
        self.inLikeness = inLikeness
        self.nativeResolution = nativeResolution
        self.sourceIds = sourceIds
        self.vintage = vintage
        self.rankable = rankable
        self.definition = definition
    }

    enum CodingKeys: String, CodingKey {
        case featureId = "feature_id"
        case label
        case shortLabel = "short_label"
        case dimension
        case unit
        case polarity
        case kind
        case describes
        case family
        case method
        case inLikeness = "in_likeness"
        case nativeResolution = "native_resolution"
        case sourceIds = "source_ids"
        case vintage
        case rankable
        case definition
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        featureId = try container.decode(FeatureId.self, forKey: .featureId)
        label = try container.decode(String.self, forKey: .label)
        shortLabel = try container.decode(String.self, forKey: .shortLabel)
        dimension = try container.decode(Dimension.self, forKey: .dimension)
        unit = try container.decode(String.self, forKey: .unit)
        polarity = try container.decode(Polarity.self, forKey: .polarity)
        kind = try container.decode(FeatureKind.self, forKey: .kind)
        describes = try container.decode(Describes.self, forKey: .describes)
        family = try container.decodeIfPresent(Family.self, forKey: .family)
        method = try container.decode(Method.self, forKey: .method)
        inLikeness = try container.decode(Bool.self, forKey: .inLikeness)
        nativeResolution = try container.decode(NativeResolution.self, forKey: .nativeResolution)
        sourceIds = try container.decode([String].self, forKey: .sourceIds)
        vintage = try container.decode(String.self, forKey: .vintage)
        rankable = try container.decode(Bool.self, forKey: .rankable)
        definition = try container.decode(String.self, forKey: .definition)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(featureId, forKey: .featureId)
        try container.encode(label, forKey: .label)
        try container.encode(shortLabel, forKey: .shortLabel)
        try container.encode(dimension, forKey: .dimension)
        try container.encode(unit, forKey: .unit)
        try container.encode(polarity, forKey: .polarity)
        try container.encode(kind, forKey: .kind)
        try container.encode(describes, forKey: .describes)
        try container.encode(family, forKey: .family)
        try container.encode(method, forKey: .method)
        try container.encode(inLikeness, forKey: .inLikeness)
        try container.encode(nativeResolution, forKey: .nativeResolution)
        try container.encode(sourceIds, forKey: .sourceIds)
        try container.encode(vintage, forKey: .vintage)
        try container.encode(rankable, forKey: .rankable)
        try container.encode(definition, forKey: .definition)
    }
}

public enum Mode: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case pt
    case cycle
    case walk
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Mode] = [.pt, .cycle, .walk]

    public init(rawValue: String) {
        switch rawValue {
        case "pt": self = .pt
        case "cycle": self = .cycle
        case "walk": self = .walk
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .pt: return "pt"
        case .cycle: return "cycle"
        case .walk: return "walk"
        case .unlisted(let value): return value
        }
    }
}

public enum ModeChoice: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case pt
    case cycle
    case walk
    case unchanged
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [ModeChoice] = [.pt, .cycle, .walk, .unchanged]

    public init(rawValue: String) {
        switch rawValue {
        case "pt": self = .pt
        case "cycle": self = .cycle
        case "walk": self = .walk
        case "unchanged": self = .unchanged
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .pt: return "pt"
        case .cycle: return "cycle"
        case .walk: return "walk"
        case .unchanged: return "unchanged"
        case .unlisted(let value): return value
        }
    }
}

public struct MoneyLimits: Hashable, Sendable, Codable {
    public let minimum: Int
    public let maximum: Int
    public let unit: Int

    public init(minimum: Int, maximum: Int, unit: Int) {
        self.minimum = minimum
        self.maximum = maximum
        self.unit = unit
    }

    enum CodingKeys: String, CodingKey {
        case minimum
        case maximum
        case unit
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        minimum = try container.decode(Int.self, forKey: .minimum)
        maximum = try container.decode(Int.self, forKey: .maximum)
        unit = try container.decode(Int.self, forKey: .unit)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(minimum, forKey: .minimum)
        try container.encode(maximum, forKey: .maximum)
        try container.encode(unit, forKey: .unit)
    }
}

/// How far the name an area bears has been checked.
public enum NameState: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case draft
    case checked
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [NameState] = [.draft, .checked]

    public init(rawValue: String) {
        switch rawValue {
        case "draft": self = .draft
        case "checked": self = .checked
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .draft: return "draft"
        case .checked: return "checked"
        case .unlisted(let value): return value
        }
    }
}

/// What is known of the name an area bears, where it is not its publisher's label.
///
/// An area is drawn as its publisher draws it, and its publisher labels it
/// with a borough and a number. Where the area bears the name of a
/// neighbourhood, this says what the label was, who wrote the name, and
/// whether a person has checked it. A name is a draft until one has.
public struct Named: Hashable, Sendable, Codable {
    public let label: String
    public let sourceIds: [String]
    public let state: NameState

    public init(label: String, sourceIds: [String], state: NameState) {
        self.label = label
        self.sourceIds = sourceIds
        self.state = state
    }

    enum CodingKeys: String, CodingKey {
        case label
        case sourceIds = "source_ids"
        case state
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        label = try container.decode(String.self, forKey: .label)
        sourceIds = try container.decode([String].self, forKey: .sourceIds)
        state = try container.decode(NameState.self, forKey: .state)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(label, forKey: .label)
        try container.encode(sourceIds, forKey: .sourceIds)
        try container.encode(state, forKey: .state)
    }
}

/// A place a spec names, by the release's own name for it. Never what was typed.
///
/// A spec holds a `place_id` and no name. A name says where someone works as
/// an id does, so it is handled as one: served in a body, and in no log.
public struct NamedPlace: Hashable, Sendable, Codable {
    public let placeId: String
    public let name: String
    public let kind: PlaceKind

    public init(placeId: String, name: String, kind: PlaceKind) {
        self.placeId = placeId
        self.name = name
        self.kind = kind
    }

    enum CodingKeys: String, CodingKey {
        case placeId = "place_id"
        case name
        case kind
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        placeId = try container.decode(String.self, forKey: .placeId)
        name = try container.decode(String.self, forKey: .name)
        kind = try container.decode(PlaceKind.self, forKey: .kind)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(placeId, forKey: .placeId)
        try container.encode(name, forKey: .name)
        try container.encode(kind, forKey: .kind)
    }
}

public enum NativeResolution: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case oa
    case lsoa
    case msoa
    case grid1km
    case point
    case polygon
    case network
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [NativeResolution] = [.oa, .lsoa, .msoa, .grid1km, .point, .polygon, .network]

    public init(rawValue: String) {
        switch rawValue {
        case "oa": self = .oa
        case "lsoa": self = .lsoa
        case "msoa": self = .msoa
        case "grid_1km": self = .grid1km
        case "point": self = .point
        case "polygon": self = .polygon
        case "network": self = .network
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .oa: return "oa"
        case .lsoa: return "lsoa"
        case .msoa: return "msoa"
        case .grid1km: return "grid_1km"
        case .point: return "point"
        case .polygon: return "polygon"
        case .network: return "network"
        case .unlisted(let value): return value
        }
    }
}

public struct Neighbourhood: Hashable, Sendable, Codable {
    public let areaId: String
    public let slug: String
    public let name: String
    public let borough: String
    public let aliases: [String]
    public let centroid: LonLat
    public let rankable: Bool
    public let neighbours: [String]
    public let homesAt: LonLat?
    public let named: Named?

    public init(
        areaId: String,
        slug: String,
        name: String,
        borough: String,
        aliases: [String],
        centroid: LonLat,
        rankable: Bool,
        neighbours: [String],
        homesAt: LonLat? = nil,
        named: Named? = nil
    ) {
        self.areaId = areaId
        self.slug = slug
        self.name = name
        self.borough = borough
        self.aliases = aliases
        self.centroid = centroid
        self.rankable = rankable
        self.neighbours = neighbours
        self.homesAt = homesAt
        self.named = named
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case slug
        case name
        case borough
        case aliases
        case centroid
        case rankable
        case neighbours
        case homesAt = "homes_at"
        case named
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        slug = try container.decode(String.self, forKey: .slug)
        name = try container.decode(String.self, forKey: .name)
        borough = try container.decode(String.self, forKey: .borough)
        aliases = try container.decode([String].self, forKey: .aliases)
        centroid = try container.decode(LonLat.self, forKey: .centroid)
        rankable = try container.decode(Bool.self, forKey: .rankable)
        neighbours = try container.decode([String].self, forKey: .neighbours)
        homesAt = try container.decodeIfPresent(LonLat.self, forKey: .homesAt)
        named = try container.decodeIfPresent(Named.self, forKey: .named)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(slug, forKey: .slug)
        try container.encode(name, forKey: .name)
        try container.encode(borough, forKey: .borough)
        try container.encode(aliases, forKey: .aliases)
        try container.encode(centroid, forKey: .centroid)
        try container.encode(rankable, forKey: .rankable)
        try container.encode(neighbours, forKey: .neighbours)
        try container.encode(homesAt, forKey: .homesAt)
        try container.encode(named, forKey: .named)
    }
}

/// A thing a person asked for that the release holds for no area, so none is ranked on it.
///
/// A vibe that no area has a band for, a measure the release does not carry,
/// a budget where it holds no cost of that kind of home, a journey where it
/// names no place. It is said, so that a person is told what is not there
/// yet. It is never offered, and nothing stands in for it.
public struct NotInRelease: Hashable, Sendable, Codable {
    public let target: String
    public let label: String
    public let spans: [Span]

    public init(target: String, label: String, spans: [Span]) {
        self.target = target
        self.label = label
        self.spans = spans
    }

    enum CodingKeys: String, CodingKey {
        case target
        case label
        case spans
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        target = try container.decode(String.self, forKey: .target)
        label = try container.decode(String.self, forKey: .label)
        spans = try container.decode([Span].self, forKey: .spans)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(target, forKey: .target)
        try container.encode(label, forKey: .label)
        try container.encode(spans, forKey: .spans)
    }
}

public enum Notice: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case nothing
    case neutralPlaces
    case offTopic
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Notice] = [.nothing, .neutralPlaces, .offTopic]

    public init(rawValue: String) {
        switch rawValue {
        case "none": self = .nothing
        case "neutral_places": self = .neutralPlaces
        case "off_topic": self = .offTopic
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .nothing: return "none"
        case .neutralPlaces: return "neutral_places"
        case .offTopic: return "off_topic"
        case .unlisted(let value): return value
        }
    }
}

public struct Operations: Hashable, Sendable, Codable {
    public let budgetOps: [BudgetEdit]
    public let commuteOps: [CommuteEdit]
    public let weightOps: [WeightEdit]
    public let tagOps: [TagEdit]
    public let areaOps: [AreaEdit]
    public let settingOps: [SettingEdit]

    public init(
        budgetOps: [BudgetEdit],
        commuteOps: [CommuteEdit],
        weightOps: [WeightEdit],
        tagOps: [TagEdit],
        areaOps: [AreaEdit],
        settingOps: [SettingEdit]
    ) {
        self.budgetOps = budgetOps
        self.commuteOps = commuteOps
        self.weightOps = weightOps
        self.tagOps = tagOps
        self.areaOps = areaOps
        self.settingOps = settingOps
    }

    enum CodingKeys: String, CodingKey {
        case budgetOps = "budget_ops"
        case commuteOps = "commute_ops"
        case weightOps = "weight_ops"
        case tagOps = "tag_ops"
        case areaOps = "area_ops"
        case settingOps = "setting_ops"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        budgetOps = try container.decode([BudgetEdit].self, forKey: .budgetOps)
        commuteOps = try container.decode([CommuteEdit].self, forKey: .commuteOps)
        weightOps = try container.decode([WeightEdit].self, forKey: .weightOps)
        tagOps = try container.decode([TagEdit].self, forKey: .tagOps)
        areaOps = try container.decode([AreaEdit].self, forKey: .areaOps)
        settingOps = try container.decode([SettingEdit].self, forKey: .settingOps)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(budgetOps, forKey: .budgetOps)
        try container.encode(commuteOps, forKey: .commuteOps)
        try container.encode(weightOps, forKey: .weightOps)
        try container.encode(tagOps, forKey: .tagOps)
        try container.encode(areaOps, forKey: .areaOps)
        try container.encode(settingOps, forKey: .settingOps)
    }
}

/// The six arrays of `Operations`, in the order the reducer applies them.
public enum OpsGroup: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case budgetOps
    case commuteOps
    case weightOps
    case tagOps
    case areaOps
    case settingOps
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [OpsGroup] = [.budgetOps, .commuteOps, .weightOps, .tagOps, .areaOps, .settingOps]

    public init(rawValue: String) {
        switch rawValue {
        case "budget_ops": self = .budgetOps
        case "commute_ops": self = .commuteOps
        case "weight_ops": self = .weightOps
        case "tag_ops": self = .tagOps
        case "area_ops": self = .areaOps
        case "setting_ops": self = .settingOps
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .budgetOps: return "budget_ops"
        case .commuteOps: return "commute_ops"
        case .weightOps: return "weight_ops"
        case .tagOps: return "tag_ops"
        case .areaOps: return "area_ops"
        case .settingOps: return "setting_ops"
        case .unlisted(let value): return value
        }
    }
}

/// What a clarification offers: a place of one of the kinds of 2.7, or an area.
public enum OptionKind: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case station
    case district
    case postcodeDistrict
    case university
    case hospital
    case school
    case landmark
    case area
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [OptionKind] = [.station, .district, .postcodeDistrict, .university, .hospital, .school, .landmark, .area]

    public init(rawValue: String) {
        switch rawValue {
        case "station": self = .station
        case "district": self = .district
        case "postcode_district": self = .postcodeDistrict
        case "university": self = .university
        case "hospital": self = .hospital
        case "school": self = .school
        case "landmark": self = .landmark
        case "area": self = .area
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .station: return "station"
        case .district: return "district"
        case .postcodeDistrict: return "postcode_district"
        case .university: return "university"
        case .hospital: return "hospital"
        case .school: return "school"
        case .landmark: return "landmark"
        case .area: return "area"
        case .unlisted(let value): return value
        }
    }
}

/// In the order that breaks a tie between two matches of the same score.
public enum PlaceKind: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case station
    case district
    case postcodeDistrict
    case university
    case hospital
    case school
    case landmark
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [PlaceKind] = [.station, .district, .postcodeDistrict, .university, .hospital, .school, .landmark]

    public init(rawValue: String) {
        switch rawValue {
        case "station": self = .station
        case "district": self = .district
        case "postcode_district": self = .postcodeDistrict
        case "university": self = .university
        case "hospital": self = .hospital
        case "school": self = .school
        case "landmark": self = .landmark
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .station: return "station"
        case .district: return "district"
        case .postcodeDistrict: return "postcode_district"
        case .university: return "university"
        case .hospital: return "hospital"
        case .school: return "school"
        case .landmark: return "landmark"
        case .unlisted(let value): return value
        }
    }
}

public struct PlaceSearchBody: Hashable, Sendable, Codable {
    public let q: String
    public let limit: Int

    public init(q: String, limit: Int = 8) {
        self.q = q
        self.limit = limit
    }

    enum CodingKeys: String, CodingKey {
        case q
        case limit
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        q = try container.decode(String.self, forKey: .q)
        limit = try container.decodeIfPresent(Int.self, forKey: .limit) ?? 8
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(q, forKey: .q)
        try container.encode(limit, forKey: .limit)
    }
}

public struct PlacesData: Hashable, Sendable, Codable {
    public let places: [FoundPlace]
    public let areas: [AreaSummary]

    public init(places: [FoundPlace], areas: [AreaSummary]) {
        self.places = places
        self.areas = areas
    }

    enum CodingKeys: String, CodingKey {
        case places
        case areas
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        places = try container.decode([FoundPlace].self, forKey: .places)
        areas = try container.decode([AreaSummary].self, forKey: .areas)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(places, forKey: .places)
        try container.encode(areas, forKey: .areas)
    }
}

public enum Polarity: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case less
    case more
    case either
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Polarity] = [.less, .more, .either]

    public init(rawValue: String) {
        switch rawValue {
        case "less": self = .less
        case "more": self = .more
        case "either": self = .either
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .less: return "less"
        case .more: return "more"
        case .either: return "either"
        case .unlisted(let value): return value
        }
    }
}

public struct Portrait: Hashable, Sendable, Codable {
    public let scales: [PortraitMark]
    public let more: [PortraitMark]
    public let less: [PortraitMark]
    public let others: [PortraitMark]
    public let unplaced: [PortraitMark]

    public init(
        scales: [PortraitMark],
        more: [PortraitMark],
        less: [PortraitMark],
        others: [PortraitMark],
        unplaced: [PortraitMark]
    ) {
        self.scales = scales
        self.more = more
        self.less = less
        self.others = others
        self.unplaced = unplaced
    }

    enum CodingKeys: String, CodingKey {
        case scales
        case more
        case less
        case others
        case unplaced
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        scales = try container.decode([PortraitMark].self, forKey: .scales)
        more = try container.decode([PortraitMark].self, forKey: .more)
        less = try container.decode([PortraitMark].self, forKey: .less)
        others = try container.decode([PortraitMark].self, forKey: .others)
        unplaced = try container.decode([PortraitMark].self, forKey: .unplaced)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(scales, forKey: .scales)
        try container.encode(more, forKey: .more)
        try container.encode(less, forKey: .less)
        try container.encode(others, forKey: .others)
        try container.encode(unplaced, forKey: .unplaced)
    }
}

/// One vibe on the portrait. The band and the sentence are in the fact it names.
public struct PortraitMark: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let factId: String
    public let figureFactId: String?
    public let parts: [PortraitPart]

    public init(
        tagId: TagId,
        factId: String,
        figureFactId: String?,
        parts: [PortraitPart]
    ) {
        self.tagId = tagId
        self.factId = factId
        self.figureFactId = figureFactId
        self.parts = parts
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case factId = "fact_id"
        case figureFactId = "figure_fact_id"
        case parts
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        factId = try container.decode(String.self, forKey: .factId)
        figureFactId = try container.decodeIfPresent(String.self, forKey: .figureFactId)
        parts = try container.decode([PortraitPart].self, forKey: .parts)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(factId, forKey: .factId)
        try container.encode(figureFactId, forKey: .figureFactId)
        try container.encode(parts, forKey: .parts)
    }
}

/// One part of a recipe, and the fact that holds this area's figure for it.
public struct PortraitPart: Hashable, Sendable, Codable {
    public let featureId: FeatureId
    public let hundredths: Int
    public let reading: TermReading
    public let factId: String?

    public init(
        featureId: FeatureId,
        hundredths: Int,
        reading: TermReading,
        factId: String?
    ) {
        self.featureId = featureId
        self.hundredths = hundredths
        self.reading = reading
        self.factId = factId
    }

    enum CodingKeys: String, CodingKey {
        case featureId = "feature_id"
        case hundredths
        case reading
        case factId = "fact_id"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        featureId = try container.decode(FeatureId.self, forKey: .featureId)
        hundredths = try container.decode(Int.self, forKey: .hundredths)
        reading = try container.decode(TermReading.self, forKey: .reading)
        factId = try container.decodeIfPresent(String.self, forKey: .factId)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(featureId, forKey: .featureId)
        try container.encode(hundredths, forKey: .hundredths)
        try container.encode(reading, forKey: .reading)
        try container.encode(factId, forKey: .factId)
    }
}

public struct PreferenceSpec: Hashable, Sendable, Codable {
    public let schemaVersion: Int
    public let tenure: Tenure
    public let budget: Budget
    public let commutes: [Commute]
    public let commuteCombine: Combine
    public let ptBasis: PtBasis
    public let commuteWeight: Double
    public let weights: [FeatureWeight]
    public let tags: [TagWeight]
    public let areas: [AreaRule]
    public let tenureFrom: Provenance
    public let commuteCombineFrom: Provenance
    public let ptBasisFrom: Provenance
    public let commuteWeightFrom: Provenance

    public init(
        schemaVersion: Int = 1,
        tenure: Tenure,
        budget: Budget,
        commutes: [Commute],
        commuteCombine: Combine,
        ptBasis: PtBasis,
        commuteWeight: Double,
        weights: [FeatureWeight],
        tags: [TagWeight],
        areas: [AreaRule],
        tenureFrom: Provenance,
        commuteCombineFrom: Provenance,
        ptBasisFrom: Provenance,
        commuteWeightFrom: Provenance
    ) {
        self.schemaVersion = schemaVersion
        self.tenure = tenure
        self.budget = budget
        self.commutes = commutes
        self.commuteCombine = commuteCombine
        self.ptBasis = ptBasis
        self.commuteWeight = commuteWeight
        self.weights = weights
        self.tags = tags
        self.areas = areas
        self.tenureFrom = tenureFrom
        self.commuteCombineFrom = commuteCombineFrom
        self.ptBasisFrom = ptBasisFrom
        self.commuteWeightFrom = commuteWeightFrom
    }

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case tenure
        case budget
        case commutes
        case commuteCombine = "commute_combine"
        case ptBasis = "pt_basis"
        case commuteWeight = "commute_weight"
        case weights
        case tags
        case areas
        case tenureFrom = "tenure_from"
        case commuteCombineFrom = "commute_combine_from"
        case ptBasisFrom = "pt_basis_from"
        case commuteWeightFrom = "commute_weight_from"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        schemaVersion = try container.decode(Int.self, forKey: .schemaVersion)
        tenure = try container.decode(Tenure.self, forKey: .tenure)
        budget = try container.decode(Budget.self, forKey: .budget)
        commutes = try container.decode([Commute].self, forKey: .commutes)
        commuteCombine = try container.decode(Combine.self, forKey: .commuteCombine)
        ptBasis = try container.decode(PtBasis.self, forKey: .ptBasis)
        commuteWeight = try container.decode(Double.self, forKey: .commuteWeight)
        weights = try container.decode([FeatureWeight].self, forKey: .weights)
        tags = try container.decode([TagWeight].self, forKey: .tags)
        areas = try container.decode([AreaRule].self, forKey: .areas)
        tenureFrom = try container.decode(Provenance.self, forKey: .tenureFrom)
        commuteCombineFrom = try container.decode(Provenance.self, forKey: .commuteCombineFrom)
        ptBasisFrom = try container.decode(Provenance.self, forKey: .ptBasisFrom)
        commuteWeightFrom = try container.decode(Provenance.self, forKey: .commuteWeightFrom)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(schemaVersion, forKey: .schemaVersion)
        try container.encode(tenure, forKey: .tenure)
        try container.encode(budget, forKey: .budget)
        try container.encode(commutes, forKey: .commutes)
        try container.encode(commuteCombine, forKey: .commuteCombine)
        try container.encode(ptBasis, forKey: .ptBasis)
        try container.encode(commuteWeight, forKey: .commuteWeight)
        try container.encode(weights, forKey: .weights)
        try container.encode(tags, forKey: .tags)
        try container.encode(areas, forKey: .areas)
        try container.encode(tenureFrom, forKey: .tenureFrom)
        try container.encode(commuteCombineFrom, forKey: .commuteCombineFrom)
        try container.encode(ptBasisFrom, forKey: .ptBasisFrom)
        try container.encode(commuteWeightFrom, forKey: .commuteWeightFrom)
    }
}

/// What is wrong with one field. A code, never the value that was sent.
public enum Problem: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case missing
    case unknownField
    case wrongType
    case notAllowed
    case badFormat
    case outOfRange
    case invalid
    case unknownPlace
    case unknownArea
    case segmentNotForTenure
    case directionNotAllowed
    case notInRelease
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Problem] = [.missing, .unknownField, .wrongType, .notAllowed, .badFormat, .outOfRange, .invalid, .unknownPlace, .unknownArea, .segmentNotForTenure, .directionNotAllowed, .notInRelease]

    public init(rawValue: String) {
        switch rawValue {
        case "missing": self = .missing
        case "unknown_field": self = .unknownField
        case "wrong_type": self = .wrongType
        case "not_allowed": self = .notAllowed
        case "bad_format": self = .badFormat
        case "out_of_range": self = .outOfRange
        case "invalid": self = .invalid
        case "unknown_place": self = .unknownPlace
        case "unknown_area": self = .unknownArea
        case "segment_not_for_tenure": self = .segmentNotForTenure
        case "direction_not_allowed": self = .directionNotAllowed
        case "not_in_release": self = .notInRelease
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .missing: return "missing"
        case .unknownField: return "unknown_field"
        case .wrongType: return "wrong_type"
        case .notAllowed: return "not_allowed"
        case .badFormat: return "bad_format"
        case .outOfRange: return "out_of_range"
        case .invalid: return "invalid"
        case .unknownPlace: return "unknown_place"
        case .unknownArea: return "unknown_area"
        case .segmentNotForTenure: return "segment_not_for_tenure"
        case .directionNotAllowed: return "direction_not_allowed"
        case .notInRelease: return "not_in_release"
        case .unlisted(let value): return value
        }
    }
}

public enum Provenance: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case stated
    case inferred
    case `default`
    case uiEdit
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Provenance] = [.stated, .inferred, .default, .uiEdit]

    public init(rawValue: String) {
        switch rawValue {
        case "stated": self = .stated
        case "inferred": self = .inferred
        case "default": self = .default
        case "ui_edit": self = .uiEdit
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .stated: return "stated"
        case .inferred: return "inferred"
        case .default: return "default"
        case .uiEdit: return "ui_edit"
        case .unlisted(let value): return value
        }
    }
}

public enum Provider: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case gemini
    case openai
    case deepseek
    case anthropic
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Provider] = [.gemini, .openai, .deepseek, .anthropic]

    public init(rawValue: String) {
        switch rawValue {
        case "gemini": self = .gemini
        case "openai": self = .openai
        case "deepseek": self = .deepseek
        case "anthropic": self = .anthropic
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .gemini: return "gemini"
        case .openai: return "openai"
        case .deepseek: return "deepseek"
        case .anthropic: return "anthropic"
        case .unlisted(let value): return value
        }
    }
}

public enum PtBasis: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case typical
    case justMissed
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [PtBasis] = [.typical, .justMissed]

    public init(rawValue: String) {
        switch rawValue {
        case "typical": self = .typical
        case "just_missed": self = .justMissed
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .typical: return "typical"
        case .justMissed: return "just_missed"
        case .unlisted(let value): return value
        }
    }
}

public struct RankBody: Hashable, Sendable, Codable {
    public let spec: PreferenceSpec
    public let limit: Int
    public let operations: Operations?

    public init(spec: PreferenceSpec, limit: Int = 20, operations: Operations? = nil) {
        self.spec = spec
        self.limit = limit
        self.operations = operations
    }

    enum CodingKeys: String, CodingKey {
        case spec
        case limit
        case operations
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        limit = try container.decodeIfPresent(Int.self, forKey: .limit) ?? 20
        operations = try container.decodeIfPresent(Operations.self, forKey: .operations)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(spec, forKey: .spec)
        try container.encode(limit, forKey: .limit)
        try container.encodeIfPresent(operations, forKey: .operations)
    }
}

public struct RankData: Hashable, Sendable, Codable {
    public let scores: [Score]
    public let ranked: [RankedArea]
    public let areasRanked: Int
    public let areasListed: Int
    public let filtered: [Filtered]
    public let unranked: [Unranked]
    public let emptySpec: Bool
    public let spec: PreferenceSpec
    public let specHash: String
    public let applied: [Applied]
    public let rejected: [Rejected]
    public let places: [NamedPlace]

    public init(
        scores: [Score],
        ranked: [RankedArea],
        areasRanked: Int,
        areasListed: Int,
        filtered: [Filtered],
        unranked: [Unranked],
        emptySpec: Bool,
        spec: PreferenceSpec,
        specHash: String,
        applied: [Applied],
        rejected: [Rejected],
        places: [NamedPlace]
    ) {
        self.scores = scores
        self.ranked = ranked
        self.areasRanked = areasRanked
        self.areasListed = areasListed
        self.filtered = filtered
        self.unranked = unranked
        self.emptySpec = emptySpec
        self.spec = spec
        self.specHash = specHash
        self.applied = applied
        self.rejected = rejected
        self.places = places
    }

    enum CodingKeys: String, CodingKey {
        case scores
        case ranked
        case areasRanked = "areas_ranked"
        case areasListed = "areas_listed"
        case filtered
        case unranked
        case emptySpec = "empty_spec"
        case spec
        case specHash = "spec_hash"
        case applied
        case rejected
        case places
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        scores = try container.decode([Score].self, forKey: .scores)
        ranked = try container.decode([RankedArea].self, forKey: .ranked)
        areasRanked = try container.decode(Int.self, forKey: .areasRanked)
        areasListed = try container.decode(Int.self, forKey: .areasListed)
        filtered = try container.decode([Filtered].self, forKey: .filtered)
        unranked = try container.decode([Unranked].self, forKey: .unranked)
        emptySpec = try container.decode(Bool.self, forKey: .emptySpec)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        specHash = try container.decode(String.self, forKey: .specHash)
        applied = try container.decode([Applied].self, forKey: .applied)
        rejected = try container.decode([Rejected].self, forKey: .rejected)
        places = try container.decode([NamedPlace].self, forKey: .places)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(scores, forKey: .scores)
        try container.encode(ranked, forKey: .ranked)
        try container.encode(areasRanked, forKey: .areasRanked)
        try container.encode(areasListed, forKey: .areasListed)
        try container.encode(filtered, forKey: .filtered)
        try container.encode(unranked, forKey: .unranked)
        try container.encode(emptySpec, forKey: .emptySpec)
        try container.encode(spec, forKey: .spec)
        try container.encode(specHash, forKey: .specHash)
        try container.encode(applied, forKey: .applied)
        try container.encode(rejected, forKey: .rejected)
        try container.encode(places, forKey: .places)
    }
}

public struct RankedArea: Hashable, Sendable, Codable {
    public let areaId: String
    public let rank: Int
    public let score: Double
    public let weightCoverage: Double
    public let contributions: [Contribution]
    public let legs: [CommuteLeg]
    public let budget: BudgetFit?
    public let untestedFilters: [FilterReason]
    public let strip: [StripMark]

    public init(
        areaId: String,
        rank: Int,
        score: Double,
        weightCoverage: Double,
        contributions: [Contribution],
        legs: [CommuteLeg],
        budget: BudgetFit?,
        untestedFilters: [FilterReason],
        strip: [StripMark]
    ) {
        self.areaId = areaId
        self.rank = rank
        self.score = score
        self.weightCoverage = weightCoverage
        self.contributions = contributions
        self.legs = legs
        self.budget = budget
        self.untestedFilters = untestedFilters
        self.strip = strip
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case rank
        case score
        case weightCoverage = "weight_coverage"
        case contributions
        case legs
        case budget
        case untestedFilters = "untested_filters"
        case strip
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        rank = try container.decode(Int.self, forKey: .rank)
        score = try container.decode(Double.self, forKey: .score)
        weightCoverage = try container.decode(Double.self, forKey: .weightCoverage)
        contributions = try container.decode([Contribution].self, forKey: .contributions)
        legs = try container.decode([CommuteLeg].self, forKey: .legs)
        budget = try container.decodeIfPresent(BudgetFit.self, forKey: .budget)
        untestedFilters = try container.decode([FilterReason].self, forKey: .untestedFilters)
        strip = try container.decode([StripMark].self, forKey: .strip)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(rank, forKey: .rank)
        try container.encode(score, forKey: .score)
        try container.encode(weightCoverage, forKey: .weightCoverage)
        try container.encode(contributions, forKey: .contributions)
        try container.encode(legs, forKey: .legs)
        try container.encode(budget, forKey: .budget)
        try container.encode(untestedFilters, forKey: .untestedFilters)
        try container.encode(strip, forKey: .strip)
    }
}

/// Who reads what a person types, and what people are told of it.
///
/// It is how the service is set, and no part of the release. A client shows
/// `notice` by the box before anything is typed, as it is served, and writes
/// no provider's name or terms of its own.
public struct Reader: Hashable, Sendable, Codable {
    public let modelReads: Bool
    public let provider: Provider?
    public let company: String?
    public let notice: String
    public let termsUrl: String?
    public let settingsSent: Bool

    public init(
        modelReads: Bool,
        provider: Provider?,
        company: String?,
        notice: String,
        termsUrl: String?,
        settingsSent: Bool
    ) {
        self.modelReads = modelReads
        self.provider = provider
        self.company = company
        self.notice = notice
        self.termsUrl = termsUrl
        self.settingsSent = settingsSent
    }

    enum CodingKeys: String, CodingKey {
        case modelReads = "model_reads"
        case provider
        case company
        case notice
        case termsUrl = "terms_url"
        case settingsSent = "settings_sent"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        modelReads = try container.decode(Bool.self, forKey: .modelReads)
        provider = try container.decodeIfPresent(Provider.self, forKey: .provider)
        company = try container.decodeIfPresent(String.self, forKey: .company)
        notice = try container.decode(String.self, forKey: .notice)
        termsUrl = try container.decodeIfPresent(String.self, forKey: .termsUrl)
        settingsSent = try container.decode(Bool.self, forKey: .settingsSent)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(modelReads, forKey: .modelReads)
        try container.encode(provider, forKey: .provider)
        try container.encode(company, forKey: .company)
        try container.encode(notice, forKey: .notice)
        try container.encode(termsUrl, forKey: .termsUrl)
        try container.encode(settingsSent, forKey: .settingsSent)
    }
}

/// How much of one vibe's recipe a release carries, and what the vibe waits on.
///
/// It is of the release and of no area. An area may have a figure for fewer
/// parts than the release carries, and its own fact says so.
public struct RecipeHeld: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let held: Int
    public let needed: Int
    public let placed: Bool
    public let waitsOn: [WaitsOn]

    public init(
        tagId: TagId,
        held: Int,
        needed: Int,
        placed: Bool,
        waitsOn: [WaitsOn]
    ) {
        self.tagId = tagId
        self.held = held
        self.needed = needed
        self.placed = placed
        self.waitsOn = waitsOn
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case held
        case needed
        case placed
        case waitsOn = "waits_on"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        held = try container.decode(Int.self, forKey: .held)
        needed = try container.decode(Int.self, forKey: .needed)
        placed = try container.decode(Bool.self, forKey: .placed)
        waitsOn = try container.decode([WaitsOn].self, forKey: .waitsOn)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(held, forKey: .held)
        try container.encode(needed, forKey: .needed)
        try container.encode(placed, forKey: .placed)
        try container.encode(waitsOn, forKey: .waitsOn)
    }
}

public enum RejectReason: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case unknownPlace
    case unknownArea
    case notInRelease
    case tooManyCommutes
    case noSuchCommute
    case outOfRange
    case segmentNotForTenure
    case directionNotAllowed
    case crimeNeedsExplicitRequest
    case mismatchedChoice
    case nothingToChange
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [RejectReason] = [.unknownPlace, .unknownArea, .notInRelease, .tooManyCommutes, .noSuchCommute, .outOfRange, .segmentNotForTenure, .directionNotAllowed, .crimeNeedsExplicitRequest, .mismatchedChoice, .nothingToChange]

    public init(rawValue: String) {
        switch rawValue {
        case "unknown_place": self = .unknownPlace
        case "unknown_area": self = .unknownArea
        case "not_in_release": self = .notInRelease
        case "too_many_commutes": self = .tooManyCommutes
        case "no_such_commute": self = .noSuchCommute
        case "out_of_range": self = .outOfRange
        case "segment_not_for_tenure": self = .segmentNotForTenure
        case "direction_not_allowed": self = .directionNotAllowed
        case "crime_needs_explicit_request": self = .crimeNeedsExplicitRequest
        case "mismatched_choice": self = .mismatchedChoice
        case "nothing_to_change": self = .nothingToChange
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .unknownPlace: return "unknown_place"
        case .unknownArea: return "unknown_area"
        case .notInRelease: return "not_in_release"
        case .tooManyCommutes: return "too_many_commutes"
        case .noSuchCommute: return "no_such_commute"
        case .outOfRange: return "out_of_range"
        case .segmentNotForTenure: return "segment_not_for_tenure"
        case .directionNotAllowed: return "direction_not_allowed"
        case .crimeNeedsExplicitRequest: return "crime_needs_explicit_request"
        case .mismatchedChoice: return "mismatched_choice"
        case .nothingToChange: return "nothing_to_change"
        case .unlisted(let value): return value
        }
    }
}

public struct Rejected: Hashable, Sendable, Codable {
    public let group: OpsGroup
    public let index: Int
    public let reason: RejectReason

    public init(group: OpsGroup, index: Int, reason: RejectReason) {
        self.group = group
        self.index = index
        self.reason = reason
    }

    enum CodingKeys: String, CodingKey {
        case group
        case index
        case reason
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        group = try container.decode(OpsGroup.self, forKey: .group)
        index = try container.decode(Int.self, forKey: .index)
        reason = try container.decode(RejectReason.self, forKey: .reason)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(group, forKey: .group)
        try container.encode(index, forKey: .index)
        try container.encode(reason, forKey: .reason)
    }
}

/// What is said of the rents of a release, where each is of a wider place than an area.
///
/// It holds words and no figure. A client shows them where no one area is
/// spoken of: the first beside the count of the areas a firm budget to rent
/// left out, and the second on the page of methods.
public struct RentsSaid: Hashable, Sendable, Codable {
    public let ofAPlace: String
    public let caution: String

    public init(ofAPlace: String, caution: String) {
        self.ofAPlace = ofAPlace
        self.caution = caution
    }

    enum CodingKeys: String, CodingKey {
        case ofAPlace = "of_a_place"
        case caution
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        ofAPlace = try container.decode(String.self, forKey: .ofAPlace)
        caution = try container.decode(String.self, forKey: .caution)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(ofAPlace, forKey: .ofAPlace)
        try container.encode(caution, forKey: .caution)
    }
}

/// Which words of the text an edit rests on: where they start and end, never the words.
///
/// `start` and `end` count the characters of the text as it was typed, as
/// Python counts them, so `text[start:end]` is the words. An edit made of
/// several parts, as a budget is of "renting", "2 bed" and "£1,500", has one
/// of these for each part. They are for showing a person which of their
/// words made each edit. Nothing stores or logs them.
public struct RestsOn: Hashable, Sendable, Codable {
    public let group: OpsGroup
    public let index: Int
    public let start: Int
    public let end: Int

    public init(
        group: OpsGroup,
        index: Int,
        start: Int,
        end: Int
    ) {
        self.group = group
        self.index = index
        self.start = start
        self.end = end
    }

    enum CodingKeys: String, CodingKey {
        case group
        case index
        case start
        case end
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        group = try container.decode(OpsGroup.self, forKey: .group)
        index = try container.decode(Int.self, forKey: .index)
        start = try container.decode(Int.self, forKey: .start)
        end = try container.decode(Int.self, forKey: .end)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(group, forKey: .group)
        try container.encode(index, forKey: .index)
        try container.encode(start, forKey: .start)
        try container.encode(end, forKey: .end)
    }
}

/// What stands beside a vibe that is a rough guide, wherever the vibe is shown.
public struct RoughGuide: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let label: String
    public let why: String

    public init(tagId: TagId, label: String, why: String) {
        self.tagId = tagId
        self.label = label
        self.why = why
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case label
        case why
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        label = try container.decode(String.self, forKey: .label)
        why = try container.decode(String.self, forKey: .why)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(label, forKey: .label)
        try container.encode(why, forKey: .why)
    }
}

public struct Score: Hashable, Sendable, Codable {
    public let areaId: String
    public let score: Double
    public let counted: Int
    public let present: Int

    public init(
        areaId: String,
        score: Double,
        counted: Int,
        present: Int
    ) {
        self.areaId = areaId
        self.score = score
        self.counted = counted
        self.present = present
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case score
        case counted
        case present
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        score = try container.decode(Double.self, forKey: .score)
        counted = try container.decode(Int.self, forKey: .counted)
        present = try container.decode(Int.self, forKey: .present)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(score, forKey: .score)
        try container.encode(counted, forKey: .counted)
        try container.encode(present, forKey: .present)
    }
}

public enum Segment: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case room
    case studio
    case bed1
    case bed2
    case bed3
    case bed4plus
    case flat
    case terraced
    case semiDetached
    case detached
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Segment] = [.room, .studio, .bed1, .bed2, .bed3, .bed4plus, .flat, .terraced, .semiDetached, .detached]

    public init(rawValue: String) {
        switch rawValue {
        case "room": self = .room
        case "studio": self = .studio
        case "bed_1": self = .bed1
        case "bed_2": self = .bed2
        case "bed_3": self = .bed3
        case "bed_4plus": self = .bed4plus
        case "flat": self = .flat
        case "terraced": self = .terraced
        case "semi_detached": self = .semiDetached
        case "detached": self = .detached
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .room: return "room"
        case .studio: return "studio"
        case .bed1: return "bed_1"
        case .bed2: return "bed_2"
        case .bed3: return "bed_3"
        case .bed4plus: return "bed_4plus"
        case .flat: return "flat"
        case .terraced: return "terraced"
        case .semiDetached: return "semi_detached"
        case .detached: return "detached"
        case .unlisted(let value): return value
        }
    }
}

public enum SegmentChoice: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case room
    case studio
    case bed1
    case bed2
    case bed3
    case bed4plus
    case flat
    case terraced
    case semiDetached
    case detached
    case unchanged
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [SegmentChoice] = [.room, .studio, .bed1, .bed2, .bed3, .bed4plus, .flat, .terraced, .semiDetached, .detached, .unchanged]

    public init(rawValue: String) {
        switch rawValue {
        case "room": self = .room
        case "studio": self = .studio
        case "bed_1": self = .bed1
        case "bed_2": self = .bed2
        case "bed_3": self = .bed3
        case "bed_4plus": self = .bed4plus
        case "flat": self = .flat
        case "terraced": self = .terraced
        case "semi_detached": self = .semiDetached
        case "detached": self = .detached
        case "unchanged": self = .unchanged
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .room: return "room"
        case .studio: return "studio"
        case .bed1: return "bed_1"
        case .bed2: return "bed_2"
        case .bed3: return "bed_3"
        case .bed4plus: return "bed_4plus"
        case .flat: return "flat"
        case .terraced: return "terraced"
        case .semiDetached: return "semi_detached"
        case .detached: return "detached"
        case .unchanged: return "unchanged"
        case .unlisted(let value): return value
        }
    }
}

public enum SentenceOrigin: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case template
    case model
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [SentenceOrigin] = [.template, .model]

    public init(rawValue: String) {
        switch rawValue {
        case "template": self = .template
        case "model": self = .model
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .template: return "template"
        case .model: return "model"
        case .unlisted(let value): return value
        }
    }
}

/// The limits of section 5.2, with the cutoffs of the release that is loaded.
///
/// A form that keeps to these never offers a value the reducer would refuse.
public struct ServedLimits: Hashable, Sendable, Codable {
    public let cutoffMinutes: Cutoffs
    public let maxText: Int
    public let maxBodyBytes: Int
    public let reasonMinUtility: Double
    public let tradeOffMaxUtility: Double
    public let budgetStepLargePercent: Int
    public let budgetStepSmallPercent: Int
    public let buy: MoneyLimits
    public let maxCommutes: Int
    public let minutesMax: Int
    public let minutesMin: Int
    public let minutesStepLarge: Int
    public let minutesStepSmall: Int
    public let rent: MoneyLimits
    public let weightStepLarge: Double
    public let weightStepSmall: Double
    public let weightUnit: Double

    public init(
        cutoffMinutes: Cutoffs,
        maxText: Int,
        maxBodyBytes: Int,
        reasonMinUtility: Double,
        tradeOffMaxUtility: Double,
        budgetStepLargePercent: Int = 15,
        budgetStepSmallPercent: Int = 5,
        buy: MoneyLimits = MoneyLimits(minimum: 50000, maximum: 20000000, unit: 5000),
        maxCommutes: Int = 3,
        minutesMax: Int = 120,
        minutesMin: Int = 10,
        minutesStepLarge: Int = 15,
        minutesStepSmall: Int = 5,
        rent: MoneyLimits = MoneyLimits(minimum: 300, maximum: 20000, unit: 25),
        weightStepLarge: Double = 0.25,
        weightStepSmall: Double = 0.1,
        weightUnit: Double = 0.05
    ) {
        self.cutoffMinutes = cutoffMinutes
        self.maxText = maxText
        self.maxBodyBytes = maxBodyBytes
        self.reasonMinUtility = reasonMinUtility
        self.tradeOffMaxUtility = tradeOffMaxUtility
        self.budgetStepLargePercent = budgetStepLargePercent
        self.budgetStepSmallPercent = budgetStepSmallPercent
        self.buy = buy
        self.maxCommutes = maxCommutes
        self.minutesMax = minutesMax
        self.minutesMin = minutesMin
        self.minutesStepLarge = minutesStepLarge
        self.minutesStepSmall = minutesStepSmall
        self.rent = rent
        self.weightStepLarge = weightStepLarge
        self.weightStepSmall = weightStepSmall
        self.weightUnit = weightUnit
    }

    enum CodingKeys: String, CodingKey {
        case cutoffMinutes = "cutoff_minutes"
        case maxText = "max_text"
        case maxBodyBytes = "max_body_bytes"
        case reasonMinUtility = "reason_min_utility"
        case tradeOffMaxUtility = "trade_off_max_utility"
        case budgetStepLargePercent = "budget_step_large_percent"
        case budgetStepSmallPercent = "budget_step_small_percent"
        case buy
        case maxCommutes = "max_commutes"
        case minutesMax = "minutes_max"
        case minutesMin = "minutes_min"
        case minutesStepLarge = "minutes_step_large"
        case minutesStepSmall = "minutes_step_small"
        case rent
        case weightStepLarge = "weight_step_large"
        case weightStepSmall = "weight_step_small"
        case weightUnit = "weight_unit"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        cutoffMinutes = try container.decode(Cutoffs.self, forKey: .cutoffMinutes)
        maxText = try container.decode(Int.self, forKey: .maxText)
        maxBodyBytes = try container.decode(Int.self, forKey: .maxBodyBytes)
        reasonMinUtility = try container.decode(Double.self, forKey: .reasonMinUtility)
        tradeOffMaxUtility = try container.decode(Double.self, forKey: .tradeOffMaxUtility)
        budgetStepLargePercent = try container.decodeIfPresent(Int.self, forKey: .budgetStepLargePercent) ?? 15
        budgetStepSmallPercent = try container.decodeIfPresent(Int.self, forKey: .budgetStepSmallPercent) ?? 5
        buy = try container.decodeIfPresent(MoneyLimits.self, forKey: .buy) ?? MoneyLimits(minimum: 50000, maximum: 20000000, unit: 5000)
        maxCommutes = try container.decodeIfPresent(Int.self, forKey: .maxCommutes) ?? 3
        minutesMax = try container.decodeIfPresent(Int.self, forKey: .minutesMax) ?? 120
        minutesMin = try container.decodeIfPresent(Int.self, forKey: .minutesMin) ?? 10
        minutesStepLarge = try container.decodeIfPresent(Int.self, forKey: .minutesStepLarge) ?? 15
        minutesStepSmall = try container.decodeIfPresent(Int.self, forKey: .minutesStepSmall) ?? 5
        rent = try container.decodeIfPresent(MoneyLimits.self, forKey: .rent) ?? MoneyLimits(minimum: 300, maximum: 20000, unit: 25)
        weightStepLarge = try container.decodeIfPresent(Double.self, forKey: .weightStepLarge) ?? 0.25
        weightStepSmall = try container.decodeIfPresent(Double.self, forKey: .weightStepSmall) ?? 0.1
        weightUnit = try container.decodeIfPresent(Double.self, forKey: .weightUnit) ?? 0.05
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(cutoffMinutes, forKey: .cutoffMinutes)
        try container.encode(maxText, forKey: .maxText)
        try container.encode(maxBodyBytes, forKey: .maxBodyBytes)
        try container.encode(reasonMinUtility, forKey: .reasonMinUtility)
        try container.encode(tradeOffMaxUtility, forKey: .tradeOffMaxUtility)
        try container.encode(budgetStepLargePercent, forKey: .budgetStepLargePercent)
        try container.encode(budgetStepSmallPercent, forKey: .budgetStepSmallPercent)
        try container.encode(buy, forKey: .buy)
        try container.encode(maxCommutes, forKey: .maxCommutes)
        try container.encode(minutesMax, forKey: .minutesMax)
        try container.encode(minutesMin, forKey: .minutesMin)
        try container.encode(minutesStepLarge, forKey: .minutesStepLarge)
        try container.encode(minutesStepSmall, forKey: .minutesStepSmall)
        try container.encode(rent, forKey: .rent)
        try container.encode(weightStepLarge, forKey: .weightStepLarge)
        try container.encode(weightStepSmall, forKey: .weightStepSmall)
        try container.encode(weightUnit, forKey: .weightUnit)
    }
}

public enum Setting: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case commuteCombine
    case ptBasis
    case commuteWeight
    case budgetWeight
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Setting] = [.commuteCombine, .ptBasis, .commuteWeight, .budgetWeight]

    public init(rawValue: String) {
        switch rawValue {
        case "commute_combine": self = .commuteCombine
        case "pt_basis": self = .ptBasis
        case "commute_weight": self = .commuteWeight
        case "budget_weight": self = .budgetWeight
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .commuteCombine: return "commute_combine"
        case .ptBasis: return "pt_basis"
        case .commuteWeight: return "commute_weight"
        case .budgetWeight: return "budget_weight"
        case .unlisted(let value): return value
        }
    }
}

public enum SettingAction: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case set
    case nudge
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [SettingAction] = [.set, .nudge]

    public init(rawValue: String) {
        switch rawValue {
        case "set": self = .set
        case "nudge": self = .nudge
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .set: return "set"
        case .nudge: return "nudge"
        case .unlisted(let value): return value
        }
    }
}

public struct SettingEdit: Hashable, Sendable, Codable {
    public let action: SettingAction
    public let setting: Setting
    public let choice: Choice
    public let value: Double
    public let step: Step
    public let provenance: EditProvenance

    public init(
        action: SettingAction,
        setting: Setting,
        choice: Choice,
        value: Double,
        step: Step,
        provenance: EditProvenance
    ) {
        self.action = action
        self.setting = setting
        self.choice = choice
        self.value = value
        self.step = step
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case action
        case setting
        case choice
        case value
        case step
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        action = try container.decode(SettingAction.self, forKey: .action)
        setting = try container.decode(Setting.self, forKey: .setting)
        choice = try container.decode(Choice.self, forKey: .choice)
        value = try container.decode(Double.self, forKey: .value)
        step = try container.decode(Step.self, forKey: .step)
        provenance = try container.decode(EditProvenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(action, forKey: .action)
        try container.encode(setting, forKey: .setting)
        try container.encode(choice, forKey: .choice)
        try container.encode(value, forKey: .value)
        try container.encode(step, forKey: .step)
        try container.encode(provenance, forKey: .provenance)
    }
}

public struct ShareBody: Hashable, Sendable, Codable {
    public let spec: PreferenceSpec
    public let exactDestinations: Bool

    public init(spec: PreferenceSpec, exactDestinations: Bool = false) {
        self.spec = spec
        self.exactDestinations = exactDestinations
    }

    enum CodingKeys: String, CodingKey {
        case spec
        case exactDestinations = "exact_destinations"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        exactDestinations = try container.decodeIfPresent(Bool.self, forKey: .exactDestinations) ?? false
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(spec, forKey: .spec)
        try container.encode(exactDestinations, forKey: .exactDestinations)
    }
}

public struct ShareCreated: Hashable, Sendable, Codable {
    public let shareId: String
    public let spec: PreferenceSpec
    public let coarsened: Bool
    public let places: [NamedPlace]

    public init(
        shareId: String,
        spec: PreferenceSpec,
        coarsened: Bool,
        places: [NamedPlace]
    ) {
        self.shareId = shareId
        self.spec = spec
        self.coarsened = coarsened
        self.places = places
    }

    enum CodingKeys: String, CodingKey {
        case shareId = "share_id"
        case spec
        case coarsened
        case places
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        shareId = try container.decode(String.self, forKey: .shareId)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        coarsened = try container.decode(Bool.self, forKey: .coarsened)
        places = try container.decode([NamedPlace].self, forKey: .places)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(shareId, forKey: .shareId)
        try container.encode(spec, forKey: .spec)
        try container.encode(coarsened, forKey: .coarsened)
        try container.encode(places, forKey: .places)
    }
}

/// A shared search, ranked now on the release that is loaded.
public struct ShareData: Hashable, Sendable, Codable {
    public let scores: [Score]
    public let ranked: [RankedArea]
    public let areasRanked: Int
    public let areasListed: Int
    public let filtered: [Filtered]
    public let unranked: [Unranked]
    public let emptySpec: Bool
    public let spec: PreferenceSpec
    public let specHash: String
    public let coarsened: Bool
    public let stale: Bool
    public let originalReleaseId: String
    public let places: [NamedPlace]

    public init(
        scores: [Score],
        ranked: [RankedArea],
        areasRanked: Int,
        areasListed: Int,
        filtered: [Filtered],
        unranked: [Unranked],
        emptySpec: Bool,
        spec: PreferenceSpec,
        specHash: String,
        coarsened: Bool,
        stale: Bool,
        originalReleaseId: String,
        places: [NamedPlace]
    ) {
        self.scores = scores
        self.ranked = ranked
        self.areasRanked = areasRanked
        self.areasListed = areasListed
        self.filtered = filtered
        self.unranked = unranked
        self.emptySpec = emptySpec
        self.spec = spec
        self.specHash = specHash
        self.coarsened = coarsened
        self.stale = stale
        self.originalReleaseId = originalReleaseId
        self.places = places
    }

    enum CodingKeys: String, CodingKey {
        case scores
        case ranked
        case areasRanked = "areas_ranked"
        case areasListed = "areas_listed"
        case filtered
        case unranked
        case emptySpec = "empty_spec"
        case spec
        case specHash = "spec_hash"
        case coarsened
        case stale
        case originalReleaseId = "original_release_id"
        case places
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        scores = try container.decode([Score].self, forKey: .scores)
        ranked = try container.decode([RankedArea].self, forKey: .ranked)
        areasRanked = try container.decode(Int.self, forKey: .areasRanked)
        areasListed = try container.decode(Int.self, forKey: .areasListed)
        filtered = try container.decode([Filtered].self, forKey: .filtered)
        unranked = try container.decode([Unranked].self, forKey: .unranked)
        emptySpec = try container.decode(Bool.self, forKey: .emptySpec)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        specHash = try container.decode(String.self, forKey: .specHash)
        coarsened = try container.decode(Bool.self, forKey: .coarsened)
        stale = try container.decode(Bool.self, forKey: .stale)
        originalReleaseId = try container.decode(String.self, forKey: .originalReleaseId)
        places = try container.decode([NamedPlace].self, forKey: .places)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(scores, forKey: .scores)
        try container.encode(ranked, forKey: .ranked)
        try container.encode(areasRanked, forKey: .areasRanked)
        try container.encode(areasListed, forKey: .areasListed)
        try container.encode(filtered, forKey: .filtered)
        try container.encode(unranked, forKey: .unranked)
        try container.encode(emptySpec, forKey: .emptySpec)
        try container.encode(spec, forKey: .spec)
        try container.encode(specHash, forKey: .specHash)
        try container.encode(coarsened, forKey: .coarsened)
        try container.encode(stale, forKey: .stale)
        try container.encode(originalReleaseId, forKey: .originalReleaseId)
        try container.encode(places, forKey: .places)
    }
}

/// One of the areas most like this one. The sentence is in the `likeness` fact it names.
public struct Similar: Hashable, Sendable, Codable {
    public let areaId: String
    public let factId: String

    public init(areaId: String, factId: String) {
        self.areaId = areaId
        self.factId = factId
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case factId = "fact_id"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        factId = try container.decode(String.self, forKey: .factId)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(factId, forKey: .factId)
    }
}

public struct Source: Hashable, Sendable, Codable {
    public let sourceId: String
    public let name: String
    public let publisher: String
    public let licence: String
    public let attribution: String
    public let url: String
    public let retrievedOn: String
    public let creditBesideFigures: Bool
    public let saidWithAttribution: String?

    public init(
        sourceId: String,
        name: String,
        publisher: String,
        licence: String,
        attribution: String,
        url: String,
        retrievedOn: String,
        creditBesideFigures: Bool = false,
        saidWithAttribution: String? = nil
    ) {
        self.sourceId = sourceId
        self.name = name
        self.publisher = publisher
        self.licence = licence
        self.attribution = attribution
        self.url = url
        self.retrievedOn = retrievedOn
        self.creditBesideFigures = creditBesideFigures
        self.saidWithAttribution = saidWithAttribution
    }

    enum CodingKeys: String, CodingKey {
        case sourceId = "source_id"
        case name
        case publisher
        case licence
        case attribution
        case url
        case retrievedOn = "retrieved_on"
        case creditBesideFigures = "credit_beside_figures"
        case saidWithAttribution = "said_with_attribution"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        sourceId = try container.decode(String.self, forKey: .sourceId)
        name = try container.decode(String.self, forKey: .name)
        publisher = try container.decode(String.self, forKey: .publisher)
        licence = try container.decode(String.self, forKey: .licence)
        attribution = try container.decode(String.self, forKey: .attribution)
        url = try container.decode(String.self, forKey: .url)
        retrievedOn = try container.decode(String.self, forKey: .retrievedOn)
        creditBesideFigures = try container.decodeIfPresent(Bool.self, forKey: .creditBesideFigures) ?? false
        saidWithAttribution = try container.decodeIfPresent(String.self, forKey: .saidWithAttribution)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(sourceId, forKey: .sourceId)
        try container.encode(name, forKey: .name)
        try container.encode(publisher, forKey: .publisher)
        try container.encode(licence, forKey: .licence)
        try container.encode(attribution, forKey: .attribution)
        try container.encode(url, forKey: .url)
        try container.encode(retrievedOn, forKey: .retrievedOn)
        try container.encode(creditBesideFigures, forKey: .creditBesideFigures)
        try container.encode(saidWithAttribution, forKey: .saidWithAttribution)
    }
}

/// A stretch of the text: where it starts and ends, counted as `RestsOn` counts.
public struct Span: Hashable, Sendable, Codable {
    public let start: Int
    public let end: Int

    public init(start: Int, end: Int) {
        self.start = start
        self.end = end
    }

    enum CodingKeys: String, CodingKey {
        case start
        case end
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        start = try container.decode(Int.self, forKey: .start)
        end = try container.decode(Int.self, forKey: .end)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(start, forKey: .start)
        try container.encode(end, forKey: .end)
    }
}

public struct StationAccess: Hashable, Sendable, Codable {
    public let areaId: String
    public let stationId: String
    public let name: String
    public let walkMinutes: Int
    public let lines: [String]
    public let stepFree: Bool
    public let nearest: Bool

    public init(
        areaId: String,
        stationId: String,
        name: String,
        walkMinutes: Int,
        lines: [String],
        stepFree: Bool,
        nearest: Bool
    ) {
        self.areaId = areaId
        self.stationId = stationId
        self.name = name
        self.walkMinutes = walkMinutes
        self.lines = lines
        self.stepFree = stepFree
        self.nearest = nearest
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case stationId = "station_id"
        case name
        case walkMinutes = "walk_minutes"
        case lines
        case stepFree = "step_free"
        case nearest
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        stationId = try container.decode(String.self, forKey: .stationId)
        name = try container.decode(String.self, forKey: .name)
        walkMinutes = try container.decode(Int.self, forKey: .walkMinutes)
        lines = try container.decode([String].self, forKey: .lines)
        stepFree = try container.decode(Bool.self, forKey: .stepFree)
        nearest = try container.decode(Bool.self, forKey: .nearest)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(stationId, forKey: .stationId)
        try container.encode(name, forKey: .name)
        try container.encode(walkMinutes, forKey: .walkMinutes)
        try container.encode(lines, forKey: .lines)
        try container.encode(stepFree, forKey: .stepFree)
        try container.encode(nearest, forKey: .nearest)
    }
}

public enum Step: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case nothing
    case upSmall
    case upLarge
    case downSmall
    case downLarge
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Step] = [.nothing, .upSmall, .upLarge, .downSmall, .downLarge]

    public init(rawValue: String) {
        switch rawValue {
        case "none": self = .nothing
        case "up_small": self = .upSmall
        case "up_large": self = .upLarge
        case "down_small": self = .downSmall
        case "down_large": self = .downLarge
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .nothing: return "none"
        case .upSmall: return "up_small"
        case .upLarge: return "up_large"
        case .downSmall: return "down_small"
        case .downLarge: return "down_large"
        case .unlisted(let value): return value
        }
    }
}

public enum Strictness: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case soft
    case hard
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Strictness] = [.soft, .hard]

    public init(rawValue: String) {
        switch rawValue {
        case "soft": self = .soft
        case "hard": self = .hard
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .soft: return "soft"
        case .hard: return "hard"
        case .unlisted(let value): return value
        }
    }
}

public enum StrictnessChoice: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case soft
    case hard
    case unchanged
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [StrictnessChoice] = [.soft, .hard, .unchanged]

    public init(rawValue: String) {
        switch rawValue {
        case "soft": self = .soft
        case "hard": self = .hard
        case "unchanged": self = .unchanged
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .soft: return "soft"
        case .hard: return "hard"
        case .unchanged: return "unchanged"
        case .unlisted(let value): return value
        }
    }
}

/// Where an area sits on one vibe, for the strip under its name. Shown, never scored.
public struct StripMark: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let band: Int
    public let spreadLow: Int
    public let spreadHigh: Int
    public let asked: Bool
    public let toward: Toward?
    public let factId: String

    public init(
        tagId: TagId,
        band: Int,
        spreadLow: Int,
        spreadHigh: Int,
        asked: Bool,
        toward: Toward?,
        factId: String
    ) {
        self.tagId = tagId
        self.band = band
        self.spreadLow = spreadLow
        self.spreadHigh = spreadHigh
        self.asked = asked
        self.toward = toward
        self.factId = factId
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case band
        case spreadLow = "spread_low"
        case spreadHigh = "spread_high"
        case asked
        case toward
        case factId = "fact_id"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        band = try container.decode(Int.self, forKey: .band)
        spreadLow = try container.decode(Int.self, forKey: .spreadLow)
        spreadHigh = try container.decode(Int.self, forKey: .spreadHigh)
        asked = try container.decode(Bool.self, forKey: .asked)
        toward = try container.decodeIfPresent(Toward.self, forKey: .toward)
        factId = try container.decode(String.self, forKey: .factId)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(band, forKey: .band)
        try container.encode(spreadLow, forKey: .spreadLow)
        try container.encode(spreadHigh, forKey: .spreadHigh)
        try container.encode(asked, forKey: .asked)
        try container.encode(toward, forKey: .toward)
        try container.encode(factId, forKey: .factId)
    }
}

/// An offer: a thing that was noticed, in four parts. The person chooses.
///
/// What it would do (`does`), the person's own words (`spans`, shown within
/// `shown`), what follows for areas (`follows`), and the choices. Every word
/// is Burro's own. The person's words are never here: a client cuts them
/// from the text it holds, by where they stand.
public struct Suggestion: Hashable, Sendable, Codable {
    public let target: String
    public let label: String
    public let does: String
    public let spans: [Span]
    public let shown: Span
    public let follows: String
    public let said: [String]
    public let choices: [SuggestionChoice]
    public let note: String
    public let readBy: InterpreterName
    public let addAll: String
    public let needs: String
    public let asksPlace: Bool
    public let namedAt: Span?
    public let options: [ClarifyOption]

    public init(
        target: String,
        label: String,
        does: String,
        spans: [Span],
        shown: Span,
        follows: String,
        said: [String],
        choices: [SuggestionChoice],
        note: String,
        readBy: InterpreterName,
        addAll: String,
        needs: String,
        asksPlace: Bool,
        namedAt: Span?,
        options: [ClarifyOption]
    ) {
        self.target = target
        self.label = label
        self.does = does
        self.spans = spans
        self.shown = shown
        self.follows = follows
        self.said = said
        self.choices = choices
        self.note = note
        self.readBy = readBy
        self.addAll = addAll
        self.needs = needs
        self.asksPlace = asksPlace
        self.namedAt = namedAt
        self.options = options
    }

    enum CodingKeys: String, CodingKey {
        case target
        case label
        case does
        case spans
        case shown
        case follows
        case said
        case choices
        case note
        case readBy = "read_by"
        case addAll = "add_all"
        case needs
        case asksPlace = "asks_place"
        case namedAt = "named_at"
        case options
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        target = try container.decode(String.self, forKey: .target)
        label = try container.decode(String.self, forKey: .label)
        does = try container.decode(String.self, forKey: .does)
        spans = try container.decode([Span].self, forKey: .spans)
        shown = try container.decode(Span.self, forKey: .shown)
        follows = try container.decode(String.self, forKey: .follows)
        said = try container.decode([String].self, forKey: .said)
        choices = try container.decode([SuggestionChoice].self, forKey: .choices)
        note = try container.decode(String.self, forKey: .note)
        readBy = try container.decode(InterpreterName.self, forKey: .readBy)
        addAll = try container.decode(String.self, forKey: .addAll)
        needs = try container.decode(String.self, forKey: .needs)
        asksPlace = try container.decode(Bool.self, forKey: .asksPlace)
        namedAt = try container.decodeIfPresent(Span.self, forKey: .namedAt)
        options = try container.decode([ClarifyOption].self, forKey: .options)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(target, forKey: .target)
        try container.encode(label, forKey: .label)
        try container.encode(does, forKey: .does)
        try container.encode(spans, forKey: .spans)
        try container.encode(shown, forKey: .shown)
        try container.encode(follows, forKey: .follows)
        try container.encode(said, forKey: .said)
        try container.encode(choices, forKey: .choices)
        try container.encode(note, forKey: .note)
        try container.encode(readBy, forKey: .readBy)
        try container.encode(addAll, forKey: .addAll)
        try container.encode(needs, forKey: .needs)
        try container.encode(asksPlace, forKey: .asksPlace)
        try container.encode(namedAt, forKey: .namedAt)
        try container.encode(options, forKey: .options)
    }
}

/// One way a person may take an offer, and the edits it would make.
///
/// It has a name of its own here because core has another `Choice`, what a
/// setting is set to, and one document cannot hold two records of one name.
public struct SuggestionChoice: Hashable, Sendable, Codable {
    public let id: String
    public let direction: SuggestionDirection
    public let label: String
    public let guess: Bool
    public let operations: Operations

    public init(
        id: String,
        direction: SuggestionDirection,
        label: String,
        guess: Bool,
        operations: Operations
    ) {
        self.id = id
        self.direction = direction
        self.label = label
        self.guess = guess
        self.operations = operations
    }

    enum CodingKeys: String, CodingKey {
        case id
        case direction
        case label
        case guess
        case operations
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        direction = try container.decode(SuggestionDirection.self, forKey: .direction)
        label = try container.decode(String.self, forKey: .label)
        guess = try container.decode(Bool.self, forKey: .guess)
        operations = try container.decode(Operations.self, forKey: .operations)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(direction, forKey: .direction)
        try container.encode(label, forKey: .label)
        try container.encode(guess, forKey: .guess)
        try container.encode(operations, forKey: .operations)
    }
}

/// What a person may choose of a thing the reader noticed. It never guesses one.
public enum SuggestionDirection: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case more
    case less
    case ignore
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [SuggestionDirection] = [.more, .less, .ignore]

    public init(rawValue: String) {
        switch rawValue {
        case "more": self = .more
        case "less": self = .less
        case "ignore": self = .ignore
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .more: return "more"
        case .less: return "less"
        case .ignore: return "ignore"
        case .unlisted(let value): return value
        }
    }
}

/// Whether a vibe is as sure as the rest, or a rough guide. It says so of itself.
///
/// It has these two values and no other. It is no number, and no word of praise or
/// blame: it says how far a vibe is to be trusted, and nothing of any place. No client
/// works it out. A vibe that does not say is as sure as the rest.
public enum Sureness: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case asTheRest
    case roughGuide
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Sureness] = [.asTheRest, .roughGuide]

    public init(rawValue: String) {
        switch rawValue {
        case "as_the_rest": self = .asTheRest
        case "rough_guide": self = .roughGuide
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .asTheRest: return "as_the_rest"
        case .roughGuide: return "rough_guide"
        case .unlisted(let value): return value
        }
    }
}

public struct Tag: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let label: String
    public let shortLabel: String
    public let family: Family
    public let shape: TagShape
    public let lowEnd: String?
    public let highEnd: String?
    public let meaning: String
    public let cannotSee: [String]
    public let lens: Bool
    public let strip: Bool
    public let table: Bool
    public let shelfWord: String?
    public let shelfToward: Toward?
    public let shelfOrder: Int?
    public let terms: [TagTerm]
    public let sureness: Sureness

    public init(
        tagId: TagId,
        label: String,
        shortLabel: String,
        family: Family,
        shape: TagShape,
        lowEnd: String?,
        highEnd: String?,
        meaning: String,
        cannotSee: [String],
        lens: Bool,
        strip: Bool,
        table: Bool,
        shelfWord: String?,
        shelfToward: Toward?,
        shelfOrder: Int?,
        terms: [TagTerm],
        sureness: Sureness = .asTheRest
    ) {
        self.tagId = tagId
        self.label = label
        self.shortLabel = shortLabel
        self.family = family
        self.shape = shape
        self.lowEnd = lowEnd
        self.highEnd = highEnd
        self.meaning = meaning
        self.cannotSee = cannotSee
        self.lens = lens
        self.strip = strip
        self.table = table
        self.shelfWord = shelfWord
        self.shelfToward = shelfToward
        self.shelfOrder = shelfOrder
        self.terms = terms
        self.sureness = sureness
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case label
        case shortLabel = "short_label"
        case family
        case shape
        case lowEnd = "low_end"
        case highEnd = "high_end"
        case meaning
        case cannotSee = "cannot_see"
        case lens
        case strip
        case table
        case shelfWord = "shelf_word"
        case shelfToward = "shelf_toward"
        case shelfOrder = "shelf_order"
        case terms
        case sureness
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        label = try container.decode(String.self, forKey: .label)
        shortLabel = try container.decode(String.self, forKey: .shortLabel)
        family = try container.decode(Family.self, forKey: .family)
        shape = try container.decode(TagShape.self, forKey: .shape)
        lowEnd = try container.decodeIfPresent(String.self, forKey: .lowEnd)
        highEnd = try container.decodeIfPresent(String.self, forKey: .highEnd)
        meaning = try container.decode(String.self, forKey: .meaning)
        cannotSee = try container.decode([String].self, forKey: .cannotSee)
        lens = try container.decode(Bool.self, forKey: .lens)
        strip = try container.decode(Bool.self, forKey: .strip)
        table = try container.decode(Bool.self, forKey: .table)
        shelfWord = try container.decodeIfPresent(String.self, forKey: .shelfWord)
        shelfToward = try container.decodeIfPresent(Toward.self, forKey: .shelfToward)
        shelfOrder = try container.decodeIfPresent(Int.self, forKey: .shelfOrder)
        terms = try container.decode([TagTerm].self, forKey: .terms)
        sureness = try container.decodeIfPresent(Sureness.self, forKey: .sureness) ?? .asTheRest
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(label, forKey: .label)
        try container.encode(shortLabel, forKey: .shortLabel)
        try container.encode(family, forKey: .family)
        try container.encode(shape, forKey: .shape)
        try container.encode(lowEnd, forKey: .lowEnd)
        try container.encode(highEnd, forKey: .highEnd)
        try container.encode(meaning, forKey: .meaning)
        try container.encode(cannotSee, forKey: .cannotSee)
        try container.encode(lens, forKey: .lens)
        try container.encode(strip, forKey: .strip)
        try container.encode(table, forKey: .table)
        try container.encode(shelfWord, forKey: .shelfWord)
        try container.encode(shelfToward, forKey: .shelfToward)
        try container.encode(shelfOrder, forKey: .shelfOrder)
        try container.encode(terms, forKey: .terms)
        try container.encode(sureness, forKey: .sureness)
    }
}

public struct TagEdit: Hashable, Sendable, Codable {
    public let action: WeightAction
    public let tagId: TagId
    public let value: Double
    public let step: Step
    public let toward: TowardChoice
    public let provenance: EditProvenance

    public init(
        action: WeightAction,
        tagId: TagId,
        value: Double,
        step: Step,
        toward: TowardChoice,
        provenance: EditProvenance
    ) {
        self.action = action
        self.tagId = tagId
        self.value = value
        self.step = step
        self.toward = toward
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case action
        case tagId = "tag_id"
        case value
        case step
        case toward
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        action = try container.decode(WeightAction.self, forKey: .action)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        value = try container.decode(Double.self, forKey: .value)
        step = try container.decode(Step.self, forKey: .step)
        toward = try container.decode(TowardChoice.self, forKey: .toward)
        provenance = try container.decode(EditProvenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(action, forKey: .action)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(value, forKey: .value)
        try container.encode(step, forKey: .step)
        try container.encode(toward, forKey: .toward)
        try container.encode(provenance, forKey: .provenance)
    }
}

/// On screen a tag is a vibe. Seven ids of catalogue version 1 are retired and never reused:
/// buzzy, evening_venues, historic_character, creative, strong_high_street,
/// near_universities and waterside.
public enum TagId: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case leafy
    case villageFeel
    case pace
    case quietResidential
    case builtAge
    case everydayOnFoot
    case parksCloseBy
    case homes
    case foodie
    case familyAmenities
    case worksWarehouses
    case streetCharacter
    case wellConnected
    case familyArea
    case youngProfessionals
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TagId] = [.leafy, .villageFeel, .pace, .quietResidential, .builtAge, .everydayOnFoot, .parksCloseBy, .homes, .foodie, .familyAmenities, .worksWarehouses, .streetCharacter, .wellConnected, .familyArea, .youngProfessionals]

    public init(rawValue: String) {
        switch rawValue {
        case "leafy": self = .leafy
        case "village_feel": self = .villageFeel
        case "pace": self = .pace
        case "quiet_residential": self = .quietResidential
        case "built_age": self = .builtAge
        case "everyday_on_foot": self = .everydayOnFoot
        case "parks_close_by": self = .parksCloseBy
        case "homes": self = .homes
        case "foodie": self = .foodie
        case "family_amenities": self = .familyAmenities
        case "works_warehouses": self = .worksWarehouses
        case "street_character": self = .streetCharacter
        case "well_connected": self = .wellConnected
        case "family_area": self = .familyArea
        case "young_professionals": self = .youngProfessionals
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .leafy: return "leafy"
        case .villageFeel: return "village_feel"
        case .pace: return "pace"
        case .quietResidential: return "quiet_residential"
        case .builtAge: return "built_age"
        case .everydayOnFoot: return "everyday_on_foot"
        case .parksCloseBy: return "parks_close_by"
        case .homes: return "homes"
        case .foodie: return "foodie"
        case .familyAmenities: return "family_amenities"
        case .worksWarehouses: return "works_warehouses"
        case .streetCharacter: return "street_character"
        case .wellConnected: return "well_connected"
        case .familyArea: return "family_area"
        case .youngProfessionals: return "young_professionals"
        case .unlisted(let value): return value
        }
    }
}

public enum TagShape: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case scale
    case oneWay
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TagShape] = [.scale, .oneWay]

    public init(rawValue: String) {
        switch rawValue {
        case "scale": self = .scale
        case "one_way": self = .oneWay
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .scale: return "scale"
        case .oneWay: return "one_way"
        case .unlisted(let value): return value
        }
    }
}

public struct TagTerm: Hashable, Sendable, Codable {
    public let featureId: FeatureId
    public let hundredths: Int
    public let reading: TermReading

    public init(featureId: FeatureId, hundredths: Int, reading: TermReading) {
        self.featureId = featureId
        self.hundredths = hundredths
        self.reading = reading
    }

    enum CodingKeys: String, CodingKey {
        case featureId = "feature_id"
        case hundredths
        case reading
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        featureId = try container.decode(FeatureId.self, forKey: .featureId)
        hundredths = try container.decode(Int.self, forKey: .hundredths)
        reading = try container.decode(TermReading.self, forKey: .reading)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(featureId, forKey: .featureId)
        try container.encode(hundredths, forKey: .hundredths)
        try container.encode(reading, forKey: .reading)
    }
}

/// Where one area sits on one vibe. `score` is for ranking and is never printed.
///
/// `band` is what is shown: one of five, counted from the low end. The
/// spread is the bands the middle half of the area's homes span, so a mixed
/// area is drawn as a range and never as a point in the middle.
public struct TagValue: Hashable, Sendable, Codable {
    public let areaId: String
    public let tagId: TagId
    public let raw: Double?
    public let score: Double?
    public let coverage: Double
    public let band: Int?
    public let spreadLow: Int?
    public let spreadHigh: Int?

    public init(
        areaId: String,
        tagId: TagId,
        raw: Double?,
        score: Double?,
        coverage: Double,
        band: Int?,
        spreadLow: Int?,
        spreadHigh: Int?
    ) {
        self.areaId = areaId
        self.tagId = tagId
        self.raw = raw
        self.score = score
        self.coverage = coverage
        self.band = band
        self.spreadLow = spreadLow
        self.spreadHigh = spreadHigh
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case tagId = "tag_id"
        case raw
        case score
        case coverage
        case band
        case spreadLow = "spread_low"
        case spreadHigh = "spread_high"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        raw = try container.decodeIfPresent(Double.self, forKey: .raw)
        score = try container.decodeIfPresent(Double.self, forKey: .score)
        coverage = try container.decode(Double.self, forKey: .coverage)
        band = try container.decodeIfPresent(Int.self, forKey: .band)
        spreadLow = try container.decodeIfPresent(Int.self, forKey: .spreadLow)
        spreadHigh = try container.decodeIfPresent(Int.self, forKey: .spreadHigh)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(raw, forKey: .raw)
        try container.encode(score, forKey: .score)
        try container.encode(coverage, forKey: .coverage)
        try container.encode(band, forKey: .band)
        try container.encode(spreadLow, forKey: .spreadLow)
        try container.encode(spreadHigh, forKey: .spreadHigh)
    }
}

public struct TagWeight: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let weight: Double
    public let provenance: Provenance
    public let toward: Toward

    public init(
        tagId: TagId,
        weight: Double,
        provenance: Provenance,
        toward: Toward = .high
    ) {
        self.tagId = tagId
        self.weight = weight
        self.provenance = provenance
        self.toward = toward
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case weight
        case provenance
        case toward
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        weight = try container.decode(Double.self, forKey: .weight)
        provenance = try container.decode(Provenance.self, forKey: .provenance)
        toward = try container.decodeIfPresent(Toward.self, forKey: .toward) ?? .high
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(weight, forKey: .weight)
        try container.encode(provenance, forKey: .provenance)
        try container.encode(toward, forKey: .toward)
    }
}

public enum TemplateId: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case area
    case feature
    case featureCrime
    case vibe
    case vibeRange
    case vibeUnknown
    case costRent
    case costBuy
    case costBuyMedian
    case costBuySold
    case costRentRecorded
    case budgetUnder
    case budgetOver
    case budgetAt
    case budgetUnderMedian
    case budgetOverMedian
    case budgetAtMedian
    case budgetUnderRecorded
    case budgetOverRecorded
    case budgetAtRecorded
    case travelPt
    case travelPtOver
    case travelOther
    case travelOtherOver
    case travelBeyond
    case travelEstimated
    case station
    case stationNearby
    case missing
    case missingJourney
    case likeness
    case likenessSame
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TemplateId] = [.area, .feature, .featureCrime, .vibe, .vibeRange, .vibeUnknown, .costRent, .costBuy, .costBuyMedian, .costBuySold, .costRentRecorded, .budgetUnder, .budgetOver, .budgetAt, .budgetUnderMedian, .budgetOverMedian, .budgetAtMedian, .budgetUnderRecorded, .budgetOverRecorded, .budgetAtRecorded, .travelPt, .travelPtOver, .travelOther, .travelOtherOver, .travelBeyond, .travelEstimated, .station, .stationNearby, .missing, .missingJourney, .likeness, .likenessSame]

    public init(rawValue: String) {
        switch rawValue {
        case "area": self = .area
        case "feature": self = .feature
        case "feature_crime": self = .featureCrime
        case "vibe": self = .vibe
        case "vibe_range": self = .vibeRange
        case "vibe_unknown": self = .vibeUnknown
        case "cost_rent": self = .costRent
        case "cost_buy": self = .costBuy
        case "cost_buy_median": self = .costBuyMedian
        case "cost_buy_sold": self = .costBuySold
        case "cost_rent_recorded": self = .costRentRecorded
        case "budget_under": self = .budgetUnder
        case "budget_over": self = .budgetOver
        case "budget_at": self = .budgetAt
        case "budget_under_median": self = .budgetUnderMedian
        case "budget_over_median": self = .budgetOverMedian
        case "budget_at_median": self = .budgetAtMedian
        case "budget_under_recorded": self = .budgetUnderRecorded
        case "budget_over_recorded": self = .budgetOverRecorded
        case "budget_at_recorded": self = .budgetAtRecorded
        case "travel_pt": self = .travelPt
        case "travel_pt_over": self = .travelPtOver
        case "travel_other": self = .travelOther
        case "travel_other_over": self = .travelOtherOver
        case "travel_beyond": self = .travelBeyond
        case "travel_estimated": self = .travelEstimated
        case "station": self = .station
        case "station_nearby": self = .stationNearby
        case "missing": self = .missing
        case "missing_journey": self = .missingJourney
        case "likeness": self = .likeness
        case "likeness_same": self = .likenessSame
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .area: return "area"
        case .feature: return "feature"
        case .featureCrime: return "feature_crime"
        case .vibe: return "vibe"
        case .vibeRange: return "vibe_range"
        case .vibeUnknown: return "vibe_unknown"
        case .costRent: return "cost_rent"
        case .costBuy: return "cost_buy"
        case .costBuyMedian: return "cost_buy_median"
        case .costBuySold: return "cost_buy_sold"
        case .costRentRecorded: return "cost_rent_recorded"
        case .budgetUnder: return "budget_under"
        case .budgetOver: return "budget_over"
        case .budgetAt: return "budget_at"
        case .budgetUnderMedian: return "budget_under_median"
        case .budgetOverMedian: return "budget_over_median"
        case .budgetAtMedian: return "budget_at_median"
        case .budgetUnderRecorded: return "budget_under_recorded"
        case .budgetOverRecorded: return "budget_over_recorded"
        case .budgetAtRecorded: return "budget_at_recorded"
        case .travelPt: return "travel_pt"
        case .travelPtOver: return "travel_pt_over"
        case .travelOther: return "travel_other"
        case .travelOtherOver: return "travel_other_over"
        case .travelBeyond: return "travel_beyond"
        case .travelEstimated: return "travel_estimated"
        case .station: return "station"
        case .stationNearby: return "station_nearby"
        case .missing: return "missing"
        case .missingJourney: return "missing_journey"
        case .likeness: return "likeness"
        case .likenessSame: return "likeness_same"
        case .unlisted(let value): return value
        }
    }
}

public enum Tenure: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case rent
    case buy
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Tenure] = [.rent, .buy]

    public init(rawValue: String) {
        switch rawValue {
        case "rent": self = .rent
        case "buy": self = .buy
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .rent: return "rent"
        case .buy: return "buy"
        case .unlisted(let value): return value
        }
    }
}

public enum TenureChoice: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case rent
    case buy
    case unchanged
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TenureChoice] = [.rent, .buy, .unchanged]

    public init(rawValue: String) {
        switch rawValue {
        case "rent": self = .rent
        case "buy": self = .buy
        case "unchanged": self = .unchanged
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .rent: return "rent"
        case .buy: return "buy"
        case .unchanged: return "unchanged"
        case .unlisted(let value): return value
        }
    }
}

public enum TermReading: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case high
    case low
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TermReading] = [.high, .low]

    public init(rawValue: String) {
        switch rawValue {
        case "high": self = .high
        case "low": self = .low
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .high: return "high"
        case .low: return "low"
        case .unlisted(let value): return value
        }
    }
}

/// Which end of a vibe is asked for. A one-way vibe has the high end alone.
public enum Toward: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case high
    case low
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Toward] = [.high, .low]

    public init(rawValue: String) {
        switch rawValue {
        case "high": self = .high
        case "low": self = .low
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .high: return "high"
        case .low: return "low"
        case .unlisted(let value): return value
        }
    }
}

public enum TowardChoice: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case high
    case low
    case `default`
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TowardChoice] = [.high, .low, .default]

    public init(rawValue: String) {
        switch rawValue {
        case "high": self = .high
        case "low": self = .low
        case "default": self = .default
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .high: return "high"
        case .low: return "low"
        case .default: return "default"
        case .unlisted(let value): return value
        }
    }
}

public enum TravelStatus: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case ok
    case beyondCutoff
    case missing
    case estimated
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TravelStatus] = [.ok, .beyondCutoff, .missing, .estimated]

    public init(rawValue: String) {
        switch rawValue {
        case "ok": self = .ok
        case "beyond_cutoff": self = .beyondCutoff
        case "missing": self = .missing
        case "estimated": self = .estimated
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .ok: return "ok"
        case .beyondCutoff: return "beyond_cutoff"
        case .missing: return "missing"
        case .estimated: return "estimated"
        case .unlisted(let value): return value
        }
    }
}

/// Something that was asked for which nothing measures, and where it was said.
public struct UnmetAt: Hashable, Sendable, Codable {
    public let category: UnmetCategory
    public let span: Span

    public init(category: UnmetCategory, span: Span) {
        self.category = category
        self.span = span
    }

    enum CodingKeys: String, CodingKey {
        case category
        case span
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        category = try container.decode(UnmetCategory.self, forKey: .category)
        span = try container.decode(Span.self, forKey: .span)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(category, forKey: .category)
        try container.encode(span, forKey: .span)
    }
}

public enum UnmetCategory: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case broadband
    case floodRisk
    case healthServices
    case driving
    case listings
    case affordabilityVerdict
    case communityAmenities
    case outsideTheCity
    case streetCleanliness
    case upkeep
    case ratings
    case pricesAndHours
    case mobileCoverage
    case changeOverTime
    case other
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [UnmetCategory] = [.broadband, .floodRisk, .healthServices, .driving, .listings, .affordabilityVerdict, .communityAmenities, .outsideTheCity, .streetCleanliness, .upkeep, .ratings, .pricesAndHours, .mobileCoverage, .changeOverTime, .other]

    public init(rawValue: String) {
        switch rawValue {
        case "broadband": self = .broadband
        case "flood_risk": self = .floodRisk
        case "health_services": self = .healthServices
        case "driving": self = .driving
        case "listings": self = .listings
        case "affordability_verdict": self = .affordabilityVerdict
        case "community_amenities": self = .communityAmenities
        case "outside_the_city": self = .outsideTheCity
        case "street_cleanliness": self = .streetCleanliness
        case "upkeep": self = .upkeep
        case "ratings": self = .ratings
        case "prices_and_hours": self = .pricesAndHours
        case "mobile_coverage": self = .mobileCoverage
        case "change_over_time": self = .changeOverTime
        case "other": self = .other
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .broadband: return "broadband"
        case .floodRisk: return "flood_risk"
        case .healthServices: return "health_services"
        case .driving: return "driving"
        case .listings: return "listings"
        case .affordabilityVerdict: return "affordability_verdict"
        case .communityAmenities: return "community_amenities"
        case .outsideTheCity: return "outside_the_city"
        case .streetCleanliness: return "street_cleanliness"
        case .upkeep: return "upkeep"
        case .ratings: return "ratings"
        case .pricesAndHours: return "prices_and_hours"
        case .mobileCoverage: return "mobile_coverage"
        case .changeOverTime: return "change_over_time"
        case .other: return "other"
        case .unlisted(let value): return value
        }
    }
}

public struct Unranked: Hashable, Sendable, Codable {
    public let areaId: String
    public let reason: UnrankedReason
    public let missing: [String]

    public init(areaId: String, reason: UnrankedReason, missing: [String]) {
        self.areaId = areaId
        self.reason = reason
        self.missing = missing
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case reason
        case missing
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        reason = try container.decode(UnrankedReason.self, forKey: .reason)
        missing = try container.decode([String].self, forKey: .missing)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(reason, forKey: .reason)
        try container.encode(missing, forKey: .missing)
    }
}

public enum UnrankedReason: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case notRankable
    case insufficientData
    case characterUnknown
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [UnrankedReason] = [.notRankable, .insufficientData, .characterUnknown]

    public init(rawValue: String) {
        switch rawValue {
        case "not_rankable": self = .notRankable
        case "insufficient_data": self = .insufficientData
        case "character_unknown": self = .characterUnknown
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .notRankable: return "not_rankable"
        case .insufficientData: return "insufficient_data"
        case .characterUnknown: return "character_unknown"
        case .unlisted(let value): return value
        }
    }
}

public struct VibeBands: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let marks: [BandMark]

    public init(tagId: TagId, marks: [BandMark]) {
        self.tagId = tagId
        self.marks = marks
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case marks
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        marks = try container.decode([BandMark].self, forKey: .marks)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(marks, forKey: .marks)
    }
}

/// A part of a recipe that a release carries no measure for. It is named, never filled in.
public struct WaitsOn: Hashable, Sendable, Codable {
    public let featureId: FeatureId
    public let label: String
    public let hundredths: Int

    public init(featureId: FeatureId, label: String, hundredths: Int) {
        self.featureId = featureId
        self.label = label
        self.hundredths = hundredths
    }

    enum CodingKeys: String, CodingKey {
        case featureId = "feature_id"
        case label
        case hundredths
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        featureId = try container.decode(FeatureId.self, forKey: .featureId)
        label = try container.decode(String.self, forKey: .label)
        hundredths = try container.decode(Int.self, forKey: .hundredths)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(featureId, forKey: .featureId)
        try container.encode(label, forKey: .label)
        try container.encode(hundredths, forKey: .hundredths)
    }
}

public enum WeightAction: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case set
    case nudge
    case remove
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [WeightAction] = [.set, .nudge, .remove]

    public init(rawValue: String) {
        switch rawValue {
        case "set": self = .set
        case "nudge": self = .nudge
        case "remove": self = .remove
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .set: return "set"
        case .nudge: return "nudge"
        case .remove: return "remove"
        case .unlisted(let value): return value
        }
    }
}

public struct WeightEdit: Hashable, Sendable, Codable {
    public let action: WeightAction
    public let featureId: FeatureId
    public let value: Double
    public let step: Step
    public let direction: DirectionChoice
    public let provenance: EditProvenance

    public init(
        action: WeightAction,
        featureId: FeatureId,
        value: Double,
        step: Step,
        direction: DirectionChoice,
        provenance: EditProvenance
    ) {
        self.action = action
        self.featureId = featureId
        self.value = value
        self.step = step
        self.direction = direction
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case action
        case featureId = "feature_id"
        case value
        case step
        case direction
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        action = try container.decode(WeightAction.self, forKey: .action)
        featureId = try container.decode(FeatureId.self, forKey: .featureId)
        value = try container.decode(Double.self, forKey: .value)
        step = try container.decode(Step.self, forKey: .step)
        direction = try container.decode(DirectionChoice.self, forKey: .direction)
        provenance = try container.decode(EditProvenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(action, forKey: .action)
        try container.encode(featureId, forKey: .featureId)
        try container.encode(value, forKey: .value)
        try container.encode(step, forKey: .step)
        try container.encode(direction, forKey: .direction)
        try container.encode(provenance, forKey: .provenance)
    }
}

/// One of several shapes. Each is tried in the contract's order.
public enum GeometryCoordinates: Hashable, Sendable, Codable {
    case polygon([[LonLat]])
    case multiPolygon([[[LonLat]]])

    public init(from decoder: any Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let value = try? container.decode([[LonLat]].self) {
            self = .polygon(value)
            return
        }
        if let value = try? container.decode([[[LonLat]]].self) {
            self = .multiPolygon(value)
            return
        }
        throw DecodingError.dataCorruptedError(
            in: container, debugDescription: "No shape of GeometryCoordinates fits.")
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .polygon(let value): try container.encode(value)
        case .multiPolygon(let value): try container.encode(value)
        }
    }
}
