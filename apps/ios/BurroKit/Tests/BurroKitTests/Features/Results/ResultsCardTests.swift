import XCTest

@testable import BurroKit

/// The result card: where the area is, the reasons, the trade-off or the
/// words that say there is none, how complete the data is, each journey, the
/// cost with its confidence, and the source and date behind every line.
///
/// A test that names a figure of a recording fails when the ranking changes
/// and the answers are recorded again. That is what it is for.
final class ResultsCardTests: XCTestCase {
    private let synthetic = "Synthetic test data"

    // MARK: - The first card

    @MainActor
    func test_the_heading_is_the_rank_the_names_the_api_gave_and_the_fit() async throws {
        let card = try await ResultsApp.searched().firstCard()

        XCTAssertEqual(card.heading, Results.Heading(rank: 1, name: "Farrowmere", borough: "Quillhaven", fit: 71))
        XCTAssertEqual(card.heading.words, "Rank 1, Farrowmere, Quillhaven, Fit 71 of 100")
        XCTAssertEqual(card.area, AreaRef(areaId: "syn-n0006", slug: "farrowmere", name: "Farrowmere", borough: "Quillhaven"))
        XCTAssertTrue(card.full)
    }

    @MainActor
    func test_where_it_is_is_the_apis_sentence_and_the_nearest_station_each_with_its_source() async throws {
        let card = try await ResultsApp.searched().firstCard()
        let explained = Answers.explained("explanations-first").explanations[0]

        let orientation = try XCTUnwrap(card.orientation.value)
        XCTAssertEqual(orientation.text, explained.orientation.text)
        XCTAssertEqual(orientation.text, "Farrowmere is in Quillhaven.")
        XCTAssertEqual(orientation.sources.map(\.words), ["Source: Synthetic test data. Data from 23 September 2026. Made-up data"])
        let station = try XCTUnwrap(card.station.value)
        XCTAssertEqual(station.name, "Nearest station")
        XCTAssertEqual(
            station.columns,
            [
                .init(name: "Station", value: "Farrowmere"),
                .init(name: "Minutes on foot", value: "5"),
                .init(name: "Lines", value: "Cobalt line"),
            ])
        XCTAssertEqual(station.sources.map(\.date), ["September 2026"])
    }

    @MainActor
    func test_the_reasons_are_the_apis_sentences_in_its_order_not_joined_and_not_reworded() async throws {
        let card = try await ResultsApp.searched().firstCard()
        let explained = Answers.explained("explanations-first").explanations[0]

        let reasons = try XCTUnwrap(card.reasons.value)
        XCTAssertEqual(reasons.map(\.text), explained.reasons.map(\.text))
        XCTAssertEqual(reasons.count, 3)
        XCTAssertEqual(
            reasons[0].text,
            "Quiet streets: band 4 of 5, counted from least to most, among the 21 areas compared in this release.")
        XCTAssertEqual(
            reasons[1].text,
            "By public transport to Cindermoor Works: about 21 minutes on a typical weekday morning, "
                + "26 if you just miss a service.")
        // Every sentence ends in its source and its date.
        for reason in reasons {
            XCTAssertEqual(reason.sources.map(\.name), [synthetic])
            XCTAssertEqual(reason.sources.map(\.synthetic), [true])
            XCTAssertFalse(reason.byModel)
        }
        XCTAssertEqual(reasons.map { $0.sources[0].date }, ["2025", "September 2026", "August 2026"])
    }

    @MainActor
    func test_the_trade_off_is_the_apis_sentence_or_the_words_that_say_there_is_none() async throws {
        let app = try await ResultsApp.searched()
        let explained = Answers.explained("explanations-first").explanations

        XCTAssertEqual(try app.firstCard().tradeOff.value?.sentence.text, explained[0].tradeOff?.text)
        XCTAssertEqual(try app.firstCard().tradeOff.value?.sentence.sources.map(\.date), ["2025"])
        // What is given up is not a journey, so nothing is said of a limit.
        XCTAssertNil(try app.firstCard().tradeOff.value?.limit)
        // A card says so when the API found none.
        let api = StandIn.firstSearch().on(
            .explainTop,
            .made { _ in
                try Recorded.read("explanations-first").with(data: { data in
                    guard case .array(var all)? = data["explanations"] else { return }
                    all[0]["trade_off"] = .null
                    all[0]["reasons"] = .array([])
                    data["explanations"] = .array(all)
                })
            })
        let none = try await ResultsApp.searched(api).firstCard()
        XCTAssertEqual(none.tradeOff, .none)
        XCTAssertEqual(none.reasons, .here([]))
        XCTAssertEqual(ResultsCopy.Card.noTradeOff, "No trade-off found for this search")
    }

    @MainActor
    func test_a_sentence_a_model_wrote_says_so() async throws {
        let api = StandIn.firstSearch().on(
            .explainTop,
            .made { _ in
                try Recorded.read("explanations-first").with(data: { data in
                    guard case .array(var all)? = data["explanations"],
                        case .array(var reasons)? = all[0]["reasons"]
                    else { return }
                    reasons[0]["origin"] = .string("model")
                    all[0]["reasons"] = .array(reasons)
                    data["explanations"] = .array(all)
                })
            })
        let card = try await ResultsApp.searched(api).firstCard()

        XCTAssertEqual(card.reasons.value?.map(\.byModel), [true, false, false])
        XCTAssertEqual(ResultsCopy.Card.byModel, "Written by AI, checked against the source")
    }

