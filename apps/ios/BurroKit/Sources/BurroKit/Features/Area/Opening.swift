import Foundation

extension AppModel {
    /// The search, once the release has been read: the app is opened if it
    /// has not been, and an opening that is under way is waited for. `nil`
    /// when the release could not be read.
    ///
    /// A link may reach the app before it has opened, and a saved area may be
    /// pressed before the release is in. Neither is told there is nothing
    /// there while the answer is still on its way.
    func searchOnceOpen() async -> SearchStore? {
        if search == nil { await open() }
        // Another screen began the opening. It ends in a search or in a failure.
        var waited = 0
        while search == nil, opening == .opening, waited < Self.longestWait, !Task.isCancelled {
            try? await Task.sleep(nanoseconds: Self.pause)
            waited += 1
        }
        return search
    }

    /// The profile of an area the search has read already, with the release that made it.
    func profile(inHandOf areaId: String) -> (data: AreaData, release: Meta)? {
        guard let state = search?.state, let held = state.details[areaId] else { return nil }
        let by = state.detailsBy[areaId] ?? Served(form: state.meta)
        return (
            held,
            Meta(
                releaseId: by.releaseId, engineVersion: by.engineVersion,
                synthetic: state.meta.synthetic, preview: state.meta.preview)
        )
    }

    /// The page of an area the search has read already. `nil` for an area it has not.
    func page(inHandOf areaId: String) -> AreaPage? {
        guard let state = search?.state, let held = profile(inHandOf: areaId) else { return nil }
        return AreaPage(
            held.data, release: held.release, features: state.meta.features, tags: state.meta.tags,
            recipes: state.meta.recipes)
    }

    /// A twentieth of a second, and no more of them than the longest a call may take.
    private static let pause: UInt64 = 50_000_000
    private static let longestWait = 300
}
