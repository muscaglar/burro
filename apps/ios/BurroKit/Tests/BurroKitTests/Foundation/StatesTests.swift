import XCTest

@testable import BurroKit

/// Every state the website's search page has, in the order of
/// docs/design/web.md section 3, each reached from recorded answers.
final class StatesTests: XCTestCase {
    private let read = Answers.read("interpret-first")
    private let ranked = Answers.ranked("rank-first")
    private let timeout = Failure.because(.timeout)

    private func after(_ events: SearchEvent...) -> SearchState {
        events.reduce(SearchState(meta: Answers.meta, areas: Answers.areas), reduce)
    }

    func test_every_phase_and_every_condition_is_reached() {
        let states: [SearchState] = [
            after(),
            after(.readStarted(seq: 1)),
            after(.readAnswered(read), .rankAnswered(ranked, sent: .none)),
            after(.rankAnswered(ranked, sent: .none), .rankStarted(seq: 2)),
            after(.readAnswered(Answers.read("interpret-clarify"))),
            after(.rankAnswered(Answers.ranked("rank-nothing-matches"), sent: .none)),
            after(.readAnswered(Answers.read("interpret-nothing-read"))),
            after(.readAnswered(Answers.read("interpret-second-sentence")),
                .readAnswered(Answers.read("interpret-second-sentence").unchanged)),
            after(.readAnswered(Answers.read("interpret-degraded"))),
            after(.readAnswered(Answers.read("interpret-notice"))),
            after(.readAnswered(Answers.read("interpret-suggest"))),
            after(.readAnswered(read.leaving(unread: [Span(start: 0, end: 7)]))),
            after(.readAnswered(Answers.read("preview/interpret-plain"))),
            after(.rankStarted(seq: 1), .failed(step: .rank, Answers.failure("rank-stale-spec"))),
            after(.rankStarted(seq: 1), .failed(step: .rank, .because(.offline))),
        ]

        XCTAssertEqual(Set(states.map(\.phase)), Set(Phase.allCases))
        XCTAssertEqual(states.reduce(into: Set()) { $0.formUnion($1.conditions) }, Set(SearchCondition.allCases))
    }

    func test_empty_no_search_yet() {
        let state = after()

        XCTAssertEqual(state.phase, .empty)
        XCTAssertEqual(state.conditions, [])
        XCTAssertFalse(state.settingsOpen)
        XCTAssertEqual(state.spec, Answers.meta.defaults.rent)
        XCTAssertFalse(state.isBusy)
    }

    func test_interpreting_the_words_are_being_read() {
        let state = after(.readStarted(seq: 1))

        XCTAssertEqual(state.phase, .interpreting)
        XCTAssertTrue(state.isReading)
        XCTAssertTrue(state.isBusy)
        // Stop returns to the state before.
        XCTAssertEqual(reduce(state, .stopped).phase, .empty)
    }

    func test_results_a_ranking_with_at_least_one_area() {
        let state = after(.readStarted(seq: 1), .readAnswered(read), .rankAnswered(ranked, sent: .none))

        XCTAssertEqual(state.phase, .results)
        XCTAssertEqual(state.conditions, [])
        XCTAssertEqual(state.ranking?.ranked.count, ranked.ranked.count)
        XCTAssertEqual(state.ranking?.ranked.first?.areaId, "syn-n0006")
        XCTAssertEqual(state.area("syn-n0006")?.name, "Farrowmere")
        XCTAssertFalse(state.explained)
    }

    func test_results_say_what_could_not_be_answered_and_what_was_not_applied() {
        let unmet = after(.readAnswered(Answers.read("interpret-unmet")))
        let rejected = after(.readAnswered(Answers.read("interpret-rejected")))

        XCTAssertEqual(unmet.unmetShown, [.broadband, .floodRisk, .communityAmenities])
        // A budget that was asked to be lower where none is set: there is nothing to lower.
        XCTAssertEqual(rejected.refusals, [Refusal(key: .budget, reason: .nothingToChange)])
    }

