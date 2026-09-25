import Foundation

// The chips: what Burro understood, one for each thing the spec holds.
// docs/design/web.md, section 5.2. It mirrors apps/web/src/lib/search/chips.ts.
//
// A chip is drawn from the spec the API returned, never from the edits. Its
// words are names the API gave (a feature's label, a place's name) and the
// app's words for the codes. A part is marked "assumed" when nobody chose it.

/// One part of a chip: how a journey is made, or whether a limit is firm.
struct ChipPart: Hashable, Sendable {
    let text: String
    /// True when nobody chose this part: the words did not say it.
    let assumed: Bool
}

/// What a chip is for. It holds an id of the release, never anything typed.
enum ChipKind: Hashable, Sendable {
    case tenure
    case budget
    case place(String)
    case feature(FeatureId)
    case tag(TagId)
    case area(String)
    /// Which journey counts, once there are two places to choose between.
    case journeys
    /// The settings nobody chose, as one chip.
    case usual

    /// The part of the search the chip is for, as an edit names it.
    var key: ChipKey? {
        switch self {
        case .tenure: return .tenure
        case .budget: return .budget
        case .place(let id): return .place(id)
        case .feature(let id): return .feature(id)
        case .tag(let id): return .tag(id)
        case .area(let id): return .area(id)
        case .journeys: return .journeys
        case .usual: return nil
        }
    }

    /// True when the chip opens the control the settings hold for it.
    var opensAControl: Bool {
        switch self {
        case .tenure, .budget, .place, .journeys, .feature, .tag: return true
        case .area, .usual: return false
        }
    }
}

struct SearchChip: Hashable, Sendable, Identifiable {
    let kind: ChipKind
    let label: String
    let parts: [ChipPart]
    /// True when the chip as a whole was assumed, or any part of it was.
    let assumed: Bool
    /// The edit that takes it out, where it can be taken out.
    let removal: Operations?

    var id: ChipKind { kind }

    /// True when the word goes after the label, because no one part carries it.
    var assumedAsAWhole: Bool {
        assumed && !parts.contains { $0.assumed }
    }

    /// The whole chip as plain words, as it is drawn and as it is read out.
    var reads: String {
        var said = label
        if assumedAsAWhole { said += " \(SearchCopy.Chips.assumed)" }
        for part in parts {
            said += ", \(part.text)"
            if part.assumed { said += " \(SearchCopy.Chips.assumed)" }
        }
        return said
    }
}

enum SearchChips {
    /// True of a vibe whose recipe holds a figure of recorded crime. Which one does is the API's to say.
    static func holdsRecordedCrime(_ tag: Tag, _ features: [Metric]) -> Bool {
        tag.terms.contains { term in
            features.first { $0.featureId == term.featureId }?.dimension == .crime
        }
    }

    /// What the recipe of a vibe counts that is recorded crime, as one line.
    /// `nil` where it counts none. The name of each part is the API's.
    static func countsCrime(_ tag: Tag, in meta: MetaData) -> String? {
        let parts = tag.terms.compactMap { term in
            meta.features.first { $0.featureId == term.featureId && $0.dimension == .crime }?.label
        }
        guard !parts.isEmpty else { return nil }
        return "\(SearchCopy.crimeCounts): \(parts.joined(separator: "; "))."
    }

    /// Whether a weight counts for anything. A spec keeps an entry of 0 for a
    /// thing a person took off, so that a change of tenure does not bring its
    /// default back (contract section 5.1). Such an entry counts for nothing,
    /// and is drawn as off.
    static func counts(_ weight: Double?) -> Bool {
        (weight ?? 0) > 0
    }

    /// The name of each place of the spec: the release's own name for it, from the
    /// answer that brought the spec. A place no answer named is said to have no name,
    /// and is never shown by a number or by what was typed.
    static func names(of spec: PreferenceSpec, held: [String: String]) -> [String: String] {
        var names: [String: String] = [:]
        for commute in spec.commutes {
            names[commute.placeId] = held[commute.placeId] ?? SearchCopy.Place.noName
        }
        return names
    }

