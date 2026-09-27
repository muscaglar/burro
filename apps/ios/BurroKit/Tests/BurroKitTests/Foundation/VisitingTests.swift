import XCTest

@testable import BurroKit

/// A search that is a visit: for somewhere to stay, and for no home. The API serves one
/// with no budget, no number of bedrooms and no kind of home, and the app shows it
/// without them. The app offers renting and buying, as it did, and offers no visit: one
/// comes to it in an answer, as when a sentence says one, an offer of one is taken or a
/// link to one is opened. Decided on 2026-09-26: docs/adr/0041.
///
/// `VisitTests` is of another thing: the whole of one person's visit to the app.
final class VisitingTests: XCTestCase {
    private let meta = Answers.meta
    /// What a visit starts from, as the API served it.
    private var visit: PreferenceSpec { meta.defaults.visit }
    /// The ranking of a visit, as it was recorded: somewhere buzzy, for a weekend.
    private let ranked = Answers.ranked("visiting/rank")
    /// The ranking of a search to rent that was made a visit: its journey stays.
    private let became = Answers.ranked("visiting/rank-becomes")

    private func sent(in scenario: String) throws -> JSON? {
        try JSON.read(XCTUnwrap(Recorded.read(scenario).sent))["operations"]
    }

    /// A search that somebody made: a place to reach and two vibes, which they asked for.
    /// - Parameter budget: What the record of its budget holds. What a visit starts from,
    ///   where none is handed.
    private func search(for tenure: Tenure, budget: Budget? = nil) -> PreferenceSpec {
        let asked = Answers.read("interpret-first").spec
        return PreferenceSpec(
            schemaVersion: visit.schemaVersion, tenure: tenure, budget: budget ?? visit.budget,
            commutes: asked.commutes, commuteCombine: visit.commuteCombine, ptBasis: visit.ptBasis,
            commuteWeight: visit.commuteWeight, weights: visit.weights, tags: asked.tags,
            areas: visit.areas, tenureFrom: .uiEdit, commuteCombineFrom: visit.commuteCombineFrom,
            ptBasisFrom: visit.ptBasisFrom, commuteWeightFrom: visit.commuteWeightFrom)
    }

    /// A visit whose record holds a budget. The API serves none, and refuses one that it
    /// is sent, so it is made here as a fault upstream might hand it.
    private var faulty: PreferenceSpec { search(for: .visit, budget: aRent) }

    /// A budget as a person might set one: an amount, a kind of home, a firm limit, and a
    /// weight that is more than anything asked of the place.
    private let aRent = Budget(amount: 1_900, segment: .bed1, strictness: .hard, weight: 1, provenance: .stated)

    /// The kinds of fact that are of what a home costs, or of a budget held against it.
    private let ofACost: Set<FactKind> = [.cost, .budgetFit]

    private func chips(_ spec: PreferenceSpec) -> [SearchChip] {
        SearchChips.of(
            spec, features: meta.features, tags: meta.tags, areas: Answers.areas,
            placeNames: ["syn-p0021": "Cindermoor Works"], assumed: [:])
    }

    /// A search on the stand-in whose sentence says a visit, as it was recorded.
    @MainActor
    private func visited() async -> OpenSearch {
        let search = OpenSearch(
            StandIn().on(.interpret, "visiting/interpret").on(.rank, "visiting/rank")
                .on(.explainTop, "visiting/explanations"))
        await search.flow.submitText("what was typed")
        return search
    }

    // MARK: - What the API serves

    func test_what_a_visit_starts_from_is_the_apis_and_holds_no_amount_and_a_budget_that_counts_for_nothing() {
        XCTAssertEqual(visit.tenure, .visit)
        XCTAssertTrue(visit.visiting)
        XCTAssertEqual(visit.commutes, [])
        XCTAssertEqual(visit.tags, [])
        // What it is ranked by where nothing is said is the API's, and is not what a renter starts from.
        XCTAssertFalse(visit.weights.isEmpty)
        XCTAssertNotEqual(visit.weights, meta.defaults.rent.weights)
        // Every visit the API answered with holds the budget a visit starts from, and no other.
        for spec in [visit, ranked.spec, became.spec, Answers.shared("visiting/share-opened").spec] {
            XCTAssertTrue(spec.visiting)
            XCTAssertNil(spec.budget.amount)
            XCTAssertEqual(spec.budget.weight, 0)
            XCTAssertEqual(spec.budget, visit.budget)
        }
        // A search for a home is no visit, and nor is a kind of search this build does not know.
        XCTAssertFalse(meta.defaults.rent.visiting)
        XCTAssertFalse(meta.defaults.buy.visiting)
        XCTAssertFalse(search(for: .unlisted("stay")).visiting)
        XCTAssertEqual(Tenure(rawValue: "visit"), .visit)
    }

