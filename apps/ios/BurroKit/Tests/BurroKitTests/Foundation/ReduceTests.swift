import XCTest

@testable import BurroKit

/// The one function that moves a search on: every event, and what it leaves.
final class ReduceTests: XCTestCase {
    private let meta = Answers.meta
    private let areas = Answers.areas
    private let read = Answers.read("interpret-first")
    private let ranked = Answers.ranked("rank-first")
    private let refined = Answers.ranked("rank-refined")
    private let shared = Answers.shared("share-opened")
    private let reasons = Answers.explained("explanations-first")
    private let later = Answers.explained("explanations-refined")
    private let shareId = "3TQkoOxY0dYBEVyMymzDjg"
    private let timeout = Failure.because(.timeout)
    private let offline = Failure.because(.offline)

    private func opened() -> SearchState {
        SearchState(meta: meta, areas: areas)
    }

    private func after(_ events: SearchEvent...) -> SearchState {
        events.reduce(opened(), reduce)
    }

    // MARK: - The whole

    func test_a_search_opens_empty_on_a_renters_defaults_as_the_api_served_them() {
        let state = opened()

        XCTAssertEqual(state.phase, .empty)
        XCTAssertEqual(state.spec, meta.defaults.rent)
        XCTAssertTrue(state.untouched)
        XCTAssertEqual(state.pending, .none)
        XCTAssertNil(state.read)
        XCTAssertNil(state.ranking)
        XCTAssertNil(state.failure)
        XCTAssertNil(state.specHash)
        XCTAssertTrue(state.online)
    }

    func test_the_state_has_no_field_for_a_sentence() {
        let fields = Mirror(reflecting: opened()).children.compactMap(\.label)
        let named = ["text", "prompt", "sentence", "query", "typed", "words"]

        XCTAssertGreaterThan(fields.count, 25)
        XCTAssertEqual(fields.filter { field in named.contains { field.lowercased().contains($0) } }, [])
    }

    func test_no_event_carries_a_sentence() throws {
        let events = try Repository.text(Repository.sources.appendingPathComponent("Search/SearchState.swift"))
        let declared = try XCTUnwrap(events.components(separatedBy: "public enum SearchEvent").last)

        // The only text an event holds is an id of the release, or the name the API gave a place.
        for word in ["text", "prompt", "sentence", "query", "typed", "words"] {
            XCTAssertFalse(declared.lowercased().contains(word), word)
        }
    }

    func test_the_same_state_and_the_same_event_give_the_same_state() {
        let before = after(.readStarted(seq: 1), .readAnswered(read))

        let once = reduce(before, .rankAnswered(ranked, sent: .none))
        let again = reduce(before, .rankAnswered(ranked, sent: .none))

        XCTAssertEqual(once, again)
        XCTAssertEqual(before, after(.readStarted(seq: 1), .readAnswered(read)))
    }

    func test_the_spec_changes_only_when_the_api_returns_one() {
        let second = Answers.read("interpret-second-sentence")
        let events: [(String, SearchEvent)] = [
            ("tenureSwapped", .tenureSwapped(.buy)),
            ("queued", .queued(Edits.tagOn(.leafy))),
            ("readStarted", .readStarted(seq: 1)),
            ("readAnswered", .readAnswered(read)),
            ("rankStarted", .rankStarted(seq: 2)),
            ("rankAnswered", .rankAnswered(refined, sent: .none)),
            ("shareAnswered", .shareAnswered(id: shareId, shared)),
            ("explainAnswered", .explainAnswered(reasons, hash: ranked.specHash)),
            ("explainFailed", .explainFailed(hash: ranked.specHash, timeout)),
            ("detailAnswered", .detailAnswered(Answers.profile("farrowmere"))),
            ("detailFailed", .detailFailed(areaId: "syn-n0006", timeout)),
            ("settled", .settled),
            ("failed", .failed(step: .rank, timeout)),
            ("stopped", .stopped),
            ("questionAnswered", .questionAnswered(Clarify(group: .commuteOps, index: 0, options: []), id: "syn-p0012")),
            ("questionLeft", .questionLeft(Clarify(group: .commuteOps, index: 0, options: []))),
            ("suggestionChosen", .suggestionChosen(at: 0, changes: true)),
            ("allAdded", .allAdded(ats: [0])),
            ("allTakenBack", .allTakenBack),
            ("readMoreAnswered", .readMoreAnswered(Answers.read("interpret-by-model-long"))),
            ("readMoreFailed", .readMoreFailed),
            ("boxChanged", .boxChanged),
            ("placeNamed", .placeNamed(placeId: "syn-p0021", name: "Cindermoor Works")),
            ("onlineChanged", .onlineChanged(false)),
            ("settingsOpened", .settingsOpened(true)),
            ("geometryLoaded", .geometryLoaded(Answers.geometry)),
            ("geometryFailed", .geometryFailed),
            ("releaseChanged", .releaseChanged(meta: meta, areas: areas)),
            ("selected", .selected(areaId: "syn-n0006")),
            ("startedAgain", .startedAgain),
        ]

        var changing: Set<String> = []
        for (name, event) in events {
            var before = after(.readAnswered(second))
            before.untouched = name == "tenureSwapped"
            if reduce(before, event).spec != before.spec { changing.insert(name) }
        }

        // A default the API served is swapped in before anything is asked for, and on starting again.
        XCTAssertEqual(
            changing, ["rankAnswered", "readAnswered", "shareAnswered", "startedAgain", "tenureSwapped"])
    }

