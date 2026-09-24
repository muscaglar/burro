import XCTest

@testable import BurroKit

// A string found nowhere else, planted in what a person types.
private let canary = "zqxcanary5127"

/// Every state of the search screen, in the order of docs/design/web.md
/// section 3, each reached by doing to the stand-in API what a person does.
/// What is tested is what the screen is told to draw: the screen draws that
/// and decides nothing.
final class SearchStatesTests: XCTestCase {
    private let always: [SearchPart] = [.box, .examples, .basics, .status, .chips, .settings]

    // MARK: - Empty

    @MainActor
    func test_empty_the_box_the_examples_the_basics_and_the_settings_closed() {
        let search = OpenSearch()

        let shown = search.shown()

        XCTAssertEqual(shown.parts, always)
        XCTAssertEqual(shown.box, .offered)
        XCTAssertEqual(shown.status, "")
        XCTAssertFalse(shown.reading)
        XCTAssertFalse(shown.busy)
        XCTAssertFalse(shown.settingsOpen)
        XCTAssertTrue(shown.canRank)
        XCTAssertFalse(shown.hasRanking)
        XCTAssertNil(shown.readBy)
        XCTAssertEqual(shown.chips.map(\.reads), ["Renting assumed", "Usual settings: 6 assumed"])
        XCTAssertEqual(search.api.calls.count, 0)
    }

    @MainActor
    func test_empty_renting_or_buying_swaps_the_default_and_sends_nothing() async {
        let search = OpenSearch()

        await search.flow.setTenure(.buy)

        XCTAssertEqual(search.shown().chips.first?.reads, "Buying assumed")
        XCTAssertEqual(search.state.spec, Answers.meta.defaults.buy)
        XCTAssertEqual(search.api.calls.count, 0)
    }

