import SwiftUI

// The controls of the settings. A chip opens the same control, in place.
//
// Each is drawn from the spec the API last returned. Between being changed
// and being answered it shows what it was set to. Each change is one edit,
// built by `Edits` and handed to `send`: a control never touches the spec.

/// What every control is given: the search as it stands, and the way to send an edit.
struct ControlContext {
    let state: SearchState
    let send: (Operations) -> Void

    var spec: PreferenceSpec { state.spec }
    var limits: ServedLimits { state.meta.limits }
    /// Changes with every answer from the API.
    var version: Int { state.answers }

    func problem(_ key: ChipKey) -> String? {
        SettingsForm.problem(key, in: state)
    }
}

/// Renting or buying. Before anything is asked for, the choice swaps in the
/// other default the API served, and sends nothing. After, it is an edit like any other.
struct TenureControl: View {
    let tenure: Tenure
    let version: Int
    let problem: String?
    let choose: (Tenure) -> Void

    @State private var draft = Draft<Tenure>()

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s1) {
            ChoiceList(
                SearchCopy.TenureChoice.legend,
                choices: SettingsForm.tenures.map { ($0, CodeCopy.tenure($0)) },
                chosen: draft.shown(tenure, at: version)
            ) { chosen in
                draft.set(chosen, at: version)
                choose(chosen)
            }
            if let problem { ProblemLine(problem) }
        }
    }
}

/// What a person can pay, for what kind of home, and how much that counts.
struct BudgetControl: View {
    let context: ControlContext

    @State private var segment = Draft<Segment>()
    @State private var firm = Draft<Bool>()

    var body: some View {
        let budget = context.spec.budget
        let tenure = context.spec.tenure
        let version = context.version
        let kinds = SettingsForm.segments(for: tenure)
        FormGroup(SettingsCopy.Budget.legend) {
            if context.state.meta.holds.costs {
                amount(budget, tenure, version)
            } else {
                // The data holds no cost to test a budget against. The kind of home is kept.
                HintLine(SettingsCopy.Budget.notInData)
            }

            if !kinds.isEmpty {
                VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                    Text(SettingsCopy.Budget.segment)
                        .font(Tokens.Text.secondary.weight(.semibold))
                        .foregroundStyle(Tokens.Colour.text)
                        .accessibilityHidden(true)
                    Picker(
                        SettingsCopy.Budget.segment,
                        selection: Binding(
                            get: { segment.shown(budget.segment, at: version) },
                            set: { chosen in
                                guard kinds.contains(chosen), chosen != budget.segment else { return }
                                segment.set(chosen, at: version)
                                context.send(Edits.budgetSegment(chosen))
                            })
                    ) {
                        ForEach(kinds, id: \.self) { kind in
                            if let word = CodeCopy.segment(kind) {
                                Text(word).tag(kind)
                            }
                        }
                    }
                    .pickerStyle(.menu)
                    .labelsHidden()
                    .frame(minHeight: Tokens.Target.least)
                }
            }

            if context.state.meta.holds.costs {
                CheckRow(
                    SettingsCopy.Budget.firm, hint: SettingsCopy.Budget.firmHint,
                    isOn: firm.shown(budget.strictness == .hard, at: version)
                ) { checked in
                    firm.set(checked, at: version)
                    context.send(Edits.budgetStrictness(SettingsForm.firm(checked)))
                }

                WeightSlider(
                    label: SettingsCopy.Budget.weight, value: budget.weight, limits: context.limits,
                    version: version
                ) { context.send(Edits.budgetWeight($0)) }
            }
        }
    }

    @ViewBuilder
    private func amount(_ budget: Budget, _ tenure: Tenure, _ version: Int) -> some View {
        AmountControl(
            words: AmountControl.Words(
                label: SettingsCopy.Budget.amount(tenure),
                hint: SettingsForm.budgetHint(tenure, context.limits),
                notANumber: SettingsCopy.Budget.notWhole,
                less: SettingsCopy.Budget.less,
                more: SettingsCopy.Budget.more,
                slider: SettingsCopy.Budget.slider,
                said: { amount in
                    amount.map { SearchChips.budget($0, tenure) } ?? SettingsCopy.Budget.noneSet
                }),
            value: budget.amount,
            scale: AmountScale.budget(tenure, context.limits),
            keptWithin: false,
            problem: context.problem(.budget),
            version: version,
            onCommit: { context.send(Edits.budgetAmount($0)) },
            onStep: { context.send(Edits.budgetStep($0)) }
        )
        Button(SettingsCopy.Budget.clear) {
            context.send(Edits.budgetClear())
        }
        .buttonStyle(.burroLesser)
        .disabled(budget.amount == nil)
    }
}

