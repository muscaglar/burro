import Foundation

// Where things are: the outline of each area, the box that holds them all,
// which area a point falls in, and the patterns that say an area has no rank.
//
// It is plain arithmetic on the positions the API sent, with no map library,
// so that it is tested on a Mac. The map draws what is worked out here.
//
// The patterns are worked out, not drawn: lines and dots are positions on the
// ground, as the website's are tiles of pixels made in code. No image is needed.

extension Results {
    /// One closed shape of an area: its outer edge, and any holes in it.
    struct Outline: Hashable, Sendable, Identifiable {
        let areaId: String
        /// Which shape of the area this is, for an area drawn as several.
        let part: Int
        let outer: [LonLat]
        let holes: [[LonLat]]

        var id: String { "\(areaId) \(part)" }

        /// Every ring of the shape, the outer one first.
        var rings: [[LonLat]] { [outer] + holes }
    }

    /// West and south, then east and north.
    struct Bounds: Hashable, Sendable {
        let west: Double
        let south: Double
        let east: Double
        let north: Double

        var width: Double { east - west }
        var height: Double { north - south }
        var centre: LonLat {
            LonLat(longitude: (west + east) / 2, latitude: (south + north) / 2)
        }
    }

    /// What the camera is asked to show: a centre, and how many degrees across and up.
    struct Frame: Hashable, Sendable {
        let centre: LonLat
        let longitudeSpan: Double
        let latitudeSpan: Double

        var bounds: Bounds {
            Bounds(
                west: centre.longitude - longitudeSpan / 2, south: centre.latitude - latitudeSpan / 2,
                east: centre.longitude + longitudeSpan / 2, north: centre.latitude + latitudeSpan / 2)
        }
    }

    /// A short straight line on the ground, for the pattern of lines.
    struct Stroke: Hashable, Sendable {
        let from: LonLat
        let to: LonLat
    }

    // MARK: - Outlines

    /// Every shape of every area, in the order the API gave them. A ring of
    /// fewer than three corners is no shape and is left out, and so is a
    /// position that is not a number.
    static func outlines(of geometry: GeometryData?) -> [Outline] {
        guard let geometry else { return [] }
        var found: [Outline] = []
        for feature in geometry.features {
            let polygons: [[[LonLat]]]
            switch feature.geometry.coordinates {
            case .polygon(let rings): polygons = [rings]
            case .multiPolygon(let many): polygons = many
            }
            for (part, rings) in polygons.enumerated() {
                let sound = rings.map { ring in ring.filter { $0.longitude.isFinite && $0.latitude.isFinite } }
                guard let outer = sound.first, outer.count >= 3 else { continue }
                found.append(
                    Outline(
                        areaId: feature.properties.areaId, part: part, outer: outer,
                        holes: sound.dropFirst().filter { $0.count >= 3 }))
            }
        }
        return found
    }

    /// The box that holds every shape. `nil` when there is nothing to hold.
    static func bounds(of outlines: [Outline]) -> Bounds? {
        var west = Double.infinity
        var south = Double.infinity
        var east = -Double.infinity
        var north = -Double.infinity
        for outline in outlines {
            for position in outline.outer {
                west = min(west, position.longitude)
                east = max(east, position.longitude)
                south = min(south, position.latitude)
                north = max(north, position.latitude)
            }
        }
        guard west <= east, south <= north else { return nil }
        return Bounds(west: west, south: south, east: east, north: north)
    }

    // MARK: - The camera

    /// The least a frame may span, in degrees, so that a single point still has a frame.
    static let leastSpan = 0.002

    /// The frame that shows the whole of a box, with room round it. The map
    /// is framed on the areas and never on what lies under them: the made-up
    /// city stands in open sea.
    static func frame(of bounds: Bounds, margin: Double = 0.15) -> Frame {
        Frame(
            centre: bounds.centre,
            longitudeSpan: max(bounds.width * (1 + 2 * margin), leastSpan),
            latitudeSpan: max(bounds.height * (1 + 2 * margin), leastSpan))
    }

    /// The frame that shows every area. `nil` when there is none to show.
    static func frame(of outlines: [Outline]) -> Frame? {
        bounds(of: outlines).map { frame(of: $0) }
    }

    /// The frame that shows one area, with the areas round it in view.
    static func frame(ofArea areaId: String, in outlines: [Outline]) -> Frame? {
        bounds(of: outlines.filter { $0.areaId == areaId }).map { frame(of: $0, margin: 1) }
    }

    /// A frame drawn in or out about its centre. It is never wider than the
    /// whole city with room to spare, nor narrower than a sixteenth of it.
    static func zoomed(_ frame: Frame, by factor: Double, within whole: Frame) -> Frame {
        guard factor.isFinite, factor > 0 else { return frame }
        let most = 1.5
        let least = 1.0 / 16
        func span(_ now: Double, of all: Double) -> Double {
            min(all * most, max(max(all * least, leastSpan), now * factor))
        }
        return Frame(
            centre: frame.centre,
            longitudeSpan: span(frame.longitudeSpan, of: whole.longitudeSpan),
            latitudeSpan: span(frame.latitudeSpan, of: whole.latitudeSpan))
    }

    /// True when a position is inside a frame, and not at its very edge.
    static func shows(_ frame: Frame, _ position: LonLat, inset: Double = 0.1) -> Bool {
        let box = frame.bounds
        let across = box.width * inset
        let up = box.height * inset
        return position.longitude >= box.west + across && position.longitude <= box.east - across
            && position.latitude >= box.south + up && position.latitude <= box.north - up
    }

