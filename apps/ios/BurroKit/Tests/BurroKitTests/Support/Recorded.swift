import Foundation
import XCTest

@testable import BurroKit

/// One recorded answer: a request, and what the real API answered.
///
/// The recordings are captured by `apps/web/test/record.py` and copied here by
/// `scripts/generate.py`. They are never written or edited by hand.
struct Recorded: Sendable {
    let scenario: String
    /// What the scenario is there to show, in a line.
    let shows: String
    let captured: Bool
    /// `nil` for a request to a path that is no route.
    let operationId: String?
    let method: String
    let route: String
    let path: String
    /// The body that was sent, as JSON. `nil` for a `GET`.
    let sent: Data?
    let status: Int
    let headers: [String: String]
    /// The body that came back, as JSON.
    let body: Data

    /// Every scenario there is a recording of, in order.
    static let scenarios: [String] = Repository.files(under: Repository.recorded, ending: ".json")
        .map { String($0.dropLast(".json".count)) }
        .filter { $0 != "index" }
        .sorted()

    private struct File: Decodable {
        struct Request: Decodable {
            let operation_id: String?
            let method: String
            let route: String
            let path: String
            let body: JSON?
        }
        let scenario: String
        let shows: String
        let captured: Bool
        let request: Request
        let status: Int
        let headers: [String: String]
        let body: JSON
    }

    static func read(_ scenario: String) throws -> Recorded {
        let url = Repository.recorded.appendingPathComponent("\(scenario).json")
        let file = try JSONDecoder().decode(File.self, from: Data(contentsOf: url))
        return Recorded(
            scenario: file.scenario,
            shows: file.shows,
            captured: file.captured,
            operationId: file.request.operation_id,
            method: file.request.method,
            route: file.request.route,
            path: file.request.path,
            sent: try file.request.body?.data,
            status: file.status,
            headers: file.headers,
            body: try file.body.data
        )
    }

    /// The `data` of a recorded answer of a route that went well, with the type the contract gives it.
    static func data<Payload: Decodable & Sendable>(
        _ route: APIRoute, _ scenario: String, as type: Payload.Type = Payload.self
    ) throws -> Payload {
        let recorded = try read(scenario)
        guard recorded.operationId == route.rawValue, recorded.status == 200 else {
            throw Problem.notAnAnswerOf(route.rawValue, scenario)
        }
        return try JSONDecoder().decode(Envelope<Payload>.self, from: recorded.body).data
    }

    /// A recorded error, in the API's error envelope.
    static func error(_ scenario: String) throws -> ErrorEnvelope {
        let recorded = try read(scenario)
        guard recorded.status >= 400 else { throw Problem.notAnError(scenario) }
        return try JSONDecoder().decode(ErrorEnvelope.self, from: recorded.body)
    }

    /// The recording with something of its `data` put in place of what was recorded.
    func with(data change: (inout JSON) -> Void) throws -> Recorded {
        var whole = try JSON.read(body)
        guard var data = whole["data"] else { throw Problem.notARecording(scenario) }
        change(&data)
        whole["data"] = data
        return try with(body: whole.data)
    }

    /// The recording with something of its `meta` put in place of what was recorded.
    func with(meta change: (inout JSON) -> Void) throws -> Recorded {
        var whole = try JSON.read(body)
        guard var meta = whole["meta"] else { throw Problem.notARecording(scenario) }
        change(&meta)
        whole["meta"] = meta
        return try with(body: whole.data)
    }

    func with(body: Data? = nil, status: Int? = nil, headers: [String: String]? = nil) -> Recorded {
        Recorded(
            scenario: scenario, shows: shows, captured: captured, operationId: operationId,
            method: method, route: route, path: path, sent: sent,
            status: status ?? self.status, headers: headers ?? self.headers, body: body ?? self.body)
    }

    enum Problem: Error {
        case notARecording(String)
        case notAnAnswerOf(String, String)
        case notAnError(String)
    }
}

/// The answers most tests begin from, read once.
enum Answers {
    static let meta: MetaData = must { try Recorded.data(.getMeta, "meta") }
    static let areas: [AreaSummary] = must { try Recorded.data(.listAreas, "areas", as: AreasData.self).areas }
    static let geometry: GeometryData = must { try Recorded.data(.getGeometry, "geometry") }

    static func read(_ scenario: String) -> InterpretData {
        must { try Recorded.data(.interpret, scenario) }
    }

    static func ranked(_ scenario: String) -> RankData {
        must { try Recorded.data(.rank, scenario) }
    }

    static func explained(_ scenario: String) -> ExplanationsData {
        must { try Recorded.data(.explainTop, scenario) }
    }

    static func shared(_ scenario: String) -> ShareData {
        must { try Recorded.data(.getShare, scenario) }
    }

    static func profile(_ slug: String) -> AreaData {
        must { try Recorded.data(.getArea, "area/\(slug)") }
    }

    /// A failure as the client makes it of a recorded error.
    static func failure(_ scenario: String) -> Failure {
        must {
            let recorded = try Recorded.read(scenario)
            let envelope = try Recorded.error(scenario)
            return .api(
                APIFailure(
                    status: recorded.status, code: envelope.error.code, message: envelope.error.message,
                    fields: envelope.error.fields, meta: envelope.meta, synthetic: envelope.meta.synthetic,
                    requestId: recorded.headers["x-request-id"]))
        }
    }

    private static func must<Value>(_ read: () throws -> Value) -> Value {
        do {
            return try read()
        } catch {
            fatalError("A recorded answer could not be read. Run `make generate`.")
        }
    }
}