    func test_suggestions_what_was_noticed_is_offered_and_nothing_is_ranked_from_it() {
        let state = after(.readStarted(seq: 1), .readAnswered(Answers.read("interpret-suggest")), .settled)

        XCTAssertEqual(state.phase, .empty)
        XCTAssertEqual(state.conditions, [.suggesting])
        XCTAssertEqual(state.read?.status, .suggest)
        XCTAssertEqual(state.suggestions.count, 2)
        XCTAssertNil(state.ranking)
        XCTAssertEqual(state.spec, Answers.meta.defaults.rent)
        XCTAssertFalse(state.settingsOpen)
        // The line that says nothing was read is not said: something was noticed.
        XCTAssertNil(state.nothingRead)
    }

    func test_read_in_part_something_was_read_and_a_stretch_was_not() {
        let part = after(.readAnswered(read.leaving(unread: [Span(start: 0, end: 7)])))
        let nothing = after(.readAnswered(Answers.read("interpret-nothing-read")))

        XCTAssertEqual(part.conditions, [.readInPart])
        XCTAssertTrue(part.readInPart)
        XCTAssertEqual(part.unread, [Span(start: 0, end: 7)])
        // Where nothing at all was read, the line that says so is the one that is said.
        XCTAssertFalse(nothing.readInPart)
        XCTAssertEqual(nothing.conditions, [.nothingRead])
        XCTAssertEqual(nothing.unread, [Span(start: 0, end: 39)])
    }

    func test_not_in_the_data_what_was_asked_for_and_is_held_for_no_area_is_said_by_name() {
        let state = after(.readAnswered(Answers.read("preview/interpret-plain")))
        let journey = after(.readAnswered(Answers.read("preview/interpret-journey")))
        let home = after(.readAnswered(Answers.read("preview/interpret-home")))

        XCTAssertEqual(state.conditions, [.notInData])
        XCTAssertEqual(state.missing, [Missing(target: "tag:leafy", label: "Leafy")])
        XCTAssertEqual(journey.missing.map(\.target), ["commute"])
        XCTAssertEqual(home.missing.map(\.target), ["budget"])
        for one in [state, journey, home] {
            // It is said once, and not again among what was not applied.
            XCTAssertEqual(one.refusals.filter { !one.isSaidAsMissing($0) }, [])
        }
    }

    func test_refining_the_last_results_stay_while_a_change_is_answered() {
        let state = after(
            .rankAnswered(ranked, sent: .none),
            .queued(Edits.placeMinutes("syn-p0021", 30)),
            .rankStarted(seq: 2))

        XCTAssertEqual(state.phase, .refining)
        XCTAssertTrue(state.isBusy)
        XCTAssertFalse(state.isReading)
        XCTAssertEqual(state.ranking?.ranked, ranked.ranked)
        XCTAssertEqual(state.pending, Edits.placeMinutes("syn-p0021", 30))
    }

    func test_clarifying_a_place_the_rest_was_read_and_the_question_stands_for_the_refusal() {
        let state = after(.readStarted(seq: 1), .readAnswered(Answers.read("interpret-clarify")), .settled)
        let noOptions = after(.readAnswered(Answers.read("interpret-clarify-no-options")))

        XCTAssertEqual(state.conditions, [.clarifying])
        XCTAssertEqual(state.questions.first?.options.map(\.name), ["Pellam Cross", "Pellam Exchange", "Pellam Infirmary"])
        XCTAssertEqual(state.questions.first?.options.map(\.kind), [.station, .district, .hospital])
        // A refusal that a question stands for is not said twice.
        XCTAssertEqual(state.refusals, [])
        XCTAssertNil(state.nothingRead)
        XCTAssertEqual(noOptions.questions.first?.options, [])
        // No question is asked while the next sentence is being read.
        XCTAssertEqual(reduce(state, .readStarted(seq: 2)).questions, [])
    }

    func test_nothing_matches_a_ranking_came_and_no_area_passes() {
        let state = after(.rankAnswered(Answers.ranked("rank-nothing-matches"), sent: .none))

        XCTAssertEqual(state.phase, .results)
        XCTAssertEqual(state.conditions, [.nothingMatches])
        XCTAssertEqual(state.ranking?.ranked, [])
        XCTAssertEqual(state.ranking?.filtered.count, Answers.ranked("rank-nothing-matches").filtered.count)
        XCTAssertEqual(state.ranking?.unranked.count, Answers.ranked("rank-nothing-matches").unranked.count)
    }

