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
docker pull get.ghostcrawl.io/ghostcrawl/ghostcrawl:2.3.9
```

Full flags (EULA, key, tmpfs, health, first scrape):
[Self-host usage](usage-selfhost.md) and
[docs.ghostcrawl.io/self-host](https://docs.ghostcrawl.io/self-host).

Easiest: the Docker-only launcher at
[`https://dev.ghostcrawl.io/ghostcrawl.sh`](https://dev.ghostcrawl.io/ghostcrawl.sh)
handles the RAM mount, storage, localhost binding and lifecycle through one shared
command set on Linux, macOS and Windows — there is no Windows-only installer. The one
full guide, with all six install requirements and inline PowerShell equivalents, is
[docs.ghostcrawl.io/self-host](https://docs.ghostcrawl.io/self-host).
Advanced: [`docker-compose.yml.template`](../docker-compose.yml.template).

### Platforms & architecture

The published image is `linux/amd64` — native on Intel/x86 and the canonical live
image (not replaced). A native `linux/arm64` leg is being built and staged for 2.3.9
but is **not publicly published yet**; no public arm64 tag exists today.
**Apple Silicon (M-series)** runs that native arm64 leg once it ships (until then Docker
Desktop translates the amd64 image). **ARM Windows** has no native arm64 image —
Docker uses amd64 emulation. All three engines (Chromium, Firefox, WebKit) are
being gated for native arm64 in 2.3.9; their per-engine status is recorded once
the sign-off evidence lands.

### Requirements

- Docker only (Docker Engine on Linux, Docker Desktop on macOS/Windows).
- An API key from your [account](https://app.ghostcrawl.io) (or a license key).
- Outbound access to GhostCrawl for the start-time license check.
- ~3 GB memory allocated to Docker (the 2 GB tmpfs is executable RAM).

### Verifying

```bash
curl http://localhost:47700/healthz
# {"status":"ok"}
```

Open the dashboard: `http://localhost:47700/dashboard`.
