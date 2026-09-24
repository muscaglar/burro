import XCTest

@testable import BurroKit

/// The map, and the table that says everything the map does.
///
/// Colour is never the only signal: a rank is a number in a pin, a fit is a
/// figure on the area, and an area with no rank is marked with a pattern and
/// given its reason in words.
final class ResultsMapTests: XCTestCase {
    private let ground = Results.Ground(Answers.geometry)
    private let square = Results.Outline(
        areaId: "a", part: 0,
        outer: [
            LonLat(longitude: 0, latitude: 0), LonLat(longitude: 0.02, latitude: 0),
            LonLat(longitude: 0.02, latitude: 0.02), LonLat(longitude: 0, latitude: 0.02),
            LonLat(longitude: 0, latitude: 0),
        ],
        holes: [
            [
                LonLat(longitude: 0.008, latitude: 0.008), LonLat(longitude: 0.012, latitude: 0.008),
                LonLat(longitude: 0.012, latitude: 0.012), LonLat(longitude: 0.008, latitude: 0.012),
                LonLat(longitude: 0.008, latitude: 0.008),
            ]
        ])

    // MARK: - The outlines and the camera

    func test_every_area_of_the_geometry_is_drawn_as_the_api_sent_it() {
        XCTAssertEqual(ground.outlines.count, Answers.geometry.features.count)
        XCTAssertEqual(Set(ground.outlines.map(\.areaId)), Set(Answers.areas.map(\.areaId)))
        for (outline, feature) in zip(ground.outlines, Answers.geometry.features) {
            guard case .polygon(let rings) = feature.geometry.coordinates else { return XCTFail() }
            XCTAssertEqual(outline.outer, rings[0])
            XCTAssertEqual(outline.holes, Array(rings.dropFirst()))
        }
    }

    func test_an_area_drawn_as_several_shapes_keeps_every_one_and_a_ring_that_is_no_shape_is_left_out() throws {
        let one = [
            LonLat(longitude: 0, latitude: 0), LonLat(longitude: 1, latitude: 0), LonLat(longitude: 1, latitude: 1),
            LonLat(longitude: 0, latitude: 0),
        ]
        let line = [LonLat(longitude: 0, latitude: 0), LonLat(longitude: 1, latitude: 1)]
        let several = GeoFeature(
            type: "Feature", id: "a", properties: GeoProperties(areaId: "a"),
            geometry: Geometry(type: .multiPolygon, coordinates: .multiPolygon([[one], [one, one], [line]])))

        let outlines = Results.outlines(of: GeometryData(type: "FeatureCollection", features: [several]))

        XCTAssertEqual(outlines.map(\.part), [0, 1])
        XCTAssertEqual(outlines.map(\.holes.count), [0, 1])
        XCTAssertEqual(Set(outlines.map(\.id)).count, 2)
        XCTAssertEqual(Results.outlines(of: nil), [])
    }

    func test_the_camera_is_framed_on_the_areas_with_room_round_them_and_not_on_what_lies_under_them() throws {
        let bounds = try XCTUnwrap(Results.bounds(of: ground.outlines))
        let frame = try XCTUnwrap(ground.whole)

        // The made-up city stands in open sea, near where the equator meets the meridian.
        XCTAssertEqual(bounds.west, -0.05566, accuracy: 1e-6)
        XCTAssertEqual(bounds.east, 0.07484, accuracy: 1e-6)
        XCTAssertEqual(bounds.south, -0.026837, accuracy: 1e-6)
        XCTAssertEqual(bounds.north, 0.055694, accuracy: 1e-6)
        XCTAssertEqual(frame.centre.longitude, (bounds.west + bounds.east) / 2, accuracy: 1e-9)
        XCTAssertEqual(frame.centre.latitude, (bounds.south + bounds.north) / 2, accuracy: 1e-9)
        XCTAssertGreaterThan(frame.longitudeSpan, bounds.width)
        XCTAssertGreaterThan(frame.latitudeSpan, bounds.height)
        XCTAssertLessThan(frame.longitudeSpan, bounds.width * 1.5)
        for outline in ground.outlines {
            for corner in outline.outer { XCTAssertTrue(Results.shows(frame, corner, inset: 0)) }
        }
        XCTAssertNil(Results.Ground.none.whole)
        XCTAssertTrue(Results.Ground.none.isEmpty)
    }