    func test_every_spec_a_search_holds_is_one_the_api_returned() {
        let returned: Set<PreferenceSpec> = [
            meta.defaults.rent, meta.defaults.buy, read.spec, ranked.spec, refined.spec, shared.spec,
        ]
        let states = [
            opened(),
            after(.tenureSwapped(.buy)),
            after(.readAnswered(read)),
            after(.readAnswered(read), .queued(Edits.tagOn(.villageFeel))),
            after(.readAnswered(read), .rankAnswered(ranked, sent: .none)),
            after(.rankAnswered(ranked, sent: .none), .rankAnswered(refined, sent: Edits.placeMinutes("syn-p0021", 30))),
            after(.shareAnswered(id: shareId, shared)),
            after(.rankAnswered(ranked, sent: .none), .startedAgain),
        ]

        XCTAssertEqual(states.filter { !returned.contains($0.spec) }.count, 0)
    }

    func test_the_answers_are_counted_so_that_a_control_knows_to_draw_itself_again() {
        let counts = [
            opened(),
            after(.readAnswered(read)),
            after(.readAnswered(read), .rankAnswered(ranked, sent: .none)),
            after(.tenureSwapped(.buy)),
            after(.queued(Edits.tagOn(.leafy))),
            after(.failed(step: .rank, timeout)),
        ].map(\.answers)

        XCTAssertEqual(counts, [0, 1, 2, 1, 0, 0])
    }

    // MARK: - Each event

    func test_the_tenure_is_swapped_only_before_anything_is_asked_for() {
        let asked = after(.rankAnswered(ranked, sent: .none))

        XCTAssertEqual(reduce(opened(), .tenureSwapped(.buy)).spec, meta.defaults.buy)
        XCTAssertEqual(reduce(reduce(opened(), .tenureSwapped(.buy)), .tenureSwapped(.rent)).spec, meta.defaults.rent)
        XCTAssertEqual(reduce(asked, .tenureSwapped(.buy)), asked)
        XCTAssertEqual(reduce(opened(), .tenureSwapped(.unlisted("lease"))), opened())
    }

    func test_an_edit_that_is_made_waits_until_it_is_answered() {
        let state = after(.queued(Edits.tagOn(.villageFeel)), .queued(Edits.budgetAmount(1700)))

        XCTAssertEqual(state.pending, Edits.tagOn(.villageFeel).merged(with: Edits.budgetAmount(1700)))
        XCTAssertEqual(state.spec, meta.defaults.rent)
        XCTAssertEqual(reduce(state, .rankAnswered(ranked, sent: state.pending)).pending, .none)
    }

    func test_reading_begins_from_where_the_search_stood_and_clears_the_last_failure() {
        let failed = after(.rankAnswered(ranked, sent: .none), .failed(step: .rank, timeout))

        let state = reduce(failed, .readStarted(seq: 4))

        XCTAssertEqual(state.phase, .interpreting)
        XCTAssertEqual(state.before, .results)
        XCTAssertEqual(state.seq, 4)
        XCTAssertNil(state.failure)
        XCTAssertNil(state.failedStep)
        XCTAssertEqual(reduce(opened(), .readStarted(seq: 1)).before, .empty)
    }

    func test_a_reading_sets_the_spec_and_says_what_was_read_and_never_the_words() {
        let state = after(.readStarted(seq: 1), .readAnswered(read))

        XCTAssertEqual(state.spec, read.spec)
        XCTAssertEqual(state.specHash, read.specHash)
        XCTAssertFalse(state.untouched)
        XCTAssertEqual(state.phase, .interpreting)
        XCTAssertEqual(state.read?.edits, 4)
        XCTAssertEqual(state.read?.changed, true)
        XCTAssertEqual(state.read?.at, 1)
        XCTAssertEqual(state.read?.interpreter, .rule)
        XCTAssertEqual(state.read?.operations, read.operations)
        XCTAssertFalse(state.settingsOpen)
        XCTAssertFalse(state.degraded)
    }

    func test_what_was_assumed_is_kept_by_the_part_it_was_assumed_of() {
        let state = after(.readAnswered(read))

        XCTAssertEqual(state.assumed, [.budget: [.strictness], .place("syn-p0021"): [.mode, .strictness]])
    }

    func test_an_assumption_goes_when_the_person_sets_that_part() {
        let state = after(
            .readAnswered(read),
            .queued(Edits.placeMode("syn-p0021", .walk)),
            .queued(Edits.budgetStrictness(.hard)))

        XCTAssertEqual(state.assumed, [.place("syn-p0021"): [.strictness]])
        XCTAssertEqual(reduce(state, .queued(Edits.placeRemove("syn-p0021"))).assumed, [:])
    }

    func test_the_kind_of_house_that_burro_took_is_assumed_and_one_a_person_pressed_is_not() throws {
        // A person named a house and no kind of house. One press holds the budget against a
        // terraced house, in an edit that says the kind is Burro's.
        let house = Answers.read("interpret-suggest-house")
        let ways = try XCTUnwrap(house.suggestions.first { $0.target == "budget" }).ways
        let terraced = try XCTUnwrap(ways.first { $0.id == "terraced" }).operations
        let semi = try XCTUnwrap(ways.first { $0.id == "semi_detached" }).operations

        let taken = after(.readAnswered(house), .queued(terraced))
        XCTAssertEqual(taken.assumed[.budget], [.segment])
        // Another kind, pressed by the person, is theirs. It takes the mark off.
        XCTAssertNil(reduce(taken, .queued(semi)).assumed[.budget])
        XCTAssertNil(after(.readAnswered(house), .queued(semi)).assumed[.budget])
    }

