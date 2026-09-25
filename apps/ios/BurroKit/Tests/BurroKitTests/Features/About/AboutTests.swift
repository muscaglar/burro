import SwiftUI
import XCTest

@testable import BurroKit

/// About: the methods, the sources and their licences, the privacy notice, the
/// accessibility statement, and which release and engine the app is reading.
/// Everything about the release is what the meta route served.
final class AboutTests: XCTestCase {
    private let meta = Answers.meta

    // MARK: - The release and the engine

    func test_the_first_screen_names_the_release_and_the_engine_as_the_api_served_them() {
        let rows = AboutPage.release(meta)

        XCTAssertEqual(
            rows.map(\.name),
            ["Data release", "Ranking engine", "Built", "Made-up data", "A preview that is not finished"])
        XCTAssertEqual(rows[0].value, meta.releaseId)
        XCTAssertEqual(rows[1].value, meta.engineVersion)
        XCTAssertEqual(rows[2].value, "23 September 2026")
        XCTAssertEqual(rows[3].value, "Yes")
        XCTAssertEqual(rows[4].value, "No")
        XCTAssertEqual(rows.map(\.isCode), [true, true, false, false, false])
    }

    func test_the_methods_say_everything_the_release_says_of_itself() {
        let rows = AboutPage.releaseInFull(meta)
        let values = Dictionary(uniqueKeysWithValues: rows.map { ($0.name, $0.value) })

        XCTAssertEqual(rows.count, 11)
        XCTAssertEqual(values["Made-up data"], "Yes")
        XCTAssertEqual(values["A preview that is not finished"], "No")
        XCTAssertEqual(values["Release"], meta.releaseId)
        XCTAssertEqual(values["Version of the ranking engine"], meta.engineVersion)
        XCTAssertEqual(values["Version of the feature catalogue"], String(meta.catalogueVersion))
        XCTAssertEqual(values["Areas"], String(meta.counts.neighbourhoods))
        XCTAssertEqual(values["Areas that can be ranked"], String(meta.counts.rankable))
        XCTAssertEqual(values["Places you can name"], String(meta.counts.places))
        XCTAssertEqual(values["Stations"], String(meta.counts.stations))
        XCTAssertEqual(values["Points journeys are measured to"], String(meta.counts.destinations))
    }

    @MainActor
    func test_a_release_that_is_not_made_up_is_said_not_to_be() throws {
        let real = try Recorded.read("meta").with(data: { $0["synthetic"] = .bool(false) })
        let served = try JSONDecoder().decode(Envelope<MetaData>.self, from: real.body).data

        XCTAssertEqual(AboutPage.release(served).first { $0.name == "Made-up data" }?.value, "No")
    }

    func test_a_release_that_is_a_preview_is_said_to_be() throws {
        let preview: MetaData = try Recorded.data(.getMeta, "preview/meta")

        XCTAssertTrue(preview.preview)
        XCTAssertEqual(
            AboutPage.release(preview).first { $0.name == "A preview that is not finished" }?.value, "Yes")
        XCTAssertEqual(
            AboutPage.releaseInFull(preview).first { $0.name == "A preview that is not finished" }?.value,
            "Yes")
    }

    // MARK: - The methods

    func test_every_feature_of_the_release_is_described_once_under_its_group() {
        let groups = AboutPage.features(meta)
        let described = groups.flatMap(\.features)

        XCTAssertEqual(
            groups.map(\.title),
            [
                "Stations", "Green space and water", "Air and noise", "Venues and culture",
                "Shops and services", "Brands nearby", "Schools", "Homes",
                "Who lived there at the census", "Recorded crime",
            ])
        XCTAssertEqual(described.count, meta.features.count)
        XCTAssertEqual(Set(described.map(\.id)), Set(meta.features.map(\.featureId.rawValue)))
    }

