import XCTest

@testable import BurroKit

/// What a person types, and the places they name, reach nothing but the body
/// of the one request each is for.
///
/// Each test plants a canary, a string found nowhere else, in the sentence, in
/// the place search and in the name of a place a stand-in answer gives. It
/// then runs a whole search: it reads, asks, ranks, refines, fails and goes
/// offline. A test that fails must not print what was typed, so each asserts
/// on a truth value.
final class SearchPrivacyTests: XCTestCase {
    private let typed = "zqxsentence8842"
    private let looked = "zqxplace3391"
    private let named = "Zqxname7706"

    /// A place search whose first place has a name found nowhere else.
    private var places: StandIn.Responder {
        let named = named
        return .made { _ in
            try Recorded.read("places-search").with(data: { data in
                data["places"] = data["places"]?.each { $0["name"] = .string(named) }
            })
        }
    }

    /// One person's whole visit: every state a search can be in.
    @MainActor
    private func visit(_ search: OpenSearch) async throws {
        let api = search.api
        // Reads, and asks which place was meant.
        api.on(.interpret, "interpret-clarify").on(.rank, StandIn.withTheSpecSent("rank-first"))
        await search.flow.submitText("Leafy, 30 minutes to \(typed)")
        // Looks for the place, and picks one.
        api.on(.searchPlaces, places)
        let found = try await search.flow.searchPlaces(looked).get().data.places
        let picked = try XCTUnwrap(found.first)
        if let question = search.state.questions.first {
            await search.flow.answerClarify(question, id: picked.placeId, name: picked.name)
        }
        await search.flow.addPlace(try XCTUnwrap(found.last))
        // Refines with a control, and with a second sentence.
        await search.flow.applyEdits(Edits.placeMinutes(picked.placeId, 25))
        api.on(.interpret, "interpret-second-sentence")
        await search.flow.submitText("a bit more \(typed)")
        // A refusal of the words, a fault, a reading that could not leave.
        api.on(.interpret, "interpret-invalid-text")
        await search.flow.submitText(typed)
        api.on(.rank, "error-internal")
        await search.flow.applyEdits(Edits.tagOn(.pace))
        await search.flow.retry(text: typed)
        api.unreachable(.interpret, .notConnectedToInternet)
        await search.flow.submitText("offline \(typed)")
        api.unreachable(.rank, .notConnectedToInternet)
        await search.flow.wentOnline()
        await search.flow.applyEdits(Edits.tagOff(.pace))
        api.on(.rank, StandIn.withTheSpecSent("rank-first"))
        await search.flow.wentOnline()
        await search.flow.stop()
    }

    private func holds(_ data: Data?, _ canary: String) -> Bool {
        data.map { String(decoding: $0, as: UTF8.self).contains(canary) } ?? false
    }

    @MainActor
    func test_the_visit_passes_through_every_kind_of_call() async throws {
        let search = OpenSearch()

        try await visit(search)

        XCTAssertGreaterThanOrEqual(search.api.calls(to: .interpret).count, 4)
        XCTAssertGreaterThanOrEqual(search.api.calls(to: .rank).count, 5)
        XCTAssertEqual(search.api.calls(to: .searchPlaces).count, 1)
        XCTAssertEqual(search.api.unexpected.count, 0)
    }

    @MainActor
    func test_typed_text_travels_only_in_a_post_body() async throws {
        let search = OpenSearch()

        try await visit(search)

        let carrying = search.api.calls.filter { holds($0.sent, typed) }
        XCTAssertFalse(carrying.isEmpty)
        XCTAssertTrue(carrying.allSatisfy { $0.route == .interpret && $0.method == "POST" })
        let looking = search.api.calls.filter { holds($0.sent, looked) }
        XCTAssertEqual(looking.count, 1)
        XCTAssertTrue(looking.allSatisfy { $0.route == .searchPlaces && $0.method == "POST" })
    }

