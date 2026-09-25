import Foundation

/// The words of the Results feature. They name controls, states and codes.
/// None says anything of a place: a name, a sentence and a figure are the
/// API's, and fill the gaps in the lines below.
///
/// Where the website has the words, these are the website's, word for word,
/// from `apps/web/src/content/`. A test holds them to it. The few the app
/// adds are listed in that test, each with its reason.
///
/// A word for a code is `nil` for a code this build does not know: a line it
/// has no words for is left out, and never shown as a blank or as the code.
enum ResultsCopy {
    /// The most a fit, a weight or a share can be, and the least.
    static let most = 100
    static let least = 0

    static let title = "Results"

    // MARK: - How the results are shown

    enum Views {
        static let label = "Show the results as"
        static let list = "List"
        static let map = "Map"
        static let table = "Table"
    }

    /// The panel over the map that holds the list.
    enum Sheet {
        static let handle = "Height of the list"
        static let low = "Low"
        static let half = "Half"
        static let full = "Full"
        static let hint = "Swipe up or down to change the height"
        static let taller = "Make the list taller"
        static let shorter = "Make the list shorter"
    }

    // MARK: - What is said of the ranking

    enum Status {
        static let reading = "Reading your search"
        static let updating = "Working out the ranking again"
        /// The whole of what is said of a first ranking: how many areas, and which is first.
        static func ranked(_ count: Int, first: String) -> String {
            "\(rankedUnnamed(count)) \(Status.first(first))"
        }
        static func first(_ name: String) -> String { "First: \(name)." }
        static func rankedUnnamed(_ count: Int) -> String {
            count == 1 ? "\(count) area ranked." : "\(count) areas ranked."
        }
        static func rankedNoOrder(_ count: Int) -> String {
            count == 1
                ? "\(count) area passes. Nothing is set to rank it by."
                : "\(count) areas pass. Nothing is set to rank them by, so they are in no order."
        }
        static func moved(_ count: Int) -> String {
            if count == 0 { return "No area changed place." }
            return count == 1 ? "\(count) area changed place." : "\(count) areas changed place."
        }
        /// Said when the settings nobody chose came to count for less.
        static let gaveWay = "What you asked for counts most."
        /// Said in its place where a journey or a budget counts for more than
        /// anything that was asked of the place.
        static func leads(journeys: Int, budget: Bool) -> String {
            guard journeys > 0 else { return "Budget counts most." }
            let who = journeys == 1 ? "Journey" : "Journeys"
            let counts = budget ? " and budget count" : journeys == 1 ? " counts" : " count"
            return "\(who)\(counts) most."
        }
        static let nothingMatches = "No area passes every limit you set."
        /// Said in its place where no limit left any area out: every area has
        /// too little data for what counts.
        static let nothingRanked =
            "No area could be ranked. This data holds too little of what counts in your search."
        static let question = "Burro has a question about a place."
        static let toSearch = "Go to the search"
    }

    enum Notice {
        static let label = "About your search"
        static let degraded = "Your words could not be read just now. The settings below do the same job."
        static let degradedHere = "Your words could not be read just now. The settings do the same job."
        /// Said when the provider of the language model would not read what was typed. It names nobody.
        static let refused = "The language model would not read this. Burro's rules have read it instead."
        /// A sentence that Burro reads whole, to show what it can read. It names no place.
        static let readable = "leafy and quiet, near a park"
        static var nothingRead: String {
            "Nothing in that could be read. Burro reads plain English, such as \(quoted(readable))"
                + ". Say it another way, or use the settings below."
        }
        static var nothingReadHere: String {
            "Nothing in that could be read. Burro reads plain English, such as \(quoted(readable))"
                + ". Say it another way, or use the settings."
        }
        /// Words between the quote marks the website writes them between.
        static func quoted(_ words: String) -> String { "“\(words)”" }
        static let nothingChanged = "That changed nothing. Your search already says it."
        /// Said when only a part of what was typed was read.
        static let partUnread =
            "Burro read only part of what you typed, and the ranking leaves the rest out. "
            + "Say the rest again in shorter sentences, one thing in each, or use the settings."
        static let offline = "You are offline. Your search is still here."
        static let offlineWaiting = "Your last change will be sent when you are back online."
        static let notUpdated = "These results were not updated."
        static let requestId = "If you report this, quote"
        static let stale = "Your search names something this data no longer has."
        static func takeOut(_ what: String) -> String { "Take \(what) out" }
        static let thePlace = "the place"
        static let theArea = "the area"
        static let theSetting = "the setting"
        static let tryAgain = "Try again"
        static let startAgain = "Start again"
        static let shared = "A shared search"
        static let sharedText = "This search was opened from a link. Changing it here does not change the link."
        static let sharedCoarsened =
            "A place in this search is the station or district that stands in for the place the sender named. "
            + "The ranking may differ a little from theirs."
        static let sharedStale =
            "The data has changed since this link was made, so the ranking may differ from what the sender saw."
    }

