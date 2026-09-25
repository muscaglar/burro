import Foundation
import XCTest

@testable import BurroKit

/// One person's whole visit, as a person makes it on a phone: the screen that
/// asks before the first search, a first sentence, a second, a control, a
/// question answered, the notice, a sentence that holds nothing, an area, the
/// shortlist with no connection, a comparison, a link made and opened, a
/// sentence the model did not answer and what the rules offered of it, a vibe
/// added and turned with nothing typed, and a sentence of which Burro applied
/// nothing until one thing was chosen.
///
/// Every other test answers the app from a recording whatever it sends. This
/// one answers a request only if it is, to the letter, a request the service
/// was sent when the visit was recorded (`record_the_visit` in
/// `apps/web/test/record.py`), where each request is made of the answer before
/// it. So it holds the app to what the service takes, and what it shows to
/// what the service said of that very search. It is the website's
/// `test/visit.test.tsx`, walked through the app.
final class VisitTests: XCTestCase {
    private var folder: URL!

    override func setUp() {
        super.setUp()
        folder = FileManager.default.temporaryDirectory
            .appendingPathComponent("burro-visit-\(UUID().uuidString)", isDirectory: true)
    }

    override func tearDown() {
        try? FileManager.default.removeItem(at: folder)
        super.tearDown()
    }

    func test_the_visit_was_recorded_step_by_step_from_the_service() throws {
        let steps = try Visit.steps()

        XCTAssertGreaterThanOrEqual(steps.count, 20)
        XCTAssertEqual(steps.filter { !$0.captured }.map(\.scenario), [])
        XCTAssertEqual(steps.filter { $0.status != 200 }.map(\.scenario), [])
    }

