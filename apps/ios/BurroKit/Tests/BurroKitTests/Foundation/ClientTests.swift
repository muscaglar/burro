import XCTest

@testable import BurroKit

/// The client: what it sends, where, and what it makes of each kind of answer.
final class ClientTests: XCTestCase {
    // A string found nowhere else, planted in what a person types.
    private let canary = "zqxcanary7431"
    private var spec: PreferenceSpec { Answers.meta.defaults.rent }

    // MARK: - What is sent

    func test_typed_text_travels_only_in_a_post_body() async throws {
        let standIn = StandIn.firstSearch().on(.searchPlaces, "places-search")
        let api = standIn.api()

        _ = await api.interpret(InterpretBody(text: "somewhere \(canary)", spec: spec))
        _ = await api.searchPlaces(PlaceSearchBody(q: canary))

        XCTAssertEqual(standIn.calls.count, 2)
        for call in standIn.calls {
            XCTAssertEqual(call.method, "POST")
            XCTAssertFalse(call.outsideTheBody.contains(canary))
            XCTAssertTrue(String(decoding: call.sent ?? Data(), as: UTF8.self).contains(canary))
        }
    }

    func test_a_post_carries_json_and_a_get_carries_nothing() async throws {
        let standIn = StandIn.firstSearch()
        let api = standIn.api()

        _ = await api.rank(RankBody(spec: spec))
        _ = await api.getMeta()

        let post = try standIn.lastCall(to: .rank)
        XCTAssertEqual(post.headers["Content-Type"], "application/json")
        XCTAssertEqual(post.headers["Accept"], "application/json")
        XCTAssertEqual(try post.body(as: RankBody.self), RankBody(spec: spec, limit: 20))
        let get = try standIn.lastCall(to: .getMeta)
        XCTAssertEqual(get.method, "GET")
        XCTAssertNil(get.sent)
        XCTAssertNil(get.headers["Content-Type"])
    }

    func test_no_call_carries_a_cookie_or_says_who_is_asking() async throws {
        let standIn = StandIn.firstSearch()

        _ = await standIn.api().rank(RankBody(spec: spec))

        let sent = try standIn.lastCall(to: .rank).headers.keys.map { $0.lowercased() }.sorted()
        XCTAssertEqual(sent, ["accept", "content-type"])
    }

    func test_the_address_of_a_call_is_the_base_and_the_route_and_no_more() async throws {
        let standIn = StandIn.firstSearch().on(.getShare, "share-opened")
        let api = standIn.api()

        _ = await api.rank(RankBody(spec: spec))
        _ = await api.getArea("farrowmere")
        _ = await api.getShare("3TQkoOxY0dYBEVyMymzDjg")
        _ = await api.getGeometry()

        XCTAssertEqual(
            standIn.calls.map(\.url.absoluteString),
            [
                "https://api.example.test/v1/rank",
                "https://api.example.test/v1/areas/farrowmere",
                "https://api.example.test/v1/shares/3TQkoOxY0dYBEVyMymzDjg",
                "https://api.example.test/v1/areas/geometry",
            ])
        XCTAssertEqual(standIn.unexpected.count, 0)
    }

    func test_what_fills_a_path_cannot_climb_out_of_its_route() {
        XCTAssertEqual(LiveBurroAPI.path(of: .getArea, parameter: "../meta"), "/v1/areas/..%2Fmeta")
        XCTAssertEqual(LiveBurroAPI.path(of: .getArea, parameter: "a?b=c#d"), "/v1/areas/a%3Fb%3Dc%23d")
        XCTAssertEqual(LiveBurroAPI.path(of: .getShare, parameter: "Ab_-9"), "/v1/shares/Ab_-9")
        XCTAssertNil(LiveBurroAPI.path(of: .getArea, parameter: nil))
        XCTAssertNil(LiveBurroAPI.path(of: .getArea, parameter: ""))
        XCTAssertEqual(LiveBurroAPI.path(of: .rank, parameter: nil), "/v1/rank")
    }

    func test_with_no_address_set_nothing_is_sent() async {
        let standIn = StandIn.firstSearch()
        let api = LiveBurroAPI(configuration: .none, transport: standIn)

        let answer = await api.interpret(InterpretBody(text: canary, spec: spec))

        XCTAssertEqual(answer.failure?.kind, .notConfigured)
        XCTAssertEqual(standIn.calls.count, 0)
    }

    // MARK: - What comes back

