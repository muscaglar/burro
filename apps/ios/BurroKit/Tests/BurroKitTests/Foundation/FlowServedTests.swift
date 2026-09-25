import XCTest

@testable import BurroKit

/// What the flow does so that what is on screen is of one release, that no
/// card is left waiting in silence, and that "Stop" puts the search back.
/// Each is a test of the website's, in `apps/web/src/lib/search/flow.test.ts`,
/// under the same name where the two share one.
final class FlowServedTests: XCTestCase {
    /// The release a service moves to, after the search was opened on the recorded one.
    private let newer = Answers.newerRelease
    private let first = (
        read: Answers.read("interpret-first"),
        rank: Answers.ranked("rank-first"),
        explain: Answers.explained("explanations-first")
    )

    // MARK: - Stopping after the words were read

    /// A search that is on screen, and a second sentence that has been read and is being ranked.
    @MainActor
    private func readAndHeld() async -> (search: OpenSearch, before: SearchState, ranking: StandIn.Gate) {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        let before = search.state
        search.api.on(.interpret, "interpret-second-sentence").on(.explainTop, "explanations-second-sentence")
        let ranking = search.api.hold(.rank, "rank-second-sentence")
        return (search, before, ranking)
    }

    @MainActor
    func test_stop_is_still_offered_while_the_ranking_of_the_words_is_worked_out() async {
        let (search, _, ranking) = await readAndHeld()
        async let sent: Void = search.flow.submitText("a bit more green space")
        await until { ranking.waiting > 0 }

        // The words are read, and the chips are drawn from them already.
        XCTAssertEqual(search.state.phase, .interpreting)
        XCTAssertEqual(search.state.specHash, Answers.read("interpret-second-sentence").specHash)
        XCTAssertNotNil(search.state.kept)
        ranking.release()
        await sent
        XCTAssertNil(search.state.kept)
    }

    @MainActor
    func test_stop_puts_the_search_back_as_it_was_and_the_late_ranking_changes_nothing() async {
        let (search, before, ranking) = await readAndHeld()
        async let sent: Void = search.flow.submitText("a bit more green space")
        await until { ranking.waiting > 0 }

        await search.flow.stop()
        // The ranking was already on its way, and comes after all.
        ranking.release()
        await sent

        XCTAssertEqual(search.state.phase, .results)
        XCTAssertEqual(search.state.spec, before.spec)
        XCTAssertEqual(search.state.specHash, search.state.rankedHash)
        XCTAssertEqual(search.state.rankedHash, first.rank.specHash)
        XCTAssertEqual(search.state.read, before.read)
        XCTAssertEqual(search.state.assumed, before.assumed)
        XCTAssertEqual(search.state.ranking, before.ranking)
        XCTAssertTrue(search.state.reasonsAreIn)
        XCTAssertNil(search.state.explanationsAhead)
        XCTAssertNil(search.state.failure)
        XCTAssertEqual(search.state.pending, .none)
        XCTAssertEqual(search.api.calls(to: .rank).count, 2)
        XCTAssertEqual(search.api.unexpected.count, 0)
    }

    @MainActor
    func test_the_next_sentence_after_stop_is_sent_with_the_spec_that_was_put_back() async throws {
        let (search, before, ranking) = await readAndHeld()
        async let sent: Void = search.flow.submitText("a bit more green space")
        await until { ranking.waiting > 0 }
        await search.flow.stop()
        ranking.release()
        await sent
        search.api.on(.rank, "rank-second-sentence")

        await search.flow.submitText("a bit more green space")

        XCTAssertEqual(try search.api.lastCall(to: .interpret).body(as: InterpretBody.self).spec, before.spec)
    }

    @MainActor
    func test_an_edit_made_meanwhile_is_sent_after_stop_with_the_spec_that_was_put_back() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        let before = search.state
        let reading = search.api.hold(.interpret, "interpret-second-sentence")
        search.api.on(.explainTop, "explanations-second-sentence")
        let ranking = StandIn.Gate()
        search.api.inTurn(
            .rank,
            [
                .made { _ in
                    try await ranking.hold()
                    return try Recorded.read("rank-second-sentence")
                },
                .recorded("rank-refined"),
            ])
        let edit = Edits.placeStrictness("syn-p0021", .hard)