    func test_no_area_of_a_visit_holds_a_fit_to_a_budget_and_none_is_left_out_for_a_cost() {
        for answer in [ranked, became, Answers.ranked("visiting/rank-usual")] {
            XCTAssertEqual(answer.ranked.compactMap(\.budget), [])
            XCTAssertFalse(answer.filtered.contains { $0.reason == .overBudget })
            XCTAssertFalse(answer.ranked.flatMap(\.contributions).contains { $0.component == "budget" })
        }
    }

    // MARK: - Its name, and what the app offers

    func test_a_visit_has_a_name_and_the_app_offers_renting_and_buying_as_it_did() throws {
        XCTAssertEqual(CodeCopy.tenure(.visit), "Visiting")
        XCTAssertEqual(SettingsForm.tenures, [.rent, .buy])
        XCTAssertEqual(SettingsForm.tenures.map(CodeCopy.tenure), ["Renting", "Buying"])
        XCTAssertEqual(SearchCopy.TenureChoice.legend, "Renting or buying")
        // The control draws what the form offers, and no choice of its own.
        let controls = try Repository.text(Written.search.appendingPathComponent("Controls.swift"))
        XCTAssertTrue(controls.contains("choices: SettingsForm.tenures.map { ($0, CodeCopy.tenure($0)) },"))
    }

    // MARK: - The chips

    func test_the_chips_of_a_visit_say_that_it_is_one_and_none_is_of_a_budget_or_of_a_home() {
        let started = chips(visit)
        let asked = chips(became.spec)

        XCTAssertEqual(started.map(\.kind), [.tenure, .usual])
        XCTAssertEqual(
            started.map(\.reads), ["Visiting assumed", "Usual settings: \(visit.weights.count) assumed"])
        XCTAssertEqual(asked.map(\.kind), [.tenure, .place("syn-p0021"), .usual])
        // A visit that a person chose is not marked as assumed.
        XCTAssertEqual(asked.first?.reads, "Visiting")
        XCTAssertEqual(chips(ranked.spec).first?.reads, "Visiting")
        XCTAssertTrue(chips(ranked.spec).map(\.reads).contains("Going out: towards Buzzy"))
        let homes = Segment.allCases.compactMap(CodeCopy.segment)
        for chip in started + asked + chips(ranked.spec) {
            XCTAssertFalse(chip.reads.contains("£"), chip.reads)
            XCTAssertFalse(homes.contains { chip.reads.contains($0) }, chip.reads)
        }
    }

    func test_no_chip_is_drawn_of_a_budget_whatever_the_record_of_a_visit_holds() {
        XCTAssertEqual(chips(faulty), chips(search(for: .visit)))
        XCTAssertFalse(chips(faulty).contains { $0.kind == .budget })
        // The same record in a search to rent is a chip, with its amount and its kind of home.
        XCTAssertEqual(
            chips(search(for: .rent, budget: aRent)).first { $0.kind == .budget }?.reads,
            "£1,900 a month, One bedroom, firm limit")
    }

    func test_nothing_is_said_of_a_budget_whatever_the_record_of_a_visit_holds() {
        var state = reduce(
            SearchState(meta: meta, areas: Answers.areas),
            .rankAnswered(Answers.ranked("rank-first"), sent: .none))

        // In a search to rent the budget is said to count most, and is a limit that can be loosened.
        state.spec = search(for: .rent, budget: aRent)
        XCTAssertEqual(state.spec.leads?.budget, true)
        XCTAssertEqual(Results.waysOut(of: state).map(\.act), [.edit(Edits.budgetStrictness(.soft))])

        // The same record in a visit is said of nothing, and nothing is offered of it.
        state.spec = faulty
        XCTAssertNil(state.spec.leads)
        XCTAssertEqual(Results.waysOut(of: state), [])
    }

