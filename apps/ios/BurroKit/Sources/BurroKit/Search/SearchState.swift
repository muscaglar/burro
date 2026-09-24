import Foundation

// What a search is, while it is open: one plain value, and the events that
// move it on. It mirrors apps/web/src/lib/search/state.ts, field for field.
//
// It is held in memory and nowhere else. It never holds what a person typed:
// the sentence stays in its box and in the body of one request. It holds ids
// of the release, the spec the API last returned, and what the API answered.

/// Where a search stands.
public enum Phase: String, Hashable, Sendable, CaseIterable {
    case empty
    case interpreting
    case results
    case refining
}

/// Which release and which engine made an answer. It is kept with what the
/// answer brought, because nothing else says it: a hash is of the spec alone,
/// and the same spec has the same hash on every release.
public struct Served: Hashable, Sendable {
    public let releaseId: String
    public let engineVersion: String

    public init(releaseId: String, engineVersion: String) {
        self.releaseId = releaseId
        self.engineVersion = engineVersion
    }

    /// The release and the engine an answer names.
    public init(_ meta: Meta) {
        self.init(releaseId: meta.releaseId, engineVersion: meta.engineVersion)
    }

    /// The release and the engine the form was read from.
    public init(form: MetaData) {
        self.init(releaseId: form.releaseId, engineVersion: form.engineVersion)
    }
}

/// Which call a failure came from: reading the words, or ranking.
public enum SearchStep: String, Hashable, Sendable {
    case read
    case rank
}

/// What route 1 said of the words, in codes and fixed text. Never the words.
public struct Read: Hashable, Sendable {
    public let status: InterpretStatus
    public let operations: Operations
    public let assumptions: [Assumption]
    public var clarify: [Clarify]
    public let unmet: [UnmetCategory]
    public var rejected: [Rejected]
    public let notice: Notice
    public let noticeText: String
    public let interpreter: InterpreterName
    public let degraded: Bool
    /// How many edits the words were read into.
    public let edits: Int
    /// True when any of them changed the spec.
    public let changed: Bool
    /// The count of answers when this one came, so a screen can tell it is the latest.
    public let at: Int
    /// The release and the engine that read the words.
    public let by: Served
}

/// The part of a ranking a screen draws.
public struct Ranking: Hashable, Sendable {
    public let scores: [Score]
    public let ranked: [RankedArea]
    public let filtered: [Filtered]
    public let unranked: [Unranked]
    public let emptySpec: Bool

    public init(
        scores: [Score], ranked: [RankedArea], filtered: [Filtered], unranked: [Unranked], emptySpec: Bool
    ) {
        self.scores = scores
        self.ranked = ranked
        self.filtered = filtered
        self.unranked = unranked
        self.emptySpec = emptySpec
    }

    init(_ data: RankData) {
        self.init(
            scores: data.scores, ranked: data.ranked, filtered: data.filtered,
            unranked: data.unranked, emptySpec: data.emptySpec)
    }

    init(_ data: ShareData) {
        self.init(
            scores: data.scores, ranked: data.ranked, filtered: data.filtered,
            unranked: data.unranked, emptySpec: data.emptySpec)
    }
}

/// Edits a control sent that the reducer refused, with the edits they point into.
public struct Refused: Hashable, Sendable {
    public let operations: Operations
    public let rejected: [Rejected]
}

/// The share a search was opened from: its id, and what the API said of it
/// when it was opened. The id is held so that coming back to the link does
/// not open it again over what the person has changed since.
public struct Shared: Hashable, Sendable {
    public let id: String
    public let coarsened: Bool
    public let stale: Bool
    public let originalReleaseId: String
}

/// Reasons, with the search and the release they are for. They came before
/// the ranking they are for.
public struct ExplanationsAhead: Hashable, Sendable {
    public let hash: String
    public let by: Served
    public let explanations: [Explanation]
    public let facts: [Fact]
}

/// Why the reasons of a search could not be loaded, whole: its message and
/// the id to quote, with the hash of the spec they were asked for.
public struct ReasonsFailure: Hashable, Sendable {
    public let hash: String
    public let failure: Failure
}

/// The search as it was when a sentence was sent: what reading the sentence
/// replaces before its ranking is in. "Stop" puts it back, so that the chips
/// are never left saying one search over the ranking of another.
public struct Kept: Hashable, Sendable {
    public let spec: PreferenceSpec
    public let specHash: String?
    public let untouched: Bool
    public let read: Read?
    public let refused: Refused?
    public let assumed: Assumed
    public let gaveWay: Bool
    public let degraded: Bool
}

/// What was assumed of each part of the search, by the key of its chip.
public typealias Assumed = [ChipKey: [AssumptionCode]]

public struct SearchState: Hashable, Sendable {
    /// What the search was opened on. Replaced if the API moves to another release.
    public var meta: MetaData
    public var areas: [AreaSummary]
    public var geometry: GeometryData?
    public var geometryFailed: Bool

