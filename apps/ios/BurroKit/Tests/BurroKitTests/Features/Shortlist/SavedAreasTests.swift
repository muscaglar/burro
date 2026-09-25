import XCTest

@testable import BurroKit

/// The shortlist: what is kept of a saved area, that it is there when the
/// store is opened again, and that nothing of a search is ever among it.
final class SavedAreasTests: XCTestCase {
    // A string found nowhere else, planted in what a person types and in a place they name.
    private let canary = "zqxcanary7431"
    private let day = Date(timeIntervalSince1970: 1_790_000_000)

    /// An app and its saved areas, on the two stores given.
    @MainActor
    private func opened(
        names: any PhoneStorage, facts: any SavedAreasStorage, api: StandIn = StandIn.firstSearch()
    ) -> (app: AppModel, saved: SavedAreas) {
        let app = AreaFixtures.app(api, storage: names)
        return (app, SavedAreas(app: app, storage: facts))
    }

    private func object(_ json: JSON?) -> [String: JSON] {
        if case .object(let fields) = json { return fields }
        return [:]
    }

    private func array(_ json: JSON?) -> [JSON] {
        if case .array(let items) = json { return items }
        return []
    }

    // MARK: - Opened again

    @MainActor
    func test_the_shortlist_is_there_with_its_facts_when_the_store_is_opened_again() {
        let names = MemoryPhoneStorage()
        let facts = FileSavedAreasStorage(MemoryPhoneStorage())
        let first = opened(names: names, facts: facts)
        first.saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))
        first.saved.add(AreaFixtures.alderwick, page: AreaFixtures.page("alderwick"))

        let again = opened(names: names, facts: facts, api: StandIn().unreachable(.getMeta))

        XCTAssertEqual(again.saved.entries.map(\.id), ["syn-n0001", "syn-n0006"])
        XCTAssertEqual(again.saved.entries.map(\.area), [AreaFixtures.alderwick, AreaFixtures.farrowmere])
        for (entry, slug) in zip(again.saved.entries, ["alderwick", "farrowmere"]) {
            let page = AreaFixtures.page(slug)
            XCTAssertEqual(entry.kept?.page.said, page.said)
            XCTAssertEqual(entry.kept?.page.measured.map(\.dimension), page.measured.map(\.dimension))
            XCTAssertEqual(entry.kept?.releaseId, "syn-2026-09-23-01")
            XCTAssertEqual(entry.kept?.synthetic, true)
            XCTAssertEqual(
                entry.kept?.savedOn.timeIntervalSince1970 ?? 0, entry.saved.savedOn.timeIntervalSince1970,
                accuracy: 1)
        }
        XCTAssertFalse(again.saved.couldNotSave)
        XCTAssertTrue(again.app.synthetic.seen)
    }

    @MainActor
    func test_the_shortlist_survives_in_files_that_are_left_out_of_backups() throws {
        let folder = FileManager.default.temporaryDirectory
            .appendingPathComponent("burro-saved-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: folder) }
        let names = FilePhoneStorage(folder: folder.appendingPathComponent("names", isDirectory: true))
        let kept = folder.appendingPathComponent("facts", isDirectory: true)
        let first = opened(names: names, facts: FileSavedAreasStorage(FilePhoneStorage(folder: kept)))
        first.saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))
        first.saved.add(AreaFixtures.alderwick, page: AreaFixtures.page("alderwick"))
        first.saved.move("syn-n0006", by: -1)

        let again = opened(
            names: FilePhoneStorage(folder: folder.appendingPathComponent("names", isDirectory: true)),
            facts: FileSavedAreasStorage(FilePhoneStorage(folder: kept)))

        XCTAssertEqual(again.saved.entries.map(\.id), ["syn-n0006", "syn-n0001"])
        XCTAssertEqual(again.saved.entries.first?.kept?.page.said, AreaFixtures.page("farrowmere").said)
        XCTAssertTrue(again.saved.factsOutliveTheApp)
        XCTAssertEqual(try kept.resourceValues(forKeys: [.isExcludedFromBackupKey]).isExcludedFromBackup, true)
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: kept.path), ["saved-areas.json"])
    }

    @MainActor
    func test_a_file_that_is_not_a_shortlist_is_read_as_an_empty_one() {
        for written in ["not a shortlist", #"{"version":2,"order":[],"areas":[]}"#, #"{"version":1}"#, "[]"] {
            let store = MemoryPhoneStorage([.savedAreas: Data(written.utf8)])

            let saved = opened(names: MemoryPhoneStorage(), facts: FileSavedAreasStorage(store)).saved

            XCTAssertEqual(saved.entries, [], written)
            XCTAssertEqual(saved.kept, [:], written)
        }
    }

    // MARK: - What is kept

    @MainActor
    func test_what_is_kept_has_fixed_keys_and_no_room_for_a_search() throws {
        let facts = FileSavedAreasStorage(MemoryPhoneStorage())
        let saved = opened(names: MemoryPhoneStorage(), facts: facts).saved
        saved.add(AreaFixtures.cindermoor, page: AreaFixtures.page("cindermoor"))

        let kept = object(try JSON.read(XCTUnwrap(facts.written)))
        let area = object(array(kept["areas"]).first)
        let rows = array(area["rows"]).map(object)

        XCTAssertEqual(Set(kept.keys), ["version", "order", "areas"])
        XCTAssertEqual(kept["version"], .number(1))
        XCTAssertEqual(kept["order"], .array([.string("syn-n0003")]))
        XCTAssertEqual(
            Set(area.keys),
            ["area_id", "slug", "name", "borough", "saved_on", "release_id", "synthetic", "preview", "rankable",
             "neighbours", "rows", "vibes"])
        XCTAssertEqual(area["release_id"], .string("syn-2026-09-23-01"))
        XCTAssertEqual(area["preview"], .bool(false))
        XCTAssertEqual(Set(object(array(area["neighbours"]).first).keys), ["area_id", "slug", "name", "borough"])
        XCTAssertFalse(rows.isEmpty)
        for row in rows {
            XCTAssertTrue(Set(row.keys).isSubset(of: ["part", "dimension", "key", "label", "fact"]))
            guard let fact = row["fact"] else { continue }
            XCTAssertEqual(
                Set(object(fact).keys), ["kind", "key", "label", "template", "slots", "sources", "as_of", "synthetic"])
        }
        // A feature with no figure is kept as having none: nothing is filled in.
        XCTAssertTrue(rows.contains { $0["fact"] == nil && $0["part"] == .string("measured") })
        // A vibe is kept by its name, its ends and its band. It has no key for what a search asked for.
        let vibes = array(area["vibes"]).map(object)
        XCTAssertEqual(vibes.count, Answers.meta.tags.count)
        for vibe in vibes {
            XCTAssertTrue(
                Set(vibe.keys).isSubset(of: [
                    "list", "tag_id", "name", "low", "high", "band", "spread_low", "spread_high", "plainly",
                    "rests_on", "waits_on", "not_in_data", "held", "rough", "fact",
                ]))
            XCTAssertNotNil(vibe["band"])
        }
        // What a vibe that is a rough guide says of itself is kept with it, and with no other.
        XCTAssertEqual(
            vibes.filter { $0["rough"] != nil }.map { $0["tag_id"] }, [.string("village_feel")])
        XCTAssertEqual(
            Mirror(reflecting: try XCTUnwrap(saved.kept["syn-n0003"])).children.compactMap(\.label),
            ["areaId", "slug", "name", "borough", "savedOn", "releaseId", "synthetic", "preview", "rankable",
             "neighbours", "rows", "vibes"])
    }

    @MainActor
    func test_an_area_saved_from_a_preview_says_so_with_no_connection() throws {
        let preview: MetaData = try Recorded.data(.getMeta, "preview/meta")
        let data: AreaData = try Recorded.data(.getArea, "preview/area-alderwick")
        let release = Meta(
            releaseId: preview.releaseId, engineVersion: preview.engineVersion, synthetic: preview.synthetic,
            preview: preview.preview)
        let page = AreaPage(
            data, release: release, features: preview.features, tags: preview.tags, recipes: preview.recipes)
        let names = MemoryPhoneStorage()
        let facts = FileSavedAreasStorage(MemoryPhoneStorage())
        let first = opened(names: names, facts: facts)
        XCTAssertFalse(first.app.preview.seen)
        first.saved.add(page.area, page: page)

        // The app is opened again, and nothing is reached.
        let again = opened(names: names, facts: facts, api: StandIn().unreachable(.getMeta))

        XCTAssertTrue(again.app.preview.seen)
        XCTAssertEqual(again.saved.kept[page.area.areaId]?.preview, true)
        XCTAssertEqual(again.saved.kept[page.area.areaId]?.page.preview, true)
        // What the vibes wait on is kept with them, so that it is said with no connection.
        XCTAssertEqual(again.saved.kept[page.area.areaId]?.page.vibes.map(\.shown), page.vibes.map(\.shown))
    }

    @MainActor
    func test_the_date_is_written_one_way_whatever_writes_the_file() throws {
        let kept = KeptArea(AreaFixtures.page("farrowmere"), savedOn: day)

        let written = try JSON.written(kept)
        let read = try JSONDecoder().decode(KeptArea.self, from: written.data)

        XCTAssertEqual(written["saved_on"], .string("2026-09-21T14:13:20Z"))
        XCTAssertEqual(read, kept)
        XCTAssertEqual(read.savedOn, day)
    }

    @MainActor
    func test_nothing_typed_and_nothing_of_the_search_is_kept() async throws {
        // A whole search: a sentence, a place looked for, two places to reach, reasons that
        // name them, and a shared link. Then the first result is saved from its screen.
        let named = canary + " Works"
        let api = StandIn()
            .on(.interpret, "interpret-two-journeys")
            .on(.rank, "rank-two-journeys")
            .on(.searchPlaces, "places-search")
            .on(.createShare, "share-made")
            .on(
                .explainTop,
                .made { [named] _ in
                    try Recorded.read("explanations-two-journeys").with(data: { data in
                        guard case .array(let facts) = data["facts"] else { return }
                        data["facts"] = .array(
                            facts.map { fact in
                                var fact = fact
                                guard fact["kind"] == .string("travel"), var slots = fact["slots"] else { return fact }
                                slots["place"] = .string(named)
                                fact["slots"] = slots
                                fact["names"] = .array([.string(named)])
                                return fact
                            })
                    })
                })
        let names = MemoryPhoneStorage()
        let facts = FileSavedAreasStorage(MemoryPhoneStorage())
        let (app, saved) = opened(names: names, facts: facts, api: api)
        app.consent.choose(.allowed)
        await app.open()
        let search = try XCTUnwrap(app.search)
        await search.flow.submitText("30 minutes to \(canary) University, leafy")
        _ = await search.flow.searchPlaces(canary)
        _ = await search.flow.createShare(exactPlaces: true)
        let first = try XCTUnwrap(search.state.ranking?.ranked.first)
        let area = AreaRef(try XCTUnwrap(search.state.area(first.areaId)))
        XCTAssertTrue(search.state.explained)
        XCTAssertTrue(search.state.facts.values.contains { $0.slots["place"] == named })

        let loader = AreaLoader(area: area, app: app, saved: saved)
        await loader.load()
        guard case .page(let page, .api) = loader.shown else { return XCTFail("The area was not read.") }
        saved.add(area, page: page)
        saved.move(area.areaId, by: 1)
        saved.keep(page)

        let said = try XCTUnwrap(AreaInSearch(search.state, areaId: area.areaId))
        var never: [String] = [canary, named, "spec_hash", "fact_id", "travel", "budget_fit", "score", "rank\""]
        never += search.state.spec.commutes.map(\.placeId)
        never += [search.state.specHash, search.state.rankedHash].compactMap { $0 }
        never += said.reasons.map(\.text)
        // A fact's id is treated as a place's is, whatever it is the id of.
        never += page.facts.map(\.factId) + search.state.facts.keys
        never += search.state.facts.values.filter { $0.kind == .travel }.compactMap { $0.slots["place"] }
        if case .success(let share) = await search.flow.createShare(exactPlaces: true) {
            never.append(share.data.shareId)
        }
        XCTAssertGreaterThan(never.count, 12)
        let ofAreas = [
            String(decoding: try XCTUnwrap(names.read(.shortlist)), as: UTF8.self),
            String(decoding: try XCTUnwrap(facts.written), as: UTF8.self),
            String(reflecting: saved.kept), String(reflecting: saved.entries),
        ]
        let written = ofAreas + [String(decoding: try XCTUnwrap(names.read(.consent)), as: UTF8.self)]
        for text in ofAreas { XCTAssertTrue(text.contains(area.name)) }
        for text in written {
            for word in never where !word.isEmpty {
                XCTAssertFalse(text.contains(word), "What is kept holds \(word.prefix(12)).")
            }
        }
    }

    @MainActor
    func test_a_fact_of_a_search_is_refused_wherever_it_is_found() throws {
        let journey = AreaFixtures.journey(to: canary)
        let real = AreaFixtures.page("farrowmere")
        func of(_ kind: FactKind, _ template: TemplateId) -> Fact {
            Fact(
                factId: "syn-n0006/x/y", areaId: "syn-n0006", kind: kind, key: canary, label: canary,
                template: template, slots: ["place": canary], numbers: [], names: [canary],
                sources: journey.sources, asOf: "2026", synthetic: true)
        }
        // A page that was handed a journey in every part of it, as a fault upstream might.
        let leafy = try XCTUnwrap(real.vibes.first { $0.shown.tagId == .leafy })
        let faulty = AreaPage(
            area: real.area, rankable: true, releaseId: real.releaseId, synthetic: true, preview: false,
            named: journey, neighbours: real.neighbours,
            stations: real.stations + [journey], rent: real.rent + [journey], buy: [journey],
            measured: [
                AreaPage.Group(
                    dimension: .homes,
                    rows: [AreaPage.Row(label: "Homes", fact: journey, kind: .feature, key: "homes_flats")])
            ],
            vibes: [AreaPage.Vibe(list: leafy.list, shown: leafy.shown, fact: of(.budgetFit, .budgetOver))])

        let kept = KeptArea(faulty, savedOn: day)

        XCTAssertNil(KeptFact(journey))
        XCTAssertNil(KeptFact(of(.budgetFit, .budgetUnder)))
        XCTAssertNil(KeptFact(of(.missing, .missing)))
        XCTAssertNil(KeptFact(of(.unlisted("opinion"), .feature)))
        XCTAssertNil(KeptFact(of(.feature, .travelPt)))
        XCTAssertNil(KeptFact(of(.feature, .unlisted("opinion"))))
        XCTAssertEqual(kept.rows.count, real.stations.count + real.rent.count)
        // A vibe is kept by its name and its band, and the fact that was handed with it is not.
        XCTAssertEqual(kept.vibes.map(\.name), ["Leafy"])
        XCTAssertEqual(kept.vibes.map(\.fact), [nil])
        XCTAssertFalse(String(decoding: try JSONEncoder().encode(kept), as: UTF8.self).contains(canary))
        XCTAssertEqual(KeptFact.kinds, [.area, .feature, .tag, .cost, .station])
    }

    @MainActor
    func test_a_file_that_holds_a_fact_of_a_search_is_not_read() throws {
        let kept = KeptShortlist(order: ["syn-n0006"], areas: [KeptArea(AreaFixtures.page("farrowmere"), savedOn: day)])
        var written = try JSON.written(kept)
        var areas = array(written["areas"])
        var rows = array(areas[0]["rows"])
        rows[0]["fact"]?["kind"] = .string("travel")
        areas[0]["rows"] = .array(rows)
        written["areas"] = .array(areas)
        let names = MemoryPhoneStorage()
        Shortlist(storage: names).add(AreaFixtures.farrowmere, synthetic: true)

        let saved = opened(
            names: names, facts: FileSavedAreasStorage(MemoryPhoneStorage([.savedAreas: try written.data]))
        ).saved

        XCTAssertEqual(saved.kept, [:])
        XCTAssertEqual(saved.entries.map(\.id), ["syn-n0006"])
    }

    // MARK: - Remove, reorder, clear

    @MainActor
    func test_an_area_that_is_removed_is_gone_from_the_phone_with_its_facts() throws {
        let names = MemoryPhoneStorage()
        let facts = FileSavedAreasStorage(MemoryPhoneStorage())
        let saved = opened(names: names, facts: facts).saved
        saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))
        saved.add(AreaFixtures.alderwick, page: AreaFixtures.page("alderwick"))

        saved.remove("syn-n0006")

        XCTAssertEqual(saved.entries.map(\.id), ["syn-n0001"])
        XCTAssertFalse(saved.contains("syn-n0006"))
        for data in [try XCTUnwrap(facts.written), try XCTUnwrap(names.read(.shortlist))] {
            XCTAssertFalse(String(decoding: data, as: UTF8.self).contains("Farrowmere"))
            XCTAssertTrue(String(decoding: data, as: UTF8.self).contains("Alderwick"))
        }
        saved.remove("syn-n0001")
        XCTAssertNil(facts.written)
    }

    @MainActor
    func test_an_area_is_saved_and_taken_off_by_the_one_button() {
        let (app, saved) = opened(names: MemoryPhoneStorage(), facts: MemorySavedAreasStorage())

        saved.toggle(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))
        XCTAssertTrue(saved.contains("syn-n0006"))
        XCTAssertTrue(app.shortlist.contains("syn-n0006"))
        XCTAssertEqual(app.shortlist.entries.first?.synthetic, true)
        saved.toggle(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))

        XCTAssertEqual(saved.entries, [])
        XCTAssertEqual(app.shortlist.entries, [])
        XCTAssertEqual(saved.kept, [:])
    }

    @MainActor
    func test_saving_an_area_twice_keeps_it_once_and_leaves_its_facts_as_they_were() {
        let older = Meta(
            releaseId: "syn-2026-08-01-01", engineVersion: "1.3.0", synthetic: true, preview: false)
        let saved = opened(names: MemoryPhoneStorage(), facts: MemorySavedAreasStorage()).saved

        saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere", release: older))
        saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))

        XCTAssertEqual(saved.entries.count, 1)
        XCTAssertEqual(saved.kept["syn-n0006"]?.releaseId, "syn-2026-08-01-01")
    }

    @MainActor
    func test_areas_are_put_in_the_persons_order_and_the_order_is_kept() {
        let names = MemoryPhoneStorage()
        let facts = FileSavedAreasStorage(MemoryPhoneStorage())
        let saved = opened(names: names, facts: facts).saved
        for slug in ["farrowmere", "alderwick", "cindermoor", "pellam-cross"] {
            saved.add(AreaRef(Answers.profile(slug).area), page: AreaFixtures.page(slug))
        }
        XCTAssertEqual(saved.entries.map(\.saved.slug), ["pellam-cross", "cindermoor", "alderwick", "farrowmere"])

        saved.move(fromOffsets: IndexSet(integer: 3), toOffset: 0)
        XCTAssertEqual(saved.entries.map(\.saved.slug), ["farrowmere", "pellam-cross", "cindermoor", "alderwick"])
        saved.move(fromOffsets: IndexSet(integer: 0), toOffset: 4)
        XCTAssertEqual(saved.entries.map(\.saved.slug), ["pellam-cross", "cindermoor", "alderwick", "farrowmere"])
        saved.move(fromOffsets: IndexSet([0, 2]), toOffset: 2)
        XCTAssertEqual(saved.entries.map(\.saved.slug), ["cindermoor", "pellam-cross", "alderwick", "farrowmere"])
        saved.move("syn-n0006", by: -1)
        saved.move("syn-n0006", by: -1)
        XCTAssertEqual(saved.entries.map(\.saved.slug), ["cindermoor", "farrowmere", "pellam-cross", "alderwick"])
        saved.move("syn-n0001", by: 1)
        saved.move(fromOffsets: IndexSet(integer: 9), toOffset: 0)

        let again = opened(names: names, facts: facts).saved
        XCTAssertEqual(again.entries.map(\.saved.slug), ["cindermoor", "farrowmere", "pellam-cross", "alderwick"])
        XCTAssertFalse(again.canMove("syn-n0003", by: -1))
        XCTAssertTrue(again.canMove("syn-n0003", by: 1))
        XCTAssertFalse(again.canMove("syn-n0001", by: 1))
        XCTAssertFalse(again.canMove("syn-n9999", by: 1))
        // Moving an area changes no date. A date is kept to the second.
        func seconds(_ entries: [SavedAreas.Entry]) -> [String: Int] {
            Dictionary(uniqueKeysWithValues: entries.map { ($0.id, Int($0.saved.savedOn.timeIntervalSince1970)) })
        }
        XCTAssertEqual(seconds(again.entries), seconds(saved.entries))
    }

    @MainActor
    func test_clearing_takes_every_area_and_every_fact_off_the_phone() {
        let names = MemoryPhoneStorage()
        let facts = FileSavedAreasStorage(MemoryPhoneStorage())
        let saved = opened(names: names, facts: facts).saved
        saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))
        saved.add(AreaFixtures.alderwick, page: AreaFixtures.page("alderwick"))

        saved.clear()

        XCTAssertEqual(saved.entries, [])
        XCTAssertEqual(saved.kept, [:])
        XCTAssertEqual(saved.order, [])
        XCTAssertNil(names.read(.shortlist))
        XCTAssertNil(facts.written)
        XCTAssertEqual(opened(names: names, facts: facts).saved.entries, [])
    }

    // MARK: - An older release

    @MainActor
    func test_a_saved_area_from_an_older_release_says_so() throws {
        let older = Meta(
            releaseId: "syn-2026-08-01-01", engineVersion: "1.3.0", synthetic: true, preview: false)
        let saved = opened(names: MemoryPhoneStorage(), facts: MemorySavedAreasStorage()).saved
        saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere", release: older))
        saved.add(AreaFixtures.alderwick, page: AreaFixtures.page("alderwick"))
        let entries = saved.entries

        let now = Answers.meta.releaseId
        let shown = entries.map { ShortlistShown($0, older: saved.isOlder($0, than: now)) }

        XCTAssertEqual(shown.map(\.older), [false, true])
        XCTAssertEqual(
            shown[1].lines(in: .gmt).last,
            "The data has changed since this area was saved, so its figures may differ now.")
        XCTAssertFalse(shown[0].lines(in: .gmt).contains(ShortlistCopy.older))
        // With no release read, as with no connection, nothing is said to have changed.
        XCTAssertFalse(saved.isOlder(entries[1], than: nil))
    }

    @MainActor
    func test_a_row_says_the_names_the_date_and_what_is_known_of_the_figures() throws {
        let names = MemoryPhoneStorage()
        Shortlist(storage: names, now: { self.day }).add(AreaFixtures.farrowmere, synthetic: true)
        let saved = opened(names: names, facts: MemorySavedAreasStorage()).saved

        let bare = ShortlistShown(try XCTUnwrap(saved.entries.first), older: false)
        saved.keep(AreaFixtures.page("farrowmere"))
        let full = ShortlistShown(try XCTUnwrap(saved.entries.first), older: false)

        XCTAssertEqual(bare.name, "Farrowmere")
        XCTAssertEqual(
            bare.lines(in: .gmt),
            [
                "Quillhaven", "Saved 21 September 2026",
                "Its figures are not on this phone. Open it with a connection to read them.",
            ])
        XCTAssertEqual(full.lines(in: .gmt), ["Quillhaven", "Saved 21 September 2026"])
        XCTAssertEqual(saved.kept["syn-n0006"]?.savedOn, day)
    }

    // MARK: - In step with the shell's list

    @MainActor
    func test_an_area_saved_elsewhere_is_listed_first_and_one_removed_elsewhere_leaves_nothing_behind() async {
        let facts = FileSavedAreasStorage(MemoryPhoneStorage())
        let (app, saved) = opened(names: MemoryPhoneStorage(), facts: facts)
        saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))

        // As a result's card does, with no page in hand.
        app.toggleShortlist(AreaFixtures.alderwick)
        XCTAssertEqual(saved.entries.map(\.id), ["syn-n0001", "syn-n0006"])
        XCTAssertNil(saved.entries.first?.kept)
        app.toggleShortlist(AreaFixtures.farrowmere)
        await until { saved.kept["syn-n0006"] == nil }

        XCTAssertEqual(saved.entries.map(\.id), ["syn-n0001"])
        XCTAssertEqual(saved.order, ["syn-n0001"])
        XCTAssertFalse(String(decoding: facts.written ?? Data(), as: UTF8.self).contains("Farrowmere"))
    }

    @MainActor
    func test_the_last_saved_comes_first_wherever_it_was_saved_from() {
        let (app, saved) = opened(names: MemoryPhoneStorage(), facts: MemorySavedAreasStorage())

        app.toggleShortlist(AreaFixtures.alderwick)
        app.toggleShortlist(AreaFixtures.cindermoor)
        saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))
        XCTAssertEqual(saved.entries.map(\.saved.slug), ["farrowmere", "cindermoor", "alderwick"])
        saved.move("syn-n0001", by: -2)
        app.toggleShortlist(AreaRef(Answers.profile("pellam-cross").area))

        XCTAssertEqual(
            saved.entries.map(\.saved.slug), ["pellam-cross", "alderwick", "farrowmere", "cindermoor"])
    }

    @MainActor
    func test_facts_left_behind_by_an_area_removed_while_the_app_was_closed_are_dropped() {
        let names = MemoryPhoneStorage()
        let facts = FileSavedAreasStorage(MemoryPhoneStorage())
        opened(names: names, facts: facts).saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))
        Shortlist(storage: names).remove("syn-n0006")

        let again = opened(names: names, facts: facts).saved

        XCTAssertEqual(again.kept, [:])
        XCTAssertNil(facts.written)
    }

    @MainActor
    func test_a_change_that_cannot_be_written_says_so_and_still_shows_what_was_saved() {
        let saved = opened(
            names: MemoryPhoneStorage(), facts: MemorySavedAreasStorage(refusesWrites: true)
        ).saved

        saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))

        XCTAssertTrue(saved.couldNotSave)
        XCTAssertTrue(saved.factsNotSaved)
        XCTAssertEqual(saved.entries.first?.kept?.page.said, AreaFixtures.page("farrowmere").said)
        XCTAssertFalse(saved.factsOutliveTheApp)
    }

    @MainActor
    func test_every_screen_of_one_app_is_given_the_same_saved_areas() {
        let one = AreaFixtures.app()
        let other = AreaFixtures.app()

        XCTAssertTrue(one.saved === one.saved)
        XCTAssertFalse(one.saved === other.saved)
        one.saved.add(AreaFixtures.farrowmere, page: AreaFixtures.page("farrowmere"))
        XCTAssertEqual(one.saved.entries.count, 1)
        XCTAssertEqual(other.saved.entries.count, 0)
    }

    // MARK: - Words

    func test_the_words_of_the_shortlist_are_the_kits() {
        XCTAssertEqual(ShortlistCopy.kept, "Kept on this phone. Burro does not hold it.")
        XCTAssertEqual(ShortlistCopy.empty, "No area saved yet. Save one from its page.")
        XCTAssertEqual(AreaCopy.addToShortlist, "Add to shortlist")
        XCTAssertEqual(AreaCopy.removeFromShortlist, "Remove from shortlist")
        XCTAssertEqual(AreaCopy.share, "Share")
        XCTAssertEqual(AreaCopy.shareHint, "The link is to this area's page. It holds nothing of your search.")
        XCTAssertEqual(ShortlistCopy.date(day, in: .gmt), "21 September 2026")
    }

    @MainActor
    func test_the_link_that_is_shared_is_to_the_areas_page_and_holds_nothing_of_the_search() async throws {
        let app = AreaFixtures.app()
        app.consent.choose(.allowed)
        await app.open()
        await app.search?.flow.submitText("leafy \(canary)")

        let address = try XCTUnwrap(app.site.area(AreaFixtures.farrowmere))

        XCTAssertEqual(address.absoluteString, "https://burro.example.test/synthetic/farrowmere")
        XCTAssertNil(AreaFixtures.app(site: nil).site.area(AreaFixtures.farrowmere))
    }
}
