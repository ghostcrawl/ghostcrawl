# Install

ghostcrawl ships two ways to install: the SDKs (for talking to the managed
cloud) and the CLI-driven self-host image (for running locally). Both come from
the same packages.

---

## SDKs (cloud)

**Python:**

```bash
pip install ghostcrawl
```

Requires Python 3.10+.

**Node:**

```bash
npm install @ghostcrawl/sdk
```

Requires Node.js 18+.

The Python package also installs the `ghostcrawl` CLI used for self-hosting.

---

## Self-host (Docker)

The self-host install is an 8-verb flow. Each verb maps 1:1 to a CLI subcommand.

| Verb | What it does |
|------|--------------|
| `init` | Prompt for your API key; store it in your OS keychain. |
| `install` | Exchange the key for a pull token; pull and verify the image. |
| `start` | Launch the container with a local API, MCP, and dashboard. |
| `stop` | Stop and remove the container. |
| `status` | Show container state, API health, and your tier/quota. |
| `updates` | Check the cloud for a newer image tag (non-blocking). |
| `upgrade` | Stop, install the new tag, and start. |
| `uninstall` | Remove the container, image, and local config. |

### First run

```bash
ghostcrawl init        # stores your API key in the OS keychain
ghostcrawl install     # pulls + verifies the container image
ghostcrawl start       # launches locally
ghostcrawl status      # confirms it is healthy
```

### Requirements

- A container runtime (Docker or Podman).
- A valid API key. Sign up to obtain one — the key gates the image, and the
  self-host runtime validates it online every time it starts.
- Outbound network access to the ghostcrawl API for the start-time license
  check (there is no offline mode).

### Getting a key

Create an account, verify your email, log in, and mint an API key from your
dashboard. That key is what `ghostcrawl init` stores.

---

## Verifying

```bash
ghostcrawl status
```

A healthy instance reports the container as running, the local API as reachable,
and your current tier and quota usage.
