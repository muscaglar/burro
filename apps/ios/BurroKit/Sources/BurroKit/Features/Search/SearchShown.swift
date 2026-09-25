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
    /// What was asked for that the data holds for no area, by name, with why.
    case notInData
    /// Something was read, and a stretch of what was typed was not.
    case readInPart
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
    /// What Burro noticed and did not apply, for the person to choose from.
    case offers
    /// Where a stretch of what was typed was not read, the way to see it in the box.
    case unread
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

/// One thing the reader noticed and did not apply, in its four parts: what it
/// would do, where the person's own words stand, what follows, and the choices.
/// Every word of it is the API's. It holds where the person's words stand, as
/// offsets, and never the words: they are cut from the box when it is drawn.
struct OfferShown: Hashable, Sendable, Identifiable {
    struct Choice: Hashable, Sendable, Identifiable {
        /// The API's id of the choice, which tells it from every other of its offer.
        /// The way a choice runs does not: a firm limit and a guide both add.
        let id: String
        /// The API's words for the choice: what it would do.
        let label: String
        /// True where this is the way Burro reads the words. It is a mark on the
        /// choice, said in words, and applies nothing.
        let guess: Bool
        /// What a screen reader is told: the words of the choice, the mark of the
        /// guess, and the thing it is a choice of where its words do not name it.
        /// "Add" and "Skip" are said of many things.
        let spoken: String
    }

    /// One place the release holds that is like the one that was typed, by the API's name for it.
    struct Option: Hashable, Sendable, Identifiable {
        let id: String
        let name: String
    }

    /// Where the suggestion stands among them all: a choice names its thing by its place.
    let at: Int
    /// By what the offer is told from every other of one answer, so that a place is
    /// chosen for the offer it was asked of, though the list changes meanwhile.
    let key: String
    /// The API's name for the thing. It is said to a screen reader and is not drawn:
    /// what the offer would do names the thing.
    let name: String
    /// What the offer would do, in the API's words. It begins with a verb, or is a question.
    let does: String
    /// Where the clause the offer rests on stands in the text that was sent. The
    /// person's words are cut from the box by it, under "You wrote".
    let shown: Span
    /// What follows for areas, and what nobody said and Burro took: a line for each,
    /// in the API's words and in the order it gave them.
    let follows: [String]
    /// What a person should know before they choose, in the API's words.
    let note: String?
    /// False where the suggestion before this one carries the same note,
    /// word for word: the note is drawn once, with the first of them.
    let noteDrawn: Bool
    let choices: [Choice]
    /// Where the words it rests on stand in the text that was sent.
    let spans: [Span]
    /// True where the journey is offered with no place: Burro does not know the place
    /// that was named, and the person says which before anything is sent.
    let asksPlace: Bool
    /// The places the release holds that are like the one that was named, five at
    /// most. None where nothing is like it.
    let options: [Option]

    var id: Int { at }

    /// True where a press on this choice asks which place, and sends nothing until one
    /// is chosen. Doing nothing needs no place.
    func asksWhichPlace(on choice: Choice) -> Bool {
        asksPlace && choice.id != Suggestion.skip
    }
}

/// Everything that is offered, as the screen draws it.
struct OffersShown: Hashable, Sendable {
    let offers: [OfferShown]
    /// Said while a model reads what the rules left unread. `nil` when none does. What
    /// the rules noticed is drawn meanwhile, and may be chosen of.
    let reading: String?
    /// What the last press of "Add all" did, in full: how many it added, how many areas
    /// a firm budget among them left out, and what is left for the person, which the API
    /// names. `nil` where nothing was added, and while a model reads: one line says what
    /// goes on.
    let added: String?
    /// The button that takes back all that the press added. `nil` where nothing was.
    let takeBack: String?
    /// The one button that adds every thing in sight that the API says one press
    /// may add, and the places in the list of those things. `nil` with fewer than two.
    let addAll: String?
    let addAllAts: [Int]
    /// The button that shows the suggestions that wait out of sight. `nil` when none does.
    let showAll: String?

    /// The one line that says what goes on: that a model reads, or else what one press added.
    var says: String? { reading ?? added }
}

