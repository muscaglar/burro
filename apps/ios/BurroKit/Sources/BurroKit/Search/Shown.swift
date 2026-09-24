import Foundation

// What a screen shows of a search, worked out from its state. Each is a state
// of docs/design/web.md section 3, read as the website's search page reads it,
// so that three screens built apart say the same thing of the same state.

/// A state that sits on a phase. Several can hold at once.
public enum SearchCondition: String, Hashable, Sendable, CaseIterable {
    /// Burro has a question about a place or an area.
    case clarifying
    /// A ranking came back and no area passes every limit.
    case nothingMatches
    /// Nothing in the words could be read as a setting.
    case nothingRead
    /// The words were read, and the search already said it.
    case nothingChanged
    /// The words could not be read, so the settings are the way in.
    case degraded
    /// Burro noticed something and did not apply it. The person chooses.
    case suggesting
    /// Something was read, and a stretch of what was typed was not.
    case readInPart
    /// Something was asked for that the data holds for no area.
    case notInData
    /// The API has one neutral sentence to show, word for word.
    case notice
    /// A call failed, and the failure is to be shown.
    case failed
    /// The phone is offline. The last results stay readable.
    case offline
}

/// Where a failure is shown. One failure is shown in one place.
public enum FailurePlace: String, Hashable, Sendable {
    case none
    /// The offline line.
    case offline
    /// Under the box the words were typed in: the API refused the words.
    case box
    /// The line that says the words could not be read, with "Try again".
    case form
    /// The error block, with the API's message and the request id.
    case block
}

/// Which of the two lines to show when a reading changed nothing.
public enum NothingRead: String, Hashable, Sendable {
    case nothingRead
    case nothingChanged
}

extension Failure {
    /// True when the failure says the search names something the data no longer has.
    public var isStale: Bool {
        guard let api, [ErrorCode.unknownPlace, .unknownArea, .invalidSpec].contains(api.code) else {
            return false
        }
        return api.fields.contains { $0.path.hasPrefix("spec.") }
    }
}

extension SearchState {
    public var isReading: Bool { phase == .interpreting }
    public var isBusy: Bool { phase == .interpreting || phase == .refining }

    /// The questions to ask. None while a sentence is being read.
    public var questions: [Clarify] {
        isReading ? [] : (read?.clarify ?? [])
    }

    /// True when the reading on hand is the last thing that set the spec.
    public var readIsLatest: Bool {
        read.map { $0.at == answers } ?? false
    }

    /// What the reader noticed and did not apply, for the person to choose
    /// from. None while a sentence is being read.
    public var suggestions: [Suggestion] {
        isReading ? [] : (read?.suggestions ?? [])
    }

    /// The stretches of the text that was sent that the reader made nothing
    /// of, as offsets. None while a sentence is being read.
    public var unread: [Span] {
        isReading ? [] : (read?.unread ?? [])
    }

    /// True when something was read and a stretch of the text was not: the
    /// ranking leaves that stretch out.
    public var readInPart: Bool {
        guard !isReading, let read else { return false }
        return read.partUnread && read.changed
    }

    /// True when nothing was applied, nothing is asked and nothing is
    /// offered: the words were read into nothing.
    private var readNothing: Bool {
        guard let read else { return false }
        return questions.isEmpty && read.suggestions.isEmpty
            && (read.status == .offTopic || read.edits == 0)
    }

    /// The line to show when the last reading changed nothing. `nil` when it changed something.
    public var nothingRead: NothingRead? {
        guard !isReading, readIsLatest, let read, questions.isEmpty, suggestions.isEmpty, !read.changed
        else { return nil }
        if readNothing { return .nothingRead }
        return read.rejected.isEmpty && read.edits > 0 ? .nothingChanged : nil
    }

    /// True when the API sent a sentence of its own to show, word for word.
    public var noticed: Bool {
        guard let read else { return false }
        return read.notice != .nothing && !read.noticeText.isEmpty
    }

