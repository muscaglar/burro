import XCTest

@testable import BurroKit

/// A vibe that is a rough guide says so wherever the app shows it: its label
/// and the sentence that says why, as route 11 serves them. The app writes
/// neither, and works out from nothing which vibe is one. Decided on
/// 2026-09-25: docs/adr/0013, as amended, and docs/design/web.md.
final class RoughGuideTests: XCTestCase {
    private let meta = Answers.meta
    /// What route 11 serves of Village feel, in one line.
    private let said =
        "Rough guide. Of the areas it puts highest, about half read as villages to people, "
        + "and it takes some busy main roads and some grand inner streets for villages."

    private func tag(_ tagId: TagId) throws -> Tag {
        try XCTUnwrap(meta.tags.first { $0.tagId == tagId })
    }

    /// The search the recording was made of, asking for one vibe in place of Village feel.
    private func asking(for tagId: TagId, weight: Double = 0.5) -> PreferenceSpec {
        let spec = Answers.ranked("rank-rough-guide").spec
        return PreferenceSpec(
            schemaVersion: spec.schemaVersion, tenure: spec.tenure, budget: spec.budget,
            commutes: spec.commutes, commuteCombine: spec.commuteCombine, ptBasis: spec.ptBasis,
            commuteWeight: spec.commuteWeight, weights: spec.weights,
            tags: [TagWeight(tagId: tagId, weight: weight, provenance: .stated, toward: .high)],
            areas: spec.areas, tenureFrom: spec.tenureFrom, commuteCombineFrom: spec.commuteCombineFrom,
            ptBasisFrom: spec.ptBasisFrom, commuteWeightFrom: spec.commuteWeightFrom)
    }

    private func chips(_ spec: PreferenceSpec) -> [SearchChip] {
        SearchChips.of(
            spec, features: meta.features, tags: meta.tags, areas: Answers.areas, placeNames: [:],
            assumed: [:], guides: meta.roughGuides)
    }

    // MARK: - Whose words they are

    func test_which_vibe_is_a_rough_guide_and_what_it_says_of_itself_are_the_apis() throws {
        XCTAssertEqual(meta.roughGuides.map(\.tagId), [.villageFeel])
        XCTAssertEqual(meta.tags.filter { $0.sureness == .roughGuide }.map(\.tagId), [.villageFeel])

        let told = try XCTUnwrap(Vibes.rough(try tag(.villageFeel), in: meta.roughGuides))

        XCTAssertEqual(told.label, "Rough guide")
        XCTAssertEqual(Vibes.said(told), said)
        for other in meta.tags where other.tagId != .villageFeel {
            XCTAssertEqual(other.sureness, .asTheRest, other.label)
            XCTAssertNil(Vibes.rough(other, in: meta.roughGuides), other.label)
        }
    }

    func test_with_no_words_from_the_api_nothing_is_said_because_the_app_has_none_of_its_own() throws {
        XCTAssertNil(Vibes.rough(try tag(.villageFeel), in: []))
        // Words that are served for a vibe that does not say it is one are said of no vibe.
        let misfiled = [RoughGuide(tagId: .leafy, label: "Rough guide", why: "No reason.")]
        XCTAssertNil(Vibes.rough(try tag(.leafy), in: misfiled))
        XCTAssertNil(Vibes.rough(try tag(.villageFeel), in: misfiled))
    }

    func test_a_vibe_that_does_not_say_is_as_sure_as_the_rest() throws {
        // An answer written before the API said it of any vibe holds no such key.
        var written = try JSON.written(try tag(.villageFeel))
        XCTAssertEqual(written["sureness"], .string("rough_guide"))
        written["sureness"] = nil

        let read = try JSONDecoder().decode(Tag.self, from: written.data)

        XCTAssertEqual(read.sureness, .asTheRest)
        XCTAssertNil(Vibes.rough(read, in: meta.roughGuides))
        var answer = try JSON.written(meta)
        answer["rough_guides"] = nil
        XCTAssertEqual(try JSONDecoder().decode(MetaData.self, from: answer.data).roughGuides, [])
    }

    // MARK: - In a search

    func test_its_chip_bears_its_label_and_the_line_under_the_chips_says_why() throws {
        let ranked = Answers.ranked("rank-rough-guide")
        let state = reduce(
            SearchState(meta: meta, areas: Answers.areas),
            .rankAnswered(ranked, sent: Edits.tagOn(.villageFeel)))

        let chip = try XCTUnwrap(SearchChips.of(state).first { $0.kind == .tag(.villageFeel) })

        XCTAssertEqual(chip.reads, "Village feel, Rough guide")
        XCTAssertEqual(chip.removal, Edits.tagOff(.villageFeel))
        XCTAssertEqual(SearchChips.rough(in: state.spec, meta: meta), ["Village feel: \(said)"])
        // It is the first of the lines that explain the chips, which are drawn with nothing pressed.
        XCTAssertEqual(
            SearchScreen.chipsHints(SearchChips.of(state), state, readBy: nil).first,
            "Village feel: \(said)")
    }

    func test_nothing_is_said_in_a_search_that_holds_no_such_vibe_or_that_took_it_off() {
        let leafy = asking(for: .leafy)
        let off = asking(for: .villageFeel, weight: 0)

        XCTAssertEqual(SearchChips.rough(in: leafy, meta: meta), [])
        XCTAssertEqual(chips(leafy).first { $0.kind == .tag(.leafy) }?.reads, "Leafy")
        XCTAssertEqual(SearchChips.rough(in: off, meta: meta), [])
        // Taken off, the chip says that it counts for nothing, and no more.
        XCTAssertEqual(
            chips(off).first { $0.kind == .tag(.villageFeel) }?.reads,
            "Village feel, \(SearchCopy.Chips.off)")
        // With no words from the API the chip is the name alone.
        XCTAssertEqual(
            SearchChips.of(
                asking(for: .villageFeel), features: meta.features, tags: meta.tags, areas: Answers.areas,
                placeNames: [:], assumed: [:]
            ).first { $0.kind == .tag(.villageFeel) }?.reads, "Village feel")
    }

