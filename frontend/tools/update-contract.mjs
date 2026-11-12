import { writeFile } from "node:fs/promises";
// Order object keys without changing ordered schema arrays. No timestamps or
// environment-specific server URL is added to the checked-in contract.
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object")
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
  return value;
}
const response = await fetch(`${process.env.ECHOCASE_API ?? "http://127.0.0.1:5080"}/openapi/v1.json`);
if (!response.ok) throw new Error(`OpenAPI request failed: ${response.status}`);
const schema = await response.json();
delete schema.servers;
await writeFile(new URL("../openapi.json", import.meta.url), JSON.stringify(canonical(schema), null, 2) + "\n");
