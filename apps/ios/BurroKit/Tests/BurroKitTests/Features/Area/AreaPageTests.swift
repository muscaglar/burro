import XCTest

@testable import BurroKit

/// An area's page: what goes under which heading, and that every word and
/// every figure on it is one the API sent.
final class AreaPageTests: XCTestCase {
    /// Every piece of text the API sent about an area: each slot, label and
    /// name, as it came, and each slot of money with the pound sign the page adds.
    private func sent(_ data: AreaData) -> Set<String> {
        var sent: Set<String> = [data.area.name, data.area.borough]
        for neighbour in data.neighbours { sent.insert(neighbour.name) }
        for fact in data.facts {
            sent.insert(fact.label)
            for source in fact.sources { sent.insert(source.name) }
            for value in fact.slots.values {
                sent.insert(value)
                sent.insert("£\(value)")
            }
            if let lower = fact.slots["lower"], let upper = fact.slots["upper"] {
                sent.insert("£\(lower) to £\(upper)")
            }
        }
        for feature in Answers.meta.features { sent.insert(feature.label) }
        for tag in Answers.meta.tags { sent.insert(tag.label) }
        return sent
    }

    /// The names the page gives a row when the fact has none of its own. They are copy.
    private let named: Set<String> = ["Nearest station", "Station within a short walk"]

    @MainActor
    func test_an_area_page_shows_only_what_the_api_sent() {
        XCTAssertEqual(AreaFixtures.slugs.count, 24)
        for slug in AreaFixtures.slugs {
            let page = AreaFixtures.page(slug)
            let sent = sent(Answers.profile(slug))

            let made = page.said.filter { !sent.contains($0) && !named.contains($0) }

            XCTAssertEqual(made, [], slug)
            XCTAssertGreaterThan(page.said.count, 20, slug)
        }
    }

    @MainActor
    func test_every_figure_on_the_page_is_a_slot_of_a_fact_as_the_api_formatted_it() {
        for slug in AreaFixtures.slugs {
            let data = Answers.profile(slug)
            let page = AreaFixtures.page(slug)
            var slots: Set<String> = []
            for fact in data.facts {
                for value in fact.slots.values { slots.formUnion([value, "£\(value)"]) }
                if let lower = fact.slots["lower"], let upper = fact.slots["upper"] {
                    slots.insert("£\(lower) to £\(upper)")
                }
            }
            let rows = page.stationRows + page.rentRows + page.buyRows
                + page.measured.flatMap { page.rows(of: $0) } + page.tagRows

            let figures = rows.flatMap(\.columns).map(\.value)

            XCTAssertEqual(figures.filter { !slots.contains($0) }, [], slug)
            XCTAssertTrue(figures.contains { $0.contains(where: \.isNumber) }, slug)
        }
    }

    @MainActor
    func test_every_figure_ends_in_its_source_and_its_date() {
        let page = AreaFixtures.page("farrowmere")
        let rows = page.stationRows + page.rentRows + page.buyRows
            + page.measured.flatMap { page.rows(of: $0) } + page.tagRows

        XCTAssertEqual(rows.count, 1 + 6 + 4 + 23 + 12)
        for row in rows where row.noFigure == nil {
            XCTAssertFalse(row.sources.isEmpty, row.name)
            XCTAssertTrue(row.sourceWords?.hasPrefix("Source: Synthetic test data. Data from ") ?? false, row.name)
            XCTAssertTrue(row.sourceWords?.hasSuffix("Made-up data") ?? false, row.name)
        }
        XCTAssertEqual(
            page.rentRows.first?.sourceWords, "Source: Synthetic test data. Data from August 2026. Made-up data")
        XCTAssertEqual(
            SourceLines.words(for: page.named.map { [$0] } ?? []),
            "Source: Synthetic test data. Data from 23 September 2026. Made-up data")
    }

    @MainActor
    func test_the_facts_are_grouped_by_what_they_are_about_in_the_order_the_website_shows_them() {
        let page = AreaFixtures.page("farrowmere")

        XCTAssertEqual(
            page.measured.map(\.dimension),
            [.stationAccess, .greenWater, .airNoise, .venuesCulture, .schools, .homes, .crime])
        XCTAssertEqual(
            page.measured.compactMap { $0.dimension.flatMap(AreaCopy.dimension) },
            ["Stations", "Green space and water", "Air and noise", "Venues and culture", "Schools", "Homes",
             "Recorded crime"])
        for group in page.measured {
            let features = Answers.meta.features.filter { $0.dimension == group.dimension }
            XCTAssertEqual(group.rows.map(\.label), features.map(\.label))
        }
        XCTAssertEqual(page.tags.map(\.label), Answers.meta.tags.map(\.label))
    }

