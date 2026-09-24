import XCTest

@testable import BurroKit

/// The words of the search screen and of the settings. Where the website has
/// the words, the app's are the website's, word for word. The rest are listed
/// here, so that a word the app made up is never passed off as the website's.
final class SearchCopyTests: XCTestCase {
    /// The words that are the app's own, because the website has no such thing
    /// to name, or writes the figure into the line where the app passes it in.
    private let ownWords: Set<String> = [
        // The screen before the first search, from the concept of the app.
        "Before your first search", "What is sent", "Who reads it", "What is kept",
        "Burro keeps nothing you type. This app keeps your shortlist and the choice you make here on this phone, and nothing of a search.",
        "The settings do the same job with no language model.",
        "Allow and continue", "Use the settings instead", "You can change this in About.",
        "Your choice could not be saved on this phone. It holds until you close the app.",
        // What stands for the box when the person chose the settings.
        "You chose to use the settings. Nothing you type is sent to be read.", "Change this in About",
        // The results are on a screen of their own.
        "Show results",
        // What a screen reader is told of a chip and of an option.
        "Opens its setting", "Open", "Closed", "Add \\(place)",
        // A slider beside each number, and what it says its value is.
        "No budget set", "Most you can pay, on a slider", "Longest journey, on a slider",
        "£\\(amount)", "£\\(amount) a month", "\\(value) of \\(most)",
        // The website writes the figures into this line. The app passes them in.
        "From \\(least), which is not at all, to \\(most), which is as much as anything can.",
        // The two quote marks, which the website's source writes as escapes.
        "“", "”",
    ]

    private let files = ["SearchCopy.swift", "SettingsCopy.swift", "CodeCopy.swift"]

    private func written() throws -> [String] {
        try files.flatMap { try Written.words(in: Written.search.appendingPathComponent($0)) }
    }

    func test_every_word_is_the_websites_or_is_listed_as_the_apps_own() throws {
        let website = try Website.words()
        let words = try written()

        XCTAssertGreaterThan(words.count, 150)
        for said in words where !ownWords.contains(said) {
            XCTAssertTrue(Website.says(said, in: website), said)
        }
    }

    func test_every_word_listed_as_the_apps_own_is_one_the_app_says() throws {
        let words = Set(try written())

        for own in ownWords {
            XCTAssertTrue(words.contains(own), own)
        }
    }

    func test_no_word_listed_as_the_apps_own_is_one_the_website_has() throws {
        let website = try Website.words()

        // If the website gains the word, the app takes the website's, and the list loses it.
        for own in ownWords where own.count > 20 {
            XCTAssertFalse(website.contains("\"\(own)\""), own)
        }
    }

    func test_the_line_on_how_words_are_handled_is_the_websites() throws {
        let site = Website.joined(
            try Repository.text(Repository.root.appendingPathComponent("apps/web/src/content/site.ts")))

        XCTAssertTrue(site.contains("\"\(SearchCopy.Permission.handled)\""))
        // It is true whoever else reads the words, so it names nobody else and no period of keeping.
        XCTAssertFalse(SearchCopy.Permission.handled.contains(where: \.isNumber))
        XCTAssertFalse(SearchCopy.Permission.handled.lowercased().contains("model"))
    }

    func test_who_reads_is_said_in_the_apis_words_and_the_app_names_no_provider() throws {
        let rules = Answers.meta.reader
        let model: MetaData = try Recorded.data(.getMeta, "meta-model-reads")
        let company = try XCTUnwrap(model.reader.company)

        // The rules read, or a language model run by a company the API names.
        XCTAssertFalse(rules.modelReads)
        XCTAssertEqual(SearchScreen.whoReads(rules, opening: .open), WhoReads(words: rules.notice, said: true))
        XCTAssertTrue(model.reader.modelReads)
        XCTAssertEqual(SearchScreen.whoReads(model.reader, opening: .open).words, model.reader.notice)
        XCTAssertTrue(model.reader.notice.contains(company))

        // Until the service has said, the screen says that it is being asked, or that it has
        // not said, and a person cannot agree to what they have not been told.
        XCTAssertEqual(
            SearchScreen.whoReads(nil, opening: .opening),
            WhoReads(words: SearchCopy.Reader.checking, said: false))
        XCTAssertEqual(
            SearchScreen.whoReads(nil, opening: .failed(.because(.network))),
            WhoReads(words: SearchCopy.Reader.unsaid, said: false))

        // No file of the app's words names a provider, a period of keeping or terms.
        for file in try Written.files() {
            for name in Provider.allCases.map(\.rawValue) + [company] {
                XCTAssertFalse(file.text.lowercased().contains(name.lowercased()), "\(file.name): \(name)")
            }
        }
    }

