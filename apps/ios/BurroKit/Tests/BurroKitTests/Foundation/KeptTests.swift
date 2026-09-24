import XCTest

@testable import BurroKit

/// What is kept on the phone: a shortlist and a choice, and nothing of a search.
final class KeptTests: XCTestCase {
    private let farrowmere = AreaRef(
        areaId: "syn-n0006", slug: "farrowmere", name: "Farrowmere", borough: "Quillhaven")
    private let alderwick = AreaRef(
        areaId: "syn-n0001", slug: "alderwick", name: "Alderwick", borough: "Quillhaven")
    private let day = Date(timeIntervalSince1970: 1_790_000_000)

    private func written(_ storage: any PhoneStorage, _ file: KeptFile) throws -> [String: JSON] {
        guard case .object(let fields) = try JSON.read(XCTUnwrap(storage.read(file))) else {
            throw CocoaError(.fileReadCorruptFile)
        }
        return fields
    }

    // MARK: - The shortlist

    @MainActor
    func test_the_shortlist_is_empty_until_an_area_is_saved() {
        let shortlist = Shortlist(storage: MemoryPhoneStorage())

        XCTAssertEqual(shortlist.entries, [])
        XCTAssertFalse(shortlist.contains("syn-n0006"))
        XCTAssertFalse(shortlist.holdsSynthetic)
    }

    @MainActor
    func test_a_saved_area_is_there_when_the_app_is_opened_again() {
        let storage = MemoryPhoneStorage()
        let shortlist = Shortlist(storage: storage, now: { self.day })
        shortlist.add(farrowmere, synthetic: true)
        shortlist.add(alderwick, synthetic: true)

        let reopened = Shortlist(storage: storage)

        XCTAssertEqual(reopened.entries.map(\.areaId), ["syn-n0001", "syn-n0006"])
        XCTAssertEqual(reopened.entries.map(\.savedOn), [day, day])
        XCTAssertEqual(reopened.entries.last?.area, farrowmere)
        XCTAssertTrue(reopened.holdsSynthetic)
        XCTAssertFalse(shortlist.couldNotSave)
    }

    @MainActor
    func test_saving_an_area_twice_keeps_it_once() {
        let shortlist = Shortlist(storage: MemoryPhoneStorage(), now: { self.day })

        shortlist.add(farrowmere, synthetic: true)
        shortlist.add(farrowmere, synthetic: true)

        XCTAssertEqual(shortlist.entries.count, 1)
    }

    @MainActor
    func test_an_area_that_is_removed_is_gone_from_the_phone() throws {
        let storage = MemoryPhoneStorage()
        let shortlist = Shortlist(storage: storage, now: { self.day })
        shortlist.add(farrowmere, synthetic: true)
        shortlist.add(alderwick, synthetic: true)

        shortlist.remove("syn-n0006")
        XCTAssertEqual(Shortlist(storage: storage).entries.map(\.areaId), ["syn-n0001"])
        XCTAssertFalse(
            String(decoding: try XCTUnwrap(storage.read(.shortlist)), as: UTF8.self).contains("Farrowmere"))

        shortlist.removeAll()
        XCTAssertNil(storage.read(.shortlist))
        XCTAssertEqual(Shortlist(storage: storage).entries, [])
    }

    @MainActor
    func test_the_shortlist_holds_ids_names_and_the_date_and_nothing_of_the_search() throws {
        let storage = MemoryPhoneStorage()
        Shortlist(storage: storage, now: { self.day }).add(farrowmere, synthetic: true)

        let kept = try written(storage, .shortlist)

        XCTAssertEqual(Set(kept.keys), ["version", "entries"])
        guard case .array(let entries) = kept["entries"], case .object(let entry) = entries.first else {
            return XCTFail("The shortlist holds no list of areas.")
        }
        XCTAssertEqual(Set(entry.keys), ["area_id", "slug", "name", "borough", "saved_on", "synthetic"])
        XCTAssertEqual(entry["saved_on"], .string("2026-09-21T14:13:20Z"))
        let fields = Mirror(reflecting: ShortlistEntry(
            areaId: "", slug: "", name: "", borough: "", savedOn: day, synthetic: true)
        ).children.compactMap(\.label)
        XCTAssertEqual(fields, ["areaId", "slug", "name", "borough", "savedOn", "synthetic"])
    }