    func test_nothing_read_the_settings_open_and_results_already_on_screen_stay() {
        let nothing = Answers.read("interpret-nothing-read")
        let first = after(.readStarted(seq: 1), .readAnswered(nothing), .settled)
        let later = after(
            .rankAnswered(ranked, sent: .none), .readStarted(seq: 2), .readAnswered(nothing), .settled)
        let offTopic = after(.readAnswered(Answers.read("interpret-off-topic")))

        XCTAssertEqual(first.phase, .empty)
        XCTAssertEqual(first.conditions, [.nothingRead])
        XCTAssertTrue(first.settingsOpen)
        // "Part of what you typed could not be read" would say the same thing a second time.
        XCTAssertEqual(first.unmetShown, [])
        XCTAssertEqual(later.phase, .results)
        XCTAssertEqual(later.ranking?.ranked, ranked.ranked)
        XCTAssertEqual(offTopic.conditions, [.nothingRead, .notice])
        XCTAssertEqual(offTopic.read?.noticeText.isEmpty, false)
    }

    func test_nothing_read_and_nothing_changed_are_told_apart() {
        let second = Answers.read("interpret-second-sentence")
        let state = after(.readAnswered(second), .readAnswered(second.unchanged))

        XCTAssertEqual(state.nothingRead, .nothingChanged)
        XCTAssertEqual(state.conditions, [.nothingChanged])
        // The line goes as soon as a control is used and answered.
        XCTAssertNil(reduce(state, .rankAnswered(ranked, sent: .none)).nothingRead)
    }

    func test_degraded_to_a_form_the_words_could_not_be_read_and_the_settings_do_the_same_job() {
        let byRules = after(.readStarted(seq: 1), .readAnswered(Answers.read("interpret-degraded")), .settled)
        let timedOut = after(.readStarted(seq: 1), .failed(step: .read, timeout))
        let fault = after(.readStarted(seq: 1), .failed(step: .read, Answers.failure("error-internal")))

        for state in [byRules, timedOut, fault] {
            XCTAssertTrue(state.conditions.contains(.degraded))
            XCTAssertTrue(state.settingsOpen)
            XCTAssertTrue(state.degraded)
        }
        // If the rules read the words, their results show as usual.
        XCTAssertEqual(byRules.spec, Answers.read("interpret-degraded").spec)
        XCTAssertEqual(timedOut.failurePlace, .form)
        XCTAssertEqual(timedOut.spec, Answers.meta.defaults.rent)
        // Words that could not be read are not a fault to report. The form does the same job.
        XCTAssertEqual(fault.failurePlace, .form)
    }

    func test_neutral_notice_the_apis_sentence_is_shown_word_for_word() {
        let state = after(.readAnswered(Answers.read("interpret-notice")))

        XCTAssertEqual(state.conditions, [.notice])
        XCTAssertTrue(state.noticed)
        XCTAssertEqual(state.read?.notice, .neutralPlaces)
        XCTAssertEqual(state.read?.noticeText, Answers.read("interpret-notice").noticeText)
        XCTAssertEqual(state.read?.status, .policyRedirect)
        XCTAssertFalse(after(.readAnswered(read)).noticed)
    }

    func test_error_from_the_api_one_failure_is_shown_in_one_place() {
        func place(_ step: SearchStep, _ failure: Failure) -> FailurePlace {
            after(.readStarted(seq: 1), .failed(step: step, failure)).failurePlace
        }

        XCTAssertEqual(place(.read, Answers.failure("interpret-invalid-text")), .box)
        XCTAssertEqual(place(.rank, Answers.failure("rank-stale-spec")), .block)
        XCTAssertEqual(place(.read, Answers.failure("rank-stale-spec")), .block)
        XCTAssertEqual(place(.rank, Answers.failure("error-internal")), .block)
        XCTAssertEqual(place(.rank, Answers.failure("rank-invalid-operations")), .block)
        XCTAssertEqual(place(.rank, timeout), .block)
        XCTAssertEqual(place(.read, timeout), .form)
        XCTAssertEqual(place(.rank, .because(.offline)), .offline)
        XCTAssertEqual(after().failurePlace, .none)
    }

