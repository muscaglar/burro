import XCTest

@testable import BurroKit

/// The controls of the settings: what each offers, how a number is read and
/// kept to its steps, and the one edit each change sends.
final class ControlsTests: XCTestCase {
    private let limits = Answers.meta.limits

    // MARK: - A number that is typed

    func test_a_typed_number_is_read_whatever_is_written_round_it() {
        XCTAssertEqual(NumberEntry.read("1700"), .number(1700))
        XCTAssertEqual(NumberEntry.read(" £1,700 "), .number(1700))
        XCTAssertEqual(NumberEntry.read("1 700"), .number(1700))
        XCTAssertEqual(NumberEntry.read("0"), .number(0))
    }

    func test_what_is_no_whole_number_is_said_to_be_none_and_is_never_sent() {
        for typed in ["12.5", "-3", "ten", "1e3", "12a", "٣٤", "9999999999999999999999"] {
            XCTAssertEqual(NumberEntry.read(typed), .notANumber, typed)
        }
    }

    func test_an_empty_field_goes_back_to_what_the_api_said() {
        XCTAssertEqual(NumberEntry.read(""), .empty)
        XCTAssertEqual(NumberEntry.read("  £ , "), .empty)
    }

    func test_a_journey_time_is_brought_within_the_limits_before_it_is_sent_and_a_budget_is_not() {
        let minutes = AmountScale.minutes(.pt, limits)

        XCTAssertEqual(NumberEntry.read("5", keptWithin: minutes.limits), .number(10))
        XCTAssertEqual(NumberEntry.read("500", keptWithin: minutes.limits), .number(90))
        XCTAssertEqual(NumberEntry.read("35", keptWithin: minutes.limits), .number(35))
        // A budget is sent as typed, so that the API can say it is out of range.
        XCTAssertEqual(NumberEntry.read("1"), .number(1))
    }

    // MARK: - A weight

    func test_a_weight_is_shown_from_0_to_100_and_keeps_to_the_steps_the_api_serves() {
        let scale = WeightScale(limits)

        XCTAssertEqual(scale.unit, 5)
        XCTAssertEqual(scale.step, 10)
        XCTAssertEqual(WeightScale.hundredths(0.05), 5)
        XCTAssertEqual(WeightScale.hundredths(0.8), 80)
        XCTAssertEqual(WeightScale.weight(80), 0.8)
        XCTAssertEqual(scale.snapped(52.4), 50)
        XCTAssertEqual(scale.snapped(52.6), 55)
        XCTAssertEqual(scale.snapped(-20), 0)
        XCTAssertEqual(scale.snapped(250), 100)
    }

    func test_every_slider_can_be_set_without_dragging() {
        let scale = WeightScale(limits)
        var value = 0
        var steps = 0
        while value < WeightScale.most, steps < 100 {
            value = scale.moved(value, .up)
            steps += 1
        }

        // The plus button alone takes a weight from nothing to everything, and the minus back.
        XCTAssertEqual(value, 100)
        XCTAssertEqual(steps, 10)
        XCTAssertEqual(scale.moved(100, .up), 100)
        XCTAssertEqual(scale.moved(0, .down), 0)
        XCTAssertEqual(scale.moved(95, .up), 100)
        XCTAssertEqual(scale.moved(5, .down), 0)
        XCTAssertEqual(Edits.budgetStep(.up).budgetOps.first?.step, .upSmall)
        XCTAssertEqual(Edits.placeStep("a", .down).commuteOps.first?.step, .downSmall)
    }

    // MARK: - An amount on a slider

    func test_a_budget_on_its_slider_runs_between_the_limits_the_api_serves_for_the_tenure() {
        let rent = AmountScale.budget(.rent, limits)
        let buy = AmountScale.budget(.buy, limits)

        XCTAssertEqual([rent.least, rent.most, rent.unit], [300, 20_000, 25])
        XCTAssertEqual([buy.least, buy.most, buy.unit], [50_000, 20_000_000, 5_000])
        XCTAssertEqual(rent.value(at: 0), 300)
        XCTAssertEqual(rent.value(at: 1), 20_000)
        XCTAssertEqual(rent.value(at: -3), 300)
        XCTAssertEqual(rent.value(at: .nan), 300)
        XCTAssertEqual(rent.value(at: 7), 20_000)
        XCTAssertEqual(rent.position(of: 300), 0)
        XCTAssertEqual(rent.position(of: 20_000), 1, accuracy: 0.000_001)
        XCTAssertEqual(rent.position(of: 1), 0)
    }

