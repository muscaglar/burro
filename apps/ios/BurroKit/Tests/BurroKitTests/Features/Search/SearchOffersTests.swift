import XCTest

@testable import BurroKit

/// What Burro noticed and did not apply, what it did not read, and what was
/// asked for that the data does not hold: what the search screen shows of
/// each, and what a press sends. Nothing is applied until a person chooses.
final class SearchOffersTests: XCTestCase {
    @MainActor
    private func noticed(_ reading: String, then ranking: String = "rank-suggestion-chosen") async
        -> OpenSearch
    {
        let search = OpenSearch(StandIn.firstSearch().on(.interpret, reading).on(.rank, ranking))
        await search.flow.submitText("what was typed")
        return search
    }

    private func sent(in scenario: String) throws -> JSON? {
        try JSON.read(XCTUnwrap(Recorded.read(scenario).sent))["operations"]
    }

    // MARK: - What is offered

    @MainActor
    func test_what_was_noticed_is_offered_and_nothing_of_it_is_applied_or_ranked() async {
        let search = await noticed("interpret-suggest")
        let shown = search.shown()

        XCTAssertEqual(search.api.routes, [.interpret])
        XCTAssertEqual(search.state.spec, Answers.meta.defaults.rent)
        XCTAssertFalse(shown.hasRanking)
        XCTAssertEqual(shown.status, "")
        XCTAssertEqual(shown.chips.map(\.reads), ["Renting assumed", "Usual settings: 6 assumed"])
        // The line that says nothing was read is not said: there is something to choose.
        XCTAssertNil(shown.nothingRead)
        XCTAssertEqual(shown.unmet, [])
        XCTAssertFalse(shown.settingsOpen)
        XCTAssertEqual(
            shown.parts, [.box, .examples, .basics, .status, .chips, .offers, .unread, .settings])
        XCTAssertFalse(SearchScreen.leadsToResults(search.state))
    }

    @MainActor
    func test_an_offer_is_the_apis_name_for_the_thing_and_the_apis_words_for_each_choice() async throws {
        let search = await noticed("interpret-suggest")
        let offers = try XCTUnwrap(search.shown().offers)

        XCTAssertEqual(offers.offers.map(\.name), ["Pubs and bars", "Less transport noise"])
        XCTAssertEqual(
            offers.offers.map { $0.choices.map(\.label) },
            [["More pubs and bars", "Fewer pubs and bars", "Leave it out"], ["Less transport noise", "Leave it out"]])
        // A thing that could be meant two ways is named before its choices. One there is
        // one way to want is named by its button alone.
        XCTAssertEqual(offers.offers.map(\.named), [true, false])
        // "Leave it out" is said of every thing, so each says what it leaves out.
        XCTAssertEqual(
            offers.offers.map { $0.choices.last?.spoken },
            ["Leave it out: Pubs and bars", "Leave it out: Less transport noise"])
        XCTAssertEqual(offers.offers.map(\.note), [nil, nil])
        // Where the words it rests on stand is held as offsets, and never as words.
        XCTAssertEqual(offers.offers.map(\.spans), [[Span(start: 0, end: 4)], [Span(start: 12, end: 17)]])
        XCTAssertFalse(String(reflecting: offers).contains("noisy"))
        // One thing that needs no choice is added by its own button.
        XCTAssertNil(offers.addAll)
        XCTAssertNil(offers.showAll)
    }

    @MainActor
    func test_a_choice_sends_the_edits_the_api_gave_for_it_as_a_control_does() async throws {
        let search = await noticed("interpret-suggest")

        await search.flow.choose(at: 0, direction: .less)

        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(try JSON.written(asked), try sent(in: "rank-suggestion-chosen"))
        XCTAssertEqual(search.api.calls(to: .interpret).count, 1)
        XCTAssertEqual(search.state.spec, Answers.ranked("rank-suggestion-chosen").spec)
        // The thing that was chosen of is gone, and the other still waits.
        XCTAssertEqual(search.shown().offers?.offers.map(\.name), ["Less transport noise"])
        XCTAssertTrue(search.shown().hasRanking)
        XCTAssertTrue(
            search.shown().chips.map(\.reads).contains("Pubs, bars and evening venues, fewer"))
    }

