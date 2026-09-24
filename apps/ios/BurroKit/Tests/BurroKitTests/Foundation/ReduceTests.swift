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
    private let shareId = "rPnAeuBsXQci-xINLK_f2w"
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
