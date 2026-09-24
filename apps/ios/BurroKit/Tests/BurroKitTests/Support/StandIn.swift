import Foundation
import XCTest

@testable import BurroKit

/// A stand-in for the API, for a test to run a whole search against.
///
/// It stands where the network would: the real client is in front of it, so
/// every request is built and every answer is read by the code the app runs.
/// It answers from the recorded answers, and keeps every request it was sent,
/// so that a test can say what left the app and where it went. Nothing here
/// reaches a network.
final class StandIn: Transport, @unchecked Sendable {
    static let base = "https://api.example.test"

    /// One request, as it was sent.
    struct Call: Sendable {
        let route: APIRoute?
        let method: String
        let url: URL
        let path: String
        let headers: [String: String]
        /// The body as it was sent. `nil` for a `GET`.
        let sent: Data?

        /// The body, read as JSON.
        var body: JSON? {
            sent.flatMap { try? JSON.read($0) }
        }

        /// The body, read as the record the contract gives the route.
        func body<Body: Decodable>(as type: Body.Type) throws -> Body {
            try JSONDecoder().decode(type, from: sent ?? Data())
        }

        /// Everything of the request that is not its body: the address and the headers.
        var outsideTheBody: String {
            ([method, url.absoluteString] + headers.map { "\($0.key): \($0.value)" }).joined(separator: "\n")
        }
    }

    /// What a route answers with.
    enum Responder: Sendable {
        /// A recording, by its name.
        case recorded(String)
        /// Whatever a function makes of the call.
        case made(@Sendable (Call) async throws -> Recorded)
        /// A request that could not leave.
        case fails(URLError.Code)
        /// No answer at all, until the call is stopped.
        case silent
        /// The profile of whichever area is asked for.
        case profiles
    }

    /// Holds an answer back until it is let go.
    final class Gate: @unchecked Sendable {
        private let lock = NSLock()
        private var open = false
        private var count = 0

        /// Lets the answer that was held go.
        func release() {
            lock.withLock { open = true }
        }

        /// How many calls are waiting on it.
        var waiting: Int {
            lock.withLock { count }
        }

        fileprivate func wait() async throws {
            try await hold()
        }

        /// Waits until it is let go, for a responder a test makes itself.
        func hold() async throws {
            lock.withLock { count += 1 }
            defer { lock.withLock { count -= 1 } }
            while !lock.withLock({ open }) {
                try await Task.sleep(nanoseconds: 1_000_000)
            }
        }
    }

    private let lock = NSLock()
    private var responders: [APIRoute: [Responder]] = [
        // What is served with nothing set: the routes that are a function of the release alone.
        .getMeta: [.recorded("meta")],
        .listAreas: [.recorded("areas")],
        .getGeometry: [.recorded("geometry")],
        .getArea: [.profiles],
        .healthz: [.recorded("healthz")],
    ]
    private var made: [Call] = []
    private var unanswered: [Call] = []
    private var toldSynthetic: [Bool] = []
    private var toldPreview: [Bool] = []
    private var release: String?

    /// A first search, as it was recorded.
    static func firstSearch() -> StandIn {
        StandIn()
            .on(.interpret, "interpret-first")
            .on(.rank, "rank-first")
            .on(.explainTop, "explanations-first")
    }

    // MARK: - Setting what is answered

    /// Sets how a route answers from now on.
    @discardableResult
    func on(_ route: APIRoute, _ scenario: String) -> StandIn {
        on(route, .recorded(scenario))
    }

    @discardableResult
    func on(_ route: APIRoute, _ responder: Responder) -> StandIn {
        lock.withLock { responders[route] = [responder] }
        return self
    }

    /// Sets the answers of a route's next calls, in order. The last one stays.
    @discardableResult
    func inTurn(_ route: APIRoute, _ scenarios: String...) -> StandIn {
        lock.withLock { responders[route] = scenarios.map { .recorded($0) } }
        return self
    }

    @discardableResult
    func inTurn(_ route: APIRoute, _ inOrder: [Responder]) -> StandIn {
        lock.withLock { responders[route] = inOrder }
        return self
    }

    /// From now on every recording is answered as a service holding this release answers
    /// it: a service names the release it holds in every answer, whatever the route.
    @discardableResult
    func movedTo(_ release: String) -> StandIn {
        lock.withLock { self.release = release }
        return self
    }

    /// A recording, as a service holding another release answers it.
    static func on(release: String, _ scenario: String) -> Responder {
        .made { _ in try Recorded.read(scenario).with(meta: { $0["release_id"] = .string(release) }) }
    }

    /// Forgets the calls that were made, so that a test counts only those made from here on.
    func forgetCalls() {
        lock.withLock { made = [] }
    }

    /// Makes a route wait until it is released, then answer.
    func hold(_ route: APIRoute, _ scenario: String) -> Gate {
        let gate = Gate()
        on(
            route,
            .made { _ in
                try await gate.wait()
                return try Recorded.read(scenario)
            })
        return gate
    }

    /// Makes a route fail as a request that could not leave.
    @discardableResult
    func unreachable(_ route: APIRoute, _ code: URLError.Code = .cannotConnectToHost) -> StandIn {
        on(route, .fails(code))
    }

    /// Makes a route never answer, until it is stopped.
    @discardableResult
    func silent(_ route: APIRoute) -> StandIn {
        on(route, .silent)
    }

    /// Answers as a recording does, but with the spec that was sent, as the API
    /// does when it is sent no edit. It is for a test whose recorded sentence and
    /// recorded ranking are of two different searches.
    static func withTheSpecSent(_ scenario: String) -> Responder {
        .made { call in
            let recorded = try Recorded.read(scenario)
            guard let spec = call.body?["spec"] else { return recorded }
            return try recorded.with(data: { $0["spec"] = spec })
        }
    }