    @MainActor
    func test_how_complete_says_how_many_of_the_things_that_count_have_data() async throws {
        let api = StandIn.firstSearch()
            .on(.rank, "rank-buyer-family").on(.explainTop, "explanations-buyer-family")
        let app = try await ResultsApp.searched(api)
        // The fourth is the first that has no figure for a thing that counts.
        let fourth = app.listed.cards[3]
        let explained = Answers.explained("explanations-buyer-family").explanations[3]

        XCTAssertEqual(
            try app.firstCard().completeness,
            Results.Completeness(
                words: "Based on everything that counts in your search", covered: 100, untested: []))
        XCTAssertEqual(try app.firstCard().missing, .hidden)
        XCTAssertEqual(fourth.heading.name, "Marrowfen")
        XCTAssertEqual(fourth.completeness?.words, "Based on 9 of the 10 things that count in your search")
        // The bar draws what the words count, and nothing else.
        XCTAssertEqual(fourth.completeness?.covered, 90)
        // One sentence of the API's for each thing that has no figure here.
        XCTAssertEqual(fourth.missing.value?.map(\.text), explained.missing.map(\.text))
        XCTAssertEqual(fourth.missing.value?.count, 1)
        XCTAssertEqual(ResultsCopy.Completeness.missingTitle, "What there is no figure for")
        // A row says how complete it is in one line, and has no sentence.
        XCTAssertEqual(app.listed.cards[5].missing, .hidden)
        XCTAssertNotNil(app.listed.cards[5].completeness)
    }

    @MainActor
    func test_room_is_held_for_the_sentences_of_what_has_no_figure_while_they_are_waited_for() async throws {
        let api = StandIn.firstSearch().on(.rank, "rank-buyer-family")
        let reasons = api.hold(.explainTop, "explanations-buyer-family")
        let app = try await ResultsApp(api)

        async let sent: Void = app.flow.submitText("leafy")
        await until { app.state.ranking != nil }

        // How many there will be is known from the ranking.
        XCTAssertEqual(app.listed.cards[3].missing, .waiting)
        XCTAssertEqual(app.listed.cards[3].held, 1)
        XCTAssertEqual(app.listed.cards[0].missing, .hidden)
        XCTAssertEqual(app.listed.cards[0].held, 0)
        reasons.release()
        await sent
        XCTAssertEqual(app.listed.cards[3].held, 0)
    }

    @MainActor
    func test_a_limit_that_could_not_be_tested_is_said_in_words() async throws {
        let api = StandIn.firstSearch().on(.rank, "rank-two-journeys").on(.explainTop, "explanations-two-journeys")
        let card = try await ResultsApp.searched(api).firstCard()

        XCTAssertEqual(
            card.completeness?.untested,
            ["Your budget is a firm limit, and it could not be tested here: there is no cost figure."])
    }

    @MainActor
    func test_each_journey_says_where_to_how_how_long_and_whether_it_is_within_the_limit() async throws {
        let card = try await ResultsApp.searched().firstCard()

        XCTAssertEqual(
            card.journeys,
            [
                Results.Journey(
                    place: "Cindermoor Works", mode: "Public transport", typical: "21 minutes",
                    missed: "26 minutes", whole: nil, verdict: .within, limit: "35 minutes",
                    sources: [
                        Results.SourceLine(
                            sourceId: "synthetic", name: synthetic, asOf: "2026-09", date: "September 2026",
                            synthetic: true)
                    ])
            ])
        XCTAssertEqual(Results.Journey.Verdict.within.word, "within")
        XCTAssertEqual(Results.Journey.Verdict.over.word, "over")
        // With one journey there is nothing to say of which one counts.
        XCTAssertNil(card.journeysNote)
    }

    @MainActor
    func test_with_two_journeys_the_one_the_fit_is_worked_out_from_is_marked() async throws {
        let api = StandIn.firstSearch().on(.rank, "rank-two-journeys").on(.explainTop, "explanations-two-journeys")
        let card = try await ResultsApp.searched(api).firstCard()
        let ranked = Answers.ranked("rank-two-journeys").ranked[0]

        XCTAssertEqual(card.journeys.count, 2)
        XCTAssertEqual(
            card.journeysNote,
            "Of these journeys, only the one to \(card.journeys[1].place) counts towards the fit: "
                + "it does worst against the limit you set for it. "
                + "You can make the average count instead, in Settings.")
        XCTAssertEqual(card.journeys.map(\.typical), ["25 minutes", "36 minutes"])
        XCTAssertEqual(card.journeys.map(\.limit), ["25 minutes", "30 minutes"])
        XCTAssertEqual(card.journeys.map(\.verdict), [.within, .over])
        XCTAssertEqual(Results.drivingLeg(of: ranked)?.placeId, "syn-p0026")
    }

    @MainActor
    func test_a_journey_beyond_the_longest_the_release_holds_says_so_and_gives_no_time() async throws {
        let api = StandIn.firstSearch().on(.rank, "rank-on-foot").on(.explainTop, "explanations-on-foot")
        let app = try await ResultsApp.searched(api)
        let beyond = try XCTUnwrap(app.listed.cards.first { $0.heading.rank == 4 }?.journeys.first)
        let within = try XCTUnwrap(app.listed.cards.first?.journeys.first)

        XCTAssertEqual(beyond.whole, "More than \(Answers.meta.limits.cutoffMinutes.walk) minutes")
        XCTAssertNil(beyond.typical)
        XCTAssertNil(beyond.missed)
        XCTAssertEqual(beyond.verdict, .over)
        XCTAssertEqual(beyond.mode, "On foot")
        // On foot there is one time, and no service to miss.
        XCTAssertEqual(within.missed, "Does not apply")
        XCTAssertNotNil(within.typical)
    }

    func test_a_journey_with_no_time_in_the_data_is_never_given_one() {
        let leg = CommuteLeg(
            placeId: "syn-p0021", mode: .pt, status: .missing, minutes: nil, minutesTypical: nil,
            minutesJustMissed: nil, utility: nil)
        let commute = Commute(
            placeId: "syn-p0021", mode: .pt, maxMinutes: 35, strictness: .soft, provenance: .stated)

        XCTAssertNil(Results.within(leg, limit: commute))
        XCTAssertEqual(ResultsCopy.Journeys.missing, "No journey time in this data")
    }