    @MainActor
    func test_everything_a_visit_sends_is_a_request_the_service_answered_and_what_is_shown_is_its_answer()
        async throws
    {
        let visit = try Visit()
        let phone = FilePhoneStorage(folder: folder)
        let app = visit.app(on: phone)

        // First launch. Nothing is chosen, so the screen that asks stands before the
        // tabs, and no sentence leaves the phone, whoever asks for it to be sent.
        XCTAssertNil(app.consent.choice)
        await app.open()
        let search = try XCTUnwrap(app.search)
        let hands = SearchHands(app: app, search: search)
        await hands.submit(try Visit.sentence("first"))
        XCTAssertEqual(visit.sent(to: .interpret), 0)
        XCTAssertTrue(app.synthetic.seen)
        // "Allow and continue".
        app.consent.choose(.allowed)
        XCTAssertEqual(SearchScreen.shown(search.state, consent: app.consent.choice).box, .offered)

        // A first sentence, sent with the defaults the app opened on. Nothing on the
        // search screen needs reading first, so the person is taken to the results.
        let first: RankData = try Visit.answer("first-rank")
        await hands.submit(try Visit.sentence("first"))
        XCTAssertEqual(app.searchPath, [.results])
        var listed = Results.listed(search.state)
        XCTAssertEqual(
            listed.headline, ResultsCopy.Status.ranked(first.scores.count, first: name(first.ranked.first)))
        XCTAssertEqual(listed.cards.count, first.ranked.count)
        XCTAssertEqual(listed.cards.first?.heading.fit, Results.fit(of: first.ranked.first?.score ?? 0))
        let reasons: ExplanationsData = try Visit.answer("first-reasons")
        XCTAssertEqual(reasons.explanations.count, 5)
        for (card, explanation) in zip(listed.cards, reasons.explanations) {
            XCTAssertEqual(card.reasons.value?.map(\.text), explanation.reasons.prefix(3).map(\.text))
        }
        XCTAssertTrue(search.state.reasonsAreIn)

        // A second sentence, typed on the search screen: one thing more, and one taken off.
        app.showRoot(of: .search)
        let second: InterpretData = try Visit.answer("second")
        await hands.submit(try Visit.sentence("second"))
        XCTAssertEqual(second.spec.weights.filter { $0.weight == 0 }.map(\.featureId), [.highstreetAccess])
        let highStreet = try XCTUnwrap(
            Answers.meta.features.first { $0.featureId == .highstreetAccess }?.label)
        var shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        let off = try XCTUnwrap(shown.chips.first { $0.kind == .feature(.highstreetAccess) })
        XCTAssertEqual(off.label, highStreet)
        XCTAssertTrue(off.reads.contains(SearchCopy.Chips.off))
        XCTAssertNil(off.removal)
        let secondRank: RankData = try Visit.answer("second-rank")
        XCTAssertEqual(Results.listed(search.state).cards.first?.heading.name, name(secondRank.ranked.first))

        // A control: the journey made a firm limit. A control never moves the person.
        app.showRoot(of: .search)
        let firm: RankData = try Visit.answer("firm-rank")
        let works = try XCTUnwrap(search.state.spec.commutes.first?.placeId)
        await hands.send(Edits.placeStrictness(works, .hard))
        XCTAssertEqual(app.searchPath, [])
        XCTAssertGreaterThan(firm.filtered.count, 0)
        XCTAssertEqual(Results.listed(search.state).cards.count, firm.ranked.count)
        shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        let journey = try XCTUnwrap(shown.chips.first { $0.kind == .place(works) })
        XCTAssertEqual(journey.label, "Cindermoor Works")
        XCTAssertTrue(journey.reads.contains(SearchCopy.Chips.firm))
        // What was taken off is off, and stays off.
        XCTAssertFalse(SearchChips.counts(search.state.spec.weights.first { $0.featureId == .highstreetAccess }?.weight))
        XCTAssertTrue(shown.parts.contains(.results))

        // A place named in part: a question, and nothing ranked again until it is answered.
        let asked: InterpretData = try Visit.answer("place")
        await hands.submit(try Visit.sentence("place"))
        XCTAssertEqual(app.searchPath, [])
        shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        let question = try XCTUnwrap(shown.questions.first)
        XCTAssertEqual(question.options.map(\.name), asked.clarify.first?.options.map(\.name))
        XCTAssertTrue(shown.parts.contains(.questions))
        XCTAssertEqual(Results.listed(search.state).cards.count, firm.ranked.count)
        let exchange = try XCTUnwrap(question.options.first { $0.name == "Pellam Exchange" })
        await search.flow.answerClarify(question.asked, id: exchange.id, name: exchange.name)
        let answered: RankData = try Visit.answer("answered-rank")
        XCTAssertEqual(answered.spec.commutes.count, 2)
        shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        XCTAssertEqual(shown.questions, [])
        XCTAssertTrue(shown.chips.contains { $0.label == "Pellam Exchange" })
        XCTAssertEqual(Results.listed(search.state).cards.first?.heading.name, name(answered.ranked.first))

        // Part of a sentence is about who lives somewhere: the API's one sentence, and the rest.
        let people: InterpretData = try Visit.answer("people")
        await hands.submit(try Visit.sentence("people"))
        XCTAssertEqual(people.notice, .neutralPlaces)
        shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        XCTAssertEqual(shown.notice, people.noticeText)
        XCTAssertTrue(shown.parts.contains(.notice))
        // The notice is to be read before the results, so the person stays where it is.
        XCTAssertEqual(app.searchPath, [])
        XCTAssertTrue(shown.chips.contains { $0.kind == .feature(.parkProximity) })
        let last: RankData = try Visit.answer("people-rank")
        XCTAssertEqual(Results.listed(search.state).cards.first?.heading.name, name(last.ranked.first))
        XCTAssertEqual(Results.listed(search.state).lines.filter { $0.kind == .notice }.map(\.words), [[people.noticeText]])

        // A sentence with nothing in it to read. The results stay, and the settings open.
        await hands.submit(try Visit.sentence("unread"))
        shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        XCTAssertEqual(shown.nothingRead, SearchCopy.Notice.nothingRead)
        XCTAssertEqual(shown.unmet, [])
        XCTAssertTrue(shown.settingsOpen)
        XCTAssertEqual(Results.listed(search.state).cards.count, last.ranked.count)

        // The results, and the first of them opened. Its page holds what the API said of it.
        hands.showResults()
        listed = Results.listed(search.state)
        let results = Results.Hands(app: app, search: search)
        let one = try XCTUnwrap(listed.cards.first).area
        let two = try XCTUnwrap(listed.cards.dropFirst().first).area
        results.open(one)
        XCTAssertEqual(app.searchPath, [.results, .area(one)])
        let loader = AreaLoader(area: one, app: app)
        await loader.load()
        guard case .page(let page, .api) = loader.shown else { return XCTFail("The area was not read.") }
        XCTAssertEqual(page.name, name(last.ranked.first))
        XCTAssertEqual(page.said, AreaFixtures.page(one.slug).said)
        XCTAssertTrue(page.synthetic)
        let inSearch = try XCTUnwrap(AreaInSearch(search.state, areaId: one.areaId))
        XCTAssertEqual(inSearch.rank, 1)
        XCTAssertEqual(inSearch.fit, listed.cards.first?.heading.fit)

        // It is saved. The phone keeps its names, the date and its facts, and nothing of the search.
        app.saved.toggle(page.area, page: page)
        XCTAssertEqual(app.saved.entries.map(\.id), [one.areaId])
        XCTAssertTrue(app.saved.factsOutliveTheApp)
        for file in KeptFile.allCases {
            let written = String(decoding: phone.read(file) ?? Data(), as: UTF8.self)
            for sentence in try ["first", "second", "place", "people", "unread"].map(Visit.sentence) {
                XCTAssertFalse(written.contains(sentence), file.fileName)
            }
            for place in search.state.spec.commutes.map(\.placeId) + ["Cindermoor Works", "Pellam Exchange"] {
                XCTAssertFalse(written.contains(place), file.fileName)
            }
            XCTAssertFalse(written.contains(search.state.specHash ?? "no hash"), file.fileName)
        }

        // The shortlist with no connection: the app is opened again where nothing can be reached.
        let nowhere = AppModel(
            api: StandIn().unreachable(.getMeta, .notConnectedToInternet)
                .unreachable(.listAreas, .notConnectedToInternet)
                .unreachable(.getArea, .notConnectedToInternet).api(),
            site: SiteAddress(Visit.site), synthetic: SyntheticNotice(), storage: FilePhoneStorage(folder: folder))
        await nowhere.open()
        XCTAssertEqual(nowhere.opening, .failed(.because(.offline)))
        XCTAssertEqual(nowhere.consent.choice, .allowed)
        XCTAssertTrue(nowhere.synthetic.seen)
        let kept = try XCTUnwrap(nowhere.saved.entries.first)
        XCTAssertEqual(ShortlistShown(kept, older: false).name, page.name)
        XCTAssertFalse(ShortlistShown(kept, older: false).noFigures)
        let offline = AreaLoader(area: kept.area, app: nowhere)
        await offline.load()
        guard case .page(let saved, .kept(_, let because)) = offline.shown else {
            return XCTFail("The saved area could not be read with no connection.")
        }
        XCTAssertTrue(because.isOffline)
        XCTAssertEqual(saved.said, page.said)
        XCTAssertNil(nowhere.search)

        // The second result is chosen to compare, and then the first. The comparison is a
        // screen of its own, on the search as it stands.
        app.showRoot(of: .search)
        hands.showResults()
        results.toggleCompare(two)
        results.toggleCompare(one)
        XCTAssertEqual(Results.tray(app.results.compare).go, ResultsCopy.Tray.go(2))
        results.compare()
        XCTAssertEqual(app.searchPath, [.results, .compare])
        let compared: CompareData = try Visit.answer("compare")
        let comparison = Results.Comparison()
        await comparison.ask(app.results.compared(among: search.state.areas), of: search)
        guard case .here(let table) = comparison.answer else { return XCTFail("No comparison came.") }
        XCTAssertEqual(table.basis, ResultsCopy.Compare.fromSearch)
        XCTAssertEqual(table.rows.count, compared.rows.count)
        XCTAssertEqual(table.places.map(\.name), [two.name, one.name])
        // What was taken off counts for nothing, so it is no row of the comparison.
        XCTAssertFalse(table.rows.map(\.label).contains(highStreet))
        XCTAssertEqual(
            table.places.last?.standing,
            ResultsCopy.CompareTable.standing(rank: 1, fit: Results.fit(of: last.ranked.first?.score ?? 0)))

        // Back to the results, which are as they were, and a link made of the search.
        results.chooseOthers()
        XCTAssertEqual(app.searchPath, [.results])
        XCTAssertEqual(Results.listed(search.state).cards.count, last.ranked.count)
        let made: ShareCreated = try Visit.answer("share-made")
        XCTAssertTrue(results.canShare)
        results.openShare()
        await results.makeLink()
        guard case .made(let link) = app.results.sharing.shown(for: search.state) else {
            return XCTFail("No link was made.")
        }
        XCTAssertEqual(link.url.absoluteString, "\(Visit.site)/s#\(made.shareId)")
        for sentence in try ["first", "second", "place", "people", "unread"].map(Visit.sentence) {
            XCTAssertFalse(link.url.absoluteString.contains(sentence))
        }

        // The link opened, as the phone hands it to the app. The search that was open gives way to it.
        let opener = LinkOpener()
        await opener.open(link.url, in: app)
        XCTAssertEqual(opener.presented, .share(id: made.shareId))
        let sharedSearch = try XCTUnwrap(SharedSearch(shareId: made.shareId, app: app))
        await sharedSearch.open()
        let opened: ShareData = try Visit.answer("share-opened")
        guard case .open(let said) = sharedSearch.stage else { return XCTFail("The link did not open.") }
        XCTAssertEqual(said.ranked, opened.scores.count)
        XCTAssertEqual(said.first, name(opened.ranked.first))
        opener.showResults(in: app)
        XCTAssertNil(opener.presented)
        XCTAssertEqual(app.searchPath, [.results])
        listed = Results.listed(search.state)
        XCTAssertEqual(listed.cards.count, opened.ranked.count)
        XCTAssertEqual(listed.cards.first?.heading.name, name(opened.ranked.first))
        XCTAssertEqual(listed.lines.first?.words.first, ResultsCopy.Notice.shared)
        XCTAssertTrue(search.state.reasonsAreIn)
        shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        XCTAssertTrue(shown.chips.first { $0.kind == .feature(.highstreetAccess) }?.reads.contains(SearchCopy.Chips.off) ?? false)
        // No route the app went by holds the id of the share.
        XCTAssertFalse(String(describing: app.searchPath).contains(made.shareId))

        // Another day: the app is opened again. The choice is remembered, and no search is.
        // A model reads, and does not answer. What the rules offer is on the screen at once,
        // and stays when the model's answer does not come.
        let later = visit.app(on: FilePhoneStorage(folder: folder))
        await later.open()
        XCTAssertEqual(later.consent.choice, .allowed)
        XCTAssertEqual(later.saved.entries.map(\.id), [one.areaId])
        let again = try XCTUnwrap(later.search)
        XCTAssertEqual(again.state.phase, .empty)
        XCTAssertEqual(again.state.spec, Answers.meta.defaults.rent)
        let atOnce: InterpretData = try Visit.answer("slow-at-once")
        let slow: InterpretData = try Visit.answer("slow")
        let slowly = SearchHands(app: later, search: again)
        let readSoFar = visit.sent(to: .interpret)
        let rankedBefore = visit.sent(to: .rank)
        await slowly.submit(try Visit.sentence("slow"))
        // The rules were asked first, and then the model, of the same words.
        XCTAssertEqual(visit.sent(to: .interpret), readSoFar + 2)
        XCTAssertTrue(atOnce.modelPending)
        XCTAssertFalse(atOnce.degraded)
        XCTAssertTrue(slow.degraded)
        XCTAssertEqual(slow.interpreter, .rule)
        XCTAssertEqual(slow.applied, [])
        shown = SearchScreen.shown(again.state, consent: later.consent.choice)
        XCTAssertEqual(shown.couldNotReadRetry, false)
        XCTAssertTrue(shown.parts.contains(.couldNotRead))
        XCTAssertEqual(shown.readBy, SearchCopy.readBy(.rule))
        // Nothing of it is applied, and nothing is ranked, until the person chooses. There is
        // something to choose from, so the settings stay shut.
        XCTAssertEqual(shown.offers?.offers.map(\.name), slow.suggestions.map(\.label))
        XCTAssertFalse(shown.settingsOpen)
        XCTAssertEqual(again.state.spec, Answers.meta.defaults.rent)
        XCTAssertEqual(visit.sent(to: .rank), rankedBefore)
        // "Add": the edits the API gave with the choice, sent as a control sends them.
        let slowRank: RankData = try Visit.answer("slow-rank")
        await slowly.choose(0, "more")
        XCTAssertEqual(visit.sent(to: .rank), rankedBefore + 1)
        XCTAssertEqual(again.state.spec, slowRank.spec)
        XCTAssertEqual(Results.listed(again.state).cards.first?.heading.name, name(slowRank.ranked.first))

        // Another day again, begun at the settings: a vibe is added, with nothing typed.
        let third = visit.app(on: FilePhoneStorage(folder: folder))
        await third.open()
        let settled = try XCTUnwrap(third.search)
        let settings = SearchHands(app: third, search: settled)
        let lively: RankData = try Visit.answer("shelf-rank")
        await settings.send(SettingsForm.tag(.pace, on: true))
        XCTAssertEqual(settled.state.spec, lively.spec)
        // A control never moves the person.
        XCTAssertEqual(third.searchPath, [])
        shown = SearchScreen.shown(settled.state, consent: third.consent.choice)
        XCTAssertTrue(shown.chips.map(\.reads).contains("Going out: towards Buzzy"))
        XCTAssertEqual(Results.listed(settled.state).cards.first?.heading.name, name(lively.ranked.first))

        // The scale is turned to its other end, with the weight it had.
        let pace = try XCTUnwrap(settled.state.spec.tags.first { $0.tagId == .pace })
        let calm: RankData = try Visit.answer("turned-rank")
        await settings.send(SettingsForm.turn(.pace, to: .low, from: pace))
        XCTAssertEqual(settled.state.spec, calm.spec)
        shown = SearchScreen.shown(settled.state, consent: third.consent.choice)
        XCTAssertTrue(shown.chips.map(\.reads).contains("Going out: towards Calm"))
        listed = Results.listed(settled.state)
        XCTAssertEqual(listed.cards.first?.heading.name, name(calm.ranked.first))
        // The strip of each result says which end was asked for, and where the area sits on it.
        XCTAssertEqual(listed.cards.first?.strip.first?.asked, "asked for: Calm")
        XCTAssertEqual(listed.cards.first?.strip.first?.placed?.band, calm.ranked.first?.strip.first?.band)

        // A sentence that is not plain. Nothing of it is applied, and nothing is ranked,
        // until the person chooses.
        let noticed: InterpretData = try Visit.answer("noticed")
        let rankedSoFar = visit.sent(to: .rank)
        await settings.submit(try Visit.sentence("noticed"))
        XCTAssertEqual(noticed.applied, [])
        XCTAssertEqual(visit.sent(to: .rank), rankedSoFar)
        XCTAssertEqual(settled.state.spec, calm.spec)
        XCTAssertEqual(third.searchPath, [])
        shown = SearchScreen.shown(settled.state, consent: third.consent.choice)
        XCTAssertEqual(shown.offers?.offers.map(\.name), noticed.suggestions.map(\.label))
        XCTAssertEqual(shown.unread, noticed.unread)
        XCTAssertTrue(shown.parts.contains(.offers))
        XCTAssertEqual(Results.listed(settled.state).cards.first?.heading.name, name(calm.ranked.first))

        // "Fewer pubs and bars": the edits the API gave with the choice, sent as a control sends them.
        let chosen: RankData = try Visit.answer("chosen-rank")
        await settings.choose(0, "less")
        XCTAssertEqual(visit.sent(to: .rank), rankedSoFar + 1)
        XCTAssertEqual(settled.state.spec, chosen.spec)
        shown = SearchScreen.shown(settled.state, consent: third.consent.choice)
        XCTAssertEqual(shown.offers?.offers.map(\.name), noticed.suggestions.dropFirst().map(\.label))
        XCTAssertTrue(shown.chips.contains { $0.kind == .feature(.venueEveningPerHomes) })
        XCTAssertEqual(Results.listed(settled.state).cards.first?.heading.name, name(chosen.ranked.first))
        XCTAssertTrue(settled.state.reasonsAreIn)
        let typed = try Visit.sentence("noticed")
        for file in KeptFile.allCases {
            let written = String(decoding: phone.read(file) ?? Data(), as: UTF8.self)
            XCTAssertFalse(written.contains(typed), file.fileName)
        }

        // Nothing was sent that the service was not sent when the visit was recorded,
        // and nothing was recorded that the app does not send.
        XCTAssertEqual(visit.unanswered, [])
        XCTAssertEqual(visit.unused, [])
    }

