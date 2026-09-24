import SwiftUI

/// What the reader noticed in a prompt it did not apply. It never guesses
/// which way a thing was meant: each thing is offered with the directions a
/// person may choose, and nothing is ranked from one until it is chosen.
///
/// A thing there is one way to want is offered by its button alone, which
/// names it. Where two or more such things are in sight, one button adds them
/// all. A thing that could be meant two ways is named, and stays a question
/// whatever is pressed. So does a thing that carries a note: its note is drawn
/// above its choices, and it is chosen by its own button, which names it, and
/// by no other. Recorded crime is such a thing, and counts only when it is
/// asked for by name.
///
/// The name of each thing and the words of each choice are the API's. The
/// words a person typed are shown nowhere but in the box, where a button
/// selects them.
struct OffersBlock: View {
    let offers: OffersShown
    /// True where the box can select a stretch of what it holds. Where it
    /// cannot, no button offers to show the words.
    let canShowWords: Bool
    let choose: (Int, SuggestionDirection) -> Void
    let chooseAll: ([Int]) -> Void
    let showAll: () -> Void
    let showWords: (OfferShown) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            Text(SearchCopy.Suggest.title)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
            HintLine(SearchCopy.Suggest.why)
            if let addAll = offers.addAll {
                Button(addAll) { chooseAll(offers.addAllAts) }
                    .buttonStyle(.burroSecondary)
            }
            ForEach(offers.offers) { offer in
                one(offer)
                    .ruledAbove()
            }
            if let more = offers.showAll {
                Button(more, action: showAll)
                    .buttonStyle(.burroLesser)
            }
        }
        .formCard()
    }

    private func one(_ offer: OfferShown) -> some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            if offer.named {
                Text(verbatim: offer.name)
                    .font(Tokens.Text.body.weight(.semibold))
                    .foregroundStyle(Tokens.Colour.text)
                    .fixedSize(horizontal: false, vertical: true)
            }
            if offer.noteDrawn, let note = offer.note {
                Text(verbatim: note)
                    .font(Tokens.Text.secondary)
                    .foregroundStyle(Tokens.Colour.text)
                    .fixedSize(horizontal: false, vertical: true)
            }
            ForEach(offer.choices) { choice in
                Button {
                    choose(offer.at, choice.direction)
                } label: {
                    Text(verbatim: choice.label)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .buttonStyle(.burroLesser)
                .accessibilityLabel(Text(verbatim: choice.spoken))
                // A note that is drawn once is still said of each thing it is a note of.
                .accessibilityHint(Text(verbatim: offer.note ?? ""))
            }
            if canShowWords && !offer.spans.isEmpty {
                Button(SearchCopy.Suggest.showWords) { showWords(offer) }
                    .buttonStyle(.burroLesser)
                    .accessibilityLabel(Text(verbatim: SearchCopy.Suggest.showWordsOf(offer.name)))
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .contain)
        .accessibilityLabel(Text(verbatim: offer.name))
    }
}

/// What a person asked for that the data does not hold yet, said by name
/// directly under what happened, with why. A vibe says what it waits on.
///
/// Nothing here is offered and nothing is pressed: the screen says what is
/// not there.
struct NotInDataBlock: View {
    let lead: String
    /// One line for each thing: its name, why, and for a vibe what it waits on.
    let lines: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            Text(SearchCopy.NotInData.title)
                .font(Tokens.Text.headline)
            Text(lead)
                .font(Tokens.Text.body)
            ForEach(lines, id: \.self) { line in
                Text(verbatim: line)
                    .font(Tokens.Text.body)
            }
        }
        .foregroundStyle(Tokens.Colour.infoText)
        .fixedSize(horizontal: false, vertical: true)
        .padding(.horizontal, Tokens.Space.s4)
        .padding(.vertical, Tokens.Space.s3)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Tokens.Colour.infoBg, in: RoundedRectangle(cornerRadius: Tokens.Radius.small))
        .accessibilityElement(children: .combine)
    }
}

/// Where a stretch of what was typed was not read: that it was so, and the
/// button that selects it in the box. The words stay in the box.
struct UnreadBlock: View {
    /// True when the line that says a part was not read is drawn already, above.
    let saidAbove: Bool
    /// True where the box can select a stretch of what it holds.
    let canShow: Bool
    /// True once a stretch has been shown and there are more to show.
    let showsNext: Bool
    let show: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            if !saidAbove {
                StateLine(SearchCopy.Suggest.unread)
            }
            if canShow {
                Button(showsNext ? SearchCopy.Suggest.showNextUnread : SearchCopy.Suggest.showUnread, action: show)
                    .buttonStyle(.burroLesser)
            }
        }
    }
}
