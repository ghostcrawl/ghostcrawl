// Extract structured JSON from a page against a schema.
//
//   npm install @ghostcrawl/sdk
//   export GHOSTCRAWL_API_KEY=YOUR_API_KEY
//   node extract.mjs

import { GhostcrawlClient } from '@ghostcrawl/sdk';

const client = new GhostcrawlClient({ apiKey: process.env.GHOSTCRAWL_API_KEY });

const result = await client.page.extract({
  url: 'https://example.com',
  engine: 'auto',
  schema: {
    type: 'object',
    properties: {
      title: { type: 'string' },
      summary: { type: 'string' },
    },
  },
});
console.log(result);
