import Foundation
import XCTest

@testable import BurroKit

/// Facts as a release of a real city holds them: of sources whose publisher asks
/// that its own statement of credit stands wherever a figure made from its data is
/// shown, and of one whose terms ask that something is said with the credit.
///
/// No recorded answer holds such a fact. The made-up release credits one source,
/// which asks for no more than its name, so a test of what is drawn for a credit
/// makes its fact here, from a recorded one. The statements are the ones the
/// website's tests of the same thing hold.
enum Credited {
    /// A publisher's own statement, in the two lines it is served in.
    static let statement = "Powered by TfL Open Data\nContains OS data © Crown copyright and database rights 2016"
    /// The same, as it is drawn: each line a sentence.
    static let drawn = "Powered by TfL Open Data. Contains OS data © Crown copyright and database rights 2016."
    /// What the terms of a publisher ask to be said wherever its credit is shown.
    static let said = "The publisher cannot warrant the quality or accuracy of the data"

    /// A source that asks for no more than its name.
    static let plain = FactSource(sourceId: "naptan", name: "NaPTAN", publisher: "Department for Transport")
    /// Two sources of one publisher, which each bring its statement.
    static let stops = FactSource(
        sourceId: "bus-stops", name: "Bus stops", publisher: "Transport for London", attribution: statement)
    static let stations = FactSource(
        sourceId: "station-data", name: "Station data", publisher: "Transport for London",
        attribution: statement)
    /// A source whose terms ask that something is said with its credit.
    static let outlines = FactSource(
        sourceId: "outlines", name: "Outlines", publisher: "An authority",
        attribution: "Contains data of an authority", saidWithAttribution: said)

    /// The day the facts made here are of, as the API writes it and as a person reads it.
    static let asOf = "2026-09-24"
    static let date = "24 September 2026"

    /// A fact as it was recorded, but of these sources, and of data that is not made up.
    static func fact(_ fact: Fact, of sources: [FactSource], asOf: String = Credited.asOf) -> Fact {
        Fact(
            factId: fact.factId, areaId: fact.areaId, kind: fact.kind, key: fact.key, label: fact.label,
            template: fact.template, slots: fact.slots, numbers: fact.numbers, names: fact.names,
            sources: sources, asOf: asOf, synthetic: false)
    }

    /// A recorded answer in which every fact is of these sources, and is not made up. The
    /// date of each fact, and everything else of the answer, is as it was recorded.
    static func answer(_ scenario: String, of sources: [FactSource]) throws -> Recorded {
        let written = try sources.map { try JSON.written($0) }
        return try Recorded.read(scenario).with(data: { data in
            data["facts"] = data["facts"]?.each { fact in
                fact["sources"] = .array(written)
                fact["synthetic"] = .bool(false)
            }
        })
    }

    /// The service, where every fact of the reasons and of the profile of an area is of
    /// these sources.
    static func service(of sources: [FactSource], reasons: String = "explanations-first") -> StandIn {
        StandIn.firstSearch()
            .on(.explainTop, .made { _ in try answer(reasons, of: sources) })
            .on(
                .getArea,
                .made { call in
                    try answer("area/\(call.path.split(separator: "/").last ?? "")", of: sources)
                })
    }

    /// The `data` of such an answer, with the type the contract gives it.
    static func data<Payload: Decodable & Sendable>(
        _ scenario: String, of sources: [FactSource], as type: Payload.Type = Payload.self
    ) throws -> Payload {
        try JSONDecoder().decode(Envelope<Payload>.self, from: answer(scenario, of: sources).body).data
    }

    /// What a source brings to be drawn beside a figure, made here from what the API
    /// sent, so that a test holds what is drawn to the answer and not to the app: each
    /// line of the statement a sentence, and what is said with it after it. `nil` for a
    /// source that brings none.
    static func asDrawn(_ source: FactSource) -> String? {
        var sentences: [String] = []
        for part in [source.attribution, source.saidWithAttribution] {
            for line in (part ?? "").components(separatedBy: "\n") {
                let words = line.trimmingCharacters(in: .whitespacesAndNewlines)
                guard let last = words.last else { continue }
                sentences.append(".!?".contains(last) ? words : words + ".")
            }
        }
        return sentences.isEmpty ? nil : sentences.joined(separator: " ")
    }
}
