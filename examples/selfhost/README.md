# Self-host BYO examples

Bring-your-own (BYO) config for a self-hosted instance. A self-host instance
reads three optional JSON files from `~/.ghostcrawl/`; drop your own in and the
instance validates them on load. All three inputs are JSON.

| Example | Copy to | What it configures |
|---------|---------|--------------------|
| [`proxies.example.json`](proxies.example.json) | `~/.ghostcrawl/proxies.json` | Your proxy pool (one entry per exit). |
| [`identity.example.json`](identity.example.json) | `~/.ghostcrawl/identities/<name>.json` | One browsing identity (drop one file per identity into the `identities/` directory). |
| [`behavior.example.json`](behavior.example.json) | `~/.ghostcrawl/behavior.json` | A per-page action script. |

See the [BYO self-host guide](../../docs/byo-selfhost.md) for the full schema of
each file.

## Bring your own proxy provider

`proxies.example.json` is **format-only** — it shows the JSON shape with a
placeholder host and placeholder credentials. Self-host uses your own compute and
your own network, so you supply your own proxy provider: sign up with a
residential proxy provider of your choice, then replace the placeholder `url` and
`auth` with the endpoint and credentials they give you.

The `claim_os` on each proxy entry must match the `claim_os` of the identity you
run through it.

## Identity and behavior work out of the box

`identity.example.json` and `behavior.example.json` are minimal but complete: copy
them as-is and they validate. Every value in them is a synthetic placeholder —
edit them to describe the identity and interaction you actually want.

## Engines

An identity's `claim_browser` selects the engine: `chrome`, `firefox`, or
`webkit`. Self-host runs all three locally.