    func test_every_amount_a_slider_gives_is_on_a_step_and_within_the_limits() {
        for scale in [AmountScale.budget(.rent, limits), .budget(.buy, limits), .minutes(.pt, limits)] {
            for place in stride(from: 0.0, through: 1.0, by: 0.01) {
                let value = scale.value(at: place)

                XCTAssertTrue(scale.limits.contains(value))
                XCTAssertEqual((value - scale.least) % scale.unit, 0)
            }
        }
    }

    func test_a_slider_stands_where_its_amount_is() {
        for scale in [AmountScale.budget(.rent, limits), .budget(.buy, limits), .minutes(.cycle, limits)] {
            for value in [scale.least, scale.least + scale.unit * 7, scale.most - scale.unit, scale.most] {
                XCTAssertEqual(scale.value(at: scale.position(of: value)), value)
            }
        }
    }

    func test_the_amounts_most_people_set_are_not_all_at_one_end_of_a_budget() {
        let rent = AmountScale.budget(.rent, limits)

        // Half way along is a rent a person might pay, not half of the most there can be.
        XCTAssertLessThan(rent.value(at: 0.5), 3_000)
        XCTAssertGreaterThan(rent.value(at: 0.5), 1_500)
        XCTAssertEqual(AmountScale(least: 0, most: 10, unit: 1, curve: .widening).curve, .even)
    }

    func test_the_longest_journey_is_no_longer_than_the_data_holds_for_that_way_of_travelling() {
        XCTAssertEqual(AmountScale.minutes(.pt, limits).limits, 10...90)
        XCTAssertEqual(AmountScale.minutes(.cycle, limits).limits, 10...60)
        XCTAssertEqual(AmountScale.minutes(.walk, limits).limits, 10...60)
        XCTAssertEqual(SettingsForm.minutesHint(.pt, limits), "Between 10 and 90 minutes.")
        XCTAssertEqual(SettingsForm.budgetHint(.rent, limits), "Between £300 and £20,000.")
        XCTAssertEqual(SettingsForm.budgetHint(.buy, limits), "Between £50,000 and £20,000,000.")
    }

    // MARK: - What a control shows between being changed and being answered

    func test_a_control_shows_what_it_was_set_to_until_the_answer_comes() {
        var draft = Draft<Bool>()

        XCTAssertFalse(draft.shown(false, at: 3))
        draft.set(true, at: 3)
        XCTAssertTrue(draft.shown(false, at: 3))
        XCTAssertTrue(draft.isSet(at: 3))
        // The answer came, and it is what stands, whatever it says.
        XCTAssertFalse(draft.shown(false, at: 4))
        XCTAssertFalse(draft.isSet(at: 4))
        draft.set(true, at: 4)
        draft.clear()
        XCTAssertFalse(draft.shown(false, at: 4))
    }

    @MainActor
    func test_a_change_is_sent_once_a_moment_after_the_last_press() async {
        let settling = Settling()
        var sent: [Int] = []

        for value in 1...5 {
            settling.soon(after: 0.01) { sent.append(value) }
        }
        await settling.settled()

        XCTAssertEqual(sent, [5])
    }

    @MainActor
    func test_lifting_the_finger_sends_at_once_in_place_of_what_was_waiting() async {
        let settling = Settling()
        var sent: [String] = []

        settling.soon(after: 0.05) { sent.append("waited") }
        settling.now { sent.append("now") }
        try? await Task.sleep(nanoseconds: 80_000_000)

        XCTAssertEqual(sent, ["now"])
    }

    // MARK: - What the form offers