    func test_the_kind_of_house_of_a_plain_sentence_is_assumed_as_the_api_says() {
        let state = after(.readAnswered(Answers.read("interpret-house")))

        XCTAssertEqual(state.assumed[.budget], [.strictness, .segment])
    }

    func test_a_reading_that_read_nothing_opens_the_settings() {
        let nothing = after(.readAnswered(Answers.read("interpret-nothing-read")))
        let offTopic = after(.readAnswered(Answers.read("interpret-off-topic")))
        let degraded = after(.readAnswered(Answers.read("interpret-degraded")))

        XCTAssertTrue(nothing.settingsOpen)
        XCTAssertTrue(nothing.untouched)
        XCTAssertTrue(offTopic.settingsOpen)
        XCTAssertTrue(degraded.settingsOpen)
        XCTAssertTrue(degraded.degraded)
        // A question is not nothing: the rest was read.
        XCTAssertFalse(after(.readAnswered(Answers.read("interpret-clarify"))).settingsOpen)
    }

    func test_ranking_after_a_reading_is_still_reading_and_ranking_alone_is_refining() {
        let reading = after(.readStarted(seq: 1), .readAnswered(read), .rankStarted(seq: 1))
        let refining = after(.rankAnswered(ranked, sent: .none), .rankStarted(seq: 2))
        let first = after(.rankStarted(seq: 1))

        XCTAssertEqual([reading.phase, reading.before], [.interpreting, .empty])
        XCTAssertEqual([refining.phase, refining.before], [.refining, .results])
        XCTAssertEqual([first.phase, first.before], [.refining, .empty])
    }

    func test_a_ranking_sets_the_results_and_empties_what_waited() {
        let state = after(
            .queued(Edits.placeMinutes("syn-p0021", 30)),
            .rankStarted(seq: 1),
            .rankAnswered(ranked, sent: Edits.placeMinutes("syn-p0021", 30)))

        XCTAssertEqual(state.phase, .results)
        XCTAssertEqual(state.before, .results)
        XCTAssertEqual(state.ranking?.ranked, ranked.ranked)
        XCTAssertEqual(state.ranking?.scores.count, 21)
        XCTAssertEqual(state.rankedHash, ranked.specHash)
        XCTAssertEqual(state.pending, .none)
        XCTAssertNil(state.moved)
        XCTAssertNil(state.refused)
        XCTAssertFalse(state.untouched)
    }

    func test_a_second_ranking_says_how_many_areas_changed_place() {
        let state = after(.rankAnswered(ranked, sent: .none), .rankAnswered(refined, sent: .none))

        XCTAssertEqual(state.moved, movedBetween(Ranking(ranked), Ranking(refined)))
        XCTAssertGreaterThan(state.moved ?? 0, 0)
        XCTAssertEqual(after(.rankAnswered(ranked, sent: .none), .rankAnswered(ranked, sent: .none)).moved, 0)
    }

    func test_an_edit_the_reducer_refused_is_kept_with_the_edits_it_points_into() {
        let sent = Edits.budgetAmount(1)
        let refusing = Answers.ranked("rank-rejected-edit")

        let state = after(.queued(sent), .rankAnswered(refusing, sent: sent))

        XCTAssertEqual(state.refused, Refused(operations: sent, rejected: refusing.rejected))
        XCTAssertEqual(state.refusedByPart, [.budget: .outOfRange])
        XCTAssertNil(reduce(state, .rankAnswered(ranked, sent: .none)).refused)
    }

    func test_a_shared_search_takes_the_place_of_the_search_whole() {
        let before = after(
            .geometryLoaded(Answers.geometry),
            .readAnswered(read),
            .rankAnswered(ranked, sent: .none),
            .placeNamed(placeId: "syn-p0021", name: "Cindermoor Works"),
            .queued(Edits.tagOn(.villageFeel)),
            .selected(areaId: "syn-n0006"))

        let state = reduce(before, .shareAnswered(id: shareId, shared))

        XCTAssertEqual(state.spec, shared.spec)
        XCTAssertEqual(state.specHash, shared.specHash)
        XCTAssertEqual(state.ranking, Ranking(shared))
        XCTAssertEqual(state.phase, .results)
        XCTAssertEqual(
            state.shared,
            Shared(id: shareId, coarsened: true, stale: false, originalReleaseId: "syn-2026-09-23-01"))
        // Nothing of the search before is carried into it. The places are named by the share's own answer.
        XCTAssertNil(state.read)
        XCTAssertEqual(state.placeNames, ["syn-p0005": "Eskerfold"])
        XCTAssertNil(state.placeNames["syn-p0021"])
        XCTAssertEqual(state.pending, .none)
        XCTAssertNil(state.selectedId)
        XCTAssertEqual(state.explanations, [])
        XCTAssertEqual(state.assumed, [:])
        // What the search was opened on stays: the release is the same one.
        XCTAssertEqual(state.meta, before.meta)
        XCTAssertEqual(state.geometry, before.geometry)
        XCTAssertGreaterThan(state.answers, before.answers)
    }

