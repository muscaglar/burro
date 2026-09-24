import Foundation

/// The words the shell carries. They name controls, states and codes. They
/// never hold a number or a proper noun about a place: those come from the API.
///
/// Where the website has the words, these are the website's, word for word,
/// from `apps/web/src/content/`. Each feature keeps its own words in its own folder.
public enum ShellCopy {
    public static let name = "Burro"

    /// The banner that says the data is made up. It is on every screen that
    /// shows data and cannot be closed.
    public static let bannerLabel = "About this data"
    public static let banner =
        "This is made-up test data. The city, its places and every figure are invented. "
        + "Nothing here describes a real place."

    public static func title(of tab: AppTab) -> String {
        switch tab {
        case .search: return "Search"
        case .shortlist: return "Shortlist"
        case .about: return "About"
        }
    }

    /// The name of the system image that stands beside a tab's name. The name
    /// is always drawn with it: the image is never the only signal.
    public static func image(of tab: AppTab) -> String {
        switch tab {
        case .search: return "magnifyingglass"
        case .shortlist: return "bookmark"
        case .about: return "info.circle"
        }
    }

    public static let opening = "Opening Burro"
    public static let couldNotOpen = "Burro could not be opened"
    public static let tryAgain = "Try again"
    public static let requestId = "If you report this, quote"
    /// What covers the screen while the app is not in front, so that the
    /// picture the phone keeps of it shows nothing of a search.
    public static let covered = "Burro"

    /// Words for a call that gave no answer, when the reason is not the API's own.
    public static func words(for kind: ClientFailureKind) -> String {
        switch kind {
        case .timeout: return "Burro took too long to answer."
        case .network: return "Burro could not be reached."
        case .offline: return "You are offline."
        case .notConfigured: return "This copy of the app is not connected to Burro's data."
        case .unreadable: return "Burro sent an answer that could not be read."
        case .aborted: return "Stopped."
        }
    }

    /// What to say of a failure. The API's message is shown as it came: it is
    /// fixed text and never holds what was sent.
    public static func words(for failure: Failure) -> String {
        switch failure {
        case .api(let refusal): return refusal.message
        case .client(let own): return words(for: own.kind)
        }
    }
}
