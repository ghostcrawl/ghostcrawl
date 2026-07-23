import { Command } from "commander";
import { getClient, rawRequest, emitResult, fail } from "../client.js";

export function mapCommand(): Command {
  return new Command("map")
    .description("Discover all reachable URLs from a seed (no content scrape)")
    .argument("<url>", "Seed URL to map")
    .option("--pretty", "Indent JSON output", false)
    .action(async (url: string, opts: { pretty: boolean }) => {
      const client = getClient();
      try {
        // /v1/map is not surfaced as a typed SDK method — use the raw passthrough.
        const result = await rawRequest(client, "POST", "/v1/map", { url });
        emitResult(result, opts.pretty);
      } catch (e) {
        fail(e);
      }
    });
}
