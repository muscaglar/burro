import XCTest

@testable import BurroKit

/// The rules the code keeps, read off the source. They hold for every file of
/// the app, whoever wrote it.
///
/// What a person types and the places they name are held in memory for the
/// search and nowhere else. These tests fail when a file reaches for anywhere
/// else they could go.
final class PrivacyRulesTests: XCTestCase {
    /// Every Swift file of the app, by its path from `apps/ios`, with its text.
    private func source() throws -> [(name: String, text: String)] {
        let kit = try Repository.files(under: Repository.sources, ending: ".swift").map {
            ("BurroKit/Sources/BurroKit/\($0)", try Repository.text(Repository.sources.appendingPathComponent($0)))
        }
        let app = try Repository.files(under: Repository.app, ending: ".swift").map {
            ("App/\($0)", try Repository.text(Repository.app.appendingPathComponent($0)))
        }
        return kit + app
    }

    /// The files that use any of these words, but for the ones allowed to.
    private func files(using words: [String], but allowed: [String] = []) throws -> [String] {
        try source()
            .filter { file in !allowed.contains { file.name.hasSuffix($0) } }
            .filter { file in words.contains { file.text.contains($0) } }
            .map(\.name)
    }

    func test_the_scan_reads_the_whole_app() throws {
        let files = try source()

        XCTAssertGreaterThan(files.count, 30)
        XCTAssertTrue(files.contains { $0.name == "App/BurroApp.swift" })
        XCTAssertTrue(files.contains { $0.name.hasSuffix("Features/Search/SearchRootView.swift") })
    }

    func test_nothing_is_ever_written_to_a_log() throws {
        let words = [
            "print(", "debugPrint(", "dump(", "NSLog(", "os_log", "Logger(", "OSLog", "import os",
            "import OSLog", "assertionFailure(\"\\(", "fatalError(\"\\(", "preconditionFailure(\"\\(",
        ]

        XCTAssertEqual(try files(using: words), [])
    }

    func test_nothing_is_kept_on_the_phone_but_through_the_one_store() throws {
        let storage = [
            "UserDefaults", "@AppStorage", "@SceneStorage", "NSUbiquitousKeyValueStore", "SecItem",
            "Keychain", "CoreData", "SwiftData", "NSPersistentContainer", "NSKeyedArchiver",
            "NSCoder", "restorationIdentifier", "NSFileCoordinator",
        ]
        let files = ["FileManager", ".write(to:", "FileHandle", "OutputStream", "contentsOf: url", "createFile("]

        XCTAssertEqual(try self.files(using: storage), [])
        XCTAssertEqual(try self.files(using: files, but: ["Kept/PhoneStorage.swift"]), [])
    }

    func test_nothing_is_offered_to_spotlight_siri_or_handoff() throws {
        let words = [
            "NSUserActivity", "userActivity(", "onContinueUserActivity", "CSSearchableIndex", "CoreSpotlight",
            "AppIntents", "AppIntent", "INInteraction", "import Intents", "AppShortcut", "handlesExternalEvents",
            "WidgetKit", "import ActivityKit",
        ]

        XCTAssertEqual(try files(using: words), [])
    }

    func test_nothing_is_put_on_the_pasteboard_but_when_the_person_copies() throws {
        // A file that copies for the person is named here, with what it copies.
        let copying: [String] = []

        XCTAssertEqual(try files(using: ["UIPasteboard", "NSPasteboard", "PasteButton"], but: copying), [])
    }

    func test_there_is_no_analytics_no_tracking_and_no_report_of_a_crash() throws {
        let words = [
            "AppTrackingTransparency", "ATTrackingManager", "AdSupport", "advertisingIdentifier",
            "identifierForVendor", "MetricKit", "MXMetricManager", "NSSetUncaughtExceptionHandler",
            "StoreKit", "SKAdNetwork", "CLLocationManager", "WKWebView", "SFSafariViewController",
        ]

        XCTAssertEqual(try files(using: words), [])
    }

    func test_only_the_client_reaches_the_network_and_never_through_a_shared_session() throws {
        let network = ["URLSession", "URLRequest", "NWConnection", "NWPathMonitor", "import Network", "CFNetwork"]
        let shared = ["URLSession.shared", "URLCache.shared", "HTTPCookieStorage.shared", "URLCredentialStorage.shared"]

        XCTAssertEqual(
            try files(using: network, but: ["API/Transport.swift", "API/LiveBurroAPI.swift"]), [])
        XCTAssertEqual(try files(using: shared), [])
    }

    func test_no_screen_knows_how_the_api_is_reached() throws {
        let screens = try source().filter { $0.name.contains("/Features/") || $0.name.contains("/Shell/") }
        let reaching = screens.filter { file in
            ["URLSession", "URLRequest", "JSONDecoder", "JSONEncoder", "LiveBurroAPI("].contains {
                file.text.contains($0)
            }
        }

        XCTAssertEqual(reaching.map(\.name), ["BurroKit/Sources/BurroKit/Shell/AppModel.swift"])
    }

    func test_every_import_is_of_what_the_system_gives() throws {
        let allowed: Set<String> = ["Foundation", "SwiftUI", "MapKit", "Observation", "BurroKit"]
        var others: Set<String> = []
        for file in try source() {
            for line in file.text.split(separator: "\n") where line.hasPrefix("import ") || line.hasPrefix("@testable import ") {
                let name = line.split(separator: " ").last.map(String.init) ?? ""
                if !allowed.contains(name) { others.insert("\(name) in \(file.name)") }
            }
        }

        XCTAssertEqual(others, [])
    }

