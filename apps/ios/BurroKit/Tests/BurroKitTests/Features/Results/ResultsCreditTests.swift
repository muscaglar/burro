import XCTest

@testable import BurroKit

/// The credit of a source on the results: every line of a card, of a row and of a
/// comparison that rests on a fact ends in the source of the fact, its credit where
/// its publisher asks to see it there, and its date.
///
/// No recorded answer holds a credit, so the service is stood in for by one that
/// answers as it was recorded, with every fact of the sources of a real release.
final class ResultsCreditTests: XCTestCase {
    /// Every line of source and date a value holds, wherever in it: those of the
    /// results, and those of a vibe.
    private func lines(in value: Any) -> (results: [Results.SourceLine], vibes: [SourceLine]) {
        var found: (results: [Results.SourceLine], vibes: [SourceLine]) = ([], [])
        func walk(_ value: Any) {
            if let line = value as? Results.SourceLine {
                found.results.append(line)
            } else if let line = value as? SourceLine {
                found.vibes.append(line)
            } else {
                for child in Mirror(reflecting: value).children { walk(child.value) }
            }
        }
        walk(value)
        return found
    }

    @MainActor
    func test_every_line_of_a_card_ends_in_the_credit_of_the_source_it_rests_on() async throws {
        // Transport for London asks that its statement is shown wherever a figure made from
        // its data is. The website shows it with the source of every sentence and figure.
        let app = try await ResultsApp.searched(Credited.service(of: [Credited.plain, Credited.stations]))
        let card = try app.firstCard()

        let found = lines(in: card)

        // Where the area is, the station, three reasons, the trade-off, the journey, the
        // cost and how the fit is worked out: each rests on a fact of the two sources.
        XCTAssertGreaterThanOrEqual(found.results.count, 2 * 8)
        XCTAssertEqual(found.results.filter { $0.name == "NaPTAN" }.count * 2, found.results.count)
        for line in found.results {
            XCTAssertEqual(line.credit, line.name == "Station data" ? Credited.drawn : nil, line.id)
            XCTAssertEqual(
                line.words,
                line.name == "Station data"
                    ? "Source: Station data. \(Credited.drawn) Data from \(line.date)."
                    : "Source: NaPTAN. Data from \(line.date).",
                line.id)
        }
        let orientation = try XCTUnwrap(card.orientation.value)
        XCTAssertEqual(
            orientation.sources.map(\.words),
            [
                "Source: NaPTAN. Data from 23 September 2026.",
                "Source: Station data. \(Credited.drawn) Data from 23 September 2026.",
            ])
        XCTAssertEqual(try XCTUnwrap(card.station.value).sources.map(\.credit), [nil, Credited.drawn])
        XCTAssertEqual(try XCTUnwrap(card.cost.value).sources.map(\.credit), [nil, Credited.drawn])
        XCTAssertEqual(card.journeys.map { $0.sources.map(\.credit) }, [[nil, Credited.drawn]])
        XCTAssertEqual(try XCTUnwrap(card.reasons.value).map { $0.sources.map(\.credit) }.count, 3)
        // The strip of vibes: each band is one line, which holds the credit once.
        XCTAssertFalse(card.strip.isEmpty)
        XCTAssertEqual(found.vibes.count, 2 * card.strip.count)
        for vibe in card.strip {
            let words = try XCTUnwrap(Results.sourceWords(of: vibe), vibe.name)
            XCTAssertEqual(vibe.sources.map(\.credit), [nil, Credited.drawn], vibe.name)
            XCTAssertTrue(words.hasPrefix("Source: NaPTAN. Data from "), vibe.name)
            XCTAssertEqual(words.components(separatedBy: Credited.drawn).count, 2, vibe.name)
            XCTAssertTrue(VibeLine.spoken(vibe, source: words).hasSuffix(words), vibe.name)
        }
        // What is drawn of a credit holds a figure, the year of the publisher's rights,
        // and is what the API sent.
        let sent = ResultsSaid.by(Array(app.state.facts.values) + (app.state.details[card.id]?.facts ?? []))
        XCTAssertTrue(ResultsDrawn.figures(in: card).contains(Credited.drawn))
        XCTAssertTrue(sent.contains(Credited.drawn))
    }

