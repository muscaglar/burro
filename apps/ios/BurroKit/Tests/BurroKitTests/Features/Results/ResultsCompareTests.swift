import XCTest

@testable import BurroKit

/// Comparing two to four areas: the areas a person chose, and the table that
/// sets them side by side on the search that is open.
final class ResultsCompareTests: XCTestCase {
    private func area(_ name: String) throws -> AreaRef {
        AreaRef(try XCTUnwrap(Answers.areas.first { $0.name == name }))
    }

    // MARK: - Choosing

    func test_an_area_is_put_in_and_taken_out_and_a_fifth_is_not_let_in() throws {
        let names = ["Farrowmere", "Cindermoor", "Alderwick", "Foxholt", "Gorsebeck"]
        let areas = try names.map(area)

        var chosen: [AreaRef] = []
        for one in areas { chosen = Results.toggled(chosen, one) }

        XCTAssertEqual(chosen.map(\.name), ["Farrowmere", "Cindermoor", "Alderwick", "Foxholt"])
        XCTAssertTrue(Results.isFull(chosen))
        chosen = Results.toggled(chosen, areas[1])
        XCTAssertEqual(chosen.map(\.name), ["Farrowmere", "Alderwick", "Foxholt"])
        chosen = Results.toggled(chosen, areas[4])
        XCTAssertEqual(chosen.map(\.name), ["Farrowmere", "Alderwick", "Foxholt", "Gorsebeck"])
    }

    func test_the_tray_says_how_many_are_chosen_and_offers_to_compare_two_to_four() throws {
        let areas = try ["Farrowmere", "Cindermoor", "Alderwick", "Foxholt"].map(area)

        XCTAssertEqual(Results.tray([]).words, "No area chosen yet. Choose two to four.")
        XCTAssertNil(Results.tray([]).go)
        XCTAssertEqual(Results.tray(Array(areas.prefix(1))).words, "One area chosen. Choose at least one more.")
        XCTAssertNil(Results.tray(Array(areas.prefix(1))).go)
        XCTAssertNil(Results.tray(Array(areas.prefix(2))).words)
        XCTAssertEqual(Results.tray(Array(areas.prefix(2))).go, "Compare 2 areas")
        XCTAssertEqual(Results.tray(Array(areas.prefix(3))).go, "Compare 3 areas")
        XCTAssertEqual(Results.tray(areas).words, "Four areas is the most. Remove one to add another.")
        XCTAssertEqual(Results.tray(areas).go, "Compare 4 areas")
        XCTAssertTrue(Results.tray(areas).full)
    }

    @MainActor
    func test_every_card_and_every_row_can_be_added_and_the_button_says_what_it_would_do() async throws {
        let app = try await ResultsApp.searched()
        let cards = app.listed.cards

        app.hands.toggleCompare(cards[0].area)
        app.hands.toggleCompare(cards[7].area)

        XCTAssertEqual(app.memory.compare, [cards[0].area, cards[7].area])
        XCTAssertTrue(app.memory.isCompared(cards[0].area))
        XCTAssertFalse(app.memory.isCompared(cards[1].area))
        XCTAssertTrue(app.hands.canToggleCompare(cards[1].area))
        app.hands.toggleCompare(cards[1].area)
        app.hands.toggleCompare(cards[2].area)
        // When four are chosen the buttons that would add a fifth are switched off.
        XCTAssertFalse(app.hands.canToggleCompare(cards[3].area))
        XCTAssertTrue(app.hands.canToggleCompare(cards[0].area))
        app.hands.toggleCompare(cards[3].area)
        XCTAssertEqual(app.memory.compare.count, 4)
        // Choosing sends nothing.
        XCTAssertEqual(app.api.calls(to: .compare).count, 0)
        XCTAssertEqual(app.api.calls(to: .rank).count, 1)
    }

    @MainActor
    func test_what_is_kept_of_an_area_to_compare_is_its_ids_and_names_and_nothing_of_the_search() async throws {
        let app = try await ResultsApp.searched()

        app.hands.toggleCompare(try app.firstCard().area)

        let kept = try XCTUnwrap(app.memory.compare.first)
        XCTAssertEqual(Mirror(reflecting: kept).children.compactMap(\.label), ["areaId", "slug", "name", "borough"])
        // Nothing is written to the phone.
        XCTAssertNil(app.storage.read(.shortlist))
    }

