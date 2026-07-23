# Publish manifest — `github.com/ghostcrawl/ghostcrawl`

> **STATUS: STAGED FOR REVIEW. NOTHING HAS BEEN PUSHED.**
>
> This directory holds the canonical, leak-clean content for the public landing
> repo at `github.com/ghostcrawl/ghostcrawl`. It was prepared and committed to the
> **private monorepo only**. No `git push`, no `gh repo create`, no change to the
> public repo has been made. The operator reviews this manifest, then runs the
> push commands below when ready.

---

## What would go public

Every file under `ghostcrawl/ghostcrawl-public/` **except this manifest**
(`PUBLISH-MANIFEST.md` is an internal staging note and must NOT be pushed).

```
README.md                         # Landing README (value props, quickstart, pricing, SDKs)
LICENSE                           # MIT License (client surface) © GhostCrawl, LLC
CONTRIBUTING.md                   # Contribution scope + DCO sign-off
.gitignore                        # Python/Node/env ignores
docker-compose.yml.template       # Self-host pull-only compose (rename to docker-compose.yml)
docs/
  install.md                      # SDK + self-host CLI install
  usage-cloud.md                  # Managed API + MCP usage
  usage-selfhost.md               # Local image usage
examples/
  README.md                       # Examples index
  curl/      scrape.sh crawl.sh extract.sh search.sh
  python/    README.md scrape.py crawl.py extract.py async_scrape.py
  node/      README.md scrape.mjs crawl.mjs extract.mjs
  cli/       README.md commands.sh
  langchain/ README.md tool.py agent.py
  mcp/       README.md config.json client.py
.github/
  SECURITY.md                     # Private vuln disclosure policy
  ISSUE_TEMPLATE/
    bug_report.yml
    feature_request.yml
    config.yml
```

### Excluded from the public push (DO NOT PUSH)

- `PUBLISH-MANIFEST.md` — this internal staging note.
- Any `__pycache__/`, `.env`, `node_modules/`, or local `docker-compose.yml`
  (covered by `.gitignore`).

---

## Proposed repo settings (for discoverability / stars)

**Description:**

> Authentic, reliable web data at scale — real Chrome, Firefox & WebKit browsers
> in the cloud. Crawl, scrape, extract & automate via API, SDKs, and MCP.
> Self-host free or use the managed cloud.

**Topics / tags:**

```
web-scraping  web-crawler  browser-automation  scraping-api  crawler
data-extraction  mcp  model-context-protocol  ai-agents  llm
headless-browser  chrome  firefox  webkit  serp  python  typescript  api
```

**Homepage:** `https://ghostcrawl.io`

**Settings:** public · Issues on · Discussions on · Wiki off · Projects off ·
Releases on · Sponsorships optional.

---

## Leak / quality gates (all PASS at staging time)

- **MANDATORY pre-push gate (run this first):**
  `bash ghostcrawl/scripts/check_prepush_public.sh` → **PASS** (exit 0). It scans
  the landing-repo push set (`ghostcrawl-public/` minus this manifest) for: wording/
  plumbing vocab, engine/proprietary source, secrets/private keys, license keys,
  internal hostnames, and the `/v1/binary` moat surface — and confirms
  PUBLISH-MANIFEST.md is excluded from the push set. Fail-closed.
  - **Advisory (non-blocking) — fix before republishing the SDK/MCP *packages*
    (not the landing repo):** the stale vendored OpenAPI specs
    `sdks/{go,csharp,java}/spec/openapi.json` + `ghostcrawl-mcp-server/openapi/v1.json`
    still list `/v1/binary/download` (removed from the live API in 171-04 —
    regenerate via the kiota SDK pipeline); and
    `ghostcrawl-mcp-server/docs/demo/opencode-session.md` carries dev paths +
    monorepo breadcrumbs (scrub or drop from the MCP package before publish).
- `bash ghostcrawl/scripts/check_wording_hygiene.sh` → **PASS** (0 forbidden
  tokens; `ghostcrawl/ghostcrawl-public` is now a scanned root).
- Manual forbidden-token grep (engine codenames, infra/provider names, method
  language) → **0 hits**.
