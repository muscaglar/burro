import Foundation

// The one function that moves a search on. It is pure: the same state and
// the same event give the same state, and the state that was is not changed.
//
// It builds no spec. Every spec in the state is one the API returned, or one
// of the two defaults the API served.

/// The state a search is in after an event.
public func reduce(_ state: SearchState, _ event: SearchEvent) -> SearchState {
    var next = state
    switch event {
    case .tenureSwapped(let tenure):
        // Nothing has been asked for yet, so the other default is swapped in as it was served.
        guard state.untouched else { return state }
        switch tenure {
        case .rent: next.spec = state.meta.defaults.rent
        case .buy: next.spec = state.meta.defaults.buy
        case .unlisted: return state
        }
        next.specHash = nil
        // The default that was swapped in is the search now, and is what "Stop" goes back to.
        next.kept = nil
        next.answers += 1

    case .queued(let operations):
        next.pending = state.pending.merged(with: operations)
        next.assumed = afterEdits(state.assumed, operations)

    case .readStarted(let seq):
        next.phase = .interpreting
        next.before = settledPhase(state)
        // A sentence sent before the last one was ranked is undone with it: what is
        // kept is the search as it was when spec and ranking last agreed.
        next.kept = state.kept ?? keep(state)
        next.seq = seq
        next.failure = nil
        next.failedStep = nil

    case .readAnswered(let data, let by):
        let applied = Set(data.applied.map { Position(group: $0.group, index: $0.index) })
        let changed = data.applied.contains { $0.changed }
        // Where something was noticed, there is something to choose from, and the settings stay shut.
        let nothingRead =
            data.status == .offTopic
            || (!changed && data.clarify.isEmpty && data.suggestions.isEmpty)
        // An edit made while the words were read has not been answered by the reading.
        let answers = state.pending.isEmpty ? state.answers + 1 : state.answers
        next.spec = data.spec
        next.specHash = data.specHash
        next.answers = answers
        next.untouched = state.untouched && !changed
        next.gaveWay = changed && gaveWayBetween(state.spec, data.spec)
        next.read = Read(
            status: data.status,
            operations: data.operations,
            assumptions: data.assumptions,
            clarify: data.clarify,
            unmet: data.unmet,
            rejected: data.rejected,
            notice: data.notice,
            noticeText: data.noticeText,
            interpreter: data.interpreter,
            degraded: data.degraded,
            modelRefused: data.modelRefused,
            suggestions: data.suggestions,
            unread: data.unread,
            notInRelease: data.notInRelease,
            edits: data.operations.count,
            changed: changed,
            partUnread: !data.unread.isEmpty,
            at: answers,
            by: by ?? Served(form: state.meta),
            more: data.modelPending,
            chosen: [],
            added: nil
        )
        next.refused = nil
        next.degraded = data.degraded
        next.settingsOpen = state.settingsOpen || data.degraded || nothingRead
        next.assumed = withAssumptions(afterEdits(state.assumed, data.operations, only: applied), data)
        next.placeNames = named(data.places, held: state.placeNames)
        next.failure = nil
        next.failedStep = nil

    case .rankStarted(let seq):
        let reading = state.phase == .interpreting
        next.phase = reading ? .interpreting : .refining
        next.before = reading ? state.before : settledPhase(state)
        next.seq = seq
        next.failure = nil
        next.failedStep = nil

    case .rankAnswered(let data, let sent, let by):
        let ranking = Ranking(data)
        let changed = data.applied.contains { $0.changed }
        let by = by ?? Served(form: state.meta)
        inHand(&next, from: state, for: data.specHash, by: by)
        next.phase = .results
        next.before = .results
        next.kept = nil
        next.spec = data.spec
        next.specHash = data.specHash
        next.answers += 1
        next.untouched = false
        next.pending = .none
        next.refused = data.rejected.isEmpty ? nil : Refused(operations: sent, rejected: data.rejected)
        next.ranking = ranking
        next.rankedHash = data.specHash
        next.rankedBy = by
        next.placeNames = named(data.places, held: state.placeNames)
        next.moved = state.ranking.map { movedBetween($0, ranking) }
        next.gaveWay =
            (changed && gaveWayBetween(state.spec, data.spec))
            || (state.phase == .interpreting && state.gaveWay)
        next.failure = nil
        next.failedStep = nil

    case .shareAnswered(let id, let data, let by):
        // Whatever search was open gives way to the one the link holds. Nothing of
        // the search before is carried into it: not a name, not a reason, not an edit.
        next = SearchState(meta: state.meta, areas: state.areas, geometry: state.geometry)
        next.geometryFailed = state.geometryFailed
        next.online = state.online
        next.phase = .results
        next.before = .results
        next.seq = state.seq
        next.answers = state.answers + 1
        next.spec = data.spec
        next.specHash = data.specHash
        next.untouched = false
        next.ranking = Ranking(data)
        next.rankedHash = data.specHash
        next.rankedBy = by ?? Served(form: state.meta)
        next.placeNames = named(data.places, held: [:])
        next.shared = Shared(
            id: id, coarsened: data.coarsened, stale: data.stale,
            originalReleaseId: data.originalReleaseId)

    case .explainAnswered(let data, let hash, let by):
        let by = by ?? Served(form: state.meta)
        withFacts(&next, data.facts, by: by, rankedBy: state.rankedBy)
        next.placeNames = namesFrom(data.facts, held: state.placeNames)
        // Whatever was asked for has come, so it is no longer said to have failed.
        if state.explainFailure?.hash == hash { next.explainFailure = nil }
        let ours = state.ranking != nil && hash == state.rankedHash && by == state.rankedBy
        // The ranking on screen has its reasons, and these are for a ranking that has not
        // come. They wait for it. If it fails, the list keeps the reasons it has.
        if !ours && state.reasonsAreIn {
            next.explanationsAhead = ExplanationsAhead(
                hash: hash, by: by, explanations: data.explanations, facts: data.facts)
        } else {
            next.explanations = data.explanations
            next.explainedHash = hash
            next.explainedBy = by
            next.explanationsAhead = nil
        }

    case .explainFailed(let hash, let failure):
        next.explainFailure = ReasonsFailure(hash: hash, failure: failure)
        if failure.isOffline { next.online = false }

    case .detailAnswered(let data, let by):
        let areaId = data.area.areaId
        let by = by ?? Served(form: state.meta)
        next.details[areaId] = data
        next.detailsBy[areaId] = by
        next.detailFailures[areaId] = nil
        withFacts(&next, data.facts, by: by, rankedBy: state.rankedBy)

    case .detailFailed(let areaId, let failure):
        next.detailFailures[areaId] = failure
        if failure.isOffline { next.online = false }

    case .settled:
        // A reading that asked for no new ranking ends here, with what was on screen.
        guard state.phase == .interpreting || state.phase == .refining else { return state }
        next.phase = settledPhase(state)
        next.kept = nil

    case .failed(let step, let failure):
        let offline = failure.isOffline
        // Words that could not be read leave the settings as the way in. A
        // refusal of the words themselves is not that: the API read them.
        let refusal = failure.api.map { $0.status < 500 } ?? false
        let unread = step == .read && !offline && !refusal
        next.phase = state.before
        // Words that were not read changed nothing, so there is nothing to put back. Words
        // that were read and then not ranked stay on screen, beside the failure that says
        // so, and what was kept stays too: a later "Stop" must not leave them there in silence.
        next.kept = step == .read ? nil : state.kept
        next.failure = failure
        next.failedStep = step
        next.online = offline ? false : state.online
        next.degraded = state.degraded || unread
        next.settingsOpen = state.settingsOpen || unread

    case .stopped:
        next.phase = state.before
        guard state.phase == .interpreting, let kept = state.kept else { break }
        // The words may have been read already, and the chips drawn from them, over the
        // ranking of the search before. The search is put back as it was when the sentence
        // was sent. An edit made meanwhile still waits, and is sent with the spec put back.
        let waits = !state.pending.isEmpty
        next.spec = kept.spec
        next.specHash = kept.specHash
        next.untouched = kept.untouched
        next.read = kept.read
        next.refused = kept.refused
        next.placeNames = kept.placeNames
        next.gaveWay = kept.gaveWay
        next.degraded = kept.degraded
        next.assumed = waits ? afterEdits(kept.assumed, state.pending) : kept.assumed
        next.kept = nil
        // Reasons that came for the ranking that was stopped are let go with it.
        if !state.reasonsAreIn {
            next.explanations = []
            next.explainedHash = nil
            next.explainedBy = nil
        }
        next.explanationsAhead = nil
        if !waits && state.spec != kept.spec { next.answers = state.answers + 1 }

    case .startedAgain:
        next = SearchState(meta: state.meta, areas: state.areas, geometry: state.geometry)
        next.geometryFailed = state.geometryFailed
        next.online = state.online
        next.answers = state.answers + 1

    case .questionAnswered(let question, let id):
        let operations = state.read?.operations ?? .none
        // What was assumed of the journey asked about is assumed of the place chosen.
        let codes = (state.read?.assumptions ?? [])
            .filter { $0.group == question.group && $0.index == question.index }
            .map(\.code)
        if let asked = operations.said(question.group, question.index).first?.key {
            next.assumed[asked] = nil
        }
        if !codes.isEmpty && question.group == .commuteOps {
            next.assumed[.place(id)] = codes
        }
        next.read = withoutQuestion(state.read, question)

    case .questionLeft(let question):
        next.read = withoutQuestion(state.read, question)

    case .suggestionChosen(let at, let changes):
        guard var read = state.read, read.suggestions.indices.contains(at) else { return state }
        read.chosen.append(read.suggestions.remove(at: at).key)
        if changes {
            // The notice was written of the words as they were read, and may end "Nothing
            // you typed has changed your search". A choice that holds edits changes it. The
            // notice is the API's, and is never cut or reworded, so it goes whole.
            read.notice = .nothing
            read.noticeText = ""
        }
        next.read = read

    case .allAdded(let ats):
        guard var read = state.read else { return state }
        let taken = Set(ats)
        let added = read.suggestions.enumerated().filter { taken.contains($0.offset) }.map(\.element)
        guard !added.isEmpty else { return state }
        let left = read.suggestions.enumerated().filter { !taken.contains($0.offset) }.map(\.element)
        read.added = Added(
            count: added.count,
            // What is left for the person: of what was added, and of what was not.
            needs: (added + left).map(\.needs).filter { !$0.isEmpty },
            spec: state.spec,
            suggestions: read.suggestions)
        read.suggestions = left
        read.chosen += added.map(\.key)
        // What was added changes the search, so the notice goes whole, as it does for one choice.
        read.notice = .nothing
        read.noticeText = ""
        next.read = read

    case .allTakenBack:
        guard var read = state.read, let added = read.added else { return state }
        let back = Set(added.suggestions.map(\.key))
        read.suggestions = added.suggestions
        read.chosen = read.chosen.filter { !back.contains($0) }
        read.added = nil
        next.read = read

    case .readMoreAnswered(let data):
        guard var read = state.read, read.more else { return state }
        // What the person chose of while the model read is not offered again.
        let chosen = read.chosen
        read.suggestions = data.suggestions.filter { !chosen.contains($0.key) }
        read.unread = data.unread
        read.unmet = data.unmet
        read.partUnread = !data.unread.isEmpty
        read.interpreter = data.interpreter
        read.degraded = data.degraded
        read.modelRefused = data.modelRefused
        read.more = false
        next.read = read
        next.degraded = data.degraded

    case .readMoreFailed:
        guard var read = state.read, read.more else { return state }
        read.more = false
        next.read = read

    case .boxChanged:
        guard var read = state.read else { return state }
        let nothing = read.suggestions.isEmpty && read.unread.isEmpty
        if nothing && !read.more && read.added == nil { return state }
        // Where the words stand is known for what was sent, and for nothing else.
        read.suggestions = []
        read.unread = []
        read.more = false
        read.added = nil
        next.read = read

    case .placeNamed(let placeId, let name):
        guard state.placeNames[placeId] != name else { return state }
        next.placeNames[placeId] = name

    case .onlineChanged(let online):
        next.online = online
        if online && state.failure?.isOffline == true {
            next.failure = nil
            next.failedStep = nil
        }

    case .settingsOpened(let open):
        next.settingsOpen = open

    case .geometryLoaded(let geometry):
        next.geometry = geometry
        next.geometryFailed = false

    case .geometryFailed:
        guard state.geometry == nil else { return state }
        next.geometryFailed = true

    case .releaseChanged(let meta, let areas):
        // The form and the areas are read again. What the ranking on screen holds is of the
        // release that made the ranking, and goes when a ranking of another comes: the form
        // may come last, after the reasons and the profiles of the new release are in.
        next.meta = meta
        next.areas = areas

    case .selected(let areaId):
        next.selectedId = areaId
    }
    return next
}

