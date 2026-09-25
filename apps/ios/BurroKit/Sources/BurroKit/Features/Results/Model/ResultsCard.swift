import Foundation

// What a result card is filled from: the joins between a ranked area and the
// facts that stand behind it, and the card as a plain value for a screen to
// draw. docs/design/web.md, section 4.
//
// Nothing here writes a word about a place. It finds what the API sent. Where
// a number must become a whole one, as with a fit, it is rounded down.

extension Results {
    // MARK: - Joins

    /// The fact of the nearest station, from the area's profile.
    static func nearestStation(_ detail: AreaData?) -> Fact? {
        detail?.facts.first { $0.kind == .station && $0.template == .station }
    }

    /// The cost of the kind of home the search is for: the fact, and the figures that place the bar.
    static func cost(in detail: AreaData?, for spec: PreferenceSpec) -> (fact: Fact, estimate: CostEstimate)? {
        guard let detail else { return nil }
        let key = "\(spec.tenure.rawValue).\(spec.budget.segment.rawValue)"
        guard let fact = detail.facts.first(where: { $0.kind == .cost && $0.key == key }),
            let estimate = detail.cost.first(where: {
                $0.tenure == spec.tenure && $0.segment == spec.budget.segment
            })
        else { return nil }
        return (fact, estimate)
    }

    /// The id of a journey's fact: the area, then the place and the way of travelling.
    /// It is used to find a fact in memory, and is never drawn or put in an address.
    static func journeyFactId(_ areaId: String, _ leg: CommuteLeg) -> String {
        "\(areaId)/travel/\(leg.placeId).\(leg.mode.rawValue)"
    }

    /// The journey the fit is worked out from: the leg named first by the journey's contribution.
    static func drivingLeg(of area: RankedArea) -> CommuteLeg? {
        guard let first = area.contributions.first(where: { $0.component == "commute" })?.factIds.first
        else { return nil }
        return area.legs.first { journeyFactId(area.areaId, $0) == first }
    }

    /// The facts that give a journey its source and date. The journey's own
    /// fact where it is in hand. Otherwise any journey's: a release states
    /// the source and the date of its journeys once, for all of them. With
    /// none in hand, none, and the screen leads to the sources instead.
    static func facts(forJourney leg: CommuteLeg, of area: RankedArea, in facts: [String: Fact]) -> [Fact] {
        if let own = facts[journeyFactId(area.areaId, leg)] { return [own] }
        // The same one is found each time, whatever order the facts are held in.
        let any = facts.values.filter { $0.kind == .travel }.min { $0.factId < $1.factId }
        return any.map { [$0] } ?? []
    }

    /// Whether a journey is within the longest the person set. `nil` when there is no time to
    /// compare: one that was estimated has a band, and is never said to be within or over.
    static func within(_ leg: CommuteLeg, limit commute: Commute?) -> Bool? {
        guard let commute, leg.status != .missing, leg.status != .estimated else { return nil }
        guard leg.status != .beyondCutoff, let minutes = leg.minutes else { return false }
        return minutes <= commute.maxMinutes
    }

    /// The name of what a contribution is for: the API's label for a feature
    /// or a tag. `nil` for one this data has no name for, which is left out.
    static func label(of component: String, meta: MetaData) -> String? {
        if component == "commute" { return ResultsCopy.Breakdown.journey }
        if component == "budget" { return ResultsCopy.Breakdown.budget }
        let parts = component.split(separator: ":", maxSplits: 1).map(String.init)
        guard parts.count == 2 else { return nil }
        switch parts[0] {
        case "feature": return meta.features.first { $0.featureId.rawValue == parts[1] }?.label
        case "tag": return meta.tags.first { $0.tagId.rawValue == parts[1] }?.label
        default: return nil
        }
    }

    /// The name of each place of the search, by its id: the release's own
    /// name for it, from the answer that brought the spec. A place no answer
    /// named is said to have no name, and is never shown by a stand-in.
    static func placeNames(of state: SearchState) -> [String: String] {
        var names: [String: String] = [:]
        for commute in state.spec.commutes {
            names[commute.placeId] = state.name(ofPlace: commute.placeId) ?? ResultsCopy.Journeys.noName
        }
        return names
    }

