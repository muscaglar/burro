import CryptoKit
import XCTest

@testable import BurroKit

/// What is generated must be what its source says now, and must say it whole.
final class GeneratedTests: XCTestCase {
    private func sha256(_ url: URL) throws -> String {
        SHA256.hash(data: try Data(contentsOf: url)).map { String(format: "%02x", $0) }.joined()
    }

    private func contract() throws -> [String: Any] {
        let whole = try JSONSerialization.jsonObject(with: Data(contentsOf: Repository.contract))
        return try XCTUnwrap(whole as? [String: Any])
    }

    func test_the_models_were_generated_from_the_contract_as_it_stands() throws {
        XCTAssertEqual(
            GeneratedFrom.contractSHA256, try sha256(Repository.contract),
            "contracts/openapi.json has changed. Run `make generate`.")
    }

    func test_the_generator_would_change_nothing_if_it_were_run_now() throws {
        #if os(macOS)
            let check = Process()
            check.executableURL = URL(fileURLWithPath: "/usr/bin/env")
            check.arguments = [
                "python3", Repository.ios.appendingPathComponent("scripts/generate.py").path, "--check",
            ]
            let said = Pipe()
            check.standardOutput = said
            check.standardError = said
            do {
                try check.run()
            } catch {
                throw XCTSkip("python3 could not be started here. `make generate-check` checks the same thing.")
            }
            let output = String(decoding: said.fileHandleForReading.readDataToEndOfFile(), as: UTF8.self)
            check.waitUntilExit()

            XCTAssertEqual(
                check.terminationStatus, 0, "A generated file was edited by hand or is stale. \(output)")
        #else
            throw XCTSkip("The generator runs on a Mac. `make generate-check` checks the same thing.")
        #endif
    }

    func test_every_route_of_the_contract_has_a_method_and_no_other_route_has() throws {
        let paths = try XCTUnwrap(contract()["paths"] as? [String: [String: [String: Any]]])
        var inContract: [String: String] = [:]
        for (path, methods) in paths {
            for (method, operation) in methods {
                let id = try XCTUnwrap(operation["operationId"] as? String)
                inContract[id] = "\(method.uppercased()) \(path)"
            }
        }

        let inTheApp = Dictionary(
            uniqueKeysWithValues: APIRoute.allCases.map { ($0.rawValue, "\($0.method.rawValue) \($0.template)") })

        XCTAssertEqual(inTheApp, inContract)
    }

    func test_every_schema_of_the_contract_has_a_model_of_its_name() throws {
        let components = try XCTUnwrap(contract()["components"] as? [String: Any])
        let schemas = try XCTUnwrap(components["schemas"] as? [String: [String: Any]])
        let models = try Repository.text(
            Repository.sources.appendingPathComponent("API/Generated/APIModels.swift"))

        let missing = schemas.keys.sorted().filter { name in
            // Every envelope is the one generic record, `Envelope`.
            guard !name.hasPrefix("Envelope_") else { return false }
            let kind = schemas[name]?["enum"] == nil ? "struct" : "enum"
            return !models.contains("public \(kind) \(name): ")
        }

        XCTAssertEqual(missing, [])
    }

    func test_every_value_of_a_code_in_the_contract_is_one_the_model_lists() throws {
        let components = try XCTUnwrap(contract()["components"] as? [String: Any])
        let schemas = try XCTUnwrap(components["schemas"] as? [String: [String: Any]])

        XCTAssertEqual(ErrorCode.allCases.map(\.rawValue), schemas["ErrorCode"]?["enum"] as? [String])
        XCTAssertEqual(FeatureId.allCases.map(\.rawValue), schemas["FeatureId"]?["enum"] as? [String])
        XCTAssertEqual(TagId.allCases.map(\.rawValue), schemas["TagId"]?["enum"] as? [String])
        XCTAssertEqual(OpsGroup.allCases.map(\.rawValue), schemas["OpsGroup"]?["enum"] as? [String])
        XCTAssertEqual(Set(OpsGroup.inOrder), Set(OpsGroup.allCases))
    }

