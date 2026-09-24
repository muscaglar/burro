import XCTest

@testable import BurroKit

/// What the search that is open says of one area: where it stands, and why.
final class AreaInSearchTests: XCTestCase {
    @MainActor
    private func searched() async -> OpenSearch {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        return search
    }

    @MainActor
    func test_with_no_ranking_open_nothing_is_said_of_where_the_area_stands() {
        XCTAssertNil(AreaInSearch(OpenSearch().state, areaId: "syn-n0006"))
    }

    @MainActor
    func test_the_rank_and_the_fit_are_the_rankings_and_the_fit_is_rounded_down() async throws {
        let search = await searched()
        XCTAssertEqual(search.state.ranking?.ranked.first?.score, 78.52)

        let first = try XCTUnwrap(AreaInSearch(search.state, areaId: "syn-n0006"))

        XCTAssertEqual(first.rank, 1)
        XCTAssertEqual(first.fit, 78)
        XCTAssertEqual(first.standing, "Rank 1, fit 78 of 100")
        XCTAssertEqual(AreaInSearch.roundedDown(78.78), 78)
        // Never more than it is, however near: and the same on the area's screen as on a result.
        XCTAssertEqual(AreaInSearch.roundedDown(79.9999999999), 79)
        for score in [0, 0.5, 49.999999, 50, 78.78, 79.9999999999, 99.9999999999, 100, 100.4] {
            XCTAssertEqual(AreaInSearch.roundedDown(score), Results.fit(of: score), "\(score)")
        }
        XCTAssertEqual(AreaInSearch.roundedDown(100), 100)
        XCTAssertEqual(AreaInSearch.roundedDown(100.4), 100)
        XCTAssertEqual(AreaInSearch.roundedDown(-1), 0)
        XCTAssertNil(AreaInSearch.roundedDown(.nan))
    }

    @MainActor
    func test_an_area_beyond_the_first_twenty_still_has_its_place() async throws {
        let search = await searched()
        let scores = try XCTUnwrap(search.state.ranking?.scores)
        let last = try XCTUnwrap(scores.last)

        let said = try XCTUnwrap(AreaInSearch(search.state, areaId: last.areaId))

        XCTAssertEqual(said.rank, scores.count)
        XCTAssertFalse(said.explained)
        XCTAssertEqual(said.reasons, [])
    }

    @MainActor
    func test_an_area_the_search_left_out_has_no_place() async throws {
        let search = await searched()
        let ranked = Set(try XCTUnwrap(search.state.ranking?.scores).map(\.areaId))
        let out = try XCTUnwrap(Answers.areas.first { !ranked.contains($0.areaId) })

        XCTAssertNil(AreaInSearch(search.state, areaId: out.areaId))
    }

    @MainActor
    func test_the_sentences_are_the_apis_each_with_the_source_of_what_it_says() async throws {
        let search = await searched()
        let explanation = try XCTUnwrap(Answers.explained("explanations-first").explanations.first)

        let said = try XCTUnwrap(AreaInSearch(search.state, areaId: "syn-n0006"))

        XCTAssertTrue(said.explained)
        XCTAssertEqual(said.orientation?.text, "Farrowmere is in Quillhaven.")
        XCTAssertEqual(said.reasons.map(\.text), explanation.reasons.map(\.text))
        XCTAssertEqual(said.tradeOff?.text, explanation.tradeOff?.text)
        for sentence in said.reasons + [said.tradeOff, said.orientation].compactMap({ $0 }) {
            XCTAssertTrue(sentence.sourceWords?.hasPrefix("Source: Synthetic test data. Data from ") ?? false)
            XCTAssertFalse(sentence.byModel)
        }
        XCTAssertEqual(Set(said.reasons.map(\.id)).count, said.reasons.count)
    }

    @MainActor
    func test_reasons_that_are_not_for_the_ranking_on_screen_are_not_shown() async throws {
        let search = OpenSearch(StandIn.firstSearch().unreachable(.explainTop))
        await search.flow.submitText("leafy and quiet")

        let said = try XCTUnwrap(AreaInSearch(search.state, areaId: "syn-n0006"))

        XCTAssertFalse(search.state.explained)
        XCTAssertFalse(said.explained)
        XCTAssertNil(said.orientation)
        XCTAssertEqual(said.standing, "Rank 1, fit 78 of 100")
    }

    @MainActor
    func test_reasons_of_the_ranking_before_are_not_shown_under_the_ranking_on_screen() async throws {
        let search = await searched()
        search.api.on(.rank, "rank-refined").unreachable(.explainTop)

        await search.flow.applyEdits(Edits.tagOn(.leafy))

        XCTAssertFalse(search.state.explanations.isEmpty)
        XCTAssertNotEqual(search.state.explainedHash, search.state.rankedHash)
        let first = try XCTUnwrap(search.state.ranking?.ranked.first)
        let said = try XCTUnwrap(AreaInSearch(search.state, areaId: first.areaId))
        XCTAssertTrue(search.state.explanations.contains { $0.areaId == first.areaId })
        XCTAssertFalse(said.explained)
        XCTAssertEqual(said.reasons, [])
        XCTAssertNil(said.tradeOff)
    }

    @MainActor
    func test_with_nothing_set_to_rank_by_no_area_has_a_fit() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.rank, "rank-empty-spec"))
        await search.flow.rankNow()
        let first = try XCTUnwrap(search.state.ranking?.scores.first)

        let said = try XCTUnwrap(AreaInSearch(search.state, areaId: first.areaId))

        XCTAssertNil(said.fit)
        XCTAssertEqual(said.standing, "Rank 1")
    }

    @MainActor
    func test_a_sentence_a_model_wrote_says_so() async throws {
        let api = StandIn.firstSearch().on(
            .explainTop,
            .made { _ in
                try Recorded.read("explanations-first").with(data: { data in
                    guard case .array(var explanations) = data["explanations"] else { return }
                    explanations[0]["orientation"]?["origin"] = .string("model")
                    data["explanations"] = .array(explanations)
                })
            })
        let search = OpenSearch(api)
        await search.flow.submitText("leafy and quiet")

        let said = try XCTUnwrap(AreaInSearch(search.state, areaId: "syn-n0006"))

        XCTAssertEqual(said.orientation?.byModel, true)
        XCTAssertEqual(said.reasons.first?.byModel, false)
        XCTAssertEqual(AreaCopy.InSearch.byModel, "Written by AI, checked against the source")
    }
}
