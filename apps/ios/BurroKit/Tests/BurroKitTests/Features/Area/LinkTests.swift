import XCTest

@testable import BurroKit

/// Opening a link: what is read from an address, where the app goes, and
/// that a link holds an id or a slug and nothing else.
final class LinkTests: XCTestCase {
    private let site = SiteAddress("https://burro.example.test")
    private let shareId = "rPnAeuBsXQci-xINLK_f2w"
    // A string found nowhere else, planted where a link could carry it.
    private let canary = "zqxcanary7431"

    private func read(_ address: String) -> IncomingLink? {
        URL(string: address).flatMap { IncomingLink.read($0, site: site) }
    }

    // MARK: - Reading an address

    func test_a_link_to_a_shared_search_holds_its_id_after_the_hash() {
        XCTAssertEqual(read("https://burro.example.test/s#\(shareId)"), .share(id: shareId))
        XCTAssertEqual(read("https://burro.example.test/s/#\(shareId)"), .share(id: shareId))
        XCTAssertEqual(read("https://BURRO.example.test/s#\(shareId)"), .share(id: shareId))
        XCTAssertEqual(read("https://burro.example.test:443/s#\(shareId)"), .share(id: shareId))
        XCTAssertEqual(try? XCTUnwrap(site.share(shareId)).absoluteString, "https://burro.example.test/s#\(shareId)")
        XCTAssertEqual(site.share(shareId).flatMap { IncomingLink.read($0, site: site) }, .share(id: shareId))
    }

    func test_a_link_to_an_area_holds_its_city_and_its_slug() {
        XCTAssertEqual(
            read("https://burro.example.test/synthetic/farrowmere"), .area(city: "synthetic", slug: "farrowmere"))
        XCTAssertEqual(
            read("https://burro.example.test/london/dulcimer-green/"),
            .area(city: "london", slug: "dulcimer-green"))
        let made = site.area(
            AreaRef(areaId: "syn-n0006", slug: "farrowmere", name: "Farrowmere", borough: "Quillhaven"))
        XCTAssertEqual(
            made.flatMap { IncomingLink.read($0, site: site) }, .area(city: "synthetic", slug: "farrowmere"))
    }

    func test_what_follows_the_hash_is_read_only_if_it_is_an_id() {
        XCTAssertEqual(read("https://burro.example.test/s"), .noShare)
        XCTAssertEqual(read("https://burro.example.test/s#"), .noShare)
        for notAnId in [
            "short", shareId + "x", String(shareId.dropLast()), "TbfsnjL3GyTlKt967hH2H!", canary,
            "leafy%20and%20quiet", "TbfsnjL3GyTlKt967hH2H%51",
        ] {
            XCTAssertEqual(read("https://burro.example.test/s#\(notAnId)"), .notAShare, notAnId)
        }
    }

    func test_an_address_that_is_not_the_websites_is_not_a_link() {
        for address in [
            "http://burro.example.test/s#\(shareId)",
            "https://example.test/s#\(shareId)",
            "https://burro.example.test.evil.test/s#\(shareId)",
            "https://evil.test/burro.example.test/s#\(shareId)",
            "https://burro.example.test:8443/s#\(shareId)",
            "burro://s#\(shareId)",
            "burro:\(shareId)",
            "file:///s#\(shareId)",
        ] {
            XCTAssertNil(read(address), address)
        }
    }

    func test_an_address_that_names_a_person_is_not_a_link() throws {
        var named = try XCTUnwrap(URLComponents(string: "https://burro.example.test/s"))
        named.fragment = shareId
        XCTAssertEqual(named.url.flatMap { IncomingLink.read($0, site: site) }, .share(id: shareId))

        named.user = "someone"
        XCTAssertNil(named.url.flatMap { IncomingLink.read($0, site: site) })
        named.password = canary
        XCTAssertNil(named.url.flatMap { IncomingLink.read($0, site: site) })
        XCTAssertNotNil(named.url)
    }

    func test_an_address_that_leads_to_nothing_the_app_shows_is_not_a_link() {
        for address in [
            "https://burro.example.test/",
            "https://burro.example.test/methods",
            "https://burro.example.test/compare?a=farrowmere&a=alderwick",
            "https://burro.example.test/synthetic",
            "https://burro.example.test/synthetic/farrowmere/more",
            "https://burro.example.test/paris/farrowmere",
            "https://burro.example.test/synthetic/Farrowmere",
            "https://burro.example.test/synthetic/far%20row",
            "https://burro.example.test/synthetic/-farrowmere",
            "https://burro.example.test/s/\(shareId)",
            "https://burro.example.test/shares/\(shareId)",
        ] {
            XCTAssertNil(read(address), address)
        }
    }

