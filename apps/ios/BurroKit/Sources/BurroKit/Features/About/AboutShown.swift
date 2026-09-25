import Foundation

// What the About screens show, worked out from what the meta route served.
// Every name, definition, licence and credit is the API's, shown as it came.
// The app writes a date out in words, and groups the thousands of a limit of
// the form. It formats nothing about a place.

/// A name and what goes with it: one row of a list of facts about the release.
struct AboutRow: Hashable, Sendable, Identifiable {
    let name: String
    let value: String
    /// True for an id or a version, which is drawn in a fixed-width face.
    var isCode = false

    var id: String { name }
}

/// One source of data, as its entry says it.
struct AboutSource: Hashable, Sendable, Identifiable {
    let source: Source
    /// What the publisher's terms ask to be said wherever its credit is shown, in the API's
    /// words. Nothing where nothing is asked.
    let said: String?
    let rows: [AboutRow]
    /// The publisher's page, where the field holds a web address.
    let address: URL?
    /// What stands for the page when there is none to open: the field as it came, or "None".
    let addressWords: String
    /// The labels of the features that came from it.
    let usedFor: [String]

    var id: String { source.sourceId }
}

/// One feature, as the methods say it.
struct AboutFeature: Hashable, Sendable, Identifiable {
    let metric: Metric
    let rows: [AboutRow]
    var id: String { metric.featureId.rawValue }
}

/// One group of features: a dimension, by the app's word for it.
struct AboutFeatureGroup: Hashable, Sendable, Identifiable {
    let title: String
    let features: [AboutFeature]
    var id: String { title }
}

/// One tag, with the formula it is.
struct AboutTag: Hashable, Sendable, Identifiable {
    struct Term: Hashable, Sendable, Identifiable {
        let feature: String
        let reading: String
        let share: String
        var id: String { feature }
    }

    let tag: Tag
    let terms: [Term]
    /// What the vibe says of itself where it is a rough guide: its label and
    /// the sentence that says why, as the API serves them. `nil` for a vibe
    /// that is as sure as the rest.
    var rough: String?
    var id: String { tag.tagId.rawValue }
}

/// Where a search starts, for a renter or for a buyer.
struct AboutDefaults: Hashable, Sendable, Identifiable {
    let title: String
    let home: String?
    let rows: [AboutRow]
    var id: String { title }
}

enum AboutPage {
    /// The day the accessibility statement was last gone over.
    static let statementUpdated = DateComponents(year: 2026, month: 9, day: 23)

    // MARK: - The release

    /// What the first screen of About says of the release: which it is, and
    /// which engine ranked it.
    static func release(_ meta: MetaData) -> [AboutRow] {
        [
            AboutRow(name: AboutCopy.Release.release, value: meta.releaseId, isCode: true),
            AboutRow(name: AboutCopy.Release.engine, value: meta.engineVersion, isCode: true),
            AboutRow(name: AboutCopy.Methods.built, value: AboutDate.readable(meta.builtAt)),
            AboutRow(name: AboutCopy.Methods.synthetic, value: yesOrNo(meta.synthetic)),
            AboutRow(name: AboutCopy.Methods.preview, value: yesOrNo(meta.preview)),
        ]
    }

    /// Everything the methods say of the release.
    static func releaseInFull(_ meta: MetaData) -> [AboutRow] {
        let copy = AboutCopy.Methods.self
        return [
            AboutRow(name: copy.release, value: meta.releaseId, isCode: true),
            AboutRow(name: copy.built, value: AboutDate.readable(meta.builtAt)),
            AboutRow(name: copy.engine, value: meta.engineVersion, isCode: true),
            AboutRow(name: copy.catalogue, value: String(meta.catalogueVersion), isCode: true),
            AboutRow(name: copy.synthetic, value: yesOrNo(meta.synthetic)),
            AboutRow(name: copy.preview, value: yesOrNo(meta.preview)),
            AboutRow(name: copy.areas, value: FormNumbers.grouped(meta.counts.neighbourhoods)),
            AboutRow(name: copy.rankable, value: FormNumbers.grouped(meta.counts.rankable)),
            AboutRow(name: copy.placesCount, value: FormNumbers.grouped(meta.counts.places)),
            AboutRow(name: copy.stations, value: FormNumbers.grouped(meta.counts.stations)),
            AboutRow(name: copy.destinations, value: FormNumbers.grouped(meta.counts.destinations)),
        ]
    }

    private static func yesOrNo(_ value: Bool) -> String {
        value ? AboutCopy.Methods.yes : AboutCopy.Methods.no
    }

    // MARK: - The methods