    /// What could not be answered. `other` is left out: that a part was not
    /// read is said beside the box, by the line for it.
    public var unmetShown: [UnmetCategory] {
        (read?.unmet ?? []).filter { $0 != .other }
    }

    /// True when the reasons in hand are the reasons of the ranking on screen:
    /// they are for the same spec, and the same release and engine made both.
    /// The hash alone cannot say so, because it is of the spec alone.
    public var reasonsAreIn: Bool {
        guard ranking != nil, let explainedHash, let explainedBy, let rankedBy else { return false }
        return explainedHash == rankedHash && explainedBy == rankedBy
    }

    /// The same, by the name the screens first knew it by.
    public var explained: Bool { reasonsAreIn }

    /// Why the reasons of the ranking on screen could not be loaded. `nil`
    /// when they were, or were not asked for.
    public var reasonsFailure: Failure? {
        guard ranking != nil, let explainFailure, explainFailure.hash == rankedHash else { return nil }
        return explainFailure.failure
    }

    /// True when the reasons of the ranking on screen could not be loaded.
    public var explainFailed: Bool { reasonsFailure != nil }

    /// The areas among the cards whose profile could not be loaded, in rank order.
    public var profilesFailed: [String] {
        (ranking?.ranked ?? []).prefix(SearchFlow.explained).map(\.areaId)
            .filter { detailFailures[$0] != nil }
    }

    /// Every area whose profile could not be loaded, in order of id.
    public var detailsFailed: [String] {
        detailFailures.keys.sorted()
    }

    /// The failure to say of what the cards hold, where the search itself did
    /// not fail: that of the reasons, or else of the first profile that is
    /// missing. One failure is shown in one place, so there is none here
    /// while the search has one of its own, and none for an area that has no card.
    public var failureOfTheCards: Failure? {
        guard failure == nil else { return nil }
        return reasonsFailure ?? profilesFailed.first.flatMap { detailFailures[$0] }
    }

    /// The release and the engine to name under a result: those that made the ranking.
    public var servedTheRanking: Served {
        rankedBy ?? Served(form: meta)
    }

    /// True when no more places can be added.
    public var placesFull: Bool {
        spec.commutes.count >= meta.limits.maxCommutes
    }

    public var failurePlace: FailurePlace {
        guard let failure else { return online ? .none : .offline }
        if failure.isOffline { return .offline }
        if failure.code == .invalidText { return .box }
        // A request the API refused, other than for its words, is a fault to report and
        // is said in the API's own words. Left to the form it would be said nowhere.
        let refused = failure.api.map { $0.status < 500 } ?? false
        // Words that could not be read are not a fault to report. The form does the same job.
        if failedStep == .read && !failure.isStale && !refused { return .form }
        return .block
    }

    /// Every state of section 3 that holds now, beside the phase.
    public var conditions: Set<SearchCondition> {
        var found: Set<SearchCondition> = []
        if !questions.isEmpty { found.insert(.clarifying) }
        if let ranking, ranking.ranked.isEmpty { found.insert(.nothingMatches) }
        switch nothingRead {
        case .nothingRead: found.insert(.nothingRead)
        case .nothingChanged: found.insert(.nothingChanged)
        case nil: break
        }
        if degraded && !isReading { found.insert(.degraded) }
        if !suggestions.isEmpty { found.insert(.suggesting) }
        if readInPart { found.insert(.readInPart) }
        if !isReading && !missing.isEmpty { found.insert(.notInData) }
        if noticed { found.insert(.notice) }
        switch failurePlace {
        case .none: break
        case .offline: found.insert(.offline)
        case .form: found.insert(.degraded)
        case .box, .block: found.insert(.failed)
        }
        return found
    }

    /// The name of each place of the search, by its id. A place no answer
    /// named has none here, and a screen says that it has no name.
    public func name(ofPlace placeId: String) -> String? {
        placeNames[placeId]
    }