    func test_with_no_address_set_for_the_website_no_link_is_one_of_its_own() throws {
        let url = try XCTUnwrap(URL(string: "https://burro.example.test/s#\(shareId)"))

        XCTAssertNil(IncomingLink.read(url, site: .none))
    }

    func test_a_link_has_no_room_for_anything_but_an_id_or_a_slug() {
        // Whatever else an address holds is dropped where it is read.
        let shared = read("https://burro.example.test/s?from=\(canary)#\(shareId)")
        let area = read("https://burro.example.test/synthetic/farrowmere?q=\(canary)#\(canary)")

        XCTAssertEqual(shared, .share(id: shareId))
        XCTAssertEqual(area, .area(city: "synthetic", slug: "farrowmere"))
        XCTAssertFalse(String(reflecting: shared).contains(canary))
        XCTAssertFalse(String(reflecting: area).contains(canary))
    }

    // MARK: - Going where a link leads

    @MainActor
    func test_a_link_to_an_area_opens_the_areas_screen() async throws {
        let api = StandIn.firstSearch()
        let app = AreaFixtures.app(api)
        let opener = LinkOpener()

        await opener.open(try XCTUnwrap(URL(string: "https://burro.example.test/synthetic/farrowmere")), in: app)

        XCTAssertEqual(app.tab, .search)
        XCTAssertEqual(app.searchPath, [.area(AreaFixtures.farrowmere)])
        XCTAssertNil(opener.presented)
        // The area is found in what the API listed. Nothing is asked for by what the link held.
        XCTAssertEqual(Set(api.routes), [.getMeta, .listAreas])
    }

    @MainActor
    func test_a_link_to_an_area_the_data_does_not_have_says_so_in_fixed_words() async throws {
        let api = StandIn.firstSearch()
        let app = AreaFixtures.app(api)
        let opener = LinkOpener()

        await opener.open(try XCTUnwrap(URL(string: "https://burro.example.test/synthetic/\(canary)")), in: app)

        XCTAssertEqual(opener.presented, .nowhere(.noArea))
        XCTAssertEqual(app.searchPath, [])
        XCTAssertFalse(api.calls.contains { $0.outsideTheBody.contains(canary) })
        for nowhere in LinkOpener.Nowhere.allCases {
            XCTAssertFalse(nowhere.title.contains(canary))
            XCTAssertFalse(nowhere.text.isEmpty)
        }
    }

    @MainActor
    func test_an_area_under_a_city_that_is_not_its_own_is_not_found() async throws {
        let app = AreaFixtures.app()
        let opener = LinkOpener()

        await opener.open(try XCTUnwrap(URL(string: "https://burro.example.test/london/farrowmere")), in: app)

        XCTAssertEqual(opener.presented, .nowhere(.noArea))
        XCTAssertEqual(app.searchPath, [])
    }

    @MainActor
    func test_a_link_to_a_saved_area_opens_with_no_connection() async throws {
        let names = MemoryPhoneStorage()
        Shortlist(storage: names).add(AreaFixtures.farrowmere, synthetic: true)
        let api = StandIn().unreachable(.getMeta, .notConnectedToInternet)
        let app = AreaFixtures.app(api, storage: names)
        let opener = LinkOpener()

        await opener.open(try XCTUnwrap(URL(string: "https://burro.example.test/synthetic/farrowmere")), in: app)

        XCTAssertEqual(app.tab, .shortlist)
        XCTAssertEqual(app.shortlistPath, [.area(AreaFixtures.farrowmere)])
    }

    @MainActor
    func test_a_link_that_arrives_while_the_app_is_opening_waits_for_the_release() async throws {
        let api = StandIn.firstSearch()
        let release = api.hold(.getMeta, "meta")
        let app = AreaFixtures.app(api)
        let opener = LinkOpener()
        let url = try XCTUnwrap(URL(string: "https://burro.example.test/synthetic/farrowmere"))

        async let opening: Void = app.open()
        await until { release.waiting == 1 }
        async let followed: Void = opener.open(url, in: app)
        try await Task.sleep(nanoseconds: 120_000_000)
        // The release is not in. The link is not said to lead nowhere.
        XCTAssertNil(opener.presented)
        XCTAssertEqual(app.searchPath, [])
        release.release()
        await opening
        await followed

        XCTAssertEqual(app.searchPath, [.area(AreaFixtures.farrowmere)])
        XCTAssertNil(opener.presented)
        XCTAssertEqual(api.calls(to: .getMeta).count, 1)
    }

