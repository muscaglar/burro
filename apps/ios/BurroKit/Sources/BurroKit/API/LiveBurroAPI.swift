import Foundation

/// The API as the app calls it. Every method of `BurroAPI` is made of `send`.
///
/// It never throws, and it writes nowhere but to the API: no log, no file, no
/// cache. What a person typed is in the body of a `POST` and in no other
/// place, the address included.
public struct LiveBurroAPI: BurroAPI, RouteSending {
    public static let syntheticHeader = "X-Burro-Synthetic"
    public static let previewHeader = "X-Burro-Preview"
    public static let requestIdHeader = "X-Request-Id"

    private let configuration: APIConfiguration
    private let transport: any Transport
    private let timeouts: Timeouts
    private let onSynthetic: @Sendable (Bool) async -> Void
    private let onPreview: @Sendable (Bool) async -> Void

    /// - Parameters:
    ///   - onSynthetic: Told what each answer says of the data, before the answer is
    ///     handed over, so the banner is never later than what it is about.
    ///   - onPreview: Told what each answer says of its release, in the same way.
    public init(
        configuration: APIConfiguration,
        transport: any Transport = URLSessionTransport(),
        timeouts: Timeouts = Timeouts(),
        onSynthetic: @escaping @Sendable (Bool) async -> Void = { _ in },
        onPreview: @escaping @Sendable (Bool) async -> Void = { _ in }
    ) {
        self.configuration = configuration
        self.transport = transport
        self.timeouts = timeouts
        self.onSynthetic = onSynthetic
        self.onPreview = onPreview
    }

    public func send<Payload: Decodable & Sendable>(
        _ route: APIRoute, parameter: String?, body: (any Encodable & Sendable)?
    ) async -> Answer<Payload> {
        let received: Received
        switch await receive(route, parameter: parameter, body: body) {
        case .failure(let failure): return .failure(failure)
        case .success(let answer): received = answer
        }

        let decoder = JSONDecoder()
        guard let meta = try? decoder.decode(MetaOnly.self, from: received.data).meta else {
            // Whoever shows a banner hears of each answer once, whatever became of it.
            if let said = received.synthetic { await onSynthetic(said) }
            if let said = received.preview { await onPreview(said) }
            return .failure(
                .client(
                    received.failed(.unreadable, synthetic: received.synthetic, preview: received.preview)))
        }
        // Made-up data is never shown as real. If the body and the header disagree,
        // or only one of them speaks, the answer counts as made up when either says so.
        // A preview is never shown as finished, in the same way.
        let synthetic = meta.synthetic || received.synthetic == true
        let preview = meta.preview || received.preview == true
        await onSynthetic(synthetic)
        await onPreview(preview)

        if let refusal = try? decoder.decode(ErrorEnvelope.self, from: received.data) {
            return .failure(
                .api(
                    APIFailure(
                        status: received.status,
                        code: refusal.error.code,
                        message: refusal.error.message,
                        fields: refusal.error.fields,
                        meta: refusal.meta,
                        synthetic: synthetic,
                        preview: preview,
                        requestId: received.requestId
                    )))
        }
        // An answer that lacks what the contract requires of it is not the API's answer.
        guard (200..<300).contains(received.status),
            let envelope = try? decoder.decode(Envelope<Payload>.self, from: received.data)
        else {
            return .failure(.client(received.failed(.unreadable, synthetic: synthetic, preview: preview)))
        }
        return .success(
            Answered(
                status: received.status,
                meta: envelope.meta,
                data: envelope.data,
                synthetic: synthetic,
                preview: preview,
                requestId: received.requestId
            ))
    }

    public func sendPlain<Payload: Decodable & Sendable>(_ route: APIRoute) async -> Result<Payload, Failure> {
        switch await receive(route, parameter: nil, body: nil) {
        case .failure(let failure):
            return .failure(failure)
        case .success(let received):
            if let said = received.synthetic { await onSynthetic(said) }
            if let said = received.preview { await onPreview(said) }
            guard (200..<300).contains(received.status),
                let payload = try? JSONDecoder().decode(Payload.self, from: received.data)
            else {
                return .failure(
                    .client(
                        received.failed(
                            .unreadable, synthetic: received.synthetic, preview: received.preview)))
            }
            return .success(payload)
        }
    }

