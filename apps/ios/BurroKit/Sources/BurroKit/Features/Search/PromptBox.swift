import SwiftUI

/// What the box does with what is typed: how much of it it holds, and when it
/// says how much room is left. It reads the text, and keeps none of it.
enum PromptText {
    /// The count of characters left is shown once fewer than this many remain.
    static let countFrom = 100

    /// How many characters are left, once few enough remain to be worth saying.
    static func left(_ text: String, of maxText: Int) -> Int? {
        let left = maxText - text.count
        return left < countFrom ? max(0, left) : nil
    }

    /// What was typed, kept to the most the API takes.
    static func kept(_ text: String, to maxText: Int) -> String {
        text.count > maxText ? String(text.prefix(max(0, maxText))) : text
    }

    /// True when there is nothing in the box to send.
    static func isEmpty(_ text: String) -> Bool {
        text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
}

/// A stretch of what the box holds, for the box to select. It holds where the
/// stretch stands, and never the words.
struct BoxSelect: Hashable, Sendable {
    let range: Range<String.Index>
    /// Changes with every press, so that the same stretch can be shown again.
    let press: Int
}

/// The one box to type in.
///
/// What is typed is held by the screen the box is on, while that screen is
/// open, and by nothing else. It goes from the box to one call. It is never
/// written to the search's state, a file, a log or the pasteboard.
struct PromptBox: View {
    @Binding var text: String
    /// The most characters a sentence may hold, as the API serves it.
    let maxText: Int
    /// True while a sentence is being read.
    let busy: Bool
    /// The API's own words for why the text was refused, when it was.
    let refusal: String?
    /// What the box asks for: only what the data can answer.
    var hint: String = SearchCopy.Prompt.hint
    /// The stretch of what the box holds to select, where one is asked for.
    var select: BoxSelect?
    let onSubmit: (String) -> Void
    let onStop: () -> Void

    @State private var empty = false
    @FocusState private var focused: Bool

    /// True where the box can select a stretch of what it holds. The system
    /// gives a way to from iOS 18. Before that no button offers to.
    static var selects: Bool {
        if #available(iOS 18.0, macOS 15.0, *) { return true }
        return false
    }

    var body: some View {
        let problem = refusal ?? (empty ? SearchCopy.Prompt.empty : nil)
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            Text(SearchCopy.Prompt.label)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
                .accessibilityAddTraits(.isHeader)
            HintLine(hint)
                .accessibilityHidden(true)
            field
                .lineLimit(3...12)
                .submitLabel(.search)
                .font(Tokens.Text.body)
                .foregroundStyle(Tokens.Colour.text)
                .formField()
                // The keyboard keeps what it corrects, to offer it again. What is typed here
                // names where a person works, so the keyboard is asked to leave it alone.
                .autocorrectionDisabled()
                .onSubmit(send)
                .accessibilityHint(Text(hint))
            if let left = PromptText.left(text, of: maxText) {
                Text(SearchCopy.Prompt.left(left))
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
            }
            if let problem {
                ProblemLine(problem)
            }
            Button(busy ? SearchCopy.Prompt.reading : SearchCopy.Prompt.submit, action: send)
                .buttonStyle(.burroPrimary)
                .disabled(busy)
            if busy {
                Button(SearchCopy.Prompt.stop, action: onStop)
                    .buttonStyle(.burroSecondary)
            }
        }
        .onChange(of: text) { _, typed in
            let kept = PromptText.kept(typed, to: maxText)
            if kept != typed { text = kept }
            if empty && !PromptText.isEmpty(typed) { empty = false }
        }
        .onChange(of: select) { _, wanted in
            // A box selects only while it is the one being typed in.
            if wanted != nil { focused = true }
        }
    }

    @ViewBuilder
    private var field: some View {
        if #available(iOS 18.0, macOS 15.0, *) {
            SelectingField(label: SearchCopy.Prompt.label, text: $text, select: select, focused: $focused)
        } else {
            TextField(SearchCopy.Prompt.label, text: $text, axis: .vertical)
                .focused($focused)
                .autocorrectionDisabled()
        }
    }

    private func send() {
        guard !busy else { return }
        guard !PromptText.isEmpty(text) else {
            empty = true
            focused = true
            return
        }
        empty = false
        focused = false
        onSubmit(text)
    }
}

/// The box, where the system lets a stretch of what it holds be selected. The
/// words stay in the box: it is given where they stand, and never what they are.
@available(iOS 18.0, macOS 15.0, *)
private struct SelectingField: View {
    let label: String
    @Binding var text: String
    let select: BoxSelect?
    let focused: FocusState<Bool>.Binding

    @State private var selection: TextSelection?

    var body: some View {
        TextField(label, text: $text, selection: $selection, axis: .vertical)
            .focused(focused)
            // What is typed here names where a person works, so the keyboard is asked to leave it alone.
            .autocorrectionDisabled()
            .onChange(of: select) { _, wanted in
                // Where the words stand is known for the text that was sent, and for no other.
                guard let wanted, wanted.range.upperBound <= text.endIndex else { return }
                selection = TextSelection(range: wanted.range)
            }
    }
}