    func test_error_from_the_api_a_search_that_names_what_the_data_no_longer_has_can_be_put_right() throws {
        let stale = Answers.failure("rank-stale-spec")
        let sent = try JSONDecoder().decode(
            RankBody.self, from: XCTUnwrap(Recorded.read("rank-stale-spec").sent))
        var state = after(.rankStarted(seq: 1), .failed(step: .rank, stale))
        state.spec = sent.spec

        XCTAssertTrue(stale.isStale)
        XCTAssertEqual(
            state.repairs,
            [Repair(what: .place, key: .place("syn-p9999"), operations: Edits.placeRemove("syn-p9999"))])
        // A position in a path is a position in the spec as the waiting edits leave it.
        XCTAssertEqual(reduce(state, .queued(Edits.tagOn(.leafy))).repairs, [])
        XCTAssertFalse(Answers.failure("rank-invalid-operations").isStale)
        XCTAssertFalse(timeout.isStale)
        XCTAssertEqual(after().repairs, [])
    }

    func test_error_from_the_api_the_last_results_stay_with_the_message_and_the_id_to_quote() {
        let fault = Answers.failure("error-internal")
        let state = after(
            .rankAnswered(ranked, sent: .none), .rankStarted(seq: 2), .failed(step: .rank, fault))

        XCTAssertEqual(state.conditions, [.failed])
        XCTAssertEqual(state.phase, .results)
        XCTAssertEqual(state.ranking?.ranked, ranked.ranked)
        XCTAssertEqual(ShellCopy.words(for: fault), "Something went wrong on the server.")
        XCTAssertNotNil(state.failure?.requestId)
    }

    func test_offline_the_search_is_still_here_and_the_latest_edit_waits() {
        let state = after(
            .rankAnswered(ranked, sent: .none),
            .queued(Edits.tagOn(.villageFeel)),
            .rankStarted(seq: 2),
            .failed(step: .rank, .because(.offline)))
        let told = after(.rankAnswered(ranked, sent: .none), .onlineChanged(false))

        XCTAssertEqual(state.conditions, [.offline])
        XCTAssertFalse(state.online)
        XCTAssertEqual(state.ranking?.ranked, ranked.ranked)
        XCTAssertEqual(state.pending, Edits.tagOn(.villageFeel))
        XCTAssertEqual(told.conditions, [.offline])
        XCTAssertEqual(reduce(state, .onlineChanged(true)).conditions, [])
    }

    func test_no_more_places_can_be_added_once_the_most_are_named() {
        XCTAssertFalse(after().placesFull)
        XCTAssertEqual(Answers.meta.limits.maxCommutes, 3)
        XCTAssertEqual(after(.readAnswered(read)).spec.commutes.count, 1)
    }
}

extension InterpretData {
    /// The same reading, as the API gives it when the search already says all of it.
    var unchanged: InterpretData {
        InterpretData(
            status: status, operations: operations, spec: spec, specHash: specHash,
            applied: applied.map { Applied(group: $0.group, index: $0.index, changed: false) },
            rejected: rejected, assumptions: assumptions, unmet: unmet, clarify: clarify,
            notice: notice, noticeText: noticeText, interpreter: interpreter, degraded: degraded,
            modelRefused: modelRefused, restsOn: restsOn, suggestions: suggestions, unread: unread,
            notInRelease: notInRelease, unmetAt: unmetAt, modelPending: modelPending, places: places)
    }

    /// The same reading, as the API gives it when it made nothing of these stretches of the words.
    func leaving(unread: [Span]) -> InterpretData {
        InterpretData(
            status: status, operations: operations, spec: spec, specHash: specHash, applied: applied,
            rejected: rejected, assumptions: assumptions, unmet: unmet, clarify: clarify,
            notice: notice, noticeText: noticeText, interpreter: interpreter, degraded: degraded,
            modelRefused: modelRefused, restsOn: restsOn, suggestions: suggestions, unread: unread,
            notInRelease: notInRelease, unmetAt: unmetAt, modelPending: modelPending, places: places)
    }
}
