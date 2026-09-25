import XCTest

@testable import BurroKit

/// The credit of a source, beside a figure. A publisher may ask that its own
/// statement stands wherever a figure made from its data is shown, and its terms
/// may ask that something is said wherever its credit is. The API says which
/// source asks, and brings both with the fact. The app draws them in the line
/// that ends every figure, in the website's words and order: the name of the
/// source, its credit, what is said with the credit, the date.
///
/// No recorded answer holds a credit, so what is drawn for one is tested on a
/// recorded fact that is given the sources of a real release.
final class CreditTests: XCTestCase {
    private let farrowmere = Answers.profile("farrowmere")

    private func recorded(_ kind: FactKind) throws -> Fact {
        try XCTUnwrap(farrowmere.facts.first { $0.kind == kind })
    }

    /// Every fact of every recording that holds facts: each area's profile, each search's
    /// reasons, and each comparison.
    private func everyRecordedFact() throws -> [Fact] {
        var facts: [Fact] = []
        for scenario in Recorded.scenarios {
            let recorded = try Recorded.read(scenario)
            guard recorded.status == 200 else { continue }
            switch recorded.operationId {
            case APIRoute.getArea.rawValue:
                facts += try Recorded.data(.getArea, scenario, as: AreaData.self).facts
            case APIRoute.explainTop.rawValue:
                facts += try Recorded.data(.explainTop, scenario, as: ExplanationsData.self).facts
            case APIRoute.compare.rawValue:
                facts += try Recorded.data(.compare, scenario, as: CompareData.self).facts
            default:
                continue
            }
        }
        return facts
    }

    // MARK: - What is drawn

    func test_a_publishers_own_statement_is_drawn_beside_the_figure_where_it_asks_to_see_it_there() throws {
        // Transport for London asks that its statement is shown wherever a figure made from
        // its data is. The API says which source asks, and brings the statement with the fact.
        let station = Credited.fact(try recorded(.station), of: [Credited.plain, Credited.stations])

        let lines = SourceLines.of([station])

        XCTAssertEqual(lines.map(\.name), ["NaPTAN", "Station data"])
        // A source that asks for no more than its name has no more than its name.
        XCTAssertEqual(lines.map(\.credit), [nil, Credited.drawn])
        XCTAssertEqual(
            lines.map(\.words),
            [
                "NaPTAN. Data from \(Credited.date).",
                "Station data. \(Credited.drawn) Data from \(Credited.date).",
            ])
        XCTAssertEqual(
            SourceLines.words(for: [station]),
            "Source: NaPTAN. Data from \(Credited.date). Station data. \(Credited.drawn) "
                + "Data from \(Credited.date).")
        XCTAssertEqual(FactRow(station)?.sourceWords, SourceLines.words(for: [station]))
    }

    func test_what_is_said_with_a_credit_follows_it_wherever_the_credit_stands() throws {
        // The terms of a publisher may ask that something is said wherever its credit is shown.
        // The API brings it with the credit, and it is said after it, as a sentence of its own.
        let feature = Credited.fact(try recorded(.feature), of: [Credited.plain, Credited.outlines])

        XCTAssertEqual(
            SourceLines.words(for: [feature]),
            "Source: NaPTAN. Data from \(Credited.date). Outlines. Contains data of an authority. "
                + "\(Credited.said). Data from \(Credited.date).")
        // A source that brings no credit brings nothing to say with one.
        let plain = Credited.fact(try recorded(.feature), of: [Credited.plain])
        XCTAssertEqual(SourceLines.words(for: [plain]), "Source: NaPTAN. Data from \(Credited.date).")
    }

    func test_a_statement_that_two_sources_of_one_publisher_bring_is_said_once() throws {
        // A figure made from two files of one publisher, the bus stops and the stations, each
        // of which brings the publisher's statement. On the website it once stood twice.
        let vibe = Credited.fact(
            try recorded(.tag), of: [Credited.stops, Credited.plain, Credited.stations], asOf: "2025")
        let other = Credited.fact(try recorded(.feature), of: [Credited.stations], asOf: "2026-08")

        let lines = SourceLines.of([vibe, vibe, other])
        let words = try XCTUnwrap(SourceLines.words(for: [vibe, vibe, other]))

        XCTAssertEqual(lines.map(\.name), ["Bus stops", "NaPTAN", "Station data", "Station data"])
        XCTAssertEqual(lines.map(\.asOf), ["2025", "2025", "2025", "2026-08"])
        // It is said with the first source that brings it, however many facts share it.
        XCTAssertEqual(lines.map(\.credit), [Credited.drawn, nil, nil, nil])
        XCTAssertEqual(words.components(separatedBy: "Powered by TfL Open Data.").count, 2)
        XCTAssertEqual(
            words,
            "Source: Bus stops. \(Credited.drawn) Data from 2025. NaPTAN. Data from 2025. "
                + "Station data. Data from 2025. Station data. Data from August 2026.")
        // Two publishers each have their own, and each is said.
        let two = Credited.fact(try recorded(.feature), of: [Credited.outlines, Credited.stations])
        XCTAssertEqual(
            SourceLines.of([two]).map(\.credit),
            ["Contains data of an authority. \(Credited.said).", Credited.drawn])
    }

