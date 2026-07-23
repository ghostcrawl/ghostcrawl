// Start a crawl run and wait for it to finish.
//
//   npm install @ghostcrawl/sdk
//   export GHOSTCRAWL_API_KEY=YOUR_API_KEY
//   node crawl.mjs

import { GhostcrawlClient } from '@ghostcrawl/sdk';

const client = new GhostcrawlClient({ apiKey: process.env.GHOSTCRAWL_API_KEY });

// Start the crawl and wait for it in one call. This is event-driven: the server
// blocks until the run is terminal (completed/failed/cancelled) or the timeout
// elapses — there is no client poll loop.
const run = await client.crawlRuns.start({
  url: 'https://example.com',
  maxDepth: 2,
  maxPages: 25,
  wait: true,      // start-and-wait (server blocks)
  timeout: 300,    // completion budget, seconds
});

console.log('run id:', run.run_id);
console.log('status:', run.status);
console.log('pages crawled:', run.pages_crawled ?? 0);
