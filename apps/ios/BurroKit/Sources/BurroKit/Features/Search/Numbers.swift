import Foundation

// How a number a person sets is read, kept to its steps, and written.
//
// Nothing here is a figure about a place. A budget, a time and a weight are
// what a person says of their own search. A figure about a place arrives
// already written, in a fact's slots, and is shown as it came.

enum FormNumbers {
    private static let british = Locale(identifier: "en_GB")

    /// A whole number with separators between the thousands.
    static func grouped(_ value: Int) -> String {
        value.formatted(.number.grouping(.automatic).locale(british))
    }
}

/// What was typed into a field for a whole number.
enum NumberEntry: Hashable, Sendable {
    /// Nothing was typed: the field goes back to what the API said.
    case empty
    /// What was typed is no whole number.
    case notANumber
    case number(Int)

    /// Reads what was typed. Spaces, commas and a pound sign are passed over,
    /// so that "£1,700" is 1700. With `keptWithin`, the number is brought
    /// within those limits before it is sent.
    static func read(_ typed: String, keptWithin limits: ClosedRange<Int>? = nil) -> NumberEntry {
        let text = typed.filter { !$0.isWhitespace && $0 != "," && $0 != "£" }
        if text.isEmpty { return .empty }
        guard text.allSatisfy({ $0.isASCII && $0.isNumber }), let number = Int(text) else {
            return .notANumber
        }
        guard let limits else { return .number(number) }
        return .number(min(limits.upperBound, max(limits.lowerBound, number)))
    }
}

/// How much something counts, as a control shows it: a whole number from 0 to
/// 100, kept to the steps the API serves.
struct WeightScale: Hashable, Sendable {
    static let least = 0
    static let most = 100

    /// The smallest change there is, in hundredths.
    let unit: Int
    /// What a press of minus or plus moves it by.
    let step: Int

    init(_ limits: ServedLimits) {
        unit = max(1, Self.hundredths(limits.weightUnit))
        step = max(unit, Self.hundredths(limits.weightStepSmall))
    }

    /// A weight from 0 to 1, as the whole number from 0 to 100 that a control shows.
    static func hundredths(_ weight: Double) -> Int {
        Int((weight * 100).rounded())
    }

    /// A number from 0 to 100, as the weight the API takes.
    static func weight(_ hundredths: Int) -> Double {
        Double(hundredths) / 100
    }

    /// The nearest value the API accepts.
    func snapped(_ value: Double) -> Int {
        let steps = (value / Double(unit)).rounded()
        return min(Self.most, max(Self.least, Int(steps) * unit))
    }

    /// Where a press of minus or plus lands.
    func moved(_ value: Int, _ step: SmallStep) -> Int {
        snapped(Double(value + (step == .up ? self.step : -self.step)))
    }
}

/// An amount or a time on a slider: its limits, the steps it keeps to, and
/// how its length is shared out.
struct AmountScale: Hashable, Sendable {
    /// How the length of the slider is shared out between the least and the most.
    enum Curve: Hashable, Sendable {
        /// Evenly: each step takes the same room. For a time.
        case even
        /// By proportion: doubling the amount takes the same room wherever it
        /// is done. For a budget, whose limits are far apart, so that the
        /// amounts most people set are not all at one end.
        case widening
    }

    let least: Int
    let most: Int
    let unit: Int
    let curve: Curve

    init(least: Int, most: Int, unit: Int, curve: Curve = .even) {
        self.least = least
        self.most = max(least, most)
        self.unit = max(1, unit)
        // A proportion needs a least amount above nothing.
        self.curve = least > 0 && most > least ? curve : .even
    }

    var limits: ClosedRange<Int> { least...most }

    /// The nearest value on a step, within the limits.
    func snapped(_ value: Double) -> Int {
        guard value.isFinite else { return least }
        let steps = ((value - Double(least)) / Double(unit)).rounded()
        let bounded = min(Double(most - least) / Double(unit), max(0, steps))
        return min(most, max(least, least + Int(bounded) * unit))
    }

    /// Where a value stands on the slider, from 0 to 1.
    func position(of value: Int) -> Double {
        guard most > least else { return 0 }
        let kept = Double(min(most, max(least, value)))
        switch curve {
        case .even:
            return (kept - Double(least)) / Double(most - least)
        case .widening:
            return log(kept / Double(least)) / log(Double(most) / Double(least))
        }
    }

    /// The value at a place on the slider, on a step.
    func value(at position: Double) -> Int {
        let place = min(1, max(0, position.isFinite ? position : 0))
        switch curve {
        case .even:
            return snapped(Double(least) + place * Double(most - least))
        case .widening:
            return snapped(Double(least) * pow(Double(most) / Double(least), place))
        }
    }

    /// A budget, for the tenure: the limits the API serves for it.
    static func budget(_ tenure: Tenure, _ limits: ServedLimits) -> AmountScale {
        let money = tenure == .buy ? limits.buy : limits.rent
        return AmountScale(
            least: money.minimum, most: money.maximum, unit: money.unit, curve: .widening)
    }

    /// The longest journey that can be asked for: no longer than the longest
    /// the data holds for that way of travelling.
    static func minutes(_ mode: Mode, _ limits: ServedLimits) -> AmountScale {
        let cutoff: Int
        switch mode {
        case .pt: cutoff = limits.cutoffMinutes.pt
        case .cycle: cutoff = limits.cutoffMinutes.cycle
        case .walk: cutoff = limits.cutoffMinutes.walk
        case .unlisted: cutoff = limits.minutesMax
        }
        return AmountScale(
            least: limits.minutesMin, most: min(limits.minutesMax, cutoff), unit: 1)
    }
}