    // MARK: - Which area a point is in

    /// True when a position is inside a ring, by counting the edges a line to the east crosses.
    static func ring(_ ring: [LonLat], holds position: LonLat) -> Bool {
        guard ring.count >= 3, var before = ring.last else { return false }
        var inside = false
        for corner in ring {
            let crosses = (corner.latitude > position.latitude) != (before.latitude > position.latitude)
            if crosses {
                let along = (position.latitude - corner.latitude) / (before.latitude - corner.latitude)
                let at = corner.longitude + along * (before.longitude - corner.longitude)
                if position.longitude < at { inside.toggle() }
            }
            before = corner
        }
        return inside
    }

    /// True when a position is inside a shape and in none of its holes.
    static func outline(_ outline: Outline, holds position: LonLat) -> Bool {
        ring(outline.outer, holds: position) && !outline.holes.contains { ring($0, holds: position) }
    }

    /// The area a position falls in. `nil` for a position in none: the sea, or a gap.
    static func area(at position: LonLat, in outlines: [Outline]) -> String? {
        outlines.first { outline($0, holds: position) }?.areaId
    }

    // MARK: - Patterns

    /// How far apart the lines and the dots of a pattern are, in degrees of
    /// latitude: about a fifth of the width of a usual area, so that an area
    /// of any release holds a few of each.
    static func patternSpacing(for outlines: [Outline]) -> Double {
        guard let box = bounds(of: outlines) else { return leastSpan }
        let areas = max(1, Set(outlines.map(\.areaId)).count)
        let squeeze = squeeze(at: box.centre.latitude)
        let ground = max(box.width * squeeze, leastSpan) * max(box.height, leastSpan)
        return max((ground / Double(areas)).squareRoot() / 5, leastSpan / 10)
    }

    /// How much narrower a degree of longitude is than one of latitude, at a latitude.
    static func squeeze(at latitude: Double) -> Double {
        max(cos(latitude * .pi / 180), 0.01)
    }

    /// The most lines, and the most dots, one area is given.
    static let mostMarks = 60

    /// Slanted lines across a shape, cut to its edge and round its holes.
    /// They climb to the east, as the website's do.
    static func lines(across outline: Outline, spacing: Double) -> [Stroke] {
        guard spacing > 0, let box = bounds(of: [outline]) else { return [] }
        let squeeze = squeeze(at: box.centre.latitude)
        // A line is every position where the latitude less the easting is one value.
        func offset(_ position: LonLat) -> Double { position.latitude - position.longitude * squeeze }
        let offsets = outline.outer.map(offset)
        guard let least = offsets.min(), let most = offsets.max(), most > least else { return [] }
        var step = spacing
        while (most - least) / step > Double(mostMarks) { step *= 2 }

        var strokes: [Stroke] = []
        var value = (least / step).rounded(.up) * step
        while value < most {
            var crossings: [LonLat] = []
            for ring in outline.rings {
                guard var before = ring.last else { continue }
                for corner in ring {
                    let one = offset(before) - value
                    let other = offset(corner) - value
                    if (one < 0) != (other < 0) {
                        let along = one / (one - other)
                        crossings.append(
                            LonLat(
                                longitude: before.longitude + along * (corner.longitude - before.longitude),
                                latitude: before.latitude + along * (corner.latitude - before.latitude)))
                    }
                    before = corner
                }
            }
            crossings.sort { $0.longitude < $1.longitude }
            var at = 0
            while at + 1 < crossings.count {
                strokes.append(Stroke(from: crossings[at], to: crossings[at + 1]))
                at += 2
            }
            value += step
        }
        return strokes
    }

    /// Dots inside a shape, in rows, each row set half a step from the one before.
    static func dots(in outline: Outline, spacing: Double) -> [LonLat] {
        guard spacing > 0, let box = bounds(of: [outline]) else { return [] }
        let squeeze = squeeze(at: box.centre.latitude)
        var up = spacing
        var across = spacing / squeeze
        while (box.height / up) * (box.width / across) > Double(mostMarks) {
            up *= 2
            across *= 2
        }
        var dots: [LonLat] = []
        var row = Int((box.south / up).rounded(.up))
        while Double(row) * up <= box.north {
            let shift = row % 2 == 0 ? 0 : across / 2
            var column = Int(((box.west - shift) / across).rounded(.up))
            while Double(column) * across + shift <= box.east {
                let position = LonLat(longitude: Double(column) * across + shift, latitude: Double(row) * up)
                if Self.outline(outline, holds: position) { dots.append(position) }
                column += 1
            }
            row += 1
        }
        return dots
    }

    // MARK: - A picture with no map

    /// A way to place a position in a picture, keeping shapes as they are on
    /// the ground at that latitude. North is up. It is for the small picture
    /// that says where one area is among the rest.
    struct Projector: Sendable {
        let bounds: Bounds
        let width: Double
        let height: Double
        let padding: Double

        func place(_ position: LonLat) -> (x: Double, y: Double) {
            let squeeze = Results.squeeze(at: bounds.centre.latitude)
            let across = max(bounds.width * squeeze, Double.ulpOfOne)
            let up = max(bounds.height, Double.ulpOfOne)
            let room = (width: max(width - 2 * padding, 0), height: max(height - 2 * padding, 0))
            let scale = min(room.width / across, room.height / up)
            let left = padding + (room.width - across * scale) / 2
            let top = padding + (room.height - up * scale) / 2
            return (
                left + (position.longitude - bounds.west) * squeeze * scale,
                top + (bounds.north - position.latitude) * scale
            )
        }
    }
}