    func test_a_feature_is_described_in_the_releases_own_words() throws {
        let walk = try XCTUnwrap(
            AboutPage.features(meta).flatMap(\.features).first { $0.metric.featureId == .stationWalk })
        let served = try XCTUnwrap(meta.features.first { $0.featureId == .stationWalk })

        XCTAssertEqual(walk.metric.label, served.label)
        XCTAssertEqual(walk.metric.definition, served.definition)
        XCTAssertEqual(
            walk.rows,
            [
                AboutRow(name: "Unit", value: served.unit),
                AboutRow(name: "Period", value: served.vintage),
                AboutRow(name: "What counts as better", value: "A lower figure counts as better"),
                AboutRow(name: "Source", value: "Synthetic test data"),
            ])
    }

    func test_each_vibe_is_shown_as_the_recipe_it_is_and_its_shares_add_up() {
        let tags = AboutPage.tags(meta)

        XCTAssertEqual(tags.map(\.tag.label), meta.tags.map(\.label))
        for tag in tags {
            XCTAssertEqual(tag.terms.count, tag.tag.terms.count)
            XCTAssertEqual(tag.tag.terms.map(\.hundredths).reduce(0, +), 100, tag.tag.label)
            XCTAssertTrue(tag.terms.allSatisfy { $0.share.hasSuffix(" of 100") })
            XCTAssertTrue(tag.terms.allSatisfy { !$0.reading.isEmpty && !$0.feature.isEmpty })
            // A term is named by the label of its feature, never by its id.
            XCTAssertFalse(tag.terms.contains { $0.feature.contains("_") })
        }
        // A vibe is said to be a band, one of five, and never a score.
        XCTAssertTrue(AboutCopy.Methods.tagsLead.contains("one of five bands"))
        XCTAssertTrue(AboutCopy.Methods.tagsLead.contains("never given a score"))
        XCTAssertEqual(AboutCopy.Methods.tagsTitle, "Vibes")
    }

    func test_a_part_of_a_recipe_the_release_does_not_carry_is_named_as_the_api_names_it() throws {
        let onFoot = try XCTUnwrap(AboutPage.tags(meta).first { $0.tag.tagId == .everydayOnFoot })
        let held = try XCTUnwrap(meta.recipes.first { $0.tagId == .everydayOnFoot })
        let carried = Set(meta.features.map(\.featureId))

        // The release carries no figure for the last two parts of this recipe.
        XCTAssertEqual(onFoot.tag.terms.map { carried.contains($0.featureId) }, [true, true, true, false, false])
        XCTAssertEqual(held.waitsOn.map(\.label), ["Straight-line distance to the nearest GP practice, placed by its postcode", "Straight-line distance to the nearest pharmacy, placed by its postcode"])
        // Each is named by the API's name for it, and said to be missing. It is never shown by its code.
        XCTAssertEqual(onFoot.terms.suffix(2).map(\.feature), held.waitsOn.map(\.label))
        for term in onFoot.terms.suffix(2) {
            XCTAssertTrue(term.reading.hasPrefix("Not in this data yet. "), term.feature)
        }
        for term in onFoot.terms.prefix(3) {
            XCTAssertFalse(term.reading.contains("Not in this data yet"), term.feature)
        }
        // A part the API names nowhere is said to be one the data does not carry.
        let unnamed = MetaData(
            releaseId: meta.releaseId, builtAt: meta.builtAt, synthetic: meta.synthetic, preview: meta.preview,
            engineVersion: meta.engineVersion, catalogueVersion: meta.catalogueVersion, counts: meta.counts,
            holds: meta.holds, attributions: meta.attributions, features: meta.features, tags: meta.tags,
            recipes: [], families: meta.families, grittyVariant: meta.grittyVariant, defaults: meta.defaults,
            limits: meta.limits, reader: meta.reader, census: meta.census, income: meta.income)
        let bare = try XCTUnwrap(AboutPage.tags(unnamed).first { $0.tag.tagId == .everydayOnFoot })
        XCTAssertEqual(
            bare.terms.suffix(2).map(\.feature),
            ["A part this data does not carry", "A part this data does not carry"])
    }

