import XCTest

@testable import BurroKit

/// Every figure the results screen shows is one the API sent.
///
/// A figure is any piece of text that holds a digit, and any whole number a
/// view is handed. Each must be a slot of a fact, a sentence, a name or a date
/// the API sent, or site copy with a number of the API's in its gap, which is
/// worked out here again from the answer itself, by other arithmetic.
final class ResultsFiguresTests: XCTestCase {
    /// Every search there is a recording of: its ranking, and the reasons for it.
    private let searches: [(read: String, rank: String, explain: String)] = [
        ("interpret-first", "rank-first", "explanations-first"),
        ("interpret-first", "rank-refined", "explanations-refined"),
        ("interpret-buyer-family", "rank-buyer-family", "explanations-buyer-family"),
        ("interpret-by-the-river", "rank-by-the-river", "explanations-by-the-river"),
        ("interpret-nights-out", "rank-nights-out", "explanations-nights-out"),
        ("interpret-two-journeys", "rank-two-journeys", "explanations-two-journeys"),
        ("interpret-second-sentence", "rank-second-sentence", "explanations-second-sentence"),
        ("interpret-first", "rank-on-foot", "explanations-on-foot"),
    ]

    @MainActor
    private func searched(_ search: (read: String, rank: String, explain: String)) async throws -> ResultsApp {
        let api = StandIn()
            .on(.interpret, StandIn.withTheSpecSent(search.read))
            .on(.rank, search.rank)
            .on(.explainTop, search.explain)
        let app = try await ResultsApp(api)
        await app.flow.loadGeometry()
        await app.flow.rankNow()
        return app
    }

    // MARK: - What may be said

    /// A number of the API's as a whole number of hundredths, rounded down, by decimal arithmetic.
    private func floorOfHundred(_ value: Double) -> Int {
        var hundred = Decimal(string: "\(value)")! * 100
        var floored = Decimal()
        NSDecimalRound(&floored, &hundred, 0, .down)
        return NSDecimalNumber(decimal: floored).intValue
    }

    private func floorOf(_ value: Double) -> Int {
        var decimal = Decimal(string: "\(value)")!
        var floored = Decimal()
        NSDecimalRound(&floored, &decimal, 0, .down)
        return NSDecimalNumber(decimal: floored).intValue
    }

    /// Everything a card of one area may say that holds a digit.
    private func allowed(for ranked: RankedArea, in state: SearchState) throws -> Set<String> {
        let areaId = ranked.areaId
        let facts =
            state.facts.values.filter { $0.areaId == areaId || $0.kind == .travel }
            + (state.details[areaId]?.facts ?? [])
        var said = ResultsSaid.by(facts)
        said.formUnion(ResultsSaid.by(state.explanations.filter { $0.areaId == areaId }))
        said.formUnion(ResultsSaid.by(state.meta, state.areas))

        // Site copy, with a number of the API's in its gap.
        let fit = floorOf(ranked.score)
        said.insert("\(fit) of 100")
        said.insert("Rank \(ranked.rank)")
        for leg in ranked.legs {
            for minutes in [leg.minutesTypical, leg.minutesJustMissed].compactMap({ $0 }) {
                said.insert("\(minutes) minutes")
            }
            if let cutoff = Results.cutoff(for: leg.mode, in: state.meta.limits.cutoffMinutes) {
                said.insert("More than \(cutoff) minutes")
            }
        }
        for (at, commute) in state.spec.commutes.enumerated() {
            said.insert("\(commute.maxMinutes) minutes")
            said.insert("Within your limit of \(commute.maxMinutes) minutes")
            said.insert("Over your limit of \(commute.maxMinutes) minutes")
            said.insert("Place \(at + 1)")
            // A place the app was never told the name of is named by its number, in a line that names it.
            said.insert(ResultsCopy.Journeys.usesOne("Place \(at + 1)"))
        }
        let asked = ranked.contributions.count
        let present = ranked.contributions.filter(\.present).count
        said.insert("Based on \(present) of the \(asked) things that count in your search")
        for contribution in ranked.contributions {
            said.insert("\(Int((contribution.weight * 100).rounded())) of 100")
            said.insert("\(floorOfHundred(contribution.share))%")
            said.insert("\(floorOfHundred(contribution.contribution)) of 100")
            if let utility = contribution.utility { said.insert("\(floorOfHundred(utility)) of 100") }
        }
        // The person's own budget, as the spec the API returned holds it.
        if let amount = state.spec.budget.amount {
            let formatter = NumberFormatter()
            formatter.numberStyle = .decimal
            formatter.locale = Locale(identifier: "en_GB")
            said.insert("£" + (try XCTUnwrap(formatter.string(from: NSNumber(value: amount)))))
        }
        return said
    }

