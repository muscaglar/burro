import SwiftUI
import XCTest

@testable import BurroKit

/// The rules the results screen keeps, read off its source, and the panel
/// that holds the list over the map.
///
/// A view cannot be drawn where these tests run, so what a view must not do
/// is looked for in its text.
final class ResultsRulesTests: XCTestCase {
    private let folder = Repository.sources.appendingPathComponent("Features/Results")

    /// Every file of the feature, by its path from the feature's folder, with its text.
    private func files() throws -> [(name: String, text: String)] {
        try Repository.files(under: folder, ending: ".swift").map {
            ($0, try Repository.text(folder.appendingPathComponent($0)))
        }
    }

    private func views() throws -> [(name: String, text: String)] {
        try files().filter { $0.name.hasPrefix("Views/") || $0.name == "ResultsView.swift" }
    }

    /// The text of a file with its comments taken out, so that a rule is held to the code.
    private func code(_ text: String) -> String {
        text.split(separator: "\n", omittingEmptySubsequences: false)
            .map { line -> Substring in
                guard let at = line.range(of: "//") else { return line }
                return line[..<at.lowerBound]
            }
            .joined(separator: "\n")
    }

    private func using(_ words: [String], in files: [(name: String, text: String)]) -> [String] {
        files.flatMap { file in
            words.filter { code(file.text).contains($0) }.map { "\($0) in \(file.name)" }
        }
    }

