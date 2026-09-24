import Foundation

// What a press on the results screen does. Each is one call to what the shell
// and the search hand to a feature, so that a press is tested with no screen.
//
// The app builds edits and never a spec. "Hide this area" is one edit, sent
// with the last spec the API returned.

extension Results {
    @MainActor
    struct Hands {
        let app: AppModel
        let search: SearchStore
        let memory: Memory

        init(app: AppModel, search: SearchStore, memory: Memory? = nil) {
            self.app = app
            self.search = search
            self.memory = memory ?? app.results
        }

        private var state: SearchState { search.state }

        // MARK: - On a result

        /// Opens the area's own screen. The route holds ids and names of the release, and nothing of the search.
        func open(_ area: AreaRef) {
            app.show(.area(area))
        }

        func isSaved(_ area: AreaRef) -> Bool {
            app.shortlist.contains(area.areaId)
        }

        /// Saves the area to the shortlist on this phone, or takes it off.
        func toggleShortlist(_ area: AreaRef) {
            app.toggleShortlist(area)
        }

        func toggleCompare(_ area: AreaRef) {
            memory.toggleCompare(area)
            // With too few left there is nothing to compare, so the comparison is left.
            if !isEnough(memory.compare) { chooseOthers() }
        }

        /// True when the area could be added to the comparison: it is in it already, or there is room.
        func canToggleCompare(_ area: AreaRef) -> Bool {
            memory.isCompared(area) || !isFull(memory.compare)
        }

        /// Hides the area from the results: one edit, which the API applies.
        func hide(_ area: AreaRef) async {
            if state.selectedId == area.areaId { search.flow.select(nil) }
            await search.flow.applyEdits(Edits.areaHide(area.areaId))
        }

        // MARK: - The list and the map, in step

        /// Chooses an area in the list: the map marks it, and is shown.
        func showOnMap(_ area: AreaRef) {
            search.flow.select(area.areaId)
            memory.showing = .map
            // The map is what was asked for, so the list stands aside.
            if memory.height == .full { memory.height = .half }
        }

        /// Chooses an area by its heading in the list, or lets it go: the map marks it, and nothing moves.
        func choose(inList area: AreaRef) {
            search.flow.select(state.selectedId == area.areaId ? nil : area.areaId)
        }

        /// Chooses an area on the map: the list marks it and brings it into view.
        func choose(onMap areaId: String?) {
            search.flow.select(areaId)
            memory.bringIntoView = areaId
        }

        /// Brings the chosen area's card into view, and makes room for it.
        func showInList(_ area: AreaRef) {
            if memory.showing == .table { memory.showing = .list }
            if memory.showing == .map && memory.height == .low { memory.height = .half }
            memory.bringIntoView = area.areaId
        }

        /// Chooses an area in the table: it is marked on the map and in the list.
        func choose(inTable area: AreaRef) {
            search.flow.select(state.selectedId == area.areaId ? nil : area.areaId)
        }

        func close() {
            search.flow.select(nil)
        }

        // MARK: - Lines above the list

        func act(_ act: Act) async {
            switch act {
            case .retry: await search.flow.retry()
            case .toSearch: app.showRoot(of: .search)
            case .edit(let operations): await search.flow.applyEdits(operations)
            case .startAgain: search.flow.startAgain()
            }
        }

        /// Opens the screen that lists every source, on the tab that is showing.
        func openSources() {
            app.show(.sources)
        }

        // MARK: - Comparing and sharing

        /// True while the comparison is on screen.
        var comparing: Bool {
            app.searchPath.contains(.compare)
        }

        /// Goes to the comparison, which is a screen of its own over the results.
        func compare() {
            guard isEnough(memory.compare), !comparing else { return }
            app.show(.compare, in: .search)
        }

        /// Goes back from the comparison to the results, to choose others.
        func chooseOthers() {
            app.searchPath.removeAll { $0 == .compare }
        }

        var canShare: Bool { Results.canShare(state, site: app.site) }

        func openShare() {
            guard canShare else { return }
            memory.shareOpen = true
            memory.bringIntoView = Memory.sharePanel
        }

        func makeLink() async {
            await memory.sharing.make(of: search, site: app.site)
        }
    }
}

extension Results.Memory {
    /// What the list is asked to bring into view when it is the share panel and not an area.
    static let sharePanel = "share"
    /// The same, for the top of the list.
    static let top = "top"
}
