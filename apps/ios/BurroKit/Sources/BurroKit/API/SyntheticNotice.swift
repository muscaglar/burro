import Observation

/// Whether anything the app has been given, since it was opened, is made up.
///
/// The banner must show as soon as any answer says the data is made up, so
/// every answer is heard here, and so is a shortlist that holds a made-up
/// area. It is held in memory, and it only ever turns on.
@MainActor
@Observable
public final class SyntheticNotice {
    public private(set) var seen: Bool

    public init(seen: Bool = false) {
        self.seen = seen
    }

    public func note(_ synthetic: Bool) {
        guard synthetic, !seen else { return }
        seen = true
    }
}