    /// What the reader noticed in a prompt it did not apply. It is chosen on the search.
    enum Suggest {
        static let title = "Choose what to add"
    }

    /// What was asked for that the data does not hold yet.
    enum NotInData {
        static let title = "Not in this data yet"
        static func lead(_ count: Int) -> String {
            count == 1
                ? "You asked for one thing this data cannot answer yet. It counts for nothing in the ranking."
                : "You asked for \(count) things this data cannot answer yet. They count for nothing in the ranking."
        }
    }

    // MARK: - A result

    enum Card {
        static let listLabel = "Areas in order of fit"
        static let firstFive = "Reasons are written for the first five results."
        static let waiting = "Results will show here."
        static let fit = "Fit"
        static func fitOf(_ fit: Int) -> String { "\(fit) of \(most)" }
        static func rank(_ rank: Int) -> String { "Rank \(rank)" }
        static let whereTitle = "Where it is"
        static let reasonsTitle = "Why it fits"
        static let noReasons = "Nothing this area does well enough to give as a reason."
        static let tradeOffTitle = "Trade-off"
        static let noTradeOff = "No trade-off found for this search"
        static let reasonsFailed = "The reasons could not be loaded."
        static let detailsFailed = "The cost and the station could not be loaded."
        static let loading = "Loading"
        static let byModel = "Written by AI, checked against the source"
        /// Opens the working of a result, in place.
        static let more = "Show the working"
        static func openArea(_ area: String) -> String { "Open the page for \(area)" }
        static func hide(_ area: String) -> String { "Hide \(area)" }
        static func showOnMap(_ area: String) -> String { "Show \(area) on the map" }
        static let actions = "Actions"
        /// What a button on a card says. The name of the area is said after it when it is read out.
        static let open = "Open the page"
        static let hideThis = "Hide this area"
        static let onMap = "Show on the map"
        static let addToCompare = "Add to compare"
        static let removeFromCompare = "Remove from compare"
        static func of(_ words: String, _ area: String) -> String { "\(words), \(area)" }
        static let release = "Data release"
        static let engine = "Ranking engine"
        static let selected = "Chosen on the map"
    }

    enum Shortlist {
        static let add = "Add to shortlist"
        static let remove = "Remove from shortlist"
        static func adding(_ area: String) -> String { "Add \(area) to shortlist" }
        static func removing(_ area: String) -> String { "Remove \(area) from shortlist" }
        static let kept = "Kept on this phone. Burro does not hold it."
        static let couldNotSave = "The shortlist could not be saved to this phone."
    }

    enum Completeness {
        static let all = "Based on everything that counts in your search"
        static func some(_ present: Int, of asked: Int) -> String {
            "Based on \(present) of the \(asked) things that count in your search"
        }
        /// The heading over the API's sentence for each thing the area has no figure for.
        static let missingTitle = "What there is no figure for"
    }

