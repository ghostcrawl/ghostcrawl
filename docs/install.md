# Install

GhostCrawl ships SDKs (talk to the managed cloud or a local self-host) and a
self-host Docker image (run the engines on your machine).

---

## SDKs (cloud or local API)

**Python:**

```bash
pip install ghostcrawl
```

Requires Python 3.10+. Also installs the `ghostcrawl` CLI for API commands
(`scrape`, `crawl`, `extract`, …).

**Node:**

```bash
npm install @ghostcrawl/sdk
```

Requires Node.js 18+.

Store a cloud key once:

```bash
ghostcrawl init   # prompts for gck_live_… ; writes ./ghostcrawl.toml
```

---

## Self-host (Docker)

Canonical path — pull and run the image:

```bash
docker pull get.ghostcrawl.io/ghostcrawl/ghostcrawl:2.3.7
```

Full flags (EULA, key, tmpfs, health, first scrape):
[Self-host usage](usage-selfhost.md) and
[docs.ghostcrawl.io/self-host](https://docs.ghostcrawl.io/self-host).

Compose template: [`docker-compose.yml.template`](../docker-compose.yml.template)
(requires a host tmpfs with `exec` — see the comments in that file).

### Requirements

- A container runtime (Docker or Podman).
- An API key from your [account](https://app.ghostcrawl.io) (or a license key).
- Outbound access to GhostCrawl for the start-time license check.
- ~2 GB RAM for `/run/gc`.

### Verifying

```bash
curl http://localhost:47700/healthz
# {"status":"ok"}
```

Open the dashboard: `http://localhost:47700/dashboard`.