    func test_a_search_the_person_began_did_not_come_from_a_link() {
        XCTAssertNil(opened().shared)
        XCTAssertNil(after(.rankAnswered(ranked, sent: .none)).shared)
    }

    func test_a_profile_is_kept_by_its_area_with_the_facts_it_cites() {
        let profile = Answers.profile("farrowmere")
        let failed = after(
            .detailFailed(areaId: profile.area.areaId, timeout),
            .detailFailed(areaId: profile.area.areaId, timeout))

        let state = reduce(failed, .detailAnswered(profile))

        XCTAssertEqual(failed.detailsFailed, [profile.area.areaId])
        XCTAssertEqual(state.details[profile.area.areaId], profile)
        XCTAssertEqual(state.detailsFailed, [])
        XCTAssertEqual(Set(state.facts.keys), Set(profile.facts.map(\.factId)))
    }

    func test_a_reading_that_asked_for_no_ranking_ends_where_the_search_stood() {
        XCTAssertEqual(after(.readStarted(seq: 1), .settled).phase, .empty)
        XCTAssertEqual(
            after(.rankAnswered(ranked, sent: .none), .readStarted(seq: 2), .settled).phase, .results)
        XCTAssertEqual(reduce(opened(), .settled), opened())
    }

    func test_a_failure_returns_to_the_phase_before_and_keeps_what_was_on_screen() {
        let state = after(
            .rankAnswered(ranked, sent: .none),
            .queued(Edits.tagOn(.villageFeel)),
            .rankStarted(seq: 2),
            .failed(step: .rank, timeout))

        XCTAssertEqual(state.phase, .results)
        XCTAssertEqual(state.ranking?.ranked, ranked.ranked)
        XCTAssertEqual(state.pending, Edits.tagOn(.villageFeel))
        XCTAssertEqual(state.failure, timeout)
        XCTAssertEqual(state.failedStep, .rank)
        XCTAssertFalse(state.degraded)
    }

    func test_only_a_failure_to_read_the_words_leaves_the_settings_as_the_way_in() {
        func degraded(_ step: SearchStep, _ failure: Failure) -> Bool {
            after(.readStarted(seq: 1), .failed(step: step, failure)).degraded
        }

        XCTAssertTrue(degraded(.read, timeout))
        XCTAssertTrue(degraded(.read, .because(.network)))
        XCTAssertTrue(degraded(.read, .because(.unreadable)))
        XCTAssertTrue(degraded(.read, Answers.failure("error-internal")))
        XCTAssertFalse(degraded(.read, Answers.failure("interpret-invalid-text")))
        XCTAssertFalse(degraded(.read, offline))
        XCTAssertFalse(degraded(.rank, timeout))
        XCTAssertTrue(after(.readStarted(seq: 1), .failed(step: .read, timeout)).settingsOpen)
    }

    func test_a_failure_that_says_offline_says_the_phone_is_offline() {
        let state = after(.rankStarted(seq: 1), .failed(step: .rank, offline))

        XCTAssertFalse(state.online)
        XCTAssertTrue(after(.rankStarted(seq: 1), .failed(step: .rank, timeout)).online)
    }

    func test_stopping_returns_to_the_phase_before_and_reports_nothing() {
        let state = after(.rankAnswered(ranked, sent: .none), .readStarted(seq: 2), .stopped)

        XCTAssertEqual(state.phase, .results)
        XCTAssertNil(state.failure)
        XCTAssertEqual(after(.readStarted(seq: 1), .stopped).phase, .empty)
    }

    func test_starting_again_keeps_the_release_and_forgets_the_search() {
        let state = after(
            .geometryLoaded(Answers.geometry),
            .readAnswered(read),
            .rankAnswered(ranked, sent: .none),
            .placeNamed(placeId: "syn-p0021", name: "Cindermoor Works"),
            .selected(areaId: "syn-n0006"),
            .startedAgain)

        var fresh = SearchState(meta: meta, areas: areas, geometry: Answers.geometry)
        fresh.answers = 3
        XCTAssertEqual(state, fresh)
    }

    func test_a_question_that_is_answered_goes_and_what_was_assumed_moves_to_the_place_picked() throws {
        let asking = Answers.read("interpret-clarify")
        let question = try XCTUnwrap(asking.clarify.first)
        let before = after(.readAnswered(asking))
        XCTAssertEqual(before.assumed, [.place(""): [.mode, .strictness]])

        let state = reduce(before, .questionAnswered(question, id: "syn-p0012"))

        XCTAssertEqual(state.read?.clarify, [])
        // The question stood for this refusal. With the question gone, so is it.
        XCTAssertEqual(state.read?.rejected, [])
        XCTAssertEqual(state.assumed, [.place("syn-p0012"): [.mode, .strictness]])
        XCTAssertEqual(state.spec, before.spec)
    }

    func test_a_question_that_is_left_out_goes_and_nothing_else_changes() throws {
        let asking = Answers.read("interpret-clarify")
        let question = try XCTUnwrap(asking.clarify.first)
        let before = after(.readAnswered(asking))

        let state = reduce(before, .questionLeft(question))

        XCTAssertEqual(state.read?.clarify, [])
        XCTAssertEqual(state.read?.rejected, [])
        XCTAssertEqual(state.pending, .none)
        XCTAssertEqual(state.spec, before.spec)
        XCTAssertEqual(reduce(opened(), .questionLeft(question)), opened())
    }

