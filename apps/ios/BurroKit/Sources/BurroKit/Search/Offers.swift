import Foundation

// What may be done with an offer: a thing Burro read in the words and did not
// apply. It mirrors apps/web/src/lib/search/suggestion.ts and spans.ts.
//
// Nothing is applied until a person presses it. Which way one press may add
// with others is the API's to say, in `add_all`, and the app works nothing out:
// a budget as the person worded it, which may be a firm limit, and a journey as
// a guide. The API never names a journey as a firm limit, a thing with two ways
// and no guess, a journey to a place that is yet to be chosen, or recorded
// crime. docs/design/contract.md, 8.2.

extension Suggestion {
    /// The id of the choice that does nothing. Its words are the API's: "Skip".
    public static let skip = "ignore"

    /// By what an offer is told from every other of one answer: its thing, its name, and
    /// where the clause it stands in begins. The rules and a model give the same thing
    /// the same three. It holds an offset, and nothing a person typed.
    public var key: String {
        "\(target) \(label) \(shown.start)"
    }

    /// The ways the thing may be taken: every choice of it but doing nothing. A way is
    /// known by its id. Two may run the same way: a firm limit and a guide both add.
    public var ways: [SuggestionChoice] {
        choices.filter { $0.id != Self.skip }
    }

    /// What a person should know before they choose, in the API's words. `nil`
    /// where the suggestion carries nothing.
    public var noteShown: String? {
        note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
    }

    /// The way of the thing that one press may add with others: the one the API
    /// names in `add_all`. `nil` where it names none, and the thing is the person's
    /// to choose.
    public var addedWithOthers: SuggestionChoice? {
        guard !addAll.isEmpty, addAll != Self.skip else { return nil }
        return ways.first { $0.id == addAll }
    }

    /// The way Burro reads the words, where it reads them one way. It is the API's
    /// mark, and applies nothing. `nil` where it marks none.
    public var guessed: SuggestionChoice? {
        ways.first { $0.guess }
    }
}

extension Array where Element == Suggestion {
    /// Some offers of the list, by where each stands in it, with those that carry
    /// Burro's guess first. Each part keeps the order of the list, which is the order
    /// the words stand in.
    public func guessFirst(_ ats: [Int]) -> [Int] {
        let held = ats.filter { indices.contains($0) }
        return held.filter { self[$0].guessed != nil } + held.filter { self[$0].guessed == nil }
    }
}

extension Operations {
    /// True when every journey of these edits says where it leads. A journey to a place
    /// the release does not hold is offered with no place, and cannot be sent as it is.
    public var namesItsPlaces: Bool {
        commuteOps.allSatisfy { !$0.placeId.isEmpty }
    }

    /// True where these edits set a budget as a firm limit, which leaves areas out.
    public var setsAFirmBudget: Bool {
        budgetOps.contains { $0.amount > 0 && $0.strictness == .hard }
    }

    /// The edits of a way, with the place a person chose put into each journey that
    /// holds none. A journey that names its place keeps it, and nothing else is changed.
    public func withPlace(_ placeId: String) -> Operations {
        Operations(
            budgetOps: budgetOps,
            commuteOps: commuteOps.map { edit in
                guard edit.placeId.isEmpty else { return edit }
                return CommuteEdit(
                    action: edit.action, placeId: placeId, mode: edit.mode, maxMinutes: edit.maxMinutes,
                    strictness: edit.strictness, step: edit.step, provenance: edit.provenance)
            },
            weightOps: weightOps, tagOps: tagOps, areaOps: areaOps, settingOps: settingOps)
    }
}

/// Where a stretch of what was typed stands in the box.
///
/// Route 1 says where words stand as offsets into the text as it was sent,
/// counted in code points. The box holds the text as it was typed, with
/// whatever space stands before it. So an offset is carried over before the
/// box selects by it.
///
/// Nothing here keeps a word. It takes the text from the box, where it already
/// is, and gives back places in it, for the box to select, or the words of one
/// stretch, for the screen to draw beside an offer while the box holds them.
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

    /// The words of one stretch, cut from the box as it stands, or `nil` where the
    /// stretch is not in it. They are cut and never retyped: what is shown is what the
    /// person wrote. Whoever calls this must know that the box still holds what was
    /// sent, and must keep the words nowhere.
    public static func written(_ box: String, _ span: Span) -> String? {
        guard let found = inTheBox(box, [span]).first else { return nil }
        let words = box[found].trimmingCharacters(in: .whitespacesAndNewlines)
        return words.isEmpty ? nil : words
    }
}
