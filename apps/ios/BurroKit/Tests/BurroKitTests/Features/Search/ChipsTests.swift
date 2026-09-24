import XCTest

@testable import BurroKit

/// The chips: what Burro understood, one for each thing the spec holds, with
/// every part nobody chose marked "assumed". docs/design/web.md section 5.2.
final class ChipsTests: XCTestCase {
    private let meta = Answers.meta

    private func chips(
        _ spec: PreferenceSpec, names: [String: String] = [:], assumed: Assumed = [:]
    ) -> [SearchChip] {
        SearchChips.of(
            spec, features: meta.features, tags: meta.tags, areas: Answers.areas, placeNames: names,
            assumed: assumed)
    }

    private func spec(
        like spec: PreferenceSpec,
        commutes: [Commute]? = nil,
        weights: [FeatureWeight]? = nil,
        areas: [AreaRule]? = nil
    ) -> PreferenceSpec {
        PreferenceSpec(
            schemaVersion: spec.schemaVersion, tenure: spec.tenure, budget: spec.budget,
            commutes: commutes ?? spec.commutes, commuteCombine: spec.commuteCombine,
            ptBasis: spec.ptBasis, commuteWeight: spec.commuteWeight, weights: weights ?? spec.weights,
            tags: spec.tags, areas: areas ?? spec.areas, tenureFrom: spec.tenureFrom,
            commuteCombineFrom: spec.commuteCombineFrom, ptBasisFrom: spec.ptBasisFrom,
            commuteWeightFrom: spec.commuteWeightFrom)
    }

    func test_a_search_nobody_has_touched_is_a_tenure_and_the_usual_settings_both_assumed() {
        let drawn = chips(meta.defaults.rent)

        XCTAssertEqual(drawn.map(\.kind), [.tenure, .usual])
        XCTAssertEqual(drawn.map(\.reads), ["Renting assumed", "Usual settings: 6 assumed"])
        XCTAssertTrue(drawn.allSatisfy { $0.assumed && $0.assumedAsAWhole && $0.removal == nil })
    }

    func test_chips_are_drawn_from_the_spec_in_the_order_tenure_budget_places_features_tags() {
        let read = Answers.read("interpret-first")

        let drawn = chips(read.spec)

        XCTAssertEqual(
            drawn.map(\.kind),
            [.tenure, .budget, .place("syn-p0021"), .tag(.leafy), .tag(.quietResidential), .usual])
        XCTAssertEqual(Set(drawn.map(\.id)).count, drawn.count)
    }

    func test_each_part_nobody_chose_carries_the_word_and_each_part_that_was_said_does_not() {
        let read = Answers.read("interpret-first")
        let state = reduce(SearchState(meta: meta, areas: Answers.areas), .readAnswered(read))

        let place = SearchChips.of(state)[2]

        XCTAssertEqual(
            place.parts,
            [
                ChipPart(text: "Public transport", assumed: true),
                ChipPart(text: "within 35 minutes", assumed: false),
                ChipPart(text: "flexible", assumed: true),
            ])
        XCTAssertTrue(place.assumed)
        XCTAssertFalse(place.assumedAsAWhole)
        // The place is named by the answer that brought the spec.
        XCTAssertEqual(
            place.reads, "Cindermoor Works, Public transport assumed, within 35 minutes, flexible assumed")
    }

    func test_the_word_goes_when_the_person_sets_that_part() {
        let read = Answers.read("interpret-first")
        var state = reduce(SearchState(meta: meta, areas: Answers.areas), .readAnswered(read))

        state = reduce(state, .queued(Edits.placeMode("syn-p0021", .pt)))
        let place = SearchChips.of(state)[2]

        XCTAssertEqual(place.parts.map(\.assumed), [false, false, true])
    }

