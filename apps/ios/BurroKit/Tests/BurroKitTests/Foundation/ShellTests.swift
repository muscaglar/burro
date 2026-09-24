import SwiftUI
import XCTest

@testable import BurroKit

/// The shell: opening the release, the three tabs, the banner, and the seams
/// each feature is built against.
final class ShellTests: XCTestCase {
    private let farrowmere = AreaRef(
        areaId: "syn-n0006", slug: "farrowmere", name: "Farrowmere", borough: "Quillhaven")

    @MainActor
    private func model(
        _ api: StandIn = StandIn.firstSearch(), storage: any PhoneStorage = MemoryPhoneStorage()
    ) -> AppModel {
        let notice = SyntheticNotice()
        let client = LiveBurroAPI(
            configuration: APIConfiguration(StandIn.base), transport: api,
            onSynthetic: { said in await notice.note(said) })
        return AppModel(
            api: client, site: SiteAddress("https://burro.example.test"), synthetic: notice, storage: storage)
    }

    // MARK: - Opening

    @MainActor
    func test_the_app_opens_on_the_form_and_the_areas_the_api_serves() async {
        let api = StandIn.firstSearch()
        let app = model(api)
        XCTAssertEqual(app.opening, .waiting)
        XCTAssertNil(app.search)

        await app.open()

        XCTAssertEqual(app.opening, .open)
        XCTAssertEqual(app.search?.state.meta, Answers.meta)
        XCTAssertEqual(app.search?.state.areas, Answers.areas)
        XCTAssertEqual(app.search?.state.phase, .empty)
        XCTAssertEqual(Set(api.routes), [.getMeta, .listAreas])
    }

    @MainActor
    func test_opening_twice_reads_the_release_once_and_keeps_the_search() async {
        let api = StandIn.firstSearch()
        let app = model(api)

        await app.open()
        let search = app.search
        await app.open()

        XCTAssertEqual(api.calls.count, 2)
        XCTAssertTrue(app.search === search)
    }

    @MainActor
    func test_an_app_that_cannot_open_says_why_and_can_try_again() async {
        let api = StandIn.firstSearch().unreachable(.getMeta, .notConnectedToInternet)
        let app = model(api)

        await app.open()
        XCTAssertEqual(app.opening, .failed(.because(.offline)))
        XCTAssertNil(app.search)
        XCTAssertEqual(ShellCopy.words(for: .because(.offline)), "You are offline.")
        api.on(.getMeta, "meta")
        await app.open()

        XCTAssertEqual(app.opening, .open)
        XCTAssertNotNil(app.search)
    }

    @MainActor
    func test_with_no_address_set_the_app_says_it_is_not_connected() async {
        let app = AppModel.live(infoDictionary: [:])

        await app.open()

        XCTAssertEqual(app.opening, .failed(.because(.notConfigured)))
    }

    // MARK: - The banner

    @MainActor
    func test_the_banner_shows_as_soon_as_any_answer_says_the_data_is_made_up() async {
        let app = model()
        XCTAssertFalse(app.synthetic.seen)

        await app.open()

        XCTAssertTrue(app.synthetic.seen)
    }

    @MainActor
    func test_the_banner_only_ever_turns_on() {
        let notice = SyntheticNotice()

        notice.note(false)
        XCTAssertFalse(notice.seen)
        notice.note(true)
        notice.note(false)

        XCTAssertTrue(notice.seen)
    }

    @MainActor
    func test_the_banner_shows_with_no_connection_when_a_saved_area_is_made_up() {
        let storage = MemoryPhoneStorage()
        Shortlist(storage: storage).add(farrowmere, synthetic: true)

        let app = model(StandIn().unreachable(.getMeta), storage: storage)

        XCTAssertTrue(app.synthetic.seen)
        XCTAssertEqual(app.shortlist.entries.map(\.name), ["Farrowmere"])
    }

    func test_the_banner_says_what_the_website_says_word_for_word() throws {
        let site = try Repository.text(Repository.root.appendingPathComponent("apps/web/src/content/site.ts"))
        let sentences = ShellCopy.banner.components(separatedBy: ". ").map {
            $0.hasSuffix(".") ? $0 : $0 + "."
        }

        XCTAssertEqual(sentences.count, 3)
        for sentence in sentences { XCTAssertTrue(site.contains(sentence), sentence) }
        XCTAssertTrue(site.contains("label: \"\(ShellCopy.bannerLabel)\""))
    }