    @MainActor
    func test_a_link_to_a_shared_search_puts_up_the_screen_that_opens_it() async throws {
        let api = StandIn.firstSearch().on(.getShare, "share-opened")
        let app = AreaFixtures.app(api)
        let opener = LinkOpener()

        await opener.open(try XCTUnwrap(URL(string: "https://burro.example.test/s#\(shareId)")), in: app)

        XCTAssertEqual(opener.presented, .share(id: shareId))
        // The id is in no route: a route may be held for as long as the app is open.
        XCTAssertEqual(app.searchPath, [])
        XCTAssertFalse(opener.presented?.id.contains(shareId) ?? true)
        XCTAssertEqual(api.calls.count, 0)
        opener.showResults(in: app)
        XCTAssertNil(opener.presented)
        XCTAssertEqual(app.tab, .search)
        XCTAssertEqual(app.searchPath, [.results])
    }

    @MainActor
    func test_what_is_not_an_id_is_never_sent_anywhere_and_never_shown() async throws {
        let api = StandIn.firstSearch().on(.getShare, "share-opened")
        let app = AreaFixtures.app(api)
        let opener = LinkOpener()

        await opener.open(try XCTUnwrap(URL(string: "https://burro.example.test/s#\(canary)")), in: app)

        XCTAssertEqual(opener.presented, .nowhere(.notAShare))
        XCTAssertEqual(api.calls.count, 0)
        XCTAssertNil(SharedSearch(shareId: canary, app: app))
        XCTAssertNil(SharedSearch(shareId: "", app: app))
        XCTAssertFalse(String(reflecting: opener.presented).contains(canary))
        XCTAssertEqual(opener.presented.map { $0.id }, "notAShare")
    }

    @MainActor
    func test_an_address_that_is_not_the_websites_does_nothing() async throws {
        let api = StandIn.firstSearch()
        let app = AreaFixtures.app(api)
        let opener = LinkOpener()

        await opener.open(try XCTUnwrap(URL(string: "https://evil.test/s#\(shareId)")), in: app)
        await opener.open(try XCTUnwrap(URL(string: "https://burro.example.test/methods")), in: app)

        XCTAssertNil(opener.presented)
        XCTAssertEqual(app.searchPath, [])
        XCTAssertEqual(api.calls.count, 0)
    }

    // MARK: - Opening a shared search

    @MainActor
    func test_a_shared_search_is_opened_and_says_what_it_holds() async throws {
        let api = StandIn.firstSearch().on(.getShare, "share-opened")
        let app = AreaFixtures.app(api)
        let shared = try XCTUnwrap(SharedSearch(shareId: shareId, app: app))
        XCTAssertEqual(shared.stage, .opening)

        await shared.open()

        guard case .open(let opened) = shared.stage else { return XCTFail("The share did not open.") }
        XCTAssertEqual(app.search?.state.spec, Answers.shared("share-opened").spec)
        XCTAssertEqual(app.search?.state.phase, .results)
        XCTAssertEqual(
            opened.lines,
            [
                "This search was opened from a link. Changing it here does not change the link.",
                LinkCopy.Shared.holds,
                "A place in this search is the station or district that stands in for the place the sender named. "
                    + "The ranking may differ a little from theirs.",
            ])
        XCTAssertEqual(opened.ranked, 21)
        let first = try XCTUnwrap(Answers.shared("share-opened").scores.first)
        XCTAssertEqual(opened.first, Answers.areas.first { $0.areaId == first.areaId }?.name)
        XCTAssertEqual(opened.status, "21 areas ranked. First: Eskerfold.")
        // The place is named by the share's own answer: the station that stands in for what the sender named.
        XCTAssertEqual(app.search?.state.placeNames, ["syn-p0005": "Eskerfold"])
        XCTAssertFalse(shared.canTryAgain)
    }

