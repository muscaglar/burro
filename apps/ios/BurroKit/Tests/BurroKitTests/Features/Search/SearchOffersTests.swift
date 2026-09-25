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

    /// The sentence a reading was recorded of, as it was sent. It is made up for the
    /// recording, and is what the box holds while what was read of it is offered.
    private func typed(in scenario: String) throws -> String {
        try XCTUnwrap(JSON.read(XCTUnwrap(Recorded.read(scenario).sent))["text"]?.string)
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
    func test_an_offer_is_in_four_parts_and_every_word_of_it_is_the_apis() async throws {
        let search = await noticed("interpret-suggest")
        let offers = try XCTUnwrap(search.shown().offers)

        // What it would do. Where Burro has no guess, it is a question.
        XCTAssertEqual(
            offers.offers.map(\.does), ["Pubs and bars: more, or fewer?", "Less transport noise: count it?"])
        // Where the person's own words stand: the clause, which here is the whole sentence.
        XCTAssertEqual(offers.offers.map(\.shown), [Span(start: 0, end: 17), Span(start: 0, end: 17)])
        XCTAssertEqual(
            try offers.offers.map { BoxSpans.written(try typed(in: "interpret-suggest"), $0.shown) },
            ["Pubs are so noisy", "Pubs are so noisy"])
        // What follows.
        XCTAssertEqual(
            offers.offers.map(\.follows),
            [
                ["What Burro counts: pubs and bars for each 1,000 homes within 800 m, in a straight line."],
                ["What Burro counts: share of residents exposed to 55 dB or more of transport noise."],
            ])
        // The choices. Doing nothing is "Skip", and is last.
        XCTAssertEqual(
            offers.offers.map { $0.choices.map(\.label) },
            [["More pubs and bars", "Fewer pubs and bars", "Skip"], ["Add", "Skip"]])
        XCTAssertEqual(offers.offers.map { $0.choices.map(\.guess) }, [[false, false, false], [false, false]])
        XCTAssertEqual(offers.offers.map(\.name), ["Pubs and bars", "Less transport noise"])
        // "Add" and "Skip" are said of many things, so each says what it is a choice of.
        XCTAssertEqual(
            offers.offers.map { $0.choices.map(\.spoken) },
            [
                ["More pubs and bars", "Fewer pubs and bars", "Skip: Pubs and bars"],
                ["Add: Less transport noise", "Skip: Less transport noise"],
            ])
        XCTAssertEqual(offers.offers.map(\.note), [nil, nil])
        // Where the words it rests on stand is held as offsets, and never as words.
        XCTAssertEqual(offers.offers.map(\.spans), [[Span(start: 0, end: 4)], [Span(start: 12, end: 17)]])
        XCTAssertFalse(String(reflecting: offers).contains("noisy"))
        // One thing that needs no choice is added by its own button.
        XCTAssertNil(offers.addAll)
        XCTAssertNil(offers.showAll)
    }

    func test_what_an_offer_would_do_and_what_follows_are_the_apis_words_in_the_apis_order() throws {
        let long = Answers.read("interpret-by-model-long").suggestions
        let offers = try XCTUnwrap(SearchScreen.offers(long, all: true))

        XCTAssertEqual(offers.offers.count, 12)
        for (offer, noticed) in zip(offers.offers, long) {
            XCTAssertEqual(offer.does, noticed.does)
            XCTAssertEqual(offer.shown, noticed.shown)
            XCTAssertEqual(offer.follows, [noticed.follows] + noticed.said)
            XCTAssertEqual(offer.choices.map(\.label), noticed.choices.map(\.label))
            XCTAssertEqual(offer.choices.map(\.id), noticed.choices.map(\.id))
            XCTAssertEqual(offer.choices.last?.label, "Skip")
        }
        // What nobody said, and what Burro took, follows what happens to areas.
        XCTAssertEqual(offers.offers[10].does, "Add a journey to Pellam Exchange: at most 40 minutes, by public transport.")
        XCTAssertEqual(
            offers.offers[10].follows,
            [
                "Areas further off are left out.", "You gave 35 to 40: Burro took 40.",
                "You named no way of travelling: Burro took public transport.",
            ])
        // An offer that says nothing of what follows draws no line for it.
        let home = try XCTUnwrap(Answers.read("interpret-rules-at-once").suggestions.last)
        XCTAssertEqual(home.follows, "")
        XCTAssertEqual(SearchScreen.offers([home], all: true)?.offers.first?.follows, [])
        XCTAssertEqual(SearchScreen.offers([home], all: true)?.offers.first?.does, "Look for a 1-bedroom home.")
    }

    func test_the_persons_words_are_cut_from_the_box_by_where_they_stand_and_never_retyped() throws {
        let box = try typed(in: "interpret-by-model-long")
        let offers = try XCTUnwrap(
            SearchScreen.offers(Answers.read("interpret-by-model-long").suggestions, all: false))

        let wrote = offers.offers.map { BoxSpans.written(box, $0.shown) }

        XCTAssertEqual(
            wrote,
            [
                "I want to live somewhere quiet", "with access to parks",
                // The first two of four readings of the word for how well off a place is, and
                // the culture beside it.
                "slightly affluent but with some culture around it",
                "slightly affluent but with some culture around it",
                "slightly affluent but with some culture around it",
                "At most 35-40min commute from Pellam Exchange",
                "If I'm renting, max £1,900 a month for a 1 bed flat",
            ])
        // The box holds the text as it was typed, with whatever space stands before it.
        XCTAssertEqual(BoxSpans.written("  \n \(box)", offers.offers[0].shown), "I want to live somewhere quiet")
        // Words that are not in the box are not drawn.
        XCTAssertNil(BoxSpans.written("leafy", offers.offers[0].shown))
        XCTAssertNil(BoxSpans.written("", offers.offers[0].shown))
        XCTAssertNil(BoxSpans.written(box, Span(start: 3, end: 3)))
        // No answer holds a word of them: what is served is where they stand. Nor does
        // what the screen is handed: the words are cut when they are drawn.
        let served = String(decoding: try Recorded.read("interpret-by-model-long").body, as: UTF8.self)
        for words in wrote.compactMap({ $0 }) {
            XCTAssertFalse(served.contains(words))
            XCTAssertFalse(String(reflecting: offers).contains(words))
        }
    }

    func test_the_way_burro_reads_the_words_is_marked_in_words_and_is_said_with_the_choice() throws {
        let long = Answers.read("interpret-by-model-long").suggestions
        let offers = try XCTUnwrap(SearchScreen.offers(long, all: false))

        XCTAssertEqual(SearchCopy.Suggest.guess, "Burro's guess")
        XCTAssertEqual(
            offers.offers.map { $0.choices.filter(\.guess).map(\.label) },
            [
                ["Add"], ["Add: nearer a park"],
                // The first two of four readings of a word for how well off a place is, which
                // are the rules' to offer: they have no guess.
                [], [],
                ["Add"], ["Add as a firm limit: areas further off are left out"],
                ["Set as a firm limit: dearer areas are left out"],
            ])
        // Doing nothing is never the guess, and the rules alone guess nothing.
        XCTAssertFalse(offers.offers.contains { $0.choices.last?.guess == true })
        let atOnce = try XCTUnwrap(
            SearchScreen.offers(Answers.read("interpret-rules-at-once").suggestions, all: true))
        XCTAssertFalse(atOnce.offers.contains { $0.choices.contains(where: \.guess) })
        // The mark is said with the words of the choice, before the thing it is a choice of.
        XCTAssertEqual(SearchScreen.marked("Add"), "Add (Burro's guess)")
        XCTAssertEqual(
            offers.offers[0].choices.map(\.spoken), ["Add (Burro's guess): Quiet streets", "Skip: Quiet streets"])
        XCTAssertEqual(
            offers.offers[1].choices.map(\.spoken),
            [
                "Add: nearer a park (Burro's guess)", "Nearer a park: stop counting it",
                "Add: Parks close by: Nearer a park", "Skip: Nearer a park",
            ])
        XCTAssertEqual(
            offers.offers[5].choices.map(\.spoken),
            [
                "Add as a firm limit: areas further off are left out (Burro's guess): Pellam Exchange",
                "Add as a guide: areas further off rank lower: Pellam Exchange", "Skip: Pellam Exchange",
            ])
    }

    func test_the_screen_draws_the_four_parts_in_the_websites_order_and_cuts_the_words_from_the_box() throws {
        let block = try Repository.text(Written.search.appendingPathComponent("OffersBlock.swift"))
        let root = try Repository.text(Written.search.appendingPathComponent("SearchRootView.swift"))
        let one = try XCTUnwrap(block.range(of: "private func one("))
        let drawn = block[one.lowerBound...]

        var last = drawn.startIndex
        for part in [
            "offer.does", "wrote(offer.shown)", "SearchCopy.Suggest.wrote", "offer.follows", "offer.noteDrawn",
            "offer.choices", "SearchCopy.Suggest.showWords",
        ] {
            let found = try XCTUnwrap(drawn.range(of: part, range: last..<drawn.endIndex), part)
            last = found.upperBound
        }
        // The guess is marked with the website's words, on the button it is the guess of.
        XCTAssertTrue(drawn.contains("SearchCopy.Suggest.guess"))
        // The words come from the box as it stands, and from nowhere that keeps them.
        XCTAssertTrue(root.contains("wrote: { BoxSpans.written(words, $0) }"))
        XCTAssertEqual(SearchCopy.Suggest.wrote, "You wrote")
    }

    @MainActor
    func test_a_choice_sends_the_edits_the_api_gave_for_it_as_a_control_does() async throws {
        let search = await noticed("interpret-suggest")

        await search.flow.choose(at: 0, id: "less")

        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(try JSON.written(asked), try sent(in: "rank-suggestion-chosen"))
        XCTAssertEqual(search.api.calls(to: .interpret).count, 1)
        XCTAssertEqual(search.state.spec, Answers.ranked("rank-suggestion-chosen").spec)
        // The thing that was chosen of is gone, and the other still waits.
        XCTAssertEqual(search.shown().offers?.offers.map(\.name), ["Less transport noise"])
        XCTAssertTrue(search.shown().hasRanking)
        XCTAssertTrue(
            search.shown().chips.map(\.reads).contains(
                "Pubs and bars for each 1,000 homes within 800 m, in a straight line, fewer"))
    }

    @MainActor
    func test_of_two_ways_that_run_the_same_way_the_one_that_was_pressed_is_the_one_that_is_sent()
        async throws
    {
        let journey = Answers.read("interpret-by-model").suggestions[1]
        let search = await noticed("interpret-by-model", then: "rank-first")

        // A firm limit and a guide both add the journey, so the way a choice runs tells
        // neither from the other. Its id does.
        XCTAssertEqual(journey.choices.map(\.id), ["firm", "guide", "ignore"])
        XCTAssertEqual(journey.choices.map(\.direction), [.more, .more, .ignore])
        XCTAssertEqual(
            search.shown().offers?.offers.map { $0.choices.map(\.id) },
            [["more", "ignore"], ["firm", "guide", "ignore"]])
        await search.flow.choose(at: 1, id: "guide")

        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(asked, journey.choices[1].operations)
        XCTAssertEqual(asked.commuteOps.map(\.strictness), [.soft])
        XCTAssertEqual(search.api.calls(to: .rank).count, 1)
        XCTAssertEqual(search.shown().offers?.offers.map(\.name), ["Leafy"])
    }

    @MainActor
    func test_the_firm_limit_is_sent_when_it_is_the_firm_limit_that_was_pressed() async throws {
        let journey = Answers.read("interpret-by-model").suggestions[1]
        let search = await noticed("interpret-by-model", then: "rank-first")

        await search.flow.choose(at: 1, id: "firm")

        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(asked, journey.choices[0].operations)
        XCTAssertEqual(asked.commuteOps.map(\.strictness), [.hard])
    }

    @MainActor
    func test_a_journey_that_does_not_say_where_it_leads_is_not_sent() async throws {
        let journey = try XCTUnwrap(Answers.read("interpret-by-model-place").suggestions.first)
        let search = await noticed("interpret-by-model-place", then: "rank-first")
        let calls = search.api.calls.count

        // Burro does not know the place, so the journey is offered with none.
        XCTAssertTrue(journey.asksPlace)
        XCTAssertEqual(journey.choices.map(\.id), ["firm", "guide", "ignore"])
        XCTAssertEqual(journey.choices.map(\.operations.namesItsPlaces), [false, false, true])
        await search.flow.choose(at: 0, id: "firm")
        await search.flow.choose(at: 0, id: "guide")

        XCTAssertEqual(search.api.calls.count, calls)
        XCTAssertEqual(search.shown().offers?.offers.map(\.name), ["A journey"])
        // Doing nothing needs no place.
        await search.flow.choose(at: 0, id: "ignore")
        XCTAssertEqual(search.api.calls.count, calls)
        XCTAssertNil(search.shown().offers)
    }

    @MainActor
    func test_leaving_a_thing_out_takes_it_away_and_sends_nothing() async {
        let search = await noticed("interpret-suggest")
        let calls = search.api.calls.count

        await search.flow.choose(at: 1, id: "ignore")

        XCTAssertEqual(search.api.calls.count, calls)
        XCTAssertEqual(search.shown().offers?.offers.map(\.name), ["Pubs and bars"])
        XCTAssertEqual(search.state.spec, Answers.meta.defaults.rent)
        // A choice the thing does not have does nothing.
        await search.flow.choose(at: 0, id: "sideways")
        await search.flow.choose(at: 9, id: "more")
        XCTAssertEqual(search.api.calls.count, calls)
        XCTAssertEqual(search.shown().offers?.offers.count, 1)
    }

    @MainActor
    func test_add_all_adds_what_the_api_says_one_press_may_add_and_leaves_the_rest_to_the_person()
        async throws
    {
        let search = await noticed("interpret-suggest-many", then: "rank-first")
        let offers = try XCTUnwrap(search.shown().offers)
        let suggestions = Answers.read("interpret-suggest-many").suggestions

        XCTAssertEqual(offers.offers.count, 6)
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
        // What the API names no way for is still the person's to choose.
        XCTAssertEqual(
            search.shown().offers?.offers.map(\.name),
            ["Pubs and bars", "Nearer a station", "Nearer a town centre"])
        XCTAssertNil(search.shown().offers?.addAll)
    }

    @MainActor
    func test_add_all_never_takes_what_the_api_names_no_way_for_whatever_it_is_handed() async throws {
        let search = await noticed("interpret-suggest-many", then: "rank-first")

        XCTAssertEqual(
            Answers.read("interpret-suggest-many").suggestions.map(\.addAll), ["", "", "", "more", "more", "less"])
        await search.flow.chooseAll([0, 1, 2])
        XCTAssertEqual(search.api.calls(to: .rank).count, 0)
        XCTAssertEqual(search.shown().offers?.offers.count, 6)
        await search.flow.chooseAll([0, 3, 3, 17])

        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(asked.weightOps.map(\.featureId), [.playSpaceProximity])
        XCTAssertEqual(search.shown().offers?.offers.count, 5)
    }

    func test_what_one_press_may_add_is_the_apis_to_say_and_the_app_works_nothing_out() throws {
        let noise = try XCTUnwrap(Answers.read("interpret-suggest").suggestions.last)
        let leafy = try XCTUnwrap(Answers.read("interpret-suggest-notice").suggestions.first)

        // There is one way to want less transport noise, and it carries no note. The API
        // leaves it to the person all the same, so no press adds it with others.
        XCTAssertEqual(noise.label, "Less transport noise")
        XCTAssertEqual(noise.ways.map(\.id), ["less"])
        XCTAssertNil(noise.noteShown)
        XCTAssertEqual(noise.addAll, "")
        XCTAssertNil(noise.addedWithOthers)
        XCTAssertNil(SearchScreen.offers(Answers.read("interpret-suggest").suggestions, all: true)?.addAll)
        // The way that is taken is the one the API names, by its id, and no other.
        XCTAssertEqual(leafy.addAll, "more")
        XCTAssertEqual(leafy.addedWithOthers?.id, "more")
        XCTAssertNil(leafy.with(addAll: "").addedWithOthers)
        XCTAssertNil(leafy.with(addAll: "ignore").addedWithOthers)
        XCTAssertNil(leafy.with(addAll: "a way it does not have").addedWithOthers)
        // What the app once went by moves nothing: a note, or how many ways there are.
        let noted = leafy.with(note: "Recorded crime counts only when you ask for it by name.")
        XCTAssertEqual(noted.noteShown, "Recorded crime counts only when you ask for it by name.")
        XCTAssertEqual(noted.addedWithOthers?.id, "more")
        XCTAssertNil(leafy.with(note: "  ").noteShown)
    }

    func test_of_a_thing_with_two_ways_one_press_adds_the_way_the_api_names() throws {
        let long = Answers.read("interpret-by-model-long").suggestions
        let offers = try XCTUnwrap(SearchScreen.offers(long, all: false))

        XCTAssertEqual(
            long.map(\.addAll), ["more", "more", "", "", "", "", "more", "", "", "", "guide", "guide"])
        // The first four, and each beyond them that one press may add.
        XCTAssertEqual(offers.offers.map(\.at), [0, 1, 2, 3, 6, 10, 11])
        XCTAssertEqual(offers.addAllAts, [0, 1, 6, 10, 11])
        XCTAssertEqual(offers.addAll, "Add the 5 that need no choice")
        XCTAssertEqual(offers.showAll, "Show all 12")
        // Burro's guess of the journey is the firm limit. One press adds the guide.
        XCTAssertEqual(long[10].ways.map(\.id), ["firm", "guide"])
        XCTAssertEqual(long[10].ways.map(\.guess), [true, false])
        XCTAssertEqual(long[10].addedWithOthers?.id, "guide")
        XCTAssertEqual(long[10].addedWithOthers?.operations.commuteOps.map(\.strictness), [.soft])
        XCTAssertEqual(long[11].addedWithOthers?.operations.budgetOps.map(\.strictness), [.soft])
    }

    @MainActor
    func test_add_all_sends_the_guide_where_the_guess_is_a_firm_limit() async throws {
        let search = await noticed("interpret-by-model-long", then: "rank-first")
        let long = Answers.read("interpret-by-model-long").suggestions
        let offers = try XCTUnwrap(search.shown().offers)

        await search.flow.chooseAll(offers.addAllAts)

        XCTAssertEqual(search.api.calls(to: .rank).count, 1)
        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(
            asked,
            [0, 1, 6, 10, 11].compactMap { long[$0].addedWithOthers?.operations }
                .reduce(Operations.none) { $0.merged(with: $1) })
        XCTAssertEqual(asked.tagOps.map(\.tagId), [.quietResidential])
        XCTAssertEqual(asked.weightOps.map(\.featureId), [.parkProximity, .cultureVenuesPerHomes])
        XCTAssertEqual(asked.commuteOps.map(\.strictness), [.soft])
        XCTAssertEqual(asked.budgetOps.map(\.strictness), [.soft])
        // What is left is the person's to choose: four in sight, and three behind "Show all".
        let left = try XCTUnwrap(search.shown().offers)
        XCTAssertEqual(
            left.offers.map(\.name),
            ["Mix of brands", "Gritty", "What homes sell for", "Homes in the higher council tax bands"])
        XCTAssertNil(left.addAll)
        XCTAssertEqual(left.showAll, "Show all 7")
    }

    @MainActor
    func test_what_one_press_added_is_said_with_what_still_needs_the_person() async throws {
        let search = await noticed("interpret-by-model-long", then: "rank-first")
        XCTAssertNil(search.shown().offers?.added)
        XCTAssertNil(search.shown().offers?.takeBack)

        await search.flow.chooseAll([0, 1, 6, 10, 11])
        let offers = try XCTUnwrap(search.shown().offers)

        XCTAssertEqual(
            offers.added,
            [
                "5 added. 9 need you: the journey can be made a firm limit",
                "the budget can be made a firm limit", "mix of brands",
                "recorded crime, which is added under its own name", "what homes sell for",
                "homes in the higher council tax bands", "Village feel", "Age of buildings",
                "nearer a town centre.",
            ].joined(separator: "; "))
        XCTAssertEqual(offers.says, offers.added)
        XCTAssertEqual(offers.takeBack, "Take it all back")
        XCTAssertEqual(offers.offers.count, 4)
        XCTAssertEqual(offers.showAll, "Show all 7")
    }

    func test_the_line_says_how_many_were_added_and_names_what_is_left_as_the_api_names_it() {
        XCTAssertEqual(SearchCopy.Suggest.added(2, needs: []), "2 added.")
        XCTAssertEqual(SearchCopy.Suggest.added(1, needs: ["pubs and bars"]), "1 added. 1 needs you: pubs and bars.")
        XCTAssertEqual(
            SearchCopy.Suggest.added(3, needs: ["pubs and bars", "nearer a station", "nearer a town centre"]),
            "3 added. 3 need you: pubs and bars; nearer a station; nearer a town centre.")
        XCTAssertEqual(SearchCopy.Suggest.takeBack, "Take it all back")
    }

    @MainActor
    func test_what_one_press_added_can_be_taken_back_though_nothing_is_left_to_choose() async throws {
        let search = await noticed("interpret-suggest-many", then: "rank-first")
        for at in [2, 1, 0] { await search.flow.choose(at: at, id: "ignore") }
        XCTAssertEqual(search.shown().offers?.addAll, "Add all 3")

        await search.flow.chooseAll([0, 1, 2])
        let offers = try XCTUnwrap(search.shown().offers)

        // Nothing is left to choose of, and nothing is left for the person. The block
        // stays, to say what was added and to take it back.
        XCTAssertEqual(offers.offers, [])
        XCTAssertEqual(offers.added, "3 added.")
        XCTAssertEqual(offers.takeBack, "Take it all back")
        XCTAssertNil(offers.addAll)
        XCTAssertTrue(search.shown().parts.contains(.offers))
    }

    @MainActor
    func test_what_is_left_for_the_person_keeps_them_where_the_line_that_says_so_is() async throws {
        // A journey and a budget, and nothing else: one press adds both, each as a guide.
        let two: StandIn.Responder = .made { _ in
            try Recorded.read("interpret-by-model-long").with(data: { data in
                guard case .array(let all) = data["suggestions"] else { return }
                data["suggestions"] = .array(Array(all.suffix(2)))
            })
        }
        let needed = OpenSearch(StandIn.firstSearch().on(.interpret, two))
        let needless = await noticed("interpret-suggest-many", then: "rank-first")
        await needed.flow.submitText("what was typed")
        for at in [2, 1, 0] { await needless.flow.choose(at: at, id: "ignore") }
        let before = (needed.state.answers, needless.state.answers)

        await needed.flow.chooseAll([0, 1])
        await needless.flow.chooseAll([0, 1, 2])

        // Nothing is left to choose of in either. In the first the line says that two
        // things need the person, so they are not taken from it to the list and the map.
        XCTAssertEqual(
            needed.shown().offers?.added,
            "2 added. 2 need you: the journey can be made a firm limit; the budget can be made a firm limit.")
        XCTAssertEqual(needed.shown().offers?.offers, [])
        XCTAssertFalse(SearchScreen.arrives(needed.state, since: before.0, onTop: true))
        XCTAssertEqual(needless.shown().offers?.added, "3 added.")
        XCTAssertTrue(SearchScreen.arrives(needless.state, since: before.1, onTop: true))
        // Taken back, nothing is said to be left, and what was offered is there to choose of.
        await needed.flow.takeBack()
        XCTAssertNil(needed.shown().offers?.added)
        XCTAssertEqual(needed.shown().offers?.offers.count, 2)
        XCTAssertFalse(SearchScreen.leadsToResults(needed.state))
    }

    @MainActor
    func test_one_press_takes_it_all_back_and_the_search_is_as_it_was() async throws {
        let search = await noticed("interpret-by-model-long", then: "rank-first")
        let before = (spec: search.state.spec, offered: search.state.suggestions)
        await search.flow.chooseAll([0, 1, 6, 10, 11])
        XCTAssertEqual(search.api.calls(to: .rank).count, 1)
        XCTAssertNotEqual(search.state.spec, before.spec)
        // The service answers a search it is sent no edit of with the search it was sent.
        search.api.on(.rank, StandIn.withTheSpecSent("rank-first"))

        await search.flow.takeBack()

        // The search that is ranked is the one that stood before the press, with no edit.
        XCTAssertEqual(search.api.calls(to: .rank).count, 2)
        let again = try search.api.lastCall(to: .rank).body(as: RankBody.self)
        XCTAssertEqual(again.spec, before.spec)
        XCTAssertNil(again.operations)
        XCTAssertEqual(search.state.spec, before.spec)
        // What was offered is offered again, and nothing says that anything was added.
        XCTAssertEqual(search.state.suggestions, before.offered)
        let offers = try XCTUnwrap(search.shown().offers)
        XCTAssertNil(offers.added)
        XCTAssertNil(offers.takeBack)
        XCTAssertEqual(offers.addAll, "Add the 5 that need no choice")
        // There is nothing more to take back.
        let calls = search.api.calls.count
        await search.flow.takeBack()
        XCTAssertEqual(search.api.calls.count, calls)
    }

    @MainActor
    func test_with_nothing_added_there_is_nothing_to_take_back() async {
        let search = await noticed("interpret-suggest")
        let calls = search.api.calls.count

        await search.flow.chooseAll([0, 1])
        await search.flow.takeBack()

        XCTAssertEqual(search.api.calls.count, calls)
        XCTAssertNil(search.state.read?.added)
        XCTAssertEqual(search.shown().offers?.offers.count, 2)
    }

    func test_add_all_sets_no_firm_limit_though_there_is_one_way_to_want_it() throws {
        let atOnce = Answers.read("interpret-rules-at-once").suggestions
        let offers = try XCTUnwrap(SearchScreen.offers(atOnce, all: false))
        let budget = atOnce[12]

        // A budget as a firm limit leaves areas out. There is one way to take it and it
        // carries no note, and the API names no way for one press to add.
        XCTAssertEqual(budget.ways.map(\.label), ["Set as a firm limit: dearer areas are left out"])
        XCTAssertEqual(budget.ways.first?.operations.budgetOps.map(\.strictness), [.hard])
        XCTAssertNil(budget.noteShown)
        XCTAssertEqual(budget.addAll, "")
        XCTAssertNil(budget.addedWithOthers)
        XCTAssertEqual(offers.offers.map(\.at), [0, 1, 2, 3, 6, 11, 13])
        XCTAssertEqual(offers.addAllAts, [0, 6, 11, 13])
        XCTAssertEqual(offers.addAll, "Add the 4 that need no choice")
        XCTAssertEqual(offers.showAll, "Show all 14")
    }

    func test_a_note_that_neighbours_share_is_drawn_once_with_the_first_of_them() throws {
        let long = Answers.read("interpret-by-model-long").suggestions
        let offers = try XCTUnwrap(SearchScreen.offers(long, all: true))

        XCTAssertEqual(offers.offers.map { $0.note != nil }, [
            false, false, true, true, true, true, false, true, true, true, false, false,
        ])
        // The last three that carry one share it, word for word.
        XCTAssertEqual(Set(offers.offers[7...9].map(\.note)).count, 1)
        XCTAssertEqual(offers.offers.map(\.noteDrawn), [
            false, false, true, true, true, false, false, true, false, false, false, false,
        ])
    }

    func test_what_waits_out_of_sight_is_only_what_is_the_persons_to_choose() throws {
        let many = Answers.read("interpret-suggest-many").suggestions
        // Three things one press may add, and then three that are the person's to choose.
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
        // Where one press may add every thing in sight, the button says how many it adds.
        XCTAssertEqual(SearchScreen.offers(Array(many[3...5]), all: false)?.addAll, "Add all 3")
    }

    @MainActor
    func test_a_choice_that_changes_the_search_takes_the_notice_with_it() async {
        let search = await noticed("interpret-suggest-notice", then: "rank-first")
        XCTAssertEqual(search.shown().notice, Answers.read("interpret-suggest-notice").noticeText)
        // One press may add one of the two, so no button adds several: its own button adds it.
        XCTAssertNil(search.shown().offers?.addAll)

        await search.flow.choose(at: 1, id: "ignore")
        XCTAssertNotNil(search.shown().notice)
        await search.flow.choose(at: 0, id: "more")

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

    // MARK: - A journey whose place Burro does not know

    func test_a_press_on_a_way_of_such_a_journey_asks_which_place_and_doing_nothing_needs_none() throws {
        let asks = try XCTUnwrap(
            SearchScreen.offers(Answers.read("interpret-by-model-place").suggestions, all: true)?.offers.first)
        let named = try XCTUnwrap(
            SearchScreen.offers(Answers.read("interpret-by-model").suggestions, all: true)?.offers.last)

        XCTAssertEqual(
            asks.does,
            "Add a journey of at most 40 minutes, by public transport. Burro does not know this place: choose one.")
        XCTAssertTrue(asks.asksPlace)
        XCTAssertEqual(asks.choices.map(\.id), ["firm", "guide", "ignore"])
        XCTAssertEqual(asks.choices.map { asks.asksWhichPlace(on: $0) }, [true, true, false])
        // The release holds nothing like the place that was named, so the search is the way to one.
        XCTAssertEqual(asks.options, [])
        // A journey to a place that was named in full asks nothing.
        XCTAssertFalse(named.asksPlace)
        XCTAssertEqual(named.choices.map { named.asksWhichPlace(on: $0) }, [false, false, false])
        XCTAssertEqual(SearchCopy.Suggest.whichPlace, "Which place?")
        XCTAssertEqual(SearchCopy.Suggest.alike, "Places like it")
    }

    func test_the_places_the_release_holds_that_are_like_it_are_offered_by_the_apis_names() throws {
        let journey = try XCTUnwrap(Answers.read("interpret-by-model-place").suggestions.first)
        let alike = try XCTUnwrap(Answers.read("interpret-clarify").clarify.first?.options)

        let offer = try XCTUnwrap(SearchScreen.offers([journey.with(options: alike)], all: true)?.offers.first)

        XCTAssertEqual(offer.options.map(\.name), ["Pellam Cross", "Pellam Exchange", "Pellam Infirmary"])
        XCTAssertEqual(offer.options.map(\.id), alike.map(\.id))
        XCTAssertEqual(offer.key, journey.key)
    }

    func test_the_place_that_is_chosen_is_put_into_the_journey_that_holds_none_and_into_no_other() throws {
        let asks = try XCTUnwrap(Answers.read("interpret-by-model-place").suggestions.first?.choices.first)
        let named = try XCTUnwrap(Answers.read("interpret-by-model").suggestions.last?.choices.first)

        let placed = asks.operations.withPlace("syn-p0012")

        XCTAssertFalse(asks.operations.namesItsPlaces)
        XCTAssertTrue(placed.namesItsPlaces)
        XCTAssertEqual(placed.commuteOps.map(\.placeId), ["syn-p0012"])
        XCTAssertEqual(placed.commuteOps.map(\.maxMinutes), [40])
        XCTAssertEqual(placed.commuteOps.map(\.strictness), [.hard])
        // A journey that names its place keeps it, and nothing else of the edits is changed.
        XCTAssertEqual(named.operations.commuteOps.map(\.placeId), ["syn-p0021"])
        XCTAssertEqual(named.operations.withPlace("syn-p0012"), named.operations)
        XCTAssertEqual(Edits.tagOn(.leafy).withPlace("syn-p0012"), Edits.tagOn(.leafy))
    }

    @MainActor
    func test_the_place_that_is_chosen_goes_with_the_way_that_was_pressed() async throws {
        let journey = try XCTUnwrap(Answers.read("interpret-by-model-place").suggestions.first)
        let place = try XCTUnwrap(try Recorded.data(.searchPlaces, "places-search", as: PlacesData.self).places.first)
        let firm = await noticed("interpret-by-model-place", then: "rank-first")
        let guide = await noticed("interpret-by-model-place", then: "rank-first")

        await firm.flow.choose(at: 0, id: "firm", place: (id: place.placeId, name: place.name))
        await guide.flow.choose(at: 0, id: "guide", place: (id: place.placeId, name: place.name))

        let asFirm = try XCTUnwrap(try firm.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        let asGuide = try XCTUnwrap(try guide.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(asFirm, journey.choices[0].operations.withPlace(place.placeId))
        XCTAssertEqual(asGuide, journey.choices[1].operations.withPlace(place.placeId))
        XCTAssertEqual(asFirm.commuteOps.map(\.placeId), ["syn-p0012"])
        XCTAssertEqual(asFirm.commuteOps.map(\.maxMinutes), [40])
        XCTAssertEqual(asFirm.commuteOps.map(\.strictness), [.hard])
        XCTAssertEqual(asGuide.commuteOps.map(\.strictness), [.soft])
        XCTAssertEqual(firm.api.calls(to: .rank).count, 1)
        // The offer has gone, and the place is named as the release names it.
        XCTAssertNil(firm.shown().offers)
        XCTAssertEqual(firm.state.placeNames[place.placeId], "Pellam Cross")
    }

    @MainActor
    func test_a_place_chosen_for_a_journey_that_names_its_own_changes_nothing_of_what_is_sent() async throws {
        let journey = Answers.read("interpret-by-model").suggestions[1]
        let search = await noticed("interpret-by-model", then: "rank-first")

        await search.flow.choose(at: 1, id: "guide", place: (id: "syn-p0012", name: "Pellam Cross"))

        let asked = try XCTUnwrap(try search.api.lastCall(to: .rank).body(as: RankBody.self).operations)
        XCTAssertEqual(asked, journey.choices[1].operations)
        XCTAssertEqual(asked.commuteOps.map(\.placeId), ["syn-p0021"])
        XCTAssertNil(search.state.placeNames["syn-p0012"])
    }

    @MainActor
    func test_what_is_typed_in_the_place_search_of_an_offer_goes_in_the_body_of_its_call_and_nowhere_else()
        async throws
    {
        let looked = "zqxplace5150"
        let search = await noticed("interpret-by-model-place", then: "rank-first")
        search.api.on(.searchPlaces, "places-search")
        let places = PlaceSearch(wait: 0) { await search.flow.searchPlaces($0) }

        places.typed(looked)
        await places.settled()
        let picked = try XCTUnwrap(places.options.first)
        await search.flow.choose(at: 0, id: "firm", place: (id: picked.id, name: picked.name))

        func holds(_ call: StandIn.Call, _ what: String) -> Bool {
            call.sent.map { String(decoding: $0, as: UTF8.self).contains(what) } ?? false
        }
        let carrying = search.api.calls.filter { holds($0, looked) }
        XCTAssertEqual(carrying.map(\.route), [.searchPlaces])
        XCTAssertEqual(carrying.map(\.method), ["POST"])
        XCTAssertFalse(search.api.calls.contains { $0.outsideTheBody.contains(looked) })
        XCTAssertFalse(String(reflecting: search.state).contains(looked))
        XCTAssertFalse(String(reflecting: search.shown()).contains(looked))
        XCTAssertFalse(String(reflecting: places.options).contains(looked))
        // The place is sent by its id, in the body of the one call that ranks, and its name nowhere.
        XCTAssertEqual(search.api.calls.filter { holds($0, picked.id) }.map(\.route), [.rank])
        XCTAssertFalse(search.api.calls.contains { $0.outsideTheBody.contains(picked.id) })
        XCTAssertFalse(search.api.calls.contains { holds($0, picked.name) })
    }

    func test_the_screen_opens_the_place_search_under_the_offer_and_takes_nothing_until_a_place_is_chosen()
        throws
    {
        let block = try Repository.text(Written.search.appendingPathComponent("OffersBlock.swift"))
        let root = try Repository.text(Written.search.appendingPathComponent("SearchRootView.swift"))
        let press = try XCTUnwrap(block.range(of: "private func press("))
        let pressed = block[press.lowerBound...]

        // A press on a way that asks which place says what is being placed, and goes no further.
        var last = pressed.startIndex
        for step in [
            "offer.asksWhichPlace(on: choice)", "placing = Placing(key: offer.key, way: choice.id)", "return",
            "choose(offer.at, choice.id, nil)",
        ] {
            let found = try XCTUnwrap(pressed.range(of: step, range: last..<pressed.endIndex), step)
            last = found.upperBound
        }
        // Every choice is pressed through it, and the place that is chosen goes with the way.
        XCTAssertTrue(block.contains("press(choice, of: offer)"))
        XCTAssertTrue(block.contains("choose(offer.at, way, place)"))
        // The search is the one a place is searched by everywhere, under the website's words.
        XCTAssertTrue(block.contains("PlaceField(label: SearchCopy.Suggest.whichPlace, search: search)"))
        XCTAssertTrue(block.contains("SearchCopy.Suggest.alike"))
        XCTAssertTrue(root.contains("search: searchPlaces,"))
    }

    // MARK: - While a model reads

    /// A search on a service with a model behind it. The rules answer at once, and the
    /// model's answer is held until it is let go.
    @MainActor
    private func opened(onRules rules: StandIn.Responder, heldBy model: StandIn.Gate) -> OpenSearch {
        let later: StandIn.Responder = .made { _ in
            try await model.hold()
            return try Recorded.read("interpret-by-model-long")
        }
        return OpenSearch(StandIn.firstSearch().inTurn(.interpret, [rules, later]))
    }

    @MainActor
    func test_while_a_model_reads_the_screen_says_so_and_what_the_rules_noticed_is_already_there()
        async throws
    {
        let atOnce = Answers.read("interpret-rules-at-once")
        let model = StandIn.Gate()
        let search = opened(onRules: .recorded("interpret-rules-at-once"), heldBy: model)

        async let sent: Void = search.flow.submitText("what was typed")
        await until { model.waiting == 1 }
        let waiting = try XCTUnwrap(search.shown().offers)

        XCTAssertTrue(atOnce.modelPending)
        XCTAssertEqual(waiting.reading, "Burro is still reading the rest of your words.")
        // What the rules offer is drawn at once and may be chosen of. It never waits on a model.
        XCTAssertEqual(
            waiting.offers.map(\.name), [0, 1, 2, 3, 6, 11, 13].map { atOnce.suggestions[$0].label })
        XCTAssertEqual(waiting.addAllAts, [0, 6, 11, 13])
        // The box is not held either: the sentence has been read, and another may be sent.
        XCTAssertFalse(search.shown().reading)
        XCTAssertFalse(search.shown().busy)
        XCTAssertTrue(search.shown().parts.contains(.offers))
        model.release()
        await sent

        // The model has read. What it read has joined what is offered, and the line has gone.
        let joined = try XCTUnwrap(search.shown().offers)
        XCTAssertNil(joined.reading)
        XCTAssertEqual(joined.offers.map(\.at), [0, 1, 2, 3, 6, 10, 11])
    }

    @MainActor
    func test_while_a_model_reads_the_one_line_says_so_and_what_was_added_can_still_be_taken_back()
        async throws
    {
        let model = StandIn.Gate()
        let search = opened(onRules: .recorded("interpret-rules-at-once"), heldBy: model)
        search.api.on(.rank, "rank-first")

        async let sent: Void = search.flow.submitText("what was typed")
        await until { model.waiting == 1 }
        await search.flow.chooseAll([0, 6, 11, 13])
        let waiting = try XCTUnwrap(search.shown().offers)

        XCTAssertEqual(waiting.says, "Burro is still reading the rest of your words.")
        XCTAssertNil(waiting.added)
        XCTAssertEqual(waiting.takeBack, "Take it all back")
        model.release()
        await sent

        // The model has read. What was added is not offered again, and the line says what was.
        let joined = try XCTUnwrap(search.shown().offers)
        XCTAssertNil(joined.reading)
        XCTAssertEqual(joined.added?.hasPrefix("4 added. "), true)
        XCTAssertFalse(joined.offers.map(\.name).contains("Quiet streets"))
    }

    @MainActor
    func test_the_screen_says_a_model_reads_though_the_rules_noticed_nothing() async throws {
        let model = StandIn.Gate()
        let nothing: StandIn.Responder = .made { _ in
            try Recorded.read("interpret-rules-at-once").with(data: { $0["suggestions"] = .array([]) })
        }
        let search = opened(onRules: nothing, heldBy: model)

        async let sent: Void = search.flow.submitText("what was typed")
        await until { model.waiting == 1 }
        let waiting = try XCTUnwrap(search.shown().offers)

        XCTAssertEqual(waiting.offers, [])
        XCTAssertEqual(waiting.reading, SearchCopy.Suggest.reading)
        XCTAssertNil(waiting.addAll)
        XCTAssertNil(waiting.showAll)
        XCTAssertTrue(search.shown().parts.contains(.offers))
        model.release()
        await sent

        XCTAssertEqual(search.shown().offers?.offers.count, 7)
        XCTAssertNil(search.shown().offers?.reading)
    }

    @MainActor
    func test_the_line_goes_when_the_model_does_not_answer_and_when_the_box_changes() async throws {
        let failing = OpenSearch(
            StandIn.firstSearch().inTurn(
                .interpret, [.recorded("interpret-rules-at-once"), .fails(.cannotConnectToHost)]))
        let model = StandIn.Gate()
        let changed = opened(onRules: .recorded("interpret-rules-at-once"), heldBy: model)

        await failing.flow.submitText("what was typed")
        async let sent: Void = changed.flow.submitText("what was typed")
        await until { model.waiting == 1 }
        XCTAssertNotNil(changed.shown().offers?.reading)
        changed.flow.boxChanged()
        model.release()
        await sent

        // A model that did not answer leaves what the rules offered, and nothing is said of it.
        XCTAssertNil(failing.shown().offers?.reading)
        XCTAssertEqual(failing.shown().offers?.offers.count, 7)
        // What rested on the words that were sent goes when the box changes, and the line with it.
        XCTAssertNil(changed.shown().offers)
    }

    @MainActor
    func test_no_model_is_said_to_read_where_the_answer_says_none_has_more_to_read() async throws {
        let search = await noticed("interpret-suggest")

        XCTAssertFalse(Answers.read("interpret-suggest").modelPending)
        XCTAssertFalse(search.state.modelIsReading)
        let offers = try XCTUnwrap(search.shown().offers)
        XCTAssertNil(offers.reading)
        XCTAssertEqual(offers.offers.count, 2)
        // Before anything is read, nothing is offered and nothing is said.
        XCTAssertFalse(OpenSearch().state.modelIsReading)
        XCTAssertNil(OpenSearch().shown().offers)
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
    /// The same thing as it was noticed, with another note, another way for one press to
    /// add, or other places that are like the one that was named.
    fileprivate func with(
        note: String? = nil, addAll: String? = nil, options: [ClarifyOption]? = nil
    ) -> Suggestion {
        Suggestion(
            target: target, label: label, does: does, spans: spans, shown: shown, follows: follows,
            said: said, choices: choices, note: note ?? self.note, readBy: readBy,
            addAll: addAll ?? self.addAll, needs: needs, asksPlace: asksPlace, namedAt: namedAt,
            options: options ?? self.options)
    }
}
