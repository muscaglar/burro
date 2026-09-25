import SwiftUI

// What the screen says of a state of the search. Every word about a failure
// or a notice is the API's own, shown as it came. The rest names a state.

/// Says something aloud to a person who is using a screen reader, as a live
/// region of a web page does. It draws nothing.
enum Spoken {
    @MainActor
    static func say(_ words: String) {
        guard !words.isEmpty else { return }
        AccessibilityNotification.Announcement(words).post()
    }
}

/// One line for a state of the screen: words that could not be read, nothing read, offline.
struct StateLine: View {
    private let words: String

    init(_ words: String) {
        self.words = words
    }

    var body: some View {
        Text(words)
            .font(Tokens.Text.body)
            .foregroundStyle(Tokens.Colour.text)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.horizontal, Tokens.Space.s4)
            .padding(.vertical, Tokens.Space.s3)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Tokens.Colour.surface, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
            .overlay(alignment: .leading) {
                Rectangle()
                    .fill(Tokens.Colour.border)
                    .frame(width: 4)
                    .accessibilityHidden(true)
            }
            .clipShape(RoundedRectangle(cornerRadius: Tokens.Radius.small))
    }
}

/// The API's one neutral notice, word for word, in a plain block. It says what
/// Burro ranks by. It never says what was left out, and neither does the screen.
struct NoticeBlock: View {
    /// The API's own sentence.
    let text: String

    var body: some View {
        Text(verbatim: text)
            .font(Tokens.Text.body)
            .foregroundStyle(Tokens.Colour.infoText)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.horizontal, Tokens.Space.s4)
            .padding(.vertical, Tokens.Space.s3)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Tokens.Colour.infoBg, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
            .overlay(alignment: .leading) {
                Rectangle()
                    .fill(Tokens.Colour.infoText)
                    .frame(width: 4)
                    .accessibilityHidden(true)
            }
            .clipShape(RoundedRectangle(cornerRadius: Tokens.Radius.small))
            .accessibilityLabel(Text(verbatim: "\(SearchCopy.Notice.label). \(text)"))
    }
}

/// Said while the phone has no connection. What is on screen stays readable.
struct OfflineBlock: View {
    /// True when a change is waiting to be sent.
    let waiting: Bool
    let tryAgain: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            StateLine(
                waiting
                    ? "\(SearchCopy.Notice.offline) \(SearchCopy.Notice.offlineWaiting)"
                    : SearchCopy.Notice.offline)
            Button(SearchCopy.Prompt.tryAgain, action: tryAgain)
                .buttonStyle(.burroLesser)
        }
    }
}

/// Said when the words could not be read, where the settings do the same job, and
/// when the language model would not read them, where the rules have.
struct CouldNotReadBlock: View {
    /// Which of the two is said.
    let words: String
    /// `nil` when there is nothing to try again.
    let tryAgain: (() -> Void)?

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            StateLine(words)
            if let tryAgain {
                Button(SearchCopy.Prompt.tryAgain, action: tryAgain)
                    .buttonStyle(.burroLesser)
            }
        }
    }
}

/// Says that a call failed, in words, and what can be done.
///
/// It shows the API's fixed text, and the id of the request to quote. It
/// shows nothing that was sent, because it is given nothing that was sent.
struct SearchErrorBlock: View {
    let failure: FailureShown
    let repair: (Operations) -> Void
    let tryAgain: () -> Void
    let startAgain: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            Label {
                Text(verbatim: failure.message)
                    .fontWeight(.semibold)
                    .fixedSize(horizontal: false, vertical: true)
            } icon: {
                Image(systemName: "exclamationmark.triangle")
                    .accessibilityHidden(true)
            }
            .font(Tokens.Text.body)
            .foregroundStyle(Tokens.Colour.error)
            if failure.notUpdated {
                Text(SearchCopy.Notice.notUpdated)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.text)
            }
            if let requestId = failure.requestId {
                VStack(alignment: .leading, spacing: 0) {
                    Text(SearchCopy.Notice.requestId)
                        .font(Tokens.Text.footnote)
                    Text(verbatim: requestId)
                        .font(Tokens.Text.code)
                        .textSelection(.enabled)
                }
                .foregroundStyle(Tokens.Colour.muted)
            }
            ForEach(failure.repairs) { one in
                Button(one.label) { repair(one.operations) }
                    .buttonStyle(.burroLesser)
            }
            Button(SearchCopy.Prompt.tryAgain, action: tryAgain)
                .buttonStyle(.burroLesser)
            Button(SearchCopy.Prompt.startAgain, action: startAgain)
                .buttonStyle(.burroLesser)
        }
        .padding(Tokens.Space.s4)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(
            RoundedRectangle(cornerRadius: Tokens.Radius.small)
                .strokeBorder(Tokens.Colour.error, lineWidth: 1)
        )
    }
}

/// A plain list of lines, under a heading that is read and not drawn.
struct LineList: View {
    struct Line: Hashable {
        /// What the line is about, where it has a name.
        let about: String?
        let words: String
    }

    let label: String
    let lines: [Line]

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s1) {
            ForEach(Array(lines.enumerated()), id: \.offset) { _, line in
                HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                    Text(verbatim: "•")
                        .accessibilityHidden(true)
                    Group {
                        if let about = line.about {
                            Text(verbatim: "\(about): ").fontWeight(.semibold)
                                .foregroundStyle(Tokens.Colour.text)
                                + Text(verbatim: line.words)
                        } else {
                            Text(verbatim: line.words)
                        }
                    }
                    .fixedSize(horizontal: false, vertical: true)
                }
                .font(Tokens.Text.secondary)
                .foregroundStyle(Tokens.Colour.muted)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .contain)
        .accessibilityLabel(Text(label))
    }
}

/// The one question Burro asks: which place was meant. Up to five buttons,
/// each a place the release holds, then a search field, then "Leave it out".
///
/// It never repeats what was typed. The API does not send it back, and the
/// app does not keep it.
struct QuestionBlock: View {
    let question: QuestionShown
    let search: @MainActor (String) async -> Answer<PlacesData>
    /// Told of the place or the area that was picked: its id, and its name as the API gave it.
    let pick: (_ id: String, _ name: String) -> Void
    let leaveOut: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            Text(question.title)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
            ForEach(question.options) { option in
                Button {
                    pick(option.id, option.name)
                } label: {
                    VStack(alignment: .leading, spacing: 0) {
                        Text(verbatim: option.name)
                            .fontWeight(.semibold)
                            .foregroundStyle(Tokens.Colour.text)
                        if !option.kind.isEmpty {
                            Text(option.kind)
                                .font(Tokens.Text.secondary)
                                .foregroundStyle(Tokens.Colour.muted)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .buttonStyle(.burroLesser)
            }
            if let none = question.none {
                Text(none)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.text)
                    .fixedSize(horizontal: false, vertical: true)
            }
            if question.searchable {
                PlaceField(label: SearchCopy.Question.search, search: search) { place in
                    pick(place.placeId, place.name)
                }
            }
            Button(SearchCopy.Question.leaveOut, action: leaveOut)
                .buttonStyle(.burroLesser)
        }
        .formCard()
    }
}
