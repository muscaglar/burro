import Foundation

// What the search screen shows, worked out from the search and from what the
// person chose about their words. The screen draws this and decides nothing
// of its own, so that every state of docs/design/web.md section 3 can be
// tested with no screen to look at.

/// One part of the screen. They are drawn in this order, and the order never changes.
enum SearchPart: Int, Hashable, Sendable, CaseIterable, Comparable {
    /// The box to type in, with its button, or the line that stands in for it.
    case box
    /// The three sentences that fill the box.
    case examples
    /// Renting or buying, and the field for a place to reach.
    case basics
    /// What has just happened, in a line.
    case status
    case offline
    /// The words could not be read, so the settings are the way in.
    case couldNotRead
    /// A call failed: the API's words for it, and what can be done.
    case failure
    /// The API's one neutral sentence, word for word.
    case notice
    /// Nothing was read, or what was read changed nothing.
    case nothingRead
    case questions
    case chips
    case unmet
    case notApplied
    /// The way to the list and the map, once there is a ranking.
    case results
    case settings

    static func < (one: SearchPart, other: SearchPart) -> Bool {
        one.rawValue < other.rawValue
    }
}

/// What stands where a sentence is typed.
enum BoxShown: Hashable, Sendable {
    /// The box, because the person agreed that their words may be read.
    case offered
    /// A line in its place, because they chose the settings. Nothing typed is sent.
    case declined
}

/// A failure, as the error block says it.
struct FailureShown: Hashable, Sendable {
    /// The API's own words, or the app's where the failure is not the API's.
    let message: String
    /// True when results from before the failure are still there.
    let notUpdated: Bool
    /// `X-Request-Id`, to quote.
    let requestId: String?
    let repairs: [RepairShown]
}

/// One thing that can be taken out of a search that names what the data no longer has.
struct RepairShown: Hashable, Sendable, Identifiable {
    let label: String
    let operations: Operations
    var id: String { label }
}

/// An edit that was not applied: what it was about, where that has a name, and why.
struct NotAppliedShown: Hashable, Sendable {
    let about: String?
    let reason: String
}

/// One question: which place, or which area, was meant.
struct QuestionShown: Hashable, Sendable, Identifiable {
    struct Option: Hashable, Sendable, Identifiable {
        let id: String
        /// The API's name for it.
        let name: String
        let kind: String
    }

    let asked: Clarify
    let title: String
    let options: [Option]
    /// True when the place can be searched for. An area cannot.
    let searchable: Bool
    /// Said when Burro found nothing to offer.
    let none: String?

    var id: String { "\(asked.group.rawValue).\(asked.index)" }
}

struct SearchShown: Hashable, Sendable {
    let box: BoxShown
    /// The API's words for why the text was refused, when it was.
    let boxProblem: String?
    /// True while a sentence is being read.
    let reading: Bool
    /// True while anything is out: the list on hand is not yet the list of what is set.
    let busy: Bool
    let status: String
    /// `nil` when online. Otherwise whether a change is waiting to be sent.
    let offlineWaiting: Bool?
    /// `nil` when the words were read. Otherwise whether "Try again" is offered.
    let couldNotReadRetry: Bool?
    let failure: FailureShown?
    let notice: String?
    let nothingRead: String?
    let questions: [QuestionShown]
    /// The heading of the chips: what they are depends on how the search was made.
    let chipsTitle: String
    let chips: [SearchChip]
    /// True while a first sentence is being read and no chip can be drawn yet.
    let chipsWaiting: Bool
    /// Everything that explains the chips, drawn where it can be seen: what
    /// "assumed" means, what the usual settings are, why a place is shown by
    /// number, and who read the words. None of it is for a screen reader alone.
    let chipsHints: [String]
    let readBy: String?
    let unmet: [String]
    let notApplied: [NotAppliedShown]
    let settingsOpen: Bool
    /// True when the settings can be ranked as they stand.
    let canRank: Bool
    let hasRanking: Bool
    /// `nil` while more places can be named. Otherwise the line that says no more can.
    let placesFull: String?

    /// The parts that are on screen, in the order they are drawn.
    var parts: [SearchPart] {
        var parts: [SearchPart] = [.box]
        if box == .offered { parts.append(.examples) }
        parts += [.basics, .status]
        if offlineWaiting != nil { parts.append(.offline) }
        if couldNotReadRetry != nil { parts.append(.couldNotRead) }
        if failure != nil { parts.append(.failure) }
        if notice != nil { parts.append(.notice) }
        if nothingRead != nil { parts.append(.nothingRead) }
        if !questions.isEmpty { parts.append(.questions) }
        parts.append(.chips)
        if !unmet.isEmpty { parts.append(.unmet) }
        if !notApplied.isEmpty { parts.append(.notApplied) }
        if hasRanking { parts.append(.results) }
        parts.append(.settings)
        return parts
    }
}