    func test_a_place_is_named_when_it_is_picked_and_from_the_fact_of_its_journey() {
        XCTAssertEqual(
            after(.placeNamed(placeId: "syn-p0012", name: "Pellam Cross")).placeNames,
            ["syn-p0012": "Pellam Cross"])
        XCTAssertEqual(
            after(.explainAnswered(reasons, hash: ranked.specHash)).placeNames,
            ["syn-p0021": "Cindermoor Works"])
    }

    func test_a_place_is_named_by_the_answer_that_brought_the_spec() {
        XCTAssertEqual(after(.readAnswered(read)).placeNames, ["syn-p0021": "Cindermoor Works"])
        XCTAssertEqual(after(.rankAnswered(ranked, sent: .none)).placeNames, ["syn-p0021": "Cindermoor Works"])
        XCTAssertEqual(opened().placeNames, [:])
    }

    // MARK: - What Burro noticed, and what it did not read

    func test_a_reading_keeps_what_was_noticed_and_applies_none_of_it() {
        let noticed = Answers.read("interpret-suggest")

        let state = after(.readStarted(seq: 1), .readAnswered(noticed), .settled)

        XCTAssertEqual(state.read?.suggestions, noticed.suggestions)
        XCTAssertEqual(state.suggestions.map(\.label), ["Pubs and bars", "Less transport noise"])
        XCTAssertEqual(state.unread, [Span(start: 5, end: 11)])
        // Nothing is applied until the person chooses: the search is as it was, and nothing waits.
        XCTAssertEqual(noticed.applied, [])
        XCTAssertEqual(state.spec, meta.defaults.rent)
        XCTAssertTrue(state.untouched)
        XCTAssertEqual(state.pending, .none)
        XCTAssertNil(state.ranking)
        // Where something was noticed there is something to choose from, and the settings stay shut.
        XCTAssertFalse(state.settingsOpen)
        XCTAssertNil(state.nothingRead)
    }

    func test_nothing_is_offered_while_a_sentence_is_being_read() {
        let reading = after(.readAnswered(Answers.read("interpret-suggest")), .readStarted(seq: 2))

        XCTAssertEqual(reading.suggestions, [])
        XCTAssertEqual(reading.unread, [])
    }

    func test_a_suggestion_goes_when_it_is_chosen_whatever_was_chosen() {
        let before = after(.readAnswered(Answers.read("interpret-suggest")))

        let left = reduce(before, .suggestionChosen(at: 0, changes: false))

        XCTAssertEqual(left.suggestions.map(\.label), ["Less transport noise"])
        XCTAssertEqual(left.spec, before.spec)
        XCTAssertEqual(left.pending, .none)
        XCTAssertEqual(reduce(left, .suggestionChosen(at: 0, changes: true)).suggestions, [])
        // A place in the list that holds nothing changes nothing.
        XCTAssertEqual(reduce(before, .suggestionChosen(at: 7, changes: true)), before)
        XCTAssertEqual(reduce(opened(), .suggestionChosen(at: 0, changes: true)), opened())
    }

    func test_a_choice_that_changes_the_search_takes_the_notice_with_it() {
        let before = after(.readAnswered(Answers.read("interpret-suggest-notice")))

        // The notice may end by saying that nothing typed changed the search. A choice that
        // holds edits changes it, and the notice is the API's, so it goes whole.
        XCTAssertTrue(before.noticed)
        XCTAssertTrue(reduce(before, .suggestionChosen(at: 0, changes: false)).noticed)
        XCTAssertFalse(reduce(before, .suggestionChosen(at: 0, changes: true)).noticed)
    }

    func test_what_rested_on_what_was_sent_goes_when_the_box_changes() {
        let before = after(.readAnswered(Answers.read("interpret-suggest")))

        let state = reduce(before, .boxChanged)

        XCTAssertEqual(state.suggestions, [])
        XCTAssertEqual(state.unread, [])
        // That a part was not read stays true of the reading.
        XCTAssertEqual(state.read?.partUnread, true)
        XCTAssertEqual(state.spec, before.spec)
        XCTAssertEqual(reduce(state, .boxChanged), state)
        XCTAssertEqual(reduce(opened(), .boxChanged), opened())
    }

    func test_what_a_model_read_joins_what_is_offered_and_only_while_it_is_waited_for() {
        let atOnce = Answers.read("interpret-rules-at-once")
        let long = Answers.read("interpret-by-model-long")
        let waiting = after(.readStarted(seq: 1), .readAnswered(atOnce), .settled)

        let joined = reduce(waiting, .readMoreAnswered(long))

        // The rules say whether a model has more to read, and what they noticed is there meanwhile.
        XCTAssertEqual(waiting.read?.more, true)
        XCTAssertEqual(waiting.suggestions, atOnce.suggestions)
        XCTAssertEqual(joined.read?.more, false)
        XCTAssertEqual(joined.suggestions, long.suggestions)
        XCTAssertEqual(joined.unread, long.unread)
        XCTAssertEqual(joined.read?.interpreter, .model)
        // Nothing of it is applied: the search is as it was.
        XCTAssertEqual(joined.spec, waiting.spec)
        XCTAssertEqual(joined.answers, waiting.answers)
        XCTAssertNil(joined.ranking)
        // An answer that nobody waits for changes nothing.
        XCTAssertEqual(reduce(joined, .readMoreAnswered(atOnce)), joined)
        XCTAssertEqual(reduce(opened(), .readMoreAnswered(long)), opened())
        let plain = after(.readAnswered(Answers.read("interpret-suggest")))
        XCTAssertEqual(plain.read?.more, false)
        XCTAssertEqual(reduce(plain, .readMoreAnswered(long)), plain)
    }