    /// The longest journey the release holds for a way of travelling.
    static func cutoff(for mode: Mode, in cutoffs: Cutoffs) -> Int? {
        switch mode {
        case .pt: return cutoffs.pt
        case .cycle: return cutoffs.cycle
        case .walk: return cutoffs.walk
        case .unlisted: return nil
        }
    }

    // MARK: - What a card shows

    /// Something a card has, is waiting for, could not get, or knows there is none of.
    enum Loaded<Value: Hashable & Sendable>: Hashable, Sendable {
        /// It has been asked for and has not come.
        case waiting
        case here(Value)
        /// It came, and there is none: the card says so.
        case none
        /// It could not be loaded: the card says so.
        case failed
        /// There is nothing to say, and nothing is drawn.
        case hidden

        var value: Value? {
            if case .here(let value) = self { return value }
            return nil
        }
    }

    /// One sentence about a place, as the API wrote it: not reworded, not
    /// joined to another, nothing added. It ends in its source.
    struct Sentence: Hashable, Sendable {
        let text: String
        /// True for a sentence a model wrote. The card says so.
        let byModel: Bool
        let sources: [SourceLine]
    }

    struct Heading: Hashable, Sendable {
        let rank: Int
        let name: String
        let borough: String
        /// The fit, rounded down. `nil` when nothing is set to rank by.
        let fit: Int?

        var rankWords: String { ResultsCopy.Card.rank(rank) }
        var fitWords: String? { fit.map(ResultsCopy.Card.fitOf) }
        /// The heading as it is read out: the rank, the name, the borough and the fit.
        var words: String {
            let start = "\(rankWords), \(name), \(borough)"
            guard let fitWords else { return start }
            return "\(start), \(ResultsCopy.Card.fit) \(fitWords)"
        }
    }

    /// How much of what counts the area has a figure for: in words, and as a
    /// bar that draws what the words count and nothing else. It sits directly
    /// under the fit, because it says how far to trust it.
    struct Completeness: Hashable, Sendable {
        let words: String
        /// How many of the things that count have a figure, out of 100, for the bar.
        let covered: Int
        /// One line for each firm limit that could not be tested here.
        let untested: [String]
    }

    /// What the area gives up, under the word "Trade-off": the API's sentence,
    /// and beside a journey, which way it falls against the limit the person set.
    struct TradeOff: Hashable, Sendable {
        let sentence: Sentence
        /// "Within your limit" or "Over your limit", with the minutes. `nil` for what is not a journey.
        let limit: String?
        let verdict: Journey.Verdict?
    }

    /// One journey: where to, how, how long, and whether that is within the longest the person set.
    struct Journey: Hashable, Sendable {
        enum Verdict: String, Hashable, Sendable {
            case within
            case over

            var word: String { self == .within ? ResultsCopy.Journeys.within : ResultsCopy.Journeys.over }
        }

        let place: String
        let mode: String?
        /// The typical time, and the time if a service is just missed. `nil` where there is one line for both.
        let typical: String?
        let missed: String?
        /// The one line that stands for both times: beyond the longest the release holds, or no time at all.
        let whole: String?
        let verdict: Verdict?
        let limit: String?
        /// Empty when no fact of a journey is in hand: the screen leads to the sources instead.
        let sources: [SourceLine]
    }

    /// Where things sit along the bar of a cost, each as a share of its width from 0 to 100.
    struct Bar: Hashable, Sendable {
        /// `nil` for an end the cost does not have. It is drawn nowhere.
        let lower: Double?
        let median: Double
        let upper: Double?
        let budget: Double?
    }

