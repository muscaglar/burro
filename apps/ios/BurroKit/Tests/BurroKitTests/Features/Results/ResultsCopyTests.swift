import XCTest

@testable import BurroKit

/// The words of the results screen. Where the website has the words, these
/// are the website's, word for word. The few the app adds are listed here,
/// each with its reason.
final class ResultsCopyTests: XCTestCase {
    /// Words the website does not have, and why the app does.
    private let ours: [String: String] = [
        "Show the results as":
            "The name of the control that chooses the list, the map or the table. The website has tabs with no name.",
        "No area chosen yet. Choose two to four.":
            "The website shows no tray until an area is chosen. The app's can be opened with none.",
        "Height of the list": "The panel over the map is the app's own.",
        "Half": "A height of the panel.",
        "Full": "A height of the panel.",
        "Swipe up or down to change the height": "How the panel's handle is worked with a screen reader.",
        "Make the list taller": "A way to set the height without a drag.",
        "Make the list shorter": "A way to set the height without a drag.",
        "Your words could not be read just now. The settings do the same job.":
            "The website's line says the settings are below. Here they are on another screen.",
        "The boundaries of the areas could not be loaded. The table says everything the map would.":
            "The website's line says the table is below. Here it is one press away.",
        "A comparison takes two to four areas. Choose areas from the results.":
            "The website's line names an area's page, which does not choose areas in the app.",
        "Left off, each place you named is replaced by the station or district that stands in for it,":
            "The website's line says unticked. The app has a switch.",
        "Loading": "The name of the room kept for what has not come, for a screen reader.",
        "Chosen on the map": "Says in words which card is the chosen one.",
        "Open the page": "A short name for a button. The area's name is said after it.",
        "Hide this area": "A short name for a button. The area's name is said after it.",
        "Show on the map": "A short name for a button. The area's name is said after it.",
        "Add to compare": "A short name for a button. The area's name is said after it.",
        "Add to shortlist": "The design kit's words for what the app adds.",
        "Remove from shortlist": "The design kit's words for what the app adds.",
        "to shortlist": "The design kit's words, with the area's name in them.",
        "from shortlist": "The design kit's words, with the area's name in them.",
        "Kept on this phone. Burro does not hold it.": "The design kit's words for what the app adds.",
        "The shortlist could not be saved to this phone.": "The website keeps nothing, so it has no such line.",
        "Each ranked area is marked with its fit.": "The app writes the fit on the map. The website does not.",
        "Open": "Whether a part that opens in place is open, for a screen reader.",
        "Closed": "Whether a part that opens in place is open, for a screen reader.",
        "Share": "The design kit's word for the button that opens the phone's share sheet.",
        "Burro sent a link that could not be read.": "The website says this of any answer. Here it is of a link.",
        "The search has changed, so the link made before is no longer shown.":
            "The website drops the link without a word. The app says why it went.",
    ]

