import MapKit
import SwiftUI

// The map. Each area is drawn from the boundaries the API serves, filled by
// the band its fit falls in. A band is a colour, so every ranked area also
// carries its fit in figures, the first ten carry their rank in a pin, an
// area a limit left out is crossed with lines, and one that is not ranked is
// marked with dots. The legend says each of these in words.
//
// The camera is framed on the areas and held to them. The made-up city
// stands in open sea, so nothing under the areas says anything: no label of
// the basemap is relied on, and its points of interest are switched off.
//
// The map asks the phone for nothing. It shows no position of the person.

extension Results {
    struct MapView: View {
        let mapped: Mapped
        let ground: Ground
        /// How much of the foot of the map the list covers, in points.
        let covered: CGFloat
        let hands: Hands
        @Bindable var memory: Memory

        @State var position: MapCameraPosition = .automatic
        /// What the camera shows now. `nil` until it has settled once.
        @State var seen: Frame?
        @Environment(\.colorScheme) var scheme
        @Environment(\.accessibilityReduceMotion) var reduceMotion

        var body: some View {
            MapReader { proxy in
                Map(position: $position, bounds: limits, interactionModes: [.pan, .zoom]) {
                    ForEach(mapped.regions) { region in
                        MapPolygon(polygon(of: region.outline))
                            .foregroundStyle(colour(of: region.fill))
                            .stroke(line, lineWidth: region.selected ? 3 : 1)
                    }
                    ForEach(numbered(mapped.strokes)) { stroke in
                        MapPolyline(coordinates: [coordinate(stroke.value.from), coordinate(stroke.value.to)])
                            .stroke(line, lineWidth: 1)
                    }
                    ForEach(numbered(mapped.dots)) { dot in
                        MapCircle(center: coordinate(dot.value), radius: mapped.dotRadius)
                            .foregroundStyle(line)
                    }
                    ForEach(mapped.marks) { mark in
                        Annotation(mark.area.name, coordinate: coordinate(mark.at), anchor: .center) {
                            MarkView(mark: mark) { hands.choose(onMap: mark.area.areaId) }
                        }
                    }
                }
                .mapStyle(
                    .standard(
                        elevation: .flat, emphasis: .muted, pointsOfInterest: .excludingAll, showsTraffic: false)
                )
                .onMapCameraChange(frequency: .onEnd) { context in
                    seen = framed(context.region)
                }
                .onTapGesture(coordinateSpace: .local) { point in
                    guard let at = proxy.convert(point, from: .local) else { return }
                    let position = LonLat(longitude: at.longitude, latitude: at.latitude)
                    hands.choose(onMap: area(at: position, in: ground.outlines))
                }
                .safeAreaPadding(.bottom, covered)
            }
            .overlay(alignment: .topTrailing) {
                controls
                    .padding(Tokens.Space.s2)
            }
            .overlay(alignment: .topLeading) {
                LegendView(entries: mapped.legend, open: $memory.legendOpen)
                    .padding(Tokens.Space.s2)
                    .padding(.trailing, Tokens.Target.least + Tokens.Space.s4)
            }
            .accessibilityElement(children: .contain)
            .accessibilityLabel(ResultsCopy.Map.label)
            .onAppear { show(ground.whole, moving: false) }
            .onChange(of: ground.whole) { _, whole in show(whole, moving: false) }
            .onChange(of: mapped.chosen?.area.areaId) { _, areaId in bringIntoView(areaId) }
        }

        // MARK: - The camera

        /// The camera is held to the city: it cannot be carried off over open sea.
        private var limits: MapCameraBounds? {
            guard let whole = ground.whole else { return nil }
            let metres = max(whole.latitudeSpan, whole.longitudeSpan) * metresInADegree
            return MapCameraBounds(
                centerCoordinateBounds: region(of: whole), minimumDistance: metres / 40,
                maximumDistance: metres * 8)
        }

        private func show(_ frame: Frame?, moving: Bool = true) {
            guard let frame else { return }
            let animation = moving ? Tokens.Motion.animation(Tokens.Motion.slow, reduceMotion: reduceMotion) : nil
            withAnimation(animation) {
                position = .region(region(of: frame))
            }
        }

        /// Nothing pans unless the chosen area is out of sight.
        private func bringIntoView(_ areaId: String?) {
            guard let areaId, let seen, let centre = hands.search.state.area(areaId)?.centroid,
                !shows(seen, centre)
            else { return }
            show(Results.frame(ofArea: areaId, in: ground.outlines))
        }

        private func zoom(by factor: Double) {
            guard let whole = ground.whole else { return }
            show(zoomed(seen ?? whole, by: factor, within: whole))
        }