    func test_where_a_search_starts_is_shown_for_a_renter_and_for_a_buyer() {
        let starts = AboutPage.defaults(meta)

        XCTAssertEqual(starts.map(\.title), ["Renting", "Buying"])
        XCTAssertEqual(starts.first?.home, "One bedroom")
        XCTAssertEqual(starts.first?.rows.first, AboutRow(name: "Budget", value: "30 of 100. Flexible"))
        XCTAssertEqual(
            starts.first?.rows[1],
            AboutRow(
                name: "Journeys",
                value: "40 of 100. Only the journey that does worst against its limit counts. "
                    + "The typical time counts"))
        XCTAssertEqual(starts.first?.rows.count, 2 + meta.defaults.rent.weights.count)
        XCTAssertEqual(
            starts.first?.rows.last,
            AboutRow(name: "Straight-line distance to the nearest way in to a station", value: "50 of 100. Lower is better"))
    }

    func test_the_limits_are_the_ones_the_form_keeps_to() {
        let rows = AboutPage.limits(meta)
        let values = Dictionary(uniqueKeysWithValues: rows.map { ($0.name, $0.value) })

        XCTAssertEqual(values["Monthly rent"], "£300 to £20,000, in steps of £25")
        XCTAssertEqual(values["Purchase price"], "£50,000 to £20,000,000, in steps of £5,000")
        XCTAssertEqual(values["Longest journey you can set"], "10 to 120 minutes")
        XCTAssertEqual(values["Longest journey in this release: Public transport"], "90 minutes")
        XCTAssertEqual(values["Longest journey in this release: By bike"], "60 minutes")
        XCTAssertEqual(values["Longest journey in this release: On foot"], "60 minutes")
        XCTAssertEqual(values["Places you can ask to reach in one search"], "3")
        XCTAssertEqual(values["Length of a sentence"], "600 characters")
        XCTAssertEqual(values["Smallest change to how much something counts"], "5 of 100")
        XCTAssertEqual(rows.count, 9)
    }

    func test_how_sure_a_cost_is_is_said_as_the_contract_defines_it() throws {
        let contract = try Repository.text(Repository.root.appendingPathComponent("docs/design/contract.md"))

        XCTAssertTrue(
            contract.contains("High: at least \(AboutPage.recordedForHigh) observations."))
        XCTAssertTrue(
            contract.contains(
                "Medium: \(AboutPage.recordedForMedium) to \(AboutPage.recordedForHigh - 1), blended."))
        XCTAssertTrue(contract.contains("Low: modelled"))
        XCTAssertEqual(AboutPage.confidence.count, Confidence.allCases.count)
    }

    func test_the_lines_the_app_fills_in_come_out_as_the_website_writes_them() throws {
        let website = try Website.words().replacingOccurrences(of: "\\\"", with: "\"")

        for line in AboutPage.confidence + [
            AboutCopy.Methods.tagsLead, SearchCopy.Chips.assumedHint,
            SettingsCopy.Slider.range(WeightScale.least, WeightScale.most),
        ] {
            XCTAssertTrue(website.contains(line), line)
        }
    }

    func test_the_methods_say_how_a_rent_is_held_in_the_websites_words() throws {
        let website = try Website.words()

        XCTAssertEqual(AboutCopy.Methods.rentsPoints.count, 6)
        for point in AboutCopy.Methods.rentsPoints + [AboutCopy.Methods.rentsTitle] {
            XCTAssertTrue(website.contains(point), point)
        }
        // What is said of the rents themselves is the API's, and the app writes none of it.
        let meta: MetaData = try Recorded.data(.getMeta, "let/meta")
        let said = try XCTUnwrap(meta.rents)
        let copy = try Repository.text(Written.about.appendingPathComponent("AboutCopy.swift"))
        XCTAssertFalse(copy.contains(said.caution))
        XCTAssertFalse(copy.contains(said.ofAPlace))
        XCTAssertFalse(said.caution.contains(where: \.isNumber))
    }

    func test_the_methods_say_how_a_journey_is_timed_in_the_websites_words() throws {
        let website = try Website.words()

        XCTAssertEqual(AboutCopy.Methods.journeysPoints.count, 6)
        for point in AboutCopy.Methods.journeysPoints + [AboutCopy.Methods.confidenceLead] {
            XCTAssertTrue(website.contains(point), point)
        }
    }

    // MARK: - The sources and their licences