    @MainActor
    func test_a_shortlist_that_cannot_be_written_says_so_and_still_shows_what_was_saved() {
        let shortlist = Shortlist(storage: MemoryPhoneStorage(refusesWrites: true))

        shortlist.add(farrowmere, synthetic: true)

        XCTAssertTrue(shortlist.couldNotSave)
        XCTAssertTrue(shortlist.contains("syn-n0006"))
    }

    @MainActor
    func test_a_file_that_is_not_a_shortlist_is_read_as_an_empty_one() {
        let storage = MemoryPhoneStorage([.shortlist: Data("not a shortlist".utf8)])

        XCTAssertEqual(Shortlist(storage: storage).entries, [])
    }

    // MARK: - The choice

    @MainActor
    func test_until_the_person_has_chosen_no_sentence_may_be_sent() {
        let consent = Consent(storage: MemoryPhoneStorage())

        XCTAssertNil(consent.choice)
        XCTAssertFalse(consent.mayReadWords)
    }

    @MainActor
    func test_the_choice_is_there_when_the_app_is_opened_again_and_can_be_changed() {
        let storage = MemoryPhoneStorage()
        let consent = Consent(storage: storage)

        consent.choose(.allowed)
        XCTAssertTrue(Consent(storage: storage).mayReadWords)
        consent.choose(.settingsOnly)
        XCTAssertEqual(Consent(storage: storage).choice, .settingsOnly)
        XCTAssertFalse(Consent(storage: storage).mayReadWords)
        consent.forget()
        XCTAssertNil(Consent(storage: storage).choice)
        XCTAssertNil(storage.read(.consent))
    }

    @MainActor
    func test_the_choice_holds_a_word_and_nothing_else() throws {
        let storage = MemoryPhoneStorage()
        Consent(storage: storage).choose(.allowed)

        let kept = try written(storage, .consent)

        XCTAssertEqual(Set(kept.keys), ["version", "choice"])
        XCTAssertEqual(kept["choice"], .string("allowed"))
    }

    @MainActor
    func test_a_choice_that_cannot_be_written_still_holds_while_the_app_is_open() {
        let consent = Consent(storage: MemoryPhoneStorage(refusesWrites: true))

        consent.choose(.allowed)

        XCTAssertTrue(consent.mayReadWords)
        XCTAssertTrue(consent.couldNotSave)
    }

    // MARK: - Where it is kept

    func test_three_things_are_kept_on_the_phone_and_no_more() throws {
        XCTAssertEqual(
            KeptFile.allCases.map(\.fileName), ["shortlist.json", "consent.json", "saved-areas.json"])
        // Each is in the table that says what is kept, so that nothing is kept unsaid.
        let guide = try Repository.text(Repository.ios.appendingPathComponent("AGENTS.md"))
        for file in KeptFile.allCases { XCTAssertTrue(guide.contains("| `\(file.fileName)` |"), file.fileName) }
    }

    func test_each_thing_is_one_file_in_the_apps_own_folder_left_out_of_backups() throws {
        let folder = FileManager.default.temporaryDirectory
            .appendingPathComponent("burro-kept-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: folder) }
        let storage = FilePhoneStorage(folder: folder)

        XCTAssertNil(storage.read(.shortlist))
        try storage.write(Data("{}".utf8), to: .shortlist)
        try storage.write(Data("[]".utf8), to: .consent)

        XCTAssertEqual(storage.read(.shortlist), Data("{}".utf8))
        XCTAssertEqual(
            try FileManager.default.contentsOfDirectory(atPath: folder.path).sorted(),
            ["consent.json", "shortlist.json"])
        XCTAssertEqual(try folder.resourceValues(forKeys: [.isExcludedFromBackupKey]).isExcludedFromBackup, true)
        try storage.remove(.shortlist)
        try storage.remove(.shortlist)
        XCTAssertNil(storage.read(.shortlist))
    }
}
