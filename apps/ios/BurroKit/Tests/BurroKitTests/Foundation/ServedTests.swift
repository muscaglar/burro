import XCTest

@testable import BurroKit

/// Which release made what is on screen, what is said when the reasons or a
/// profile cannot be loaded, and what "Stop" puts back. Each is a test of the
/// website's, in `apps/web/src/lib/search/state.test.ts`, under the same name.
final class ServedTests: XCTestCase {
    private let meta = Answers.meta
    private let areas = Answers.areas
    private let read = Answers.read("interpret-first")
    private let second = Answers.read("interpret-second-sentence")
    private let ranked = Answers.ranked("rank-first")
    private let refined = Answers.ranked("rank-refined")
    private let shared = Answers.shared("share-opened")
    private let reasons = Answers.explained("explanations-first")
    private let later = Answers.explained("explanations-refined")
    private let profile = Answers.profile("farrowmere")
    private let shareId = "rPnAeuBsXQci-xINLK_f2w"
    private let timeout = Failure.because(.timeout)
    private let fault = Answers.failure("error-internal")

    /// What every recording was served by, and the same service once it holds a newer release.
    private var a: Served { Served(form: meta) }
    private var b: Served { Served(releaseId: "syn-2026-10-01-01", engineVersion: meta.engineVersion) }
    private var newerEngine: Served { Served(releaseId: meta.releaseId, engineVersion: "9.9.9") }

    private func opened() -> SearchState {
        SearchState(meta: meta, areas: areas)
    }

    private func after(_ events: SearchEvent...) -> SearchState {
        events.reduce(opened(), reduce)
    }

    private func moved(to release: String) -> MetaData {
        MetaData(
            releaseId: release, builtAt: meta.builtAt, synthetic: true, preview: false,
            engineVersion: meta.engineVersion, catalogueVersion: meta.catalogueVersion,
            counts: meta.counts, holds: meta.holds, attributions: meta.attributions,
            features: meta.features, tags: meta.tags, recipes: meta.recipes, families: meta.families,
            grittyVariant: meta.grittyVariant, defaults: meta.defaults, limits: meta.limits,
            reader: meta.reader, census: meta.census)
    }

    // MARK: - A release that changes

    func test_reading_the_form_again_leaves_the_ranking_on_screen_its_reasons_its_facts_and_its_profiles() {
        // The search was opened on an older release. Every answer of the search came from the newer one.
        let before = after(
            .rankAnswered(ranked, sent: .none, by: b),
            .explainAnswered(reasons, hash: ranked.specHash, by: b),
            .detailAnswered(profile, by: b))
        XCTAssertGreaterThan(before.facts.count, 50)

        // The form of the newer release comes last, as it may: it is the largest thing asked for.
        let state = reduce(before, .releaseChanged(meta: moved(to: b.releaseId), areas: areas))

        XCTAssertEqual(state.meta.releaseId, b.releaseId)
        XCTAssertEqual(state.explanations, before.explanations)
        XCTAssertEqual(state.facts, before.facts)
        XCTAssertEqual(state.details, before.details)
        XCTAssertTrue(state.reasonsAreIn)
    }

    func test_what_is_of_the_old_release_goes_when_a_ranking_of_the_new_one_comes() {
        let before = after(
            .rankAnswered(ranked, sent: .none, by: a),
            .explainAnswered(reasons, hash: ranked.specHash, by: a),
            .detailAnswered(profile, by: a))
        XCTAssertTrue(before.reasonsAreIn)

        let state = reduce(before, .rankAnswered(ranked, sent: .none, by: b))

        // Facts and profiles are of the release that made them, so they go with it.
        XCTAssertEqual(state.facts, [:])
        XCTAssertEqual(state.details, [:])
        XCTAssertEqual(state.explanations, [])
        XCTAssertNil(state.explainedHash)
        XCTAssertEqual(state.factsBy, [:])
        XCTAssertEqual(state.detailsBy, [:])
        XCTAssertNil(state.explainedBy)
        XCTAssertFalse(state.reasonsAreIn)
        XCTAssertEqual(state.rankedBy, b)
    }

    func test_a_ranking_of_the_same_release_leaves_the_profiles_and_the_facts_in_hand() {
        let before = after(.rankAnswered(ranked, sent: .none, by: a), .detailAnswered(profile, by: a))

        let state = reduce(before, .rankAnswered(refined, sent: .none, by: a))

        XCTAssertEqual(state.details, before.details)
        XCTAssertEqual(state.facts, before.facts)
    }