    /// A budget as the person gave it: pounds, and "a month" for a rent.
    static func budget(_ amount: Int, _ tenure: Tenure) -> String {
        let pounds = FormNumbers.grouped(amount)
        return tenure == .rent ? SettingsCopy.Budget.aMonth(pounds) : SettingsCopy.Budget.pounds(pounds)
    }

    /// The chips as the screen draws them: the search's own, and the one that
    /// says which journey counts.
    static func of(_ state: SearchState) -> [SearchChip] {
        withWhichJourneyCounts(
            of(
                state.spec, features: state.meta.features, tags: state.meta.tags, areas: state.areas,
                placeNames: state.placeNames, assumed: state.assumed, guides: state.meta.roughGuides),
            state.spec)
    }

    /// The chips of the search, with the one that says which journey counts
    /// after the places, once there are two of them. With one place there is
    /// nothing to choose between. With two, only one journey feeds the fit
    /// unless the person says otherwise, and until they do the chip is marked
    /// "assumed". It is for the eye alone: a stored search says nothing of it.
    static func withWhichJourneyCounts(_ chips: [SearchChip], _ spec: PreferenceSpec) -> [SearchChip] {
        // A choice the app has no word for is left out.
        guard spec.commutes.count >= 2, let label = CodeCopy.combine(spec.commuteCombine) else {
            return chips
        }
        let from = spec.commuteCombineFrom
        let which = SearchChip(
            kind: .journeys, label: label, parts: [],
            assumed: from == .default || from == .inferred, removal: nil)
        let after = chips.lastIndex { chip in
            if case .place = chip.kind { return true }
            return false
        }
        var drawn = chips
        drawn.insert(which, at: after.map { $0 + 1 } ?? chips.count)
        return drawn
    }

    /// What a vibe that is a rough guide says of itself where it stands in a
    /// search, in one line under the chips: its name, its label and the
    /// sentence that says why. The name, the label and the sentence are the
    /// API's. One line for each such vibe that counts, in the order of the spec.
    static func rough(in spec: PreferenceSpec, meta: MetaData) -> [String] {
        spec.tags.compactMap { weight in
            guard counts(weight.weight),
                let tag = meta.tags.first(where: { $0.tagId == weight.tagId }),
                let told = Vibes.rough(tag, in: meta.roughGuides)
            else { return nil }
            return "\(tag.label): \(Vibes.said(told))"
        }
    }