    // MARK: - Its offer

    func test_its_offer_says_both_in_the_apis_note_and_one_press_never_takes_it() throws {
        let read = Answers.read("interpret-suggest-rough-guide")

        let offers = try XCTUnwrap(SearchScreen.offers(read.suggestions, all: true))

        XCTAssertEqual(offers.offers.map(\.name), ["Leafy", "Quiet streets", "Village feel"])
        XCTAssertEqual(offers.offers.map(\.note), [nil, nil, said])
        XCTAssertEqual(offers.offers.map(\.noteDrawn), [false, false, true])
        // No way of it is marked as Burro's guess, and the one button adds the other two alone.
        XCTAssertEqual(offers.offers[2].choices.map(\.guess), [false, false])
        XCTAssertEqual(offers.addAllAts, [0, 1])
        XCTAssertEqual(offers.addAll, SearchCopy.Suggest.addThese(2))
        XCTAssertNil(read.suggestions[2].addedWithOthers)
        // Nothing of the sentence was applied.
        XCTAssertEqual(read.spec.tags.filter { $0.weight > 0 }.map(\.tagId), [])
    }

    // MARK: - On a result, on the page of an area, in a comparison

    @MainActor
    func test_on_a_result_the_line_of_the_vibe_says_so_under_its_band_and_no_other_line_does() throws {
        let ranked = Answers.ranked("rank-rough-guide")
        let first = try XCTUnwrap(ranked.ranked.first)

        let strip = Vibes.strip(first.strip, meta: meta, facts: [:])

        let village = try XCTUnwrap(strip.first { $0.tagId == .villageFeel })
        XCTAssertEqual(village.rough, said)
        XCTAssertEqual(village.asked, "asked for")
        // It is the first thing under the band, and is read out with the rest of the line.
        XCTAssertEqual(VibeLine.notes(of: village).first, said)
        XCTAssertTrue(village.reads.contains(said))
        XCTAssertEqual(strip.filter { $0.tagId != .villageFeel }.map(\.rough), [nil, nil])
        // A result shows the vibe only where it was asked for.
        for area in ranked.ranked {
            XCTAssertEqual(area.strip.filter { $0.tagId == .villageFeel }.map(\.asked), [true], area.areaId)
        }
        for area in Answers.ranked("rank-first").ranked {
            XCTAssertFalse(area.strip.contains { $0.tagId == .villageFeel }, area.areaId)
        }
    }

    @MainActor
    func test_on_the_page_of_an_area_it_says_so_under_its_band_whether_or_not_the_area_is_placed() throws {
        for slug in ["thrushcombe", "otterby-fields"] {
            let page = AreaFixtures.page(slug)
            let village = try XCTUnwrap(page.vibes.first { $0.shown.tagId == .villageFeel })

            XCTAssertEqual(village.shown.rough, said, slug)
            XCTAssertEqual(VibeLine.notes(of: village.shown).first, said, slug)
            XCTAssertEqual(page.vibes.filter { $0.shown.rough != nil }.count, 1, slug)
            // It is among what an area has most or least of for no area.
            XCTAssertFalse([.more, .less].contains(village.list), slug)
        }
    }

    @MainActor
    func test_a_saved_area_says_it_with_no_connection_and_a_file_written_before_says_nothing() throws {
        let page = AreaFixtures.page("thrushcombe")

        let kept = KeptArea(page, savedOn: Date(timeIntervalSince1970: 1_790_000_000))

        let village = try XCTUnwrap(kept.vibes.first { $0.tagId == "village_feel" })
        XCTAssertEqual(village.rough, said)
        XCTAssertEqual(village.vibe(of: page.area.areaId).shown.rough, said)
        XCTAssertEqual(kept.vibes.filter { $0.rough != nil }.count, 1)
        // A file that was written before the API said it of any vibe is read, and says nothing.
        var written = try JSON.written(village)
        written["rough"] = nil
        XCTAssertNil(try JSONDecoder().decode(KeptVibe.self, from: written.data).rough)
    }

    func test_in_a_comparison_every_area_under_the_vibe_says_so() throws {
        let data: CompareData = try Recorded.data(.compare, "compare-three")
        let facts = Dictionary(data.facts.map { ($0.factId, $0) }, uniquingKeysWith: { first, _ in first })

        let compared = Results.character(data, facts: facts, meta: meta)

        let village = try XCTUnwrap(compared.first { $0.tagId == .villageFeel })
        XCTAssertEqual(village.cells.map(\.vibe.rough), [said, said, said])
        for other in compared where other.tagId != .villageFeel {
            XCTAssertEqual(other.cells.compactMap(\.vibe.rough), [], other.name)
        }
    }

    // MARK: - Where the vibes are set out

    func test_where_the_recipes_are_set_out_it_says_so_under_its_name() throws {
        let tags = AboutPage.tags(meta)

        XCTAssertEqual(tags.first { $0.tag.tagId == .villageFeel }?.rough, said)
        XCTAssertEqual(tags.filter { $0.rough != nil }.map(\.tag.tagId), [.villageFeel])
    }
}
