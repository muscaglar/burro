import Foundation
import Observation

/// What the app does with a link that was opened: it goes to an area's
/// screen, or it puts up the screen that opens a shared search, or it says in
/// fixed words that the link leads nowhere.
///
/// The link is read and let go. Nothing of it is kept, and nothing of it is
/// shown but the area or the search it leads to.
@MainActor
@Observable
public final class LinkOpener {
    /// What is said of a link that leads nowhere. The words are fixed: what
    /// the link held is never repeated.
    public enum Nowhere: String, Hashable, Sendable, CaseIterable {
        case noShare
        case notAShare
        case noArea

        public var title: String {
            switch self {
            case .noShare: return LinkCopy.NoShare.title
            case .notAShare: return LinkCopy.NotAShare.title
            case .noArea: return LinkCopy.NoArea.title
            }
        }

        public var text: String {
            switch self {
            case .noShare: return LinkCopy.NoShare.text
            case .notAShare: return LinkCopy.NotAShare.text
            case .noArea: return LinkCopy.NoArea.text
            }
        }
    }

    /// What is put up over the app for a link.
    public enum Presented: Hashable, Sendable, Identifiable {
        /// A shared search, by its id. It is held while the screen is up, and no longer.
        case share(id: String)
        case nowhere(Nowhere)

        /// Tells one thing put up from the next. It never holds the id of a share.
        public var id: String {
            switch self {
            case .share: return "share"
            case .nowhere(let nowhere): return nowhere.rawValue
            }
        }
    }

    public var presented: Presented?

    public init() {}

    /// Opens a link. An address that is not the website's does nothing.
    public func open(_ url: URL, in app: AppModel) async {
        guard let link = IncomingLink.read(url, site: app.site) else { return }
        switch link {
        case .share(let id):
            presented = .share(id: id)
        case .noShare:
            presented = .nowhere(.noShare)
        case .notAShare:
            presented = .nowhere(.notAShare)
        case .area(let city, let slug):
            await openArea(city: city, slug: slug, in: app)
        }
    }

    /// Goes to the screen of the area a link names. The area is looked up in
    /// what the API listed, and then in what the phone kept, so that a saved
    /// area opens with no connection.
    private func openArea(city: String, slug: String, in app: AppModel) async {
        _ = await app.searchOnceOpen()
        func isIt(_ areaId: String, _ found: String) -> Bool {
            found == slug && SiteAddress.city(of: areaId) == city
        }
        if let listed = app.search?.state.areas.first(where: { isIt($0.areaId, $0.slug) }) {
            presented = nil
            app.show(.area(AreaRef(listed)), in: .search)
        } else if let saved = app.shortlist.entries.first(where: { isIt($0.areaId, $0.slug) }) {
            presented = nil
            app.show(.area(saved.area), in: .shortlist)
        } else {
            presented = .nowhere(.noArea)
        }
    }

    /// Takes down what was put up, and goes to the results of the search that is open.
    public func showResults(in app: AppModel) {
        presented = nil
        app.showRoot(of: .search)
        app.show(.results, in: .search)
    }

    /// Takes down what was put up, and goes to where a search is made.
    public func searchInstead(in app: AppModel) {
        presented = nil
        app.showRoot(of: .search)
    }
}
