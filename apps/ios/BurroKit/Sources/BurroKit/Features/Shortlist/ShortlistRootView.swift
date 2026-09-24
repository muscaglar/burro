import SwiftUI

/// The first screen of the Shortlist tab: the areas a person saved. It is
/// kept on the phone and read with no connection.
///
/// It lists them in the person's order. Each can be opened, moved up or down,
/// and removed, and the whole list can be cleared.
public struct ShortlistRootView: View {
    @Environment(AppModel.self) private var app
    @State private var asking = false

    public init() {}

    public var body: some View {
        let saved = app.saved
        let entries = saved.entries
        List {
            Section {
                Text(ShortlistCopy.kept)
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
                    .listRowSeparator(.hidden)
                if saved.couldNotSave {
                    Text(ShortlistCopy.couldNotSave)
                        .font(Tokens.Text.footnote)
                        .foregroundStyle(Tokens.Colour.error)
                        .listRowSeparator(.hidden)
                }
                if entries.isEmpty {
                    Text(ShortlistCopy.empty)
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.text)
                        .listRowSeparator(.hidden)
                }
            }
            .listRowBackground(Rectangle().fill(Tokens.Colour.bg))
            if !entries.isEmpty {
                Section {
                    ForEach(entries) { entry in
                        ShortlistRow(
                            shown: ShortlistShown(
                                entry, older: saved.isOlder(entry, than: app.search?.state.meta.releaseId)),
                            canMoveUp: saved.canMove(entry.id, by: -1),
                            canMoveDown: saved.canMove(entry.id, by: 1),
                            open: { app.show(.area(entry.area), in: .shortlist) },
                            move: { saved.move(entry.id, by: $0) },
                            remove: { saved.remove(entry.id) })
                    }
                    .onMove { saved.move(fromOffsets: $0, toOffset: $1) }
                    .onDelete { offsets in
                        for id in offsets.compactMap({ entries.indices.contains($0) ? entries[$0].id : nil }) {
                            saved.remove(id)
                        }
                    }
                }
                .listRowBackground(Rectangle().fill(Tokens.Colour.bg))
                Section {
                    Button(ShortlistCopy.clear, role: .destructive) {
                        asking = true
                    }
                    .target()
                }
                .listRowBackground(Rectangle().fill(Tokens.Colour.bg))
            }
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
        .background(Tokens.Colour.bg)
        .navigationTitle(ShellCopy.title(of: .shortlist))
        .toolbar {
            #if os(iOS)
            if !entries.isEmpty {
                // The system's own way to move and remove rows, for a person who would sooner not swipe.
                ToolbarItem(placement: .primaryAction) { EditButton() }
            }
            #endif
        }
        .confirmationDialog(ShortlistCopy.clearTitle, isPresented: $asking, titleVisibility: .visible) {
            Button(ShortlistCopy.clearConfirm, role: .destructive) {
                saved.clear()
            }
            Button(ShortlistCopy.cancel, role: .cancel) {}
        }
    }
}

/// What a row of the shortlist says: the names and the date that were saved,
/// and what is to be known of the figures.
public struct ShortlistShown: Hashable, Sendable, Identifiable {
    public let id: String
    public let name: String
    public let borough: String
    public let savedOn: Date
    /// True when the figures are of another release than the one being read now.
    public let older: Bool
    /// True when the phone holds no figures for the area.
    public let noFigures: Bool

    public init(_ entry: SavedAreas.Entry, older: Bool) {
        id = entry.id
        name = entry.saved.name
        borough = entry.saved.borough
        savedOn = entry.saved.savedOn
        self.older = older
        noFigures = entry.kept == nil
    }

    /// Every line of the row under the name, in the order it is read.
    public func lines(in zone: TimeZone = .current) -> [String] {
        var lines = [borough, ShortlistCopy.saved(on: ShortlistCopy.date(savedOn, in: zone))]
        if older { lines.append(ShortlistCopy.older) }
        if noFigures { lines.append(ShortlistCopy.noFigures) }
        return lines
    }
}

/// One saved area. The whole row opens the area. It can be moved and removed
/// without a swipe or a drag, by the actions a screen reader offers.
struct ShortlistRow: View {
    let shown: ShortlistShown
    let canMoveUp: Bool
    let canMoveDown: Bool
    let open: () -> Void
    let move: (Int) -> Void
    let remove: () -> Void

    var body: some View {
        Button(action: open) {
            VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                Text(shown.name)
                    .font(Tokens.Text.headline)
                    .foregroundStyle(Tokens.Colour.text)
                ForEach(shown.lines(), id: \.self) { line in
                    Text(line)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.muted)
                }
            }
            .multilineTextAlignment(.leading)
            .frame(maxWidth: .infinity, minHeight: Tokens.Target.row, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityElement(children: .combine)
        .accessibilityHint(Text(ShortlistCopy.open(shown.name)))
        .accessibilityActions {
            if canMoveUp {
                Button(ShortlistCopy.moveUp) { move(-1) }
            }
            if canMoveDown {
                Button(ShortlistCopy.moveDown) { move(1) }
            }
            Button(ShortlistCopy.remove(shown.name), action: remove)
        }
        .contextMenu {
            if canMoveUp {
                Button(ShortlistCopy.moveUp) { move(-1) }
            }
            if canMoveDown {
                Button(ShortlistCopy.moveDown) { move(1) }
            }
            Button(ShortlistCopy.remove(shown.name), role: .destructive, action: remove)
        }
    }
}