    func test_a_place_is_called_by_the_name_in_hand_or_is_said_to_have_none() {
        let two = Answers.read("interpret-two-journeys").spec

        let unnamed = chips(two).filter { $0.kind.key.map { if case .place = $0 { true } else { false } } ?? false }
        let named = chips(two, names: ["syn-p0026": "A name the API gave"])

        // A place is never shown by a number, by its id or by what was typed.
        XCTAssertEqual(
            unnamed.map(\.label), ["A place with no name in this data", "A place with no name in this data"])
        XCTAssertTrue(named.map(\.label).contains("A name the API gave"))
        XCTAssertTrue(named.map(\.label).contains("A place with no name in this data"))
        XCTAssertFalse(String(reflecting: unnamed.map(\.label)).contains("syn-p"))
        XCTAssertEqual(unnamed.first?.removal, Edits.placeRemove("syn-p0019"))
    }

    func test_a_scale_says_which_of_its_ends_is_asked_for_in_the_apis_names_for_them() {
        let calm = chips(Answers.read("interpret-scale").spec).first { $0.kind == .tag(.pace) }
        let buzzy = chips(Answers.read("interpret-nights-out").spec).first { $0.kind == .tag(.pace) }
        let newer = chips(Answers.read("interpret-no-time").spec).first { $0.kind == .tag(.builtAge) }
        let leafy = chips(Answers.read("interpret-first").spec).first { $0.kind == .tag(.leafy) }

        XCTAssertEqual(calm?.reads, "Pace: towards Calm")
        XCTAssertEqual(buzzy?.reads, "Pace: towards Buzzy")
        XCTAssertEqual(newer?.reads, "Built age: towards Newer")
        // A vibe that runs one way has no end to name.
        XCTAssertEqual(leafy?.reads, "Leafy")
        XCTAssertEqual(calm?.removal, Edits.tagOff(.pace))
    }

    func test_a_vibe_whose_recipe_holds_recorded_crime_says_so_on_its_chip() throws {
        let gritty = chips(Answers.read("interpret-gritty").spec).first { $0.kind == .tag(.streetCharacter) }
        let street = try XCTUnwrap(meta.tags.first { $0.tagId == .streetCharacter })
        let leafy = try XCTUnwrap(meta.tags.first { $0.tagId == .leafy })

        XCTAssertEqual(gritty?.reads, "Street character: towards Gritty, counts recorded crime")
        XCTAssertTrue(SearchChips.holdsRecordedCrime(street, meta.features))
        XCTAssertFalse(SearchChips.holdsRecordedCrime(leafy, meta.features))
        // Which parts of the recipe are of recorded crime is said by the API's names for them.
        XCTAssertEqual(
            SearchChips.countsCrime(street, in: meta),
            "This vibe counts recorded crime: "
                + street.terms.compactMap { term in
                    meta.features.first { $0.featureId == term.featureId && $0.dimension == .crime }?.label
                }.joined(separator: "; ") + ".")
        XCTAssertNil(SearchChips.countsCrime(leafy, in: meta))
    }

    func test_with_two_places_a_chip_says_which_journey_counts_and_is_assumed_until_it_is_chosen() {
        let two = Answers.read("interpret-two-journeys").spec
        let one = Answers.read("interpret-first").spec
        let state = reduce(
            SearchState(meta: meta, areas: Answers.areas),
            .readAnswered(Answers.read("interpret-two-journeys")))

        let drawn = SearchChips.of(state)
        let which = drawn.first { $0.kind == .journeys }

        XCTAssertEqual(which?.reads, "Only the journey that does worst against its limit counts assumed")
        XCTAssertNil(which?.removal)
        XCTAssertEqual(ChipKind.journeys.key, .journeys)
        XCTAssertTrue(ChipKind.journeys.opensAControl)
        // It comes after the places, and before whatever follows them.
        let kinds = drawn.map(\.kind)
        XCTAssertEqual(kinds.firstIndex(of: .journeys), kinds.lastIndex(of: .place("syn-p0026")).map { $0 + 1 })
        // With one place there is nothing to choose between.
        XCTAssertFalse(SearchChips.withWhichJourneyCounts(chips(one), one).contains { $0.kind == .journeys })
        // The search's own chips say nothing of it.
        XCTAssertFalse(chips(two).contains { $0.kind == .journeys })
    }