        async let sent: Void = search.flow.submitText("a bit more green space")
        await until { reading.waiting > 0 }
        async let edited: Void = search.flow.applyEdits(edit)
        await until { !search.state.pending.isEmpty }
        reading.release()
        await until { ranking.waiting > 0 }
        search.api.on(.explainTop, "explanations-refined")
        await search.flow.stop()
        ranking.release()
        _ = await (sent, edited)

        // The sentence is undone, and the control that was moved is not.
        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self),
            RankBody(spec: before.spec, limit: 20, operations: edit))
        XCTAssertEqual(search.state.spec, Answers.ranked("rank-refined").spec)
        XCTAssertEqual(search.state.specHash, search.state.rankedHash)
        XCTAssertEqual(search.state.pending, .none)
    }

    @MainActor
    func test_stop_on_a_first_search_leaves_the_search_as_it_opened() async {
        let api = StandIn.firstSearch()
        let ranking = api.hold(.rank, "rank-first")
        let search = OpenSearch(api)

        async let sent: Void = search.flow.submitText("leafy")
        await until { ranking.waiting > 0 }
        await search.flow.stop()
        ranking.release()
        await sent

        XCTAssertEqual(search.state.phase, .empty)
        XCTAssertEqual(search.state.spec, Answers.meta.defaults.rent)
        XCTAssertNil(search.state.read)
        XCTAssertNil(search.state.ranking)
        XCTAssertNil(search.state.specHash)
        XCTAssertEqual(search.state.explanations, [])
    }

    // MARK: - Reasons and profiles that cannot be loaded

    @MainActor
    func test_reasons_that_cannot_be_loaded_keep_the_apis_message_and_the_id_to_quote() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.explainTop, "error-internal"))

        await search.flow.submitText("leafy")

        let fault = try Recorded.error("error-internal")
        let failure = try XCTUnwrap(search.state.failureOfTheCards?.api)
        XCTAssertEqual(failure.status, 500)
        XCTAssertEqual(failure.code, .internalError)
        XCTAssertEqual(failure.message, fault.error.message)
        XCTAssertEqual(failure.requestId, try Recorded.read("error-internal").headers["x-request-id"])
        XCTAssertNotNil(failure.requestId)
        XCTAssertNil(search.state.failure)
        XCTAssertEqual(search.state.ranking?.ranked, first.rank.ranked)
        // It was asked for once. A failure is said, and is not tried again behind the person's back.
        XCTAssertEqual(search.api.calls(to: .explainTop).count, 1)
    }

    @MainActor
    func test_trying_again_brings_the_reasons_that_could_not_be_loaded() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.explainTop, "error-internal"))
        await search.flow.submitText("leafy")
        search.api.forgetCalls()
        search.api.on(.explainTop, "explanations-first")

        await search.flow.retry()

        XCTAssertEqual(search.api.calls(to: .explainTop).count, 1)
        XCTAssertEqual(
            try search.api.lastCall(to: .explainTop).body(as: ExplanationsBody.self),
            ExplanationsBody(spec: first.rank.spec, limit: 5))
        XCTAssertTrue(search.state.reasonsAreIn)
        XCTAssertEqual(search.state.explanations, first.explain.explanations)
        XCTAssertNil(search.state.failureOfTheCards)
        // The profiles were in hand, and are not asked for again.
        XCTAssertEqual(search.api.calls(to: .getArea).count, 0)
        XCTAssertEqual(search.state.phase, .results)
        XCTAssertEqual(search.api.unexpected.count, 0)
    }

    @MainActor
    func test_a_profile_that_cannot_be_loaded_is_kept_whole_and_the_rest_are_kept() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.getArea, Self.profiles(but: "area-not-found")))

        await search.flow.submitText("leafy")

        XCTAssertEqual(Array(search.state.detailFailures.keys), ["syn-n0006"])
        XCTAssertEqual(search.state.details.count, 4)
        // The failure is kept whole, with the API's own words for it.
        let refusal = try Recorded.error("area-not-found")
        let failure = try XCTUnwrap(search.state.failureOfTheCards?.api)
        XCTAssertEqual(failure.code, .areaNotFound)
        XCTAssertEqual(failure.message, refusal.error.message)
        XCTAssertEqual(failure.requestId, try Recorded.read("area-not-found").headers["x-request-id"])
    }

    @MainActor
    func test_trying_again_asks_for_the_profile_that_failed_and_for_no_other() async {
        let search = OpenSearch(StandIn.firstSearch().on(.getArea, Self.profiles(but: "error-internal")))
        await search.flow.submitText("leafy")
        XCTAssertEqual(Array(search.state.detailFailures.keys), ["syn-n0006"])
        search.api.forgetCalls()
        search.api.on(.getArea, .profiles)

        await search.flow.retry()

        XCTAssertEqual(search.api.calls(to: .getArea).map(\.path), ["/v1/areas/farrowmere"])
        XCTAssertEqual(search.state.detailFailures, [:])
        XCTAssertEqual(search.state.details.count, 5)
        XCTAssertNil(search.state.failureOfTheCards)
    }

    @MainActor
    func test_reasons_that_could_not_leave_are_asked_for_again_when_the_phone_is_back() async {
        let search = OpenSearch()
        await search.flow.submitText("leafy")
        // The connection goes between a ranking and its reasons.
        search.api.on(.rank, "rank-refined").unreachable(.explainTop, .notConnectedToInternet)
        await search.flow.applyEdits(Edits.placeStrictness("syn-p0021", .hard))
        XCTAssertEqual(search.state.rankedHash, Answers.ranked("rank-refined").specHash)
        XCTAssertEqual(search.state.reasonsFailure, .because(.offline))
        XCTAssertFalse(search.state.online)
        XCTAssertEqual(search.state.failurePlace, .offline)

        search.api.on(.rank, StandIn.withTheSpecSent("rank-refined")).on(.explainTop, "explanations-refined")
        await search.flow.wentOnline()

        XCTAssertTrue(search.state.online)
        XCTAssertTrue(search.state.reasonsAreIn)
        XCTAssertNil(search.state.failureOfTheCards)
    }

    /// Every profile as it was recorded, but Farrowmere's, which is answered with an error.
    private static func profiles(but error: String) -> StandIn.Responder {
        .made { call in
            let slug = call.path.split(separator: "/").last ?? ""
            return try Recorded.read(slug == "farrowmere" ? error : "area/\(slug)")
        }
    }

    // MARK: - A release that changes while the app is open

    @MainActor
    func test_a_first_search_after_a_release_keeps_its_reasons_and_profiles_when_the_form_comes_last() async {
        // The form is read again beside the search, and is the largest thing asked for: it may well come last.
        let api = StandIn.firstSearch().movedTo(newer)
        let slow = api.hold(.getMeta, "meta")
        let search = OpenSearch(api)

        await search.flow.submitText("leafy")
        XCTAssertEqual(search.state.explanations.count, 5)
        XCTAssertEqual(search.state.details.count, 5)
        let facts = search.state.facts.count
        XCTAssertGreaterThan(facts, 50)

        api.on(.getMeta, "meta")
        slow.release()
        await search.flow.caughtUp()

        XCTAssertEqual(search.state.explanations.count, 5)
        XCTAssertTrue(search.state.reasonsAreIn)
        XCTAssertEqual(search.state.details.count, 5)
        XCTAssertEqual(search.state.facts.count, facts)
        XCTAssertNil(search.state.failureOfTheCards)
        // Nothing had to be asked for a second time.
        XCTAssertEqual(api.calls(to: .explainTop).count, 1)
        XCTAssertEqual(api.calls(to: .getArea).count, 5)
        XCTAssertEqual(api.unexpected.count, 0)
    }

    @MainActor
    func test_a_first_search_after_a_release_has_its_reasons_and_profiles_when_the_form_comes_first() async {
        let api = StandIn.firstSearch().movedTo(newer)
        let ranking = api.hold(.rank, "rank-first")
        let search = OpenSearch(api)

        async let sent: Void = search.flow.submitText("leafy")
        await until { ranking.waiting > 0 }
        await search.flow.caughtUp()
        XCTAssertEqual(search.state.meta.releaseId, newer)
        api.on(.rank, "rank-first")
        ranking.release()
        await sent

        XCTAssertEqual(search.state.explanations.count, 5)
        XCTAssertTrue(search.state.reasonsAreIn)
        XCTAssertEqual(search.state.details.count, 5)
    }

    @MainActor
    func test_a_search_on_screen_gets_the_profiles_of_the_new_release_when_its_ranking_moves_to_it() async {
        let search = OpenSearch()
        await search.flow.submitText("leafy")
        XCTAssertEqual(Set(search.state.detailsBy.values.map(\.releaseId)), [Answers.meta.releaseId])
        search.api.forgetCalls()

        // The service moves to a newer release. The next edit is answered by it.
        search.api.movedTo(newer).on(.rank, "rank-rejected-edit")
        await search.flow.applyEdits(Edits.budgetAmount(1))
        await search.flow.caughtUp()

        // The spec did not change, so neither did its hash. The release did, and what the cards hold with it.
        XCTAssertEqual(search.state.rankedHash, first.rank.specHash)
        XCTAssertEqual(search.api.calls(to: .explainTop).count, 1)
        XCTAssertEqual(search.api.calls(to: .getArea).count, 5)
        XCTAssertTrue(search.state.reasonsAreIn)
        XCTAssertEqual(search.state.explainedBy?.releaseId, newer)
        XCTAssertEqual(search.state.detailsBy.count, 5)
        XCTAssertEqual(Set(search.state.detailsBy.values.map(\.releaseId)), [newer])
        XCTAssertEqual(Set(search.state.factsBy.values.map(\.releaseId)), [newer])
    }

    @MainActor
    func test_the_form_is_read_again_on_the_next_answer_when_reading_it_failed() async {
        let api = StandIn.firstSearch().movedTo(newer).on(.getMeta, "error-internal")
        let search = OpenSearch(api)

        await search.flow.submitText("leafy")
        await search.flow.caughtUp()
        XCTAssertEqual(search.state.meta.releaseId, Answers.meta.releaseId)
        // The search is whole all the same: nothing of it waits on the form.
        XCTAssertTrue(search.state.reasonsAreIn)

        api.on(.getMeta, "meta")
        let asked = api.calls(to: .getMeta).count
        await search.flow.rankNow()
        await search.flow.caughtUp()

        XCTAssertGreaterThan(api.calls(to: .getMeta).count, asked)
        XCTAssertEqual(search.state.meta.releaseId, newer)
    }

    @MainActor
    func test_the_form_is_not_asked_for_twice_while_it_is_being_read() async {
        let api = StandIn.firstSearch().movedTo(newer)
        let slow = api.hold(.getMeta, "meta")
        let search = OpenSearch(api)

        // Two answers name the newer release before the form has come: the reading, and the ranking.
        await search.flow.submitText("leafy")
        XCTAssertEqual(slow.waiting, 1)
        api.on(.getMeta, "meta")
        slow.release()
        await search.flow.caughtUp()

        XCTAssertEqual(api.calls(to: .getMeta).count, 1)
    }

    @MainActor
    func test_boundaries_that_could_not_be_read_again_are_asked_for_on_the_next_answer() async {
        let api = StandIn.firstSearch().movedTo(newer).on(.getGeometry, "error-internal")
        let search = OpenSearch(api)
        await search.flow.submitText("leafy")
        await search.flow.caughtUp()
        XCTAssertEqual(search.state.meta.releaseId, newer)
        XCTAssertNil(search.state.geometry)

        api.on(.getGeometry, "geometry")
        await search.flow.rankNow()
        await search.flow.caughtUp()

        XCTAssertEqual(search.state.geometry?.features.count, Answers.areas.count)
    }

    // MARK: - Which release made what is on screen

    @MainActor
    func test_the_release_of_every_answer_of_a_search_is_kept_with_it() async {
        let search = OpenSearch()

        await search.flow.submitText("leafy")

        let by = Served(form: Answers.meta)
        XCTAssertEqual(search.state.read?.by, by)
        XCTAssertEqual(search.state.rankedBy, by)
        XCTAssertEqual(search.state.explainedBy, by)
        XCTAssertEqual(Array(search.state.detailsBy.values), Array(repeating: by, count: 5))
    }

    @MainActor
    func test_reasons_made_by_another_release_than_the_ranking_are_asked_for_once_more() async {
        // The release moved between the ranking and its reasons, as it can while a service is replaced.
        let api = StandIn.firstSearch().inTurn(
            .explainTop, [StandIn.on(release: newer, "explanations-first"), .recorded("explanations-first")])
        let search = OpenSearch(api)

        await search.flow.submitText("leafy")

        XCTAssertEqual(api.calls(to: .explainTop).count, 2)
        XCTAssertTrue(search.state.reasonsAreIn)
        XCTAssertEqual(search.state.explainedBy, search.state.rankedBy)
        XCTAssertNil(search.state.failureOfTheCards)
    }

    @MainActor
    func test_reasons_that_are_still_another_releases_are_said_to_have_failed_and_never_shown() async {
        let api = StandIn.firstSearch().on(.explainTop, StandIn.on(release: newer, "explanations-first"))
        let search = OpenSearch(api)

        await search.flow.submitText("leafy")

        // The hashes agree, as they must: a hash is of the spec alone.
        XCTAssertEqual(search.state.explainedHash, search.state.rankedHash)
        XCTAssertFalse(search.state.reasonsAreIn)
        // The cards are not left waiting for ever: the reasons are said not to have come.
        XCTAssertEqual(search.state.failureOfTheCards, .because(.unreadable))
        XCTAssertEqual(api.calls(to: .explainTop).count, 2)

        // Trying again ranks again, so that the ranking and its reasons come from one release.
        api.movedTo(newer).on(.explainTop, "explanations-first")
        api.forgetCalls()
        await search.flow.retry()
        await search.flow.caughtUp()

        XCTAssertEqual(api.calls(to: .rank).count, 1)
        XCTAssertEqual(search.state.rankedBy?.releaseId, newer)
        XCTAssertTrue(search.state.reasonsAreIn)
        XCTAssertNil(search.state.failureOfTheCards)
    }

    // MARK: - A second sentence whose ranking fails

    @MainActor
    func test_the_first_rankings_reasons_stay_on_the_cards() async {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        let shown = search.state.explanations
        search.api.on(.interpret, "interpret-second-sentence").on(.rank, "error-internal")

        await search.flow.submitText("and near the water")

        // The ranking on screen is the first one's, and so are its reasons.
        XCTAssertEqual(search.state.failure?.code, .internalError)
        XCTAssertEqual(search.state.ranking?.ranked, first.rank.ranked)
        XCTAssertEqual(search.state.explanations, shown)
        XCTAssertEqual(search.state.explainedHash, search.state.rankedHash)
    }

    // MARK: - A share

    @MainActor
    func test_a_share_opened_on_a_release_that_has_moved_on_still_gets_its_reasons() async throws {
        let stale = try Recorded.read("share-opened-stale")
        let release = try XCTUnwrap(try JSON.read(stale.body)["meta"]?["release_id"]?.string)
        // The service that holds the newer release answers every call as that release.
        let api = StandIn()
            .movedTo(release)
            .on(.getShare, "share-opened-stale")
            .on(.explainTop, "explanations-first")
        let search = OpenSearch(api)

        let failure = await search.flow.openShare(String(stale.path.split(separator: "/").last ?? ""))

        // The answer names another release than the search was opened on, so the form is read again.
        XCTAssertNil(failure)
        XCTAssertNotEqual(release, Answers.meta.releaseId)
        XCTAssertEqual(api.calls(to: .getMeta).count, 1)
        XCTAssertEqual(search.state.meta.releaseId, release)
        // The share's own reasons come, and stay.
        XCTAssertTrue(search.state.reasonsAreIn)
        XCTAssertEqual(search.state.explanations.count, 5)
        XCTAssertEqual(search.state.details.count, 5)
        XCTAssertEqual(search.state.rankedBy?.releaseId, release)
    }
}
