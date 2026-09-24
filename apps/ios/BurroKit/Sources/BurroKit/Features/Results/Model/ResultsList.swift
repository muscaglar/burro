import Foundation

// The list of results, and everything that is said above it: what was ranked,
// what changed, and each state of docs/design/web.md section 3 that holds.
//
// One failure is said in one place on this screen. A line that needs the box
// the words were typed in leads back to the search: the words are not kept,
// so this screen cannot send them again.

extension Results {
    /// What a press on a line does.
    enum Act: Hashable, Sendable {
        /// Tries the call that failed again.
        case retry
        /// Goes back to the search, where the box and the settings are.
        case toSearch
        /// Sends one edit.
        case edit(Operations)
        /// Puts the search back to the settings the API serves, with nothing ranked.
        case startAgain
    }

    struct Press: Hashable, Sendable, Identifiable {
        let words: String
        let act: Act

        var id: String { words }
    }

    /// One thing said above the list.
    struct Line: Hashable, Sendable, Identifiable {
        enum Kind: String, Hashable, Sendable {
            /// The API's own neutral sentence, word for word.
            case notice
            /// Something about the search that is not a fault.
            case info
            /// A call failed.
            case failure
            case offline
        }

        let kind: Kind
        /// Each is a paragraph.
        let words: [String]
        /// The id of the request, to quote when reporting a fault.
        let requestId: String?
        let presses: [Press]

        var id: String { "\(kind.rawValue) \(words.joined(separator: " "))" }

        init(_ kind: Kind, _ words: [String], requestId: String? = nil, presses: [Press] = []) {
            self.kind = kind
            self.words = words
            self.requestId = requestId
            self.presses = presses
        }
    }

    /// Said when the ranking came back with nobody in it: why, as a count for
    /// each reason, and one press for each firm limit, which sends the one
    /// edit that loosens it.
    struct NothingMatches: Hashable, Sendable {
        struct Count: Hashable, Sendable, Identifiable {
            let reason: String
            let areas: String

            var id: String { reason }
        }

        let counts: [Count]
        let ways: [Press]
    }

    /// The list as a screen draws it.
    struct Listed: Hashable, Sendable {
        /// True while a sentence is being read or a new ranking worked out. The list stays where it is.
        let busy: Bool
        /// What is being waited for, in words. `nil` when nothing is.
        let waitingFor: String?
        /// How many areas were ranked, and the first of them by name.
        let headline: String?
        /// What the last answer changed: how many areas moved, and whether the usual settings gave way.
        let changes: [String]
        let lines: [Line]
        let nothing: NothingMatches?
        /// The results, in rank order. The order is the rank.
        let cards: [Card]
        /// True when there is no ranking yet.
        let empty: Bool
        let release: String
        let engine: String

        /// True when any result is a row, so the list says why it has no reasons.
        var saysFirstFive: Bool { cards.contains { !$0.full } }

        /// What is said aloud when the list changes.
        var announcement: String? {
            if let waitingFor { return waitingFor }
            let said = ([headline] + changes.map(Optional.some)).compactMap { $0 }
            return said.isEmpty ? nil : said.joined(separator: " ")
        }
    }

    // MARK: - Making it

    static func headline(of state: SearchState) -> String? {
        guard let ranking = state.ranking else { return nil }
        let count = ranking.scores.count
        if ranking.ranked.isEmpty { return ResultsCopy.Status.nothingMatches }
        if ranking.emptySpec { return ResultsCopy.Status.rankedNoOrder(count) }
        // The first result the app has a name for. With a name for none, the count alone.
        if let first = ranking.ranked.first, let name = state.area(first.areaId)?.name {
            return ResultsCopy.Status.ranked(count, first: name)
        }
        return ResultsCopy.Status.rankedUnnamed(count)
    }

