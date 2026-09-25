import XCTest

@testable import BurroKit

/// Every state the website's search page has, in the order of
/// docs/design/web.md section 3, as the results screen shows it. Each is
/// reached by a search run against the stand-in, which answers from what the
/// real API answered.
final class ResultsStatesTests: XCTestCase {
    private let first = Answers.ranked("rank-first")

    // MARK: - Empty

    @MainActor
    func test_empty_the_list_waits_and_the_map_gives_no_area_a_band() async throws {
        let app = try await ResultsApp()
        await app.flow.loadGeometry()

        let listed = app.listed
        XCTAssertTrue(listed.empty)
        XCTAssertFalse(listed.busy)
        XCTAssertNil(listed.headline)
        XCTAssertEqual(listed.cards, [])
        XCTAssertEqual(listed.lines, [])
        XCTAssertNil(listed.nothing)
        XCTAssertNil(listed.announcement)
        // The map of every area in one plain colour, with no pin and no figure.
        XCTAssertEqual(app.mapped.regions.count, Answers.areas.count)
        XCTAssertEqual(Set(app.mapped.regions.map(\.fill)), [.land])
        XCTAssertEqual(app.mapped.marks, [])
        XCTAssertEqual(app.mapped.legend.map(\.words), ["No fit yet"])
        XCTAssertEqual(app.tabled.caption, "Every area, by name")
        XCTAssertEqual(Set(app.tabled.rows.map(\.status)), ["Not ranked yet", "Not ranked in this data"])
        XCTAssertEqual(app.api.calls(to: .rank).count, 0)
    }

    // MARK: - Interpreting

    @MainActor
    func test_interpreting_the_list_says_it_is_reading_and_has_nothing_to_show_yet() async throws {
        let api = StandIn.firstSearch()
        let reading = api.hold(.interpret, "interpret-first")
        let app = try await ResultsApp(api)

        async let sent: Void = app.flow.submitText("leafy")
        await until { reading.waiting == 1 }

        XCTAssertTrue(app.listed.busy)
        XCTAssertTrue(app.listed.empty)
        XCTAssertEqual(app.listed.waitingFor, "Reading your search")
        XCTAssertEqual(app.listed.announcement, "Reading your search")
        XCTAssertEqual(app.listed.cards, [])
        reading.release()
        await sent
        XCTAssertNil(app.listed.waitingFor)
    }

    // MARK: - Results

    @MainActor
    func test_results_twenty_in_rank_order_the_first_five_in_full_and_the_rest_as_rows() async throws {
        let app = try await ResultsApp.searched()

        let listed = app.listed
        XCTAssertFalse(listed.empty)
        XCTAssertFalse(listed.busy)
        XCTAssertEqual(listed.headline, "21 areas ranked. First: Farrowmere.")
        // What was asked of the place counts for more than the journey and the budget, and the
        // settings nobody chose gave way to it.
        XCTAssertEqual(listed.changes, ["What you asked for counts most."])
        XCTAssertEqual(
            listed.announcement, "21 areas ranked. First: Farrowmere. What you asked for counts most.")
        XCTAssertEqual(listed.cards.map(\.heading.rank), Array(1...first.ranked.count))
        XCTAssertEqual(listed.cards.map(\.id), first.ranked.map(\.areaId))
        XCTAssertEqual(listed.cards.map(\.full), Array(repeating: true, count: 5) + Array(repeating: false, count: first.ranked.count - 5))
        XCTAssertTrue(listed.saysFirstFive)
        XCTAssertEqual(listed.lines, [])
        XCTAssertEqual(listed.release, Answers.meta.releaseId)
        XCTAssertEqual(listed.engine, app.state.meta.engineVersion)
    }

