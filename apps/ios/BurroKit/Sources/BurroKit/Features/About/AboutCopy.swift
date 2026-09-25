import Foundation

// The words of the About tab: what Burro is, how a person's words are
// handled, the methods, the sources and the accessibility statement.
//
// They say how Burro works, in words that stay true whatever release is
// loaded. Every figure on these screens comes from the API: no number is
// written here. Where the website has the words, these are the website's,
// from apps/web/src/content/. A test holds them to it, and lists the ones
// that are the app's own.

enum AboutCopy {
    /// What Burro is, in the website's words.
    static let what =
        "Describe the life you want and name the places you need to reach. "
        + "Burro ranks named neighbourhoods on a map and shows its working."

    enum Links {
        static let title = "How Burro works"
        static let methods = "Methods"
        static let sources = "Data sources"
        static let accessibility = "Accessibility"
    }

    /// The privacy notice.
    enum Words {
        static let title = "How your words are handled"
        static let body =
            "What you type travels in the body of a request. It is never put in a web address."
        static let memory =
            "The app writes nothing of a search to your phone. A search lives in memory and is gone "
            + "when you close the app."
        static let shortlist =
            "Your shortlist is kept on this phone and nowhere else. It holds the areas you saved, the day "
            + "you saved each and the figures of each as they were that day, and nothing of the search "
            + "that led to them."
        static let choice = "The choice you make about your words is kept on this phone too."
        static let link =
            "A link to an area holds nothing of your search. A link to a search holds an id made at "
            + "random, and the screen that makes one says what Burro keeps under it."
        static let nobodyElse =
            "There is no analytics in this app, no advertising, and no code from anyone else."
        static let keyboard =
            "Only your phone's own keyboard can be used in this app, and it is asked not to correct or "
            + "to keep what you type in the search box."

        /// Every point of the notice, in the order it is read. Who else reads
        /// what is typed is the API's to say: its words are drawn after the
        /// first point, as they were served, where the service has said.
        static func points(reader: String?) -> [String] {
            [SearchCopy.Permission.handled] + (reader.map { [$0] } ?? []) + [
                SearchCopy.Permission.model,
                body,
                memory,
                shortlist,
                choice,
                link,
                nobodyElse,
                keyboard,
            ]
        }
    }

    enum Choice {
        static let title = "Your choice"
        static let allowed = "You allowed your words to be read."
        static let settingsOnly = "You chose to use the settings. No sentence is sent."
        static let notChosen = "You have not chosen yet."
        static let change = "Read it again and choose"
    }

    enum Release {
        static let title = "This data release"
        static let release = "Data release"
        static let engine = "Ranking engine"
        static let opening = "The release is being read."
        static let failed = "The release could not be read."
    }

    enum Methods {
        static let title = "Methods"
        static let lead = "How Burro ranks areas, what it measures, and where each figure comes from."

        static let rankingTitle = "How the ranking works"
        static let ranking: [String] = [
            "Burro ranks areas by arithmetic over published data. The same search on the same data always gives the same ranking.",
            "Each thing you ask for is scored for each area, and the area's fit is the weighted average of those scores. Settings you did not choose count for less once you have asked for something.",
            "A firm limit removes an area that is known to break it. A flexible limit lowers the area's fit instead.",
            "When an area has no figure for something you asked for, that thing is left out for that area and the rest count for more. Nothing is filled in, and the result says how complete it is. Such an area stands below every area that has the figure, whatever its fit.",
            "An area with a figure for under half of what you asked of the place itself, by how much each thing counts, is not ranked. Journeys and cost do not make up for it. The area says what it lacks.",
            "Burro ranks places by what is there. Of the people who live in an area it counts two things, and only when you ask: how old they were and what their households were made of, when the census was taken. It counts nothing else about who lives anywhere, and you cannot ask for fewer of anyone.",
            SearchCopy.crimeRule,
            "When your words are not a plain list of what you want, Burro applies none of them. It shows what it noticed, and you choose what to add.",
            "A language model may read your words into settings. It never ranks or scores a place, and never describes one from its own knowledge.",
        ]

        static let featuresTitle = "What is measured"
        static let featuresLead =
            "Each feature describes a place, its buildings, what was recorded there, or who lived there at the census. A feature about residents says so in its name, and is of their age or their households and nothing else. The definition, the period and the source are as the data release states them."
        static let unit = "Unit"
        static let period = "Period"
        static let polarity = "What counts as better"
        static let sources = "Source"
        static let notRanked = "Shown, but not used in ranking in this release."
        static let noFeatures = "This release carries no feature in this group."

        static let tagsTitle = "Vibes"
        static let tagsLead =
            "A vibe is a fixed recipe over the features above. A vibe that counts who lived in an area says so, and counts their age or their households and nothing else. An area is placed in one of five bands among the areas compared, and never given a score."
        static func share(_ hundredths: Int) -> String { "\(hundredths) of \(WeightScale.most)" }
        /// In place of the name of a part that this data does not carry, where the API names none.
        static let notCarried = "A part this data does not carry"

        static let defaultsTitle = "Where a search starts"
        static let defaultsLead =
            "Before you say anything, a search starts from these settings. Nobody chose them, so they count for less as soon as you ask for something."
        static let budget = "Budget"
        static let journeys = "Journeys"
        static let home = "Size or type of home"

