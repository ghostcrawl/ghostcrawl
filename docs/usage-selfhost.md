# Self-host usage

Run the Docker image on your own machine. Your compute, your IP, your data.

A self-hosted instance runs the browser engines locally and exposes MCP, REST API,
and dashboard on **one port** (`47700`).

Canonical guide: [docs.ghostcrawl.io/self-host](https://docs.ghostcrawl.io/self-host).

---

## Bring it up (Docker)

**Recommended:** use the Docker-only launcher — it asks for your key and configures
everything. One launcher works on Linux, macOS and Windows; there is no Windows-only
installer. Download it from
[`https://dev.ghostcrawl.io/ghostcrawl.sh`](https://dev.ghostcrawl.io/ghostcrawl.sh) and run:

```bash
./ghostcrawl.sh start
```

The single full guide — all six install requirements and inline PowerShell equivalents
on one page — is [docs.ghostcrawl.io/self-host](https://docs.ghostcrawl.io/self-host).

**Advanced — docker run directly:**

```bash
docker pull get.ghostcrawl.io/ghostcrawl/ghostcrawl:2.3.9
docker volume create gc-data
docker run -d --name ghostcrawl --restart unless-stopped \
  -p 127.0.0.1:47700:47700 \
  --tmpfs /run/gc:rw,exec,size=2g,mode=1777 \
  -v gc-data:/data \
  -e GHOSTCRAWL_EULA_ACCEPTED=1 \
  -e GHOSTCRAWL_API_KEY="$GC_API_KEY" \
  -e GHOSTCRAWL_LOCAL_PORT=47700 \
  get.ghostcrawl.io/ghostcrawl/ghostcrawl:2.3.9
```

Set `GC_API_KEY` to your account key first. Do not add `--rm`: keeping a failed
container lets you read its logs. You need:

- **Docker only** — Docker Engine on Linux, Docker Desktop on macOS/Windows. No VM,
  WSL, or hypervisor setup by you. Docker Desktop manages its own Linux environment.
- An account API key (`gck_live_…`) from [app.ghostcrawl.io](https://app.ghostcrawl.io).
- `GHOSTCRAWL_EULA_ACCEPTED=1`.
- Outbound HTTPS to GhostCrawl for the **online license check on every start**
  (no offline grace). Configure proxies in Docker Desktop settings if needed.
- ~3 GB allocated to Docker (the 2 GB tmpfs counts against the container's limit).
- **Architecture:** native `linux/amd64` on Intel/x86 (the published, canonical
  image); a native `linux/arm64` leg is being staged for 2.3.9 and is not public
  yet — see [Platforms & architecture](#platforms--architecture) below.

Compose users: copy [`docker-compose.yml.template`](../docker-compose.yml.template)
and run `docker compose up -d` (requires Compose v2.20+/v5). The launcher is simpler.

### Platforms & architecture (2.3.9)

The published self-host image is `linux/amd64` — native on Intel/x86, and it stays
the canonical live image (nothing is replaced). A native `linux/arm64` leg is being
built and staged into the 2.3.9 multi-arch index; it is **not publicly published
yet**, so no public arm64 tag exists today. Per-engine native-arm64 status is gated
for 2.3.9 and will be recorded engine-by-engine (native or blocked) when the sign-off
evidence lands — until then, no shipped arm64 engine is claimed.

| Engine | Intel/x86 — `linux/amd64` (published, canonical) | Apple Silicon — native `linux/arm64` | ARM Windows |
|--------|--------------------------------------------------|--------------------------------------|-------------|
| Chromium | native | native arm64 leg staged for 2.3.9; not public yet (amd64 translation until it ships) | `linux/amd64` via Docker emulation; no native arm64 build |
| Firefox | native | native arm64 leg staged for 2.3.9; not public yet (amd64 translation until it ships) | `linux/amd64` via Docker emulation; no native arm64 build |
| WebKit | native | native arm64 leg staged for 2.3.9; not public yet (amd64 translation until it ships) | `linux/amd64` via Docker emulation; no native arm64 build |

**Apple Silicon (M-series)** runs the native `linux/arm64` leg once it ships; until
then Docker Desktop runs the amd64 image through its built-in translation.
**ARM Windows** has no native arm64 image — Docker runs `linux/amd64` via amd64
emulation (translation).

## Local endpoints

| Surface | URL |
|---------|-----|
| REST API | `http://localhost:47700` |
| MCP | `http://localhost:47700/mcp` |
| Dashboard | `http://localhost:47700/dashboard` |
| Playground | `http://localhost:47700/dashboard/playground` |

Health (no auth):

```bash
curl http://localhost:47700/healthz
```

First API call uses the **per-boot** local token from the container log:

```bash
docker logs ghostcrawl 2>&1 | grep LOCAL_ADMIN_READY
# LOCAL_ADMIN_READY port=47700 token=<YOUR_LOCAL_TOKEN>
```

```python
from ghostcrawl import GhostCrawl

client = GhostCrawl(
    token="YOUR_LOCAL_TOKEN",
    base_url="http://localhost:47700",
)
print(client.scrape(url="https://example.com", format="markdown"))
```

(`token=` and `api_key=` both work.)

---

## Free tier limits

On the free self-host tier:

- **One interactive browser session per engine** (Chrome, Firefox, WebKit).
  Extra sessions return `402` (`free_seat_limit`). One-shot scrapes are serial
  on your machine (not extra interactive seats).
- Hosted stock setups: Windows Chrome, Windows Firefox, Mac Safari. BYO
  identity files are fine; hosted non-stock needs Plus / paid.

Raise seats and unlock premium routing / identities / behavior with
**Self-host Plus ($9/mo)** or any paid cloud plan — choose **Contact sales** in the
[cloud dashboard](https://app.ghostcrawl.io/dashboard/contact?plan=selfhost_bundle).
Your license entitlement unlocks it on the next boot; no extra container config.

You can also set a local concurrency ceiling in the dashboard
(`http://localhost:47700/dashboard`) within what your license allows. Higher
concurrency uses more CPU/RAM on **your** machine.

---

## Updating

```bash
docker pull get.ghostcrawl.io/ghostcrawl/ghostcrawl:2.3.9
docker rm -f ghostcrawl
# re-run the docker run command above
```

---

## CLI note

`pip install ghostcrawl` gives you the `ghostcrawl` CLI for **API verbs**
(`scrape`, `crawl`, `extract`, …) against cloud or a local `base_url`.
Container lifecycle is Docker (`docker run` / Compose) — use the recipe above,
not a separate start/stop CLI.