    enum Journeys {
        static let title = "Journeys"
        static let place = "To"
        static let how = "How"
        static let typical = "Typical"
        static let missed = "If you just miss one"
        static let limit = "Your limit"
        static func minutes(_ minutes: Int) -> String { "\(minutes) minutes" }
        static let within = "within"
        static let over = "over"
        static func withinLimit(_ minutes: Int) -> String { "Within your limit of \(minutes) minutes" }
        static func overLimit(_ minutes: Int) -> String { "Over your limit of \(minutes) minutes" }
        static func beyond(_ minutes: Int) -> String { "More than \(minutes) minutes" }
        static let missing = "No journey time in this data"
        /// Where a journey that was estimated stands against the limit a person set: the
        /// three bands of the API, each in the words its fact says it in where it stands
        /// alone. An estimate is never given in minutes.
        static func estimated(_ band: JourneyBand?) -> String? {
            switch band {
            case .likelyWithin: return "Likely within your limit"
            case .borderline: return "Borderline for your limit"
            case .likelyBeyond: return "Likely beyond your limit"
            case .unlisted, nil: return nil
            }
        }
        /// What stands wherever an estimate is shown: the API's line, word for word.
        static let estimatedFrom = "Estimated from distance, not from a timetable."
        static let time = "How long"
        /// Under two journeys or more: which of them the fit is worked out from.
        static func usesOne(_ place: String) -> String {
            "Of these journeys, only the one to \(place) counts towards the fit: "
                + "it does worst against the limit you set for it. "
                + "You can make the average count instead, in Settings."
        }
        static let usesMean =
            "The average of these journeys counts towards the fit. "
            + "You can make only the worst one count instead, in Settings."
        static let notGiven = "Not given"
        static let notApply = "Does not apply"
        /// In place of the name of a place, where an answer named a place and gave no name for it.
        static let noName = "A place with no name in this data"
    }

    enum Cost {
        static let title = "Cost"
        static let none = "No cost figure in this data"
        static let to = "to"
        static let middle = "Middle"
        static let asOf = "As of"
        static let confidence = "Confidence"
        static let aMonth = "a month"
        static let budget = "Your budget"
        static let picture = "The range of cost, with your budget marked on it"
        static let below = "Your budget is below this range."
        static let above = "Your budget is above this range."
        static let inside = "Your budget is inside this range."
        static let pound = "£"
        // A price that is one number, as a publisher gives it. No range is drawn for it.
        static let what = "What this is"
        static let middleOfAll = "The middle price of homes of this kind, of all sizes"
        static let soldIn = "Homes sold in"
        static let pictureOfOne = "The middle price, with your budget marked beside it"
        static let belowMiddle = "Your budget is below this middle price."
        static let aboveMiddle = "Your budget is above this middle price."
        static let atMiddle = "Your budget is this middle price."
        static let oneNumber =
            "The publisher gives no range, and does not say how many sales this figure rests on."
    }

    static func word(for confidence: Confidence) -> String? {
        switch confidence {
        case .high: return "High"
        case .medium: return "Medium"
        case .low: return "Low"
        // Of a price that is one number. A card says what is not known of it, and not this word.
        case .unstated: return "unstated"
        case .unlisted: return nil
        }
    }

    enum Breakdown {
        static let title = "How the fit is worked out"
        static let caption = "Each thing that counts, and what it adds to the fit"
        static let thing = "What counts"
        static let weight = "Counts for"
        static let share = "Share of the fit"
        static let adds = "Adds"
        static let says = "What the data says"
        static let journey = "Journey"
        static let budget = "Budget"
        /// There is a figure, and the fact that holds it is not in hand to show.
        static let has = "Has a figure"
        static let hasNot = "No figure"
        static func outOf(_ value: Int) -> String { "\(value) of \(most)" }
        static func percent(_ value: Int) -> String { "\(value)%" }
        static let roundedDown =
            "Every figure here is rounded down, so what the things add can come to a little less than the fit."
    }

    enum Source {
        static let source = "Source"
        static func sourceFor(_ what: String) -> String { "Source for \(what)" }
        static let dataFrom = "Data from"
        static let madeUp = "Made-up data"
        static let all = "Data sources"
    }

    enum Locator {
        static func title(_ area: String) -> String { "Where \(area) is among the areas of this data" }
    }

    // MARK: - The map

    enum Map {
        static let label = "Map of the areas"
        static let loading = "The map is loading."
        static let noGeometry =
            "The boundaries of the areas could not be loaded. The table below says everything the map would."
        static let noGeometryHere =
            "The boundaries of the areas could not be loaded. The table says everything the map would."
        static let zoomIn = "Zoom in"
        static let zoomOut = "Zoom out"
        static let whole = "Show every area"
        static let controls = "Map controls"
        static func pin(rank: Int, area: String, fit: String) -> String { "Rank \(rank), \(area), fit \(fit)" }
        static func pinNoFit(rank: Int, area: String) -> String { "Rank \(rank), \(area)" }
        static func fitLabel(_ fit: Int) -> String { "Fit \(fit)" }
    }