        private var controls: some View {
            VStack(spacing: Tokens.Space.s2) {
                control(ResultsCopy.Map.zoomIn, image: "plus") { zoom(by: 0.5) }
                control(ResultsCopy.Map.zoomOut, image: "minus") { zoom(by: 2) }
                control(ResultsCopy.Map.whole, image: "arrow.up.left.and.arrow.down.right") {
                    show(ground.whole)
                }
            }
            .accessibilityElement(children: .contain)
            .accessibilityLabel(ResultsCopy.Map.controls)
        }

        private func control(_ words: String, image: String, press: @escaping () -> Void) -> some View {
            Button(action: press) {
                Image(systemName: image)
                    .font(Tokens.Text.headline)
                    .foregroundStyle(Tokens.Colour.text)
                    .frame(width: Tokens.Target.least, height: Tokens.Target.least)
                    .background(Tokens.Colour.bg, in: RoundedRectangle(cornerRadius: Tokens.Radius.card))
                    .overlay(
                        RoundedRectangle(cornerRadius: Tokens.Radius.card)
                            .strokeBorder(Tokens.Colour.border, lineWidth: 1)
                    )
            }
            .buttonStyle(.plain)
            .accessibilityLabel(words)
        }

        // MARK: - From positions to the map's own

        private var line: Color { Tokens.Colour.mapLine.color(in: scheme) }

        private func colour(of fill: Fill) -> Color {
            let bands = Tokens.Colour.mapBands
            guard fill.band >= 1, fill.band <= bands.count else {
                return Tokens.Colour.mapLand.color(in: scheme)
            }
            return bands[fill.band - 1].color(in: scheme)
        }

        private func coordinate(_ position: LonLat) -> CLLocationCoordinate2D {
            CLLocationCoordinate2D(latitude: position.latitude, longitude: position.longitude)
        }

        private func polygon(of outline: Outline) -> MKPolygon {
            let outer = outline.outer.map(coordinate)
            let holes = outline.holes.map { ring -> MKPolygon in
                let corners = ring.map(coordinate)
                return MKPolygon(coordinates: corners, count: corners.count)
            }
            return MKPolygon(coordinates: outer, count: outer.count, interiorPolygons: holes)
        }

        private func region(of frame: Frame) -> MKCoordinateRegion {
            MKCoordinateRegion(
                center: coordinate(frame.centre),
                span: MKCoordinateSpan(latitudeDelta: frame.latitudeSpan, longitudeDelta: frame.longitudeSpan))
        }

        private func framed(_ region: MKCoordinateRegion) -> Frame {
            Frame(
                centre: LonLat(longitude: region.center.longitude, latitude: region.center.latitude),
                longitudeSpan: region.span.longitudeDelta, latitudeSpan: region.span.latitudeDelta)
        }

        private struct Numbered<Value>: Identifiable {
            let id: Int
            let value: Value
        }

        private func numbered<Value>(_ values: [Value]) -> [Numbered<Value>] {
            values.enumerated().map { Numbered(id: $0.offset, value: $0.element) }
        }
    }

    /// What stands on a ranked area: the rank in a disc, for one of the first
    /// ten, and the fit in figures. It is a button, and it is as large as a finger needs.
    struct MarkView: View {
        let mark: Mark
        let press: () -> Void

        var body: some View {
            Button(action: press) {
                VStack(spacing: 0) {
                    if let pin = mark.pin {
                        RankDisc(rank: pin, large: mark.selected)
                    }
                    if let fit = mark.fit {
                        Text(fit)
                            .font(Tokens.Text.footnote.monospacedDigit().weight(mark.selected ? .bold : .regular))
                            .foregroundStyle(Tokens.Colour.text)
                            .padding(.horizontal, Tokens.Space.s1)
                            .background(Tokens.Colour.bg, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
                            .overlay(
                                RoundedRectangle(cornerRadius: Tokens.Radius.small)
                                    .strokeBorder(Tokens.Colour.mapLine, lineWidth: mark.selected ? 2 : 0.5)
                            )
                    }
                }
                .target()
            }
            .buttonStyle(.plain)
            .accessibilityLabel(mark.words)
            .accessibilityAddTraits(mark.selected ? .isSelected : [])
        }
    }

