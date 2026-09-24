import Foundation

/// Everything the app keeps on the phone. There are three things, and no more.
///
/// None holds what a person typed, a place they named, a spec, or anything
/// of a search. To keep a fourth thing, add it here, and say in
/// `apps/ios/AGENTS.md` what it holds and why.
public enum KeptFile: String, Hashable, Sendable, CaseIterable {
    /// The areas a person saved: ids, names and the date.
    case shortlist
    /// Whether the person agreed that their words may be read.
    case consent
    /// The facts of each saved area as they were when it was saved, and the
    /// order the person put the areas in, so that a saved area reads with no connection.
    case savedAreas = "saved-areas"

    var fileName: String { "\(rawValue).json" }
}

/// Where the app keeps what it keeps. This is the only way anything is
/// written to the phone: no other file, no defaults, no keychain.
public protocol PhoneStorage: Sendable {
    /// True when what is written is still there after the app is closed.
    var outlivesTheApp: Bool { get }
    /// What is kept, or `nil` when nothing is, or when it cannot be read.
    func read(_ file: KeptFile) -> Data?
    func write(_ data: Data, to file: KeptFile) throws
    func remove(_ file: KeptFile) throws
}

/// Keeps each thing as one file in the app's own folder.
///
/// The folder is left out of backups, so what is kept on the phone stays on
/// the phone, and each file is locked while the phone is.
public struct FilePhoneStorage: PhoneStorage {
    private let folder: URL

    public init(folder: URL) {
        self.folder = folder
    }

    public var outlivesTheApp: Bool { true }

    /// The folder the app uses: `Burro`, inside the app's Application Support.
    public static func inApplicationSupport() -> FilePhoneStorage? {
        guard
            let support = try? FileManager.default.url(
                for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
        else { return nil }
        return FilePhoneStorage(folder: support.appendingPathComponent("Burro", isDirectory: true))
    }

    public func read(_ file: KeptFile) -> Data? {
        try? Data(contentsOf: url(of: file))
    }

    public func write(_ data: Data, to file: KeptFile) throws {
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        var kept = folder
        var values = URLResourceValues()
        values.isExcludedFromBackup = true
        try? kept.setResourceValues(values)
        try data.write(to: url(of: file), options: [.atomic, .completeFileProtection])
    }

    public func remove(_ file: KeptFile) throws {
        let url = url(of: file)
        guard FileManager.default.fileExists(atPath: url.path) else { return }
        try FileManager.default.removeItem(at: url)
    }

    private func url(of file: KeptFile) -> URL {
        folder.appendingPathComponent(file.fileName, isDirectory: false)
    }
}

/// Keeps each thing in memory, for a test, and for an app whose folder cannot be made.
public final class MemoryPhoneStorage: PhoneStorage, @unchecked Sendable {
    private let lock = NSLock()
    private var held: [KeptFile: Data]
    private let refusesWrites: Bool

    public init(_ held: [KeptFile: Data] = [:], refusesWrites: Bool = false) {
        self.held = held
        self.refusesWrites = refusesWrites
    }

    public var outlivesTheApp: Bool { false }

    public func read(_ file: KeptFile) -> Data? {
        lock.withLock { held[file] }
    }

    public func write(_ data: Data, to file: KeptFile) throws {
        if refusesWrites { throw CocoaError(.fileWriteNoPermission) }
        lock.withLock { held[file] = data }
    }

    public func remove(_ file: KeptFile) throws {
        if refusesWrites { throw CocoaError(.fileWriteNoPermission) }
        lock.withLock { held[file] = nil }
    }
}
