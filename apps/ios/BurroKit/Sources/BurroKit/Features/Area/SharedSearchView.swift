import SwiftUI

/// The screen a shared link opens. It says what a share holds, opens it, and
/// then says how this one may differ from what its sender saw: a place stood
/// in for by a station or a district, or data that has changed since. From
/// there the person goes to the results.
///
/// The id is handed to the one call that opens the share, and to nothing else.
public struct SharedSearchView: View {
    @Environment(AppModel.self) private var app
    @State private var shared: SharedSearch?
    private let shareId: String
    private let seeResults: () -> Void
    private let searchInstead: () -> Void

    /// - Parameters:
    ///   - shareId: The id the link holds.
    ///   - seeResults: Goes to the results, once the share is open.
    ///   - searchInstead: Goes to where a search is made.
    public init(shareId: String, seeResults: @escaping () -> Void, searchInstead: @escaping () -> Void) {
        self.shareId = shareId
        self.seeResults = seeResults
        self.searchInstead = searchInstead
    }

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Space.s4) {
                Text(LinkCopy.Shared.title)
                    .font(Tokens.Text.largeTitle)
                    .foregroundStyle(Tokens.Colour.text)
                    .accessibilityAddTraits(.isHeader)
                switch shared?.stage ?? .opening {
                case .opening:
                    Text(LinkCopy.Shared.holds)
                    HStack(spacing: Tokens.Space.s2) {
                        ProgressView()
                            .accessibilityHidden(true)
                        Text(LinkCopy.Shared.opening)
                            .foregroundStyle(Tokens.Colour.muted)
                    }
                case .open(let opened):
                    ForEach(opened.lines, id: \.self) { Text($0) }
                    Text(opened.status)
                        .font(Tokens.Text.headline)
                    Button(LinkCopy.seeResults, action: seeResults)
                        .buttonStyle(.burroPrimary)
                case .failed(let failure):
                    Text(LinkCopy.Shared.holds)
                    Text(LinkCopy.Shared.failedTitle)
                        .font(Tokens.Text.title)
                        .accessibilityAddTraits(.isHeader)
                    AreaFailureWords(failure: failure)
                    if shared?.canTryAgain == true {
                        Button(LinkCopy.Shared.tryAgain) {
                            Task { await shared?.open() }
                        }
                        .buttonStyle(.burroPrimary)
                    }
                    Button(LinkCopy.Shared.own, action: searchInstead)
                        .buttonStyle(.burroSecondary)
                }
            }
            .font(Tokens.Text.body)
            .foregroundStyle(Tokens.Colour.text)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(Tokens.Space.gutter)
        }
        .background(Tokens.Colour.bg)
        .task {
            let shared = self.shared ?? SharedSearch(shareId: shareId, app: app)
            self.shared = shared
            await shared?.open()
        }
    }
}

/// What is said of a link that leads nowhere, in fixed words.
struct LinkNowhereView: View {
    let nowhere: LinkOpener.Nowhere
    let searchInstead: () -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Space.s4) {
                Text(nowhere.title)
                    .font(Tokens.Text.title)
                    .accessibilityAddTraits(.isHeader)
                Text(nowhere.text)
                Button(LinkCopy.Shared.own, action: searchInstead)
                    .buttonStyle(.burroPrimary)
            }
            .font(Tokens.Text.body)
            .foregroundStyle(Tokens.Colour.text)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(Tokens.Space.gutter)
        }
        .background(Tokens.Colour.bg)
    }
}

/// Opens the website's own links in the app. The shell puts it on its root,
/// inside the environment that holds the app.
///
/// A link to an area goes to the area's screen. A link to a shared search
/// puts up the screen that opens it, under the banner, and then goes to the
/// results.
public struct LinkOpening: ViewModifier {
    @Environment(AppModel.self) private var app
    @Environment(\.scenePhase) private var scenePhase
    @State private var opener = LinkOpener()

    public init() {}

    public func body(content: Content) -> some View {
        @Bindable var opener = opener
        content
            .onOpenURL { url in
                Task { await opener.open(url, in: app) }
            }
            .sheet(item: $opener.presented) { presented in
                ZStack {
                    VStack(spacing: 0) {
                        // What a share opens is data, so the banner stands over it.
                        SyntheticBanner()
                        switch presented {
                        case .share(let id):
                            SharedSearchView(
                                shareId: id,
                                seeResults: { opener.showResults(in: app) },
                                searchInstead: { opener.searchInstead(in: app) })
                        case .nowhere(let nowhere):
                            LinkNowhereView(nowhere: nowhere) { opener.searchInstead(in: app) }
                        }
                    }
                    // A sheet stands over the shell's own cover, so it is covered here as well.
                    if scenePhase != .active {
                        PrivacyCover()
                    }
                }
                .environment(app)
                .tint(Tokens.Colour.accent)
            }
    }
}

extension View {
    /// Opens the website's own links in the app.
    public func opensLinks() -> some View {
        modifier(LinkOpening())
    }
}
