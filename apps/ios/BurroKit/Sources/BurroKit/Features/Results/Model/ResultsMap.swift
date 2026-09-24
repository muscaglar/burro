import Foundation

// What the map draws, and the table that says everything the map does.
// docs/design/web.md, section 6.
//
// | Shown                | By colour | And always by                                         |
// | Rank                 |           | The number in the pin, and the order of the list      |
// | Fit                  | The band  | The figure on the area, in the legend and in the list |
// | Filtered, not ranked |           | The pattern, and the reason in words                  |
// | Chosen               |           | The thick outline, the larger pin, and the card       |

extension Results {
    /// The outlines of a release, and what is worked out from them once: the
    /// frame that holds them all, and how far apart the marks of a pattern are.
    struct Ground: Hashable, Sendable {
        let outlines: [Outline]
        let whole: Frame?
        let spacing: Double

        init(_ geometry: GeometryData?) {
            outlines = Results.outlines(of: geometry)
            whole = Results.frame(of: outlines)
            spacing = Results.patternSpacing(for: outlines)
        }

        static let none = Ground(nil)

        var isEmpty: Bool { outlines.isEmpty }
    }

    /// One shape on the map, with what fills it.
    struct Region: Hashable, Sendable, Identifiable {
        let outline: Outline
        let fill: Fill
        let selected: Bool

        var id: String { outline.id }
    }

    /// What stands on a ranked area: its rank in a pin, for one of the first
    /// ten, and its fit in figures. The band is a colour. This is the figure.
    struct Mark: Hashable, Sendable, Identifiable {
        let area: AreaRef
        let at: LonLat
        /// The rank, for one of the first ten. `nil` for an area further down.
        let pin: Int?
        /// The fit, as the mark writes it. `nil` when nothing is set to rank by.
        let fit: String?
        /// The mark as it is read out: the rank, the name and the fit.
        let words: String
        let selected: Bool

        var id: String { area.areaId }
    }

    /// One line of the legend: what it stands for, and its words.
    struct LegendEntry: Hashable, Sendable, Identifiable {
        enum Sign: Hashable, Sendable {
            case band(Int)
            case land
            case lines
            case dots
            case pin
            case fit
        }

        let sign: Sign
        let words: String

        var id: String { words }
    }

    /// What the map says of the area chosen on it, in words.
    struct Chosen: Hashable, Sendable {
        let area: AreaRef
        /// Its rank and its fit, or the reason it has no rank. `nil` before any search.
        let words: String?
        /// True when the area is among the results in the list.
        let inList: Bool
        /// True when it is ranked and is further down than the list goes.
        let beyondList: Bool
    }

    /// Everything the map draws.
    struct Mapped: Hashable, Sendable {
        let regions: [Region]
        let strokes: [Stroke]
        let dots: [LonLat]
        /// How wide a dot is on the ground, in metres.
        let dotRadius: Double
        let marks: [Mark]
        let legend: [LegendEntry]
        let chosen: Chosen?
        let whole: Frame?
    }

    /// The most areas that are marked with their fit. The first of the list
    /// come first. It keeps a map of a whole city readable.
    static let mostFitMarks = 40

    /// How many metres a degree of latitude is, near enough for the width of a dot.
    static let metresInADegree = 111_320.0

    // MARK: - Words for one area

    /// Where an area stands in a ranking: its place in the order, and its fit.
    struct Standing: Hashable, Sendable {
        let rank: Int
        /// The fit out of 100, rounded down. `nil` when nothing is set to rank by.
        let fit: Int?
    }

    /// The standing of each ranked area, by its id. The order of the scores is the rank.
    static func standings(_ ranking: Ranking?) -> [String: Standing] {
        guard let ranking else { return [:] }
        var found: [String: Standing] = [:]
        for (at, score) in ranking.scores.enumerated() where found[score.areaId] == nil {
            found[score.areaId] = Standing(rank: at + 1, fit: ranking.emptySpec ? nil : fit(of: score.score))
        }
        return found
    }

    /// Why an area has no rank, in words. `nil` for an area that has one, or that nothing is said of.
    static func reason(for areaId: String, in ranking: Ranking?) -> String? {
        guard let ranking else { return nil }
        if let left = ranking.filtered.first(where: { $0.areaId == areaId }) {
            return ResultsCopy.word(for: left.reason)
        }
        if let not = ranking.unranked.first(where: { $0.areaId == areaId }) {
            return ResultsCopy.word(for: not.reason)
        }
        return nil
    }

    static func words(for standing: Standing, area name: String) -> String {
        guard let fit = standing.fit else { return ResultsCopy.Map.pinNoFit(rank: standing.rank, area: name) }
        return ResultsCopy.Map.pin(rank: standing.rank, area: name, fit: ResultsCopy.Card.fitOf(fit))
    }

    // MARK: - Making the map

    static func legend(for ranking: Ranking?) -> [LegendEntry] {
        guard let ranking else {
            return [LegendEntry(sign: .land, words: ResultsCopy.Legend.noScore)]
        }
        var entries: [LegendEntry] = []
        if ranking.emptySpec || ranking.scores.isEmpty {
            entries.append(LegendEntry(sign: .land, words: ResultsCopy.Legend.noScore))
        } else {
            for band in bands.reversed() {
                entries.append(
                    LegendEntry(
                        sign: .band(band.number),
                        words: "\(ResultsCopy.Legend.fit) \(ResultsCopy.Legend.band(from: band.from, to: band.to))"))
            }
        }
        entries.append(LegendEntry(sign: .lines, words: ResultsCopy.Legend.filtered))
        entries.append(LegendEntry(sign: .dots, words: ResultsCopy.Legend.unranked))
        if !ranking.emptySpec && !ranking.scores.isEmpty {
            entries.append(LegendEntry(sign: .pin, words: ResultsCopy.Legend.pin))
            entries.append(LegendEntry(sign: .fit, words: ResultsCopy.Legend.fitLabel))
        }
        return entries
    }