    /// The area of the release with this id.
    public func area(_ areaId: String) -> AreaSummary? {
        areas.first { $0.areaId == areaId }
    }
}

/// What counts most in a search, where it is not what the person asked of the place.
///
/// A journey and a budget each count for more than a thing that was asked for
/// in a word, until the person says otherwise. So a person who asks for leafy
/// and quiet and names a workplace is first shown the areas nearest the
/// workplace. Nothing is wrong with the order, and a screen must say why it is
/// so: a person who is not told reads the first result as the leafiest.
public struct Leads: Hashable, Sendable {
    /// True where the journeys count for more than anything that was asked of the place.
    public let journey: Bool
    /// True where the budget does.
    public let budget: Bool
    /// How many places the search names, to say "journey" or "journeys".
    public let journeys: Int
}

extension PreferenceSpec {
    /// The most that anything asked of the place counts for: a vibe, or a
    /// thing nearby that a person chose.
    public var mostAskedOfThePlace: Double {
        let asked =
            tags.map(\.weight)
            + weights.filter { $0.provenance != .default }.map(\.weight)
        return max(0, asked.max() ?? 0)
    }

    /// What outweighs everything that was asked of the place. `nil` where
    /// nothing does, or nothing was asked of the place.
    public var leads: Leads? {
        let most = mostAskedOfThePlace
        guard most > 0 else { return nil }
        let journey = !commutes.isEmpty && commuteWeight > most
        let budget = budget.amount != nil && budget.weight > most
        return journey || budget ? Leads(journey: journey, budget: budget, journeys: commutes.count) : nil
    }
}

extension SearchState {
    /// What counts for more than what was asked of the place, in the ranking
    /// on screen. `nil` where nothing does, where nothing is set to rank by,
    /// and while the spec on screen is not the one that was ranked.
    public var leads: Leads? {
        guard let ranking, !ranking.emptySpec, rankedHash == specHash else { return nil }
        return spec.leads
    }
}

/// An edit that was not applied, and the part of the search it was about.
public struct Refusal: Hashable, Sendable {
    /// The part the edit was about. `nil` when the edit names none.
    public let key: ChipKey?
    public let reason: RejectReason
}

extension SearchState {
    /// Every edit that was not applied: the ones a sentence made, and the ones
    /// a control made since. An edit that a question is being asked about is
    /// left out, because the question stands for it.
    public var refusals: [Refusal] {
        var found: [Refusal] = []
        if let read, !isReading {
            for refusal in read.rejected {
                let asked = read.clarify.contains { $0.group == refusal.group && $0.index == refusal.index }
                if asked { continue }
                found.append(
                    Refusal(
                        key: read.operations.said(refusal.group, refusal.index).first?.key,
                        reason: refusal.reason))
            }
        }
        if let refused {
            for refusal in refused.rejected {
                found.append(
                    Refusal(
                        key: refused.operations.said(refusal.group, refusal.index).first?.key,
                        reason: refusal.reason))
            }
        }
        return found
    }

    /// The reasons by part, for the controls. Only what a control sent is said at the control.
    public var refusedByPart: [ChipKey: RejectReason] {
        guard let refused else { return [:] }
        var byPart: [ChipKey: RejectReason] = [:]
        for refusal in refused.rejected {
            if let key = refused.operations.said(refusal.group, refusal.index).first?.key {
                byPart[key] = refusal.reason
            }
        }
        return byPart
    }
}

/// A thing that was asked for and that the data does not hold, as a screen names it.
public struct Missing: Hashable, Sendable, Identifiable {
    /// `budget`, `commute`, `feature:<id>` or `tag:<id>`, as the API names the target of a suggestion.
    public let target: String
    /// The API's label for it.
    public let label: String

    public var id: String { target }
}

extension ChipKey {
    /// The target an edit of a control was about, as the API names one.
    /// `nil` for a part that is never said to be missing from the data.
    var target: String? {
        switch self {
        case .budget: return "budget"
        case .journeys, .place: return "commute"
        case .tag(let id): return "tag:\(id.rawValue)"
        case .feature(let id): return "feature:\(id.rawValue)"
        case .tenure, .area: return nil
        }
    }
}