    func test_the_camera_draws_in_and_out_by_a_press_and_is_held_to_the_city() throws {
        let whole = try XCTUnwrap(ground.whole)

        let closer = Results.zoomed(whole, by: 0.5, within: whole)
        var closest = whole
        var furthest = whole
        for _ in 0..<20 {
            closest = Results.zoomed(closest, by: 0.5, within: whole)
            furthest = Results.zoomed(furthest, by: 2, within: whole)
        }

        XCTAssertEqual(closer.longitudeSpan, whole.longitudeSpan / 2, accuracy: 1e-12)
        XCTAssertEqual(closer.centre, whole.centre)
        XCTAssertEqual(closest.longitudeSpan, whole.longitudeSpan / 16, accuracy: 1e-12)
        XCTAssertEqual(furthest.longitudeSpan, whole.longitudeSpan * 1.5, accuracy: 1e-12)
        XCTAssertEqual(Results.zoomed(whole, by: 0, within: whole), whole)
        XCTAssertEqual(Results.zoomed(whole, by: .nan, within: whole), whole)
    }

    func test_the_map_moves_to_a_chosen_area_only_when_it_is_out_of_sight() throws {
        let whole = try XCTUnwrap(ground.whole)
        let farrowmere = try XCTUnwrap(Answers.areas.first { $0.name == "Farrowmere" })
        let alderwick = try XCTUnwrap(Answers.areas.first { $0.name == "Alderwick" })
        let near = try XCTUnwrap(Results.frame(ofArea: farrowmere.areaId, in: ground.outlines))

        XCTAssertTrue(Results.shows(whole, farrowmere.centroid))
        XCTAssertTrue(Results.shows(near, farrowmere.centroid))
        XCTAssertFalse(Results.shows(near, alderwick.centroid))
        XCTAssertLessThan(near.longitudeSpan, whole.longitudeSpan)
        XCTAssertNil(Results.frame(ofArea: "syn-n9999", in: ground.outlines))
    }

    // MARK: - Which area a press falls in

    func test_a_press_on_the_map_chooses_the_area_it_falls_in_and_the_sea_chooses_none() {
        for area in Answers.areas {
            // The middle of each area of the made-up city is inside it.
            XCTAssertEqual(Results.area(at: area.centroid, in: ground.outlines), area.areaId, area.name)
        }
        XCTAssertNil(Results.area(at: LonLat(longitude: 0.5, latitude: 0.5), in: ground.outlines))
        XCTAssertNil(Results.area(at: LonLat(longitude: -0.3, latitude: 0), in: ground.outlines))
    }

    func test_a_hole_in_an_area_is_not_part_of_it() {
        XCTAssertTrue(Results.outline(square, holds: LonLat(longitude: 0.004, latitude: 0.004)))
        XCTAssertFalse(Results.outline(square, holds: LonLat(longitude: 0.01, latitude: 0.01)))
        XCTAssertFalse(Results.outline(square, holds: LonLat(longitude: 0.03, latitude: 0.01)))
        XCTAssertFalse(Results.ring([], holds: LonLat(longitude: 0, latitude: 0)))
    }

    // MARK: - Patterns

    func test_the_lines_of_a_pattern_lie_inside_the_area_and_round_its_holes() {
        let strokes = Results.lines(across: square, spacing: 0.002)

        XCTAssertGreaterThan(strokes.count, 10)
        for stroke in strokes {
            let middle = LonLat(
                longitude: (stroke.from.longitude + stroke.to.longitude) / 2,
                latitude: (stroke.from.latitude + stroke.to.latitude) / 2)
            XCTAssertTrue(Results.outline(square, holds: middle))
            // A line climbs to the east.
            XCTAssertLessThan(stroke.from.longitude, stroke.to.longitude)
            XCTAssertLessThan(stroke.from.latitude, stroke.to.latitude)
        }
        XCTAssertEqual(Results.lines(across: square, spacing: 0), [])
    }

