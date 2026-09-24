import SwiftUI

// One result. The first five are cards in full: where the area is, up to
// three reasons, one trade-off, how complete the data is, each journey, the
// cost, and how the fit is worked out. The rest are rows, which open to the
// journeys and to how the fit is worked out.
//
// Every sentence is the API's, and every line ends in its source and date,
// written out so that it is read without a press.

extension Results {
    /// Rank, name, borough, and the fit as a figure with a bar that repeats it.
    struct HeadingView: View {
        let heading: Heading

        var body: some View {
            Beside {
                RankDisc(rank: heading.rank)
                VStack(alignment: .leading, spacing: 0) {
                    Text(heading.name)
                        .font(Tokens.Text.headline)
                        .foregroundStyle(Tokens.Colour.text)
                    Text(heading.borough)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.muted)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                if let fit = heading.fit, let words = heading.fitWords {
                    VStack(alignment: .trailing, spacing: Tokens.Space.s1) {
                        Text(verbatim: "\(ResultsCopy.Card.fit) \(words)")
                            .font(Tokens.Text.figure)
                            .foregroundStyle(Tokens.Colour.text)
                        Meter(filled: fit)
                            .frame(width: Tokens.Space.s8 + Tokens.Space.s6)
                    }
                }
            }
            .frame(maxWidth: .infinity, minHeight: Tokens.Target.least, alignment: .leading)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(heading.words)
            .accessibilityAddTraits(.isHeader)
        }
    }

