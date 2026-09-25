import XCTest

@testable import BurroKit

/// Where the API is: one build setting, read in one place.
final class ConfigurationTests: XCTestCase {
    private func cleaned(_ value: String?) -> String? {
        APIConfiguration(value).baseURL?.absoluteString
    }

    func test_the_address_is_kept_with_no_slash_at_its_end() {
        XCTAssertEqual(cleaned("https://api.example.test"), "https://api.example.test")
        XCTAssertEqual(cleaned("https://api.example.test/"), "https://api.example.test")
        XCTAssertEqual(cleaned("  https://api.example.test/burro//  "), "https://api.example.test/burro")
        XCTAssertEqual(cleaned("https://api.example.test:8443"), "https://api.example.test:8443")
    }

    func test_with_nothing_set_there_is_no_address() {
        XCTAssertNil(cleaned(nil))
        XCTAssertNil(cleaned(""))
        XCTAssertNil(cleaned("   "))
        // A build setting that was never filled in comes through as it was written.
        XCTAssertNil(cleaned("$(BURRO_API_BASE_URL)"))
        XCTAssertNil(APIConfiguration.none.baseURL)
    }

    func test_what_is_not_an_address_of_the_api_is_refused() {
        XCTAssertNil(cleaned("api.example.test"))
        XCTAssertNil(cleaned("ftp://api.example.test"))
        XCTAssertNil(cleaned("file:///etc/hosts"))
        XCTAssertNil(cleaned("https://"))
        XCTAssertNil(cleaned("https://api.example.test?key=1"))
        XCTAssertNil(cleaned("https://api.example.test#part"))
    }

    func test_an_address_with_a_name_and_a_password_in_it_is_refused() {
        XCTAssertNil(cleaned("https://someone:secret@api.example.test"))  // public-only: allow
        XCTAssertNil(cleaned("https://someone@api.example.test"))  // public-only: allow
    }

    func test_what_a_person_types_is_never_sent_in_the_clear_across_a_network() {
        XCTAssertNil(cleaned("http://api.example.test"))
        XCTAssertNil(cleaned("http://192.168.1.20:8000"))
        XCTAssertEqual(cleaned("http://127.0.0.1:8000"), "http://127.0.0.1:8000")
        XCTAssertEqual(cleaned("http://localhost:8000/"), "http://localhost:8000")
    }

    func test_the_address_is_read_from_the_one_key_of_the_info_file() {
        let info: [String: Any] = [APIConfiguration.infoKey: "https://api.example.test/"]

        XCTAssertEqual(APIConfiguration.infoKey, "BurroAPIBaseURL")
        XCTAssertEqual(
            APIConfiguration(infoDictionary: info).baseURL?.absoluteString, "https://api.example.test")
        XCTAssertNil(APIConfiguration(infoDictionary: nil).baseURL)
        XCTAssertNil(APIConfiguration(infoDictionary: ["BurroAPIBaseURL": 8000]).baseURL)
    }

    func test_the_build_setting_is_what_fills_the_key_and_nothing_else_names_an_address() throws {
        let info = try Repository.text(Repository.app.appendingPathComponent("Info.plist"))
        let project = try Repository.text(
            Repository.ios.appendingPathComponent("Burro.xcodeproj/project.pbxproj"))

        XCTAssertTrue(info.contains("<key>BurroAPIBaseURL</key>\n\t<string>$(BURRO_API_BASE_URL)</string>"))
        // A build for release names no address until one is given to it.
        XCTAssertTrue(project.contains(#"BURRO_API_BASE_URL = "";"#))
        XCTAssertTrue(project.contains(#"BURRO_API_BASE_URL = "http://127.0.0.1:8000";"#))
        XCTAssertEqual(project.components(separatedBy: "BURRO_API_BASE_URL").count - 1, 2)

        let naming = try Repository.files(under: Repository.sources, ending: ".swift").filter { name in
            let text = try Repository.text(Repository.sources.appendingPathComponent(name))
            return text.contains("infoDictionary") || text.contains("BurroAPIBaseURL")
        }
        XCTAssertEqual(naming, ["API/APIConfiguration.swift", "Shell/AppModel.swift", "Shell/SiteAddress.swift"])
    }

    // MARK: - Where the website is

    private let farrowmere = AreaRef(
        areaId: "syn-n0006", slug: "farrowmere", name: "Farrowmere", borough: "Quillhaven")

    func test_the_website_has_no_address_until_one_is_given() throws {
        let info = try Repository.text(Repository.app.appendingPathComponent("Info.plist"))
        let project = try Repository.text(
            Repository.ios.appendingPathComponent("Burro.xcodeproj/project.pbxproj"))

        XCTAssertTrue(info.contains("<key>BurroSiteURL</key>\n\t<string>$(BURRO_SITE_URL)</string>"))
        XCTAssertEqual(project.components(separatedBy: #"BURRO_SITE_URL = "";"#).count - 1, 2)
        XCTAssertNil(SiteAddress.none.area(farrowmere))
        XCTAssertNil(SiteAddress("$(BURRO_SITE_URL)").origin)
        XCTAssertNil(SiteAddress(infoDictionary: [:]).share("3TQkoOxY0dYBEVyMymzDjg"))
    }

    func test_the_address_of_an_area_holds_its_city_and_its_slug_and_nothing_else() {
        let site = SiteAddress(infoDictionary: ["BurroSiteURL": "https://burro.example.test/"])

        XCTAssertEqual(site.area(farrowmere)?.absoluteString, "https://burro.example.test/synthetic/farrowmere")
        XCTAssertEqual(
            site.area(AreaRef(areaId: "lon-n0412", slug: "a-b", name: "A", borough: "B"))?.absoluteString,
            "https://burro.example.test/london/a-b")
        XCTAssertNil(site.area(AreaRef(areaId: "xyz-n1", slug: "a", name: "A", borough: "B")))
        XCTAssertNil(site.area(AreaRef(areaId: "syn-n1", slug: "../meta", name: "A", borough: "B")))
        XCTAssertNil(site.area(AreaRef(areaId: "syn-n1", slug: "A b?c", name: "A", borough: "B")))
    }

    func test_a_shares_id_goes_in_the_fragment_and_what_is_not_an_id_goes_nowhere() {
        let site = SiteAddress("https://burro.example.test")

        XCTAssertEqual(
            site.share("3TQkoOxY0dYBEVyMymzDjg")?.absoluteString, "https://burro.example.test/s#3TQkoOxY0dYBEVyMymzDjg")
        XCTAssertEqual(site.share("Prqi4-zqlo9VIPSME2DL6A")?.fragment, "Prqi4-zqlo9VIPSME2DL6A")
        XCTAssertNil(site.share("too-short"))
        XCTAssertNil(site.share("TbfsnjL3GyTlKt967hH2H?"))
        XCTAssertNil(site.share("leafy and quiet, near X"))
        XCTAssertNil(site.share(""))
    }

    func test_the_website_is_an_origin_served_over_https() {
        XCTAssertEqual(SiteAddress(" https://Burro.Example.test/ ").origin?.absoluteString, "https://burro.example.test")
        XCTAssertNil(SiteAddress("http://burro.example.test").origin)
        XCTAssertNil(SiteAddress("https://burro.example.test/app").origin)
        XCTAssertNil(SiteAddress("https://burro.example.test?x=1").origin)
        XCTAssertNil(SiteAddress("burro.example.test").origin)
    }
}
