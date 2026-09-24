import Foundation

/// Where the API is. One build setting says so, and nothing else does.
///
/// The build setting `BURRO_API_BASE_URL` is written into the app's
/// `Info.plist` under `BurroAPIBaseURL`, and read here. With it unset the
/// client answers `notConfigured` and sends nothing.
public struct APIConfiguration: Hashable, Sendable {
    /// The key in `Info.plist` that holds the value of the build setting.
    public static let infoKey = "BurroAPIBaseURL"

    /// The address with no slash at the end. `nil` when none is set or it is not an address.
    public let baseURL: URL?

    public init(baseURL: URL?) {
        self.baseURL = baseURL.flatMap { Self.clean($0.absoluteString) }
    }

    public init(_ value: String?) {
        baseURL = Self.clean(value)
    }

    /// Reads the address from an `Info.plist`, as `Bundle.main.infoDictionary` gives it.
    public init(infoDictionary: [String: Any]?) {
        self.init(infoDictionary?[Self.infoKey] as? String)
    }

    /// No address: every call answers `notConfigured`.
    public static let none = APIConfiguration(nil)

    static func clean(_ value: String?) -> URL? {
        guard let trimmed = value?.trimmingCharacters(in: .whitespacesAndNewlines), !trimmed.isEmpty,
            let parts = URLComponents(string: trimmed),
            let scheme = parts.scheme?.lowercased(),
            let host = parts.host?.lowercased(), !host.isEmpty
        else { return nil }
        // An address with a name and a password in it would send them with every call.
        guard parts.user == nil, parts.password == nil, parts.query == nil, parts.fragment == nil else {
            return nil
        }
        switch scheme {
        case "https":
            break
        case "http":
            // What a person types is never sent in the clear across a network.
            guard ["localhost", "127.0.0.1", "::1", "[::1]"].contains(host) else { return nil }
        default:
            return nil
        }
        var cleaned = URLComponents()
        cleaned.scheme = scheme
        cleaned.host = parts.host
        cleaned.port = parts.port
        var path = parts.path
        while path.hasSuffix("/") { path.removeLast() }
        cleaned.path = path
        return cleaned.url
    }
}

/// How long the app waits for each route, for the whole call and not for each read of it.
///
/// 8 seconds for reading a sentence, which may wait on a model, 3 for place
/// search, which runs as a person types, 5 for the rest that depend on a
/// search, and 10 for what the release alone decides. They are the website's.
public struct Timeouts: Hashable, Sendable {
    public var reading: Duration
    public var places: Duration
    public var search: Duration
    public var release: Duration

    public init(
        reading: Duration = .seconds(8),
        places: Duration = .seconds(3),
        search: Duration = .seconds(5),
        release: Duration = .seconds(10)
    ) {
        self.reading = reading
        self.places = places
        self.search = search
        self.release = release
    }

    public func of(_ route: APIRoute) -> Duration {
        switch route {
        case .interpret: return reading
        case .searchPlaces: return places
        case .rank, .explainTop, .compare, .createShare, .getShare: return search
        case .listAreas, .getGeometry, .getArea, .getMeta, .healthz: return release
        }
    }
}