    /// Every feature of the release, grouped by dimension, in the order they
    /// are shown. A dimension the release carries nothing in is still named,
    /// with nothing under it, so that what is missing is said.
    static func features(_ meta: MetaData) -> [AboutFeatureGroup] {
        let names = sourceNames(meta)
        return CodeCopy.dimensionOrder.compactMap { dimension in
            guard let title = CodeCopy.dimension(dimension) else { return nil }
            let inGroup = meta.features.filter { $0.dimension == dimension }
            return AboutFeatureGroup(
                title: title,
                features: inGroup.map { metric in
                    var rows = [
                        AboutRow(name: AboutCopy.Methods.unit, value: metric.unit),
                        AboutRow(name: AboutCopy.Methods.period, value: metric.vintage),
                    ]
                    if let polarity = CodeCopy.polarity(metric.polarity) {
                        rows.append(AboutRow(name: AboutCopy.Methods.polarity, value: polarity))
                    }
                    if !metric.sourceIds.isEmpty {
                        rows.append(
                            AboutRow(
                                name: AboutCopy.Methods.sources,
                                value: metric.sourceIds.map { names[$0] ?? $0 }.joined(separator: ", ")))
                    }
                    return AboutFeature(metric: metric, rows: rows.filter { !$0.value.isEmpty })
                })
        }
    }

    /// The recipe of each vibe. A part the release does not carry is named as
    /// the API names it, and said to be missing. It is never shown by its code.
    static func tags(_ meta: MetaData) -> [AboutTag] {
        let labels = featureLabels(meta)
        return meta.tags.map { tag in
            let waited = ReleaseHolds.recipe(of: tag.tagId, in: meta)?.waitsOn ?? []
            return AboutTag(
                tag: tag,
                terms: tag.terms.map { term in
                    let carried = labels[term.featureId]
                    let named = waited.first { $0.featureId == term.featureId }?.label
                    let reading = CodeCopy.reading(term.reading) ?? ""
                    return AboutTag.Term(
                        feature: carried ?? named ?? AboutCopy.Methods.notCarried,
                        reading: carried == nil
                            ? [VibeCopy.notYet, reading].filter { !$0.isEmpty }.joined(separator: ". ")
                            : reading,
                        share: AboutCopy.Methods.share(term.hundredths))
                },
                rough: Vibes.rough(tag, in: meta.roughGuides).map(Vibes.said))
        }
    }

    /// Where a search starts, for each tenure the app has a word for.
    static func defaults(_ meta: MetaData) -> [AboutDefaults] {
        let labels = featureLabels(meta)
        return [meta.defaults.rent, meta.defaults.buy].compactMap { spec in
            guard let title = CodeCopy.tenure(spec.tenure) else { return nil }
            var rows = [
                AboutRow(
                    name: AboutCopy.Methods.budget,
                    value: counted(spec.budget.weight, CodeCopy.strictness(spec.budget.strictness))),
                AboutRow(
                    name: AboutCopy.Methods.journeys,
                    value: counted(
                        spec.commuteWeight,
                        [CodeCopy.combine(spec.commuteCombine), CodeCopy.basis(spec.ptBasis)]
                            .compactMap { $0 }.joined(separator: ". "))),
            ]
            rows += spec.weights.map { weight in
                AboutRow(
                    name: labels[weight.featureId] ?? weight.featureId.rawValue,
                    value: counted(weight.weight, CodeCopy.direction(weight.direction)))
            }
            return AboutDefaults(title: title, home: CodeCopy.segment(spec.budget.segment), rows: rows)
        }
    }

    /// How much something counts, and which way, as one value: "80 of 100. Flexible".
    private static func counted(_ weight: Double, _ how: String?) -> String {
        let share = AboutCopy.Methods.share(WeightScale.hundredths(weight))
        guard let how, !how.isEmpty else { return share }
        return "\(share). \(how)"
    }

    /// The limits the form keeps to.
    static func limits(_ meta: MetaData) -> [AboutRow] {
        let limits = meta.limits
        let copy = AboutCopy.Methods.self
        func money(_ money: MoneyLimits) -> String {
            copy.money(
                FormNumbers.grouped(money.minimum), FormNumbers.grouped(money.maximum),
                FormNumbers.grouped(money.unit))
        }
        var rows = [
            AboutRow(name: copy.rent, value: money(limits.rent)),
            AboutRow(name: copy.buy, value: money(limits.buy)),
            AboutRow(name: copy.minutes, value: copy.minutesBetween(limits.minutesMin, limits.minutesMax)),
        ]
        let cutoffs: [(Mode, Int)] = [
            (.pt, limits.cutoffMinutes.pt), (.cycle, limits.cutoffMinutes.cycle),
            (.walk, limits.cutoffMinutes.walk),
        ]
        for (mode, minutes) in cutoffs {
            guard let word = CodeCopy.mode(mode) else { continue }
            rows.append(AboutRow(name: "\(copy.cutoff): \(word)", value: copy.minutes(minutes)))
        }
        rows += [
            AboutRow(name: copy.places, value: String(limits.maxCommutes)),
            AboutRow(name: copy.text, value: copy.characters(FormNumbers.grouped(limits.maxText))),
            AboutRow(
                name: copy.weightStep,
                value: copy.share(WeightScale.hundredths(limits.weightUnit))),
        ]
        return rows
    }

