import Foundation

/// What carries one request to the API and brings the answer back.
///
/// The client is written against this, so a test passes a stand-in and no
/// test reaches a network.
public protocol Transport: Sendable {
    func send(_ request: URLRequest) async throws -> (Data, HTTPURLResponse)
}

/// The transport the app uses: a `URLSession` that keeps nothing.
///
/// No cache, no cookie and no credential is written to the phone, so which
/// area a person read and what they sent leave no trace there. The API never
/// redirects, so a redirect is never followed: a body that followed one would
/// carry what was typed somewhere else.
public struct URLSessionTransport: Transport {
    private let session: URLSession

    public init() {
        session = URLSession(configuration: Self.configuration(), delegate: NoRedirects(), delegateQueue: nil)
    }

    /// A session that writes nothing to the phone: no cache, no cookie, no credential.
    static func configuration() -> URLSessionConfiguration {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.urlCache = nil
        configuration.requestCachePolicy = .reloadIgnoringLocalCacheData
        configuration.httpCookieStorage = nil
        configuration.httpShouldSetCookies = false
        configuration.httpCookieAcceptPolicy = .never
        configuration.urlCredentialStorage = nil
        configuration.waitsForConnectivity = false
        return configuration
    }

    public func send(_ request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        return (data, response)
    }
}

private final class NoRedirects: NSObject, URLSessionTaskDelegate, Sendable {
    func urlSession(
        _ session: URLSession,
        task: URLSessionTask,
        willPerformHTTPRedirection response: HTTPURLResponse,
        newRequest request: URLRequest
    ) async -> URLRequest? {
        nil
    }
}