    static func changes(of state: SearchState) -> [String] {
        guard state.ranking != nil, !state.isBusy else { return [] }
        var said: [String] = []
        if let moved = state.moved { said.append(ResultsCopy.Status.moved(moved)) }
        if state.gaveWay { said.append(ResultsCopy.Status.gaveWay) }
        return said
    }

    /// Each firm limit in the spec, with the one edit that loosens it.
    static func waysOut(of state: SearchState) -> [Press] {
        var ways: [Press] = []
        let spec = state.spec
        if spec.budget.amount != nil && spec.budget.strictness == .hard {
            ways.append(
                Press(words: ResultsCopy.NothingMatches.budgetFlexible, act: .edit(Edits.budgetStrictness(.soft))))
        }
        let names = placeNames(of: state)
        for commute in spec.commutes where commute.strictness == .hard {
            ways.append(
                Press(
                    words: ResultsCopy.NothingMatches.journeyFlexible(names[commute.placeId] ?? ""),
                    act: .edit(Edits.placeStrictness(commute.placeId, .soft))))
        }
        for rule in spec.areas {
            guard let name = state.area(rule.areaId)?.name else { continue }
            let words: String
            switch rule.rule {
            case .exclude: words = ResultsCopy.NothingMatches.showHidden(name)
            case .only: words = ResultsCopy.NothingMatches.showAll(name)
            case .unlisted: continue
            }
            ways.append(Press(words: words, act: .edit(Edits.areaClear(rule.areaId))))
        }
        return ways
    }

    static func nothingMatches(of state: SearchState) -> NothingMatches? {
        guard let ranking = state.ranking, ranking.ranked.isEmpty else { return nil }
        var counts: [NothingMatches.Count] = []
        for reason in FilterReason.allCases {
            let count = ranking.filtered.filter { $0.reason == reason }.count
            if count > 0, let words = ResultsCopy.word(for: reason) {
                counts.append(.init(reason: words, areas: ResultsCopy.NothingMatches.count(count)))
            }
        }
        for reason in UnrankedReason.allCases {
            let count = ranking.unranked.filter { $0.reason == reason }.count
            if count > 0, let words = ResultsCopy.word(for: reason) {
                counts.append(.init(reason: words, areas: ResultsCopy.NothingMatches.count(count)))
            }
        }
        return NothingMatches(counts: counts, ways: waysOut(of: state))
    }

    /// Every state that sits on the phase, as a line. Several can hold at once.
    static func lines(of state: SearchState) -> [Line] {
        var lines: [Line] = []
        let conditions = state.conditions
        let toSearch = Press(words: ResultsCopy.Status.toSearch, act: .toSearch)

        if let shared = state.shared {
            var words = [ResultsCopy.Notice.shared, ResultsCopy.Notice.sharedText]
            if shared.coarsened { words.append(ResultsCopy.Notice.sharedCoarsened) }
            if shared.stale { words.append(ResultsCopy.Notice.sharedStale) }
            lines.append(Line(.info, words))
        }

        switch state.failurePlace {
        case .none:
            // The search came, and the reasons or a profile of one of its cards did not.
            // The card says what it lacks. Here is why, in the API's words with the id to
            // quote, and "Try again", which ranks again and asks for what is missing.
            if let failure = state.failureOfTheCards {
                lines.append(block(for: failure, in: state, ofTheCards: true))
            }
        case .offline:
            var words = [ResultsCopy.Notice.offline]
            if !state.pending.isEmpty { words.append(ResultsCopy.Notice.offlineWaiting) }
            lines.append(Line(.offline, words))
        case .form:
            // Said below, with the rest of what makes the settings the way in.
            break
        case .box:
            // The API refused the words. They are in the box, on the search.
            if let failure = state.failure {
                lines.append(Line(.failure, [ShellCopy.words(for: failure)], presses: [toSearch]))
            }
        case .block:
            if let failure = state.failure {
                lines.append(block(for: failure, in: state))
            }
        }

        if conditions.contains(.degraded) {
            lines.append(Line(.info, [ResultsCopy.Notice.degradedHere], presses: [toSearch]))
        }
        if conditions.contains(.notice), let read = state.read {
            lines.append(Line(.notice, [read.noticeText]))
        }
        if conditions.contains(.nothingRead) {
            // The API's own sentence says it, where there is one.
            if !conditions.contains(.notice) {
                lines.append(Line(.info, [ResultsCopy.Notice.nothingReadHere], presses: [toSearch]))
            }
        }
        if conditions.contains(.nothingChanged) {
            lines.append(Line(.info, [ResultsCopy.Notice.nothingChanged]))
        }
        if conditions.contains(.clarifying) {
            lines.append(Line(.info, [ResultsCopy.Status.question], presses: [toSearch]))
        }
        return lines
    }

