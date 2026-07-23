# Contributing to GhostCrawl

Thank you for your interest in contributing. This document explains what we accept,
how the PR process works, and the sign-off requirement.

---

## What we accept

Pull requests are accepted **only against the public-safe surface**:

| Surface | Path |
|---------|------|
| Python SDK | `sdks/python/` |
| Node SDK | `sdks/node/` |
| Node CLI SDK | `sdks/node-cli/` |
| Python LangChain SDK | `sdks/python-langchain/` |
| CLI (`ghostcrawl install` 8-verb flow) | `cli/` |
| Documentation | `docs/` |

**Backend, engine, proxy, and identity changes are operator-only** and are developed
privately. PRs that touch anything outside the table above will be closed without merge.
This is not a judgment on the quality of the contribution — it is a hard scope boundary.

If you have an idea for a backend or engine change, open a
[Feature request](https://github.com/ghostcrawl/ghostcrawl/issues/new?template=feature_request.yml)
instead. The operator evaluates those privately.

---

## PR process

1. **Open an issue first** (bug report or feature request) so we can align on the approach
   before you invest time coding.
2. **Fork the repo** and branch from `main`:
   ```
   git checkout -b fix/short-description
   ```
3. **Write your change.** Keep it focused — one issue per PR.
4. **Title your PR using Conventional Commits style:**
   ```
   fix(sdk-python): handle empty response in scrape()
   feat(cli): add --timeout flag to ghostcrawl start
   docs: clarify rate-limit headers in usage-cloud.md
   ```
5. **Link the related issue** in the PR body with `Closes #NNN` or `Relates to #NNN`.
6. **Sign off** (see below) and push to your fork. Open a PR against `main`.

---

## Code style

### Python SDKs (`sdks/python/`, `sdks/python-langchain/`)

- Formatter: `black` (project default, no config changes needed).
- Type checking: `mypy --strict` must pass on changed files.
- Tests: `pytest` — add or update tests for any behavioral change.

```bash
cd sdks/python
pip install -e ".[dev]"
mypy ghostcrawl/
pytest
```

### TypeScript SDKs (`sdks/node/`, `sdks/node-cli/`)

- Linting: `eslint` (project config).
- Type checking: `tsc --noEmit` must pass.
- Tests: `npm test`.

```bash
cd sdks/node
npm install
npm run lint
npm run typecheck
npm test
```

### Docs (`docs/`)

Plain Markdown. Run a link check if you add external URLs:
```bash
npx markdown-link-check docs/YOUR_FILE.md
```

---

## Sign-off (DCO)

This project uses the **Developer Certificate of Origin (DCO)** — not a CLA. Add a sign-off
line to every commit you contribute:

```
git commit -s -m "fix(sdk-python): handle empty response"
```

This appends:

```
Signed-off-by: Your Name <you@example.com>
```

By signing off you certify that you wrote the code (or have the right to submit it) and grant
GhostCrawl, LLC the rights to use it under the [GhostCrawl Software License](LICENSE) terms.
Full DCO text at <https://developercertificate.org>.

---

## License

By contributing you agree that your contribution is licensed to GhostCrawl, LLC under the
[GhostCrawl Software License](LICENSE) (proprietary).