    func test_a_budget_is_written_with_a_month_for_a_rent_and_without_for_a_price() {
        let rent = chips(Answers.read("interpret-first").spec)[1]
        let buy = chips(Answers.read("interpret-buyer-family").spec)[1]

        XCTAssertEqual(rent.label, "£1,700 a month")
        XCTAssertEqual(buy.label, "£450,000")
        XCTAssertEqual(buy.parts.map(\.text), ["A terraced house", "flexible"])
        XCTAssertEqual(rent.removal, Edits.budgetClear())
        XCTAssertEqual(chips(Answers.read("interpret-buyer-family").spec)[0].reads, "Buying")
    }

    func test_a_feature_that_counts_either_way_says_which_way() {
        let drawn = chips(Answers.read("interpret-nights-out").spec)
        let evening = drawn.first { $0.kind == .feature(.venueEvening) }

        XCTAssertEqual(evening?.reads, "Pubs, bars and evening venues, more")
        XCTAssertEqual(evening?.removal, Edits.featureOff(.venueEvening))
    }

    func test_a_thing_a_person_took_off_is_said_to_count_for_nothing_and_cannot_be_removed() {
        let drawn = chips(Answers.read("interpret-second-sentence").spec)
        let off = drawn.first { $0.kind == .feature(.highstreetAccess) }

        XCTAssertEqual(
            off?.reads,
            "Straight-line distance to the nearest town centre boundary, does not count")
        XCTAssertNil(off?.removal)
        XCTAssertEqual(off?.assumed, false)
        XCTAssertFalse(SearchChips.counts(0))
        XCTAssertFalse(SearchChips.counts(nil))
        XCTAssertTrue(SearchChips.counts(0.05))
    }

    func test_the_usual_settings_are_one_chip_that_says_how_many_and_is_never_one_of_them() {
        let drawn = chips(Answers.read("interpret-second-sentence").spec)

        XCTAssertEqual(drawn.last?.reads, "Usual settings: 5 assumed")
        XCTAssertEqual(drawn.filter { $0.kind == .usual }.count, 1)
        XCTAssertFalse(drawn.contains { $0.kind == .feature(.stationWalk) })
        XCTAssertFalse(ChipKind.usual.opensAControl)
        XCTAssertNil(ChipKind.usual.key)
    }

    func test_a_hidden_area_is_named_and_said_to_be_hidden() {
        let farrowmere = Answers.areas[5]
        let hidden = spec(
            like: meta.defaults.rent,
            areas: [
                AreaRule(areaId: farrowmere.areaId, rule: .exclude, provenance: .uiEdit),
                AreaRule(areaId: Answers.areas[0].areaId, rule: .only, provenance: .uiEdit),
            ])

        let drawn = chips(hidden).filter { !$0.kind.opensAControl && $0.kind != .usual }

        XCTAssertEqual(drawn.map(\.reads), ["Farrowmere, hidden", "\(Answers.areas[0].name), only"])
        XCTAssertEqual(drawn.first?.removal, Edits.areaClear(farrowmere.areaId))
        XCTAssertFalse(drawn.contains { $0.assumed })
    }

    func test_a_code_this_build_has_no_word_for_makes_no_part_and_never_shows_as_the_code() {
        let odd = spec(
            like: meta.defaults.rent,
            commutes: [
                Commute(
                    placeId: "syn-p0021", mode: .unlisted("by_boat"), maxMinutes: 30,
                    strictness: .unlisted("sometimes"), provenance: .stated)
            ])

        let place = chips(odd)[1]

        XCTAssertEqual(place.reads, "A place with no name in this data, within 30 minutes")
        XCTAssertFalse(String(reflecting: chips(odd)).contains("by_boat"))
    }

    func test_an_inferred_weight_is_assumed_as_a_whole() {
        let inferred = spec(
            like: meta.defaults.rent,
            weights: [FeatureWeight(featureId: .greenCover, weight: 0.5, direction: .more, provenance: .inferred)])

        let drawn = chips(inferred)

        XCTAssertEqual(
            drawn.map(\.reads), ["Renting assumed", "Public parks and gardens as a share of the area assumed"])
        XCTAssertEqual(drawn[1].removal, Edits.featureOff(.greenCover))
    }