/// One place to reach: how, within how long, and whether that is a firm limit.
struct CommuteControl: View {
    let commute: Commute
    /// The name of the place, as the API gave it.
    let name: String
    let context: ControlContext

    @State private var mode = Draft<Mode>()
    @State private var firm = Draft<Bool>()

    var body: some View {
        let placeId = commute.placeId
        let version = context.version
        let how = mode.shown(commute.mode, at: version)
        FormGroup(SettingsCopy.Journey.place(name)) {
            ChoiceList(
                SettingsCopy.Journey.how,
                choices: SettingsForm.modes.map { ($0, CodeCopy.mode($0)) },
                chosen: how
            ) { chosen in
                mode.set(chosen, at: version)
                context.send(Edits.placeMode(placeId, chosen))
            }
            AmountControl(
                words: AmountControl.Words(
                    label: SettingsCopy.Journey.longest,
                    hint: SettingsForm.minutesHint(how, context.limits),
                    notANumber: SettingsCopy.Journey.notWhole,
                    less: SettingsCopy.Journey.shorter,
                    more: SettingsCopy.Journey.longer,
                    slider: SettingsCopy.Journey.slider,
                    said: { SettingsCopy.Journey.minutes($0 ?? commute.maxMinutes) }),
                value: commute.maxMinutes,
                scale: AmountScale.minutes(how, context.limits),
                keptWithin: true,
                problem: context.problem(.place(placeId)),
                version: version,
                onCommit: { context.send(Edits.placeMinutes(placeId, $0)) },
                onStep: { context.send(Edits.placeStep(placeId, $0)) }
            )
            CheckRow(
                SettingsCopy.Journey.firm, hint: SettingsCopy.Journey.firmHint,
                isOn: firm.shown(commute.strictness == .hard, at: version)
            ) { checked in
                firm.set(checked, at: version)
                context.send(Edits.placeStrictness(placeId, SettingsForm.firm(checked)))
            }
            Button(SettingsCopy.Journey.remove(name)) {
                context.send(Edits.placeRemove(placeId))
            }
            .buttonStyle(.burroLesser)
        }
    }
}

/// How the journeys count: which one, which time, and how much.
struct JourneySettingsControl: View {
    let context: ControlContext

    @State private var combine = Draft<Combine>()
    @State private var basis = Draft<PtBasis>()

    var body: some View {
        let spec = context.spec
        let version = context.version
        FormGroup(SettingsCopy.Journey.settingsLegend) {
            ChoiceList(
                SettingsCopy.Journey.combine,
                choices: SettingsForm.combines.map { ($0, CodeCopy.combine($0)) },
                chosen: combine.shown(spec.commuteCombine, at: version)
            ) { chosen in
                combine.set(chosen, at: version)
                context.send(Edits.journeyCombine(chosen))
            }
            ChoiceList(
                SettingsCopy.Journey.basis,
                choices: SettingsForm.bases.map { ($0, CodeCopy.basis($0)) },
                chosen: basis.shown(spec.ptBasis, at: version)
            ) { chosen in
                basis.set(chosen, at: version)
                context.send(Edits.journeyBasis(chosen))
            }
            WeightSlider(
                label: SettingsCopy.Journey.weight, value: spec.commuteWeight, limits: context.limits,
                version: version
            ) { context.send(Edits.journeyWeight($0)) }
        }
    }
}

/// One feature: a switch that says whether it counts, and, while it does, how
/// much. Where more or fewer can be the better, which one. Its name is the
/// API's own label for it, which names a measure and not a wish: so under the
/// switch the form says which way counts as better, in the words Methods uses.
struct FeatureControl: View {
    let metric: Metric
    let context: ControlContext

    @State private var on = Draft<Bool>()
    @State private var direction = Draft<Direction>()
    /// The weight the person set since the last answer, which is on its way and not yet in the spec.
    @State private var set = Draft<Double>()

