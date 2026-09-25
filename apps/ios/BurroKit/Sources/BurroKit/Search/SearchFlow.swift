import Foundation

/// What a person can do to a search: each thing, as the calls it makes and
/// the events it sends to the store. It mirrors apps/web/src/lib/search/flow.ts.
///
/// Five rules are kept here.
///
/// 1. The sentence a person typed is passed to the call that reads it, and to
///    one more where a model reads, and is never kept. It is not in the store,
///    and not in this object once they are answered.
/// 2. No sentence is sent until the person has agreed that their words may be read.
/// 3. The app never edits a spec. An edit is sent with the last spec the API
///    returned, and the spec that comes back replaces it. Edits made while a
///    call is out are sent again together, so none is lost.
/// 4. The latest request wins. Each run of calls has a number, and an answer
///    to an older run is dropped.
/// 5. What is on screen is of one release. Every answer names the release
///    that made it, and that is kept with what the answer brought. Reasons
///    are a ranking's only when the same release made both.
@MainActor
public final class SearchFlow {
    /// How many results the list holds, and how many of them the API gives reasons for.
    public nonisolated static let listLength = 20
    public nonisolated static let explained = 5
    /// The fewest and the most characters a place search may hold, and how many it asks for.
    public nonisolated static let placeQuery = (least: 2, most: 80, limit: 8)

    private let api: any BurroAPI
    private unowned let store: SearchStore
    private let mayReadWords: @MainActor () -> Bool

    private var current = Run(number: 0)
    private var readingRun: Int?
    /// The model's reading of what the rules left unread, while it is under way.
    private var reading: Task<Void, Never>?
    /// Counts such readings, so that the answer to one that was let go is dropped.
    private var readings = 0
    /// The release the form is being read again for, while it is, so that it is not asked for twice at once.
    private var catchingUp: (release: String, token: Int, done: Task<Void, Never>)?
    private var catchUps = 0
    /// The release whose boundaries could not be read when its form could.
    private var boundariesOwed: String?

    init(api: any BurroAPI, store: SearchStore, mayReadWords: @escaping @MainActor () -> Bool) {
        self.api = api
        self.store = store
        self.mayReadWords = mayReadWords
    }

    private var state: SearchState { store.state }

    // MARK: - What a person can do

    /// Sends a sentence to be read. The text goes to the call and nowhere else.
    /// Nothing is sent if the person has not agreed, or if the line is empty.
    public func submitText(_ text: String) async {
        let said = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !said.isEmpty, mayReadWords() else { return }
        stopReading()
        let mine = begin()
        readingRun = mine.number
        store.dispatch(.readStarted(seq: mine.number))
        // The rules are asked first, and answer at once. What they offer never waits on a model.
        let sent = state.spec
        let body = InterpretBody(text: said, askModel: false, spec: sent)
        let answer = await call(mine) { [api] in await api.interpret(body) }
        guard !isStale(mine) else { return }
        readingRun = nil
        switch answer {
        case .failure(let failure):
            fail(.read, failure)
            // A control moved while the words were being read is not lost with them.
            if !failure.isOffline { await sendWhatWaits() }
        case .success(let read):
            heard(read.meta)
            store.dispatch(.readAnswered(read.data, by: Served(read.meta)))
            // Then the model, where one reads and the rules left words unread.
            let more = read.data.modelPending ? readMore(said, with: sent) : nil
            let changed = read.data.applied.contains { $0.changed }
            let pending = state.pending
            if changed || !pending.isEmpty {
                await settle(mine, spec: read.data.spec, hash: read.data.specHash, operations: pending)
            } else {
                store.dispatch(.settled)
            }
            await more?.value
        }
    }