    @MainActor
    func test_a_journey_with_no_fact_in_hand_takes_the_source_of_any_journey_or_leads_to_the_sources() async throws {
        let app = try await ResultsApp.searched()
        // A row is not explained, so its journey is cited by no sentence.
        let row = app.listed.cards[10]
        XCTAssertFalse(row.full)
        XCTAssertEqual(row.journeys.first?.sources.map(\.date), ["September 2026"])

        let bare = try await ResultsApp.searched(StandIn.firstSearch().on(.explainTop, "error-internal"))
        XCTAssertEqual(bare.state.facts.values.filter { $0.kind == .travel }, [])
        XCTAssertEqual(try bare.firstCard().journeys.first?.sources, [])
        // The place is named by the answer that brought the ranking, so it has its name with no reasons.
        XCTAssertEqual(try bare.firstCard().journeys.first?.place, "Cindermoor Works")
    }

    @MainActor
    func test_the_cost_is_the_range_the_middle_the_month_and_the_confidence_as_a_word() async throws {
        let card = try await ResultsApp.searched().firstCard()
        let cost = try XCTUnwrap(card.cost.value)

        XCTAssertEqual(cost.range, "£975 to £1,300")
        XCTAssertTrue(cost.aMonth)
        XCTAssertEqual(cost.label, "Rent")
        XCTAssertEqual(cost.segment, "1-bedroom home")
        XCTAssertEqual(cost.middle, "£1,125")
        XCTAssertEqual(cost.month, "August 2026")
        XCTAssertEqual(cost.confidence, "High")
        XCTAssertEqual(cost.pips, 3)
        XCTAssertFalse(cost.oneNumber)
        XCTAssertEqual(cost.budget, "£1,700")
        XCTAssertEqual(cost.falls, "Your budget is above this range.")
        XCTAssertEqual(cost.sources.map(\.words), ["Source: Synthetic test data. Data from August 2026. Made-up data"])
    }

    @MainActor
    func test_the_cost_is_for_the_kind_of_home_the_search_is_for() async throws {
        let api = StandIn.firstSearch()
            .on(.rank, "rank-buyer-family").on(.explainTop, "explanations-buyer-family")
        let app = try await ResultsApp.searched(api)
        let card = try app.firstCard()
        let spec = Answers.ranked("rank-buyer-family").spec
        let profile = try XCTUnwrap(app.state.details[card.id])
        let fact = try XCTUnwrap(
            profile.facts.first { $0.key == "\(spec.tenure.rawValue).\(spec.budget.segment.rawValue)" })

        XCTAssertEqual(spec.tenure, .buy)
        XCTAssertEqual(card.cost.value?.label, "Price")
        XCTAssertEqual(card.cost.value?.aMonth, false)
        XCTAssertEqual(card.cost.value?.segment, fact.slots["segment"])
        XCTAssertEqual(card.cost.value?.range, "£\(fact.slots["lower"] ?? "") to £\(fact.slots["upper"] ?? "")")
    }

    func test_with_no_cost_figure_the_card_says_so_and_shows_none() throws {
        var state = SearchState(meta: Answers.meta, areas: Answers.areas)
        state = reduce(state, .rankAnswered(Answers.ranked("rank-first"), sent: .none))
        let profile = Answers.profile("farrowmere")
        let bare = AreaData(
            area: profile.area, features: profile.features, tags: profile.tags, cost: [],
            stations: profile.stations, neighbours: profile.neighbours, portrait: profile.portrait,
            similar: profile.similar, facts: profile.facts.filter { $0.kind != .cost })
        state = reduce(state, .detailAnswered(bare))

        let card = try XCTUnwrap(Results.card(for: Answers.ranked("rank-first").ranked[0], at: 0, in: state))

        XCTAssertEqual(card.cost, .none)
        XCTAssertEqual(ResultsCopy.Cost.none, "No cost figure in this data")
        XCTAssertFalse(ResultsDrawn.figures(in: card.cost).contains { $0.contains("£") })
    }

    func test_a_price_that_is_one_number_is_drawn_as_one_and_no_range_is_made_of_it() throws {
        let profile: AreaData = try Recorded.data(.getArea, "one-number/area")
        let ranked: RankData = try Recorded.data(.rank, "one-number/rank-buyer")
        let found = try XCTUnwrap(Results.cost(in: profile, for: ranked.spec))

        let cost = try XCTUnwrap(
            Results.cost(of: found.fact, estimate: found.estimate, budget: ranked.spec.budget.amount))

        XCTAssertNil(found.estimate.lowerQuartile)
        XCTAssertNil(found.estimate.upperQuartile)
        XCTAssertTrue(cost.oneNumber)
        XCTAssertEqual(cost.range, "£260,000")
        XCTAssertEqual(cost.what, "The middle price of homes of this kind, of all sizes")
        XCTAssertEqual(cost.soldIn, "the year ending August 2026")
        XCTAssertEqual(
            cost.caveat, "The publisher gives no range, and does not say how many sales this figure rests on.")
        XCTAssertEqual(cost.segment, "flat")
        XCTAssertFalse(cost.aMonth)
        // No word says how sure a figure is when its publisher does not.
        XCTAssertNil(cost.confidence)
        XCTAssertEqual(cost.pips, 0)
        XCTAssertNil(cost.middle)
        XCTAssertEqual(cost.budget, "£455,000")
        XCTAssertEqual(cost.falls, "Your budget is above this middle price.")
        // The bar has a middle and a budget, and no end is drawn for it.
        XCTAssertNil(cost.bar.lower)
        XCTAssertNil(cost.bar.upper)
        XCTAssertNotNil(cost.bar.budget)
        XCTAssertEqual(cost.sources.map(\.date), ["August 2026"])
    }

