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
        /// How Burro itself handles a person's words: the website's line under
        /// its box, word for word. It is true whoever else reads them, and it
        /// names nobody else. Who else reads what is typed, what is sent with
        /// it, how long it is kept and where, are the API's to say, and are
        /// shown as they are served.
        static let handled = "What you type is sent to Burro to be read, and Burro does not keep it."
        static let whoTitle = "Who reads it"
        static let model =
            "A language model may read your words into settings. It never ranks or scores a place, "
            + "and never describes one from its own knowledge."
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

    /// What stands where the API's notice will stand, until the service has
    /// said who reads what is typed. No sentence is sent before it has.
    enum Reader {
        static let label = "Who reads what you type"
        static let checking =
            "Burro is asking the service who else reads what you type. Nothing is sent until it has said."
        static let unsaid =
            "The service has not said who else reads what you type, so nothing you type is sent."
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
        /// The hint where the data cannot answer all of it. It asks only for
        /// what can be answered, and says what cannot.
        static func hint(costs: Bool, journeys: Bool) -> String {
            if costs && journeys { return hint }
            if costs {
                return "Say what you can pay and what you want nearby. This data holds no journey times yet."
            }
            if journeys {
                return
                    "Say where you need to get to and what you want nearby. This data holds no rents and no prices yet."
            }
            return "Say what you want nearby. This data holds no rents, no prices and no journey times yet."
        }
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
        /// In place of the name of a place, where an answer named a place and gave no name for it.
        static let noName = "A place with no name in this data"
        /// In place of the field, where the data names no place: no spelling could match.
        static let notInData =
            "This data names no places yet, so Burro cannot work out a journey. "
            + "Nothing you type here could match."
        /// What a press on an option does, for a person who cannot see that it is a button in a list.
        static func add(_ place: String) -> String { "Add \(place)" }
    }

    enum Status {
        static let reading = "Reading your search"
        /// The whole of what is said of a first ranking: how many areas, and which is first.
        static func ranked(_ count: Int, first: String) -> String {
            [rankedUnnamed(count), Status.first(first)].joined(separator: " ")
        }
        /// The first result, by name.
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
            switch count {
            case 0: return "No area changed place."
            case 1: return "\(count) area changed place."
            default: return "\(count) areas changed place."
            }
        }
        /// Said when the settings nobody chose came to count for less.
        static let gaveWay = "What you asked for counts most."
        /// Said in its place where a journey or a budget counts for more than
        /// anything that was asked of the place. A person who asked for leafy
        /// and quiet must not read the first result as the leafiest.
        static func leads(journeys: Int, budget: Bool) -> String {
            guard journeys > 0 else { return "Budget counts most." }
            let who = journeys == 1 ? "Journey" : "Journeys"
            let counts = budget ? " and budget count" : journeys == 1 ? " counts" : " count"
            return who + counts + " most."
        }
        static let nothingMatches = "No area passes every limit you set."
        /// Said in its place where no limit left any area out: every area has
        /// too little data for what counts.
        static let nothingRanked =
            "No area could be ranked. This data holds too little of what counts in your search."
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
        /// A scale, and the end of it that is asked for. Both names are the API's.
        static func towards(_ vibe: String, _ end: String) -> String { "\(vibe): towards \(end)" }
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
        /// Said when the provider of the language model would not read what was typed. It names nobody.
        static let refused = "The language model would not read this. Burro's rules have read it instead."
        /// A sentence that Burro reads whole, to show what it can read. It names no place.
        static let readable = "leafy and quiet, near a park"
        /// The website writes the sentence between quote marks. So does this.
        static var nothingRead: String {
            "Nothing in that could be read. Burro reads plain English, such as \(open)\(readable)\(close). "
                + "Say it another way, or use the settings below."
        }
        private static let open = "“"
        private static let close = "”"
        static let nothingChanged = "That changed nothing. Your search already says it."
        /// Beside the box, when only a part of what was typed was read.
        static let partLabel = "What was not read"
        static let partUnread =
            "Burro read only part of what you typed, and the ranking leaves the rest out. "
            + "Say the rest again in shorter sentences, one thing in each, or use the settings."
        static func partShown(_ at: Int, of: Int) -> String {
            of == 1
                ? "The part that was not read is selected in the box."
                : "Part \(at) of the \(of) that were not read is selected in the box."
        }
        static let partNotFound = "Burro cannot show which part it was."
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

    /// What the reader noticed in a prompt it did not apply. What an offer would
    /// do, what follows from it and the words of each choice are the API's.
    enum Suggest {
        static let title = "Choose what to add"
        /// Under the heading, in one line: that nothing is added until it is pressed.
        static let why = "Nothing is added until you press it."
        /// Beside the way Burro reads the words. It marks a choice, and applies nothing.
        static let guess = "Burro's guess"
        /// Before the person's own words, which are cut from the box by where they stand.
        static let wrote = "You wrote"
        /// While a model reads what the rules left unread. What the rules noticed is on the screen.
        static let reading = "Burro is still reading the rest of your words."
        /// The one button that adds every thing in sight that one press may add.
        static func addAll(_ count: Int) -> String { "Add all \(count)" }
        /// The same, where a thing that is the person's to choose is in sight as well.
        static func addThese(_ count: Int) -> String { "Add the \(count) that need no choice" }
        /// What one press did, in full: how many it added, how many areas a firm budget
        /// among them left out, and what is left for the person, which the API names.
        /// `leftOut` is `nil` where no firm budget was among them, and until the ranking
        /// that follows is in. `since` is what the person has chosen of since, offer by
        /// offer: it is said straight after what the press added, so that it is the first
        /// thing read when the line changes.
        static func added(
            _ count: Int, needs: [String], leftOut: Int? = nil, heldAgainst: String? = nil,
            since: (added: Int, skipped: Int) = (0, 0)
        ) -> String {
            var said = ["\(count) added."]
            if let then = Self.since(since.added, since.skipped) { said.append(then) }
            if let leftOut { said.append(Self.leftOut(leftOut, heldAgainst: heldAgainst)) }
            if !needs.isEmpty {
                let verb = needs.count == 1 ? "needs" : "need"
                let listed = needs.joined(separator: "; ") + "."
                said += [String(needs.count), verb, "you:", listed]
            }
            return said.joined(separator: " ")
        }
        /// How many areas a firm budget left out, as the API lists them, and where each is
        /// listed. `heldAgainst` is what the API says of the rents the budget was held
        /// against, where each is of a postcode district or a borough: the line says so, in
        /// the API's words.
        static func leftOut(_ count: Int, heldAgainst: String? = nil) -> String {
            let of = heldAgainst.map { heldAgainst in " \(heldAgainst)" } ?? ""
            guard count > 0 else { return "Your budget is a firm limit. It left no area out.\(of)" }
            // The figure is passed in and never written here: the words hold none.
            let (areas, which) = count == 1 ? ("\(count) area", "it") : ("\(count) areas", "each")
            return
                "Your budget is a firm limit and left out \(areas): the table of all areas lists \(which).\(of)"
        }
        /// How many offers were added and how many skipped since one press, each by its
        /// own button. `nil` where none was.
        static func since(_ added: Int, _ skipped: Int) -> String? {
            if added > 0 && skipped > 0 { return "Then \(added) more added, and \(skipped) skipped." }
            if added > 0 { return "Then \(added) more added." }
            return skipped > 0 ? "Then \(skipped) skipped." : nil
        }
        static let takeBack = "Take it all back"
        /// A choice that is said of every suggestion, named by the thing it is a choice of.
        static func named(_ choice: String, _ thing: String) -> String { "\(choice): \(thing)" }
        /// Over the field where a place is chosen for a journey whose place Burro does not know.
        static let whichPlace = "Which place?"
        /// Over the places the release holds that are like the one that was typed.
        static let alike = "Places like it"
        static let showWords = "Show the words"
        static func showWordsOf(_ thing: String) -> String { "Show the words in the box: \(thing)" }
        static func showAll(_ count: Int) -> String { "Show all \(count)" }
        /// The one line that what is left folds to, once one press has added what it may.
        /// It says how many are left, under the line that names each, and opens them all.
        static func showLeft(_ count: Int) -> String {
            count == 1 ? "Show the one left to choose" : "Show the \(count) left to choose"
        }
        /// Selects, in the box, a part of what was typed that the reader made nothing of.
        static let showUnread = "Show in the box"
        static let showNextUnread = "Show the next in the box"
        /// Beside the button, where a part of what was typed was not read.
        static let unread = "Some of your words were not read."
        static let wordsShown = "The words are selected in the box."
    }

    /// What was asked for that the data does not hold yet. The name of each
    /// thing and the name of each part it waits on are the API's.
    enum NotInData {
        static let title = "Not in this data yet"
        static func lead(_ count: Int) -> String {
            count == 1
                ? "You asked for one thing this data cannot answer yet. It counts for nothing in the ranking."
                : "You asked for \(count) things this data cannot answer yet. They count for nothing in the ranking."
        }
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
        case .model: return "Read by AI. Check what it understood."
        case .rule: return "Read without AI."
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
            return "Burro has no data on health services other than GP surgeries and pharmacies, so that part was left out."
        case .driving:
            return "Burro does not work out journeys by car. It covers public transport, cycling and walking."
        case .listings: return "Burro does not show homes to rent or to buy. It ranks areas."
        case .affordabilityVerdict:
            return "Burro does not say what you can afford. It shows what homes cost in each area."
        case .communityAmenities:
            return
                "Burro has no data on places of worship, or on shops and venues for one community, so that part was left out."
        case .outsideTheCity: return "Burro covers one city. A place outside it was left out."
        case .streetCleanliness:
            return "Burro has no measure of how clean a street is, so that part was left out."
        case .upkeep: return "Burro has no measure of how well kept a place is, so that part was left out."
        case .ratings: return "Burro has no ratings or reviews of any place, so that part was left out."
        case .pricesAndHours:
            return "Burro has no data on what a place charges or when it opens, so that part was left out."
        case .mobileCoverage: return "Burro has no data on mobile signal, so that part was left out."
        case .changeOverTime:
            return "Burro has no measure of how an area is changing, so that part was left out."
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
        case .crimeNeedsExplicitRequest: return crimeRule
        case .mismatchedChoice: return "That setting does not take that choice."
        case .nothingToChange: return "That changed nothing."
        case .unlisted: return nil
        }
    }

    /// When recorded crime counts, said one way wherever it is said.
    static let crimeRule =
        "Recorded crime counts only when you ask for it by name, switch it on in the settings, "
        + "or ask for a vibe whose recipe holds it."
    /// Said after it where no vibe of the release holds recorded crime.
    static let crimeNoVibe = "In this data no vibe holds it."
    /// On the chip of a vibe whose recipe holds recorded crime, after its name.
    static let crimeChip = "counts recorded crime"
    /// Beside such a vibe in the settings, before the parts of its recipe that are of crime.
    static let crimeCounts = "This vibe counts recorded crime"

    /// Words for a call that gave no answer, when the reason is not the API's own.
    /// They are the shell's, which are the website's.
    static func failure(_ kind: ClientFailureKind) -> String {
        kind == .offline ? Notice.offline : ShellCopy.words(for: kind)
    }
}