    func test_only_the_kinds_that_have_a_control_open_one() {
        let opens: [ChipKind] = [.tenure, .budget, .place("a"), .journeys, .feature(.greenCover), .tag(.leafy)]

        XCTAssertTrue(opens.allSatisfy(\.opensAControl))
        XCTAssertFalse(ChipKind.area("a").opensAControl)
        XCTAssertEqual(ChipKind.place("a").key, .place("a"))
        XCTAssertEqual(ChipKind.tag(.leafy).key, .tag(.leafy))
    }

    // MARK: - The line that says what has just happened

    private func after(_ events: SearchEvent...) -> SearchState {
        events.reduce(SearchState(meta: meta, areas: Answers.areas), reduce)
    }

    func test_the_line_names_the_first_area_there_is_a_name_for() {
        let ranked = Answers.ranked("rank-first")
        var nameless = after(.rankAnswered(ranked, sent: .none))
        nameless.areas = []

        // The journey and the budget count for more than what was asked of the place, and the line says so.
        XCTAssertEqual(
            SearchStatus.line(after(.rankAnswered(ranked, sent: .none))),
            "21 areas ranked. First: Farrowmere. Journey and budget count most.")
        XCTAssertEqual(SearchStatus.line(nameless), "21 areas ranked. Journey and budget count most.")
    }

    func test_the_line_says_what_counts_for_more_than_what_was_asked_of_the_place() {
        let first = Answers.ranked("rank-first").spec
        let scale = Answers.ranked("rank-scale").spec

        XCTAssertEqual(first.mostAskedOfThePlace, 0.5)
        XCTAssertEqual(first.leads, Leads(journey: true, budget: true, journeys: 1))
        // Nothing but a vibe was asked for: nothing outweighs it.
        XCTAssertNil(scale.leads)
        // Nothing was asked of the place: there is nothing to outweigh.
        XCTAssertNil(meta.defaults.rent.leads)
        XCTAssertNil(Answers.ranked("rank-two-journeys").spec.leads)
        XCTAssertEqual(
            SearchStatus.line(after(.rankAnswered(Answers.ranked("rank-scale"), sent: .none))),
            "21 areas ranked. First: Farrowmere.")
        // While the spec on screen is not the one that was ranked, nothing is said of what leads.
        var ahead = after(.rankAnswered(Answers.ranked("rank-first"), sent: .none))
        ahead.specHash = "another"
        XCTAssertNil(ahead.leads)
    }

    func test_the_line_says_when_there_is_nothing_to_rank_by() {
        let state = after(.rankAnswered(Answers.ranked("rank-empty-spec"), sent: .none))

        XCTAssertTrue(SearchStatus.line(state).hasSuffix("Nothing is set to rank them by, so they are in no order."))
    }

    func test_the_line_says_one_thing_for_each_state() {
        XCTAssertEqual(SearchStatus.line(after()), "")
        XCTAssertEqual(SearchStatus.line(after(.readStarted(seq: 1))), "Reading your search")
        XCTAssertEqual(
            SearchStatus.line(after(.rankAnswered(Answers.ranked("rank-nothing-matches"), sent: .none))),
            "No area passes every limit you set.")
        XCTAssertEqual(
            SearchStatus.line(after(.readAnswered(Answers.read("interpret-clarify")))),
            "Burro has a question about a place.")
        XCTAssertEqual(SearchCopy.Status.moved(0), "No area changed place.")
        XCTAssertEqual(SearchCopy.Status.moved(1), "1 area changed place.")
        XCTAssertEqual(SearchCopy.Status.moved(7), "7 areas changed place.")
        XCTAssertEqual(SearchCopy.Status.ranked(1, first: "A"), "1 area ranked. First: A.")
    }

    func test_where_no_limit_left_an_area_out_the_line_does_not_say_that_one_did() {
        let first = Answers.ranked("rank-first")
        var state = after(.rankAnswered(first, sent: .none))
        // Every area has too little data for what counts, and no limit was set.
        state.ranking = Ranking(
            scores: [], ranked: [], filtered: [], unranked: first.unranked, emptySpec: false)

        XCTAssertEqual(
            SearchStatus.line(state),
            "No area could be ranked. This data holds too little of what counts in your search.")
        XCTAssertEqual(Results.headline(of: state), SearchStatus.line(state))
    }
}