    func test_a_rent_of_a_wider_place_is_never_drawn_without_its_place_its_months_and_its_count() throws {
        let profile: AreaData = try Recorded.data(.getArea, "let/area")
        let ranked: RankData = try Recorded.data(.rank, "let/rank-firm")
        let found = try XCTUnwrap(Results.cost(in: profile, for: ranked.spec))

        let cost = try XCTUnwrap(
            Results.cost(of: found.fact, estimate: found.estimate, budget: ranked.spec.budget.amount))

        XCTAssertEqual(found.fact.template, .costRentRecorded)
        XCTAssertEqual(found.estimate.of?.kind, .postcodeDistrict)
        XCTAssertFalse(cost.oneNumber)
        XCTAssertTrue(cost.aMonth)
        // Each is a slot of the fact, as the API wrote it.
        XCTAssertEqual(cost.figureOf, found.fact.slots["of"])
        XCTAssertEqual(cost.recordedIn, found.fact.slots["period"])
        XCTAssertEqual(cost.rents, found.fact.slots["rents"])
        XCTAssertEqual(cost.isOf, found.fact.slots["is_of"])
        XCTAssertEqual(cost.recordedIn, "April 2025 to March 2026")
        XCTAssertEqual(cost.caveat, found.fact.slots["half_let"])
        // No word says how sure it is: the count of rents does.
        XCTAssertNil(cost.confidence)
        XCTAssertNil(cost.month)
        XCTAssertEqual(cost.pips, 0)
        // A budget is held against the middle rent, and the words say where it falls against it.
        XCTAssertTrue(
            [
                ResultsCopy.Cost.belowMiddleRent, ResultsCopy.Cost.aboveMiddleRent,
                ResultsCopy.Cost.atMiddleRent,
            ].contains(try XCTUnwrap(cost.falls)))
        XCTAssertNotNil(cost.bar.lower)
        XCTAssertNotNil(cost.bar.upper)
        XCTAssertNotNil(cost.bar.budget)
    }

    func test_a_rent_of_a_wider_place_that_does_not_say_its_place_is_not_drawn() throws {
        let profile: AreaData = try Recorded.data(.getArea, "let/area")
        let ranked: RankData = try Recorded.data(.rank, "let/rank-firm")
        let found = try XCTUnwrap(Results.cost(in: profile, for: ranked.spec))

        for missing in ["of", "period", "rents"] {
            var slots = found.fact.slots
            slots[missing] = nil
            let bare = Fact(
                factId: found.fact.factId, areaId: found.fact.areaId, kind: found.fact.kind,
                key: found.fact.key, label: found.fact.label, template: found.fact.template,
                slots: slots, numbers: found.fact.numbers, names: found.fact.names,
                sources: found.fact.sources, asOf: found.fact.asOf, synthetic: found.fact.synthetic)

            XCTAssertNil(Results.cost(of: bare, estimate: found.estimate, budget: nil), missing)
        }
    }

    func test_a_rent_that_is_of_the_area_alone_says_nothing_of_a_wider_place() throws {
        let profile = Answers.profile("farrowmere")
        let renter = Answers.meta.defaults.rent
        let found = try XCTUnwrap(Results.cost(in: profile, for: renter))

        let cost = try XCTUnwrap(Results.cost(of: found.fact, estimate: found.estimate, budget: nil))

        XCTAssertNil(found.estimate.of)
        XCTAssertNil(cost.figureOf)
        XCTAssertNil(cost.recordedIn)
        XCTAssertNil(cost.rents)
        XCTAssertNil(cost.isOf)
        XCTAssertNotNil(cost.confidence)
    }

    // MARK: - The strip of vibes

    @MainActor
    func test_the_strip_is_the_vibes_the_api_chose_in_its_order_each_as_a_band_of_five() async throws {
        let card = try await ResultsApp.searched().firstCard()
        let ranked = Answers.ranked("rank-first").ranked[0]

        XCTAssertEqual(card.strip.map(\.tagId), ranked.strip.map(\.tagId))
        XCTAssertEqual(card.strip.map(\.name), ["Leafy", "Quiet streets", "Age of buildings", "Houses or flats"])
        XCTAssertEqual(card.strip.map(\.band), ["band 3 of 5", "band 4 of 5", "band 1 of 5", "band 5 of 5"])
        XCTAssertEqual(card.strip.compactMap(\.placed?.band), ranked.strip.map(\.band))
        XCTAssertEqual(
            card.strip.map(\.plainly),
            ["around the middle here", "on the high side here", "at the Newer end", "at the Flats end"])
        // A vibe that was asked for says so, and what was asked for stands first.
        XCTAssertEqual(card.strip.map(\.asked), ["asked for", "asked for", nil, nil])
        XCTAssertEqual(
            card.strip.indices.map { Results.group(before: $0, in: card.strip) },
            ["Asked for", nil, "Also", nil])
        // A band that rests on part of its recipe says so, in the API's own clause.
        XCTAssertEqual(
            card.strip.map(\.restsOn),
            [nil, nil, nil, "Worked out from 2 of its 3 parts, 75 of 100 by weight."])
        // Every band ends in its source and its date.
        for vibe in card.strip {
            XCTAssertEqual(
                Results.sourceWords(of: vibe), "Source: Synthetic test data. Data from 2025. Made-up data",
                vibe.name)
            XCTAssertFalse(vibe.reads.contains("%"), vibe.name)
        }
    }

