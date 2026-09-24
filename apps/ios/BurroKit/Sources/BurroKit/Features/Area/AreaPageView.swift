import SwiftUI

/// The page of one area, once there is something to show: the API's answer,
/// or the copy the shortlist kept.
struct AreaPageView: View {
    @Environment(AppModel.self) private var app
    let page: AreaPage
    let origin: AreaLoader.Origin
    let keptIsOlder: Bool
    let keepNewer: () -> Void
    let again: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s5) {
            head
            notices
            AreaActions(page: page)
            if let search = app.search, let inSearch = AreaInSearch(search.state, areaId: page.area.areaId) {
                AreaInSearchSection(inSearch: inSearch)
            }
            if !page.vibes.isEmpty {
                AreaCharacterSection(page: page)
            }
            AreaWhereSection(page: page)
            AreaSection(title: AreaCopy.Stations.title) {
                AreaFactRows(rows: page.stationRows, none: AreaCopy.Stations.none)
            }
            AreaSection(title: AreaCopy.Cost.title, lead: AreaCopy.Cost.lead) {
                AreaPart(title: AreaCopy.Cost.rent) {
                    AreaFactRows(rows: page.rentRows, none: AreaCopy.Cost.noRent)
                }
                AreaPart(title: AreaCopy.Cost.buy) {
                    AreaFactRows(rows: page.buyRows, none: AreaCopy.Cost.noPrice)
                }
            }
            if !page.measured.isEmpty {
                AreaSection(title: AreaCopy.Measured.title, lead: AreaCopy.Measured.lead) {
                    ForEach(page.measured) { group in
                        let rows = page.rows(of: group)
                        // A group this build has no word for is left out, and never shown as its code.
                        if let title = title(of: group), !rows.isEmpty {
                            AreaPart(title: title) {
                                AreaFactRows(rows: rows, none: nil)
                            }
                        }
                    }
                }
            }
            AreaSourcesSection(page: page)
        }
    }

    private func title(of group: AreaPage.Group) -> String? {
        guard let dimension = group.dimension else { return AreaCopy.noGroups }
        return AreaCopy.dimension(dimension)
    }

    private var head: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            // The name is written on the page, where it wraps at any size of text.
            Text(page.name)
                .font(Tokens.Text.largeTitle)
                .foregroundStyle(Tokens.Colour.text)
                .accessibilityAddTraits(.isHeader)
            AreaLabelled(name: AreaCopy.borough, value: page.borough)
            if let named = page.named, let words = SourceLines.words(for: [named]) {
                AreaSourceWords(words: words)
            }
            if !page.rankable {
                Text(AreaCopy.notRanked)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.infoText)
                    .padding(Tokens.Space.s3)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Tokens.Colour.infoBg, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
            }
        }
    }

    @ViewBuilder
    private var notices: some View {
        switch origin {
        case .api:
            if keptIsOlder {
                AreaNotice {
                    Text(AreaCopy.changedSince)
                    Button(AreaCopy.keepNewer, action: keepNewer)
                        .buttonStyle(.burroSecondary)
                }
            }
        case .kept(let savedOn, let failure):
            AreaNotice {
                Text(ShellCopy.words(for: failure))
                Text(AreaCopy.asSaved(on: ShortlistCopy.date(savedOn), release: page.releaseId))
                // Where the API has said the area is gone, asking again would be told the same.
                if !(failure.api.map { $0.status < 500 } ?? false) {
                    Button(ShellCopy.tryAgain, action: again)
                        .buttonStyle(.burroSecondary)
                }
            }
        }
    }
}

/// A plain block that says something of the page, above it.
struct AreaNotice<Content: View>: View {
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            content()
        }
        .font(Tokens.Text.body)
        .foregroundStyle(Tokens.Colour.infoText)
        .padding(Tokens.Space.s3)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Tokens.Colour.infoBg, in: RoundedRectangle(cornerRadius: Tokens.Radius.card))
    }
}

/// "Add to shortlist" and "Share".
struct AreaActions: View {
    @Environment(AppModel.self) private var app
    let page: AreaPage

    var body: some View {
        let saved = app.saved
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            // The button says what it would do, so that whether the area is saved is never told by colour.
            Button(saved.contains(page.area.areaId) ? AreaCopy.removeFromShortlist : AreaCopy.addToShortlist) {
                saved.toggle(page.area, page: page)
            }
            .buttonStyle(.burroPrimary)
            if saved.couldNotSave {
                Text(ShortlistCopy.couldNotSave)
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.error)
            }
            // With no address for the website there is nothing to share.
            if let address = app.site.area(page.area) {
                ShareLink(item: address) {
                    Text(AreaCopy.share)
                }
                .buttonStyle(.burroSecondary)
                Text(AreaCopy.shareHint)
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
            }
        }
    }
}

