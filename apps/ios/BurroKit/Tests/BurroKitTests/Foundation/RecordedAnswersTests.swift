import XCTest

@testable import BurroKit

/// Every recorded answer is read by the generated models, and written back as it came.
final class RecordedAnswersTests: XCTestCase {
    /// Reads the `data` of an answer as its type, writes it again, and says whether it came back the same.
    private func comesBackTheSame<Payload: Codable & Sendable>(
        _ type: Payload.Type, _ recorded: Recorded
    ) throws -> Bool {
        let envelope = try JSONDecoder().decode(Envelope<Payload>.self, from: recorded.body)
        let original = try JSON.read(recorded.body)
        let data = try JSON.written(envelope.data)
        let meta = try JSON.written(envelope.meta)
        return data == original["data"] && meta == original["meta"] && unlisted(in: envelope.data).isEmpty
    }

    /// Where a value holds something this build does not know.
    private func unlisted(in value: Any, at path: String = "") -> [String] {
        let mirror = Mirror(reflecting: value)
        if mirror.displayStyle == .enum, mirror.children.first?.label == "unlisted" { return [path] }
        return mirror.children.flatMap { unlisted(in: $0.value, at: "\(path).\($0.label ?? "_")") }
    }

    private func isReadWhole(_ recorded: Recorded) throws -> Bool {
        guard recorded.status == 200 else {
            let envelope = try JSONDecoder().decode(ErrorEnvelope.self, from: recorded.body)
            let written = try JSON.written(envelope)
            let original = try JSON.read(recorded.body)
            return written == original && unlisted(in: envelope).isEmpty
        }
        let route = try XCTUnwrap(recorded.operationId.flatMap(APIRoute.init(rawValue:)))
        switch route {
        case .interpret: return try comesBackTheSame(InterpretData.self, recorded)
        case .rank: return try comesBackTheSame(RankData.self, recorded)
        case .explainTop: return try comesBackTheSame(ExplanationsData.self, recorded)
        case .compare: return try comesBackTheSame(CompareData.self, recorded)
        case .searchPlaces: return try comesBackTheSame(PlacesData.self, recorded)
        case .createShare: return try comesBackTheSame(ShareCreated.self, recorded)
        case .getShare: return try comesBackTheSame(ShareData.self, recorded)
        case .listAreas: return try comesBackTheSame(AreasData.self, recorded)
        case .getGeometry: return try comesBackTheSame(GeometryData.self, recorded)
        case .getArea: return try comesBackTheSame(AreaData.self, recorded)
        case .getCensus: return try comesBackTheSame(CensusPanel.self, recorded)
        case .getIncome: return try comesBackTheSame(IncomeShown.self, recorded)
        case .getMeta: return try comesBackTheSame(MetaData.self, recorded)
        case .healthz:
            let health = try JSONDecoder().decode(Health.self, from: recorded.body)
            let written = try JSON.written(health)
            let original = try JSON.read(recorded.body)
            return written == original
        }
    }

    func test_the_copies_are_the_recordings_byte_for_byte() throws {
        let theirs = Repository.files(under: Repository.webRecorded, ending: ".json")
        let ours = Repository.files(under: Repository.recorded, ending: ".json")
        XCTAssertFalse(theirs.isEmpty, "apps/web/test/recorded was not found.")

        XCTAssertEqual(ours, theirs, "Run `make generate`.")
        let changed = try theirs.filter { name in
            try Data(contentsOf: Repository.webRecorded.appendingPathComponent(name))
                != Data(contentsOf: Repository.recorded.appendingPathComponent(name))
        }
        XCTAssertEqual(changed, [], "Run `make generate`.")
    }

    func test_the_index_lists_exactly_the_recordings_that_are_there() throws {
        struct Index: Decodable {
            struct Entry: Decodable {
                let scenario: String
                let operation_id: String?
                let status: Int
            }
            let scenarios: [Entry]
        }
        let index = try JSONDecoder().decode(
            Index.self, from: Data(contentsOf: Repository.recorded.appendingPathComponent("index.json")))

        XCTAssertEqual(index.scenarios.map(\.scenario).sorted(), Recorded.scenarios)
        for entry in index.scenarios {
            let recorded = try Recorded.read(entry.scenario)
            XCTAssertEqual(recorded.scenario, entry.scenario)
            XCTAssertEqual(recorded.operationId, entry.operation_id)
            XCTAssertEqual(recorded.status, entry.status)
        }
    }

    func test_every_recording_was_captured_from_the_api_and_none_was_made_by_hand() throws {
        XCTAssertGreaterThan(Recorded.scenarios.count, 100)
        XCTAssertEqual(try Recorded.scenarios.filter { try !Recorded.read($0).captured }, [])
    }

