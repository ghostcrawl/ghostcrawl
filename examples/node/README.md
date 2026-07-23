# Node / TypeScript examples

```bash
npm install @ghostcrawl/sdk
export GHOSTCRAWL_API_KEY="YOUR_API_KEY"
```

| File | What it shows |
|------|---------------|
| `scrape.mjs` | Scrape one page. |
| `crawl.mjs` | Start a crawl run and read its status. |
| `extract.mjs` | Extract structured JSON against a schema. |

Run any example (Node 18+):

```bash
node scrape.mjs
```

The SDK is TypeScript-first and ships full type declarations; these examples use
plain ESM so they run with no build step.