extension SearchState {
    /// Everything that was asked for and that the data holds for no area,
    /// each thing once: what the API named of the words that were read, and
    /// what a control asked for since and was turned away as not in the release.
    public var missing: [Missing] {
        var found: [Missing] = []
        for one in read?.notInRelease ?? [] where !found.contains(where: { $0.target == one.target }) {
            found.append(Missing(target: one.target, label: one.label))
        }
        guard let refused else { return found }
        for refusal in refused.rejected where refusal.reason == .notInRelease {
            guard let key = refused.operations.said(refusal.group, refusal.index).first?.key,
                let target = key.target, !found.contains(where: { $0.target == target })
            else { continue }
            found.append(Missing(target: target, label: label(of: key) ?? ""))
        }
        return found
    }

    /// True when a refusal is one a screen says under the box, as a thing the data does not hold.
    public func isSaidAsMissing(_ refusal: Refusal) -> Bool {
        guard refusal.reason == .notInRelease else { return false }
        // An edit that names no part is a budget's or a journey's, which the API names by its target.
        guard let target = refusal.key?.target else { return !missing.isEmpty }
        return missing.contains { $0.target == target }
    }

    /// The API's name for a feature or a vibe a chip is for. `nil` for any other part.
    private func label(of key: ChipKey) -> String? {
        switch key {
        case .feature(let id): return meta.features.first { $0.featureId == id }?.label
        case .tag(let id): return meta.tags.first { $0.tagId == id }?.label
        default: return nil
        }
    }
}

/// What puts right a search that names something the data no longer has.
public struct Repair: Hashable, Sendable {
    public enum What: String, Hashable, Sendable {
        case place
        case area
        case setting
    }

    public let what: What
    /// The part to take out, as the chips name it.
    public let key: ChipKey
    public let operations: Operations
}

extension SearchState {
    /// The repairs the failure on hand allows. None when the failure is of
    /// another kind, or when edits are waiting: a position in a path is a
    /// position in the spec as those edits leave it, which the app does not hold.
    public var repairs: [Repair] {
        guard let api = failure?.api,
            [ErrorCode.unknownPlace, .unknownArea, .invalidSpec].contains(api.code),
            pending.isEmpty
        else { return [] }
        var found: [Repair] = []
        for field in api.fields {
            guard let (list, at) = Self.position(in: field.path) else { continue }
            let repair: Repair?
            switch list {
            case "commutes":
                repair = spec.commutes[safe: at].map {
                    Repair(what: .place, key: .place($0.placeId), operations: Edits.placeRemove($0.placeId))
                }
            case "areas":
                repair = spec.areas[safe: at].map {
                    Repair(what: .area, key: .area($0.areaId), operations: Edits.areaClear($0.areaId))
                }
            case "weights":
                repair = spec.weights[safe: at].map {
                    Repair(
                        what: .setting, key: .feature($0.featureId),
                        operations: Edits.featureOff($0.featureId))
                }
            case "tags":
                repair = spec.tags[safe: at].map {
                    Repair(what: .setting, key: .tag($0.tagId), operations: Edits.tagOff($0.tagId))
                }
            default:
                repair = nil
            }
            if let repair, !found.contains(where: { $0.key == repair.key }) { found.append(repair) }
        }
        return found
    }

    /// Reads `spec.commutes[2].max_minutes` as the list `commutes` and the position 2.
    private static func position(in path: String) -> (String, Int)? {
        let prefix = "spec."
        guard path.hasPrefix(prefix) else { return nil }
        let rest = path.dropFirst(prefix.count)
        guard let open = rest.firstIndex(of: "["), let close = rest[open...].firstIndex(of: "]"),
            let at = Int(rest[rest.index(after: open)..<close])
        else { return nil }
        return (String(rest[..<open]), at)
    }
}