    static func of(
        _ spec: PreferenceSpec,
        features: [Metric],
        tags: [Tag],
        areas: [AreaSummary],
        placeNames: [String: String],
        assumed: Assumed,
        guides: [RoughGuide] = []
    ) -> [SearchChip] {
        func has(_ key: ChipKey, _ code: AssumptionCode) -> Bool {
            assumed[key]?.contains(code) ?? false
        }
        func notChosen(_ provenance: Provenance) -> Bool {
            provenance == .default || provenance == .inferred
        }
        func chip(
            _ kind: ChipKind, _ label: String, parts: [ChipPart?] = [], assumed: Bool = false,
            removal: Operations? = nil
        ) -> SearchChip {
            // A code the app has no word for makes a part with nothing in it, which is left out.
            let said = parts.compactMap { $0 }.filter { !$0.text.isEmpty }
            return SearchChip(
                kind: kind, label: label, parts: said,
                assumed: assumed || said.contains { $0.assumed }, removal: removal)
        }
        func firmness(_ strictness: Strictness, _ key: ChipKey) -> ChipPart? {
            switch strictness {
            case .hard: return ChipPart(text: SearchCopy.Chips.firm, assumed: has(key, .strictness))
            case .soft: return ChipPart(text: SearchCopy.Chips.flexible, assumed: has(key, .strictness))
            case .unlisted: return nil
            }
        }

        var chips: [SearchChip] = []

        if let tenure = CodeCopy.tenure(spec.tenure) {
            chips.append(
                chip(.tenure, tenure, assumed: notChosen(spec.tenureFrom) || has(.tenure, .tenure)))
        }

        if let amount = spec.budget.amount {
            chips.append(
                chip(
                    .budget, budget(amount, spec.tenure),
                    parts: [
                        CodeCopy.segment(spec.budget.segment).map {
                            ChipPart(text: $0, assumed: has(.budget, .segment))
                        },
                        firmness(spec.budget.strictness, .budget),
                    ],
                    removal: Edits.budgetClear()))
        }

        let names = names(of: spec, held: placeNames)
        for commute in spec.commutes {
            let key = ChipKey.place(commute.placeId)
            chips.append(
                chip(
                    .place(commute.placeId), names[commute.placeId] ?? "",
                    parts: [
                        CodeCopy.mode(commute.mode).map { ChipPart(text: $0, assumed: has(key, .mode)) },
                        ChipPart(
                            text: SearchCopy.Chips.within(commute.maxMinutes),
                            assumed: has(key, .maxMinutes)),
                        firmness(commute.strictness, key),
                    ],
                    removal: Edits.placeRemove(commute.placeId)))
        }

        // An entry of 0 is a thing a person took off. It is said to count for nothing, so
        // that a wish to ignore the high street is never shown as a wish for one, and it
        // has nothing to remove.
        let takenOff = ChipPart(text: SearchCopy.Chips.off, assumed: false)

        for weight in spec.weights where weight.provenance != .default {
            let metric = features.first { $0.featureId == weight.featureId }
            let key = ChipKey.feature(weight.featureId)
            var direction: ChipPart?
            if metric?.polarity == .either {
                switch weight.direction {
                case .more: direction = ChipPart(text: SearchCopy.Chips.more, assumed: has(key, .direction))
                case .less: direction = ChipPart(text: SearchCopy.Chips.fewer, assumed: has(key, .direction))
                case .unlisted: direction = nil
                }
            }
            let on = counts(weight.weight)
            chips.append(
                chip(
                    .feature(weight.featureId), metric?.label ?? weight.featureId.rawValue,
                    parts: on ? [direction] : [takenOff],
                    assumed: weight.provenance == .inferred || has(key, .weight),
                    removal: on ? Edits.featureOff(weight.featureId) : nil))
        }

        for weight in spec.tags {
            let key = ChipKey.tag(weight.tagId)
            let on = counts(weight.weight)
            let tag = tags.first { $0.tagId == weight.tagId }
            // A scale says which of its ends is asked for. Both names are the API's.
            var label = tag?.label ?? weight.tagId.rawValue
            if on, let tag, tag.shape == .scale, let low = tag.lowEnd, let high = tag.highEnd {
                label = SearchCopy.Chips.towards(tag.label, weight.toward == .low ? low : high)
            }
            // A vibe whose recipe holds recorded crime says so wherever it is in a search.
            let crime =
                tag.map { holdsRecordedCrime($0, features) } == true
                ? ChipPart(text: SearchCopy.crimeChip, assumed: false) : nil
            // A vibe that is a rough guide says so on its chip, in the API's own word.
            let rough = tag.flatMap { Vibes.rough($0, in: guides) }
                .map { ChipPart(text: $0.label, assumed: false) }
            chips.append(
                chip(
                    .tag(weight.tagId), label,
                    parts: on ? [rough, crime] : [takenOff],
                    assumed: weight.provenance == .inferred || has(key, .weight),
                    removal: on ? Edits.tagOff(weight.tagId) : nil))
        }

        for rule in spec.areas {
            let how: ChipPart?
            switch rule.rule {
            case .exclude: how = ChipPart(text: SearchCopy.Chips.hidden, assumed: false)
            case .only: how = ChipPart(text: SearchCopy.Chips.only, assumed: false)
            case .unlisted: how = nil
            }
            chips.append(
                chip(
                    .area(rule.areaId),
                    areas.first { $0.areaId == rule.areaId }?.name ?? rule.areaId,
                    parts: [how], removal: Edits.areaClear(rule.areaId)))
        }

        let usual = spec.weights.filter { $0.provenance == .default }.count
        if usual > 0 {
            chips.append(chip(.usual, SearchCopy.Chips.usual(usual), assumed: true))
        }

        return chips
    }
}
