/* =============================================================================
 * docs.js — GhostCrawl documentation: nav + interactive sandboxed API explorer.
 *
 * The explorer is "bring your own key": the visitor pastes their OWN gck_live_
 * key, edits a request, and hits Run. Security posture for the key:
 *   • Stored ONLY in this tab's sessionStorage — cleared automatically when the
 *     tab/window closes (not persisted across sessions like localStorage), which
 *     shrinks the window in which a page-script could read it.
 *   • Sent ONLY to https://api.ghostcrawl.io over TLS, as the visitor's own
 *     bearer — scoped to their own quota. It is never transmitted anywhere else
 *     and never embedded in shareable example code.
 * This is a deliberate static BYO-key design (no server tier / BFF): the only
 * key in play is the visitor's own, so the residual is exposure of one's own
 * key to one's own browser — no cross-tenant or server-secret surface.
 *   • LIVE  — with a key, the call goes straight to https://api.ghostcrawl.io and
 *             shows the real response (works from docs.ghostcrawl.io once that
 *             origin is allowlisted).
 *   • SANDBOX — without a key (or if a live call can't be made from this origin),
 *             a representative cached example response is shown, clearly badged,
 *             so the docs are always explorable.
 * ============================================================================= */
(() => {
"use strict";

const API_BASE = "https://api.ghostcrawl.io";
const KEY_STORE = "gc_docs_api_key";
const ASSET = "./data/playground/";

/* Key lives in sessionStorage (per-tab, cleared on close) — NOT localStorage —
 * so it does not persist across browser sessions. See header for the BYO-key
 * security posture. */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ---------- API key (per-tab session only) ----------------------------- */
function getKey() { try { return sessionStorage.getItem(KEY_STORE) || ""; } catch { return ""; } }
function setKey(v) { try { v ? sessionStorage.setItem(KEY_STORE, v) : sessionStorage.removeItem(KEY_STORE); } catch {} }

function initKeyBar() {
  const input = $("[data-key-input]");
  const status = $("[data-key-status]");
  if (!input) return;
  input.value = getKey();
  const refresh = () => {
    const has = !!getKey();
    if (status) {
      status.textContent = has ? "● live — your key stays in this tab, sent only to the API" : "○ sandbox — add your key to run live";
      status.className = "gc-docs-keybar__status" + (has ? " is-live" : "");
    }
  };
  input.addEventListener("input", () => { setKey(input.value.trim()); refresh(); });
  refresh();
}

/* ---------- sandbox sample responses (cached, real captured data) ------- */
let _sites = null;
async function loadSite(id) {
  if (!_sites) {
    try { _sites = {}; } catch {}
  }
  if (_sites[id]) return _sites[id];
  const r = await fetch(`${ASSET}sites/${id}.json`, { cache: "no-cache" });
  _sites[id] = await r.json();
  return _sites[id];
}

/* Build a representative sample response for a lane from the cached fixtures. */
async function sampleResponse(lane, url) {
  // Pick the closest cached site for the URL, else fall back to example.
  let id = "example";
  try {
    const host = new URL(/^https?:/.test(url) ? url : "https://" + url).host;
    const map = { "ghostcrawl.io": "ghostcrawl", "example.com": "example",
      "books.toscrape.com": "books", "quotes.toscrape.com": "quotes",
      "news.ycombinator.com": "hackernews", "en.wikipedia.org": "wikipedia" };
    id = map[host] || "example";
  } catch {}
  const fx = await loadSite(id);
  const d = (fx.lanes || {})[lane] || {};
  switch (lane) {
    case "scrape":
    case "content":
      return { status: "completed", url: fx.url,
        results: [{ ok: true, title: d.title, engine: d.engine, markdown: (d.markdown || "").slice(0, 600) }] };
    case "search":
      return { query: d.query, hits: d.hits };
    case "extract":
      return { url: fx.url, data: d.data };
    case "crawl":
      return { status: "completed", pages: d.pages, urls: d.urls };
    case "map":
      return { success: true, count: d.count, paths: d.paths };
    case "screenshot":
      return { ok: true, engine: d.engine, format: "jpeg", image: `<${(d.img || "").split("/").pop()} · base64 omitted in sandbox>` };
    case "pdf":
      return { ok: true, paper: d.paper, file: "<application/pdf · base64 omitted in sandbox>" };
    default:
      return d.receipt ? { status: "completed", receipt: d.receipt } : { status: "completed" };
  }
}

/* ---------- run an explorer (live or sandbox) -------------------------- */
async function runExplorer(panel) {
  const lane = panel.dataset.explorer;
  const urlInput = $("[data-ex-url]", panel);
  const out = $("[data-ex-out]", panel);
  const badge = $("[data-ex-badge]", panel);
  const btn = $("[data-ex-run]", panel);
  const url = (urlInput ? urlInput.value : "").trim() || "https://example.com";
  const key = getKey();
  if (btn) { btn.disabled = true; btn.classList.add("is-running"); }
  out.textContent = "…  running /v1/" + lane;

  const renderJSON = (obj, mode) => {
    if (badge) {
      badge.textContent = mode === "live" ? "live" : "sandbox";
      badge.className = "gc-docs-ex__badge" + (mode === "live" ? " is-live" : "");
      badge.hidden = false;
    }
    out.innerHTML = `<pre>${esc(JSON.stringify(obj, null, 2))}</pre>`;
  };

  try {
    if (key) {
      // LIVE: call the real API with the visitor's key.
      const body = lane === "search" ? { query: url } : { url: /^https?:/.test(url) ? url : "https://" + url };
      const res = await fetch(`${API_BASE}/v1/${lane}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${key}`, "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const txt = await res.text();
      let data; try { data = JSON.parse(txt); } catch { data = txt; }
      renderJSON(data, "live");
      return;
    }
    // SANDBOX: no key → representative cached example.
    renderJSON(await sampleResponse(lane, url), "sandbox");
  } catch (e) {
    // Live call blocked (e.g. CORS from this origin) → graceful sandbox sample.
    try {
      renderJSON(await sampleResponse(lane, url), "sandbox");
    } catch {
      out.innerHTML = `<pre>${esc("could not reach the API from this origin — add your key on the deployed docs to run live")}</pre>`;
    }
  } finally {
    if (btn) { btn.disabled = false; btn.classList.remove("is-running"); }
  }
}

/* ---------- code-snippet language tabs --------------------------------- */
function initCodeTabs() {
  $$("[data-code-tabs]").forEach((group) => {
    // Panes live as siblings inside the .gc-docs-code block, not inside the tab
    // strip — scope the pane lookup to the whole code block.
    const scope = group.closest(".gc-docs-code") || group.parentElement;
    const tabs = $$("[data-lang]", group);
    const setLang = (lang) => {
      tabs.forEach((t) => t.classList.toggle("is-active", t.dataset.lang === lang));
      $$("[data-code-for]", scope).forEach((b) => { b.hidden = b.dataset.codeFor !== lang; });
    };
    tabs.forEach((t) => t.addEventListener("click", () => setLang(t.dataset.lang)));
    if (tabs[0]) setLang(tabs[0].dataset.lang);
  });
}

/* ---------- copy buttons ----------------------------------------------- */
function initCopy() {
  $$("[data-copy]").forEach((btn) => btn.addEventListener("click", async () => {
    const tgt = btn.closest("[data-copy-scope]")?.querySelector("[data-copy-src]:not([hidden])")
      || btn.closest(".gc-docs-code")?.querySelector("code");
    if (!tgt) return;
    try { await navigator.clipboard.writeText(tgt.textContent); const o = btn.textContent; btn.textContent = "Copied ✓"; setTimeout(() => (btn.textContent = o), 1300); } catch {}
  }));
}

/* ---------- sidebar nav: active-section highlight + mobile toggle ------- */
function initNav() {
  const links = $$("[data-nav-link]");
  const map = new Map(links.map((l) => [l.getAttribute("href").slice(1), l]));
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        links.forEach((l) => l.classList.remove("is-active"));
        const l = map.get(e.target.id);
        if (l) l.classList.add("is-active");
      }
    });
  }, { rootMargin: "-10% 0px -80% 0px" });
  $$("section[id], h2[id]").forEach((s) => io.observe(s));
  const burger = $("[data-docs-burger]");
  if (burger) burger.addEventListener("click", () => document.body.classList.toggle("gc-docs-nav-open"));
  links.forEach((l) => l.addEventListener("click", () => document.body.classList.remove("gc-docs-nav-open")));
}

function init() {
  initKeyBar();
  initCodeTabs();
  initCopy();
  initNav();
  $$("[data-explorer]").forEach((panel) => {
    const btn = $("[data-ex-run]", panel);
    if (btn) btn.addEventListener("click", () => runExplorer(panel));
  });
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
else init();

})();
