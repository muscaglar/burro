import Foundation

/// Where things are in the repository, worked out from where this file is.
///
/// The tests read the recorded answers, the contract and the website's tokens
/// by their path. They run on a Mac, from the source tree, and nowhere else.
enum Repository {
    /// `apps/ios/BurroKit/Tests/BurroKitTests`
    static let tests = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()
        .deletingLastPathComponent()
    /// `apps/ios/BurroKit`
    static let package = tests.deletingLastPathComponent().deletingLastPathComponent()
    /// `apps/ios`
    static let ios = package.deletingLastPathComponent()
    /// The root of the repository.
    static let root = ios.deletingLastPathComponent().deletingLastPathComponent()

    static let sources = package.appendingPathComponent("Sources/BurroKit")
    static let app = ios.appendingPathComponent("App")
    static let recorded = tests.appendingPathComponent("Recorded")
    static let webRecorded = root.appendingPathComponent("apps/web/test/recorded")
    static let contract = root.appendingPathComponent("contracts/openapi.json")
    static let tokens = root.appendingPathComponent("apps/web/src/styles/tokens.css")

    /// Every file under a folder, by its path from that folder, in order.
    static func files(under folder: URL, ending: String) -> [String] {
        guard let found = FileManager.default.enumerator(at: folder, includingPropertiesForKeys: nil) else {
            return []
        }
        let base = folder.standardizedFileURL.path
        return found.compactMap { $0 as? URL }
            .filter { $0.lastPathComponent.hasSuffix(ending) }
            .map { String($0.standardizedFileURL.path.dropFirst(base.count + 1)) }
            .sorted()
    }

    static func text(_ url: URL) throws -> String {
        try String(contentsOf: url, encoding: .utf8)
    }

    /// The records of these names that a text makes: the name as a whole word, and
    /// the bracket that makes one of it. A function whose name ends as the name of a
    /// record does makes none: `againstTheBudget(` reads a fact, and is no `Budget(`.
    static func made(_ records: [String], in text: String) -> [String] {
        records.filter { record in
            let named = NSRegularExpression.escapedPattern(for: record)
            let pattern = "(?<![A-Za-z0-9_])\(named)(\\.init)?\\s*\\("
            // A pattern that cannot be read finds the record, and never lets it by.
            guard let making = try? NSRegularExpression(pattern: pattern) else { return true }
            return making.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)) != nil
        }
    }
}
