import { Command } from "commander";
import { getClient, emitResult, fail } from "../client.js";

export function contentCommand(): Command {
  return new Command("content")
    .description("Fetch a URL's rendered content via /v1/content")
    .argument("<url>", "URL to fetch content from")
    .option("--engine <engine>", "Browser engine (auto | chrome | firefox | webkit)")
    .option("--pretty", "Indent JSON output", false)
    .action(async (url: string, opts: { engine?: string; pretty: boolean }) => {
      const client = getClient();
      try {
        // Wraps the real node SDK content() method (Plan 02) → POST /v1/content.
        const options: { url: string; engine?: string } = { url };
        if (opts.engine) options.engine = opts.engine;
        const result = await client.content(options);
        emitResult(result, opts.pretty);
      } catch (e) {
        fail(e);
      }
    });
}