    @MainActor
    func test_empty_the_settings_can_be_ranked_as_they_stand() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.rank, "rank-default-rent"))

        await search.flow.rankNow()

        XCTAssertNil(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertFalse(search.shown().canRank)
        XCTAssertTrue(search.shown().hasRanking)
        XCTAssertEqual(search.api.calls(to: .interpret).count, 0)
    }

    // MARK: - Interpreting

    @MainActor
    func test_interpreting_the_screen_says_it_is_reading_and_the_chips_wait() async {
        let api = StandIn.firstSearch()
        let reading = api.hold(.interpret, "interpret-first")
        let search = OpenSearch(api)

        async let sent: Void = search.flow.submitText("leafy \(canary)")
        await until { reading.waiting == 1 }
        let shown = search.shown()

        XCTAssertTrue(shown.reading)
        XCTAssertTrue(shown.busy)
        XCTAssertEqual(shown.status, "Reading your search")
        XCTAssertTrue(shown.chipsWaiting)
        XCTAssertEqual(shown.chips, [])
        XCTAssertFalse(shown.canRank)
        XCTAssertEqual(shown.parts, always)
        reading.release()
        await sent
    }

    @MainActor
    func test_interpreting_stop_returns_to_the_state_before_and_takes_nobody_anywhere() async {
        let api = StandIn.firstSearch()
        let reading = api.hold(.interpret, "interpret-first")
        let search = OpenSearch(api)
        let before = search.state.answers

        async let sent: Void = search.flow.submitText("leafy")
        await until { reading.waiting == 1 }
        await search.flow.stop()
        reading.release()
        await sent

        XCTAssertEqual(search.shown().parts, always)
        XCTAssertFalse(search.shown().reading)
        XCTAssertEqual(search.api.calls(to: .rank).count, 0)
        XCTAssertFalse(SearchScreen.arrives(search.state, since: before, onTop: true))
    }

    // MARK: - Results

    @MainActor
    func test_results_chips_for_what_was_read_with_every_assumed_part_marked() async {
        let search = OpenSearch()

        await search.flow.submitText("Renting a 1 bed for about £1,700 a month, leafy and quiet")
        let shown = search.shown()

        XCTAssertEqual(
            shown.chips.map(\.reads),
            [
                "Renting",
                "£1,700 a month, One bedroom, flexible assumed",
                "Cindermoor Works, Public transport assumed, within 35 minutes, flexible assumed",
                "Leafy",
                "Quiet streets",
                "Usual settings: 6 assumed",
            ])
        XCTAssertEqual(shown.readBy, "Read without AI.")
        // The journey and the budget count for more than anything asked of the place, and the line says so.
        XCTAssertEqual(shown.status, "21 areas ranked. First: Farrowmere. Journey and budget count most.")
        XCTAssertEqual(shown.parts, [.box, .examples, .basics, .status, .chips, .results, .settings])
        XCTAssertFalse(shown.canRank)
    }

    @MainActor
    func test_results_a_reading_with_nothing_to_stop_for_leads_to_the_list_and_the_map() async {
        let search = OpenSearch()
        let before = search.state.answers

        await search.flow.submitText("leafy and quiet")

        XCTAssertTrue(SearchScreen.leadsToResults(search.state))
        XCTAssertTrue(SearchScreen.arrives(search.state, since: before, onTop: true))
        // The person has gone elsewhere meanwhile: they are left where they are.
        XCTAssertFalse(SearchScreen.arrives(search.state, since: before, onTop: false))
        // Nothing new has come since: a press that sent nothing takes nobody anywhere.
        XCTAssertFalse(SearchScreen.arrives(search.state, since: search.state.answers, onTop: true))
    }

    @MainActor
    func test_results_a_sentence_read_by_a_model_says_so_and_asks_to_be_checked() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-by-model")
                .on(.rank, StandIn.withTheSpecSent("rank-first")))

        await search.flow.submitText("Somewhere leafy")

        XCTAssertEqual(search.shown().readBy, "Read by AI. Check what it understood.")
    }

    // MARK: - What the chips are called, and what explains them

    @MainActor
    func test_the_chips_are_called_by_how_the_search_was_made() async {
        let untouched = OpenSearch()
        let typed = OpenSearch()
        let set = OpenSearch()
        let unread = OpenSearch(StandIn.firstSearch().on(.interpret, "interpret-nothing-read"))

        await typed.flow.submitText("leafy and quiet")
        await set.flow.applyEdits(Edits.tagOn(.leafy))
        await unread.flow.submitText("the piano")

        XCTAssertEqual(untouched.shown().chipsTitle, "What a search starts from")
        XCTAssertEqual(typed.shown().chipsTitle, "What Burro understood")
        // Nobody understood anything: the person set it.
        XCTAssertEqual(set.shown().chipsTitle, "What this search holds")
        // Words that were read into nothing leave the search where it starts.
        XCTAssertEqual(unread.shown().chipsTitle, "What a search starts from")
    }

    @MainActor
    func test_what_explains_the_chips_is_drawn_where_it_can_be_seen() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-two-journeys").on(.rank, "rank-two-journeys")
                .on(.explainTop, .fails(.cannotConnectToHost)))
        let explained = [
            "A part marked \"assumed\" is one you did not say. Burro filled it in, and you can change it.",
            "Usual settings are ones nobody chose. They count for less once you ask for something. "
                + "Press it to open the settings.",
        ]

        XCTAssertEqual(search.shown().chipsHints, explained)
        await search.flow.submitText("two journeys")

        XCTAssertEqual(search.shown().chipsHints, explained + ["Read without AI."])
    }

    @MainActor
    func test_a_place_is_named_by_the_answer_that_brought_it_and_never_by_a_number() async {
        // No reasons come, so no fact of a journey is in hand to name a place from.
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-two-journeys").on(.rank, "rank-two-journeys")
                .on(.explainTop, .fails(.cannotConnectToHost)))

        await search.flow.submitText("two journeys")
        let places = search.shown().chips.filter { chip in
            if case .place = chip.kind { return true }
            return false
        }

        XCTAssertEqual(search.state.facts.values.filter { $0.kind == .travel }, [])
        XCTAssertEqual(places.map(\.label), ["Foxholt Market", "Wexmoor University"])
        XCTAssertFalse(search.shown().chipsHints.contains { $0.contains("by number") })
        // A place no answer named is said to have no name. Nothing stands in for it.
        let unnamed = SearchChips.names(of: search.state.spec, held: [:])
        XCTAssertEqual(Set(unnamed.values), ["A place with no name in this data"])
    }

    @MainActor
    func test_a_search_with_every_place_named_and_nothing_assumed_has_less_to_explain() async {
        let search = OpenSearch()

        await search.flow.submitText("leafy and quiet")

        XCTAssertFalse(search.shown().chipsHints.contains { $0.contains("shown by number") })
        XCTAssertEqual(search.shown().chipsHints.last, "Read without AI.")
    }

    @MainActor
    func test_the_settings_are_opened_for_a_person_who_chose_them() async {
        let search = OpenSearch(agreed: false)

        XCTAssertTrue(SearchScreen.opensTheForm(search.state, consent: .settingsOnly))
        XCTAssertFalse(SearchScreen.opensTheForm(search.state, consent: .allowed))
        XCTAssertFalse(SearchScreen.opensTheForm(search.state, consent: nil))
        search.flow.openSettings(true)
        XCTAssertFalse(SearchScreen.opensTheForm(search.state, consent: .settingsOnly))
        search.flow.openSettings(false)
        await search.flow.applyEdits(Edits.tagOn(.leafy))

        // Once they have asked for something the form is theirs to open and to close.
        XCTAssertFalse(SearchScreen.opensTheForm(search.state, consent: .settingsOnly))
    }

    @MainActor
    func test_nothing_moves_when_less_motion_is_asked_for() async {
        let search = OpenSearch()
        let reading = search.api.hold(.interpret, "interpret-first")

        async let sent: Void = search.flow.submitText("leafy")
        await until { reading.waiting == 1 }

        XCTAssertTrue(SearchScreen.showsItIsBusy(search.shown(), reduceMotion: false))
        XCTAssertFalse(SearchScreen.showsItIsBusy(search.shown(), reduceMotion: true))
        // The words still say it.
        XCTAssertEqual(search.shown().status, "Reading your search")
        reading.release()
        await sent
        XCTAssertFalse(SearchScreen.showsItIsBusy(search.shown(), reduceMotion: false))
    }

    func test_every_movement_of_these_screens_is_one_that_less_motion_takes_away() throws {
        for file in try Written.files() {
            // Nothing is animated by hand. What opens in place is the system's own, and
            // its movement is taken away when less motion is asked for. The one way to
            // an animation is the token, which gives none when less motion is asked for.
            let text = file.text.replacingOccurrences(of: "Tokens.Motion.animation(", with: "")
            for word in ["withAnimation", ".animation(", ".transition(", "matchedGeometryEffect", "TimelineView"] {
                XCTAssertFalse(text.contains(word), "\(file.name): \(word)")
            }
            // A picture is hidden from a screen reader, or the button it is in is named.
            let pictures = file.text.components(separatedBy: "Image(systemName:").count - 1
            let said = file.text.components(separatedBy: ".accessibilityHidden(true)").count
                + file.text.components(separatedBy: ".accessibilityLabel(").count - 2
            XCTAssertGreaterThanOrEqual(said, pictures, file.name)
            if file.text.contains("DisclosureGroup(") {
                XCTAssertTrue(file.text.contains("accessibilityReduceMotion"), file.name)
            }
            if file.text.contains("ProgressView(") {
                XCTAssertTrue(file.text.contains("showsItIsBusy"), file.name)
            }
        }
    }

    // MARK: - Refining

    @MainActor
    func test_refining_the_last_results_stay_and_are_marked_busy() async {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        let ranking = search.api.hold(.rank, "rank-refined")

        async let sent: Void = search.flow.applyEdits(Edits.placeStrictness("syn-p0021", .hard))
        await until { ranking.waiting == 1 }
        let shown = search.shown()

        XCTAssertTrue(shown.busy)
        XCTAssertFalse(shown.reading)
        XCTAssertFalse(shown.chipsWaiting)
        XCTAssertEqual(shown.chips.count, 6)
        XCTAssertTrue(shown.hasRanking)
        ranking.release()
        await sent
    }

    @MainActor
    func test_refining_when_the_answer_comes_the_chips_are_drawn_from_the_returned_spec() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        search.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        let before = search.state.answers

        await search.flow.applyEdits(Edits.placeStrictness("syn-p0021", .hard))
        let shown = search.shown()

        XCTAssertEqual(
            shown.chips.map(\.reads)[2],
            "Cindermoor Works, Public transport assumed, within 30 minutes, firm limit")
        let moved = try XCTUnwrap(search.state.moved)
        XCTAssertGreaterThan(moved, 0)
        // What explains the order on screen is said of every ranking it is true of.
        XCTAssertEqual(shown.status, "\(SearchCopy.Status.moved(moved)) Journey and budget count most.")
        XCTAssertTrue(shown.status.contains("changed place."))
        XCTAssertGreaterThan(search.state.answers, before)
    }

    @MainActor
    func test_refining_an_edit_the_api_refuses_is_said_at_its_control_and_under_the_chips() async {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        search.api.on(.rank, "rank-rejected-edit")

        await search.flow.applyEdits(Edits.budgetAmount(1))
        let shown = search.shown()

        XCTAssertEqual(SettingsForm.problem(.budget, in: search.state), "That number is outside what Burro accepts.")
        XCTAssertEqual(
            shown.notApplied,
            [NotAppliedShown(about: nil, reason: "That number is outside what Burro accepts.")])
        XCTAssertTrue(shown.parts.contains(.notApplied))
        XCTAssertEqual(shown.chips.map(\.reads)[1], "£1,700 a month, One bedroom, flexible assumed")
    }

    // MARK: - Clarifying a place

    @MainActor
    private func asked() async -> OpenSearch {
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-clarify")
                .on(.rank, StandIn.withTheSpecSent("rank-first")))
        await search.flow.submitText("Leafy, renting, 30 minutes to \(canary)")
        return search
    }

    @MainActor
    func test_clarifying_one_question_with_its_options_and_never_what_was_typed() async {
        let search = await asked()

        let shown = search.shown()

        XCTAssertEqual(shown.questions.count, 1)
        XCTAssertEqual(shown.questions.first?.title, "Which place did you mean?")
        XCTAssertEqual(
            shown.questions.first?.options.map(\.name),
            ["Pellam Cross", "Pellam Exchange", "Pellam Infirmary"])
        XCTAssertEqual(shown.questions.first?.options.map(\.kind), ["Station", "District", "Hospital"])
        XCTAssertEqual(shown.questions.first?.searchable, true)
        XCTAssertNil(shown.questions.first?.none)
        XCTAssertTrue(shown.status.hasSuffix("Burro has a question about a place."))
        // The question stands for the edit that was refused. It is not said twice.
        XCTAssertEqual(shown.notApplied, [])
        // The rest of what was read is applied, and ranked.
        XCTAssertTrue(shown.chips.map(\.reads).contains("Leafy"))
        XCTAssertTrue(shown.hasRanking)
        XCTAssertFalse(String(reflecting: shown).contains(canary))
        XCTAssertFalse(SearchScreen.leadsToResults(search.state))
    }

    @MainActor
    func test_clarifying_a_pick_sends_the_edit_that_was_asked_about_with_the_place_in_it() async throws {
        let search = await asked()
        let question = try XCTUnwrap(search.shown().questions.first)

        await search.flow.answerClarify(question.asked, id: "syn-p0012", name: "Pellam Cross")

        let sent = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(sent.count, 1)
        XCTAssertEqual(sent.commuteOps.first?.placeId, "syn-p0012")
        XCTAssertEqual(sent.commuteOps.first?.maxMinutes, 30)
        XCTAssertEqual(sent.commuteOps.first?.action, .add)
        XCTAssertEqual(search.shown().questions, [])
        XCTAssertEqual(search.state.placeNames["syn-p0012"], "Pellam Cross")
    }

    @MainActor
    func test_clarifying_leave_it_out_takes_the_question_away_and_sends_nothing() async throws {
        let search = await asked()
        let question = try XCTUnwrap(search.shown().questions.first)
        let calls = search.api.calls.count

        search.flow.leaveOut(question.asked)

        XCTAssertEqual(search.shown().questions, [])
        XCTAssertFalse(search.shown().parts.contains(.questions))
        XCTAssertEqual(search.shown().notApplied, [])
        XCTAssertEqual(search.api.calls.count, calls)
    }

    @MainActor
    func test_clarifying_with_nothing_to_offer_the_search_field_stands_alone() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-clarify-no-options")
                .on(.rank, StandIn.withTheSpecSent("rank-first")))

        await search.flow.submitText("Quiet, and I work in \(canary)")
        let question = search.shown().questions.first

        XCTAssertEqual(question?.options, [])
        XCTAssertEqual(question?.none, "Burro did not find the place you named. Search for it here.")
        XCTAssertEqual(question?.searchable, true)
        XCTAssertFalse(String(reflecting: search.shown()).contains(canary))
    }

    @MainActor
    func test_clarifying_two_questions_are_told_apart_by_their_number() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(
                .interpret,
                .made { _ in
                    try Recorded.read("interpret-clarify").with(data: { data in
                        guard case .array(let asked)? = data["clarify"], var second = asked.first else {
                            return
                        }
                        second["group"] = .string("area_ops")
                        second["options"] = .array([])
                        data["clarify"] = .array(asked + [second])
                    })
                }
            ).on(.rank, StandIn.withTheSpecSent("rank-first")))

        await search.flow.submitText("Leafy, 30 minutes to somewhere")
        let questions = search.shown().questions

        XCTAssertEqual(
            questions.map(\.title),
            ["Which place did you mean? Question 1 of 2.", "Which area did you mean? Question 2 of 2."])
        // An area is picked from what is offered. There is no search for one.
        XCTAssertEqual(questions.map(\.searchable), [true, false])
        XCTAssertEqual(questions.map(\.none), [nil, nil])
        XCTAssertEqual(Set(questions.map(\.id)).count, 2)
    }

    // MARK: - Nothing matches

    @MainActor
    func test_nothing_matches_is_said_in_words_and_the_person_is_left_with_the_settings() async {
        let search = OpenSearch(StandIn.firstSearch().on(.rank, "rank-nothing-matches"))
        let before = search.state.answers

        await search.flow.submitText("a firm budget")
        let shown = search.shown()

        XCTAssertEqual(shown.status, "No area passes every limit you set.")
        XCTAssertTrue(shown.chips.map(\.reads).contains { $0.contains("firm limit") })
        XCTAssertTrue(shown.parts.contains(.results))
        XCTAssertFalse(SearchScreen.arrives(search.state, since: before, onTop: true))
    }

    // MARK: - Nothing read

    @MainActor
    func test_nothing_read_is_said_once_and_the_settings_open() async {
        let search = OpenSearch(StandIn.firstSearch().on(.interpret, "interpret-nothing-read"))

        await search.flow.submitText("What is the best way to learn the piano")
        let shown = search.shown()

        XCTAssertEqual(
            shown.nothingRead,
            "Nothing in that could be read. Burro reads plain English, such as “leafy and quiet, near a park”. "
                + "Say it another way, or use the settings below.")
        // The line has said it. It is not said a second time in other words.
        XCTAssertEqual(shown.unmet, [])
        XCTAssertNil(shown.notice)
        XCTAssertFalse(shown.readInPart)
        XCTAssertNil(shown.offers)
        XCTAssertTrue(shown.settingsOpen)
        // Where the words that were not read stand is known, so the box can show them.
        XCTAssertEqual(shown.unread, [Span(start: 0, end: 39)])
        XCTAssertEqual(
            shown.parts, [.box, .examples, .basics, .status, .nothingRead, .chips, .unread, .settings])
        XCTAssertEqual(search.api.routes, [.interpret])
    }

    @MainActor
    func test_nothing_read_by_a_model_is_said_in_the_apis_own_words() async {
        let search = OpenSearch(StandIn.firstSearch().on(.interpret, "interpret-off-topic"))

        await search.flow.submitText("What is the best way to learn the piano")
        let shown = search.shown()

        XCTAssertEqual(shown.notice, Answers.read("interpret-off-topic").noticeText)
        XCTAssertNil(shown.nothingRead)
        XCTAssertEqual(shown.parts, [.box, .examples, .basics, .status, .notice, .chips, .unread, .settings])
    }

    @MainActor
    func test_nothing_changed_is_told_apart_from_nothing_read() async {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        search.api.on(.interpret, StandIn.readingThatChangesNothing("interpret-first"))
        let before = search.state.answers

        await search.flow.submitText("leafy and quiet")
        let shown = search.shown()

        XCTAssertEqual(shown.nothingRead, "That changed nothing. Your search already says it.")
        XCTAssertFalse(SearchScreen.arrives(search.state, since: before, onTop: true))
        XCTAssertEqual(search.api.calls(to: .rank).count, 1)
    }

    // MARK: - Degraded to a form

    @MainActor
    func test_degraded_the_rules_read_the_words_and_the_screen_says_the_settings_do_the_same_job() async {
        let search = OpenSearch(StandIn.firstSearch().on(.interpret, "interpret-degraded"))

        await search.flow.submitText("leafy and quiet")
        let shown = search.shown()

        // The words were read, by rules: there is nothing to try again.
        XCTAssertEqual(shown.couldNotReadRetry, false)
        XCTAssertTrue(shown.settingsOpen)
        XCTAssertEqual(shown.chips.count, 6)
        XCTAssertTrue(shown.hasRanking)
        XCTAssertNil(shown.failure)
        XCTAssertEqual(
            shown.parts, [.box, .examples, .basics, .status, .couldNotRead, .chips, .results, .settings])
    }

    @MainActor
    func test_degraded_a_reading_that_takes_too_long_shows_the_form_and_offers_to_try_again() async {
        let search = OpenSearch(
            StandIn.firstSearch().silent(.interpret), timeouts: Timeouts(reading: .milliseconds(30)))

        await search.flow.submitText("leafy \(canary)")
        let shown = search.shown()

        XCTAssertEqual(shown.couldNotReadRetry, true)
        XCTAssertTrue(shown.settingsOpen)
        XCTAssertNil(shown.failure)
        XCTAssertNil(shown.boxProblem)
        XCTAssertNil(shown.offlineWaiting)
        XCTAssertTrue(shown.canRank)
        XCTAssertFalse(String(reflecting: shown).contains(canary))
    }

    @MainActor
    func test_degraded_a_fault_while_reading_shows_the_form_and_every_control_works() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.interpret, "error-internal"))

        await search.flow.submitText("leafy")
        XCTAssertEqual(search.shown().couldNotReadRetry, true)
        await search.flow.applyEdits(SettingsForm.tag(.leafy, on: true))

        XCTAssertEqual(search.state.phase, .results)
        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self).operations,
            Edits.tagOn(.leafy))
    }

    @MainActor
    func test_degraded_try_again_sends_the_sentence_from_the_box_because_none_is_kept() async throws {
        let api = StandIn.firstSearch().unreachable(.interpret)
        let search = OpenSearch(api)
        await search.flow.submitText("leafy")
        api.on(.interpret, "interpret-first")

        await search.flow.retry(text: "leafy")

        XCTAssertEqual(api.calls(to: .interpret).count, 2)
        XCTAssertNil(search.shown().couldNotReadRetry)
        XCTAssertEqual(search.state.phase, .results)
    }

    // MARK: - Neutral notice

    @MainActor
    func test_the_neutral_notice_is_the_apis_sentence_and_nothing_says_what_was_left_out() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-notice")
                .on(.rank, StandIn.withTheSpecSent("rank-first")))
        let before = search.state.answers

        await search.flow.submitText("Quiet and leafy, 30 minutes to work")
        let shown = search.shown()

        XCTAssertEqual(
            shown.notice,
            "Burro ranks places by what is there, such as schools, parks, venues and transport, "
                + "and never by who lives there. The rest of your search has been applied.")
        XCTAssertEqual(shown.unmet, [])
        XCTAssertEqual(shown.notApplied, [])
        XCTAssertNil(shown.nothingRead)
        XCTAssertEqual(
            shown.chips.map(\.label),
            ["Renting", "Cindermoor Works", "Leafy", "Quiet streets", "Usual settings: 6"])
        XCTAssertEqual(
            shown.parts, [.box, .examples, .basics, .status, .notice, .chips, .results, .settings])
        // The person reads it before they are shown anything else.
        XCTAssertFalse(SearchScreen.arrives(search.state, since: before, onTop: true))
    }

    // MARK: - What could not be answered, and what was not applied

    @MainActor
    func test_each_thing_that_cannot_be_answered_has_its_line() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-unmet")
                .on(.rank, StandIn.withTheSpecSent("rank-first")))

        await search.flow.submitText("Leafy, with fast broadband")
        let shown = search.shown()

        XCTAssertEqual(
            shown.unmet,
            [
                "Burro has no data on broadband, so that part was left out.",
                "Burro has no data on flood risk, so that part was left out.",
                "Burro has no data on places of worship, or on shops and venues for one community, so that part was left out.",
            ])
        XCTAssertTrue(shown.parts.contains(.unmet))
        XCTAssertFalse(SearchScreen.leadsToResults(search.state))
    }

    @MainActor
    func test_an_edit_that_was_not_applied_is_said_with_what_it_was_about() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-rejected")
                .on(.rank, StandIn.withTheSpecSent("rank-first")))

        await search.flow.submitText("Somewhere a bit cheaper, near a park")
        let shown = search.shown()

        // There was no budget to lower. A budget has no name of its own, so the reason stands alone.
        XCTAssertEqual(shown.notApplied, [NotAppliedShown(about: nil, reason: "That changed nothing.")])
        XCTAssertFalse(SearchScreen.leadsToResults(search.state))
    }

    @MainActor
    func test_an_edit_of_recorded_crime_that_was_not_applied_says_the_rule_and_names_what_it_was_about() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(
                .interpret,
                .made { _ in
                    try Recorded.read("interpret-rejected").with(data: { data in
                        data["rejected"] = data["rejected"]?.each {
                            $0["group"] = .string("weight_ops")
                            $0["reason"] = .string("crime_needs_explicit_request")
                        }
                        data["applied"] = .array([])
                        // The edits are read before they are put back: the answer is changed
                        // in one place at a time.
                        let ofCrime = data["operations"]?["weight_ops"]?.each {
                            $0["feature_id"] = .string("crime_burglary_theft")
                        }
                        data["operations"]?["weight_ops"] = ofCrime
                    })
                }
            ).on(.rank, StandIn.withTheSpecSent("rank-first")))

        await search.flow.submitText("Somewhere safe")
        let shown = search.shown()

        let rule =
            "Recorded crime counts only when you ask for it by name, switch it on in the settings, "
            + "or ask for a vibe whose recipe holds it."
        XCTAssertEqual(shown.notApplied, [NotAppliedShown(about: "Recorded burglary and theft", reason: rule)])
        XCTAssertFalse(shown.chips.contains { $0.label.contains("Recorded") })
        // Where no vibe of the release holds recorded crime, the line says so, and offers nothing that is not there.
        XCTAssertEqual(SearchScreen.rejected(.crimeNeedsExplicitRequest, in: Answers.meta), rule)
        let other: MetaData? = try? Recorded.data(.getMeta, "variant-a/meta")
        XCTAssertEqual(
            other.flatMap { SearchScreen.rejected(.crimeNeedsExplicitRequest, in: $0) },
            "\(rule) In this data no vibe holds it.")
    }

    // MARK: - Error from the API

    @MainActor
    func test_a_refusal_of_the_words_is_said_under_the_box_in_the_apis_words() async {
        let search = OpenSearch(StandIn.firstSearch().on(.interpret, "interpret-invalid-text"))

        await search.flow.submitText("leafy \(canary)")
        let shown = search.shown()

        XCTAssertEqual(shown.boxProblem, "The text must be 1 to 600 characters.")
        XCTAssertNil(shown.failure)
        XCTAssertNil(shown.couldNotReadRetry)
        XCTAssertFalse(shown.settingsOpen)
        XCTAssertEqual(shown.parts, always)
        XCTAssertFalse(String(reflecting: shown).contains(canary))
    }

    @MainActor
    func test_a_fault_in_the_service_leaves_the_results_and_gives_the_id_to_quote() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        search.api.on(.rank, "error-internal")

        await search.flow.applyEdits(Edits.tagOn(.pace))
        let shown = search.shown()
        let failure = try XCTUnwrap(shown.failure)

        XCTAssertEqual(failure.message, "Something went wrong on the server.")
        XCTAssertTrue(failure.notUpdated)
        XCTAssertEqual(failure.requestId, try Recorded.read("error-internal").headers["x-request-id"])
        XCTAssertEqual(failure.repairs, [])
        XCTAssertEqual(shown.chips.count, 6)
        XCTAssertEqual(shown.parts, [.box, .examples, .basics, .status, .failure, .chips, .results, .settings])
    }

    @MainActor
    func test_a_fault_try_again_sends_the_edit_that_was_kept() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        search.api.on(.rank, "error-internal")
        await search.flow.applyEdits(Edits.tagOn(.pace))
        search.api.on(.rank, "rank-refined")

        await search.flow.retry(text: "leafy and quiet")

        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self).operations, Edits.tagOn(.pace))
        XCTAssertNil(search.shown().failure)
        // The sentence is not read again: it was the ranking that failed.
        XCTAssertEqual(search.api.calls(to: .interpret).count, 1)
    }

    func test_a_search_that_names_what_the_data_no_longer_has_offers_to_take_it_out() throws {
        let sent = try JSONDecoder().decode(
            RankBody.self, from: XCTUnwrap(Recorded.read("rank-stale-spec").sent))
        var state = [SearchEvent.rankStarted(seq: 1), .failed(step: .rank, Answers.failure("rank-stale-spec"))]
            .reduce(SearchState(meta: Answers.meta, areas: Answers.areas), reduce)
        state.spec = sent.spec

        let failure = try XCTUnwrap(SearchScreen.shown(state, consent: .allowed).failure)

        XCTAssertEqual(failure.message, "Your search names something this data no longer has.")
        // No answer named the place, so it is said as what it is, and never by a number.
        XCTAssertEqual(failure.repairs.map(\.label), ["Take the place out"])
        XCTAssertEqual(failure.repairs.map(\.operations), [Edits.placeRemove("syn-p9999")])
        XCTAssertFalse(failure.notUpdated)
    }

    @MainActor
    func test_a_wrong_address_of_the_api_is_said_and_never_passed_over_in_silence() async {
        let search = OpenSearch(StandIn.firstSearch().on(.interpret, "not-found"))

        await search.flow.submitText("leafy")
        let shown = search.shown()

        XCTAssertEqual(shown.failure?.message, "There is no such route.")
        XCTAssertNil(shown.couldNotReadRetry)
        XCTAssertNil(shown.boxProblem)
    }

    @MainActor
    func test_start_again_forgets_the_search_and_the_failure() async {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        search.api.on(.rank, "error-internal")
        await search.flow.applyEdits(Edits.tagOn(.pace))

        search.flow.startAgain()

        XCTAssertEqual(search.shown().parts, always)
        XCTAssertEqual(search.shown().chips.map(\.reads), ["Renting assumed", "Usual settings: 6 assumed"])
    }

    // MARK: - Offline

    @MainActor
    func test_offline_the_search_stays_and_the_change_waits() async {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        search.api.unreachable(.rank, .notConnectedToInternet)

        await search.flow.applyEdits(Edits.tagOn(.pace))
        let shown = search.shown()

        XCTAssertEqual(shown.offlineWaiting, true)
        XCTAssertNil(shown.failure)
        XCTAssertNil(shown.couldNotReadRetry)
        XCTAssertEqual(shown.chips.count, 6)
        XCTAssertTrue(shown.hasRanking)
        XCTAssertEqual(shown.parts, [.box, .examples, .basics, .status, .offline, .chips, .results, .settings])
    }

    @MainActor
    func test_offline_try_again_sends_what_waited_once_and_the_line_goes() async throws {
        let search = OpenSearch()
        await search.flow.submitText("leafy and quiet")
        search.api.unreachable(.rank, .notConnectedToInternet)
        await search.flow.applyEdits(Edits.tagOn(.pace))
        search.api.on(.rank, "rank-refined")
        let calls = search.api.calls(to: .rank).count

        await search.flow.wentOnline()

        XCTAssertEqual(search.api.calls(to: .rank).count, calls + 1)
        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self).operations, Edits.tagOn(.pace))
        XCTAssertNil(search.shown().offlineWaiting)
        XCTAssertFalse(search.shown().parts.contains(.offline))
    }

    @MainActor
    func test_offline_a_sentence_that_could_not_leave_is_not_said_to_be_unreadable() async {
        let search = OpenSearch(StandIn.firstSearch().unreachable(.interpret, .notConnectedToInternet))

        await search.flow.submitText("leafy")
        let shown = search.shown()

        XCTAssertEqual(shown.offlineWaiting, false)
        XCTAssertNil(shown.couldNotReadRetry)
        XCTAssertNil(shown.failure)
    }

    // MARK: - Declined

    @MainActor
    func test_a_person_who_chose_the_settings_has_no_box_and_nothing_typed_is_sent() async {
        let search = OpenSearch(agreed: false)

        let shown = search.shown(.settingsOnly)
        await search.flow.submitText("leafy \(canary)")

        XCTAssertEqual(shown.box, .declined)
        XCTAssertEqual(shown.parts, [.box, .basics, .status, .chips, .settings])
        XCTAssertTrue(shown.canRank)
        XCTAssertEqual(search.api.calls.count, 0)
    }

    @MainActor
    func test_a_person_who_has_not_chosen_has_no_box_either() {
        XCTAssertEqual(OpenSearch(agreed: false).shown(nil).box, .declined)
    }

    @MainActor
    func test_the_form_does_the_whole_job_for_a_person_who_chose_the_settings() async throws {
        let search = OpenSearch(StandIn.firstSearch().on(.searchPlaces, "places-search"), agreed: false)

        let found = try await search.flow.searchPlaces("pel").get().data.places
        await search.flow.addPlace(try XCTUnwrap(found.first))
        await search.flow.applyEdits(Edits.budgetAmount(1700))

        XCTAssertEqual(search.state.phase, .results)
        XCTAssertEqual(search.api.calls(to: .interpret).count, 0)
        XCTAssertEqual(search.api.calls(to: .rank).count, 2)
        XCTAssertTrue(search.shown(.settingsOnly).hasRanking)
    }

    // MARK: - Every state

    @MainActor
    func test_the_parts_are_always_drawn_in_one_order() async {
        var seen: [[SearchPart]] = []
        for (reading, ranking) in [
            ("interpret-first", "rank-first"), ("interpret-clarify", "rank-first"),
            ("interpret-notice", "rank-first"), ("interpret-unmet", "rank-first"),
            ("interpret-rejected", "rank-first"), ("interpret-degraded", "rank-first"),
            ("interpret-nothing-read", "rank-first"), ("interpret-first", "rank-nothing-matches"),
            ("interpret-suggest", "rank-first"), ("interpret-suggest-notice", "rank-first"),
            ("preview/interpret-plain", "preview/rank-plain"),
            ("interpret-first", "error-internal"), ("interpret-invalid-text", "rank-first"),
        ] {
            let search = OpenSearch(StandIn.firstSearch().on(.interpret, reading).on(.rank, ranking))
            await search.flow.submitText("leafy")
            seen.append(search.shown().parts)
        }

        for parts in seen {
            XCTAssertEqual(parts, parts.sorted())
            XCTAssertEqual(Set(parts).count, parts.count)
            XCTAssertTrue(Set(always).isSubset(of: Set(parts)))
        }
        XCTAssertGreaterThan(Set(seen).count, 6)
    }

    @MainActor
    func test_one_failure_is_shown_in_one_place() async {
        let failures: [(APIRoute, StandIn.Responder)] = [
            (.interpret, .recorded("interpret-invalid-text")), (.interpret, .recorded("error-internal")),
            (.interpret, .fails(.notConnectedToInternet)), (.interpret, .fails(.cannotConnectToHost)),
            (.interpret, .recorded("not-found")), (.rank, .recorded("error-internal")),
            (.rank, .fails(.notConnectedToInternet)), (.rank, .recorded("rank-stale-spec")),
        ]

        for (route, responder) in failures {
            let search = OpenSearch(StandIn.firstSearch().on(route, responder))
            await search.flow.submitText("leafy")
            let shown = search.shown()
            let places = [
                shown.boxProblem != nil, shown.couldNotReadRetry == true, shown.offlineWaiting != nil,
                shown.failure != nil,
            ]

            XCTAssertEqual(places.filter { $0 }.count, 1, "\(route.rawValue)")
        }
    }

    @MainActor
    func test_a_code_this_build_has_no_word_for_is_left_out_and_never_shown_as_the_code() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(
                .interpret,
                .made { _ in
                    try Recorded.read("interpret-unmet").with(data: { data in
                        data["unmet"] = .array([.string("broadband"), .string("a_new_kind")])
                        data["interpreter"] = .string("a_new_reader")
                    })
                }
            ).on(.rank, StandIn.withTheSpecSent("rank-first")))

        await search.flow.submitText("leafy")
        let shown = search.shown()

        XCTAssertEqual(shown.unmet, ["Burro has no data on broadband, so that part was left out."])
        XCTAssertNil(shown.readBy)
        XCTAssertFalse(String(reflecting: shown.unmet).contains("a_new_kind"))
    }
}
