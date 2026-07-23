/**
 * CLI auth helper: resolves the GhostCrawl API key and builds a
 * GhostCrawlClient. Never reads the key from CLI args.
 *
 * Key resolution order (first non-empty wins):
 *   1. GHOSTCRAWL_API_KEY environment variable
 *   2. $XDG_CONFIG_HOME/ghostcrawl/config.toml  (written by `init` / `config set-key`)
 *
 * Base URL: GHOSTCRAWL_BASE_URL env var, else the public SaaS endpoint.
 */
import { createGhostCrawlClient, GhostCrawlClient, RESULT_CODES, isRetryable } from "@ghostcrawl/sdk";
import { readFileSync } from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

/**
 * Process exit codes by error class. Extends the original convention
 * (0 = ok, 1 = generic, 2 = invalid request) with distinct codes per class so
 * scripts can branch on `$?`:
 *
 *   0  success
 *   1  generic / unknown error
 *   2  invalid request           (400 / 422 — bad params; NOT retryable)
 *   3  authentication failed      (401 — fix the API key)
 *   4  payment required           (402 — upgrade your plan or contact us)
 *   5  retryable server failure   (429 / 5xx — rate-limited, pool exhausted,
 *                                  render timeout, engine crash — safe to retry)
 *   6  target scrape failure      (200 + result_error: blocked / captcha /
 *                                  target HTTP error / navigation failed /
 *                                  empty content — retry meaning depends on code)
 */
export const EXIT = {
  OK: 0,
  GENERIC: 1,
  INVALID_REQUEST: 2,
  AUTH: 3,
  PAYMENT_REQUIRED: 4,
  RETRYABLE: 5,
  TARGET_FAILURE: 6,
} as const;

const DEFAULT_BASE_URL = "https://api.ghostcrawl.io";

function _configPath(): string {
  const xdg = (process.env["XDG_CONFIG_HOME"] ?? "").trim();
  const base = xdg.length > 0 ? xdg : path.join(os.homedir(), ".config");
  return path.join(base, "ghostcrawl", "config.toml");
}

/** Read `api_key = "..."` from config.toml, or null if absent/unreadable. */
function _keyFromConfig(): string | null {
  try {
    const txt = readFileSync(_configPath(), "utf-8");
    for (const raw of txt.split(/\r?\n/)) {
      const line = raw.trim();
      if (!line || line.startsWith("#")) continue;
      if (!line.startsWith("api_key")) continue;
      const idx = line.indexOf("=");
      if (idx < 0) continue;
      let rhs = line.slice(idx + 1).trim();
      if (rhs.startsWith('"') && rhs.endsWith('"')) {
        rhs = rhs.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, "\\");
      }
      return rhs || null;
    }
  } catch {
    return null;
  }
  return null;
}

export function resolveApiKey(): string {
  const fromEnv = (process.env["GHOSTCRAWL_API_KEY"] ?? "").trim();
  if (fromEnv) return fromEnv;
  const fromConfig = (_keyFromConfig() ?? "").trim();
  if (fromConfig) return fromConfig;
  process.stderr.write(
    "Error: GHOSTCRAWL_API_KEY environment variable required " +
      "(or run `ghostcrawl init` to save a key)\n",
  );
  process.exit(1);
}

export function baseUrl(): string {
  return (process.env["GHOSTCRAWL_BASE_URL"] ?? "").trim() || DEFAULT_BASE_URL;
}

export function getClient(): GhostCrawlClient {
  return createGhostCrawlClient({
    token: resolveApiKey(),
    baseUrl: baseUrl(),
  });
}

/**
 * Raw JSON request for endpoints the SDK does not surface as a typed method
 * (e.g. /v1/map, /v1/extract).
 *
 * Delegates to the SDK client's generic `request()` escape hatch so the Bearer
 * header and base URL are applied identically to the typed calls. Returns the
 * parsed JSON body; the escape hatch throws an Error carrying `statusCode` on a
 * non-2xx response so `fail()` can route exit codes (422 → 2).
 */
export async function rawRequest(
  client: GhostCrawlClient,
  method: "GET" | "POST",
  endpoint: string,
  body?: unknown,
): Promise<unknown> {
  return client.request(method, endpoint, body);
}

export function emit(payload: unknown, pretty: boolean): void {
  const out = pretty
    ? JSON.stringify(payload, null, 2)
    : JSON.stringify(payload);
  process.stdout.write(out + "\n");
}

/**
 * Extract an HTTP status code from a thrown error, if present.
 *
 * The SDK throws `GhostCrawl*` error classes that expose a ``statusCode``
 * field. Raw httpx-style errors may attach the status under
 * ``response.status`` instead.
 */
function _extractStatus(err: unknown): number | undefined {
  if (err === null || err === undefined || typeof err !== "object") return undefined;
  const e = err as Record<string, unknown>;
  if (typeof e["statusCode"] === "number") return e["statusCode"] as number;
  const resp = e["response"];
  if (resp && typeof resp === "object") {
    const r = resp as Record<string, unknown>;
    if (typeof r["status"] === "number") return r["status"] as number;
    if (typeof r["statusCode"] === "number") return r["statusCode"] as number;
  }
  return undefined;
}

/**
 * Extract the canonical error `code` from a thrown error. The SDK's typed
 * errors carry it directly; raw errors may carry a problem+json `body.code`.
 */
