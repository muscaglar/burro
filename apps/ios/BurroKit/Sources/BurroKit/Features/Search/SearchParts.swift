import SwiftUI

// The small parts the search screen and the settings are built from. Each is
// a system control with a label, takes its colours and text styles from
// `Tokens`, and is 44 points high at least where it can be pressed.

/// A group of controls under a heading, as a fieldset is under its legend.
struct FormGroup<Content: View>: View {
    enum Level {
        /// A group of the settings: "Budget", "Places you need to reach".
        case group
        /// A set of choices, or a dimension, inside a group.
        case inner
    }

    private let title: String
    private let level: Level
    private let content: Content

    init(_ title: String, level: Level = .group, @ViewBuilder content: () -> Content) {
        self.title = title
        self.level = level
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            Text(title)
                .font(level == .group ? Tokens.Text.headline : Tokens.Text.secondary.weight(.semibold))
                .foregroundStyle(Tokens.Colour.text)
                .accessibilityAddTraits(.isHeader)
            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// A line that explains a control, under it.
struct HintLine: View {
    private let words: String

    init(_ words: String) {
        self.words = words
    }

    var body: some View {
        Text(words)
            .font(Tokens.Text.footnote)
            .foregroundStyle(Tokens.Colour.muted)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// Why a control's last change was not taken, in words, under the control.
/// It is told by its words and its mark, and not by its colour alone.
struct ProblemLine: View {
    private let words: String

    init(_ words: String) {
        self.words = words
    }

    var body: some View {
        Label {
            Text(words)
                .fixedSize(horizontal: false, vertical: true)
        } icon: {
            Image(systemName: "exclamationmark.circle")
                .accessibilityHidden(true)
        }
        .font(Tokens.Text.secondary)
        .foregroundStyle(Tokens.Colour.error)
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// One of a few choices, each on a line of its own, as radio buttons are. The
/// one chosen is told by its mark and by what a screen reader says of it.
struct ChoiceList<Value: Hashable>: View {
    struct Choice: Identifiable {
        let value: Value
        let label: String
        var id: String { label }
    }

    private let title: String
    private let choices: [Choice]
    private let chosen: Value
    private let choose: (Value) -> Void

    /// - Parameter choices: Each value with its word. A value with no word is left out.
    init(_ title: String, choices: [(Value, String?)], chosen: Value, choose: @escaping (Value) -> Void) {
        self.title = title
        self.choices = choices.compactMap { value, label in
            label.map { Choice(value: value, label: $0) }
        }
        self.chosen = chosen
        self.choose = choose
    }

    var body: some View {
        FormGroup(title, level: .inner) {
            VStack(alignment: .leading, spacing: 0) {
                ForEach(choices) { choice in
                    let isChosen = choice.value == chosen
                    Button {
                        if !isChosen { choose(choice.value) }
                    } label: {
                        HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                            Image(systemName: isChosen ? "largecircle.fill.circle" : "circle")
                                .foregroundStyle(isChosen ? Tokens.Colour.accent : Tokens.Colour.border)
                                .accessibilityHidden(true)
                            Text(choice.label)
                                .font(Tokens.Text.body)
                                .fontWeight(isChosen ? .semibold : .regular)
                                .foregroundStyle(Tokens.Colour.text)
                                .multilineTextAlignment(.leading)
                                .fixedSize(horizontal: false, vertical: true)
                            Spacer(minLength: 0)
                        }
                        .frame(maxWidth: .infinity, minHeight: Tokens.Target.least, alignment: .leading)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(Text(verbatim: "\(title): \(choice.label)"))
                    .accessibilityAddTraits(isChosen ? [.isSelected] : [])
                }
            }
        }
    }
}

/// A switch, or a box to tick, with its words and the line that explains it.
struct CheckRow: View {
    private let label: String
    private let hint: String?
    private let isOn: Bool
    private let set: (Bool) -> Void

    init(_ label: String, hint: String? = nil, isOn: Bool, set: @escaping (Bool) -> Void) {
        self.label = label
        self.hint = hint
        self.isOn = isOn
        self.set = set
    }

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s1) {
            Toggle(isOn: Binding(get: { isOn }, set: { set($0) })) {
                Text(label)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.text)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(minHeight: Tokens.Target.least)
            .accessibilityHint(Text(hint ?? ""))
            if let hint {
                HintLine(hint)
                    .accessibilityHidden(true)
            }
        }
    }
}

/// A button that is pressed to take a small step: less, or more.
struct StepButton: View {
    private let step: SmallStep
    private let label: String
    private let action: () -> Void

    init(_ step: SmallStep, label: String, action: @escaping () -> Void) {
        self.step = step
        self.label = label
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            Image(systemName: step == .down ? "minus" : "plus")
                .font(Tokens.Text.headline)
                .frame(width: Tokens.Target.least, height: Tokens.Target.least)
                .overlay(
                    RoundedRectangle(cornerRadius: Tokens.Radius.small)
                        .strokeBorder(Tokens.Colour.border, lineWidth: 1)
                )
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .foregroundStyle(Tokens.Colour.text)
        .accessibilityLabel(Text(label))
    }
}

/// A plain button that stands in a line of its own, for the lesser actions of a control.
struct LesserButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Tokens.Text.body)
            .multilineTextAlignment(.leading)
            .padding(.horizontal, Tokens.Space.s3)
            .padding(.vertical, Tokens.Space.s2)
            .frame(minWidth: Tokens.Target.least, minHeight: Tokens.Target.least)
            .foregroundStyle(isEnabled ? Tokens.Colour.text : Tokens.Colour.muted)
            .background(Tokens.Colour.bg, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.small)
                    .strokeBorder(Tokens.Colour.border, lineWidth: 1)
            )
            .opacity(configuration.isPressed ? 0.8 : 1)
            .contentShape(Rectangle())
    }
}