/// How many areas are at another place in the order than they were, or are new to it or gone from it.
public func movedBetween(_ before: Ranking, _ after: Ranking) -> Int {
    let was = Dictionary(before.scores.enumerated().map { ($1.areaId, $0) }, uniquingKeysWith: { first, _ in first })
    let now = Dictionary(after.scores.enumerated().map { ($1.areaId, $0) }, uniquingKeysWith: { first, _ in first })
    let changed = now.filter { was[$0.key] != $0.value }.count
    let gone = was.keys.filter { now[$0] == nil }.count
    return changed + gone
}

/// True when a setting nobody chose counts for less in `after` than it did in `before`.
public func gaveWayBetween(_ before: PreferenceSpec, _ after: PreferenceSpec) -> Bool {
    let was = Dictionary(
        before.weights.filter { $0.provenance == .default }.map { ($0.featureId, $0.weight) },
        uniquingKeysWith: { first, _ in first })
    return after.weights.contains { weight in
        guard weight.provenance == .default, let held = was[weight.featureId] else { return false }
        return weight.weight < held
    }
}

// MARK: - Parts

private struct Position: Hashable {
    let group: OpsGroup
    let index: Int
}

private func settledPhase(_ state: SearchState) -> Phase {
    state.ranking == nil ? .empty : .results
}