    @MainActor
    func test_typed_text_never_reaches_an_address_or_a_header() async throws {
        let search = OpenSearch()

        try await visit(search)

        for canary in [typed, looked, named] {
            XCTAssertFalse(search.api.calls.contains { $0.outsideTheBody.contains(canary) })
        }
    }

    @MainActor
    func test_a_place_name_is_never_sent_anywhere() async throws {
        let search = OpenSearch()

        try await visit(search)

        // A place is sent by its id. Its name is for the person to read.
        XCTAssertFalse(search.api.calls.contains { holds($0.sent, named) })
        XCTAssertTrue(search.state.placeNames.values.contains(named))
    }

    @MainActor
    func test_a_place_id_is_only_ever_in_a_post_body() async throws {
        let search = OpenSearch()

        try await visit(search)

        let ids = Set(search.state.placeNames.keys)
        XCTAssertFalse(ids.isEmpty)
        for id in ids {
            XCTAssertFalse(search.api.calls.contains { $0.outsideTheBody.contains(id) })
        }
    }

    @MainActor
    func test_the_search_and_the_screen_hold_no_sentence() async throws {
        let search = OpenSearch()

        try await visit(search)

        for canary in [typed, looked] {
            XCTAssertFalse(String(reflecting: search.state).contains(canary))
            XCTAssertFalse(String(reflecting: search.shown()).contains(canary))
            XCTAssertFalse(String(reflecting: SearchChips.of(search.state)).contains(canary))
        }
    }

    @MainActor
    func test_the_place_search_keeps_the_places_and_nothing_that_was_typed() async {
        let api = StandIn.firstSearch().on(.searchPlaces, places)
        let search = OpenSearch(api)
        let model = PlaceSearch(wait: 0) { await search.flow.searchPlaces($0) }

        model.typed(looked)
        await model.settled()

        XCTAssertEqual(model.options.count, 3)
        XCTAssertEqual(model.status, .found(3))
        let held = Mirror(reflecting: model).children.map { String(reflecting: $0.value) }.joined()
        XCTAssertFalse(held.contains(looked))
        XCTAssertFalse(String(reflecting: model.options).contains(looked))
    }

    @MainActor
    func test_nothing_typed_is_ever_written_to_the_phone() async throws {
        let storage = MemoryPhoneStorage()
        let api = StandIn.firstSearch()
        let notice = SyntheticNotice()
        let app = AppModel(
            api: api.api(), site: SiteAddress("https://burro.example.test"), synthetic: notice,
            storage: storage)
        await app.open()
        app.consent.choose(.allowed)
        let store = try XCTUnwrap(app.search)

        api.on(.interpret, "interpret-first")
        await store.flow.submitText("leafy \(typed)")
        api.on(.searchPlaces, places)
        let found = try await store.flow.searchPlaces(looked).get().data.places
        await store.flow.addPlace(try XCTUnwrap(found.first))
        app.toggleShortlist(AreaRef(Answers.areas[5]))
        app.consent.choose(.settingsOnly)

        for file in KeptFile.allCases {
            let kept = storage.read(file)
            for canary in [typed, looked, named] + Array(store.state.placeNames.keys) {
                XCTAssertFalse(holds(kept, canary))
            }
        }
        XCTAssertTrue(holds(storage.read(.consent), "settingsOnly"))
    }

    @MainActor
    func test_no_sentence_is_sent_until_the_person_has_agreed_and_none_after_they_take_it_back() async throws {
        let api = StandIn.firstSearch()
        let app = AppModel(
            api: api.api(), site: .none, synthetic: SyntheticNotice(), storage: MemoryPhoneStorage())
        await app.open()
        let store = try XCTUnwrap(app.search)

        await store.flow.submitText(typed)
        XCTAssertEqual(api.calls(to: .interpret).count, 0)
        XCTAssertEqual(SearchScreen.shown(store.state, consent: app.consent.choice).box, .declined)

        app.consent.choose(.allowed)
        await store.flow.submitText(typed)
        XCTAssertEqual(api.calls(to: .interpret).count, 1)
        XCTAssertEqual(SearchScreen.shown(store.state, consent: app.consent.choice).box, .offered)

        app.consent.choose(.settingsOnly)
        await store.flow.submitText(typed)
        XCTAssertEqual(api.calls(to: .interpret).count, 1)
        XCTAssertEqual(SearchScreen.shown(store.state, consent: app.consent.choice).box, .declined)
    }