    @MainActor
    func test_no_area_is_said_to_be_left_out_by_the_budget_of_a_visit() async throws {
        // One press added a firm budget to a search to rent, and the line counts what it left out.
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-by-model-long").on(.rank, "rank-one-press"))
        await search.flow.submitText("what was typed")
        await search.flow.chooseAll([0, 1, 6, 10, 11])
        var state = search.state
        XCTAssertEqual(state.spec.budget.strictness, .hard)
        XCTAssertNotNil(state.leftOutByTheBudget)

        // The search is then a visit, and whatever its record holds, nothing is counted.
        state.spec = faulty

        XCTAssertEqual(state.spec.budget.strictness, .hard)
        XCTAssertNil(state.leftOutByTheBudget)
    }

    // MARK: - The settings

    func test_the_settings_ask_nothing_of_a_budget_or_of_a_home_of_a_visit_and_say_why() throws {
        for spec in [visit, ranked.spec, became.spec, faulty] {
            XCTAssertFalse(SettingsForm.asksForABudget(spec))
        }
        XCTAssertTrue(SettingsForm.asksForABudget(meta.defaults.rent))
        XCTAssertTrue(SettingsForm.asksForABudget(meta.defaults.buy))
        XCTAssertTrue(SettingsForm.asksForABudget(Answers.ranked("visiting/rank-back").spec))
        XCTAssertEqual(SettingsForm.segments(for: .visit), [])
        XCTAssertEqual(
            SettingsCopy.Budget.notForAVisit,
            "You are visiting, so Burro does not ask what you can pay or what kind of home you want. "
                + "It ranks the areas by everything else you choose, such as the places you need to reach "
                + "and what you want around you.")
    }

    func test_the_control_of_the_budget_draws_the_line_in_the_place_of_everything_it_asks() throws {
        let controls = try Repository.text(Written.search.appendingPathComponent("Controls.swift"))
        let from = try XCTUnwrap(controls.range(of: "struct BudgetControl: View {"))
        let to = try XCTUnwrap(controls.range(of: "struct CommuteControl: View {"))
        let budget = controls[from.lowerBound..<to.lowerBound]
        let asked = try XCTUnwrap(budget.range(of: "private var asked: some View {"))

        // What is drawn is decided once, by what is tested, and the line is the only other thing.
        var last = budget.startIndex
        for step in [
            "var body: some View {", "if SettingsForm.asksForABudget(context.spec) {", "asked", "} else {",
            "HintLine(SettingsCopy.Budget.notForAVisit)",
        ] {
            let found = try XCTUnwrap(budget.range(of: step, range: last..<budget.endIndex), step)
            XCTAssertLessThan(found.lowerBound, asked.lowerBound, step)
            last = found.upperBound
        }
        // Everything that asks for an amount, a kind of home, a firm limit or a weight is under it.
        for control in ["amount(budget, tenure, version)", "Picker(", "CheckRow(", "WeightSlider(", "AmountControl("] {
            let found = try XCTUnwrap(budget.range(of: control), control)
            XCTAssertGreaterThan(found.lowerBound, asked.upperBound, control)
            XCTAssertEqual(budget.components(separatedBy: control).count - 1, 1, control)
        }
    }

    // MARK: - A result

    @MainActor
    func test_a_result_of_a_visit_draws_nothing_of_what_a_home_costs() async throws {
        let rented = try await ResultsApp.searched()
        let app = try await ResultsApp.searched(
            StandIn().on(.interpret, "visiting/interpret").on(.rank, "visiting/rank")
                .on(.explainTop, "visiting/explanations"))
        let reasons = Answers.explained("visiting/explanations")

        // A search to rent says what a home costs on its first result, and a visit does not.
        XCTAssertNotNil(try rented.firstCard().cost.value)
        XCTAssertNotNil(Results.scale(of: rented.state))
        XCTAssertEqual(app.state.spec, ranked.spec)
        let card = try app.firstCard()
        XCTAssertEqual(card.cost, .hidden)
        XCTAssertNil(Results.scale(of: app.state))
        XCTAssertEqual(Set(app.listed.cards.map(\.cost)), [.hidden])
        // The rest of the card is drawn as any card is, in the API's words.
        XCTAssertTrue(card.full)
        XCTAssertNotNil(card.station.value)
        XCTAssertEqual(card.reasons.value?.map(\.text), reasons.explanations[0].reasons.prefix(3).map(\.text))
        XCTAssertFalse(card.breakdown.isEmpty)
        XCTAssertFalse(card.breakdown.map(\.thing).contains(ResultsCopy.Breakdown.budget))
        // No fact of its reasons is of what a home costs, or of a budget.
        XCTAssertFalse(reasons.facts.isEmpty)
        XCTAssertEqual(reasons.facts.filter { ofACost.contains($0.kind) }, [])
    }

