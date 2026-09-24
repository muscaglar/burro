import BurroKit
import SwiftUI

/// The app. It shows BurroKit's root view and holds nothing else: every
/// screen, and everything a screen needs, is in BurroKit, where it is tested.
@main
struct BurroApp: App {
    @UIApplicationDelegateAdaptor(OwnKeyboardOnly.self) private var delegate
    @State private var model = AppModel.live(infoDictionary: Bundle.main.infoDictionary)

    var body: some Scene {
        WindowGroup {
            BurroRootView(model: model)
        }
    }
}

/// Lets nobody's keyboard but the phone's own be typed on in the app.
///
/// A keyboard from another maker sees every key pressed, and one that was
/// given full access may send what it sees to its maker. What a person types
/// here names where they work and what they can pay, so it is typed on the
/// phone's own keyboard or not at all.
final class OwnKeyboardOnly: NSObject, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        shouldAllowExtensionPointIdentifier extensionPointIdentifier: UIApplication.ExtensionPointIdentifier
    ) -> Bool {
        extensionPointIdentifier != .keyboard
    }
}
