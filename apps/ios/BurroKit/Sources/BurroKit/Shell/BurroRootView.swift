import SwiftUI

/// The root of the app: the screen that asks before the first search, and
/// then the three tabs under the banner. The app target shows this and
/// nothing else.
public struct BurroRootView: View {
    @State private var app: AppModel
    @Environment(\.scenePhase) private var scenePhase

    public init(model: AppModel) {
        _app = State(initialValue: model)
    }

    public var body: some View {
        ZStack {
            Rectangle().fill(Tokens.Colour.bg).ignoresSafeArea()
            if app.consent.choice == nil {
                // It shows no data, so it has no banner, and it stands before the tabs.
                PermissionView()
            } else {
                tabs
            }
            if scenePhase != .active {
                PrivacyCover()
            }
        }
        // A link is opened whichever of the two is showing: opening one sends no sentence.
        .opensLinks()
        .environment(app)
        .tint(Tokens.Colour.accent)
        .task { await app.open() }
    }

    private var tabs: some View {
        VStack(spacing: 0) {
            SyntheticBanner()
                .frame(maxHeight: bannerLimit)
            TabView(selection: $app.tab) {
                ForEach(AppTab.allCases) { tab in
                    TabStack(tab: tab)
                        .tabItem {
                            Label(ShellCopy.title(of: tab), systemImage: ShellCopy.image(of: tab))
                        }
                        .tag(tab)
                }
            }
        }
    }

    /// The most of the screen the banner may take, however large the text.
    private var bannerLimit: CGFloat { 160 }
}

/// One tab: its first screen, and whatever is pushed onto it.
struct TabStack: View {
    let tab: AppTab
    @Environment(AppModel.self) private var app

    var body: some View {
        @Bindable var app = app
        NavigationStack(path: path($app)) {
            root
                .navigationDestination(for: Screen.self) { screen in
                    destination(screen)
                }
        }
    }

    private func path(_ app: Bindable<AppModel>) -> Binding<[Screen]> {
        switch tab {
        case .search: return app.searchPath
        case .shortlist: return app.shortlistPath
        case .about: return app.aboutPath
        }
    }

    @ViewBuilder
    private var root: some View {
        switch tab {
        case .search:
            Opened { SearchRootView() }
        case .shortlist:
            ShortlistRootView()
        case .about:
            AboutRootView()
        }
    }

    @ViewBuilder
    private func destination(_ screen: Screen) -> some View {
        switch screen {
        case .results:
            Opened { ResultsView() }
        case .area(let area):
            AreaView(area: area)
        case .compare:
            Opened { ResultsCompareView() }
        case .methods, .sources, .accessibility:
            AboutScreenView(screen: screen)
        }
    }
}

/// Shows a screen that needs a search once there is one. Until then it says
/// that Burro is opening, or why it could not be, with a way to try again.
///
/// Inside it, `SearchStore` is in the environment.
public struct Opened<Content: View>: View {
    @Environment(AppModel.self) private var app
    private let content: () -> Content

    public init(@ViewBuilder content: @escaping () -> Content) {
        self.content = content
    }

    public var body: some View {
        if let search = app.search {
            content().environment(search)
        } else {
            OpeningView()
        }
    }
}

/// What is shown while the release is being read, and when it could not be.
struct OpeningView: View {
    @Environment(AppModel.self) private var app

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Space.s4) {
                switch app.opening {
                case .waiting, .opening, .open:
                    ProgressView()
                        .accessibilityHidden(true)
                    Text(ShellCopy.opening)
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.text)
                case .failed(let failure):
                    Text(ShellCopy.couldNotOpen)
                        .font(Tokens.Text.title)
                        .foregroundStyle(Tokens.Colour.text)
                        .accessibilityAddTraits(.isHeader)
                    Text(ShellCopy.words(for: failure))
                        .font(Tokens.Text.body)
                        .foregroundStyle(Tokens.Colour.error)
                    if let requestId = failure.requestId {
                        Text(verbatim: "\(ShellCopy.requestId) \(requestId)")
                            .font(Tokens.Text.code)
                            .foregroundStyle(Tokens.Colour.muted)
                            .textSelection(.enabled)
                    }
                    Button(ShellCopy.tryAgain) {
                        Task { await app.open() }
                    }
                    .buttonStyle(.burroPrimary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(Tokens.Space.gutter)
        }
        .background(Tokens.Colour.bg)
    }
}

/// Covers the screen while the app is not in front. The phone keeps a picture
/// of every app for its switcher, and that picture is a file: this keeps what
/// a person typed out of it.
struct PrivacyCover: View {
    var body: some View {
        ZStack {
            Rectangle().fill(Tokens.Colour.bg).ignoresSafeArea()
            Text(ShellCopy.covered)
                .font(Tokens.Text.largeTitle)
                .foregroundStyle(Tokens.Colour.text)
        }
        .accessibilityHidden(true)
    }
}
