import { Command } from "commander";
import { getClient, emitResult, fail } from "../client.js";

export function scrapeCommand(): Command {
  return new Command("scrape")
    .description("Scrape a URL and emit JSON to stdout")
    .argument("<url>", "URL to scrape")
    .option("--render-js", "Execute JavaScript on the page", false)
    .option("--country <cc>", "ISO 3166-1 alpha-2 country code", "us")
    .option("--format <fmt>", "Output format: html | markdown", "html")
    .option("--pretty", "Indent JSON output", false)
    .action(
      async (
        url: string,
        opts: { renderJs: boolean; country: string; format: string; pretty: boolean },
      ) => {
        const client = getClient();
        try {
          // The /v1/scrape contract: the server assembles a coherent
          // identity for the request — the CLI does NOT send a profile_id
          // (an empty profile_id forces a server-side identity-assembly
          // path that times out).
          //
          // `format` maps the --format flag onto the API's response format.
          // `render_js` / `country` are forwarded as extra fields (the server
          // ignores unknown keys) to preserve the historical flag surface.
          const result = await client.scrape({
            url,
            format: opts.format as "markdown" | "html" | "text",
            render_js: opts.renderJs,
            country: opts.country,
          });
          // Scan for a TARGET failure (blocked / captcha / target HTTP error /
          // navigation failed / empty content) before emitting — a failed
          // scrape must exit non-zero, never print as a fake success.
          emitResult(result, opts.pretty);
        } catch (e) {
          fail(e);
        }
      },
    );
}