    func test_every_source_is_listed_with_its_licence_its_credit_and_what_it_is_used_for() throws {
        let sources = AboutPage.sources(meta)
        let first = try XCTUnwrap(sources.first)
        let served = try XCTUnwrap(meta.attributions.first)

        XCTAssertEqual(sources.map(\.id), meta.attributions.map(\.sourceId))
        XCTAssertEqual(first.source.name, served.name)
        XCTAssertEqual(first.source.attribution, served.attribution)
        XCTAssertEqual(
            first.rows,
            [
                AboutRow(name: "Publisher", value: served.publisher),
                AboutRow(name: "Licence", value: served.licence),
                AboutRow(name: "Retrieved", value: "23 September 2026"),
            ])
        XCTAssertEqual(
            Set(first.usedFor),
            Set(meta.features.filter { $0.sourceIds.contains(served.sourceId) }.map(\.label)))
        XCTAssertFalse(first.usedFor.isEmpty)
    }

    func test_a_source_with_no_page_says_none_and_offers_nothing_to_open() throws {
        let synthetic = try XCTUnwrap(AboutPage.sources(meta).first)

        XCTAssertEqual(synthetic.source.url, "")
        XCTAssertNil(synthetic.address)
        XCTAssertEqual(synthetic.addressWords, "None")
    }

    func test_an_address_is_opened_only_if_it_is_a_web_address() {
        XCTAssertEqual(
            AboutPage.webAddress("https://data.example.test/licence")?.absoluteString,
            "https://data.example.test/licence")
        XCTAssertEqual(AboutPage.webAddress(" http://data.example.test ")?.host, "data.example.test")
        // An address that carries a name and a word to get in with. It is put together
        // here, so that no file of the repository holds one.
        let withAWayIn = ["https://someone", "a-word@data.example.test"].joined(separator: ":")
        for field in [
            "", "   ", "data.example.test", "javascript:alert(1)", "file:///etc/hosts", "ftp://a.example.test",
            "tel:123", "burro://open", "https://", withAWayIn, "not an address",
        ] {
            XCTAssertNil(AboutPage.webAddress(field), field)
        }
        XCTAssertNotNil(URLComponents(string: withAWayIn)?.password)
    }

    @MainActor
    func test_a_source_that_has_a_page_is_shown_with_it() throws {
        let linked = try Recorded.read("meta").with(data: { data in
            data["attributions"] = data["attributions"]?.each {
                $0["url"] = .string("https://data.example.test/licence")
            }
        })
        let served = try JSONDecoder().decode(Envelope<MetaData>.self, from: linked.body).data

        let source = try XCTUnwrap(AboutPage.sources(served).first)

        XCTAssertEqual(source.address?.host, "data.example.test")
        XCTAssertEqual(source.addressWords, "https://data.example.test/licence")
    }

    @MainActor
    func test_what_is_said_with_a_credit_is_shown_with_it_and_with_no_other() throws {
        // The terms of a publisher may ask that something is said wherever its credit is
        // shown. The API brings it with the source, and the credit stays as it was worded.
        let said = "The publisher cannot warrant the quality or accuracy of the data."
        let asked = try Recorded.read("meta").with(data: { data in
            data["attributions"] = data["attributions"]?.each {
                $0["said_with_attribution"] = .string(said)
            }
        })
        let served = try JSONDecoder().decode(Envelope<MetaData>.self, from: asked.body).data

        let source = try XCTUnwrap(AboutPage.sources(served).first)

        XCTAssertEqual(source.said, said)
        XCTAssertEqual(source.source.attribution, try XCTUnwrap(meta.attributions.first).attribution)
        // The release that is recorded asks for nothing to be said, and nothing is.
        XCTAssertNil(try XCTUnwrap(AboutPage.sources(meta).first).said)
    }

    // MARK: - Dates

    func test_a_date_is_written_out_and_anything_else_is_shown_as_it_came() {
        XCTAssertEqual(AboutDate.readable("2026-09-23"), "23 September 2026")
        XCTAssertEqual(AboutDate.readable("2026-09-23T00:00:00Z"), "23 September 2026")
        XCTAssertEqual(AboutDate.readable("2026-01-01T23:59:59.5Z"), "1 January 2026")
        XCTAssertEqual(AboutDate.readable("2026-08"), "August 2026")
        for asItCame in ["2025", "2024-10 to 2026-09", "2026-13-40", "2026-02-30", "soon", "", "26-09-23", "2026-9-3"] {
            XCTAssertEqual(AboutDate.readable(asItCame), asItCame)
        }
    }

