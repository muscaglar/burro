import type { Config } from "jest";
import nextJest from "next/jest.js";

// next/jest compiles TypeScript and CSS modules the way the build does, with
// the compiler that comes inside Next as a library. Nothing here starts a
// program of its own.
const withNext = nextJest({ dir: "./" });

const config: Config = {
  testEnvironment: "<rootDir>/test/support/environment.ts",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    // jsdom has no WebGL, so the map library cannot draw in a test. A
    // stand-in that records what it was asked takes its place.
    "^maplibre-gl$": "<rootDir>/test/support/maplibre.ts",
  },
  // A component's test sits beside it. Tests of the whole site sit in test/.
  // tests/ is read too, so that a test filed under the older name still runs.
  testMatch: [
    "<rootDir>/src/**/*.test.ts",
    "<rootDir>/src/**/*.test.tsx",
    "<rootDir>/test/**/*.test.ts",
    "<rootDir>/test/**/*.test.tsx",
    "<rootDir>/tests/**/*.test.ts",
    "<rootDir>/tests/**/*.test.tsx",
  ],
  // Files are found by Node alone. A file-watching service, where one is
  // installed, is another program to wait on, and a run can hang on it.
  watchman: false,
  // A test that draws the whole search page takes seconds. The slowest opens every setting
  // and checks all of it for faults: it took 21 to 32 seconds with three tests running at
  // once, and it grows as the release measures more. A hosted runner has four cores, and
  // slower ones, so a test is given two minutes.
  testTimeout: 120_000,
  // Tests run offline and leave nothing behind them.
  clearMocks: true,
  restoreMocks: true,
};

export default withNext(config);
