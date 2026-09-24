import SwiftUI

/// Every colour, size and space the app uses is named here and nowhere else.
///
/// The values are the website's, generated from `apps/web/src/styles/tokens.css`
/// into `TokenValues`. docs/design/web.md section 8 says what each is for and
/// what it must contrast with, and a test works the contrast out again.
///
/// Text has no fixed size. Each style below is one of the system's, so it
/// grows and shrinks with the size of text the person has chosen.
public enum Tokens {
    public enum Colour {
        /// The page.
        public static let bg = TokenValues.bg
        /// Cards and settings.
        public static let surface = TokenValues.surface
        public static let text = TokenValues.text
        /// Labels and dates.
        public static let muted = TokenValues.muted
        /// Links and the main button.
        public static let accent = TokenValues.accent
        /// Text on the main button.
        public static let onAccent = TokenValues.onAccent
        /// Edges of fields and buttons.
        public static let border = TokenValues.border
        public static let focus = TokenValues.focus
        /// The banner.
        public static let noticeText = TokenValues.noticeText
        public static let noticeBg = TokenValues.noticeBg
        public static let noticeEdge = TokenValues.noticeEdge
        /// The neutral notice.
        public static let infoText = TokenValues.infoText
        public static let infoBg = TokenValues.infoBg
        /// The trade-off mark, and "over". Never the only signal: the word is beside it.
        public static let tradeoff = TokenValues.tradeoff
        /// "within". Never the only signal: the word is beside it.
        public static let good = TokenValues.good
        public static let error = TokenValues.error

        public static let mapWater = TokenValues.mapWater
        /// An area with no score.
        public static let mapLand = TokenValues.mapLand
        /// Outlines, patterns and the pin's disc.
        public static let mapLine = TokenValues.mapLine
        /// Score bands, low to high. A band is never the only place a score is told.
        public static let mapBands = [
            TokenValues.map1, TokenValues.map2, TokenValues.map3, TokenValues.map4, TokenValues.map5,
        ]
    }

    /// Text styles. Each is a system style, so none has a fixed size.
    public enum Text {
        /// The name of the screen. One a screen.
        public static let largeTitle = Font.largeTitle.weight(.bold)
        /// The title of a sheet or a section.
        public static let title = Font.title2.weight(.bold)
        /// An area's name in a row.
        public static let headline = Font.headline
        public static let body = Font.body
        /// A borough, a hint. Drawn in `Colour.muted`.
        public static let secondary = Font.subheadline
        /// A source line, a date. Drawn in `Colour.muted`.
        public static let footnote = Font.footnote
        /// A release id, an engine version, a link.
        public static let code = Font.footnote.monospaced()
        /// A figure in a row or a table, so that columns of figures line up.
        public static let figure = Font.subheadline.monospacedDigit()
    }

    public enum Space {
        public static let s1 = CGFloat(TokenValues.space1)
        public static let s2 = CGFloat(TokenValues.space2)
        public static let s3 = CGFloat(TokenValues.space3)
        public static let s4 = CGFloat(TokenValues.space4)
        public static let s5 = CGFloat(TokenValues.space5)
        public static let s6 = CGFloat(TokenValues.space6)
        public static let s7 = CGFloat(TokenValues.space7)
        public static let s8 = CGFloat(TokenValues.space8)
        /// The space at each side of a screen.
        public static let gutter = s4
    }

    public enum Radius {
        /// A chip, a field.
        public static let small = CGFloat(TokenValues.radius)
        /// A card and a button.
        public static let card = CGFloat(TokenValues.radiusCard)
        /// The top corners of a sheet.
        public static let sheet = CGFloat(12)
    }

    public enum Target {
        /// The least height and width of anything that can be pressed.
        public static let least = CGFloat(TokenValues.target)
        /// The height of a full-width button.
        public static let button = CGFloat(50)
        /// The least height of a row in a list.
        public static let row = CGFloat(60)
    }

    public enum Motion {
        /// Seconds. Used only where the system says motion is welcome.
        public static let fast = TokenValues.durations["motion-fast"] ?? 0
        public static let slow = TokenValues.durations["motion-slow"] ?? 0

        /// The animation for a change, or none when the person has asked for less motion.
        public static func animation(_ seconds: Double, reduceMotion: Bool) -> Animation? {
            reduceMotion || seconds <= 0 ? nil : .easeInOut(duration: seconds)
        }
    }
}

extension View {
    /// Makes a control at least as large as a finger needs, whatever it draws.
    public func target() -> some View {
        frame(minWidth: Tokens.Target.least, minHeight: Tokens.Target.least)
            .contentShape(Rectangle())
    }
}
