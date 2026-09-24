import Foundation

// Where things are: the bounds of the areas, and a way to draw them flat. It
// mirrors apps/web/src/lib/map/project.ts.
//
// It is for the small picture that says where one area is among the rest. The
// picture is drawn from the outlines the API serves, and from nothing else: no
// tile is fetched from anyone, so nobody is told which area a person is reading.

/// The room a picture is drawn in.
public struct LocatorFrame: Hashable, Sendable {
    public let width: Double
    public let height: Double
    public let padding: Double

    public init(width: Double, height: Double, padding: Double) {
        self.width = width
        self.height = height
        self.padding = padding
    }
}

/// A point of a picture, from its top left corner.
public struct LocatorPoint: Hashable, Sendable {
    public let x: Double
    public let y: Double
}

/// The outline of one area, placed in a frame.
public struct LocatorOutline: Hashable, Sendable, Identifiable {
    public let areaId: String
    public let rings: [[LocatorPoint]]

    public var id: String { areaId }
}

/// West and south, then east and north.
public struct LocatorBounds: Hashable, Sendable {
    public let west: Double
    public let south: Double
    public let east: Double
    public let north: Double
}

public enum Locator {
    /// The size the picture is worked out at. It is scaled to the room it is given.
    public static let frame = LocatorFrame(width: 160, height: 120, padding: 4)

    /// Every ring of a polygon or of a multipolygon, outer and inner alike.
    public static func rings(of geometry: Geometry) -> [[LonLat]] {
        switch geometry.coordinates {
        case .polygon(let rings): return rings
        case .multiPolygon(let polygons): return polygons.flatMap { $0 }
        }
    }

    /// The box that holds every area. `nil` when there is nothing to hold.
    public static func bounds(of data: GeometryData) -> LocatorBounds? {
        var west = Double.infinity
        var south = Double.infinity
        var east = -Double.infinity
        var north = -Double.infinity
        for feature in data.features {
            for ring in rings(of: feature.geometry) {
                for position in ring where position.longitude.isFinite && position.latitude.isFinite {
                    west = min(west, position.longitude)
                    east = max(east, position.longitude)
                    south = min(south, position.latitude)
                    north = max(north, position.latitude)
                }
            }
        }
        guard west <= east, south <= north else { return nil }
        return LocatorBounds(west: west, south: south, east: east, north: north)
    }

    /// A way to place a position in a frame, keeping shapes as they are on the
    /// ground at that latitude: a degree of longitude is drawn narrower than
    /// one of latitude, by the cosine of the latitude. North is up.
    public static func projector(_ bounds: LocatorBounds, in frame: LocatorFrame) -> @Sendable (LonLat) -> LocatorPoint {
        let squeeze = cos((bounds.south + bounds.north) / 2 * .pi / 180)
        let across = max((bounds.east - bounds.west) * squeeze, .ulpOfOne)
        let up = max(bounds.north - bounds.south, .ulpOfOne)
        let room = (width: frame.width - 2 * frame.padding, height: frame.height - 2 * frame.padding)
        let scale = min(room.width / across, room.height / up)
        let left = frame.padding + (room.width - across * scale) / 2
        let top = frame.padding + (room.height - up * scale) / 2
        return { position in
            LocatorPoint(
                x: left + (position.longitude - bounds.west) * squeeze * scale,
                y: top + (bounds.north - position.latitude) * scale)
        }
    }

    /// The outline of every area, drawn flat in one frame.
    public static func outlines(of data: GeometryData, in frame: LocatorFrame = Locator.frame) -> [LocatorOutline] {
        guard let bounds = bounds(of: data) else { return [] }
        let place = projector(bounds, in: frame)
        return data.features.map { feature in
            LocatorOutline(
                areaId: feature.properties.areaId,
                rings: rings(of: feature.geometry)
                    .filter { $0.count > 2 }
                    .map { ring in
                        ring.filter { $0.longitude.isFinite && $0.latitude.isFinite }.map(place)
                    })
        }
    }
}
