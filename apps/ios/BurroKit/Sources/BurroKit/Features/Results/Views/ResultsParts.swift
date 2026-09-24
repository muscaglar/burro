import SwiftUI

// The small parts every view of the results is made of. Each draws what it
// is handed and works nothing out: the words and the figures are made in
// `Model/`, where they are tested.
//
// Text takes a style from `Tokens.Text`, so it grows with the size a person
// has chosen, and nothing fixes the height of text. At the largest sizes what
// stands side by side is set one under the other.

extension Results {
    /// Sets its parts side by side, and one under the other at the largest sizes of text.
    struct Beside<Content: View>: View {
        @Environment(\.dynamicTypeSize) private var size
        private let spacing: CGFloat
        private let content: () -> Content

        init(spacing: CGFloat = Tokens.Space.s3, @ViewBuilder content: @escaping () -> Content) {
            self.spacing = spacing
            self.content = content
        }

        var body: some View {
            if size.isAccessibilitySize {
                VStack(alignment: .leading, spacing: spacing, content: content)
            } else {
                HStack(alignment: .firstTextBaseline, spacing: spacing, content: content)
            }
        }
    }

    /// The title of a part of a card.
    struct PartTitle: View {
        let words: String

        var body: some View {
            Text(words)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityAddTraits(.isHeader)
        }
    }

    /// What is called something, and its value: "Middle", then the figure.
    struct Named: View {
        let name: String
        let value: String

        var body: some View {
            Beside(spacing: Tokens.Space.s2) {
                Text(name)
                    .font(Tokens.Text.secondary)
                    .foregroundStyle(Tokens.Colour.muted)
                Text(value)
                    .font(Tokens.Text.figure)
                    .foregroundStyle(Tokens.Colour.text)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityElement(children: .combine)
        }
    }

    /// The source and the date behind a line, written out so that it is read
    /// without a press. With no fact in hand it leads to the sources instead.
    struct SourceLines: View {
        let lines: [SourceLine]
        /// What the source is of, to tell one from the next when it is read out.
        let of: String?
        let openSources: () -> Void

        var body: some View {
            if lines.isEmpty {
                Button(action: openSources) {
                    Text(ResultsCopy.Source.source)
                        .font(Tokens.Text.footnote)
                        .underline()
                        .foregroundStyle(Tokens.Colour.accent)
                        .target()
                }
                .buttonStyle(.plain)
                .accessibilityLabel(of.map(ResultsCopy.Source.sourceFor) ?? ResultsCopy.Source.source)
            } else {
                VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                    ForEach(lines) { line in
                        Text(line.words)
                            .font(Tokens.Text.footnote)
                            .foregroundStyle(Tokens.Colour.muted)
                            .multilineTextAlignment(.leading)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
        }
    }

    /// One sentence about a place, as the API wrote it, ending in its source.
    /// It is read out whole: the sentence, and then where it came from.
    struct SentenceView: View {
        let sentence: Sentence
        let of: String?
        let openSources: () -> Void

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                Text(sentence.text)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.text)
                    .frame(maxWidth: .infinity, alignment: .leading)
                if sentence.byModel {
                    Text(ResultsCopy.Card.byModel)
                        .font(Tokens.Text.footnote)
                        .foregroundStyle(Tokens.Colour.muted)
                }
                SourceLines(lines: sentence.sources, of: of, openSources: openSources)
            }
            .accessibilityElement(children: sentence.sources.isEmpty ? .contain : .combine)
        }
    }

    /// A bar that repeats a figure written beside it. It is kept from a screen reader.
    struct Meter: View {
        /// From 0 to 100.
        let filled: Int

