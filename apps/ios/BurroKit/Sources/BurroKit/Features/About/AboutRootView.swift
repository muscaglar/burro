import SwiftUI

/// The first screen of the About tab: what Burro is, how a person's words are
/// handled and the choice they made about it, the way to the methods, the
/// sources and the accessibility statement, and which release and engine
/// the app is reading.
///
/// It changes the choice by showing the screen that asked for it again.
public struct AboutRootView: View {
    @Environment(AppModel.self) private var app
    @State private var asking = false

    public init() {}

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Space.s5) {
                Text(AboutCopy.what)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.text)
                    .fixedSize(horizontal: false, vertical: true)
                AboutSection(AboutCopy.Words.title) {
                    AboutPoints(AboutCopy.Words.points)
                }
                AboutSection(AboutCopy.Choice.title) {
                    Text(AboutPage.choice(app.consent.choice))
                        .fixedSize(horizontal: false, vertical: true)
                    if app.consent.couldNotSave {
                        Text(SearchCopy.Permission.couldNotSave)
                            .foregroundStyle(Tokens.Colour.error)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    Button(AboutCopy.Choice.change) {
                        asking = true
                    }
                    .buttonStyle(.burroSecondary)
                }
                AboutSection(AboutCopy.Links.title) {
                    VStack(alignment: .leading, spacing: 0) {
                        AboutLink(AboutCopy.Links.methods, to: .methods)
                        AboutLink(AboutCopy.Links.sources, to: .sources)
                        AboutLink(AboutCopy.Links.accessibility, to: .accessibility)
                    }
                }
                AboutSection(AboutCopy.Release.title) {
                    release
                }
            }
            .font(Tokens.Text.body)
            .foregroundStyle(Tokens.Colour.text)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(Tokens.Space.gutter)
        }
        .background(Tokens.Colour.bg)
        .navigationTitle(ShellCopy.title(of: .about))
        .sheet(isPresented: $asking) {
            PermissionView { asking = false }
                .environment(app)
        }
    }

    @ViewBuilder
    private var release: some View {
        if let search = app.search {
            AboutRows(AboutPage.release(search.state.meta))
        } else if case .failed(let failure) = app.opening {
            Text(AboutCopy.Release.failed)
            Text(verbatim: ShellCopy.words(for: failure))
                .foregroundStyle(Tokens.Colour.error)
                .fixedSize(horizontal: false, vertical: true)
            Button(ShellCopy.tryAgain) {
                Task { await app.open() }
            }
            .buttonStyle(.burroSecondary)
        } else {
            Text(AboutCopy.Release.opening)
                .foregroundStyle(Tokens.Colour.muted)
        }
    }
}

/// One of the three screens About leads to: `.methods`, `.sources` or `.accessibility`.
public struct AboutScreenView: View {
    private let screen: Screen

    public init(screen: Screen) {
        self.screen = screen
    }

    public var body: some View {
        switch screen {
        case .methods:
            Opened { MethodsScreen() }
        case .sources:
            Opened { SourcesScreen() }
        case .accessibility:
            AccessibilityScreen()
        default:
            // No other screen is About's. One that is asked for here is a fault
            // in the shell, and the first screen is a fair answer to it.
            AboutRootView()
        }
    }
}

// MARK: - Parts

/// A part of a screen under its heading.
struct AboutSection<Content: View>: View {
    enum Level {
        case section
        case inner
    }

    private let title: String
    private let level: Level
    private let content: Content

    init(_ title: String, level: Level = .section, @ViewBuilder content: () -> Content) {
        self.title = title
        self.level = level
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            Text(title)
                .font(level == .section ? Tokens.Text.title : Tokens.Text.headline)
                .foregroundStyle(Tokens.Colour.text)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// A list of points, each read as one thing.
struct AboutPoints: View {
    private let points: [String]

    init(_ points: [String]) {
        self.points = points
    }

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            ForEach(points, id: \.self) { point in
                HStack(alignment: .firstTextBaseline, spacing: Tokens.Space.s2) {
                    Text(verbatim: "•")
                        .accessibilityHidden(true)
                    Text(verbatim: point)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .font(Tokens.Text.body)
        .foregroundStyle(Tokens.Colour.text)
    }
}

/// Names and what goes with each, one under another, so that neither is cut
/// short at the largest size of text.
struct AboutRows: View {
    private let rows: [AboutRow]

    init(_ rows: [AboutRow]) {
        self.rows = rows
    }

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            ForEach(rows) { row in
                VStack(alignment: .leading, spacing: 0) {
                    Text(verbatim: row.name)
                        .font(Tokens.Text.secondary)
                        .foregroundStyle(Tokens.Colour.muted)
                    Text(verbatim: row.value)
                        .font(row.isCode ? Tokens.Text.code : Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.text)
                        .textSelection(.enabled)
                }
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityElement(children: .combine)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

/// A row that leads to another screen of About.
struct AboutLink: View {
    private let title: String
    private let screen: Screen

    init(_ title: String, to screen: Screen) {
        self.title = title
        self.screen = screen
    }

    var body: some View {
        NavigationLink(value: screen) {
            HStack(spacing: Tokens.Space.s2) {
                Text(title)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.accent)
                    .multilineTextAlignment(.leading)
                Spacer(minLength: 0)
                Image(systemName: "chevron.right")
                    .font(Tokens.Text.footnote)
                    .foregroundStyle(Tokens.Colour.muted)
                    .accessibilityHidden(true)
            }
            .frame(maxWidth: .infinity, minHeight: Tokens.Target.least, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(Tokens.Colour.border)
                .frame(height: 1)
                .accessibilityHidden(true)
        }
    }
}
