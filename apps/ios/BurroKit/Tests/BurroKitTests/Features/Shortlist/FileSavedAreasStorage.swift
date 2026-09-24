import Foundation

@testable import BurroKit

extension FileSavedAreasStorage {
    /// The bytes as they are on the phone.
    var written: Data? { storage.read(.savedAreas) }
}
