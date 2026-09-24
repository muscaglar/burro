import Observation

/// The search that is open: the one object a screen watches.
///
/// It holds the state in memory and nowhere else. A screen reads `state` and
/// asks `flow` to do things. Nothing but `reduce` makes a new state, and
/// nothing but the flow sends an event.
@MainActor
@Observable
public final class SearchStore {
    public private(set) var state: SearchState

    /// What a person can do to the search, as the calls each thing makes.
    @ObservationIgnored
    public private(set) lazy var flow: SearchFlow = SearchFlow(
        api: api, store: self, mayReadWords: mayReadWords)

    @ObservationIgnored private let api: any BurroAPI
    @ObservationIgnored private let mayReadWords: @MainActor () -> Bool

    /// - Parameters:
    ///   - api: The API to call. A test passes a stand-in.
    ///   - mayReadWords: Whether the person has agreed that their words may be
    ///     read. Until they have, no sentence is sent.
    public init(
        meta: MetaData,
        areas: [AreaSummary],
        geometry: GeometryData? = nil,
        api: any BurroAPI,
        mayReadWords: @escaping @MainActor () -> Bool
    ) {
        state = SearchState(meta: meta, areas: areas, geometry: geometry)
        self.api = api
        self.mayReadWords = mayReadWords
    }

    /// Applies an event at once, so the next read sees it. An event that
    /// changes nothing tells nobody.
    func dispatch(_ event: SearchEvent) {
        let next = reduce(state, event)
        guard next != state else { return }
        state = next
    }
}