    // MARK: - The cards

    @MainActor
    func test_every_figure_on_every_card_of_every_recorded_search_is_one_the_api_sent() async throws {
        var cards = 0
        for search in searches {
            let app = try await searched(search)
            let ranking = try XCTUnwrap(app.state.ranking)
            XCTAssertTrue(app.state.explained, search.rank)
            for card in app.listed.cards {
                let ranked = try XCTUnwrap(ranking.ranked.first { $0.areaId == card.id })
                let allowed = try allowed(for: ranked, in: app.state)
                let strangers = ResultsDrawn.figures(in: card).filter { !allowed.contains($0) }
                XCTAssertEqual(strangers, [], "\(search.rank), rank \(ranked.rank)")
                cards += 1
            }
        }
        XCTAssertGreaterThan(cards, 100)
    }

    @MainActor
    func test_every_whole_number_a_card_holds_is_the_apis_own_rounded_down() async throws {
        for search in searches {
            let app = try await searched(search)
            let ranking = try XCTUnwrap(app.state.ranking)
            for card in app.listed.cards {
                let ranked = try XCTUnwrap(ranking.ranked.first { $0.areaId == card.id })
                for number in ResultsDrawn.all(in: card).numbers {
                    switch number.label {
                    case "rank": XCTAssertEqual(number.value, ranked.rank)
                    case "fit": XCTAssertEqual(number.value, floorOf(ranked.score))
                    case "covered":
                        // The bar draws what the words count: how many of the things that count have a figure.
                        let present = ranked.contributions.filter(\.present).count
                        XCTAssertEqual(number.value, present * 100 / ranked.contributions.count)
                    case "held": XCTAssertEqual(number.value, 0)
                    case "pips": XCTAssertTrue((1...3).contains(number.value))
                    default: XCTFail("A card holds a number nothing accounts for: \(number.label)")
                    }
                }
            }
        }
    }

    @MainActor
    func test_a_fit_is_rounded_down_and_never_up() async throws {
        let app = try await ResultsApp.searched()
        let first = try XCTUnwrap(app.state.ranking?.ranked.first)

        // The recorded fit has a fraction to lose, and would round up to the next whole number.
        XCTAssertEqual(first.score, 80.99)
        XCTAssertEqual(try app.firstCard().heading.fit, 80)
        XCTAssertEqual(try app.firstCard().heading.fitWords, "80 of 100")
        XCTAssertEqual(Results.fit(of: 99.999), 99)
        XCTAssertEqual(Results.fit(of: 100), 100)
        XCTAssertEqual(Results.fit(of: 0.4), 0)
        XCTAssertEqual(Results.fit(of: -3), 0)
        XCTAssertEqual(Results.fit(of: 250), 100)
        XCTAssertEqual(Results.fit(of: .nan), 0)
        XCTAssertEqual(Results.hundredths(0.3175), 31)
        XCTAssertEqual(Results.hundredths(0.29), 29)
        XCTAssertEqual(Results.hundredths(1), 100)
        XCTAssertNil(Results.hundredths(nil))
        // The fit always falls in the band the legend gives for it.
        for score in stride(from: 0.0, through: 100.0, by: 0.37) {
            let band = Results.bands[Results.band(of: score) - 1]
            XCTAssertTrue((band.from...band.to).contains(Results.fit(of: score)), "\(score)")
        }
    }

    @MainActor
    func test_the_test_bites_a_figure_the_api_did_not_send_is_found() async throws {
        let app = try await ResultsApp.searched()
        let ranked = try XCTUnwrap(app.state.ranking?.ranked.first)
        let allowed = try allowed(for: ranked, in: app.state)
        let card = try app.firstCard()
        // A fit rounded up, a time made up, a percentile, and a number from another area's card.
        let other = try XCTUnwrap(app.listed.cards.last?.heading.fitWords)
        let wrong = [
            Results.Heading(rank: 1, name: "Farrowmere", borough: "Quillhaven", fit: 81).fitWords ?? "",
            ResultsCopy.Journeys.minutes(22), "56.8", other,
        ]

        for figure in wrong { XCTAssertFalse(allowed.contains(figure), figure) }
        XCTAssertEqual(ResultsDrawn.figures(in: card).filter { !allowed.contains($0) }, [])
        XCTAssertGreaterThan(ResultsDrawn.figures(in: card).count, 20)
    }