    @MainActor
    func test_the_same_visit_can_be_made_with_the_settings_alone_and_no_sentence_is_ever_sent() async throws {
        let api = StandIn.firstSearch().on(.rank, StandIn.withTheSpecSent("rank-first"))
        let app = AreaFixtures.app(api)
        await app.open()
        let search = try XCTUnwrap(app.search)
        let hands = SearchHands(app: app, search: search)

        // "Use the settings instead". The box gives way to a line, and the settings open by themselves.
        app.consent.choose(.settingsOnly)
        var shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        XCTAssertEqual(shown.box, .declined)
        XCTAssertFalse(shown.parts.contains(.examples))
        XCTAssertTrue(SearchScreen.opensTheForm(search.state, consent: app.consent.choice))
        search.flow.openSettings(true)
        XCTAssertTrue(shown.canRank)

        // Renting or buying swaps the default, and sends nothing.
        await hands.chooseTenure(.buy)
        XCTAssertEqual(search.state.spec, Answers.meta.defaults.buy)
        await hands.chooseTenure(.rent)
        XCTAssertEqual(api.calls(to: .rank).count, 0)

        // A control is an edit, sent with the spec the API served.
        await hands.send(Edits.tagOn(.leafy))
        XCTAssertEqual(
            try api.lastCall(to: .rank).body(as: RankBody.self),
            RankBody(spec: Answers.meta.defaults.rent, limit: 20, operations: Edits.tagOn(.leafy)))
        XCTAssertEqual(search.state.phase, .results)
        // A control never moves the person. The way to the results is a button.
        XCTAssertEqual(app.searchPath, [])
        shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        XCTAssertTrue(shown.parts.contains(.results))
        hands.showResults()
        XCTAssertEqual(app.searchPath, [.results])
        XCTAssertEqual(Results.listed(search.state).cards.count, Answers.ranked("rank-first").ranked.count)

        // Whatever is pressed, a sentence is never sent.
        await hands.submit("leafy and quiet")
        await hands.tryAgain("leafy and quiet")
        XCTAssertEqual(api.calls(to: .interpret).count, 0)
        XCTAssertEqual(api.unexpected.count, 0)
    }