    enum Legend {
        static let title = "What the map shows"
        static let fit = "Fit"
        static func band(from: Int, to: Int) -> String { "\(from) to \(to)" }
        static let noScore = "No fit yet"
        static let filtered = "Left out by a limit you set. Shown with lines."
        static let unranked = "Not ranked. Shown with dots."
        static let pin = "A numbered pin is the rank of one of the first ten."
        static let fitLabel = "Each ranked area is marked with its fit."
        static let open = "Open"
        static let closed = "Closed"
    }

    enum MapCard {
        static let label = "The area chosen on the map"
        static let showInList = "Show in the list"
        static let close = "Close"
        static let notInList = "This area is not in the list."
    }

    enum Table {
        static let caption = "Every area, in order of fit and then by name"
        static let captionEmpty = "Every area, by name"
        static let rank = "Rank"
        static let area = "Area"
        static let borough = "Borough"
        static let fit = "Fit"
        static let status = "Status"
        static let ranked = "Ranked"
        static let notYet = "Not ranked yet"
        static let none = "None"
        static let show = "Show"
        static func select(_ area: String) -> String { "Show \(area) on the map and in the list" }
    }

    // MARK: - Words for codes

    static func word(for reason: FilterReason) -> String? {
        switch reason {
        case .excluded: return "Hidden by you"
        case .notSelected: return "Not one of the areas you chose"
        case .overBudget: return "Over your budget, which is a firm limit"
        case .commuteCap: return "A journey is longer than a firm limit"
        case .commuteLikelyBeyond:
            return "A journey is likely beyond a firm limit. \(Journeys.estimatedFrom)"
        case .unlisted: return nil
        }
    }

    static func word(for reason: UnrankedReason) -> String? {
        switch reason {
        case .notRankable: return "Not ranked in this data"
        case .insufficientData: return "Too little data for what counts in your search"
        case .characterUnknown: return "Too little is known of the character that counts in your search"
        case .unlisted: return nil
        }
    }

    /// A limit that could not be tested for an area, because the figure is missing.
    static func untested(_ reason: FilterReason) -> String? {
        switch reason {
        case .excluded: return "Whether you hid this area could not be checked."
        case .notSelected: return "Whether this is one of the areas you chose could not be checked."
        case .overBudget:
            return "Your budget is a firm limit, and it could not be tested here: there is no cost figure."
        case .commuteCap, .commuteLikelyBeyond:
            return "A journey is a firm limit, and it could not be tested here: there is no journey time."
        case .unlisted: return nil
        }
    }

    /// Why an edit was not applied.
    static func word(for reason: RejectReason) -> String? {
        switch reason {
        case .unknownPlace: return "That place is not in this data."
        case .unknownArea: return "That area is not in this data."
        case .notInRelease: return "This data cannot rank that."
        case .tooManyCommutes: return "No more places can be added. Remove one first."
        case .noSuchCommute: return "That place is not part of your search."
        case .outOfRange: return "That number is outside what Burro accepts."
        case .segmentNotForTenure:
            return "That kind of home does not go with the choice of renting or buying."
        case .directionNotAllowed: return "That counts one way only."
        case .crimeNeedsExplicitRequest:
            return
                "Recorded crime counts only when you ask for it by name, switch it on in the settings, or ask for a vibe whose recipe holds it."
        case .mismatchedChoice: return "That setting does not take that choice."
        case .nothingToChange: return "That changed nothing."
        case .unlisted: return nil
        }
    }

    static func word(for mode: Mode) -> String? {
        switch mode {
        case .pt: return "Public transport"
        case .cycle: return "By bike"
        case .walk: return "On foot"
        case .unlisted: return nil
        }
    }

