import Foundation
import Observation

/// The saved areas, as the Shortlist screen and an area's screen use them:
/// which areas are saved, in the person's order, each with its facts as they
/// were when it was saved.
///
/// Which areas are saved is the shell's `Shortlist`, which writes their ids,
/// names and dates to the phone. This adds what that does not hold: the
/// release each came from, its facts, and the order. It holds nothing of a
/// search, because a `KeptArea` has no room for it.
///
/// There is one for each app: `app.saved`.
@MainActor
@Observable
public final class SavedAreas {
    /// One saved area: what the shell holds of it, and its facts if they are in hand.
    public struct Entry: Hashable, Sendable, Identifiable {
        public let saved: ShortlistEntry
        public let kept: KeptArea?

        public var id: String { saved.areaId }
        public var area: AreaRef { saved.area }
    }

    /// The facts of each saved area, by its id.
    public private(set) var kept: [String: KeptArea]
    /// The ids of the saved areas, in the order the person put them in.
    public private(set) var order: [String]
    /// True when the last change to the facts or the order could not be written.
    public private(set) var factsNotSaved = false

    @ObservationIgnored private let shortlist: Shortlist
    @ObservationIgnored private let notice: SyntheticNotice
    /// The app is asked whether an area is made up. It holds nothing of this, so it is not held here.
    @ObservationIgnored private weak var app: AppModel?
    @ObservationIgnored private let storage: any SavedAreasStorage

    public init(app: AppModel, storage: any SavedAreasStorage) {
        self.app = app
        shortlist = app.shortlist
        notice = app.synthetic
        self.storage = storage
        let read = storage.read() ?? .empty
        kept = Dictionary(read.areas.map { ($0.areaId, $0) }, uniquingKeysWith: { first, _ in first })
        order = read.order
        // An area taken off elsewhere leaves nothing of itself here.
        tidy(write: true)
        watch()
        // A saved area that is made up is data on a screen, with or without a connection.
        notice.note(kept.values.contains { $0.synthetic })
    }

    // MARK: - Reading

    /// The saved areas, in the person's order. One saved since the order was
    /// last set comes first, as the last saved does.
    public var entries: [Entry] {
        let saved = shortlist.entries
        let byId = Dictionary(saved.map { ($0.areaId, $0) }, uniquingKeysWith: { first, _ in first })
        let placed = order.compactMap { byId[$0] }
        let rest = saved.filter { !order.contains($0.areaId) }
        return (rest + placed).map { Entry(saved: $0, kept: kept[$0.areaId]) }
    }

    public func contains(_ areaId: String) -> Bool {
        shortlist.contains(areaId)
    }

    /// True when any change could not be written to the phone. What is on
    /// screen still holds it, until the app is closed.
    public var couldNotSave: Bool {
        shortlist.couldNotSave || factsNotSaved
    }

    /// True when the facts are still there after the app is closed.
    public var factsOutliveTheApp: Bool {
        storage.outlivesTheApp
    }

    /// True when the saved facts are of another release than the one the app is reading now.
    public func isOlder(_ entry: Entry, than releaseId: String?) -> Bool {
        guard let releaseId, let kept = entry.kept else { return false }
        return kept.releaseId != releaseId
    }

    // MARK: - Changing

    /// Saves an area, with its facts if its screen has been read.
    public func add(_ area: AreaRef, page: AreaPage? = nil) {
        if !shortlist.contains(area.areaId) {
            // As the shell's own `toggleShortlist` does it.
            let madeUp = page?.synthetic ?? app?.isSynthetic(area) ?? notice.seen
            shortlist.add(area, synthetic: madeUp)
            notice.note(shortlist.holdsSynthetic)
        }
        guard let saved = shortlist.entries.first(where: { $0.areaId == area.areaId }) else { return }
        if let page, page.area.areaId == area.areaId, kept[area.areaId] == nil {
            kept[area.areaId] = KeptArea(page, savedOn: saved.savedOn)
        }
        save()
    }

    /// Keeps the facts of a saved area as they are now, in place of the copy that was kept.
    public func keep(_ page: AreaPage) {
        guard let saved = shortlist.entries.first(where: { $0.areaId == page.area.areaId }) else { return }
        kept[saved.areaId] = KeptArea(page, savedOn: saved.savedOn)
        notice.note(page.synthetic)
        save()
    }

    public func remove(_ areaId: String) {
        shortlist.remove(areaId)
        kept[areaId] = nil
        order.removeAll { $0 == areaId }
        save()
    }

    /// Saves the area, or takes it off.
    public func toggle(_ area: AreaRef, page: AreaPage? = nil) {
        if contains(area.areaId) {
            remove(area.areaId)
        } else {
            add(area, page: page)
        }
    }

    /// Moves the areas at some places of the list to another place in it, as a list asks.
    public func move(fromOffsets: IndexSet, toOffset: Int) {
        var ids = entries.map(\.id)
        let moving = fromOffsets.filter { ids.indices.contains($0) }.map { ids[$0] }
        guard !moving.isEmpty else { return }
        let before = fromOffsets.filter { $0 < toOffset }.count
        ids.removeAll { moving.contains($0) }
        let at = min(max(toOffset - before, 0), ids.count)
        ids.insert(contentsOf: moving, at: at)
        order = ids
        save()
    }

    /// Moves one area up or down the list by one place, for a person who does not drag.
    public func move(_ areaId: String, by places: Int) {
        var ids = entries.map(\.id)
        guard let at = ids.firstIndex(of: areaId) else { return }
        let to = min(max(at + places, 0), ids.count - 1)
        guard to != at else { return }
        ids.remove(at: at)
        ids.insert(areaId, at: to)
        order = ids
        save()
    }

    public func canMove(_ areaId: String, by places: Int) -> Bool {
        let ids = entries.map(\.id)
        guard let at = ids.firstIndex(of: areaId) else { return false }
        return ids.indices.contains(at + places)
    }

    /// Takes every saved area, and every fact of one, off the phone.
    public func clear() {
        shortlist.removeAll()
        kept = [:]
        order = []
        do {
            try storage.remove()
            factsNotSaved = false
        } catch {
            factsNotSaved = true
        }
    }

    // MARK: - Keeping in step with the shell's list

    /// Drops whatever is held of an area that is no longer saved.
    private func tidy(write: Bool) {
        let saved = Set(shortlist.entries.map(\.areaId))
        let stray = kept.keys.contains { !saved.contains($0) } || order.contains { !saved.contains($0) }
        guard stray else { return }
        kept = kept.filter { saved.contains($0.key) }
        order = order.filter { saved.contains($0) }
        if write { save() }
    }

    /// Hears of an area saved or taken off elsewhere, as from a result.
    private func watch() {
        withObservationTracking {
            _ = shortlist.entries
        } onChange: { [weak self] in
            Task { @MainActor [weak self] in
                guard let self else { return }
                self.tidy(write: true)
                self.watch()
            }
        }
    }

    private func save() {
        tidy(write: false)
        // The order is written out whole, so that an area saved since has its place in it.
        let entries = entries
        order = entries.map(\.id)
        do {
            if entries.isEmpty {
                try storage.remove()
            } else {
                try storage.write(KeptShortlist(order: order, areas: entries.compactMap(\.kept)))
            }
            factsNotSaved = false
        } catch {
            factsNotSaved = true
        }
    }
}