    @MainActor
    func test_a_search_made_with_no_connection_waits_and_is_sent_when_the_person_comes_back() async throws {
        let api = StandIn.firstSearch().unreachable(.interpret, .notConnectedToInternet)
        let app = AreaFixtures.app(api)
        app.consent.choose(.allowed)
        await app.open()
        let search = try XCTUnwrap(app.search)
        let hands = SearchHands(app: app, search: search)

        // The sentence cannot leave. The screen says so, and the person stays where the box is.
        await hands.submit("leafy and quiet")
        var shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        XCTAssertEqual(shown.offlineWaiting, false)
        XCTAssertTrue(shown.parts.contains(.offline))
        XCTAssertNil(shown.failure)
        XCTAssertEqual(app.searchPath, [])

        // Coming back sends the sentence that is still in the box, once.
        api.on(.interpret, "interpret-first")
        await hands.comeBack("leafy and quiet")
        XCTAssertEqual(api.calls(to: .interpret).count, 2)
        XCTAssertEqual(app.searchPath, [.results])
        XCTAssertTrue(search.state.online)

        // A control moved with no connection waits, the results stay, and it is sent once when the phone is back.
        app.showRoot(of: .search)
        api.unreachable(.rank, .notConnectedToInternet)
        await hands.send(Edits.tagOn(.villageFeel))
        shown = SearchScreen.shown(search.state, consent: app.consent.choice)
        XCTAssertEqual(shown.offlineWaiting, true)
        XCTAssertEqual(Results.listed(search.state).cards.count, Answers.ranked("rank-first").ranked.count)
        XCTAssertEqual(Results.listed(search.state).lines.map(\.kind), [.offline])
        let asked = api.calls(to: .rank).count
        api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        await hands.comeBack("")
        XCTAssertEqual(api.calls(to: .rank).count, asked + 1)
        XCTAssertEqual(search.state.pending, .none)
        XCTAssertEqual(SearchScreen.shown(search.state, consent: app.consent.choice).offlineWaiting, nil)
        // A control never moves the person.
        XCTAssertEqual(app.searchPath, [])
    }

