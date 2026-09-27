// Generated from contracts/openapi.json by apps/ios/scripts/generate.py.
// Never edited by hand: change the source and run `make generate`.
// source-sha256: aee0db27962f10ef3c88f64dd44018806f2bdb9ab372aaaec4d243be067025a0

import Foundation

public enum HTTPMethod: String, Hashable, Sendable {
    case get = "GET"
    case post = "POST"
    case delete = "DELETE"
    case put = "PUT"
}

/// Every route of the contract that the app asks, named by its operation id.
public enum APIRoute: String, Hashable, Sendable, CaseIterable {
    case compare = "compare"
    case createShare = "create_share"
    case explainTop = "explain_top"
    case getArea = "get_area"
    case getCensus = "get_census"
    case getGeometry = "get_geometry"
    case getIncome = "get_income"
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
        case .getCensus: return .get
        case .getGeometry: return .get
        case .getIncome: return .get
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
        case .getCensus: return "/v1/areas/{id_or_slug}/census"
        case .getGeometry: return "/v1/areas/geometry"
        case .getIncome: return "/v1/areas/{id_or_slug}/income"
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
        case .getCensus: return "id_or_slug"
        case .getGeometry: return nil
        case .getIncome: return "id_or_slug"
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
        case .getCensus: return true
        case .getGeometry: return true
        case .getIncome: return true
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
        case .getArea: return [304, 404, 422, 500]
        case .getCensus: return [404, 422, 500]
        case .getGeometry: return [304, 500]
        case .getIncome: return [404, 422, 500]
        case .getMeta: return [304, 500]
        case .getShare: return [404, 410, 422, 500]
        case .healthz: return [500]
        case .interpret: return [400, 413, 415, 422, 500]
        case .listAreas: return [304, 500]
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
    /// `GET /v1/areas/{id_or_slug}/census`. The census figures of one area, beside the figures of the whole city and nothing else.
    func getCensus(_ idOrSlug: String) async -> Answer<CensusPanel>
    /// `GET /v1/areas/geometry`. The boundary of every area, as a GeoJSON feature collection.
    func getGeometry() async -> Answer<GeometryData>
    /// `GET /v1/areas/{id_or_slug}/income`. The household income of one area, as its publisher estimates it, and nothing else.
    func getIncome(_ idOrSlug: String) async -> Answer<IncomeShown>
    /// `GET /v1/meta`. The release that is loaded, the vocabulary, the defaults, the limits, and who reads.
    func getMeta() async -> Answer<MetaData>
    /// `GET /v1/shares/{share_id}`. A shared search, ranked now on the release that is loaded.
    func getShare(_ shareId: String) async -> Answer<ShareData>
    /// `GET /healthz`. Whether the service is up. It says nothing about the release, so it has no `meta`.
    func healthz() async -> Result<Health, Failure>
    /// `POST /v1/interpret`. Read a request in words into typed edits, and apply them to the spec.
    func interpret(_ body: InterpretBody) async -> Answer<InterpretData>
    /// `GET /v1/areas`. Every area of the release, by id, and where each sits on every vibe.
    func listAreas() async -> Answer<AreasData>
    /// `POST /v1/rank`. Apply any edits to the spec, then rank every area of the release for it.
    func rank(_ body: RankBody) async -> Answer<RankData>
    /// `POST /v1/places/search`. The places and the areas that match, each best first.
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

    public func getCensus(_ idOrSlug: String) async -> Answer<CensusPanel> {
        await send(.getCensus, parameter: idOrSlug, body: nil)
    }

    public func getGeometry() async -> Answer<GeometryData> {
        await send(.getGeometry, parameter: nil, body: nil)
    }