    /// Asks again, of the model this time, for the same words and the same search. It has
    /// a stop of its own: a control that is moved meanwhile ranks, and does not stop the
    /// reading. The words go to the call and nowhere else.
    private func readMore(_ said: String, with sent: PreferenceSpec) -> Task<Void, Never> {
        readings += 1
        let mine = readings
        let body = InterpretBody(text: said, askModel: true, spec: sent)
        let asked = Task { @MainActor [self] in
            let answer = await call(nil) { [api] in await api.interpret(body) }
            // A reading that was let go has nothing to say.
            guard reading != nil, readings == mine else { return }
            reading = nil
            switch answer {
            case .success(let read): store.dispatch(.readMoreAnswered(read.data))
            case .failure: store.dispatch(.readMoreFailed)
            }
        }
        reading = asked
        return asked
    }

    /// Stops the model's reading, where one is under way. What it would have added is let go.
    private func stopReading() {
        reading?.cancel()
        reading = nil
    }

    /// Sends the edits of one control.
    public func applyEdits(_ operations: Operations) async {
        guard !operations.isEmpty else { return }
        store.dispatch(.queued(operations))
        // A sentence is being read: its answer brings the spec these edits are for.
        if let readingRun, readingRun == current.number { return }
        await rerank()
    }

    /// Answers "Which place did you mean?" with the place that was picked.
    public func answerClarify(_ question: Clarify, id: String, name: String) async {
        guard let read = state.read,
            let operations = Edits.answered(read.operations, question.group, question.index, id: id)
        else { return }
        if question.group == .commuteOps {
            store.dispatch(.placeNamed(placeId: id, name: name))
        }
        store.dispatch(.questionAnswered(question, id: id))
        await applyEdits(operations)
    }

    /// "Leave it out": the question goes, and nothing is sent.
    public func leaveOut(_ question: Clarify) {
        store.dispatch(.questionLeft(question))
    }

    /// Takes one of the choices of an offer, by its id. The offer goes, whatever was
    /// chosen. A choice that holds edits sends them as the API gave them, as a control
    /// does. "Skip" holds none, and sends nothing. A journey to a place the release does
    /// not hold is sent with the place the person chose for it, and is not sent without
    /// one: the person has yet to say.
    public func choose(at: Int, id: String, place: (id: String, name: String)? = nil) async {
        guard let choice = state.read?.suggestions[safe: at]?.choices.first(where: { $0.id == id })
        else { return }
        let operations = place.map { choice.operations.withPlace($0.id) } ?? choice.operations
        guard operations.namesItsPlaces else { return }
        // A place that was picked is named before the answer that holds it has come.
        if let place, operations != choice.operations {
            store.dispatch(.placeNamed(placeId: place.id, name: place.name))
        }
        store.dispatch(.suggestionChosen(at: at, changes: !operations.isEmpty))
        await applyEdits(operations)
    }

    /// Takes, of each of these offers, the way the API says one press may add, in one
    /// request. What the API names no way for is left as it is: it is the person's to
    /// choose.
    public func chooseAll(_ ats: [Int]) async {
        let offered = state.read?.suggestions ?? []
        let taken = Set(ats).sorted().compactMap { at -> (at: Int, operations: Operations)? in
            guard let only = offered[safe: at]?.addedWithOthers, only.operations.namesItsPlaces else {
                return nil
            }
            return (at, only.operations)
        }
        guard !taken.isEmpty else { return }
        store.dispatch(.allAdded(ats: taken.map(\.at)))
        // The edits of each choice, as the API gave them, in the order the things were noticed.
        await applyEdits(taken.reduce(Operations.none) { $0.merged(with: $1.operations) })
    }

    /// Takes back all that the last "Add all" added: the search and the offers are as
    /// they were. The search as it stood before the press is ranked again, with no edit,
    /// and nothing of what was added is kept.
    public func takeBack() async {
        guard let added = state.read?.added else { return }
        store.dispatch(.allTakenBack)
        let mine = begin()
        readingRun = nil
        await settle(mine, spec: added.spec, hash: nil, operations: .none)
    }

    /// Told that the box changed, and never what to. What rested on the text that was sent goes.
    public func boxChanged() {
        stopReading()
        store.dispatch(.boxChanged)
    }

