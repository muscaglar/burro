import Foundation
import Observation

/// Opens a search that someone shared, and says what the screen is to show
/// while it opens, once it is open, and when it cannot be.
///
/// The id of the share is held here, in memory, while the link is being
/// opened. It is sent in one place only: the path of the one call that opens
/// the share. It is never put in a route, a file or a log.
@MainActor
@Observable
public final class SharedSearch {
    public enum Stage: Hashable, Sendable {
        case opening
        case open(Opened)
        case failed(Failure)
    }

    /// What is said of a share once it is open.
    public struct Opened: Hashable, Sendable {
        /// True when a place was replaced by the station or district that stands in for it.
        public let coarsened: Bool
        /// True when the search names a place to reach.
        public let hasPlaces: Bool
        /// True when the data has changed since the link was made.
        public let stale: Bool
        /// The release the link was made on, and the one it is shown on.
        public let madeOn: String
        public let shownOn: String
        /// How many areas were ranked, and the name of the first, where the app has one.
        public let ranked: Int
        public let first: String?
        /// False when nothing is set to rank by, so the areas are in no order.
        public let inOrder: Bool

        /// What is said of the share, line by line, in fixed words.
        public var lines: [String] {
            var lines = [LinkCopy.Shared.text, LinkCopy.Shared.holds]
            if coarsened {
                lines.append(LinkCopy.Shared.coarsened)
            } else if hasPlaces {
                lines.append(LinkCopy.Shared.exact)
            }
            if stale {
                lines.append(LinkCopy.Shared.staleBetween(madeOn: madeOn, shownOn: shownOn))
            }
            return lines
        }

        /// What came of ranking it.
        public var status: String {
            if ranked == 0 { return LinkCopy.Ranked.none }
            if !inOrder { return LinkCopy.Ranked.inNoOrder(ranked) }
            if let first { return LinkCopy.Ranked.named(ranked, first: first) }
            return LinkCopy.Ranked.unnamed(ranked)
        }
    }

    public private(set) var stage: Stage = .opening

    @ObservationIgnored private let shareId: String
    @ObservationIgnored private let app: AppModel
    @ObservationIgnored private var busy = false

    /// - Parameter shareId: The id the link holds. `nil` is answered for
    ///   anything that is not an id the API makes: it is then never sent anywhere.
    public init?(shareId: String, app: AppModel) {
        guard SiteAddress.isShareId(shareId) else { return nil }
        self.shareId = shareId
        self.app = app
    }

    /// Opens the share. A share that is open already is not opened again over
    /// what the person has changed since.
    public func open() async {
        guard !busy else { return }
        busy = true
        defer { busy = false }
        stage = .opening

        guard let search = await app.searchOnceOpen() else {
            if case .failed(let failure) = app.opening { stage = .failed(failure) }
            return
        }
        if search.state.shared?.id != shareId {
            if let failure = await search.flow.openShare(shareId) {
                stage = .failed(failure)
                return
            }
        }
        // Something the person did since took the place of the share: there is nothing to say of it.
        guard let opened = Self.opened(search.state, shareId: shareId) else {
            stage = .failed(.because(.aborted))
            return
        }
        stage = .open(opened)
    }

    /// True when asking again could be answered otherwise. The API has said a
    /// link leads nowhere when it refuses it: asking again would be told the same.
    public var canTryAgain: Bool {
        guard case .failed(let failure) = stage else { return false }
        return !(failure.api.map { $0.status < 500 } ?? false)
    }

    /// What the state says of the share that is open in it.
    static func opened(_ state: SearchState, shareId: String) -> Opened? {
        guard let shared = state.shared, shared.id == shareId, let ranking = state.ranking else { return nil }
        return Opened(
            coarsened: shared.coarsened,
            hasPlaces: !state.spec.commutes.isEmpty,
            stale: shared.stale,
            madeOn: shared.originalReleaseId,
            shownOn: state.meta.releaseId,
            ranked: ranking.scores.count,
            first: ranking.scores.first.flatMap { state.area($0.areaId)?.name },
            inOrder: !ranking.emptySpec)
    }
}