    struct Cost: Hashable, Sendable {
        /// The range, as the API wrote each end. For a price that is one
        /// number, that number: no range is made of it.
        let range: String
        /// True for a price that is one number: a publisher's own middle price, with no range.
        let oneNumber: Bool
        /// What the one number is, and the period of sales it is of, as the API wrote it.
        let what: String?
        let soldIn: String?
        /// What is not known of a price that is one number.
        let caveat: String?
        /// True for a rent, which is said to be for a month.
        let aMonth: Bool
        /// What the figure is, in the API's word, and the kind of home it is for.
        let label: String
        let segment: String?
        let middle: String?
        /// The month the figure is as of, as the API wrote it.
        let month: String?
        let confidence: String?
        /// One to three, and none where how sure the figure is was not stated. The word
        /// says it, and the pips repeat it.
        let pips: Int
        /// The person's own budget, where one is set.
        let budget: String?
        let bar: Bar
        /// Where the budget falls, in words, so the bar holds nothing the text does not.
        let falls: String?
        let sources: [SourceLine]
    }

    /// What the data says of one thing that counts.
    ///
    /// How the area scores on the thing is never shown. For a feature that
    /// score is the percentile it is ranked by, which is never printed: where
    /// areas tie it is untrue of the release. The fact's own standing is the
    /// literal truth, and has a source.
    enum Says: Hashable, Sendable {
        /// There is no figure for it here.
        case nothing
        /// There is a figure, and the fact that holds it is not in hand to show.
        case something
        /// The slots of its fact, as the API wrote them, and the fact's source.
        case figures([Column], sources: [SourceLine])
    }

    /// One line of how the fit is worked out. Every figure is rounded down.
    struct BreakdownRow: Hashable, Sendable, Identifiable {
        let thing: String
        let weight: String
        let share: String
        let adds: String
        let says: Says

        var id: String { thing }
    }

    /// One result, as a screen draws it. The first five are in full. The
    /// rest are rows, which the API writes no reasons for.
    struct Card: Hashable, Sendable, Identifiable {
        let area: AreaRef
        /// True for one of the first five, which is drawn in full.
        let full: Bool
        let heading: Heading
        let orientation: Loaded<Sentence>
        let station: Loaded<FactShown>
        /// Up to three. Empty when the area does nothing well enough to give as a reason.
        let reasons: Loaded<[Sentence]>
        let tradeOff: Loaded<TradeOff>
        let completeness: Completeness?
        /// One sentence of the API's for each thing that has no figure here.
        let missing: Loaded<[Sentence]>
        /// How many such sentences room is held for while they are waited for.
        let held: Int
        let journeys: [Journey]
        /// With two journeys or more, which of them the fit is worked out from.
        let journeysNote: String?
        /// Where the area sits on the vibes that were asked for, and on the
        /// others the API chose. It is shown and never scored.
        let strip: [VibeShown]
        let cost: Loaded<Cost>
        let breakdown: [BreakdownRow]
        /// Why the last edit a control sent about this area was not applied.
        let refusal: RejectReason?
        let selected: Bool

        var id: String { area.areaId }
    }

    /// How many reasons a card keeps room for.
    static let reasonsShown = 3

    /// How many results are drawn in full: as many as the API gives reasons for.
    static let inFull = SearchFlow.explained

    // MARK: - Making one

    /// The facts a sentence cites, of those in hand.
    static func facts(citedBy sentence: ExplainedSentence, in facts: [String: Fact]) -> [Fact] {
        sentence.factIds.compactMap { facts[$0] }
    }

    static func sentence(_ sentence: ExplainedSentence, facts: [String: Fact]) -> Sentence {
        // The first fact cited is the one the sentence is about. Any other only names the area.
        let about = Array(Self.facts(citedBy: sentence, in: facts).prefix(1))
        return Sentence(
            text: sentence.text, byModel: sentence.origin == .model, sources: sourceLines(of: about))
    }

    static func completeness(of area: RankedArea) -> Completeness? {
        let asked = area.contributions.count
        guard asked > 0 else { return nil }
        let present = area.contributions.filter(\.present).count
        return Completeness(
            words: present == asked
                ? ResultsCopy.Completeness.all : ResultsCopy.Completeness.some(present, of: asked),
            covered: present * ResultsCopy.most / asked,
            untested: area.untestedFilters.compactMap(ResultsCopy.untested))
    }

    // MARK: - Whether a sentence may stand under the word "Trade-off"

    /// The least a thing must be worth to an area to be something the area
    /// does well: `REASON_MIN_UTILITY` of the contract, section 7.5.
    static let doesWellFrom = 0.5