    /// Adds a place picked from the place search as a journey.
    public func addPlace(_ place: FoundPlace) async {
        store.dispatch(.placeNamed(placeId: place.placeId, name: place.name))
        await applyEdits(Edits.placeAdd(place.placeId))
    }

    public func setTenure(_ tenure: Tenure) async {
        guard state.spec.tenure != tenure else { return }
        // Before anything is asked for, the other default is shown, and nothing is sent.
        if state.untouched && state.pending.isEmpty && readingRun == nil {
            store.dispatch(.tenureSwapped(tenure))
            return
        }
        await applyEdits(Edits.tenure(tenure))
    }

    /// Ranks the settings as they stand, with no edit.
    public func rankNow() async {
        await rerank()
    }

    /// Tries again what failed. A sentence is passed in, because none is kept. Where it is
    /// the reasons or a profile that failed, the search is ranked again and they are asked
    /// for with it, so that the ranking and what its cards hold come from one release.
    public func retry(text: String? = nil) async {
        if state.failedStep == .read, let text,
            !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        {
            await submitText(text)
            return
        }
        await rerank()
    }

    /// Stops what is being worked out. While a sentence is read or ranked, the search goes
    /// back to what it was when the sentence was sent. It answers when the edits that
    /// waited on it have been sent.
    public func stop() async {
        // "Stop" is offered until the ranking of the words is in, which is after they are read.
        let wasReading = state.phase == .interpreting
        stopReading()
        _ = begin()
        readingRun = nil
        store.dispatch(.stopped)
        // Stopping the reading of a sentence does not undo a control moved meanwhile.
        if wasReading { await sendWhatWaits() }
    }

    public func startAgain() {
        stopReading()
        _ = begin()
        readingRun = nil
        store.dispatch(.startedAgain)
    }

    /// Opens a shared search: the spec the link holds, ranked now. It answers
    /// with the failure where there is one, for the screen that opened the
    /// link to say, and with `nil` when the search is open.
    public func openShare(_ shareId: String) async -> Failure? {
        let mine = begin()
        readingRun = nil
        let answer = await call(mine) { [api] in await api.getShare(shareId) }
        guard !isStale(mine) else { return nil }
        switch answer {
        case .failure(let failure):
            // The screen that opened the link says what went wrong. The search
            // that was open is left as it was.
            return failure
        case .success(let share):
            // Where the release has moved on, the form is read again first, so that the shared
            // search is drawn with the names and the limits of the release that ranked it.
            await catchUp(with: share.meta)?.value
            guard !isStale(mine) else { return nil }
            store.dispatch(.shareAnswered(id: shareId, share.data, by: Served(share.meta)))
            await fill(
                mine, spec: share.data.spec, hash: share.data.specHash, ranked: share.data.ranked,
                explaining: nil)
            return nil
        }
    }

    /// Route 9. Stores the search as it stands and answers with the id of the share.
    public func createShare(exactPlaces: Bool) async -> Answer<ShareCreated> {
        // The spec is the last one the API returned. Nothing a person typed goes with it.
        await api.createShare(ShareBody(spec: state.spec, exactDestinations: exactPlaces))
    }

    /// Route 7. Two to four areas, side by side, for the search as it stands.
    public func compare(areaIds: [String]) async -> Answer<CompareData> {
        await api.compare(CompareBody(areaIds: areaIds, spec: state.spec))
    }

    /// Route 8, for the place search. What is typed goes in the body of the call.
    public func searchPlaces(_ text: String) async -> Answer<PlacesData> {
        await api.searchPlaces(PlaceSearchBody(q: text, limit: Self.placeQuery.limit))
    }

    /// Route 6, for an area that is not among the first of the list.
    public func loadDetail(areaId: String) async {
        await details(nil, [areaId])
    }

    public func select(_ areaId: String?) {
        store.dispatch(.selected(areaId: areaId))
    }

    public func openSettings(_ open: Bool) {
        store.dispatch(.settingsOpened(open))
    }

