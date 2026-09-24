import XCTest

@testable import BurroKit

/// Sharing the search, and what a press on a card does.
///
/// A share's id unlocks a search, so it is treated as what was typed is: it
/// is held in memory, goes in the fragment of the one link the person asked
/// for, and is handed to the phone's share sheet and to nothing else.
final class ResultsShareTests: XCTestCase {
    // A string found nowhere else, planted in what a person types.
    private let canary = "zqxresults5290"
    private let shareId = "rPnAeuBsXQci-xINLK_f2w"

    // MARK: - Sharing the search

    @MainActor
    func test_no_share_is_offered_until_the_website_has_an_address() async throws {
        let none = try await ResultsApp.searched(site: nil)
        let some = try await ResultsApp.searched()
        let empty = try await ResultsApp()

        XCTAssertFalse(none.hands.canShare)
        XCTAssertTrue(some.hands.canShare)
        // Nor before there is a ranking to share.
        XCTAssertFalse(empty.hands.canShare)

        none.hands.openShare()
        await none.hands.makeLink()
        XCTAssertFalse(none.memory.shareOpen)
        XCTAssertEqual(none.api.calls(to: .createShare).count, 0)
        XCTAssertEqual(none.memory.sharing.shown(for: none.state), .idle)
    }

    @MainActor
    func test_opening_the_panel_makes_nothing_and_sends_nothing() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.createShare, "share-made"))

        app.hands.openShare()

        XCTAssertTrue(app.memory.shareOpen)
        XCTAssertEqual(app.memory.bringIntoView, Results.Memory.sharePanel)
        XCTAssertEqual(app.api.calls(to: .createShare).count, 0)
        XCTAssertEqual(app.memory.sharing.shown(for: app.state), .idle)
        // What the link will hold is said before anything is made.
        XCTAssertEqual(ResultsCopy.Share.points.count, 5)
    }

    @MainActor
    func test_the_link_is_made_of_the_spec_the_api_last_returned_and_coarse_unless_asked() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.createShare, "share-made"))
        XCTAssertFalse(app.memory.sharing.exact)

        await app.hands.makeLink()

        XCTAssertEqual(
            try app.api.lastCall(to: .createShare).body(as: ShareBody.self),
            ShareBody(spec: app.state.spec, exactDestinations: false))
        guard case .made(let link) = app.memory.sharing.shown(for: app.state) else {
            return XCTFail("No link was made.")
        }
        XCTAssertEqual(link.url.absoluteString, "https://burro.example.test/s#\(shareId)")
        XCTAssertTrue(link.coarsened)
        XCTAssertEqual(link.words, ResultsCopy.Share.coarsened)
        XCTAssertFalse(link.exact)
    }

    @MainActor
    func test_the_exact_places_are_kept_only_when_the_person_turns_that_on() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.createShare, "share-made-exact"))
        app.memory.sharing.exact = true

        await app.hands.makeLink()

        XCTAssertEqual(try app.api.lastCall(to: .createShare).body(as: ShareBody.self).exactDestinations, true)
        guard case .made(let link) = app.memory.sharing.shown(for: app.state) else {
            return XCTFail("No link was made.")
        }
        XCTAssertFalse(link.coarsened)
        XCTAssertEqual(link.words, "The link holds the places as you named them.")
    }

    @MainActor
    func test_a_search_that_names_no_place_has_nothing_to_keep_exact() async throws {
        let api = StandIn.firstSearch().on(.rank, "rank-default-rent").on(.createShare, "share-made-no-place")
        let app = try await ResultsApp(api)
        await app.flow.rankNow()
        app.memory.sharing.exact = true

        await app.hands.makeLink()

        XCTAssertEqual(try app.api.lastCall(to: .createShare).body(as: ShareBody.self).exactDestinations, false)
        guard case .made(let link) = app.memory.sharing.shown(for: app.state) else {
            return XCTFail("No link was made.")
        }
        XCTAssertEqual(link.words, "This search names no place, so the link holds none.")
    }

    @MainActor
    func test_the_link_holds_the_id_in_its_fragment_and_nothing_of_the_search() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.createShare, "share-made"))
        await app.flow.submitText("leafy \(canary)")

        await app.hands.makeLink()

        guard case .made(let link) = app.memory.sharing.shown(for: app.state) else {
            return XCTFail("No link was made.")
        }
        let parts = try XCTUnwrap(URLComponents(url: link.url, resolvingAgainstBaseURL: false))
        XCTAssertEqual(parts.scheme, "https")
        XCTAssertEqual(parts.host, "burro.example.test")
        XCTAssertEqual(parts.path, "/s")
        XCTAssertNil(parts.query)
        XCTAssertEqual(parts.fragment, shareId)
        let text = link.url.absoluteString
        XCTAssertFalse(text.contains(canary))
        for commute in app.state.spec.commutes { XCTAssertFalse(text.contains(commute.placeId)) }
        for name in app.state.placeNames.values { XCTAssertFalse(text.contains(name)) }
        XCTAssertFalse(text.contains(try XCTUnwrap(app.state.specHash)))
    }

    @MainActor
    func test_the_id_of_a_share_is_in_no_request_and_is_never_written_to_the_phone() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.createShare, "share-made"))

        await app.hands.makeLink()
        app.hands.toggleShortlist(try app.firstCard().area)

        for call in app.api.calls {
            XCTAssertFalse(call.outsideTheBody.contains(shareId))
            XCTAssertFalse(String(decoding: call.sent ?? Data(), as: UTF8.self).contains(shareId))
        }
        let kept = String(decoding: try XCTUnwrap(app.storage.read(.shortlist)), as: UTF8.self)
        XCTAssertFalse(kept.contains(shareId))
        // Nor is it drawn: the screen hands the link to the share sheet, and shows none of it.
        XCTAssertFalse(ResultsDrawn.all(in: app.listed).texts.contains { $0.contains(shareId) })
        XCTAssertFalse(String(describing: app.state).contains(shareId))
    }

    @MainActor
    func test_a_link_is_shown_only_for_the_search_it_was_made_of() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.createShare, "share-made"))
        await app.hands.makeLink()
        XCTAssertFalse(app.memory.sharing.isGone(for: app.state))
        app.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")

        await app.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))

        XCTAssertEqual(app.memory.sharing.shown(for: app.state), .idle)
        XCTAssertTrue(app.memory.sharing.isGone(for: app.state))
        app.memory.sharing.forget()
        XCTAssertFalse(app.memory.sharing.isGone(for: app.state))
    }

    @MainActor
    func test_an_id_that_is_not_one_the_api_makes_is_put_in_no_link() async throws {
        let api = StandIn.firstSearch().on(
            .createShare,
            .made { _ in
                try Recorded.read("share-made").with(data: { $0["share_id"] = .string("../../not an id?x=1") })
            })
        let app = try await ResultsApp.searched(api)

        await app.hands.makeLink()

        guard case .failed(let words, _) = app.memory.sharing.shown(for: app.state) else {
            return XCTFail("A link was made of what is not an id.")
        }
        XCTAssertEqual(words, "Burro sent a link that could not be read.")
    }

    @MainActor
    func test_a_link_that_cannot_be_made_says_so_in_the_apis_words_with_the_id_to_quote() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.createShare, "error-internal"))

        await app.hands.makeLink()

        XCTAssertEqual(
            app.memory.sharing.shown(for: app.state),
            .failed(
                words: "Something went wrong on the server.",
                requestId: try Recorded.read("error-internal").headers["x-request-id"]))
        // The search is as it was.
        XCTAssertEqual(app.listed.cards.count, 20)
        XCTAssertEqual(app.listed.lines, [])
    }

    // MARK: - What a press on a card does

    @MainActor
    func test_open_goes_to_the_area_with_a_route_that_holds_nothing_of_the_search() async throws {
        let app = try await ResultsApp(StandIn.firstSearch())
        await app.flow.submitText("leafy \(canary)")
        app.app.show(.results)
        let card = try app.firstCard()

        app.hands.open(card.area)

        XCTAssertEqual(
            app.app.searchPath,
            [.results, .area(AreaRef(areaId: "syn-n0006", slug: "farrowmere", name: "Farrowmere", borough: "Quillhaven"))])
        XCTAssertEqual(app.app.tab, .search)
        XCTAssertFalse(String(describing: app.app.searchPath).contains(canary))
        XCTAssertFalse(String(describing: app.app.searchPath).contains("syn-p"))
        // The page is asked for when it is opened, and not before, by this screen.
        XCTAssertEqual(app.api.calls(to: .getArea).count, 5)
    }

    @MainActor
    func test_the_shortlist_keeps_the_area_and_the_date_and_never_the_search_that_led_to_it() async throws {
        let app = try await ResultsApp(StandIn.firstSearch())
        await app.flow.submitText("leafy \(canary)")
        let card = try app.firstCard()
        XCTAssertFalse(app.hands.isSaved(card.area))

        app.hands.toggleShortlist(card.area)

        XCTAssertTrue(app.hands.isSaved(card.area))
        let kept = try JSON.read(try XCTUnwrap(app.storage.read(.shortlist)))
        guard case .array(let entries)? = kept["entries"], let entry = entries.first,
            case .object(let fields) = entry
        else { return XCTFail("Nothing was kept.") }
        XCTAssertEqual(Set(fields.keys), ["area_id", "slug", "name", "borough", "saved_on", "synthetic"])
        XCTAssertEqual(entry["name"]?.string, "Farrowmere")
        XCTAssertEqual(entry["synthetic"]?.bool, true)
        let text = String(decoding: try XCTUnwrap(app.storage.read(.shortlist)), as: UTF8.self)
        for unkept in [canary, "syn-p0021", "Cindermoor Works", "leafy", try XCTUnwrap(app.state.specHash)] {
            XCTAssertFalse(text.contains(unkept), unkept)
        }
        // The button says what it would do next, so that it is never told by colour alone.
        app.hands.toggleShortlist(card.area)
        XCTAssertFalse(app.hands.isSaved(card.area))
        XCTAssertEqual(ResultsCopy.Shortlist.add, "Add to shortlist")
        XCTAssertEqual(ResultsCopy.Shortlist.remove, "Remove from shortlist")
    }

    @MainActor
    func test_hide_sends_one_edit_with_the_last_spec_the_api_returned_and_builds_no_spec() async throws {
        let app = try await ResultsApp.searched()
        let card = try app.firstCard()
        let before = app.state.spec
        app.hands.choose(onMap: card.id)
        app.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")

        await app.hands.hide(card.area)

        XCTAssertEqual(
            try app.api.lastCall(to: .rank).body(as: RankBody.self),
            RankBody(spec: before, limit: 20, operations: Edits.areaHide("syn-n0006")))
        // The spec on screen is the one the API returned, whatever the app asked for.
        XCTAssertEqual(app.state.spec, Answers.ranked("rank-refined").spec)
        XCTAssertNil(app.state.selectedId)
    }

    @MainActor
    func test_an_edit_the_api_refused_is_said_on_the_card_it_was_about() async throws {
        let app = try await ResultsApp.searched()
        // No recording shows an area that could not be hidden, so one is made of a recorded ranking.
        app.api.on(
            .rank,
            .made { _ in
                try Recorded.read("rank-first").with(data: { data in
                    data["rejected"] = .array([
                        .object([
                            "group": .string("area_ops"), "index": .number(0),
                            "reason": .string("nothing_to_change"),
                        ])
                    ])
                })
            })

        await app.hands.hide(try app.firstCard().area)

        XCTAssertEqual(try app.firstCard().refusal, .nothingToChange)
        XCTAssertTrue(app.listed.cards.dropFirst().allSatisfy { $0.refusal == nil })
        XCTAssertEqual(ResultsCopy.word(for: RejectReason.nothingToChange), "That changed nothing.")
    }

    @MainActor
    func test_a_line_that_needs_the_box_goes_back_to_the_search() async throws {
        let app = try await ResultsApp.searched()
        app.app.show(.results)
        app.app.show(.area(try app.firstCard().area))

        await app.hands.act(.toSearch)

        XCTAssertEqual(app.app.searchPath, [])
        XCTAssertEqual(app.app.tab, .search)
        // The search is still open.
        XCTAssertEqual(app.listed.cards.count, 20)
    }

    @MainActor
    func test_a_source_leads_to_the_screen_of_every_source() async throws {
        let app = try await ResultsApp.searched()
        app.app.show(.results)

        app.hands.openSources()

        XCTAssertEqual(app.app.searchPath, [.results, .sources])
    }

    @MainActor
    func test_show_in_the_list_makes_room_for_the_card_and_brings_it_into_view() async throws {
        let app = try await ResultsApp.searched()
        let card = app.listed.cards[3]
        app.memory.height = .low

        app.hands.showInList(card.area)
        XCTAssertEqual(app.memory.height, .half)
        XCTAssertEqual(app.memory.bringIntoView, card.id)
        app.memory.showing = .table
        app.hands.showInList(card.area)

        XCTAssertEqual(app.memory.showing, .list)
    }

    @MainActor
    func test_a_row_of_the_table_is_chosen_and_let_go_by_the_same_button() async throws {
        let app = try await ResultsApp.searched()
        let row = app.tabled.rows[4]

        app.hands.choose(inTable: row.area)
        XCTAssertEqual(app.tabled.rows.filter(\.selected).map(\.id), [row.id])
        app.hands.choose(inTable: row.area)

        XCTAssertNil(app.state.selectedId)
        app.hands.choose(inTable: row.area)
        app.hands.close()
        XCTAssertNil(app.state.selectedId)
    }

    // MARK: - What was typed is nowhere on this screen

    @MainActor
    func test_nothing_the_person_typed_is_held_or_drawn_by_the_results() async throws {
        let api = StandIn.firstSearch()
            .on(.createShare, "share-made")
            .on(.compare, "compare-three")
        let app = try await ResultsApp(api)
        await app.flow.loadGeometry()
        await app.flow.submitText("leafy \(canary)")
        let cards = app.listed.cards
        cards.prefix(3).forEach { app.hands.toggleCompare($0.area) }
        app.hands.toggleShortlist(cards[0].area)
        app.hands.choose(onMap: cards[1].id)
        let comparison = Results.Comparison()
        await comparison.ask(app.memory.compare, of: app.search)
        await app.hands.makeLink()

        let drawn: [Any] = [
            app.listed, app.mapped, app.tabled, app.memory.compare, comparison.answer,
            app.memory.sharing.shown(for: app.state), app.app.searchPath,
        ]
        for value in drawn {
            XCTAssertFalse(String(describing: value).contains(canary))
            XCTAssertFalse(String(reflecting: value).contains(canary))
        }
        for file in KeptFile.allCases {
            let kept = app.storage.read(file).map { String(decoding: $0, as: UTF8.self) } ?? ""
            XCTAssertFalse(kept.contains(canary))
        }
        // The canary left the app once, in the body of the one call that reads a sentence.
        for call in app.api.calls where call.route != .interpret {
            XCTAssertFalse(String(decoding: call.sent ?? Data(), as: UTF8.self).contains(canary))
            XCTAssertFalse(call.outsideTheBody.contains(canary))
        }
        XCTAssertEqual(app.api.calls(to: .interpret).count, 1)
        XCTAssertEqual(app.api.unexpected.count, 0)
    }
}