/// Where the area stands in the search that is open, and why, in the API's sentences.
struct AreaInSearchSection: View {
    let inSearch: AreaInSearch

    var body: some View {
        AreaSection(title: AreaCopy.InSearch.title) {
            Text(inSearch.standing)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
            if inSearch.explained {
                if let orientation = inSearch.orientation {
                    AreaSaidView(said: orientation)
                }
                if !inSearch.reasons.isEmpty {
                    AreaPart(title: AreaCopy.InSearch.reasons) {
                        ForEach(inSearch.reasons) { AreaSaidView(said: $0) }
                    }
                }
                AreaPart(title: AreaCopy.InSearch.tradeOff) {
                    if let tradeOff = inSearch.tradeOff {
                        AreaSaidView(said: tradeOff)
                    } else {
                        Text(AreaCopy.InSearch.noTradeOff)
                            .font(Tokens.Text.body)
                            .foregroundStyle(Tokens.Colour.muted)
                    }
                }
            }
        }
    }
}

/// One sentence of the API's, with its source and its date under it.
struct AreaSaidView: View {
    let said: AreaInSearch.Said

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s1) {
            Text(said.text)
                .font(Tokens.Text.body)
                .foregroundStyle(Tokens.Colour.text)
            if said.byModel {
                Text(AreaCopy.InSearch.byModel)
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
            }
            if let words = said.sourceWords {
                AreaSourceWords(words: words)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .combine)
    }
}

/// Where the area sits on each vibe, in the lists the API puts them in. What
/// Burro cannot place the area on is said last, with why: for want of a
/// figure for this area, or because the data holds too little for any area.
struct AreaCharacterSection: View {
    let page: AreaPage

    var body: some View {
        AreaSection(title: AreaCopy.Portrait.title) {
            ForEach(AreaPage.VibeList.allCases.filter { $0 != .unplaced }, id: \.self) { list in
                let vibes = page.vibes(in: list)
                if !vibes.isEmpty {
                    AreaPart(title: AreaCopy.Portrait.title(of: list)) {
                        AreaVibeLines(vibes: vibes)
                    }
                }
            }
            let unplaced = page.vibes(in: .unplaced)
            if !unplaced.isEmpty {
                AreaPart(title: AreaCopy.Portrait.title(of: .unplaced)) {
                    let here = unplaced.filter { !$0.shown.notInData }
                    let everywhere = unplaced.filter { $0.shown.notInData }
                    if !here.isEmpty {
                        why(AreaCopy.Portrait.unplacedWhy)
                        AreaVibeLines(vibes: here)
                    }
                    if !everywhere.isEmpty {
                        why(AreaCopy.Portrait.notInData)
                        AreaVibeLines(vibes: everywhere)
                    }
                }
            }
        }
    }

    private func why(_ words: String) -> some View {
        Text(words)
            .font(Tokens.Text.secondary)
            .foregroundStyle(Tokens.Colour.muted)
            .fixedSize(horizontal: false, vertical: true)
    }
}

/// The vibes of one list, with a line between each and the next.
struct AreaVibeLines: View {
    let vibes: [AreaPage.Vibe]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ForEach(vibes) { vibe in
                Rectangle()
                    .fill(Tokens.Colour.border)
                    .frame(height: 1)
                    .accessibilityHidden(true)
                VibeLine(vibe.shown, source: SourceLines.words(for: vibe.fact.map { [$0] } ?? []))
                    .padding(.vertical, Tokens.Space.s3)
            }
        }
    }
}

/// The small picture of where the area is, and the areas next to it, which
/// say in words what the picture shows.
struct AreaWhereSection: View {
    @Environment(AppModel.self) private var app
    @State private var outlines: [LocatorOutline] = []
    let page: AreaPage

    var body: some View {
        AreaSection(title: AreaCopy.Where.title) {
            LocatorMapView(outlines: outlines, areaId: page.area.areaId, name: page.name)
            AreaPart(title: AreaCopy.Where.neighbours) {
                if page.neighbours.isEmpty {
                    Text(AreaCopy.Where.noNeighbours)
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.muted)
                } else {
                    ForEach(page.neighbours) { neighbour in
                        Button {
                            app.show(.area(neighbour))
                        } label: {
                            Text(neighbour.name)
                                .font(Tokens.Text.body)
                                .foregroundStyle(Tokens.Colour.accent)
                                .underline()
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        .buttonStyle(.plain)
                        .target()
                    }
                }
            }
        }
        // The outlines are of the release. They are asked for once, and worked out once.
        .task(id: outlinesInHand) {
            guard let search = app.search else { return }
            if search.state.geometry == nil { await search.flow.loadGeometry() }
            if let geometry = search.state.geometry {
                outlines = Locator.outlines(of: geometry)
            }
        }
    }