    // MARK: - The privacy notice, and the choice

    func test_the_notice_says_what_is_sent_to_whom_and_what_is_kept() {
        let served = meta.reader.notice
        let notice = AboutCopy.Words.points(reader: served)

        XCTAssertEqual(notice.first, SearchCopy.Permission.handled)
        // Who else reads what is typed is said second, in the API's words, as they were served.
        XCTAssertEqual(notice[1], served)
        XCTAssertFalse(served.isEmpty)
        XCTAssertTrue(notice.contains { $0.contains("never put in a web address") })
        XCTAssertTrue(notice.contains { $0.contains("shortlist is kept on this phone and nowhere else") })
        XCTAssertTrue(notice.contains { $0.contains("no analytics") })
        XCTAssertEqual(Set(notice).count, notice.count)
    }

    func test_the_notice_names_the_company_that_runs_a_model_only_as_the_api_serves_it() throws {
        let reads: MetaData = try Recorded.data(.getMeta, "meta-model-reads")
        let company = try XCTUnwrap(reads.reader.company)

        let notice = AboutCopy.Words.points(reader: reads.reader.notice)
        let unsaid = AboutCopy.Words.points(reader: nil)

        XCTAssertTrue(reads.reader.modelReads)
        XCTAssertTrue(notice[1].contains(company))
        // The app writes no provider's name of its own: with nothing served, none is said.
        XCTAssertFalse(unsaid.contains { $0.contains(company) })
        XCTAssertEqual(unsaid.count, notice.count - 1)
        let copy = try Repository.text(Written.about.appendingPathComponent("AboutCopy.swift"))
            + Repository.text(Written.search.appendingPathComponent("SearchCopy.swift"))
        XCTAssertFalse(copy.contains(company))
    }

    func test_what_the_notice_says_is_kept_is_what_is_kept() {
        // The notice names the shortlist, with its figures, and the choice. The store can hold
        // those three files, and no more.
        XCTAssertEqual(Set(KeptFile.allCases), [.shortlist, .consent, .savedAreas])
        XCTAssertTrue(AboutCopy.Words.shortlist.contains("shortlist"))
        XCTAssertTrue(AboutCopy.Words.shortlist.contains("the figures of each as they were that day"))
        XCTAssertTrue(AboutCopy.Words.choice.contains("choice"))
    }

    func test_what_the_notice_says_of_the_keyboard_is_what_the_app_does() throws {
        let app = try Repository.text(Repository.app.appendingPathComponent("BurroApp.swift"))
        let box = try Repository.text(
            Repository.sources.appendingPathComponent("Features/Search/PromptBox.swift"))

        // No keyboard but the phone's own.
        XCTAssertTrue(app.contains("@UIApplicationDelegateAdaptor(OwnKeyboardOnly.self)"))
        XCTAssertTrue(app.contains("shouldAllowExtensionPointIdentifier"))
        XCTAssertTrue(app.contains("extensionPointIdentifier != .keyboard"))
        // And every field a person types in asks it to leave what is typed alone.
        let fields = box.components(separatedBy: "TextField(").dropFirst()
        // The box, as it is where the system lets it select and where it does not, and the place field.
        XCTAssertEqual(fields.count, 3)
        for field in fields {
            let modifiers = String(field.prefix(700))
            XCTAssertTrue(
                modifiers.contains(".autocorrectionDisabled()") || modifiers.contains(".nameKeyboard()"))
        }
    }

    func test_about_says_which_choice_was_made() {
        XCTAssertEqual(AboutPage.choice(.allowed), "You allowed your words to be read.")
        XCTAssertEqual(AboutPage.choice(.settingsOnly), "You chose to use the settings. No sentence is sent.")
        XCTAssertEqual(AboutPage.choice(nil), "You have not chosen yet.")
    }