/// Who reads what is typed, as the screen before the first search says it.
struct WhoReads: Hashable, Sendable {
    /// The API's words, as they were served, or what stands in their place
    /// until the service has said.
    let words: String
    /// True once the service has said who reads.
    let said: Bool
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
    /// What the box asks for. It asks only for what the data can answer, and says what it cannot.
    let hint: String
    /// Who reads what is typed, in the API's words, as they were served.
    let reader: String
    /// The sentences to start from: the first three the data can answer the whole of.
    let examples: [String]
    /// True where the data names no place to reach: no field is offered for one.
    let noPlaces: Bool
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
    /// What is said then: that the words could not be read just now, or that the
    /// language model would not read them and the rules have. `nil` when the words were read.
    let couldNotRead: String?
    let failure: FailureShown?
    let notice: String?
    let nothingRead: String?
    /// What was asked for that the data holds for no area: one line for each thing.
    let notInData: [String]
    /// The words that say so, where there is any.
    let notInDataLead: String?
    /// True when something was read and a stretch of what was typed was not.
    let readInPart: Bool
    let offers: OffersShown?
    /// The stretches of the text that was sent that were not read, as offsets.
    let unread: [Span]
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
        if box == .offered && !examples.isEmpty { parts.append(.examples) }
        parts += [.basics, .status]
        if offlineWaiting != nil { parts.append(.offline) }
        if !notInData.isEmpty { parts.append(.notInData) }
        if readInPart { parts.append(.readInPart) }
        if couldNotReadRetry != nil { parts.append(.couldNotRead) }
        if failure != nil { parts.append(.failure) }
        if notice != nil { parts.append(.notice) }
        if nothingRead != nil { parts.append(.nothingRead) }
        if !questions.isEmpty { parts.append(.questions) }
        parts.append(.chips)
        if !unmet.isEmpty { parts.append(.unmet) }
        if !notApplied.isEmpty { parts.append(.notApplied) }
        if offers != nil { parts.append(.offers) }
        if !unread.isEmpty { parts.append(.unread) }
        if hasRanking { parts.append(.results) }
        parts.append(.settings)
        return parts
    }
}

enum SearchScreen {
    /// How many suggestions are shown before "Show all" is pressed. Every thing beyond
    /// them that one press may add is shown as well.
    static let offersAtFirst = 4

    /// Where in the list the suggestions stand that are drawn before "Show all" is
    /// pressed: the first four, and every other that one press may add. So what waits
    /// out of sight is only what is the person's to choose, and the one button adds
    /// nothing that is not in sight.
    ///
    /// Those that carry Burro's guess come first, in the order their words stand in the
    /// sentence, and the rest after them in theirs: what Burro read stands before what
    /// it asks.
    static func inSight(_ suggestions: [Suggestion]) -> [Int] {
        suggestions.guessFirst(
            suggestions.indices.filter { $0 < offersAtFirst || suggestions[$0].addedWithOthers != nil })
    }

    /// Where every suggestion stands, as they are drawn once "Show all" is pressed: in
    /// the same order, so that nothing that was in sight moves when the rest is shown.
    static func everyOffer(_ suggestions: [Suggestion]) -> [Int] {
        suggestions.guessFirst(Array(suggestions.indices))
    }

    /// What is offered, as the screen draws it. `nil` where nothing is, no model reads
    /// and nothing was added: while one reads the screen says so, though the rules
    /// noticed nothing, and what one press added can be taken back though nothing is left.
    static func offers(
        _ suggestions: [Suggestion], all: Bool, reading: Bool = false, added: Added? = nil,
        leftOut: Int? = nil, heldAgainst: String? = nil
    ) -> OffersShown? {
        guard !suggestions.isEmpty || reading || added != nil else { return nil }
        let shown = all ? everyOffer(suggestions) : inSight(suggestions)
        var offers: [OfferShown] = []
        for at in shown {
            let suggestion = suggestions[at]
            let note = suggestion.noteShown
            // A note that neighbours share word for word is drawn once, with the first of them.
            let sameAsBefore = note != nil && offers.last?.note == note
            offers.append(
                OfferShown(
                    at: at, key: suggestion.key, name: suggestion.label, does: suggestion.does,
                    shown: suggestion.shown,
                    follows: (suggestion.follows.isEmpty ? [] : [suggestion.follows]) + suggestion.said,
                    note: note, noteDrawn: note != nil && !sameAsBefore,
                    choices: suggestion.choices.map { choice in
                        OfferShown.Choice(
                            id: choice.id, label: choice.label, guess: choice.guess,
                            spoken: spoken(choice, of: suggestion))
                    },
                    spans: suggestion.spans, asksPlace: suggestion.asksPlace,
                    options: suggestion.options.map { OfferShown.Option(id: $0.id, name: $0.name) }))
        }
        // The things in sight that one press may add, as the API marks them. What is
        // out of sight is never added.
        let oneWay = shown.filter { suggestions[$0].addedWithOthers != nil }
        let every = oneWay.count == shown.count
        let more = suggestions.count - shown.count
        return OffersShown(
            offers: offers,
            reading: reading ? SearchCopy.Suggest.reading : nil,
            added: reading
                ? nil
                : added.map {
                    SearchCopy.Suggest.added(
                        $0.count, needs: $0.needs, leftOut: leftOut, heldAgainst: heldAgainst)
                },
            takeBack: added == nil ? nil : SearchCopy.Suggest.takeBack,
            addAll: oneWay.count > 1
                ? (every
                    ? SearchCopy.Suggest.addAll(oneWay.count) : SearchCopy.Suggest.addThese(oneWay.count))
                : nil,
            addAllAts: oneWay.count > 1 ? oneWay : [],
            showAll: more > 0 ? SearchCopy.Suggest.showAll(suggestions.count) : nil)
    }

