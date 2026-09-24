import SwiftUI

/// The main action of a screen: full width, in the accent colour.
public struct PrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled

    public init() {}

    public func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Tokens.Text.headline)
            .multilineTextAlignment(.center)
            .padding(.horizontal, Tokens.Space.s4)
            .padding(.vertical, Tokens.Space.s3)
            .frame(maxWidth: .infinity, minHeight: Tokens.Target.button)
            // A button that is switched off is drawn in colours of its own, at full strength.
            // Dimmed, its words would fall below the contrast the tokens were checked for.
            .foregroundStyle(isEnabled ? Tokens.Colour.onAccent : Tokens.Colour.muted)
            .background(
                isEnabled ? Tokens.Colour.accent : Tokens.Colour.surface,
                in: RoundedRectangle(cornerRadius: Tokens.Radius.card)
            )
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(Tokens.Colour.border, lineWidth: isEnabled ? 0 : 1)
            )
            .opacity(configuration.isPressed ? 0.8 : 1)
            .contentShape(Rectangle())
    }
}

/// The other action of a screen: full width, with an edge and no fill.
public struct SecondaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled

    public init() {}

    public func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Tokens.Text.headline)
            .multilineTextAlignment(.center)
            .padding(.horizontal, Tokens.Space.s4)
            .padding(.vertical, Tokens.Space.s3)
            .frame(maxWidth: .infinity, minHeight: Tokens.Target.button)
            .foregroundStyle(isEnabled ? Tokens.Colour.accent : Tokens.Colour.muted)
            .background(
                isEnabled ? Tokens.Colour.bg : Tokens.Colour.surface,
                in: RoundedRectangle(cornerRadius: Tokens.Radius.card)
            )
            .overlay(
                RoundedRectangle(cornerRadius: Tokens.Radius.card)
                    .strokeBorder(Tokens.Colour.border, lineWidth: 1)
            )
            .opacity(configuration.isPressed ? 0.8 : 1)
            .contentShape(Rectangle())
    }
}

extension ButtonStyle where Self == PrimaryButtonStyle {
    public static var burroPrimary: PrimaryButtonStyle { PrimaryButtonStyle() }
}

extension ButtonStyle where Self == SecondaryButtonStyle {
    public static var burroSecondary: SecondaryButtonStyle { SecondaryButtonStyle() }
}