    func test_every_route_answers_with_the_data_the_contract_gives_it() async throws {
        let standIn = StandIn.firstSearch()
            .on(.compare, "compare-three")
            .on(.searchPlaces, "places-search")
            .on(.createShare, "share-made")
            .on(.getShare, "share-opened")
            .on(.getCensus, "census")
            .on(.getIncome, "income")
        let api = standIn.api()

        let interpret = await api.interpret(InterpretBody(text: "leafy", spec: spec))
        let rank = await api.rank(RankBody(spec: spec))
        let explain = await api.explainTop(ExplanationsBody(spec: spec, limit: 5))
        let compare = await api.compare(CompareBody(areaIds: ["syn-n0006", "syn-n0017"], spec: spec))
        let places = await api.searchPlaces(PlaceSearchBody(q: "pel"))
        let made = await api.createShare(ShareBody(spec: spec))
        let share = await api.getShare("3TQkoOxY0dYBEVyMymzDjg")
        let areas = await api.listAreas()
        let geometry = await api.getGeometry()
        let area = await api.getArea("farrowmere")
        let census = await api.getCensus("foxholt")
        let income = await api.getIncome("foxholt")
        let meta = await api.getMeta()
        let health = await api.healthz()

        XCTAssertEqual(try interpret.get().data, Answers.read("interpret-first"))
        XCTAssertEqual(try rank.get().data, Answers.ranked("rank-first"))
        XCTAssertEqual(try explain.get().data, Answers.explained("explanations-first"))
        XCTAssertEqual(try compare.get().data.areas.count, 3)
        XCTAssertEqual(try places.get().data.places.first?.placeId, "syn-p0012")
        XCTAssertEqual(try made.get().data.shareId, "3TQkoOxY0dYBEVyMymzDjg")
        XCTAssertEqual(try share.get().data, Answers.shared("share-opened"))
        XCTAssertEqual(try areas.get().data.areas, Answers.areas)
        XCTAssertEqual(try geometry.get().data, Answers.geometry)
        XCTAssertEqual(try area.get().data, Answers.profile("farrowmere"))
        XCTAssertEqual(try census.get().data, try Recorded.data(.getCensus, "census", as: CensusPanel.self))
        XCTAssertEqual(try income.get().data, try Recorded.data(.getIncome, "income", as: IncomeShown.self))
        XCTAssertEqual(try meta.get().data, Answers.meta)
        XCTAssertEqual(try health.get(), Health(ok: true))
        XCTAssertEqual(Set(standIn.routes), Set(APIRoute.allCases))
        XCTAssertEqual(standIn.unexpected.count, 0)
    }

    func test_an_answer_carries_its_meta_its_status_and_the_id_to_quote() async throws {
        let standIn = StandIn.firstSearch()

        let answer = try await standIn.api().rank(RankBody(spec: spec)).get()

        let recorded = try Recorded.read("rank-first")
        XCTAssertEqual(answer.status, 200)
        XCTAssertEqual(answer.meta.releaseId, "syn-2026-09-23-01")
        XCTAssertTrue(answer.synthetic)
        XCTAssertFalse(answer.preview)
        XCTAssertEqual(answer.requestId, recorded.headers["x-request-id"])
        XCTAssertNotNil(answer.requestId)
    }

    func test_the_banner_is_told_of_every_answer_before_the_answer_is_handed_over() async throws {
        let standIn = StandIn.firstSearch().on(.getShare, "share-gone")
        let api = standIn.api()

        _ = await api.rank(RankBody(spec: spec))
        XCTAssertEqual(standIn.synthetic, [true])
        XCTAssertEqual(standIn.preview, [false])
        _ = await api.getShare("a9yIlz7uQ1b3F4vDySSZRg")
        XCTAssertEqual(standIn.synthetic, [true, true])
        XCTAssertEqual(standIn.preview, [false, false])
    }