    func test_a_statement_is_written_as_the_website_writes_it_each_line_a_sentence() {
        func credit(_ attribution: String?, _ said: String? = nil) -> String? {
            SourceLines.credit(
                of: FactSource(
                    sourceId: "a-source", name: "A source", publisher: "A publisher",
                    attribution: attribution, saidWithAttribution: said))
        }

        XCTAssertEqual(credit(Credited.statement), Credited.drawn)
        // A line that ends a sentence already is left as it ends.
        XCTAssertEqual(credit("One line.\nIs it another?\nIt is!"), "One line. Is it another? It is!")
        // An empty line, and the space round a line, are not drawn.
        XCTAssertEqual(credit("  One line \n\n\r\n Another\n"), "One line. Another.")
        XCTAssertEqual(credit("A credit", "What is said with it"), "A credit. What is said with it.")
        XCTAssertEqual(credit("A credit.", "Said in\ntwo lines."), "A credit. Said in. two lines.")
        // Nothing is made of nothing: no name of the publisher, and no words of the app's.
        XCTAssertNil(credit(nil))
        XCTAssertNil(credit(nil, nil))
        XCTAssertNil(credit("", ""))
        XCTAssertNil(credit(" \n ", "\n"))
        // What is said with a credit is the API's to bring, and is drawn as it came.
        XCTAssertEqual(credit(nil, Credited.said), "\(Credited.said).")
        for source in [Credited.plain, Credited.stops, Credited.stations, Credited.outlines] {
            XCTAssertEqual(SourceLines.credit(of: source), Credited.asDrawn(source), source.name)
        }
    }