    // MARK: - Which release made what is on screen

    func test_the_release_and_the_engine_of_each_answer_are_kept_with_what_it_brought() {
        let state = after(
            .readAnswered(read, by: a),
            .rankAnswered(ranked, sent: .none, by: a),
            .explainAnswered(reasons, hash: ranked.specHash, by: a),
            .detailAnswered(profile, by: a))

        XCTAssertEqual(state.read?.by, a)
        XCTAssertEqual(state.rankedBy, a)
        XCTAssertEqual(state.explainedBy, a)
        XCTAssertEqual(state.detailsBy, [profile.area.areaId: a])
        XCTAssertEqual(Set(state.factsBy.keys), Set(state.facts.keys))
        XCTAssertEqual(Set(state.factsBy.values.map(\.releaseId)), [a.releaseId])
        // Whether the data is made up is the banner's to say, and is not kept a second time here.
        XCTAssertEqual(Mirror(reflecting: a).children.compactMap(\.label), ["releaseId", "engineVersion"])
    }

    func test_an_answer_that_names_no_release_is_taken_to_be_of_the_one_the_form_was_read_from() {
        let state = after(.rankAnswered(ranked, sent: .none), .explainAnswered(reasons, hash: ranked.specHash))

        XCTAssertEqual(state.rankedBy, a)
        XCTAssertEqual(state.explainedBy, a)
        XCTAssertTrue(state.reasonsAreIn)
    }

    func test_the_flow_says_which_release_made_every_answer_it_passes_on() throws {
        let flow = try Repository.text(Repository.sources.appendingPathComponent("Search/SearchFlow.swift"))

        for event in ["readAnswered", "rankAnswered", "shareAnswered", "explainAnswered", "detailAnswered"] {
            let sent = flow.components(separatedBy: ".\(event)(").dropFirst()
            XCTAssertFalse(sent.isEmpty, event)
            for call in sent {
                let line = call.prefix { $0 != "\n" }
                XCTAssertTrue(line.contains("by: Served("), "\(event) is passed on without its release")
            }
        }
    }

    func test_a_shared_search_keeps_the_release_that_ranked_it() {
        let state = after(.shareAnswered(id: shareId, shared, by: b))

        XCTAssertEqual(state.rankedBy, b)
        XCTAssertEqual(state.servedTheRanking, b)
        // Not the release the search was opened on, which is another.
        XCTAssertEqual(state.meta.releaseId, a.releaseId)
    }

    func test_the_release_named_under_a_result_is_the_one_that_made_the_ranking() {
        XCTAssertEqual(opened().servedTheRanking, a)
        XCTAssertEqual(after(.rankAnswered(ranked, sent: .none, by: b)).servedTheRanking, b)
    }

    func test_reasons_made_by_another_release_or_engine_than_the_ranking_are_not_its_reasons() {
        for other in [b, newerEngine] {
            // A hash is of the spec alone, so the two hashes agree whatever release made each answer.
            let state = after(
                .rankAnswered(ranked, sent: .none, by: a),
                .explainAnswered(reasons, hash: ranked.specHash, by: other))

            XCTAssertEqual(state.explainedHash, state.rankedHash)
            XCTAssertFalse(state.reasonsAreIn)
            XCTAssertFalse(state.explained)
        }
    }

    func test_reasons_that_came_first_are_not_the_reasons_of_a_ranking_another_release_made() {
        let state = after(
            .explainAnswered(reasons, hash: ranked.specHash, by: a),
            .rankAnswered(ranked, sent: .none, by: b))

        XCTAssertFalse(state.reasonsAreIn)
        XCTAssertEqual(state.explanations, [])
    }

    func test_reasons_of_another_release_wait_and_the_reasons_on_screen_stay() {
        let shown = after(
            .rankAnswered(ranked, sent: .none, by: a),
            .explainAnswered(reasons, hash: ranked.specHash, by: a))

        let waiting = reduce(shown, .explainAnswered(later, hash: refined.specHash, by: b))
        XCTAssertEqual(waiting.explanations, reasons.explanations)
        XCTAssertTrue(waiting.reasonsAreIn)

        // The ranking they are for comes from the same release, and they are its reasons.
        let state = reduce(waiting, .rankAnswered(refined, sent: .none, by: b))
        XCTAssertEqual(state.explanations, later.explanations)
        XCTAssertEqual(state.explainedBy, b)
        XCTAssertTrue(state.reasonsAreIn)
        for fact in later.facts { XCTAssertEqual(state.factsBy[fact.factId], b) }
    }