    func test_the_shell_draws_the_banner_above_every_tab_and_not_on_the_screen_that_shows_no_data() throws {
        let root = try Repository.text(Repository.sources.appendingPathComponent("Shell/BurroRootView.swift"))
        let permission = try Repository.text(
            Repository.sources.appendingPathComponent("Features/Search/PermissionView.swift"))

        let banner = try XCTUnwrap(root.range(of: "SyntheticBanner()"))
        let tabs = try XCTUnwrap(root.range(of: "TabView(selection:"))
        XCTAssertLessThan(banner.lowerBound, tabs.lowerBound)
        XCTAssertEqual(root.components(separatedBy: "SyntheticBanner()").count - 1, 1)
        XCTAssertFalse(permission.contains("SyntheticBanner"))
    }

    // MARK: - Going somewhere

    @MainActor
    func test_there_are_three_tabs_in_the_order_search_shortlist_about() {
        XCTAssertEqual(AppTab.allCases, [.search, .shortlist, .about])
        XCTAssertEqual(AppTab.allCases.map(ShellCopy.title(of:)), ["Search", "Shortlist", "About"])
        XCTAssertEqual(Set(AppTab.allCases.map(ShellCopy.image(of:))).count, 3)
        XCTAssertEqual(model().tab, .search)
    }

    @MainActor
    func test_a_screen_is_pushed_onto_the_tab_that_is_showing() {
        let app = model()

        app.show(.results)
        app.show(.area(farrowmere))
        app.show(.area(farrowmere), in: .shortlist)
        app.show(.sources, in: .about)

        XCTAssertEqual(app.searchPath, [.results, .area(farrowmere)])
        XCTAssertEqual(app.shortlistPath, [.area(farrowmere)])
        XCTAssertEqual(app.aboutPath, [.sources])
        XCTAssertEqual(app.tab, .about)
        app.showRoot(of: .search)
        XCTAssertEqual(app.searchPath, [])
        XCTAssertEqual(app.tab, .search)
        XCTAssertEqual(app.shortlistPath, [.area(farrowmere)])
    }

    func test_a_route_holds_ids_and_names_of_the_release_and_nothing_of_a_search() {
        let fields = Mirror(reflecting: farrowmere).children.compactMap(\.label)

        XCTAssertEqual(fields, ["areaId", "slug", "name", "borough"])
        XCTAssertEqual(AreaRef(Answers.areas[5]), farrowmere)
        XCTAssertEqual(AreaRef(Answers.profile("farrowmere").area), farrowmere)
    }

    // MARK: - The shortlist and the choice, from a screen

    @MainActor
    func test_an_area_is_saved_and_taken_off_from_its_screen() async {
        let app = model()
        await app.open()

        app.toggleShortlist(farrowmere)
        XCTAssertEqual(app.shortlist.entries.map(\.areaId), ["syn-n0006"])
        XCTAssertEqual(app.shortlist.entries.first?.synthetic, true)
        app.toggleShortlist(farrowmere)

        XCTAssertEqual(app.shortlist.entries, [])
    }

    @MainActor
    func test_an_area_saved_from_a_result_is_kept_with_its_facts_and_nothing_of_the_search() async throws {
        let storage = MemoryPhoneStorage()
        let app = model(storage: storage)
        app.consent.choose(.allowed)
        await app.open()
        await app.search?.flow.submitText("leafy zqxcanary5150")

        // The search has read the first five areas, and this is the first of them.
        app.toggleShortlist(farrowmere)

        let kept = try XCTUnwrap(app.saved.kept["syn-n0006"])
        XCTAssertEqual(kept.releaseId, Answers.meta.releaseId)
        XCTAssertFalse(kept.rows.isEmpty)
        XCTAssertEqual(app.shortlist.entries.map(\.areaId), ["syn-n0006"])
        let spec = try XCTUnwrap(app.search?.state.spec)
        for file in KeptFile.allCases {
            let written = String(decoding: storage.read(file) ?? Data(), as: UTF8.self)
            XCTAssertFalse(written.contains("zqxcanary5150"), file.fileName)
            XCTAssertFalse(written.contains("travel"), file.fileName)
            for place in spec.commutes.map(\.placeId) { XCTAssertFalse(written.contains(place), file.fileName) }
        }
        // It is there when the app is opened again, with no connection.
        let again = model(StandIn().unreachable(.getMeta), storage: storage)
        XCTAssertEqual(again.saved.entries.first?.kept?.page.said, kept.page.said)
        XCTAssertEqual(again.saved.entries.first?.kept?.releaseId, kept.releaseId)

        app.toggleShortlist(farrowmere)
        XCTAssertNil(storage.read(.savedAreas))
        XCTAssertEqual(app.shortlist.entries, [])
    }

