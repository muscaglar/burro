import SwiftUI

/// The banner that says the data is made up. The shell draws it above every
/// tab, so no screen that shows data can be without it. It cannot be closed.
///
/// It draws nothing until something the app was given says it is made up.
/// At the largest sizes of text it keeps to a share of the screen and scrolls
/// inside itself, so that it is never cut short and never takes the screen.
public struct SyntheticBanner: View {
    @Environment(AppModel.self) private var app

    public init() {}

    public var body: some View {
        if app.synthetic.seen {
            ViewThatFits(in: .vertical) {
                words
                ScrollView { words }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Tokens.Colour.noticeBg)
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(Tokens.Colour.noticeEdge)
                    .frame(height: 2)
                    .accessibilityHidden(true)
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel(Text(verbatim: "\(ShellCopy.bannerLabel). \(ShellCopy.banner)"))
        }
    }

    private var words: some View {
        Text(ShellCopy.banner)
            .font(Tokens.Text.footnote)
            .foregroundStyle(Tokens.Colour.noticeText)
            .multilineTextAlignment(.leading)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.horizontal, Tokens.Space.gutter)
            .padding(.vertical, Tokens.Space.s2)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}
