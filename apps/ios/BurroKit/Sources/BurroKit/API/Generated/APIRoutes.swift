// Generated from contracts/openapi.json by apps/ios/scripts/generate.py.
// Never edited by hand: change the source and run `make generate`.
// source-sha256: 06d39ed9bd188b88a51e52be7d59dfe6b17588cfb2a3752794964144ab34772f

import Foundation

public enum HTTPMethod: String, Hashable, Sendable {
    case get = "GET"
    case post = "POST"
}

/// Every route of the contract, named by its operation id.
public enum APIRoute: String, Hashable, Sendable, CaseIterable {
    case compare = "compare"
    case createShare = "create_share"
    case explainTop = "explain_top"
    case getArea = "get_area"
    case getGeometry = "get_geometry"
    case getMeta = "get_meta"
    case getShare = "get_share"
    case healthz = "healthz"
    case interpret = "interpret"
    case listAreas = "list_areas"
    case rank = "rank"
    case searchPlaces = "search_places"

    public var method: HTTPMethod {
        switch self {
        case .compare: return .post
        case .createShare: return .post
        case .explainTop: return .post
        case .getArea: return .get
        case .getGeometry: return .get
        case .getMeta: return .get
        case .getShare: return .get
        case .healthz: return .get
        case .interpret: return .post
        case .listAreas: return .get
        case .rank: return .post
        case .searchPlaces: return .post
        }
    }

    /// The path as the contract writes it, with its parameter unfilled.
    public var template: String {
        switch self {
        case .compare: return "/v1/compare"
        case .createShare: return "/v1/shares"
        case .explainTop: return "/v1/explanations"
        case .getArea: return "/v1/areas/{id_or_slug}"
        case .getGeometry: return "/v1/areas/geometry"
        case .getMeta: return "/v1/meta"
        case .getShare: return "/v1/shares/{share_id}"
        case .healthz: return "/healthz"
        case .interpret: return "/v1/interpret"
        case .listAreas: return "/v1/areas"
        case .rank: return "/v1/rank"
        case .searchPlaces: return "/v1/places/search"
        }
    }

    /// The name of the one value in the path, for the routes that have one.
    public var parameter: String? {
        switch self {
        case .compare: return nil
        case .createShare: return nil
        case .explainTop: return nil
        case .getArea: return "id_or_slug"
        case .getGeometry: return nil
        case .getMeta: return nil
        case .getShare: return "share_id"
        case .healthz: return nil
        case .interpret: return nil
        case .listAreas: return nil
        case .rank: return nil
        case .searchPlaces: return nil
        }
    }

    /// False for the one answer that comes with no `meta` around it.
    public var enveloped: Bool {
        switch self {
        case .compare: return true
        case .createShare: return true
        case .explainTop: return true
        case .getArea: return true
        case .getGeometry: return true
        case .getMeta: return true
        case .getShare: return true
        case .healthz: return false
        case .interpret: return true
        case .listAreas: return true
        case .rank: return true
        case .searchPlaces: return true
        }
    }

    /// The statuses the contract says the route can fail with.
    public var failures: [Int] {
        switch self {
        case .compare: return [400, 404, 413, 415, 422, 500]
        case .createShare: return [400, 413, 415, 422, 500]
        case .explainTop: return [400, 413, 415, 422, 500]
        case .getArea: return [404, 422, 500]
        case .getGeometry: return [500]
        case .getMeta: return [500]
        case .getShare: return [404, 410, 422, 500]
        case .healthz: return [500]
        case .interpret: return [400, 413, 415, 422, 500]
        case .listAreas: return [500]
        case .rank: return [400, 413, 415, 422, 500]
        case .searchPlaces: return [400, 413, 415, 422, 500]
        }
    }
}