    var body: some View {
        let featureId = metric.featureId
        let version = context.version
        // A feature counts when its entry is above 0. One a person took off
        // keeps an entry of 0, and is drawn as off.
        let weight = context.spec.weights.first { $0.featureId == featureId }
        let counts = SearchChips.counts(weight?.weight)
        let isOn = on.shown(counts, at: version)
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            CheckRow(metric.label, hint: CodeCopy.polarity(metric.polarity), isOn: isOn) { checked in
                on.set(checked, at: version)
                context.send(SettingsForm.feature(featureId, on: checked))
            }
            if let weight, counts, isOn {
                VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                    WeightSlider(
                        label: SettingsCopy.Features.weight(metric.label), value: weight.weight,
                        limits: context.limits, version: version
                    ) { value in
                        set.set(value, at: version)
                        context.send(Edits.featureWeight(featureId, value))
                    }
                    if metric.polarity == .either {
                        ChoiceList(
                            SettingsCopy.Features.direction(metric.label),
                            choices: SettingsForm.directions.map { ($0, CodeCopy.direction($0)) },
                            chosen: direction.shown(weight.direction, at: version)
                        ) { chosen in
                            direction.set(chosen, at: version)
                            // A `set` always reads its value, and a later edit wins. So the weight
                            // sent with the direction is the one just set, or it would undo the one
                            // on its way.
                            context.send(
                                SettingsForm.direction(
                                    featureId, chosen, weight: set.shown(weight.weight, at: version)))
                        }
                    }
                }
                .belongsToSwitch()
            }
            if let problem = context.problem(.feature(featureId)) { ProblemLine(problem) }
        }
    }
}

/// One vibe. One that runs one way is a switch, and how much it counts while
/// it is on. A scale has two ends, and the person chooses which is asked for:
/// Burro guesses neither. A vibe that no area of the data can be placed on has
/// no control: it says that it is not in the data yet, and what it waits on.
struct TagControl: View {
    let tag: Tag
    let context: ControlContext

    @State private var on = Draft<Bool>()
    @State private var end = Draft<SettingsForm.End>()

    var body: some View {
        let tagId = tag.tagId
        let version = context.version
        let weight = context.spec.tags.first { $0.tagId == tagId }
        let counts = SearchChips.counts(weight?.weight)
        let isOn = on.shown(counts, at: version)
        let held = ReleaseHolds.recipe(of: tagId, in: context.state.meta)
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            if !ReleaseHolds.isPlaced(tagId, in: context.state.meta) {
                VibeWaiting(name: tag.label, held: held)
            } else if tag.shape == .scale, let low = tag.lowEnd, let high = tag.highEnd {
                ChoiceList(
                    tag.label,
                    choices: [
                        (SettingsForm.End.off, SearchCopy.Chips.off),
                        (.low, SettingsCopy.Features.toward(tag.label, low)),
                        (.high, SettingsCopy.Features.toward(tag.label, high)),
                    ],
                    chosen: end.shown(SettingsForm.end(of: weight), at: version)
                ) { chosen in
                    end.set(chosen, at: version)
                    context.send(SettingsForm.turn(tagId, to: chosen, from: weight))
                }
            } else {
                CheckRow(tag.label, isOn: isOn) { checked in
                    on.set(checked, at: version)
                    context.send(SettingsForm.tag(tagId, on: checked))
                }
            }
            if let countsCrime = SearchChips.countsCrime(tag, in: context.state.meta) {
                HintLine(countsCrime)
            }
            if let weight, counts, isOn {
                WeightSlider(
                    label: SettingsCopy.Features.weight(tag.label), value: weight.weight,
                    limits: context.limits, version: version
                ) { context.send(Edits.tagWeight(tagId, $0)) }
                .belongsToSwitch()
            }
            if let problem = context.problem(.tag(tagId)) { ProblemLine(problem) }
        }
    }
}

extension View {
    /// Sets what belongs to a switch that is on a little in from it, with a line down its side.
    fileprivate func belongsToSwitch() -> some View {
        padding(.leading, Tokens.Space.s4)
            .overlay(alignment: .leading) {
                Rectangle()
                    .fill(Tokens.Colour.border)
                    .frame(width: 2)
                    .accessibilityHidden(true)
            }
            .padding(.leading, Tokens.Space.s3)
    }
}
