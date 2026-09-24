import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

// The accessibility plugin comes with Next's own rules. Taking it from there
// means there is one copy of it, and its recommended rules can be made errors.
const a11y = nextVitals.find((entry) => entry.plugins?.["jsx-a11y"])?.plugins["jsx-a11y"];
if (!a11y) throw new Error("The accessibility rules were not found in eslint-config-next.");

const a11yAsErrors = Object.fromEntries(
  Object.entries(a11y.flatConfigs.recommended.rules).map(([rule, setting]) => {
    const [level, ...options] = Array.isArray(setting) ? setting : [setting];
    return [rule, level === "off" || level === 0 ? "off" : ["error", ...options]];
  }),
);

// What the website must never touch: nothing a person does is kept in the browser.
const STORAGE = ["localStorage", "sessionStorage", "indexedDB", "caches", "cookieStore"];

export default defineConfig([
  ...nextVitals,
  ...nextTypescript,
  {
    rules: {
      ...a11yAsErrors,
      // Nothing is written to the console: what is written there can hold what a person typed.
      "no-console": "error",
      "no-restricted-globals": [
        "error",
        ...STORAGE.map((name) => ({
          name,
          message: "The website stores nothing in the browser. See docs/design/web.md, section 10.",
        })),
      ],
      "no-restricted-properties": [
        "error",
        ...STORAGE.flatMap((property) =>
          ["window", "globalThis", "self"].map((object) => ({
            object,
            property,
            message:
              "The website stores nothing in the browser. See docs/design/web.md, section 10.",
          })),
        ),
        {
          object: "document",
          property: "cookie",
          message: "The website sets no cookie and reads none.",
        },
        {
          object: "navigator",
          property: "serviceWorker",
          message: "The website has no service worker.",
        },
        {
          object: "navigator",
          property: "sendBeacon",
          message: "There is no analytics and no error reporter.",
        },
      ],
    },
  },
  {
    // A test has to look at storage to say that nothing was put there.
    files: ["**/*.test.ts", "**/*.test.tsx", "test/**", "tests/**"],
    rules: {
      "no-restricted-globals": "off",
      "no-restricted-properties": "off",
    },
  },
  globalIgnores([
    ".next/**",
    ".swc/**",
    "coverage/**",
    "node_modules/**",
    "next-env.d.ts",
    // Generated from the contract, and recorded from the API. Neither is written by hand.
    "src/lib/api/schema.d.ts",
    "src/lib/api/required.ts",
    "test/recorded/**",
  ]),
]);