    /// Every piece of fixed text in the copy: each string, cut at each gap a name or a figure fills.
    private func pieces() throws -> [String] {
        let source = try Repository.text(
            Repository.sources.appendingPathComponent("Features/Results/ResultsCopy.swift"))
        let code = source.split(separator: "\n", omittingEmptySubsequences: false)
            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            .joined(separator: "\n")
        let strings = code.components(separatedBy: "\"").enumerated()
            .filter { $0.offset % 2 == 1 }.map(\.element)
        let gap = try NSRegularExpression(pattern: #"\\\([^)]*\)"#)
        return strings.flatMap { string -> [String] in
            let range = NSRange(string.startIndex..., in: string)
            return gap.stringByReplacingMatches(in: string, range: range, withTemplate: "\u{1}")
                .components(separatedBy: "\u{1}")
                .map { $0.trimmingCharacters(in: .whitespaces) }
                .filter { $0.count >= 3 }
        }
    }

    private func website() throws -> String {
        let folder = Repository.root.appendingPathComponent("apps/web/src/content")
        return try Repository.files(under: folder, ending: ".ts")
            .map { try Repository.text(folder.appendingPathComponent($0)) }
            .joined(separator: "\n")
    }

    func test_every_word_is_the_websites_or_is_listed_here_with_its_reason() throws {
        let website = try website()
        let pieces = try pieces()

        XCTAssertGreaterThan(pieces.count, 200)
        let strangers = Set(pieces.filter { !website.contains($0) && ours[$0] == nil })
        XCTAssertEqual(strangers, [])
    }

    func test_nothing_is_listed_as_the_apps_own_that_the_copy_does_not_hold() throws {
        let pieces = Set(try pieces())
        let website = try website()

        for (words, reason) in ours {
            XCTAssertTrue(pieces.contains(words), words)
            XCTAssertFalse(reason.isEmpty)
            // What the website has is the website's, and is not listed as ours.
            XCTAssertFalse(website.contains("\"\(words)\""), words)
        }
    }

    func test_the_copy_holds_no_figure_and_names_no_place() throws {
        let source = try Repository.text(
            Repository.sources.appendingPathComponent("Features/Results/ResultsCopy.swift"))
        let strings = source.components(separatedBy: "\"").enumerated()
            .filter { $0.offset % 2 == 1 }.map(\.element)

        XCTAssertEqual(strings.filter { $0.contains(where: \.isNumber) }, [])
        for place in Answers.areas.map(\.name) + Answers.areas.map(\.borough) {
            XCTAssertFalse(source.contains(place), place)
        }
        // A word about who lives somewhere, or about how safe a place is, is never the app's to say.
        for word in ["safe", "unsafe", "dangerous", "residents", "community of", "demographic"] {
            XCTAssertFalse(strings.contains { $0.lowercased().contains(word) }, word)
        }
    }

    func test_every_code_the_contract_lists_has_a_word_and_a_code_it_does_not_has_none() {
        for reason in FilterReason.allCases {
            XCTAssertNotNil(ResultsCopy.word(for: reason))
            XCTAssertNotNil(ResultsCopy.untested(reason))
        }
        for reason in UnrankedReason.allCases { XCTAssertNotNil(ResultsCopy.word(for: reason)) }
        for reason in RejectReason.allCases { XCTAssertNotNil(ResultsCopy.word(for: reason)) }
        for status in CompareStatus.allCases { XCTAssertNotNil(ResultsCopy.word(for: status)) }
        for mode in Mode.allCases { XCTAssertNotNil(ResultsCopy.word(for: mode)) }
        for confidence in Confidence.allCases { XCTAssertNotNil(ResultsCopy.word(for: confidence)) }
        for template in TemplateId.allCases { XCTAssertNotNil(ResultsCopy.kind(of: template)) }

        // A code this build does not know is left out, and never shown as a blank or as the code.
        XCTAssertNil(ResultsCopy.word(for: FilterReason.unlisted("new")))
        XCTAssertNil(ResultsCopy.untested(.unlisted("new")))
        XCTAssertNil(ResultsCopy.word(for: UnrankedReason.unlisted("new")))
        XCTAssertNil(ResultsCopy.word(for: RejectReason.unlisted("new")))
        XCTAssertNil(ResultsCopy.word(for: CompareStatus.unlisted("new")))
        XCTAssertNil(ResultsCopy.word(for: Mode.unlisted("new")))
        XCTAssertNil(ResultsCopy.word(for: Confidence.unlisted("new")))
        XCTAssertNil(ResultsCopy.kind(of: .unlisted("new")))
    }

    func test_a_code_the_build_does_not_know_draws_nothing() throws {
        var state = SearchState(meta: Answers.meta, areas: Answers.areas)
        let first = Answers.ranked("rank-first")
        state.ranking = Ranking(
            scores: Array(first.scores.dropFirst(2)), ranked: [],
            filtered: [Filtered(areaId: first.scores[0].areaId, reason: .unlisted("new_reason"))],
            unranked: [Unranked(areaId: first.scores[1].areaId, reason: .unlisted("other_reason"), missing: [])],
            emptySpec: false)
        state.selectedId = first.scores[0].areaId

        let drawn = ResultsDrawn.all(in: Results.listed(state)).texts
            + ResultsDrawn.all(in: Results.tabled(state)).texts
            + ResultsDrawn.all(in: Results.mapped(state, on: Results.Ground(Answers.geometry))).texts

        XCTAssertFalse(drawn.contains { $0.contains("new_reason") || $0.contains("other_reason") })
        XCTAssertEqual(Results.nothingMatches(of: state)?.counts, [])
        XCTAssertNil(Results.chosen(of: state)?.words)
        // The pattern still marks it, and the table still lists it.
        XCTAssertEqual(Results.fills(state.ranking)[first.scores[0].areaId]?.pattern, .filtered)
        XCTAssertEqual(Results.tabled(state).rows.count, 24)
    }

    func test_one_is_said_as_one_and_many_as_many() {
        XCTAssertEqual(ResultsCopy.Status.ranked(1, first: "A"), "1 area ranked. First: A.")
        XCTAssertEqual(ResultsCopy.Status.ranked(22, first: "A"), "22 areas ranked. First: A.")
        XCTAssertEqual(ResultsCopy.Status.leads(journeys: 1, budget: true), "Journey and budget count most.")
        XCTAssertEqual(ResultsCopy.Status.leads(journeys: 2, budget: true), "Journeys and budget count most.")
        XCTAssertEqual(ResultsCopy.Status.leads(journeys: 1, budget: false), "Journey counts most.")
        XCTAssertEqual(ResultsCopy.Status.leads(journeys: 2, budget: false), "Journeys count most.")
        XCTAssertEqual(ResultsCopy.Status.leads(journeys: 0, budget: true), "Budget counts most.")
        XCTAssertEqual(ResultsCopy.Status.rankedUnnamed(1), "1 area ranked.")
        XCTAssertEqual(ResultsCopy.Status.rankedUnnamed(3), "3 areas ranked.")
        XCTAssertEqual(ResultsCopy.Status.rankedNoOrder(1), "1 area passes. Nothing is set to rank it by.")
        XCTAssertEqual(ResultsCopy.Status.moved(0), "No area changed place.")
        XCTAssertEqual(ResultsCopy.Status.moved(1), "1 area changed place.")
        XCTAssertEqual(ResultsCopy.Status.moved(4), "4 areas changed place.")
        XCTAssertEqual(ResultsCopy.NothingMatches.count(1), "1 area")
        XCTAssertEqual(ResultsCopy.NothingMatches.count(2), "2 areas")
        XCTAssertEqual(ResultsCopy.CompareTable.standing(rank: 3, fit: nil), "Rank 3")
        XCTAssertEqual(ResultsCopy.CompareTable.standing(rank: 3, fit: 61), "Rank 3. Fit 61 of 100")
    }

    func test_the_list_names_the_first_result_it_has_a_name_for_and_gives_the_count_alone_with_none() {
        var state = SearchState(meta: Answers.meta, areas: Answers.areas)
        state = reduce(state, .rankAnswered(Answers.ranked("rank-first"), sent: .none))
        XCTAssertEqual(Results.headline(of: state), "21 areas ranked. First: Farrowmere.")

        state.areas = []

        XCTAssertEqual(Results.headline(of: state), "21 areas ranked.")
        // An area the app has no name for is not drawn as its id.
        XCTAssertEqual(Results.listed(state).cards, [])
    }
}