    public func loadGeometry() async {
        guard state.geometry == nil else { return }
        switch await api.getGeometry() {
        case .success(let answer): store.dispatch(.geometryLoaded(answer.data))
        case .failure: store.dispatch(.geometryFailed)
        }
    }

    public func wentOffline() {
        store.dispatch(.onlineChanged(false))
    }

    public func wentOnline() async {
        let waiting =
            !state.pending.isEmpty || (state.failure?.isOffline == true && state.failedStep == .rank)
            // The reasons or a profile that could not leave are asked for again with the ranking.
            || state.failureOfTheCards?.isOffline == true
        store.dispatch(.onlineChanged(true))
        // The edit that waited is sent once, now that it can leave.
        if waiting { await rerank() }
    }

    /// Waits until a change of release that an answer told of has been read in.
    /// Nothing on a screen needs it. A test does.
    func caughtUp() async {
        await catchingUp?.done.value
    }

    // MARK: - Runs

    /// One run of calls. Starting the next one stops every call of this one.
    @MainActor
    private final class Run {
        let number: Int
        private var stops: [() -> Void] = []
        private(set) var stopped = false

        init(number: Int) {
            self.number = number
        }

        func onStop(_ stop: @escaping () -> Void) {
            if stopped { stop() } else { stops.append(stop) }
        }

        func stop() {
            stopped = true
            stops.forEach { $0() }
            stops = []
        }
    }

    /// Starts a run: the one before it is stopped, and its answers are dropped.
    private func begin() -> Run {
        current.stop()
        current = Run(number: current.number + 1)
        return current
    }

    private func isStale(_ mine: Run) -> Bool {
        mine.number != current.number
    }

    /// Makes one call of a run, so that the run after it can stop it.
    private func call<Value: Sendable>(
        _ mine: Run?, _ work: @escaping @Sendable () async -> Value
    ) async -> Value {
        let task = Task(operation: work)
        mine?.onStop { task.cancel() }
        return await withTaskCancellationHandler {
            await task.value
        } onCancel: {
            task.cancel()
        }
    }

    private func fail(_ step: SearchStep, _ failure: Failure) {
        // A call that was stopped has nothing to report.
        if failure.isAborted {
            store.dispatch(.stopped)
        } else {
            store.dispatch(.failed(step: step, failure))
        }
    }

    /// Every answer says which release made it. If that has changed, the form is read again.
    private func heard(_ meta: Meta) {
        catchUp(with: meta)
    }

    /// The same, for whoever must wait until the form has been read again
    /// before going on. `nil` when there is nothing to wait for.
    @discardableResult
    private func catchUp(with meta: Meta) -> Task<Void, Never>? {
        let release = meta.releaseId
        let upToDate = release == state.meta.releaseId && boundariesOwed != release
        if upToDate { return nil }
        if let catchingUp, catchingUp.release == release { return catchingUp.done }
        catchUps += 1
        let token = catchUps
        // A read that fails is not remembered. The next answer that names the release asks again.
        let done = Task { @MainActor [self] in
            await refresh()
            if catchingUp?.token == token { catchingUp = nil }
        }
        catchingUp = (release, token, done)
        return done
    }

    private func refresh() async {
        async let served = api.getMeta()
        async let listed = api.listAreas()
        async let drawn = api.getGeometry()
        let (metaAnswer, areasAnswer, geometryAnswer) = await (served, listed, drawn)
        guard case .success(let newMeta) = metaAnswer, case .success(let newAreas) = areasAnswer else {
            return
        }
        store.dispatch(.releaseChanged(meta: newMeta.data, areas: newAreas.data.areas))
        if case .success(let geometry) = geometryAnswer {
            boundariesOwed = nil
            store.dispatch(.geometryLoaded(geometry.data))
        } else {
            boundariesOwed = newMeta.data.releaseId
        }
    }

