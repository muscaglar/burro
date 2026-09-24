// Generated from contracts/openapi.json by apps/ios/scripts/generate.py.
// Never edited by hand: change the source and run `make generate`.
// source-sha256: 06d39ed9bd188b88a51e52be7d59dfe6b17588cfb2a3752794964144ab34772f

import Foundation

/// What these files were generated from, for the test that says when they are stale.
public enum GeneratedFrom {
    /// The SHA-256 of `contracts/openapi.json` when the models were written.
    public static let contractSHA256 = "06d39ed9bd188b88a51e52be7d59dfe6b17588cfb2a3752794964144ab34772f"
    /// The title and the version the contract gives itself.
    public static let contractTitle = "Burro API"
    public static let contractVersion = "1"
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
    public let facts: [Fact]

    public init(
        area: Neighbourhood,
        features: [FeatureValue],
        tags: [TagValue],
        cost: [CostEstimate],
        stations: [StationAccess],
        neighbours: [AreaSummary],
        facts: [Fact]
    ) {
        self.area = area
        self.features = features
        self.tags = tags
        self.cost = cost
        self.stations = stations
        self.neighbours = neighbours
        self.facts = facts
    }

    enum CodingKeys: String, CodingKey {
        case area
        case features
        case tags
        case cost
        case stations
        case neighbours
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

    public init(
        areaId: String,
        slug: String,
        name: String,
        borough: String,
        centroid: LonLat,
        rankable: Bool
    ) {
        self.areaId = areaId
        self.slug = slug
        self.name = name
        self.borough = borough
        self.centroid = centroid
        self.rankable = rankable
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case slug
        case name
        case borough
        case centroid
        case rankable
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        slug = try container.decode(String.self, forKey: .slug)
        name = try container.decode(String.self, forKey: .name)
        borough = try container.decode(String.self, forKey: .borough)
        centroid = try container.decode(LonLat.self, forKey: .centroid)
        rankable = try container.decode(Bool.self, forKey: .rankable)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(slug, forKey: .slug)
        try container.encode(name, forKey: .name)
        try container.encode(borough, forKey: .borough)
        try container.encode(centroid, forKey: .centroid)
        try container.encode(rankable, forKey: .rankable)
    }
}

public struct AreasData: Hashable, Sendable, Codable {
    public let areas: [AreaSummary]

    public init(areas: [AreaSummary]) {
        self.areas = areas
    }

    enum CodingKeys: String, CodingKey {
        case areas
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areas = try container.decode([AreaSummary].self, forKey: .areas)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areas, forKey: .areas)
    }
}

/// What was chosen for an edit because the text did not say.
public struct Assumption: Hashable, Sendable, Codable {
    public let code: AssumptionCode
    public let group: OpsGroup
    public let index: Int

    public init(code: AssumptionCode, group: OpsGroup, index: Int) {
        self.code = code
        self.group = group
        self.index = index
    }

    enum CodingKeys: String, CodingKey {
        case code
        case group
        case index
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        code = try container.decode(AssumptionCode.self, forKey: .code)
        group = try container.decode(OpsGroup.self, forKey: .group)
        index = try container.decode(Int.self, forKey: .index)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(code, forKey: .code)
        try container.encode(group, forKey: .group)
        try container.encode(index, forKey: .index)
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
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [AssumptionCode] = [.tenure, .segment, .strictness, .mode, .maxMinutes, .direction, .weight]

