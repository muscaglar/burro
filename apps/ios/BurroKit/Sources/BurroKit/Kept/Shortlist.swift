import Foundation
import Observation

/// One saved area: its ids, its names, the date, and whether it is made up.
///
/// It holds nothing of the search that led to it: no rank, no fit, no place,
/// no spec. Its keys are fixed, so nothing else can be written beside them.
public struct ShortlistEntry: Codable, Hashable, Sendable, Identifiable {
    public let areaId: String
    public let slug: String
    public let name: String
    public let borough: String
    public let savedOn: Date
    /// True when the area came from made-up data, so that the list can say so offline.
    public let synthetic: Bool

    public var id: String { areaId }

    /// What a route to this area holds.
    public var area: AreaRef {
        AreaRef(areaId: areaId, slug: slug, name: name, borough: borough)
    }

    enum CodingKeys: String, CodingKey {
        case areaId = "area_id"
        case slug
        case name
        case borough
        case savedOn = "saved_on"
        case synthetic
    }
}

/// The areas a person saved. Kept on the phone, readable with no connection.
/// Burro does not hold it, and there is no account.
@MainActor
@Observable
public final class Shortlist {
    /// The saved areas, the last saved first.
    public private(set) var entries: [ShortlistEntry]
    /// True when the last change could not be written to the phone. The list
    /// on screen still holds it, until the app is closed.
    public private(set) var couldNotSave = false

    @ObservationIgnored private let storage: any PhoneStorage
    @ObservationIgnored private let now: @MainActor () -> Date

    public init(storage: any PhoneStorage, now: @escaping @MainActor () -> Date = { Date() }) {
        self.storage = storage
        self.now = now
        entries = Self.read(from: storage)
    }

    /// True when any saved area is made up.
    public var holdsSynthetic: Bool {
        entries.contains { $0.synthetic }
    }

    public func contains(_ areaId: String) -> Bool {
        entries.contains { $0.areaId == areaId }
    }

    /// Saves an area. Saving one that is saved already changes nothing.
    public func add(_ area: AreaRef, synthetic: Bool) {
        guard !contains(area.areaId) else { return }
        let entry = ShortlistEntry(
            areaId: area.areaId, slug: area.slug, name: area.name, borough: area.borough,
            savedOn: now(), synthetic: synthetic)
        entries.insert(entry, at: 0)
        save()
    }

    public func remove(_ areaId: String) {
        guard contains(areaId) else { return }
        entries.removeAll { $0.areaId == areaId }
        save()
    }

    /// Takes every saved area off the phone.
    public func removeAll() {
        entries = []
        do {
            try storage.remove(.shortlist)
            couldNotSave = false
        } catch {
            couldNotSave = true
        }
    }

    private func save() {
        do {
            try storage.write(Self.encoder.encode(Kept(entries: entries)), to: .shortlist)
            couldNotSave = false
        } catch {
            couldNotSave = true
        }
    }

    // MARK: - The file

    private struct Kept: Codable {
        var version = 1
        let entries: [ShortlistEntry]
    }

    private static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys]
        return encoder
    }()

    private static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    private static func read(from storage: any PhoneStorage) -> [ShortlistEntry] {
        guard let data = storage.read(.shortlist),
            let kept = try? decoder.decode(Kept.self, from: data)
        else { return [] }
        return kept.entries
    }
}