    @MainActor
    func test_results_are_drawn_before_their_reasons_and_their_profiles_have_come() async throws {
        let api = StandIn.firstSearch()
        let reasons = api.hold(.explainTop, "explanations-first")
        let profiles = ResultsGate()
        api.on(
            .getArea,
            .made { call in
                try await profiles.wait()
                return try Recorded.read("area/\(call.path.split(separator: "/").last ?? "")")
            })
        let app = try await ResultsApp(api)

        async let sent: Void = app.flow.submitText("leafy")
        await until { app.state.ranking != nil }

        let card = try app.firstCard()
        XCTAssertEqual(card.heading.name, "Farrowmere")
        XCTAssertEqual(card.orientation, .waiting)
        XCTAssertEqual(card.reasons, .waiting)
        XCTAssertEqual(card.tradeOff, .waiting)
        XCTAssertEqual(card.station, .waiting)
        XCTAssertEqual(card.cost, .waiting)
        // What the ranking itself holds is there at once.
        XCTAssertEqual(card.journeys.count, 1)
        XCTAssertNotNil(card.completeness)
        reasons.release()
        profiles.release()
        await sent
        XCTAssertNotNil(try app.firstCard().reasons.value)
        XCTAssertNotNil(try app.firstCard().cost.value)
    }

    @MainActor
    func test_results_the_release_named_under_a_result_is_the_one_that_made_the_ranking() async throws {
        // The service moved to a newer release after the app was opened, and its form cannot be read again.
        let app = try await ResultsApp()
        app.api.movedTo(Answers.newerRelease).on(.getMeta, "error-internal")

        await app.flow.submitText("leafy and quiet")
        await app.flow.caughtUp()

        XCTAssertEqual(app.state.meta.releaseId, Answers.meta.releaseId)
        XCTAssertEqual(app.listed.release, Answers.newerRelease)
        XCTAssertEqual(app.listed.engine, Answers.meta.engineVersion)
    }

    @MainActor
    func test_results_reasons_that_cannot_be_had_are_said_to_have_failed_and_the_ranking_stays() async throws {
        let app = try await ResultsApp.searched(StandIn.firstSearch().on(.explainTop, "error-internal"))

        let card = try app.firstCard()
        XCTAssertEqual(card.reasons, .failed)
        XCTAssertEqual(card.orientation, .hidden)
        XCTAssertEqual(card.tradeOff, .hidden)
        XCTAssertEqual(app.listed.cards.count, first.ranked.count)
        // The card says what it lacks. One line says why, in the API's words, with the id to quote.
        let fault = try Recorded.error("error-internal")
        XCTAssertEqual(app.listed.lines.map(\.kind), [.failure])
        let line = try XCTUnwrap(app.listed.lines.first)
        XCTAssertEqual(line.words, [fault.error.message])
        XCTAssertEqual(line.requestId, try Recorded.read("error-internal").headers["x-request-id"])
        // The reasons are not a fault of the search, so nothing says the results were not updated.
        XCTAssertFalse(line.words.contains(ResultsCopy.Notice.notUpdated))
        // "Try again" ranks again, and asks for what is missing with it.
        XCTAssertEqual(line.presses.map(\.act), [.retry, .startAgain])
        app.api.on(.explainTop, "explanations-first")
        await app.hands.act(.retry)
        XCTAssertEqual(app.listed.lines, [])
        XCTAssertNotNil(try app.firstCard().reasons.value)
    }

    @MainActor
    func test_results_a_profile_that_cannot_be_had_says_so_where_the_cost_would_be() async throws {
        let api = StandIn.firstSearch().on(
            .getArea,
            .made { call in
                try Recorded.read(call.path.hasSuffix("/farrowmere") ? "error-internal" : "area/\(call.path.split(separator: "/").last ?? "")")
            })
        let app = try await ResultsApp.searched(api)

        XCTAssertEqual(try app.firstCard().cost, .failed)
        XCTAssertEqual(try app.firstCard().station, .hidden)
        XCTAssertNotNil(app.listed.cards[1].cost.value)
    }

    // MARK: - Refining

