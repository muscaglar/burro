import Foundation

/// What a control shows between being changed and being answered.
///
/// A control is drawn from the spec the API returned. When a person changes
/// it, it shows the new value at once, and keeps showing it until an answer
/// comes back. Then it is drawn from the returned spec again, whatever that
/// says: if the edit was refused, the control goes back.
///
/// `version` is `SearchState.answers`, which changes with every answer.
struct Draft<Value: Hashable & Sendable>: Hashable, Sendable {
    private var held: Value?
    private var version: Int?

    init() {}

    /// What to show: what was set since the last answer, or else what the API said.
    func shown(_ value: Value, at version: Int) -> Value {
        guard self.version == version, let held else { return value }
        return held
    }

    /// True when something was set that no answer has yet replaced.
    func isSet(at version: Int) -> Bool {
        self.version == version && held != nil
    }

    mutating func set(_ value: Value, at version: Int) {
        held = value
        self.version = version
    }

    mutating func clear() {
        held = nil
        version = nil
    }
}

/// Sends a change once, a moment after the last press, and never while a
/// slider is dragged, so that moving a control does not flood the API.
@MainActor
final class Settling {
    /// How long after the last key or press a change is sent, in seconds.
    static let wait = 0.15

    private var waiting: Task<Void, Never>?

    init() {}

    /// Does the work after a moment, unless something else is asked for first.
    func soon(after seconds: Double = Settling.wait, _ work: @escaping @MainActor () -> Void) {
        waiting?.cancel()
        waiting = Task { @MainActor in
            try? await Task.sleep(nanoseconds: UInt64(max(0, seconds) * 1_000_000_000))
            guard !Task.isCancelled else { return }
            work()
        }
    }

    /// Does the work now, in place of whatever was waiting.
    func now(_ work: @MainActor () -> Void) {
        cancel()
        work()
    }

    func cancel() {
        waiting?.cancel()
        waiting = nil
    }

    /// Waits for whatever is waiting. Nothing on a screen needs it. A test does.
    func settled() async {
        await waiting?.value
    }
}