    @MainActor
    func test_a_row_that_opens_ends_each_line_in_the_credit_too() async throws {
        let app = try await ResultsApp.searched(Credited.service(of: [Credited.stops, Credited.stations]))
        let row = try XCTUnwrap(app.listed.cards.first { !$0.full })

        let found = lines(in: row)

        // A row holds its journeys, its vibes and how its fit is worked out. Two sources of
        // one publisher bring the same statement, and it is said once with each figure.
        XCTAssertFalse(found.results.isEmpty)
        for line in found.results {
            XCTAssertEqual(line.credit, line.name == "Bus stops" ? Credited.drawn : nil, line.id)
        }
        XCTAssertEqual(
            found.results.filter { $0.credit != nil }.count * 2, found.results.count)
    }

    @MainActor
    func test_every_cell_of_a_comparison_ends_in_the_credit_of_its_source() async throws {
        let sources = [Credited.plain, Credited.outlines]
        let api = StandIn.firstSearch()
            .on(.compare, .made { _ in try Credited.answer("compare-three", of: sources) })
        let app = try await ResultsApp.searched(api)
        let chosen = try ["Farrowmere", "Cindermoor", "Alderwick"].map { name in
            AreaRef(try XCTUnwrap(Answers.areas.first { $0.name == name }))
        }
        let comparison = Results.Comparison()

        await comparison.ask(chosen, of: app.search)
        guard case .here(let compared) = comparison.answer else { return XCTFail("No comparison came.") }
        let found = lines(in: compared)

        // What is said with a credit follows it, in each cell that holds a figure and
        // under each band of a vibe.
        let credit = "Contains data of an authority. \(Credited.said)."
        XCTAssertFalse(found.results.isEmpty)
        XCTAssertFalse(found.vibes.isEmpty)
        for line in found.results {
            XCTAssertEqual(line.credit, line.name == "Outlines" ? credit : nil, line.id)
        }
        for line in found.vibes {
            XCTAssertEqual(line.credit, line.name == "Outlines" ? credit : nil, line.id)
        }
        let cell = try XCTUnwrap(compared.rows.flatMap(\.cells).first { !$0.sources.isEmpty })
        XCTAssertEqual(
            cell.sources.map(\.words),
            [
                "Source: NaPTAN. Data from \(try XCTUnwrap(cell.sources.first).date).",
                "Source: Outlines. \(credit) Data from \(try XCTUnwrap(cell.sources.last).date).",
            ])
        // A cell with no figure has no source, and nothing is drawn for a credit.
        for cell in compared.rows.flatMap(\.cells) where cell.none != nil {
            XCTAssertEqual(cell.sources, [])
        }
    }

    func test_a_statement_that_two_sources_of_one_publisher_bring_is_said_once_with_a_figure() throws {
        let recorded = try XCTUnwrap(Answers.explained("explanations-first").facts.first)
        let fact = Credited.fact(recorded, of: [Credited.stops, Credited.plain, Credited.stations])
        let later = Credited.fact(recorded, of: [Credited.stations], asOf: "2026-08")

        let lines = Results.sourceLines(of: [fact, fact, later])

        XCTAssertEqual(lines.map(\.name), ["Bus stops", "NaPTAN", "Station data", "Station data"])
        XCTAssertEqual(lines.map(\.credit), [Credited.drawn, nil, nil, nil])
        XCTAssertEqual(
            lines.map(\.words),
            [
                "Source: Bus stops. \(Credited.drawn) Data from \(Credited.date).",
                "Source: NaPTAN. Data from \(Credited.date).",
                "Source: Station data. Data from \(Credited.date).",
                "Source: Station data. Data from August 2026.",
            ])
        // Each figure says it for itself: a second figure of the same source says it again.
        XCTAssertEqual(Results.sourceLines(of: [later]).map(\.credit), [Credited.drawn])
        XCTAssertEqual(Results.row(of: fact).sources, Results.sourceLines(of: [fact]))
        // A line that is made with no credit says none, as before there was one to say.
        XCTAssertNil(
            Results.SourceLine(
                sourceId: "synthetic", name: "Synthetic test data", asOf: "2025", date: "2025", synthetic: true
            ).credit)
    }
}
