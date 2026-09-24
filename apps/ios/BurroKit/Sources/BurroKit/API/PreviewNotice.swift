import Observation

/// Whether anything the app has been given, since it was opened, is of a
/// release that is a preview.
///
/// The banner must show as soon as any answer says its release is not
/// finished, so every answer is heard here, and so is a shortlist that holds
/// an area saved from a preview. It is held in memory, and it only ever turns on.
@MainActor
@Observable
public final class PreviewNotice {
    public private(set) var seen: Bool

    public init(seen: Bool = false) {
        self.seen = seen
    }

    public func note(_ preview: Bool) {
        guard preview, !seen else { return }
        seen = true
    }
}
