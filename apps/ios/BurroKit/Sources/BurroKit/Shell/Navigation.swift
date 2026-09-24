import Foundation

// Where the app can go. Every tab, and every screen a tab can show, is named
// here, so that a feature reaches another feature's screen by its name and
// never by its view.
//
// A route holds ids and names of the release, and nothing of a search: no
// text, no place a person named, no spec. Routes are held in memory. They are
// never restored from a file, offered to Handoff or indexed by Spotlight.

/// The three tabs, in the order they are drawn.
public enum AppTab: String, Hashable, Sendable, CaseIterable, Identifiable {
    case search
    case shortlist
    case about

    public var id: String { rawValue }
}

/// An area, as a route to its screen holds it: ids and names of the release.
public struct AreaRef: Hashable, Sendable, Identifiable {
    public let areaId: String
    /// What route 6 is asked for, and what the address of the area's page on the website ends in.
    public let slug: String
    public let name: String
    public let borough: String

    public var id: String { areaId }

    public init(areaId: String, slug: String, name: String, borough: String) {
        self.areaId = areaId
        self.slug = slug
        self.name = name
        self.borough = borough
    }

    public init(_ area: AreaSummary) {
        self.init(areaId: area.areaId, slug: area.slug, name: area.name, borough: area.borough)
    }

    public init(_ area: Neighbourhood) {
        self.init(areaId: area.areaId, slug: area.slug, name: area.name, borough: area.borough)
    }
}

/// A screen that is pushed onto a tab. The root of each tab is not one: it is always there.
public enum Screen: Hashable, Sendable {
    /// The ranking of the search that is open: the map, and the list under it.
    case results
    /// One area. It is reached from the results and from the shortlist.
    case area(AreaRef)
    /// Two to four areas side by side, for the search that is open. The route
    /// names none of them: the areas chosen are held in memory.
    case compare
    /// How Burro works: each feature, each tag, the limits and the release.
    case methods
    /// Every source of data, with its licence.
    case sources
    /// What is met, what has not been tested, and how to report a problem.
    case accessibility
}