    func test_the_kinds_of_home_are_the_ones_the_api_serves_a_cost_for() {
        var served: [Tenure: Set<Segment>] = [:]
        for area in Answers.areas {
            for cost in Answers.profile(area.slug).cost {
                served[cost.tenure, default: []].insert(cost.segment)
            }
        }

        XCTAssertEqual(Set(SettingsForm.segments(for: .rent)), served[.rent])
        XCTAssertEqual(Set(SettingsForm.segments(for: .buy)), served[.buy])
        XCTAssertEqual(SettingsForm.segments(for: .unlisted("lease")), [])
        for kind in SettingsForm.segments(for: .rent) + SettingsForm.segments(for: .buy) {
            XCTAssertNotNil(CodeCopy.segment(kind))
        }
        // The default of each tenure is a kind its own form offers.
        XCTAssertTrue(SettingsForm.segments(for: .rent).contains(Answers.meta.defaults.rent.budget.segment))
        XCTAssertTrue(SettingsForm.segments(for: .buy).contains(Answers.meta.defaults.buy.budget.segment))
    }

    func test_the_form_offers_every_feature_the_release_can_rank_once_under_its_group() {
        let groups = SettingsForm.groups(Answers.meta)
        let crime = SettingsForm.crime(Answers.meta)
        let offered = groups.flatMap(\.features) + (crime?.features ?? [])

        XCTAssertEqual(
            groups.map(\.title),
            ["Stations", "Green space and water", "Air and noise", "Venues and culture", "Schools", "Homes"])
        XCTAssertEqual(
            Set(offered.map(\.featureId)), Set(Answers.meta.features.filter(\.rankable).map(\.featureId)))
        XCTAssertEqual(offered.count, Set(offered.map(\.featureId)).count)
    }

    func test_recorded_crime_is_its_own_group_and_is_never_among_the_rest() {
        let crime = SettingsForm.crime(Answers.meta)

        XCTAssertEqual(crime?.title, "Recorded crime")
        XCTAssertEqual(
            crime.map { Set($0.features.map(\.featureId)) }, [.crimeBurglaryTheft, .crimeViolenceRobbery])
        XCTAssertFalse(SettingsForm.groups(Answers.meta).contains { $0.dimension == .crime })
        XCTAssertFalse(
            SettingsForm.groups(Answers.meta).flatMap(\.features).contains { $0.dimension == .crime })
    }

    func test_recorded_crime_is_off_until_it_is_switched_on() {
        for spec in [Answers.meta.defaults.rent, Answers.meta.defaults.buy] {
            for feature in SettingsForm.crime(Answers.meta)?.features ?? [] {
                XCTAssertFalse(
                    SearchChips.counts(spec.weights.first { $0.featureId == feature.featureId }?.weight))
            }
        }
    }

    func test_the_caveat_of_recorded_crime_is_the_contracts_word_for_word() throws {
        let contract = try Repository.text(Repository.root.appendingPathComponent("docs/design/contract.md"))

        XCTAssertTrue(contract.contains(SettingsCopy.Crime.caveat))
    }

    func test_no_word_of_the_settings_says_safe_or_unsafe() throws {
        for file in try Written.files() {
            let words = try Written.words(
                in: Repository.sources.appendingPathComponent("Features/\(file.name)"))
            for said in words {
                let lower = said.lowercased()
                XCTAssertFalse(lower.contains("safe"), "\(file.name): \(said)")
                XCTAssertFalse(lower.contains("dangerous"), "\(file.name): \(said)")
            }
        }
    }

    // MARK: - The one edit each change sends

    @MainActor
    func test_each_control_sends_one_edit_that_says_a_control_made_it() async throws {
        let changes: [Operations] = [
            Edits.budgetAmount(1700), Edits.budgetStep(.up), Edits.budgetClear(),
            Edits.budgetSegment(.bed2), Edits.budgetStrictness(SettingsForm.firm(true)),
            Edits.budgetWeight(0.6), Edits.placeMode("syn-p0021", .cycle),
            Edits.placeMinutes("syn-p0021", 30), Edits.placeStep("syn-p0021", .down),
            Edits.placeStrictness("syn-p0021", SettingsForm.firm(false)),
            Edits.placeRemove("syn-p0021"), Edits.journeyCombine(.mean), Edits.journeyBasis(.justMissed),
            Edits.journeyWeight(0.5), SettingsForm.feature(.greenCover, on: true),
            SettingsForm.feature(.greenCover, on: false), Edits.featureWeight(.greenCover, 0.4),
            Edits.featureDirection(.homesFlats, 0.4, .less), SettingsForm.tag(.leafy, on: true),
            SettingsForm.tag(.leafy, on: false), Edits.tagWeight(.leafy, 0.4),
            Edits.areaClear("syn-n0006"),
        ]
        let search = OpenSearch()

        for change in changes {
            await search.flow.applyEdits(change)
            let body = try search.api.lastCall(to: .rank).body(as: RankBody.self)
            let sent = try XCTUnwrap(try search.api.lastCall(to: .rank).body?["operations"])

            XCTAssertEqual(body.operations, change)
            XCTAssertEqual(change.count, 1)
            XCTAssertTrue(String(reflecting: sent).contains("ui_edit"))
        }
        XCTAssertEqual(search.api.calls(to: .rank).count, changes.count)
        XCTAssertEqual(search.api.calls(to: .interpret).count, 0)
    }