    func test_reasons_that_waited_are_not_given_to_a_ranking_another_release_made() {
        let state = after(
            .rankAnswered(ranked, sent: .none, by: a),
            .explainAnswered(reasons, hash: ranked.specHash, by: a),
            .explainAnswered(later, hash: refined.specHash, by: a),
            .rankAnswered(refined, sent: .none, by: b))

        XCTAssertFalse(state.reasonsAreIn)
        XCTAssertNil(state.explanationsAhead)
    }

    func test_a_fact_of_the_rankings_release_is_not_given_up_for_one_of_another() throws {
        let shown = after(
            .rankAnswered(ranked, sent: .none, by: a),
            .explainAnswered(reasons, hash: ranked.specHash, by: a))
        let cited = try XCTUnwrap(reasons.facts.first)
        // The same fact, as another release dated it.
        var dated = try JSON.written(cited)
        dated["as_of"] = .string("1999-01")
        let recorded = try Recorded.read("area/farrowmere").with(data: { $0["facts"] = .array([dated]) })
        let stale = try JSONDecoder().decode(Envelope<AreaData>.self, from: recorded.body).data
        XCTAssertEqual(stale.facts.map(\.factId), [cited.factId])
        XCTAssertNotEqual(stale.facts.first, cited)

        // A profile may be answered from a cache for an hour after the release has moved.
        let state = reduce(shown, .detailAnswered(stale, by: b))

        XCTAssertEqual(state.facts[cited.factId], cited)
        XCTAssertEqual(state.factsBy[cited.factId], a)
        // The profile itself is kept, with the release that made it.
        XCTAssertEqual(state.detailsBy[profile.area.areaId], b)
    }

    // MARK: - Reasons and profiles that could not be loaded

    private func shown() -> SearchState {
        after(.rankAnswered(ranked, sent: .none, by: a))
    }

    func test_a_failure_of_the_reasons_is_kept_whole_with_its_message_and_the_id_to_quote() {
        let state = reduce(shown(), .explainFailed(hash: ranked.specHash, fault))

        XCTAssertEqual(state.reasonsFailure, fault)
        XCTAssertEqual(state.failureOfTheCards, fault)
        XCTAssertNotNil(state.failureOfTheCards?.requestId)
        XCTAssertEqual(state.failureOfTheCards?.api?.message, fault.api?.message)
        // It is not a failure of the search: the ranking is in, and the search is in no other state.
        XCTAssertNil(state.failure)
        XCTAssertNil(state.failedStep)
        XCTAssertEqual(state.phase, .results)
        XCTAssertEqual(state.failurePlace, .none)
    }

    func test_a_failure_of_the_reasons_of_another_search_is_not_a_failure_of_the_one_on_screen() {
        let state = reduce(shown(), .explainFailed(hash: refined.specHash, fault))

        XCTAssertNil(state.reasonsFailure)
        XCTAssertNil(state.failureOfTheCards)
        XCTAssertFalse(state.explainFailed)
    }

    func test_the_failure_goes_when_the_reasons_come() {
        let state = after(
            .rankAnswered(ranked, sent: .none, by: a),
            .explainFailed(hash: ranked.specHash, fault),
            .explainAnswered(reasons, hash: ranked.specHash, by: a))

        XCTAssertNil(state.reasonsFailure)
        XCTAssertTrue(state.reasonsAreIn)
    }

    func test_a_failure_of_a_profile_is_kept_by_its_area_and_goes_when_the_profile_comes() {
        let areaId = profile.area.areaId
        let failed = reduce(shown(), .detailFailed(areaId: areaId, timeout))

        XCTAssertEqual(failed.detailFailures, [areaId: timeout])
        XCTAssertEqual(failed.profilesFailed, [areaId])
        XCTAssertEqual(failed.failureOfTheCards, timeout)

        let state = reduce(failed, .detailAnswered(profile, by: a))
        XCTAssertEqual(state.detailFailures, [:])
        XCTAssertNil(state.failureOfTheCards)
    }