- No muted-integration reference anywhere in the published content → **confirmed
  absent** (the publishable files carry zero forbidden tokens).
- All examples syntax-check clean (Python `py_compile`, `node --check`,
  `bash -n`, JSON parse).
- SDK names + install commands match the published packages: `ghostcrawl`
  (PyPI), `@ghostcrawl/sdk` / `@ghostcrawl/cli` (npm, v2.3.0),
  `ghostcrawl-langchain` (PyPI). API base `https://api.ghostcrawl.io`,
  MCP `https://mcp.ghostcrawl.io`, Bearer auth with `gck_live_…` keys.

---

## Operator push procedure (run only after review)

These commands are for the operator to run **manually** after reviewing the
staged content. They push the staged directory (minus this manifest) to the
public repo.

### Pre-flight (operator)

```bash
# 1. Publish the self-host image under the new org BEFORE the compose template
#    becomes public (the template references ghcr.io/ghostcrawl/ghostcrawl:latest):
#       docker tag <built-image> ghcr.io/ghostcrawl/ghostcrawl:latest
#       docker push ghcr.io/ghostcrawl/ghostcrawl:latest
#
# 2. Confirm the SDK packages are live on PyPI / npm so the README badges + install
#    commands resolve (ghostcrawl, @ghostcrawl/sdk, @ghostcrawl/cli, ghostcrawl-langchain).
```

### Push (operator)

```bash
# From the monorepo root. CLONE the LIVE repo, rsync the staged tree OVER it,
# and push a NORMAL fast-forward commit. Do NOT `git init` + `--force` — the
# live repo carries assets + history NOT present in the monorepo (e.g.
# images/banner.png, prior operator commits) that a force-push would DESTROY.
#
# Before every push: diff the staged tree against the LIVE repo and inspect
# what would be deleted/overwritten (the pre-push leak gate does NOT catch a
# missing banner or a re-published pricing table — see 171-12-SUMMARY.md).

SRC="$(pwd)/ghostcrawl/ghostcrawl-public"
WORK="$(mktemp -d)/ghostcrawl"
git clone git@github.com:ghostcrawl/ghostcrawl.git "$WORK"

# rsync the staged tree over the live checkout, EXCLUDING the internal manifest.
# --delete removes files the monorepo intentionally drops, but ALWAYS review the
# rsync --dry-run first so a live-only asset (banner.png) is never silently deleted.
rsync -a --delete --exclude='.git' --exclude='PUBLISH-MANIFEST.md' "$SRC/" "$WORK/"

cd "$WORK"
# NOTE: do NOT rename docker-compose.yml.template → docker-compose.yml — the
# repo .gitignore lists `docker-compose.yml`, so `git add -A` would silently drop
# it, leaving the repo with NEITHER file. Keep the `.template` suffix.
git add -A
git commit -m "GhostCrawl: public landing, SDK quickstarts, examples, docs"
git push origin main                   # normal fast-forward; history + assets preserved

# Set description, homepage, and topics:
gh repo edit ghostcrawl/ghostcrawl \
  --description "Authentic, reliable web data at scale — real Chrome, Firefox & WebKit browsers in the cloud. Crawl, scrape, extract & automate via API, SDKs, and MCP. Self-host free or use the managed cloud." \
  --homepage "https://ghostcrawl.io" \
  --enable-issues --enable-discussions --enable-wiki=false \
  --add-topic web-scraping --add-topic web-crawler --add-topic browser-automation \
  --add-topic scraping-api --add-topic crawler --add-topic data-extraction \
  --add-topic mcp --add-topic model-context-protocol --add-topic ai-agents \
  --add-topic llm --add-topic headless-browser --add-topic serp \
  --add-topic python --add-topic typescript --add-topic api
```

> The live repo is populated (as of 2026-07-09 it carries a README banner asset
> and operator history). Never `--force`: clone → rsync → fast-forward so
> `images/banner.png` and prior commits survive.

---

## Confirmation

- **Nothing in this task ran `git push`, `gh repo create`, or touched
  `github.com/ghostcrawl/ghostcrawl`.**
- The staged content + this manifest were committed to the **private monorepo
  only**.
- The operator owns the decision to push and runs the commands above after review.
