import SwiftUI

/// What Burro understood, one chip for each thing. A chip opens the same
/// control the settings hold, in place, and can be removed where the setting
/// can be. A part nobody chose carries the word "assumed" and a dashed edge.
/// The word is the signal. The edge repeats it.
///
/// The chips are one under another, so that the longest of them, at the
/// largest size of text, wraps inside itself and is never cut short.
struct ChipList: View {
    /// What the chips are: what Burro understood, what a search starts from, or what was set.
    let title: String
    let chips: [SearchChip]
    /// True while a first sentence is being read and no chip can be drawn yet.
    let waiting: Bool
    /// What explains the chips, each line drawn where it can be seen.
    let hints: [String]
    let context: ControlContext
    let chooseTenure: (Tenure) -> Void
    let openSettings: () -> Void

    @State private var open: ChipKind?

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            Text(title)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
                .accessibilityAddTraits(.isHeader)
            if waiting {
                ForEach(0..<3, id: \.self) { _ in
                    RoundedRectangle(cornerRadius: Tokens.Radius.small)
                        .fill(Tokens.Colour.surface)
                        .frame(height: Tokens.Target.least)
                }
                .accessibilityHidden(true)
            } else {
                ForEach(chips) { chip in
                    ChipRow(
                        chip: chip,
                        isOpen: open == chip.kind,
                        press: { pressed(chip) },
                        remove: chip.removal.map { removal in
                            {
                                if open == chip.kind { open = nil }
                                context.send(removal)
                            }
                        })
                    if open == chip.kind, chip.kind.opensAControl {
                        control(for: chip)
                            .formCard()
                    }
                }
            }
            if !waiting {
                ForEach(hints, id: \.self) { hint in
                    HintLine(hint)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func pressed(_ chip: SearchChip) {
        if chip.kind == .usual {
            openSettings()
        } else if chip.kind.opensAControl {
            open = open == chip.kind ? nil : chip.kind
        }
    }

    @ViewBuilder
    private func control(for chip: SearchChip) -> some View {
        switch chip.kind {
        case .tenure:
            TenureControl(
                tenure: context.spec.tenure, version: context.version,
                problem: context.problem(.tenure), choose: chooseTenure)
        case .budget:
            BudgetControl(context: context)
        case .place(let placeId):
            if let commute = context.spec.commutes.first(where: { $0.placeId == placeId }) {
                CommuteControl(commute: commute, name: chip.label, context: context)
            }
        case .feature(let featureId):
            if let metric = context.state.meta.features.first(where: { $0.featureId == featureId }) {
                FeatureControl(metric: metric, context: context)
            }
        case .tag(let tagId):
            if let tag = context.state.meta.tags.first(where: { $0.tagId == tagId }) {
                TagControl(tag: tag, context: context)
            }
        case .journeys:
            JourneySettingsControl(context: context)
        case .area, .usual:
            EmptyView()
        }
    }
}

/// One chip: its words, and the button that takes it out where it can be.
struct ChipRow: View {
    let chip: SearchChip
    let isOpen: Bool
    let press: () -> Void
    let remove: (() -> Void)?

    private var pressable: Bool {
        chip.kind.opensAControl || chip.kind == .usual
    }

    var body: some View {
        HStack(spacing: 0) {
            if pressable {
                Button(action: press) { face }
                    .buttonStyle(.plain)
                    .accessibilityLabel(Text(verbatim: chip.reads))
                    .accessibilityValue(Text(value))
                    .accessibilityHint(Text(hint))
            } else {
                face
                    .accessibilityElement(children: .ignore)
                    .accessibilityLabel(Text(verbatim: chip.reads))
            }
            if let remove {
                Rectangle()
                    .fill(Tokens.Colour.border)
                    .frame(width: 1)
                    .accessibilityHidden(true)
                Button(action: remove) {
                    Image(systemName: "xmark")
                        .font(Tokens.Text.secondary.weight(.semibold))
                        .foregroundStyle(Tokens.Colour.text)
                        .frame(minWidth: Tokens.Target.least, maxHeight: .infinity)
                        .frame(minHeight: Tokens.Target.least)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(Text(verbatim: "\(SearchCopy.Chips.remove): \(chip.label)"))
            }
        }
        .fixedSize(horizontal: false, vertical: true)
        .background(Tokens.Colour.surface, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
        .overlay(
            RoundedRectangle(cornerRadius: Tokens.Radius.small)
                .strokeBorder(
                    Tokens.Colour.border,
                    style: StrokeStyle(lineWidth: 1, dash: chip.assumed ? [4, 3] : []))
        )
    }

    private var face: some View {
        HStack(alignment: .center, spacing: Tokens.Space.s2) {
            words
                .font(Tokens.Text.body)
                .foregroundStyle(Tokens.Colour.text)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
            if chip.kind.opensAControl {
                Image(systemName: isOpen ? "chevron.down" : "chevron.right")
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
                    .accessibilityHidden(true)
            }
        }
        .padding(.horizontal, Tokens.Space.s3)
        .padding(.vertical, Tokens.Space.s2)
        .frame(maxWidth: .infinity, minHeight: Tokens.Target.least, alignment: .leading)
        .contentShape(Rectangle())
    }

    /// The label in a heavier weight, then each part after a comma, with the
    /// word "assumed" after whatever nobody chose.
    private var words: Text {
        var said = Text(verbatim: chip.label).fontWeight(.semibold)
        if chip.assumedAsAWhole { said = said + mark }
        for part in chip.parts {
            said = said + Text(verbatim: ", \(part.text)")
            if part.assumed { said = said + mark }
        }
        return said
    }

    private var mark: Text {
        Text(verbatim: " \(SearchCopy.Chips.assumed)")
            .italic()
            .foregroundStyle(Tokens.Colour.muted)
    }

    private var value: String {
        guard chip.kind.opensAControl else { return "" }
        return isOpen ? SearchCopy.Chips.open : SearchCopy.Chips.closed
    }

    private var hint: String {
        // What the usual settings are is said under the chips, where it can be seen.
        chip.kind == .usual ? SearchCopy.Chips.openSettings : SearchCopy.Chips.opens
    }
}
