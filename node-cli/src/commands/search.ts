import { Command } from "commander";
import { getClient, emitResult, fail } from "../client.js";

export function searchCommand(): Command {
  return new Command("search")
    .description("Web search via /v1/search (BYO — needs your own search-backend key)")
    .argument("<query>", "Search query string")
    .option("--engine <engine>", "Search backend (google | bing | duckduckgo)", "google")
    .option("--limit <n>", "Max results (1-20)", "10")
    .option(
      "--provider-key <key>",
      "Your BYO search-backend API key (sent as X-Provider-Authorization: Bearer). " +
        "Without it the API replies 401 search_backend_key_missing.",
    )
    .option("--pretty", "Indent JSON output", false)
    .action(
      async (
        query: string,
        opts: { engine: string; limit: string; providerKey?: string; pretty: boolean },
      ) => {
        const client = getClient();
        try {
          // Wraps the real node SDK search() method → POST /v1/search. The provider
          // key is BYO and never read from CLI args unless the user passes it.
          const options: {
            query: string;
            engine?: "google" | "bing" | "duckduckgo";
            limit?: number;
            providerKey?: string;
          } = {
            query,
            engine: opts.engine as "google" | "bing" | "duckduckgo",
            limit: Number(opts.limit),
          };
          if (opts.providerKey) options.providerKey = opts.providerKey;
          const result = await client.search(options);
          emitResult(result, opts.pretty);
        } catch (e) {
          fail(e);
        }
      },
    );
}
