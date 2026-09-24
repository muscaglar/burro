import XCTest

@testable import BurroKit

/// The edits a control sends: one edit each, as the website writes them.
final class EditsTests: XCTestCase {
    private func sent(in scenario: String) throws -> JSON? {
        try JSON.read(XCTUnwrap(Recorded.read(scenario).sent))["operations"]
    }

    private let every: [Operations] = [
        Edits.tenure(.buy), Edits.budgetAmount(1700), Edits.budgetStep(.up), Edits.budgetClear(),
        Edits.budgetSegment(.bed2), Edits.budgetStrictness(.hard), Edits.budgetWeight(0.5),
        Edits.placeAdd("syn-p0021"), Edits.placeMode("syn-p0021", .cycle),
        Edits.placeMinutes("syn-p0021", 30), Edits.placeStep("syn-p0021", .down),
        Edits.placeStrictness("syn-p0021", .hard), Edits.placeRemove("syn-p0021"),
        Edits.journeyCombine(.mean), Edits.journeyBasis(.justMissed), Edits.journeyWeight(0.4),
        Edits.featureOn(.greenCover), Edits.featureWeight(.greenCover, 0.6),
        Edits.featureDirection(.homesFlats, 0.3, .less), Edits.featureOff(.stationWalk),
        Edits.tagOn(.villageFeel), Edits.tagWeight(.leafy, 0.2), Edits.tagOff(.leafy),
        Edits.tagOn(.pace, toward: .low), Edits.tagWeight(.pace, 0.5, toward: .low),
        Edits.areaHide("syn-n0006"), Edits.areaClear("syn-n0006"),
    ]