    @MainActor
    func test_no_cost_is_drawn_whatever_the_record_of_a_visit_holds_and_none_is_waited_for() async throws {
        let app = try await ResultsApp.searched()
        var state = app.state
        let first = try XCTUnwrap(state.ranking?.ranked.first)
        let detail = try XCTUnwrap(state.details[first.areaId])
        XCTAssertNotNil(Results.cost(in: detail, for: state.spec))

        state.spec = faulty

        XCTAssertEqual(Results.card(for: first, at: 0, in: state)?.cost, .hidden)
        XCTAssertNil(Results.cost(in: detail, for: state.spec))
        XCTAssertNil(Results.scale(of: state))
        // It is neither waited for nor said to be missing, while the area is still being read.
        state.details = [:]
        XCTAssertEqual(Results.card(for: first, at: 0, in: state)?.cost, .hidden)
        XCTAssertEqual(Results.card(for: first, at: 0, in: state)?.station, .waiting)
    }

    func test_the_card_draws_no_part_for_a_cost_that_is_hidden_and_no_title_of_one() throws {
        let view = try Repository.text(
            Repository.sources.appendingPathComponent("Features/Results/Views/ResultsCardView.swift"))

        let part = try XCTUnwrap(view.range(of: "part(ResultsCopy.Cost.title) {"))
        let unless = try XCTUnwrap(view.range(of: "if card.cost != .hidden {"))
        XCTAssertLessThan(unless.upperBound, part.lowerBound)
        // Nothing stands between the two: the part is what is left out.
        XCTAssertEqual(
            view[unless.upperBound..<part.lowerBound].trimmingCharacters(in: .whitespacesAndNewlines), "")
        XCTAssertEqual(view.components(separatedBy: "ResultsCopy.Cost.title").count - 1, 1)
    }

    // MARK: - A comparison, and a link

    func test_a_comparison_of_a_visit_has_a_row_for_its_journey_and_none_for_a_budget() throws {
        let data: CompareData = try Recorded.data(.compare, "visiting/compare")
        var state = reduce(SearchState(meta: meta, areas: Answers.areas), .rankAnswered(became, sent: .none))
        state.placeNames = ["syn-p0021": "Cindermoor Works"]

        let compared = Results.compared(data, in: state)

        XCTAssertEqual(compared.basis, ResultsCopy.Compare.fromSearch)
        XCTAssertEqual(compared.rows.map(\.label), data.rows.map(\.label))
        XCTAssertTrue(compared.rows.contains { $0.label == ResultsCopy.Breakdown.journey })
        XCTAssertFalse(compared.rows.contains { $0.component == "budget" })
        XCTAssertFalse(compared.rows.map(\.label).contains(ResultsCopy.Breakdown.budget))
        XCTAssertEqual(data.facts.filter { ofACost.contains($0.kind) }, [])
    }

    func test_a_link_to_a_visit_opens_as_one() {
        let shared = Answers.shared("visiting/share-opened")

        let state = reduce(
            SearchState(meta: meta, areas: Answers.areas),
            .shareAnswered(id: Answers.shareId(askedForIn: "visiting/share-opened"), shared))

        XCTAssertEqual(state.spec, shared.spec)
        XCTAssertTrue(state.spec.visiting)
        XCTAssertEqual(SearchChips.of(state).first?.reads, "Visiting")
        XCTAssertFalse(SearchChips.of(state).contains { $0.kind == .budget })
        XCTAssertFalse(SettingsForm.asksForABudget(state.spec))
        XCTAssertEqual(Set(Results.listed(state).cards.map(\.cost)), [.hidden])
    }

    // MARK: - Before anything is asked for

