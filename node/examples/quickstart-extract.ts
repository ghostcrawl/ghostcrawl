/**
 * Quickstart: extract structured data from a URL.
 *
 * /v1/extract performs fast, deterministic extraction driven by your JSON Schema.
 * Annotate each property with `x-css` (a CSS selector applied to the page) or
 * `x-regex` (a pattern matched against the page text, capture group 1) to tell
 * the extractor where each field lives. Fields without a selector are best-effort.
 *
 * Run with:
 *   GHOSTCRAWL_API_KEY=gck_live_YOUR_KEY npx tsx examples/quickstart-extract.ts
 */
import { createGhostCrawlClient } from "../src/index.js";

// Selectors target the structure of https://example.com (an <h1> title and a
// descriptive <p>). Point TARGET_URL at your own page and adjust the selectors.
const PAGE_SCHEMA = {
  type: "object",
  properties: {
    title: { type: "string", "x-css": "h1" },
    description: { type: "string", "x-css": "p" },
  },
};

async function main(): Promise<void> {
  const token = process.env.GHOSTCRAWL_API_KEY;
  if (!token) {
    console.error("Set GHOSTCRAWL_API_KEY in your environment.");
    process.exit(1);
  }

  const target = process.env.TARGET_URL ?? "https://example.com";
  const client = createGhostCrawlClient({ token });

  const result = await client.extract({ url: target, schema: PAGE_SCHEMA });
  console.log("Extracted data:");
  // The API returns { url, data, token_estimate }; `data` holds the structured fields.
  console.log(JSON.stringify(result.data ?? result, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