    /// How many rents or prices must be on record for a range to be called
    /// sure, as contract 2.5 has it. A test holds these to the contract.
    static let recordedForHigh = 50
    static let recordedForMedium = 10

    /// What each word for how sure a cost is means.
    static let confidence: [String] = [
        AboutCopy.Methods.high(atLeast: recordedForHigh),
        AboutCopy.Methods.medium(from: recordedForMedium, to: recordedForHigh - 1),
        AboutCopy.Methods.low,
        AboutCopy.Methods.unstated,
    ]

    // MARK: - The sources

    /// Every source of the release, with its licence, the credit its publisher
    /// asks for, what its terms ask to be said with the credit, and the features
    /// that came from it.
    static func sources(_ meta: MetaData) -> [AboutSource] {
        meta.attributions.map { source in
            let address = webAddress(source.url)
            let field = source.url.trimmingCharacters(in: .whitespacesAndNewlines)
            return AboutSource(
                source: source,
                said: source.saidWithAttribution.flatMap { $0.isEmpty ? nil : $0 },
                rows: [
                    AboutRow(name: AboutCopy.Sources.publisher, value: source.publisher),
                    AboutRow(name: AboutCopy.Sources.licence, value: source.licence),
                    AboutRow(name: AboutCopy.Sources.retrieved, value: AboutDate.readable(source.retrievedOn)),
                ].filter { !$0.value.isEmpty },
                address: address,
                addressWords: field.isEmpty ? AboutCopy.Sources.noLink : field,
                usedFor: meta.features
                    .filter { $0.sourceIds.contains(source.sourceId) }
                    .map(\.label))
        }
    }

    /// A web address is opened only if it is one. Anything else in the field is shown as text.
    static func webAddress(_ field: String) -> URL? {
        let text = field.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, let parts = URLComponents(string: text),
            let scheme = parts.scheme?.lowercased(), scheme == "https" || scheme == "http",
            let host = parts.host, !host.isEmpty,
            parts.user == nil, parts.password == nil
        else { return nil }
        return parts.url
    }

    // MARK: - The choice

    /// What About says of the choice the person made about their words.
    static func choice(_ choice: ConsentChoice?) -> String {
        switch choice {
        case .allowed: return AboutCopy.Choice.allowed
        case .settingsOnly: return AboutCopy.Choice.settingsOnly
        case nil: return AboutCopy.Choice.notChosen
        }
    }

    // MARK: - Names

    private static func sourceNames(_ meta: MetaData) -> [String: String] {
        Dictionary(meta.attributions.map { ($0.sourceId, $0.name) }, uniquingKeysWith: { first, _ in first })
    }

    private static func featureLabels(_ meta: MetaData) -> [FeatureId: String] {
        Dictionary(meta.features.map { ($0.featureId, $0.label) }, uniquingKeysWith: { first, _ in first })
    }
}

/// How a date the API sent is written for a person to read.
///
/// Only dates are written out here. A figure about a place arrives already
/// written, in a fact's slots, and is shown as it came.
enum AboutDate {
    private static let british = Locale(identifier: "en_GB")

    private static let calendar: Calendar = {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(secondsFromGMT: 0) ?? .gmt
        calendar.locale = british
        return calendar
    }()

    /// A date or a timestamp, as "23 September 2026", and a month, as "August
    /// 2026". Anything else is returned as it came: a year, or a period, is
    /// the release's own words.
    static func readable(_ value: String) -> String {
        let day = value.split(separator: "T", maxSplits: 1, omittingEmptySubsequences: false)
        guard let first = day.first, day.count == 1 || (day.count == 2 && day[1].hasSuffix("Z")) else {
            return value
        }
        let parts = first.split(separator: "-", omittingEmptySubsequences: false)
        let numbers = parts.compactMap { part -> Int? in
            part.allSatisfy { $0.isASCII && $0.isNumber } ? Int(part) : nil
        }
        guard numbers.count == parts.count, parts.first?.count == 4,
            parts.dropFirst().allSatisfy({ $0.count == 2 })
        else { return value }
        switch numbers.count {
        case 3:
            return readable(DateComponents(year: numbers[0], month: numbers[1], day: numbers[2])) ?? value
        case 2 where day.count == 1:
            guard let date = date(DateComponents(year: numbers[0], month: numbers[1], day: 1)) else {
                return value
            }
            return date.formatted(
                Date.FormatStyle(locale: british, calendar: calendar, timeZone: calendar.timeZone)
                    .month(.wide).year())
        default:
            return value
        }
    }

    /// A day, written out. `nil` when there is no such day.
    static func readable(_ day: DateComponents) -> String? {
        date(day)?.formatted(
            Date.FormatStyle(locale: british, calendar: calendar, timeZone: calendar.timeZone)
                .day().month(.wide).year())
    }

    private static func date(_ day: DateComponents) -> Date? {
        var asked = day
        asked.calendar = calendar
        asked.timeZone = calendar.timeZone
        guard asked.isValidDate(in: calendar) else { return nil }
        return calendar.date(from: asked)
    }
}