    /// The error block: the API's message as it came, the id to quote, and what can be done.
    ///
    /// - Parameter ofTheCards: True when the search itself did not fail, and what its cards
    ///   hold did. The results were updated then, so nothing says they were not.
    private static func block(for failure: Failure, in state: SearchState, ofTheCards: Bool = false) -> Line {
        var words = [failure.isStale ? ResultsCopy.Notice.stale : ShellCopy.words(for: failure)]
        if state.ranking != nil && !ofTheCards { words.append(ResultsCopy.Notice.notUpdated) }
        let repairs = (ofTheCards ? [] : state.repairs).map { repair in
            let what: String
            switch repair.what {
            case .place: what = ResultsCopy.Notice.thePlace
            case .area: what = ResultsCopy.Notice.theArea
            case .setting: what = ResultsCopy.Notice.theSetting
            }
            return Press(
                words: ResultsCopy.Notice.takeOut(named(repair, in: state) ?? what),
                act: .edit(repair.operations))
        }
        // A sentence is not kept, so one that could not be read is sent again from its box.
        let sendsWords = state.failedStep == .read && !ofTheCards
        let again = Press(words: ResultsCopy.Notice.tryAgain, act: sendsWords ? .toSearch : .retry)
        let afresh = Press(words: ResultsCopy.Notice.startAgain, act: .startAgain)
        return Line(.failure, words, requestId: failure.requestId, presses: unique(repairs + [again, afresh]))
    }

    /// The name of what a repair takes out, where the app has one: a place
    /// the person picked, an area of the release, a feature or a tag.
    private static func named(_ repair: Repair, in state: SearchState) -> String? {
        switch repair.key {
        case .place(let placeId): return state.name(ofPlace: placeId)
        case .area(let areaId): return state.area(areaId)?.name
        case .feature(let featureId): return state.meta.features.first { $0.featureId == featureId }?.label
        case .tag(let tagId): return state.meta.tags.first { $0.tagId == tagId }?.label
        case .tenure, .budget, .journeys: return nil
        }
    }

    /// No two presses of a line have one name.
    private static func unique(_ presses: [Press]) -> [Press] {
        var seen: Set<String> = []
        return presses.filter { seen.insert($0.words).inserted }
    }

    static func listed(_ state: SearchState) -> Listed {
        let ranked = state.ranking?.ranked ?? []
        let scale = Results.scale(of: state)
        let waitingFor: String? =
            state.isReading ? ResultsCopy.Status.reading : state.isBusy ? ResultsCopy.Status.updating : nil
        return Listed(
            busy: state.isBusy,
            waitingFor: waitingFor,
            headline: headline(of: state),
            changes: changes(of: state),
            lines: lines(of: state),
            nothing: nothingMatches(of: state),
            cards: ranked.enumerated().compactMap { card(for: $1, at: $0, in: state, on: scale) },
            empty: state.ranking == nil,
            // The release and the engine that made the ranking, and not those the form was read from.
            release: state.servedTheRanking.releaseId,
            engine: state.servedTheRanking.engineVersion)
    }
}
