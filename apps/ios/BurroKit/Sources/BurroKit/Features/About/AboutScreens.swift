import SwiftUI

/// The methods: how the ranking works, what is measured, the recipe of each
/// vibe, where a search starts, the limits, the release, and how a person's
/// words are handled. Every figure and every definition is the API's.
struct MethodsScreen: View {
    @Environment(SearchStore.self) private var search

    var body: some View {
        let meta = search.state.meta
        AboutScroll(AboutCopy.Links.methods, title: AboutCopy.Methods.title, lead: AboutCopy.Methods.lead) {
            AboutSection(AboutCopy.Methods.rankingTitle) {
                AboutPoints(AboutCopy.Methods.ranking)
            }
            AboutSection(AboutCopy.Methods.featuresTitle) {
                Text(AboutCopy.Methods.featuresLead)
                ForEach(AboutPage.features(meta)) { group in
                    AboutSection(group.title, level: .inner) {
                        if group.features.isEmpty {
                            Text(AboutCopy.Methods.noFeatures)
                                .foregroundStyle(Tokens.Colour.muted)
                        }
                        ForEach(group.features) { feature in
                            FeatureEntry(feature: feature)
                        }
                    }
                }
            }
            AboutSection(AboutCopy.Methods.tagsTitle) {
                Text(AboutCopy.Methods.tagsLead)
                ForEach(AboutPage.tags(meta)) { tag in
                    AboutSection(tag.tag.label, level: .inner) {
                        // A vibe that is a rough guide says so under its name, and says why.
                        if let rough = tag.rough {
                            Text(verbatim: rough)
                                .foregroundStyle(Tokens.Colour.text)
                        }
                        AboutRows(
                            tag.terms.map { term in
                                AboutRow(
                                    name: term.feature,
                                    value: term.reading.isEmpty ? term.share : "\(term.reading). \(term.share)")
                            })
                    }
                }
            }
            AboutSection(AboutCopy.Methods.defaultsTitle) {
                Text(AboutCopy.Methods.defaultsLead)
                ForEach(AboutPage.defaults(meta)) { start in
                    AboutSection(start.title, level: .inner) {
                        if let home = start.home {
                            AboutRows([AboutRow(name: AboutCopy.Methods.home, value: home)])
                        }
                        AboutRows(start.rows)
                    }
                }
            }
            AboutSection(AboutCopy.Methods.limitsTitle) {
                Text(AboutCopy.Methods.limitsLead)
                AboutRows(AboutPage.limits(meta))
            }
            AboutSection(AboutCopy.Methods.journeysTitle) {
                AboutPoints(AboutCopy.Methods.journeysPoints)
            }
            if let rents = meta.rents {
                // Each rent of the data is of a wider place than an area. What is said of the
                // rents is the API's: that each is of a district or a borough, and what their
                // publisher advises. How an area takes one, and how a budget is held, follows.
                AboutSection(AboutCopy.Methods.rentsTitle) {
                    Text(verbatim: "\(rents.ofAPlace) \(rents.caution)")
                    AboutPoints(AboutCopy.Methods.rentsPoints)
                }
            }
            AboutSection(AboutCopy.Methods.confidenceTitle) {
                Text(AboutCopy.Methods.confidenceLead)
                AboutPoints(AboutPage.confidence)
            }
            AboutSection(AboutCopy.Methods.releaseTitle) {
                AboutRows(AboutPage.releaseInFull(meta))
            }
            AboutSection(AboutCopy.Words.title) {
                AboutPoints(AboutCopy.Words.points(reader: meta.reader.notice))
            }
        }
    }
}

/// One feature: its name and its definition, as the release states them, and
/// its unit, its period and its source.
private struct FeatureEntry: View {
    let feature: AboutFeature

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            Text(verbatim: feature.metric.label)
                .font(Tokens.Text.body.weight(.semibold))
                .accessibilityAddTraits(.isHeader)
            Text(verbatim: feature.metric.definition)
            if !feature.metric.rankable {
                Text(AboutCopy.Methods.notRanked)
                    .foregroundStyle(Tokens.Colour.muted)
            }
            AboutRows(feature.rows)
        }
        .fixedSize(horizontal: false, vertical: true)
        .padding(.bottom, Tokens.Space.s2)
    }
}