    func test_the_release_counts_as_a_preview_when_either_the_body_or_the_header_says_so() async throws {
        let finished = try Recorded.read("rank-first")
        func answered(body: Bool, header: String?) async throws -> (Bool, [Bool]) {
            var headers = finished.headers
            headers["x-burro-preview"] = header
            let sent = try finished.with(meta: { $0["preview"] = .bool(body) }).with(headers: headers)
            let standIn = StandIn().on(.rank, .made { _ in sent })
            let answer = try await standIn.api().rank(RankBody(spec: spec)).get()
            return (answer.preview, standIn.preview)
        }

        let byBody = try await answered(body: true, header: "false")
        let byHeader = try await answered(body: false, header: "true")
        let byNeither = try await answered(body: false, header: "false")
        let bySilence = try await answered(body: false, header: nil)
        let recorded = try await StandIn().on(.rank, "preview/rank-plain").api().rank(RankBody(spec: spec)).get()

        // A preview is never shown as finished: either saying so is enough.
        XCTAssertEqual(byBody.0, true)
        XCTAssertEqual(byHeader.0, true)
        XCTAssertEqual(byNeither.0, false)
        XCTAssertEqual(bySilence.0, false)
        // The banner is told what the answer counts as, before the answer is handed over.
        XCTAssertEqual([byBody.1, byHeader.1, byNeither.1, bySilence.1], [[true], [true], [false], [false]])
        XCTAssertTrue(recorded.preview)
        XCTAssertTrue(recorded.meta.preview)
    }

    func test_the_data_counts_as_made_up_when_either_the_body_or_the_header_says_so() async throws {
        let real = try Recorded.read("rank-first").with(meta: { $0["synthetic"] = .bool(false) })
        func answered(header: String?) async throws -> Bool {
            var headers = real.headers
            headers["x-burro-synthetic"] = header
            let sent = real.with(headers: headers)
            let standIn = StandIn().on(.rank, .made { _ in sent })
            return try await standIn.api().rank(RankBody(spec: spec)).get().synthetic
        }

        let byHeader = try await answered(header: "true")
        let byNeither = try await answered(header: "false")
        let bySilence = try await answered(header: nil)

        XCTAssertTrue(byHeader)
        XCTAssertFalse(byNeither)
        XCTAssertFalse(bySilence)
        XCTAssertEqual(LiveBurroAPI.flag("true"), true)
        XCTAssertEqual(LiveBurroAPI.flag("false"), false)
        XCTAssertNil(LiveBurroAPI.flag("yes"))
        XCTAssertNil(LiveBurroAPI.flag(nil))
    }

    func test_an_error_comes_back_as_the_apis_own_code_words_and_paths() async throws {
        let standIn = StandIn()
            .on(.interpret, "interpret-invalid-text")
            .on(.rank, "rank-stale-spec")
            .on(.getShare, "share-gone")
            .on(.explainTop, "error-internal")
        let api = standIn.api()

        let text = await api.interpret(InterpretBody(text: canary, spec: spec))
        let stale = await api.rank(RankBody(spec: spec))
        let gone = await api.getShare("a9yIlz7uQ1b3F4vDySSZRg")
        let fault = await api.explainTop(ExplanationsBody(spec: spec))

        let refusal = try XCTUnwrap(text.failure?.api)
        XCTAssertEqual(refusal.status, 422)
        XCTAssertEqual(refusal.code, .invalidText)
        XCTAssertEqual(refusal.message, "The text must be 1 to 600 characters.")
        XCTAssertEqual(refusal.fields, [FieldProblem(path: "text", problem: .outOfRange)])
        XCTAssertTrue(refusal.synthetic)
        XCTAssertTrue(text.hasCode(.invalidText))
        XCTAssertEqual(stale.failure?.code, .unknownPlace)
        XCTAssertEqual(stale.failure?.api?.fields.map(\.path), ["spec.commutes[1].place_id"])
        XCTAssertEqual(gone.failure?.status, 410)
        XCTAssertEqual(gone.failure?.code, .releaseChanged)
        XCTAssertEqual(fault.failure?.status, 500)
        XCTAssertNotNil(fault.failure?.requestId)
        // A failure never holds what was sent.
        XCTAssertFalse(String(describing: text.failure).contains(canary))
    }