    func test_every_control_sends_one_edit_and_says_a_control_made_it() throws {
        for operations in every {
            XCTAssertEqual(operations.count, 1)
            let text = String(decoding: try JSONEncoder().encode(operations), as: UTF8.self)
            XCTAssertTrue(text.contains(#""provenance":"ui_edit""#))
            XCTAssertFalse(text.contains("null"))
        }
        XCTAssertEqual(Set(every).count, every.count)
    }

    func test_an_edit_is_written_as_the_website_writes_it() throws {
        XCTAssertEqual(try JSON.written(Edits.featureOff(.stationWalk)), try sent(in: "rank-switched-off"))
        XCTAssertEqual(try JSON.written(Edits.placeRemove("syn-p9999")), try sent(in: "rank-stale-spec-repaired"))
        XCTAssertEqual(try JSON.written(Edits.budgetAmount(1)), try sent(in: "rank-rejected-edit"))
        let refined = Edits.placeMinutes("syn-p0021", 30).commuteOps[0]
        let both = CommuteEdit(
            action: refined.action, placeId: refined.placeId, mode: refined.mode, maxMinutes: 30,
            strictness: .hard, step: refined.step, provenance: refined.provenance)
        XCTAssertEqual(
            try JSON.written(
                Operations(budgetOps: [], commuteOps: [both], weightOps: [], tagOps: [], areaOps: [], settingOps: [])),
            try sent(in: "rank-refined"))
        XCTAssertNotEqual(try JSON.written(Edits.budgetAmount(2)), try sent(in: "rank-rejected-edit"))
        XCTAssertEqual(try JSON.written(Edits.placeMode("syn-p0021", .walk)), try sent(in: "rank-on-foot"))
        XCTAssertEqual(
            try JSON.written(Edits.featureOn(.crimeBurglaryTheft)), try sent(in: "rank-crime-switched-on"))
    }

    func test_an_edit_of_a_vibe_says_which_end_is_asked_for_as_the_website_writes_it() throws {
        // A vibe that is added is asked for towards its high end, unless the other is named.
        XCTAssertEqual(try JSON.written(Edits.tagOn(.leafy)), try sent(in: "rank-shelf"))
        XCTAssertEqual(try JSON.written(Edits.tagOn(.pace)), try sent(in: "visit/23-shelf-rank"))
        // A scale is turned by setting how much it counts, towards the end that was chosen.
        XCTAssertEqual(
            try JSON.written(Edits.tagWeight(.pace, 0.5, toward: .high)), try sent(in: "rank-scale-turned"))
        XCTAssertEqual(
            try JSON.written(Edits.tagWeight(.pace, 0.5, toward: .low)), try sent(in: "visit/25-turned-rank"))
        // How much a vibe counts leaves the end that is asked for as it is.
        XCTAssertEqual(Edits.tagWeight(.leafy, 0.2).tagOps[0].toward, .default)
        XCTAssertEqual(Edits.tagOff(.leafy).tagOps[0].toward, .default)
        XCTAssertEqual(Edits.tagOn(.pace, toward: .low).tagOps[0].toward, .low)
    }

    func test_a_field_an_edit_has_nothing_to_say_in_carries_its_sentinel() {
        let budget = Edits.budgetAmount(1700).budgetOps[0]
        let commute = Edits.placeMode("syn-p0021", .walk).commuteOps[0]
        let weight = Edits.featureOn(.greenCover).weightOps[0]
        let setting = Edits.journeyCombine(.mean).settingOps[0]

        XCTAssertEqual([budget.tenure.rawValue, budget.segment.rawValue, budget.strictness.rawValue],
            ["unchanged", "unchanged", "unchanged"])
        XCTAssertEqual(budget.step, .nothing)
        XCTAssertEqual(commute.action, .update)
        XCTAssertEqual([commute.maxMinutes, commute.strictness == .unchanged ? 1 : 0], [0, 1])
        XCTAssertEqual(weight.action, .nudge)
        XCTAssertEqual([weight.step, weight.direction == .default ? .upLarge : .nothing], [.upLarge, .upLarge])
        XCTAssertEqual(weight.value, 0)
        XCTAssertEqual(setting.choice, .mean)
        XCTAssertEqual(Edits.journeyWeight(0.4).settingOps[0].choice, .nothing)
    }

    func test_edits_are_merged_group_by_group_in_the_order_they_were_made() {
        let merged = Edits.tagOn(.leafy)
            .merged(with: Edits.budgetAmount(1700))
            .merged(with: Edits.tagOff(.villageFeel))

        XCTAssertEqual(merged.count, 3)
        XCTAssertEqual(merged.tagOps.map(\.tagId), [.leafy, .villageFeel])
        XCTAssertEqual(merged.budgetOps.map(\.amount), [1700])
        XCTAssertTrue(Operations.none.isEmpty)
        XCTAssertEqual(Operations.none.merged(with: .none), .none)
        XCTAssertEqual(OpsGroup.inOrder.map { merged.count(in: $0) }, [1, 0, 0, 2, 0, 0])
    }

    func test_the_answer_to_a_question_is_the_edit_it_asked_about_with_the_id_that_was_picked() throws {
        let read = Answers.read("interpret-clarify")
        let asked = try XCTUnwrap(read.clarify.first)

        let answer = try XCTUnwrap(Edits.answered(read.operations, asked.group, asked.index, id: "syn-p0012"))

        // Nothing else of the edit is touched, so what the words said of the journey is kept.
        let edit = read.operations.commuteOps[0]
        XCTAssertEqual(
            answer.commuteOps,
            [
                CommuteEdit(
                    action: edit.action, placeId: "syn-p0012", mode: edit.mode, maxMinutes: 30,
                    strictness: edit.strictness, step: edit.step, provenance: .stated)
            ])
        XCTAssertEqual(answer.count, 1)
        XCTAssertNil(Edits.answered(read.operations, .commuteOps, 7, id: "syn-p0012"))
        XCTAssertNil(Edits.answered(read.operations, .budgetOps, 0, id: "syn-p0012"))
        XCTAssertEqual(
            Edits.answered(Edits.areaHide(""), .areaOps, 0, id: "syn-n0006"), Edits.areaHide("syn-n0006"))
    }

    func test_each_edit_is_about_a_part_of_the_search_and_says_what_it_states_of_it() {
        XCTAssertEqual(Edits.tenure(.buy).said(.budgetOps, 0), [Said(key: .tenure, states: [.tenure])])
        XCTAssertEqual(Edits.budgetAmount(1700).said(.budgetOps, 0), [Said(key: .budget, states: [])])
        XCTAssertEqual(
            Edits.budgetStrictness(.hard).said(.budgetOps, 0), [Said(key: .budget, states: [.strictness])])
        XCTAssertEqual(Edits.budgetClear().said(.budgetOps, 0), [Said(key: .budget, states: [])])
        XCTAssertEqual(
            Edits.placeMode("syn-p0021", .walk).said(.commuteOps, 0),
            [Said(key: .place("syn-p0021"), states: [.mode])])
        XCTAssertEqual(
            Edits.placeStep("syn-p0021", .up).said(.commuteOps, 0),
            [Said(key: .place("syn-p0021"), states: [.maxMinutes])])
        XCTAssertEqual(
            Edits.featureDirection(.homesFlats, 0.3, .less).said(.weightOps, 0),
            [Said(key: .feature(.homesFlats), states: [.weight, .direction])])
        // A vibe a person set is theirs: it is no longer what a word with two meanings was read as.
        XCTAssertEqual(
            Edits.tagOn(.leafy).said(.tagOps, 0), [Said(key: .tag(.leafy), states: [.weight, .word])])
        XCTAssertEqual(Edits.areaHide("syn-n0006").said(.areaOps, 0), [Said(key: .area("syn-n0006"), states: [])])
        XCTAssertEqual(Edits.budgetWeight(0.5).said(.settingOps, 0), [Said(key: .budget, states: [])])
        XCTAssertEqual(Edits.journeyBasis(.typical).said(.settingOps, 0), [Said(key: .journeys, states: [])])
        XCTAssertEqual(Edits.tagOn(.leafy).said(.tagOps, 3), [])
        XCTAssertEqual(Edits.tagOn(.leafy).said(.unlisted("later_ops"), 0), [])
    }

    func test_an_assumption_belongs_to_the_part_its_edit_is_about() {
        let read = Answers.read("interpret-first")

        XCTAssertEqual(read.operations.chip(.budgetOps, 0, .strictness), .budget)
        XCTAssertEqual(read.operations.chip(.budgetOps, 0, .tenure), .tenure)
        XCTAssertEqual(read.operations.chip(.commuteOps, 0, .mode), .place("syn-p0021"))
        XCTAssertNil(read.operations.chip(.budgetOps, 4, .strictness))
        XCTAssertNil(read.operations.chip(.weightOps, 0, .weight))
    }
}
