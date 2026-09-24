import XCTest

@testable import BurroKit

/// The search for a place to reach, as a person types.
final class PlaceSearchTests: XCTestCase {
    @MainActor
    private func model(_ api: StandIn, wait: Double = 0.01) -> (PlaceSearch, OpenSearch) {
        let search = OpenSearch(api)
        return (PlaceSearch(wait: wait) { await search.flow.searchPlaces($0) }, search)
    }

    @MainActor
    func test_one_letter_is_too_few_and_sends_nothing() async {
        let (places, search) = model(StandIn().on(.searchPlaces, "places-search"))

        places.typed("p")
        places.typed("  p  ")
        await places.settled()

        XCTAssertEqual(search.api.calls.count, 0)
        XCTAssertEqual(places.status, .idle)
        XCTAssertEqual(places.status.words, "")
    }

    @MainActor
    func test_the_search_is_sent_once_a_moment_after_the_last_key() async throws {
        let (places, search) = model(StandIn().on(.searchPlaces, "places-search"))

        places.typed("pe")
        places.typed("pel")
        places.typed(" pell ")
        await places.settled()

        XCTAssertEqual(search.api.calls(to: .searchPlaces).count, 1)
        XCTAssertEqual(
            try search.api.lastCall(to: .searchPlaces).body(as: PlaceSearchBody.self),
            PlaceSearchBody(q: "pell", limit: 8))
        XCTAssertEqual(places.status, .found(3))
        XCTAssertEqual(places.status.words, "3 places found")
        XCTAssertEqual(places.options.map(\.name), ["Pellam Cross", "Pellam Exchange", "Pellam Infirmary"])
    }

    @MainActor
    func test_a_place_is_said_with_what_it_is_and_where_it_stands() async {
        let (places, _) = model(StandIn().on(.searchPlaces, "places-search"))

        places.typed("pel")
        await places.settled()

        XCTAssertEqual(places.options.map(\.detail), ["Station", "District", "Hospital, in Coracle Row"])
    }

    @MainActor
    func test_an_answer_to_what_was_typed_before_the_last_key_is_dropped() async {
        let api = StandIn()
        let first = api.hold(.searchPlaces, "places-search")
        let (places, _) = model(api, wait: 0)

        places.typed("pel")
        await until { first.waiting == 1 }
        api.on(.searchPlaces, "places-search-one-kind")
        places.typed("school")
        first.release()
        await places.settled()

        XCTAssertEqual(places.options.first?.name, "Kindlewharf School of Art")
        XCTAssertFalse(places.options.contains { $0.name == "Pellam Cross" })
    }

    @MainActor
    func test_nothing_found_and_a_search_that_failed_are_each_said() async {
        let (none, _) = model(StandIn().on(.searchPlaces, "places-search-none"))
        let (failed, _) = model(StandIn().unreachable(.searchPlaces))

        none.typed("zzzz")
        failed.typed("pel")
        await none.settled()
        await failed.settled()

        XCTAssertEqual(none.status, .none)
        XCTAssertEqual(none.status.words, "No place matches. Try another spelling, or a place nearby.")
        XCTAssertEqual(none.options, [])
        XCTAssertEqual(failed.status, .failed)
        XCTAssertEqual(failed.status.words, "Places could not be searched just now.")
    }

    @MainActor
    func test_what_is_sent_is_never_longer_than_the_api_takes() async throws {
        let (places, search) = model(StandIn().on(.searchPlaces, "places-search"))

        places.typed(String(repeating: "a", count: 200))
        await places.settled()

        XCTAssertEqual(try search.api.lastCall(to: .searchPlaces).body(as: PlaceSearchBody.self).q.count, 80)
    }

    @MainActor
    func test_emptying_the_field_or_picking_a_place_takes_the_list_away() async {
        let (places, search) = model(StandIn().on(.searchPlaces, "places-search"))
        places.typed("pel")
        await places.settled()

        places.typed("")
        XCTAssertEqual(places.options, [])
        XCTAssertEqual(places.status, .idle)
        places.typed("pel")
        places.clear()
        await places.settled()

        XCTAssertEqual(places.options, [])
        XCTAssertEqual(places.status, .idle)
        XCTAssertEqual(search.api.calls(to: .searchPlaces).count, 1)
    }

    @MainActor
    func test_one_place_found_is_said_as_one() {
        XCTAssertEqual(PlaceSearch.Status.found(1).words, "1 place found")
        XCTAssertEqual(PlaceSearch.Status.searching.words, "Searching")
    }

    @MainActor
    func test_a_place_that_is_picked_becomes_a_journey_by_its_id() async throws {
        let (places, search) = model(StandIn.firstSearch().on(.searchPlaces, "places-search"))
        places.typed("pel")
        await places.settled()
        let picked = try XCTUnwrap(places.options.last)

        await search.flow.addPlace(picked.place)

        XCTAssertEqual(
            try search.api.lastCall(to: .rank).body(as: RankBody.self).operations,
            Edits.placeAdd("syn-p0028"))
        XCTAssertEqual(search.state.placeNames["syn-p0028"], "Pellam Infirmary")
    }

    @MainActor
    func test_when_no_more_places_can_be_named_the_screen_says_so_in_place_of_the_field() async {
        let search = OpenSearch(
            StandIn.firstSearch().on(.interpret, "interpret-two-journeys").on(.rank, "rank-two-journeys"))

        await search.flow.submitText("two journeys")
        XCTAssertNil(search.shown().placesFull)

        XCTAssertEqual(Answers.meta.limits.maxCommutes, 3)
        XCTAssertEqual(SearchCopy.Place.full(3), "You have named 3 places, which is the most.")
        XCTAssertEqual(SearchCopy.Place.full(1), "You have named 1 place, which is the most.")
    }
}
