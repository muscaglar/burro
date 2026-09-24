import Foundation

/// Where the facts of the saved areas are kept. It is the one way they are
/// read and written, so a test passes a stand-in, and the app passes
/// `FileSavedAreasStorage`.
///
/// It deals in records and not in bytes. How a record is written to a file is
/// for `Kept/` to say, where everything written to the phone is written.
public protocol SavedAreasStorage: Sendable {
    /// True when what is written is still there after the app is closed.
    var outlivesTheApp: Bool { get }
    /// What is kept, or `nil` when nothing is, or when it cannot be read.
    func read() -> KeptShortlist?
    func write(_ kept: KeptShortlist) throws
    func remove() throws
}

/// Keeps the saved areas' facts in memory, for a test.
public final class MemorySavedAreasStorage: SavedAreasStorage, @unchecked Sendable {
    private let lock = NSLock()
    private var held: KeptShortlist?
    private let refusesWrites: Bool

    public init(_ held: KeptShortlist? = nil, refusesWrites: Bool = false) {
        self.held = held
        self.refusesWrites = refusesWrites
    }

    public var outlivesTheApp: Bool { false }

    public func read() -> KeptShortlist? {
        lock.withLock { held }
    }

    public func write(_ kept: KeptShortlist) throws {
        if refusesWrites { throw CocoaError(.fileWriteNoPermission) }
        lock.withLock { held = kept }
    }

    public func remove() throws {
        if refusesWrites { throw CocoaError(.fileWriteNoPermission) }
        lock.withLock { held = nil }
    }
}
