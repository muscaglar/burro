import SwiftUI

/// How much something counts, from 0 to 100.
///
/// It can be set two ways, and neither needs dragging: the slider itself, by
/// finger or by a screen reader's own gesture, and a minus and a plus button.
///
/// It shows its new value at once and sends it once: when the finger lifts, or
/// a moment after the last press. It never sends while it is dragged.
struct WeightSlider: View {
    /// What is being weighed. It names the slider and its buttons.
    let label: String
    /// The weight as the API returned it, from 0 to 1.
    let value: Double
    let limits: ServedLimits
    /// Changes with every answer from the API, so that the slider is drawn again from it.
    let version: Int
    let onCommit: (Double) -> Void

    @State private var draft = Draft<Int>()
    @State private var dragging = false
    @State private var settling = Settling()

    private var scale: WeightScale { WeightScale(limits) }
    private var returned: Int { WeightScale.hundredths(value) }
    private var shown: Int { draft.shown(returned, at: version) }

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s1) {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                    name
                    Spacer(minLength: Tokens.Space.s2)
                    figure
                }
                VStack(alignment: .leading, spacing: 0) {
                    name
                    figure
                }
            }
            .accessibilityHidden(true)
            HStack(spacing: Tokens.Space.s2) {
                StepButton(.down, label: SettingsCopy.Slider.less(label)) { move(.down) }
                    .disabled(shown <= WeightScale.least)
                Slider(
                    value: Binding(get: { Double(shown) }, set: { slid(to: $0) }),
                    in: Double(WeightScale.least)...Double(WeightScale.most),
                    step: Double(scale.unit)
                ) {
                    Text(label)
                } onEditingChanged: { editing in
                    editing ? held() : released()
                }
                .frame(minHeight: Tokens.Target.least)
                .accessibilityValue(Text(SettingsCopy.Slider.outOf(shown, WeightScale.most)))
                .accessibilityHint(
                    Text(SettingsCopy.Slider.range(WeightScale.least, WeightScale.most)))
                StepButton(.up, label: SettingsCopy.Slider.more(label)) { move(.up) }
                    .disabled(shown >= WeightScale.most)
            }
        }
        .onDisappear { settling.cancel() }
    }

    private var name: some View {
        Text(label)
            .font(Tokens.Text.secondary)
            .foregroundStyle(Tokens.Colour.muted)
            .fixedSize(horizontal: false, vertical: true)
    }

    private var figure: some View {
        Text(SettingsCopy.Slider.outOf(shown, WeightScale.most))
            .font(Tokens.Text.figure)
            .foregroundStyle(Tokens.Colour.text)
    }

    private func slid(to position: Double) {
        let next = scale.snapped(position)
        draft.set(next, at: version)
        // While a finger is down nothing is sent. Any other change is sent a moment after the last.
        if !dragging { settling.soon { send(next) } }
    }

    private func held() {
        dragging = true
        settling.cancel()
    }

    private func released() {
        dragging = false
        let next = shown
        settling.now { send(next) }
    }

    private func move(_ step: SmallStep) {
        let next = scale.moved(shown, step)
        draft.set(next, at: version)
        settling.soon { send(next) }
    }

    private func send(_ next: Int) {
        guard next != returned else { return }
        onCommit(WeightScale.weight(next))
    }
}

/// A number a person sets: a budget, or the longest journey.
///
/// It can be set three ways: typed into the field, stepped with the minus and
/// the plus button, and slid. A typed number is sent when the field is left,
/// or on Return, and never key by key: half a number is not a number. A
/// button sends a step, and the field shows where the API says it landed.
struct AmountControl: View {
    struct Words {
        let label: String
        let hint: String
        let notANumber: String
        let less: String
        let more: String
        let slider: String
        /// What the slider says its value is, to a person who cannot see it.
        let said: (Int?) -> String
    }

    let words: Words
    /// The number as the API returned it. `nil` when none is set.
    let value: Int?
    let scale: AmountScale
    /// True when a typed number is brought within the limits before it is sent.
    /// A budget is sent as typed, so that the API can say it is out of range.
    let keptWithin: Bool
    /// Why the last number was not taken, in words.
    let problem: String?
    let version: Int
    let onCommit: (Int) -> Void
    let onStep: (SmallStep) -> Void

    @State private var typed = Draft<String>()
    @State private var slid = Draft<Int>()
    @State private var unread = false
    @State private var dragging = false
    @State private var settling = Settling()
    @FocusState private var focused: Bool

    private var inField: String {
        typed.shown(value.map(String.init) ?? "", at: version)
    }

    private var onSlider: Int {
        slid.shown(value ?? scale.least, at: version)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s1) {
            Text(words.label)
                .font(Tokens.Text.secondary.weight(.semibold))
                .foregroundStyle(Tokens.Colour.text)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityHidden(true)
            HStack(spacing: Tokens.Space.s2) {
                StepButton(.down, label: words.less) { onStep(.down) }
                    .disabled(value == nil)
                TextField(
                    words.label,
                    text: Binding(
                        get: { inField },
                        set: { new in
                            guard new != inField else { return }
                            typed.set(new, at: version)
                            unread = false
                        })
                )
                .focused($focused)
                .numberKeyboard()
                .multilineTextAlignment(.trailing)
                .font(Tokens.Text.body.monospacedDigit())
                .foregroundStyle(Tokens.Colour.text)
                .formField()
                .onSubmit(commit)
                .accessibilityHint(Text(words.hint))
                StepButton(.up, label: words.more) { onStep(.up) }
                    .disabled(value == nil)
            }
            Slider(
                value: Binding(
                    get: { scale.position(of: onSlider) },
                    set: { moved(to: scale.value(at: $0)) }),
                in: 0...1
            ) {
                Text(words.slider)
            } onEditingChanged: { editing in
                editing ? held() : released()
            }
            .frame(minHeight: Tokens.Target.least)
            .accessibilityValue(Text(words.said(slid.isSet(at: version) ? onSlider : value)))
            HintLine(words.hint)
                .accessibilityHidden(true)
            if let said = unread ? words.notANumber : problem {
                ProblemLine(said)
            }
        }
        .onChange(of: focused) { _, isFocused in
            if !isFocused { commit() }
        }
        .onDisappear { settling.cancel() }
    }

    private func commit() {
        guard typed.isSet(at: version) else { return }
        switch NumberEntry.read(inField, keptWithin: keptWithin ? scale.limits : nil) {
        case .empty:
            typed.clear()
            unread = false
        case .notANumber:
            unread = true
        case .number(let number):
            unread = false
            guard number != value else {
                typed.clear()
                return
            }
            typed.set(String(number), at: version)
            slid.set(scale.snapped(Double(number)), at: version)
            onCommit(number)
        }
    }

    private func moved(to next: Int) {
        slid.set(next, at: version)
        typed.set(String(next), at: version)
        unread = false
        if !dragging { settling.soon { send(next) } }
    }

    private func held() {
        dragging = true
        settling.cancel()
    }

    private func released() {
        dragging = false
        guard slid.isSet(at: version) else { return }
        let next = onSlider
        settling.now { send(next) }
    }

    private func send(_ next: Int) {
        guard next != value else { return }
        onCommit(next)
    }
}