    @MainActor
    func test_the_search_screen_shows_who_reads_as_the_api_served_it() throws {
        let model = try Recorded.read("meta-model-reads")
        let search = OpenSearch(StandIn.firstSearch())
        let served = try JSONDecoder().decode(Envelope<MetaData>.self, from: model.body).data
        search.store.dispatch(.releaseChanged(meta: served, areas: Answers.areas))

        XCTAssertEqual(search.shown().reader, served.reader.notice)
        XCTAssertEqual(OpenSearch().shown().reader, Answers.meta.reader.notice)
    }

    // MARK: - The screen before the first search

    func test_the_screen_says_what_is_sent_who_reads_it_and_what_is_kept() throws {
        let screen = try Repository.text(Written.search.appendingPathComponent("PermissionView.swift"))
        let said = [
            "Permission.sentTitle", "Permission.handled", "Permission.whoTitle", "who.words",
            "Permission.model", "Permission.keptTitle", "Permission.kept", "Permission.allow",
            "Permission.settingsInstead", "Permission.changeLater",
        ]

        var last = screen.startIndex
        for words in said {
            let found = try XCTUnwrap(screen.range(of: words), words)
            // Each is said, and in this order: what is sent, to whom, what is kept, the choice.
            XCTAssertGreaterThanOrEqual(found.lowerBound, last, words)
            last = found.lowerBound
        }
        // Who reads is what the API serves, and nobody can agree before it has said.
        XCTAssertTrue(screen.contains("SearchScreen.whoReads(app.search?.state.meta.reader"))
        XCTAssertTrue(screen.contains(".disabled(!who.said)"))
        XCTAssertTrue(SearchCopy.Permission.kept.contains("nothing you type"))
    }

    func test_the_screen_offers_two_choices_and_each_is_remembered() throws {
        let screen = try Repository.text(Written.search.appendingPathComponent("PermissionView.swift"))

        XCTAssertEqual(screen.components(separatedBy: "choose(.allowed)").count - 1, 1)
        XCTAssertEqual(screen.components(separatedBy: "choose(.settingsOnly)").count - 1, 1)
        XCTAssertTrue(screen.contains("app.consent.choose(choice)"))
        // It keeps the choice. It has no field, so there is nothing typed for it to keep.
        XCTAssertFalse(screen.contains("TextField"))
        XCTAssertFalse(screen.contains("TextEditor"))
    }

    // MARK: - The examples

    func test_the_examples_are_the_websites_three() throws {
        let search = try Repository.text(
            Repository.root.appendingPathComponent("apps/web/src/content/search.ts"))

        XCTAssertEqual(Examples.sentences.count, 3)
        for sentence in Examples.sentences {
            XCTAssertTrue(search.contains("\"\(sentence)\""), sentence)
        }
        // The rest of the sentences that are tried, and what each asks for, are the website's too.
        XCTAssertEqual(Examples.pool.count, 6)
        for example in Examples.pool {
            XCTAssertTrue(search.contains("\"\(example.text)\""), example.text)
            for asked in example.asks { XCTAssertTrue(search.contains("\"\(asked)\""), asked) }
        }
        XCTAssertEqual(Examples.offered(for: Answers.meta), Examples.sentences)
    }

    func test_an_example_is_offered_only_where_the_data_can_answer_all_of_it() throws {
        let preview: MetaData = try Recorded.data(.getMeta, "preview/meta")

        let offered = Examples.offered(for: preview)

        // The preview holds no cost, no journey and too little of most recipes.
        XCTAssertFalse(preview.holds.costs)
        XCTAssertEqual(offered, Examples.pool.suffix(3).map(\.text))
        for sentence in offered {
            let example = try XCTUnwrap(Examples.pool.first { $0.text == sentence })
            XCTAssertTrue(example.asks.allSatisfy { ReleaseHolds.canAnswer($0, in: preview) }, sentence)
            XCTAssertFalse(example.asks.contains("budget"), sentence)
        }
        XCTAssertFalse(offered.contains(Examples.sentences[0]))
    }

