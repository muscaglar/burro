/** @jest-environment node */
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";

import { REQUIRED_OF_A_LINK } from "@/lib/account/client";
import { ACCOUNT_ROUTES } from "@/lib/account/routes";
import { ROUTES } from "@/lib/api/operations";
import { REQUIRED_IN_DATA } from "@/lib/api/required";

const ROOT = path.resolve(__dirname, "..");

describe("the generated API types", () => {
  test("test_the_committed_types_are_what_the_contract_generates", () => {
    // The generator is an ES module, so it is run as the npm script runs it.
    const run = spawnSync(process.execPath, ["scripts/gen-api.mjs", "--check"], {
      cwd: ROOT,
      encoding: "utf8",
    });

    expect(run.stderr).toBe("");
    expect(run.status).toBe(0);
  });

  test("test_what_each_answer_must_hold_is_what_the_contract_requires_of_it", () => {
    const contract = JSON.parse(
      readFileSync(path.join(ROOT, "..", "..", "contracts", "openapi.json"), "utf8"),
    ) as { components: { schemas: Record<string, { required?: string[] }> } };
    const written = readFileSync(path.join(ROOT, "src", "lib", "api", "required.ts"), "utf8");

    expect(written.startsWith("/**\n * Generated from contracts/openapi.json")).toBe(true);
    // Two that a search cannot do without, held to the contract by name.
    expect([...REQUIRED_IN_DATA.rank].sort()).toEqual([...(contract.components.schemas.RankData?.required ?? [])].sort());
    expect([...REQUIRED_IN_DATA.interpret].sort()).toEqual(
      [...(contract.components.schemas.InterpretData?.required ?? [])].sort(),
    );
    // Every operation the website calls is there, so none goes unchecked: of the API
    // itself, and of accounts. What is generated lists what an answer of 200 must hold, and
    // asking for a link is answered 202: the client of accounts holds that one itself.
    const called = [...Object.keys(ROUTES), ...Object.keys(ACCOUNT_ROUTES)];
    expect([...Object.keys(REQUIRED_IN_DATA), "ask_for_link"].sort()).toEqual(called.sort());
    expect(REQUIRED_OF_A_LINK.length).toBeGreaterThan(0);
    for (const names of Object.values(REQUIRED_IN_DATA)) expect(names.length).toBeGreaterThan(0);
  });

  test("test_the_types_file_says_it_is_generated_and_names_every_schema", () => {
    const contract = JSON.parse(
      readFileSync(path.join(ROOT, "..", "..", "contracts", "openapi.json"), "utf8"),
    ) as { components: { schemas: Record<string, unknown> } };
    const types = readFileSync(path.join(ROOT, "src", "lib", "api", "schema.d.ts"), "utf8");

    expect(types.startsWith("/**\n * Generated from contracts/openapi.json")).toBe(true);
    for (const name of Object.keys(contract.components.schemas)) {
      expect(types).toContain(`components['schemas']['${name}']`);
    }
  });
});
