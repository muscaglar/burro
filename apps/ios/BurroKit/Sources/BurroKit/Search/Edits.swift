import Foundation

// The edits a control sends. Each is one `Operations` with one edit in it and
// five empty arrays, as docs/design/web.md section 5.1 lists them.
//
// The app builds edits and never a spec: the API's reducer applies an edit,
// and what it returns is what the controls are drawn from. A field an edit
// has nothing to say in carries its sentinel: `unchanged`, `none`, `default`,
// `0` or `0.0`.

extension OpsGroup {
    /// The six arrays, in the order the reducer applies them.
    public static let inOrder: [OpsGroup] = [
        .budgetOps, .commuteOps, .weightOps, .tagOps, .areaOps, .settingOps,
    ]
}

extension Operations {
    /// No edit at all.
    public static let none = Operations(
        budgetOps: [], commuteOps: [], weightOps: [], tagOps: [], areaOps: [], settingOps: [])

    /// How many edits a group holds.
    public func count(in group: OpsGroup) -> Int {
        switch group {
        case .budgetOps: return budgetOps.count
        case .commuteOps: return commuteOps.count
        case .weightOps: return weightOps.count
        case .tagOps: return tagOps.count
        case .areaOps: return areaOps.count
        case .settingOps: return settingOps.count
        case .unlisted: return 0
        }
    }

    public var count: Int {
        OpsGroup.inOrder.reduce(0) { $0 + count(in: $1) }
    }

    public var isEmpty: Bool { count == 0 }

    /// The edits of this one followed by the edits of the other, group by group.
    public func merged(with other: Operations) -> Operations {
        Operations(
            budgetOps: budgetOps + other.budgetOps,
            commuteOps: commuteOps + other.commuteOps,
            weightOps: weightOps + other.weightOps,
            tagOps: tagOps + other.tagOps,
            areaOps: areaOps + other.areaOps,
            settingOps: settingOps + other.settingOps
        )
    }

    /// True when the edit at `[group][index]` takes a part of the search out.
    func takesOut(_ group: OpsGroup, _ index: Int) -> Bool {
        switch group {
        case .budgetOps: return budgetOps[safe: index]?.action == .clear
        case .commuteOps: return commuteOps[safe: index]?.action == .remove
        case .weightOps: return weightOps[safe: index]?.action == .remove
        case .tagOps: return tagOps[safe: index]?.action == .remove
        case .areaOps: return areaOps[safe: index]?.action == .clear
        case .settingOps, .unlisted: return false
        }
    }
}

extension Array {
    /// The element at a position, or `nil` where there is none. An index from
    /// the API is checked before it is used.
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}

/// A step a button takes: one small step down, or one small step up.
public enum SmallStep: Hashable, Sendable {
    case down
    case up

    var step: Step { self == .down ? .downSmall : .upSmall }
}

/// Every edit a control can make. Each says that a control made it.
public enum Edits {
    private static let byAControl = EditProvenance.uiEdit

    private static func budget(
        action: BudgetAction = .set,
        tenure: TenureChoice = .unchanged,
        amount: Int = 0,
        segment: SegmentChoice = .unchanged,
        strictness: StrictnessChoice = .unchanged,
        step: Step = .nothing
    ) -> Operations {
        let edit = BudgetEdit(
            action: action, tenure: tenure, amount: amount, segment: segment,
            strictness: strictness, step: step, provenance: byAControl)
        return Operations.none.merged(
            with: Operations(
                budgetOps: [edit], commuteOps: [], weightOps: [], tagOps: [], areaOps: [], settingOps: []))
    }

    private static func commute(
        _ placeId: String,
        action: CommuteAction = .update,
        mode: ModeChoice = .unchanged,
        maxMinutes: Int = 0,
        strictness: StrictnessChoice = .unchanged,
        step: Step = .nothing
    ) -> Operations {
        let edit = CommuteEdit(
            action: action, placeId: placeId, mode: mode, maxMinutes: maxMinutes,
            strictness: strictness, step: step, provenance: byAControl)
        return Operations(
            budgetOps: [], commuteOps: [edit], weightOps: [], tagOps: [], areaOps: [], settingOps: [])
    }

    private static func weight(
        _ featureId: FeatureId,
        action: WeightAction = .set,
        value: Double = 0,
        step: Step = .nothing,
        direction: DirectionChoice = .default
    ) -> Operations {
        let edit = WeightEdit(
            action: action, featureId: featureId, value: value, step: step,
            direction: direction, provenance: byAControl)
        return Operations(
            budgetOps: [], commuteOps: [], weightOps: [edit], tagOps: [], areaOps: [], settingOps: [])
    }