    public init(rawValue: String) {
        switch rawValue {
        case "tenure": self = .tenure
        case "segment": self = .segment
        case "strictness": self = .strictness
        case "mode": self = .mode
        case "max_minutes": self = .maxMinutes
        case "direction": self = .direction
        case "weight": self = .weight
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
        case .unlisted(let value): return value
        }
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
    public let upperQuartile: Int
    public let margin: Int
    public let utility: Double
    public let confidence: Confidence
    public let asOf: String

    public init(
        upperQuartile: Int,
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
        upperQuartile = try container.decode(Int.self, forKey: .upperQuartile)
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

    public init(
        placeId: String,
        mode: Mode,
        status: TravelStatus,
        minutes: Int?,
        minutesTypical: Int?,
        minutesJustMissed: Int?,
        utility: Double?
    ) {
        self.placeId = placeId
        self.mode = mode
        self.status = status
        self.minutes = minutes
        self.minutesTypical = minutesTypical
        self.minutesJustMissed = minutesJustMissed
        self.utility = utility
    }

    enum CodingKeys: String, CodingKey {
        case placeId = "place_id"
        case mode
        case status
        case minutes
        case minutesTypical = "minutes_typical"
        case minutesJustMissed = "minutes_just_missed"
        case utility
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

    public init(
        areaId: String,
        value: Double?,
        percentile: Double?,
        utility: Double?,
        contribution: Double?,
        factId: String?
    ) {
        self.areaId = areaId
        self.value = value
        self.percentile = percentile
        self.utility = utility
        self.contribution = contribution
        self.factId = factId
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case value
        case percentile
        case utility
        case contribution
        case factId = "fact_id"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        value = try container.decodeIfPresent(Double.self, forKey: .value)
        percentile = try container.decodeIfPresent(Double.self, forKey: .percentile)
        utility = try container.decodeIfPresent(Double.self, forKey: .utility)
        contribution = try container.decodeIfPresent(Double.self, forKey: .contribution)
        factId = try container.decodeIfPresent(String.self, forKey: .factId)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(value, forKey: .value)
        try container.encode(percentile, forKey: .percentile)
        try container.encode(utility, forKey: .utility)
        try container.encode(contribution, forKey: .contribution)
        try container.encode(factId, forKey: .factId)
    }
}

public struct CompareData: Hashable, Sendable, Codable {
    public let areas: [ComparedArea]
    public let rows: [CompareRow]
    public let facts: [Fact]

    public init(areas: [ComparedArea], rows: [CompareRow], facts: [Fact]) {
        self.areas = areas
        self.rows = rows
        self.facts = facts
    }

    enum CodingKeys: String, CodingKey {
        case areas
        case rows
        case facts
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areas = try container.decode([ComparedArea].self, forKey: .areas)
        rows = try container.decode([CompareRow].self, forKey: .rows)
        facts = try container.decode([Fact].self, forKey: .facts)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areas, forKey: .areas)
        try container.encode(rows, forKey: .rows)
        try container.encode(facts, forKey: .facts)
    }
}

public struct CompareRow: Hashable, Sendable, Codable {
    public let component: String
    public let label: String
    public let weight: Double
    public let cells: [CompareCell]

    public init(
        component: String,
        label: String,
        weight: Double,
        cells: [CompareCell]
    ) {
        self.component = component
        self.label = label
        self.weight = weight
        self.cells = cells
    }

    enum CodingKeys: String, CodingKey {
        case component
        case label
        case weight
        case cells
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        component = try container.decode(String.self, forKey: .component)
        label = try container.decode(String.self, forKey: .label)
        weight = try container.decode(Double.self, forKey: .weight)
        cells = try container.decode([CompareCell].self, forKey: .cells)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(component, forKey: .component)
        try container.encode(label, forKey: .label)
        try container.encode(weight, forKey: .weight)
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
    case notRankable
    case insufficientData
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [CompareStatus] = [.ranked, .excluded, .notSelected, .overBudget, .commuteCap, .notRankable, .insufficientData]

    public init(rawValue: String) {
        switch rawValue {
        case "ranked": self = .ranked
        case "excluded": self = .excluded
        case "not_selected": self = .notSelected
        case "over_budget": self = .overBudget
        case "commute_cap": self = .commuteCap
        case "not_rankable": self = .notRankable
        case "insufficient_data": self = .insufficientData
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
        case .notRankable: return "not_rankable"
        case .insufficientData: return "insufficient_data"
        case .unlisted(let value): return value
        }
    }
}

public struct ComparedArea: Hashable, Sendable, Codable {
    public let areaId: String
    public let name: String
    public let status: CompareStatus

    public init(areaId: String, name: String, status: CompareStatus) {
        self.areaId = areaId
        self.name = name
        self.status = status
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case name
        case status
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        name = try container.decode(String.self, forKey: .name)
        status = try container.decode(CompareStatus.self, forKey: .status)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(name, forKey: .name)
        try container.encode(status, forKey: .status)
    }
}

public enum Confidence: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case high
    case medium
    case low
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Confidence] = [.high, .medium, .low]

    public init(rawValue: String) {
        switch rawValue {
        case "high": self = .high
        case "medium": self = .medium
        case "low": self = .low
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .high: return "high"
        case .medium: return "medium"
        case .low: return "low"
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

public struct CostEstimate: Hashable, Sendable, Codable {
    public let areaId: String
    public let tenure: Tenure
    public let segment: Segment
    public let lowerQuartile: Int
    public let median: Int
    public let upperQuartile: Int
    public let confidence: Confidence
    public let asOf: String
    public let sourceIds: [String]

    public init(
        areaId: String,
        tenure: Tenure,
        segment: Segment,
        lowerQuartile: Int,
        median: Int,
        upperQuartile: Int,
        confidence: Confidence,
        asOf: String,
        sourceIds: [String]
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
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        tenure = try container.decode(Tenure.self, forKey: .tenure)
        segment = try container.decode(Segment.self, forKey: .segment)
        lowerQuartile = try container.decode(Int.self, forKey: .lowerQuartile)
        median = try container.decode(Int.self, forKey: .median)
        upperQuartile = try container.decode(Int.self, forKey: .upperQuartile)
        confidence = try container.decode(Confidence.self, forKey: .confidence)
        asOf = try container.decode(String.self, forKey: .asOf)
        sourceIds = try container.decode([String].self, forKey: .sourceIds)
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

public enum Dimension: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case crime
    case schools
    case greenWater
    case airNoise
    case venuesCulture
    case homes
    case stationAccess
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [Dimension] = [.crime, .schools, .greenWater, .airNoise, .venuesCulture, .homes, .stationAccess]

    public init(rawValue: String) {
        switch rawValue {
        case "crime": self = .crime
        case "schools": self = .schools
        case "green_water": self = .greenWater
        case "air_noise": self = .airNoise
        case "venues_culture": self = .venuesCulture
        case "homes": self = .homes
        case "station_access": self = .stationAccess
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
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [ErrorCode] = [.malformedJson, .bodyTooLarge, .unsupportedMediaType, .internalError, .notFound, .methodNotAllowed, .invalidRequest, .invalidText, .invalidSpec, .invalidOperations, .invalidCompare, .invalidQuery, .unknownPlace, .unknownArea, .areaNotFound, .shareNotFound, .releaseChanged]

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
    public let explanations: [Explanation]
    public let facts: [Fact]

    public init(explanations: [Explanation], facts: [Fact]) {
        self.explanations = explanations
        self.facts = facts
    }

    enum CodingKeys: String, CodingKey {
        case explanations
        case facts
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        explanations = try container.decode([Explanation].self, forKey: .explanations)
        facts = try container.decode([Fact].self, forKey: .facts)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
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
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [FactKind] = [.area, .feature, .tag, .cost, .budgetFit, .travel, .station, .missing]

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
        case .unlisted(let value): return value
        }
    }
}

public struct FactSource: Hashable, Sendable, Codable {
    public let sourceId: String
    public let name: String

    public init(sourceId: String, name: String) {
        self.sourceId = sourceId
        self.name = name
    }

    enum CodingKeys: String, CodingKey {
        case sourceId = "source_id"
        case name
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        sourceId = try container.decode(String.self, forKey: .sourceId)
        name = try container.decode(String.self, forKey: .name)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(sourceId, forKey: .sourceId)
        try container.encode(name, forKey: .name)
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
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [FeatureId] = [.crimeViolenceRobbery, .crimeBurglaryTheft, .schoolPrimaryNearby, .schoolPrimaryAttainment, .schoolSecondaryAttainment, .universityProximity, .greenCover, .parkProximity, .playSpaceProximity, .waterAccess, .airNo2, .noiseExposure, .venueFoodDrink, .venueEvening, .venueIndependent, .cultureVenues, .highstreetAccess, .homesFlats, .homesPre1919, .homesDensity, .conservationCover, .stationWalk, .stationLines]

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
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [FilterReason] = [.excluded, .notSelected, .overBudget, .commuteCap]

    public init(rawValue: String) {
        switch rawValue {
        case "excluded": self = .excluded
        case "not_selected": self = .notSelected
        case "over_budget": self = .overBudget
        case "commute_cap": self = .commuteCap
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .excluded: return "excluded"
        case .notSelected: return "not_selected"
        case .overBudget: return "over_budget"
        case .commuteCap: return "commute_cap"
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

public struct InterpretBody: Hashable, Sendable, Codable {
    public let text: String
    public let spec: PreferenceSpec?

    public init(text: String, spec: PreferenceSpec? = nil) {
        self.text = text
        self.spec = spec
    }

    enum CodingKeys: String, CodingKey {
        case text
        case spec
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        text = try container.decode(String.self, forKey: .text)
        spec = try container.decodeIfPresent(PreferenceSpec.self, forKey: .spec)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(text, forKey: .text)
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
    public let restsOn: [RestsOn]

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
        restsOn: [RestsOn]
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
        self.restsOn = restsOn
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
        case restsOn = "rests_on"
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
        restsOn = try container.decode([RestsOn].self, forKey: .restsOn)
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
        try container.encode(restsOn, forKey: .restsOn)
    }
}

/// In the order that decides the status: the first that applies wins.
public enum InterpretStatus: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case offTopic
    case policyRedirect
    case clarify
    case ok
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [InterpretStatus] = [.offTopic, .policyRedirect, .clarify, .ok]

    public init(rawValue: String) {
        switch rawValue {
        case "off_topic": self = .offTopic
        case "policy_redirect": self = .policyRedirect
        case "clarify": self = .clarify
        case "ok": self = .ok
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .offTopic: return "off_topic"
        case .policyRedirect: return "policy_redirect"
        case .clarify: return "clarify"
        case .ok: return "ok"
        case .unlisted(let value): return value
        }
    }
}

public enum InterpreterName: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case rule
    case claude
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [InterpreterName] = [.rule, .claude]

    public init(rawValue: String) {
        switch rawValue {
        case "rule": self = .rule
        case "claude": self = .claude
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .rule: return "rule"
        case .claude: return "claude"
        case .unlisted(let value): return value
        }
    }
}

public struct Meta: Hashable, Sendable, Codable {
    public let releaseId: String
    public let engineVersion: String
    public let synthetic: Bool

    public init(releaseId: String, engineVersion: String, synthetic: Bool) {
        self.releaseId = releaseId
        self.engineVersion = engineVersion
        self.synthetic = synthetic
    }

    enum CodingKeys: String, CodingKey {
        case releaseId = "release_id"
        case engineVersion = "engine_version"
        case synthetic
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        releaseId = try container.decode(String.self, forKey: .releaseId)
        engineVersion = try container.decode(String.self, forKey: .engineVersion)
        synthetic = try container.decode(Bool.self, forKey: .synthetic)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(releaseId, forKey: .releaseId)
        try container.encode(engineVersion, forKey: .engineVersion)
        try container.encode(synthetic, forKey: .synthetic)
    }
}

public struct MetaData: Hashable, Sendable, Codable {
    public let releaseId: String
    public let builtAt: String
    public let synthetic: Bool
    public let engineVersion: String
    public let catalogueVersion: Int
    public let counts: Counts
    public let attributions: [Source]
    public let features: [Metric]
    public let tags: [Tag]
    public let defaults: Defaults
    public let limits: ServedLimits

    public init(
        releaseId: String,
        builtAt: String,
        synthetic: Bool,
        engineVersion: String,
        catalogueVersion: Int,
        counts: Counts,
        attributions: [Source],
        features: [Metric],
        tags: [Tag],
        defaults: Defaults,
        limits: ServedLimits
    ) {
        self.releaseId = releaseId
        self.builtAt = builtAt
        self.synthetic = synthetic
        self.engineVersion = engineVersion
        self.catalogueVersion = catalogueVersion
        self.counts = counts
        self.attributions = attributions
        self.features = features
        self.tags = tags
        self.defaults = defaults
        self.limits = limits
    }

    enum CodingKeys: String, CodingKey {
        case releaseId = "release_id"
        case builtAt = "built_at"
        case synthetic
        case engineVersion = "engine_version"
        case catalogueVersion = "catalogue_version"
        case counts
        case attributions
        case features
        case tags
        case defaults
        case limits
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        releaseId = try container.decode(String.self, forKey: .releaseId)
        builtAt = try container.decode(String.self, forKey: .builtAt)
        synthetic = try container.decode(Bool.self, forKey: .synthetic)
        engineVersion = try container.decode(String.self, forKey: .engineVersion)
        catalogueVersion = try container.decode(Int.self, forKey: .catalogueVersion)
        counts = try container.decode(Counts.self, forKey: .counts)
        attributions = try container.decode([Source].self, forKey: .attributions)
        features = try container.decode([Metric].self, forKey: .features)
        tags = try container.decode([Tag].self, forKey: .tags)
        defaults = try container.decode(Defaults.self, forKey: .defaults)
        limits = try container.decode(ServedLimits.self, forKey: .limits)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(releaseId, forKey: .releaseId)
        try container.encode(builtAt, forKey: .builtAt)
        try container.encode(synthetic, forKey: .synthetic)
        try container.encode(engineVersion, forKey: .engineVersion)
        try container.encode(catalogueVersion, forKey: .catalogueVersion)
        try container.encode(counts, forKey: .counts)
        try container.encode(attributions, forKey: .attributions)
        try container.encode(features, forKey: .features)
        try container.encode(tags, forKey: .tags)
        try container.encode(defaults, forKey: .defaults)
        try container.encode(limits, forKey: .limits)
    }
}

/// A feature this release carries. Core decides what it is; the release says where from.
public struct Metric: Hashable, Sendable, Codable {
    public let featureId: FeatureId
    public let label: String
    public let dimension: Dimension
    public let unit: String
    public let polarity: Polarity
    public let nativeResolution: NativeResolution
    public let sourceIds: [String]
    public let vintage: String
    public let rankable: Bool
    public let definition: String

    public init(
        featureId: FeatureId,
        label: String,
        dimension: Dimension,
        unit: String,
        polarity: Polarity,
        nativeResolution: NativeResolution,
        sourceIds: [String],
        vintage: String,
        rankable: Bool,
        definition: String
    ) {
        self.featureId = featureId
        self.label = label
        self.dimension = dimension
        self.unit = unit
        self.polarity = polarity
        self.nativeResolution = nativeResolution
        self.sourceIds = sourceIds
        self.vintage = vintage
        self.rankable = rankable
        self.definition = definition
    }

    enum CodingKeys: String, CodingKey {
        case featureId = "feature_id"
        case label
        case dimension
        case unit
        case polarity
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
        dimension = try container.decode(Dimension.self, forKey: .dimension)
        unit = try container.decode(String.self, forKey: .unit)
        polarity = try container.decode(Polarity.self, forKey: .polarity)
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
        try container.encode(dimension, forKey: .dimension)
        try container.encode(unit, forKey: .unit)
        try container.encode(polarity, forKey: .polarity)
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

public enum NativeResolution: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case oa
    case lsoa
    case grid1km
    case point
    case polygon
    case network
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [NativeResolution] = [.oa, .lsoa, .grid1km, .point, .polygon, .network]

    public init(rawValue: String) {
        switch rawValue {
        case "oa": self = .oa
        case "lsoa": self = .lsoa
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

    public init(
        areaId: String,
        slug: String,
        name: String,
        borough: String,
        aliases: [String],
        centroid: LonLat,
        rankable: Bool,
        neighbours: [String]
    ) {
        self.areaId = areaId
        self.slug = slug
        self.name = name
        self.borough = borough
        self.aliases = aliases
        self.centroid = centroid
        self.rankable = rankable
        self.neighbours = neighbours
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

    public init(places: [FoundPlace]) {
        self.places = places
    }

    enum CodingKeys: String, CodingKey {
        case places
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        places = try container.decode([FoundPlace].self, forKey: .places)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(places, forKey: .places)
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
    public let filtered: [Filtered]
    public let unranked: [Unranked]
    public let emptySpec: Bool
    public let spec: PreferenceSpec
    public let specHash: String
    public let applied: [Applied]
    public let rejected: [Rejected]

    public init(
        scores: [Score],
        ranked: [RankedArea],
        filtered: [Filtered],
        unranked: [Unranked],
        emptySpec: Bool,
        spec: PreferenceSpec,
        specHash: String,
        applied: [Applied],
        rejected: [Rejected]
    ) {
        self.scores = scores
        self.ranked = ranked
        self.filtered = filtered
        self.unranked = unranked
        self.emptySpec = emptySpec
        self.spec = spec
        self.specHash = specHash
        self.applied = applied
        self.rejected = rejected
    }

    enum CodingKeys: String, CodingKey {
        case scores
        case ranked
        case filtered
        case unranked
        case emptySpec = "empty_spec"
        case spec
        case specHash = "spec_hash"
        case applied
        case rejected
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        scores = try container.decode([Score].self, forKey: .scores)
        ranked = try container.decode([RankedArea].self, forKey: .ranked)
        filtered = try container.decode([Filtered].self, forKey: .filtered)
        unranked = try container.decode([Unranked].self, forKey: .unranked)
        emptySpec = try container.decode(Bool.self, forKey: .emptySpec)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        specHash = try container.decode(String.self, forKey: .specHash)
        applied = try container.decode([Applied].self, forKey: .applied)
        rejected = try container.decode([Rejected].self, forKey: .rejected)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(scores, forKey: .scores)
        try container.encode(ranked, forKey: .ranked)
        try container.encode(filtered, forKey: .filtered)
        try container.encode(unranked, forKey: .unranked)
        try container.encode(emptySpec, forKey: .emptySpec)
        try container.encode(spec, forKey: .spec)
        try container.encode(specHash, forKey: .specHash)
        try container.encode(applied, forKey: .applied)
        try container.encode(rejected, forKey: .rejected)
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

    public init(
        areaId: String,
        rank: Int,
        score: Double,
        weightCoverage: Double,
        contributions: [Contribution],
        legs: [CommuteLeg],
        budget: BudgetFit?,
        untestedFilters: [FilterReason]
    ) {
        self.areaId = areaId
        self.rank = rank
        self.score = score
        self.weightCoverage = weightCoverage
        self.contributions = contributions
        self.legs = legs
        self.budget = budget
        self.untestedFilters = untestedFilters
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

public struct Score: Hashable, Sendable, Codable {
    public let areaId: String
    public let score: Double

    public init(areaId: String, score: Double) {
        self.areaId = areaId
        self.score = score
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case score
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        score = try container.decode(Double.self, forKey: .score)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(score, forKey: .score)
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

    public init(shareId: String, spec: PreferenceSpec, coarsened: Bool) {
        self.shareId = shareId
        self.spec = spec
        self.coarsened = coarsened
    }

    enum CodingKeys: String, CodingKey {
        case shareId = "share_id"
        case spec
        case coarsened
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        shareId = try container.decode(String.self, forKey: .shareId)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        coarsened = try container.decode(Bool.self, forKey: .coarsened)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(shareId, forKey: .shareId)
        try container.encode(spec, forKey: .spec)
        try container.encode(coarsened, forKey: .coarsened)
    }
}

/// A shared search, ranked now on the release that is loaded.
public struct ShareData: Hashable, Sendable, Codable {
    public let scores: [Score]
    public let ranked: [RankedArea]
    public let filtered: [Filtered]
    public let unranked: [Unranked]
    public let emptySpec: Bool
    public let spec: PreferenceSpec
    public let specHash: String
    public let coarsened: Bool
    public let stale: Bool
    public let originalReleaseId: String

    public init(
        scores: [Score],
        ranked: [RankedArea],
        filtered: [Filtered],
        unranked: [Unranked],
        emptySpec: Bool,
        spec: PreferenceSpec,
        specHash: String,
        coarsened: Bool,
        stale: Bool,
        originalReleaseId: String
    ) {
        self.scores = scores
        self.ranked = ranked
        self.filtered = filtered
        self.unranked = unranked
        self.emptySpec = emptySpec
        self.spec = spec
        self.specHash = specHash
        self.coarsened = coarsened
        self.stale = stale
        self.originalReleaseId = originalReleaseId
    }

    enum CodingKeys: String, CodingKey {
        case scores
        case ranked
        case filtered
        case unranked
        case emptySpec = "empty_spec"
        case spec
        case specHash = "spec_hash"
        case coarsened
        case stale
        case originalReleaseId = "original_release_id"
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        scores = try container.decode([Score].self, forKey: .scores)
        ranked = try container.decode([RankedArea].self, forKey: .ranked)
        filtered = try container.decode([Filtered].self, forKey: .filtered)
        unranked = try container.decode([Unranked].self, forKey: .unranked)
        emptySpec = try container.decode(Bool.self, forKey: .emptySpec)
        spec = try container.decode(PreferenceSpec.self, forKey: .spec)
        specHash = try container.decode(String.self, forKey: .specHash)
        coarsened = try container.decode(Bool.self, forKey: .coarsened)
        stale = try container.decode(Bool.self, forKey: .stale)
        originalReleaseId = try container.decode(String.self, forKey: .originalReleaseId)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(scores, forKey: .scores)
        try container.encode(ranked, forKey: .ranked)
        try container.encode(filtered, forKey: .filtered)
        try container.encode(unranked, forKey: .unranked)
        try container.encode(emptySpec, forKey: .emptySpec)
        try container.encode(spec, forKey: .spec)
        try container.encode(specHash, forKey: .specHash)
        try container.encode(coarsened, forKey: .coarsened)
        try container.encode(stale, forKey: .stale)
        try container.encode(originalReleaseId, forKey: .originalReleaseId)
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

    public init(
        sourceId: String,
        name: String,
        publisher: String,
        licence: String,
        attribution: String,
        url: String,
        retrievedOn: String
    ) {
        self.sourceId = sourceId
        self.name = name
        self.publisher = publisher
        self.licence = licence
        self.attribution = attribution
        self.url = url
        self.retrievedOn = retrievedOn
    }

    enum CodingKeys: String, CodingKey {
        case sourceId = "source_id"
        case name
        case publisher
        case licence
        case attribution
        case url
        case retrievedOn = "retrieved_on"
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

public struct Tag: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let label: String
    public let terms: [TagTerm]

    public init(tagId: TagId, label: String, terms: [TagTerm]) {
        self.tagId = tagId
        self.label = label
        self.terms = terms
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case label
        case terms
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        label = try container.decode(String.self, forKey: .label)
        terms = try container.decode([TagTerm].self, forKey: .terms)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(label, forKey: .label)
        try container.encode(terms, forKey: .terms)
    }
}

public struct TagEdit: Hashable, Sendable, Codable {
    public let action: WeightAction
    public let tagId: TagId
    public let value: Double
    public let step: Step
    public let provenance: EditProvenance

    public init(
        action: WeightAction,
        tagId: TagId,
        value: Double,
        step: Step,
        provenance: EditProvenance
    ) {
        self.action = action
        self.tagId = tagId
        self.value = value
        self.step = step
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case action
        case tagId = "tag_id"
        case value
        case step
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        action = try container.decode(WeightAction.self, forKey: .action)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        value = try container.decode(Double.self, forKey: .value)
        step = try container.decode(Step.self, forKey: .step)
        provenance = try container.decode(EditProvenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(action, forKey: .action)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(value, forKey: .value)
        try container.encode(step, forKey: .step)
        try container.encode(provenance, forKey: .provenance)
    }
}

public enum TagId: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case villageFeel
    case buzzy
    case leafy
    case creative
    case familyAmenities
    case nearUniversities
    case waterside
    case strongHighStreet
    case eveningVenues
    case quietResidential
    case foodie
    case historicCharacter
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TagId] = [.villageFeel, .buzzy, .leafy, .creative, .familyAmenities, .nearUniversities, .waterside, .strongHighStreet, .eveningVenues, .quietResidential, .foodie, .historicCharacter]

    public init(rawValue: String) {
        switch rawValue {
        case "village_feel": self = .villageFeel
        case "buzzy": self = .buzzy
        case "leafy": self = .leafy
        case "creative": self = .creative
        case "family_amenities": self = .familyAmenities
        case "near_universities": self = .nearUniversities
        case "waterside": self = .waterside
        case "strong_high_street": self = .strongHighStreet
        case "evening_venues": self = .eveningVenues
        case "quiet_residential": self = .quietResidential
        case "foodie": self = .foodie
        case "historic_character": self = .historicCharacter
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .villageFeel: return "village_feel"
        case .buzzy: return "buzzy"
        case .leafy: return "leafy"
        case .creative: return "creative"
        case .familyAmenities: return "family_amenities"
        case .nearUniversities: return "near_universities"
        case .waterside: return "waterside"
        case .strongHighStreet: return "strong_high_street"
        case .eveningVenues: return "evening_venues"
        case .quietResidential: return "quiet_residential"
        case .foodie: return "foodie"
        case .historicCharacter: return "historic_character"
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

public struct TagValue: Hashable, Sendable, Codable {
    public let areaId: String
    public let tagId: TagId
    public let raw: Double?
    public let score: Double?
    public let coverage: Double

    public init(
        areaId: String,
        tagId: TagId,
        raw: Double?,
        score: Double?,
        coverage: Double
    ) {
        self.areaId = areaId
        self.tagId = tagId
        self.raw = raw
        self.score = score
        self.coverage = coverage
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case tagId = "tag_id"
        case raw
        case score
        case coverage
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        areaId = try container.decode(String.self, forKey: .areaId)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        raw = try container.decodeIfPresent(Double.self, forKey: .raw)
        score = try container.decodeIfPresent(Double.self, forKey: .score)
        coverage = try container.decode(Double.self, forKey: .coverage)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(raw, forKey: .raw)
        try container.encode(score, forKey: .score)
        try container.encode(coverage, forKey: .coverage)
    }
}

public struct TagWeight: Hashable, Sendable, Codable {
    public let tagId: TagId
    public let weight: Double
    public let provenance: Provenance

    public init(tagId: TagId, weight: Double, provenance: Provenance) {
        self.tagId = tagId
        self.weight = weight
        self.provenance = provenance
    }

    enum CodingKeys: String, CodingKey {
        case tagId = "tag_id"
        case weight
        case provenance
    }

    public init(from decoder: any Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tagId = try container.decode(TagId.self, forKey: .tagId)
        weight = try container.decode(Double.self, forKey: .weight)
        provenance = try container.decode(Provenance.self, forKey: .provenance)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tagId, forKey: .tagId)
        try container.encode(weight, forKey: .weight)
        try container.encode(provenance, forKey: .provenance)
    }
}

public enum TemplateId: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case area
    case feature
    case featureCrime
    case tag
    case costRent
    case costBuy
    case budgetUnder
    case budgetOver
    case travelPt
    case travelOther
    case travelBeyond
    case station
    case stationNearby
    case missing
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TemplateId] = [.area, .feature, .featureCrime, .tag, .costRent, .costBuy, .budgetUnder, .budgetOver, .travelPt, .travelOther, .travelBeyond, .station, .stationNearby, .missing]

    public init(rawValue: String) {
        switch rawValue {
        case "area": self = .area
        case "feature": self = .feature
        case "feature_crime": self = .featureCrime
        case "tag": self = .tag
        case "cost_rent": self = .costRent
        case "cost_buy": self = .costBuy
        case "budget_under": self = .budgetUnder
        case "budget_over": self = .budgetOver
        case "travel_pt": self = .travelPt
        case "travel_other": self = .travelOther
        case "travel_beyond": self = .travelBeyond
        case "station": self = .station
        case "station_nearby": self = .stationNearby
        case "missing": self = .missing
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .area: return "area"
        case .feature: return "feature"
        case .featureCrime: return "feature_crime"
        case .tag: return "tag"
        case .costRent: return "cost_rent"
        case .costBuy: return "cost_buy"
        case .budgetUnder: return "budget_under"
        case .budgetOver: return "budget_over"
        case .travelPt: return "travel_pt"
        case .travelOther: return "travel_other"
        case .travelBeyond: return "travel_beyond"
        case .station: return "station"
        case .stationNearby: return "station_nearby"
        case .missing: return "missing"
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

public enum TravelStatus: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case ok
    case beyondCutoff
    case missing
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [TravelStatus] = [.ok, .beyondCutoff, .missing]

    public init(rawValue: String) {
        switch rawValue {
        case "ok": self = .ok
        case "beyond_cutoff": self = .beyondCutoff
        case "missing": self = .missing
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .ok: return "ok"
        case .beyondCutoff: return "beyond_cutoff"
        case .missing: return "missing"
        case .unlisted(let value): return value
        }
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
    case other
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [UnmetCategory] = [.broadband, .floodRisk, .healthServices, .driving, .listings, .affordabilityVerdict, .communityAmenities, .outsideTheCity, .other]

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
        case .other: return "other"
        case .unlisted(let value): return value
        }
    }
}

public struct Unranked: Hashable, Sendable, Codable {
    public let areaId: String
    public let reason: UnrankedReason

    public init(areaId: String, reason: UnrankedReason) {
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
        reason = try container.decode(UnrankedReason.self, forKey: .reason)
    }

    public func encode(to encoder: any Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(areaId, forKey: .areaId)
        try container.encode(reason, forKey: .reason)
    }
}

public enum UnrankedReason: Hashable, Sendable, Codable, CaseIterable, RawRepresentable {
    case notRankable
    case insufficientData
    /// A value this build does not know. It is kept, and sent back, as it came.
    case unlisted(String)

    /// Every value the contract lists.
    public static let allCases: [UnrankedReason] = [.notRankable, .insufficientData]

    public init(rawValue: String) {
        switch rawValue {
        case "not_rankable": self = .notRankable
        case "insufficient_data": self = .insufficientData
        default: self = .unlisted(rawValue)
        }
    }

    public var rawValue: String {
        switch self {
        case .notRankable: return "not_rankable"
        case .insufficientData: return "insufficient_data"
        case .unlisted(let value): return value
        }
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