    private func name(_ ranked: RankedArea?) -> String {
        Answers.areas.first { $0.areaId == ranked?.areaId }?.name ?? "no such area"
    }
}

/// A stand-in for the API that answers one person's whole visit, and nothing else.
///
/// It answers a request only if it is one of the steps, to the letter: the
/// same route and the same body. Anything else is kept as unanswered, and the
/// test that uses it expects none. What is a function of the release alone is
/// answered from the recordings every test uses: the form, the areas, an
/// area's profile and the boundaries.
final class Visit: Transport, @unchecked Sendable {
    static let site = "https://burro.example.test"

    private let recorded: [Recorded]
    private let lock = NSLock()
    private var used: Set<String> = []
    private var strays: [String] = []
    private var routes: [APIRoute] = []

    init() throws {
        recorded = try Self.steps()
    }

    /// The steps of the visit, in the order they were recorded.
    static func steps() throws -> [Recorded] {
        try Recorded.scenarios.filter { $0.hasPrefix("visit/") }.sorted().map(Recorded.read)
    }

    /// One step by its name, which is its file's name with no number: `first-rank`.
    static func step(_ name: String) throws -> Recorded {
        let found = try steps().first { step in
            step.scenario.replacingOccurrences(
                of: #"^visit/\d+-"#, with: "", options: .regularExpression) == name
        }
        return try XCTUnwrap(found, "The visit has no step named \(name).")
    }

    static func answer<Payload: Decodable & Sendable>(_ name: String) throws -> Payload {
        try JSONDecoder().decode(Envelope<Payload>.self, from: step(name).body).data
    }

    /// The sentence a step sent.
    static func sentence(_ name: String) throws -> String {
        try JSONDecoder().decode(InterpretBody.self, from: XCTUnwrap(step(name).sent)).text
    }

    /// The app, as the shell makes it, with this where the network would be.
    @MainActor
    func app(on phone: any PhoneStorage) -> AppModel {
        let notice = SyntheticNotice()
        let client = LiveBurroAPI(
            configuration: APIConfiguration(StandIn.base), transport: self,
            onSynthetic: { said in await notice.note(said) })
        return AppModel(api: client, site: SiteAddress(Self.site), synthetic: notice, storage: phone)
    }

    /// The route of each request that was no step of the visit. Never what was sent.
    var unanswered: [String] { lock.withLock { strays } }

    /// The steps no request has asked for yet.
    var unused: [String] {
        lock.withLock { recorded.map(\.scenario).filter { !used.contains($0) } }
    }

    func sent(to route: APIRoute) -> Int {
        lock.withLock { routes.filter { $0 == route }.count }
    }

    func send(_ request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        guard let url = request.url else { throw URLError(.badURL) }
        let method = request.httpMethod ?? "GET"
        let body = try request.httpBody.map(JSON.read)
        let answer: Recorded? = try lock.withLock {
            if let route = APIRoute.allCases.first(where: { $0.method.rawValue == method && $0.template == url.path }) {
                routes.append(route)
            }
            // Two steps may be one request: the reasons of a search, asked for again when its
            // link is opened. The service answers both alike, so either answer will do for both.
            let same = try recorded.filter { step in
                try step.method == method && step.path == url.path && step.sent.map(JSON.read) == body
            }
            if let step = same.first {
                same.forEach { used.insert($0.scenario) }
                return step
            }
            guard method == "GET" else { return nil }
            switch url.path {
            case "/v1/meta": return try Recorded.read("meta")
            case "/v1/areas": return try Recorded.read("areas")
            case "/v1/areas/geometry": return try Recorded.read("geometry")
            default:
                let parts = url.path.split(separator: "/")
                guard parts.count == 3, parts[0] == "v1", parts[1] == "areas" else { return nil }
                return try Recorded.read("area/\(parts[2])")
            }
        }
        guard let answer else {
            let route = url.path.replacingOccurrences(
                of: #"^(/v1/shares)/.+$"#, with: "$1/{share_id}", options: .regularExpression)
            lock.withLock { strays.append("\(method) \(route)") }
            throw URLError(.unsupportedURL)
        }
        try Task.checkCancellation()
        guard
            let response = HTTPURLResponse(
                url: url, statusCode: answer.status, httpVersion: "HTTP/1.1", headerFields: answer.headers)
        else { throw URLError(.badServerResponse) }
        return (answer.body, response)
    }
}
