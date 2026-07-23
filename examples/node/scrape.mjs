// Scrape a single page with the GhostCrawl Node SDK.
//
//   npm install @ghostcrawl/sdk
//   export GHOSTCRAWL_API_KEY=YOUR_API_KEY
//   node scrape.mjs

import { GhostcrawlClient } from '@ghostcrawl/sdk';

const client = new GhostcrawlClient({ apiKey: process.env.GHOSTCRAWL_API_KEY });

const result = await client.page.scrape({ url: 'https://example.com', engine: 'chrome' });
console.log(result);
