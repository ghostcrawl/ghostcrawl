import { Command } from "commander";
import { writeFileSync } from "node:fs";
import { getClient, emit, scanResult, fail } from "../client.js";

export function crawlCommand(): Command {
  return new Command("crawl")
    .description("Start a crawl run (/v1/crawl-runs)")
    .argument("<url>", "Seed URL")
    .option("--max-depth <n>", "Max crawl depth", "2")
    .option("--max-pages <n>", "Max pages to crawl", "100")
    .option("--out <path>", "Output file path")
    .option("--pretty", "Indent JSON output", false)
    .action(
      async (
        url: string,
        opts: { maxDepth: string; maxPages: string; out?: string; pretty: boolean },
      ) => {
        const client = getClient();
        try {
          // The SDK's crawlRuns.start maps { url, maxDepth, maxPages } onto the
          // /v1/crawl-runs tagged-union body (action="start", seed_urls=[url]).
          const result = scanResult(
            await client.crawlRuns.start({
              url,
              maxDepth: Number(opts.maxDepth),
              maxPages: Number(opts.maxPages),
            }),
          );
          if (opts.out) {
            writeFileSync(
              opts.out,
              JSON.stringify(result, null, opts.pretty ? 2 : 0),
            );
            process.stderr.write(`Wrote crawl result to ${opts.out}\n`);
          } else {
            emit(result, opts.pretty);
          }
        } catch (e) {
          fail(e);
        }
      },
    );
}
