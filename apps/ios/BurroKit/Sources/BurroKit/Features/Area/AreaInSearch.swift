import Foundation

/// What the search that is open says of one area: where it stands, and the
/// sentences the API wrote about why.
///
/// It is read from the search's state each time the screen is drawn. It is
/// never kept: a rank and a fit depend on what a person asked for, and on the
/// places they named.
public struct AreaInSearch: Hashable, Sendable {
    /// One sentence of the API's, with the source and the date of what it says.
    public struct Said: Hashable, Sendable, Identifiable {
        public let text: String
        public let sources: [SourceLine]
        /// True when a model wrote the sentence. The screen then says so.
        public let byModel: Bool
        public let id: Int

        public var sourceWords: String? {
            guard !sources.isEmpty else { return nil }
            return "\(AreaCopy.Source.source): " + sources.map(\.words).joined(separator: " ")
        }
    }

    /// The most a fit can be.
    public static let most = 100

    public let rank: Int
    /// The fit as a whole number, rounded down. `nil` when nothing is set to
    /// rank by: every area then scores nothing, and none has a fit.
    public let fit: Int?
    /// True when the reasons on hand are for the ranking on screen, and one of them is for this area.
    public let explained: Bool
    public let orientation: Said?
    public let reasons: [Said]
    public let tradeOff: Said?

    /// What the state says of an area. `nil` when no ranking is open, or the
    /// ranking does not rank the area.
    public init?(_ state: SearchState, areaId: String) {
        guard let ranking = state.ranking,
            let at = ranking.scores.firstIndex(where: { $0.areaId == areaId })
        else { return nil }
        rank = ranking.ranked.first { $0.areaId == areaId }?.rank ?? at + 1
        fit = ranking.emptySpec ? nil : Self.roundedDown(ranking.scores[at].score)

        // Reasons must be for the ranking on screen.
        guard state.explained, let explanation = state.explanations.first(where: { $0.areaId == areaId })
        else {
            explained = false
            orientation = nil
            reasons = []
            tradeOff = nil
            return
        }
        func said(_ sentence: ExplainedSentence, _ id: Int) -> Said {
            Said(
                text: sentence.text,
                sources: SourceLines.of(sentence.factIds.prefix(1).compactMap { state.facts[$0] }),
                byModel: sentence.origin == .model, id: id)
        }
        explained = true
        orientation = said(explanation.orientation, 0)
        reasons = explanation.reasons.enumerated().map { said($1, $0 + 1) }
        tradeOff = explanation.tradeOff.map { said($0, -1) }
    }

    /// A fit is rounded down, so that it is never said to be more than it is.
    /// It is rounded as the results round it, so that one area has one fit on every screen.
    public static func roundedDown(_ score: Double) -> Int? {
        guard score.isFinite else { return nil }
        return min(most, max(0, Int(score.rounded(.down))))
    }

    /// "Rank 1, fit 80 of 100", or the rank alone when there is no fit.
    public var standing: String {
        guard let fit else { return AreaCopy.InSearch.rank(rank) }
        return AreaCopy.InSearch.rankAndFit(rank: rank, fit: fit, of: Self.most)
    }
}