    // MARK: - One request

    private struct MetaOnly: Decodable {
        let meta: Meta
    }

    private struct Received: Sendable {
        let data: Data
        let status: Int
        let synthetic: Bool?
        let preview: Bool?
        let requestId: String?

        func failed(_ kind: ClientFailureKind, synthetic: Bool?, preview: Bool?) -> ClientFailure {
            ClientFailure(
                kind, status: status, synthetic: synthetic, preview: preview, requestId: requestId)
        }
    }

    private struct TimedOut: Error {}

    private func receive(
        _ route: APIRoute, parameter: String?, body: (any Encodable & Sendable)?
    ) async -> Result<Received, Failure> {
        guard let base = configuration.baseURL else { return .failure(.because(.notConfigured)) }
        if Task.isCancelled { return .failure(.because(.aborted)) }
        guard let request = Self.request(route, base: base, parameter: parameter, body: body) else {
            return .failure(.because(.unreadable))
        }
        let transport = self.transport
        let limit = timeouts.of(route)
        do {
            let (data, response) = try await withThrowingTaskGroup(of: (Data, HTTPURLResponse).self) { group in
                group.addTask { try await transport.send(request) }
                group.addTask {
                    try await Task.sleep(for: limit)
                    throw TimedOut()
                }
                defer { group.cancelAll() }
                guard let first = try await group.next() else { throw URLError(.unknown) }
                return first
            }
            return .success(
                Received(
                    data: data,
                    status: response.statusCode,
                    synthetic: Self.flag(response.value(forHTTPHeaderField: Self.syntheticHeader)),
                    preview: Self.flag(response.value(forHTTPHeaderField: Self.previewHeader)),
                    requestId: response.value(forHTTPHeaderField: Self.requestIdHeader)
                ))
        } catch {
            return .failure(.because(Self.why(error)))
        }
    }

    /// The request for a route. `nil` when the route has a parameter and none was given.
    static func request(
        _ route: APIRoute, base: URL, parameter: String?, body: (any Encodable & Sendable)?
    ) -> URLRequest? {
        guard let path = path(of: route, parameter: parameter),
            let url = URL(string: base.absoluteString + path)
        else { return nil }
        var request = URLRequest(url: url)
        request.httpMethod = route.method.rawValue
        request.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
        // The API sets no cookie and reads none.
        request.httpShouldHandleCookies = false
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if route.method == .post {
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.sortedKeys]
            guard let body, let encoded = try? encoder.encode(body) else { return nil }
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = encoded
        }
        return request
    }

    /// The path of a route, with its one parameter filled in where it has one.
    static func path(of route: APIRoute, parameter: String?) -> String? {
        guard let name = route.parameter else { return route.template }
        // An id from the release or from a share. It is never something a person typed.
        var allowed = CharacterSet.alphanumerics
        allowed.insert(charactersIn: "-._~")
        guard let parameter, !parameter.isEmpty,
            let encoded = parameter.addingPercentEncoding(withAllowedCharacters: allowed)
        else { return nil }
        return route.template.replacingOccurrences(of: "{\(name)}", with: encoded)
    }

    static func flag(_ header: String?) -> Bool? {
        switch header {
        case "true": return true
        case "false": return false
        default: return nil
        }
    }

    private static func why(_ error: any Error) -> ClientFailureKind {
        if error is TimedOut { return .timeout }
        if error is CancellationError || Task.isCancelled { return .aborted }
        guard let error = error as? URLError else { return .network }
        switch error.code {
        case .cancelled: return .aborted
        case .timedOut: return .timeout
        case .notConnectedToInternet, .dataNotAllowed, .internationalRoamingOff: return .offline
        default: return .network
        }
    }
}