    enum NothingMatches {
        static let title = Status.nothingMatches
        static let lead = "Each area was left out for one of these reasons."
        static func count(_ count: Int) -> String { count == 1 ? "\(count) area" : "\(count) areas" }
        static let loosen = "Make a limit flexible"
        static let budgetFlexible = "Make the budget flexible"
        static func journeyFlexible(_ place: String) -> String { "Make the journey to \(place) flexible" }
        static func showHidden(_ area: String) -> String { "Show \(area) again" }
        static func showAll(_ area: String) -> String { "Stop showing only \(area)" }
    }

    // MARK: - Comparing

    enum Compare {
        static let title = "Compare areas"
        static let lead =
            "Two to four areas side by side: where each sits on each vibe, and then how each does on what counts."
        static func add(_ area: String) -> String { "Add \(area) to compare" }
        static func remove(_ area: String) -> String { "Remove \(area) from compare" }
        static let comparing = "Comparing the areas"
        static func compared(_ count: Int) -> String { "\(count) areas compared." }
        static let tooFew = "A comparison takes two to four areas. Choose areas from the search or from an area's page."
        static let tooFewHere = "A comparison takes two to four areas. Choose areas from the results."
        static let fromSearch =
            "These areas are compared on your search. The rows are in the order of what counts most in it."
        static let fromDefaultsRent =
            "No search is open, so these areas are compared on the usual settings for renting. "
            + "A search of your own puts the rows in the order of what counts most to you."
        static let fromDefaultsBuy =
            "No search is open, so these areas are compared on the usual settings for buying. "
            + "A search of your own puts the rows in the order of what counts most to you."
        static let nothingCounts =
            "Nothing is set to count in this search, so there is nothing to compare the areas on."
        static let chooseOthers = "Choose other areas"
        static let failedTitle = "The areas could not be compared"
    }

    enum Tray {
        static let title = "Areas to compare"
        static let none = "No area chosen yet. Choose two to four."
        static let one = "One area chosen. Choose at least one more."
        static let full = "Four areas is the most. Remove one to add another."
        static func go(_ count: Int) -> String { "Compare \(count) areas" }
        static let clear = "Clear"
        static func remove(_ area: String) -> String { "Remove \(area)" }
    }

    enum CompareTable {
        static let areas = "The areas compared"
        /// The vibes of each area, side by side. They come before the measured parts.
        static let character = "Character"
        static let characterCaption = "Where each area sits on each vibe, in one of five bands"
        /// The heading over the things that count, each with how each area does on it.
        static let counts = "What counts"
        static let caption = "Each thing that counts, and how each area does on it"
        static let what = "What counts"
        /// How much a thing counts, under its name. It is a weight and no share.
        static func countsFor(_ weight: Int) -> String { "Weight \(weight)" }
        /// Over the table, once: what a weight is.
        static let weights =
            "A weight says how much a thing counts beside the others, from \(least) to \(most), "
            + "as its slider is set. The weights are not shares, and do not add up to \(most)."
        /// Under the name of the row of a journey: where the journey is to. The name is the API's.
        static func journeyTo(_ place: String) -> String { "To \(place)" }
        static func adds(_ points: Int) -> String { "Adds \(points) of \(most) to the fit" }
        static let noFigure = "No figure in this data"
        static let notScored = "Not worked out: this area was left out before it was scored"
        static func standing(rank: Int, fit: Int?) -> String {
            guard let fit else { return "Rank \(rank)" }
            return "Rank \(rank). Fit \(fit) of \(most)"
        }
        static func takeOut(_ area: String) -> String { "Take \(area) out of this comparison" }
    }

    static func word(for status: CompareStatus) -> String? {
        switch status {
        case .ranked: return "Ranked"
        case .excluded: return "Left out: hidden by you"
        case .notSelected: return "Left out: not one of the areas you chose"
        case .overBudget: return "Left out: over your budget, which is a firm limit"
        case .commuteCap: return "Left out: a journey is longer than a firm limit"
        case .commuteLikelyBeyond:
            return "Left out: a journey is likely beyond a firm limit. \(Journeys.estimatedFrom)"
        case .notRankable: return "Not ranked in this data"
        case .insufficientData: return "Not ranked: too little data for what counts"
        case .characterUnknown: return "Not ranked: too little is known of the character that counts"
        case .unlisted: return nil
        }
    }

