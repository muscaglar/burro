import SwiftUI

/// What Burro read in a prompt and did not apply. Nothing is added until it
/// is pressed.
///
/// Each offer is drawn in four parts, in this order: what it would do, the
/// person's own words, what follows for areas, and the choices. Where Burro
/// reads a thing one way, that way is marked as its guess, and the mark
/// applies nothing. Doing nothing is "Skip". A note is drawn above the choices
/// of the thing it is a note of.
///
/// A journey to a place Burro does not know is offered with no place. A press
/// on a way of it sends nothing: it opens the search for a place under the
/// offer, and the journey is sent with the place that is chosen and the way
/// that was pressed.
///
/// What an offer would do, what follows and the words of each choice are the
/// API's. The person's words are cut from the box by where they stand, while
/// the box holds what was sent, and are kept nowhere.
///
/// Where two or more things in sight are ones the API says one press may add,
/// one button adds them all. Which those are is the API's to say: the screen
/// works nothing out. What the API marks for no such press stays the person's
/// to choose whatever is pressed. The block says what the press added and what
/// is left for the person, and one press takes it all back.
struct OffersBlock: View {
    let offers: OffersShown
    /// True where the box can select a stretch of what it holds. Where it
    /// cannot, no button offers to show the words.
    let canShowWords: Bool
    /// The person's own words of one stretch, cut from the box as it stands, or `nil`
    /// where the box does not hold them. They are drawn, and kept nowhere.
    let wrote: (Span) -> String?
    /// Route 8, for a journey whose place Burro does not know. What is typed there goes
    /// in the body of the call and nowhere else.
    let search: @MainActor (String) async -> Answer<PlacesData>
    /// Takes one choice of the offer at that place in the list, by the id of the choice.
    /// A journey to a place the release does not hold comes with the place the person chose.
    let choose: (Int, String, OfferShown.Option?) -> Void
    let chooseAll: ([Int]) -> Void
    /// Takes back all that the last press of "Add all" added.
    let takeItBack: () -> Void
    let showAll: () -> Void
    let showWords: (OfferShown) -> Void

    /// The offer a place is being chosen for, and the way of it that was pressed.
    @State private var placing: Placing?

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            Text(SearchCopy.Suggest.title)
                .font(Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
            HintLine(SearchCopy.Suggest.why)
            if let says = offers.says {
                // That a model reads the rest, or else what one press added. What is
                // offered is drawn below, and is there to choose of meanwhile.
                HintLine(says)
            }
            if let takeBack = offers.takeBack {
                Button(takeBack, action: takeItBack)
                    .buttonStyle(.burroLesser)
            }
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
            Text(verbatim: offer.does)
                .font(Tokens.Text.body.weight(.semibold))
                .foregroundStyle(Tokens.Colour.text)
                .fixedSize(horizontal: false, vertical: true)
            if let words = wrote(offer.shown) {
                // The quote marks are those a browser draws around a quotation.
                (Text(SearchCopy.Suggest.wrote).foregroundStyle(Tokens.Colour.muted)
                    + Text(verbatim: " \u{201C}\(words)\u{201D}"))
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.text)
                    .fixedSize(horizontal: false, vertical: true)
            }
            ForEach(Array(offer.follows.enumerated()), id: \.offset) { _, line in
                Text(verbatim: line)
                    .font(Tokens.Text.footnote)
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
                    press(choice, of: offer)
                } label: {
                    label(of: choice)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .buttonStyle(.burroLesser)
                .accessibilityLabel(Text(verbatim: choice.spoken))
                // A note that is drawn once is still said of each thing it is a note of.
                .accessibilityHint(Text(verbatim: offer.note ?? ""))
                // The way that was pressed is said to be the one, while its place is chosen.
                .accessibilityAddTraits(asked(of: offer) == choice.id ? [.isSelected] : [])
            }
            if canShowWords && !offer.spans.isEmpty {
                Button(SearchCopy.Suggest.showWords) { showWords(offer) }
                    .buttonStyle(.burroLesser)
                    .accessibilityLabel(Text(verbatim: SearchCopy.Suggest.showWordsOf(offer.name)))
            }
            if let way = asked(of: offer) {
                place(of: offer, way: way)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .contain)
        .accessibilityLabel(Text(verbatim: offer.name))
    }

    /// Where the place of a journey is chosen: the places the release holds that are like
    /// the one that was named, and the search for any other. What is typed in the search
    /// is held by its field, and goes in the body of its call and nowhere else.
    private func place(of offer: OfferShown, way: String) -> some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            if !offer.options.isEmpty {
                VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                    ForEach(offer.options) { option in
                        Button {
                            pick(option, of: offer, way: way)
                        } label: {
                            Text(verbatim: option.name)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        .buttonStyle(.burroLesser)
                    }
                }
                .accessibilityElement(children: .contain)
                .accessibilityLabel(Text(SearchCopy.Suggest.alike))
            }
            PlaceField(label: SearchCopy.Suggest.whichPlace, search: search) { found in
                pick(OfferShown.Option(id: found.placeId, name: found.name), of: offer, way: way)
            }
        }
    }

    /// The way of this offer that was pressed, while its place is being chosen.
    private func asked(of offer: OfferShown) -> String? {
        placing?.key == offer.key ? placing?.way : nil
    }

    /// A press on a choice. A journey whose place Burro does not know asks which place
    /// before it is added, and nothing is sent until one is chosen.
    private func press(_ choice: OfferShown.Choice, of offer: OfferShown) {
        guard !offer.asksWhichPlace(on: choice) else {
            placing = Placing(key: offer.key, way: choice.id)
            return
        }
        // The offer goes with its choice, and so does the search for its place.
        if placing?.key == offer.key { placing = nil }
        choose(offer.at, choice.id, nil)
    }

    /// The place that is chosen goes with the way that was pressed.
    private func pick(_ place: OfferShown.Option, of offer: OfferShown, way: String) {
        placing = nil
        choose(offer.at, way, place)
    }

    /// The words of a choice, and after them the mark of Burro's guess where it is the
    /// guess. The mark is said in words, and not by the weight of the letters alone.
    private func label(of choice: OfferShown.Choice) -> Text {
        guard choice.guess else { return Text(verbatim: choice.label) }
        return Text(verbatim: choice.label).fontWeight(.semibold)
            + Text(verbatim: " (\(SearchCopy.Suggest.guess))").font(Tokens.Text.footnote)
    }
}

/// The offer a place is being chosen for, by its key, and the way of it that was pressed.
private struct Placing: Hashable {
    let key: String
    let way: String
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