    func test_a_value_this_build_does_not_know_is_kept_and_sent_back_as_it_came() throws {
        let sent = Data(#"["leafy","a_tag_of_next_year"]"#.utf8)

        let tags = try JSONDecoder().decode([TagId].self, from: sent)

        XCTAssertEqual(tags, [.leafy, .unlisted("a_tag_of_next_year")])
        XCTAssertEqual(try JSONEncoder().encode(tags), sent)
        XCTAssertFalse(TagId.allCases.contains(.unlisted("a_tag_of_next_year")))
    }

    func test_a_field_the_api_adds_later_does_not_stop_an_answer_being_read() throws {
        let later = Data(
            #"{"area_id":"syn-n0001","score":12.5,"counted":3,"present":2,"added_next_year":true}"#.utf8)

        let score = try JSONDecoder().decode(Score.self, from: later)

        XCTAssertEqual(score, Score(areaId: "syn-n0001", score: 12.5, counted: 3, present: 2))
    }

    func test_an_answer_that_lacks_what_the_contract_requires_is_not_read() {
        let lacking = Data(#"{"area_id":"syn-n0001"}"#.utf8)

        XCTAssertThrowsError(try JSONDecoder().decode(Score.self, from: lacking))
    }

    func test_a_field_the_contract_requires_is_written_even_when_it_holds_nothing() throws {
        let budget = Answers.meta.defaults.rent.budget
        XCTAssertNil(budget.amount)

        let written = try JSON.written(budget)

        XCTAssertEqual(written["amount"], .null)
    }

    func test_a_field_the_contract_gives_a_default_is_always_sent() throws {
        let spec = Answers.meta.defaults.rent
        XCTAssertEqual(try JSON.written(RankBody(spec: spec))["limit"], .number(20))
        XCTAssertEqual(try JSON.written(ExplanationsBody(spec: spec))["limit"], .number(3))
        XCTAssertEqual(try JSON.written(PlaceSearchBody(q: "pel"))["limit"], .number(8))
        XCTAssertEqual(try JSON.written(ShareBody(spec: spec))["exact_destinations"], .bool(false))
        // Edits that are not there are left out, and never sent as nothing.
        XCTAssertNil(try JSON.written(RankBody(spec: spec))["operations"])
    }

    func test_a_number_is_sent_as_a_number() throws {
        let edit = Edits.featureWeight(.airNo2, 1)

        let written = String(decoding: try JSONEncoder().encode(edit), as: UTF8.self)

        XCTAssertTrue(written.contains(#""value":1"#))
        XCTAssertFalse(written.contains(#""value":"1""#))
        XCTAssertFalse(written.contains(#""value":true"#))
    }

    func test_a_position_is_a_longitude_then_a_latitude() throws {
        let position = try JSONDecoder().decode(LonLat.self, from: Data("[-0.016848, 0.040758]".utf8))

        XCTAssertEqual(position, LonLat(longitude: -0.016848, latitude: 0.040758))
        XCTAssertThrowsError(try JSONDecoder().decode(LonLat.self, from: Data("[1, 2, 3]".utf8)))
        XCTAssertThrowsError(try JSONDecoder().decode(LonLat.self, from: Data("[1]".utf8)))
    }

    func test_a_boundary_is_read_as_the_shape_its_type_says() throws {
        for feature in Answers.geometry.features {
            switch (feature.geometry.type, feature.geometry.coordinates) {
            case (.polygon, .polygon(let rings)):
                XCTAssertFalse(rings.isEmpty)
            case (.multiPolygon, .multiPolygon(let polygons)):
                XCTAssertFalse(polygons.isEmpty)
            default:
                XCTFail("The boundary of \(feature.id) is not the shape its type says.")
            }
        }
        XCTAssertEqual(Answers.geometry.features.count, Answers.areas.count)
    }
}
