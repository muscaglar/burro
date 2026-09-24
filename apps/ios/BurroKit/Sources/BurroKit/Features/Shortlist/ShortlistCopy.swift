import Foundation

/// The words of the Shortlist screen. They name controls and states. None is
/// about a place: a name and a date are filled in from what was saved.
enum ShortlistCopy {
    /// Under the title. The list is held on the phone and nowhere else.
    static let kept = "Kept on this phone. Burro does not hold it."
    static let empty = "No area saved yet. Save one from its page."

    static func saved(on date: String) -> String {
        "Saved \(date)"
    }

    /// Said of a saved area whose figures are of another release than the one being read now.
    static let older = "The data has changed since this area was saved, so its figures may differ now."
    /// Said of a saved area whose figures are not in hand.
    static let noFigures = "Its figures are not on this phone. Open it with a connection to read them."
    static let couldNotSave =
        "The last change could not be written to this phone. It holds until the app is closed."

    static func open(_ area: String) -> String {
        "Open \(area)"
    }

    static func remove(_ area: String) -> String {
        "Remove \(area) from the shortlist"
    }

    static let removeShort = "Remove"
    static let moveUp = "Move up"
    static let moveDown = "Move down"

    static let clear = "Remove every area"
    static let clearTitle = "Remove every saved area from this phone?"
    static let clearConfirm = "Remove every area"
    static let cancel = "Cancel"

    /// A date as a person reads it: the day, the month in words, the year.
    static func date(_ date: Date, in zone: TimeZone = .current) -> String {
        var style = Date.FormatStyle(date: .long, time: .omitted)
        style.locale = Locale(identifier: "en_GB")
        style.timeZone = zone
        return date.formatted(style)
    }
}
