#!/usr/bin/env bash
# Build the OPERATOR-INTERNAL ghostcrawl wheel that ghostopia vendors (plug-and-play).
#
# It is the customer SDK PLUS the powerhouse human-realism layer (ghostcrawl.human), which the
# ghostopia harness consumes for human-realistic in-site input. Realism is operator-internal: it is
# NOT committed into the SDK source tree and NOT shipped on public PyPI — it is INJECTED here at
# build time from its ONE source of truth (repo-root ghostcrawl/human/), so there is no fork.
#
# Usage:  bash sdks/python/build_internal_wheel.sh
# Output: ghostopia/packages/.../vendor is refreshed via the copy at the end (prints the path).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"          # sdks/python
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
PY="$REPO_ROOT/.venv-ghostcrawl/bin/python"
SRC_HUMAN="$REPO_ROOT/ghostcrawl/human"                        # the ONE source of truth
DST_HUMAN="$HERE/ghostcrawl/human"                             # build-time-only injection point
PYPROJECT="$HERE/pyproject.toml"
# Vendor the operator-internal wheel (SDK + ghostcrawl.human) into BOTH harnesses that install it as
# a wheel: ghostopia (plug-and-play) AND the analogsoul-daemon image (analogsoul/deploy/Dockerfile
# pip-installs analogsoul/vendor/*.whl → the daemon needs ghostcrawl.human at runtime for the souls).
# VER is derived from the single source of truth so the wheel FILENAME always matches its METADATA
# Version (a 2.3.7-content wheel named 2.3.6 makes pip/uv fail with a METADATA-mismatch error).
VER="$(grep -E '^__version__[[:space:]]*=' "$REPO_ROOT/ghostcrawl/__init__.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')"
[ -n "$VER" ] || { echo "FATAL: could not derive __version__ from ghostcrawl/__init__.py"; exit 1; }
VENDORS=(
  "$REPO_ROOT/ghostopia/vendor/ghostcrawl-${VER}-py3-none-any.whl"
  "$REPO_ROOT/analogsoul/vendor/ghostcrawl-${VER}-py3-none-any.whl"
)
VENDOR="${VENDORS[0]}"  # primary (kept for the verification/echo below)

[ -d "$SRC_HUMAN" ] || { echo "FATAL: $SRC_HUMAN missing (the human-realism source)"; exit 1; }

cleanup() {
  rm -rf "$DST_HUMAN"
  [ -f "$PYPROJECT.bak_internal" ] && mv -f "$PYPROJECT.bak_internal" "$PYPROJECT"
  rm -rf "$HERE/dist_internal"
}
trap cleanup EXIT

# 1) Inject human/ from the single source (build-time only; never committed to the SDK tree).
rm -rf "$DST_HUMAN"
cp -r "$SRC_HUMAN" "$DST_HUMAN"
find "$DST_HUMAN" -name __pycache__ -type d -prune -exec rm -rf {} +

# 2) Add numpy to the wheel metadata for this build only (human/trajectory needs it), then restore.
cp "$PYPROJECT" "$PYPROJECT.bak_internal"
"$PY" - "$PYPROJECT" <<'PYEOF'
import re, sys
p = sys.argv[1]; s = open(p).read()
if '"numpy' not in s:
    s = s.replace('dependencies = [\n', 'dependencies = [\n  "numpy>=1.26",  # ghostcrawl.human.trajectory (operator-internal build only)\n', 1)
    open(p, "w").write(s)
    print("injected numpy dep for the internal build")
PYEOF

# 3) Build the wheel (no isolation → use the repo venv's setuptools; no network).
rm -rf "$HERE/dist_internal"
"$PY" -m build --wheel --no-isolation --outdir "$HERE/dist_internal" "$HERE"

WHEEL="$(ls -t "$HERE"/dist_internal/ghostcrawl-*-py3-none-any.whl | head -1)"
[ -n "$WHEEL" ] || { echo "FATAL: no wheel produced"; exit 1; }

# 4) Verify human/ + numpy landed in the wheel; then vendor it into ghostopia.
echo "=== human/ modules in the built wheel ==="
"$PY" - "$WHEEL" <<'PYEOF'
import sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
hum = sorted(n for n in z.namelist() if n.startswith("ghostcrawl/human/") and n.endswith(".py"))
assert hum, "human/ NOT in the wheel"
print("\n".join(hum))
meta = [l for n in z.namelist() if n.endswith("METADATA") for l in z.read(n).decode().splitlines() if l.lower().startswith("requires-dist: numpy")]
print("numpy metadata:", meta or "MISSING")
PYEOF

for v in "${VENDORS[@]}"; do
  mkdir -p "$(dirname "$v")"
  rm -f "$(dirname "$v")"/ghostcrawl-*-py3-none-any.whl   # drop superseded-version wheels
  cp -f "$WHEEL" "$v"
  echo "=== vendored → $v ==="
  sha256sum "$v"
done
echo "NOTE: ghostopia — run 'uv lock --upgrade-package ghostcrawl && uv sync' to pin the new build."
echo "NOTE: analogsoul-daemon — rebuild the image (analogsoul/deploy/Dockerfile) to bake the new wheel."