/// The sentences to start from. Pressing one fills the box and sends nothing.
struct ExampleList: View {
    @Binding var open: Bool
    /// The sentences the data can answer the whole of.
    let sentences: [String]
    let use: (String) -> Void

    var body: some View {
        OpensInPlace(SearchCopy.Prompt.examplesTitle, open: $open) {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                HintLine(SearchCopy.Prompt.examplesHint)
                ForEach(sentences, id: \.self) { sentence in
                    Button {
                        use(sentence)
                    } label: {
                        Text(sentence)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .buttonStyle(.burroLesser)
                    .accessibilityHint(Text(SearchCopy.Prompt.examplesHint))
                }
            }
        }
    }
}

/// What stands where the box would, for a person who chose the settings.
struct DeclinedLine: View {
    let change: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            StateLine(SearchCopy.Declined.line)
            Button(SearchCopy.Declined.change, action: change)
                .buttonStyle(.burroLesser)
        }
    }
}

/// Search as you type for a place to reach.
///
/// What is typed is held by the field and by nothing else. A place is picked
/// by pressing its row, and the field is emptied.
struct PlaceField: View {
    let label: String
    let hint: String
    /// Said in place of the field when no more places can be named.
    let full: String?
    /// True where the data names no place: no field is offered, because nothing typed could match.
    let noPlaces: Bool
    let onPick: (FoundPlace) -> Void

    @State private var query = ""
    @State private var places: PlaceSearch

    init(
        label: String = SearchCopy.Place.label,
        hint: String = SearchCopy.Place.hint,
        full: String? = nil,
        noPlaces: Bool = false,
        search: @escaping @MainActor (String) async -> Answer<PlacesData>,
        onPick: @escaping (FoundPlace) -> Void
    ) {
        self.label = label
        self.hint = hint
        self.full = full
        self.noPlaces = noPlaces
        self.onPick = onPick
        _places = State(initialValue: PlaceSearch(search: search))
    }

    var body: some View {
        if noPlaces {
            // The label stays, and a line says that nothing typed there could match.
            VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                Text(label)
                    .font(Tokens.Text.secondary.weight(.semibold))
                    .foregroundStyle(Tokens.Colour.text)
                StateLine(SearchCopy.Place.notInData)
            }
        } else if let full {
            StateLine(full)
        } else {
            VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                Text(label)
                    .font(Tokens.Text.secondary.weight(.semibold))
                    .foregroundStyle(Tokens.Colour.text)
                    .accessibilityHidden(true)
                HintLine(hint)
                    .accessibilityHidden(true)
                TextField(label, text: $query)
                    .nameKeyboard()
                    .submitLabel(.done)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.text)
                    .formField()
                    .accessibilityHint(Text(hint))
                if !places.options.isEmpty {
                    VStack(alignment: .leading, spacing: 0) {
                        ForEach(places.options) { option in
                            Button {
                                pick(option.place)
                            } label: {
                                VStack(alignment: .leading, spacing: 0) {
                                    Text(verbatim: option.name)
                                        .font(Tokens.Text.body.weight(.semibold))
                                        .foregroundStyle(Tokens.Colour.text)
                                    if !option.detail.isEmpty {
                                        Text(verbatim: option.detail)
                                            .font(Tokens.Text.secondary)
                                            .foregroundStyle(Tokens.Colour.muted)
                                    }
                                }
                                .multilineTextAlignment(.leading)
                                .padding(.horizontal, Tokens.Space.s3)
                                .padding(.vertical, Tokens.Space.s2)
                                .frame(maxWidth: .infinity, minHeight: Tokens.Target.least, alignment: .leading)
                                .contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                            .accessibilityHint(Text(SearchCopy.Place.add(option.name)))
                        }
                    }
                    .background(Tokens.Colour.bg, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
                    .overlay(
                        RoundedRectangle(cornerRadius: Tokens.Radius.small)
                            .strokeBorder(Tokens.Colour.border, lineWidth: 1)
                    )
                    .accessibilityElement(children: .contain)
                    .accessibilityLabel(Text(SearchCopy.Place.options))
                }
                if !places.status.words.isEmpty {
                    Text(places.status.words)
                        .font(Tokens.Text.footnote)
                        .foregroundStyle(Tokens.Colour.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .onChange(of: query) { _, typed in
                let kept = PromptText.kept(typed, to: SearchFlow.placeQuery.most)
                if kept != typed { query = kept }
                places.typed(kept)
            }
            .onChange(of: places.status) { _, status in
                Spoken.say(status.words)
            }
            .onDisappear { places.clear() }
        }
    }

    private func pick(_ place: FoundPlace) {
        query = ""
        places.clear()
        onPick(place)
    }
}