    func test_a_model_that_did_not_answer_leaves_what_the_rules_offered() throws {
        let atOnce: InterpretData = try Visit.answer("slow-at-once")
        let slow: InterpretData = try Visit.answer("slow")
        let waiting = after(.readStarted(seq: 1), .readAnswered(atOnce), .settled)

        let failed = reduce(waiting, .readMoreFailed)
        let answered = reduce(waiting, .readMoreAnswered(slow))

        XCTAssertEqual(failed.read?.more, false)
        XCTAssertEqual(failed.suggestions, atOnce.suggestions)
        XCTAssertFalse(failed.degraded)
        XCTAssertEqual(reduce(failed, .readMoreFailed), failed)
        // The service answered for a model that did not: the rules' offers, and that the model did not read.
        XCTAssertEqual(answered.suggestions.map(\.label), ["Nearer a river or canal"])
        XCTAssertTrue(answered.degraded)
        XCTAssertEqual(answered.read?.degraded, true)
        XCTAssertEqual(answered.read?.interpreter, .rule)
        // There is something to choose from, so the settings stay shut.
        XCTAssertFalse(answered.settingsOpen)
    }

    func test_what_was_chosen_of_while_a_model_read_is_not_offered_again() {
        let atOnce = Answers.read("interpret-rules-at-once")
        let long = Answers.read("interpret-by-model-long")
        let waiting = after(.readAnswered(atOnce))

        let chosen = reduce(waiting, .suggestionChosen(at: 0, changes: true))
        let joined = reduce(chosen, .readMoreAnswered(long))

        XCTAssertEqual(chosen.read?.chosen, [atOnce.suggestions[0].key])
        XCTAssertEqual(atOnce.suggestions[0].key, long.suggestions[0].key)
        XCTAssertEqual(joined.suggestions, Array(long.suggestions.dropFirst()))
        // The model's reading is let go when the box changes, with what rested on what was sent.
        let changed = reduce(waiting, .boxChanged)
        XCTAssertEqual(changed.read?.more, false)
        XCTAssertEqual(reduce(changed, .readMoreAnswered(long)), changed)
    }

    func test_a_reading_says_when_the_language_model_would_not_read_the_words() {
        let refused = after(.readAnswered(Answers.read("interpret-refused")))
        let degraded = after(.readAnswered(Answers.read("interpret-degraded")))

        XCTAssertEqual(refused.read?.modelRefused, true)
        XCTAssertTrue(refused.modelRefused)
        XCTAssertEqual(degraded.read?.modelRefused, false)
        XCTAssertFalse(degraded.modelRefused)
        XCTAssertFalse(after(.readAnswered(read)).modelRefused)
        XCTAssertFalse(opened().modelRefused)
        // While the next is read nothing is said of the last. The reading before is still
        // held when a read fails, and what nothing read was refused by nothing.
        let reading = reduce(refused, .readStarted(seq: 2))
        let failed = reduce(reading, .failed(step: .read, timeout))
        XCTAssertFalse(reading.modelRefused)
        XCTAssertEqual(failed.read?.modelRefused, true)
        XCTAssertEqual(failed.failurePlace, .form)
        XCTAssertFalse(failed.modelRefused)
        // A model that is asked after the rules says so in its own answer.
        let waiting = after(.readAnswered(Answers.read("interpret-rules-at-once")))
        let joined = reduce(waiting, .readMoreAnswered(Answers.read("interpret-refused")))
        XCTAssertEqual(waiting.read?.modelRefused, false)
        XCTAssertEqual(joined.read?.modelRefused, true)
        XCTAssertTrue(joined.modelRefused)
    }

    func test_one_press_adds_several_and_keeps_what_it_takes_to_take_them_back() {
        let long = Answers.read("interpret-by-model-long")
        let before = after(.readAnswered(long))

        let added = reduce(before, .allAdded(ats: [0, 1, 6, 10, 11]))

        XCTAssertEqual(
            added.suggestions.map(\.label),
            [
                "Mix of brands", "Gritty", "What homes sell for", "Homes in the higher council tax bands",
                "Village feel", "Age of buildings", "Nearer a town centre",
            ])
        XCTAssertEqual(added.read?.added?.count, 5)
        // What is left for the person: of what was added, and then of what was not.
        XCTAssertEqual(
            added.read?.added?.needs,
            [
                "the journey can be made a firm limit", "mix of brands",
                "recorded crime, which is added under its own name", "what homes sell for",
                "homes in the higher council tax bands", "Village feel", "Age of buildings",
                "nearer a town centre",
            ])
        // The budget was added as it was worded, which is firm. No other press adds one.
        XCTAssertEqual(added.read?.added?.firm, true)
        XCTAssertEqual(reduce(before, .allAdded(ats: [0, 1, 6, 10])).read?.added?.firm, false)
        // The search as it stood before the press, and what was offered then.
        XCTAssertEqual(added.read?.added?.spec, before.spec)
        XCTAssertEqual(added.read?.added?.suggestions, long.suggestions)
        XCTAssertEqual(added.read?.chosen, [0, 1, 6, 10, 11].map { long.suggestions[$0].key })
        // The press sends nothing of itself: the search is as it was until the answer comes.
        XCTAssertEqual(added.spec, before.spec)
        XCTAssertEqual(added.pending, .none)
        // A place in the list that holds nothing adds nothing.
        XCTAssertEqual(reduce(before, .allAdded(ats: [17])), before)
        XCTAssertEqual(reduce(before, .allAdded(ats: [])), before)
        XCTAssertEqual(reduce(opened(), .allAdded(ats: [0])), opened())
        XCTAssertEqual(reduce(before, .allAdded(ats: [0, 17])).read?.added?.count, 1)
    }

