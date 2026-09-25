import XCTest

@testable import BurroKit

/// Reading one area for its screen: what is asked for, and what the screen
/// shows when the API answers, when it refuses, and when it cannot be reached.
final class AreaLoaderTests: XCTestCase {
    @MainActor
    func test_an_area_is_read_by_its_slug_and_nothing_of_a_search_is_sent() async throws {
        let api = StandIn.firstSearch()
        let app = AreaFixtures.app(api)
        let loader = AreaLoader(area: AreaFixtures.farrowmere, app: app)
        XCTAssertEqual(loader.shown, .reading)

        await loader.load()

        XCTAssertEqual(loader.shown, .page(AreaFixtures.page("farrowmere"), .api))
        let call = try api.lastCall(to: .getArea)
        XCTAssertEqual(call.path, "/v1/areas/farrowmere")
        XCTAssertEqual(call.method, "GET")
        XCTAssertNil(call.sent)
        XCTAssertNil(call.url.query)
        XCTAssertNil(call.url.fragment)
        XCTAssertEqual(Set(api.routes), [.getMeta, .listAreas, .getArea])
        XCTAssertEqual(api.unexpected.count, 0)
    }

    @MainActor
    func test_an_area_the_search_has_read_already_is_not_asked_for_again() async {
        let api = StandIn.firstSearch()
        let app = AreaFixtures.app(api)
        app.consent.choose(.allowed)
        await app.open()
        await app.search?.flow.submitText("leafy and quiet")
        let asked = api.calls(to: .getArea).count

        let loader = AreaLoader(area: AreaFixtures.farrowmere, app: app)
        await loader.load()

        XCTAssertEqual(api.calls(to: .getArea).count, asked)
        XCTAssertEqual(loader.shown, .page(AreaFixtures.page("farrowmere"), .api))
    }

    @MainActor
    func test_reading_twice_asks_once() async {
        let api = StandIn.firstSearch()
        let loader = AreaLoader(area: AreaFixtures.farrowmere, app: AreaFixtures.app(api))

        await loader.load()
        await loader.load()

        XCTAssertEqual(api.calls(to: .getArea).count, 1)
    }

    @MainActor
    func test_an_area_the_data_does_not_have_is_said_in_the_apis_words() async {
        let api = StandIn.firstSearch().on(.getArea, "area-not-found")
        let app = AreaFixtures.app(api)
        let gone = AreaRef(areaId: "syn-n9999", slug: "nowhere-at-all", name: "Nowhere", borough: "None")

        let loader = AreaLoader(area: gone, app: app)
        await loader.load()

        guard case .failed(let failure) = loader.shown else { return XCTFail("The page was shown.") }
        XCTAssertEqual(failure.code, .areaNotFound)
        XCTAssertEqual(ShellCopy.words(for: failure), "There is no such area in this release.")
        XCTAssertNotNil(failure.requestId)
    }

    @MainActor
    func test_an_area_that_cannot_be_reached_and_is_not_saved_says_why_and_can_be_tried_again() async {
        let api = StandIn.firstSearch().unreachable(.getArea, .notConnectedToInternet)
        let loader = AreaLoader(area: AreaFixtures.farrowmere, app: AreaFixtures.app(api))

        await loader.load()
        XCTAssertEqual(loader.shown, .failed(.because(.offline)))
        api.on(.getArea, "area/farrowmere")
        await loader.retry()

        XCTAssertEqual(loader.shown, .page(AreaFixtures.page("farrowmere"), .api))
    }

