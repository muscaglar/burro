import XCTest

@testable import BurroKit

/// What a person can do to a search, as the calls each thing makes.
final class FlowTests: XCTestCase {
    // A string found nowhere else, planted in what a person types.
    private let canary = "zqxcanary7431"
    private let first = (
        read: Answers.read("interpret-first"),
        rank: Answers.ranked("rank-first"),
        explain: Answers.explained("explanations-first")
    )

    // MARK: - Sending a sentence

    @MainActor
    func test_a_sentence_is_read_then_ranked_and_explained_and_the_first_five_are_fetched() async throws {
        let search = OpenSearch()

        await search.flow.submitText("Renting a 1 bed, leafy and quiet")

        XCTAssertEqual(search.api.routes.first, .interpret)
        XCTAssertEqual(
            search.api.routes.sorted { $0.rawValue < $1.rawValue },
            [.explainTop] + Array(repeating: .getArea, count: 5) + [.interpret, .rank])
        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self),
            RankBody(spec: first.read.spec, limit: 20))
        XCTAssertEqual(
            try search.api.lastCall(to: .explainTop).body(as: ExplanationsBody.self),
            ExplanationsBody(spec: first.read.spec, limit: 5))
        XCTAssertEqual(
            Set(search.api.calls(to: .getArea).map(\.path)),
            Set(first.rank.ranked.prefix(5).compactMap { area in
                Answers.areas.first { $0.areaId == area.areaId }.map { "/v1/areas/\($0.slug)" }
            }))
        XCTAssertEqual(search.state.phase, .results)
        XCTAssertEqual(search.state.spec, first.read.spec)
        XCTAssertEqual(search.state.ranking?.ranked, first.rank.ranked)
        XCTAssertEqual(search.state.explanations, first.explain.explanations)
        XCTAssertTrue(search.state.explained)
        XCTAssertEqual(search.state.details.count, 5)
        XCTAssertEqual(search.api.unexpected.count, 0)
    }

    @MainActor
    func test_a_first_sentence_is_sent_with_the_default_the_api_served() async throws {
        let search = OpenSearch()

        await search.flow.submitText("  leafy \n")

        // The rules are asked first, and answer at once. "leafy" is plain, so no model is asked at all.
        XCTAssertEqual(
            try search.api.calls(to: .interpret).map { try $0.body(as: InterpretBody.self) },
            [InterpretBody(text: "leafy", askModel: false, spec: Answers.meta.defaults.rent)])
    }

    @MainActor
    func test_a_second_sentence_is_sent_with_the_spec_the_first_one_left() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        search.api.on(.interpret, "interpret-second-sentence")

        await search.flow.submitText("a bit more green space")

        XCTAssertEqual(try search.api.lastCall(to: .interpret).body(as: InterpretBody.self).spec, first.rank.spec)
    }

    @MainActor
    func test_a_line_of_spaces_is_not_sent() async {
        let search = OpenSearch()

        await search.flow.submitText("   \n ")

        XCTAssertEqual(search.api.calls.count, 0)
        XCTAssertEqual(search.state.phase, .empty)
    }

    @MainActor
    func test_no_sentence_is_sent_until_the_person_has_agreed() async {
        let search = OpenSearch(agreed: false)

        await search.flow.submitText("leafy \(canary)")

        XCTAssertEqual(search.api.calls.count, 0)
        XCTAssertEqual(search.state.phase, .empty)
        XCTAssertNil(search.state.read)
    }

    @MainActor
    func test_the_settings_work_for_a_person_who_has_not_agreed() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.searchPlaces, "places-search"), agreed: false)

        await search.flow.applyEdits(Edits.tagOn(.leafy))
        let places = await search.flow.searchPlaces("pel")

        XCTAssertEqual(search.state.phase, .results)
        XCTAssertEqual(try places.get().data.places.first?.name, "Pellam Cross")
        XCTAssertEqual(search.api.calls(to: .interpret).count, 0)
    }

    @MainActor
    func test_the_screen_says_it_is_reading_until_the_ranking_is_in() async {
        let api = StandIn.firstSearch()
        let reading = api.hold(.interpret, "interpret-first")
        let search = OpenSearch(api)

        async let sent: Void = search.flow.submitText("leafy")
        await until { reading.waiting == 1 }
        XCTAssertEqual(search.state.phase, .interpreting)
        reading.release()
        await sent

        XCTAssertEqual(search.state.phase, .results)
    }

    @MainActor
    func test_what_was_read_can_be_drawn_before_the_ranking_is_in() async {
        let api = StandIn.firstSearch()
        let ranking = api.hold(.rank, "rank-first")
        let search = OpenSearch(api)

        async let sent: Void = search.flow.submitText("leafy")
        await until { ranking.waiting == 1 }

        XCTAssertEqual(search.state.spec, first.read.spec)
        XCTAssertEqual(search.state.read?.interpreter, .rule)
        XCTAssertEqual(search.state.phase, .interpreting)
        XCTAssertNil(search.state.ranking)
        ranking.release()
        await sent
    }

    @MainActor
    func test_words_that_changed_nothing_ask_for_no_new_ranking() async {
        let search = OpenSearch(StandIn.firstSearch().on(.interpret, "interpret-nothing-read"))

        await search.flow.submitText("hello there")

        XCTAssertEqual(search.api.routes, [.interpret])
        XCTAssertEqual(search.state.phase, .empty)
        XCTAssertEqual(search.state.conditions, [.nothingRead])
    }

    @MainActor
    func test_the_sentence_is_nowhere_in_the_search_once_it_has_been_sent() async {
        let search = OpenSearch()

        await search.flow.submitText("leafy \(canary)")

        XCTAssertFalse(String(describing: search.state).contains(canary))
        XCTAssertFalse(String(reflecting: search.state).contains(canary))
        for call in search.api.calls where call.route != .interpret {
            XCTAssertFalse(String(decoding: call.sent ?? Data(), as: UTF8.self).contains(canary))
            XCTAssertFalse(call.outsideTheBody.contains(canary))
        }
    }

    // MARK: - Moving a control

    @MainActor
    func test_a_control_sends_its_one_edit_with_the_last_spec_the_api_returned() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy")
        search.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        let edit = Edits.placeMinutes("syn-p0021", 30)

        await search.flow.applyEdits(edit)

        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self),
            RankBody(spec: first.rank.spec, limit: 20, operations: edit))
        XCTAssertEqual(search.state.spec, Answers.ranked("rank-refined").spec)
        XCTAssertEqual(search.state.pending, .none)
        XCTAssertEqual(search.state.explanations, Answers.explained("explanations-refined").explanations)
        XCTAssertTrue(search.state.explained)
        XCTAssertNotNil(search.state.moved)
    }

    @MainActor
    func test_the_reasons_are_asked_for_with_the_spec_the_ranking_returned() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy")
        search.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")

        await search.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))

        XCTAssertEqual(
            try search.api.lastCall(to: .explainTop).body(as: ExplanationsBody.self).spec,
            Answers.ranked("rank-refined").spec)
    }

    @MainActor
    func test_no_edit_at_all_sends_nothing() async {
        let search = OpenSearch()

        await search.flow.applyEdits(.none)

        XCTAssertEqual(search.api.calls.count, 0)
    }

    @MainActor
    func test_the_settings_can_be_ranked_as_they_stand() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.rank, "rank-default-rent"))

        await search.flow.rankNow()

        let sent = try search.api.lastCall(to: .rank).body(as: RankBody.self)
        XCTAssertEqual(sent, RankBody(spec: Answers.meta.defaults.rent, limit: 20))
        XCTAssertEqual(search.state.phase, .results)
        XCTAssertFalse(search.state.untouched)
    }

    @MainActor
    func test_renting_or_buying_sends_nothing_before_anything_is_asked_for() async throws {
        let search = OpenSearch()

        await search.flow.setTenure(.buy)
        XCTAssertEqual(search.api.calls.count, 0)
        XCTAssertEqual(search.state.spec, Answers.meta.defaults.buy)
        await search.flow.setTenure(.buy)
        XCTAssertEqual(search.api.calls.count, 0)

        // Once something has been asked for, it is an edit like any other.
        await search.flow.rankNow()
        XCTAssertEqual(search.state.spec.tenure, .rent)
        await search.flow.setTenure(.buy)
        XCTAssertEqual(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations, Edits.tenure(.buy))
    }

    @MainActor
    func test_a_control_moved_while_a_sentence_is_read_waits_for_the_reading() async throws {
        let api = StandIn.firstSearch()
        let reading = api.hold(.interpret, "interpret-first")
        let search = OpenSearch(api)

        async let sent: Void = search.flow.submitText("leafy")
        await until { reading.waiting == 1 }
        await search.flow.applyEdits(Edits.tagOn(.villageFeel))
        XCTAssertEqual(api.calls(to: .rank).count, 0)
        reading.release()
        await sent

        // Its edit goes with the spec the reading returns.
        XCTAssertEqual(
            try api.lastCall(to: .rank).body(as: RankBody.self),
            RankBody(spec: first.read.spec, limit: 20, operations: Edits.tagOn(.villageFeel)))
        XCTAssertEqual(api.calls(to: .rank).count, 1)
    }

    @MainActor
    func test_edits_made_while_a_call_is_out_are_sent_again_together_and_the_latest_wins() async throws {
        let api = StandIn.firstSearch()
        let search = OpenSearch(api)
        await search.flow.submitText("leafy")
        let slow = api.hold(.rank, "rank-refined")

        async let one: Void = search.flow.applyEdits(Edits.tagOn(.villageFeel))
        await until { slow.waiting == 1 }
        api.on(.rank, "rank-second-sentence")
        await search.flow.applyEdits(Edits.budgetAmount(1800))
        slow.release()
        await one

        XCTAssertEqual(
            try api.lastCall(to: .rank).body(as: RankBody.self).operations,
            Edits.tagOn(.villageFeel).merged(with: Edits.budgetAmount(1800)))
        // The answer to the older call is dropped.
        XCTAssertEqual(search.state.spec, Answers.ranked("rank-second-sentence").spec)
        XCTAssertEqual(search.state.pending, .none)
        XCTAssertEqual(search.state.phase, .results)
    }

    // MARK: - Failing, stopping and trying again

    @MainActor
    func test_a_reading_that_fails_leaves_the_settings_as_the_way_in() async {
        let search = OpenSearch(StandIn.firstSearch().unreachable(.interpret))

        await search.flow.submitText("leafy")

        XCTAssertEqual(search.state.failure?.kind, .network)
        XCTAssertEqual(search.state.failedStep, .read)
        XCTAssertEqual(search.state.failurePlace, .form)
        XCTAssertTrue(search.state.settingsOpen)
        XCTAssertEqual(search.state.phase, .empty)
        XCTAssertEqual(search.api.calls(to: .rank).count, 0)
    }

    @MainActor
    func test_a_reading_that_takes_too_long_is_given_up_on_and_the_form_is_shown() async {
        let search = OpenSearch(
            StandIn.firstSearch().silent(.interpret), timeouts: Timeouts(reading: .milliseconds(30)))

        await search.flow.submitText("leafy")

        XCTAssertEqual(search.state.failure?.kind, .timeout)
        XCTAssertTrue(search.state.conditions.contains(.degraded))
    }

    @MainActor
    func test_a_control_moved_while_a_reading_failed_is_not_lost_with_it() async throws {
        let api = StandIn.firstSearch()
        let reading = api.hold(.interpret, "error-internal")
        api.on(.rank, .made { _ in try Recorded.read("rank-default-rent") })
        let search = OpenSearch(api)

        async let sent: Void = search.flow.submitText("leafy")
        await until { reading.waiting == 1 }
        await search.flow.applyEdits(Edits.tagOn(.villageFeel))
        reading.release()
        await sent

        XCTAssertEqual(
            try api.lastCall(to: .rank).body(as: RankBody.self),
            RankBody(spec: Answers.meta.defaults.rent, limit: 20, operations: Edits.tagOn(.villageFeel)))
    }

    @MainActor
    func test_a_ranking_that_fails_keeps_the_edit_and_trying_again_sends_it_again() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy")
        search.api.on(.rank, "error-internal")
        let edit = Edits.tagOn(.villageFeel)

        await search.flow.applyEdits(edit)
        XCTAssertEqual(search.state.failure?.code, .internalError)
        XCTAssertEqual(search.state.pending, edit)
        XCTAssertEqual(search.state.ranking?.ranked, first.rank.ranked)
        search.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        await search.flow.retry()

        XCTAssertEqual(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations, edit)
        XCTAssertNil(search.state.failure)
        XCTAssertEqual(search.state.pending, .none)
    }

    @MainActor
    func test_trying_a_reading_again_needs_the_sentence_because_none_is_kept() async throws {
        let search = OpenSearch(StandIn.firstSearch().unreachable(.interpret))
        await search.flow.submitText("leafy")
        search.api.on(.interpret, "interpret-first")

        await search.flow.retry(text: "leafy")

        XCTAssertEqual(search.api.calls(to: .interpret).count, 2)
        XCTAssertEqual(search.state.phase, .results)
        XCTAssertNil(search.state.failure)
    }

    @MainActor
    func test_stop_ends_the_reading_and_returns_to_the_state_before() async {
        let api = StandIn.firstSearch().silent(.interpret)
        let search = OpenSearch(api)

        async let sent: Void = search.flow.submitText("leafy")
        await until { api.calls(to: .interpret).count == 1 }
        await search.flow.stop()
        await sent

        XCTAssertEqual(search.state.phase, .empty)
        XCTAssertNil(search.state.failure)
        XCTAssertEqual(api.calls(to: .rank).count, 0)
    }

    @MainActor
    func test_stopping_a_reading_does_not_undo_a_control_moved_meanwhile() async throws {
        let api = StandIn.firstSearch().silent(.interpret).on(.rank, "rank-default-rent")
        let search = OpenSearch(api)

        async let sent: Void = search.flow.submitText("leafy")
        await until { api.calls(to: .interpret).count == 1 }
        await search.flow.applyEdits(Edits.tagOn(.villageFeel))
        await search.flow.stop()
        await sent

        XCTAssertEqual(try api.lastCall(to: .rank).body(as: RankBody.self).operations, Edits.tagOn(.villageFeel))
        XCTAssertEqual(search.state.phase, .results)
    }

    @MainActor
    func test_starting_again_forgets_the_search_and_drops_what_is_out() async {
        let api = StandIn.firstSearch()
        let search = OpenSearch(api)
        await search.flow.submitText("leafy")
        let slow = api.hold(.rank, "rank-refined")

        async let edit: Void = search.flow.applyEdits(Edits.tagOn(.villageFeel))
        await until { slow.waiting == 1 }
        search.flow.startAgain()
        slow.release()
        await edit

        XCTAssertEqual(search.state.phase, .empty)
        XCTAssertEqual(search.state.spec, Answers.meta.defaults.rent)
        XCTAssertNil(search.state.ranking)
        XCTAssertEqual(search.state.pending, .none)
    }

    @MainActor
    func test_offline_the_edit_waits_and_is_sent_once_when_the_phone_is_back() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy")
        search.api.unreachable(.rank, .notConnectedToInternet)
        let edit = Edits.tagOn(.villageFeel)

        await search.flow.applyEdits(edit)
        XCTAssertEqual(search.state.conditions, [.offline])
        XCTAssertEqual(search.state.pending, edit)
        XCTAssertEqual(search.state.ranking?.ranked, first.rank.ranked)
        let before = search.api.calls(to: .rank).count
        search.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        await search.flow.wentOnline()

        XCTAssertEqual(search.api.calls(to: .rank).count, before + 1)
        XCTAssertEqual(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations, edit)
        XCTAssertEqual(search.state.conditions, [])
        XCTAssertTrue(search.state.online)
    }

    @MainActor
    func test_coming_back_online_with_nothing_waiting_sends_nothing() async {
        let search = OpenSearch()
        search.flow.wentOffline()

        await search.flow.wentOnline()

        XCTAssertEqual(search.api.calls.count, 0)
        XCTAssertTrue(search.state.online)
    }

    @MainActor
    func test_reasons_that_cannot_be_had_leave_the_ranking_on_screen() async {
        let search = OpenSearch(StandIn.firstSearch().on(.explainTop, "error-internal"))

        await search.flow.submitText("leafy")

        XCTAssertEqual(search.state.phase, .results)
        XCTAssertTrue(search.state.explainFailed)
        XCTAssertEqual(search.state.explanations, [])
        XCTAssertNil(search.state.failure)
    }

    @MainActor
    func test_a_profile_that_cannot_be_had_is_marked_and_the_rest_come() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(
                .getArea,
                .made { call in
                    try Recorded.read(call.path.hasSuffix("/farrowmere") ? "area-not-found" : "area/\(call.path.split(separator: "/").last ?? "")")
                }))

        await search.flow.submitText("leafy")

        XCTAssertEqual(search.state.detailsFailed, ["syn-n0006"])
        XCTAssertEqual(search.state.details.count, 4)
    }

    // MARK: - Questions and places

    @MainActor
    func test_a_question_is_answered_with_the_edit_it_asked_about_and_the_place_that_was_picked() async throws {
        let api = StandIn.firstSearch()
            .on(.interpret, "interpret-clarify")
            .on(.rank, StandIn.withTheSpecSent("rank-first"))
        let search = OpenSearch(api)
        await search.flow.submitText("near pellam")
        let question = try XCTUnwrap(search.state.questions.first)
        let option = try XCTUnwrap(question.options.first)

        await search.flow.answerClarify(question, id: option.id, name: option.name)

        let sent = try XCTUnwrap(api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(sent.commuteOps.map(\.placeId), ["syn-p0012"])
        XCTAssertEqual(sent.commuteOps.map(\.maxMinutes), [30])
        XCTAssertEqual(sent.count, 1)
        XCTAssertEqual(search.state.questions, [])
        XCTAssertEqual(search.state.name(ofPlace: "syn-p0012"), "Pellam Cross")
    }

    @MainActor
    func test_leaving_a_question_out_sends_nothing() async throws {
        let api = StandIn.firstSearch().on(.interpret, "interpret-clarify")
        let search = OpenSearch(api)
        await search.flow.submitText("near pellam")
        let calls = api.calls.count

        search.flow.leaveOut(try XCTUnwrap(search.state.questions.first))

        XCTAssertEqual(api.calls.count, calls)
        XCTAssertEqual(search.state.questions, [])
    }

    @MainActor
    func test_a_place_that_is_picked_is_added_as_a_journey_and_named() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.searchPlaces, "places-search"))
        let found = try await search.flow.searchPlaces("pel").get().data.places
        let place = try XCTUnwrap(found.first)

        await search.flow.addPlace(place)

        XCTAssertEqual(
            try search.api.lastCall(to: .searchPlaces).body(as: PlaceSearchBody.self),
            PlaceSearchBody(q: "pel", limit: 8))
        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self).operations, Edits.placeAdd("syn-p0012"))
        XCTAssertEqual(search.state.name(ofPlace: "syn-p0012"), "Pellam Cross")
    }

    // MARK: - Sharing and comparing

    @MainActor
    func test_a_link_is_made_of_the_spec_the_api_last_returned_and_coarse_unless_asked() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.createShare, "share-made"))
        await search.flow.submitText("leafy \(canary)")

        let made = await search.flow.createShare(exactPlaces: false)

        let call = try search.api.lastCall(to: .createShare)
        XCTAssertEqual(
            try call.body(as: ShareBody.self), ShareBody(spec: first.rank.spec, exactDestinations: false))
        XCTAssertFalse(String(decoding: call.sent ?? Data(), as: UTF8.self).contains(canary))
        XCTAssertEqual(try made.get().data.shareId, Answers.made.shareId)
        XCTAssertEqual(try made.get().data.coarsened, true)
        // The search is as it was.
        XCTAssertEqual(search.state.spec, first.rank.spec)
    }

    @MainActor
    func test_opening_a_share_shows_the_search_the_link_holds_with_its_reasons() async throws {
        let api = StandIn.firstSearch().on(.getShare, "share-opened")
        let search = OpenSearch(api)

        let failure = await search.flow.openShare(Answers.shareId)

        let shared = Answers.shared("share-opened")
        XCTAssertNil(failure)
        XCTAssertEqual(search.state.spec, shared.spec)
        XCTAssertEqual(search.state.shared?.id, Answers.shareId)
        XCTAssertEqual(search.state.shared?.coarsened, true)
        XCTAssertEqual(search.state.ranking, Ranking(shared))
        XCTAssertEqual(try api.lastCall(to: .explainTop).body(as: ExplanationsBody.self).spec, shared.spec)
        XCTAssertEqual(api.calls(to: .getArea).count, 5)
        XCTAssertEqual(try api.lastCall(to: .getShare).path, try Recorded.read("share-opened").path)
    }

    @MainActor
    func test_a_link_that_leads_nowhere_leaves_the_search_that_was_open_alone() async {
        let api = StandIn.firstSearch().on(.getShare, "share-gone")
        let search = OpenSearch(api)
        await search.flow.submitText("leafy")
        let before = search.state

        let failure = await search.flow.openShare(Answers.shareId(askedForIn: "share-gone"))

        XCTAssertEqual(failure?.code, .releaseChanged)
        XCTAssertEqual(failure?.api?.message, "The data has changed and this shared search cannot be shown.")
        XCTAssertEqual(search.state, before)
    }

    @MainActor
    func test_a_comparison_is_asked_for_with_the_search_as_it_stands() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.compare, "compare-three"))
        await search.flow.submitText("leafy")

        let compared = await search.flow.compare(areaIds: ["syn-n0006", "syn-n0017", "syn-n0003"])

        XCTAssertEqual(
            try search.api.lastCall(to: .compare).body(as: CompareBody.self),
            CompareBody(areaIds: ["syn-n0006", "syn-n0017", "syn-n0003"], spec: first.rank.spec))
        XCTAssertEqual(try compared.get().data, try Recorded.data(.compare, "compare-three", as: CompareData.self))
    }

    // MARK: - The map and the release

    @MainActor
    func test_the_map_is_asked_for_once() async {
        let search = OpenSearch()

        await search.flow.loadGeometry()
        await search.flow.loadGeometry()

        XCTAssertEqual(search.api.calls(to: .getGeometry).count, 1)
        XCTAssertEqual(search.state.geometry, Answers.geometry)
    }

    @MainActor
    func test_a_map_that_cannot_be_had_is_said_to_have_failed_and_the_list_still_works() async {
        let search = OpenSearch(StandIn.firstSearch().unreachable(.getGeometry))

        await search.flow.loadGeometry()
        await search.flow.submitText("leafy")

        XCTAssertTrue(search.state.geometryFailed)
        XCTAssertEqual(search.state.ranking?.ranked.count, first.rank.ranked.count)
    }

    @MainActor
    func test_a_profile_outside_the_first_five_is_fetched_when_it_is_asked_for() async {
        let search = OpenSearch()

        await search.flow.loadDetail(areaId: "syn-n0001")
        await search.flow.loadDetail(areaId: "syn-n0001")
        await search.flow.loadDetail(areaId: "syn-n9999")

        XCTAssertEqual(search.api.calls(to: .getArea).map(\.path), ["/v1/areas/alderwick"])
        XCTAssertEqual(search.state.details["syn-n0001"], Answers.profile("alderwick"))
    }

    @MainActor
    func test_when_an_answer_names_another_release_the_form_is_read_again() async throws {
        let api = StandIn.firstSearch().movedTo(Answers.newerRelease)
        let search = OpenSearch(api)

        await search.flow.submitText("leafy")
        await search.flow.caughtUp()
        await search.flow.rankNow()
        await search.flow.caughtUp()

        // It is read once for each release, however many answers name it.
        XCTAssertEqual(api.calls(to: .getMeta).count, 1)
        XCTAssertEqual(api.calls(to: .listAreas).count, 1)
        XCTAssertEqual(search.state.meta.releaseId, Answers.newerRelease)
        XCTAssertEqual(search.state.geometry, Answers.geometry)
    }

    @MainActor
    func test_choosing_an_area_and_opening_the_settings_send_nothing() {
        let search = OpenSearch()

        search.flow.select("syn-n0006")
        search.flow.openSettings(true)

        XCTAssertEqual(search.state.selectedId, "syn-n0006")
        XCTAssertTrue(search.state.settingsOpen)
        XCTAssertEqual(search.api.calls.count, 0)
    }

    // MARK: - A sentence that is not plain, where a model reads

    /// A service with a model behind it: the rules answer at once, and then the model.
    private func reading(then model: StandIn.Responder = .recorded("interpret-by-model-long")) -> StandIn {
        StandIn.firstSearch()
            .inTurn(.interpret, [.recorded("interpret-rules-at-once"), model])
            .on(.rank, "rank-suggestion-chosen")
            .on(.explainTop, "explanations-suggestion-chosen")
    }

    @MainActor
    func test_the_rules_are_asked_first_and_then_the_model_with_the_same_words_and_the_same_search()
        async throws
    {
        let long = Answers.read("interpret-by-model-long")
        let search = OpenSearch(reading())

        await search.flow.submitText("quiet \(canary)")

        let sent = try search.api.calls(to: .interpret).map { try $0.body(as: InterpretBody.self) }
        XCTAssertEqual(sent.map(\.askModel), [false, true])
        XCTAssertEqual(sent.map(\.text), ["quiet \(canary)", "quiet \(canary)"])
        XCTAssertEqual(sent.map(\.spec), [Answers.meta.defaults.rent, Answers.meta.defaults.rent])
        // What the model read has joined what is offered, and nothing of it is applied.
        XCTAssertEqual(search.state.read?.more, false)
        XCTAssertEqual(search.state.read?.suggestions, long.suggestions)
        XCTAssertEqual(search.state.spec, Answers.meta.defaults.rent)
        XCTAssertEqual(search.api.calls(to: .rank).count, 0)
        XCTAssertFalse(String(reflecting: search.state).contains(canary))
    }

    @MainActor
    func test_what_the_rules_offer_is_on_the_screen_while_the_model_reads_and_goes_when_the_box_changes()
        async
    {
        let atOnce = Answers.read("interpret-rules-at-once")
        // A model that never answers.
        let search = OpenSearch(reading(then: .silent))

        async let sent: Void = search.flow.submitText("quiet")
        await until { search.api.calls(to: .interpret).count == 2 }

        XCTAssertEqual(search.state.read?.more, true)
        XCTAssertEqual(search.state.suggestions, atOnce.suggestions)
        XCTAssertEqual(search.state.phase, .empty)
        // The model's reading is let go when the box changes, with what rested on what was sent.
        search.flow.boxChanged()
        await sent
        XCTAssertEqual(search.state.read?.more, false)
        XCTAssertEqual(search.state.suggestions, [])
        XCTAssertEqual(search.state.unread, [])
    }

    @MainActor
    func test_a_model_that_does_not_answer_leaves_what_the_rules_offered() async {
        let atOnce = Answers.read("interpret-rules-at-once")
        let search = OpenSearch(reading(then: .fails(.cannotConnectToHost)))

        await search.flow.submitText("quiet")

        XCTAssertEqual(search.api.calls(to: .interpret).count, 2)
        XCTAssertEqual(search.state.read?.more, false)
        XCTAssertEqual(search.state.suggestions, atOnce.suggestions)
        XCTAssertNil(search.state.failure)
    }

    @MainActor
    func test_an_offer_chosen_while_the_model_reads_is_not_offered_again() async {
        let long = Answers.read("interpret-by-model-long")
        let model = StandIn.Gate()
        let search = OpenSearch(
            reading(
                then: .made { _ in
                    try await model.hold()
                    return try Recorded.read("interpret-by-model-long")
                }))

        async let sent: Void = search.flow.submitText("quiet")
        await until { model.waiting == 1 }
        // "Quiet streets" is added while the model reads. A control that is moved does not stop the reading.
        await search.flow.choose(at: 0, id: "more")
        XCTAssertEqual(search.state.read?.more, true)
        XCTAssertEqual(search.api.calls(to: .rank).count, 1)
        model.release()
        await sent

        XCTAssertEqual(search.state.read?.more, false)
        XCTAssertEqual(search.state.suggestions.map(\.target), long.suggestions.dropFirst().map(\.target))
    }

    @MainActor
    func test_a_sentence_with_nothing_left_for_a_model_is_sent_once() async {
        let search = OpenSearch(StandIn.firstSearch().on(.interpret, "interpret-suggest"))

        await search.flow.submitText("pubs are so noisy")

        XCTAssertFalse(Answers.read("interpret-suggest").modelPending)
        XCTAssertEqual(search.api.calls(to: .interpret).count, 1)
        XCTAssertEqual(search.state.read?.more, false)
    }
}