    @MainActor
    func test_a_share_id_is_only_ever_in_the_one_call_that_opens_it() async throws {
        let api = StandIn.firstSearch().on(.getShare, "share-opened")
        let names = MemoryPhoneStorage()
        let facts = MemorySavedAreasStorage()
        let app = AreaFixtures.app(api, storage: names)
        let saved = SavedAreas(app: app, storage: facts)
        let opener = LinkOpener()

        await opener.open(try XCTUnwrap(URL(string: "https://burro.example.test/s#\(shareId)")), in: app)
        await SharedSearch(shareId: shareId, app: app)?.open()
        opener.showResults(in: app)
        saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))

        let holding = api.calls.filter {
            $0.outsideTheBody.contains(shareId) || String(decoding: $0.sent ?? Data(), as: UTF8.self).contains(shareId)
        }
        XCTAssertEqual(holding.map(\.path), ["/v1/shares/\(shareId)"])
        XCTAssertEqual(holding.first?.method, "GET")
        XCTAssertNil(holding.first?.url.query)
        XCTAssertFalse(String(reflecting: app.searchPath).contains(shareId))
        XCTAssertFalse(String(reflecting: opener.presented).contains(shareId))
        for file in KeptFile.allCases {
            XCTAssertFalse(String(decoding: names.read(file) ?? Data(), as: UTF8.self).contains(shareId))
        }
        XCTAssertFalse(String(reflecting: facts.read()).contains(shareId))
    }

    @MainActor
    func test_a_share_that_is_open_already_is_not_opened_again_over_what_was_changed_since() async throws {
        let api = StandIn.firstSearch().on(.getShare, "share-opened")
        let app = AreaFixtures.app(api)
        await SharedSearch(shareId: shareId, app: app)?.open()
        api.on(.rank, StandIn.withTheSpecSent("rank-refined"))
        await app.search?.flow.applyEdits(Edits.tagOn(.leafy))
        let changed = app.search?.state.spec

        let again = try XCTUnwrap(SharedSearch(shareId: shareId, app: app))
        await again.open()

        XCTAssertEqual(api.calls(to: .getShare).count, 1)
        XCTAssertEqual(app.search?.state.spec, changed)
        guard case .open = again.stage else { return XCTFail("The share was not shown as open.") }
    }

    @MainActor
    func test_a_share_made_on_older_data_says_so_and_names_both_releases() async throws {
        let api = StandIn.firstSearch().on(.getShare, "share-opened-stale")
        let app = AreaFixtures.app(api)
        let shared = try XCTUnwrap(SharedSearch(shareId: "a9yIlz7uQ1b3F4vDySSZRg", app: app))

        await shared.open()

        guard case .open(let opened) = shared.stage else { return XCTFail("The share did not open.") }
        XCTAssertTrue(opened.stale)
        XCTAssertFalse(opened.coarsened)
        XCTAssertTrue(opened.hasPlaces)
        XCTAssertEqual(opened.madeOn, "syn-2026-09-23-01")
        XCTAssertEqual(
            Array(opened.lines.suffix(2)),
            [
                "The places in this search are the ones the sender named: "
                    + "they chose to share them, or each is a station or a district already.",
                "The data has changed since this link was made, so the ranking may differ from what the sender saw. "
                    + "It was made on data release syn-2026-09-23-01. It is shown on \(opened.shownOn).",
            ])
    }

    @MainActor
    func test_a_link_that_leads_nowhere_is_said_in_the_apis_words_and_the_search_is_left_alone() async throws {
        for (scenario, code, words) in [
            ("share-not-found", ErrorCode.shareNotFound, "There is no such shared search."),
            ("share-gone", ErrorCode.releaseChanged, "The data has changed and this shared search cannot be shown."),
        ] {
            let api = StandIn.firstSearch().on(.getShare, scenario)
            let app = AreaFixtures.app(api)
            app.consent.choose(.allowed)
            await app.open()
            await app.search?.flow.submitText("leafy and quiet")
            let before = app.search?.state
            let shared = try XCTUnwrap(SharedSearch(shareId: shareId, app: app))

            await shared.open()

            guard case .failed(let failure) = shared.stage else { return XCTFail("The share opened.") }
            XCTAssertEqual(failure.code, code)
            XCTAssertEqual(ShellCopy.words(for: failure), words)
            // The API has said the link leads nowhere. Asking again would be told the same.
            XCTAssertFalse(shared.canTryAgain)
            XCTAssertEqual(app.search?.state, before)
        }
    }

    @MainActor
    func test_a_share_that_could_not_be_reached_can_be_tried_again() async throws {
        let api = StandIn.firstSearch().unreachable(.getShare, .notConnectedToInternet)
        let app = AreaFixtures.app(api)
        let shared = try XCTUnwrap(SharedSearch(shareId: shareId, app: app))

        await shared.open()
        XCTAssertEqual(shared.stage, .failed(.because(.offline)))
        XCTAssertTrue(shared.canTryAgain)
        api.on(.getShare, "share-opened")
        await shared.open()

        guard case .open = shared.stage else { return XCTFail("The share did not open.") }
    }

    @MainActor
    func test_a_share_cannot_be_opened_while_the_app_cannot_be_and_says_why() async throws {
        let api = StandIn.firstSearch().unreachable(.getMeta, .notConnectedToInternet)
        let app = AreaFixtures.app(api)
        let shared = try XCTUnwrap(SharedSearch(shareId: shareId, app: app))

        await shared.open()

        XCTAssertEqual(shared.stage, .failed(.because(.offline)))
        XCTAssertEqual(api.calls(to: .getShare).count, 0)
    }

    @MainActor
    func test_opening_a_share_needs_no_agreement_because_it_sends_no_sentence() async throws {
        let api = StandIn.firstSearch().on(.getShare, "share-opened")
        let app = AreaFixtures.app(api)
        XCTAssertNil(app.consent.choice)

        await SharedSearch(shareId: shareId, app: app)?.open()

        XCTAssertEqual(api.calls(to: .interpret).count, 0)
        XCTAssertEqual(api.calls(to: .getShare).count, 1)
        XCTAssertNotNil(app.search?.state.shared)
    }

    func test_what_is_said_of_the_ranking_a_share_opened() {
        func opened(_ ranked: Int, first: String?, inOrder: Bool = true) -> SharedSearch.Opened {
            SharedSearch.Opened(
                coarsened: false, hasPlaces: false, stale: false, madeOn: "a", shownOn: "a", ranked: ranked,
                first: first, inOrder: inOrder)
        }

        XCTAssertEqual(opened(22, first: "Farrowmere").status, "22 areas ranked. First: Farrowmere.")
        XCTAssertEqual(opened(1, first: "Farrowmere").status, "1 area ranked. First: Farrowmere.")
        XCTAssertEqual(opened(3, first: nil).status, "3 areas ranked.")
        XCTAssertEqual(opened(0, first: nil).status, "No area passes every limit you set.")
        XCTAssertEqual(
            opened(24, first: "Alderwick", inOrder: false).status,
            "24 areas pass. Nothing is set to rank them by, so they are in no order.")
        XCTAssertEqual(opened(2, first: nil).lines.count, 2)
    }

    func test_the_words_for_a_shared_search_are_the_websites_word_for_word() throws {
        let share = try Repository.text(Repository.root.appendingPathComponent("apps/web/src/content/share.ts"))
        let search = try Repository.text(Repository.root.appendingPathComponent("apps/web/src/content/search.ts"))

        for words in [
            LinkCopy.Shared.title, LinkCopy.Shared.text, LinkCopy.Shared.holds, LinkCopy.Shared.coarsened,
            LinkCopy.Shared.exact, LinkCopy.Shared.stale, LinkCopy.Shared.madeOn, LinkCopy.Shared.shownOn,
            LinkCopy.Shared.opening, LinkCopy.Shared.failedTitle, LinkCopy.Shared.tryAgain, LinkCopy.Shared.own,
            LinkCopy.NoShare.title, LinkCopy.NoShare.text, LinkCopy.NotAShare.title, LinkCopy.NotAShare.text,
        ] {
            XCTAssertTrue(share.contains("\"\(words)\""), words)
        }
        XCTAssertTrue(search.contains("\"\(LinkCopy.Ranked.none)\""))
        // The line is made of two parts, as the website makes it: how many, and which is first.
        XCTAssertTrue(search.contains("${count} areas ranked."))
        XCTAssertTrue(search.contains("\"1 area ranked.\""))
        XCTAssertTrue(search.contains("First: ${name}."))
        XCTAssertEqual(LinkCopy.Ranked.named(3, first: "A"), "3 areas ranked. First: A.")
        XCTAssertTrue(search.contains("${count} areas pass. Nothing is set to rank them by, so they are in no order."))
    }
}