    /// The caveat of the contract, section 7.3, word for word.
    static let crimeCaveat = "Recorded crime depends on what is reported, and locations are approximate."

    // MARK: - A fact laid out in columns

    enum Columns {
        static let value = "Figure"
        static let standing = "Where it sits"
        static let segment = "Kind of home"
        static let range = "Range"
        static let median = "Middle"
        static let asOf = "As of"
        static let confidence = "Confidence"
        static let upper = "Upper end of the range"
        static let amount = "Your budget"
        static let under = "Under your budget by"
        static let over = "Over your budget by"
        static let place = "To"
        static let mode = "How"
        static let typical = "Typical minutes"
        static let missed = "Minutes if you just miss one"
        static let minutes = "Minutes"
        static let moreThan = "More than, in minutes"
        static let name = "Name"
        static let borough = "Borough"
        static let station = "Station"
        static let walk = "Minutes on foot"
        static let lines = "Lines"
        static let to = "to"
        static let middleOfAll = "Middle price, homes of all sizes"
        static let soldIn = "Homes sold in"
        static let sales = "Sales it rests on"
        static let limit = "Your limit, in minutes"
        /// Over where a journey that was estimated stands against the limit, and over what
        /// says that it is an estimate.
        static let estimate = "Against your limit"
        static let howKnown = "How this is known"
        static let underLimit = "Under your limit by, in minutes"
        static let overLimit = "Over your limit by, in minutes"
        static let band = "Band, of five"
        static let bands = "Varies within this area, across bands"
        static let ends = "Counted from"
        static let compared = "Areas compared in this release"
        static let partsDated = "Parts dated"
        static let partsKnown = "Parts with a figure in this release"
        static let parts = "Parts in the recipe"
        static let share = "Share of the recipe they carry, in hundredths"
    }

    /// What each kind of row is called when nothing else names it.
    static func kind(of template: TemplateId) -> String? {
        switch template {
        case .area: return "Area"
        case .feature: return "Feature"
        case .featureCrime: return "Recorded crime"
        case .vibe, .vibeRange, .vibeUnknown: return "Vibe"
        case .costRent: return "Rent"
        case .costBuy, .costBuyMedian, .costBuySold: return "Price"
        case .budgetUnder, .budgetOver, .budgetUnderMedian, .budgetOverMedian: return "Budget"
        case .travelPt, .travelPtOver, .travelOther, .travelOtherOver, .travelBeyond: return "Journey"
        case .travelEstimated: return "Journey, estimated"
        case .station: return "Nearest station"
        case .stationNearby: return "Station within a short walk"
        case .missing: return "No figure"
        case .missingJourney: return "No journey time"
        case .likeness, .likenessSame: return "Likeness"
        case .unlisted: return nil
        }
    }

    // MARK: - Sharing the search

    enum Share {
        static let open = "Share this search"
        static let holdsTitle = "What the link holds"
        static let points = [
            "The link holds an id made at random, and nothing else. The id says nothing about your search.",
            "Burro keeps the settings of this search under that id: renting or buying, the budget, "
                + "the places to reach, what counts, and any area you hid.",
            "It does not keep what you typed, and it does not keep who made the link.",
            "Anyone who has the link can see those settings, and the ranking they give.",
            "A link may stop working. Burro keeps only so many, and one made on older data may no longer open.",
        ]
        static let exact = "Share the exact places"
        static let exactHint =
            "Left unticked, each place you named is replaced by the station or district that stands in for it, "
            + "so that the link does not say where you work or study."
        static let exactHintHere =
            "Left off, each place you named is replaced by the station or district that stands in for it, "
            + "so that the link does not say where you work or study."
        static let make = "Make the link"
        static let makeAgain = "Make a new link"
        static let making = "Making the link"
        static let made = "The link is made."
        static let link = "Link to this search"
        static let share = "Share"
        static let coarsened =
            "A place you named was replaced by the station or district that stands in for it. "
            + "The ranking from this link may differ a little from yours."
        static let exactKept = "The link holds the places as you named them."
        static let noPlaces = "This search names no place, so the link holds none."
        static let failed = "The link could not be made."
        static let notAnId = "Burro sent a link that could not be read."
        static let gone = "The search has changed, so the link made before is no longer shown."
    }
}
