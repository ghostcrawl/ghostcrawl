# Self-host usage

Run the Docker image on your own machine. Your compute, your IP, your data.

A self-hosted instance runs the browser engines locally and exposes MCP, REST API,
and dashboard on **one port** (`47700`).

Canonical guide: [docs.ghostcrawl.io/self-host](https://docs.ghostcrawl.io/self-host).

---

## Bring it up (Docker)

```bash
docker pull get.ghostcrawl.io/ghostcrawl/ghostcrawl:2.3.7

docker run --rm -d \
  --name ghostcrawl \
  -p 47700:47700 \
  --tmpfs /run/gc:size=2g,mode=1777,exec \
  -v gc-data:/data \
  -e GHOSTCRAWL_EULA_ACCEPTED=1 \
  -e GHOSTCRAWL_API_KEY="gck_live_YOUR_KEY" \  # pragma: allowlist secret
  -e GHOSTCRAWL_LOCAL_PORT=47700 \
  get.ghostcrawl.io/ghostcrawl/ghostcrawl:2.3.7
```

You need:

- Docker (or Podman / Kubernetes).
- An account API key (`gck_live_…`) from [app.ghostcrawl.io](https://app.ghostcrawl.io)
  — or a `GHOSTCRAWL_LICENSE_KEY` if you already have one.
- `GHOSTCRAWL_EULA_ACCEPTED=1`.
- Outbound access to GhostCrawl for the **online license check on every start**
  (no offline grace).
- ~2 GB free RAM for the `/run/gc` tmpfs (`exec` is required).

Compose users: copy [`docker-compose.yml.template`](../docker-compose.yml.template)
and mount a **host** tmpfs with `exec` (Compose’s built-in `tmpfs:` is not enough).

---

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
**Self-host Plus ($9/mo)** or any paid cloud plan — buy in the
[cloud dashboard](https://app.ghostcrawl.io) (billing → Self-host Plus). Your
license entitlement unlocks it on the next boot; no extra container config.

You can also set a local concurrency ceiling in the dashboard
(`http://localhost:47700/dashboard`) within what your license allows. Higher
concurrency uses more CPU/RAM on **your** machine.

---

## Updating

```bash
docker pull get.ghostcrawl.io/ghostcrawl/ghostcrawl:2.3.7
docker rm -f ghostcrawl
# re-run the docker run command above
```

---

## CLI note

`pip install ghostcrawl` gives you the `ghostcrawl` CLI for **API verbs**
(`scrape`, `crawl`, `extract`, …) against cloud or a local `base_url`.
Container lifecycle is Docker (`docker run` / Compose) — use the recipe above,
not a separate start/stop CLI.
