import Foundation

// The words of the search screen. They name controls and states, and say how a
// person's words are handled. None is about a place, and none holds a figure:
// where a line has a gap in it, the gap is filled with a name or a number the
// API sent, or with a count the screen worked out.
//
// Where the website has the words, these are the website's, word for word,
// from apps/web/src/content/search.ts. A test holds them to it, and lists the
// few that are the app's own.

enum SearchCopy {
    /// The screen shown once, before the first sentence is sent, and again from About.
    enum Permission {
        static let title = "Before your first search"
        static let sentTitle = "What is sent"
        /// The website's line under its box, word for word.
        static let handled =
            "What you type is sent to Burro to be read, and Burro does not keep it. "
            + "If a language model reads it, the model's provider may keep it for up to 30 days, "
            + "or longer if it is flagged."
        static let whoTitle = "Who reads it"
        static let model =
            "A language model may read your words into settings. It never ranks or scores a place, "
            + "and never describes one from its own knowledge."
        static let otherCompany = "The language model is run by another company, not by Burro."
        static let keptTitle = "What is kept"
        static let kept =
            "Burro keeps nothing you type. This app keeps your shortlist and the choice you make here "
            + "on this phone, and nothing of a search."
        static let eitherWay = "The settings do the same job with no language model."
        static let allow = "Allow and continue"
        static let settingsInstead = "Use the settings instead"
        static let changeLater = "You can change this in About."
        static let couldNotSave =
            "Your choice could not be saved on this phone. It holds until you close the app."
    }

    /// What stands where the box would, for a person who chose the settings.
    enum Declined {
        static let line = "You chose to use the settings. Nothing you type is sent to be read."
        static let change = "Change this in About"
    }

    enum Prompt {
        static let formLabel = "Your search"
        static let label = "Describe the life you want"
        static let hint = "Say what you can pay, where you need to get to, and what you want nearby."
        static let submit = "Search"
        static let reading = "Reading"
        static let stop = "Stop"
        static let tryAgain = "Try again"
        static let startAgain = "Start again"
        static func left(_ count: Int) -> String {
            count == 1 ? "\(count) character left" : "\(count) characters left"
        }
        static let empty = "Type what you are looking for first, or use the settings below."
        static let wordsLink = "How your words are handled"
        static let examplesTitle = "Examples"
        static let examplesHint = "An example fills the box. Nothing is sent until you press Search."
    }

    enum TenureChoice {
        static let legend = "Renting or buying"
        static let rent = "Renting"
        static let buy = "Buying"
    }

    enum Place {
        static let label = "A place you need to reach"
        static let hint = "A station, a workplace, a school or a district. Type two letters or more."
        static let searching = "Searching"
        static let none = "No place matches. Try another spelling, or a place nearby."
        static func found(_ count: Int) -> String {
            count == 1 ? "\(count) place found" : "\(count) places found"
        }
        static let failed = "Places could not be searched just now."
        static func full(_ most: Int) -> String {
            most == 1
                ? "You have named \(most) place, which is the most."
                : "You have named \(most) places, which is the most."
        }
        static let options = "Places that match"
        static let within = "in"
        /// The name of a place the app was never told the name of.
        static func unnamed(_ position: Int) -> String { "Place \(position)" }
        /// Said under the chips while a place is shown by number. `unnamed` is how
        /// many are, and `named` how many places the search holds in all. The
        /// number is where the data lists the place, so with more than one place
        /// it is said not to be the order they were named in.
        static func unnamedHint(_ unnamed: Int, of named: Int) -> String {
            let shown =
                unnamed == 1
                ? "Burro cannot show the name of one place you named yet, so it is shown by number."
                : "Burro cannot show the names of \(unnamed) places you named yet, so they are shown by number."
            guard named > 1 else { return shown }
            let order =
                "The numbers are the order the data lists your places in, not the order you named them in."
            return [shown, order].joined(separator: " ")
        }
        /// What a press on an option does, for a person who cannot see that it is a button in a list.
        static func add(_ place: String) -> String { "Add \(place)" }
    }

    enum Status {
        static let reading = "Reading your search"
        static func ranked(_ count: Int, first: String) -> String {
            count == 1 ? "\(count) area ranked: \(first)." : "\(count) areas ranked. First: \(first)."
        }
        static func rankedUnnamed(_ count: Int) -> String {
            count == 1 ? "\(count) area ranked." : "\(count) areas ranked."
        }
        static func rankedNoOrder(_ count: Int) -> String {
            count == 1
                ? "\(count) area passes. Nothing is set to rank it by."
                : "\(count) areas pass. Nothing is set to rank them by, so they are in no order."
        }
        static func moved(_ count: Int) -> String {
            switch count {
            case 0: return "No area changed place."
            case 1: return "\(count) area changed place."
            default: return "\(count) areas changed place."
            }
        }
        static let gaveWay = "Settings you did not choose now count for less."
        static let nothingMatches = "No area passes every limit you set."
        static let question = "Burro has a question about a place."
        /// The list is on another screen, so the way to it is a button here.
        static let showResults = "Show results"
    }