    func test_before_anything_is_asked_for_a_visit_is_what_the_api_served_for_one() {
        let opened = SearchState(meta: meta, areas: Answers.areas)

        let swapped = reduce(opened, .tenureSwapped(.visit))

        XCTAssertEqual(swapped.spec, meta.defaults.visit)
        XCTAssertTrue(swapped.untouched)
        XCTAssertNil(swapped.specHash)
        XCTAssertEqual(swapped.answers, opened.answers + 1)
        XCTAssertTrue(SearchScreen.isWhereASearchStarts(swapped))
        XCTAssertEqual(SearchScreen.chipsTitle(swapped, waiting: false), SearchCopy.Chips.startLabel)
        // And back to a search for a home, as that was served.
        XCTAssertEqual(reduce(swapped, .tenureSwapped(.rent)).spec, meta.defaults.rent)
        XCTAssertEqual(reduce(swapped, .tenureSwapped(.buy)).spec, meta.defaults.buy)
        // A visit that holds what a person asked for is no longer where a search starts.
        var asked = swapped
        asked.spec = became.spec
        XCTAssertFalse(SearchScreen.isWhereASearchStarts(asked))
    }

    @MainActor
    func test_the_usual_settings_of_a_visit_are_ranked_as_the_api_served_them() async throws {
        let search = OpenSearch(StandIn().on(.rank, "visiting/rank-usual").on(.explainTop, "visiting/explanations"))

        await search.flow.setTenure(.visit)
        XCTAssertEqual(search.api.calls.count, 0)
        await search.flow.rankNow()

        let asked = try search.api.lastCall(to: .rank)
        XCTAssertEqual(try asked.body(as: RankBody.self), RankBody(spec: meta.defaults.visit, limit: 20))
        // It is the request the service was sent when the answer was recorded.
        XCTAssertEqual(asked.body, try JSON.read(XCTUnwrap(Recorded.read("visiting/rank-usual").sent)))
        XCTAssertEqual(search.state.spec, meta.defaults.visit)
        XCTAssertEqual(search.shown().chips.map(\.kind), [.tenure, .usual])
    }

    func test_a_comparison_with_no_search_open_says_that_it_is_on_the_usual_settings_of_a_visit() {
        let swapped = reduce(SearchState(meta: meta, areas: Answers.areas), .tenureSwapped(.visit))
        var asked = swapped
        asked.untouched = false

        XCTAssertEqual(
            Results.basis(of: swapped),
            "No search is open, so these areas are compared on the usual settings for visiting. "
                + "A search of your own puts the rows in the order of what counts most to you.")
        XCTAssertEqual(Results.basis(of: asked), ResultsCopy.Compare.fromSearch)
        // It is the line of a search to rent, of a visit.
        XCTAssertEqual(
            ResultsCopy.Compare.fromDefaultsVisit,
            ResultsCopy.Compare.fromDefaultsRent.replacingOccurrences(of: "for renting", with: "for visiting"))
    }

    // MARK: - How a search becomes one

    func test_a_search_is_made_a_visit_by_one_edit_that_names_no_amount_and_no_kind_of_home() throws {
        let edit = Edits.tenure(.visit)

        XCTAssertEqual(edit.count, 1)
        XCTAssertEqual(edit.budgetOps.map(\.tenure), [.visit])
        XCTAssertEqual(edit.budgetOps.map(\.action), [.set])
        XCTAssertEqual(edit.budgetOps.map(\.amount), [0])
        XCTAssertEqual(edit.budgetOps.map(\.segment), [.unchanged])
        XCTAssertEqual(edit.budgetOps.map(\.strictness), [.unchanged])
        XCTAssertEqual(edit.said(.budgetOps, 0), [Said(key: .tenure, states: [.tenure])])
        // It is written as the website writes it, and so is the edit that makes a visit a search to rent.
        XCTAssertEqual(try JSON.written(edit), try sent(in: "visiting/rank-becomes"))
        XCTAssertEqual(try JSON.written(Edits.tenure(.rent)), try sent(in: "visiting/rank-back"))
    }

