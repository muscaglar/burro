/**
 * Holds a value to a schema of the contract, for a test to say that what the
 * website sends is what the API takes.
 *
 * It reads contracts/openapi.json whole, because every schema in it points at
 * another by its place in that document.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import Ajv2020 from "ajv/dist/2020";

const CONTRACT_FILE = path.resolve(__dirname, "..", "..", "..", "..", "contracts", "openapi.json");

let ajv: Ajv2020 | null = null;

function validator(): Ajv2020 {
  if (ajv === null) {
    ajv = new Ajv2020({ strict: false, allErrors: true, validateFormats: false });
    ajv.addSchema(JSON.parse(readFileSync(CONTRACT_FILE, "utf8")) as object, "contract");
  }
  return ajv;
}

/**
 * What is wrong with `value` as the schema of that name, as where and what
 * kind. Never the value: a failure prints nothing that was sent.
 */
export function problemsWith(schema: string, value: unknown): string[] {
  const validate = validator().getSchema(`contract#/components/schemas/${schema}`);
  if (!validate) return [`the contract has no schema named ${schema}`];
  validate(value);
  return (validate.errors ?? []).map((error) => `${error.instancePath} ${error.keyword}`);
}
