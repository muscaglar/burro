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
                + page.measured.flatMap { page.rows(of: $0) }

            let figures = rows.flatMap(\.columns).map(\.value)

            XCTAssertEqual(figures.filter { !slots.contains($0) }, [], slug)
            XCTAssertTrue(figures.contains { $0.contains(where: \.isNumber) }, slug)
            // The band of a vibe is the one its fact holds, and no other.
            for vibe in page.vibes {
                XCTAssertEqual(vibe.shown.placed?.band, vibe.fact?.slots["band"].flatMap { Int($0) }, slug)
            }
        }
    }

    @MainActor
    func test_every_figure_ends_in_its_source_and_its_date() {
        let page = AreaFixtures.page("farrowmere")
        let rows = page.stationRows + page.rentRows + page.buyRows
            + page.measured.flatMap { page.rows(of: $0) }

        XCTAssertEqual(rows.count, 1 + 6 + 4 + 40)
        XCTAssertEqual(page.vibes.count, 11)
        for vibe in page.vibes {
            XCTAssertEqual(vibe.shown.sources.map(\.name), ["Synthetic test data"], vibe.shown.name)
        }
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
            [.stationAccess, .greenWater, .airNoise, .venuesCulture, .services, .schools, .homes, .crime])
        XCTAssertEqual(
            page.measured.compactMap { $0.dimension.flatMap(AreaCopy.dimension) },
            ["Stations", "Green space and water", "Air and noise", "Venues and culture",
             "Shops and services", "Schools", "Homes", "Recorded crime"])
        for group in page.measured {
            let features = Answers.meta.features.filter { $0.dimension == group.dimension }
            XCTAssertEqual(group.rows.map(\.label), features.map(\.label))
        }
    }

    @MainActor
    func test_the_vibes_stand_in_the_lists_the_api_puts_them_in_and_in_its_order() {
        let data = Answers.profile("farrowmere")
        let page = AreaFixtures.page("farrowmere")

        XCTAssertEqual(page.vibes(in: .scales).map(\.shown.tagId), data.portrait.scales.map(\.tagId))
        XCTAssertEqual(page.vibes(in: .more).map(\.shown.tagId), data.portrait.more.map(\.tagId))
        XCTAssertEqual(page.vibes(in: .less).map(\.shown.tagId), data.portrait.less.map(\.tagId))
        XCTAssertEqual(page.vibes(in: .others).map(\.shown.tagId), data.portrait.others.map(\.tagId))
        XCTAssertEqual(page.vibes(in: .unplaced), [])
        XCTAssertEqual(
            page.vibes.map(\.shown.tagId),
            [
                .homes, .pace, .builtAge, .streetCharacter, .familyAmenities, .quietResidential, .foodie,
                .parksCloseBy, .everydayOnFoot, .leafy, .villageFeel,
            ])
        XCTAssertEqual(
            AreaPage.VibeList.allCases.map(AreaCopy.Portrait.title),
            ["On a scale", "More than most here", "Less than most here", "Also placed", "Burro cannot place"])
    }

    @MainActor
    func test_a_vibe_is_its_name_its_band_of_five_and_what_the_band_rests_on() throws {
        let page = AreaFixtures.page("farrowmere")
        let homes = try XCTUnwrap(page.vibes.first { $0.shown.tagId == .homes })
        let leafy = try XCTUnwrap(page.vibes.first { $0.shown.tagId == .leafy })
        let fact = try XCTUnwrap(homes.fact)

        // A scale is named by the API, and so are its two ends.
        XCTAssertEqual(homes.shown.name, "Homes")
        XCTAssertEqual([homes.shown.low, homes.shown.high], ["Houses", "Flats"])
        XCTAssertEqual(homes.shown.placed, Placed(fact))
        XCTAssertEqual(homes.shown.band, "band \(fact.slots["band"] ?? "") of 5")
        // A band that rests on part of a recipe says so, in the API's own clause.
        XCTAssertEqual(fact.slots["known"], "2")
        XCTAssertEqual(fact.slots["parts"], "3")
        XCTAssertEqual(homes.shown.restsOn, fact.slots["partly"])
        XCTAssertEqual(homes.shown.restsOn, "Worked out from 2 of its 3 parts, 75 of 100 by weight.")
        // One that rests on the whole of its recipe says nothing of it.
        XCTAssertEqual(leafy.fact?.slots["known"], leafy.fact?.slots["parts"])
        XCTAssertNil(leafy.shown.restsOn)
        // A vibe that runs one way is counted from least to most.
        XCTAssertEqual([leafy.shown.low, leafy.shown.high], ["least", "most"])
        // It is a band in words, and never a score or a percentage.
        for vibe in page.vibes {
            XCTAssertFalse(vibe.shown.reads.contains("%"), vibe.shown.name)
            XCTAssertTrue(vibe.shown.reads.contains(" of 5"), vibe.shown.name)
            XCTAssertNotNil(vibe.shown.plainly, vibe.shown.name)
        }
    }

    @MainActor
    func test_a_mixed_area_is_said_to_vary_and_is_never_put_at_a_point() throws {
        let page = AreaFixtures.page("sable-reach")
        let homes = try XCTUnwrap(page.vibes.first { $0.shown.tagId == .homes })

        XCTAssertEqual(homes.fact?.template, .vibeRange)
        XCTAssertEqual(homes.shown.placed, Placed(band: 4, spreadLow: 3, spreadHigh: 5))
        XCTAssertEqual(homes.shown.plainly, "varies within this area")
        XCTAssertEqual(homes.shown.band, "varies within this area, from band 3 to band 5 of 5")
        XCTAssertEqual((1...5).filter { homes.shown.placed?.fills($0) == true }, [3, 4, 5])
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
                FactColumn(name: "Confidence", value: "high"),
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
    func test_a_vibe_that_cannot_place_an_area_says_so_and_is_never_put_in_the_middle() throws {
        let page = AreaFixtures.page("otterby-fields")

        let unplaced = page.vibes(in: .unplaced)

        XCTAssertEqual(page.vibes.count, Answers.meta.tags.count)
        XCTAssertEqual(unplaced.count, 10)
        XCTAssertEqual(page.vibes(in: .scales).map(\.shown.tagId), [.homes])
        for vibe in unplaced {
            XCTAssertNil(vibe.shown.placed, vibe.shown.name)
            XCTAssertNil(vibe.shown.plainly, vibe.shown.name)
            XCTAssertEqual(vibe.shown.band, "Burro cannot place this area on it", vibe.shown.name)
            XCTAssertEqual(vibe.fact?.template, .vibeUnknown, vibe.shown.name)
            // The release holds enough of each recipe: it is this area that has too few figures.
            XCTAssertFalse(vibe.shown.notInData, vibe.shown.name)
            XCTAssertNil(vibe.shown.held, vibe.shown.name)
            XCTAssertFalse(vibe.shown.reads.contains("band "), vibe.shown.name)
        }
    }

    @MainActor
    func test_a_vibe_the_data_holds_too_little_of_says_what_it_waits_on() throws {
        let preview: MetaData = try Recorded.data(.getMeta, "preview/meta")
        let data: AreaData = try Recorded.data(.getArea, "preview/area-alderwick")
        let release = Meta(
            releaseId: preview.releaseId, engineVersion: preview.engineVersion, synthetic: preview.synthetic,
            preview: preview.preview)

        let page = AreaPage(
            data, release: release, features: preview.features, tags: preview.tags, recipes: preview.recipes)
        let leafy = try XCTUnwrap(page.vibes.first { $0.shown.tagId == .leafy })
        let held = try XCTUnwrap(preview.recipes.first { $0.tagId == .leafy })

        XCTAssertTrue(page.preview)
        XCTAssertFalse(held.placed)
        XCTAssertEqual(leafy.list, .unplaced)
        XCTAssertTrue(leafy.shown.notInData)
        XCTAssertNil(leafy.shown.placed)
        // Each part the data does not carry is named as the API names it, with its share of the recipe.
        XCTAssertEqual(leafy.shown.waitsOn, held.waitsOn.map { "\($0.label), \($0.hundredths) of 100" })
        XCTAssertEqual(
            leafy.shown.waitsOn,
            ["Land that is residential garden, 40 of 100", "Land that is woodland, 30 of 100"])
        XCTAssertEqual(
            leafy.shown.held, "This data holds 30 of 100 of its recipe. An area needs 60 of 100 to be placed.")
        XCTAssertTrue(leafy.shown.reads.contains("It waits on: Land that is residential garden, 40 of 100;"))
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
        XCTAssertFalse(page.preview)
    }

    @MainActor
    func test_what_is_served_with_no_fact_behind_it_is_not_shown() {
        // Whether a station is step-free, an area's other names, its position, a feature's
        // coverage and a tag's raw score have no source and no date. The page has no room for one.
        let fields = Mirror(reflecting: AreaFixtures.page("farrowmere")).children.compactMap(\.label)

        XCTAssertEqual(
            fields,
            ["area", "rankable", "releaseId", "synthetic", "preview", "named", "neighbours", "stations",
             "rent", "buy", "measured", "vibes"])
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

        XCTAssertEqual(rows.count, 4)
        for row in rows {
            XCTAssertEqual(
                row.caveats, ["Recorded crime depends on what is reported, and locations are approximate."])
        }
        XCTAssertTrue(contract.contains(AreaCopy.crimeCaveat))
        XCTAssertEqual(page.measured.last?.dimension, .crime)
        XCTAssertEqual(page.stationRows.first?.caveats, [])
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
        // A vibe the release does not name is left out: nothing can be said of it.
        XCTAssertEqual(page.vibes, [])
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
            AreaCopy.Portrait.title, AreaCopy.Sources.title,
            AreaCopy.Sources.lead, AreaCopy.Sources.methods, AreaCopy.Source.source,
        ] + AreaPage.VibeList.allCases.map(AreaCopy.Portrait.title) {
            XCTAssertTrue(area.contains("\"\(words)\""), words)
        }
        // Why a vibe cannot place an area, of this area alone and of every area.
        for words in [AreaCopy.Portrait.unplacedWhy, AreaCopy.Portrait.notInData] {
            XCTAssertTrue(Website.joined(area).contains("\"\(words)\""), words)
        }
        for words in [
            AreaCopy.Column.value, AreaCopy.Column.standing, AreaCopy.Column.segment, AreaCopy.Column.range,
            AreaCopy.Column.median, AreaCopy.Column.asOf, AreaCopy.Column.confidence, AreaCopy.Column.station,
            AreaCopy.Column.walk, AreaCopy.Column.lines, AreaCopy.Column.name, AreaCopy.Column.borough,
            AreaCopy.Column.to, AreaCopy.Column.middleOfAll, AreaCopy.Column.soldIn, AreaCopy.Column.band,
            AreaCopy.Column.bands, AreaCopy.Column.ends, AreaCopy.Column.compared, AreaCopy.Column.partsDated,
            AreaCopy.Column.partsKnown, AreaCopy.Column.parts, AreaCopy.Column.share, AreaCopy.oneNumber,
            VibeCopy.cannotPlace,
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
