// Writes what the website takes from contracts/openapi.json.
//
//   node scripts/gen-api.mjs           write the files
//   node scripts/gen-api.mjs --check   write nothing; fail if a file is out of date
//
// Two files come of it:
//   src/lib/api/schema.d.ts   every API type
//   src/lib/api/required.ts   what each answer must hold, by name, for the client to check
//
// The contract is the only source of either. Nothing in src/ writes one by hand.

import { readFile, writeFile } from "node:fs/promises";

import openapiTS, { astToString } from "openapi-typescript";

const CONTRACT = new URL("../../../contracts/openapi.json", import.meta.url);
const TYPES = new URL("../src/lib/api/schema.d.ts", import.meta.url);
const REQUIRED = new URL("../src/lib/api/required.ts", import.meta.url);

const BANNER = `/**
 * Generated from contracts/openapi.json by \`npm run gen:api\`.
 * Never edited by hand: change the contract and generate again.
 */

`;

async function types(contract) {
  const tree = await openapiTS(contract, {
    // The website never changes what the API returned, so every record is read-only.
    immutable: true,
    // One exported name for each schema, so that no file has to spell out
    // components["schemas"]["Name"], and none is tempted to write its own.
    rootTypes: true,
    rootTypesNoSchemaPrefix: true,
    // A field the contract gives a default is typed as always there. The API
    // always sends it, and the website always sends it: nothing is left to a
    // default the two might come to disagree about.
    defaultNonNullable: true,
    silent: true,
  });
  return BANNER + astToString(tree);
}

/** The schema a reference names, or the schema itself where it is written in place. */
function resolved(contract, schema) {
  const name = schema?.$ref?.split("/").pop();
  return name === undefined ? (schema ?? {}) : (contract.components.schemas[name] ?? {});
}

/**
 * The fields the contract requires in the `data` of each operation's answer,
 * by operation id. An operation whose answer has no `data` is left out.
 */
function required(contract) {
  const byOperation = {};
  for (const item of Object.values(contract.paths)) {
    for (const operation of Object.values(item)) {
      const answer = operation.responses?.["200"]?.content?.["application/json"]?.schema;
      const data = resolved(contract, answer).properties?.data;
      if (data === undefined) continue;
      byOperation[operation.operationId] = [...(resolved(contract, data).required ?? [])].sort();
    }
  }
  const lines = Object.keys(byOperation)
    .sort()
    .map((id) => `  ${id}: ${JSON.stringify(byOperation[id]).replaceAll(",", ", ")},`);
  return `${BANNER}/** What the contract requires in the \`data\` of each operation's answer. */
export const REQUIRED_IN_DATA = {
${lines.join("\n")}
} as const;
`;
}

async function committed(target) {
  try {
    return await readFile(target, "utf8");
  } catch {
    return null;
  }
}

const check = process.argv.includes("--check");
const contract = JSON.parse(await readFile(CONTRACT, "utf8"));
const files = [
  ["src/lib/api/schema.d.ts", TYPES, await types(contract)],
  ["src/lib/api/required.ts", REQUIRED, required(contract)],
];

for (const [name, target, fresh] of files) {
  if (!check) {
    await writeFile(target, fresh);
    process.stdout.write(`Wrote ${name}\n`);
  } else if ((await committed(target)) !== fresh) {
    process.stderr.write(
      `${name} is out of date with contracts/openapi.json. Run \`npm run gen:api\`.\n`,
    );
    process.exitCode = 1;
  } else {
    process.stdout.write(`${name} matches contracts/openapi.json\n`);
  }
}
