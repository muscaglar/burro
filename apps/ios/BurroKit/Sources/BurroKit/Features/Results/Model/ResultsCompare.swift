import Foundation
import Observation

// Comparing two to four areas: the areas a person chose, and the table that
// sets them side by side. docs/design/web.md, section 2.
//
// A comparison shows a fact's slots and never a cell's numbers. A cell holds
// a value, a percentile, a utility and a contribution as numbers. The screen
// shows the slots of the fact the cell cites, as the API formatted them, and
// the contribution rounded down. It never shows the value, which is the same
// figure unformatted, nor the percentile, nor the utility.

extension Results {
    /// The fewest and the most areas a comparison takes. The API refuses any other number.
    static let leastCompared = 2
    static let mostCompared = 4

    /// True when the list holds as many areas as a comparison takes.
    static func isFull(_ chosen: [AreaRef]) -> Bool { chosen.count >= mostCompared }

    /// True when the list holds enough areas to compare.
    static func isEnough(_ chosen: [AreaRef]) -> Bool {
        chosen.count >= leastCompared && chosen.count <= mostCompared
    }

    /// The list with the area taken out if it was in, and put in if it was not and there is room.
    static func toggled(_ chosen: [AreaRef], _ area: AreaRef) -> [AreaRef] {
        if chosen.contains(where: { $0.areaId == area.areaId }) {
            return chosen.filter { $0.areaId != area.areaId }
        }
        return isFull(chosen) ? chosen : chosen + [area]
    }

    /// The tray that holds the areas chosen: what it says, and whether it can go.
    struct Tray: Hashable, Sendable {
        let areas: [AreaRef]
        /// What the tray says of itself. `nil` when two or three are chosen and there is nothing to say.
        let words: String?
        /// The words of the button that compares. `nil` with too few to compare.
        let go: String?
        let full: Bool
    }

    static func tray(_ chosen: [AreaRef]) -> Tray {
        let words: String?
        switch chosen.count {
        case 0: words = ResultsCopy.Tray.none
        case 1: words = ResultsCopy.Tray.one
        case mostCompared...: words = ResultsCopy.Tray.full
        default: words = nil
        }
        return Tray(
            areas: chosen, words: words,
            go: isEnough(chosen) ? ResultsCopy.Tray.go(chosen.count) : nil, full: isFull(chosen))
    }

    // MARK: - The table

    /// One of the areas compared: its name, its status in words, and where it stands in the search.
    struct ComparedPlace: Hashable, Sendable, Identifiable {
        let areaId: String
        /// What leads to its page. `nil` for an area the app has no slug for.
        let area: AreaRef?
        let name: String
        let status: String?
        /// Its rank and its fit in the search that is open. `nil` with no search, or when it has no rank.
        let standing: String?

        var id: String { areaId }
    }

    /// What one area has for one thing that counts.
    struct ComparedCell: Hashable, Sendable, Identifiable {
        let areaId: String
        let area: String
        /// Each figure under the name of its column, as the API wrote it.
        let columns: [Column]
        let adds: String?
        /// What is said where there is no figure to show.
        let none: String?
        let sources: [SourceLine]

        var id: String { areaId }
    }

    /// One thing that counts, and how each area does on it.
    struct ComparedRow: Hashable, Sendable, Identifiable {
        let component: String
        let label: String
        let countsFor: String
        /// The caveat that goes with a figure of recorded crime.
        let caveat: String?
        let cells: [ComparedCell]

        var id: String { component }
    }

    struct Compared: Hashable, Sendable {
        /// What the areas are compared on: the search that is open, or the usual settings.
        let basis: String?
        let places: [ComparedPlace]
        /// In the order the API gave them, which is the order of the weights from high to low.
        let rows: [ComparedRow]

        /// True when nothing is set to count, so there is nothing to compare the areas on.
        var nothingCounts: Bool { rows.isEmpty }
    }

    /// What the comparison is made on, in words.
    static func basis(of state: SearchState) -> String? {
        if !state.untouched { return ResultsCopy.Compare.fromSearch }
        switch state.spec.tenure {
        case .rent: return ResultsCopy.Compare.fromDefaultsRent
        case .buy: return ResultsCopy.Compare.fromDefaultsBuy
        case .unlisted: return nil
        }
    }

