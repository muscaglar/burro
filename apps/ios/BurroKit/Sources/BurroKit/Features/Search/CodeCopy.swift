import Foundation

// Words for the codes the API sends. A code is the API's. The word for it is
// the app's, and is the website's word for it, from
// apps/web/src/content/labels.ts.
//
// Each answers `nil` for a code this build does not know, and a screen draws
// nothing for it: never a blank, and never the code.

enum CodeCopy {
    static func dimension(_ dimension: Dimension) -> String? {
        switch dimension {
        case .crime: return "Recorded crime"
        case .schools: return "Schools"
        case .greenWater: return "Green space and water"
        case .airNoise: return "Air and noise"
        case .venuesCulture: return "Venues and culture"
        case .homes: return "Homes"
        case .stationAccess: return "Stations"
        case .services: return "Shops and services"
        case .unlisted: return nil
        }
    }

    /// The order the dimensions are shown in. Recorded crime is last: it is off unless asked for.
    static let dimensionOrder: [Dimension] = [
        .stationAccess, .greenWater, .airNoise, .venuesCulture, .services, .schools, .homes, .crime,
    ]

    static func polarity(_ polarity: Polarity) -> String? {
        switch polarity {
        case .more: return "A higher figure counts as better"
        case .less: return "A lower figure counts as better"
        case .either: return "You choose whether higher or lower is better"
        case .unlisted: return nil
        }
    }

    static func direction(_ direction: Direction) -> String? {
        switch direction {
        case .more: return "Higher is better"
        case .less: return "Lower is better"
        case .unlisted: return nil
        }
    }

    static func reading(_ reading: TermReading) -> String? {
        switch reading {
        case .high: return "A higher figure counts towards the vibe"
        case .low: return "A lower figure counts towards the vibe"
        case .unlisted: return nil
        }
    }

    static func tenure(_ tenure: Tenure) -> String? {
        switch tenure {
        case .rent: return "Renting"
        case .buy: return "Buying"
        case .unlisted: return nil
        }
    }

    static func segment(_ segment: Segment) -> String? {
        switch segment {
        case .room: return "A room"
        case .studio: return "A studio"
        case .bed1: return "One bedroom"
        case .bed2: return "Two bedrooms"
        case .bed3: return "Three bedrooms"
        case .bed4plus: return "Four bedrooms or more"
        case .flat: return "A flat"
        case .terraced: return "A terraced house"
        case .semiDetached: return "A semi-detached house"
        case .detached: return "A detached house"
        case .unlisted: return nil
        }
    }

    static func mode(_ mode: Mode) -> String? {
        switch mode {
        case .pt: return "Public transport"
        case .cycle: return "By bike"
        case .walk: return "On foot"
        case .unlisted: return nil
        }
    }

    static func strictness(_ strictness: Strictness) -> String? {
        switch strictness {
        case .soft: return "Flexible"
        case .hard: return "Firm limit"
        case .unlisted: return nil
        }
    }

    static func combine(_ combine: Combine) -> String? {
        switch combine {
        case .slowest: return "Only the journey that does worst against its limit counts"
        case .mean: return "The average of the journeys counts"
        case .unlisted: return nil
        }
    }

    static func basis(_ basis: PtBasis) -> String? {
        switch basis {
        case .typical: return "The typical time counts"
        case .justMissed: return "The time if you just miss a service counts"
        case .unlisted: return nil
        }
    }
}
