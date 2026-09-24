import Foundation
import Observation

/// The search for a place to reach, as a person types.
///
/// What is typed is held by the field it was typed in. It is handed here one
/// key at a time, waits a moment in case another key follows, goes into the
/// body of one call, and is then let go. This object keeps the places that
/// came back, and nothing of what was typed.
@MainActor
@Observable
final class PlaceSearch {
    /// How long after the last key the search is sent, in seconds.
    static let wait = 0.25

    enum Status: Hashable, Sendable {
        case idle
        case searching
        case found(Int)
        case none
        case failed

        /// What is said under the field. Nothing while there is nothing to say.
        var words: String {
            switch self {
            case .idle: return ""
            case .searching: return SearchCopy.Place.searching
            case .found(let count): return SearchCopy.Place.found(count)
            case .none: return SearchCopy.Place.none
            case .failed: return SearchCopy.Place.failed
            }
        }
    }

    /// One place that was found, as its row says it.
    struct Option: Hashable, Sendable, Identifiable {
        let place: FoundPlace
        var id: String { place.placeId }
        var name: String { place.name }
        /// What it is, and where, when it stands inside somewhere with another name.
        var detail: String {
            let kind = SearchCopy.kind(place.kind) ?? ""
            guard place.coarseName != place.name, !place.coarseName.isEmpty else { return kind }
            let within = "\(SearchCopy.Place.within) \(place.coarseName)"
            return kind.isEmpty ? within : "\(kind), \(within)"
        }
    }

    private(set) var options: [Option] = []
    private(set) var status: Status = .idle

    @ObservationIgnored private let search: @MainActor (String) async -> Answer<PlacesData>
    @ObservationIgnored private let wait: Double
    @ObservationIgnored private var latest = 0
    @ObservationIgnored private var looking: Task<Void, Never>?

    /// - Parameters:
    ///   - wait: How long after the last key the search is sent. A test passes less.
    ///   - search: Route 8. What is typed goes in the body of the call and nowhere else.
    init(wait: Double = PlaceSearch.wait, search: @escaping @MainActor (String) async -> Answer<PlacesData>) {
        self.wait = wait
        self.search = search
    }

    /// Told of what the field holds, each time it changes.
    func typed(_ text: String) {
        halt()
        let said = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard said.count >= SearchFlow.placeQuery.least else {
            options = []
            status = .idle
            return
        }
        let mine = latest
        let wait = wait
        let asked = String(said.prefix(SearchFlow.placeQuery.most))
        looking = Task { @MainActor [weak self] in
            try? await Task.sleep(nanoseconds: UInt64(max(0, wait) * 1_000_000_000))
            guard let self, !Task.isCancelled, mine == self.latest else { return }
            self.status = .searching
            let answer = await self.search(asked)
            // An answer to what was typed before the last key is dropped.
            guard !Task.isCancelled, mine == self.latest else { return }
            switch answer {
            case .success(let found):
                self.options = found.data.places.map(Option.init)
                self.status = found.data.places.isEmpty ? .none : .found(found.data.places.count)
            case .failure:
                self.options = []
                self.status = .failed
            }
        }
    }

    /// A place was picked, or the field was emptied: the list goes.
    func clear() {
        halt()
        options = []
        status = .idle
    }

    /// Waits for whatever search is out. Nothing on a screen needs it. A test does.
    func settled() async {
        await looking?.value
    }

    private func halt() {
        latest += 1
        looking?.cancel()
        looking = nil
    }
}
