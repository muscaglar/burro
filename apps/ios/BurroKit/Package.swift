// swift-tools-version: 6.0

import PackageDescription

// BurroKit holds everything but the app's entry point: the API models and
// client, the search, the design tokens and every view. It depends on nothing.
//
// The recorded answers under Tests/BurroKitTests/Recorded are read by their
// path, so they are left out of what the test target is built from.
let package = Package(
    name: "BurroKit",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "BurroKit", targets: ["BurroKit"])
    ],
    dependencies: [],
    targets: [
        .target(name: "BurroKit"),
        .testTarget(
            name: "BurroKitTests",
            dependencies: ["BurroKit"],
            exclude: ["Recorded"]
        ),
    ],
    swiftLanguageModes: [.v6]
)
