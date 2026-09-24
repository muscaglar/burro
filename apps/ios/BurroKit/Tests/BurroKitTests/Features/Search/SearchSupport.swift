import Foundation
import XCTest

@testable import BurroKit

/// What the Search and About tests share: the website's own words, to hold
/// the app's words to, and the files these two features are made of.
enum Website {
    /// Every file of the website's own words, as one text. Two pieces of a
    /// sentence that the file joins with a plus are joined here too, and a
    /// quote mark written with a backslash is written plain.
    static func words() throws -> String {
        let folder = Repository.root.appendingPathComponent("apps/web/src/content")
        return try Repository.files(under: folder, ending: ".ts")
            .map { joined(try Repository.text(folder.appendingPathComponent($0))) }
            .joined(separator: "\n")
    }

    /// True when the website says this, as it stands or with its gaps named
    /// as the website names them. A line for one of something, which the
    /// website writes with the figure in it, is tried with the figure.
    static func says(_ words: String, in website: String) -> Bool {
        let asWritten = words.replacingOccurrences(
            of: #"\\\(([A-Za-z]+)\)"#, with: "\\${$1}", options: .regularExpression)
        let tries = [
            asWritten,
            asWritten.replacingOccurrences(of: "${count}", with: "1"),
            asWritten.replacingOccurrences(of: "${most}", with: "1"),
            // A word the website writes between quote marks, as its source writes them.
            asWritten.replacingOccurrences(of: "${quote}", with: "\\\"")
                .replacingOccurrences(of: "${assumed}", with: SearchCopy.Chips.assumed),
        ]
        return tries.contains { website.contains($0) }
    }

    /// Joins `"one " + "two"` into `"one two"`, however the break is laid out.
    static func joined(_ source: String) -> String {
        source.replacingOccurrences(of: #""\s*\+\s*""#, with: "", options: .regularExpression)
    }
}

/// The source of the two features, read off the disk.
enum Written {
    static let search = Repository.sources.appendingPathComponent("Features/Search")
    static let about = Repository.sources.appendingPathComponent("Features/About")

    /// Every file of the two features, by its name, with its text.
    static func files() throws -> [(name: String, text: String)] {
        try [search, about].flatMap { folder in
            try Repository.files(under: folder, ending: ".swift").map {
                ("\(folder.lastPathComponent)/\($0)", try Repository.text(folder.appendingPathComponent($0)))
            }
        }
    }

    /// Every piece of text a file holds between quote marks, with pieces that
    /// are joined by a plus joined.
    static func words(in file: URL) throws -> [String] {
        let text = Website.joined(try Repository.text(file))
        return text.components(separatedBy: "\"").enumerated()
            .filter { $0.offset % 2 == 1 }
            .map(\.element)
            .filter { !$0.isEmpty }
    }
}

extension JSON {
    /// Each element of a list changed, where this is a list.
    func each(_ change: (inout JSON) -> Void) -> JSON {
        guard case .array(let elements) = self else { return self }
        return .array(
            elements.map { element in
                var changed = element
                change(&changed)
                return changed
            })
    }
}

extension StandIn {
    /// Answers as a recorded reading does, with nothing of it changing the
    /// search: what the API says when the search already says all of it.
    static func readingThatChangesNothing(_ scenario: String) -> Responder {
        .made { _ in
            try Recorded.read(scenario).with(data: { data in
                data["applied"] = data["applied"]?.each { $0["changed"] = .bool(false) }
            })
        }
    }
}

/// What the search screen shows of a search that is open on the stand-in.
extension OpenSearch {
    @MainActor
    func shown(_ consent: ConsentChoice? = .allowed) -> SearchShown {
        SearchScreen.shown(state, consent: consent)
    }
}
