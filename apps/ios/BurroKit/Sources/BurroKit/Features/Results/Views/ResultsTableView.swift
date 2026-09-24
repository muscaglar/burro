import SwiftUI

// The table of every area, and the small picture that says where one area is
// among the rest.
//
// The table is the list that says everything the map does: every area of the
// release, with its rank, its fit, and in words why it has none. It is one
// press away from the map, and it is what is shown where the map cannot be drawn.

extension Results {
    struct TableView: View {
        let tabled: Tabled
        let hands: Hands

        var body: some View {
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 0) {
                    Text(tabled.caption)
                        .font(Tokens.Text.title)
                        .foregroundStyle(Tokens.Colour.text)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.bottom, Tokens.Space.s3)
                        .accessibilityAddTraits(.isHeader)
                    ForEach(tabled.rows) { row in
                        AreaRowView(row: row, hands: hands)
                        Rectangle()
                            .fill(Tokens.Colour.border)
                            .frame(height: 1)
                            .accessibilityHidden(true)
                    }
                }
                .padding(Tokens.Space.gutter)
            }
            .background(Tokens.Colour.bg)
        }
    }

    /// One area of the release: its rank, its name and borough, its fit, and its status in words.
    struct AreaRowView: View {
        let row: AreaRow
        let hands: Hands

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                Button {
                    hands.open(row.area)
                } label: {
                    Beside {
                        if let rank = row.rank {
                            RankDisc(rank: rank)
                        }
                        VStack(alignment: .leading, spacing: 0) {
                            Text(row.area.name)
                                .font(Tokens.Text.headline)
                                .foregroundStyle(Tokens.Colour.text)
                            Text(row.area.borough)
                                .font(Tokens.Text.secondary)
                                .foregroundStyle(Tokens.Colour.muted)
                            Text(row.status)
                                .font(Tokens.Text.secondary)
                                .foregroundStyle(Tokens.Colour.text)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        if row.fit != nil {
                            Text(verbatim: "\(ResultsCopy.Table.fit) \(row.fitWords)")
                                .font(Tokens.Text.figure)
                                .foregroundStyle(Tokens.Colour.text)
                        }
                        Image(systemName: "chevron.right")
                            .foregroundStyle(Tokens.Colour.muted)
                            .accessibilityHidden(true)
                    }
                    .multilineTextAlignment(.leading)
                    .frame(maxWidth: .infinity, minHeight: Tokens.Target.row, alignment: .leading)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(row.words)
                .accessibilityHint(ResultsCopy.Card.openArea(row.area.name))
                .accessibilityAddTraits(row.selected ? .isSelected : [])
                Button(row.selected ? ResultsCopy.MapCard.close : ResultsCopy.Table.show) {
                    hands.choose(inTable: row.area)
                }
                .buttonStyle(.burroSecondary)
                .accessibilityLabel(
                    row.selected
                        ? ResultsCopy.Card.of(ResultsCopy.MapCard.close, row.area.name)
                        : ResultsCopy.Table.select(row.area.name))
                if row.selected {
                    Text(ResultsCopy.Card.selected)
                        .font(Tokens.Text.footnote.weight(.semibold))
                        .foregroundStyle(Tokens.Colour.text)
                }
            }
            .padding(.vertical, Tokens.Space.s2)
        }
    }

    /// Where one area is among the areas of this data: every outline, with
    /// the one area filled. It is a picture, and its name says what it shows.
    struct Locator: View {
        let ground: Ground
        let areaId: String
        let name: String

        var body: some View {
            Canvas { context, size in
                guard let bounds = Results.bounds(of: ground.outlines) else { return }
                let projector = Projector(
                    bounds: bounds, width: size.width, height: size.height, padding: Tokens.Space.s2)
                for outline in ground.outlines {
                    var path = Path()
                    for ring in outline.rings {
                        guard let first = ring.first else { continue }
                        let start = projector.place(first)
                        path.move(to: CGPoint(x: start.x, y: start.y))
                        for corner in ring.dropFirst() {
                            let at = projector.place(corner)
                            path.addLine(to: CGPoint(x: at.x, y: at.y))
                        }
                        path.closeSubpath()
                    }
                    let here = outline.areaId == areaId
                    context.fill(
                        path, with: .style(here ? Tokens.Colour.mapLine : Tokens.Colour.mapLand),
                        style: FillStyle(eoFill: true))
                    context.stroke(path, with: .style(Tokens.Colour.mapLine), lineWidth: here ? 2 : 0.5)
                }
            }
            .aspectRatio(4.0 / 3.0, contentMode: .fit)
            .frame(maxWidth: Tokens.Space.s8 * 3)
            .background(Tokens.Colour.mapWater, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(ResultsCopy.Locator.title(name))
            .accessibilityAddTraits(.isImage)
        }
    }
}