    private static func tag(
        _ tagId: TagId, action: WeightAction = .set, value: Double = 0, step: Step = .nothing
    ) -> Operations {
        let edit = TagEdit(action: action, tagId: tagId, value: value, step: step, provenance: byAControl)
        return Operations(
            budgetOps: [], commuteOps: [], weightOps: [], tagOps: [edit], areaOps: [], settingOps: [])
    }

    private static func setting(
        _ name: Setting, choice: Choice = .nothing, value: Double = 0
    ) -> Operations {
        let edit = SettingEdit(
            action: .set, setting: name, choice: choice, value: value, step: .nothing,
            provenance: byAControl)
        return Operations(
            budgetOps: [], commuteOps: [], weightOps: [], tagOps: [], areaOps: [], settingOps: [edit])
    }

    private static func area(_ areaId: String, _ action: AreaAction) -> Operations {
        let edit = AreaEdit(action: action, areaId: areaId, provenance: byAControl)
        return Operations(
            budgetOps: [], commuteOps: [], weightOps: [], tagOps: [], areaOps: [edit], settingOps: [])
    }

    public static func tenure(_ tenure: Tenure) -> Operations {
        budget(tenure: TenureChoice(rawValue: tenure.rawValue))
    }
    public static func budgetAmount(_ amount: Int) -> Operations { budget(amount: amount) }
    public static func budgetStep(_ step: SmallStep) -> Operations {
        budget(action: .nudge, step: step.step)
    }
    public static func budgetClear() -> Operations { budget(action: .clear) }
    public static func budgetSegment(_ segment: Segment) -> Operations {
        budget(segment: SegmentChoice(rawValue: segment.rawValue))
    }
    public static func budgetStrictness(_ strictness: Strictness) -> Operations {
        budget(strictness: StrictnessChoice(rawValue: strictness.rawValue))
    }
    public static func budgetWeight(_ value: Double) -> Operations {
        setting(.budgetWeight, value: value)
    }

    public static func placeAdd(_ placeId: String) -> Operations { commute(placeId, action: .add) }
    public static func placeMode(_ placeId: String, _ mode: Mode) -> Operations {
        commute(placeId, mode: ModeChoice(rawValue: mode.rawValue))
    }
    public static func placeMinutes(_ placeId: String, _ minutes: Int) -> Operations {
        commute(placeId, maxMinutes: minutes)
    }
    public static func placeStep(_ placeId: String, _ step: SmallStep) -> Operations {
        commute(placeId, step: step.step)
    }
    public static func placeStrictness(_ placeId: String, _ strictness: Strictness) -> Operations {
        commute(placeId, strictness: StrictnessChoice(rawValue: strictness.rawValue))
    }
    public static func placeRemove(_ placeId: String) -> Operations {
        commute(placeId, action: .remove)
    }

    public static func journeyCombine(_ choice: Combine) -> Operations {
        setting(.commuteCombine, choice: Choice(rawValue: choice.rawValue))
    }
    public static func journeyBasis(_ choice: PtBasis) -> Operations {
        setting(.ptBasis, choice: Choice(rawValue: choice.rawValue))
    }
    public static func journeyWeight(_ value: Double) -> Operations {
        setting(.commuteWeight, value: value)
    }

    /// A switch turned on is worth what a word is: a large step up.
    public static func featureOn(_ featureId: FeatureId) -> Operations {
        weight(featureId, action: .nudge, step: .upLarge)
    }
    public static func featureWeight(_ featureId: FeatureId, _ value: Double) -> Operations {
        weight(featureId, value: value)
    }
    /// The weight is sent as it is, because `set` always reads it.
    public static func featureDirection(
        _ featureId: FeatureId, _ value: Double, _ direction: Direction
    ) -> Operations {
        weight(featureId, value: value, direction: DirectionChoice(rawValue: direction.rawValue))
    }
    public static func featureOff(_ featureId: FeatureId) -> Operations {
        weight(featureId, action: .remove)
    }

    public static func tagOn(_ tagId: TagId) -> Operations { tag(tagId, action: .nudge, step: .upLarge) }
    public static func tagWeight(_ tagId: TagId, _ value: Double) -> Operations { tag(tagId, value: value) }
    public static func tagOff(_ tagId: TagId) -> Operations { tag(tagId, action: .remove) }