        static let limitsTitle = "Limits"
        static let limitsLead = "The form offers no value outside these limits."
        static let rent = "Monthly rent"
        static let buy = "Purchase price"
        static let minutes = "Longest journey you can set"
        static let cutoff = "Longest journey in this release"
        static let places = "Places you can ask to reach in one search"
        static let text = "Length of a sentence"
        static let weightStep = "Smallest change to how much something counts"
        static func money(_ least: String, _ most: String, _ unit: String) -> String {
            "£\(least) to £\(most), in steps of £\(unit)"
        }
        static func minutesBetween(_ least: Int, _ most: Int) -> String {
            "\(least) to \(most) minutes"
        }
        static func minutes(_ count: Int) -> String { "\(count) minutes" }
        static func characters(_ count: String) -> String { "\(count) characters" }

        /// How a journey is timed and how it counts, as contract 2.6, 6.3 and 6.4
        /// define it. It holds no figure: the longest journey a release holds is
        /// in the limits, from the API.
        static let journeysTitle = "How journeys are timed"
        static let journeysPoints: [String] = [
            "A journey is timed door to door, at the weekday morning peak.",
            "By public transport there are two times: the typical one, and the time if you just miss a service. The settings choose which of the two counts.",
            "By bike and on foot there is one time.",
            "A journey longer than this release holds a time for is given as more than that many minutes. The limits above say how many.",
            "A short journey counts in full. After that a journey counts for less the longer it is: for a half at the longest time you set, and for nothing at half as long again.",
            "With two places or more, only the journey that does worst against its own limit counts, unless you choose the average in the settings.",
        ]

        /// What each word for how sure a cost is means, as contract 2.5 defines
        /// it. The figures are passed in, and a test holds them to the contract.
        static let confidenceTitle = "How sure a cost is"
        static let confidenceLead =
            "Every range of rents or prices says how far it is to be trusted, in one word. A range is a guide to what homes cost in an area, and says nothing of any one home."
        static func high(atLeast least: Int) -> String {
            "High: the range is worked out from at least \(least) rents or prices recorded for that kind of home."
        }
        static func medium(from least: Int, to most: Int) -> String {
            "Medium: from \(least) to \(most) were recorded, so the range is blended."
        }
        static let low = "Low: the range is modelled."
        static let unstated =
            "Not stated: the figure is one number, the middle price of the homes of one kind that were sold in a year, as its publisher gives it. The publisher gives no range, and does not say how many sales the figure rests on."

        static let releaseTitle = "This data release"
        static let release = "Release"
        static let built = "Built"
        static let engine = "Version of the ranking engine"
        static let catalogue = "Version of the feature catalogue"
        static let synthetic = "Made-up data"
        static let preview = "A preview that is not finished"
        static let areas = "Areas"
        static let rankable = "Areas that can be ranked"
        static let placesCount = "Places you can name"
        static let stations = "Stations"
        static let destinations = "Points journeys are measured to"
        static let yes = "Yes"
        static let no = "No"
    }

    enum Sources {
        static let title = "Data sources and licences"
        static let lead =
            "Every figure Burro shows comes from one of these sources. Each is listed with its licence and the credit its publisher asks for."
        static let publisher = "Publisher"
        static let licence = "Licence"
        static let retrieved = "Retrieved"
        static let link = "Publisher's page"
        static let usedFor = "Used for"
        static let noLink = "None"
        static let notUsed = "No feature in this release"
        static let none = "This release names no source."
        /// Said of a link, which leaves the app for the phone's browser.
        static let opens = "Opens in your browser"
    }

    /// The statement must stay true. When a check below is made by hand, move
    /// it from `notTested` to `checked` and say when. Do not claim what has not
    /// been done.
    enum Accessibility {
        static let title = "Accessibility statement"
        static let lead =
            "Burro is built to work with VoiceOver, with text at any size your phone offers, and without fine movement. "
            + "It has not been audited, and nothing in it has yet been tried on a phone by a person."
        static let updated = "Last updated"

        static let builtTitle = "What the app is built to do"
        static func built(target: Int) -> [String] {
            [
                "Every map has a list that says everything the map shows.",
                "Every control is one of the phone's own, with a name a screen reader can say.",
                "Text follows the size you set on your phone. No text has a fixed size.",
                "Anything that can be pressed is at least \(target) points wide and high.",
                "Colour is never the only signal. Rank, fit and status are always given in words or figures.",
                "A slider has a minus and a plus button beside it, so nothing needs dragging.",
                "Nothing moves if your phone asks for less motion.",
                "The app follows your phone's light or dark setting.",
            ]
        }

        static let checkedTitle = "What is checked automatically"
        static let checked: [String] = [
            "The contrast of every colour pair, in light and in dark, against the ratio it needs.",
            "That no text has a fixed size.",
            "That what the search screen shows in each state of a search is in words, and in one order.",
            "That a number on a slider can be set with its buttons, and keeps to the steps Burro accepts.",
        ]

        static let shortTitle = "What is known to fall short"
        static let short: [String] = [
            "Nothing has yet been seen on a screen, so what falls short is not yet known."
        ]

        static let notTestedTitle = "What has not been tested"
        static let notTestedLead =
            "None of these has been checked by a person yet. Each will be, before the app is offered to the public."
        static let notTested: [String] = [
            "Use with VoiceOver.",
            "Text at the largest sizes.",
            "The real size of each control.",
            "Less motion, on a phone.",
            "Dark appearance, and increased contrast.",
            "The map, used with VoiceOver.",
            "Voice Control and Switch Control.",
        ]

        static let reportTitle = "How to report a problem"
        // There is no address yet. Do not invent one.
        static let noAddressYet =
            "There is nowhere to send a report yet. This is a test release on made-up data. "
            + "An address will be given here before the app is offered to the public."
    }
}
