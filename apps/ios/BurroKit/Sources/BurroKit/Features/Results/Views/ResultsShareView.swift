import SwiftUI

// Sharing the search. The panel opens in place and says what the link will
// hold before anything is made. "Share the exact places" is off until the
// person turns it on. The link is handed to the phone's own share sheet when
// the person presses "Share", and to nothing else: it is not copied for them,
// not written to the phone, and not shown as text.
//
// It is offered only when the website has an address to make a link to.

extension Results {
    struct ShareView: View {
        let hands: Hands
        @Bindable var memory: Memory

        var body: some View {
            let state = hands.search.state
            let sharing = memory.sharing
            let linking = sharing.shown(for: state)
            VStack(alignment: .leading, spacing: Tokens.Space.s3) {
                Button {
                    memory.shareOpen.toggle()
                } label: {
                    HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                        Image(systemName: memory.shareOpen ? "chevron.down" : "chevron.right")
                            .accessibilityHidden(true)
                        Text(ResultsCopy.Share.open)
                        Spacer(minLength: 0)
                    }
                    .font(Tokens.Text.headline)
                    .foregroundStyle(Tokens.Colour.accent)
                    .frame(maxWidth: .infinity, minHeight: Tokens.Target.least, alignment: .leading)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityValue(memory.shareOpen ? ResultsCopy.Legend.open : ResultsCopy.Legend.closed)

                if memory.shareOpen {
                    PartTitle(words: ResultsCopy.Share.holdsTitle)
                    ForEach(ResultsCopy.Share.points, id: \.self) { point in
                        HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                            Text(verbatim: "•")
                                .accessibilityHidden(true)
                            Text(point)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.text)
                    }
                    if state.spec.commutes.isEmpty {
                        Text(ResultsCopy.Share.noPlaces)
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.muted)
                    } else {
                        @Bindable var sharing = sharing
                        Toggle(ResultsCopy.Share.exact, isOn: $sharing.exact)
                            .font(Tokens.Text.body)
                            .foregroundStyle(Tokens.Colour.text)
                            .frame(minHeight: Tokens.Target.least)
                        Text(ResultsCopy.Share.exactHintHere)
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.muted)
                    }
                    Button(makeWords(linking)) {
                        Task { await hands.makeLink() }
                    }
                    .buttonStyle(.burroSecondary)
                    .disabled(linking == .making)

                    if sharing.isGone(for: state) {
                        Text(ResultsCopy.Share.gone)
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.muted)
                    }
                    switch linking {
                    case .idle, .making:
                        EmptyView()
                    case .failed(let words, let requestId):
                        LineView(
                            line: Line(.failure, [ResultsCopy.Share.failed, words], requestId: requestId),
                            act: { _ in })
                    case .made(let link):
                        Text(ResultsCopy.Share.made)
                            .font(Tokens.Text.body)
                            .foregroundStyle(Tokens.Colour.text)
                        Text(link.words)
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.muted)
                        // The phone's own share sheet. The app hands it the link and draws nothing of it.
                        ShareLink(item: link.url) {
                            Text(ResultsCopy.Share.share)
                        }
                        .buttonStyle(.burroPrimary)
                        .accessibilityLabel("\(ResultsCopy.Share.share): \(ResultsCopy.Share.link)")
                    }
                }
            }
            .padding(Tokens.Space.s3)
            .frame(maxWidth: .infinity, alignment: .leading)
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(Tokens.Colour.border, lineWidth: 1)
            )
        }

        private func makeWords(_ linking: Linking) -> String {
            switch linking {
            case .making: return ResultsCopy.Share.making
            case .made: return ResultsCopy.Share.makeAgain
            case .idle, .failed: return ResultsCopy.Share.make
            }
        }
    }
}
