import Foundation

/// The words for a vibe and for a band. Each is a word for a code, and none
/// names a place: the name of a vibe and of each of its ends are the API's.
///
/// They are the website's, word for word, from `bands.ts`, from `STRIP`,
/// `SHELF` and `NOT_IN_DATA` of `search.ts`, and from `facts.ts`, all under
/// `apps/web/src/content/`. A test holds them to it. No figure is written
/// here: how many bands there are, and what a recipe adds up to, are passed in.
public enum VibeCopy {
    /// How many bands a vibe is counted in, and what the shares of a recipe add up to.
    public static let bandCount = 5
    public static let whole = 100

    /// The ends of a vibe that runs one way, as the contract names them.
    public static let least = "least"
    public static let most = "most"

    public static func band(_ band: Int) -> String { "band \(band) of \(bandCount)" }
    public static func bands(_ low: Int, _ high: Int) -> String {
        "varies within this area, from band \(low) to band \(high) of \(bandCount)"
    }
    public static func from(_ low: String, _ high: String) -> String { "counted from \(low) to \(high)" }

    /// Said of a vibe that was asked for.
    public static let asked = "asked for"
    public static func askedFor(_ end: String) -> String { "asked for: \(end)" }
    /// Said once before a run of vibes: that they were asked for, or that they were not.
    public static let groupAsked = "Asked for"
    public static let groupAlso = "Also"
    public static func label(_ area: String) -> String { "Vibes of \(area)" }

    /// Said of a mixed area, which spans three bands or more and is no one point.
    public static let varies = "varies within this area"

    /// Where an area sits on a vibe that runs one way, from least to most, by
    /// its band. `nil` for what is no band.
    public static func oneWay(_ band: Int) -> String? {
        let words = [
            "among the least here", "on the low side here", "around the middle here",
            "on the high side here", "among the most here",
        ]
        return words.indices.contains(band - 1) ? words[band - 1] : nil
    }

    /// Where an area sits on a scale, by its band. The names of the two ends
    /// are the API's. `nil` for what is no band.
    public static func onAScale(_ band: Int, low: String, high: String) -> String? {
        let words = [
            "at the \(low) end", "towards \(low)", "between \(low) and \(high)", "towards \(high)",
            "at the \(high) end",
        ]
        return words.indices.contains(band - 1) ? words[band - 1] : nil
    }

    /// Beside a band that rests on part of a recipe. Both counts are the API's.
    public static func restsOn(_ known: String, of parts: String) -> String {
        "from \(known) of its \(parts) parts"
    }

    /// Said of an area a vibe cannot place, in place of a band. It names a state and no figure.
    public static let cannotPlace = "Burro cannot place this area on it"

    /// Over the parts of a recipe that the data does not hold, each by the name the API gives it.
    public static let waitsOnTitle = "What it waits on"
    public static func waitsOn(_ parts: String) -> String { "It waits on: \(parts)." }
    /// One part a vibe waits on: its name, and what it carries of the recipe. Both are the API's.
    public static func part(_ label: String, _ hundredths: Int) -> String {
        "\(label), \(hundredths) of \(whole)"
    }

    /// Said of a vibe that no area of the data can be placed on.
    public static let notYet = "Not in this data yet"
    public static let noAreaPlaced = "No area can be placed on it yet."

    /// How much of a recipe the data holds, as one number, and how much an area needs. Both are the API's.
    public static func held(_ held: Int, needed: Int) -> String {
        if held == 0 {
            return "This data holds none of its recipe. An area needs \(needed) of \(whole) to be placed."
        }
        if held >= needed {
            return "A band rests on \(held) of \(whole) of its recipe, which is what this data holds."
        }
        return "This data holds \(held) of \(whole) of its recipe. An area needs \(needed) of \(whole) to be placed."
    }
}