    enum Chips {
        /// The heading of the chips once words have been read into a search.
        static let label = "What Burro understood"
        /// The heading before anything has changed the search: nobody said any of it.
        static let startLabel = "What a search starts from"
        /// The heading of a search that no words were read into: one made with the settings, or a shared one.
        static let setLabel = "What this search holds"
        static let assumed = "assumed"
        /// The website writes the word between quote marks. So does this.
        static var assumedHint: String {
            "A part marked \(quote)\(assumed)\(quote) is one you did not say. Burro filled it in, and you can change it."
        }
        private static let quote = String(UnicodeScalar(UInt8(34)))
        static let remove = "Remove"
        static let firm = "firm limit"
        static let flexible = "flexible"
        static func within(_ minutes: Int) -> String { "within \(minutes) minutes" }
        static let more = "more"
        static let fewer = "fewer"
        static let hidden = "hidden"
        static let only = "only"
        static let off = "does not count"
        static func usual(_ count: Int) -> String { "Usual settings: \(count)" }
        static let usualHint =
            "Usual settings are ones nobody chose. They count for less once you ask for something."
        static let openSettings = "Press it to open the settings."
        /// Said of a chip that opens its control in place, for a person who cannot see the mark.
        static let opens = "Opens its setting"
        static let open = "Open"
        static let closed = "Closed"
    }

    enum Notice {
        static let label = "About your search"
        static let degraded = "Your words could not be read just now. The settings below do the same job."
        static let nothingRead =
            "Nothing in that could be read as a setting. Say it another way, or use the settings below."
        static let nothingChanged = "That changed nothing. Your search already says it."
        static let offline = "You are offline. Your search is still here."
        static let offlineWaiting = "Your last change will be sent when you are back online."
        static let notUpdated = "These results were not updated."
        static let requestId = "If you report this, quote"
        static let stale = "Your search names something this data no longer has."
        static func takeOut(_ what: String) -> String { "Take \(what) out" }
        static let thePlace = "the place"
        static let theArea = "the area"
        static let theSetting = "the setting"
        static let unmetLabel = "What could not be answered"
        static let rejectedLabel = "What was not applied"
    }

    enum Question {
        static let place = "Which place did you mean?"
        static let area = "Which area did you mean?"
        static func numbered(_ at: Int, of: Int) -> String { "Question \(at) of \(of)." }
        static let search = "Or search for the place"
        static let leaveOut = "Leave it out"
        static let none = "Burro did not find the place you named. Search for it here."
    }

    /// Who read the words. `nil` for a reader this build has no word for.
    static func readBy(_ interpreter: InterpreterName) -> String? {
        switch interpreter {
        case .claude: return "Read by AI. Check what it understood."
        case .rule: return "Read without AI, by fixed rules."
        case .unlisted: return nil
        }
    }

    /// What a place is. `nil` for a kind this build has no word for.
    static func kind(_ kind: OptionKind) -> String? {
        switch kind {
        case .station: return "Station"
        case .district: return "District"
        case .postcodeDistrict: return "Postcode district"
        case .university: return "University"
        case .hospital: return "Hospital"
        case .school: return "School"
        case .landmark: return "Landmark"
        case .area: return "Area"
        case .unlisted: return nil
        }
    }

    /// The same words, for a place the place search found.
    static func kind(_ kind: PlaceKind) -> String? {
        self.kind(OptionKind(rawValue: kind.rawValue))
    }

    /// One line for a thing that was asked for and cannot be answered.
    static func unmet(_ category: UnmetCategory) -> String? {
        switch category {
        case .broadband: return "Burro has no data on broadband, so that part was left out."
        case .floodRisk: return "Burro has no data on flood risk, so that part was left out."
        case .healthServices:
            return "Burro has no data on health services nearby, so that part was left out."
        case .driving:
            return "Burro does not work out journeys by car. It covers public transport, cycling and walking."
        case .listings: return "Burro does not show homes to rent or to buy. It ranks areas."
        case .affordabilityVerdict:
            return "Burro does not say what you can afford. It shows what homes cost in each area."
        case .communityAmenities:
            return
                "Burro has no data on places of worship, or on shops and venues for one community, so that part was left out."
        case .outsideTheCity: return "Burro covers one city. A place outside it was left out."
        case .other: return "Part of what you typed could not be read. Say it another way, or use the settings."
        case .unlisted: return nil
        }
    }

    /// Why an edit was not applied.
    static func rejected(_ reason: RejectReason) -> String? {
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
            return "Recorded crime counts only when you ask for it by name, or switch it on in the settings."
        case .mismatchedChoice: return "That setting does not take that choice."
        case .nothingToChange: return "That changed nothing."
        case .unlisted: return nil
        }
    }

    /// Words for a call that gave no answer, when the reason is not the API's own.
    /// They are the shell's, which are the website's.
    static func failure(_ kind: ClientFailureKind) -> String {
        kind == .offline ? Notice.offline : ShellCopy.words(for: kind)
    }
}