    @MainActor
    func test_the_choice_is_remembered_and_can_be_changed_and_nothing_typed_is_kept_with_it() async throws {
        let storage = MemoryPhoneStorage()
        let api = StandIn.firstSearch()
        let app = AppModel(api: api.api(), site: .none, synthetic: SyntheticNotice(), storage: storage)
        await app.open()
        app.consent.choose(.allowed)
        await app.search?.flow.submitText("leafy zqxcanary9043")

        app.consent.choose(.settingsOnly)
        let again = AppModel(api: api.api(), site: .none, synthetic: SyntheticNotice(), storage: storage)

        XCTAssertEqual(again.consent.choice, .settingsOnly)
        XCTAssertFalse(again.consent.mayReadWords)
        let kept = try XCTUnwrap(storage.read(.consent))
        XCTAssertEqual(
            try JSON.read(kept), .object(["version": .number(1), "choice": .string("settingsOnly")]))
        XCTAssertNil(storage.read(.shortlist))
    }

    func test_about_shows_the_screen_that_asked_again_and_the_screen_tells_it_when_it_is_done() throws {
        let about = try Repository.text(Written.about.appendingPathComponent("AboutRootView.swift"))
        let asked = try Repository.text(Written.search.appendingPathComponent("PermissionView.swift"))

        XCTAssertTrue(about.contains("PermissionView { asking = false }"))
        XCTAssertTrue(asked.contains("onChosen?()"))
    }

    // MARK: - The accessibility statement

    func test_the_statement_claims_nothing_that_has_not_been_done() {
        let copy = AboutCopy.Accessibility.self

        XCTAssertTrue(copy.lead.contains("has not been audited"))
        XCTAssertTrue(copy.lead.contains("nothing in it has yet been tried on a phone"))
        XCTAssertTrue(copy.notTested.contains("Use with VoiceOver."))
        XCTAssertTrue(copy.notTested.contains("Text at the largest sizes."))
        XCTAssertGreaterThanOrEqual(copy.notTested.count, 6)
        XCTAssertFalse(copy.short.isEmpty)
        XCTAssertTrue(copy.noAddressYet.contains("nowhere to send a report yet"))
        for claim in copy.built(target: 44) + copy.checked + [copy.lead] {
            for word in ["fully accessible", "compliant", "conforms", "meets", "certified", "WCAG"] {
                XCTAssertFalse(claim.contains(word), "\(claim): \(word)")
            }
        }
    }

    func test_what_the_statement_says_is_checked_is_checked() throws {
        let tests = Repository.files(under: Repository.tests, ending: ".swift")
            .compactMap { try? Repository.text(Repository.tests.appendingPathComponent($0)) }
            .joined()

        // One test for each line of "What is checked automatically".
        XCTAssertEqual(AboutCopy.Accessibility.checked.count, 4)
        XCTAssertTrue(tests.contains("func test_every_pair_that_must_contrast_does_in_light_and_in_dark"))
        XCTAssertTrue(tests.contains("func test_no_text_has_a_fixed_size"))
        XCTAssertTrue(tests.contains("func test_the_parts_are_always_drawn_in_one_order"))
        XCTAssertTrue(tests.contains("func test_every_slider_can_be_set_without_dragging"))
    }

    func test_the_statement_says_how_large_a_target_is_from_the_size_the_app_uses() {
        let built = AboutCopy.Accessibility.built(target: Int(Tokens.Target.least))

        XCTAssertTrue(built.contains("Anything that can be pressed is at least 44 points wide and high."))
    }

    func test_the_statement_is_dated() {
        XCTAssertEqual(AboutDate.readable(AboutPage.statementUpdated), "23 September 2026")
        XCTAssertNil(AboutDate.readable(DateComponents(year: 2026, month: 2, day: 30)))
    }

    // MARK: - Words

