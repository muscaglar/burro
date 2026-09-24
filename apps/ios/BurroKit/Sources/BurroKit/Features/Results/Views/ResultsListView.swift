import SwiftUI

// The list of results, and everything that is said above it. It is complete
// without the map: whatever the map shows of a result, its card says in words.
//
// The order of the list is the rank. When an area is chosen on the map its
// card is brought into view, and the focus stays where it was.

extension Results {
    struct ListView: View {
        let listed: Listed
        /// The area chosen on the map, said in words at the head of the list. `nil` with no map.
        let chosen: Chosen?
        let ground: Ground
        let hands: Hands
        @Bindable var memory: Memory
        @Environment(\.accessibilityReduceMotion) var reduceMotion

        var body: some View {
            ScrollViewReader { reader in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: Tokens.Space.s4) {
                        StatusView(listed: listed)
                            .id(Memory.top)
                        if let chosen {
                            ChosenView(chosen: chosen, hands: hands)
                        }
                        ForEach(listed.lines) { line in
                            LineView(line: line) { act in
                                Task { await hands.act(act) }
                            }
                        }
                        if let nothing = listed.nothing {
                            NothingView(nothing: nothing) { act in
                                Task { await hands.act(act) }
                            }
                        }
                        if !listed.empty {
                            TrayView(tray: tray(memory.compared(among: hands.search.state.areas)), hands: hands)
                        }
                        if hands.canShare {
                            ShareView(hands: hands, memory: memory)
                                .id(Memory.sharePanel)
                        }
                        if listed.empty && !listed.busy {
                            Text(ResultsCopy.Card.waiting)
                                .font(Tokens.Text.body)
                                .foregroundStyle(Tokens.Colour.muted)
                        }
                        if listed.empty && listed.busy {
                            ForEach(0..<inFull, id: \.self) { _ in
                                Skeleton(lines: 4)
                            }
                        }
                        cards
                        if !listed.empty {
                            FootView(release: listed.release, engine: listed.engine)
                        }
                    }
                    .padding(Tokens.Space.gutter)
                }
                // It is asked for before the list is drawn when the list is what a press leads to.
                .onChange(of: memory.bringIntoView, initial: true) { _, wanted in
                    guard let wanted else { return }
                    let inList = wanted == Memory.sharePanel || listed.cards.contains { $0.id == wanted }
                    withAnimation(Tokens.Motion.animation(Tokens.Motion.slow, reduceMotion: reduceMotion)) {
                        reader.scrollTo(inList ? wanted : Memory.top, anchor: .top)
                    }
                    memory.bringIntoView = nil
                }
            }
            .background(Tokens.Colour.bg)
        }

        @ViewBuilder
        private var cards: some View {
            let firstRow = listed.cards.first { !$0.full }?.id
            ForEach(listed.cards) { card in
                if card.id == firstRow {
                    Text(ResultsCopy.Card.firstFive)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.muted)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                CardView(card: card, ground: ground, hands: hands)
                    .id(card.id)
            }
        }
    }

    /// What was ranked and what changed, and what is being waited for.
    struct StatusView: View {
        let listed: Listed

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                if let waitingFor = listed.waitingFor {
                    HStack(alignment: .center, spacing: Tokens.Space.s2) {
                        ProgressView()
                            .accessibilityHidden(true)
                        Text(waitingFor)
                            .font(Tokens.Text.body)
                            .foregroundStyle(Tokens.Colour.text)
                    }
                    .accessibilityElement(children: .combine)
                }
                if let headline = listed.headline {
                    Text(headline)
                        .font(Tokens.Text.title)
                        .foregroundStyle(Tokens.Colour.text)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .accessibilityAddTraits(.isHeader)
                }
                ForEach(listed.changes, id: \.self) { change in
                    Text(change)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.muted)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
    }

    /// Said when no area passes every limit: why, and what would loosen each limit.
    struct NothingView: View {
        let nothing: NothingMatches
        let act: (Act) -> Void

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s3) {
                Text(ResultsCopy.NothingMatches.lead)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.text)
                    .frame(maxWidth: .infinity, alignment: .leading)
                ForEach(nothing.counts) { count in
                    Named(name: count.reason, value: count.areas)
                }
                if !nothing.ways.isEmpty {
                    PartTitle(words: ResultsCopy.NothingMatches.loosen)
                    ForEach(nothing.ways) { way in
                        Button(way.words) { act(way.act) }
                            .buttonStyle(.burroSecondary)
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
    }

    /// The release and the engine behind the list.
    struct FootView: View {
        let release: String
        let engine: String

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                Text(verbatim: "\(ResultsCopy.Card.release) \(release)")
                Text(verbatim: "\(ResultsCopy.Card.engine) \(engine)")
            }
            .font(Tokens.Text.code)
            .foregroundStyle(Tokens.Colour.muted)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    /// The panel that holds the list over the map, at one of three heights.
    /// It is pulled by its handle, and the handle is a control as well: a
    /// press takes the next height, so nothing here needs a drag.
    struct SheetView<Content: View>: View {
        @Binding var height: Height
        /// How tall the room is that the map and the list share.
        let room: CGFloat
        let content: () -> Content
        @GestureState var pulled: CGFloat = 0
        @Environment(\.accessibilityReduceMotion) var reduceMotion

        init(height: Binding<Height>, room: CGFloat, @ViewBuilder content: @escaping () -> Content) {
            _height = height
            self.room = room
            self.content = content
        }

        /// The least the panel stands: its handle, and room for a line under it.
        static var least: CGFloat { Tokens.Target.least * 2.5 }

        var body: some View {
            let tall = CGFloat(height.points(in: Double(room), least: Double(Self.least)))
            VStack(spacing: 0) {
                handle(tall: tall)
                content()
            }
            .frame(height: min(max(tall - pulled, Self.least), room))
            .frame(maxWidth: .infinity)
            .background(
                Tokens.Colour.bg,
                in: UnevenRoundedRectangle(
                    topLeadingRadius: Tokens.Radius.sheet, topTrailingRadius: Tokens.Radius.sheet)
            )
            .overlay(alignment: .top) {
                UnevenRoundedRectangle(
                    topLeadingRadius: Tokens.Radius.sheet, topTrailingRadius: Tokens.Radius.sheet
                )
                .strokeBorder(Tokens.Colour.border, lineWidth: 1)
                .accessibilityHidden(true)
                .allowsHitTesting(false)
            }
        }

        private func set(_ next: Height) {
            withAnimation(Tokens.Motion.animation(Tokens.Motion.slow, reduceMotion: reduceMotion)) {
                height = next
            }
        }

        private func handle(tall: CGFloat) -> some View {
            Button {
                set(height.next)
            } label: {
                Capsule()
                    .fill(Tokens.Colour.border)
                    .frame(width: Tokens.Space.s6 + Tokens.Space.s1, height: Tokens.Space.s1 + 1)
                    .frame(maxWidth: .infinity, minHeight: Tokens.Target.least)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .simultaneousGesture(
                DragGesture(minimumDistance: Tokens.Space.s2)
                    .updating($pulled) { value, pulled, _ in pulled = value.translation.height }
                    .onEnded { value in
                        guard room > 0 else { return }
                        set(.nearest(to: Double((tall - value.predictedEndTranslation.height) / room)))
                    }
            )
            .accessibilityLabel(ResultsCopy.Sheet.handle)
            .accessibilityValue(height.words)
            .accessibilityAdjustableAction { direction in
                switch direction {
                case .increment: set(height.taller)
                case .decrement: set(height.shorter)
                @unknown default: break
                }
            }
        }
    }
}