    func test_no_example_names_a_place() throws {
        var names = Answers.areas.map(\.name) + Answers.areas.map(\.borough)
        for scenario in ["places-search", "places-search-one-kind"] {
            let places: PlacesData = try Recorded.data(.searchPlaces, scenario)
            names += places.places.flatMap { [$0.name, $0.coarseName] }
        }

        for sentence in Examples.sentences {
            for name in names {
                XCTAssertFalse(sentence.localizedCaseInsensitiveContains(name), "\(sentence) names \(name)")
            }
            // No word after the first begins with a capital, as the name of a place would.
            let rest = sentence.split(separator: " ").dropFirst()
            XCTAssertFalse(rest.contains { $0.first?.isUppercase == true }, sentence)
            XCTAssertLessThanOrEqual(sentence.count, Answers.meta.limits.maxText)
        }
    }

    // MARK: - Words for codes

    func test_every_code_the_contract_lists_has_a_word() {
        XCTAssertFalse(UnmetCategory.allCases.contains { SearchCopy.unmet($0) == nil })
        XCTAssertFalse(RejectReason.allCases.contains { SearchCopy.rejected($0) == nil })
        XCTAssertFalse(OptionKind.allCases.contains { SearchCopy.kind($0) == nil })
        XCTAssertFalse(PlaceKind.allCases.contains { SearchCopy.kind($0) == nil })
        XCTAssertFalse(InterpreterName.allCases.contains { SearchCopy.readBy($0) == nil })
        XCTAssertFalse(Dimension.allCases.contains { CodeCopy.dimension($0) == nil })
        XCTAssertFalse(Polarity.allCases.contains { CodeCopy.polarity($0) == nil })
        XCTAssertFalse(Direction.allCases.contains { CodeCopy.direction($0) == nil })
        XCTAssertFalse(TermReading.allCases.contains { CodeCopy.reading($0) == nil })
        XCTAssertFalse(Tenure.allCases.contains { CodeCopy.tenure($0) == nil })
        XCTAssertFalse(Segment.allCases.contains { CodeCopy.segment($0) == nil })
        XCTAssertFalse(Mode.allCases.contains { CodeCopy.mode($0) == nil })
        XCTAssertFalse(Strictness.allCases.contains { CodeCopy.strictness($0) == nil })
        XCTAssertFalse(Combine.allCases.contains { CodeCopy.combine($0) == nil })
        XCTAssertFalse(PtBasis.allCases.contains { CodeCopy.basis($0) == nil })
        XCTAssertEqual(Set(CodeCopy.dimensionOrder), Set(Dimension.allCases))
        XCTAssertEqual(CodeCopy.dimensionOrder.last, .crime)
    }

    func test_a_code_this_build_does_not_know_has_no_word_and_so_is_left_out() {
        XCTAssertNil(SearchCopy.unmet(.unlisted("x")))
        XCTAssertNil(SearchCopy.rejected(.unlisted("x")))
        XCTAssertNil(SearchCopy.kind(OptionKind.unlisted("x")))
        XCTAssertNil(SearchCopy.kind(PlaceKind.unlisted("x")))
        XCTAssertNil(SearchCopy.readBy(.unlisted("x")))
        XCTAssertNil(CodeCopy.dimension(.unlisted("x")))
        XCTAssertNil(CodeCopy.segment(.unlisted("x")))
        XCTAssertNil(CodeCopy.mode(.unlisted("x")))
        XCTAssertNil(CodeCopy.tenure(.unlisted("x")))
    }

    func test_a_failure_of_the_apps_own_is_said_in_the_websites_words() throws {
        let website = try Website.words()

        for kind in ClientFailureKind.allCases where kind != .notConfigured {
            XCTAssertTrue(website.contains(SearchCopy.failure(kind)), kind.rawValue)
        }
        XCTAssertEqual(SearchCopy.failure(.offline), "You are offline. Your search is still here.")
    }

    // MARK: - No figure about a place, and nothing about who lives there

    func test_the_words_hold_no_figure() throws {
        // How long a provider keeps what it reads is the API's to say, and is written nowhere here.
        XCTAssertEqual(try written().filter { $0.contains(where: \.isNumber) }, [])
    }

    func test_no_word_is_about_who_lives_somewhere() throws {
        let about = [
            "resident", "people who live", "families", "students", "young", "elderly", "affluent",
            "deprived", "ethnic", "religio", "income", "class", "demographic", "community feel",
        ]
        for said in try written() + Examples.sentences {
            // The one line that names a community says Burro has no data on it.
            if said.contains("Burro has no data on places of worship") { continue }
            for word in about {
                XCTAssertFalse(said.lowercased().contains(word), "\(said): \(word)")
            }
        }
    }
}
