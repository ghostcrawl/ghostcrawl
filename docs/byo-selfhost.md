# Bring your own config (self-host)

A self-hosted instance reads three optional JSON files from `~/.ghostcrawl/`. Each
is validated when the instance loads it — if a file is malformed or missing a
required field, the instance tells you which file and which field. All BYO input
is JSON.

| File | Path | Purpose |
|------|------|---------|
| Proxy pool | `~/.ghostcrawl/proxies.json` | The proxy exits requests can egress through. |
| Identities | `~/.ghostcrawl/identities/*.json` | One file per browsing identity. |
| Behavior | `~/.ghostcrawl/behavior.json` | A per-page action script. |

Copy the [examples](../examples/selfhost/) as a starting point.

---

## Proxy pool — `proxies.json`

Self-host egresses from your own machine's network by default. Add a proxy pool
when you want requests to exit through proxies you supply. The file is a single
object with a `proxies` array; each entry is one exit:

```json
{
  "proxies": [
    {
      "url": "socks5://your-proxy.example.com:1080",
      "auth": "username:password",
      "claim_os": "windows",
      "geo": "US",
      "asn": null,
      "sticky_session_id": null
    }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `url` | yes | Proxy endpoint. `socks5://`, `http://`, or `https://`. |
| `claim_os` | yes | The OS this exit is for. Must match the identity's `claim_os`. |
| `auth` | no | `username:password` for the proxy, if it needs credentials. |
| `geo` | no | ISO-3166 country hint, e.g. `"US"`. |
| `asn` | no | ASN hint, e.g. `"AS7922"`. |
| `sticky_session_id` | no | Pin an exit to a session. |

> **Bring your own provider.** The shipped `proxies.example.json` is
> **format-only** — a placeholder host and placeholder credentials that show the
> shape, not a working proxy. Self-host is your compute and your network, so you
> supply the provider: sign up with a residential proxy provider of your choice
> and paste the endpoint and credentials they give you into `url` and `auth`.

An identity that claims a non-Linux OS should egress through a proxy on that OS
(`claim_os` match) so the network path is consistent with the identity.

---

## Identities — `identities/*.json`

Drop one JSON file per identity into `~/.ghostcrawl/identities/`. The instance
draws from this pool at request time, filtered by `claim_os` (and optionally
`claim_browser`). Every file must contain all eight keys:

```json
{
  "claim_os": "windows",
  "claim_browser": "chrome",
  "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  "canvas": "0011223344556677",
  "webgl": {
    "vendor": "Google Inc. (Intel)",
    "renderer": "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)"
  },
  "audio": "0.12345678901234",
  "screen": { "width": 1920, "height": 1080, "availWidth": 1920, "availHeight": 1040 },
  "tz": "America/New_York"
}
```

| Key | Description |
|-----|-------------|
| `claim_os` | The OS to present, e.g. `windows`, `macos`, `ios`. |
| `claim_browser` | The engine to run: `chrome`, `firefox`, or `webkit`. |
| `ua` | The `User-Agent` string. |
| `canvas` | Canvas readback token. |
| `webgl` | `{ "vendor", "renderer" }` for the WebGL context. |
| `audio` | Audio context token. |
| `screen` | `{ "width", "height", "availWidth", "availHeight" }`. |
| `tz` | IANA timezone, e.g. `America/New_York`. |

The values in `identity.example.json` are synthetic placeholders — copy the file
and edit each field to describe the identity you want.

---

## Behavior — `behavior.json`

An optional per-page action script. The file is a single object with a
`human_actions` array; each action is one of three kinds:

```json
{
  "human_actions": [
    { "kind": "dwell", "ms": 500 },
    { "kind": "move", "x": 640, "y": 400 },
    { "kind": "wheel", "x": 640, "y": 400, "dy": -300 },
    { "kind": "dwell", "ms": 200 }
  ]
}
```

| Kind | Fields | Bounds |
|------|--------|--------|
| `dwell` | `ms` | `0`–`1500` ms |
| `move` | `x`, `y` | `0`–`10000` px |
| `wheel` | `x`, `y`, `dy` | `x`/`y` `0`–`10000` px; `dy` `-4000`–`4000` |

Actions outside these bounds are clamped; unknown kinds are dropped; the list is
capped at 256 actions. Keep every action within the bounds above and the script
loads exactly as written.

---

## Validating your config

Point a self-host instance at your `~/.ghostcrawl/` files and it validates each on
load, naming the file and field on any error. The instance dashboard also shows
and re-validates the current config.