    @MainActor
    func test_a_row_has_its_strip_from_the_ranking_alone_and_cites_nothing_it_does_not_hold() async throws {
        let app = try await ResultsApp.searched()
        let row = app.listed.cards[10]
        let ranked = Answers.ranked("rank-first").ranked[10]

        XCTAssertFalse(row.full)
        XCTAssertEqual(row.strip.compactMap(\.placed?.band), ranked.strip.map(\.band))
        // Village feel is a rough guide, and is on a result only where it was asked for.
        XCTAssertEqual(row.strip.map(\.name), ["Leafy", "Quiet streets", "Age of buildings", "Food and drink"])
        XCTAssertEqual(row.strip.map(\.rough), [nil, nil, nil, nil])
        // The fact behind a band of a row is not in hand, so nothing is said of what it rests on.
        XCTAssertEqual(row.strip.map(\.sources), [[], [], [], []])
        XCTAssertEqual(row.strip.map(\.restsOn), [nil, nil, nil, nil])
        XCTAssertNil(row.strip.first.flatMap { Results.sourceWords(of: $0) })
    }

    func test_a_scale_that_was_asked_for_names_the_end_that_was_asked_for() {
        let ranked = Answers.ranked("rank-scale")
        let mixed = ranked.ranked[13]

        let strip = Vibes.strip(ranked.ranked[0].strip, meta: Answers.meta, facts: [:])
        let varies = Vibes.strip(mixed.strip, meta: Answers.meta, facts: [:])

        XCTAssertEqual(strip.map(\.name), ["Going out", "Age of buildings", "Houses or flats"])
        XCTAssertEqual(strip.map(\.asked), ["asked for: Calm", nil, nil])
        XCTAssertEqual(strip.first?.plainly, "at the Calm end")
        XCTAssertEqual([strip.first?.low, strip.first?.high], ["Calm", "Buzzy"])
        // A mixed area is said to vary, and is never put at a point.
        XCTAssertEqual(mixed.rank, 14)
        XCTAssertEqual(varies.first?.placed, Placed(band: 4, spreadLow: 3, spreadHigh: 5))
        XCTAssertEqual(varies.first?.plainly, "varies within this area")
        XCTAssertEqual(varies.first?.band, "varies within this area, from band 3 to band 5 of 5")
        // A vibe the release does not name is left out, and never shown as its code.
        let unnamed = StripMark(
            tagId: .unlisted("a_vibe_of_next_year"), band: 3, spreadLow: 3, spreadHigh: 3, asked: false,
            toward: nil, factId: "syn-n0006/tag/a_vibe_of_next_year")
        XCTAssertEqual(Vibes.strip([unnamed], meta: Answers.meta, facts: [:]), [])
    }

    func test_the_bar_places_the_range_the_middle_and_the_budget_and_keeps_them_in_order() throws {
        let estimate = CostEstimate(
            areaId: "syn-n0006", tenure: .rent, segment: .bed1, lowerQuartile: 975, median: 1125,
            upperQuartile: 1300, confidence: .medium, asOf: "2026-08", sourceIds: ["synthetic"])

        let above = Results.bar(for: estimate, budget: 1700)
        let below = Results.bar(for: estimate, budget: 500)
        let none = Results.bar(for: estimate, budget: nil)

        XCTAssertLessThan(try XCTUnwrap(above.lower), above.median)
        XCTAssertLessThan(above.median, try XCTUnwrap(above.upper))
        XCTAssertLessThan(try XCTUnwrap(above.upper), try XCTUnwrap(above.budget))
        XCTAssertLessThan(try XCTUnwrap(below.budget), try XCTUnwrap(below.lower))
        XCTAssertNil(none.budget)
        for bar in [above, below, none] {
            for place in [bar.lower, bar.median, bar.upper, bar.budget].compactMap({ $0 }) {
                XCTAssertTrue((0...100).contains(place))
            }
        }
    }

    @MainActor
    func test_how_the_fit_is_worked_out_is_every_contribution_in_the_apis_order_rounded_down() async throws {
        let card = try await ResultsApp.searched().firstCard()

        // A feature is named as the release names it, and a tag as well.
        XCTAssertEqual(
            card.breakdown.map(\.thing),
            [
                "Quiet streets", "Journey", "Budget", "Leafy",
                "Modelled annual mean nitrogen dioxide",
                "Straight-line distance to the nearest way in to a station",
                "Share of residents exposed to 55 dB or more of transport noise",
                "Lines within a 10-minute walk",
                "Straight-line distance to the nearest marked way into a park of 2 ha or more",
                "Straight-line distance to the nearest town centre boundary",
            ])
        XCTAssertEqual(
            card.breakdown.first,
            Results.BreakdownRow(
                thing: "Quiet streets", weight: "50 of 100", share: "24%", adds: "16 of 100",
                says: .figures(
                    [
                        .init(name: "Band, of five", value: "4"),
                        .init(name: "Counted from", value: "least to most"),
                        .init(name: "Areas compared in this release", value: "21"),
                        .init(name: "Parts dated", value: "2025"),
                    ],
                    sources: [
                        Results.SourceLine(
                            sourceId: "synthetic", name: synthetic, asOf: "2025", date: "2025", synthetic: true)
                    ])))
        XCTAssertEqual(
            card.breakdown.first { $0.thing == "Journey" },
            Results.BreakdownRow(
                thing: "Journey", weight: "40 of 100", share: "19%", adds: "16 of 100",
                says: .figures(
                    [
                        .init(name: "To", value: "Cindermoor Works"),
                        .init(name: "How", value: "By public transport"),
                        .init(name: "Typical minutes", value: "21"),
                        .init(name: "Minutes if you just miss one", value: "26"),
                        .init(name: "Your limit, in minutes", value: "35"),
                        .init(name: "Under your limit by, in minutes", value: "14"),
                    ],
                    sources: [
                        Results.SourceLine(
                            sourceId: "synthetic", name: synthetic, asOf: "2026-09", date: "September 2026",
                            synthetic: true)
                    ])))
        XCTAssertEqual(card.breakdown.count, 10)
        XCTAssertEqual(
            ResultsCopy.Breakdown.roundedDown,
            "Every figure here is rounded down, so what the things add can come to a little less than the fit.")
    }