    // MARK: - What was sent

    var calls: [Call] { lock.withLock { made } }
    /// Calls that no answer was set for. A test expects none.
    var unexpected: [Call] { lock.withLock { unanswered } }
    /// What the client told the banner, answer by answer.
    var synthetic: [Bool] { lock.withLock { toldSynthetic } }
    /// What the client told the banner of a preview, answer by answer.
    var preview: [Bool] { lock.withLock { toldPreview } }

    func calls(to route: APIRoute) -> [Call] {
        calls.filter { $0.route == route }
    }

    func lastCall(to route: APIRoute, file: StaticString = #filePath, line: UInt = #line) throws -> Call {
        try XCTUnwrap(calls(to: route).last, "No call was made to \(route.rawValue).", file: file, line: line)
    }

    /// The routes that were called, in the order they were.
    var routes: [APIRoute] { calls.compactMap(\.route) }

    // MARK: - The client in front of it

    /// The real client, with this where the network would be.
    func api(timeouts: Timeouts = Timeouts()) -> LiveBurroAPI {
        LiveBurroAPI(
            configuration: APIConfiguration(Self.base),
            transport: self,
            timeouts: timeouts,
            onSynthetic: { [weak self] said in
                self?.lock.withLock { self?.toldSynthetic.append(said) }
            },
            onPreview: { [weak self] said in
                self?.lock.withLock { self?.toldPreview.append(said) }
            }
        )
    }

    // MARK: - Transport

    func send(_ request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        guard let url = request.url else { throw URLError(.badURL) }
        let method = request.httpMethod ?? "GET"
        let call = Call(
            route: Self.route(method: method, path: url.path),
            method: method,
            url: url,
            path: url.path,
            headers: request.allHTTPHeaderFields ?? [:],
            sent: request.httpBody
        )
        let responder: Responder? = lock.withLock {
            made.append(call)
            guard let route = call.route, var queue = responders[route], !queue.isEmpty else {
                unanswered.append(call)
                return nil
            }
            let next = queue.count > 1 ? queue.removeFirst() : queue[0]
            responders[route] = queue
            return next
        }
        guard let responder else { throw URLError(.unsupportedURL) }
        try Task.checkCancellation()

        var recorded: Recorded
        switch responder {
        case .recorded(let scenario):
            recorded = try Recorded.read(scenario)
        case .made(let make):
            recorded = try await make(call)
        case .fails(let code):
            throw URLError(code)
        case .silent:
            try await Task.sleep(nanoseconds: 3_600_000_000_000)
            throw URLError(.timedOut)
        case .profiles:
            recorded = try Recorded.read("area/\(call.path.split(separator: "/").last ?? "")")
        }
        if let release = lock.withLock({ self.release }) {
            recorded = Self.asTheReleaseNow(recorded, release, of: call.route)
        }
        try Task.checkCancellation()
        guard
            let response = HTTPURLResponse(
                url: url, statusCode: recorded.status, httpVersion: "HTTP/1.1", headerFields: recorded.headers)
        else { throw URLError(.badServerResponse) }
        return (recorded.body, response)
    }

    /// An answer, as a service that holds this release gives it: the release is named in
    /// the `meta` of every answer, and in the form itself.
    private static func asTheReleaseNow(_ made: Recorded, _ release: String, of route: APIRoute?) -> Recorded {
        var moved = (try? made.with(meta: { $0["release_id"] = .string(release) })) ?? made
        if route == .getMeta, made.status == 200 {
            moved = (try? moved.with(data: { $0["release_id"] = .string(release) })) ?? moved
        }
        return moved
    }

    private static func route(method: String, path: String) -> APIRoute? {
        let routes = APIRoute.allCases.filter { $0.method.rawValue == method }
        // A route with nothing to fill in comes first: `/v1/areas/geometry` is not an area.
        if let exact = routes.first(where: { $0.template == path }) { return exact }
        return routes.first { route in
            guard let name = route.parameter else { return false }
            let parts = route.template.components(separatedBy: "{\(name)}")
            guard parts.count == 2, path.hasPrefix(parts[0]), path.hasSuffix(parts[1]) else { return false }
            let filled = path.dropFirst(parts[0].count).dropLast(parts[1].count)
            return !filled.isEmpty && !filled.contains("/")
        }
    }
}

/// A search that is open on the stand-in, as the app opens one.
@MainActor
struct OpenSearch {
    let api: StandIn
    let store: SearchStore
    var flow: SearchFlow { store.flow }
    var state: SearchState { store.state }

    /// - Parameter agreed: Whether the person has agreed that their words may be read.
    /// - Parameter meta: The release the search is opened on. The recorded one, unless another is given.
    init(
        _ api: StandIn = StandIn.firstSearch(), agreed: Bool = true, timeouts: Timeouts = Timeouts(),
        meta: MetaData = Answers.meta
    ) {
        self.api = api
        store = SearchStore(
            meta: meta, areas: Answers.areas, api: api.api(timeouts: timeouts),
            mayReadWords: { agreed })
    }
}

/// Waits until something holds, for a test that watches a call that is out.
@MainActor
func until(
    _ holds: @MainActor () -> Bool, file: StaticString = #filePath, line: UInt = #line
) async {
    for _ in 0..<5_000 {
        if holds() { return }
        try? await Task.sleep(nanoseconds: 1_000_000)
    }
    XCTFail("What was waited for never came.", file: file, line: line)
}