    /// The thing that counts which a sentence is about: the one whose fact it cites first.
    static func part(of area: RankedArea, about sentence: ExplainedSentence) -> Contribution? {
        guard let about = sentence.factIds.first else { return nil }
        return area.contributions.first { $0.factIds.contains(about) }
    }

    /// The journey a sentence is about, where it is about one.
    static func leg(of area: RankedArea, about sentence: ExplainedSentence) -> CommuteLeg? {
        guard let about = sentence.factIds.first else { return nil }
        return area.legs.first { journeyFactId(area.areaId, $0) == about }
    }

    /// True when the sentence is about something that counts in the search
    /// and that the area does badly: it is worth less than a half, or it
    /// falls short of what was asked for. Anything else is no trade-off, and
    /// is not shown as one: the heading is the app's own word.
    ///
    /// Nothing here writes or rewords a sentence. It says whether one is
    /// shown under that heading.
    static func isGivenUp(_ area: RankedArea, _ sentence: ExplainedSentence, commutes: [Commute]) -> Bool {
        guard let part = part(of: area, about: sentence), part.present else { return false }
        if part.component == "budget", let budget = area.budget, budget.margin < 0 { return true }
        if part.component == "commute" {
            let over = area.legs.contains { leg in
                within(leg, limit: commutes.first { $0.placeId == leg.placeId }) == false
            }
            if over { return true }
        }
        return part.utility.map { $0 < doesWellFrom } ?? false
    }

    static func tradeOff(
        of explanation: Explanation, for area: RankedArea, in state: SearchState
    ) -> Loaded<TradeOff> {
        guard let given = explanation.tradeOff, isGivenUp(area, given, commutes: state.spec.commutes) else {
            return .none
        }
        var limit: String?
        var verdict: Journey.Verdict?
        if let leg = leg(of: area, about: given),
            let commute = state.spec.commutes.first(where: { $0.placeId == leg.placeId }),
            let within = within(leg, limit: commute)
        {
            verdict = within ? .within : .over
            limit =
                within
                ? ResultsCopy.Journeys.withinLimit(commute.maxMinutes)
                : ResultsCopy.Journeys.overLimit(commute.maxMinutes)
        }
        return .here(TradeOff(sentence: sentence(given, facts: state.facts), limit: limit, verdict: verdict))
    }

    /// With two journeys or more, which of them the fit is worked out from.
    static func journeysNote(of area: RankedArea, in state: SearchState) -> String? {
        guard area.legs.count >= 2 else { return nil }
        switch state.spec.commuteCombine {
        case .mean:
            return ResultsCopy.Journeys.usesMean
        case .slowest:
            guard let driver = drivingLeg(of: area), let name = placeNames(of: state)[driver.placeId] else {
                return nil
            }
            return ResultsCopy.Journeys.usesOne(name)
        case .unlisted:
            return nil
        }
    }

    static func journeys(of area: RankedArea, in state: SearchState) -> [Journey] {
        let names = placeNames(of: state)
        return area.legs.map { leg in
            let commute = state.spec.commutes.first { $0.placeId == leg.placeId }
            // By bike and on foot there is one time, and no service to miss.
            let oneTime = leg.mode != .pt
            var typical: String?
            var missed: String?
            var whole: String?
            switch leg.status {
            case .ok:
                typical = leg.minutesTypical.map(ResultsCopy.Journeys.minutes) ?? ResultsCopy.Journeys.notGiven
                missed =
                    oneTime
                    ? ResultsCopy.Journeys.notApply
                    : leg.minutesJustMissed.map(ResultsCopy.Journeys.minutes) ?? ResultsCopy.Journeys.notGiven
            case .beyondCutoff:
                whole = cutoff(for: leg.mode, in: state.meta.limits.cutoffMinutes)
                    .map(ResultsCopy.Journeys.beyond)
            case .missing:
                whole = ResultsCopy.Journeys.missing
            case .estimated:
                // No time is held. The band is said, and that it is an estimate, and no minutes.
                whole = ResultsCopy.Journeys.estimated(leg.estimate)
                    .map { "\($0). \(ResultsCopy.Journeys.estimatedFrom)" }
            case .unlisted:
                break
            }
            return Journey(
                place: names[leg.placeId] ?? "",
                mode: ResultsCopy.word(for: leg.mode),
                typical: typical,
                missed: missed,
                whole: whole,
                verdict: within(leg, limit: commute).map { $0 ? .within : .over },
                limit: commute.map { ResultsCopy.Journeys.minutes($0.maxMinutes) },
                sources: sourceLines(of: facts(forJourney: leg, of: area, in: state.facts)))
        }
    }

