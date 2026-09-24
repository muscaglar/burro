import Foundation
import Observation

// What the results screen keeps while the app is open: how the results are
// shown, how tall the list stands over the map, and the areas chosen to
// compare. It is held in memory, by the app's model, and nowhere else, and
// holds nothing of a search: an area is its id, its slug, its name and its borough.
//
// The areas to compare are not part of the search. Starting the search again
// leaves them as they are, as it does on the website.

extension Results {
    /// How the results are shown.
    enum Showing: String, Hashable, Sendable, CaseIterable, Identifiable {
        /// The map, with the list over it.
        case map
        /// The list alone, on the whole screen.
        case list
        /// Every area of the release, with everything the map says of it.
        case table

        var id: String { rawValue }

        var words: String {
            switch self {
            case .map: return ResultsCopy.Views.map
            case .list: return ResultsCopy.Views.list
            case .table: return ResultsCopy.Views.table
            }
        }
    }

    /// How tall the list stands over the map: one of three heights.
    enum Height: Int, Hashable, Sendable, CaseIterable, Comparable {
        case low
        case half
        case full

        static func < (one: Height, other: Height) -> Bool { one.rawValue < other.rawValue }

        /// The share of the room the list takes.
        var share: Double {
            switch self {
            case .low: return 0.22
            case .half: return 0.5
            case .full: return 0.9
            }
        }

        var words: String {
            switch self {
            case .low: return ResultsCopy.Sheet.low
            case .half: return ResultsCopy.Sheet.half
            case .full: return ResultsCopy.Sheet.full
            }
        }

        var taller: Height { Height(rawValue: rawValue + 1) ?? self }
        var shorter: Height { Height(rawValue: rawValue - 1) ?? self }
        /// The next height up, and from the tallest back to the lowest, for a press on the handle.
        var next: Height { self == .full ? .low : taller }

        /// The height nearest to a share of the room, as when a drag ends.
        static func nearest(to share: Double) -> Height {
            allCases.min { abs($0.share - share) < abs($1.share - share) } ?? .half
        }

        /// How many points tall the list is in a room, and never less than its handle and a line need.
        func points(in room: Double, least: Double) -> Double {
            guard room.isFinite, room > 0 else { return least }
            return min(room, max(room * share, least))
        }
    }

    @MainActor
    @Observable
    final class Memory {
        var showing: Showing = .map
        var height: Height = .half
        /// The areas chosen to compare, in the order they were chosen.
        var compare: [AreaRef] = []
        var shareOpen = false
        var legendOpen = false
        /// The area the list is asked to bring into view. It is set by the map, and cleared once done.
        var bringIntoView: String?
        let sharing = Sharing()

        init() {}

        func toggleCompare(_ area: AreaRef) {
            compare = toggled(compare, area)
        }

        func isCompared(_ area: AreaRef) -> Bool {
            compare.contains { $0.areaId == area.areaId }
        }

        /// The areas to compare that the release still holds. One it has dropped is left out.
        func compared(among areas: [AreaSummary]) -> [AreaRef] {
            compare.filter { chosen in areas.contains { $0.areaId == chosen.areaId } }
        }
    }
}