    @MainActor
    func test_starting_the_search_again_leaves_the_areas_to_compare_as_they_are() async throws {
        let app = try await ResultsApp.searched()
        app.hands.toggleCompare(app.listed.cards[0].area)
        app.hands.toggleCompare(app.listed.cards[1].area)

        app.flow.startAgain()

        XCTAssertEqual(app.memory.compare.count, 2)
        XCTAssertEqual(app.memory.compared(among: app.state.areas).count, 2)
        XCTAssertEqual(app.memory.compared(among: []).count, 0)
    }

    @MainActor
    func test_what_is_kept_for_a_search_is_there_when_the_screen_is_made_again() async throws {
        let app = try await ResultsApp.searched()
        let other = try await ResultsApp()

        let memory = app.app.results
        memory.compare = [try area("Farrowmere")]
        memory.showing = .table

        XCTAssertTrue(Results.Hands(app: app.app, search: app.search).memory === memory)
        XCTAssertEqual(Results.Hands(app: app.app, search: app.search).memory.showing, .table)
        XCTAssertFalse(other.app.results === memory)
        XCTAssertEqual(other.app.results.compare, [])
    }

    @MainActor
    func test_the_comparison_is_a_screen_of_its_own_and_the_way_back_is_to_the_results() async throws {
        let app = try await ResultsApp.searched()
        app.app.show(.results, in: .search)
        try ["Farrowmere", "Cindermoor"].map(area).forEach(app.hands.toggleCompare)

        app.hands.compare()
        app.hands.compare()

        XCTAssertEqual(app.app.searchPath, [.results, .compare])
        XCTAssertEqual(app.app.tab, .search)
        // The route names no area: what is compared is held in memory.
        XCTAssertEqual(Mirror(reflecting: Screen.compare).children.count, 0)
        app.hands.chooseOthers()
        XCTAssertEqual(app.app.searchPath, [.results])
        XCTAssertEqual(app.memory.compare.count, 2)
    }

    // MARK: - Asking