    /// What a bar is drawn along: the figure at its start and the figure at its end.
    struct Scale: Hashable, Sendable {
        let from: Double
        let to: Double
    }

    /// The two ends of a cost that is a range. `nil` for a cost that lacks
    /// either: it is one number, and no range is drawn for it.
    static func ends(of estimate: CostEstimate) -> (lower: Int, upper: Int)? {
        guard let lower = estimate.lowerQuartile, let upper = estimate.upperQuartile else { return nil }
        return (lower, upper)
    }

    /// One scale for several costs and a budget: from a little under the
    /// least figure among them to a little over the most. A cost that is one
    /// number counts as that number, and nothing stands in for the ends it
    /// lacks. `nil` when there is no cost to draw.
    static func scale(of estimates: [CostEstimate], budget amount: Int?) -> Scale? {
        guard !estimates.isEmpty else { return nil }
        let figures =
            estimates.flatMap { estimate in
                ends(of: estimate).map { [$0.lower, $0.upper] } ?? [estimate.median]
            } + (amount.map { [$0] } ?? [])
        let least = Double(figures.min() ?? 0)
        let most = Double(figures.max() ?? 0)
        // A little room either side, so that a mark at an end is not cut off.
        let room = max((most - least) * 0.1, 1)
        return Scale(from: least - room, to: most + room)
    }

    /// The scale the cost of every card of a list is drawn on, so that one
    /// budget is in one place on all of them and a dearer home is drawn further along.
    static func scale(of state: SearchState) -> Scale? {
        let ranked = state.ranking?.ranked.prefix(inFull) ?? []
        let costs = ranked.compactMap { cost(in: state.details[$0.areaId], for: state.spec)?.estimate }
        return scale(of: costs, budget: state.spec.budget.amount)
    }

    /// Where the ends of the range, its middle and the budget sit along the
    /// bar. Left with no scale, the bar is drawn on a scale of its own.
    static func bar(for estimate: CostEstimate, budget amount: Int?, on scale: Scale? = nil) -> Bar {
        let along = scale ?? Self.scale(of: [estimate], budget: amount) ?? Scale(from: 0, to: 1)
        let width = max(along.to - along.from, 1)
        // What a scale does not reach is drawn at its end, and never outside the bar.
        func at(_ figure: Int) -> Double {
            min(100, max(0, ((Double(figure) - along.from) / width * 1000).rounded() / 10))
        }
        return Bar(
            lower: estimate.lowerQuartile.map(at), median: at(estimate.median),
            upper: estimate.upperQuartile.map(at), budget: amount.map(at))
    }

    static func cost(
        of fact: Fact, estimate: CostEstimate, budget amount: Int?, on scale: Scale? = nil
    ) -> Cost? {
        let pound = ResultsCopy.Cost.pound
        guard let ends = ends(of: estimate) else {
            return oneNumber(of: fact, estimate: estimate, budget: amount, on: scale)
        }
        // A range with an end missing is no range, and nothing is filled in.
        guard let lower = fact.slots["lower"], let upper = fact.slots["upper"] else { return nil }
        // The fact's own word where it is one this build knows. Otherwise the estimate's.
        let said = fact.slots["confidence"].map { Confidence(rawValue: $0) }
        let confidence = said.flatMap { Confidence.allCases.contains($0) ? $0 : nil } ?? estimate.confidence
        let pips: Int
        switch confidence {
        case .high: pips = 3
        case .medium: pips = 2
        case .low: pips = 1
        case .unstated, .unlisted: pips = 0
        }
        var falls: String?
        if let amount {
            falls =
                amount < ends.lower
                ? ResultsCopy.Cost.below
                : amount > ends.upper ? ResultsCopy.Cost.above : ResultsCopy.Cost.inside
        }
        return Cost(
            range: "\(pound)\(lower) \(ResultsCopy.Cost.to) \(pound)\(upper)",
            oneNumber: false, what: nil, soldIn: nil, caveat: nil,
            aMonth: fact.template == .costRent,
            label: fact.label,
            segment: fact.slots["segment"],
            middle: fact.slots["median"].map { "\(pound)\($0)" },
            month: fact.slots["as_of"],
            confidence: ResultsCopy.word(for: confidence),
            pips: pips,
            budget: amount.map { "\(pound)\(grouped($0))" },
            bar: bar(for: estimate, budget: amount, on: scale),
            falls: falls,
            sources: sourceLines(of: [fact]))
    }

