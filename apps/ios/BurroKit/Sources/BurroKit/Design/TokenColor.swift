import SwiftUI

/// A colour of the design tokens: one value for light and one for dark.
///
/// It is a `ShapeStyle`, so it goes wherever a colour is drawn:
/// `.foregroundStyle(Tokens.Colour.text)`, `.background(Tokens.Colour.surface)`.
/// It follows the system's appearance. There is no switch in the app, because
/// a remembered choice would need storage.
public struct TokenColor: ShapeStyle, Hashable, Sendable {
    /// `0xRRGGBB`, as `tokens.css` writes it.
    public let light: UInt32
    public let dark: UInt32

    public init(light: UInt32, dark: UInt32) {
        self.light = light
        self.dark = dark
    }

    /// The colour for an appearance, for the few places that take a `Color` and no style.
    public func color(in scheme: ColorScheme) -> Color {
        let (red, green, blue) = parts(in: scheme)
        return Color(.sRGB, red: red, green: green, blue: blue, opacity: 1)
    }

    public func resolve(in environment: EnvironmentValues) -> Color {
        color(in: environment.colorScheme)
    }

    /// Red, green and blue, each from 0 to 1.
    public func parts(in scheme: ColorScheme) -> (red: Double, green: Double, blue: Double) {
        let value = scheme == .dark ? dark : light
        return (
            Double((value >> 16) & 0xff) / 255,
            Double((value >> 8) & 0xff) / 255,
            Double(value & 0xff) / 255
        )
    }

    /// How bright the colour is, by the WCAG formula.
    public func luminance(in scheme: ColorScheme) -> Double {
        func linear(_ part: Double) -> Double {
            part <= 0.03928 ? part / 12.92 : pow((part + 0.055) / 1.055, 2.4)
        }
        let (red, green, blue) = parts(in: scheme)
        return 0.2126 * linear(red) + 0.7152 * linear(green) + 0.0722 * linear(blue)
    }

    /// The contrast of this colour against another, by the WCAG formula: from 1 to 21.
    public func contrast(against other: TokenColor, in scheme: ColorScheme) -> Double {
        let one = luminance(in: scheme)
        let two = other.luminance(in: scheme)
        return (max(one, two) + 0.05) / (min(one, two) + 0.05)
    }
}