    func test_the_package_depends_on_nothing() throws {
        let manifest = try Repository.text(Repository.package.appendingPathComponent("Package.swift"))
        let project = try Repository.text(
            Repository.ios.appendingPathComponent("Burro.xcodeproj/project.pbxproj"))

        XCTAssertTrue(manifest.contains("dependencies: [],"))
        XCTAssertFalse(manifest.contains(".package("))
        XCTAssertFalse(manifest.contains("://"))
        XCTAssertFalse(manifest.contains(".plugin("))
        XCTAssertFalse(project.contains("XCRemoteSwiftPackageReference"))
        XCTAssertFalse(FileManager.default.fileExists(
            atPath: Repository.package.appendingPathComponent("Package.resolved").path))
    }

    func test_the_privacy_manifest_declares_no_tracking_and_no_collected_data() throws {
        let data = try Data(contentsOf: Repository.app.appendingPathComponent("PrivacyInfo.xcprivacy"))
        let manifest = try XCTUnwrap(
            try PropertyListSerialization.propertyList(from: data, format: nil) as? [String: Any])

        XCTAssertEqual(manifest["NSPrivacyTracking"] as? Bool, false)
        XCTAssertEqual((manifest["NSPrivacyTrackingDomains"] as? [Any])?.count, 0)
        XCTAssertEqual((manifest["NSPrivacyCollectedDataTypes"] as? [Any])?.count, 0)
        // No API that needs a reason is used: nothing reads defaults, a file's dates or the disk's size.
        XCTAssertEqual((manifest["NSPrivacyAccessedAPITypes"] as? [Any])?.count, 0)
        XCTAssertEqual(manifest.count, 4)
    }

    func test_the_app_asks_the_phone_for_nothing() throws {
        let data = try Data(contentsOf: Repository.app.appendingPathComponent("Info.plist"))
        let info = try XCTUnwrap(
            try PropertyListSerialization.propertyList(from: data, format: nil) as? [String: Any])

        XCTAssertEqual(info.keys.filter { $0.hasSuffix("UsageDescription") }, [])
        XCTAssertNil(info["CFBundleURLTypes"])
        XCTAssertNil(info["NSUserActivityTypes"])
        XCTAssertNil(info["UIBackgroundModes"])
        XCTAssertNil(info["CFBundleDocumentTypes"])
        XCTAssertNil(info["LSApplicationQueriesSchemes"])
        // A connection in the clear is allowed to this machine alone, for a build that is being worked on.
        XCTAssertEqual(info["NSAppTransportSecurity"] as? [String: Bool], ["NSAllowsLocalNetworking": true])
    }

    func test_the_project_names_no_team_and_the_one_bundle_id() throws {
        let project = try Repository.text(
            Repository.ios.appendingPathComponent("Burro.xcodeproj/project.pbxproj"))

        XCTAssertEqual(project.components(separatedBy: "PRODUCT_BUNDLE_IDENTIFIER = london.burro.app;").count - 1, 2)
        XCTAssertEqual(project.components(separatedBy: "PRODUCT_BUNDLE_IDENTIFIER").count - 1, 2)
        XCTAssertEqual(project.components(separatedBy: #"DEVELOPMENT_TEAM = "";"#).count - 1, 2)
        XCTAssertEqual(project.components(separatedBy: "DEVELOPMENT_TEAM").count - 1, 2)
        XCTAssertFalse(project.contains("/Users/"))
        XCTAssertFalse(project.contains("PROVISIONING_PROFILE"))
    }

    func test_no_file_of_the_app_names_a_machine_or_a_home_folder() throws {
        let folder = Repository.ios
        let names = Repository.files(under: folder, ending: "")
            .filter { !$0.hasPrefix("build/") && !$0.contains(".build/") && !$0.contains("/Recorded/") }
            .filter { !$0.hasSuffix(".DS_Store") && !$0.contains("xcuserdata") }
        var naming: [String] = []
        for name in names {
            guard let text = try? String(contentsOf: folder.appendingPathComponent(name), encoding: .utf8) else {
                continue
            }
            // This file holds the words it looks for.
            if name.hasSuffix("PrivacyRulesTests.swift") { continue }
            if text.contains("/Users/") || text.contains("/home/") || text.contains(NSUserName() + "/") {
                naming.append(name)
            }
        }

        XCTAssertGreaterThan(names.count, 60)
        XCTAssertEqual(naming, [])
    }

    func test_site_copy_holds_no_figure_about_a_place() throws {
        let copy = try source().filter { $0.name.hasSuffix("Copy.swift") }

        XCTAssertGreaterThanOrEqual(copy.count, 2)
        for file in copy {
            let strings = file.text.components(separatedBy: "\"").enumerated()
                .filter { $0.offset % 2 == 1 }.map(\.element)
            // How long a provider keeps what it reads is the API's to say, and is written nowhere here.
            XCTAssertEqual(strings.filter { $0.contains(where: \.isNumber) }, [], file.name)
            for place in Answers.areas.map(\.name) + Answers.areas.map(\.borough) {
                XCTAssertFalse(file.text.contains(place), "\(file.name) names \(place)")
            }
        }
    }
}
