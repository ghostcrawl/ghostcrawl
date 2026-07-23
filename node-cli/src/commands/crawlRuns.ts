import { Command } from "commander";
import { getClient, emit, fail } from "../client.js";

export function crawlRunsCommand(): Command {
  return new Command("crawl-runs")
    .description("List crawl-run status via GET /v1/crawl-runs")
    .option("--pretty", "Indent JSON output", false)
    .action(async (opts: { pretty: boolean }) => {
      const client = getClient();
      try {
        // Wraps the real node SDK crawlRuns.list() → GET /v1/crawl-runs.
        const result = await client.crawlRuns.list();
        emit(result, opts.pretty);
      } catch (e) {
        fail(e);
      }
    });
}
