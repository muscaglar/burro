import Foundation

/// Everything the Results feature works out is inside this name, so that no
/// name of it can meet a name of another feature.
///
/// Nothing in it writes a word about a place. It finds what the API sent, and
/// lays it out. What a screen draws is a plain value made here, so that it
/// can be tested on a Mac with no screen.
enum Results {}

// What the map and the list show of a fit: the whole number, and the band it
// falls in. docs/design/web.md, sections 4 and 6.
//
// Colour is never the only signal. A band is a range of fit that the legend
// gives in figures, a pattern goes with a reason given in words, and the rank
// itself is a number, in the pin and in the order of the list.

extension Results {
    /// A fit as a screen shows it: a whole number from 0 to 100, rounded
    /// down, so that a fit is never said to be more than it is and always
    /// falls in the band the legend gives for it.
    static func fit(of score: Double) -> Int {
        guard score.isFinite else { return 0 }
        return min(ResultsCopy.most, max(0, Int(score.rounded(.down))))
    }

    /// A share from 0 to 1 as a whole number out of 100, rounded down: never more than is so.
    static func hundredths(_ share: Double?) -> Int? {
        guard let share, share.isFinite else { return nil }
        return min(ResultsCopy.most, max(0, Int((share * 100 + 1e-9).rounded(.down))))
    }

    /// A weight from 0 to 1, as the whole number from 0 to 100 that a control shows.
    static func outOfHundred(_ weight: Double) -> Int {
        guard weight.isFinite else { return 0 }
        return Int((weight * 100).rounded())
    }

    /// One of the five bands of fit, with the range it stands for.
    struct Band: Hashable, Sendable, Identifiable {
        /// 1 to 5, from low to high.
        let number: Int
        let from: Int
        let to: Int

        var id: Int { number }
    }

    /// How wide a band is, in points of fit.
    static let bandWidth = 20

    /// The five bands, low to high.
    static let bands: [Band] = (1...5).map { number in
        Band(
            number: number,
            from: (number - 1) * bandWidth,
            to: number == 5 ? ResultsCopy.most : number * bandWidth - 1)
    }

    /// The band a score falls in, from 1 to 5.
    static func band(of score: Double) -> Int {
        let fit = fit(of: score)
        return bands.first { fit >= $0.from && fit <= $0.to }?.number ?? 1
    }

    /// Lines on an area a limit left out, dots on one that is not ranked.
    enum Pattern: String, Hashable, Sendable {
        case none
        case filtered
        case unranked
    }

    /// What the map shows of one area. Band 0 is an area with no fit to show.
    struct Fill: Hashable, Sendable {
        let band: Int
        let pattern: Pattern

        static let land = Fill(band: 0, pattern: .none)
    }

    /// How many areas a numbered pin is drawn for.
    static let pins = 10

    /// The fill of every area the ranking speaks of, by area id. An area it
    /// says nothing of has no entry, and is drawn as land with no fit.
    ///
    /// With nothing set to rank by every area scores 0, which is no fit at
    /// all, so none is given a band.
    static func fills(_ ranking: Ranking?) -> [String: Fill] {
        guard let ranking else { return [:] }
        var fills: [String: Fill] = [:]
        for score in ranking.scores {
            fills[score.areaId] = Fill(
                band: ranking.emptySpec ? 0 : band(of: score.score), pattern: .none)
        }
        for left in ranking.filtered { fills[left.areaId] = Fill(band: 0, pattern: .filtered) }
        for not in ranking.unranked { fills[not.areaId] = Fill(band: 0, pattern: .unranked) }
        return fills
    }

    /// A whole number with separators between the thousands, as people write one here.
    /// It is for the person's own budget. A figure about a place comes already written.
    static func grouped(_ value: Int) -> String {
        let digits = String(abs(value))
        var out = ""
        for (offset, digit) in digits.enumerated() {
            if offset > 0 && (digits.count - offset) % 3 == 0 { out.append(",") }
            out.append(digit)
        }
        return value < 0 ? "-" + out : out
    }
}