    @MainActor
    func test_a_sentence_that_says_a_visit_makes_the_search_one() async throws {
        let read = Answers.read("visiting/interpret")

        let search = await visited()

        // The rules read it of a plain sentence, and applied it: nothing was offered.
        XCTAssertEqual(read.suggestions, [])
        XCTAssertEqual(read.operations.budgetOps.map(\.tenure), [.visit])
        XCTAssertEqual(search.api.routes.first, .interpret)
        // It is ranked once, as the API read it. The reasons are asked for beside the ranking.
        XCTAssertEqual(search.api.calls(to: .rank).count, 1)
        XCTAssertEqual(try search.api.lastCall(to: .rank).body(as: RankBody.self).spec, read.spec)
        XCTAssertEqual(search.state.spec, ranked.spec)
        let shown = search.shown()
        XCTAssertEqual(shown.chips.first?.reads, "Visiting")
        XCTAssertFalse(shown.chips.contains { $0.kind == .budget })
        XCTAssertNil(shown.offers)
        XCTAssertTrue(shown.hasRanking)
        XCTAssertNotEqual(search.state.leads?.budget, true)
    }

    @MainActor
    func test_an_offer_of_a_visit_is_drawn_in_the_apis_words_and_a_press_sends_its_edit() async throws {
        let read = Answers.read("visiting/interpret-said")
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "visiting/interpret-said").on(.rank, "visiting/rank-becomes"))
        await search.flow.submitText("what was typed")
        let offer = try XCTUnwrap(search.shown().offers?.offers.first)

        XCTAssertEqual(search.shown().offers?.offers.map(\.name), ["Visiting", "Leafy"])
        XCTAssertEqual(offer.does, read.suggestions[0].does)
        XCTAssertEqual(offer.does, "Look for somewhere to stay on a visit.")
        XCTAssertEqual(offer.follows, [read.suggestions[0].follows])
        XCTAssertEqual(offer.choices.map(\.label), ["Set", "Skip"])
        XCTAssertEqual(offer.choices.map(\.guess), [true, false])
        // Nothing of it is applied until it is pressed.
        XCTAssertEqual(search.state.spec, meta.defaults.rent)
        XCTAssertEqual(search.api.calls(to: .rank).count, 0)

        await search.flow.choose(at: 0, id: "more")

        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(asked, read.suggestions[0].choices[0].operations)
        XCTAssertEqual(asked, Edits.tenure(.visit))
        XCTAssertEqual(search.state.spec, became.spec)
        XCTAssertEqual(search.shown().chips.first?.reads, "Visiting")
        XCTAssertEqual(search.shown().offers?.offers.map(\.name), ["Leafy"])
    }

    @MainActor
    func test_a_search_for_a_home_becomes_a_visit_and_either_choice_the_app_offers_makes_it_one_for_a_home()
        async throws
    {
        let search = OpenSearch(
            StandIn.firstSearch().inTurn(.rank, "rank-first", "visiting/rank-becomes", "visiting/rank-back"))
        await search.flow.submitText("leafy and quiet")
        XCTAssertEqual(search.state.spec.tenure, .rent)
        XCTAssertTrue(search.shown().chips.contains { $0.kind == .budget })

        await search.flow.setTenure(.visit)

        // What was asked for of the journeys is kept, and the budget and the home are dropped.
        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self).operations, Edits.tenure(.visit))
        XCTAssertEqual(search.state.spec, became.spec)
        XCTAssertEqual(search.shown().chips.map(\.kind), [.tenure, .place("syn-p0021"), .usual])
        XCTAssertFalse(SettingsForm.asksForABudget(search.state.spec))
        XCTAssertEqual(Set(Results.listed(search.state).cards.map(\.cost)), [.hidden])

        await search.flow.setTenure(.rent)

        // It takes the usual budget of renting, with no amount, and is asked for one again.
        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self).operations, Edits.tenure(.rent))
        XCTAssertEqual(search.state.spec, Answers.ranked("visiting/rank-back").spec)
        XCTAssertNil(search.state.spec.budget.amount)
        XCTAssertEqual(search.shown().chips.first?.reads, "Renting")
        XCTAssertTrue(SettingsForm.asksForABudget(search.state.spec))
    }

    func test_nothing_is_said_of_the_rents_a_budget_is_held_against_where_the_search_is_a_visit() throws {
        // A release whose rents are of a postcode district or of a borough says so of a search to rent.
        let meta: MetaData = try Recorded.data(.getMeta, "let/meta")
        var state = SearchState(meta: meta, areas: Answers.areas)
        XCTAssertEqual(state.spec.tenure, .rent)
        XCTAssertNotNil(state.rentsHeldAgainst)

        state.spec = meta.defaults.visit

        XCTAssertNil(state.rentsHeldAgainst)
        XCTAssertNil(state.spec.leads)
    }
}