    @MainActor
    func test_no_card_shows_a_percentile_a_coverage_a_raw_value_or_an_id() async throws {
        let app = try await ResultsApp.searched()
        let drawn = ResultsDrawn.all(in: app.listed).texts + ResultsDrawn.all(in: app.mapped).texts
            + ResultsDrawn.all(in: app.tabled).texts
        let profile = try XCTUnwrap(app.state.details["syn-n0006"])

        for text in drawn {
            XCTAssertFalse(text.contains("syn-n"), text)
            XCTAssertFalse(text.contains("syn-p"), text)
            XCTAssertFalse(text.contains("/travel/"), text)
        }
        // What is served with no fact behind it has no source and no date, and is not shown.
        for feature in profile.features {
            if let percentile = feature.percentile { XCTAssertFalse(drawn.contains("\(percentile)")) }
            if let value = feature.value { XCTAssertFalse(drawn.contains("\(value)")) }
        }
        XCTAssertFalse(drawn.contains { $0.lowercased().contains("step-free") || $0.lowercased().contains("step free") })
        XCTAssertFalse(drawn.contains { $0.lowercased().contains("percentile") })
    }

    // MARK: - The map, the table and the comparison

    @MainActor
    func test_every_figure_on_the_map_and_in_the_table_is_a_rank_or_a_fit_of_the_ranking() async throws {
        for search in searches {
            let app = try await searched(search)
            let ranking = try XCTUnwrap(app.state.ranking)
            var allowed = ResultsSaid.by(app.state.meta, app.state.areas)
            for (at, score) in ranking.scores.enumerated() {
                let name = try XCTUnwrap(app.state.area(score.areaId)?.name)
                let fit = floorOf(score.score)
                allowed.insert("Fit \(fit)")
                allowed.insert("Rank \(at + 1), \(name), fit \(fit) of 100")
                allowed.insert("Rank \(at + 1), fit \(fit) of 100")
            }
            for band in [(0, 19), (20, 39), (40, 59), (60, 79), (80, 100)] {
                allowed.insert("Fit \(band.0) to \(band.1)")
            }

            XCTAssertEqual(ResultsDrawn.figures(in: app.mapped).filter { !allowed.contains($0) }, [], search.rank)
            for row in app.tabled.rows {
                let at = ranking.scores.firstIndex { $0.areaId == row.area.areaId }
                XCTAssertEqual(row.rank, at.map { $0 + 1 })
                XCTAssertEqual(row.fit, at.map { floorOf(ranking.scores[$0].score) })
            }
        }
    }

    @MainActor
    func test_every_figure_of_a_comparison_is_a_slot_of_a_fact_or_a_share_rounded_down() async throws {
        for scenario in ["compare-three", "compare-crime", "compare-two-defaults"] {
            let app = try await ResultsApp.searched()
            let data: CompareData = try Recorded.data(.compare, scenario)
            let compared = Results.compared(data, in: app.state)
            var allowed = ResultsSaid.by(data.facts)
            for row in data.rows {
                allowed.insert("Counts for \(Int((row.weight * 100).rounded())) of 100")
                for cell in row.cells {
                    if let adds = cell.contribution { allowed.insert("Adds \(floorOfHundred(adds)) of 100 to the fit") }
                }
            }
            for standing in Results.standings(app.state.ranking) {
                if let fit = standing.value.fit {
                    allowed.insert("Rank \(standing.value.rank). Fit \(fit) of 100")
                }
            }

            XCTAssertEqual(ResultsDrawn.figures(in: compared).filter { !allowed.contains($0) }, [], scenario)
            // The number in the cell itself is never shown: it is the same figure unformatted.
            let drawn = ResultsDrawn.all(in: compared).texts
            for cell in data.rows.flatMap(\.cells) {
                if let percentile = cell.percentile { XCTAssertFalse(drawn.contains("\(percentile)")) }
                if let utility = cell.utility, utility != 1 { XCTAssertFalse(drawn.contains("\(utility)")) }
            }
        }
    }
}