    public static func areaHide(_ areaId: String) -> Operations { area(areaId, .exclude) }
    public static func areaClear(_ areaId: String) -> Operations { area(areaId, .clear) }

    /// The answer to a question about a place or an area: the edit the
    /// question points at, copied, with the id the person picked in it.
    /// Nothing else of the edit is touched, so what the words said of the
    /// journey is kept. `nil` when the question points at no edit that takes an id.
    public static func answered(
        _ operations: Operations, _ group: OpsGroup, _ index: Int, id: String
    ) -> Operations? {
        switch group {
        case .commuteOps:
            guard let edit = operations.commuteOps[safe: index] else { return nil }
            let copy = CommuteEdit(
                action: edit.action, placeId: id, mode: edit.mode, maxMinutes: edit.maxMinutes,
                strictness: edit.strictness, step: edit.step, provenance: edit.provenance)
            return Operations(
                budgetOps: [], commuteOps: [copy], weightOps: [], tagOps: [], areaOps: [], settingOps: [])
        case .areaOps:
            guard let edit = operations.areaOps[safe: index] else { return nil }
            let copy = AreaEdit(action: edit.action, areaId: id, provenance: edit.provenance)
            return Operations(
                budgetOps: [], commuteOps: [], weightOps: [], tagOps: [], areaOps: [copy], settingOps: [])
        default:
            return nil
        }
    }
}

/// The part of the search an edit is about, as the chips name it. It holds an
/// id of the release and never anything a person typed.
public enum ChipKey: Hashable, Sendable {
    case tenure
    case budget
    case journeys
    case place(String)
    case feature(FeatureId)
    case tag(TagId)
    case area(String)
}

/// A part of the search, and what an edit itself states of it, so that it is
/// no longer an assumption.
public struct Said: Hashable, Sendable {
    public let key: ChipKey
    public let states: [AssumptionCode]

    public init(key: ChipKey, states: [AssumptionCode]) {
        self.key = key
        self.states = states
    }
}

extension Operations {
    /// Which parts of the search the edit at `[group][index]` is about.
    public func said(_ group: OpsGroup, _ index: Int) -> [Said] {
        switch group {
        case .budgetOps:
            guard let edit = budgetOps[safe: index] else { return [] }
            guard edit.action == .set else { return [Said(key: .budget, states: [])] }
            var said: [Said] = []
            if edit.tenure != .unchanged { said.append(Said(key: .tenure, states: [.tenure])) }
            var states: [AssumptionCode] = []
            if edit.segment != .unchanged { states.append(.segment) }
            if edit.strictness != .unchanged { states.append(.strictness) }
            if !states.isEmpty || edit.amount != 0 || said.isEmpty {
                said.append(Said(key: .budget, states: states))
            }
            return said
        case .commuteOps:
            guard let edit = commuteOps[safe: index] else { return [] }
            var states: [AssumptionCode] = []
            if edit.mode != .unchanged { states.append(.mode) }
            if edit.maxMinutes != 0 || (edit.action == .update && edit.step != .nothing) {
                states.append(.maxMinutes)
            }
            if edit.strictness != .unchanged { states.append(.strictness) }
            return [Said(key: .place(edit.placeId), states: states)]
        case .weightOps:
            guard let edit = weightOps[safe: index] else { return [] }
            var states: [AssumptionCode] = edit.provenance == .inferred ? [] : [.weight]
            if edit.direction != .default { states.append(.direction) }
            return [Said(key: .feature(edit.featureId), states: states)]
        case .tagOps:
            guard let edit = tagOps[safe: index] else { return [] }
            return [Said(key: .tag(edit.tagId), states: edit.provenance == .inferred ? [] : [.weight])]
        case .areaOps:
            guard let edit = areaOps[safe: index] else { return [] }
            return [Said(key: .area(edit.areaId), states: [])]
        case .settingOps:
            guard let edit = settingOps[safe: index] else { return [] }
            return [Said(key: edit.setting == .budgetWeight ? .budget : .journeys, states: [])]
        case .unlisted:
            return []
        }
    }

    /// The part an assumption of this code belongs to, for the edit it was made about.
    public func chip(_ group: OpsGroup, _ index: Int, _ code: AssumptionCode) -> ChipKey? {
        if group == .budgetOps {
            guard budgetOps[safe: index] != nil else { return nil }
            return code == .tenure ? .tenure : .budget
        }
        return said(group, index).first?.key
    }
}
