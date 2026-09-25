import SwiftUI

/// Five cells from the low end of a vibe to its high end, with the one the
/// area sits in filled. A mixed area fills the cells it spans, and is never
/// drawn as a point in the middle.
///
/// It is a picture, and is kept from a screen reader: the words beside it say
/// what it shows.
public struct VibeTrack: View {
    private let placed: Placed

    public init(_ placed: Placed) {
        self.placed = placed
    }

    public var body: some View {
        HStack(spacing: Tokens.Space.s1) {
            ForEach(Array(Placed.bands), id: \.self) { cell in
                RoundedRectangle(cornerRadius: Tokens.Radius.small)
                    .fill(placed.fills(cell) ? Tokens.Colour.text : Tokens.Colour.bg)
                    .overlay(
                        RoundedRectangle(cornerRadius: Tokens.Radius.small)
                            .strokeBorder(Tokens.Colour.text, lineWidth: 1)
                    )
                    .frame(width: Tokens.Space.s5, height: Tokens.Space.s3)
            }
        }
        .accessibilityHidden(true)
    }
}

/// One vibe of an area: its name, the line of five with its two ends, where
/// the area sits in words, what the band rests on, and what the vibe waits on.
///
/// A vibe is a band between two named ends, and never a score or a
/// percentage. The band is said in words beside the picture. An area a vibe
/// cannot place is said to be so, and is never put in the middle. It is read
/// as one. A vibe that is a rough guide says so under its band, with why: the
/// line is drawn, and is behind no press.
public struct VibeLine: View {
    private let vibe: VibeShown
    /// The area the line is of, where several areas stand under one vibe. The
    /// line is then headed by the area's name, and the vibe is named over them all.
    private let area: String?
    /// The source and the date of the band, as one line, where they are in hand.
    private let source: String?

    public init(_ vibe: VibeShown, of area: String? = nil, source: String? = nil) {
        self.vibe = vibe
        self.area = area
        self.source = source
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s1) {
            Text(verbatim: area ?? vibe.name)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
            if let placed = vibe.placed {
                // Side by side where there is room, and one above the other where there is not.
                ViewThatFits(in: .horizontal) {
                    HStack(alignment: .center, spacing: Tokens.Space.s2) {
                        end(vibe.low)
                        VibeTrack(placed)
                        end(vibe.high)
                    }
                    VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                        VibeTrack(placed)
                        end(VibeCopy.from(vibe.low, vibe.high))
                    }
                }
            }
            Text(verbatim: VibeLine.sits(vibe))
                .font(Tokens.Text.body)
                .foregroundStyle(Tokens.Colour.text)
            ForEach(notes, id: \.self) { note in
                Text(verbatim: note)
                    .font(Tokens.Text.secondary)
                    .foregroundStyle(Tokens.Colour.muted)
            }
            if let source {
                Text(verbatim: source)
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
            }
        }
        .fixedSize(horizontal: false, vertical: true)
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Text(verbatim: VibeLine.spoken(vibe, of: area, source: source)))
    }

    private var notes: [String] {
        VibeLine.notes(of: vibe)
    }

    private func end(_ name: String) -> some View {
        Text(verbatim: name)
            .font(Tokens.Text.footnote)
            .foregroundStyle(Tokens.Colour.muted)
    }

    // MARK: - What it says

    /// Where the area sits, in words: where it sits between the two ends and
    /// its band, or that it cannot be placed.
    static func sits(_ vibe: VibeShown) -> String {
        [vibe.plainly, vibe.band].compactMap { $0 }.joined(separator: ", ")
    }

    /// What follows the band: that the vibe is a rough guide, and why, that it
    /// was asked for, what it rests on, and what the vibe waits on.
    static func notes(of vibe: VibeShown) -> [String] {
        var notes: [String] = []
        if let rough = vibe.rough { notes.append(rough) }
        if let asked = vibe.asked { notes.append(asked) }
        if let restsOn = vibe.restsOn { notes.append(restsOn) }
        if vibe.notInData { notes.append(VibeCopy.noAreaPlaced) }
        if let held = vibe.held { notes.append(held) }
        if !vibe.waitsOn.isEmpty {
            notes.append(VibeCopy.waitsOn(vibe.waitsOn.joined(separator: "; ")))
        }
        return notes
    }

    /// The whole line as it is read out: everything that is drawn, once each.
    static func spoken(_ vibe: VibeShown, of area: String? = nil, source: String?) -> String {
        ((area.map { [$0] } ?? []) + [vibe.reads] + (source.map { [$0] } ?? [])).joined(separator: ". ")
    }
}

/// A vibe that no area of the data can be placed on, where a control for it
/// would stand: its name, that it is not in the data yet, how much of its
/// recipe the data holds, and what it waits on, by name. Nothing is offered
/// that the API could only turn away.
public struct VibeWaiting: View {
    private let name: String
    private let held: RecipeHeld?

    public init(name: String, held: RecipeHeld?) {
        self.name = name
        self.held = held
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s1) {
            Text(verbatim: name)
                .font(Tokens.Text.body)
                .foregroundStyle(Tokens.Colour.text)
            ForEach(VibeWaiting.lines(held), id: \.self) { line in
                Text(verbatim: line)
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
            }
        }
        .fixedSize(horizontal: false, vertical: true)
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .combine)
    }

    /// What is said under the name: that it is not in the data yet, how much
    /// of its recipe is held, and what it waits on.
    static func lines(_ held: RecipeHeld?) -> [String] {
        var lines = [VibeCopy.notYet, VibeCopy.noAreaPlaced]
        if let held { lines.append(VibeCopy.held(held.held, needed: held.needed)) }
        let parts = Vibes.waitsOn(held)
        if !parts.isEmpty { lines.append(VibeCopy.waitsOn(parts.joined(separator: "; "))) }
        return lines
    }
}