    @MainActor
    func test_what_the_data_says_is_the_slots_of_the_fact_or_that_there_is_a_figure_or_that_there_is_none()
        async throws
    {
        let api = StandIn.firstSearch()
            .on(.rank, "rank-buyer-family").on(.explainTop, "explanations-buyer-family")
        let app = try await ResultsApp.searched(api)
        let fourth = app.listed.cards[3]
        let row = app.listed.cards[10]

        XCTAssertEqual(fourth.breakdown.filter { $0.says == .nothing }.count, 1)
        XCTAssertEqual(fourth.breakdown.count, 10)
        // A row's facts are not in hand, so it says that there is a figure and shows none.
        XCTAssertTrue(row.breakdown.contains { $0.says == .something })
        XCTAssertFalse(ResultsDrawn.figures(in: row.breakdown.map(\.says)).contains { $0.contains("%") })
        XCTAssertEqual(ResultsCopy.Breakdown.has, "Has a figure")
        XCTAssertEqual(ResultsCopy.Breakdown.hasNot, "No figure")
    }

    @MainActor
    func test_how_well_an_area_scores_on_a_thing_is_never_shown() async throws {
        let app = try await ResultsApp.searched()
        let ranked = try XCTUnwrap(app.state.ranking?.ranked.first)
        let card = try app.firstCard()
        let drawn = ResultsDrawn.all(in: card.breakdown).texts

        // For a feature the score is the percentile it is ranked by, which is never printed.
        let shownOfRight = Set(
            ranked.contributions.flatMap {
                [Results.outOfHundred($0.weight), Results.hundredths($0.contribution) ?? 0]
            })
        var looked = 0
        for contribution in ranked.contributions {
            guard let utility = contribution.utility, let score = Results.hundredths(utility),
                !shownOfRight.contains(score)
            else { continue }
            XCTAssertFalse(drawn.contains("\(score) of 100"), contribution.component)
            XCTAssertFalse(drawn.contains("\(score)%"), contribution.component)
            looked += 1
        }
        XCTAssertGreaterThan(looked, 4)
        XCTAssertEqual(Mirror(reflecting: try XCTUnwrap(card.breakdown.first)).children.compactMap(\.label),
            ["thing", "weight", "share", "adds", "says"])
    }

    func test_a_thing_the_data_has_no_name_for_is_left_out_and_never_shown_as_its_code() {
        XCTAssertEqual(Results.label(of: "commute", meta: Answers.meta), "Journey")
        XCTAssertEqual(Results.label(of: "budget", meta: Answers.meta), "Budget")
        XCTAssertEqual(Results.label(of: "tag:leafy", meta: Answers.meta), "Leafy")
        XCTAssertEqual(
            Results.label(of: "feature:station_walk", meta: Answers.meta),
            Answers.meta.features.first { $0.featureId == .stationWalk }?.label)
        XCTAssertNil(Results.label(of: "feature:not_a_feature", meta: Answers.meta))
        XCTAssertNil(Results.label(of: "weather", meta: Answers.meta))
    }

    // MARK: - Reasons are for the ranking on screen