    @MainActor
    func test_leaving_a_thing_out_takes_it_away_and_sends_nothing() async {
        let search = await noticed("interpret-suggest")
        let calls = search.api.calls.count

        await search.flow.choose(at: 1, direction: .ignore)

        XCTAssertEqual(search.api.calls.count, calls)
        XCTAssertEqual(search.shown().offers?.offers.map(\.name), ["Pubs and bars"])
        XCTAssertEqual(search.state.spec, Answers.meta.defaults.rent)
        // A choice the thing does not have does nothing.
        await search.flow.choose(at: 0, direction: .unlisted("sideways"))
        await search.flow.choose(at: 9, direction: .more)
        XCTAssertEqual(search.api.calls.count, calls)
        XCTAssertEqual(search.shown().offers?.offers.count, 1)
    }

    @MainActor
    func test_add_all_adds_only_what_there_is_one_way_to_want_and_leaves_each_question_asked() async throws {
        let search = await noticed("interpret-suggest-many", then: "rank-first")
        let offers = try XCTUnwrap(search.shown().offers)
        let suggestions = Answers.read("interpret-suggest-many").suggestions

        XCTAssertEqual(offers.offers.count, 6)
        XCTAssertEqual(offers.offers.map(\.named), [true, true, true, false, false, false])
        XCTAssertEqual(offers.addAll, "Add the 3 that need no choice")
        XCTAssertEqual(offers.addAllAts, [3, 4, 5])
        await search.flow.chooseAll(offers.addAllAts)

        // One request, with the edits of each choice as the API gave them, in the order noticed.
        XCTAssertEqual(search.api.calls(to: .rank).count, 1)
        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(
            asked,
            [3, 4, 5].compactMap { suggestions[$0].addedWithOthers?.operations }
                .reduce(Operations.none) { $0.merged(with: $1) })
        XCTAssertEqual(asked.weightOps.map(\.featureId), [.playSpaceProximity, .waterAccess, .airNo2])
        // What could be meant two ways is still a question.
        XCTAssertEqual(
            search.shown().offers?.offers.map(\.name),
            ["Pubs and bars", "Nearer a station", "Nearer a town centre"])
        XCTAssertNil(search.shown().offers?.addAll)
    }

    @MainActor
    func test_add_all_never_takes_a_thing_that_could_be_meant_two_ways_whatever_it_is_handed() async throws {
        let search = await noticed("interpret-suggest-many", then: "rank-first")

        await search.flow.chooseAll([0, 1, 2])
        XCTAssertEqual(search.api.calls(to: .rank).count, 0)
        XCTAssertEqual(search.shown().offers?.offers.count, 6)
        await search.flow.chooseAll([0, 3, 3, 17])

        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(asked.weightOps.map(\.featureId), [.playSpaceProximity])
        XCTAssertEqual(search.shown().offers?.offers.count, 5)
    }

    func test_a_thing_that_carries_a_note_is_never_added_with_others() throws {
        let plain = try XCTUnwrap(Answers.read("interpret-suggest-notice").suggestions.first)
        let noted = plain.with(note: "Recorded crime counts only when you ask for it by name.")
        let blank = plain.with(note: "  ")

        XCTAssertNotNil(plain.addedWithOthers)
        XCTAssertNil(noted.addedWithOthers)
        XCTAssertEqual(noted.noteShown, "Recorded crime counts only when you ask for it by name.")
        XCTAssertNil(blank.noteShown)
        XCTAssertNotNil(blank.addedWithOthers)
        let offers = try XCTUnwrap(SearchScreen.offers([noted, noted, plain, plain], all: false))
        // The note is drawn once, with the first of the things that share it.
        XCTAssertEqual(offers.offers.map(\.noteDrawn), [true, false, false, false])
        XCTAssertEqual(offers.addAllAts, [2, 3])
        XCTAssertEqual(offers.addAll, "Add the 2 that need no choice")
    }

