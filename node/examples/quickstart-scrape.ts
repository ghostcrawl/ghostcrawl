/**
 * Quickstart: scrape a single URL and print the content.
 *
 * Run with:
 *   GHOSTCRAWL_API_KEY=gck_live_YOUR_KEY npx tsx examples/quickstart-scrape.ts
 */
import { createGhostCrawlClient } from "../src/index.js";

async function main(): Promise<void> {
  const token = process.env.GHOSTCRAWL_API_KEY;
  if (!token) {
    console.error("Set GHOSTCRAWL_API_KEY in your environment.");
    process.exit(1);
  }

  const client = createGhostCrawlClient({ token });

  // Canonical LLM-ready markdown scrape. On the cloud a no-identity scrape is served by
  // an auto-assigned SPOOFED identity, and the markdown envelope carries identity_id so
  // this exact drive can be correlated to its egress-exit assignment (D-04).
  const result = await client.scrape({
    url: "https://example.com",
    format: "markdown",
  });

  console.log("Scrape status:", result["status"] ?? "unknown");
  console.log("identity_id:", result["identity_id"] ?? "unknown");
  const content = result["markdown"] ?? result["content"] ?? result["html"] ?? "";
  console.log("Content preview:");
  console.log(String(content).slice(0, 500));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
