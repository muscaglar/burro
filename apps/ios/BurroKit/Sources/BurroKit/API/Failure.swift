import Foundation

/// Why a call gave no answer, when the reason is not the API's own.
public enum ClientFailureKind: String, Hashable, Sendable, CaseIterable {
    /// The app stopped waiting.
    case timeout
    /// The caller stopped it, as "Stop" does.
    case aborted
    /// The phone says it has no connection.
    case offline
    /// The request could not leave, or no answer came back.
    case network
    /// No address is set for the API.
    case notConfigured
    /// An answer came back that is not the API's envelope.
    case unreadable
}

/// The API's error envelope, as a value. `message` is the API's fixed text for the code.
///
/// It holds codes and fixed words, and never anything that was sent.
public struct APIFailure: Hashable, Sendable {
    public let status: Int
    public let code: ErrorCode
    public let message: String
    public let fields: [FieldProblem]
    public let meta: Meta
    /// True if the body or the header says the data is made up.
    public let synthetic: Bool
    /// True if the body or the header says the release is a preview.
    public let preview: Bool
    /// `X-Request-Id`, to quote when reporting a fault.
    public let requestId: String?

    public init(
        status: Int,
        code: ErrorCode,
        message: String,
        fields: [FieldProblem],
        meta: Meta,
        synthetic: Bool,
        preview: Bool,
        requestId: String?
    ) {
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields
        self.meta = meta
        self.synthetic = synthetic
        self.preview = preview
        self.requestId = requestId
    }
}

/// A failure that is the client's own.
public struct ClientFailure: Hashable, Sendable {
    public let kind: ClientFailureKind
    /// The status of the answer, where one came back.
    public let status: Int?
    /// What the answer said of the data, where it said anything.
    public let synthetic: Bool?
    /// What the answer said of its release, where it said anything.
    public let preview: Bool?
    public let requestId: String?

    public init(
        _ kind: ClientFailureKind, status: Int? = nil, synthetic: Bool? = nil, preview: Bool? = nil,
        requestId: String? = nil
    ) {
        self.kind = kind
        self.status = status
        self.synthetic = synthetic
        self.preview = preview
        self.requestId = requestId
    }
}

/// Why a call failed: the API said so in its envelope, or the call never got that far.
public enum Failure: Error, Hashable, Sendable {
    case api(APIFailure)
    case client(ClientFailure)

    /// A failure of the client's own, with nothing seen of an answer.
    public static func because(_ kind: ClientFailureKind) -> Failure {
        .client(ClientFailure(kind))
    }

    /// The API's failure, when it is one.
    public var api: APIFailure? {
        if case .api(let failure) = self { return failure }
        return nil
    }

    /// The kind of the client's failure. `nil` when the API answered.
    public var kind: ClientFailureKind? {
        if case .client(let failure) = self { return failure.kind }
        return nil
    }

    /// The API's code, when the API answered with one.
    public var code: ErrorCode? { api?.code }

    /// The status of the answer, where one came back.
    public var status: Int? {
        switch self {
        case .api(let failure): return failure.status
        case .client(let failure): return failure.status
        }
    }

    public var requestId: String? {
        switch self {
        case .api(let failure): return failure.requestId
        case .client(let failure): return failure.requestId
        }
    }

    public var isOffline: Bool { kind == .offline }
    public var isAborted: Bool { kind == .aborted }
}

/// An answer that went well: `meta`, `data`, and what was said of the data.
public struct Answered<Payload: Sendable>: Sendable {
    public let status: Int
    public let meta: Meta
    public let data: Payload
    /// True if the body or the header says the data is made up.
    public let synthetic: Bool
    /// True if the body or the header says the release is a preview.
    public let preview: Bool
    public let requestId: String?

    public init(
        status: Int, meta: Meta, data: Payload, synthetic: Bool, preview: Bool, requestId: String?
    ) {
        self.status = status
        self.meta = meta
        self.data = data
        self.synthetic = synthetic
        self.preview = preview
        self.requestId = requestId
    }
}

/// What a call to the API comes back as: an answer, or a failure that says why.
public typealias Answer<Payload: Sendable> = Result<Answered<Payload>, Failure>

extension Result where Failure == BurroKit.Failure {
    /// The failure, when the call failed.
    public var failure: BurroKit.Failure? {
        if case .failure(let failure) = self { return failure }
        return nil
    }

    /// True when the API answered with this code.
    public func hasCode(_ code: ErrorCode) -> Bool {
        failure?.code == code
    }
}
