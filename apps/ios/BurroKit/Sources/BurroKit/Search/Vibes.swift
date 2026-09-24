import Foundation

// Where an area sits on a vibe, read off what the API sent. It mirrors
// apps/web/src/lib/vibes.ts. Its words are in `VibeCopy`.
//
// A vibe is said as a band, one of five, counted from its low end, and never
// as a percentage, a score or a rank. Nothing here writes a sentence about a
// place: it says a band in the words a screen uses for one, and names the
// ends of a vibe as the API names them.

/// Where an area sits on a vibe: a band, and the bands it spans. All three are the API's.
public struct Placed: Hashable, Sendable {
    public static let bands = 1...VibeCopy.bandCount

    public let band: Int
    public let spreadLow: Int
    public let spreadHigh: Int

    public init(band: Int, spreadLow: Int, spreadHigh: Int) {
        self.band = band
        self.spreadLow = spreadLow
        self.spreadHigh = spreadHigh
    }

    /// Where a mark of a result's strip says the area sits.
    public init(_ mark: StripMark) {
        self.init(band: mark.band, spreadLow: mark.spreadLow, spreadHigh: mark.spreadHigh)
    }

    /// Where a fact of a vibe says the area sits. `nil` where it names no
    /// band, as the fact of a vibe that cannot place the area does, and where
    /// what it names is not a band.
    public init?(_ fact: Fact) {
        guard let band = fact.slots["band"].flatMap(Int.init),
            let low = fact.slots["spread_low"].flatMap(Int.init),
            let high = fact.slots["spread_high"].flatMap(Int.init),
            Self.bands.contains(band), Self.bands.contains(low), Self.bands.contains(high),
            low <= band, band <= high
        else { return nil }
        self.init(band: band, spreadLow: low, spreadHigh: high)
    }

    /// True when the area is drawn as a range: it spans three bands or more, and is no one point.
    public var isRange: Bool { spreadHigh - spreadLow >= 2 }

    /// True for a cell of the line of five that the area fills.
    public func fills(_ cell: Int) -> Bool {
        isRange ? (spreadLow...spreadHigh).contains(cell) : cell == band
    }

    /// Where the mark sits, in words: what a person who sees the screen reads from the line of five.
    public var inWords: String {
        isRange ? VibeCopy.bands(spreadLow, spreadHigh) : VibeCopy.band(band)
    }
}

/// One vibe of an area, as a screen draws it. Every name, band and count in
/// it is the API's, and the words for the band are the app's words for a code.
public struct VibeShown: Hashable, Sendable, Identifiable {
    public let tagId: TagId
    /// The API's name for the vibe.
    public let name: String
    /// The names of its two ends: the API's for a scale, and "least" and "most" for one that runs one way.
    public let low: String
    public let high: String
    /// Where the area sits. `nil` for a vibe that cannot place it: it is never put in the middle.
    public let placed: Placed?
    /// Where it sits, in words a person would use: "towards Flats", "among the most here".
    public let plainly: String?
    /// What the band rests on, where that is part of the recipe: the API's
    /// own clause, or the two counts the fact holds.
    public let restsOn: String?
    /// What the vibe waits on: each part of its recipe that the data does not
    /// carry, by the API's name for it, with what it carries of the recipe.
    public let waitsOn: [String]
    /// True when the data holds too little of the recipe to place any area on the vibe.
    public let notInData: Bool
    /// How much of the recipe the data holds, where the API says.
    public let held: String?
    /// What is said of a vibe that was asked for in the search. `nil` for one that was not.
    public let asked: String?
    public let sources: [SourceLine]

    public var id: String { tagId.rawValue }

    /// The band, in words: "band 4 of 5", or that Burro cannot place the area.
    public var band: String {
        placed?.inWords ?? VibeCopy.cannotPlace
    }

