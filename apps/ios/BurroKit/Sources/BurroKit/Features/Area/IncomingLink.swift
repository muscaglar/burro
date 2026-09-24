import Foundation

/// What a link that was opened leads to. A link is one of the website's own
/// addresses: an area's page, or a search that someone shared.
///
/// A link holds an id or a slug and nothing else. Whatever else an address
/// holds is never read, never sent and never shown.
public enum IncomingLink: Hashable, Sendable {
    /// One area's page, by the city and the slug its address holds.
    case area(city: String, slug: String)
    /// A search that someone shared, by the id the link holds.
    case share(id: String)
    /// The address of a shared search, with nothing after the `#`.
    case noShare
    /// The address of a shared search, with something after the `#` that is not an id.
    case notAShare

    /// Reads a link. `nil` for an address that is not the website's, or that
    /// leads to nothing the app shows.
    ///
    /// - Parameter site: Where the website is. With no address set, no link is one of its own.
    public static func read(_ url: URL, site: SiteAddress) -> IncomingLink? {
        guard let origin = site.origin,
            let parts = URLComponents(url: url, resolvingAgainstBaseURL: false),
            parts.scheme?.lowercased() == "https",
            let host = parts.host?.lowercased(), !host.isEmpty, host == origin.host?.lowercased(),
            port(parts.port) == port(origin.port),
            parts.user == nil, parts.password == nil
        else { return nil }

        // The address is read as it was written. An id or a slug has nothing in it to decode.
        let path = parts.percentEncodedPath.split(separator: "/", omittingEmptySubsequences: true)
            .map(String.init)
        if path == ["s"] {
            guard let fragment = parts.percentEncodedFragment, !fragment.isEmpty else { return .noShare }
            return SiteAddress.isShareId(fragment) ? .share(id: fragment) : .notAShare
        }
        // An area's address holds its city and its slug, and no more.
        guard path.count == 2, cities.contains(path[0]), SiteAddress.isSlug(path[1]) else { return nil }
        return .area(city: path[0], slug: path[1])
    }

    /// The cities an area's address may name.
    private static let cities: Set<String> = Set(["syn-", "lon-"].compactMap(SiteAddress.city(of:)))

    /// The port a browser would leave out is the same as none.
    private static func port(_ port: Int?) -> Int? {
        port == 443 ? nil : port
    }
}