    static func marks(of state: SearchState) -> [Mark] {
        guard let ranking = state.ranking, !ranking.emptySpec else { return [] }
        let standings = standings(ranking)
        var marks: [Mark] = []
        for (at, score) in ranking.scores.enumerated() {
            let chosen = state.selectedId == score.areaId
            // Beyond the first of them only the area that was chosen is marked.
            guard at < mostFitMarks || chosen else { continue }
            guard let summary = state.area(score.areaId), let standing = standings[score.areaId] else {
                continue
            }
            marks.append(
                Mark(
                    area: AreaRef(summary), at: summary.centroid,
                    pin: at < pins ? standing.rank : nil,
                    fit: standing.fit.map(ResultsCopy.Map.fitLabel),
                    words: words(for: standing, area: summary.name),
                    selected: chosen))
        }
        return marks
    }

    static func chosen(of state: SearchState) -> Chosen? {
        guard let areaId = state.selectedId, let summary = state.area(areaId) else { return nil }
        let standing = standings(state.ranking)[areaId]
        let inList = state.ranking?.ranked.contains { $0.areaId == areaId } ?? false
        let words: String?
        if let standing {
            let rank = ResultsCopy.Card.rank(standing.rank)
            words =
                standing.fit.map {
                    "\(rank), \(ResultsCopy.Card.fit.lowercased()) \(ResultsCopy.Card.fitOf($0))"
                } ?? rank
        } else {
            words = reason(for: areaId, in: state.ranking)
                ?? (summary.rankable ? nil : ResultsCopy.word(for: UnrankedReason.notRankable))
        }
        return Chosen(
            area: AreaRef(summary), words: words, inList: inList, beyondList: standing != nil && !inList)
    }

    static func mapped(_ state: SearchState, on ground: Ground) -> Mapped {
        let fills = fills(state.ranking)
        var strokes: [Stroke] = []
        var dots: [LonLat] = []
        var regions: [Region] = []
        for outline in ground.outlines {
            let fill = fills[outline.areaId] ?? .land
            regions.append(Region(outline: outline, fill: fill, selected: state.selectedId == outline.areaId))
            switch fill.pattern {
            case .none: break
            case .filtered: strokes += lines(across: outline, spacing: ground.spacing)
            case .unranked: dots += Self.dots(in: outline, spacing: ground.spacing)
            }
        }
        // The chosen area is drawn last, so that its thick edge is over its neighbours'.
        let inOrder = regions.filter { !$0.selected } + regions.filter(\.selected)
        return Mapped(
            regions: inOrder, strokes: strokes, dots: dots,
            dotRadius: ground.spacing * metresInADegree / 8,
            marks: marks(of: state), legend: legend(for: state.ranking),
            chosen: chosen(of: state), whole: ground.whole)
    }

    // MARK: - The table of every area

    /// One area of the release, with everything the map says of it.
    struct AreaRow: Hashable, Sendable, Identifiable {
        let area: AreaRef
        let rank: Int?
        let fit: Int?
        /// In words: ranked, or why not.
        let status: String
        let selected: Bool

        var id: String { area.areaId }

        var rankWords: String { rank.map(String.init) ?? ResultsCopy.Table.none }
        var fitWords: String { fit.map(ResultsCopy.Card.fitOf) ?? ResultsCopy.Table.none }
        /// The row as it is read out.
        var words: String {
            var said = [area.name, area.borough]
            if let rank { said.append(ResultsCopy.Card.rank(rank)) }
            if let fit { said.append("\(ResultsCopy.Card.fit) \(ResultsCopy.Card.fitOf(fit))") }
            said.append(status)
            return said.joined(separator: ", ")
        }
    }

    struct Tabled: Hashable, Sendable {
        let caption: String
        let rows: [AreaRow]
    }

    /// True when one area comes before another by its name, as a reader here would order them.
    static func byName(_ one: AreaRef, _ other: AreaRef) -> Bool {
        let order = one.name.compare(
            other.name, options: [.caseInsensitive, .diacriticInsensitive], range: nil,
            locale: Locale(identifier: "en_GB"))
        return order == .orderedSame ? one.areaId < other.areaId : order == .orderedAscending
    }

    /// Every area of the release, with its rank, its fit, and in words why it
    /// has none. In rank order, and then by name.
    static func tabled(_ state: SearchState) -> Tabled {
        let ranking = state.ranking
        let standings = standings(ranking)
        let searched = ranking != nil
        var rows = state.areas.map { area -> AreaRow in
            let selected = state.selectedId == area.areaId
            if let standing = standings[area.areaId] {
                return AreaRow(
                    area: AreaRef(area), rank: standing.rank, fit: standing.fit,
                    status: ResultsCopy.Table.ranked, selected: selected)
            }
            let status =
                reason(for: area.areaId, in: ranking)
                ?? (!area.rankable
                    ? ResultsCopy.word(for: UnrankedReason.notRankable) ?? ResultsCopy.Table.none
                    : searched ? ResultsCopy.Table.none : ResultsCopy.Table.notYet)
            return AreaRow(area: AreaRef(area), rank: nil, fit: nil, status: status, selected: selected)
        }
        rows.sort { one, other in
            switch (one.rank, other.rank) {
            case (let first?, let second?): return first < second
            case (.some, nil): return true
            case (nil, .some): return false
            case (nil, nil):
                return byName(one.area, other.area)
            }
        }
        return Tabled(
            caption: searched ? ResultsCopy.Table.caption : ResultsCopy.Table.captionEmpty, rows: rows)
    }
}