    /// The vibe as it is read out, and as a test reads it: its name, where
    /// the area sits, the band, the ends it is counted between, what it rests
    /// on and what it waits on.
    public var reads: String {
        var said: [String] = [name]
        if let plainly { said.append(plainly) }
        said.append(band)
        if placed != nil { said.append(VibeCopy.from(low, high)) }
        if let asked { said.append(asked) }
        if let restsOn { said.append(restsOn) }
        if notInData { said.append(VibeCopy.noAreaPlaced) }
        if let held { said.append(held) }
        if !waitsOn.isEmpty { said.append(VibeCopy.waitsOn(waitsOn.joined(separator: "; "))) }
        return said.joined(separator: ", ")
    }
}

public enum Vibes {
    /// The names of the two ends of a vibe.
    public static func ends(of tag: Tag) -> (low: String, high: String) {
        (tag.lowEnd ?? VibeCopy.least, tag.highEnd ?? VibeCopy.most)
    }

    /// Where a mark sits, in words a person would use. A mixed area is said
    /// to vary, and is never put at a point. `nil` for what is no band.
    public static func plainly(_ tag: Tag, _ placed: Placed) -> String? {
        if placed.isRange { return VibeCopy.varies }
        guard let low = tag.lowEnd, let high = tag.highEnd else { return VibeCopy.oneWay(placed.band) }
        return VibeCopy.onAScale(placed.band, low: low, high: high)
    }

    /// What a band rests on, where the fact says the area has no figure for a
    /// part of the recipe: the API's own clause where the fact holds one, and
    /// otherwise the two counts it does hold. Nothing is added up here.
    public static func restsOn(_ fact: Fact?) -> String? {
        guard let fact, let known = fact.slots["known"], let parts = fact.slots["parts"], known != parts
        else { return nil }
        if let partly = fact.slots["partly"], !partly.isEmpty { return partly }
        return VibeCopy.restsOn(known, of: parts)
    }

    /// What a vibe waits on, as the release says it: each part by name, with its share.
    public static func waitsOn(_ held: RecipeHeld?) -> [String] {
        (held?.waitsOn ?? []).map { VibeCopy.part($0.label, $0.hundredths) }
    }

    /// One vibe of an area. `placed` is `nil` for a vibe that cannot place the area.
    public static func shown(
        _ tag: Tag, placed: Placed?, fact: Fact?, held: RecipeHeld?, asked: String? = nil
    ) -> VibeShown {
        let ends = ends(of: tag)
        let notInData = held.map { !$0.placed } ?? false
        return VibeShown(
            tagId: tag.tagId, name: tag.label, low: ends.low, high: ends.high, placed: placed,
            plainly: placed.flatMap { plainly(tag, $0) },
            restsOn: placed == nil ? nil : restsOn(fact),
            waitsOn: waitsOn(held), notInData: notInData,
            held: notInData ? held.map { VibeCopy.held($0.held, needed: $0.needed) } : nil,
            asked: asked,
            sources: SourceLines.of(fact.map { [$0] } ?? []))
    }

    /// What a mark of a strip says of being asked for: the end that was asked
    /// for, of a scale, and that it was, of a vibe that runs one way.
    public static func asked(_ mark: StripMark, _ tag: Tag) -> String? {
        guard mark.asked else { return nil }
        guard tag.shape == .scale else { return VibeCopy.asked }
        let ends = ends(of: tag)
        return VibeCopy.askedFor(mark.toward == .low ? ends.low : ends.high)
    }

    /// The strip of a result: where the area sits on the vibes that were
    /// asked for, and on the others the API chose. Which vibes, in what order,
    /// and every band are the API's. A vibe the release does not name is left out.
    public static func strip(_ marks: [StripMark], meta: MetaData, facts: [String: Fact]) -> [VibeShown] {
        marks.compactMap { mark in
            guard let tag = meta.tags.first(where: { $0.tagId == mark.tagId }) else { return nil }
            return shown(
                tag, placed: Placed(mark), fact: facts[mark.factId],
                held: ReleaseHolds.recipe(of: mark.tagId, in: meta), asked: asked(mark, tag))
        }
    }
}
