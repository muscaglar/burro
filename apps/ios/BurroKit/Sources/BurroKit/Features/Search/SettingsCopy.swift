import Foundation

// The words of the settings: the form that does the same job as the box.
//
// They name controls. A feature's name and a tag's name are the API's, from
// the meta route, and are not written here. Where the website has the words,
// these are the website's, from apps/web/src/content/settings.ts.

enum SettingsCopy {
    static let title = "Settings"
    static let lead = "Every setting here does what typing does. Change one and the ranking is worked out again."
    static let rank = "Rank with these settings"

    enum Budget {
        static let legend = "Budget"
        static func amount(_ tenure: Tenure) -> String {
            tenure == .buy ? "Most you can pay, in pounds" : "Most you can pay a month, in pounds"
        }
        static let less = "Lower the budget a little"
        static let more = "Raise the budget a little"
        static let clear = "Clear the budget"
        static let segment = "Size or type of home"
        static let firm = "The budget is a firm limit"
        static let firmHint =
            "A firm limit leaves out every area known to cost more. Otherwise a dearer area is ranked lower."
        static let weight = "How much the budget counts"
        static func between(_ least: String, _ most: String) -> String {
            "Between £\(least) and £\(most)."
        }
        static let notWhole = "Give the amount as a whole number of pounds."
        /// What the slider says while no amount is set.
        static let noneSet = "No budget set"
        /// The slider beside the field. It sets the same amount.
        static let slider = "Most you can pay, on a slider"
        static func pounds(_ amount: String) -> String { "£\(amount)" }
        static func aMonth(_ amount: String) -> String { "£\(amount) a month" }
    }

    enum Journey {
        static let legend = "Places you need to reach"
        static let none = "No place named yet."
        static func place(_ name: String) -> String { "Journey to \(name)" }
        static let how = "How you travel there"
        static let longest = "Longest journey, in minutes"
        static let shorter = "Make the longest journey shorter"
        static let longer = "Make the longest journey longer"
        static let firm = "The journey is a firm limit"
        static let firmHint =
            "A firm limit leaves out every area known to be further. Otherwise a longer journey is ranked lower."
        static func remove(_ name: String) -> String { "Remove \(name)" }
        static func between(_ least: Int, _ most: Int) -> String {
            "Between \(least) and \(most) minutes."
        }
        static let notWhole = "Give the time as a whole number of minutes."
        static let combine = "Which journey counts"
        static let basis = "Which time counts"
        static let weight = "How much journeys count"
        static let settingsLegend = "How journeys count"
        /// The slider beside the field. It sets the same time.
        static let slider = "Longest journey, on a slider"
        static func minutes(_ minutes: Int) -> String { "\(minutes) minutes" }
    }

    enum Features {
        static let legend = "What you want nearby"
        static let tagsLegend = "The feel of the place"
        static let tagsHint = "A tag is a fixed formula over the features above. Methods says what is in each."
        static func weight(_ label: String) -> String { "How much it counts: \(label)" }
        static func direction(_ label: String) -> String { "Which way counts as better: \(label)" }
    }

    enum Slider {
        static func less(_ label: String) -> String { "Less: \(label)" }
        static func more(_ label: String) -> String { "More: \(label)" }
        /// How much something counts, as it is shown and read out: a figure, and what it is out of.
        static func outOf(_ value: Int, _ most: Int) -> String { "\(value) of \(most)" }
        static func range(_ least: Int, _ most: Int) -> String {
            "From \(least), which is not at all, to \(most), which is as much as anything can."
        }
    }

    enum Hidden {
        static let legend = "Hidden areas"
        static let none = "No area is hidden."
        static func show(_ area: String) -> String { "Show \(area) again" }
        static func only(_ area: String) -> String { "Stop showing only \(area)" }
    }

    enum Crime {
        static let lead =
            "Recorded crime is off unless you switch it on. It is a count of what was reported, by kind."
        /// The caveat that goes with recorded crime, word for word as the
        /// contract states it in section 7.3. A test holds it to the contract.
        static let caveat = "Recorded crime depends on what is reported, and locations are approximate."
    }
}
