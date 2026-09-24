import Foundation

/// Three sentences to start from. Pressing one fills the box and sends nothing.
///
/// They are the website's, word for word. None names a place, so none can go
/// stale when a release changes. One names a budget, which is a thing a
/// person says of themselves and no figure about a place. A test holds all
/// of this.
enum Examples {
    static let sentences: [String] = [
        "Renting a one bedroom flat for up to £1,700 a month, somewhere leafy and quiet",
        "Buying a terraced house, with good primary schools and a park nearby",
        "Somewhere buzzy with bars and restaurants, close to a station",
    ]
}
