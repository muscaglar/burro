import SwiftUI

/// A small picture of where one area is among the rest. It is a picture and
/// no more: it takes no press, and its label says what it shows. The area is
/// told from the rest by its heavy outline as well as its colour, and the
/// list of the areas next to it, beside it, says the same in words.
///
/// It is drawn from the outlines the API serves. No tile is fetched, so it
/// draws with no connection once the outlines are in hand, and nobody is told
/// which area is on screen.
struct LocatorMapView: View {
    let outlines: [LocatorOutline]
    let areaId: String
    /// The area's name, as the API gave it. It names the picture.
    let name: String

    var body: some View {
        let here = outlines.filter { $0.areaId == areaId }.flatMap(\.rings)
        if !here.isEmpty {
            let others = outlines.filter { $0.areaId != areaId }.flatMap(\.rings)
            let corners = RoundedRectangle(cornerRadius: Tokens.Radius.small)
            ZStack {
                Rectangle().fill(Tokens.Colour.mapWater)
                LocatorOutlines(rings: others).fill(Tokens.Colour.mapLand)
                LocatorOutlines(rings: others).stroke(Tokens.Colour.mapLine, lineWidth: Self.thin)
                LocatorOutlines(rings: here).fill(Tokens.Colour.mapBands.last ?? Tokens.Colour.mapLand)
                LocatorOutlines(rings: here)
                    .stroke(Tokens.Colour.mapLine, style: StrokeStyle(lineWidth: Self.heavy, lineJoin: .round))
            }
            .aspectRatio(Locator.frame.width / Locator.frame.height, contentMode: .fit)
            .frame(maxWidth: Self.widest)
            .clipShape(corners)
            .overlay(corners.strokeBorder(Tokens.Colour.border, lineWidth: 1))
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(Text(AreaCopy.Where.picture(of: name)))
            .accessibilityAddTraits(.isImage)
        }
    }

    /// The widest the picture is drawn: twice the size it is worked out at.
    private static let widest = CGFloat(Locator.frame.width * 2)
    private static let thin = CGFloat(0.5)
    private static let heavy = CGFloat(2.5)
}

/// The outlines of some areas, scaled to the room they are given.
struct LocatorOutlines: Shape {
    let rings: [[LocatorPoint]]

    func path(in rect: CGRect) -> Path {
        let scale = min(rect.width / Locator.frame.width, rect.height / Locator.frame.height)
        let left = rect.minX + (rect.width - Locator.frame.width * scale) / 2
        let top = rect.minY + (rect.height - Locator.frame.height * scale) / 2
        func place(_ point: LocatorPoint) -> CGPoint {
            CGPoint(x: left + point.x * scale, y: top + point.y * scale)
        }
        var path = Path()
        for ring in rings where ring.count > 2 {
            path.move(to: place(ring[0]))
            for point in ring.dropFirst() { path.addLine(to: place(point)) }
            path.closeSubpath()
        }
        return path
    }
}
