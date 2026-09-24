import Foundation

/// The facts of the saved areas, written as one JSON file through the one
/// store the app keeps things in.
///
/// It writes `KeptShortlist` and nothing else. That record has fixed keys, and
/// refuses a journey, a budget and anything else of a search when it is
/// written and again when it is read.
public struct FileSavedAreasStorage: SavedAreasStorage {
    let storage: any PhoneStorage

    public init(_ storage: any PhoneStorage) {
        self.storage = storage
    }

    public var outlivesTheApp: Bool { storage.outlivesTheApp }

    public func read() -> KeptShortlist? {
        storage.read(.savedAreas).flatMap { try? JSONDecoder().decode(KeptShortlist.self, from: $0) }
    }

    public func write(_ kept: KeptShortlist) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        try storage.write(encoder.encode(kept), to: .savedAreas)
    }

    public func remove() throws {
        try storage.remove(.savedAreas)
    }
}