    /// The same, for words that are looked for whole: `.red`, and not `.reduce`.
    private func usingWhole(_ words: [String], in files: [(name: String, text: String)]) throws -> [String] {
        try files.flatMap { file -> [String] in
            let text = code(file.text)
            return try words.filter { word in
                let pattern = "(?<![A-Za-z0-9_])" + NSRegularExpression.escapedPattern(for: word) + "(?![A-Za-z0-9_])"
                let whole = try NSRegularExpression(pattern: pattern)
                return whole.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)) != nil
            }.map { "\($0) in \(file.name)" }
        }
    }

    // MARK: - One feature, one name

    func test_every_file_and_every_name_of_the_feature_is_the_features_own() throws {
        let files = try files()

        XCTAssertGreaterThan(files.count, 15)
        for file in files {
            let name = file.name.split(separator: "/").last.map(String.init) ?? file.name
            // Two files of one module cannot share a name, whatever folder each is in.
            XCTAssertTrue(name.hasPrefix("Results"), file.name)
            for line in file.text.split(separator: "\n") {
                let declares = ["struct ", "class ", "enum ", "func ", "let ", "var ", "protocol ", "typealias ", "actor "]
                    .contains { line.hasPrefix($0) || line.hasPrefix("public \($0)") || line.hasPrefix("final \($0)") }
                guard declares || line.hasPrefix("extension ") else { continue }
                let allowed = [
                    "enum Results {}", "enum ResultsCopy {", "public struct ResultsView: View {",
                    "public struct ResultsCompareView: View {", "extension Results {",
                    "extension Results.Memory {",
                ]
                XCTAssertTrue(allowed.contains(String(line)), "\(file.name): \(line)")
            }
        }
    }

    // MARK: - Words and figures are the API's

    func test_no_view_reads_a_number_of_the_apis_or_a_slot_for_itself() throws {
        let numbers = [
            ".score", ".percentile", ".utility", ".weightCoverage", ".lowerQuartile", ".upperQuartile",
            ".minutesTypical", ".minutesJustMissed", ".maxMinutes", ".slots", ".factId", ".contributions",
            ".legs", ".explanations", ".facts",
        ]

        XCTAssertEqual(using(numbers, in: try views()), [])
    }

    func test_no_number_is_formatted_but_the_whole_numbers_the_model_makes() throws {
        let formatting = [
            "String(format:", "NumberFormatter", ".formatted(", "Measurement", "DateFormatter",
            "ByteCountFormatter", "specifier:",
        ]

        XCTAssertEqual(using(formatting, in: try files()), [])
    }

    func test_the_app_builds_edits_and_never_a_spec() throws {
        let building = ["PreferenceSpec(", "Budget(", "Commute(", "FeatureWeight(", "TagWeight(", "AreaRule("]

        XCTAssertEqual(using(building, in: try files()), [])
    }

    func test_nothing_is_said_of_who_lives_somewhere_or_of_how_safe_a_place_is() throws {
        for file in try files() {
            let strings = file.text.components(separatedBy: "\"").enumerated()
                .filter { $0.offset % 2 == 1 }.map(\.element)
            for string in strings {
                for word in ["safe", "dangerous", "residents", "demographic", "ethnic", "religio"] {
                    XCTAssertFalse(string.lowercased().contains(word), "\(file.name): \(string)")
                }
            }
        }
    }

    // MARK: - The banner stays in sight

    func test_nothing_is_drawn_over_the_banner_that_says_the_data_is_made_up() throws {
        // A sheet of the system's covers the whole screen, and the banner with it.
        let covering = [
            ".sheet(", ".fullScreenCover(", ".popover(", ".alert(", ".confirmationDialog(", ".inspector(",
            ".presentationDetents(", "ignoresSafeArea", "SyntheticBanner",
        ]

        XCTAssertEqual(using(covering, in: try files()), [])
    }

    // MARK: - Privacy

    func test_no_id_of_a_fact_a_place_or_a_share_is_given_to_the_system_as_a_name() throws {
        let naming = [
            "accessibilityIdentifier(", "NSUserActivity", "userActivity(", "focusedSceneValue",
            "UIPasteboard", "NSPasteboard", "PasteButton", "openURL",
        ]

        XCTAssertEqual(using(naming, in: try files()), [])
        // A link on the page would hold an address. The one link there is goes to the share sheet.
        XCTAssertEqual(try usingWhole(["Link"], in: try views()), [])
        XCTAssertEqual(
            try files().filter { code($0.text).contains("ShareLink(") }.map(\.name),
            ["Views/ResultsShareView.swift"])
    }

    func test_the_map_asks_the_phone_for_nothing_and_shows_no_position_of_the_person() throws {
        let asking = [
            "CLLocationManager", "UserAnnotation", "MapUserLocationButton", "showsUserLocation",
            ".userLocation", "requestWhenInUseAuthorization", "MKLocalSearch", "MKDirections",
            "MKGeocoder", "CLGeocoder", "LookAround",
        ]

        XCTAssertEqual(using(asking, in: try files()), [])
        // The map is imported by the one file that draws it.
        let importing = try files().filter { $0.text.contains("import MapKit") }.map(\.name)
        XCTAssertEqual(importing, ["Views/ResultsMapView.swift"])
    }

    func test_the_model_is_plain_and_knows_no_view() throws {
        for file in try files() where file.name.hasPrefix("Model/") || file.name == "ResultsCopy.swift" {
            XCTAssertFalse(file.text.contains("import SwiftUI"), file.name)
            XCTAssertFalse(file.text.contains("import MapKit"), file.name)
        }
    }

    // MARK: - Accessibility

    func test_every_colour_is_a_token() throws {
        let colours = ["Color(", "Color.", ".foregroundColor(", "UIColor", "NSColor", ".tint(", "opacity("]
        let named = ["red", "green", "blue", "black", "white", "gray", "orange", "yellow", "pink", "purple"]

        XCTAssertEqual(using(colours, in: try views()), [])
        XCTAssertEqual(try usingWhole(named, in: try views()), [])
    }

    func test_every_size_of_text_is_a_token_so_that_it_grows_with_the_persons_setting() throws {
        let fixed = [
            ".system(size:", "Font.custom(", ".font(.system(", ".font(.body", ".font(.title", ".font(.caption",
            ".font(.headline", ".font(.footnote", ".font(.subheadline", ".lineLimit(", ".minimumScaleFactor(",
            ".truncationMode(", "fixedSize(horizontal: true",
        ]

        XCTAssertEqual(using(fixed, in: try views()), [])
        for file in try views() where file.text.contains("Text(") {
            XCTAssertTrue(file.text.contains("Tokens.Text."), file.name)
        }
    }

    func test_nothing_moves_but_through_the_token_that_heeds_less_motion() throws {
        let moving = [
            ".animation(", ".transition(", ".easeIn", ".easeOut", ".spring", ".linear(", ".matchedGeometryEffect(",
            "TimelineView", ".symbolEffect(", ".phaseAnimator(", ".keyframeAnimator(",
        ]

        // The token is the one animation there is.
        let views = try views().map { (name: $0.name, text: $0.text.replacingOccurrences(of: "Tokens.Motion.animation(", with: "")) }
        XCTAssertEqual(using(moving, in: views), [])
        for file in try self.views() where code(file.text).contains("withAnimation") {
            XCTAssertTrue(file.text.contains("Tokens.Motion.animation("), file.name)
            XCTAssertTrue(file.text.contains("accessibilityReduceMotion"), file.name)
            let bare = code(file.text).components(separatedBy: "withAnimation(").dropFirst().filter {
                !$0.hasPrefix("Tokens.Motion.animation(") && !$0.hasPrefix("animation)")
            }
            XCTAssertEqual(bare.count, 0, file.name)
        }
    }

    func test_everything_that_can_be_pressed_is_as_large_as_a_finger_needs() throws {
        let sized = [".burroPrimary", ".burroSecondary", ".target()", "Tokens.Target.least", "Tokens.Target.row"]
        for file in try views() {
            let text = code(file.text)
            let pressed = ["Button(", "Button {", "Toggle(", "Picker(", "ShareLink("]
            for control in pressed {
                var from = text.startIndex
                while let found = text.range(of: control, range: from..<text.endIndex) {
                    // The size is set on the control, or on what holds it, within the lines that follow.
                    let near = text[found.lowerBound...].split(separator: "\n", omittingEmptySubsequences: false)
                        .prefix(40).joined(separator: "\n")
                    XCTAssertTrue(sized.contains { near.contains($0) }, "\(file.name): \(near.prefix(80))")
                    from = found.upperBound
                }
            }
        }
        XCTAssertGreaterThanOrEqual(Tokens.Target.least, 44)
    }

    func test_every_picture_and_every_mark_has_a_name_or_is_kept_from_a_screen_reader() throws {
        for file in try views() {
            let text = code(file.text)
            for drawn in ["Image(systemName:", "Canvas {", "Meter(", "Pips(", "Capsule()", "Circle()"] {
                guard text.contains(drawn) else { continue }
                XCTAssertTrue(
                    text.contains("accessibilityHidden(true)") || text.contains("accessibilityLabel("),
                    "\(file.name): \(drawn)")
            }
        }
        // Whether a thing is chosen, saved or within a limit is always a word.
        XCTAssertFalse(ResultsCopy.Card.selected.isEmpty)
        XCTAssertFalse(ResultsCopy.Journeys.within.isEmpty)
        XCTAssertFalse(ResultsCopy.Journeys.over.isEmpty)
        XCTAssertFalse(ResultsCopy.Journeys.withinLimit(1).isEmpty)
    }

    // MARK: - The panel over the map

    func test_the_list_stands_at_three_heights_and_the_nearest_is_taken_when_a_drag_ends() {
        XCTAssertEqual(Results.Height.allCases, [.low, .half, .full])
        XCTAssertLessThan(Results.Height.low.share, Results.Height.half.share)
        XCTAssertLessThan(Results.Height.half.share, Results.Height.full.share)
        XCTAssertLessThan(Results.Height.full.share, 1)
        XCTAssertEqual(Results.Height.nearest(to: 0), .low)
        XCTAssertEqual(Results.Height.nearest(to: 0.3), .low)
        XCTAssertEqual(Results.Height.nearest(to: 0.4), .half)
        XCTAssertEqual(Results.Height.nearest(to: 0.69), .half)
        XCTAssertEqual(Results.Height.nearest(to: 0.75), .full)
        XCTAssertEqual(Results.Height.nearest(to: 3), .full)
        XCTAssertEqual(Results.Height.nearest(to: -1), .low)
    }

    func test_the_height_can_be_set_without_a_drag() {
        XCTAssertEqual(Results.Height.low.taller, .half)
        XCTAssertEqual(Results.Height.half.taller, .full)
        XCTAssertEqual(Results.Height.full.taller, .full)
        XCTAssertEqual(Results.Height.full.shorter, .half)
        XCTAssertEqual(Results.Height.low.shorter, .low)
        // A press on the handle takes the next height, and from the tallest the lowest.
        XCTAssertEqual([Results.Height.low, .half, .full].map(\.next), [.half, .full, .low])
        XCTAssertEqual(Results.Height.allCases.map(\.words), ["Low", "Half", "Full"])
    }

    func test_the_list_is_never_shorter_than_its_handle_needs_nor_taller_than_the_room() {
        let least = 110.0

        XCTAssertEqual(Results.Height.half.points(in: 700, least: least), 350)
        XCTAssertEqual(Results.Height.low.points(in: 700, least: least), 154, accuracy: 0.001)
        XCTAssertEqual(Results.Height.low.points(in: 300, least: least), least)
        XCTAssertEqual(Results.Height.full.points(in: 100, least: least), 100)
        XCTAssertEqual(Results.Height.half.points(in: 0, least: least), least)
        XCTAssertEqual(Results.Height.half.points(in: .nan, least: least), least)
    }

    @MainActor
    func test_the_results_are_shown_as_a_map_a_list_or_a_table_and_as_a_map_at_first() {
        let memory = Results.Memory()

        XCTAssertEqual(memory.showing, .map)
        XCTAssertEqual(memory.height, .half)
        XCTAssertEqual(Results.Showing.allCases.map(\.words), ["Map", "List", "Table"])
        XCTAssertFalse(memory.shareOpen)
        XCTAssertFalse(memory.legendOpen)
    }

    // MARK: - The seam with the shell

    @MainActor
    func test_the_screen_is_made_as_the_shell_makes_it() {
        let view: any View = ResultsView()

        XCTAssertNotNil(view)
    }
}
