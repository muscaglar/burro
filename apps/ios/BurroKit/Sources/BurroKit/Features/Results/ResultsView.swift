import SwiftUI

/// The ranking of the search that is open: the map, and over it the list
/// that says everything the map shows.
///
/// It is drawn inside `Opened`, so the search is in the environment. It goes
/// to an area with `app.show(.area(AreaRef(area)))`.
///
/// Everything it draws is worked out in `Model/`, as plain values, and drawn
/// by the views in `Views/`. It writes no word about a place, builds no spec,
/// and keeps nothing: what it holds while the app is open is in `Results.Memory`.
public struct ResultsView: View {
    @Environment(AppModel.self) private var app
    @Environment(SearchStore.self) private var search

    public init() {}

    public var body: some View {
        let memory = app.results
        Results.Whole(hands: Results.Hands(app: app, search: search, memory: memory), memory: memory)
    }
}

/// Two to four areas side by side, for the search that is open. It is pushed
/// over the results, so the way back is to them.
///
/// It is drawn inside `Opened`, so the search is in the environment. The
/// areas are those chosen on the results, which the app holds in memory.
public struct ResultsCompareView: View {
    @Environment(AppModel.self) private var app
    @Environment(SearchStore.self) private var search

    public init() {}

    public var body: some View {
        Results.CompareView(
            chosen: app.results.compared(among: search.state.areas),
            hands: Results.Hands(app: app, search: search, memory: app.results)
        )
        .navigationTitle(ResultsCopy.Compare.title)
        #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
        #endif
    }
}

extension Results {
    /// The whole screen: how the results are shown, and the one way that is showing.
    struct Whole: View {
        let hands: Hands
        @Bindable var memory: Memory
        @State var ground = Ground.none
        @Environment(\.dynamicTypeSize) var size

        var body: some View {
            let state = hands.search.state
            let listed = Results.listed(state)
            VStack(spacing: 0) {
                picker
                switch memory.showing {
                case .map:
                    mapAndList(state, listed)
                case .list:
                    ListView(listed: listed, chosen: nil, ground: ground, hands: hands, memory: memory)
                case .table:
                    TableView(tabled: tabled(state), hands: hands)
                }
            }
            .background(Tokens.Colour.bg)
            .navigationTitle(ResultsCopy.title)
            #if os(iOS)
                .navigationBarTitleDisplayMode(.inline)
            #endif
            .task { await hands.search.flow.loadGeometry() }
            .onChange(of: state.geometry, initial: true) { _, geometry in
                ground = Ground(geometry)
            }
            .onChange(of: listed.announcement) { _, said in
                guard let said else { return }
                AccessibilityNotification.Announcement(said).post()
            }
        }

        /// The toggle between the map, the list on the whole screen, and the table of every area.
        @ViewBuilder
        private var picker: some View {
            let choice = Picker(ResultsCopy.Views.label, selection: $memory.showing) {
                ForEach(Showing.allCases) { showing in
                    Text(showing.words).tag(showing)
                }
            }
            Group {
                if size.isAccessibilitySize {
                    // Three words side by side do not fit at the largest sizes, so they are a menu.
                    HStack {
                        Text(ResultsCopy.Views.label)
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.text)
                        Spacer(minLength: Tokens.Space.s2)
                        choice.pickerStyle(.menu)
                    }
                } else {
                    choice.pickerStyle(.segmented)
                }
            }
            .frame(minHeight: Tokens.Target.least)
            .padding(.horizontal, Tokens.Space.gutter)
            .padding(.vertical, Tokens.Space.s1)
        }

        /// The map, with the list over it at one of three heights.
        @ViewBuilder
        private func mapAndList(_ state: SearchState, _ listed: Listed) -> some View {
            if ground.isEmpty {
                // With no boundaries there is no map, and the table says everything it would.
                VStack(alignment: .leading, spacing: 0) {
                    Text(state.geometryFailed ? ResultsCopy.Map.noGeometryHere : ResultsCopy.Map.loading)
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.text)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(Tokens.Space.gutter)
                    if state.geometryFailed {
                        TableView(tabled: tabled(state), hands: hands)
                    } else {
                        ListView(listed: listed, chosen: nil, ground: ground, hands: hands, memory: memory)
                    }
                }
            } else {
                GeometryReader { room in
                    let tall = room.size.height
                    let mapped = Results.mapped(state, on: ground)
                    ZStack(alignment: .bottom) {
                        MapView(
                            mapped: mapped, ground: ground,
                            covered: covered(in: tall), hands: hands, memory: memory)
                        SheetView(height: $memory.height, room: tall) {
                            ListView(
                                listed: listed, chosen: mapped.chosen, ground: ground, hands: hands,
                                memory: memory)
                        }
                    }
                }
            }
        }

        /// How much of the map the list covers, for the map to frame the city in what is left.
        /// At its tallest the list covers nearly all of it, and the map is framed as for half.
        private func covered(in room: CGFloat) -> CGFloat {
            let height = min(memory.height, .half)
            return CGFloat(height.points(in: Double(room), least: Double(SheetView<EmptyView>.least)))
        }
    }
}
