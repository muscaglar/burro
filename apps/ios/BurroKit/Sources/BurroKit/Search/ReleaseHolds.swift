import Foundation

// What the release that is loaded can answer at all, read off route 11. It
// mirrors apps/web/src/lib/holds.ts.
//
// A first build holds a few measures, a band for a few vibes, and no journey
// and no cost. A screen then says what is not there yet where a person would
// look for it, and offers no control that the API could only turn away.
// Nothing here is worked out: whether a vibe places any area, how much of its
// recipe is held and what it waits on are the API's to say.

public enum ReleaseHolds {
    /// What the release holds of one vibe's recipe. `nil` where the API said nothing of it.
    public static func recipe(of tagId: TagId, in meta: MetaData) -> RecipeHeld? {
        meta.recipes.first { $0.tagId == tagId }
    }

    /// Whether any area has a band for the vibe. A vibe the API says nothing
    /// of is taken to be placed: a screen then offers it, and the API answers for it.
    public static func isPlaced(_ tagId: TagId, in meta: MetaData) -> Bool {
        recipe(of: tagId, in: meta)?.placed ?? true
    }

    /// What a sentence may ask for, as the target of a suggestion names it:
    /// `budget`, `commute`, `feature:<id>` or `tag:<id>`. True where the
    /// release can answer it.
    public static func canAnswer(_ target: String, in meta: MetaData) -> Bool {
        if target == "budget" { return meta.holds.costs }
        if target == "commute" { return meta.holds.journeys }
        let parts = target.split(separator: ":", maxSplits: 1).map(String.init)
        guard parts.count == 2 else { return true }
        switch parts[0] {
        case "tag":
            return meta.recipes.contains { $0.tagId.rawValue == parts[1] && $0.placed }
        case "feature":
            return meta.features.contains { $0.featureId.rawValue == parts[1] && $0.rankable }
        default:
            return true
        }
    }
}
