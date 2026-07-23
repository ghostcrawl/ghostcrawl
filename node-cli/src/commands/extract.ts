import { Command } from "commander";
import { promises as fs } from "node:fs";
import { getClient, rawRequest, emitResult, fail } from "../client.js";

export function extractCommand(): Command {
  return new Command("extract")
    .description("Extract structured data via /v1/extract")
    .argument("<url>", "URL to extract from")
    .requiredOption("--schema <path>", "Path to a JSON schema file (required by the API)")
    .option("--pretty", "Indent JSON output", false)
    .action(async (url: string, opts: { schema: string; pretty: boolean }) => {
      const client = getClient();
      let schema: unknown;
      try {
        schema = JSON.parse(await fs.readFile(opts.schema, "utf-8"));
      } catch (e) {
        process.stderr.write(
          `Error: could not read/parse schema file ${opts.schema}: ${(e as Error).message}\n`,
        );
        process.exit(1);
      }
      try {
        // /v1/extract is not a typed SDK method; the `schema` field is required.
        const result = await rawRequest(client, "POST", "/v1/extract", { url, schema });
        emitResult(result, opts.pretty);
      } catch (e) {
        fail(e);
      }
    });
}