enum SearchScreen {
    /// What the screen shows of a search.
    static func shown(_ state: SearchState, consent: ConsentChoice?) -> SearchShown {
        let reading = state.isReading
        let place = state.failurePlace
        let names = SearchChips.names(of: state.spec, held: state.placeNames)

        var boxProblem: String?
        if place == .box, let refusal = state.failure?.api { boxProblem = refusal.message }

        var failure: FailureShown?
        if place == .block, let failed = state.failure {
            failure = FailureShown(
                message: words(for: failed),
                notUpdated: state.ranking != nil,
                requestId: failed.requestId,
                repairs: state.repairs.map { repair in
                    RepairShown(
                        label: SearchCopy.Notice.takeOut(
                            name(of: repair.key, in: state, names: names) ?? words(for: repair.what)),
                        operations: repair.operations)
                })
        }

        // Where the API has words of its own for it, they are in the notice, and are not said twice.
        let notice = state.read != nil && !reading && state.noticed ? state.read?.noticeText : nil
        var nothingRead: String?
        if notice == nil {
            switch state.nothingRead {
            case .nothingRead: nothingRead = SearchCopy.Notice.nothingRead
            case .nothingChanged: nothingRead = SearchCopy.Notice.nothingChanged
            case nil: nothingRead = nil
            }
        }

        let questions = state.questions
        let readBy = state.read.flatMap { SearchCopy.readBy($0.interpreter) }
        let waiting = reading && state.read == nil && state.ranking == nil
        let chips = waiting ? [] : SearchChips.of(state)

        return SearchShown(
            box: consent == .allowed ? .offered : .declined,
            boxProblem: boxProblem,
            reading: reading,
            busy: state.isBusy,
            status: SearchStatus.line(state),
            offlineWaiting: place == .offline ? !state.pending.isEmpty : nil,
            couldNotReadRetry: state.degraded && !reading ? place == .form : nil,
            failure: failure,
            notice: notice,
            nothingRead: nothingRead,
            questions: questions.enumerated().map { at, question in
                asked(question, at: at + 1, of: questions.count)
            },
            chipsTitle: chipsTitle(state, waiting: waiting),
            chips: chips,
            chipsWaiting: waiting,
            chipsHints: waiting ? [] : chipsHints(chips, state, readBy: readBy),
            readBy: waiting ? nil : readBy,
            unmet: state.read != nil && !reading ? state.unmetShown.compactMap(SearchCopy.unmet) : [],
            notApplied: reading
                ? []
                : state.refusals.compactMap { refusal in
                    SearchCopy.rejected(refusal.reason).map { reason in
                        NotAppliedShown(
                            about: refusal.key.flatMap { name(of: $0, in: state, names: names) },
                            reason: reason)
                    }
                },
            settingsOpen: state.settingsOpen,
            canRank: state.ranking == nil && !state.isBusy,
            hasRanking: state.ranking != nil,
            placesFull: state.placesFull ? SearchCopy.Place.full(state.meta.limits.maxCommutes) : nil
        )
    }

    /// True when the spec is one of the two a search starts from, as the API served them.
    static func isWhereASearchStarts(_ state: SearchState) -> Bool {
        switch state.spec.tenure {
        case .rent: return state.spec == state.meta.defaults.rent
        case .buy: return state.spec == state.meta.defaults.buy
        case .unlisted: return false
        }
    }

    /// Before anything has changed the search, the chips are what a search
    /// starts from, and were understood from nothing. So are they after words
    /// that were read into nothing. A search made with the settings alone was
    /// not understood either: it is what the person set.
    static func chipsTitle(_ state: SearchState, waiting: Bool) -> String {
        if isWhereASearchStarts(state) { return SearchCopy.Chips.startLabel }
        return state.read != nil || waiting ? SearchCopy.Chips.label : SearchCopy.Chips.setLabel
    }

    static func chipsHints(_ chips: [SearchChip], _ state: SearchState, readBy: String?) -> [String] {
        var hints: [String] = []
        if chips.contains(where: \.assumed) { hints.append(SearchCopy.Chips.assumedHint) }
        if chips.contains(where: { $0.kind == .usual }) {
            hints.append("\(SearchCopy.Chips.usualHint) \(SearchCopy.Chips.openSettings)")
        }
        // The API gives a place's id and not its name (docs/design/web.md, section 13, gap 1).
        let unnamed = state.spec.commutes.filter { state.placeNames[$0.placeId] == nil }.count
        if unnamed > 0 {
            hints.append(SearchCopy.Place.unnamedHint(unnamed, of: state.spec.commutes.count))
        }
        if let readBy { hints.append(readBy) }
        return hints
    }