    @MainActor
    func test_cost_is_a_row_for_each_kind_of_home_named_by_its_kind() {
        let page = AreaFixtures.page("farrowmere")

        XCTAssertEqual(
            page.rent.map(\.key),
            ["rent.room", "rent.studio", "rent.bed_1", "rent.bed_2", "rent.bed_3", "rent.bed_4plus"])
        XCTAssertEqual(page.buy.map(\.key), ["buy.flat", "buy.terraced", "buy.semi_detached", "buy.detached"])
        let studio = page.rentRows[1]
        XCTAssertEqual(studio.name, "studio")
        XCTAssertEqual(
            studio.columns,
            [
                FactColumn(name: "Range", value: "£775 to £1,025"),
                FactColumn(name: "Middle", value: "£875"),
                FactColumn(name: "As of", value: "August 2026"),
                FactColumn(name: "Confidence", value: "medium"),
            ])
    }

    @MainActor
    func test_an_area_with_no_cost_figure_has_no_cost_row() {
        let page = AreaFixtures.page("ostrel-vale")

        XCTAssertEqual(page.rentRows, [])
        XCTAssertEqual(page.buyRows, [])
        XCTAssertFalse(page.said.contains { $0.hasPrefix("£") })
    }

    @MainActor
    func test_the_nearest_station_comes_first_and_is_named_by_what_it_is() {
        let page = AreaFixtures.page("pellam-cross")

        XCTAssertEqual(page.stations.map(\.template), [.station, .stationNearby])
        XCTAssertEqual(page.stationRows.map(\.name), ["Nearest station", "Station within a short walk"])
        XCTAssertEqual(page.stationRows.first?.columns.map(\.name), ["Station", "Minutes on foot", "Lines"])
    }

    @MainActor
    func test_every_feature_of_the_release_has_a_row_and_one_with_no_figure_says_so() throws {
        let page = AreaFixtures.page("alderwick")
        let air = try XCTUnwrap(page.measured.first { $0.dimension == .airNoise })

        let rows = page.rows(of: air)

        XCTAssertEqual(page.measured.flatMap(\.rows).count, Answers.meta.features.count)
        let missing = try XCTUnwrap(rows.first { $0.noFigure != nil })
        XCTAssertEqual(missing.noFigure, "No figure in this data")
        XCTAssertEqual(missing.columns, [])
        XCTAssertEqual(missing.sources, [])
        XCTAssertNil(missing.sourceWords)
        XCTAssertEqual(missing.name, Answers.meta.features.first { $0.featureId == .airNo2 }?.label)
    }

    @MainActor
    func test_a_tag_that_was_not_worked_out_says_so() throws {
        let page = AreaFixtures.page("gorsebeck")

        let missing = try XCTUnwrap(page.tagRows.first { $0.noFigure != nil })

        XCTAssertEqual(page.tagRows.count, Answers.meta.tags.count)
        XCTAssertEqual(missing.noFigure, "Not worked out in this data")
        XCTAssertEqual(missing.name, Answers.meta.tags.first { $0.tagId == .historicCharacter }?.label)
    }

    @MainActor
    func test_an_area_the_data_does_not_rank_is_shown_with_what_is_known_of_it() {
        let page = AreaFixtures.page("grapnel-dock")

        XCTAssertFalse(page.rankable)
        XCTAssertEqual(page.name, "Grapnel Dock")
        XCTAssertFalse(page.stationRows.isEmpty)
        XCTAssertEqual(page.neighbours.count, 2)
    }

    @MainActor
    func test_the_name_and_the_borough_are_the_facts_and_carry_their_source() {
        let page = AreaFixtures.page("farrowmere")

        XCTAssertEqual(page.name, "Farrowmere")
        XCTAssertEqual(page.borough, "Quillhaven")
        XCTAssertEqual(page.named?.kind, .area)
        XCTAssertEqual(page.area, AreaFixtures.farrowmere)
        XCTAssertEqual(page.neighbours.map(\.name), ["Cindermoor", "Dulcimer Green", "Sedgewater Marsh"])
        XCTAssertEqual(page.sources.map(\.name), ["Synthetic test data"])
        XCTAssertEqual(page.releaseId, "syn-2026-09-23-01")
        XCTAssertTrue(page.synthetic)
    }

