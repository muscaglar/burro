import SwiftUI
import XCTest

@testable import BurroKit

/// The design tokens are the website's, and each pair that must contrast does.
final class TokensTests: XCTestCase {
    /// Every `--name: value;` of a block of `tokens.css`.
    private func values(in block: String) -> [String: String] {
        var found: [String: String] = [:]
        for line in block.split(separator: "\n") {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            guard trimmed.hasPrefix("--"), let colon = trimmed.firstIndex(of: ":"),
                let end = trimmed.lastIndex(of: ";")
            else { continue }
            let name = String(trimmed[trimmed.index(trimmed.startIndex, offsetBy: 2)..<colon])
            found[name] = trimmed[trimmed.index(after: colon)..<end].trimmingCharacters(in: .whitespaces)
        }
        return found
    }

    /// The light block and the dark block of `tokens.css`.
    private func website() throws -> (light: [String: String], dark: [String: String]) {
        let css = try Repository.text(Repository.tokens)
        let parts = css.components(separatedBy: "@media (prefers-color-scheme: dark)")
        XCTAssertEqual(parts.count, 2)
        let dark = parts[1].components(separatedBy: "@media").first ?? ""
        return (values(in: parts[0]), values(in: dark))
    }

    private func hex(_ value: String?) -> UInt32? {
        guard let value, value.hasPrefix("#"), value.count == 7 else { return nil }
        return UInt32(value.dropFirst(), radix: 16)
    }

    func test_every_colour_is_the_websites_in_light_and_in_dark() throws {
        let (light, dark) = try website()
        let colours = light.filter { hex($0.value) != nil }.keys.sorted()

        XCTAssertEqual(colours.count, 24)
        XCTAssertEqual(TokenValues.colours.keys.sorted(), colours)
        for name in colours {
            XCTAssertEqual(TokenValues.colours[name]?.light, hex(light[name]), name)
            XCTAssertEqual(TokenValues.colours[name]?.dark, hex(dark[name]), name)
        }
        XCTAssertEqual(Tokens.Colour.accent, TokenColor(light: 0x0a5a8c, dark: 0x8ecbf3))
        XCTAssertEqual(Tokens.Colour.mapBands.count, 5)
    }

    func test_every_space_and_target_is_the_websites() throws {
        let (light, _) = try website()
        let lengths = light.filter { $0.value.hasSuffix("px") }

        XCTAssertEqual(TokenValues.lengths.count, lengths.count)
        for (name, value) in lengths {
            XCTAssertEqual(TokenValues.lengths[name], Double(value.dropLast(2)), name)
        }
        XCTAssertEqual(
            [Tokens.Space.s1, Tokens.Space.s2, Tokens.Space.s3, Tokens.Space.s4, Tokens.Space.s5,
                Tokens.Space.s6, Tokens.Space.s7, Tokens.Space.s8],
            [4, 8, 12, 16, 24, 32, 48, 64])
        XCTAssertEqual(Tokens.Radius.card, 8)
    }

    func test_anything_that_can_be_pressed_is_at_least_forty_four_points() {
        XCTAssertGreaterThanOrEqual(Tokens.Target.least, 44)
        XCTAssertGreaterThanOrEqual(Tokens.Target.button, Tokens.Target.least)
        XCTAssertGreaterThanOrEqual(Tokens.Target.row, Tokens.Target.least)
    }

    func test_nothing_moves_when_the_person_has_asked_for_less_motion() {
        XCTAssertEqual(Tokens.Motion.fast, 0.12)
        XCTAssertEqual(Tokens.Motion.slow, 0.2)
        XCTAssertNil(Tokens.Motion.animation(Tokens.Motion.fast, reduceMotion: true))
        XCTAssertNil(Tokens.Motion.animation(0, reduceMotion: false))
        XCTAssertNotNil(Tokens.Motion.animation(Tokens.Motion.slow, reduceMotion: false))
    }

    func test_no_text_has_a_fixed_size() throws {
        let tokens = try Repository.text(Repository.sources.appendingPathComponent("Design/Tokens.swift"))
        let fixed = try Repository.files(under: Repository.sources, ending: ".swift").filter { name in
            let text = try Repository.text(Repository.sources.appendingPathComponent(name))
            return text.contains(".system(size:") || text.contains("Font.custom(") || text.contains(".font(.system(")
        }

        XCTAssertEqual(fixed, [])
        XCTAssertTrue(tokens.contains("Font.largeTitle"))
        XCTAssertTrue(tokens.contains("Font.footnote"))
    }

