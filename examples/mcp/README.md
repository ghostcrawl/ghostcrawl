# MCP client examples

These files configure an MCP **client** (your AI agent / IDE) to talk to
GhostCrawl's MCP endpoint. They are **not** an MCP server package, and GhostCrawl
does not host an AI model for you today — you bring the agent; we provide the
browsers and tools.

GhostCrawl MCP is available only as:

| Mode | Endpoint | License |
|------|----------|---------|
| Managed cloud | `https://mcp.ghostcrawl.io` | Proprietary (cloud / EULA) |
| Self-host Docker image | `http://localhost:47700/mcp` | Proprietary (self-host image / EULA) |

There is no public, standalone `ghostcrawl-mcp-server` install. The MIT-licensed
pieces here are client configs and the optional SDK wrappers
(`pip install ghostcrawl[mcp]`, `@ghostcrawl/sdk`).

| File | What it shows |
|------|---------------|
| `config.json` | Agent **client** connection config for the hosted MCP endpoint. |
| `client.py` | Connect from Python via the MIT SDK MCP client wrapper. |

## Configure an MCP client (cloud)

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

## Self-host Docker

Run the proprietary image first
([self-host guide](https://docs.ghostcrawl.io/self-host)), then point the same
client config at `http://localhost:47700/mcp`.