    @MainActor
    func test_what_is_served_with_no_fact_behind_it_is_not_shown() {
        // Whether a station is step-free, an area's other names, its position, a feature's
        // coverage and a tag's raw score have no source and no date. The page has no room for one.
        let fields = Mirror(reflecting: AreaFixtures.page("farrowmere")).children.compactMap(\.label)

        XCTAssertEqual(
            fields,
            ["area", "rankable", "releaseId", "synthetic", "named", "neighbours", "stations", "rent", "buy",
             "measured", "tags"])
        XCTAssertEqual(
            Mirror(reflecting: AreaFixtures.page("farrowmere").measured[0].rows[0]).children.compactMap(\.label),
            ["label", "fact", "kind", "key"])
    }

    @MainActor
    func test_recorded_crime_carries_its_caveat_word_for_word() throws {
        let page = AreaFixtures.page("farrowmere")
        let crime = try XCTUnwrap(page.measured.first { $0.dimension == .crime })
        let contract = try Repository.text(Repository.root.appendingPathComponent("docs/design/contract.md"))

        let rows = page.rows(of: crime)

        XCTAssertEqual(rows.count, 2)
        for row in rows {
            XCTAssertEqual(row.caveat, "Recorded crime depends on what is reported, and locations are approximate.")
        }
        XCTAssertTrue(contract.contains(AreaCopy.crimeCaveat))
        XCTAssertEqual(page.measured.last?.dimension, .crime)
        XCTAssertNil(page.stationRows.first?.caveat)
        for word in ["safe", "unsafe", "danger"] {
            XCTAssertFalse(page.said.contains { $0.lowercased().contains(word) }, word)
        }
    }

    @MainActor
    func test_a_code_this_build_does_not_know_is_left_out_and_never_shown_as_the_code() throws {
        let known = try XCTUnwrap(AreaFixtures.page("farrowmere").stations.first)
        let unknown = Fact(
            factId: known.factId, areaId: known.areaId, kind: known.kind, key: known.key, label: known.label,
            template: .unlisted("station_by_boat"), slots: known.slots, numbers: [], names: [],
            sources: known.sources, asOf: known.asOf, synthetic: true)

        XCTAssertNil(FactRow(unknown))
        XCTAssertNil(AreaCopy.dimension(.unlisted("broadband")))
        XCTAssertNil(AreaCopy.kind(.unlisted("station_by_boat")))
    }

    @MainActor
    func test_a_fact_of_a_search_has_no_row_on_an_areas_page() {
        let journey = AreaFixtures.journey(to: "Cindermoor Works")

        XCTAssertNil(FactRow(journey))
        XCTAssertNil(FactLayout.columns(of: journey))
    }

    @MainActor
    func test_with_no_list_of_features_in_hand_the_figures_the_area_has_are_still_shown() {
        let data = Answers.profile("farrowmere")

        let page = AreaPage(data, release: AreaFixtures.release, features: [], tags: [])

        XCTAssertEqual(page.measured.count, 1)
        XCTAssertNil(page.measured.first?.dimension)
        XCTAssertEqual(page.measured.first?.rows.count, data.facts.filter { $0.kind == .feature }.count)
        XCTAssertEqual(page.tags.count, data.facts.filter { $0.kind == .tag }.count)
    }

    func test_a_date_is_written_out_and_anything_else_is_shown_as_it_came() {
        XCTAssertEqual(ReadableDate.words("2026-08"), "August 2026")
        XCTAssertEqual(ReadableDate.words("2026-09-23"), "23 September 2026")
        XCTAssertEqual(ReadableDate.words("2026-09-03"), "3 September 2026")
        XCTAssertEqual(ReadableDate.words("2026-09-23T10:00:00Z"), "23 September 2026")
        XCTAssertEqual(ReadableDate.words("2026-09-23T10:00:00.250Z"), "23 September 2026")
        XCTAssertEqual(ReadableDate.words("2025"), "2025")
        XCTAssertEqual(ReadableDate.words("2024-10 to 2026-09"), "2024-10 to 2026-09")
        XCTAssertEqual(ReadableDate.words("2026-13"), "2026-13")
        XCTAssertEqual(ReadableDate.words("2026-02-30"), "2026-02-30")
        XCTAssertEqual(ReadableDate.words("2026-09-23T25:00:00Z"), "2026-09-23T25:00:00Z")
        XCTAssertEqual(ReadableDate.words("23/09/2026"), "23/09/2026")
        XCTAssertEqual(ReadableDate.words(""), "")
    }