extension ButtonStyle where Self == LesserButtonStyle {
    static var burroLesser: LesserButtonStyle { LesserButtonStyle() }
}

/// Something that opens in place: the settings, the examples, recorded crime.
/// Nothing moves when the person has asked for less motion.
struct OpensInPlace<Content: View>: View {
    private let title: String
    @Binding private var open: Bool
    private let content: () -> Content
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    init(_ title: String, open: Binding<Bool>, @ViewBuilder content: @escaping () -> Content) {
        self.title = title
        _open = open
        self.content = content
    }

    var body: some View {
        DisclosureGroup(isExpanded: $open) {
            VStack(alignment: .leading, spacing: Tokens.Space.s5) {
                content()
            }
            .padding(.top, Tokens.Space.s3)
        } label: {
            Text(title)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
                .frame(maxWidth: .infinity, minHeight: Tokens.Target.least, alignment: .leading)
                .accessibilityAddTraits(.isHeader)
        }
        .transaction { change in
            // The system opens it with a movement of its own. That is taken away
            // when the person has asked for less motion, and nothing is added.
            if Tokens.Motion.animation(Tokens.Motion.slow, reduceMotion: reduceMotion) == nil {
                change.animation = nil
            }
        }
    }
}

extension View {
    /// The edge and the space of a field to type in.
    func formField() -> some View {
        padding(.horizontal, Tokens.Space.s3)
            .padding(.vertical, Tokens.Space.s2)
            .frame(minHeight: Tokens.Target.least)
            .background(Tokens.Colour.bg, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.small)
                    .strokeBorder(Tokens.Colour.border, lineWidth: 1)
            )
    }

    /// The ground and the edge of a card: the settings, a question, a chip's control.
    func formCard() -> some View {
        padding(Tokens.Space.s4)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Tokens.Colour.surface, in: RoundedRectangle(cornerRadius: Tokens.Radius.card))
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(Tokens.Colour.border, lineWidth: 1)
            )
    }

    /// A rule above a group that follows another.
    func ruledAbove() -> some View {
        padding(.top, Tokens.Space.s4)
            .overlay(alignment: .top) {
                Rectangle()
                    .fill(Tokens.Colour.border)
                    .frame(height: 1)
                    .accessibilityHidden(true)
            }
    }

    /// A keyboard for a whole number, where the system has one.
    func numberKeyboard() -> some View {
        #if os(iOS)
        return keyboardType(.numbersAndPunctuation)
            .autocorrectionDisabled()
            .textInputAutocapitalization(.never)
        #else
        return autocorrectionDisabled()
        #endif
    }

    /// A field for the name of a place: a name is not a word to correct or to capitalise.
    func nameKeyboard() -> some View {
        #if os(iOS)
        return autocorrectionDisabled()
            .textInputAutocapitalization(.never)
        #else
        return autocorrectionDisabled()
        #endif
    }
}
