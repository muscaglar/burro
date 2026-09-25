import Foundation

/// The words of an area's screen: the names of its headings, its columns and
/// its states. None says anything of a place. Every name and every figure on
/// the screen is the API's, and is shown as it came. Where a line below has a
/// gap in it, the gap is filled with a name or a date the API sent.
///
/// Where the website has the words, these are the website's, word for word,
/// from `apps/web/src/content/`. A test holds them to it.
enum AreaCopy {
    static let borough = "Borough"
    static let notRanked =
        "This data does not rank this area, so no search lists it. What is known of it is below."

    enum Where {
        static let title = "Where it is"
        static let neighbours = "Areas next to it"
        static let noNeighbours = "No area in this data is next to it."

        /// What the small picture shows, for a person who cannot see it.
        static func picture(of area: String) -> String {
            "Where \(area) is among the areas of this data"
        }
    }

    enum Stations {
        static let title = "Stations nearby"
        static let none = "No station near this area is in this data."
    }

    enum Cost {
        static let title = "What homes cost"
        static let lead =
            "Half of homes of this kind cost between these two figures. The middle is the figure half are below."
        static let rent = "Renting, a month"
        static let buy = "Buying"
        static let noRent = "No rent figure in this data."
        static let noPrice = "No price figure in this data."
    }

    enum Measured {
        static let title = "What is measured here"
        static let lead =
            "Each figure says where it sits among the areas of this data. None is a judgement of the place."
        static let noFigure = "No figure in this data"
    }

    /// The portrait an area's screen opens with: where the area sits on each
    /// vibe. Every vibe, band and name in it is the API's. These are the
    /// headings the API's lists stand under.
    enum Portrait {
        static let title = "Character"
        static let unplacedWhy =
            "Too few parts of each recipe have a figure for this area, so Burro says nothing of it on these. "
            + "An area is never put in the middle for want of data."
        /// Why, of the vibes that no area of the data can be placed on.
        static let notInData =
            "This data does not hold enough of each recipe to place any area on these yet. "
            + "It is so of every area, and not of this one alone."

        /// The heading of each list of the portrait. Which vibe stands in which list is the API's to say.
        static func title(of list: AreaPage.VibeList) -> String {
            switch list {
            case .scales: return "On a scale"
            case .more: return "More than most here"
            case .less: return "Less than most here"
            case .others: return "Also placed"
            case .unplaced: return "Burro cannot place"
            }
        }
    }

    enum Sources {
        static let title = "Sources on this page"
        static let lead = "Every figure on this page comes from one of these."
        static let methods = "How each figure is worked out"
    }

    /// The line that ends a figure: its source and its date.
    enum Source {
        static let source = "Source"
        static let dataFrom = "Data from"
        static let madeUp = "Made-up data"
    }

    /// The name of each column a fact is laid out in.
    enum Column {
        static let value = "Figure"
        static let standing = "Where it sits"
        static let segment = "Kind of home"
        static let range = "Range"
        static let median = "Middle"
        static let asOf = "As of"
        static let confidence = "Confidence"
        static let station = "Station"
        static let walk = "Minutes on foot"
        static let lines = "Lines"
        static let name = "Name"
        static let borough = "Borough"
        /// Between the two ends of a range.
        static let to = "to"
        // A price that is one number: the middle of what homes of one kind sold for.
        static let middleOfAll = "Middle price, homes of all sizes"
        static let soldIn = "Homes sold in"
        // A price that was counted from sales says how many it rests on. The count is the API's.
        static let sales = "Sales it rests on"
        static let band = "Band, of five"
        static let bands = "Varies within this area, across bands"
        static let ends = "Counted from"
        static let compared = "Areas compared in this release"
        static let partsDated = "Parts dated"
        static let partsKnown = "Parts with a figure in this release"
        static let parts = "Parts in the recipe"
        static let share = "Share of the recipe they carry, in hundredths"
    }

    /// Said of a price that is one number, where a range would stand its two ends.
    static let oneNumber =
        "The publisher gives no range, and does not say how many sales this figure rests on."

    /// The caveat that goes with recorded crime, word for word as the contract
    /// states it in section 7.3.
    static let crimeCaveat = "Recorded crime depends on what is reported, and locations are approximate."

    /// What a row is called when nothing else names it. `nil` for a row this
    /// build has no word for, which is then left out.
    static func kind(_ template: TemplateId) -> String? {
        switch template {
        case .area: return "Area"
        case .feature: return "Feature"
        case .featureCrime: return "Recorded crime"
        case .vibe, .vibeRange, .vibeUnknown: return "Vibe"
        case .costRent: return "Rent"
        case .costBuy, .costBuyMedian, .costBuySold: return "Price"
        case .station: return "Nearest station"
        case .stationNearby: return "Station within a short walk"
        case .likeness, .likenessSame: return "Likeness"
        // These are of a search, and an area's page holds none of them.
        case .budgetUnder, .budgetOver, .budgetUnderMedian, .budgetOverMedian, .travelPt, .travelPtOver,
            .travelOther, .travelOtherOver, .travelBeyond, .travelEstimated, .missing, .missingJourney:
            return nil
        case .unlisted: return nil
        }
    }

    /// What each group of figures is about. `nil` for one this build has no word for.
    static func dimension(_ dimension: Dimension) -> String? {
        switch dimension {
        case .crime: return "Recorded crime"
        case .schools: return "Schools"
        case .greenWater: return "Green space and water"
        case .airNoise: return "Air and noise"
        case .venuesCulture: return "Venues and culture"
        case .homes: return "Homes"
        case .stationAccess: return "Stations"
        case .services: return "Shops and services"
        case .brands: return "Brands nearby"
        case .residents: return "Who lived there at the census"
        case .unlisted: return nil
        }
    }

    // MARK: - What the app adds

    static let addToShortlist = "Add to shortlist"
    static let removeFromShortlist = "Remove from shortlist"
    static let share = "Share"
    static let shareHint = "The link is to this area's page. It holds nothing of your search."

    // MARK: - What a search says of the area

    enum InSearch {
        static let title = "In your search"
        static let reasons = "Why it fits"
        static let tradeOff = "Trade-off"
        static let noTradeOff = "No trade-off found for this search"
        static let byModel = "Written by AI, checked against the source"

        static func rank(_ rank: Int) -> String {
            "Rank \(rank)"
        }

        /// The fit is a whole number, rounded down, so that it is never said to be more than it is.
        static func rankAndFit(rank: Int, fit: Int, of most: Int) -> String {
            "Rank \(rank), fit \(fit) of \(most)"
        }
    }

    // MARK: - States

    static let reading = "Opening this area"
    static let failed = "This area could not be opened"
    static let release = "Data release"

    /// Said above a saved copy, when the area could not be read again.
    static func asSaved(on date: String, release: String) -> String {
        "This is the data as it was when you saved this area, on \(date), from data release \(release)."
    }

    static let changedSince =
        "The data has changed since you saved this area. This page shows the data as it is now."
    static let keepNewer = "Keep the data as it is now"
    static let noGroups = "Figures"
}
