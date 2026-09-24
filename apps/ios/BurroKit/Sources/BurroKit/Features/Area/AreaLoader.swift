import Foundation
import Observation

/// Reads one area for its screen, and says what the screen is to show: the
/// area as the API gives it now, the copy the shortlist kept when the API
/// cannot be reached, or why there is nothing to show.
///
/// It asks route 6 for the area by its slug. It sends nothing of a search.
@MainActor
@Observable
public final class AreaLoader {
    /// Where what is on screen came from.
    public enum Origin: Hashable, Sendable {
        /// The API, since the app was opened.
        case api
        /// The copy the shortlist kept, because the area could not be read again.
        case kept(savedOn: Date, because: Failure)
    }

    public enum Shown: Hashable, Sendable {
        case reading
        case page(AreaPage, Origin)
        case failed(Failure)
    }

    public private(set) var shown: Shown = .reading
    public let area: AreaRef

    @ObservationIgnored private let app: AppModel
    @ObservationIgnored private let saved: SavedAreas
    @ObservationIgnored private var answered: (data: AreaData, release: Meta)?
    @ObservationIgnored private var reading = false

    public init(area: AreaRef, app: AppModel, saved: SavedAreas? = nil) {
        self.area = area
        self.app = app
        self.saved = saved ?? app.saved
    }

    /// Reads the area, if it has not been read. Called again once the release
    /// has been read, it lays the same answer out under the release's headings.
    public func load() async {
        guard !reading else { return }
        reading = true
        defer { reading = false }

        // The names of the features come with the release. Without them the figures are still shown.
        _ = await app.searchOnceOpen()
        if answered == nil, let held = app.profile(inHandOf: area.areaId) {
            // The search has read this area already, for a result.
            answered = held
        }
        if answered == nil {
            if case .page = shown {} else { shown = .reading }
            switch await app.api.getArea(area.slug) {
            case .success(let answer):
                answered = (
                    answer.data,
                    Meta(
                        releaseId: answer.meta.releaseId, engineVersion: answer.meta.engineVersion,
                        synthetic: answer.synthetic, preview: answer.preview)
                )
            case .failure(let failure):
                show(failure)
                return
            }
        }
        guard let answered else { return }
        let meta = app.search?.state.meta
        let page = AreaPage(
            answered.data, release: answered.release, features: meta?.features ?? [],
            tags: meta?.tags ?? [], recipes: meta?.recipes ?? [])
        shown = .page(page, .api)
        // A saved area with no copy of its facts is given one. A copy that is
        // there is left as it was saved, until the person asks for the newer one.
        if saved.contains(page.area.areaId), saved.kept[page.area.areaId] == nil {
            saved.keep(page)
        }
    }

    /// Asks the API again.
    public func retry() async {
        await load()
    }

    /// True when the copy the shortlist kept is of another release than the one on screen.
    public var keptIsOlder: Bool {
        guard case .page(let page, .api) = shown, let kept = saved.kept[page.area.areaId] else {
            return false
        }
        return kept.releaseId != page.releaseId
    }

    /// Keeps what is on screen in place of the copy that was kept.
    public func keepWhatIsShown() {
        guard case .page(let page, .api) = shown else { return }
        saved.keep(page)
    }

    private func show(_ failure: Failure) {
        if let kept = saved.kept[area.areaId], saved.contains(area.areaId) {
            shown = .page(kept.page, .kept(savedOn: kept.savedOn, because: failure))
        } else {
            shown = .failed(failure)
        }
    }
}