    func test_what_one_press_added_takes_the_notice_with_it() {
        let before = after(.readAnswered(Answers.read("interpret-suggest-notice")))

        XCTAssertTrue(before.noticed)
        XCTAssertFalse(reduce(before, .allAdded(ats: [0])).noticed)
    }

    func test_taking_it_all_back_offers_again_what_was_offered_before_the_press() {
        let long = Answers.read("interpret-by-model-long")
        let before = after(.readAnswered(long))
        let skipped = reduce(before, .suggestionChosen(at: 2, changes: false))
        let added = reduce(skipped, .allAdded(ats: [0, 1]))

        let back = reduce(added, .allTakenBack)

        // What was offered when the button was pressed is offered again. What the person
        // had chosen of before that is not.
        XCTAssertEqual(back.suggestions, skipped.suggestions)
        XCTAssertEqual(back.suggestions.count, 11)
        XCTAssertEqual(back.read?.chosen, [long.suggestions[2].key])
        XCTAssertNil(back.read?.added)
        XCTAssertEqual(back.spec, before.spec)
        // There is nothing more to take back.
        XCTAssertEqual(reduce(back, .allTakenBack), back)
        XCTAssertEqual(reduce(before, .allTakenBack), before)
        XCTAssertEqual(reduce(opened(), .allTakenBack), opened())
    }

    func test_what_one_press_added_goes_when_the_box_changes_and_with_the_next_reading() {
        let atOnce = Answers.read("interpret-rules-at-once")
        let long = Answers.read("interpret-by-model-long")
        let added = after(.readAnswered(atOnce), .allAdded(ats: [0, 6, 11, 13]))

        XCTAssertEqual(added.added?.count, 4)
        XCTAssertNil(reduce(added, .boxChanged).added)
        XCTAssertEqual(reduce(added, .boxChanged).suggestions, [])
        XCTAssertEqual(reduce(reduce(added, .boxChanged), .boxChanged), reduce(added, .boxChanged))
        // While another is read nothing of the last is said, and its answer takes its place.
        XCTAssertNil(reduce(added, .readStarted(seq: 2)).added)
        XCTAssertNil(reduce(added, .readAnswered(Answers.read("interpret-suggest"))).added)
        // A choice of one thing, and what a model reads meanwhile, take nothing of it away.
        XCTAssertEqual(reduce(added, .suggestionChosen(at: 0, changes: true)).added, added.added)
        let joined = reduce(added, .readMoreAnswered(long))
        XCTAssertEqual(joined.added, added.added)
        // What was added is not offered again when the model has read.
        XCTAssertEqual(
            joined.suggestions.map(\.label),
            [
                "Nearer a park", "Mix of brands", "Gritty", "What homes sell for",
                "Homes in the higher council tax bands", "Village feel", "Age of buildings",
                "Nearer a town centre", "Pellam Exchange", "A budget of £1,900",
            ])
    }

    func test_what_was_asked_for_and_is_not_in_the_data_is_kept_by_the_apis_name_for_it() throws {
        let plain: InterpretData = try Recorded.data(.interpret, "preview/interpret-plain")
        let preview: MetaData = try Recorded.data(.getMeta, "preview/meta")

        let state = reduce(SearchState(meta: preview, areas: areas), .readAnswered(plain))

        XCTAssertEqual(state.read?.notInRelease.map(\.target), ["tag:leafy"])
        XCTAssertEqual(state.missing, [Missing(target: "tag:leafy", label: "Leafy")])
        // It is said once: under the box, and not again among what was not applied.
        XCTAssertEqual(state.refusals.map(\.reason), [.notInRelease])
        XCTAssertEqual(state.refusals.filter { !state.isSaidAsMissing($0) }, [])
        XCTAssertTrue(state.conditions.contains(.notInData))
    }

    func test_coming_back_online_clears_the_failure_that_said_offline_and_no_other() {
        let wasOffline = after(.rankStarted(seq: 1), .failed(step: .rank, offline), .onlineChanged(true))
        let timedOut = after(.rankStarted(seq: 1), .failed(step: .rank, timeout), .onlineChanged(true))

        XCTAssertTrue(wasOffline.online)
        XCTAssertNil(wasOffline.failure)
        XCTAssertNil(wasOffline.failedStep)
        XCTAssertEqual(timedOut.failure, timeout)
        XCTAssertFalse(after(.onlineChanged(false)).online)
    }

    func test_the_settings_open_and_close() {
        XCTAssertTrue(after(.settingsOpened(true)).settingsOpen)
        XCTAssertFalse(after(.settingsOpened(true), .settingsOpened(false)).settingsOpen)
    }

    func test_the_map_is_kept_once_it_has_come_and_a_later_failure_does_not_lose_it() {
        XCTAssertTrue(after(.geometryFailed).geometryFailed)
        let loaded = after(.geometryFailed, .geometryLoaded(Answers.geometry))
        XCTAssertEqual(loaded.geometry, Answers.geometry)
        XCTAssertFalse(loaded.geometryFailed)
        XCTAssertEqual(reduce(loaded, .geometryFailed), loaded)
    }

