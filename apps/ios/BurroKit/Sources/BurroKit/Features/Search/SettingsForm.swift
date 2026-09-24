import Foundation

// What the settings offer, worked out from the release and the spec. The form
// offers only what the release can rank, within the limits the API served, so
// it never offers what the reducer would refuse. docs/design/web.md section 5.1.
//
// Every control ends in one call to `Edits`, which builds the one edit it
// sends. The app builds edits and never a spec.

enum SettingsForm {
    /// The kinds of home that go with each tenure, in the order a form lists
    /// them. The contract names the kinds and the API refuses a kind that does
    /// not suit the tenure. No route lists which suit which (web.md section 13,
    /// gap 8), so they are held here, and a test holds them to the cost
    /// figures the API serves.
    static func segments(for tenure: Tenure) -> [Segment] {
        switch tenure {
        case .rent: return [.room, .studio, .bed1, .bed2, .bed3, .bed4plus]
        case .buy: return [.flat, .terraced, .semiDetached, .detached]
        case .unlisted: return []
        }
    }

    static let tenures: [Tenure] = [.rent, .buy]
    static let modes: [Mode] = [.pt, .cycle, .walk]
    static let combines: [Combine] = [.slowest, .mean]
    static let bases: [PtBasis] = [.typical, .justMissed]
    static let directions: [Direction] = [.more, .less]

    /// One group of features: a dimension, by the app's word for it.
    struct Group: Hashable, Sendable, Identifiable {
        let dimension: Dimension
        let title: String
        let features: [Metric]
        var id: String { dimension.rawValue }
    }

    /// The features that can be ranked, grouped by dimension, in the order
    /// they are shown. Recorded crime is not among them: it is its own group,
    /// closed and off at first. A dimension with nothing in it is left out.
    static func groups(_ meta: MetaData) -> [Group] {
        CodeCopy.dimensionOrder
            .filter { $0 != .crime }
            .compactMap { group($0, meta) }
    }

    /// Recorded crime, where the release can rank it.
    static func crime(_ meta: MetaData) -> Group? {
        group(.crime, meta)
    }

    private static func group(_ dimension: Dimension, _ meta: MetaData) -> Group? {
        let features = meta.features.filter { $0.rankable && $0.dimension == dimension }
        guard !features.isEmpty, let title = CodeCopy.dimension(dimension) else { return nil }
        return Group(dimension: dimension, title: title, features: features)
    }

    /// What a switch sends when it is turned.
    static func feature(_ featureId: FeatureId, on: Bool) -> Operations {
        on ? Edits.featureOn(featureId) : Edits.featureOff(featureId)
    }

    static func tag(_ tagId: TagId, on: Bool) -> Operations {
        on ? Edits.tagOn(tagId) : Edits.tagOff(tagId)
    }

    /// Which way counts as better, with the weight as it stands.
    static func direction(_ featureId: FeatureId, _ direction: Direction, weight: Double) -> Operations {
        Edits.featureDirection(featureId, weight, direction)
    }

    static func firm(_ firm: Bool) -> Strictness {
        firm ? .hard : .soft
    }

    /// The limits of the budget, as the hint under its field says them.
    static func budgetHint(_ tenure: Tenure, _ limits: ServedLimits) -> String {
        let scale = AmountScale.budget(tenure, limits)
        return SettingsCopy.Budget.between(FormNumbers.grouped(scale.least), FormNumbers.grouped(scale.most))
    }

    static func minutesHint(_ mode: Mode, _ limits: ServedLimits) -> String {
        let scale = AmountScale.minutes(mode, limits)
        return SettingsCopy.Journey.between(scale.least, scale.most)
    }

    /// What the button for a hidden area, or for the one area that is shown, says.
    static func show(_ rule: AreaRule, in state: SearchState) -> String? {
        let name = state.area(rule.areaId)?.name ?? rule.areaId
        switch rule.rule {
        case .exclude: return SettingsCopy.Hidden.show(name)
        case .only: return SettingsCopy.Hidden.only(name)
        case .unlisted: return nil
        }
    }

    /// Why the last edit to a part was not taken, in words. Only what a control
    /// sent is said at the control.
    static func problem(_ key: ChipKey, in state: SearchState) -> String? {
        state.refusedByPart[key].flatMap(SearchCopy.rejected)
    }
}