    /// A price that is one number: a publisher's own middle price, with no
    /// range. It is drawn as one number. No range is made of it, no word says
    /// how sure it is, and the line under it says what is not known of it.
    /// The figure and the period it is of are slots of the fact, as the API
    /// formatted them.
    static func oneNumber(
        of fact: Fact, estimate: CostEstimate, budget amount: Int?, on scale: Scale? = nil
    ) -> Cost? {
        let pound = ResultsCopy.Cost.pound
        guard let median = fact.slots["median"], !median.isEmpty else { return nil }
        var falls: String?
        if let amount {
            falls =
                amount < estimate.median
                ? ResultsCopy.Cost.belowMiddle
                : amount > estimate.median ? ResultsCopy.Cost.aboveMiddle : ResultsCopy.Cost.atMiddle
        }
        return Cost(
            range: "\(pound)\(median)",
            oneNumber: true, what: ResultsCopy.Cost.middleOfAll, soldIn: fact.slots["period"],
            // A price that was counted says how many sales it rests on, and what a middle
            // price means, in the API's words. A publisher's own says what is not known of it.
            caveat: fact.slots["sales"] == nil ? ResultsCopy.Cost.oneNumber : fact.slots["half_sold"],
            aMonth: false,
            label: fact.label,
            segment: fact.slots["segment"],
            middle: nil, month: nil, confidence: nil, pips: 0,
            budget: amount.map { "\(pound)\(grouped($0))" },
            bar: bar(for: estimate, budget: amount, on: scale),
            falls: falls,
            sources: sourceLines(of: [fact]))
    }

    /// What the data says of a thing that counts: the slots of the fact it names first.
    static func says(_ contribution: Contribution, facts: [String: Fact]) -> Says {
        guard contribution.present else { return .nothing }
        guard let fact = contribution.factIds.first.flatMap({ facts[$0] }), fact.kind != .missing else {
            return .something
        }
        let columns = columns(of: fact)
        return columns.isEmpty ? .something : .figures(columns, sources: sourceLines(of: [fact]))
    }

    static func breakdown(of area: RankedArea, in state: SearchState) -> [BreakdownRow] {
        area.contributions.compactMap { contribution in
            guard let thing = label(of: contribution.component, meta: state.meta) else { return nil }
            let copy = ResultsCopy.Breakdown.self
            return BreakdownRow(
                thing: thing,
                weight: copy.outOf(outOfHundred(contribution.weight)),
                share: copy.percent(hundredths(contribution.share) ?? 0),
                adds: copy.outOf(hundredths(contribution.contribution) ?? 0),
                says: says(contribution, facts: state.facts))
        }
    }