    func test_the_dots_of_a_pattern_lie_inside_the_area_and_in_none_of_its_holes() {
        let dots = Results.dots(in: square, spacing: 0.002)

        XCTAssertGreaterThan(dots.count, 10)
        for dot in dots { XCTAssertTrue(Results.outline(square, holds: dot)) }
        XCTAssertEqual(Set(dots).count, dots.count)
        XCTAssertEqual(Results.dots(in: square, spacing: 0), [])
    }

    func test_an_area_is_given_a_few_marks_of_a_pattern_and_never_more_than_the_most() {
        XCTAssertGreaterThan(ground.spacing, 0)
        for outline in ground.outlines {
            let lines = Results.lines(across: outline, spacing: ground.spacing)
            let dots = Results.dots(in: outline, spacing: ground.spacing)
            XCTAssertGreaterThanOrEqual(lines.count, 3, outline.areaId)
            XCTAssertGreaterThanOrEqual(dots.count, 3, outline.areaId)
            XCTAssertLessThanOrEqual(lines.count, Results.mostMarks * 2)
            XCTAssertLessThanOrEqual(dots.count, Results.mostMarks)
        }
        // However fine the pattern is asked for, an area is not covered in marks.
        XCTAssertLessThanOrEqual(Results.lines(across: square, spacing: 1e-7).count, Results.mostMarks * 2)
        XCTAssertLessThanOrEqual(Results.dots(in: square, spacing: 1e-7).count, Results.mostMarks)
    }

    // MARK: - What the map shows of a ranking

    @MainActor
    func test_each_area_is_filled_by_the_band_its_fit_falls_in() async throws {
        let app = try await ResultsApp.searched()
        let ranking = try XCTUnwrap(app.state.ranking)

        let fills = Results.fills(ranking)

        XCTAssertEqual(fills.count, 24)
        for score in ranking.scores {
            let band = try XCTUnwrap(fills[score.areaId]?.band)
            XCTAssertEqual(band, min(Int(score.score) / 20 + 1, 5))
            XCTAssertEqual(fills[score.areaId]?.pattern, Results.Pattern.none)
        }
        XCTAssertEqual(fills["syn-n0006"], Results.Fill(band: 5, pattern: .none))
        XCTAssertEqual(fills["syn-n0009"], Results.Fill(band: 0, pattern: .unranked))
        XCTAssertEqual(Results.bands.map(\.from), [0, 20, 40, 60, 80])
        XCTAssertEqual(Results.bands.map(\.to), [19, 39, 59, 79, 100])
        XCTAssertEqual(Tokens.Colour.mapBands.count, Results.bands.count)
    }

    @MainActor
    func test_the_first_ten_carry_their_rank_in_a_pin_and_every_ranked_area_carries_its_fit() async throws {
        let app = try await ResultsApp.searched()
        let ranking = try XCTUnwrap(app.state.ranking)

        let marks = app.mapped.marks

        XCTAssertEqual(marks.count, ranking.scores.count)
        XCTAssertEqual(marks.compactMap(\.pin), Array(1...10))
        XCTAssertEqual(marks.prefix(10).map(\.area.areaId), ranking.scores.prefix(10).map(\.areaId))
        XCTAssertTrue(marks.allSatisfy { $0.fit != nil })
        XCTAssertEqual(marks[0].fit, "Fit 80")
        XCTAssertEqual(marks[0].words, "Rank 1, Farrowmere, fit 80 of 100")
        XCTAssertEqual(marks[0].at, app.state.area("syn-n0006")?.centroid)
        XCTAssertEqual(marks[11].words, "Rank 12, \(marks[11].area.name), fit \(Results.fit(of: ranking.scores[11].score)) of 100")
        // A band is a colour. On every area that has one, the fit is there in figures as well.
        let banded = Set(app.mapped.regions.filter { $0.fill.band > 0 }.map(\.outline.areaId))
        XCTAssertEqual(banded, Set(marks.map(\.area.areaId)))
    }

