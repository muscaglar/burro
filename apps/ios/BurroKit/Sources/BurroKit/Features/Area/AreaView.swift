import SwiftUI

/// One area: where it is, its stations, what homes cost, every figure the
/// release holds for it laid out by what it is about, and its tags. Every
/// figure is a fact of the API's, shown as it came, with its source and its
/// date written out under it.
///
/// It is reached from a result, from the shortlist and from a link. It may be
/// shown with no search open, as from the shortlist with no connection, so it
/// reads the search from `app.search`, which may be `nil`.
public struct AreaView: View {
    @Environment(AppModel.self) private var app
    @State private var loader: AreaLoader?
    private let area: AreaRef

    public init(area: AreaRef) {
        self.area = area
    }

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Space.s5) {
                switch loader?.shown ?? .reading {
                case .reading:
                    AreaReading(area: area)
                case .failed(let failure):
                    AreaFailed(area: area, failure: failure) { again() }
                case .page(let page, let origin):
                    AreaPageView(
                        page: page, origin: origin, keptIsOlder: loader?.keptIsOlder ?? false,
                        keepNewer: { loader?.keepWhatIsShown() }, again: again)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(Tokens.Space.gutter)
        }
        .background(Tokens.Colour.bg)
        .navigationTitle(title)
        #if os(iOS)
        // The bar holds the name small. The page holds it large, where it can wrap.
        .navigationBarTitleDisplayMode(.inline)
        #endif
        // Read once the screen is shown, and laid out again once the release has been read.
        .task(id: app.search != nil) {
            let loader = self.loader ?? AreaLoader(area: area, app: app)
            self.loader = loader
            await loader.load()
        }
    }

    private var title: String {
        if case .page(let page, _) = loader?.shown { return page.name }
        return area.name
    }

    private func again() {
        Task { await loader?.retry() }
    }
}

/// What is shown while the area is being read: its name, which the route
/// holds, and one line that says it is being read.
struct AreaReading: View {
    let area: AreaRef

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            AreaNamed(area: area)
            HStack(spacing: Tokens.Space.s2) {
                ProgressView()
                    .accessibilityHidden(true)
                Text(AreaCopy.reading)
                    .font(Tokens.Text.body)
                    .foregroundStyle(Tokens.Colour.muted)
            }
        }
    }
}

/// What is shown when the area could not be read and the phone holds no copy
/// of it: why, in the API's words where it gave any, and a way to try again.
struct AreaFailed: View {
    @Environment(AppModel.self) private var app
    let area: AreaRef
    let failure: Failure
    let again: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s3) {
            AreaNamed(area: area)
            Text(AreaCopy.failed)
                .font(Tokens.Text.title)
                .foregroundStyle(Tokens.Colour.text)
                .accessibilityAddTraits(.isHeader)
            AreaFailureWords(failure: failure)
            // The API has said there is no such area. Asking again would be told the same.
            if !isRefusal {
                Button(ShellCopy.tryAgain, action: again)
                    .buttonStyle(.burroPrimary)
            }
            if app.saved.contains(area.areaId) {
                Button(AreaCopy.removeFromShortlist) {
                    app.saved.remove(area.areaId)
                }
                .buttonStyle(.burroSecondary)
            }
        }
    }

    private var isRefusal: Bool {
        failure.api.map { $0.status < 500 } ?? false
    }
}

/// A failure, in words: the API's own where it gave any, and the id to quote.
struct AreaFailureWords: View {
    let failure: Failure

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            Text(ShellCopy.words(for: failure))
                .font(Tokens.Text.body)
                .foregroundStyle(Tokens.Colour.error)
            if let requestId = failure.requestId {
                Text(verbatim: "\(ShellCopy.requestId) \(requestId)")
                    .font(Tokens.Text.code)
                    .foregroundStyle(Tokens.Colour.muted)
                    .textSelection(.enabled)
            }
        }
    }
}

/// A name and its value, one above the other, read as one.
struct AreaLabelled: View {
    let name: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(name)
                .font(Tokens.Text.footnote)
                .foregroundStyle(Tokens.Colour.muted)
            Text(value)
                .font(Tokens.Text.body)
                .foregroundStyle(Tokens.Colour.text)
        }
        .accessibilityElement(children: .combine)
    }
}

/// The name and the borough of an area, as the route to its screen holds
/// them, for when there is nothing else of it to show.
struct AreaNamed: View {
    let area: AreaRef

    var body: some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            Text(area.name)
                .font(Tokens.Text.largeTitle)
                .foregroundStyle(Tokens.Colour.text)
                .accessibilityAddTraits(.isHeader)
            AreaLabelled(name: AreaCopy.borough, value: area.borough)
        }
    }
}