        var body: some View {
            GeometryReader { room in
                ZStack(alignment: .leading) {
                    Rectangle().fill(Tokens.Colour.bg)
                    Rectangle()
                        .fill(Tokens.Colour.mapLine)
                        .frame(width: room.size.width * CGFloat(min(max(filled, 0), ResultsCopy.most)) / 100)
                }
            }
            .frame(height: Tokens.Space.s2)
            .clipShape(RoundedRectangle(cornerRadius: Tokens.Radius.small))
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.small)
                    .strokeBorder(Tokens.Colour.border, lineWidth: 1)
            )
            .accessibilityHidden(true)
        }
    }

    /// The rank, as a number in a disc. It grows with the text it holds.
    struct RankDisc: View {
        let rank: Int
        var large = false

        var body: some View {
            Text(String(rank))
                .font(large ? Tokens.Text.headline.monospacedDigit() : Tokens.Text.figure.weight(.bold))
                .foregroundStyle(Tokens.Colour.bg)
                .padding(.horizontal, Tokens.Space.s2)
                .padding(.vertical, Tokens.Space.s1)
                .frame(minWidth: Tokens.Space.s6, minHeight: Tokens.Space.s6)
                .background(Tokens.Colour.mapLine, in: Capsule())
                .accessibilityLabel(ResultsCopy.Card.rank(rank))
        }
    }

    /// Room kept for what has not come yet. It does not move.
    struct Skeleton: View {
        var lines = 1

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                ForEach(0..<max(lines, 1), id: \.self) { _ in
                    RoundedRectangle(cornerRadius: Tokens.Radius.small)
                        .fill(Tokens.Colour.surface)
                        .frame(maxWidth: .infinity)
                        .frame(height: Tokens.Space.s4)
                }
            }
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(ResultsCopy.Card.loading)
        }
    }

    /// A block that says something about the search: a notice, a failure, that the phone is offline.
    struct LineView: View {
        let line: Line
        let act: (Act) -> Void

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                ForEach(Array(line.words.enumerated()), id: \.offset) { _, words in
                    Text(words)
                        .font(Tokens.Text.body)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                if let requestId = line.requestId {
                    Text(verbatim: "\(ResultsCopy.Notice.requestId) \(requestId)")
                        .font(Tokens.Text.code)
                        .textSelection(.enabled)
                }
                ForEach(line.presses) { press in
                    Button(press.words) { act(press.act) }
                        .buttonStyle(.burroSecondary)
                }
            }
            .foregroundStyle(ink)
            .padding(Tokens.Space.s3)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(paper, in: RoundedRectangle(cornerRadius: Tokens.Radius.card))
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(edge, lineWidth: 1)
            )
            .accessibilityElement(children: .contain)
            .accessibilityLabel(ResultsCopy.Notice.label)
        }

        private var ink: TokenColor {
            switch line.kind {
            case .notice: return Tokens.Colour.infoText
            case .failure: return Tokens.Colour.error
            case .info, .offline: return Tokens.Colour.text
            }
        }

        private var paper: TokenColor {
            line.kind == .notice ? Tokens.Colour.infoBg : Tokens.Colour.surface
        }

        private var edge: TokenColor {
            line.kind == .failure ? Tokens.Colour.error : Tokens.Colour.border
        }
    }

    /// A part that opens in place, closed at first. The button says what it opens.
    struct Opening<Content: View>: View {
        let title: String
        /// What it is the breakdown of, to tell one from the next when it is read out.
        let of: String?
        @State var open = false
        @Environment(\.accessibilityReduceMotion) var reduceMotion
        @ViewBuilder let content: () -> Content

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                Button {
                    withAnimation(Tokens.Motion.animation(Tokens.Motion.fast, reduceMotion: reduceMotion)) {
                        open.toggle()
                    }
                } label: {
                    HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                        Image(systemName: open ? "chevron.down" : "chevron.right")
                            .accessibilityHidden(true)
                        Text(title)
                            .multilineTextAlignment(.leading)
                        Spacer(minLength: 0)
                    }
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.accent)
                    .frame(maxWidth: .infinity, minHeight: Tokens.Target.least, alignment: .leading)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(of.map { "\(title): \($0)" } ?? title)
                .accessibilityValue(open ? ResultsCopy.Legend.open : ResultsCopy.Legend.closed)
                if open {
                    content()
                }
            }
        }
    }
}