    func test_an_area_is_chosen_and_let_go() {
        XCTAssertEqual(after(.selected(areaId: "syn-n0006")).selectedId, "syn-n0006")
        XCTAssertNil(after(.selected(areaId: "syn-n0006"), .selected(areaId: nil)).selectedId)
    }

    // MARK: - Reasons that come before the ranking they are for

    private func shown() -> SearchState {
        after(.rankAnswered(ranked, sent: .none), .explainAnswered(reasons, hash: ranked.specHash))
    }

    func test_the_reasons_on_screen_stay_until_the_ranking_the_new_ones_are_for_has_come() {
        let state = reduce(shown(), .explainAnswered(later, hash: refined.specHash))

        XCTAssertEqual(state.explanations, reasons.explanations)
        XCTAssertEqual(state.explainedHash, ranked.specHash)
        XCTAssertEqual(state.explainedHash, state.rankedHash)
        XCTAssertTrue(state.explained)
        // What the new reasons cite is kept, so that they have their sources when their turn comes.
        for fact in later.facts { XCTAssertEqual(state.facts[fact.factId], fact) }
    }

    func test_the_reasons_that_waited_are_the_rankings_when_it_comes() {
        let state = reduce(
            reduce(shown(), .explainAnswered(later, hash: refined.specHash)),
            .rankAnswered(refined, sent: .none))

        XCTAssertEqual(state.explanations, later.explanations)
        XCTAssertEqual(state.explainedHash, refined.specHash)
        XCTAssertNil(state.explanationsAhead)
    }

    func test_a_ranking_that_fails_leaves_the_list_the_reasons_it_has() {
        let state = reduce(
            reduce(shown(), .explainAnswered(later, hash: refined.specHash)),
            .failed(step: .rank, timeout))

        XCTAssertEqual(state.explanations, reasons.explanations)
        XCTAssertEqual(state.explainedHash, state.rankedHash)
    }

    func test_reasons_that_waited_for_another_ranking_are_not_given_to_this_one() {
        let state = reduce(
            reduce(shown(), .explainAnswered(later, hash: String(repeating: "a", count: 64))),
            .rankAnswered(refined, sent: .none))

        XCTAssertEqual(state.explanations, reasons.explanations)
        XCTAssertNotEqual(state.explainedHash, state.rankedHash)
        XCTAssertFalse(state.explained)
        XCTAssertNil(state.explanationsAhead)
    }

    func test_the_first_reasons_of_a_search_are_shown_as_soon_as_they_come() {
        let state = after(.explainAnswered(reasons, hash: ranked.specHash))

        XCTAssertEqual(state.explanations, reasons.explanations)
        XCTAssertNil(state.explanationsAhead)
    }

    func test_reasons_for_the_ranking_on_screen_take_the_place_of_ones_that_were_not() {
        let mismatched = after(
            .rankAnswered(refined, sent: .none), .explainAnswered(reasons, hash: ranked.specHash))

        let state = reduce(mismatched, .explainAnswered(later, hash: refined.specHash))

        XCTAssertEqual(state.explanations, later.explanations)
        XCTAssertEqual(state.explainedHash, state.rankedHash)
    }

    func test_reasons_that_could_not_be_had_are_said_to_have_failed_until_some_come() {
        let failed = after(.rankAnswered(ranked, sent: .none), .explainFailed(hash: ranked.specHash, timeout))

        XCTAssertTrue(failed.explainFailed)
        XCTAssertFalse(reduce(failed, .explainAnswered(reasons, hash: ranked.specHash)).explainFailed)
    }

    // MARK: - How much a ranking moved

    func test_an_area_that_changed_place_came_in_or_went_out_has_moved() {
        func scores(_ ids: String...) -> Ranking {
            Ranking(
                scores: ids.map { Score(areaId: $0, score: 1, counted: 1, present: 1) }, ranked: [], filtered: [],
                unranked: [],
                emptySpec: false)
        }

        XCTAssertEqual(movedBetween(scores("a", "b", "c"), scores("a", "b", "c")), 0)
        XCTAssertEqual(movedBetween(scores("a", "b", "c"), scores("b", "a", "c")), 2)
        XCTAssertEqual(movedBetween(scores("a", "b", "c"), scores("a", "b")), 1)
        XCTAssertEqual(movedBetween(scores("a", "b"), scores("a", "b", "c")), 1)
        XCTAssertEqual(movedBetween(scores("a", "b", "c"), scores("b", "c")), 3)
    }

    func test_defaults_gave_way_when_a_setting_nobody_chose_counts_for_less_than_it_did() {
        XCTAssertTrue(gaveWayBetween(meta.defaults.rent, read.spec))
        XCTAssertFalse(gaveWayBetween(read.spec, refined.spec))
        XCTAssertFalse(gaveWayBetween(meta.defaults.rent, meta.defaults.rent))
        XCTAssertTrue(after(.readAnswered(read)).gaveWay)
        XCTAssertTrue(after(.readStarted(seq: 1), .readAnswered(read), .rankAnswered(ranked, sent: .none)).gaveWay)
        XCTAssertFalse(after(.rankAnswered(ranked, sent: .none), .rankAnswered(refined, sent: .none)).gaveWay)
    }
}