function _extractCode(err: unknown): string | undefined {
  if (err === null || err === undefined || typeof err !== "object") return undefined;
  const e = err as Record<string, unknown>;
  if (typeof e["code"] === "string") return e["code"] as string;
  const body = e["body"];
  if (body && typeof body === "object") {
    const b = body as Record<string, unknown>;
    if (typeof b["code"] === "string") return b["code"] as string;
  }
  return undefined;
}

/**
 * Map a thrown error to a process exit code by class. Prefers the canonical
 * `code`, falling back to the HTTP status — so the exit code is meaningful even
 * for raw/untyped errors.
 */
function _exitCodeFor(err: unknown): number {
  const code = _extractCode(err);
  const status = _extractStatus(err);
  // The result-channel ScrapeError (status 200 + a TARGET-failure code).
  if (code && RESULT_CODES.has(code)) return EXIT.TARGET_FAILURE;
  if (code === "unauthorized" || status === 401) return EXIT.AUTH;
  if (code === "payment_required" || status === 402) return EXIT.PAYMENT_REQUIRED;
  if (
    code === "bad_request" ||
    code === "byo_proxy_invalid" ||
    code === "tier_unavailable" ||
    status === 400 ||
    status === 422
  ) {
    return EXIT.INVALID_REQUEST;
  }
  if (code === "rate_limited" || status === 429) return EXIT.RETRYABLE;
  if (isRetryable(code) || (typeof status === "number" && status >= 500 && status < 600)) {
    return EXIT.RETRYABLE;
  }
  return EXIT.GENERIC;
}

export function fail(err: unknown): never {
  const msg = err instanceof Error ? `${err.name}: ${err.message}` : String(err);
  process.stderr.write(`Error: ${msg}\n`);
  // Code-aware exit: distinct codes per error class (see EXIT above). Preserves
  // the original 422 → 2 and other → 1 convention as the baseline; adds 3/4/5/6
  // for auth / payment / retryable / target-scrape failures.
  const exitCode = _exitCodeFor(err);
  const code = _extractCode(err);
  if (code) {
    process.stderr.write(`Error code: ${code}${isRetryable(code) ? " (retryable)" : ""}\n`);
  }
  process.exit(exitCode);
}

/**
 * A TARGET-side scrape failure surfaced on an HTTP-200 result body
 * (`ok: false` + `result_error`). Thrown so `fail()` routes it to the
 * `TARGET_FAILURE` exit code rather than emitting a fake-success and exiting 0.
 */
export class CliScrapeError extends Error {
  public readonly code?: string;
  public readonly retryable: boolean;
  public readonly targetStatus?: number;
  public readonly statusCode = 200;
  constructor(opts: { code?: string; retryable: boolean; targetStatus?: number; reason?: string }) {
    let detail = `Scrape failed (${opts.code ?? "unknown"})`;
    if (opts.targetStatus !== undefined) detail += `: target returned HTTP ${opts.targetStatus}`;
    else if (opts.reason) detail += `: ${opts.reason}`;
    super(detail);
    this.name = "CliScrapeError";
    this.code = opts.code;
    this.retryable = opts.retryable;
    this.targetStatus = opts.targetStatus;
  }
}

/**
 * Inspect a decoded result and throw {@link CliScrapeError} when it reports a
 * TARGET failure (`ok: false` / `result_error`). Otherwise returns it
 * unchanged. Mirrors the SDK's `scanResultError`, so the CLI never emits a
 * blocked / timed-out / errored scrape as a success.
 */
export function scanResult<T>(result: T): T {
  if (result === null || typeof result !== "object" || Array.isArray(result)) return result;
  const r = result as Record<string, unknown>;
  const inner = r["results"];
  if (Array.isArray(inner)) {
    for (const item of inner) scanResult(item);
    return result;
  }
  const resultError = r["result_error"];
  const topCode = r["code"];
  const ok = r["ok"];

  let code: string | undefined;
  let retryable = false;
  let targetStatus: number | undefined;
  let reason: string | undefined;

  if (resultError !== null && typeof resultError === "object") {
    const re = resultError as Record<string, unknown>;
    code = (typeof re["code"] === "string" ? (re["code"] as string) : undefined) ?? (typeof topCode === "string" ? topCode : undefined);
    retryable = Boolean(re["retryable"]);
    if (typeof re["target_status"] === "number") targetStatus = re["target_status"] as number;
    if (typeof re["reason"] === "string") reason = re["reason"] as string;
  } else if (ok === false && typeof topCode === "string" && RESULT_CODES.has(topCode)) {
    code = topCode;
    retryable = isRetryable(code);
    if (typeof r["target_status"] === "number") targetStatus = r["target_status"] as number;
  } else if (r["status"] === "failed") {
    code = typeof topCode === "string" ? topCode : undefined;
    if (typeof r["target_status"] === "number") targetStatus = r["target_status"] as number;
  } else {
    return result;
  }

  throw new CliScrapeError({ code, retryable: retryable || isRetryable(code), targetStatus, reason });
}

/**
 * Scan a result for a TARGET failure, then emit it. The common
 * success-or-target-failure path for the scrape/crawl/extract/map commands:
 * a clean result is printed (exit 0 via the caller); a TARGET failure throws
 * so the command's `catch (e) { fail(e); }` exits non-zero.
 */
export function emitResult(result: unknown, pretty: boolean): void {
  emit(scanResult(result), pretty);
}
