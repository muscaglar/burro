import Foundation

// What a person asked for that the data does not hold yet, said by name, with
// why. A vibe says what it waits on. It mirrors the website's `NotInData`.
//
// Nothing here is offered and nothing is pressed: a screen says what is not
// there. The name of each thing and the name of each part it waits on are the
// API's. A budget and a journey are named by the app, as a setting is: the
// API's label for one may hold the amount that was typed.

/// The words for what the data does not hold. They are the website's, word
/// for word, from `NOT_IN_DATA` of `apps/web/src/content/search.ts`.
public enum NotInDataCopy {
    public static let budget = "What you can pay"
    public static let commute = "A journey"
    public static let whyBudget = "This data holds no rents and no prices, so a budget cannot be tested."
    public static let whyCommute = "This data names no place to reach and holds no journey times."
    public static let whyFeature = "This data holds no figure for it."
    public static let whyVibe = "No area can be placed on it yet."
}

public enum NotInData {
    /// What kind of thing a target names, by how it begins.
    enum Kind {
        case budget
        case commute
        case vibe
        case feature
    }

    static func kind(of target: String) -> Kind {
        if target == "budget" { return .budget }
        if target == "commute" { return .commute }
        return target.hasPrefix("tag:") ? .vibe : .feature
    }

    /// One line for each thing that was asked for and is in the data for no
    /// area: its name, why, and for a vibe what it waits on.
    public static func lines(of state: SearchState) -> [String] {
        state.missing.map { line(for: $0, in: state.meta) }
    }

    static func line(for missing: Missing, in meta: MetaData) -> String {
        let name: String
        let why: String
        var waits: String?
        switch kind(of: missing.target) {
        case .budget:
            name = NotInDataCopy.budget
            why = NotInDataCopy.whyBudget
        case .commute:
            name = NotInDataCopy.commute
            why = NotInDataCopy.whyCommute
        case .feature:
            name = missing.label
            why = NotInDataCopy.whyFeature
        case .vibe:
            name = missing.label
            why = NotInDataCopy.whyVibe
            let id = String(missing.target.dropFirst("tag:".count))
            let parts = Vibes.waitsOn(meta.recipes.first { $0.tagId.rawValue == id })
            if !parts.isEmpty { waits = VibeCopy.waitsOn(parts.joined(separator: "; ")) }
        }
        return ([name.isEmpty ? nil : "\(name).", why, waits] as [String?])
            .compactMap { $0 }
            .joined(separator: " ")
    }
}
