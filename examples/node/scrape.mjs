// Scrape a single page with the GhostCrawl Node SDK.
//
//   npm install @ghostcrawl/sdk
//   export GHOSTCRAWL_API_KEY=YOUR_API_KEY
//   node scrape.mjs

import { GhostCrawlClient } from '@ghostcrawl/sdk';

const client = new GhostCrawlClient({ apiKey: process.env.GHOSTCRAWL_API_KEY });

const result = await client.scrape({ url: 'https://example.com', engine: 'chrome' });
console.log(result);
