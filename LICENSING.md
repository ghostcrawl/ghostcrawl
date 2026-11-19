# Licensing boundaries

This repository is the **public client toolkit**. Read this before assuming MIT
covers everything GhostCrawl ships.

| Component | License | Where it lives |
|-----------|---------|----------------|
| SDKs, CLI, examples, docs in this repo | **MIT** (`LICENSE`) | This GitHub repository + package registries |
| Optional MCP **client** wrappers (`ghostcrawl[mcp]`, `@ghostcrawl/sdk` MCP client) | **MIT** | Same |
| Managed cloud API + hosted MCP (`mcp.ghostcrawl.io`) | **Proprietary** (Terms + [EULA](https://docs.ghostcrawl.io/legal/eula)) | GhostCrawl cloud |
| Self-host **Docker image** (engines, sidecar, in-image MCP, MCP server) | **Proprietary** (EULA; `GHOSTCRAWL_EULA_ACCEPTED=1`) | `get.ghostcrawl.io/ghostcrawl/ghostcrawl:<ver>` |

## No public MCP server

There is **no** public, standalone, open-source MCP server package.

Customers connect an MCP **client** (their AI agent / IDE) to:

1. `https://mcp.ghostcrawl.io` (cloud), or
2. `http://localhost:47700/mcp` after running the proprietary self-host image.

`examples/mcp/` here is client configuration only.

## No GhostCrawl-hosted AI (today)

GhostCrawl does **not** run an AI / LLM on the managed cloud or in the self-host
image today. MCP is only the connection surface so *your* agent can call our
browser tools. Hosted GhostCrawl AI on cloud is a future option, not current.

## Docker / self-host protection

The self-host image is free to run under the Free tier seat limits, but it is
**licensed, not sold**, under the Software License Agreement. You may not
redistribute, sublicense, or re-host the image as a service to third parties.
See [docs.ghostcrawl.io/legal/eula](https://docs.ghostcrawl.io/legal/eula).
