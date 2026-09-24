import XCTest

@testable import BurroKit

/// The small picture of where an area is: every area's outline, placed in one frame.
final class LocatorTests: XCTestCase {
    func test_every_area_of_the_release_has_an_outline_in_the_picture() {
        let outlines = Locator.outlines(of: Answers.geometry)

        XCTAssertEqual(Set(outlines.map(\.areaId)), Set(Answers.areas.map(\.areaId)))
        XCTAssertTrue(outlines.allSatisfy { !$0.rings.isEmpty })
    }

    func test_every_point_is_inside_the_frame_and_the_city_touches_its_padding() {
        let frame = Locator.frame
        let points = Locator.outlines(of: Answers.geometry).flatMap(\.rings).flatMap { $0 }

        XCTAssertFalse(points.isEmpty)
        for point in points {
            XCTAssertGreaterThanOrEqual(point.x, frame.padding - 0.001)
            XCTAssertLessThanOrEqual(point.x, frame.width - frame.padding + 0.001)
            XCTAssertGreaterThanOrEqual(point.y, frame.padding - 0.001)
            XCTAssertLessThanOrEqual(point.y, frame.height - frame.padding + 0.001)
        }
        // The city fills the room one way, and is centred the other.
        let across = (points.map(\.x).max() ?? 0) - (points.map(\.x).min() ?? 0)
        let up = (points.map(\.y).max() ?? 0) - (points.map(\.y).min() ?? 0)
        let fillsAcross = abs(across - (frame.width - 2 * frame.padding)) < 0.001
        let fillsUp = abs(up - (frame.height - 2 * frame.padding)) < 0.001
        XCTAssertTrue(fillsAcross || fillsUp)
    }

    func test_north_is_up_and_east_is_right() throws {
        let bounds = try XCTUnwrap(Locator.bounds(of: Answers.geometry))
        let place = Locator.projector(bounds, in: Locator.frame)

        let southWest = place(LonLat(longitude: bounds.west, latitude: bounds.south))
        let northEast = place(LonLat(longitude: bounds.east, latitude: bounds.north))

        XCTAssertLessThan(northEast.y, southWest.y)
        XCTAssertGreaterThan(northEast.x, southWest.x)
    }

    func test_with_no_outline_in_hand_there_is_no_picture() {
        let nothing = GeometryData(features: [])

        XCTAssertNil(Locator.bounds(of: nothing))
        XCTAssertEqual(Locator.outlines(of: nothing), [])
    }

    func test_a_shape_of_many_parts_keeps_every_part() {
        let square: [LonLat] = [
            LonLat(longitude: 0, latitude: 0), LonLat(longitude: 1, latitude: 0),
            LonLat(longitude: 1, latitude: 1), LonLat(longitude: 0, latitude: 1),
            LonLat(longitude: 0, latitude: 0),
        ]
        let island = square.map { LonLat(longitude: $0.longitude + 2, latitude: $0.latitude) }
        let data = GeometryData(features: [
            GeoFeature(
                id: "syn-n0001", properties: GeoProperties(areaId: "syn-n0001"),
                geometry: Geometry(type: .multiPolygon, coordinates: .multiPolygon([[square], [island]])))
        ])

        let outlines = Locator.outlines(of: data)

        XCTAssertEqual(outlines.first?.rings.count, 2)
        XCTAssertEqual(outlines.first?.rings.map(\.count), [5, 5])
    }

    func test_the_picture_is_named_for_a_person_who_cannot_see_it() {
        XCTAssertEqual(AreaCopy.Where.picture(of: "Farrowmere"), "Where Farrowmere is among the areas of this data")
    }
}