    func test_the_words_a_failure_is_said_in_are_fixed_and_hold_nothing_that_was_sent() {
        for scenario in ["interpret-invalid-text", "error-internal", "rank-stale-spec", "not-found"] {
            let failure = Answers.failure(scenario)
            let sent = (try? Recorded.read(scenario).sent).flatMap { $0 }
            let words = SearchScreen.words(for: failure)

            XCTAssertFalse(words.isEmpty)
            if let text = sent.flatMap({ try? JSON.read($0) })?["text"]?.string, !text.isEmpty {
                XCTAssertFalse(words.contains(text))
            }
        }
        for kind in ClientFailureKind.allCases {
            XCTAssertFalse(SearchScreen.words(for: .because(kind)).isEmpty)
        }
    }

    // MARK: - Read off the source

    func test_no_screen_of_these_features_keeps_copies_or_offers_what_was_typed() throws {
        let banned = [
            "UserDefaults", "@AppStorage", "@SceneStorage", "UIPasteboard", "NSPasteboard", "PasteButton",
            "ShareLink(", "NSUserActivity", "userActivity(", "searchable(", "CSSearchable", "print(",
            "Logger(", "FileManager", ".write(to:", "draggable(", "onDrag(", "Transferable",
        ]
        for file in try Written.files() {
            for word in banned {
                XCTAssertFalse(file.text.contains(word), "\(file.name) uses \(word)")
            }
        }
    }

    func test_the_app_builds_edits_and_never_a_spec_or_a_state() throws {
        let making = ["PreferenceSpec(", "SearchState(", ".dispatch(", "reduce(", "Budget(", "Commute("]
        for file in try Written.files() {
            for word in making {
                XCTAssertFalse(file.text.contains(word), "\(file.name) makes \(word)")
            }
        }
    }

    func test_every_edit_a_control_sends_is_built_in_one_place() throws {
        let sending = try Written.files().flatMap { file in
            file.text.components(separatedBy: "context.send(").dropFirst().map { (file.name, $0) }
        }

        XCTAssertGreaterThan(sending.count, 15)
        for (name, after) in sending {
            let first = after.drop { $0.isWhitespace }
            let built = ["Edits.", "SettingsForm.", "removal)"].contains { first.hasPrefix($0) }
            XCTAssertTrue(built, "\(name) sends what it built itself")
        }
    }

    func test_words_from_the_api_are_never_read_as_a_key_or_as_markup() throws {
        // `Text("...")` with words written in place looks its words up, and reads
        // marks in them as markup. Every word drawn is a value, or is drawn verbatim.
        for file in try Written.files() {
            XCTAssertFalse(file.text.contains("Text(\""), file.name)
            XCTAssertFalse(file.text.contains("Button(\""), file.name)
            XCTAssertFalse(file.text.contains("Label(\""), file.name)
            XCTAssertFalse(file.text.contains("LocalizedStringKey"), file.name)
            XCTAssertFalse(file.text.contains("AttributedString(markdown"), file.name)
        }
    }

    func test_an_example_fills_the_box_and_there_is_nothing_in_it_to_send_it() throws {
        let box = try Repository.text(Written.search.appendingPathComponent("PromptBox.swift"))
        let list = try XCTUnwrap(box.range(of: "struct ExampleList"))
        let end = try XCTUnwrap(box.range(of: "struct DeclinedLine"))
        let examples = String(box[list.lowerBound..<end.lowerBound])

        XCTAssertTrue(examples.contains("use(sentence)"))
        for word in ["onSubmit", "submitText", "flow", "Task"] {
            XCTAssertFalse(examples.contains(word), word)
        }
    }
}