    /// True where the words of a choice name the thing it is a choice of, as "More pubs
    /// and bars" names pubs and bars, and "Add" names nothing.
    static func names(_ choice: String, _ thing: String) -> Bool {
        choice.localizedCaseInsensitiveContains(thing)
    }

    /// The words of a choice that is Burro's guess, with the mark after them.
    static func marked(_ label: String) -> String {
        "\(label) (\(SearchCopy.Suggest.guess))"
    }

    /// What a choice is called to whoever cannot see what it stands under: its own
    /// words, the mark of the guess, and the thing it is of where its words do not name it.
    static func spoken(_ choice: SuggestionChoice, of suggestion: Suggestion) -> String {
        let words = choice.guess ? marked(choice.label) : choice.label
        return names(choice.label, suggestion.label)
            ? words : SearchCopy.Suggest.named(words, suggestion.label)
    }

    /// What the screen shows of a search.
    ///
    /// - Parameter allOffers: True once "Show all" was pressed, of what was noticed.
    static func shown(
        _ state: SearchState, consent: ConsentChoice?, allOffers: Bool = false
    ) -> SearchShown {
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
        let holds = state.meta.holds
        // What was asked for that the data does not hold is said by name, directly under
        // the status. It is not said a second time among what was not applied.
        let missing = reading ? [] : NotInData.lines(of: state)

        return SearchShown(
            box: consent == .allowed ? .offered : .declined,
            hint: SearchCopy.Prompt.hint(costs: holds.costs, journeys: holds.journeys),
            reader: state.meta.reader.notice,
            examples: Examples.offered(for: state.meta),
            noPlaces: !holds.journeys,
            boxProblem: boxProblem,
            reading: reading,
            busy: state.isBusy,
            status: SearchStatus.line(state),
            offlineWaiting: place == .offline ? !state.pending.isEmpty : nil,
            couldNotReadRetry: state.degraded && !reading ? place == .form : nil,
            couldNotRead: state.degraded && !reading
                ? (state.modelRefused ? SearchCopy.Notice.refused : SearchCopy.Notice.degraded) : nil,
            failure: failure,
            notice: notice,
            nothingRead: nothingRead,
            notInData: missing,
            notInDataLead: missing.isEmpty ? nil : SearchCopy.NotInData.lead(missing.count),
            readInPart: state.readInPart,
            offers: offers(
                state.suggestions, all: allOffers, reading: state.modelIsReading, added: state.added,
                leftOut: state.leftOutByTheBudget, heldAgainst: state.rentsHeldAgainst),
            unread: state.unread,
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
                : state.refusals.filter { !state.isSaidAsMissing($0) }.compactMap { refusal in
                    rejected(refusal.reason, in: state.meta).map { reason in
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

    /// Who reads what is typed: what the API served, word for word. Until the
    /// service has said, the screen says that it is being asked, or that it
    /// has not said, and nothing typed is sent.
    static func whoReads(_ reader: Reader?, opening: AppModel.Opening) -> WhoReads {
        if let reader { return WhoReads(words: reader.notice, said: true) }
        if case .failed = opening { return WhoReads(words: SearchCopy.Reader.unsaid, said: false) }
        return WhoReads(words: SearchCopy.Reader.checking, said: false)
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
        // What a vibe that is a rough guide says of itself comes first: it is of
        // what the search holds, and is drawn under the chips with nothing pressed.
        var hints: [String] = SearchChips.rough(in: state.spec, meta: state.meta)
        if chips.contains(where: \.assumed) { hints.append(SearchCopy.Chips.assumedHint) }
        if chips.contains(where: { $0.kind == .usual }) {
            hints.append("\(SearchCopy.Chips.usualHint) \(SearchCopy.Chips.openSettings)")
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
    /// notice, a line about what was not read, a failure: each keeps them here. So
    /// does what one press added, where the line says that something is left for them.
    static func leadsToResults(_ state: SearchState) -> Bool {
        guard state.phase == .results, let ranking = state.ranking, !ranking.ranked.isEmpty else {
            return false
        }
        guard state.added?.needs.isEmpty ?? true else { return false }
        return state.conditions.isEmpty && state.unmetShown.isEmpty && state.refusals.isEmpty
    }

    /// True when the person is to be taken to the list and the map: an answer
    /// has come since they asked, it leads there, and this screen is the one
    /// they are on. Stopping a search takes nobody anywhere.
    static func arrives(_ state: SearchState, since answers: Int, onTop: Bool) -> Bool {
        onTop && state.answers > answers && leadsToResults(state)
    }

    /// Why an edit was not applied, as a screen says it of one release. The rule on
    /// recorded crime is followed by what is true of the release, where no vibe of
    /// it holds recorded crime. `nil` for a reason this build has no word for.
    static func rejected(_ reason: RejectReason, in meta: MetaData) -> String? {
        guard reason == .crimeNeedsExplicitRequest, !holdsACrimeVibe(meta) else {
            return SearchCopy.rejected(reason)
        }
        return "\(SearchCopy.crimeRule) \(SearchCopy.crimeNoVibe)"
    }

    /// True when the recipe of some vibe of the release holds a figure of
    /// recorded crime. Which one does is the API's to say.
    static func holdsACrimeVibe(_ meta: MetaData) -> Bool {
        meta.tags.contains { SearchChips.holdsRecordedCrime($0, meta.features) }
    }

    /// What is said of a failure: the API's own words for it, or the app's
    /// where the failure is not the API's.
    static func words(for failure: Failure) -> String {
        switch failure {
        case .api(let refusal): return failure.isStale ? SearchCopy.Notice.stale : refusal.message
        case .client(let own): return SearchCopy.failure(own.kind)
        }
    }

    /// The name of a part of the search, where it has one: the API's label, or a place's
    /// name. A place no answer named has none, and is said as "the place".
    static func name(of key: ChipKey, in state: SearchState, names: [String: String]) -> String? {
        switch key {
        case .feature(let id): return state.meta.features.first { $0.featureId == id }?.label
        case .tag(let id): return state.meta.tags.first { $0.tagId == id }?.label
        case .place(let id): return state.placeNames[id]
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
        // Where no limit left an area out, the line does not say that one did.
        if ranking.ranked.isEmpty {
            return ranking.filtered.isEmpty
                ? SearchCopy.Status.nothingRanked : SearchCopy.Status.nothingMatches
        }

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
        // What explains the order on screen is said of every ranking it is true of.
        if let leads = state.leads {
            said.append(
                SearchCopy.Status.leads(journeys: leads.journey ? leads.journeys : 0, budget: leads.budget))
        } else if state.gaveWay {
            said.append(SearchCopy.Status.gaveWay)
        }
        if asking { said.append(SearchCopy.Status.question) }
        return said.joined(separator: " ")
    }
}

/// Which stretch of what is in the box is selected, and what is said of it.
///
/// It holds where a stretch stands and never the words. Where words stand is
/// known for the text that was sent, and for no other, so this goes when the
/// box changes.
struct Showing: Hashable, Sendable {
    /// What the stretches are of: what was not read, or the suggestion at that place in the list.
    enum Of: Hashable, Sendable {
        case unread
        case offer(Int)
    }

    /// `nil` until something is shown.
    var of: Of?
    /// Which of the stretches is selected, from 1, and how many there are.
    var at = 0
    var among = 0
    /// How many times a stretch has been shown, so that the same one can be shown again.
    var presses = 0
    /// The stretch for the box to select. `nil` where there is none to select.
    var select: BoxSelect?

    /// What is said once a stretch is shown: that it is selected in the box,
    /// or that Burro cannot show which part it was.
    var said: String? {
        guard let of else { return nil }
        if among == 0 { return SearchCopy.Notice.partNotFound }
        switch of {
        case .unread: return SearchCopy.Notice.partShown(at, of: among)
        case .offer: return SearchCopy.Suggest.wordsShown
        }
    }

    /// The state after one more press: the next of these stretches is
    /// selected, and the first again after the last.
    func next(of wanted: Of, in found: [Range<String.Index>]) -> Showing {
        let first = of != wanted || among != found.count
        let index = first || found.isEmpty ? 0 : at % found.count
        var next = Showing()
        next.of = wanted
        next.presses = presses + 1
        next.among = found.count
        guard found.indices.contains(index) else { return next }
        next.at = index + 1
        next.select = BoxSelect(range: found[index], press: next.presses)
        return next
    }
}
