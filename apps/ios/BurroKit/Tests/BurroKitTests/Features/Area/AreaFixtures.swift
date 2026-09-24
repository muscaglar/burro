import Foundation
import XCTest

@testable import BurroKit

/// What the tests of an area's screen and of the shortlist begin from.
@MainActor
enum AreaFixtures {
    static let site = "https://burro.example.test"

    static let farrowmere = AreaRef(
        areaId: "syn-n0006", slug: "farrowmere", name: "Farrowmere", borough: "Quillhaven")
    static let alderwick = AreaRef(
        areaId: "syn-n0001", slug: "alderwick", name: "Alderwick", borough: "Quillhaven")
    static let cindermoor = AreaRef(Answers.profile("cindermoor").area)

    /// The release the recordings were made on.
    static let release = Meta(
        releaseId: Answers.meta.releaseId, engineVersion: Answers.meta.engineVersion,
        synthetic: Answers.meta.synthetic)

    /// An app on the stand-in, as the shell makes one.
    static func app(
        _ api: StandIn = StandIn.firstSearch(), storage: any PhoneStorage = MemoryPhoneStorage(),
        site: String? = AreaFixtures.site
    ) -> AppModel {
        let notice = SyntheticNotice()
        let client = LiveBurroAPI(
            configuration: APIConfiguration(StandIn.base), transport: api,
            onSynthetic: { said in await notice.note(said) })
        return AppModel(api: client, site: SiteAddress(site), synthetic: notice, storage: storage)
    }

    /// The page of a recorded area, laid out under the release's headings.
    static func page(_ slug: String, release: Meta = AreaFixtures.release) -> AreaPage {
        AreaPage(
            Answers.profile(slug), release: release, features: Answers.meta.features, tags: Answers.meta.tags)
    }

    /// Every recorded area, by its slug.
    static let slugs: [String] = Recorded.scenarios
        .filter { $0.hasPrefix("area/") }
        .map { String($0.dropFirst("area/".count)) }

    /// A journey's fact, as route 3 serves one: it names a place a person must reach.
    static func journey(to place: String, from areaId: String = "syn-n0006") -> Fact {
        Fact(
            factId: "\(areaId)/travel/syn-p0021.pt", areaId: areaId, kind: .travel, key: "syn-p0021.pt",
            label: "Journey", template: .travelPt,
            slots: ["place": place, "mode": "By public transport", "typical": "21", "missed": "26"],
            numbers: ["21", "26"], names: [place],
            sources: [FactSource(sourceId: "synthetic", name: "Synthetic test data")],
            asOf: "2026-09", synthetic: true)
    }
}