    static func compared(_ data: CompareData, in state: SearchState) -> Compared {
        let facts = Dictionary(data.facts.map { ($0.factId, $0) }, uniquingKeysWith: { first, _ in first })
        // Where an area stands is shown only from a search, and only when its
        // ranking is of the spec that was sent.
        let standings =
            !state.untouched && state.rankedHash != nil && state.rankedHash == state.specHash
            ? Self.standings(state.ranking) : [:]

        let places = data.areas.map { area in
            ComparedPlace(
                areaId: area.areaId,
                area: state.area(area.areaId).map { AreaRef($0) },
                name: area.name,
                status: ResultsCopy.word(for: area.status),
                standing: area.status == .ranked
                    ? standings[area.areaId].map { ResultsCopy.CompareTable.standing(rank: $0.rank, fit: $0.fit) }
                    : nil)
        }

        let rows = data.rows.map { row in
            let cited = row.cells.compactMap { $0.factId.flatMap { facts[$0] } }
            return ComparedRow(
                component: row.component,
                label: row.label,
                countsFor: ResultsCopy.CompareTable.countsFor(outOfHundred(row.weight)),
                caveat: cited.contains { $0.template == .featureCrime } ? ResultsCopy.crimeCaveat : nil,
                cells: data.areas.map { area in
                    let cell = row.cells.first { $0.areaId == area.areaId }
                    let fact = cell?.factId.flatMap { facts[$0] }
                    let columns = fact.map { $0.template == .missing ? [] : Self.columns(of: $0) } ?? []
                    guard let fact, !columns.isEmpty else {
                        let notScored = cell == nil || (cell?.factId == nil && area.status != .ranked)
                        return ComparedCell(
                            areaId: area.areaId, area: area.name, columns: [], adds: nil,
                            none: notScored
                                ? ResultsCopy.CompareTable.notScored : ResultsCopy.CompareTable.noFigure,
                            sources: [])
                    }
                    return ComparedCell(
                        areaId: area.areaId, area: area.name, columns: columns,
                        adds: hundredths(cell?.contribution).map(ResultsCopy.CompareTable.adds),
                        none: nil, sources: sourceLines(of: [fact]))
                })
        }
        return Compared(basis: basis(of: state), places: places, rows: rows)
    }

    // MARK: - Asking for one

    /// A comparison that was asked for: waited for, answered, or failed.
    enum Comparing: Hashable, Sendable {
        case waiting
        case here(Compared)
        case failed(words: String, requestId: String?)
    }

    /// What names a comparison: the areas, and the search they are compared
    /// on. An answer to an older question is never shown for a newer one.
    static func question(_ chosen: [AreaRef], of state: SearchState) -> String {
        let areas = chosen.map(\.areaId).joined(separator: " ")
        let search = state.specHash ?? "default \(state.spec.tenure.rawValue)"
        return "\(areas) \(search) \(state.answers)"
    }

    /// Asks for a comparison and holds its answer. It is held in memory, by
    /// the screen that shows it, and asks again when what it was asked changes.
    @MainActor
    @Observable
    final class Comparison {
        private(set) var answer: Comparing = .waiting
        @ObservationIgnored private var asked: String?
        @ObservationIgnored private var attempt = 0

        /// Asks, unless this very question was asked last and has been answered.
        func ask(_ chosen: [AreaRef], of store: SearchStore, again: Bool = false) async {
            guard isEnough(chosen) else { return }
            if again { attempt += 1 }
            let question = "\(Results.question(chosen, of: store.state)) \(attempt)"
            guard question != asked else { return }
            asked = question
            answer = .waiting
            let answered = await store.flow.compare(areaIds: chosen.map(\.areaId))
            // A newer question was asked while this one was out.
            guard asked == question else { return }
            switch answered {
            case .success(let compared):
                answer = .here(Results.compared(compared.data, in: store.state))
            case .failure(let failure):
                answer = .failed(words: ShellCopy.words(for: failure), requestId: failure.requestId)
            }
        }
    }
}