    @MainActor
    func test_an_area_with_no_rank_is_marked_with_a_pattern_and_never_with_a_band() async throws {
        let app = try await ResultsApp.searched()
        app.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        await app.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))
        let ranking = try XCTUnwrap(app.state.ranking)

        let mapped = app.mapped

        for region in mapped.regions {
            let areaId = region.outline.areaId
            if ranking.filtered.contains(where: { $0.areaId == areaId }) {
                XCTAssertEqual(region.fill, Results.Fill(band: 0, pattern: .filtered))
            } else if ranking.unranked.contains(where: { $0.areaId == areaId }) {
                XCTAssertEqual(region.fill, Results.Fill(band: 0, pattern: .unranked))
            } else {
                XCTAssertGreaterThan(region.fill.band, 0)
            }
        }
        // Every line is in an area a limit left out, and every dot in one that is not ranked.
        let filtered = Set(ranking.filtered.map(\.areaId))
        let unranked = Set(ranking.unranked.map(\.areaId))
        XCTAssertFalse(mapped.strokes.isEmpty)
        XCTAssertFalse(mapped.dots.isEmpty)
        for stroke in mapped.strokes {
            let middle = LonLat(
                longitude: (stroke.from.longitude + stroke.to.longitude) / 2,
                latitude: (stroke.from.latitude + stroke.to.latitude) / 2)
            XCTAssertTrue(filtered.contains(Results.area(at: middle, in: app.ground.outlines) ?? ""))
        }
        for dot in mapped.dots {
            XCTAssertTrue(unranked.contains(Results.area(at: dot, in: app.ground.outlines) ?? ""))
        }
        XCTAssertGreaterThan(mapped.dotRadius, 0)
    }

    @MainActor
    func test_the_legend_gives_each_band_in_figures_and_each_pattern_in_words() async throws {
        let app = try await ResultsApp.searched()

        XCTAssertEqual(
            app.mapped.legend.map(\.words),
            [
                "Fit 80 to 100", "Fit 60 to 79", "Fit 40 to 59", "Fit 20 to 39", "Fit 0 to 19",
                "Left out by a limit you set. Shown with lines.",
                "Not ranked. Shown with dots.",
                "A numbered pin is the rank of one of the first ten.",
                "Each ranked area is marked with its fit.",
            ])
        XCTAssertEqual(
            app.mapped.legend.map(\.sign),
            [.band(5), .band(4), .band(3), .band(2), .band(1), .lines, .dots, .pin, .fit])
    }

    @MainActor
    func test_a_map_of_a_whole_city_marks_the_first_forty_and_the_area_that_is_chosen() async throws {
        let app = try await ResultsApp()
        var state = app.state
        // A release of two hundred areas, made of the recorded one, to see what a large one does.
        let many = (0..<200).map { at -> AreaSummary in
            let area = Answers.areas[at % Answers.areas.count]
            return AreaSummary(
                areaId: "syn-x\(at)", slug: "x\(at)", name: area.name, borough: area.borough,
                centroid: area.centroid, rankable: true)
        }
        state.areas = many
        state.ranking = Ranking(
            scores: many.enumerated().map { Score(areaId: $1.areaId, score: Double(200 - $0) / 2) },
            ranked: [], filtered: [], unranked: [], emptySpec: false)

        XCTAssertEqual(Results.marks(of: state).count, Results.mostFitMarks)
        state.selectedId = "syn-x150"
        let marks = Results.marks(of: state)

        XCTAssertEqual(marks.count, Results.mostFitMarks + 1)
        XCTAssertEqual(marks.last?.area.areaId, "syn-x150")
        XCTAssertEqual(marks.last?.selected, true)
        XCTAssertNil(marks.last?.pin)
        XCTAssertEqual(marks.compactMap(\.pin).count, Results.pins)
    }

    // MARK: - The list and the map, in step both ways

    @MainActor
    func test_an_area_chosen_on_the_map_is_marked_in_the_list_and_brought_into_view() async throws {
        let app = try await ResultsApp.searched()

        app.hands.choose(onMap: "syn-n0017")

        XCTAssertEqual(app.state.selectedId, "syn-n0017")
        XCTAssertEqual(app.listed.cards.filter(\.selected).map(\.heading.name), ["Otterby Fields"])
        XCTAssertEqual(app.memory.bringIntoView, "syn-n0017")
        let chosen = try XCTUnwrap(app.mapped.chosen)
        XCTAssertEqual(chosen.area.name, "Otterby Fields")
        XCTAssertEqual(chosen.words, "Rank 2, fit 79 of 100")
        XCTAssertTrue(chosen.inList)
        XCTAssertFalse(chosen.beyondList)
        XCTAssertEqual(app.mapped.regions.last?.outline.areaId, "syn-n0017")
        XCTAssertEqual(app.mapped.regions.filter(\.selected).count, 1)
        XCTAssertEqual(app.mapped.marks.filter(\.selected).map(\.area.areaId), ["syn-n0017"])
        // It sends nothing.
        XCTAssertEqual(app.api.calls(to: .rank).count, 1)
    }

    @MainActor
    func test_an_area_chosen_in_the_list_is_marked_on_the_map_and_the_map_is_shown() async throws {
        let app = try await ResultsApp.searched()
        let card = app.listed.cards[2]
        app.memory.showing = .list
        app.memory.height = .full

        app.hands.showOnMap(card.area)

        XCTAssertEqual(app.state.selectedId, card.id)
        XCTAssertEqual(app.memory.showing, .map)
        XCTAssertEqual(app.memory.height, .half)
        XCTAssertEqual(app.mapped.chosen?.area, card.area)
        XCTAssertEqual(app.mapped.marks.first { $0.selected }?.pin, 3)
    }

    @MainActor
    func test_a_press_on_the_heading_of_a_card_marks_the_area_on_the_map_and_moves_nothing() async throws {
        let app = try await ResultsApp.searched()
        let card = app.listed.cards[6]
        app.memory.height = .full

        app.hands.choose(inList: card.area)

        XCTAssertEqual(app.state.selectedId, card.id)
        XCTAssertEqual(app.mapped.regions.last?.outline.areaId, card.id)
        XCTAssertEqual(app.mapped.regions.last?.selected, true)
        XCTAssertEqual(app.memory.showing, .map)
        XCTAssertEqual(app.memory.height, .full)
        XCTAssertNil(app.memory.bringIntoView)
        // A second press lets it go.
        app.hands.choose(inList: card.area)
        XCTAssertNil(app.state.selectedId)
    }

    @MainActor
    func test_a_press_on_the_sea_lets_the_chosen_area_go() async throws {
        let app = try await ResultsApp.searched()
        app.hands.choose(onMap: "syn-n0017")

        app.hands.choose(onMap: Results.area(at: LonLat(longitude: 0.5, latitude: 0.5), in: app.ground.outlines))

        XCTAssertNil(app.state.selectedId)
        XCTAssertNil(app.mapped.chosen)
        XCTAssertEqual(app.listed.cards.filter(\.selected), [])
    }

    @MainActor
    func test_an_area_with_no_rank_says_why_in_words_when_it_is_chosen() async throws {
        let app = try await ResultsApp.searched()
        app.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        await app.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))
        let left = try XCTUnwrap(app.state.ranking?.filtered.first)

        app.hands.choose(onMap: left.areaId)
        XCTAssertEqual(app.mapped.chosen?.words, "A journey is longer than a firm limit")
        XCTAssertEqual(app.mapped.chosen?.inList, false)
        app.hands.choose(onMap: "syn-n0009")

        XCTAssertEqual(app.mapped.chosen?.words, "Not ranked in this data")
        XCTAssertEqual(app.mapped.chosen?.area.name, "Grapnel Dock")
    }

    @MainActor
    func test_a_ranked_area_further_down_than_the_list_goes_says_that_it_is_not_in_the_list() async throws {
        let app = try await ResultsApp.searched()
        let last = try XCTUnwrap(app.state.ranking?.scores.last)

        app.hands.choose(onMap: last.areaId)

        XCTAssertEqual(app.mapped.chosen?.beyondList, true)
        XCTAssertEqual(app.mapped.chosen?.inList, false)
        XCTAssertEqual(app.mapped.chosen?.words, "Rank 22, fit \(Results.fit(of: last.score)) of 100")
        XCTAssertEqual(ResultsCopy.MapCard.notInList, "This area is not in the list.")
    }

    // MARK: - The table of every area

    @MainActor
    func test_everything_the_map_shows_is_in_the_table() async throws {
        let app = try await ResultsApp.searched()
        app.api.on(.rank, "rank-refined").on(.explainTop, "explanations-refined")
        await app.flow.applyEdits(Edits.placeMinutes("syn-p0021", 30))
        let mapped = app.mapped
        let rows = Dictionary(uniqueKeysWithValues: app.tabled.rows.map { ($0.area.areaId, $0) })

        // Every area on the map has a row.
        XCTAssertEqual(Set(mapped.regions.map(\.outline.areaId)), Set(rows.keys))
        for region in mapped.regions {
            let row = try XCTUnwrap(rows[region.outline.areaId])
            switch region.fill.pattern {
            case .none:
                // A band on the map is a fit in figures in the table, in the band the legend gives.
                let fit = try XCTUnwrap(row.fit)
                XCTAssertEqual(Results.bands[region.fill.band - 1].from...Results.bands[region.fill.band - 1].to ~= fit, true)
                XCTAssertEqual(row.status, "Ranked")
            case .filtered:
                XCTAssertEqual(row.status, "A journey is longer than a firm limit")
                XCTAssertNil(row.rank)
            case .unranked:
                XCTAssertEqual(row.status, "Not ranked in this data")
                XCTAssertNil(row.fit)
            }
        }
        // Every pin is a rank in the table.
        for mark in mapped.marks {
            let row = try XCTUnwrap(rows[mark.area.areaId])
            if let pin = mark.pin { XCTAssertEqual(row.rank, pin) }
            XCTAssertEqual(mark.fit, row.fit.map(ResultsCopy.Map.fitLabel))
            XCTAssertTrue(mark.words.contains(row.fitWords))
        }
    }

    @MainActor
    func test_the_table_is_in_rank_order_and_then_by_name() async throws {
        let app = try await ResultsApp.searched()

        let rows = app.tabled.rows

        XCTAssertEqual(rows.count, 24)
        XCTAssertEqual(rows.prefix(22).map(\.rank), (1...22).map(Optional.some))
        XCTAssertEqual(rows.suffix(2).map(\.area.name), ["Grapnel Dock", "Sedgewater Marsh"])
        XCTAssertEqual(rows[0].words, "Farrowmere, Quillhaven, Rank 1, Fit 80 of 100, Ranked")
        XCTAssertEqual(rows[23].words, "Sedgewater Marsh, \(rows[23].area.borough), Not ranked in this data")
        XCTAssertEqual(rows[23].rankWords, "None")
        XCTAssertEqual(rows[23].fitWords, "None")
        XCTAssertEqual(app.tabled.caption, "Every area, in order of fit and then by name")
    }

    @MainActor
    func test_with_no_boundaries_there_is_no_map_and_the_table_still_says_everything() async throws {
        let app = try await ResultsApp(StandIn.firstSearch().on(.getGeometry, "error-internal"))
        await app.flow.loadGeometry()
        await app.flow.submitText("leafy")

        XCTAssertTrue(app.state.geometryFailed)
        XCTAssertTrue(app.ground.isEmpty)
        XCTAssertEqual(app.mapped.regions, [])
        XCTAssertEqual(app.tabled.rows.count, 24)
        XCTAssertEqual(app.listed.cards.count, 20)
        XCTAssertEqual(
            ResultsCopy.Map.noGeometryHere,
            "The boundaries of the areas could not be loaded. The table says everything the map would.")
    }

    // MARK: - A picture with no map

    func test_the_small_picture_keeps_every_area_inside_it_with_north_up() throws {
        let bounds = try XCTUnwrap(Results.bounds(of: ground.outlines))
        let picture = Results.Projector(bounds: bounds, width: 160, height: 120, padding: 8)

        for outline in ground.outlines {
            for corner in outline.outer {
                let at = picture.place(corner)
                XCTAssertTrue((8.0 - 1e-9...152.0 + 1e-9).contains(at.x))
                XCTAssertTrue((8.0 - 1e-9...112.0 + 1e-9).contains(at.y))
            }
        }
        let north = picture.place(LonLat(longitude: 0, latitude: bounds.north))
        let south = picture.place(LonLat(longitude: 0, latitude: bounds.south))
        XCTAssertLessThan(north.y, south.y)
    }
}