    func test_a_switch_turned_on_is_worth_what_a_word_is_and_off_takes_the_thing_out() {
        XCTAssertEqual(SettingsForm.feature(.greenCover, on: true), Edits.featureOn(.greenCover))
        XCTAssertEqual(SettingsForm.feature(.greenCover, on: true).weightOps.first?.step, .upLarge)
        XCTAssertEqual(SettingsForm.feature(.greenCover, on: false).weightOps.first?.action, .remove)
        XCTAssertEqual(SettingsForm.tag(.leafy, on: true).tagOps.first?.step, .upLarge)
        XCTAssertEqual(SettingsForm.tag(.leafy, on: false).tagOps.first?.action, .remove)
        XCTAssertEqual(SettingsForm.firm(true), .hard)
        XCTAssertEqual(SettingsForm.firm(false), .soft)
    }

    @MainActor
    func test_the_control_is_drawn_from_the_spec_the_api_returned_and_never_from_the_edit() async {
        let search = OpenSearch(StandIn.firstSearch().on(.rank, "rank-switched-off"))

        // The answer is what stands: the stand-in returns a spec of its own, and the
        // controls are drawn from that, whatever was asked for.
        await search.flow.applyEdits(Edits.tagOn(.buzzy))

        XCTAssertEqual(search.state.spec, Answers.ranked("rank-switched-off").spec)
        let walk = search.state.spec.weights.first { $0.featureId == .stationWalk }
        XCTAssertEqual(walk?.weight, 0)
        XCTAssertFalse(SearchChips.counts(walk?.weight))
        XCTAssertFalse(search.state.spec.tags.contains { $0.tagId == .buzzy })
    }

    func test_a_hidden_area_has_a_button_that_shows_it_again() {
        let state = SearchState(meta: Answers.meta, areas: Answers.areas)
        let farrowmere = Answers.areas[5]

        XCTAssertEqual(
            SettingsForm.show(
                AreaRule(areaId: farrowmere.areaId, rule: .exclude, provenance: .uiEdit), in: state),
            "Show Farrowmere again")
        XCTAssertEqual(
            SettingsForm.show(
                AreaRule(areaId: farrowmere.areaId, rule: .only, provenance: .uiEdit), in: state),
            "Stop showing only Farrowmere")
        XCTAssertNil(
            SettingsForm.show(
                AreaRule(areaId: farrowmere.areaId, rule: .unlisted("dim"), provenance: .uiEdit), in: state))
    }

    // MARK: - The box

    func test_the_count_of_characters_left_shows_once_fewer_than_a_hundred_remain() {
        let most = limits.maxText

        XCTAssertNil(PromptText.left(String(repeating: "a", count: most - 100), of: most))
        XCTAssertEqual(PromptText.left(String(repeating: "a", count: most - 99), of: most), 99)
        XCTAssertEqual(PromptText.left(String(repeating: "a", count: most), of: most), 0)
        XCTAssertEqual(SearchCopy.Prompt.left(1), "1 character left")
        XCTAssertEqual(SearchCopy.Prompt.left(99), "99 characters left")
    }

    func test_the_box_holds_no_more_than_the_api_takes() {
        let most = limits.maxText

        XCTAssertEqual(PromptText.kept(String(repeating: "a", count: most + 50), to: most).count, most)
        XCTAssertEqual(PromptText.kept("leafy", to: most), "leafy")
        XCTAssertTrue(PromptText.isEmpty("  \n "))
        XCTAssertFalse(PromptText.isEmpty(" leafy "))
    }
}
