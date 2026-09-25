import Foundation

/// Sentences to start from. Pressing one fills the box and sends nothing.
///
/// They are the website's, word for word, in the order they are tried. None
/// names a place, so none can go stale when a release changes. One names a
/// budget, which is a thing a person says of themselves and no figure about a
/// place. A test holds all of this.
enum Examples {
    /// A sentence, and everything it asks for, as the API names each thing in
    /// the target of a suggestion. An example is offered only where the data
    /// can answer all of it.
    struct Example: Hashable, Sendable {
        let text: String
        let asks: [String]
    }

    /// How many examples the screen shows.
    static let shown = 3

    static let pool: [Example] = [
        Example(
            text: "Renting a one bedroom flat for about £1,700 a month, somewhere leafy and quiet",
            asks: ["budget", "tag:leafy", "tag:quiet_residential"]),
        Example(
            text: "Buying a terraced house, with good primary schools and a park nearby",
            asks: ["feature:school_primary_attainment", "feature:park_proximity"]),
        Example(
            text: "Somewhere buzzy with bars and restaurants, close to a station",
            asks: [
                "tag:pace", "feature:venue_evening_per_homes", "feature:venue_food_drink_per_homes",
                "feature:station_walk",
            ]),
        Example(
            text: "Somewhere quiet, near a big park", asks: ["tag:quiet_residential", "tag:parks_close_by"]),
        Example(text: "Clean air and a park nearby", asks: ["feature:air_no2", "feature:park_proximity"]),
        Example(
            text: "Buying a house, somewhere quiet with clean air",
            asks: ["feature:air_no2", "tag:quiet_residential"]),
    ]

    /// The three that were first written, which a release that holds everything shows.
    static let sentences: [String] = pool.prefix(shown).map(\.text)

    /// The sentences the first screen offers to start from: the first three
    /// that the release can answer the whole of. With nothing it can answer, none.
    static func offered(for meta: MetaData) -> [String] {
        pool.filter { example in example.asks.allSatisfy { ReleaseHolds.canAnswer($0, in: meta) } }
            .prefix(shown)
            .map(\.text)
    }
}
