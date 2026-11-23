# GhostCrawl — public-surface audit remediation record

**Date:** 2026-11-23
**Product version:** 2.3.9 (canonical). No 2.4.0 release was created.
**Scope:** independent review of a third-party public-surface audit (55 findings: legal/licensing, API contract, SDK registries, self-host, billing, trust, UX, Ghostopia) followed by a second source-level and security deep dive.

This document is written so an independent reviewer can reproduce the claims from public sources. It records what was fixed, what was deliberately accepted, and what remains open. Nothing here is a certification of the full audit document's own "Definition of Done" (authenticated dashboard walkthroughs, every-route live execution, full private-repository security review) — those are separate workstreams.

## 1. Version and registry contract

| Surface | Canonical identifier | Note |
|---|---|---|
| Product / cloud / self-host image | **2.3.9** | Unchanged. No product minor bump. |
| PyPI `ghostcrawl` | **2.3.91** | 2.3.9-band package patch identifier; corrected README (Python 3.11+). |
| npm `@ghostcrawl/sdk` | **2.3.91** | Corrected Node 22+ and canonical MCP URL. |
| npm `@ghostcrawl/cli` | **2.3.91** | Corrected Node 22+. |
| RubyGems `ghostcrawl` | **2.3.91** | Carries the generated-client compatibility fix. |
| NuGet `GhostCrawlApi` | **2.3.91** | Corrected README (.NET 10 / net10.0). |
| PyPI `ghostcrawl-langchain`, Go `/v2`, PHP, Java | **2.3.9** | No stale published text; no patch identifier needed. |

Publishing platforms do not permit overwriting a published version; the `2.3.91` identifiers are package-level patches within the 2.3.9 band, published with build-time version overrides so all source version files remain at 2.3.9.

## 2. What the review found and what changed