    @MainActor
    func test_an_area_the_search_has_not_read_is_saved_by_its_names_until_its_page_is_read() async {
        let app = model()
        await app.open()

        app.toggleShortlist(farrowmere)

        XCTAssertEqual(app.saved.entries.map(\.id), ["syn-n0006"])
        XCTAssertNil(app.saved.entries.first?.kept)
    }

    func test_the_shell_opens_the_websites_links_and_covers_what_a_link_puts_up() throws {
        let root = try Repository.text(Repository.sources.appendingPathComponent("Shell/BurroRootView.swift"))
        let links = try Repository.text(
            Repository.sources.appendingPathComponent("Features/Area/SharedSearchView.swift"))

        // Inside the environment that holds the app, and whichever screen is showing.
        let opens = try XCTUnwrap(root.range(of: ".opensLinks()"))
        let environment = try XCTUnwrap(root.range(of: ".environment(app)"))
        XCTAssertLessThan(opens.lowerBound, environment.lowerBound)
        // A sheet stands over the shell's cover and its banner, so it draws its own of each.
        let sheet = try XCTUnwrap(links.components(separatedBy: ".sheet(item:").last)
        XCTAssertTrue(sheet.contains("SyntheticBanner()"))
        XCTAssertTrue(sheet.contains("if scenePhase != .active {\n                        PrivacyCover()"))
    }

    @MainActor
    func test_an_area_saved_with_no_search_open_is_known_to_be_made_up_by_its_id() {
        let app = model()

        XCTAssertTrue(app.isSynthetic(farrowmere))
        XCTAssertFalse(
            app.isSynthetic(AreaRef(areaId: "lon-n0006", slug: "a", name: "A", borough: "B")))
    }

    @MainActor
    func test_the_search_sends_no_sentence_until_the_person_agrees_and_does_once_they_have() async {
        let api = StandIn.firstSearch()
        let app = model(api)
        await app.open()

        await app.search?.flow.submitText("leafy")
        XCTAssertEqual(api.calls(to: .interpret).count, 0)
        app.consent.choose(.settingsOnly)
        await app.search?.flow.submitText("leafy")
        XCTAssertEqual(api.calls(to: .interpret).count, 0)
        app.consent.choose(.allowed)
        await app.search?.flow.submitText("leafy")

        XCTAssertEqual(api.calls(to: .interpret).count, 1)
    }

    // MARK: - The seams

    @MainActor
    func test_every_screen_a_feature_owns_is_made_as_the_shell_makes_it() {
        let screens: [any View] = [
            PermissionView(),
            SearchRootView(),
            ResultsView(),
            ResultsCompareView(),
            AreaView(area: farrowmere),
            ShortlistRootView(),
            AboutRootView(),
            AboutScreenView(screen: .methods),
            Opened { ResultsView() },
            SyntheticBanner(),
            BurroRootView(model: model()),
        ]

        XCTAssertEqual(screens.count, 11)
    }

    func test_every_feature_has_its_own_folder_with_its_first_screen_in_it() {
        let files = Set(Repository.files(under: Repository.sources.appendingPathComponent("Features"), ending: ".swift"))

        for first in [
            "Search/SearchRootView.swift", "Search/PermissionView.swift", "Results/ResultsView.swift",
            "Area/AreaView.swift", "Shortlist/ShortlistRootView.swift", "About/AboutRootView.swift",
        ] {
            XCTAssertTrue(files.contains(first), first)
        }
    }

    func test_the_guide_says_who_owns_every_folder_of_the_package() throws {
        let guide = try Repository.text(Repository.ios.appendingPathComponent("AGENTS.md"))
        let folders = try FileManager.default.contentsOfDirectory(atPath: Repository.sources.path)
            .filter { !$0.hasPrefix(".") }
        let features = try FileManager.default.contentsOfDirectory(
            atPath: Repository.sources.appendingPathComponent("Features").path
        ).filter { !$0.hasPrefix(".") }

        for folder in folders where folder != "Features" {
            XCTAssertTrue(guide.contains("`\(folder)/`"), folder)
        }
        for feature in features {
            XCTAssertTrue(guide.contains("`Features/\(feature)/`"), feature)
        }
        XCTAssertLessThanOrEqual(guide.components(separatedBy: "\n").count, 150)
    }
}