    @MainActor
    func test_a_comparison_is_asked_for_with_the_areas_chosen_and_the_spec_the_api_last_returned() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.compare, "compare-three"))
        let chosen = try ["Cindermoor", "Farrowmere", "Alderwick"].map(area)
        let comparison = Results.Comparison()

        await comparison.ask(chosen, of: app.search)

        XCTAssertEqual(
            try app.api.lastCall(to: .compare).body(as: CompareBody.self),
            CompareBody(areaIds: ["syn-n0003", "syn-n0006", "syn-n0001"], spec: app.state.spec))
        guard case .here(let compared) = comparison.answer else { return XCTFail("No comparison came.") }
        XCTAssertEqual(compared.places.map(\.name), ["Cindermoor", "Farrowmere", "Alderwick"])
        // The search is as it was.
        XCTAssertEqual(app.state.ranking?.ranked, Answers.ranked("rank-first").ranked)
    }

    @MainActor
    func test_the_same_question_is_not_asked_twice_and_a_changed_search_is_asked_again() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.compare, "compare-three"))
        let chosen = try ["Farrowmere", "Cindermoor"].map(area)
        let comparison = Results.Comparison()

        await comparison.ask(chosen, of: app.search)
        await comparison.ask(chosen, of: app.search)
        XCTAssertEqual(app.api.calls(to: .compare).count, 1)
        app.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        await app.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))
        await comparison.ask(chosen, of: app.search)

        XCTAssertEqual(app.api.calls(to: .compare).count, 2)
        XCTAssertEqual(
            try app.api.lastCall(to: .compare).body(as: CompareBody.self).spec,
            Answers.ranked("rank-refined").spec)
    }

    @MainActor
    func test_fewer_than_two_areas_are_not_asked_about() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.compare, "compare-invalid"))
        let comparison = Results.Comparison()

        await comparison.ask([try area("Farrowmere")], of: app.search)
        app.hands.toggleCompare(try area("Farrowmere"))
        app.hands.compare()

        XCTAssertEqual(app.api.calls(to: .compare).count, 0)
        XCTAssertFalse(app.hands.comparing)
        XCTAssertEqual(comparison.answer, .waiting)
    }

    @MainActor
    func test_a_comparison_that_fails_says_so_in_the_apis_words_and_can_be_tried_again() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.compare, "compare-area-not-found"))
        let chosen = try ["Farrowmere", "Cindermoor"].map(area)
        let comparison = Results.Comparison()

        await comparison.ask(chosen, of: app.search)

        let refusal = try Recorded.error("compare-area-not-found")
        XCTAssertEqual(
            comparison.answer,
            .failed(
                words: refusal.error.message,
                requestId: try Recorded.read("compare-area-not-found").headers["x-request-id"]))
        app.api.on(.compare, "compare-three")
        await comparison.ask(chosen, of: app.search, again: true)
        guard case .here = comparison.answer else { return XCTFail("No comparison came.") }
        XCTAssertEqual(app.api.calls(to: .compare).count, 2)
    }

    @MainActor
    func test_taking_an_area_out_leaves_the_comparison_when_too_few_are_left() async throws {
        let app = try await ResultsApp.searched()
        let chosen = try ["Farrowmere", "Cindermoor"].map(area)
        chosen.forEach(app.hands.toggleCompare)

        app.hands.compare()
        XCTAssertTrue(app.hands.comparing)
        app.hands.toggleCompare(chosen[0])

        XCTAssertFalse(app.hands.comparing)
        XCTAssertEqual(app.memory.compare, [chosen[1]])
        app.hands.toggleCompare(chosen[0])
        app.hands.compare()
        app.hands.chooseOthers()
        XCTAssertFalse(app.hands.comparing)
        XCTAssertEqual(app.memory.compare.count, 2)
    }

    // MARK: - The table

    @MainActor
    func test_the_rows_are_in_the_order_the_api_gave_them_with_one_cell_for_each_area() async throws {
        let app = try await ResultsApp.searched()
        let data: CompareData = try Recorded.data(.compare, "compare-three")

        let compared = Results.compared(data, in: app.state)

        XCTAssertEqual(compared.rows.map(\.label), data.rows.map(\.label))
        XCTAssertEqual(compared.rows.prefix(4).map(\.label), ["Journey", "Budget", "Leafy", "Quiet streets"])
        // How much a thing counts is said as a weight, and never as a share.
        XCTAssertEqual(
            compared.rows.prefix(4).map(\.countsFor), ["Weight 100", "Weight 80", "Weight 50", "Weight 50"])
        // A journey has a row of its own, and says where it is to in the API's name for the place.
        XCTAssertEqual(compared.rows.first?.to, "To Cindermoor Works")
        XCTAssertEqual(compared.rows.compactMap(\.to), ["To Cindermoor Works"])
        XCTAssertEqual(compared.rows.count, 10)
        for row in compared.rows {
            XCTAssertEqual(row.cells.map(\.area), ["Cindermoor", "Farrowmere", "Alderwick"])
        }
        XCTAssertFalse(compared.nothingCounts)
    }

    @MainActor
    func test_the_vibes_of_each_area_are_set_side_by_side_each_as_a_band_of_five() async throws {
        let app = try await ResultsApp.searched()
        let data: CompareData = try Recorded.data(.compare, "compare-three")

        let compared = Results.compared(data, in: app.state)

        XCTAssertEqual(compared.character.map(\.tagId), data.character.map(\.tagId))
        XCTAssertEqual(compared.character.map(\.name), Answers.meta.tags.map(\.label))
        let leafy = try XCTUnwrap(compared.character.first)
        XCTAssertEqual(leafy.name, "Leafy")
        XCTAssertEqual(leafy.cells.map(\.area), ["Cindermoor", "Farrowmere", "Alderwick"])
        // The vibes are of the release and of no search: an area the search left out has its band all the same.
        XCTAssertEqual(leafy.cells.map(\.vibe.band), ["band 2 of 5", "band 3 of 5", "band 5 of 5"])
        XCTAssertEqual(
            leafy.cells.map(\.vibe.plainly),
            ["on the low side here", "around the middle here", "among the most here"])
        for vibe in compared.character {
            for cell in vibe.cells {
                XCTAssertFalse(cell.vibe.sources.isEmpty, "\(vibe.name), \(cell.area)")
                XCTAssertNil(cell.vibe.asked)
                XCTAssertFalse(cell.vibe.reads.contains("%"))
            }
        }
    }

    @MainActor
    func test_a_cell_shows_the_slots_of_its_fact_and_what_it_adds_rounded_down() async throws {
        let app = try await ResultsApp.searched()
        let data: CompareData = try Recorded.data(.compare, "compare-three")

        let compared = Results.compared(data, in: app.state)

        let journey = compared.rows[0].cells
        XCTAssertEqual(
            journey[1].columns,
            [
                .init(name: "To", value: "Cindermoor Works"),
                .init(name: "How", value: "By public transport"),
                .init(name: "Typical minutes", value: "21"),
                .init(name: "Minutes if you just miss one", value: "26"),
                .init(name: "Your limit, in minutes", value: "30"),
                .init(name: "Under your limit by, in minutes", value: "9"),
            ])
        XCTAssertEqual(journey[0].adds, "Adds 31 of 100 to the fit")
        XCTAssertEqual(journey[1].adds, "Adds 25 of 100 to the fit")
        XCTAssertEqual(journey[0].sources.map(\.date), ["September 2026"])
        // A journey over its limit says by how much, and the area it left out adds nothing.
        XCTAssertEqual(journey[2].columns.last, .init(name: "Over your limit by, in minutes", value: "23"))
        XCTAssertNil(journey[2].adds)
        let budget = compared.rows[1].cells
        XCTAssertEqual(
            budget[1].columns,
            [
                .init(name: "Upper end of the range", value: "£1,300"),
                .init(name: "Your budget", value: "£1,700"),
                .init(name: "Under your budget by", value: "£400"),
            ])
        XCTAssertEqual(budget[2].columns.last, .init(name: "Over your budget by", value: "£225"))
        // An area that was left out has a figure and adds nothing.
        XCTAssertNil(budget[2].adds)
        XCTAssertNil(budget[2].none)
        // A vibe that counts is its band, the ends it is counted between, and what it was compared among.
        XCTAssertEqual(
            compared.rows[2].cells[0].columns,
            [
                .init(name: "Band, of five", value: "2"),
                .init(name: "Counted from", value: "least to most"),
                .init(name: "Areas compared in this release", value: "21"),
                .init(name: "Parts dated", value: "2025"),
            ])
    }

    @MainActor
    func test_a_cell_with_no_figure_says_why_and_shows_no_source() async throws {
        let app = try await ResultsApp.searched()
        let data: CompareData = try Recorded.data(.compare, "compare-three")

        let compared = Results.compared(data, in: app.state)

        // Nitrogen dioxide has no figure for Alderwick in this release.
        let none = try XCTUnwrap(compared.rows.first { $0.component == "feature:air_no2" }?.cells[2])
        XCTAssertEqual(none.area, "Alderwick")
        XCTAssertEqual(none.none, "No figure in this data")
        XCTAssertEqual(none.columns, [])
        XCTAssertEqual(none.sources, [])
        XCTAssertNil(none.adds)
        // A cell the API sent no fact for, of an area that was left out, says that it was not worked out.
        let journeys = try XCTUnwrap(data.rows.first)
        let bare = CompareData(
            areas: data.areas, character: [],
            rows: [
                CompareRow(
                    component: journeys.component, label: journeys.label, weight: journeys.weight,
                    place: journeys.place,
                    cells: journeys.cells.map { cell in
                        CompareCell(
                            areaId: cell.areaId, value: nil, percentile: nil, utility: nil,
                            contribution: nil, factId: cell.areaId == "syn-n0001" ? nil : cell.factId)
                    })
            ], facts: data.facts)
        let leftOut = Results.compared(bare, in: app.state).rows[0].cells[2]
        XCTAssertEqual(leftOut.none, "Not worked out: this area was left out before it was scored")
        XCTAssertEqual(leftOut.columns, [])
        XCTAssertEqual(leftOut.sources, [])
        XCTAssertNil(leftOut.adds)
        let missing = compared.rows.flatMap(\.cells).filter { $0.none == "No figure in this data" }
        XCTAssertEqual(
            missing.count,
            data.rows.flatMap(\.cells).filter { cell in
                guard let factId = cell.factId else {
                    return data.areas.first { $0.areaId == cell.areaId }?.status == .ranked
                }
                return data.facts.first { $0.factId == factId }?.template == .missing
            }.count)
    }

    @MainActor
    func test_each_area_says_its_status_in_words_and_where_it_stands_in_the_search() async throws {
        let api = StandIn.firstSearch().on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        let app = try await ResultsApp.searched(api)
        let data: CompareData = try Recorded.data(.compare, "compare-three")

        let compared = Results.compared(data, in: app.state)

        XCTAssertEqual(compared.basis, ResultsCopy.Compare.fromSearch)
        XCTAssertEqual(
            compared.places.map(\.status),
            ["Ranked", "Ranked", "Left out: a journey is longer than a firm limit"])
        XCTAssertEqual(compared.places.map(\.standing), ["Rank 1. Fit 77 of 100", "Rank 2. Fit 76 of 100", nil])
        XCTAssertEqual(compared.places.map(\.area?.slug), ["cindermoor", "farrowmere", "alderwick"])
    }

    @MainActor
    func test_with_no_search_open_the_areas_are_compared_on_the_usual_settings_and_none_has_a_standing() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.compare, "compare-two-defaults"))
        let chosen = try ["Farrowmere", "Cindermoor"].map(area)
        let comparison = Results.Comparison()

        await comparison.ask(chosen, of: app.search)

        guard case .here(let compared) = comparison.answer else { return XCTFail("No comparison came.") }
        XCTAssertEqual(try app.api.lastCall(to: .compare).body(as: CompareBody.self).spec, Answers.meta.defaults.rent)
        XCTAssertEqual(compared.basis, ResultsCopy.Compare.fromDefaultsRent)
        XCTAssertTrue(compared.places.allSatisfy { $0.standing == nil })
        await app.flow.setTenure(.buy)
        XCTAssertEqual(Results.basis(of: app.state), ResultsCopy.Compare.fromDefaultsBuy)
    }

    @MainActor
    func test_a_standing_is_shown_only_when_the_ranking_is_of_the_spec_that_was_sent() async throws {
        let app = try await ResultsApp.searched()
        let data: CompareData = try Recorded.data(.compare, "compare-three")
        var state = app.state
        state.specHash = "another"

        XCTAssertTrue(Results.compared(data, in: state).places.allSatisfy { $0.standing == nil })
        XCTAssertNotNil(Results.compared(data, in: app.state).places[0].standing)
    }

    @MainActor
    func test_recorded_crime_carries_its_caveat_word_for_word_and_is_never_called_safe() async throws {
        let app = try await ResultsApp.searched()
        let data: CompareData = try Recorded.data(.compare, "compare-crime")

        let compared = Results.compared(data, in: app.state)

        let crime = compared.rows.filter { $0.caveat != nil }
        XCTAssertFalse(crime.isEmpty)
        XCTAssertTrue(crime.allSatisfy { $0.caveat == "Recorded crime depends on what is reported, and locations are approximate." })
        XCTAssertEqual(compared.rows.filter { $0.caveat == nil }.count, compared.rows.count - crime.count)
        let contract = try Repository.text(Repository.root.appendingPathComponent("docs/design/contract.md"))
        XCTAssertTrue(contract.contains(ResultsCopy.crimeCaveat))
        for text in ResultsDrawn.all(in: compared).texts {
            XCTAssertFalse(text.lowercased().contains("safe"), text)
            XCTAssertFalse(text.lowercased().contains("dangerous"), text)
        }
    }

    func test_nothing_set_to_count_leaves_nothing_to_compare_the_areas_on() {
        let data = CompareData(
            areas: [
                ComparedArea(areaId: "syn-n0006", name: "Farrowmere", status: .ranked, counted: 0, present: 0),
                ComparedArea(areaId: "syn-n0003", name: "Cindermoor", status: .ranked, counted: 0, present: 0),
            ], character: [], rows: [], facts: [])

        let compared = Results.compared(data, in: SearchState(meta: Answers.meta, areas: Answers.areas))

        XCTAssertTrue(compared.nothingCounts)
        XCTAssertEqual(
            ResultsCopy.Compare.nothingCounts,
            "Nothing is set to count in this search, so there is nothing to compare the areas on.")
    }
}