    /// The words that are the app's own. The rest are the website's, word for word.
    private let ownWords: Set<String> = [
        "How Burro works", "Your choice", "You allowed your words to be read.",
        "You chose to use the settings. No sentence is sent.", "You have not chosen yet.",
        "Read it again and choose", "The release is being read.", "The release could not be read.",
        "Opens in your browser",
        // The notice, where the app keeps what the website does not.
        "The app writes nothing of a search to your phone. A search lives in memory and is gone when you close the app.",
        "Your shortlist is kept on this phone and nowhere else. It holds the areas you saved, the day you saved each and the figures of each as they were that day, and nothing of the search that led to them.",
        "The choice you make about your words is kept on this phone too.",
        "A link to an area holds nothing of your search. A link to a search holds an id made at random, and the screen that makes one says what Burro keeps under it.",
        "There is no analytics in this app, no advertising, and no code from anyone else.",
        "Only your phone's own keyboard can be used in this app, and it is asked not to correct or to keep what you type in the search box.",
        // The website builds these lines from parts. The app passes the figures in.
        "\\(hundredths) of \\(WeightScale.most)", "£\\(least) to £\\(most), in steps of £\\(unit)",
        "\\(least) to \\(most) minutes", "\\(count) minutes", "\\(count) characters",
        "High: the range is worked out from at least \\(least) rents or prices recorded for that kind of home.",
        "Medium: from \\(least) to \\(most) were recorded, so the range is blended.",
        // The statement is the app's own: it says what is true of the app.
        "Burro is built to work with VoiceOver, with text at any size your phone offers, and without fine movement. It has not been audited, and nothing in it has yet been tried on a phone by a person.",
        "What the app is built to do",
        "Every map has a list that says everything the map shows.",
        "Every control is one of the phone's own, with a name a screen reader can say.",
        "Text follows the size you set on your phone. No text has a fixed size.",
        "Anything that can be pressed is at least \\(target) points wide and high.",
        "A slider has a minus and a plus button beside it, so nothing needs dragging.",
        "Nothing moves if your phone asks for less motion.",
        "The app follows your phone's light or dark setting.",
        "That no text has a fixed size.",
        "That what the search screen shows in each state of a search is in words, and in one order.",
        "That a number on a slider can be set with its buttons, and keeps to the steps Burro accepts.",
        "Nothing has yet been seen on a screen, so what falls short is not yet known.",
        "None of these has been checked by a person yet. Each will be, before the app is offered to the public.",
        "Use with VoiceOver.", "Text at the largest sizes.", "The real size of each control.",
        "Less motion, on a phone.", "Dark appearance, and increased contrast.",
        "The map, used with VoiceOver.", "Voice Control and Switch Control.",
        "There is nowhere to send a report yet. This is a test release on made-up data. An address will be given here before the app is offered to the public.",
    ]

    func test_every_word_is_the_websites_or_is_listed_as_the_apps_own() throws {
        let website = try Website.words()
        let words = try Written.words(in: Written.about.appendingPathComponent("AboutCopy.swift"))

        XCTAssertGreaterThan(words.count, 80)
        for said in words where !ownWords.contains(said) {
            XCTAssertTrue(Website.says(said, in: website), said)
        }
        for own in ownWords {
            XCTAssertTrue(words.contains(own), own)
        }
    }

    func test_the_words_hold_no_figure() throws {
        let words = try Written.words(in: Written.about.appendingPathComponent("AboutCopy.swift"))

        for said in words {
            XCTAssertFalse(said.contains(where: \.isNumber), said)
        }
    }

    // MARK: - The screens

    @MainActor
    func test_each_of_the_three_screens_is_made_as_the_shell_makes_it() {
        let screens: [any View] = [
            AboutRootView(), AboutScreenView(screen: .methods), AboutScreenView(screen: .sources),
            AboutScreenView(screen: .accessibility), MethodsScreen(), SourcesScreen(), AccessibilityScreen(),
        ]

        XCTAssertEqual(screens.count, 7)
    }

    func test_the_screens_that_show_the_release_wait_until_it_has_been_read() throws {
        let root = try Repository.text(Written.about.appendingPathComponent("AboutRootView.swift"))

        XCTAssertTrue(root.contains("Opened { MethodsScreen() }"))
        XCTAssertTrue(root.contains("Opened { SourcesScreen() }"))
        // The shell draws the banner. A screen does not draw its own.
        for file in try Written.files() {
            XCTAssertFalse(file.text.contains("SyntheticBanner"), file.name)
        }
    }
}