### Already resolved before this pass (no change needed)
- Terms/EULA licensing split: the client toolkit (SDKs, CLI, examples) is MIT; cloud and the self-host engine image are proprietary. Public pages and the repository README agree.
- Governing law: California (the operating entity's place of formation). Legal summary pages agree.
- Recording of a legal sign-off gate: none exists by explicit maintainer decision; the sign-off checklist is advisory.
- Sub-processor names: intentionally category-only in public docs, with a named appendix held under NDA.
- OpenAPI `{}` tabs on showcase pages: intentional, key-gated documentation display.
- Benchmark percentages: retired because they were not reproducible.

### Legal / trust / billing documentation
- Trust page authentication language was qualified to match the acceptable-use rule: unauthorized access is out of scope; a customer's own authorized authenticated sessions are supported.
- Trust and refund page display dates were reconciled with the current legal cut while keeping legal effective dates distinct.
- Billing documentation now distinguishes API usage dimensions from the credits/cost endpoint (`/v1/me/usage`).
- The pricing source-of-truth docstring was rewritten to describe the live list-plus-promotion model; no price changed.
- Security page now states that both Bearer and `X-Api-Key` are accepted, with precedence documented.
- At-rest wording is limited to the control actually implemented: backups encrypted with AES-256. Broader at-rest claims are not made.
- The SLA states there are no service credits and that remedy is support priority; no credit schedule was invented.

### API contract
- Newsletter confirm/unsubscribe `GET` and `POST` operations now have unique operation identifiers in every published spec; generated clients no longer collide.
- `POST /v1/agent` has a complete published contract: operation identifier, success response, Bearer security declaration, and idempotency header.
- Anonymous routes (sign-in, refresh, password reset, email verification, OAuth flows, newsletter, waitlist, contact, public pricing, entitlement and status checks) are now declared as unauthenticated in the spec. Protected account routes remain Bearer-only.
- Search provider headers (`X-Provider-Authorization`, `X-Ghostcrawl-Search-Engine`) are declared on `/v1/search`.
- Homepage capability tiles point to real routes; two former labels pointed to unregistered paths.
- The recordings guide uses methods that actually exist in the published SDKs and distinguishes session-recording concepts.
- A transport guide explains CDP-over-WebSocket passthrough versus WebRTC live viewing.
- Error semantics: method-not-allowed responses use a proper problem type; a shadowed `GET` on the session-create path returns 405 instead of 404; the billing invoice `limit` query parameter is validated; capability docstrings match the response shape.
- Route-to-runtime parity check: every in-schema registered operation appears in the published specification; the only specification-only operation is the intentionally hand-documented agent route.

### SDKs, registries, and public repositories
- Python, Node, Go, PHP runtime floors in public documentation now match their package manifests; a gate fails on future drift.
- Broken billing links in published error docstrings now point to the canonical pricing anchor.
- Public contribution instructions use the paths that exist in the public repository.
- Go and PHP repository descriptions now say MIT (client toolkit).
- Ruby, C#, and Java source metadata points to the canonical public repository.
- Nine published packages were installed into clean temporary environments: six fully smoke-tested green; two were blocked only by absent local toolchains (Ruby 3.4, .NET 10); one Go module requires the correctly capitalized module path used in the documentation.

### Self-host
- Launcher documentation verifies the checksum before executing the downloaded script, with a fail-closed command and a PowerShell read-and-compare equivalent.
- The launcher now forwards the bind setting into the container, so the runtime's refusal to serve with default dashboard credentials on a non-loopback bind actually fires. Detection now catches either shipped default, not only both.
- Windows instructions state that the POSIX launcher runs under Git Bash/WSL; Windows Docker commands use native syntax.
- The public pricing card reflects the shipped free-tier limits (one interactive session per engine, one persisted identity, minimal built-in behavior, host egress, user-supplied identities/proxies/behaviors).

### Source-level security follow-up
- Async-job callback URLs are validated with the same URL policy used for target fetches (HTTP/HTTPS only, no private or metadata addresses) at creation and again at delivery; delivery no longer follows redirects.
- Abuse-suspension enforcement referenced a field that does not exist on the tenant context; it now uses the team identifier, restoring the intended 403 instead of a server error.
- Download filenames from target sites are reduced to a safe basename with control characters and quotes removed, with an RFC 5987 fallback, preventing response-header injection.
- Webhook HMAC verification uses constant-time comparison and timestamp tolerance; tenant-scoped resources were checked for cross-tenant access; logging and error telemetry have committed redaction coverage and fail closed on scrubbing errors.

## 3. Verification

The following checks were executed after the final changes and all returned exit code 0:

```
python3 scripts/check_public_sdk_manifest.py
bash ghostcrawl/scripts/check_openapi_hash_equality.sh
bash ghostcrawl/scripts/check_version_stamp.sh
python3 ghostcrawl/scripts/check_seal_id_consistency.py
bash ghostcrawl/scripts/check_prepush_public.sh
python3 ghostcrawl/scripts/check_pricing_numbers.py
python3 ghostcrawl/scripts/check_pricing_ssot_drift.py
python3 ghostcrawl/scripts/scan_doc_drift.py --quiet
```

Focused regression tests were added for each code fix (contract uniqueness, anonymous-route declarations, callback validation, abuse suspension, filename sanitization, error semantics, runtime-floor gates, and the stale CLI assertion). Test runs are green under the project's pinned Python environment.

One pre-existing documentation test failure is known and unchanged: an assertion forbidding PowerShell fenced blocks conflicts with the current, deliberately documented inline PowerShell equivalents. It predates this remediation and is recorded, not silently altered.

## 4. Open, deferred, or accepted items

These are stated plainly so an independent reviewer does not mistake them for oversights:

1. **TOTP replay across separate challenges** — a time-based code can be reused within its validity window across different challenges. Requires a persisted last-used step with an atomic comparison and a schema change; deferred rather than shipped without review.
2. **Prelaunch test identities** — four non-operator test keys have unverified email addresses, so account self-service endpoints return `401 email_not_verified` for them. No administrative verification endpoint exists; this needs a provisioning change, not a code change.
3. **Rust extension dependency (`pyo3`)** — a newer patch exists for an advisory, but changing it requires a Rust rebuild and artifact reship. Left unchanged to avoid source/binary drift.
4. **Developer-only npm dependency advisories** — present in lockfiles for test/build tooling, not shipped runtime code. Resolution needs fresh advisory data and per-package regeneration.
5. **Two transitive web-portal dependencies** — patched-version selection and a major-version transition need a network-approved resolution and browser build check.
6. **Container hardening** — base-image digest pinning, non-root users in several development images, and Kubernetes security-context triage require image rebuilds and redeploys; no production change was made.
7. **Authenticated dashboard and full customer-journey review** — not part of this pass; requires human interaction and a dedicated test account.
8. **Old UAT register** — a separate cross-phase list of human-verification items remains; it is tracked independently of public-surface remediation.

## 5. How to re-audit

From a clean clone of the public repository:

1. Read this file together with the public README, licensing notes, SDK READMEs, self-host guide, legal pages, and API reference.
2. Check the live registry identifiers listed in section 1 and install at least one SDK from a clean environment.
3. Re-run the route/auth/operation-identifier checks against the published OpenAPI document and compare with unauthenticated live probes for the public routes.
4. Verify the self-host checksum ordering and bind/credential behavior against the published launcher and self-host guide.
5. Treat section 4 as the authoritative open-risk list: items there are intentionally unresolved, not hidden.

No credentials, customer data, or production infrastructure are required for this review.

## 6. Independent re-audit response (2026-11-23)

An independent reviewer claimed 10 public discrepancies. Each was re-checked against live HTTP, live registries, and the GitHub API. Six were caused by source fixes that had not been **deployed**; four were already false on the live surfaces.

Both hosted Pages projects were rebuilt and deployed in this session: the documentation portal (`ghostcrawl-docs`, 87 routes) and the marketing/blog site (`ghostcrawl-marketing` + `ghostcrawl-blog`, edge cache purged).

| Claim | Live result after deploy |
|---|---|
| Terms/EULA proprietary vs MIT | Live legal pages agree: MIT toolkit, proprietary cloud/self-host image; no Delaware governing law. Refuted. |
| Trust page prohibits authenticated sessions | Live page now qualifies the restriction to content the customer is **not authorized** to access; authorized customer sessions supported. Fixed by deploy. |
| Trust date Oct 20 | Live page now says 19 November 2026. Fixed by deploy. |
| npm README Bearer-only | Published `@ghostcrawl/sdk@2.3.91` README documents X-Api-Key; no "only auth scheme" claim. Refuted. |
| NuGet 2.3.8 / net8 | NuGet index contains 2.3.91; cache-busted package download HTTP 200, registration `listed:true`. Refuted. |
| PHP README 8.1 / About proprietary | Public docs/install says Python 3.11+, examples/node says Node 22+; GitHub About says MIT (client toolkit); Packagist requires PHP >=8.3. Refuted. |
| Security page Bearer-only | Live page now says Bearer and X-Api-Key are both supported. Fixed by deploy. |
| SLA lacks no-credits remedy | Live page now states no service credits and support-priority remedy. Fixed by deploy. |
| Self-host checksum after execution | Live page now orders download → checksum verification (fail-closed) → chmod → execute. Fixed by deploy. |
| Homepage free limits absent | Live `plans.json` free card now lists one interactive session per engine, one persisted identity, minimal built-in behavior. Fixed by deploy. |

**Claim-list reconstruction (10 vs 9 vs 11).** The private claim list has 11 entries; this public table has 10 because the "Governing law Delaware vs California" claim was folded into the Terms/EULA row above (all live legal pages say California). Conversely, the single merged Trust row was split back into its two independently re-checked claims, using the private list's exact phrasings — "Trust page prohibits authenticated sessions" and "Trust date Oct 20", both **Fixed by deploy**. The result is 10 rows: **6 fixed / 4 refuted**, matching the prose at the start of this section.

Section 4 remains the authoritative open-risk list. No production runtime, browser fleet, or billing system was changed; only documentation sites were deployed.