    @MainActor
    func test_reasons_for_another_ranking_are_never_shown_on_this_one() async throws {
        let app = try await ResultsApp.searched()
        XCTAssertNotNil(try app.firstCard().reasons.value)
        app.api.on(.rank, "rank-refined")
        let reasons = app.api.hold(.explainTop, "explanations-refined")

        async let sent: Void = app.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))
        await until { reasons.waiting == 1 && app.state.rankedHash == Answers.ranked("rank-refined").specHash }

        // The new ranking is on screen, and the reasons in hand are for the one before.
        XCTAssertFalse(app.state.explained)
        XCTAssertFalse(app.state.explanations.isEmpty)
        let card = try app.firstCard()
        XCTAssertEqual(card.reasons, .waiting)
        XCTAssertEqual(card.orientation, .waiting)
        XCTAssertEqual(card.tradeOff, .waiting)
        XCTAssertNil(card.missing.value)
        reasons.release()
        await sent
        XCTAssertEqual(
            try app.firstCard().reasons.value?.map(\.text),
            Answers.explained("explanations-refined").explanations[0].reasons.map(\.text))
    }

    @MainActor
    func test_a_ranking_that_fails_leaves_the_list_the_reasons_it_has() async throws {
        let app = try await ResultsApp.searched()
        let before = try app.firstCard().reasons
        app.api.on(.rank, "error-internal").on(.explainTop, "explanations-refined")

        await app.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))

        XCTAssertEqual(try app.firstCard().reasons, before)
        XCTAssertNotNil(before.value)
    }

    // MARK: - What may stand under the word "Trade-off"

    @MainActor
    func test_a_thing_the_area_does_well_is_never_shown_as_what_it_gives_up() async throws {
        // An engine before this one gave the least good thing as the trade-off even when it was good.
        let api = StandIn.firstSearch().on(
            .explainTop,
            .made { _ in
                try Recorded.read("explanations-first").with(data: { data in
                    guard case .array(var all)? = data["explanations"],
                        case .array(let reasons)? = all[0]["reasons"]
                    else { return }
                    // The journey is worth 0.85 to the area, and is within its limit.
                    all[0]["trade_off"] = reasons[1]
                    data["explanations"] = .array(all)
                })
            })
        let card = try await ResultsApp.searched(api).firstCard()

        XCTAssertEqual(card.tradeOff, .none)
        XCTAssertEqual(card.reasons.value?.count, 3)
    }

    func test_a_trade_off_is_what_is_worth_less_than_a_half_or_falls_short_of_what_was_asked() throws {
        let ranked = Answers.ranked("rank-first")
        let area = ranked.ranked[0]
        func about(_ component: String) throws -> ExplainedSentence {
            let part = try XCTUnwrap(area.contributions.first { $0.component == component })
            return ExplainedSentence(text: "", factIds: part.factIds, origin: .template, replaced: false)
        }
        let commutes = ranked.spec.commutes

        // Worth 0.455: something the area does badly.
        XCTAssertTrue(Results.isGivenUp(area, try about("feature:station_walk"), commutes: commutes))
        // Worth 0.85 and within its limit, worth 1 and under the budget: things it does well.
        XCTAssertFalse(Results.isGivenUp(area, try about("commute"), commutes: commutes))
        XCTAssertFalse(Results.isGivenUp(area, try about("budget"), commutes: commutes))
        // A journey over the longest that was set falls short, whatever it is worth.
        let shorter = commutes.map {
            Commute(placeId: $0.placeId, mode: $0.mode, maxMinutes: 20, strictness: .soft, provenance: .stated)
        }
        XCTAssertTrue(Results.isGivenUp(area, try about("commute"), commutes: shorter))
        // A sentence about nothing that counts is no trade-off.
        let stray = ExplainedSentence(text: "", factIds: ["syn-n0006/area/name"], origin: .template, replaced: false)
        XCTAssertFalse(Results.isGivenUp(area, stray, commutes: commutes))
        XCTAssertFalse(
            Results.isGivenUp(
                area, ExplainedSentence(text: "", factIds: [], origin: .template, replaced: false),
                commutes: commutes))
    }

    func test_the_least_a_thing_must_be_worth_to_be_done_well_is_the_contracts() throws {
        let contract = try Repository.text(Repository.root.appendingPathComponent("docs/design/contract.md"))

        let written = String(format: "%.2f", Results.doesWellFrom)
        XCTAssertTrue(contract.contains("at least `REASON_MIN_UTILITY`, \(written),"))
        // It is the one the API serves with the release.
        XCTAssertEqual(Answers.meta.limits.reasonMinUtility, Results.doesWellFrom)
    }

    @MainActor
    func test_a_journey_given_as_the_trade_off_says_which_way_it_falls_against_the_limit() async throws {
        let api = StandIn.firstSearch().on(.rank, "rank-on-foot").on(.explainTop, "explanations-on-foot")
        let app = try await ResultsApp.searched(api)
        let card = try XCTUnwrap(app.listed.cards.first { $0.heading.rank == 4 })
        let limit = try XCTUnwrap(Answers.ranked("rank-on-foot").spec.commutes.first?.maxMinutes)

        let tradeOff = try XCTUnwrap(card.tradeOff.value)
        XCTAssertEqual(
            tradeOff.sentence.text, Answers.explained("explanations-on-foot").explanations[3].tradeOff?.text)
        // The sentence gives the minutes and not the limit. The card holds both, and says which way it falls.
        XCTAssertEqual(tradeOff.limit, "Over your limit of \(limit) minutes")
        XCTAssertEqual(tradeOff.verdict, .over)
    }

    // MARK: - One scale for the cost of every card

    @MainActor
    func test_the_cost_of_every_card_is_drawn_on_one_scale_so_the_budget_is_in_one_place_on_all() async throws {
        let app = try await ResultsApp.searched()
        let bars = app.listed.cards.compactMap(\.cost.value?.bar)

        XCTAssertEqual(bars.count, 5)
        XCTAssertEqual(Set(bars.compactMap(\.budget)).count, 1)
        // A dearer home is drawn further along.
        let uppers = app.listed.cards.prefix(5).compactMap { card in
            app.state.details[card.id].flatMap { Results.cost(in: $0, for: app.state.spec)?.estimate.upperQuartile }
        }
        XCTAssertEqual(uppers.count, 5)
        for (one, other) in zip(zip(uppers, bars), zip(uppers, bars).dropFirst()) where one.0 < other.0 {
            XCTAssertLessThan(try XCTUnwrap(one.1.upper), try XCTUnwrap(other.1.upper))
        }
        XCTAssertNil(Results.scale(of: [], budget: 1700))
    }

    func test_what_a_scale_does_not_reach_is_drawn_at_its_end_and_never_outside_the_bar() {
        let estimate = CostEstimate(
            areaId: "syn-n0006", tenure: .rent, segment: .bed1, lowerQuartile: 975, median: 1125,
            upperQuartile: 1300, confidence: .medium, asOf: "2026-08", sourceIds: ["synthetic"])

        let bar = Results.bar(for: estimate, budget: 5000, on: Results.Scale(from: 1000, to: 1200))

        XCTAssertEqual(bar.lower, 0)
        XCTAssertEqual(bar.upper, 100)
        XCTAssertEqual(bar.budget, 100)
        XCTAssertEqual(bar.median, 62.5)
    }

    // MARK: - Rows

    @MainActor
    func test_results_six_to_twenty_are_rows_that_open_to_the_journeys_and_the_breakdown() async throws {
        let app = try await ResultsApp.searched()
        let rows = app.listed.cards.dropFirst(5)

        XCTAssertEqual(rows.count, 15)
        for row in rows {
            XCTAssertFalse(row.full)
            XCTAssertEqual(row.orientation, .hidden)
            XCTAssertEqual(row.reasons, .hidden)
            XCTAssertEqual(row.tradeOff, .hidden)
            XCTAssertEqual(row.cost, .hidden)
            XCTAssertFalse(row.breakdown.isEmpty)
            XCTAssertFalse(row.journeys.isEmpty)
            XCTAssertNotNil(row.completeness)
            XCTAssertNotNil(row.heading.fit)
        }
        // The API writes reasons for the first five only, and the list says so.
        XCTAssertEqual(ResultsCopy.Card.firstFive, "Reasons are written for the first five results.")
        XCTAssertEqual(Results.inFull, SearchFlow.explained)
        // A row asks the API for nothing more.
        XCTAssertEqual(app.api.calls(to: .getArea).count, 5)
    }

    // MARK: - Sources and dates

    func test_a_date_is_written_for_a_person_to_read_and_anything_else_is_left_as_it_came() {
        XCTAssertEqual(Results.readableDate("2026-09-23"), "23 September 2026")
        XCTAssertEqual(Results.readableDate("2026-09-03"), "3 September 2026")
        XCTAssertEqual(Results.readableDate("2026-08"), "August 2026")
        XCTAssertEqual(Results.readableDate("2026-09-23T10:00:00Z"), "23 September 2026")
        XCTAssertEqual(Results.readableDate("2025"), "2025")
        XCTAssertEqual(Results.readableDate("2024-10 to 2026-09"), "2024-10 to 2026-09")
        XCTAssertEqual(Results.readableDate("2026-13"), "2026-13")
        XCTAssertEqual(Results.readableDate("2026-02-30"), "2026-02-30")
        XCTAssertEqual(Results.readableDate(""), "")
    }

    func test_one_line_is_given_for_each_source_and_date_however_many_facts_share_them() {
        let facts = Answers.explained("explanations-first").facts

        let lines = Results.sourceLines(of: facts)

        XCTAssertEqual(Set(lines.map(\.id)).count, lines.count)
        XCTAssertEqual(Set(lines.map(\.asOf)), Set(facts.map(\.asOf)))
        XCTAssertTrue(lines.allSatisfy { $0.name == synthetic && $0.synthetic })
        XCTAssertEqual(Results.sourceLines(of: []), [])
    }

    func test_a_fact_is_laid_out_by_its_template_with_nothing_filled_in() throws {
        let profile = Answers.profile("farrowmere")
        let crime = try XCTUnwrap(profile.facts.first { $0.template == .featureCrime })
        let rent = try XCTUnwrap(profile.facts.first { $0.key == "rent.bed_1" })
        let empty = Fact(
            factId: "x", areaId: "syn-n0006", kind: .feature, key: "k", label: "A feature",
            template: .feature, slots: ["value": ""], numbers: [], names: [], sources: [], asOf: "2026",
            synthetic: true)
        let unknown = Fact(
            factId: "x", areaId: "syn-n0006", kind: .unlisted("new"), key: "k", label: "New",
            template: .unlisted("new"), slots: ["value": "12"], numbers: [], names: [], sources: [],
            asOf: "2026", synthetic: true)

        XCTAssertEqual(Results.row(of: crime).caveats, [ResultsCopy.crimeCaveat])
        XCTAssertEqual(
            Results.columns(of: rent).map(\.name),
            ["Kind of home", "Range", "Middle", "As of", "Confidence"])
        XCTAssertEqual(Results.columns(of: rent)[1].value, "£975 to £1,300")
        XCTAssertEqual(Results.columns(of: empty), [])
        // A kind of fact this build does not know is not laid out by guesswork.
        XCTAssertEqual(Results.columns(of: unknown), [])
        XCTAssertEqual(Results.row(of: rent).caveats, [])
    }

    func test_a_cost_at_the_budget_and_a_journey_at_its_limit_are_said_in_the_apis_words() throws {
        // Seen in a browser: "Under your budget by £0". A difference of nothing is no figure of
        // a fact: the fact says where the cost stands, and the row lays that out.
        let ranged: CompareData = try Recorded.data(.compare, "at/compare")
        let recorded: CompareData = try Recorded.data(.compare, "at/compare-let")
        let priced = Answers.explained("one-number/explanations-buyer")
        let first = Answers.explained("explanations-first")
        let atTheUpperEnd = try XCTUnwrap(ranged.facts.first { $0.template == .budgetAt })
        let atTheMiddleRent = try XCTUnwrap(recorded.facts.first { $0.template == .budgetAtRecorded })
        let atTheMiddlePrice = try XCTUnwrap(priced.facts.first { $0.template == .budgetAtMedian })
        let atTheLimit = try XCTUnwrap(first.facts.first { $0.slots["verdict"] == "At your limit" })

        XCTAssertEqual(
            Results.columns(of: atTheUpperEnd),
            [
                .init(name: "Upper end of the range", value: "£1,925"),
                .init(name: "Your budget", value: "£1,925"),
                .init(name: "Against your budget", value: "At your budget"),
            ])
        XCTAssertEqual(
            Array(Results.columns(of: atTheMiddleRent).suffix(2)),
            [
                .init(name: "Your budget", value: "£1,675"),
                .init(name: "Against your budget", value: "At your budget"),
            ])
        XCTAssertEqual(
            Results.columns(of: atTheMiddlePrice).map(\.name),
            ["Middle price, homes of all sizes", "Your budget", "Against your budget"])
        XCTAssertEqual(
            Array(Results.columns(of: atTheLimit).suffix(2)),
            [
                .init(name: "Your limit, in minutes", value: "35"),
                .init(name: "Against your limit", value: "At your limit"),
            ])
        // No fact of these answers is drawn with a difference of nothing, and each that is
        // not at its budget or its limit says by how much it is under or over.
        let differences = [
            ResultsCopy.Columns.under, ResultsCopy.Columns.over,
            ResultsCopy.Columns.underLimit, ResultsCopy.Columns.overLimit,
        ]
        var drawn = 0
        for fact in ranged.facts + recorded.facts + priced.facts + first.facts {
            for column in Results.columns(of: fact) where differences.contains(column.name) {
                drawn += 1
                XCTAssertNotEqual(column.value, "0", fact.factId)
                XCTAssertNotEqual(column.value, "£0", fact.factId)
                XCTAssertNil(fact.slots["verdict"], fact.factId)
            }
        }
        XCTAssertGreaterThan(drawn, 10)
    }
}