    @MainActor
    func test_a_saved_area_is_read_from_the_phone_when_there_is_no_connection() async throws {
        let day = Date(timeIntervalSince1970: 1_790_000_000)
        let names = MemoryPhoneStorage()
        Shortlist(storage: names, now: { day }).add(AreaFixtures.farrowmere, synthetic: true)
        let kept = KeptArea(AreaFixtures.page("farrowmere"), savedOn: day)
        let facts = MemorySavedAreasStorage(KeptShortlist(order: ["syn-n0006"], areas: [kept]))
        let api = StandIn()
            .unreachable(.getMeta, .notConnectedToInternet)
            .unreachable(.listAreas, .notConnectedToInternet)
            .unreachable(.getArea, .notConnectedToInternet)
        let app = AreaFixtures.app(api, storage: names)
        let saved = SavedAreas(app: app, storage: facts)

        let loader = AreaLoader(area: AreaFixtures.farrowmere, app: app, saved: saved)
        await loader.load()

        guard case .page(let page, let origin) = loader.shown else { return XCTFail("Nothing was shown.") }
        XCTAssertEqual(origin, .kept(savedOn: day, because: .because(.offline)))
        XCTAssertEqual(page.said, AreaFixtures.page("farrowmere").said)
        XCTAssertEqual(page.releaseId, Answers.meta.releaseId)
        XCTAssertTrue(app.synthetic.seen)
        XCTAssertNil(app.search)
        XCTAssertEqual(
            AreaCopy.asSaved(on: ShortlistCopy.date(day, in: .gmt), release: page.releaseId),
            "This is the data as it was when you saved this area, on 21 September 2026, "
                + "from data release \(Answers.meta.releaseId).")
    }

    @MainActor
    func test_a_saved_area_with_no_copy_of_its_facts_is_given_one_when_it_is_read() async {
        let app = AreaFixtures.app()
        let saved = SavedAreas(app: app, storage: MemorySavedAreasStorage())
        app.toggleShortlist(AreaFixtures.farrowmere)
        XCTAssertNil(saved.kept["syn-n0006"])

        await AreaLoader(area: AreaFixtures.farrowmere, app: app, saved: saved).load()

        XCTAssertEqual(saved.kept["syn-n0006"]?.page.said, AreaFixtures.page("farrowmere").said)
    }

    @MainActor
    func test_an_area_that_is_not_saved_is_not_kept_by_being_read() async {
        let app = AreaFixtures.app()
        let saved = SavedAreas(app: app, storage: MemorySavedAreasStorage())

        await AreaLoader(area: AreaFixtures.farrowmere, app: app, saved: saved).load()

        XCTAssertEqual(saved.kept, [:])
        XCTAssertEqual(app.shortlist.entries, [])
    }

    @MainActor
    func test_a_copy_from_an_older_release_is_left_as_it_was_saved_until_the_person_asks_for_the_newer() async {
        let day = Date(timeIntervalSince1970: 1_790_000_000)
        let older = Meta(
            releaseId: "syn-2026-08-01-01", engineVersion: "1.3.0", synthetic: true, preview: false)
        let names = MemoryPhoneStorage()
        Shortlist(storage: names, now: { day }).add(AreaFixtures.farrowmere, synthetic: true)
        let kept = KeptArea(AreaFixtures.page("farrowmere", release: older), savedOn: day)
        let app = AreaFixtures.app(storage: names)
        let saved = SavedAreas(
            app: app, storage: MemorySavedAreasStorage(KeptShortlist(order: ["syn-n0006"], areas: [kept])))
        let loader = AreaLoader(area: AreaFixtures.farrowmere, app: app, saved: saved)

        await loader.load()
        XCTAssertEqual(loader.shown, .page(AreaFixtures.page("farrowmere"), .api))
        XCTAssertTrue(loader.keptIsOlder)
        XCTAssertEqual(saved.kept["syn-n0006"]?.releaseId, "syn-2026-08-01-01")
        loader.keepWhatIsShown()

        XCTAssertFalse(loader.keptIsOlder)
        XCTAssertEqual(saved.kept["syn-n0006"]?.releaseId, Answers.meta.releaseId)
        XCTAssertEqual(saved.kept["syn-n0006"]?.savedOn, day)
    }

    @MainActor
    func test_the_area_is_laid_out_under_the_releases_headings_once_the_release_has_been_read() async {
        let api = StandIn.firstSearch().unreachable(.getMeta, .timedOut)
        let app = AreaFixtures.app(api)
        let loader = AreaLoader(area: AreaFixtures.farrowmere, app: app)

        await loader.load()
        guard case .page(let bare, .api) = loader.shown else { return XCTFail("Nothing was shown.") }
        XCTAssertEqual(bare.measured.map(\.dimension), [nil])
        api.on(.getMeta, "meta")
        await loader.load()

        XCTAssertEqual(loader.shown, .page(AreaFixtures.page("farrowmere"), .api))
        XCTAssertEqual(api.calls(to: .getArea).count, 1)
    }
}