    /// How far the outlines have got: no search to ask, asked for, or in hand.
    private var outlinesInHand: Int {
        guard let search = app.search else { return 0 }
        return search.state.geometry == nil ? 1 : 2
    }
}

/// The sources the page names, and the way to how each figure is worked out.
struct AreaSourcesSection: View {
    @Environment(AppModel.self) private var app
    let page: AreaPage

    var body: some View {
        AreaSection(title: AreaCopy.Sources.title, lead: AreaCopy.Sources.lead) {
            ForEach(page.sources, id: \.sourceId) { source in
                AreaLinkRow(words: source.name) { app.show(.sources) }
            }
            AreaLinkRow(words: AreaCopy.Sources.methods) { app.show(.methods) }
            Text(verbatim: "\(AreaCopy.release) \(page.releaseId)")
                .font(Tokens.Text.code)
                .foregroundStyle(Tokens.Colour.muted)
        }
    }
}

/// A line that leads to another screen. It is as tall as a finger needs.
struct AreaLinkRow: View {
    let words: String
    let go: () -> Void

    var body: some View {
        Button(action: go) {
            Text(words)
                .font(Tokens.Text.body)
                .foregroundStyle(Tokens.Colour.accent)
                .underline()
                .multilineTextAlignment(.leading)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .buttonStyle(.plain)
        .target()
    }
}

// MARK: - Parts a section is made of

/// A part of the page, under its heading.
struct AreaSection<Content: View>: View {
    let title: String
    var lead: String?
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            Text(title)
                .font(Tokens.Text.title)
                .foregroundStyle(Tokens.Colour.text)
                .accessibilityAddTraits(.isHeader)
            if let lead {
                Text(lead)
                    .font(Tokens.Text.secondary)
                    .foregroundStyle(Tokens.Colour.muted)
            }
            content()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// A group inside a part: a dimension, or renting, or buying.
struct AreaPart<Content: View>: View {
    let title: String
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            Text(title)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
                .accessibilityAddTraits(.isHeader)
            content()
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// The rows of a part, with a line between each and the next. With no row,
/// the words that say there is none.
struct AreaFactRows: View {
    let rows: [FactRow]
    let none: String?

    var body: some View {
        if rows.isEmpty {
            if let none {
                Text(none)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.muted)
            }
        } else {
            VStack(alignment: .leading, spacing: 0) {
                ForEach(rows) { row in
                    Rectangle()
                        .fill(Tokens.Colour.border)
                        .frame(height: 1)
                        .accessibilityHidden(true)
                    AreaFactRowView(row: row)
                }
            }
        }
    }
}

/// One fact, laid out: its name, each column with its value, and its source
/// and date under it. It is read as one.
struct AreaFactRowView: View {
    let row: FactRow

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s1) {
            Text(row.name)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
            if let says = row.noFigure {
                Text(says)
                    .font(Tokens.Text.secondary)
                    .foregroundStyle(Tokens.Colour.muted)
            }
            ForEach(row.columns) { column in
                // Side by side where there is room, and one above the other where there is not.
                ViewThatFits(in: .horizontal) {
                    HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s3) {
                        name(of: column)
                        Spacer(minLength: Tokens.Space.s2)
                        value(of: column)
                    }
                    VStack(alignment: .leading, spacing: 0) {
                        name(of: column)
                        value(of: column)
                    }
                }
            }
            ForEach(row.caveats, id: \.self) { caveat in
                Text(caveat)
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.text)
            }
            if let words = row.sourceWords {
                AreaSourceWords(words: words)
            }
        }
        .padding(.vertical, Tokens.Space.s3)
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .combine)
    }

    private func name(of column: FactColumn) -> some View {
        Text(column.name)
            .font(Tokens.Text.secondary)
            .foregroundStyle(Tokens.Colour.muted)
    }

    private func value(of column: FactColumn) -> some View {
        Text(column.value)
            .font(Tokens.Text.figure)
            .foregroundStyle(Tokens.Colour.text)
    }
}

/// The source and the date of a figure, written out under it, so that it is
/// read without a press.
struct AreaSourceWords: View {
    let words: String

    var body: some View {
        Text(words)
            .font(Tokens.Text.footnote)
            .foregroundStyle(Tokens.Colour.muted)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}