    func test_what_waits_out_of_sight_is_only_what_is_a_question() throws {
        let many = Answers.read("interpret-suggest-many").suggestions
        // Three things there is one way to want, and then three that could be meant two ways.
        let mixed = Array(many[3...5]) + Array(many[0...2])

        let first = try XCTUnwrap(SearchScreen.offers(mixed, all: false))
        let all = try XCTUnwrap(SearchScreen.offers(mixed, all: true))

        XCTAssertEqual(SearchScreen.inSight(mixed), [0, 1, 2, 3])
        XCTAssertEqual(SearchScreen.inSight(many), [0, 1, 2, 3, 4, 5])
        XCTAssertEqual(first.offers.map(\.at), [0, 1, 2, 3])
        XCTAssertEqual(first.showAll, "Show all 6")
        XCTAssertEqual(first.addAll, "Add the 3 that need no choice")
        XCTAssertEqual(all.offers.map(\.at), [0, 1, 2, 3, 4, 5])
        XCTAssertNil(all.showAll)
        XCTAssertEqual(all.addAllAts, [0, 1, 2])
        XCTAssertNil(SearchScreen.offers([], all: true))
        // Where every thing in sight needs no choice, the button says how many it adds.
        XCTAssertEqual(SearchScreen.offers(Array(many[3...5]), all: false)?.addAll, "Add all 3")
    }

    @MainActor
    func test_a_choice_that_changes_the_search_takes_the_notice_with_it() async {
        let search = await noticed("interpret-suggest-notice", then: "rank-first")
        XCTAssertEqual(search.shown().notice, Answers.read("interpret-suggest-notice").noticeText)
        XCTAssertEqual(search.shown().offers?.addAll, "Add all 2")

        await search.flow.choose(at: 1, direction: .ignore)
        XCTAssertNotNil(search.shown().notice)
        await search.flow.choose(at: 0, direction: .more)

        // The notice ended by saying that nothing typed had changed the search. Now something has.
        XCTAssertNil(search.shown().notice)
        XCTAssertNil(search.shown().offers)
        XCTAssertEqual(search.api.calls(to: .rank).count, 1)
    }

    @MainActor
    func test_what_was_offered_goes_when_the_box_changes_or_another_sentence_is_read() async {
        let search = await noticed("interpret-suggest")

        search.flow.boxChanged()

        XCTAssertNil(search.shown().offers)
        XCTAssertEqual(search.shown().unread, [])
        XCTAssertEqual(search.api.calls.count, 1)
        let again = await noticed("interpret-suggest")
        again.api.on(.interpret, "interpret-first").on(.rank, "rank-first")
        await again.flow.submitText("another sentence")
        XCTAssertNil(again.shown().offers)
        XCTAssertEqual(again.shown().unread, [])
    }

    @MainActor
    func test_nothing_is_offered_while_a_sentence_is_being_read() async {
        let search = await noticed("interpret-suggest")
        let reading = search.api.hold(.interpret, "interpret-first")

        async let sent: Void = search.flow.submitText("another sentence")
        await until { reading.waiting == 1 }

        XCTAssertNil(search.shown().offers)
        XCTAssertEqual(search.shown().unread, [])
        XCTAssertEqual(search.shown().notInData, [])
        reading.release()
        await sent
    }

    // MARK: - What was not read