private func keep(_ state: SearchState) -> Kept {
    Kept(
        spec: state.spec, specHash: state.specHash, untouched: state.untouched, read: state.read,
        refused: state.refused, assumed: state.assumed, placeNames: state.placeNames,
        gaveWay: state.gaveWay, degraded: state.degraded)
}

/// The name of each place an answer names, by its id. The names are the release's own.
/// A name in hand for a place the answer does not name is kept: a place that was picked
/// is named before the answer that holds it has come.
private func named(_ places: [NamedPlace], held: [String: String]) -> [String: String] {
    var names = held
    for place in places where !place.name.isEmpty { names[place.placeId] = place.name }
    return names
}

/// What a ranking finds in hand when it comes. When the release or the engine
/// that made it is another than made the ranking before, what the other made
/// goes: facts and profiles are of the release that made them. Reasons go
/// whenever another made them, and reasons that waited for this ranking, from
/// this release, are its reasons now.
private func inHand(_ next: inout SearchState, from state: SearchState, for hash: String, by: Served) {
    if state.rankedBy != by {
        next.facts = state.facts.filter { state.factsBy[$0.key] == by }
        next.factsBy = state.factsBy.filter { $0.value == by && state.facts[$0.key] != nil }
        next.details = state.details.filter { state.detailsBy[$0.key] == by }
        next.detailsBy = state.detailsBy.filter { $0.value == by && state.details[$0.key] != nil }
    }
    let waited = state.explanationsAhead
    let ahead = waited.flatMap { $0.hash == hash && $0.by == by ? $0 : nil }
    let ours = state.explainedBy == nil || state.explainedBy == by
    if let ahead {
        next.explanations = ahead.explanations
        next.explainedHash = ahead.hash
        next.explainedBy = ahead.by
        withFacts(&next, ahead.facts, by: by, rankedBy: by)
    } else if !ours {
        next.explanations = []
        next.explainedHash = nil
        next.explainedBy = nil
    }
    next.explanationsAhead = nil
}

