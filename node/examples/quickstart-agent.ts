/**
 * Quickstart: crawl a site and wait for it to finish.
 *
 * NOTE: despite the "agent" in the filename, this example demonstrates a crawl
 * run (client.crawlRuns) — there is no agent call here.
 *
 * A crawl run is asynchronous: start() returns a run_id immediately. Instead of
 * hand-rolling a poll-with-sleep loop, use the event-driven wait() — it
 * long-polls the server (which BLOCKS until the run is terminal) and resolves
 * with the finished run. No client-side timers, no request storm.
 *
 * Prefer webhooks for long-running crawls in production: register a webhook
 * (client.webhooks.create({ url, event_types: ["crawl.completed"] })) and let the
 * server call you back instead of holding a connection open.
 *
 * Run with:
 *   GHOSTCRAWL_API_KEY=gck_live_YOUR_KEY npx tsx examples/quickstart-agent.ts
 */
import { createGhostCrawlClient, GhostCrawlTimeoutError } from "../src/index.js";

async function main(): Promise<void> {
  const token = process.env.GHOSTCRAWL_API_KEY;
  if (!token) {
    console.error("Set GHOSTCRAWL_API_KEY in your environment.");
    process.exit(1);
  }

  const client = createGhostCrawlClient({ token });

  // Start a crawl run.
  const run = await client.crawlRuns.start({
    url: "https://example.com",
    maxDepth: 2,
    maxPages: 25,
  });
  const runId = run.run_id as string;
  console.log(`Started crawl run: ${runId}`);

  // Wait for a terminal state (completed | failed | cancelled). This blocks
  // server-side and returns as soon as the run finishes — no polling loop.
  try {
    const finished = await client.crawlRuns.wait(runId, { timeout: 600 });
    console.log(`Status: ${finished.status}`);
    console.log(`Pages crawled: ${finished.pages_crawled ?? 0}`);
  } catch (err) {
    if (err instanceof GhostCrawlTimeoutError) {
      // Not finished within our deadline — the run keeps going server-side;
      // call wait(runId) again to resume, or check back later.
      console.log("Still running after our deadline — try again or use a webhook.");
    } else {
      throw err;
    }
  }

  // One-liner alternative — start and block until done in a single call:
  //   const done = await client.crawlRuns.start({
  //     url: "https://example.com", wait: true, timeout: 600,
  //   });
  //   console.log(done.status);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