    @MainActor
    func test_something_read_and_a_stretch_left_unread_says_so_and_stays_on_the_screen() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(
                .interpret,
                .made { _ in
                    try Recorded.read("interpret-first").with(data: { data in
                        data["unread"] = .array([.object(["start": .number(0), "end": .number(7)])])
                    })
                }))
        let before = search.state.answers

        await search.flow.submitText("leafy and quiet")
        let shown = search.shown()

        XCTAssertTrue(shown.readInPart)
        XCTAssertEqual(shown.unread, [Span(start: 0, end: 7)])
        XCTAssertTrue(shown.hasRanking)
        XCTAssertEqual(
            shown.parts,
            [.box, .examples, .basics, .status, .readInPart, .chips, .unread, .results, .settings])
        // The person reads that a part was left out before they are shown the ranking.
        XCTAssertFalse(SearchScreen.arrives(search.state, since: before, onTop: true))
        XCTAssertEqual(
            SearchCopy.Notice.partUnread,
            "Burro read only part of what you typed, and the ranking leaves the rest out. "
                + "Say the rest again in shorter sentences, one thing in each, or use the settings.")
    }

    func test_a_stretch_is_found_in_the_box_by_where_it_stood_in_what_was_sent() {
        let typed = "Pubs are so noisy"
        func words(_ box: String, _ spans: [Span]) -> [String] {
            BoxSpans.inTheBox(box, spans).map { String(box[$0]) }
        }

        XCTAssertEqual(words(typed, [Span(start: 0, end: 4), Span(start: 12, end: 17)]), ["Pubs", "noisy"])
        XCTAssertEqual(words(typed, [Span(start: 5, end: 11)]), ["are so"])
        // What was sent had no space before it or after it. The box may.
        XCTAssertEqual(words("  \n\(typed)  ", [Span(start: 0, end: 4), Span(start: 12, end: 17)]), ["Pubs", "noisy"])
        // A stretch that is empty, or that falls outside what was sent, is left out.
        XCTAssertEqual(words(typed, [Span(start: 4, end: 4), Span(start: 9, end: 5), Span(start: 12, end: 18)]), [])
        XCTAssertEqual(words(typed, [Span(start: -1, end: 3)]), [])
        XCTAssertEqual(words("   ", [Span(start: 0, end: 1)]), [])
        XCTAssertEqual(words("", [Span(start: 0, end: 1)]), [])
        // An offset counts code points. A letter made of two is selected whole.
        let accented = "cafe\u{301} noisy"
        XCTAssertEqual(words(accented, [Span(start: 6, end: 11)]), ["noisy"])
        XCTAssertEqual(words(accented, [Span(start: 0, end: 4)]), ["cafe\u{301}"])
    }

    func test_each_press_shows_the_next_stretch_and_the_first_again_after_the_last() {
        let box = "one two three"
        let found = BoxSpans.inTheBox(box, [Span(start: 0, end: 3), Span(start: 8, end: 13)])

        let first = Showing().next(of: .unread, in: found)
        let second = first.next(of: .unread, in: found)
        let third = second.next(of: .unread, in: found)
        let other = second.next(of: .offer(0), in: Array(found.prefix(1)))
        let none = second.next(of: .unread, in: [])

        XCTAssertNil(Showing().said)
        XCTAssertEqual([first.at, second.at, third.at], [1, 2, 1])
        XCTAssertEqual([first.among, second.among, third.among], [2, 2, 2])
        XCTAssertEqual(first.select.map { String(box[$0.range]) }, "one")
        XCTAssertEqual(second.select.map { String(box[$0.range]) }, "three")
        XCTAssertEqual(first.said, "Part 1 of the 2 that were not read is selected in the box.")
        XCTAssertEqual(second.said, "Part 2 of the 2 that were not read is selected in the box.")
        // The same stretch can be shown again: each press is a new one.
        XCTAssertNotEqual(first.select, third.select)
        XCTAssertEqual(other.at, 1)
        XCTAssertEqual(other.said, "The words are selected in the box.")
        XCTAssertNil(none.select)
        XCTAssertEqual(none.said, "Burro cannot show which part it was.")
        XCTAssertEqual(
            Showing().next(of: .unread, in: Array(found.prefix(1))).said,
            "The part that was not read is selected in the box.")
        // It holds where a stretch stands, and never the words.
        XCTAssertFalse(String(reflecting: second).contains("three"))
    }

    // MARK: - What the data does not hold

    @MainActor
    private func preview(_ reading: String, then ranking: String = "preview/rank-plain") async throws
        -> OpenSearch
    {
        let meta: MetaData = try Recorded.data(.getMeta, "preview/meta")
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, reading).on(.rank, ranking)
                .on(.explainTop, "preview/explanations-plain"),
            meta: meta)
        await search.flow.submitText("what was typed")
        return search
    }

    @MainActor
    func test_a_vibe_the_data_cannot_place_is_said_by_name_with_what_it_waits_on() async throws {
        let search = try await preview("preview/interpret-plain")
        let shown = search.shown()

        XCTAssertEqual(
            shown.notInData,
            [
                "Leafy. No area can be placed on it yet. It waits on: "
                    + "Land that is residential garden, 40 of 100; Land that is woodland, 30 of 100."
            ])
        XCTAssertEqual(
            shown.notInDataLead,
            "You asked for one thing this data cannot answer yet. It counts for nothing in the ranking.")
        // It is said once, and not again among what was not applied.
        XCTAssertEqual(shown.notApplied, [])
        // The rest of what was read is applied and ranked.
        XCTAssertTrue(shown.hasRanking)
        XCTAssertTrue(shown.chips.map(\.label).contains("Quiet streets"))
        XCTAssertFalse(shown.chips.map(\.label).contains("Leafy"))
        XCTAssertEqual(
            shown.parts, [.box, .examples, .basics, .status, .notInData, .chips, .results, .settings])
        XCTAssertFalse(SearchScreen.leadsToResults(search.state))
    }

    @MainActor
    func test_a_budget_and_a_journey_the_data_cannot_answer_are_named_by_the_app_and_never_by_what_was_typed()
        async throws
    {
        let search = try await preview("preview/interpret-long")
        let shown = search.shown()

        XCTAssertEqual(
            shown.notInData,
            [
                "More culture nearby. This data holds no figure for it.",
                "A journey. This data names no place to reach and holds no journey times.",
                "What you can pay. This data holds no rents and no prices, so a budget cannot be tested.",
            ])
        XCTAssertEqual(
            shown.notInDataLead,
            "You asked for 3 things this data cannot answer yet. They count for nothing in the ranking.")
        // The API's name for the budget holds the amount that was typed. The screen does not.
        XCTAssertFalse(String(reflecting: shown.notInData).contains("350"))
        XCTAssertEqual(shown.offers?.offers.map(\.name), ["Quiet streets", "Nearer a park", "Buying"])
        XCTAssertEqual(search.api.routes, [.interpret])
    }

    @MainActor
    func test_the_box_asks_only_for_what_the_data_can_answer_and_offers_no_field_for_a_place() throws {
        let meta: MetaData = try Recorded.data(.getMeta, "preview/meta")
        let lacking = OpenSearch(meta: meta).shown()
        let whole = OpenSearch().shown()

        XCTAssertEqual(
            lacking.hint, "Say what you want nearby. This data holds no rents, no prices and no journey times yet.")
        XCTAssertTrue(lacking.noPlaces)
        XCTAssertEqual(
            whole.hint, "Say what you can pay, where you need to get to, and what you want nearby.")
        XCTAssertFalse(whole.noPlaces)
        XCTAssertEqual(
            SearchCopy.Prompt.hint(costs: true, journeys: false),
            "Say what you can pay and what you want nearby. This data holds no journey times yet.")
        XCTAssertEqual(
            SearchCopy.Prompt.hint(costs: false, journeys: true),
            "Say where you need to get to and what you want nearby. This data holds no rents and no prices yet.")
        XCTAssertEqual(
            SearchCopy.Place.notInData,
            "This data names no places yet, so Burro cannot work out a journey. Nothing you type here could match.")
    }

    func test_what_the_release_holds_is_read_off_what_the_api_serves() throws {
        let preview: MetaData = try Recorded.data(.getMeta, "preview/meta")

        XCTAssertFalse(preview.holds.costs)
        XCTAssertFalse(preview.holds.journeys)
        XCTAssertTrue(Answers.meta.holds.costs)
        XCTAssertTrue(Answers.meta.holds.journeys)
        XCTAssertFalse(ReleaseHolds.isPlaced(.leafy, in: preview))
        XCTAssertTrue(ReleaseHolds.isPlaced(.quietResidential, in: preview))
        XCTAssertTrue(ReleaseHolds.isPlaced(.leafy, in: Answers.meta))
        XCTAssertEqual(ReleaseHolds.recipe(of: .leafy, in: preview)?.held, 30)
        XCTAssertNil(ReleaseHolds.recipe(of: .unlisted("a_vibe_of_next_year"), in: preview))
    }
}

extension Suggestion {
    /// The same thing as it was noticed, with another note.
    fileprivate func with(note: String) -> Suggestion {
        Suggestion(
            target: target, label: label, does: does, spans: spans, shown: shown, follows: follows,
            said: said, choices: choices, note: note, readBy: readBy, addAll: addAll, needs: needs,
            asksPlace: asksPlace, namedAt: namedAt, options: options)
    }
}
