# Self-host usage

Run the Docker image on your own machine. Your compute, your IP, your data.

A self-hosted instance runs the browser engines locally and exposes its own MCP,
REST API, and dashboard. It is not the managed cloud control plane — it is you
managing your own local instance, including watching and driving live sessions on
your own hardware.

---

## Bring it up

```bash
ghostcrawl init        # stores your API key in your OS keychain
ghostcrawl install     # pulls + verifies the container image
ghostcrawl start       # launches locally
ghostcrawl status      # confirms it is healthy
```

`ghostcrawl init` stores your API key; `ghostcrawl install` pulls and verifies
the signed image; `ghostcrawl start` launches it with local endpoints.

---

## Online-required start

The self-host image validates your API key online **every time it starts**.
There is no offline grace period: if the cloud license check fails or the API is
unreachable, `start` aborts. Keep outbound access to the ghostcrawl API open on
the host.

---

## Local endpoints

A running instance exposes three local surfaces:

| Surface | Default | Purpose |
|---------|---------|---------|
| REST API | `http://localhost:8000` | Same SDK surface as the cloud, pointed at your local instance. |
| MCP | `http://localhost:3143` | Drive the local browsers from an agent. |
| Dashboard | local web UI | Manage your instance, watch and control live sessions. |

Point an SDK at your local instance by overriding the base URL:

```python
client = GhostcrawlClient(api_key="YOUR_API_KEY", base_url="http://localhost:8000")
```

Live browser viewing and control are available locally — it is your own
hardware.

---

## Concurrency

You choose how many browsers run at once: a total concurrency limit and a
per-engine limit.

> **Warning:** Higher concurrency uses more of your local CPU, memory, and
> network. Each running browser is a real engine process. Start low and raise it
> only as far as your machine comfortably handles.

---

## What self-host includes

The self-host image runs the browser engines and the local API/MCP/dashboard on
your own compute, using your own IP. The managed cloud's automatic exit routing
is a cloud-only feature — self-host requests egress from your machine's own
network.

---

## Updating

```bash
ghostcrawl updates     # check for a newer image tag (non-blocking)
ghostcrawl upgrade     # stop, install the new tag, start
```

## Removing

```bash
ghostcrawl uninstall   # remove the container, image, and local config
```