/// The assumptions that still stand after these edits have said what they say.
private func afterEdits(_ assumed: Assumed, _ operations: Operations, only: Set<Position>? = nil) -> Assumed {
    var next = assumed
    for group in OpsGroup.inOrder {
        for index in 0..<operations.count(in: group) {
            if let only, !only.contains(Position(group: group, index: index)) { continue }
            let takenOut = operations.takesOut(group, index)
            for said in operations.said(group, index) {
                // A part that is taken out leaves nothing assumed behind it.
                if takenOut && said.key != .budget {
                    next[said.key] = nil
                    continue
                }
                let kept = (next[said.key] ?? []).filter { !said.states.contains($0) }
                next[said.key] = kept.isEmpty ? nil : kept
            }
        }
    }
    return next
}

private func withAssumptions(_ assumed: Assumed, _ data: InterpretData) -> Assumed {
    var next = assumed
    for assumption in data.assumptions {
        guard let key = data.operations.chip(assumption.group, assumption.index, assumption.code) else {
            continue
        }
        var held = next[key] ?? []
        if !held.contains(assumption.code) { held.append(assumption.code) }
        next[key] = held
    }
    return next
}

private func withoutQuestion(_ read: Read?, _ question: Clarify) -> Read? {
    guard var read else { return nil }
    let same: (OpsGroup, Int) -> Bool = { $0 == question.group && $1 == question.index }
    read.clarify = read.clarify.filter { !same($0.group, $0.index) }
    // The question stood for this refusal. With the question gone, so is it.
    read.rejected = read.rejected.filter { !same($0.group, $0.index) }
    return read
}

private func namesFrom(_ facts: [Fact], held: [String: String]) -> [String: String] {
    var names = held
    for fact in facts where fact.kind == .travel {
        // The key of a journey's fact is the place and the mode: `syn-p0021.pt`.
        guard let dot = fact.key.lastIndex(of: "."), let name = fact.slots["place"], !name.isEmpty else {
            continue
        }
        let placeId = String(fact.key[..<dot])
        if !placeId.isEmpty { names[placeId] = name }
    }
    return names
}

/// Adds the facts an answer brought to those in hand. A fact made by the
/// release that made the ranking is not given up for one made by another: a
/// profile may be answered from a cache for an hour after the release has moved.
private func withFacts(_ next: inout SearchState, _ facts: [Fact], by: Served, rankedBy: Served?) {
    let stranger = rankedBy != nil && rankedBy != by
    for fact in facts {
        if stranger && next.factsBy[fact.factId] == rankedBy { continue }
        next.facts[fact.factId] = fact
        next.factsBy[fact.factId] = by
    }
}
