import SwiftUI

/// The screen before the first search. It says what is sent, who reads it and
/// what is kept, and asks. Nothing is sent until the person agrees, and
/// saying no loses nothing: the settings do the same job with no language model.
///
/// Who reads what is typed is the API's to say: the rules that are part of
/// Burro, or a language model run by a company it names. The screen shows what
/// the API serves, word for word, and writes no provider's name and no terms
/// of its own. Until the service has said, a person cannot agree: they have
/// not been told what they would agree to.
///
/// It shows no data, so it has no banner, and it stands before the tabs. About
/// shows it again, over itself. The choice is remembered. Nothing typed is.
public struct PermissionView: View {
    @Environment(AppModel.self) private var app
    /// Told once the person has chosen, by whoever showed the screen over their own.
    private let onChosen: (() -> Void)?

    public init(onChosen: (() -> Void)? = nil) {
        self.onChosen = onChosen
    }

    public var body: some View {
        let who = SearchScreen.whoReads(app.search?.state.meta.reader, opening: app.opening)
        ScrollView {
            VStack(alignment: .leading, spacing: Tokens.Space.s4) {
                Text(SearchCopy.Permission.title)
                    .font(Tokens.Text.largeTitle)
                    .foregroundStyle(Tokens.Colour.text)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityAddTraits(.isHeader)
                section(SearchCopy.Permission.sentTitle, [SearchCopy.Permission.handled])
                section(SearchCopy.Permission.whoTitle, [who.words, SearchCopy.Permission.model])
                section(SearchCopy.Permission.keptTitle, [SearchCopy.Permission.kept])
                VStack(spacing: Tokens.Space.s3) {
                    Button(SearchCopy.Permission.allow) {
                        choose(.allowed)
                    }
                    .buttonStyle(.burroPrimary)
                    .disabled(!who.said)
                    Button(SearchCopy.Permission.settingsInstead) {
                        choose(.settingsOnly)
                    }
                    .buttonStyle(.burroSecondary)
                }
                .padding(.top, Tokens.Space.s2)
                VStack(alignment: .leading, spacing: Tokens.Space.s1) {
                    Text(SearchCopy.Permission.eitherWay)
                    Text(SearchCopy.Permission.changeLater)
                }
                .font(Tokens.Text.footnote)
                .foregroundStyle(Tokens.Colour.muted)
                .fixedSize(horizontal: false, vertical: true)
            }
            .font(Tokens.Text.body)
            .foregroundStyle(Tokens.Colour.text)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(Tokens.Space.gutter)
        }
        .background(Tokens.Colour.bg)
    }

    private func section(_ title: String, _ paragraphs: [String]) -> some View {
        VStack(alignment: .leading, spacing: Tokens.Space.s2) {
            Text(title)
                .font(Tokens.Text.title)
                .accessibilityAddTraits(.isHeader)
            ForEach(paragraphs, id: \.self) { paragraph in
                Text(verbatim: paragraph)
            }
        }
        .fixedSize(horizontal: false, vertical: true)
    }

    private func choose(_ choice: ConsentChoice) {
        app.consent.choose(choice)
        onChosen?()
    }
}