    /// One result as a screen draws it. `nil` for an area the app has no name for.
    static func card(
        for ranked: RankedArea, at position: Int, in state: SearchState, on scale: Scale? = nil
    ) -> Card? {
        guard let summary = state.area(ranked.areaId) else { return nil }
        let full = position < inFull
        let noFit = state.ranking?.emptySpec ?? false
        let heading = Heading(
            rank: ranked.rank, name: summary.name, borough: summary.borough,
            fit: noFit ? nil : fit(of: ranked.score))
        let refusal = state.refusedByPart[.area(ranked.areaId)]
        let selected = state.selectedId == ranked.areaId

        guard full else {
            return Card(
                area: AreaRef(summary), full: false, heading: heading,
                orientation: .hidden, station: .hidden, reasons: .hidden, tradeOff: .hidden,
                completeness: completeness(of: ranked), missing: .hidden, held: 0,
                journeys: journeys(of: ranked, in: state), journeysNote: journeysNote(of: ranked, in: state),
                strip: strip(of: ranked, in: state),
                cost: .hidden, breakdown: breakdown(of: ranked, in: state), refusal: refusal,
                selected: selected)
        }

        // Reasons must be for the ranking on screen.
        let explanation = state.explained ? state.explanations.first { $0.areaId == ranked.areaId } : nil
        let waitingForReasons = !state.explained && !state.explainFailed
        let detail = state.details[ranked.areaId]
        let detailFailed = state.detailFailures[ranked.areaId] != nil
        let waitingForDetail = detail == nil && !detailFailed

        let orientation: Loaded<Sentence> =
            explanation.map { .here(sentence($0.orientation, facts: state.facts)) }
            ?? (waitingForReasons ? .waiting : .hidden)
        let station: Loaded<FactShown> =
            nearestStation(detail).map { .here(row(of: $0)) } ?? (waitingForDetail ? .waiting : .hidden)
        let reasons: Loaded<[Sentence]> =
            explanation.map { .here($0.reasons.prefix(reasonsShown).map { sentence($0, facts: state.facts) }) }
            ?? (waitingForReasons ? .waiting : state.explainFailed ? .failed : .hidden)
        let tradeOff: Loaded<TradeOff> =
            explanation.map { Self.tradeOff(of: $0, for: ranked, in: state) }
            ?? (waitingForReasons ? .waiting : .hidden)
        // How many sentences there will be is known from the ranking, so their place is held.
        let without = ranked.contributions.filter { !$0.present }.count
        let said = (explanation?.missing ?? []).map { sentence($0, facts: state.facts) }
        let missing: Loaded<[Sentence]> =
            !said.isEmpty ? .here(said) : (waitingForReasons && without > 0 ? .waiting : .hidden)
        let cost: Loaded<Cost>
        if let found = Self.cost(in: detail, for: state.spec),
            let shown = Self.cost(
                of: found.fact, estimate: found.estimate, budget: state.spec.budget.amount, on: scale)
        {
            cost = .here(shown)
        } else {
            cost = waitingForDetail ? .waiting : detailFailed ? .failed : .none
        }

        return Card(
            area: AreaRef(summary), full: true, heading: heading,
            orientation: orientation, station: station, reasons: reasons, tradeOff: tradeOff,
            completeness: completeness(of: ranked), missing: missing,
            held: missing == .waiting ? without : 0,
            journeys: journeys(of: ranked, in: state), journeysNote: journeysNote(of: ranked, in: state),
            strip: strip(of: ranked, in: state),
            cost: cost, breakdown: breakdown(of: ranked, in: state), refusal: refusal, selected: selected)
    }

    /// The strip of a result: its vibes, as the API chose and ordered them.
    static func strip(of ranked: RankedArea, in state: SearchState) -> [VibeShown] {
        Vibes.strip(ranked.strip, meta: state.meta, facts: state.facts)
    }

    /// What is said once before a run of vibes of a strip: that they were
    /// asked for, or that they were not. The vibes stand in the order the API
    /// gave them. `nil` where the vibe before says the same, and before the
    /// first where nothing in the strip was asked for.
    static func group(before at: Int, in strip: [VibeShown]) -> String? {
        guard strip.indices.contains(at) else { return nil }
        let asked = strip[at].asked != nil
        if at > 0, (strip[at - 1].asked != nil) == asked { return nil }
        if asked { return VibeCopy.groupAsked }
        return at > 0 ? VibeCopy.groupAlso : nil
    }

    /// The source and the date of a vibe's band, as one line. `nil` where its fact is not in hand.
    static func sourceWords(of vibe: VibeShown) -> String? {
        guard !vibe.sources.isEmpty else { return nil }
        return "\(ResultsCopy.Source.source): " + vibe.sources.map(\.words).joined(separator: " ")
    }
}