    /// What the colours, the patterns and the marks of the map stand for, in
    /// figures and in words. Closed at first, so that it does not cover the map.
    struct LegendView: View {
        let entries: [LegendEntry]
        @Binding var open: Bool

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                Button {
                    open.toggle()
                } label: {
                    HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                        Image(systemName: open ? "chevron.down" : "chevron.right")
                            .accessibilityHidden(true)
                        Text(ResultsCopy.Legend.title)
                            .multilineTextAlignment(.leading)
                    }
                    .font(Tokens.Text.secondary.weight(.semibold))
                    .foregroundStyle(Tokens.Colour.text)
                    .frame(minHeight: Tokens.Target.least)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityValue(open ? ResultsCopy.Legend.open : ResultsCopy.Legend.closed)
                if open {
                    ScrollView {
                        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                            ForEach(entries) { entry in
                                HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                                    Swatch(sign: entry.sign)
                                    Text(entry.words)
                                        .font(Tokens.Text.footnote)
                                        .foregroundStyle(Tokens.Colour.text)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                }
                                .accessibilityElement(children: .combine)
                            }
                        }
                    }
                    .frame(maxHeight: Tokens.Space.s8 * 4)
                }
            }
            .padding(.horizontal, Tokens.Space.s3)
            .padding(.vertical, Tokens.Space.s1)
            .background(Tokens.Colour.bg, in: RoundedRectangle(cornerRadius: Tokens.Radius.card))
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(Tokens.Colour.border, lineWidth: 1)
            )
            .accessibilityElement(children: .contain)
            .accessibilityLabel(ResultsCopy.Legend.title)
        }
    }

    /// The sign that goes with a line of the legend. The words beside it say what it is.
    struct Swatch: View {
        let sign: LegendEntry.Sign

        var body: some View {
            Canvas { context, size in
                let box = CGRect(origin: .zero, size: size)
                let edge = Path(roundedRect: box.insetBy(dx: 0.5, dy: 0.5), cornerRadius: 2)
                switch sign {
                case .band(let band):
                    let bands = Tokens.Colour.mapBands
                    let at = min(max(band, 1), bands.count) - 1
                    context.fill(edge, with: .style(bands[at]))
                case .land:
                    context.fill(edge, with: .style(Tokens.Colour.mapLand))
                case .lines:
                    context.fill(edge, with: .style(Tokens.Colour.mapLand))
                    var lines = Path()
                    var start = -size.height
                    while start < size.width {
                        lines.move(to: CGPoint(x: start, y: size.height))
                        lines.addLine(to: CGPoint(x: start + size.height, y: 0))
                        start += 5
                    }
                    context.clip(to: edge)
                    context.stroke(lines, with: .style(Tokens.Colour.mapLine), lineWidth: 1)
                case .dots:
                    context.fill(edge, with: .style(Tokens.Colour.mapLand))
                    var dots = Path()
                    var row = 0
                    var down: CGFloat = 3
                    while down < size.height {
                        var across: CGFloat = row % 2 == 0 ? 3 : 6
                        while across < size.width {
                            dots.addEllipse(in: CGRect(x: across - 1, y: down - 1, width: 2, height: 2))
                            across += 6
                        }
                        down += 5
                        row += 1
                    }
                    context.fill(dots, with: .style(Tokens.Colour.mapLine))
                case .pin:
                    context.fill(Path(ellipseIn: box), with: .style(Tokens.Colour.mapLine))
                case .fit:
                    context.fill(edge, with: .style(Tokens.Colour.bg))
                }
                if sign != .pin {
                    context.stroke(edge, with: .style(Tokens.Colour.mapLine), lineWidth: 1)
                }
            }
            .frame(width: Tokens.Space.s5, height: Tokens.Space.s4)
            .accessibilityHidden(true)
        }
    }

    /// What the map says of the area chosen on it, in words: its name, its
    /// borough, its rank and its fit, or the reason it has no rank.
    struct ChosenView: View {
        let chosen: Chosen
        let hands: Hands

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                Text(chosen.area.name)
                    .font(Tokens.Text.headline)
                    .foregroundStyle(Tokens.Colour.text)
                    .accessibilityAddTraits(.isHeader)
                Text(chosen.area.borough)
                    .font(Tokens.Text.secondary)
                    .foregroundStyle(Tokens.Colour.muted)
                if let words = chosen.words {
                    Text(words)
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.text)
                }
                if chosen.beyondList {
                    Text(ResultsCopy.MapCard.notInList)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.muted)
                }
                if chosen.inList {
                    Button(ResultsCopy.MapCard.showInList) { hands.showInList(chosen.area) }
                        .buttonStyle(.burroSecondary)
                }
                Button(ResultsCopy.Card.open) { hands.open(chosen.area) }
                    .buttonStyle(.burroSecondary)
                    .accessibilityLabel(ResultsCopy.Card.openArea(chosen.area.name))
                Button(ResultsCopy.MapCard.close) { hands.close() }
                    .buttonStyle(.burroSecondary)
            }
            .padding(Tokens.Space.s3)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Tokens.Colour.surface, in: RoundedRectangle(cornerRadius: Tokens.Radius.card))
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(Tokens.Colour.mapLine, lineWidth: 2)
            )
            .accessibilityElement(children: .contain)
            .accessibilityLabel(ResultsCopy.MapCard.label)
        }
    }
}
