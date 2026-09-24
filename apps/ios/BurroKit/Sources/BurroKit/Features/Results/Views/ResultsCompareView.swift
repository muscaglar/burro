import SwiftUI

// Comparing two to four areas, and the tray that holds the areas chosen.
//
// The comparison is one table: a row for each thing that counts, in the
// order the API gave them, and under it each area by name. It is stacked, as
// the website stacks it on a narrow screen, so that it reads at the largest
// size of text: no figure is ever squeezed into a column.
//
// It is drawn in place, under the banner, and never in a sheet of its own.

extension Results {
    /// The areas chosen to compare, above the results.
    struct TrayView: View {
        let tray: Tray
        let hands: Hands

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                PartTitle(words: ResultsCopy.Tray.title)
                if let words = tray.words {
                    Text(words)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.muted)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                ForEach(tray.areas) { area in
                    Beside {
                        Text(area.name)
                            .font(Tokens.Text.body)
                            .foregroundStyle(Tokens.Colour.text)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        Button(ResultsCopy.Tray.remove(area.name)) { hands.toggleCompare(area) }
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.accent)
                            .target()
                    }
                }
                if let go = tray.go {
                    Button(go) { hands.compare() }
                        .buttonStyle(.burroPrimary)
                }
                if !tray.areas.isEmpty {
                    Button(ResultsCopy.Tray.clear) { hands.memory.compare = [] }
                        .buttonStyle(.burroSecondary)
                }
            }
            .padding(Tokens.Space.s3)
            .frame(maxWidth: .infinity, alignment: .leading)
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(Tokens.Colour.border, lineWidth: 1)
            )
            .accessibilityElement(children: .contain)
            .accessibilityLabel(ResultsCopy.Tray.title)
        }
    }

    /// The comparison, in place of the results until the person goes back to choose others.
    struct CompareView: View {
        let chosen: [AreaRef]
        let hands: Hands
        @State var comparison = Comparison()

        var body: some View {
            let state = hands.search.state
            ScrollView {
                VStack(alignment: .leading, spacing: Tokens.Space.s4) {
                    Text(ResultsCopy.Compare.lead)
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.muted)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    if !isEnough(chosen) {
                        Text(ResultsCopy.Compare.tooFewHere)
                            .font(Tokens.Text.body)
                            .foregroundStyle(Tokens.Colour.text)
                    } else {
                        switch comparison.answer {
                        case .waiting:
                            ProgressView()
                                .accessibilityHidden(true)
                            Text(ResultsCopy.Compare.comparing)
                                .font(Tokens.Text.body)
                                .foregroundStyle(Tokens.Colour.text)
                        case .failed(let words, let requestId):
                            LineView(
                                line: Line(
                                    .failure, [ResultsCopy.Compare.failedTitle, words], requestId: requestId,
                                    presses: [Press(words: ResultsCopy.Notice.tryAgain, act: .retry)]),
                                act: { _ in Task { await comparison.ask(chosen, of: hands.search, again: true) } })
                        case .here(let compared):
                            ComparedView(compared: compared, hands: hands)
                        }
                    }
                    Button(ResultsCopy.Compare.chooseOthers) { hands.chooseOthers() }
                        .buttonStyle(.burroSecondary)
                }
                .padding(Tokens.Space.gutter)
            }
            .background(Tokens.Colour.bg)
            // It is asked for again when the areas or the search change, and not otherwise.
            .task(id: question(chosen, of: state)) {
                await comparison.ask(chosen, of: hands.search)
            }
        }
    }

    /// The areas compared, and the table.
    struct ComparedView: View {
        let compared: Compared
        let hands: Hands

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s5) {
                if let basis = compared.basis {
                    Text(basis)
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.text)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                VStack(alignment: .leading, spacing: Tokens.Space.s3) {
                    PartTitle(words: ResultsCopy.CompareTable.areas)
                    ForEach(compared.places) { place in
                        PlaceView(place: place, alone: compared.places.count <= leastCompared, hands: hands)
                    }
                }
                // The vibes of each area come first. They are of the release, and are
                // compared whatever the search holds.
                if !compared.character.isEmpty {
                    VStack(alignment: .leading, spacing: Tokens.Space.s4) {
                        Text(ResultsCopy.CompareTable.character)
                            .font(Tokens.Text.title)
                            .foregroundStyle(Tokens.Colour.text)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .accessibilityAddTraits(.isHeader)
                        Text(ResultsCopy.CompareTable.characterCaption)
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.muted)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        ForEach(compared.character) { vibe in
                            VibeRowView(vibe: vibe)
                        }
                    }
                }
                if compared.nothingCounts {
                    Text(ResultsCopy.Compare.nothingCounts)
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.text)
                } else {
                    VStack(alignment: .leading, spacing: Tokens.Space.s4) {
                        Text(ResultsCopy.CompareTable.counts)
                            .font(Tokens.Text.title)
                            .foregroundStyle(Tokens.Colour.text)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .accessibilityAddTraits(.isHeader)
                        Text(ResultsCopy.CompareTable.caption)
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.muted)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        Text(ResultsCopy.CompareTable.weights)
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.muted)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        ForEach(compared.rows) { row in
                            RowView(row: row, openSources: hands.openSources)
                        }
                    }
                }
            }
        }
    }

    /// One of the areas compared: its name, its status in words, and where it stands in the search.
    struct PlaceView: View {
        let place: ComparedPlace
        /// True when taking this area out would leave too few to compare.
        let alone: Bool
        let hands: Hands

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                Text(place.name)
                    .font(Tokens.Text.headline)
                    .foregroundStyle(Tokens.Colour.text)
                    .accessibilityAddTraits(.isHeader)
                if let status = place.status {
                    Text(status)
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.text)
                }
                if let standing = place.standing {
                    Text(standing)
                        .font(Tokens.Text.figure)
                        .foregroundStyle(Tokens.Colour.text)
                }
                if let area = place.area {
                    Button(ResultsCopy.Card.open) { hands.open(area) }
                        .buttonStyle(.burroSecondary)
                        .accessibilityLabel(ResultsCopy.Card.openArea(place.name))
                    if !alone {
                        Button(ResultsCopy.Card.removeFromCompare) { hands.toggleCompare(area) }
                            .buttonStyle(.burroSecondary)
                            .accessibilityLabel(ResultsCopy.CompareTable.takeOut(place.name))
                    }
                }
            }
            .padding(Tokens.Space.s3)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Tokens.Colour.surface, in: RoundedRectangle(cornerRadius: Tokens.Radius.card))
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(Tokens.Colour.border, lineWidth: 1)
            )
        }
    }

    /// One vibe, and under it each area by name with where it sits on it.
    struct VibeRowView: View {
        let vibe: ComparedVibe

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s3) {
                Text(verbatim: vibe.name)
                    .font(Tokens.Text.headline)
                    .foregroundStyle(Tokens.Colour.text)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .accessibilityAddTraits(.isHeader)
                ForEach(vibe.cells) { cell in
                    VibeLine(cell.vibe, of: cell.area, source: Results.sourceWords(of: cell.vibe))
                        .padding(.leading, Tokens.Space.s3)
                        .overlay(alignment: .leading) {
                            Rectangle()
                                .fill(Tokens.Colour.border)
                                .frame(width: 2)
                                .accessibilityHidden(true)
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

    /// One thing that counts, and under it each area by name with what it has for it.
    struct RowView: View {
        let row: ComparedRow
        let openSources: () -> Void

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s3) {
                VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                    Text(row.label)
                        .font(Tokens.Text.headline)
                        .foregroundStyle(Tokens.Colour.text)
                    if let to = row.to {
                        Text(verbatim: to)
                            .font(Tokens.Text.body)
                            .foregroundStyle(Tokens.Colour.text)
                    }
                    Text(row.countsFor)
                        .font(Tokens.Text.figure)
                        .foregroundStyle(Tokens.Colour.muted)
                    if let caveat = row.caveat {
                        Text(caveat)
                            .font(Tokens.Text.footnote)
                            .foregroundStyle(Tokens.Colour.muted)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityElement(children: .combine)
                .accessibilityAddTraits(.isHeader)
                ForEach(row.cells) { cell in
                    VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                        Text(cell.area)
                            .font(Tokens.Text.body.weight(.semibold))
                            .foregroundStyle(Tokens.Colour.text)
                        ForEach(cell.columns) { column in
                            Named(name: column.name, value: column.value)
                        }
                        if let adds = cell.adds {
                            Text(adds)
                                .font(Tokens.Text.figure)
                                .foregroundStyle(Tokens.Colour.text)
                        }
                        if let none = cell.none {
                            Text(none)
                                .font(Tokens.Text.secondary)
                                .foregroundStyle(Tokens.Colour.muted)
                        } else {
                            SourceLines(
                                lines: cell.sources, of: "\(row.label), \(cell.area)", openSources: openSources)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.leading, Tokens.Space.s3)
                    .overlay(alignment: .leading) {
                        Rectangle()
                            .fill(Tokens.Colour.border)
                            .frame(width: 2)
                            .accessibilityHidden(true)
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
}