    func test_the_credit_stands_where_the_website_puts_it_after_the_name_and_before_the_date() throws {
        let web = Repository.root.appendingPathComponent("apps/web/src")
        let written = try Repository.text(web.appendingPathComponent("components/SourceLine/SourceLine.tsx"))
        let pressed = try Repository.text(web.appendingPathComponent("components/SourceNote/SourceNote.tsx"))
        let facts = try Repository.text(web.appendingPathComponent("lib/facts.ts"))

        // The website: the name of the source, its credit, the date, and that it is made up,
        // under a figure that is written out and behind the press of "Source" alike.
        for page in [written, pressed] {
            var last = page.startIndex
            for part in ["{source.name}", "creditOf", "SOURCE.dataFrom", "SOURCE.madeUp"] {
                let found = try XCTUnwrap(page.range(of: part, range: last..<page.endIndex), part)
                last = found.upperBound
            }
        }
        // The credit comes first, and what is said with it after it.
        XCTAssertTrue(
            facts.contains(#"`${source.attribution ?? ""}\n${source.said_with_attribution ?? ""}`"#))
        // The app: the same order, in the same words.
        let fact = Fact(
            factId: "x", areaId: "syn-n0006", kind: .feature, key: "k", label: "A feature",
            template: .feature, slots: [:], numbers: [], names: [], sources: [Credited.outlines],
            asOf: Credited.asOf, synthetic: true)
        let words = try XCTUnwrap(SourceLines.words(for: [fact]))
        var last = words.startIndex
        for part in [
            "Source", "Outlines", "Contains data of an authority", Credited.said, "Data from",
            Credited.date, "Made-up data",
        ] {
            let found = try XCTUnwrap(words.range(of: part, range: last..<words.endIndex), part)
            last = found.upperBound
        }
        XCTAssertEqual(
            words,
            "Source: Outlines. Contains data of an authority. \(Credited.said). "
                + "Data from \(Credited.date). Made-up data")
    }

    // MARK: - Where there is none

    func test_where_a_fact_has_no_credit_nothing_is_drawn_for_one_and_nothing_is_made_up() throws {
        let facts = try everyRecordedFact()

        XCTAssertGreaterThan(facts.count, 3_000)
        for fact in facts {
            // The made-up release credits one source, which asks for no more than its name.
            XCTAssertEqual(fact.sources.map(\.attribution), [nil], fact.factId)
            XCTAssertEqual(fact.sources.map(\.saidWithAttribution), [nil], fact.factId)
            let lines = SourceLines.of([fact])
            XCTAssertEqual(lines.map(\.credit), [nil], fact.factId)
            // The line is the name, the date and that the data is made up, and no word more.
            XCTAssertEqual(
                lines.map(\.words),
                ["Synthetic test data. Data from \(ReadableDate.words(fact.asOf)). Made-up data"],
                fact.factId)
            XCTAssertEqual(
                Results.sourceLines(of: [fact]).map(\.words),
                ["Source: Synthetic test data. Data from \(Results.readableDate(fact.asOf)). Made-up data"],
                fact.factId)
        }
        // The source has a statement of its own, on the screen of sources. It asks to see it
        // nowhere else, so no figure is followed by it.
        let served = try XCTUnwrap(Answers.meta.attributions.first)
        XCTAssertFalse(served.creditBesideFigures)
        XCTAssertFalse(served.attribution.isEmpty)
        XCTAssertFalse(SourceLines.words(for: facts)?.contains(served.attribution) ?? true)
    }

    // MARK: - On the screen of an area

    @MainActor
    func test_every_row_and_every_vibe_of_an_areas_screen_ends_in_the_credit_of_its_sources() throws {
        let data: AreaData = try Credited.data("area/farrowmere", of: [Credited.plain, Credited.stations])
        let page = AreaPage(
            data, release: AreaFixtures.release, features: Answers.meta.features, tags: Answers.meta.tags,
            recipes: Answers.meta.recipes, guides: Answers.meta.roughGuides)
        let rows = page.stationRows + page.rentRows + page.buyRows
            + page.measured.flatMap { page.rows(of: $0) }

        XCTAssertEqual(rows.count, AreaFixtures.page("farrowmere").stationRows.count + 6 + 4 + 109)
        for row in rows where row.noFigure == nil {
            XCTAssertEqual(row.sources.map(\.credit), [nil, Credited.drawn], row.name)
            XCTAssertEqual(
                row.sourceWords?.components(separatedBy: Credited.drawn).count, 2, row.name)
            XCTAssertFalse(row.sourceWords?.contains("Made-up data") ?? true, row.name)
        }
        // A row with no figure has no source, and so no credit.
        for row in rows where row.noFigure != nil {
            XCTAssertNil(row.sourceWords, row.name)
        }
        XCTAssertEqual(page.vibes.count, 14)
        for vibe in page.vibes {
            XCTAssertEqual(vibe.shown.sources.map(\.credit), [nil, Credited.drawn], vibe.shown.name)
            let drawn = SourceLines.words(for: vibe.fact.map { [$0] } ?? [])
            XCTAssertEqual(drawn?.components(separatedBy: Credited.drawn).count, 2, vibe.shown.name)
            // The line is read out with the vibe, so the credit is heard where it is seen.
            XCTAssertTrue(
                VibeLine.spoken(vibe.shown, source: drawn).hasSuffix(drawn ?? "no source"), vibe.shown.name)
        }
        // The name of the area rests on a fact too.
        XCTAssertEqual(
            SourceLines.words(for: page.named.map { [$0] } ?? []),
            "Source: NaPTAN. Data from 23 September 2026. Station data. \(Credited.drawn) "
                + "Data from 23 September 2026.")
        // What the screen says of a credit is what the API sent, and the screen lists it
        // with everything else it says.
        XCTAssertTrue(page.said.contains(Credited.drawn))
        XCTAssertEqual(Credited.asDrawn(Credited.stations), Credited.drawn)
    }

    @MainActor
    func test_a_sentence_of_the_search_ends_in_the_credit_of_the_fact_it_cites() async throws {
        let search = OpenSearch(Credited.service(of: [Credited.stops, Credited.stations]))
        await search.flow.submitText("leafy and quiet")

        let said = try XCTUnwrap(AreaInSearch(search.state, areaId: "syn-n0006"))

        XCTAssertTrue(said.explained)
        XCTAssertEqual(said.reasons.count, 3)
        for sentence in said.reasons + [said.tradeOff, said.orientation].compactMap({ $0 }) {
            XCTAssertEqual(sentence.sources.map(\.name), ["Bus stops", "Station data"], sentence.text)
            XCTAssertEqual(sentence.sources.map(\.credit), [Credited.drawn, nil], sentence.text)
            XCTAssertTrue(
                sentence.sourceWords?.hasPrefix("Source: Bus stops. \(Credited.drawn) Data from ") ?? false,
                sentence.text)
        }
    }
}
