import Foundation
import XCTest

@testable import BurroKit

/// The app, opened on the stand-in, as the results screen finds it: a search
/// in the environment, a website with an address, and a phone to keep things on.
@MainActor
struct ResultsApp {
    static let site = "https://burro.example.test"

    let api: StandIn
    let app: AppModel
    let storage: MemoryPhoneStorage
    let search: SearchStore
    let memory: Results.Memory
    let hands: Results.Hands

    var flow: SearchFlow { search.flow }
    var state: SearchState { search.state }
    var listed: Results.Listed { Results.listed(search.state) }
    var ground: Results.Ground { Results.Ground(search.state.geometry) }
    var mapped: Results.Mapped { Results.mapped(search.state, on: ground) }
    var tabled: Results.Tabled { Results.tabled(search.state) }

    /// - Parameter site: The website's address. `nil` for an app that was given none.
    init(_ api: StandIn = StandIn.firstSearch(), site: String? = ResultsApp.site) async throws {
        self.api = api
        let storage = MemoryPhoneStorage()
        self.storage = storage
        let notice = SyntheticNotice()
        let client = LiveBurroAPI(
            configuration: APIConfiguration(StandIn.base), transport: api,
            onSynthetic: { said in await notice.note(said) })
        app = AppModel(api: client, site: SiteAddress(site), synthetic: notice, storage: storage)
        app.consent.choose(.allowed)
        await app.open()
        search = try XCTUnwrap(app.search)
        let memory = app.results
        self.memory = memory
        hands = Results.Hands(app: app, search: search, memory: memory)
    }

    /// The app after a first search, with the map loaded: what a person sees on the results screen.
    static func searched(_ api: StandIn = StandIn.firstSearch(), site: String? = ResultsApp.site) async throws
        -> ResultsApp
    {
        let app = try await ResultsApp(api, site: site)
        await app.flow.loadGeometry()
        await app.flow.submitText("leafy and quiet")
        return app
    }

    /// The first of the results, as its card.
    func firstCard(file: StaticString = #filePath, line: UInt = #line) throws -> Results.Card {
        try XCTUnwrap(listed.cards.first, file: file, line: line)
    }
}

/// Every piece of text a value holds, and every whole number: what a view
/// that is handed the value could draw. It reads the value as it is, so a
/// field that is added later is read as well.
enum ResultsDrawn {
    /// What is held to find something in memory, and is never drawn.
    static let notDrawn: Set<String> = [
        "areaId", "slug", "sourceId", "asOf", "component", "id", "url", "hash", "act",
    ]

    struct Found {
        var texts: [String] = []
        var numbers: [(label: String, value: Int)] = []
    }

    static func all(in value: Any) -> Found {
        var found = Found()
        walk(value, label: "", into: &found)
        return found
    }

    /// The texts that hold a digit.
    static func figures(in value: Any) -> [String] {
        all(in: value).texts.filter { $0.contains(where: \.isNumber) }
    }

    private static func walk(_ value: Any, label: String, into found: inout Found) {
        if notDrawn.contains(label) { return }
        if let text = value as? String {
            found.texts.append(text)
            return
        }
        if let number = value as? Int {
            found.numbers.append((label, number))
            return
        }
        if value is Double || value is Bool || value is URL { return }
        let mirror = Mirror(reflecting: value)
        for child in mirror.children {
            walk(child.value, label: child.label ?? label, into: &found)
        }
    }
}

/// Everything the API said that a screen may repeat: each slot as it came,
/// each slot as a row lays it out, each label and name, and the date and the
/// sources of each fact.
enum ResultsSaid {
    static func by(_ facts: [Fact]) -> Set<String> {
        var said: Set<String> = []
        for fact in facts {
            said.insert(fact.label)
            for value in fact.slots.values { said.insert(value) }
            for column in Results.columns(of: fact) { said.insert(column.value) }
            for name in fact.names { said.insert(name) }
            said.insert(fact.asOf)
            said.insert(Results.readableDate(fact.asOf))
            for source in fact.sources { said.insert(source.name) }
            for line in Results.sourceLines(of: [fact]) { said.insert(line.date) }
        }
        return said
    }

    static func by(_ explanations: [Explanation]) -> Set<String> {
        var said: Set<String> = []
        for explanation in explanations {
            let sentences =
                [explanation.orientation] + explanation.reasons + explanation.missing
                + (explanation.tradeOff.map { [$0] } ?? [])
            for sentence in sentences { said.insert(sentence.text) }
        }
        return said
    }

    /// The names the release gives: of each area, each borough, each feature and each tag.
    static func by(_ meta: MetaData, _ areas: [AreaSummary]) -> Set<String> {
        Set(areas.map(\.name) + areas.map(\.borough) + meta.features.map(\.label) + meta.tags.map(\.label))
            .union([meta.releaseId, meta.engineVersion])
    }
}

/// Holds an answer back until it is let go, for an answer a test makes itself.
final class ResultsGate: @unchecked Sendable {
    private let lock = NSLock()
    private var open = false

    func release() {
        lock.withLock { open = true }
    }

    func wait() async throws {
        while !lock.withLock({ open }) {
            try await Task.sleep(nanoseconds: 1_000_000)
        }
    }
}
