import Foundation
import Observation

/// What the person chose on the screen before their first search.
public enum ConsentChoice: String, Codable, Hashable, Sendable, CaseIterable {
    /// Their words may be sent to Burro to be read, and a language model may read them.
    case allowed
    /// No sentence is sent. The settings do the same job with no language model.
    case settingsOnly
}

/// Whether the person agreed that their words may be read.
///
/// Until they have chosen, the app shows the screen that asks, and sends no
/// sentence. The choice is kept on the phone, and can be changed in About.
@MainActor
@Observable
public final class Consent {
    /// `nil` until the person has chosen.
    public private(set) var choice: ConsentChoice?
    /// True when the choice could not be written to the phone. It holds until the app is closed.
    public private(set) var couldNotSave = false

    @ObservationIgnored private let storage: any PhoneStorage

    public init(storage: any PhoneStorage) {
        self.storage = storage
        choice = storage.read(.consent)
            .flatMap { try? JSONDecoder().decode(Kept.self, from: $0) }
            .flatMap { ConsentChoice(rawValue: $0.choice) }
    }

    /// True when a sentence may be sent.
    public var mayReadWords: Bool { choice == .allowed }

    public func choose(_ choice: ConsentChoice) {
        self.choice = choice
        do {
            try storage.write(JSONEncoder().encode(Kept(choice: choice.rawValue)), to: .consent)
            couldNotSave = false
        } catch {
            couldNotSave = true
        }
    }

    /// Forgets the choice, so that the screen that asks is shown again.
    public func forget() {
        choice = nil
        do {
            try storage.remove(.consent)
            couldNotSave = false
        } catch {
            couldNotSave = true
        }
    }

    private struct Kept: Codable {
        var version = 1
        let choice: String
    }
}
