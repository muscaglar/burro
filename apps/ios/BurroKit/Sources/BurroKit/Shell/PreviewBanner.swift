import SwiftUI

/// The banner that says the release is a preview. The shell draws it above
/// every tab, under the banner that says the data is made up, so no screen
/// that shows data can be without it. It cannot be closed.
///
/// It draws nothing until something the app was given says its release is a
/// preview. It says nothing of whether the figures are made up. On a preview
/// of data that is not made up, it says that the figures are of real places.
public struct PreviewBanner: View {
    @Environment(AppModel.self) private var app

    public init() {}

    public var body: some View {
        if app.preview.seen {
            let said = PreviewBanner.words(madeUp: app.synthetic.seen)
            ViewThatFits(in: .vertical) {
                words(said)
                ScrollView { words(said) }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Tokens.Colour.infoBg)
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(Tokens.Colour.infoText)
                    .frame(height: 2)
                    .accessibilityHidden(true)
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel(Text(verbatim: "\(ShellCopy.previewLabel). \(said)"))
        }
    }

    /// What the banner says. The figures are said to be real only where
    /// nothing the app was given has said its data is made up.
    static func words(madeUp: Bool) -> String {
        madeUp ? ShellCopy.previewBanner : "\(ShellCopy.previewBanner) \(ShellCopy.previewReal)"
    }

    private func words(_ said: String) -> some View {
        Text(verbatim: said)
            .font(Tokens.Text.footnote)
            .foregroundStyle(Tokens.Colour.infoText)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.horizontal, Tokens.Space.gutter)
            .padding(.vertical, Tokens.Space.s2)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}