    func test_an_answer_that_is_not_the_apis_envelope_is_unreadable() async throws {
        let recorded = try Recorded.read("rank-first")
        let shapes: [Recorded] = [
            recorded.with(body: Data("<html>Bad gateway</html>".utf8), status: 502),
            recorded.with(body: Data(#"{"data": {}}"#.utf8)),
            try recorded.with(data: { $0["ranked"] = nil }),
            try recorded.with(data: { $0["scores"] = .string("many") }),
            // An answer that does not say whether its release is a preview is not the API's.
            try recorded.with(meta: { $0["preview"] = nil }),
            recorded.with(status: 302),
            recorded.with(body: Data()),
        ]

        for shape in shapes {
            let standIn = StandIn().on(.rank, .made { _ in shape })
            let answer = await standIn.api().rank(RankBody(spec: spec))
            XCTAssertEqual(answer.failure?.kind, .unreadable)
            XCTAssertEqual(answer.failure?.status, shape.status)
        }
    }

    func test_an_unreadable_answer_still_tells_the_banner_what_its_header_said() async throws {
        let broken = try Recorded.read("rank-first").with(body: Data("not json".utf8))
        let standIn = StandIn().on(.rank, .made { _ in broken })

        let answer = await standIn.api().rank(RankBody(spec: spec))

        XCTAssertEqual(answer.failure, .client(ClientFailure(
            .unreadable, status: 200, synthetic: true, preview: false,
            requestId: broken.headers["x-request-id"])))
        XCTAssertEqual(standIn.synthetic, [true])
        XCTAssertEqual(standIn.preview, [false])
    }

    // MARK: - What goes wrong on the way

    func test_a_call_that_takes_too_long_is_given_up_on() async {
        let standIn = StandIn().silent(.rank)
        let api = standIn.api(timeouts: Timeouts(search: .milliseconds(30)))

        let answer = await api.rank(RankBody(spec: spec))

        XCTAssertEqual(answer.failure?.kind, .timeout)
    }

    func test_each_route_waits_as_long_as_the_website_does() {
        let timeouts = Timeouts()

        XCTAssertEqual(timeouts.of(.interpret), .seconds(8))
        XCTAssertEqual(timeouts.of(.searchPlaces), .seconds(3))
        for route in [APIRoute.rank, .explainTop, .compare, .createShare, .getShare] {
            XCTAssertEqual(timeouts.of(route), .seconds(5))
        }
        for route in [APIRoute.listAreas, .getGeometry, .getArea, .getMeta] {
            XCTAssertEqual(timeouts.of(route), .seconds(10))
        }
    }

    func test_a_call_that_is_stopped_says_so_and_reports_nothing_else() async {
        let standIn = StandIn().silent(.rank)
        let api = standIn.api()
        let spec = self.spec

        let call = Task { await api.rank(RankBody(spec: spec)) }
        while standIn.calls.isEmpty { try? await Task.sleep(nanoseconds: 1_000_000) }
        call.cancel()
        let answer = await call.value

        XCTAssertEqual(answer.failure?.kind, .aborted)
    }

    func test_a_call_that_was_stopped_before_it_began_is_never_sent() async {
        let standIn = StandIn.firstSearch()
        let api = standIn.api()
        let spec = self.spec

        let call = Task {
            withUnsafeCurrentTask { $0?.cancel() }
            return await api.rank(RankBody(spec: spec))
        }
        let answer = await call.value

        XCTAssertEqual(answer.failure?.kind, .aborted)
        XCTAssertEqual(standIn.calls.count, 0)
    }

    func test_a_phone_with_no_connection_is_offline_and_any_other_fault_is_the_network() async {
        func kind(of code: URLError.Code) async -> ClientFailureKind? {
            await StandIn().unreachable(.rank, code).api().rank(RankBody(spec: spec)).failure?.kind
        }

        let none = await kind(of: .notConnectedToInternet)
        let barred = await kind(of: .dataNotAllowed)
        let refused = await kind(of: .cannotConnectToHost)
        let lost = await kind(of: .networkConnectionLost)
        let slow = await kind(of: .timedOut)
        let unsafe = await kind(of: .appTransportSecurityRequiresSecureConnection)

        XCTAssertEqual(none, .offline)
        XCTAssertEqual(barred, .offline)
        XCTAssertEqual(refused, .network)
        XCTAssertEqual(lost, .network)
        XCTAssertEqual(slow, .timeout)
        XCTAssertEqual(unsafe, .network)
    }

    func test_the_answer_that_says_the_service_is_up_has_no_meta() async throws {
        let standIn = StandIn()

        let up = await standIn.api().healthz()
        let down = await StandIn().unreachable(.healthz).api().healthz()

        XCTAssertEqual(try up.get(), Health(ok: true))
        XCTAssertEqual(down.failure?.kind, .network)
        XCTAssertEqual(try standIn.lastCall(to: .healthz).path, "/healthz")
    }

    func test_the_session_the_app_uses_keeps_nothing_on_the_phone() {
        let configuration = URLSessionTransport.configuration()

        XCTAssertNil(configuration.urlCache)
        XCTAssertNil(configuration.httpCookieStorage)
        XCTAssertNil(configuration.urlCredentialStorage)
        XCTAssertFalse(configuration.httpShouldSetCookies)
        XCTAssertEqual(configuration.httpCookieAcceptPolicy, .never)
        XCTAssertEqual(configuration.requestCachePolicy, .reloadIgnoringLocalCacheData)
    }
}