    /// A fact with no sentence of its own, laid out under the names of its columns.
    struct FactView: View {
        let fact: FactShown
        let openSources: () -> Void

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                Text(fact.name)
                    .font(Tokens.Text.body.weight(.semibold))
                    .foregroundStyle(Tokens.Colour.text)
                ForEach(fact.columns) { column in
                    Named(name: column.name, value: column.value)
                }
                ForEach(fact.caveats, id: \.self) { caveat in
                    Text(caveat)
                        .font(Tokens.Text.footnote)
                        .foregroundStyle(Tokens.Colour.muted)
                }
                SourceLines(lines: fact.sources, of: fact.name, openSources: openSources)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    /// How complete the data is. It sits directly under the fit, because it
    /// says how far to trust it. A firm limit that could not be tested here
    /// carries the mark of a trade-off: it is the one thing the person called
    /// firm, and it was not applied.
    struct CompletenessView: View {
        let completeness: Completeness

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                Text(completeness.words)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.text)
                    .frame(maxWidth: .infinity, alignment: .leading)
                Meter(filled: completeness.covered)
                ForEach(completeness.untested, id: \.self) { line in
                    HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                        Image(systemName: "arrow.left.arrow.right")
                            .foregroundStyle(Tokens.Colour.tradeoff)
                            .accessibilityHidden(true)
                        Text(line)
                            .foregroundStyle(Tokens.Colour.text)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .font(Tokens.Text.secondary)
                }
            }
        }
    }

    /// Each journey: where to, how, how long, and whether that is within the
    /// longest the person set. "Within" and "over" are words.
    struct JourneysView: View {
        let journeys: [Journey]
        /// With two journeys or more, which of them the fit is worked out from.
        let note: String?
        let openSources: () -> Void

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s3) {
                ForEach(Array(journeys.enumerated()), id: \.offset) { _, journey in
                    VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                        Text(verbatim: "\(ResultsCopy.Journeys.place) \(journey.place)")
                            .font(Tokens.Text.body.weight(.semibold))
                            .foregroundStyle(Tokens.Colour.text)
                        if let mode = journey.mode {
                            Named(name: ResultsCopy.Journeys.how, value: mode)
                        }
                        if let whole = journey.whole {
                            Named(name: ResultsCopy.Journeys.time, value: whole)
                        }
                        if let typical = journey.typical {
                            Named(name: ResultsCopy.Journeys.typical, value: typical)
                        }
                        if let missed = journey.missed {
                            Named(name: ResultsCopy.Journeys.missed, value: missed)
                        }
                        if let limit = journey.limit {
                            Beside(spacing: Tokens.Space.s2) {
                                Text(ResultsCopy.Journeys.limit)
                                    .font(Tokens.Text.secondary)
                                    .foregroundStyle(Tokens.Colour.muted)
                                if let verdict = journey.verdict {
                                    Text(verdict.word)
                                        .font(Tokens.Text.figure.weight(.bold))
                                        .foregroundStyle(
                                            verdict == .within ? Tokens.Colour.good : Tokens.Colour.tradeoff)
                                }
                                Text(limit)
                                    .font(Tokens.Text.figure)
                                    .foregroundStyle(Tokens.Colour.text)
                            }
                            .accessibilityElement(children: .combine)
                        }
                        SourceLines(lines: journey.sources, of: journey.place, openSources: openSources)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                if let note {
                    Text(note)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.text)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
    }

    /// What homes cost in an area. Every figure in words is a slot of the
    /// fact. The bar is a picture of the same range, and the words under it
    /// say where the budget falls, so it holds nothing the text does not.
    struct CostView: View {
        let cost: Cost
        let openSources: () -> Void

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                Text(cost.aMonth ? "\(cost.range) \(ResultsCopy.Cost.aMonth)" : cost.range)
                    .font(Tokens.Text.title)
                    .foregroundStyle(Tokens.Colour.text)
                    .frame(maxWidth: .infinity, alignment: .leading)
                if let segment = cost.segment {
                    Named(name: cost.label, value: segment)
                }
                if let what = cost.what {
                    Named(name: ResultsCopy.Cost.what, value: what)
                }
                if let soldIn = cost.soldIn {
                    Named(name: ResultsCopy.Cost.soldIn, value: soldIn)
                }
                if let middle = cost.middle {
                    Named(name: ResultsCopy.Cost.middle, value: middle)
                }
                if let month = cost.month {
                    Named(name: ResultsCopy.Cost.asOf, value: month)
                }
                if let confidence = cost.confidence {
                    Beside(spacing: Tokens.Space.s2) {
                        Text(ResultsCopy.Cost.confidence)
                            .font(Tokens.Text.secondary)
                            .foregroundStyle(Tokens.Colour.muted)
                        Text(confidence)
                            .font(Tokens.Text.figure)
                            .foregroundStyle(Tokens.Colour.text)
                        Pips(on: cost.pips)
                    }
                    .accessibilityElement(children: .combine)
                }
                if let budget = cost.budget {
                    Named(name: ResultsCopy.Cost.budget, value: budget)
                }
                // A price that is one number has a bar only where there is a budget to hold it against.
                if !cost.oneNumber || cost.bar.budget != nil {
                    CostBar(bar: cost.bar, oneNumber: cost.oneNumber)
                }
                if let falls = cost.falls {
                    Text(falls)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.text)
                }
                if let caveat = cost.caveat {
                    Text(caveat)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.text)
                }
                SourceLines(lines: cost.sources, of: cost.label, openSources: openSources)
            }
        }
    }

    /// One to three pips. The word beside them says it, and they repeat it.
    struct Pips: View {
        let on: Int

        var body: some View {
            HStack(spacing: Tokens.Space.s1) {
                ForEach(1...3, id: \.self) { pip in
                    Circle()
                        .strokeBorder(Tokens.Colour.mapLine, lineWidth: 1)
                        .background(Circle().fill(pip <= on ? Tokens.Colour.mapLine : Tokens.Colour.bg))
                        .frame(width: Tokens.Space.s2, height: Tokens.Space.s2)
                }
            }
            .accessibilityHidden(true)
        }
    }

    /// The range of cost as a bar, with the middle and the budget marked on it.
    struct CostBar: View {
        let bar: Bar
        /// True for a price that is one number: the bar then holds its middle and no range.
        var oneNumber = false

        var body: some View {
            GeometryReader { room in
                let width = room.size.width
                let high = room.size.height
                ZStack(alignment: .topLeading) {
                    Capsule()
                        .fill(Tokens.Colour.surface)
                        .overlay(Capsule().strokeBorder(Tokens.Colour.border, lineWidth: 1))
                        .frame(height: high / 2)
                        .offset(y: high / 4)
                    // An end the cost does not have is drawn nowhere.
                    if let lower = bar.lower, let upper = bar.upper {
                        Rectangle()
                            .fill(Tokens.Colour.mapBands[2])
                            .overlay(Rectangle().strokeBorder(Tokens.Colour.mapLine, lineWidth: 1))
                            .frame(width: max(width * (upper - lower) / 100, 1), height: high / 2)
                            .offset(x: width * lower / 100, y: high / 4)
                    }
                    Rectangle()
                        .fill(Tokens.Colour.mapLine)
                        .frame(width: 2, height: high / 2)
                        .offset(x: width * bar.median / 100 - 1, y: high / 4)
                    if let budget = bar.budget {
                        // The budget is a line the whole height of the bar, with a disc at its head.
                        Rectangle()
                            .fill(Tokens.Colour.accent)
                            .frame(width: 3, height: high)
                            .offset(x: width * budget / 100 - 1.5)
                        Circle()
                            .fill(Tokens.Colour.accent)
                            .frame(width: Tokens.Space.s3, height: Tokens.Space.s3)
                            .offset(x: width * budget / 100 - Tokens.Space.s3 / 2)
                    }
                }
            }
            .frame(height: Tokens.Space.s6)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(oneNumber ? ResultsCopy.Cost.pictureOfOne : ResultsCopy.Cost.picture)
        }
    }

    /// How the fit is worked out: each thing that counts, how much it counts,
    /// its share of the fit, what it adds, and what the data says of it.
    /// Closed at first. How the area scores on a thing is never shown.
    struct BreakdownView: View {
        let rows: [BreakdownRow]
        let of: String
        let openSources: () -> Void
        /// True in a row, which has opened to it already. On a card it is closed at first.
        var opened = false

        var body: some View {
            if opened {
                VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                    PartTitle(words: ResultsCopy.Breakdown.title)
                    table
                }
            } else {
                Opening(title: ResultsCopy.Breakdown.title, of: of) {
                    table
                }
            }
        }

        private var table: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s3) {
                Text(ResultsCopy.Breakdown.caption)
                    .font(Tokens.Text.secondary)
                    .foregroundStyle(Tokens.Colour.muted)
                ForEach(rows) { row in
                    VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                        Text(row.thing)
                            .font(Tokens.Text.body.weight(.semibold))
                            .foregroundStyle(Tokens.Colour.text)
                            .accessibilityAddTraits(.isHeader)
                        Named(name: ResultsCopy.Breakdown.weight, value: row.weight)
                        Named(name: ResultsCopy.Breakdown.share, value: row.share)
                        Named(name: ResultsCopy.Breakdown.adds, value: row.adds)
                        switch row.says {
                        case .nothing:
                            Named(name: ResultsCopy.Breakdown.says, value: ResultsCopy.Breakdown.hasNot)
                        case .something:
                            Named(name: ResultsCopy.Breakdown.says, value: ResultsCopy.Breakdown.has)
                        case .figures(let columns, let sources):
                            Text(ResultsCopy.Breakdown.says)
                                .font(Tokens.Text.secondary)
                                .foregroundStyle(Tokens.Colour.muted)
                            ForEach(columns) { column in
                                Named(name: column.name, value: column.value)
                            }
                            SourceLines(
                                lines: sources, of: "\(ResultsCopy.Breakdown.title): \(row.thing)",
                                openSources: openSources)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                Text(ResultsCopy.Breakdown.roundedDown)
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    /// What can be done with a result. Each button says what it would do, so
    /// that whether an area is saved or chosen is never told by colour alone.
    struct ActionsView: View {
        let area: AreaRef
        let refusal: RejectReason?
        let hands: Hands
        @Environment(\.dynamicTypeSize) var size

        var body: some View {
            let copy = ResultsCopy.Card.self
            let saved = hands.isSaved(area)
            let compared = hands.memory.isCompared(area)
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                Button(copy.open) { hands.open(area) }
                    .buttonStyle(.burroPrimary)
                    .accessibilityLabel(copy.of(copy.open, area.name))
                LazyVGrid(columns: columns, alignment: .leading, spacing: Tokens.Space.s2) {
                    let shortlist = saved ? ResultsCopy.Shortlist.remove : ResultsCopy.Shortlist.add
                    Button(shortlist) { hands.toggleShortlist(area) }
                        .accessibilityLabel(copy.of(shortlist, area.name))
                    let compare = compared ? copy.removeFromCompare : copy.addToCompare
                    Button(compare) { hands.toggleCompare(area) }
                        .disabled(!hands.canToggleCompare(area))
                        .accessibilityLabel(copy.of(compare, area.name))
                    Button(copy.onMap) { hands.showOnMap(area) }
                        .accessibilityLabel(copy.of(copy.onMap, area.name))
                    Button(copy.hideThis) { Task { await hands.hide(area) } }
                        .accessibilityLabel(copy.of(copy.hideThis, area.name))
                    if hands.canShare {
                        Button(ResultsCopy.Share.open) { hands.openShare() }
                    }
                    Button(ResultsCopy.Source.all) { hands.openSources() }
                }
                .buttonStyle(.burroSecondary)
                if !hands.canToggleCompare(area) {
                    Text(ResultsCopy.Tray.full)
                        .font(Tokens.Text.footnote)
                        .foregroundStyle(Tokens.Colour.muted)
                }
                if hands.app.shortlist.couldNotSave {
                    Text(ResultsCopy.Shortlist.couldNotSave)
                        .font(Tokens.Text.footnote)
                        .foregroundStyle(Tokens.Colour.error)
                }
                if let refusal, let words = ResultsCopy.word(for: refusal) {
                    Text(words)
                        .font(Tokens.Text.footnote)
                        .foregroundStyle(Tokens.Colour.error)
                }
            }
            .accessibilityElement(children: .contain)
            .accessibilityLabel(copy.of(copy.actions, area.name))
        }

        private var columns: [GridItem] {
            let one = GridItem(.flexible(), spacing: Tokens.Space.s2, alignment: .top)
            return size.isAccessibilitySize ? [one] : [one, one]
        }
    }

    /// The strip under a result's name: where the area sits on the vibes that
    /// were asked for, and on the others the API chose. It is shown and never
    /// scored: only what is in the search counts. A vibe is a band between
    /// two named ends, said in words beside the picture of it.
    struct StripView: View {
        let strip: [VibeShown]
        /// The area, to name the strip for a screen reader.
        let of: String

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s3) {
                ForEach(Array(strip.enumerated()), id: \.element.id) { at, vibe in
                    if let group = Results.group(before: at, in: strip) {
                        // Said once, where it can be seen, before the vibes it is true of.
                        Text(group)
                            .font(Tokens.Text.footnote.weight(.semibold))
                            .foregroundStyle(Tokens.Colour.muted)
                            .accessibilityHidden(true)
                    }
                    VibeLine(vibe, source: Results.sourceWords(of: vibe))
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityElement(children: .contain)
            .accessibilityLabel(VibeCopy.label(of))
        }
    }

    /// One result, in full or as a row.
    struct CardView: View {
        let card: Card
        let ground: Ground
        let hands: Hands

        var body: some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s4) {
                Button {
                    hands.choose(inList: card.area)
                } label: {
                    HeadingView(heading: card.heading)
                        .frame(minHeight: Tokens.Target.least)
                }
                .buttonStyle(.plain)
                .accessibilityHint(ResultsCopy.Card.showOnMap(card.heading.name))
                if card.selected {
                    Text(ResultsCopy.Card.selected)
                        .font(Tokens.Text.footnote.weight(.semibold))
                        .foregroundStyle(Tokens.Colour.text)
                }
                // Directly under the fit, on a card as on a row: it says how far the fit is to be trusted.
                if let completeness = card.completeness {
                    CompletenessView(completeness: completeness)
                }
                if !card.strip.isEmpty {
                    StripView(strip: card.strip, of: name)
                }
                if card.full {
                    full
                } else {
                    row
                }
            }
            .padding(Tokens.Space.s3)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Tokens.Colour.surface, in: RoundedRectangle(cornerRadius: Tokens.Radius.card))
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(
                        card.selected ? Tokens.Colour.mapLine : Tokens.Colour.border,
                        lineWidth: card.selected ? 3 : 1)
            )
            .accessibilityElement(children: .contain)
            .accessibilityAddTraits(card.selected ? .isSelected : [])
        }

        private var name: String { card.heading.name }

        @ViewBuilder
        private var full: some View {
            part(ResultsCopy.Card.whereTitle) {
                switch card.orientation {
                case .here(let sentence):
                    SentenceView(sentence: sentence, of: name, openSources: hands.openSources)
                case .waiting:
                    Skeleton()
                case .none, .failed, .hidden:
                    EmptyView()
                }
                switch card.station {
                case .here(let fact):
                    FactView(fact: fact, openSources: hands.openSources)
                case .waiting:
                    Skeleton()
                case .none, .failed, .hidden:
                    EmptyView()
                }
                if !ground.isEmpty {
                    Locator(ground: ground, areaId: card.area.areaId, name: name)
                }
            }
            part(ResultsCopy.Card.reasonsTitle) {
                switch card.reasons {
                case .here(let reasons) where reasons.isEmpty:
                    words(ResultsCopy.Card.noReasons)
                case .here(let reasons):
                    ForEach(Array(reasons.enumerated()), id: \.offset) { at, reason in
                        SentenceView(
                            sentence: reason, of: "\(name), \(at + 1)", openSources: hands.openSources)
                    }
                case .waiting:
                    Skeleton(lines: reasonsShown)
                case .failed:
                    words(ResultsCopy.Card.reasonsFailed, failed: true)
                case .none, .hidden:
                    EmptyView()
                }
            }
            if card.tradeOff != .hidden && card.tradeOff != .failed {
                part(ResultsCopy.Card.tradeOffTitle, mark: true) {
                    switch card.tradeOff {
                    case .here(let tradeOff):
                        SentenceView(
                            sentence: tradeOff.sentence, of: "\(name), \(ResultsCopy.Card.tradeOffTitle)",
                            openSources: hands.openSources)
                        if let limit = tradeOff.limit {
                            Text(limit)
                                .font(Tokens.Text.secondary.weight(.semibold))
                                .foregroundStyle(
                                    tradeOff.verdict == .within ? Tokens.Colour.good : Tokens.Colour.tradeoff)
                        }
                    case .none:
                        words(ResultsCopy.Card.noTradeOff)
                    case .waiting:
                        Skeleton()
                    case .failed, .hidden:
                        EmptyView()
                    }
                }
            }
            switch card.missing {
            case .here(let missing):
                part(ResultsCopy.Completeness.missingTitle) {
                    ForEach(Array(missing.enumerated()), id: \.offset) { _, sentence in
                        SentenceView(sentence: sentence, of: nil, openSources: hands.openSources)
                    }
                }
            case .waiting:
                part(ResultsCopy.Completeness.missingTitle) {
                    Skeleton(lines: card.held)
                }
            case .none, .failed, .hidden:
                EmptyView()
            }
            if !card.journeys.isEmpty {
                part(ResultsCopy.Journeys.title) {
                    JourneysView(
                        journeys: card.journeys, note: card.journeysNote, openSources: hands.openSources)
                }
            }
            part(ResultsCopy.Cost.title) {
                switch card.cost {
                case .here(let cost):
                    CostView(cost: cost, openSources: hands.openSources)
                case .waiting:
                    Skeleton(lines: 2)
                case .failed:
                    words(ResultsCopy.Card.detailsFailed, failed: true)
                case .none:
                    words(ResultsCopy.Cost.none)
                case .hidden:
                    EmptyView()
                }
            }
            if !card.breakdown.isEmpty {
                BreakdownView(rows: card.breakdown, of: name, openSources: hands.openSources)
            }
            ActionsView(area: card.area, refusal: card.refusal, hands: hands)
        }

        @ViewBuilder
        private var row: some View {
            Opening(title: ResultsCopy.Card.more, of: name) {
                VStack(alignment: .leading, spacing: Tokens.Space.s4) {
                    if !card.breakdown.isEmpty {
                        BreakdownView(
                            rows: card.breakdown, of: name, openSources: hands.openSources, opened: true)
                    }
                    if !card.journeys.isEmpty {
                        part(ResultsCopy.Journeys.title) {
                            JourneysView(
                                journeys: card.journeys, note: card.journeysNote,
                                openSources: hands.openSources)
                        }
                    }
                    ActionsView(area: card.area, refusal: card.refusal, hands: hands)
                }
            }
        }

        private func part<Content: View>(
            _ title: String, mark: Bool = false, @ViewBuilder content: () -> Content
        ) -> some View {
            VStack(alignment: .leading, spacing: Tokens.Space.s2) {
                HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                    if mark {
                        // The mark goes with the word "Trade-off", which says it.
                        Image(systemName: "arrow.left.arrow.right")
                            .font(Tokens.Text.headline)
                            .foregroundStyle(Tokens.Colour.tradeoff)
                            .accessibilityHidden(true)
                    }
                    PartTitle(words: title)
                }
                content()
            }
        }

        private func words(_ text: String, failed: Bool = false) -> some View {
            Text(text)
                .font(Tokens.Text.body)
                .foregroundStyle(failed ? Tokens.Colour.error : Tokens.Colour.text)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}
