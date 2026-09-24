import Foundation

/// The words for a link that was opened: a search that someone shared, or an
/// area's page. They say what a link holds, in words that stay true of the
/// API as the contract describes it. None says anything of a place.
///
/// The words for a shared search are the website's, word for word, from
/// `apps/web/src/content/share.ts`. A test holds them to it.
enum LinkCopy {
    enum Shared {
        static let title = "A shared search"
        static let text = "This search was opened from a link. Changing it here does not change the link."
        static let holds =
            "A shared link holds the settings of a search, and not what was typed. "
            + "Each place in it is the station or district that stands in for the place the sender named, "
            + "unless the sender chose to share the exact places."
        static let coarsened =
            "A place in this search is the station or district that stands in for the place the sender named. "
            + "The ranking may differ a little from theirs."
        static let exact = "The places in this search are the ones the sender named."
        static let stale =
            "The data has changed since this link was made, so the ranking may differ from what the sender saw."
        static let madeOn = "It was made on data release"
        static let shownOn = "It is shown on"
        static let opening = "Opening the shared search"
        static let failedTitle = "The shared search could not be opened"
        static let tryAgain = "Try again"
        static let own = "Make a search of your own"

        /// The two ids are of releases, and say nothing of a search.
        static func staleBetween(madeOn made: String, shownOn shown: String) -> String {
            "\(stale) \(madeOn) \(made). \(shownOn) \(shown)."
        }
    }

    /// A link that holds no id.
    enum NoShare {
        static let title = "No shared search in this address"
        static let text =
            "A link to a shared search ends in an id. This address has none. "
            + "Ask for the link again, or make a search of your own."
    }

    /// A link whose end is not an id. What it held is never sent and never shown.
    enum NotAShare {
        static let title = "This is not a link to a shared search"
        static let text =
            "The end of this address is not an id Burro makes. Part of the link may be missing. "
            + "Ask for it again, or make a search of your own."
    }

    /// A link to an area the release does not have.
    enum NoArea {
        static let title = "This link is to an area this data does not have"
        static let text = "The area may have been renamed, or the link may be of other data. Search for areas instead."
    }

    /// What is said of the ranking a share opened. The count and the name are the API's.
    enum Ranked {
        static func named(_ count: Int, first: String) -> String {
            count == 1 ? "\(count) area ranked: \(first)." : "\(count) areas ranked. First: \(first)."
        }

        static func unnamed(_ count: Int) -> String {
            count == 1 ? "\(count) area ranked." : "\(count) areas ranked."
        }

        static func inNoOrder(_ count: Int) -> String {
            count == 1
                ? "\(count) area passes. Nothing is set to rank it by."
                : "\(count) areas pass. Nothing is set to rank them by, so they are in no order."
        }

        static let none = "No area passes every limit you set."
    }

    static let seeResults = "See the results"
    static let done = "Done"
}