    @MainActor
    func test_refining_the_last_results_stay_and_the_list_says_it_is_updating() async throws {
        let app = try await ResultsApp.searched()
        let before = app.listed.cards
        let slow = app.api.hold(.rank, "rank-refined")
        app.api.on(.explainTop, "explanations-refined")

        async let sent: Void = app.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))
        await until { slow.waiting == 1 }

        XCTAssertEqual(app.state.phase, .refining)
        XCTAssertTrue(app.listed.busy)
        XCTAssertEqual(app.listed.waitingFor, "Working out the ranking again")
        XCTAssertEqual(app.listed.cards, before)
        XCTAssertEqual(app.listed.headline, "21 areas ranked. First: Farrowmere.")
        slow.release()
        await sent
    }

    @MainActor
    func test_refined_the_list_is_the_new_ranking_and_says_how_many_areas_changed_place() async throws {
        let app = try await ResultsApp.searched()
        app.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")

        await app.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))

        let refined = Answers.ranked("rank-refined")
        let moved = try XCTUnwrap(app.state.moved)
        XCTAssertEqual(app.listed.cards.map(\.id), refined.ranked.map(\.areaId))
        XCTAssertEqual(app.listed.headline, "10 areas ranked. First: Farrowmere.")
        XCTAssertEqual(moved, 20)
        XCTAssertEqual(app.listed.changes, ["20 areas changed place."])
        XCTAssertEqual(app.listed.announcement, "10 areas ranked. First: Farrowmere. 20 areas changed place.")
        // The areas a firm limit left out are on the map with lines, and in the table with the reason.
        XCTAssertEqual(app.mapped.regions.filter { $0.fill.pattern == .filtered }.count, refined.filtered.count)
        XCTAssertTrue(app.tabled.rows.contains { $0.status == "A journey is longer than a firm limit" })
    }

    @MainActor
    func test_refined_the_list_says_when_the_settings_nobody_chose_gave_way() async throws {
        // Nothing but a vibe is asked for, so nothing counts for more than it.
        let app = try await ResultsApp(
            StandIn.firstSearch().on(.interpret, "interpret-scale").on(.rank, "rank-scale")
                .on(.explainTop, "explanations-scale"))

        await app.flow.submitText("not buzzy")

        XCTAssertTrue(app.state.gaveWay)
        XCTAssertNil(app.state.leads)
        XCTAssertEqual(app.listed.changes, ["What you asked for counts most."])
    }

    @MainActor
    func test_refined_what_counts_for_more_than_what_was_asked_is_said_in_place_of_it() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.rank, "rank-default-rent"))
        await app.flow.rankNow()
        // The ranking of a person who has made the journey and the budget count for more than the place.
        let led: StandIn.Responder = .made { _ in
            try Recorded.read("rank-refined").with(data: { data in
                data["spec"]?["commute_weight"] = .number(1)
                data["spec"]?["budget"]?["weight"] = .number(0.8)
            })
        }
        app.api.on(.rank, led).on(.explainTop, "explanations-refined")

        await app.flow.applyEdits(Edits.placeAdd("syn-p0021"))

        XCTAssertTrue(app.state.gaveWay)
        XCTAssertEqual(app.state.leads, Leads(journey: true, budget: true, journeys: 1))
        XCTAssertTrue(app.listed.changes.contains("Journey and budget count most."))
        XCTAssertFalse(app.listed.changes.contains("What you asked for counts most."))
    }

    // MARK: - Clarifying a place

    @MainActor
    func test_clarifying_the_rest_is_ranked_and_the_question_leads_back_to_the_search() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.interpret, "interpret-clarify"))

        await app.flow.submitText("near pellam")

        XCTAssertTrue(app.state.conditions.contains(.clarifying))
        XCTAssertEqual(app.listed.cards.count, first.ranked.count)
        let line = try XCTUnwrap(app.listed.lines.first)
        XCTAssertEqual(app.listed.lines.count, 1)
        XCTAssertEqual(line.words, ["Burro has a question about a place."])
        XCTAssertEqual(line.presses, [Results.Press(words: "Go to the search", act: .toSearch)])
        // The question never repeats what was typed, and neither does this line.
        XCTAssertFalse(line.words.joined().lowercased().contains("pellam"))
    }

    // MARK: - Nothing matches

    @MainActor
    func test_nothing_matches_the_list_says_why_and_offers_one_edit_for_each_firm_limit() async throws {
        let api = StandIn.firstSearch()
            .on(.interpret, "interpret-two-journeys")
            .on(.rank, "rank-nothing-matches")
        let app = try await ResultsApp(api)
        await app.flow.loadGeometry()

        await app.flow.submitText("a firm budget")

        let listed = app.listed
        let nothing = try XCTUnwrap(listed.nothing)
        XCTAssertEqual(listed.headline, "No area passes every limit you set.")
        XCTAssertEqual(listed.cards, [])
        XCTAssertFalse(listed.empty)
        XCTAssertEqual(
            nothing.counts,
            [
                .init(reason: "Over your budget, which is a firm limit", areas: "21 areas"),
                .init(reason: "A journey is longer than a firm limit", areas: "1 area"),
                .init(reason: "Not ranked in this data", areas: "2 areas"),
            ])
        let spec = Answers.ranked("rank-nothing-matches").spec
        XCTAssertEqual(spec.budget.strictness, .hard)
        XCTAssertEqual(nothing.ways.first, Results.Press(words: "Make the budget flexible", act: .edit(Edits.budgetStrictness(.soft))))
        XCTAssertEqual(nothing.ways.count, 1 + spec.commutes.filter { $0.strictness == .hard }.count)
        // The map is hatched, and gives no area a pin.
        XCTAssertEqual(app.mapped.marks, [])
        XCTAssertEqual(app.mapped.regions.filter { $0.fill.pattern == .filtered }.count, Answers.ranked("rank-nothing-matches").filtered.count)
        XCTAssertEqual(app.mapped.regions.filter { $0.fill.pattern == .unranked }.count, Answers.ranked("rank-nothing-matches").unranked.count)
        XCTAssertFalse(app.mapped.strokes.isEmpty)
        XCTAssertFalse(app.mapped.dots.isEmpty)
    }

    @MainActor
    func test_nothing_matches_a_press_sends_the_one_edit_that_loosens_the_limit() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.rank, "rank-nothing-matches"))
        await app.flow.rankNow()
        let way = try XCTUnwrap(app.listed.nothing?.ways.first)
        app.api.on(.rank, "rank-first")

        await app.hands.act(way.act)

        let sent = try app.api.lastCall(to: .rank).body(as: RankBody.self)
        XCTAssertEqual(sent.operations, Edits.budgetStrictness(.soft))
        XCTAssertEqual(sent.spec, Answers.ranked("rank-nothing-matches").spec)
        XCTAssertNil(app.listed.nothing)
        XCTAssertEqual(app.listed.cards.count, first.ranked.count)
    }

    // MARK: - Nothing read

    @MainActor
    func test_nothing_read_results_already_on_screen_stay_and_the_line_leads_to_the_settings() async throws {
        let app = try await ResultsApp.searched()
        let before = app.listed.cards
        // The API sends back the spec it was sent when nothing was read.
        app.api.on(.interpret, StandIn.withTheSpecSent("interpret-nothing-read"))

        await app.flow.submitText("hello there")

        XCTAssertEqual(app.state.conditions, [.nothingRead])
        XCTAssertEqual(app.listed.cards, before)
        XCTAssertEqual(
            app.listed.lines,
            [
                Results.Line(
                    .info,
                    [
                        "Nothing in that could be read. Burro reads plain English, such as "
                            + "“leafy and quiet, near a park”. Say it another way, or use the settings."
                    ],
                    presses: [Results.Press(words: "Go to the search", act: .toSearch)])
            ])
        // No new ranking is asked for.
        XCTAssertEqual(app.api.calls(to: .rank).count, 1)
    }

    @MainActor
    func test_nothing_read_the_apis_own_sentence_says_it_where_there_is_one() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.interpret, "interpret-off-topic"))

        await app.flow.submitText("what is the time")

        XCTAssertEqual(app.state.conditions, [.nothingRead, .notice])
        XCTAssertEqual(
            app.listed.lines,
            [Results.Line(.notice, [Answers.read("interpret-off-topic").noticeText])])
        XCTAssertTrue(app.listed.empty)
    }

    @MainActor
    func test_nothing_changed_is_told_apart_from_nothing_read() async throws {
        let app = try await ResultsApp.searched()
        app.api.on(
            .interpret,
            .made { call in
                try Recorded.read("interpret-second-sentence").with(data: { data in
                    // The API sends back the spec it was sent when nothing changed.
                    if let spec = call.body?["spec"] { data["spec"] = spec }
                    guard case .array(let applied)? = data["applied"] else { return }
                    data["applied"] = .array(
                        applied.map { one in
                            var one = one
                            one["changed"] = .bool(false)
                            return one
                        })
                    data["rejected"] = .array([])
                })
            })

        await app.flow.submitText("renting")

        XCTAssertEqual(app.state.conditions, [.nothingChanged])
        XCTAssertEqual(
            app.listed.lines, [Results.Line(.info, ["That changed nothing. Your search already says it."])])
        XCTAssertEqual(app.listed.cards.count, first.ranked.count)
    }

    // MARK: - What was noticed, what was not read, and what the data does not hold

    @MainActor
    func test_suggestions_nothing_is_ranked_from_what_was_noticed_and_the_line_leads_to_the_search() async throws {
        let app = try await ResultsApp.searched()
        let before = app.listed.cards
        app.api.on(.interpret, StandIn.withTheSpecSent("interpret-suggest"))

        await app.flow.submitText("pubs are so noisy")

        XCTAssertEqual(app.state.conditions, [.suggesting])
        XCTAssertEqual(
            app.listed.lines,
            [
                Results.Line(
                    .info, ["Choose what to add"],
                    presses: [Results.Press(words: "Go to the search", act: .toSearch)])
            ])
        // Nothing of what was noticed is applied: the results are as they were, and nothing new is asked for.
        XCTAssertEqual(app.listed.cards, before)
        XCTAssertEqual(app.api.calls(to: .rank).count, 1)
        XCTAssertEqual(app.state.spec, Answers.ranked("rank-first").spec)
    }

    @MainActor
    func test_read_in_part_the_ranking_is_shown_and_the_list_says_it_leaves_the_rest_out() async throws {
        let api = StandIn.firstSearch().on(
            .interpret,
            .made { _ in
                try Recorded.read("interpret-first").with(data: { data in
                    data["unread"] = .array([.object(["start": .number(0), "end": .number(7)])])
                })
            })
        let app = try await ResultsApp(api)

        await app.flow.submitText("leafy and quiet")

        XCTAssertEqual(app.state.conditions, [.readInPart])
        XCTAssertEqual(app.listed.cards.count, first.ranked.count)
        XCTAssertEqual(
            app.listed.lines,
            [
                Results.Line(
                    .info,
                    [
                        "Burro read only part of what you typed, and the ranking leaves the rest out. "
                            + "Say the rest again in shorter sentences, one thing in each, or use the settings."
                    ],
                    presses: [Results.Press(words: "Go to the search", act: .toSearch)])
            ])
        // Where the words stand is never drawn, and neither are the words.
        XCTAssertFalse(ResultsDrawn.all(in: app.listed).texts.contains { $0.contains("leafy and") })
    }

    @MainActor
    func test_not_in_the_data_what_was_asked_for_is_said_by_name_with_what_it_waits_on() async throws {
        let app = try await ResultsApp(
            StandIn.firstSearch()
                .on(.getMeta, "preview/meta").on(.listAreas, "preview/areas")
                .on(.interpret, "preview/interpret-plain").on(.rank, "preview/rank-plain")
                .on(.explainTop, "preview/explanations-plain"))

        await app.flow.submitText("leafy and quiet")

        XCTAssertEqual(app.state.conditions, [.notInData])
        XCTAssertEqual(
            app.listed.lines,
            [
                Results.Line(
                    .info,
                    [
                        "Not in this data yet",
                        "You asked for one thing this data cannot answer yet. It counts for nothing in the ranking.",
                        "Leafy. No area can be placed on it yet. It waits on: "
                            + "Land that is residential garden, 40 of 100; Land that is woodland, 30 of 100.",
                    ])
            ])
        XCTAssertEqual(app.listed.cards.count, Answers.ranked("preview/rank-plain").ranked.count)
        XCTAssertTrue(app.app.preview.seen)
    }

    // MARK: - Degraded to a form

    @MainActor
    func test_degraded_the_rules_read_the_words_and_their_results_show_as_usual() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.interpret, "interpret-degraded"))

        await app.flow.submitText("leafy")

        XCTAssertTrue(app.state.conditions.contains(.degraded))
        XCTAssertEqual(app.listed.cards.count, first.ranked.count)
        XCTAssertEqual(
            app.listed.lines,
            [
                Results.Line(
                    .info, ["Your words could not be read just now. The settings do the same job."],
                    presses: [Results.Press(words: "Go to the search", act: .toSearch)])
            ])
    }

    @MainActor
    func test_degraded_the_list_says_when_the_language_model_would_not_read_the_words() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.interpret, "interpret-refused"))

        await app.flow.submitText("leafy")

        XCTAssertTrue(app.state.modelRefused)
        XCTAssertEqual(app.listed.cards.count, first.ranked.count)
        XCTAssertEqual(
            app.listed.lines,
            [
                Results.Line(
                    .info, ["The language model would not read this. Burro's rules have read it instead."],
                    presses: [Results.Press(words: "Go to the search", act: .toSearch)])
            ])
    }

    @MainActor
    func test_degraded_a_reading_that_failed_is_not_a_fault_to_report() async throws {
        let app = try await ResultsApp.searched()
        app.api.on(.interpret, "error-internal")

        await app.flow.submitText("leafy")

        XCTAssertEqual(app.state.failurePlace, .form)
        XCTAssertEqual(app.listed.lines.map(\.kind), [.info])
        XCTAssertEqual(
            app.listed.lines.first?.words,
            ["Your words could not be read just now. The settings do the same job."])
        // The last results stay readable.
        XCTAssertEqual(app.listed.cards.count, first.ranked.count)
    }

    // MARK: - Neutral notice

    @MainActor
    func test_notice_the_apis_sentence_is_shown_word_for_word_above_the_results() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.interpret, "interpret-notice"))

        await app.flow.submitText("leafy")

        let said = Answers.read("interpret-notice").noticeText
        XCTAssertEqual(app.listed.lines, [Results.Line(.notice, [said])])
        XCTAssertFalse(said.isEmpty)
        XCTAssertEqual(app.listed.cards.count, first.ranked.count)
    }

    // MARK: - Error from the API

    @MainActor
    func test_error_the_last_results_stay_marked_not_updated_with_the_message_and_the_id_to_quote() async throws {
        let app = try await ResultsApp.searched()
        let before = app.listed.cards
        app.api.on(.rank, "error-internal")

        await app.flow.applyEdits(Edits.tagOn(.villageFeel))

        let line = try XCTUnwrap(app.listed.lines.first)
        XCTAssertEqual(app.listed.lines.count, 1)
        XCTAssertEqual(line.kind, .failure)
        XCTAssertEqual(line.words, ["Something went wrong on the server.", "These results were not updated."])
        XCTAssertEqual(line.requestId, try Recorded.read("error-internal").headers["x-request-id"])
        XCTAssertEqual(line.presses.map(\.words), ["Try again", "Start again"])
        XCTAssertEqual(line.presses.map(\.act), [.retry, .startAgain])
        XCTAssertEqual(app.listed.cards, before)
        XCTAssertFalse(app.listed.busy)
    }

    @MainActor
    func test_error_trying_again_sends_the_edit_that_waited() async throws {
        let app = try await ResultsApp.searched()
        app.api.on(.rank, "error-internal")
        await app.flow.applyEdits(Edits.tagOn(.villageFeel))
        app.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")

        await app.hands.act(.retry)

        XCTAssertEqual(try app.api.lastCall(to: .rank).body(as: RankBody.self).operations, Edits.tagOn(.villageFeel))
        XCTAssertEqual(app.listed.lines, [])
        XCTAssertEqual(app.listed.cards.count, Answers.ranked("rank-refined").ranked.count)
    }

    @MainActor
    func test_error_a_search_that_names_what_the_data_no_longer_has_is_put_right_by_one_press() async throws {
        let stale = try JSONDecoder().decode(
            RankBody.self, from: XCTUnwrap(Recorded.read("rank-stale-spec").sent))
        let staleSpec = try JSON.written(stale.spec)
        let api = StandIn.firstSearch().on(
            .rank, .made { _ in try Recorded.read("rank-first").with(data: { $0["spec"] = staleSpec }) })
        let app = try await ResultsApp(api)
        await app.flow.rankNow()
        XCTAssertEqual(app.state.spec, stale.spec)
        app.api.on(.rank, "rank-stale-spec")

        await app.flow.rankNow()

        let line = try XCTUnwrap(app.listed.lines.first)
        XCTAssertEqual(line.kind, .failure)
        XCTAssertEqual(
            line.words,
            ["Your search names something this data no longer has.", "These results were not updated."])
        XCTAssertEqual(line.presses.map(\.words), ["Take the place out", "Try again", "Start again"])
        XCTAssertEqual(line.presses.first?.act, .edit(Edits.placeRemove("syn-p9999")))
        // The id of the place is never drawn.
        XCTAssertFalse(ResultsDrawn.all(in: app.listed).texts.contains { $0.contains("syn-p9999") })

        app.api.on(.rank, "rank-stale-spec-repaired")
        await app.hands.act(try XCTUnwrap(line.presses.first).act)

        XCTAssertEqual(
            try app.api.lastCall(to: .rank).body(as: RankBody.self),
            RankBody(spec: stale.spec, limit: 20, operations: Edits.placeRemove("syn-p9999")))
        XCTAssertEqual(app.listed.lines, [])
    }

    @MainActor
    func test_error_a_refusal_of_the_words_is_said_in_the_apis_words_and_leads_to_the_box() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.interpret, "interpret-invalid-text"))

        await app.flow.submitText("?")

        XCTAssertEqual(app.state.failurePlace, .box)
        XCTAssertEqual(
            app.listed.lines,
            [
                Results.Line(
                    .failure, [try Recorded.error("interpret-invalid-text").error.message],
                    presses: [Results.Press(words: "Go to the search", act: .toSearch)])
            ])
    }

    @MainActor
    func test_error_a_call_that_gave_no_answer_is_never_met_with_silence() async throws {
        let app = try await ResultsApp.searched()
        app.api.unreachable(.rank)

        await app.flow.applyEdits(Edits.tagOn(.villageFeel))

        XCTAssertEqual(
            app.listed.lines.first?.words, ["Burro could not be reached.", "These results were not updated."])
        XCTAssertEqual(app.listed.lines.first?.presses.first?.act, .retry)
    }

    @MainActor
    func test_error_starting_again_forgets_the_search_and_the_list_waits() async throws {
        let app = try await ResultsApp.searched()
        app.api.on(.rank, "error-internal")
        await app.flow.applyEdits(Edits.tagOn(.villageFeel))

        await app.hands.act(.startAgain)

        XCTAssertTrue(app.listed.empty)
        XCTAssertEqual(app.listed.lines, [])
        XCTAssertEqual(app.state.spec, Answers.meta.defaults.rent)
    }

    // MARK: - Offline

    @MainActor
    func test_offline_the_results_stay_readable_and_the_latest_edit_waits() async throws {
        let app = try await ResultsApp.searched()
        let before = app.listed.cards
        app.api.unreachable(.rank, .notConnectedToInternet)

        await app.flow.applyEdits(Edits.tagOn(.villageFeel))

        XCTAssertEqual(app.state.conditions, [.offline])
        XCTAssertEqual(
            app.listed.lines,
            [
                Results.Line(
                    .offline,
                    [
                        "You are offline. Your search is still here.",
                        "Your last change will be sent when you are back online.",
                    ])
            ])
        XCTAssertEqual(app.listed.cards, before)
    }

    @MainActor
    func test_offline_the_edit_is_sent_once_when_the_phone_is_back() async throws {
        let app = try await ResultsApp.searched()
        app.api.unreachable(.rank, .notConnectedToInternet)
        await app.flow.applyEdits(Edits.tagOn(.villageFeel))
        app.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")

        await app.flow.wentOnline()

        XCTAssertEqual(app.listed.lines, [])
        XCTAssertEqual(app.listed.cards.count, Answers.ranked("rank-refined").ranked.count)
    }

    // MARK: - A shared search, and nothing to rank by

    @MainActor
    func test_a_shared_search_says_that_it_came_from_a_link_and_what_that_means() async throws {
        let api = StandIn.firstSearch().on(.getShare, "share-opened")
        let app = try await ResultsApp(api)

        let failure = await app.flow.openShare(Answers.shareId)

        XCTAssertNil(failure)
        let line = try XCTUnwrap(app.listed.lines.first)
        XCTAssertEqual(line.kind, .info)
        XCTAssertEqual(
            line.words,
            [
                "A shared search",
                "This search was opened from a link. Changing it here does not change the link.",
                ResultsCopy.Notice.sharedCoarsened,
            ])
        XCTAssertFalse(app.listed.cards.isEmpty)
        // The id of the share is never drawn.
        XCTAssertFalse(ResultsDrawn.all(in: app.listed).texts.contains { $0.contains(Answers.shareId) })
    }

    @MainActor
    func test_a_shared_search_on_newer_data_says_the_ranking_may_differ() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.getShare, "share-opened-stale"))

        _ = await app.flow.openShare(Answers.shareId(askedForIn: "share-opened-stale"))

        XCTAssertEqual(app.listed.lines.first?.words.last, ResultsCopy.Notice.sharedStale)
    }

    @MainActor
    func test_nothing_to_rank_by_no_area_is_given_a_fit_a_band_or_a_pin() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.rank, "rank-empty-spec"))
        await app.flow.loadGeometry()

        await app.flow.rankNow()

        let count = Answers.ranked("rank-empty-spec").scores.count
        XCTAssertEqual(
            app.listed.headline,
            "\(count) areas pass. Nothing is set to rank them by, so they are in no order.")
        XCTAssertTrue(app.listed.cards.allSatisfy { $0.heading.fit == nil && $0.heading.fitWords == nil })
        XCTAssertTrue(app.listed.cards.allSatisfy { $0.completeness == nil && $0.breakdown.isEmpty })
        XCTAssertEqual(app.mapped.marks, [])
        XCTAssertTrue(app.mapped.regions.allSatisfy { $0.fill.band == 0 })
        XCTAssertTrue(app.tabled.rows.allSatisfy { $0.fit == nil })
        XCTAssertEqual(app.mapped.legend.first?.words, "No fit yet")
    }

    // MARK: - Every state has a test

    func test_every_state_of_the_website_is_shown_by_a_test_here() throws {
        let tests = try Repository.text(
            Repository.tests.appendingPathComponent("Features/Results/ResultsStatesTests.swift"))
        let states = [
            "test_empty_", "test_interpreting_", "test_results_", "test_refining_", "test_clarifying_",
            "test_nothing_matches_", "test_nothing_read_", "test_degraded_", "test_notice_", "test_error_",
            "test_offline_", "test_suggestions_", "test_read_in_part_", "test_not_in_the_data_",
        ]

        for state in states { XCTAssertTrue(tests.contains("func \(state)"), state) }
        // One for each phase and each condition the search can be in.
        XCTAssertEqual(Phase.allCases.count, 4)
        XCTAssertEqual(SearchCondition.allCases.count, 11)
    }
}