    public var phase: Phase
    /// The phase to go back to when a request is stopped or fails: `empty` or `results`.
    public var before: Phase
    /// The search as it was when the sentence now being read was sent. `nil` once its ranking is in.
    public var kept: Kept?
    public var seq: Int
    /// Counts the answers that leave no edit waiting. A control holds what it was set to
    /// against this count, and is the API's again when it moves. A reading that comes while
    /// an edit waits does not move it: the edit has not been answered.
    public var answers: Int
    public var failure: Failure?
    public var failedStep: SearchStep?
    public var online: Bool
    /// True when the words could not be read, so the settings are the way in.
    public var degraded: Bool
    public var settingsOpen: Bool

    public var spec: PreferenceSpec
    public var specHash: String?
    /// True until an answer changes the spec: the spec is still a default as served.
    public var untouched: Bool
    /// Edits made and not yet answered. They are sent again with the last spec returned.
    public var pending: Operations

    public var read: Read?
    public var refused: Refused?
    public var ranking: Ranking?
    public var rankedHash: String?
    /// The release and the engine that made the ranking on screen.
    public var rankedBy: Served?
    /// How many areas changed place at the last answer. `nil` for a first ranking.
    public var moved: Int?
    /// True when the last answer made the settings nobody chose count for less.
    public var gaveWay: Bool

    /// The reasons in hand. They are the ranking's only if `reasonsAreIn` says so.
    public var explanations: [Explanation]
    public var explainedHash: String?
    public var explainedBy: Served?
    /// Why the reasons of a search could not be loaded, whole.
    public var explainFailure: ReasonsFailure?
    /// Reasons that came before the ranking they are for. They wait here, and
    /// the reasons on screen stay, until that ranking comes. If it never
    /// does, the ranking on screen keeps its own reasons.
    public var explanationsAhead: ExplanationsAhead?
    public var facts: [String: Fact]
    /// The release and the engine that made each fact, by its id.
    public var factsBy: [String: Served]
    public var details: [String: AreaData]
    /// The release and the engine that made each profile, by the id of its area.
    public var detailsBy: [String: Served]
    /// Why the profile of an area could not be loaded, by the id of the area.
    public var detailFailures: [String: Failure]

    public var placeNames: [String: String]
    public var assumed: Assumed

    /// The share the search was opened from. `nil` for a search the person began.
    public var shared: Shared?

    public var selectedId: String?

    /// A search that has just been opened: empty, on a renter's defaults as the API served them.
    public init(meta: MetaData, areas: [AreaSummary], geometry: GeometryData? = nil) {
        self.meta = meta
        self.areas = areas
        self.geometry = geometry
        geometryFailed = false
        phase = .empty
        before = .empty
        kept = nil
        seq = 0
        answers = 0
        failure = nil
        failedStep = nil
        online = true
        degraded = false
        settingsOpen = false
        spec = meta.defaults.rent
        specHash = nil
        untouched = true
        pending = .none
        read = nil
        refused = nil
        ranking = nil
        rankedHash = nil
        rankedBy = nil
        moved = nil
        gaveWay = false
        explanations = []
        explainedHash = nil
        explainedBy = nil
        explainFailure = nil
        explanationsAhead = nil
        facts = [:]
        factsBy = [:]
        details = [:]
        detailsBy = [:]
        detailFailures = [:]
        placeNames = [:]
        assumed = [:]
        shared = nil
        selectedId = nil
    }
}

/// Everything that can happen to a search.
///
/// Every answer comes with `by`: the release and the engine its envelope
/// names. The flow always says it. With none said, as in a test of one event,
/// the answer is taken to be of the release the form was read from.
public enum SearchEvent: Sendable {
    case tenureSwapped(Tenure)
    case queued(Operations)
    case readStarted(seq: Int)
    case readAnswered(InterpretData, by: Served? = nil)
    case rankStarted(seq: Int)
    case rankAnswered(RankData, sent: Operations, by: Served? = nil)
    case shareAnswered(id: String, ShareData, by: Served? = nil)
    case explainAnswered(ExplanationsData, hash: String, by: Served? = nil)
    case explainFailed(hash: String, Failure)
    case detailAnswered(AreaData, by: Served? = nil)
    case detailFailed(areaId: String, Failure)
    case settled
    case failed(step: SearchStep, Failure)
    case stopped
    case startedAgain
    case questionAnswered(Clarify, id: String)
    case questionLeft(Clarify)
    case placeNamed(placeId: String, name: String)
    case onlineChanged(Bool)
    case settingsOpened(Bool)
    case geometryLoaded(GeometryData)
    case geometryFailed
    case releaseChanged(meta: MetaData, areas: [AreaSummary])
    case selected(areaId: String?)
}
