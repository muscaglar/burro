// Generated from apps/web/src/styles/tokens.css by apps/ios/scripts/generate.py.
// Never edited by hand: change the source and run `make generate`.
// source-sha256: a1cd4235e4bf2873396eec3c40d9c241bbb2f5963d51249f43ef7ca9ba5b22d2

/// Every colour, space and time of the website's tokens, as it names them.
///
/// `Tokens` gives each its Swift name. Use that, and not this.
public enum TokenValues {
    /// Each colour by its name in `tokens.css`: light, then dark, as `0xRRGGBB`.
    public static let colours: [String: (light: UInt32, dark: UInt32)] = [
        "accent": (0x0a5a8c, 0x8ecbf3),
        "bg": (0xffffff, 0x111416),
        "border": (0x6f7a83, 0x88939c),
        "error": (0x9b1c1c, 0xff9d9d),
        "focus": (0x0a5a8c, 0x8ecbf3),
        "good": (0x1b6638, 0x8fd3a5),
        "info-bg": (0xe8f1f8, 0x12324a),
        "info-text": (0x12324a, 0xd7e9f7),
        "map-1": (0xd6eed1, 0x1c3328),
        "map-2": (0x98d496, 0x284d3a),
        "map-3": (0x58b765, 0x32654a),
        "map-4": (0x3d965b, 0x3b7e58),
        "map-5": (0x287850, 0x449866),
        "map-land": (0xeceae2, 0x25282a),
        "map-line": (0x1b1f23, 0xeef0f1),
        "map-water": (0xc9dfec, 0x0c2735),
        "muted": (0x4d565e, 0xb3bcc3),
        "notice-bg": (0xfff1c2, 0x3a2c00),
        "notice-edge": (0x8a6d00, 0xd1a935),
        "notice-text": (0x3a2c00, 0xffe7a3),
        "on-accent": (0xffffff, 0x0b1c27),
        "surface": (0xf4f5f3, 0x1a1e21),
        "text": (0x1b1f23, 0xeef0f1),
        "tradeoff": (0x8f3a12, 0xf0a57e),
    ]

    /// Each length by its name in `tokens.css`, in points.
    public static let lengths: [String: Double] = [
        "focus-band": 2,
        "focus-ring": 3,
        "radius": 4,
        "radius-card": 8,
        "space-1": 4,
        "space-2": 8,
        "space-3": 12,
        "space-4": 16,
        "space-5": 24,
        "space-6": 32,
        "space-7": 48,
        "space-8": 64,
        "target": 44,
        "target-gap": 8,
        "target-min": 24,
    ]

    /// How long a change takes where motion is welcome, in seconds. Where it is not, none.
    public static let durations: [String: Double] = [
        "motion-fast": 0.12,
        "motion-slow": 0.2,
    ]

    public static let accent = TokenColor(light: 0x0a5a8c, dark: 0x8ecbf3)
    public static let bg = TokenColor(light: 0xffffff, dark: 0x111416)
    public static let border = TokenColor(light: 0x6f7a83, dark: 0x88939c)
    public static let error = TokenColor(light: 0x9b1c1c, dark: 0xff9d9d)
    public static let focus = TokenColor(light: 0x0a5a8c, dark: 0x8ecbf3)
    public static let good = TokenColor(light: 0x1b6638, dark: 0x8fd3a5)
    public static let infoBg = TokenColor(light: 0xe8f1f8, dark: 0x12324a)
    public static let infoText = TokenColor(light: 0x12324a, dark: 0xd7e9f7)
    public static let map1 = TokenColor(light: 0xd6eed1, dark: 0x1c3328)
    public static let map2 = TokenColor(light: 0x98d496, dark: 0x284d3a)
    public static let map3 = TokenColor(light: 0x58b765, dark: 0x32654a)
    public static let map4 = TokenColor(light: 0x3d965b, dark: 0x3b7e58)
    public static let map5 = TokenColor(light: 0x287850, dark: 0x449866)
    public static let mapLand = TokenColor(light: 0xeceae2, dark: 0x25282a)
    public static let mapLine = TokenColor(light: 0x1b1f23, dark: 0xeef0f1)
    public static let mapWater = TokenColor(light: 0xc9dfec, dark: 0x0c2735)
    public static let muted = TokenColor(light: 0x4d565e, dark: 0xb3bcc3)
    public static let noticeBg = TokenColor(light: 0xfff1c2, dark: 0x3a2c00)
    public static let noticeEdge = TokenColor(light: 0x8a6d00, dark: 0xd1a935)
    public static let noticeText = TokenColor(light: 0x3a2c00, dark: 0xffe7a3)
    public static let onAccent = TokenColor(light: 0xffffff, dark: 0x0b1c27)
    public static let surface = TokenColor(light: 0xf4f5f3, dark: 0x1a1e21)
    public static let text = TokenColor(light: 0x1b1f23, dark: 0xeef0f1)
    public static let tradeoff = TokenColor(light: 0x8f3a12, dark: 0xf0a57e)

    public static let focusBand: Double = 2
    public static let focusRing: Double = 3
    public static let radius: Double = 4
    public static let radiusCard: Double = 8
    public static let space1: Double = 4
    public static let space2: Double = 8
    public static let space3: Double = 12
    public static let space4: Double = 16
    public static let space5: Double = 24
    public static let space6: Double = 32
    public static let space7: Double = 48
    public static let space8: Double = 64
    public static let target: Double = 44
    public static let targetGap: Double = 8
    public static let targetMin: Double = 24
}
