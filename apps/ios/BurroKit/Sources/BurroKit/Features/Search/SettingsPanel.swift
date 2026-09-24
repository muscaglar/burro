import SwiftUI

/// The settings: the same search as a form. Every control here makes the edit
/// a sentence would, so the screen works with no words read at all.
///
/// It offers only what the release can rank, within the limits the API
/// served, so it never offers what the reducer would refuse.
struct SettingsPanel: View {
    let context: ControlContext
    let open: Bool
    let setOpen: (Bool) -> Void
    /// Ranks the settings as they stand. `nil` once there is a ranking.
    let rank: (() -> Void)?

    @State private var crimeOpen = false

    var body: some View {
        OpensInPlace(SettingsCopy.title, open: Binding(get: { open }, set: { setOpen($0) })) {
            HintLine(SettingsCopy.lead)
            BudgetControl(context: context)
            places.ruledAbove()
            nearby.ruledAbove()
            feel.ruledAbove()
            if let crime = SettingsForm.crime(context.state.meta) {
                // Recorded crime is its own group, closed and off at first, under its caveat.
                OpensInPlace(crime.title, open: $crimeOpen) {
                    Text(SettingsCopy.Crime.lead)
                    Text(SettingsCopy.Crime.caveat)
                    switches(crime.features)
                }
                .font(Tokens.Text.body)
                .foregroundStyle(Tokens.Colour.text)
                .ruledAbove()
            }
            hidden.ruledAbove()
            if let rank {
                Button(SettingsCopy.rank, action: rank)
                    .buttonStyle(.burroPrimary)
            }
        }
        .formCard()
    }

    private var places: some View {
        let spec = context.spec
        let names = SearchChips.names(of: spec, held: context.state.placeNames)
        return FormGroup(SettingsCopy.Journey.legend) {
            if spec.commutes.isEmpty { HintLine(SettingsCopy.Journey.none) }
            ForEach(spec.commutes, id: \.placeId) { commute in
                CommuteControl(commute: commute, name: names[commute.placeId] ?? "", context: context)
            }
            if !spec.commutes.isEmpty { JourneySettingsControl(context: context) }
        }
    }

    private var nearby: some View {
        FormGroup(SettingsCopy.Features.legend) {
            ForEach(SettingsForm.groups(context.state.meta)) { group in
                FormGroup(group.title, level: .inner) {
                    switches(group.features)
                }
            }
        }
    }

    private var feel: some View {
        FormGroup(SettingsCopy.Features.tagsLegend) {
            HintLine(SettingsCopy.Features.tagsHint)
            ForEach(context.state.meta.tags, id: \.tagId) { tag in
                TagControl(tag: tag, context: context)
            }
        }
    }

    private var hidden: some View {
        let rules = context.spec.areas
        return FormGroup(SettingsCopy.Hidden.legend) {
            if rules.isEmpty { HintLine(SettingsCopy.Hidden.none) }
            ForEach(rules, id: \.areaId) { rule in
                if let words = SettingsForm.show(rule, in: context.state) {
                    Button(words) {
                        context.send(Edits.areaClear(rule.areaId))
                    }
                    .buttonStyle(.burroLesser)
                }
            }
        }
    }

    private func switches(_ features: [Metric]) -> some View {
        ForEach(features, id: \.featureId) { metric in
            FeatureControl(metric: metric, context: context)
        }
    }
}