/// Every source of the release, with its licence, the credit its publisher
/// asks for, and the features that came from it. Every word about a source is
/// the API's.
struct SourcesScreen: View {
    @Environment(SearchStore.self) private var search

    var body: some View {
        let sources = AboutPage.sources(search.state.meta)
        AboutScroll(AboutCopy.Links.sources, title: AboutCopy.Sources.title, lead: AboutCopy.Sources.lead) {
            if sources.isEmpty {
                Text(AboutCopy.Sources.none)
            }
            ForEach(sources) { source in
                AboutSection(source.source.name) {
                    Text(verbatim: source.source.attribution)
                        .fixedSize(horizontal: false, vertical: true)
                    // What the publisher's terms ask to be said wherever its credit is shown.
                    if let said = source.said {
                        Text(verbatim: said)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    AboutRows(source.rows)
                    page(of: source)
                    AboutSection(AboutCopy.Sources.usedFor, level: .inner) {
                        if source.usedFor.isEmpty {
                            Text(AboutCopy.Sources.notUsed)
                                .foregroundStyle(Tokens.Colour.muted)
                        } else {
                            AboutPoints(source.usedFor)
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func page(of source: AboutSource) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(AboutCopy.Sources.link)
                .font(Tokens.Text.secondary)
                .foregroundStyle(Tokens.Colour.muted)
            if let address = source.address {
                // It opens in the phone's browser. The app shows no page of anyone else's.
                Link(destination: address) {
                    Text(verbatim: source.addressWords)
                        .underline()
                        .multilineTextAlignment(.leading)
                        .frame(minHeight: Tokens.Target.least, alignment: .leading)
                        .contentShape(Rectangle())
                }
                .accessibilityHint(Text(AboutCopy.Sources.opens))
            } else {
                Text(verbatim: source.addressWords)
            }
        }
    }
}

/// The accessibility statement: what the app is built to do, what is checked,
/// what has not been tested, and how to report a problem.
struct AccessibilityScreen: View {
    var body: some View {
        let copy = AboutCopy.Accessibility.self
        AboutScroll(AboutCopy.Links.accessibility, title: copy.title, lead: copy.lead) {
            AboutSection(copy.builtTitle) {
                AboutPoints(copy.built(target: Int(Tokens.Target.least)))
            }
            AboutSection(copy.checkedTitle) {
                AboutPoints(copy.checked)
            }
            AboutSection(copy.shortTitle) {
                AboutPoints(copy.short)
            }
            AboutSection(copy.notTestedTitle) {
                Text(copy.notTestedLead)
                AboutPoints(copy.notTested)
            }
            AboutSection(copy.reportTitle) {
                Text(copy.noAddressYet)
            }
            if let day = AboutDate.readable(AboutPage.statementUpdated) {
                Text(verbatim: "\(copy.updated): \(day)")
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
            }
        }
    }
}

/// A screen of About: its name, a line that says what it is, and its parts.
///
/// The bar at the top holds the short name the link to the screen had. A
/// longer name is drawn on the screen itself, where it can wrap.
struct AboutScroll<Content: View>: View {
    private let name: String
    private let title: String
    private let lead: String
    private let content: Content

    init(_ name: String, title: String, lead: String, @ViewBuilder content: () -> Content) {
        self.name = name
        self.title = title
        self.lead = lead
        self.content = content()
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Space.s5) {
                if title != name {
                    Text(title)
                        .font(Tokens.Text.title)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityAddTraits(.isHeader)
                }
                Text(lead)
                    .fixedSize(horizontal: false, vertical: true)
                content
            }
            .font(Tokens.Text.body)
            .foregroundStyle(Tokens.Colour.text)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(Tokens.Space.gutter)
        }
        .background(Tokens.Colour.bg)
        .navigationTitle(name)
    }
}