    public func getIncome(_ idOrSlug: String) async -> Answer<IncomeShown> {
        await send(.getIncome, parameter: idOrSlug, body: nil)
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

extension Accounts {
    /// Every route of accounts, named by its operation id. The app asks none of them.
    public enum Route: String, Hashable, Sendable, CaseIterable {
        /// `POST /v1/auth/link`. Send a link to sign in with. The answer is the same whether or not the address is known.
        /// It takes `LinkBody` and gives `LinkAsked`.
        case askForLink = "ask_for_link"
        /// `DELETE /v1/me`. Delete the account and everything of it. It asks for a sign-in in the last ten minutes.
        /// It takes nothing and gives `Session`.
        case deleteMe = "delete_me"
        /// `DELETE /v1/me/sessions`. Sign out of one browser, or of every one.
        /// It takes `SignOutBody` and gives `Sessions`.
        case endSessions = "end_sessions"
        /// `GET /v1/me/export`. Everything Burro holds of the account.
        /// It takes nothing and gives `Export`.
        case exportMe = "export_me"
        /// `DELETE /v1/me/recent`. Take every one of the last searches away.
        /// It takes nothing and gives `RecentSearches`.
        case forgetRecent = "forget_recent"
        /// `DELETE /v1/me/searches`. Take one search away, and give back those that are left.
        /// It takes `ForgetBody` and gives `KeptSearches`.
        case forgetSearch = "forget_search"
        /// `GET /v1/me`. The address of the account and its preferences.
        /// It takes nothing and gives `Me`.
        case getMe = "get_me"
        /// `GET /v1/auth/session`. Whether the browser is signed in, and as whom. It is answered 200 either way.
        /// It takes nothing and gives `Session`.
        case getSession = "get_session"
        /// `POST /v1/me/recent`. Put a search among the last ten, where the person lets Burro keep them.
        /// It takes `KeepBody` and gives `RecentSearches`.
        case keepRecent = "keep_recent"
        /// `POST /v1/me/searches`. Keep a search. What is kept is the spec, and a name worked out from it.
        /// It takes `KeepBody` and gives `KeptSearch`.
        case keepSearch = "keep_search"
        /// `GET /v1/me/recent`. The last ten searches, where the person lets Burro keep them.
        /// It takes nothing and gives `RecentSearches`.
        case listRecent = "list_recent"
        /// `GET /v1/me/searches`. The searches a person has kept, the newest first.
        /// It takes nothing and gives `KeptSearches`.
        case listSearches = "list_searches"
        /// `GET /v1/me/sessions`. Where a person is signed in.
        /// It takes nothing and gives `Sessions`.
        case listSessions = "list_sessions"
        /// `PUT /v1/me/preferences`. Set a preference, and give back every preference as it now stands.
        /// It takes `PreferencesBody` and gives `Preferences`.
        case setPreferences = "set_preferences"
        /// `POST /v1/auth/session`. Use a link up and sign the browser in. The first time, it makes the account.
        /// It takes `SignInBody` and gives `SignedIn`.
        case signIn = "sign_in"
        /// `DELETE /v1/auth/session`. Sign the browser out. Its session is revoked, and not only forgotten.
        /// It takes nothing and gives `Session`.
        case signOut = "sign_out"
        /// `POST /v1/auth/link/whose`. Whose link this is, for a page to show before it signs anybody in. It uses nothing up.
        /// It takes `TokenBody` and gives `WhoseLink`.
        case whoseLink = "whose_link"

        public var method: HTTPMethod {
            switch self {
            case .askForLink: return .post
            case .deleteMe: return .delete
            case .endSessions: return .delete
            case .exportMe: return .get
            case .forgetRecent: return .delete
            case .forgetSearch: return .delete
            case .getMe: return .get
            case .getSession: return .get
            case .keepRecent: return .post
            case .keepSearch: return .post
            case .listRecent: return .get
            case .listSearches: return .get
            case .listSessions: return .get
            case .setPreferences: return .put
            case .signIn: return .post
            case .signOut: return .delete
            case .whoseLink: return .post
            }
        }

        /// The path as the contract writes it. No route of accounts has a parameter.
        public var template: String {
            switch self {
            case .askForLink: return "/v1/auth/link"
            case .deleteMe: return "/v1/me"
            case .endSessions: return "/v1/me/sessions"
            case .exportMe: return "/v1/me/export"
            case .forgetRecent: return "/v1/me/recent"
            case .forgetSearch: return "/v1/me/searches"
            case .getMe: return "/v1/me"
            case .getSession: return "/v1/auth/session"
            case .keepRecent: return "/v1/me/recent"
            case .keepSearch: return "/v1/me/searches"
            case .listRecent: return "/v1/me/recent"
            case .listSearches: return "/v1/me/searches"
            case .listSessions: return "/v1/me/sessions"
            case .setPreferences: return "/v1/me/preferences"
            case .signIn: return "/v1/auth/session"
            case .signOut: return "/v1/auth/session"
            case .whoseLink: return "/v1/auth/link/whose"
            }
        }

        /// The status the route answers with where all goes well.
        public var answers: Int {
            switch self {
            case .askForLink: return 202
            case .deleteMe: return 200
            case .endSessions: return 200
            case .exportMe: return 200
            case .forgetRecent: return 200
            case .forgetSearch: return 200
            case .getMe: return 200
            case .getSession: return 200
            case .keepRecent: return 200
            case .keepSearch: return 200
            case .listRecent: return 200
            case .listSearches: return 200
            case .listSessions: return 200
            case .setPreferences: return 200
            case .signIn: return 200
            case .signOut: return 200
            case .whoseLink: return 200
            }
        }

        /// The statuses the contract says the route can fail with.
        public var failures: [Int] {
            switch self {
            case .askForLink: return [400, 403, 413, 415, 422, 429, 500, 503]
            case .deleteMe: return [401, 403, 413, 415, 422, 500]
            case .endSessions: return [400, 401, 403, 404, 413, 415, 422, 500]
            case .exportMe: return [401, 403, 422, 500]
            case .forgetRecent: return [401, 403, 413, 415, 422, 500]
            case .forgetSearch: return [400, 401, 403, 404, 413, 415, 422, 500]
            case .getMe: return [401, 403, 422, 500]
            case .getSession: return [403, 422, 500]
            case .keepRecent: return [400, 401, 403, 413, 415, 422, 500]
            case .keepSearch: return [400, 401, 403, 409, 413, 415, 422, 500]
            case .listRecent: return [401, 403, 422, 500]
            case .listSearches: return [401, 403, 422, 500]
            case .listSessions: return [401, 403, 422, 500]
            case .setPreferences: return [400, 401, 403, 413, 415, 422, 500]
            case .signIn: return [400, 403, 409, 410, 413, 415, 422, 429, 500]
            case .signOut: return [403, 413, 415, 422, 500]
            case .whoseLink: return [400, 403, 410, 413, 415, 422, 429, 500]
            }
        }
    }
}