/// The API: one method a route, named by its operation id.
///
/// No method throws. Each answers with `meta` and `data`, or with a failure that says why.
public protocol BurroAPI: Sendable {
    /// `POST /v1/compare`. Two to four areas side by side, the rows in the order of the person's own weights.
    func compare(_ body: CompareBody) async -> Answer<CompareData>
    /// `POST /v1/shares`. Store a search and give back the id of a link to it.
    func createShare(_ body: ShareBody) async -> Answer<ShareCreated>
    /// `POST /v1/explanations`. A few checked sentences about each of the top areas, and the facts they cite.
    func explainTop(_ body: ExplanationsBody) async -> Answer<ExplanationsData>
    /// `GET /v1/areas/{id_or_slug}`. One area: what the release holds about it, and the facts a profile page shows.
    func getArea(_ idOrSlug: String) async -> Answer<AreaData>
    /// `GET /v1/areas/geometry`. The boundary of every area, as a GeoJSON feature collection.
    func getGeometry() async -> Answer<GeometryData>
    /// `GET /v1/meta`. The release that is loaded, the vocabulary, the defaults and the limits.
    func getMeta() async -> Answer<MetaData>
    /// `GET /v1/shares/{share_id}`. A shared search, ranked now on the release that is loaded.
    func getShare(_ shareId: String) async -> Answer<ShareData>
    /// `GET /healthz`. Whether the service is up. It says nothing about the release, so it has no `meta`.
    func healthz() async -> Result<Health, Failure>
    /// `POST /v1/interpret`. Read a request in words into typed edits, and apply them to the spec.
    func interpret(_ body: InterpretBody) async -> Answer<InterpretData>
    /// `GET /v1/areas`. Every area of the release, by id.
    func listAreas() async -> Answer<AreasData>
    /// `POST /v1/rank`. Apply any edits to the spec, then rank every area of the release for it.
    func rank(_ body: RankBody) async -> Answer<RankData>
    /// `POST /v1/places/search`. The places that match, best first.
    func searchPlaces(_ body: PlaceSearchBody) async -> Answer<PlacesData>
}

/// What a client has to be able to do. Every method of `BurroAPI` is made of it.
public protocol RouteSending: Sendable {
    /// Sends one request and reads the envelope of the answer.
    func send<Payload: Decodable & Sendable>(
        _ route: APIRoute, parameter: String?, body: (any Encodable & Sendable)?
    ) async -> Answer<Payload>
    /// Sends one request to a route whose answer has no `meta` around it.
    func sendPlain<Payload: Decodable & Sendable>(_ route: APIRoute) async -> Result<Payload, Failure>
}

extension BurroAPI where Self: RouteSending {
    public func compare(_ body: CompareBody) async -> Answer<CompareData> {
        await send(.compare, parameter: nil, body: body)
    }

    public func createShare(_ body: ShareBody) async -> Answer<ShareCreated> {
        await send(.createShare, parameter: nil, body: body)
    }

    public func explainTop(_ body: ExplanationsBody) async -> Answer<ExplanationsData> {
        await send(.explainTop, parameter: nil, body: body)
    }

    public func getArea(_ idOrSlug: String) async -> Answer<AreaData> {
        await send(.getArea, parameter: idOrSlug, body: nil)
    }

    public func getGeometry() async -> Answer<GeometryData> {
        await send(.getGeometry, parameter: nil, body: nil)
    }

    public func getMeta() async -> Answer<MetaData> {
        await send(.getMeta, parameter: nil, body: nil)
    }

    public func getShare(_ shareId: String) async -> Answer<ShareData> {
        await send(.getShare, parameter: shareId, body: nil)
    }

    public func healthz() async -> Result<Health, Failure> {
        await sendPlain(.healthz)
    }

    public func interpret(_ body: InterpretBody) async -> Answer<InterpretData> {
        await send(.interpret, parameter: nil, body: body)
    }

    public func listAreas() async -> Answer<AreasData> {
        await send(.listAreas, parameter: nil, body: nil)
    }

    public func rank(_ body: RankBody) async -> Answer<RankData> {
        await send(.rank, parameter: nil, body: body)
    }

    public func searchPlaces(_ body: PlaceSearchBody) async -> Answer<PlacesData> {
        await send(.searchPlaces, parameter: nil, body: body)
    }
}