    func test_a_failure_of_the_profile_of_an_area_that_has_no_card_is_not_said() throws {
        let sixth = try XCTUnwrap(ranked.ranked.dropFirst(5).first?.areaId)

        let state = reduce(shown(), .detailFailed(areaId: sixth, timeout))

        XCTAssertEqual(state.detailsFailed, [sixth])
        XCTAssertEqual(state.profilesFailed, [])
        XCTAssertNil(state.failureOfTheCards)
    }

    func test_the_failure_of_the_search_itself_is_said_before_that_of_its_cards() {
        let state = after(
            .rankAnswered(ranked, sent: .none, by: a),
            .explainFailed(hash: ranked.specHash, fault),
            .failed(step: .rank, timeout))

        // One failure is shown in one place: the error block says the one that stopped the search.
        XCTAssertEqual(state.failure, timeout)
        XCTAssertNil(state.failureOfTheCards)
    }

    func test_reasons_or_a_profile_that_could_not_leave_say_that_the_phone_is_offline() {
        let offline = Failure.because(.offline)

        XCTAssertFalse(reduce(shown(), .explainFailed(hash: ranked.specHash, offline)).online)
        XCTAssertFalse(reduce(shown(), .detailFailed(areaId: profile.area.areaId, offline)).online)
        XCTAssertTrue(reduce(shown(), .explainFailed(hash: ranked.specHash, timeout)).online)
        XCTAssertEqual(reduce(shown(), .explainFailed(hash: ranked.specHash, offline)).failurePlace, .offline)
    }

    // MARK: - Stopping after the words were read

    private func searched() -> SearchState {
        after(
            .readStarted(seq: 1),
            .readAnswered(read, by: a),
            .rankStarted(seq: 1),
            .rankAnswered(ranked, sent: .none, by: a),
            .explainAnswered(reasons, hash: ranked.specHash, by: a))
    }

    private func readAgain(_ from: SearchState) -> SearchState {
        [.readStarted(seq: 2), .readAnswered(second, by: a), .rankStarted(seq: 2)].reduce(from, reduce)
    }

    func test_stop_puts_the_search_back_as_it_was_when_the_sentence_was_sent() {
        let before = searched()
        let reading = readAgain(before)
        // The chips already show the second sentence, over the ranking of the first.
        XCTAssertEqual(reading.specHash, second.specHash)
        XCTAssertEqual(reading.rankedHash, ranked.specHash)

        let state = reduce(reading, .stopped)

        XCTAssertEqual(state.phase, .results)
        XCTAssertEqual(state.spec, before.spec)
        XCTAssertEqual(state.specHash, state.rankedHash)
        XCTAssertEqual(state.read, before.read)
        XCTAssertEqual(state.assumed, before.assumed)
        XCTAssertEqual(state.gaveWay, before.gaveWay)
        XCTAssertEqual(state.ranking, before.ranking)
        XCTAssertTrue(state.reasonsAreIn)
        // Every control is drawn again, from the spec that was put back.
        XCTAssertGreaterThan(state.answers, reading.answers)
    }

    func test_reasons_that_came_for_the_ranking_that_was_stopped_are_let_go() {
        let reading = reduce(
            readAgain(searched()),
            .explainAnswered(Answers.explained("explanations-second-sentence"), hash: second.specHash, by: a))
        XCTAssertEqual(reading.explanationsAhead?.hash, second.specHash)

        XCTAssertNil(reduce(reading, .stopped).explanationsAhead)
    }

    func test_stop_on_a_first_search_goes_back_to_the_defaults_as_served() {
        let reading = after(.readStarted(seq: 1), .readAnswered(read, by: a), .rankStarted(seq: 1))

        let state = reduce(reading, .stopped)

        XCTAssertEqual(state.phase, .empty)
        XCTAssertEqual(state.spec, meta.defaults.rent)
        XCTAssertNil(state.specHash)
        XCTAssertNil(state.read)
        XCTAssertNil(state.ranking)
        XCTAssertTrue(state.untouched)
        XCTAssertEqual(state.assumed, [:])
    }

    func test_stop_while_the_words_are_still_being_read_changes_nothing_of_the_search() {
        let before = searched()

        let state = reduce(reduce(before, .readStarted(seq: 2)), .stopped)

        XCTAssertEqual(state.spec, before.spec)
        XCTAssertEqual(state.read, before.read)
        XCTAssertEqual(state.answers, before.answers)
        XCTAssertEqual(state.phase, .results)
    }

