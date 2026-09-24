import Foundation

// What may be done with a thing Burro noticed and did not apply. It mirrors
// apps/web/src/lib/search/suggestion.ts and spans.ts.
//
// Burro guesses nothing. A thing that could be wanted two ways is a question
// until the person chooses. A thing that carries a note is chosen by its own
// label, and never with others at once: the note is what a person should know
// before they choose. For recorded crime that is a rule and no courtesy.
// Recorded crime counts only when it is asked for by name, and a button that
// adds several things at once names none of them. docs/design/contract.md, 8.2.

extension Suggestion {
    /// The ways the thing may be wanted: every choice of it but leaving it out.
    public var ways: [SuggestionChoice] {
        choices.filter { $0.direction != .ignore }
    }

    /// What a person should know before they choose, in the API's words. `nil`
    /// where the suggestion carries nothing.
    public var noteShown: String? {
        note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
    }

    /// The one way the thing may be added together with others. `nil` where it
    /// may not be: it could be meant two ways, or it carries a note.
    public var addedWithOthers: SuggestionChoice? {
        let ways = ways
        guard ways.count == 1, noteShown == nil else { return nil }
        return ways.first
    }
}

/// Where a stretch of what was typed stands in the box.
///
/// Route 1 says where words stand as offsets into the text as it was sent,
/// counted in code points. The box holds the text as it was typed, with
/// whatever space stands before it. So an offset is carried over before the
/// box selects by it.
///
/// Nothing here keeps or returns a word. It takes the text from the box, where
/// it already is, and gives back places in it, for the box to select.
public enum BoxSpans {
    /// The stretches as places in the box as it stands, in the order given.
    /// One that is empty, or that falls outside the text, is left out.
    ///
    /// The offsets mean nothing unless the box still holds what was sent:
    /// whoever calls this must know that it does.
    public static func inTheBox(_ box: String, _ spans: [Span]) -> [Range<String.Index>] {
        let points = box.unicodeScalars
        let blank = CharacterSet.whitespacesAndNewlines
        guard let first = points.firstIndex(where: { !blank.contains($0) }),
            let last = points.lastIndex(where: { !blank.contains($0) })
        else { return [] }
        let sent = points.distance(from: first, to: last) + 1
        return spans.compactMap { span in
            guard span.start >= 0, span.end <= sent, span.end > span.start else { return nil }
            let from = points.index(first, offsetBy: span.start)
            let to = points.index(first, offsetBy: span.end)
            // A place inside a letter that is made of several code points is moved to its edge.
            return box.rangeOfComposedCharacterSequences(for: from..<to)
        }
    }
}
