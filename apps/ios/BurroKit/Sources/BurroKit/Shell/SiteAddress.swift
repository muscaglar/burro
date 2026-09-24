import Foundation

/// Where the website is, and every address on it the app hands to the share
/// sheet. They are built here and nowhere else.
///
/// An address is made from a slug or from a share's id. None takes anything
/// a person typed, a place, a spec or a fact. A share's id goes in the
/// fragment, which a browser sends to no server.
///
/// The build setting `BURRO_SITE_URL` is written into `Info.plist` under
/// `BurroSiteURL`. With it unset there is no address, and nothing is shared.
public struct SiteAddress: Hashable, Sendable {
    /// The key in `Info.plist` that holds the value of the build setting.
    public static let infoKey = "BurroSiteURL"

    /// The website's origin, with no path. `nil` when none is set.
    public let origin: URL?

    public init(_ value: String?) {
        origin = Self.clean(value)
    }

    /// Reads the address from an `Info.plist`, as `Bundle.main.infoDictionary` gives it.
    public init(infoDictionary: [String: Any]?) {
        self.init(infoDictionary?[Self.infoKey] as? String)
    }

    /// No address: nothing can be shared.
    public static let none = SiteAddress(nil)

    /// The address of one area's page. It holds the area's slug and nothing of a search.
    public func area(_ area: AreaRef) -> URL? {
        guard let origin, let city = Self.city(of: area.areaId), Self.isSlug(area.slug) else { return nil }
        return URL(string: "\(origin.absoluteString)/\(city)/\(area.slug)")
    }

    /// The address that opens a share. `nil` for anything that is not a share's id.
    public func share(_ shareId: String) -> URL? {
        guard let origin, Self.isShareId(shareId) else { return nil }
        return URL(string: "\(origin.absoluteString)/s#\(shareId)")
    }

    /// The city an id belongs to, as it appears in an area's address.
    public static func city(of id: String) -> String? {
        switch id.split(separator: "-", maxSplits: 1).first {
        case "syn": return "synthetic"
        case "lon": return "london"
        default: return nil
        }
    }

    /// True when the text is a share's id as the API makes one: 128 random bits, as 22 characters.
    public static func isShareId(_ value: String) -> Bool {
        value.utf8.count == 22
            && value.utf8.allSatisfy { byte in
                (byte >= 0x30 && byte <= 0x39) || (byte >= 0x41 && byte <= 0x5a)
                    || (byte >= 0x61 && byte <= 0x7a) || byte == 0x2d || byte == 0x5f
            }
    }

    /// True when the text is a slug as the contract writes one.
    public static func isSlug(_ value: String) -> Bool {
        let parts = value.split(separator: "-", omittingEmptySubsequences: false)
        return !parts.isEmpty
            && parts.allSatisfy { part in
                !part.isEmpty
                    && part.utf8.allSatisfy { byte in
                        (byte >= 0x30 && byte <= 0x39) || (byte >= 0x61 && byte <= 0x7a)
                    }
            }
    }

    private static func clean(_ value: String?) -> URL? {
        guard let trimmed = value?.trimmingCharacters(in: .whitespacesAndNewlines), !trimmed.isEmpty,
            let parts = URLComponents(string: trimmed),
            parts.scheme?.lowercased() == "https",
            let host = parts.host, !host.isEmpty,
            parts.user == nil, parts.password == nil, parts.query == nil, parts.fragment == nil,
            parts.path.isEmpty || parts.path == "/"
        else { return nil }
        var origin = URLComponents()
        origin.scheme = "https"
        origin.host = host.lowercased()
        origin.port = parts.port
        return origin.url
    }
}