    func test_nothing_is_dimmed_but_a_button_while_it_is_pressed() throws {
        // A dimmed colour is not the colour whose contrast was checked. A state is said in
        // words, and a control that is switched off is drawn in colours of its own.
        var dimmed: [String] = []
        for name in Repository.files(under: Repository.sources, ending: ".swift") {
            let text = try Repository.text(Repository.sources.appendingPathComponent(name))
            for line in text.components(separatedBy: "\n") {
                let code = line.components(separatedBy: "//").first ?? line
                let seeThrough = [".opacity(", ".blur(", ".saturation(", ".grayscale(", ".colorMultiply("]
                guard seeThrough.contains(where: code.contains) else { continue }
                if code.trimmingCharacters(in: .whitespaces) != ".opacity(configuration.isPressed ? 0.8 : 1)" {
                    dimmed.append("\(name): \(code.trimmingCharacters(in: .whitespaces))")
                }
            }
        }

        XCTAssertEqual(dimmed, [])
    }

    func test_every_text_that_holds_what_the_api_said_is_drawn_as_it_came() throws {
        // A text made of a piece of writing in the source is looked up as a key and read as
        // markup. What the API said, and an id to quote, is drawn letter for letter.
        let keyed = try Repository.files(under: Repository.sources, ending: ".swift").filter { name in
            try Repository.text(Repository.sources.appendingPathComponent(name)).contains("Text(\"\\(")
        }

        XCTAssertEqual(keyed, [])
    }

    func test_a_colour_is_worked_out_for_the_appearance_the_system_asks_for() {
        let colour = TokenColor(light: 0xff8000, dark: 0x0080ff)

        let light = colour.parts(in: .light)
        let dark = colour.parts(in: .dark)

        XCTAssertEqual(light.red, 1)
        XCTAssertEqual(light.green, 128.0 / 255, accuracy: 0.0001)
        XCTAssertEqual(light.blue, 0)
        XCTAssertEqual(dark.red, 0)
        XCTAssertEqual(dark.blue, 1)
    }

    func test_the_contrast_formula_is_the_one_wcag_gives() {
        let black = TokenColor(light: 0x000000, dark: 0x000000)
        let white = TokenColor(light: 0xffffff, dark: 0xffffff)
        let grey = TokenColor(light: 0x767676, dark: 0x767676)

        XCTAssertEqual(black.contrast(against: white, in: .light), 21, accuracy: 0.001)
        XCTAssertEqual(white.contrast(against: white, in: .light), 1, accuracy: 0.001)
        XCTAssertEqual(grey.contrast(against: white, in: .light), 4.54, accuracy: 0.01)
    }

    func test_every_pair_that_must_contrast_does_in_light_and_in_dark() {
        // docs/design/web.md section 8: what each is used against, and what it needs.
        let c = Tokens.Colour.self
        let pairs: [(String, TokenColor, [TokenColor], Double)] = [
            ("text", c.text, [c.bg, c.surface], 4.5),
            ("muted", c.muted, [c.bg, c.surface], 4.5),
            ("accent", c.accent, [c.bg, c.surface], 4.5),
            ("on-accent", c.onAccent, [c.accent], 4.5),
            ("border", c.border, [c.bg, c.surface], 3),
            ("focus", c.focus, [c.bg], 3),
            ("notice-text", c.noticeText, [c.noticeBg], 4.5),
            ("notice-edge", c.noticeEdge, [c.noticeBg], 3),
            ("info-text", c.infoText, [c.infoBg], 4.5),
            ("tradeoff", c.tradeoff, [c.bg, c.surface], 4.5),
            ("good", c.good, [c.bg, c.surface], 4.5),
            ("error", c.error, [c.bg, c.surface], 4.5),
            ("map-line", c.mapLine, [c.bg, c.mapWater, c.mapLand] + c.mapBands, 3),
        ]

        var short: [String] = []
        for (name, colour, against, needs) in pairs {
            for other in against {
                for scheme in [ColorScheme.light, .dark] where colour.contrast(against: other, in: scheme) < needs {
                    short.append("\(name) in \(scheme)")
                }
            }
        }

        XCTAssertEqual(short, [])
        XCTAssertEqual(c.text.contrast(against: c.bg, in: .light), 16.5, accuracy: 0.1)
    }
}