    func test_there_is_a_recorded_answer_for_every_route() throws {
        let recorded = Set(try Recorded.scenarios.compactMap { try Recorded.read($0).operationId })

        XCTAssertEqual(APIRoute.allCases.map(\.rawValue).filter { !recorded.contains($0) }, [])
    }

    func test_every_recorded_answer_is_read_whole_and_written_back_as_it_came() throws {
        var notRead: [String] = []
        for scenario in Recorded.scenarios {
            do {
                if try !isReadWhole(Recorded.read(scenario)) { notRead.append(scenario) }
            } catch {
                notRead.append("\(scenario): \(type(of: error))")
            }
        }

        XCTAssertEqual(notRead, [])
    }

    func test_every_request_that_was_answered_is_one_the_models_can_send() throws {
        var notSent: [String] = []
        for scenario in Recorded.scenarios {
            let recorded = try Recorded.read(scenario)
            guard recorded.status == 200, let sent = recorded.sent,
                let route = recorded.operationId.flatMap(APIRoute.init(rawValue:))
            else { continue }
            do {
                let decoder = JSONDecoder()
                let spec: PreferenceSpec?
                switch route {
                case .interpret: spec = try decoder.decode(InterpretBody.self, from: sent).spec
                case .rank: spec = try decoder.decode(RankBody.self, from: sent).spec
                case .explainTop: spec = try decoder.decode(ExplanationsBody.self, from: sent).spec
                case .compare: spec = try decoder.decode(CompareBody.self, from: sent).spec
                case .createShare: spec = try decoder.decode(ShareBody.self, from: sent).spec
                case .searchPlaces:
                    _ = try decoder.decode(PlaceSearchBody.self, from: sent)
                    spec = nil
                default: spec = nil
                }
                // A spec is sent again with every call, so it must leave as it arrived.
                if let spec {
                    let original = try JSON.read(sent)["spec"]
                    let written = try JSON.written(spec)
                    if written != original { notSent.append(scenario) }
                }
            } catch {
                notSent.append("\(scenario): \(type(of: error))")
            }
        }

        XCTAssertEqual(notSent, [])
    }

    /// What the service makes, and what says which build answered, as the recordings hold
    /// them: the id of a share and of a request, the hash of a spec, the release and the engine.
    private func madeByTheService() throws -> Set<String> {
        let made: Set<String> = ["share_id", "spec_hash", "release_id", "original_release_id", "engine_version"]
        var held: Set<String> = []
        func gather(_ value: JSON, under key: String) {
            switch value {
            case .object(let fields): fields.forEach { gather($0.value, under: $0.key) }
            case .array(let items): items.forEach { gather($0, under: key) }
            case .string(let text): if made.contains(key) { held.insert(text) }
            default: break
            }
        }
        for scenario in Recorded.scenarios {
            let recorded = try Recorded.read(scenario)
            gather(try JSON.read(recorded.body), under: "")
            if let id = recorded.headers["x-request-id"] { held.insert(id) }
            // A share that was asked for is named in the path, and in no body.
            if recorded.operationId == APIRoute.getShare.rawValue, let id = recorded.path.split(separator: "/").last {
                held.insert(String(id))
            }
        }
        return held.filter { !$0.isEmpty }
    }

    func test_no_test_holds_as_written_what_the_service_made_or_which_build_answered() throws {
        // An id is made again each time the answers are recorded, and the release and the
        // engine move with a build. A test that held one as written went on holding it
        // after the recordings had moved: it failed, or it looked for an id nothing made.
        let made = try madeByTheService()
        XCTAssertTrue(made.contains(Answers.shareId))
        XCTAssertTrue(made.contains(Answers.meta.releaseId))
        XCTAssertTrue(made.contains(Answers.meta.engineVersion))
        XCTAssertTrue(made.contains(Answers.ranked("rank-first").specHash))

        let holding = try Repository.files(under: Repository.tests, ending: ".swift").filter { name in
            let text = try Repository.text(Repository.tests.appendingPathComponent(name))
            return made.contains { text.contains($0) }
        }

        // Which file holds one is said, and never what it holds.
        XCTAssertEqual(holding, [], "Read it from the recording: `Answers.shareId`, `Answers.meta`.")
    }

    func test_every_area_of_the_release_has_a_recorded_profile() {
        XCTAssertEqual(Answers.areas.filter { !Recorded.scenarios.contains("area/\($0.slug)") }.map(\.slug), [])
    }

    func test_every_recorded_answer_says_the_data_is_made_up() throws {
        for scenario in Recorded.scenarios {
            let recorded = try Recorded.read(scenario)
            XCTAssertEqual(recorded.headers["x-burro-synthetic"], "true", scenario)
        }
        XCTAssertTrue(Answers.meta.synthetic)
    }
}
