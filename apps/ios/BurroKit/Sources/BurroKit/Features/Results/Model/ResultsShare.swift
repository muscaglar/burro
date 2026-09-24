import Foundation
import Observation

// Sharing a search. A share is the stored settings of a search under an id
// made at random. The app asks the API to store it, builds the link with the
// id in its fragment, and hands the link to the phone's own share sheet when
// the person presses "Share".
//
// The id is held in memory while the screen is open, and nowhere else. It is
// never written to the phone, never copied for the person, and never put in
// any address but the one link the person asked for.

extension Results {
    /// A link that was made, and the search it was made of.
    struct MadeLink: Hashable, Sendable {
        let url: URL
        /// True when a place was replaced by the station or district that stands in for it.
        let coarsened: Bool
        /// True when the person asked for the exact places to be kept.
        let exact: Bool
        /// The search the link is of. A link is shown only for the search it was made of.
        let hash: String?
        let hasPlaces: Bool

        /// What is said of the places in the link.
        var words: String {
            if coarsened { return ResultsCopy.Share.coarsened }
            return hasPlaces ? ResultsCopy.Share.exactKept : ResultsCopy.Share.noPlaces
        }
    }

    /// Where the making of a link stands.
    enum Linking: Hashable, Sendable {
        case idle
        case making
        case made(MadeLink)
        case failed(words: String, requestId: String?)
    }

    /// True when a search can be shared: the website has an address, and there is a ranking to share.
    static func canShare(_ state: SearchState, site: SiteAddress) -> Bool {
        site.origin != nil && state.ranking != nil
    }

    /// Makes the link, and holds it while the search is the one it was made of.
    @MainActor
    @Observable
    final class Sharing {
        private var held: Linking = .idle
        /// Whether the exact places are to be kept. Off until the person turns it on.
        var exact = false

        /// What to show for the search as it stands. A link made of another search is not shown.
        func shown(for state: SearchState) -> Linking {
            if case .made(let link) = held, link.hash != state.specHash { return .idle }
            return held
        }

        /// True when a link was made of a search that has since changed.
        func isGone(for state: SearchState) -> Bool {
            if case .made(let link) = held { return link.hash != state.specHash }
            return false
        }

        /// Route 9, with the spec the API last returned. Nothing a person typed goes with it.
        func make(of store: SearchStore, site: SiteAddress) async {
            guard canShare(store.state, site: site), held != .making else { return }
            held = .making
            // With no place in the search there is nothing to keep exact.
            let exact = self.exact && !store.state.spec.commutes.isEmpty
            let answer = await store.flow.createShare(exactPlaces: exact)
            switch answer {
            case .failure(let failure):
                held = .failed(words: ShellCopy.words(for: failure), requestId: failure.requestId)
            case .success(let made):
                // The link is built in the one place an address is built, and only of an id.
                guard let url = site.share(made.data.shareId) else {
                    held = .failed(words: ResultsCopy.Share.notAnId, requestId: made.requestId)
                    return
                }
                held = .made(
                    MadeLink(
                        url: url, coarsened: made.data.coarsened, exact: exact,
                        hash: store.state.specHash, hasPlaces: !made.data.spec.commutes.isEmpty))
            }
        }

        /// Forgets the link, as when the panel is closed.
        func forget() {
            held = .idle
        }
    }
}
