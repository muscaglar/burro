import Foundation
import Observation

/// Everything the app holds while it is open: the API, the search, what is
/// kept on the phone, and where each tab stands.
///
/// It is made once, by the app target, and handed to the root view. Every
/// screen reads it from the environment. It is held in memory: closing the
/// app loses the search and the areas chosen to compare, and keeps the
/// shortlist and the choice of consent.
@MainActor
@Observable
public final class AppModel {
    /// How far the app has got with reading the release it is to search.
    public enum Opening: Hashable, Sendable {
        case waiting
        case opening
        case open
        case failed(Failure)
    }

    public let api: any BurroAPI
    /// Where the website is, for the addresses the share sheet is handed.
    public let site: SiteAddress
    public let synthetic: SyntheticNotice
    public let shortlist: Shortlist
    public let consent: Consent
    /// The saved areas with their facts as they were when saved, and the
    /// order the person put them in. Save and remove an area through this.
    @ObservationIgnored public private(set) lazy var saved = SavedAreas(
        app: self, storage: FileSavedAreasStorage(storage))
    /// What the results screen keeps while the app is open: how the results
    /// are shown, and the areas chosen to compare. It is never written to the phone.
    @ObservationIgnored let results = Results.Memory()

    @ObservationIgnored private let storage: any PhoneStorage

    public private(set) var opening: Opening = .waiting
    /// The search that is open. `nil` until the release has been read.
    public private(set) var search: SearchStore?

    public var tab: AppTab = .search
    /// What is pushed onto each tab, the last pushed last.
    public var searchPath: [Screen] = []
    public var shortlistPath: [Screen] = []
    public var aboutPath: [Screen] = []

    public init(
        api: any BurroAPI,
        site: SiteAddress = .none,
        synthetic: SyntheticNotice,
        storage: any PhoneStorage
    ) {
        self.api = api
        self.site = site
        self.synthetic = synthetic
        self.storage = storage
        shortlist = Shortlist(storage: storage)
        consent = Consent(storage: storage)
        // A saved area that is made up is data on a screen, with or without a connection.
        synthetic.note(shortlist.holdsSynthetic)
    }

    /// The app as it runs on a phone: the API and the website at the addresses
    /// the build settings give, and the app's own folder to keep things in.
    public static func live(infoDictionary: [String: Any]?) -> AppModel {
        let notice = SyntheticNotice()
        let api = LiveBurroAPI(
            configuration: APIConfiguration(infoDictionary: infoDictionary),
            onSynthetic: { said in await notice.note(said) }
        )
        let storage: any PhoneStorage = FilePhoneStorage.inApplicationSupport() ?? MemoryPhoneStorage()
        return AppModel(
            api: api, site: SiteAddress(infoDictionary: infoDictionary), synthetic: notice, storage: storage)
    }

    /// Reads what a search is built on: the form, from route 11, and every
    /// area, from route 4. It does nothing when the search is open already.
    public func open() async {
        guard search == nil, opening != .opening else { return }
        opening = .opening
        async let served = api.getMeta()
        async let listed = api.listAreas()
        let (meta, areas) = await (served, listed)
        switch (meta, areas) {
        case (.success(let meta), .success(let areas)):
            let consent = self.consent
            search = SearchStore(
                meta: meta.data,
                areas: areas.data.areas,
                api: api,
                mayReadWords: { consent.mayReadWords }
            )
            opening = .open
        case (.failure(let failure), _), (_, .failure(let failure)):
            opening = .failed(failure)
        }
    }

    // MARK: - Going somewhere

    /// Pushes a screen onto the tab that is showing.
    public func show(_ screen: Screen) {
        show(screen, in: tab)
    }

    /// Goes to a tab, and pushes a screen onto it.
    public func show(_ screen: Screen, in tab: AppTab) {
        self.tab = tab
        switch tab {
        case .search: searchPath.append(screen)
        case .shortlist: shortlistPath.append(screen)
        case .about: aboutPath.append(screen)
        }
    }

    /// Goes back to the first screen of a tab.
    public func showRoot(of tab: AppTab) {
        self.tab = tab
        switch tab {
        case .search: searchPath = []
        case .shortlist: shortlistPath = []
        case .about: aboutPath = []
        }
    }

    /// True when an area of this release is made up. It is, when the release is.
    public func isSynthetic(_ area: AreaRef) -> Bool {
        if let search { return search.state.meta.synthetic }
        return synthetic.seen || area.areaId.hasPrefix("syn-")
    }

    /// Saves an area to the shortlist, or takes it off. Its facts are kept
    /// with it where the search has read them, and nothing of the search is.
    public func toggleShortlist(_ area: AreaRef) {
        saved.toggle(area, page: page(inHandOf: area.areaId))
    }
}