    func test_an_edit_made_meanwhile_still_waits_after_stop_and_what_it_says_is_no_longer_assumed() {
        let before = searched()
        XCTAssertEqual(before.assumed[.place("syn-p0021")], [.mode, .strictness])
        let edit = Edits.placeStrictness("syn-p0021", .hard)
        let reading = readAgain(reduce(reduce(before, .readStarted(seq: 2)), .queued(edit)))

        let state = reduce(reading, .stopped)

        XCTAssertEqual(state.spec, before.spec)
        XCTAssertEqual(state.pending, edit)
        XCTAssertEqual(state.assumed[.place("syn-p0021")], [.mode])
        // The control that was moved keeps showing what it was set to: its edit is on its way.
        XCTAssertEqual(state.answers, reading.answers)
    }

    func test_a_second_sentence_sent_before_the_first_is_ranked_is_undone_with_it() {
        let before = searched()

        XCTAssertEqual(reduce(readAgain(readAgain(before)), .stopped).spec, before.spec)
    }

    func test_a_sentence_whose_ranking_failed_is_undone_by_stop_on_the_next_one() {
        let failed = reduce(readAgain(searched()), .failed(step: .rank, timeout))
        // The failure is on screen, with the new spec over the old ranking, and says "not updated".
        XCTAssertNotEqual(failed.specHash, failed.rankedHash)

        let state = reduce(readAgain(failed), .stopped)

        // Stop takes the failure line away, so it must not leave the two apart in silence.
        XCTAssertNil(state.failure)
        XCTAssertEqual(state.specHash, state.rankedHash)
    }

    func test_words_that_could_not_be_read_leave_nothing_to_put_back() {
        let failed = after(.readStarted(seq: 1), .failed(step: .read, timeout))
        XCTAssertNil(failed.kept)

        // The person chooses to buy, which swaps the default in. That is the search a later Stop goes back to.
        let swapped = reduce(failed, .tenureSwapped(.buy))
        let reading = [.readStarted(seq: 2), .readAnswered(read, by: a), .rankStarted(seq: 2)]
            .reduce(swapped, reduce)

        XCTAssertEqual(reduce(reading, .stopped).spec, meta.defaults.buy)
    }

    func test_once_the_ranking_is_in_there_is_nothing_to_put_back() {
        let again = Answers.ranked("rank-second-sentence")
        let done = reduce(readAgain(searched()), .rankAnswered(again, sent: .none, by: a))

        let state = reduce(done, .stopped)

        XCTAssertEqual(state.spec, again.spec)
        XCTAssertNil(state.kept)
    }

    func test_what_is_kept_for_stop_holds_nothing_a_person_typed() {
        let fields = Mirror(reflecting: readAgain(searched()).kept as Any).children.first
            .map { Mirror(reflecting: $0.value).children.compactMap(\.label) }

        // The names of the places are the release's own, from the answer that brought the spec.
        XCTAssertEqual(
            fields,
            [
                "spec", "specHash", "untouched", "read", "refused", "assumed", "placeNames", "gaveWay",
                "degraded",
            ])
    }

    // MARK: - What a control is drawn from while an edit waits

    func test_a_reading_that_comes_while_an_edit_waits_does_not_take_the_control_back() {
        let edit = Edits.tagWeight(.leafy, 0.7)
        let waiting = after(.readStarted(seq: 1), .queued(edit))

        let state = reduce(waiting, .readAnswered(read, by: a))

        // The count of answers is what a control holds its own value against. The edit has
        // not been answered, so the count stands, and the control shows what it was set to.
        XCTAssertEqual(state.answers, waiting.answers)
        XCTAssertEqual(state.read?.at, state.answers)
        XCTAssertEqual(reduce(state, .rankAnswered(ranked, sent: edit, by: a)).answers, waiting.answers + 1)
    }

    func test_the_answers_are_counted_so_that_a_control_knows_to_draw_itself_again() {
        let counts = [
            opened(),
            after(.readAnswered(read, by: a)),
            after(.readAnswered(read, by: a), .rankAnswered(ranked, sent: .none, by: a)),
            after(.tenureSwapped(.buy)),
            after(.queued(Edits.tagOn(.leafy))),
            after(.failed(step: .rank, timeout)),
        ].map(\.answers)

        XCTAssertEqual(counts, [0, 1, 2, 1, 0, 0])
    }
}