    private func explain(_ mine: Run, spec: PreferenceSpec, hash: String) async {
        let body = ExplanationsBody(spec: spec, limit: Self.explained)
        let answer = await call(mine) { [api] in await api.explainTop(body) }
        guard !isStale(mine) else { return }
        switch answer {
        case .success(let explained):
            store.dispatch(.explainAnswered(explained.data, hash: hash, by: Served(explained.meta)))
        case .failure(let failure):
            if !failure.isAborted { store.dispatch(.explainFailed(hash: hash, failure)) }
        }
    }

    /// Route 6 for each area not yet in hand. An area is asked for by its slug.
    private func details(_ mine: Run?, _ areaIds: [String]) async {
        let held = state.details
        let wanted =
            areaIds
            .filter { held[$0] == nil }
            .compactMap { areaId in state.areas.first { $0.areaId == areaId } }
        // Each is asked for at once, and the run can stop any of them.
        let asked = wanted.map { area in
            Task { @MainActor [self] in await detail(mine, area) }
        }
        for one in asked { await one.value }
    }

    private func detail(_ mine: Run?, _ area: AreaSummary) async {
        let answer = await call(mine) { [api] in await api.getArea(area.slug) }
        switch answer {
        case .success(let profile):
            // A profile is of the release and not of the search, so a late one is still right.
            store.dispatch(.detailAnswered(profile.data, by: Served(profile.meta)))
        case .failure(let failure):
            if !failure.isAborted { store.dispatch(.detailFailed(areaId: area.areaId, failure)) }
        }
    }

    /// What the cards of a ranking hold: the profiles of its first areas, and its reasons.
    /// `explaining` is the call for the reasons where it was made beside the ranking.
    private func fill(
        _ mine: Run, spec: PreferenceSpec, hash: String, ranked: [RankedArea],
        explaining: Task<Void, Never>?
    ) async {
        let first = ranked.prefix(Self.explained).map(\.areaId)
        async let profiles: Void = details(mine, first)
        if let explaining {
            await explaining.value
        } else if !first.isEmpty && !state.reasonsAreIn {
            await explain(mine, spec: spec, hash: hash)
        }
        await profiles
        // The reasons must be for the ranking on screen: for the same spec, and made by the
        // same release. If they are not, as when the release moved between the two calls,
        // they are asked for once more.
        func settled() -> Bool {
            isStale(mine) || state.reasonsAreIn || state.reasonsFailure != nil
        }
        if first.isEmpty || settled() { return }
        await explain(mine, spec: spec, hash: hash)
        if settled() { return }
        // Reasons that are still another release's are never shown as this ranking's. They are
        // said not to have come, so that no card is left waiting, and "Try again" ranks again.
        store.dispatch(.explainFailed(hash: hash, .because(.unreadable)))
    }

    private func settle(_ mine: Run, spec: PreferenceSpec, hash: String?, operations: Operations) async {
        // With no edit to apply the spec is final, so its reasons are asked for at once.
        var explaining: Task<Void, Never>?
        if operations.isEmpty, let hash {
            explaining = Task { @MainActor [self] in await explain(mine, spec: spec, hash: hash) }
        }
        store.dispatch(.rankStarted(seq: mine.number))
        let body = RankBody(
            spec: spec, limit: Self.listLength, operations: operations.isEmpty ? nil : operations)
        let answer = await call(mine) { [api] in await api.rank(body) }
        guard !isStale(mine) else {
            await explaining?.value
            return
        }
        guard case .success(let ranked) = answer else {
            if let failure = answer.failure { fail(.rank, failure) }
            await explaining?.value
            return
        }
        heard(ranked.meta)
        store.dispatch(.rankAnswered(ranked.data, sent: operations, by: Served(ranked.meta)))
        await fill(
            mine, spec: ranked.data.spec, hash: ranked.data.specHash, ranked: ranked.data.ranked,
            explaining: explaining)
    }

    private func rerank() async {
        let mine = begin()
        readingRun = nil
        await settle(mine, spec: state.spec, hash: state.specHash, operations: state.pending)
    }

    /// Sends the edits that are waiting, if any are.
    private func sendWhatWaits() async {
        if !state.pending.isEmpty { await rerank() }
    }
}