    func test_one_line_is_given_for_each_source_and_date_however_many_facts_share_them() {
        let facts = Answers.profile("farrowmere").facts

        let lines = SourceLines.of(facts)

        XCTAssertEqual(Set(lines.map(\.sourceId)), ["synthetic"])
        XCTAssertEqual(lines.count, Set(facts.map(\.asOf)).count)
        XCTAssertEqual(Set(lines.map(\.id)).count, lines.count)
        XCTAssertNil(SourceLines.words(for: []))
    }

    func test_the_words_of_the_page_are_the_websites_word_for_word() throws {
        let content = Repository.root.appendingPathComponent("apps/web/src/content")
        let area = try Repository.text(content.appendingPathComponent("area.ts"))
        let facts = try Repository.text(content.appendingPathComponent("facts.ts"))
        let labels = try Repository.text(content.appendingPathComponent("labels.ts"))
        let search = try Repository.text(content.appendingPathComponent("search.ts"))

        for words in [
            AreaCopy.borough, AreaCopy.notRanked, AreaCopy.Where.title, AreaCopy.Where.neighbours,
            AreaCopy.Where.noNeighbours, AreaCopy.Stations.title, AreaCopy.Stations.none, AreaCopy.Cost.title,
            AreaCopy.Cost.lead, AreaCopy.Cost.rent, AreaCopy.Cost.buy, AreaCopy.Cost.noRent,
            AreaCopy.Cost.noPrice, AreaCopy.Measured.title, AreaCopy.Measured.lead, AreaCopy.Measured.noFigure,
            AreaCopy.Tags.title, AreaCopy.Tags.lead, AreaCopy.Tags.noFigure, AreaCopy.Sources.title,
            AreaCopy.Sources.lead, AreaCopy.Sources.methods, AreaCopy.Source.source,
        ] {
            XCTAssertTrue(area.contains("\"\(words)\""), words)
        }
        for words in [
            AreaCopy.Column.value, AreaCopy.Column.standing, AreaCopy.Column.segment, AreaCopy.Column.range,
            AreaCopy.Column.median, AreaCopy.Column.asOf, AreaCopy.Column.confidence, AreaCopy.Column.station,
            AreaCopy.Column.walk, AreaCopy.Column.lines, AreaCopy.Column.name, AreaCopy.Column.borough,
            AreaCopy.Column.to,
        ] + TemplateId.allCases.compactMap(AreaCopy.kind) {
            XCTAssertTrue(facts.contains("\"\(words)\""), words)
        }
        for words in Dimension.allCases.compactMap(AreaCopy.dimension) {
            XCTAssertTrue(labels.contains("\"\(words)\""), words)
        }
        XCTAssertEqual(Dimension.allCases.compactMap(AreaCopy.dimension).count, Dimension.allCases.count)
        XCTAssertEqual(Set(AreaPage.dimensions), Set(Dimension.allCases))
        for words in [
            AreaCopy.Source.dataFrom, AreaCopy.Source.madeUp, AreaCopy.InSearch.reasons,
            AreaCopy.InSearch.tradeOff, AreaCopy.InSearch.noTradeOff, AreaCopy.InSearch.byModel,
        ] {
            XCTAssertTrue(search.contains("\"\(words)\""), words)
        }
        XCTAssertTrue(search.contains("Where ${area} is among the areas of this data"))
        XCTAssertEqual(AreaCopy.Where.picture(of: "Farrowmere"), "Where Farrowmere is among the areas of this data")
    }

    func test_the_kinds_of_home_are_the_ones_the_website_lists_for_each_tenure() throws {
        let settings = try Repository.text(
            Repository.root.appendingPathComponent("apps/web/src/content/settings.ts"))

        XCTAssertTrue(
            settings.contains(
                "rent: [" + AreaPage.rented.map { "\"\($0.rawValue)\"" }.joined(separator: ", ") + "]"))
        XCTAssertTrue(
            settings.contains(
                "buy: [" + AreaPage.bought.map { "\"\($0.rawValue)\"" }.joined(separator: ", ") + "]"))
        XCTAssertEqual(Set(AreaPage.rented + AreaPage.bought), Set(Segment.allCases))
    }
}
