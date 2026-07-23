# MCP examples

GhostCrawl's full user API is available over the Model Context Protocol (MCP) at
`https://mcp.ghostcrawl.io`. Any MCP-capable agent can connect with your API key
as a bearer token.

| File | What it shows |
|------|---------------|
| `config.json` | Drop-in MCP server config for agent clients. |
| `client.py` | Connect to the MCP surface from Python. |

## Configure an MCP client

Add GhostCrawl to your agent's MCP server list (see [`config.json`](config.json)):

```json
{
  "mcpServers": {
    "ghostcrawl": {
      "url": "https://mcp.ghostcrawl.io",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

The MCP surface exposes navigate, act, extract, screenshot, scrape, crawl, and
more — the same managed browsers behind the REST API.

To use a self-hosted instance instead, point the URL at your local MCP endpoint
(default `http://localhost:3143`).