    /// True when the mark that turns while a call is out is drawn. It moves, so
    /// it is left out for a person who has asked for less motion: the words
    /// and the button say what is happening without it.
    static func showsItIsBusy(_ shown: SearchShown, reduceMotion: Bool) -> Bool {
        shown.busy && !reduceMotion
    }

    /// True when the settings are to be opened for the person: they chose the
    /// settings, so the form is the way in, and nothing has yet been asked for.
    static func opensTheForm(_ state: SearchState, consent: ConsentChoice?) -> Bool {
        consent == .settingsOnly && state.untouched && state.phase == .empty && !state.settingsOpen
    }

    /// True when a sentence has just been ranked and nothing here needs reading
    /// first, so that the person is taken to the list and the map. A question, a
    /// notice, a line about what was not read, a failure: each keeps them here.
    static func leadsToResults(_ state: SearchState) -> Bool {
        guard state.phase == .results, let ranking = state.ranking, !ranking.ranked.isEmpty else {
            return false
        }
        return state.conditions.isEmpty && state.unmetShown.isEmpty && state.refusals.isEmpty
    }

    /// True when the person is to be taken to the list and the map: an answer
    /// has come since they asked, it leads there, and this screen is the one
    /// they are on. Stopping a search takes nobody anywhere.
    static func arrives(_ state: SearchState, since answers: Int, onTop: Bool) -> Bool {
        onTop && state.answers > answers && leadsToResults(state)
    }

    /// What is said of a failure: the API's own words for it, or the app's
    /// where the failure is not the API's.
    static func words(for failure: Failure) -> String {
        switch failure {
        case .api(let refusal): return failure.isStale ? SearchCopy.Notice.stale : refusal.message
        case .client(let own): return SearchCopy.failure(own.kind)
        }
    }

    /// The name of a part of the search, where it has one: the API's label, or a place's name.
    static func name(of key: ChipKey, in state: SearchState, names: [String: String]) -> String? {
        switch key {
        case .feature(let id): return state.meta.features.first { $0.featureId == id }?.label
        case .tag(let id): return state.meta.tags.first { $0.tagId == id }?.label
        case .place(let id): return names[id] ?? state.placeNames[id]
        case .area(let id): return state.area(id)?.name
        case .tenure, .budget, .journeys: return nil
        }
    }

    private static func words(for what: Repair.What) -> String {
        switch what {
        case .place: return SearchCopy.Notice.thePlace
        case .area: return SearchCopy.Notice.theArea
        case .setting: return SearchCopy.Notice.theSetting
        }
    }

    private static func asked(_ question: Clarify, at: Int, of: Int) -> QuestionShown {
        let aboutAnArea = question.group == .areaOps
        let asked = aboutAnArea ? SearchCopy.Question.area : SearchCopy.Question.place
        // Two questions are told apart by their number, so that each has a name of its own.
        let title = of > 1 ? "\(asked) \(SearchCopy.Question.numbered(at, of: of))" : asked
        return QuestionShown(
            asked: question,
            title: title,
            options: question.options.map {
                QuestionShown.Option(id: $0.id, name: $0.name, kind: SearchCopy.kind($0.kind) ?? "")
            },
            searchable: !aboutAnArea,
            none: question.options.isEmpty && !aboutAnArea ? SearchCopy.Question.none : nil
        )
    }
}

enum SearchStatus {
    /// What the line says for a state of the search. One state, one thing said.
    static func line(_ state: SearchState) -> String {
        if state.phase == .interpreting { return SearchCopy.Status.reading }
        let asking = !state.questions.isEmpty
        guard let ranking = state.ranking else {
            return asking ? SearchCopy.Status.question : ""
        }
        if ranking.ranked.isEmpty { return SearchCopy.Status.nothingMatches }

        var said: [String] = []
        if ranking.emptySpec {
            said.append(SearchCopy.Status.rankedNoOrder(ranking.scores.count))
        } else if let moved = state.moved {
            said.append(SearchCopy.Status.moved(moved))
        } else {
            // The first result there is a name for. An area the release was not read
            // with has none, and a line that ends with no name says nothing.
            let first = ranking.ranked.lazy
                .compactMap { state.area($0.areaId)?.name }
                .first { !$0.isEmpty }
            said.append(
                first.map { SearchCopy.Status.ranked(ranking.scores.count, first: $0) }
                    ?? SearchCopy.Status.rankedUnnamed(ranking.scores.count))
        }
        if state.gaveWay { said.append(SearchCopy.Status.gaveWay) }
        if asking { said.append(SearchCopy.Status.question) }
        return said.joined(separator: " ")
    }
}
