/**
 * Canonical GhostCrawl error codes.
 *
 * SDK-side mirror of the server's single source of truth
 * (`ghostcrawl/errors/codes.json`, generated from the server error catalog).
 * The values here are copied verbatim from that catalog so the SDK never
 * invents its own vocabulary — keep them in lockstep when the catalog changes.
 *
 * Two channels:
 *  - `"problem"` — OUR failure. The API returns a non-2xx
 *    `application/problem+json` body. The facade throws a typed error keyed on
 *    the `code` (e.g. `payment_required` → `GhostCrawlQuotaError`).
 *  - `"result"` — TARGET failure. The API returns HTTP 200 with `ok: false` +
 *    `result_error: { code, retryable, target_status? }`. The facade throws
 *    `GhostCrawlScrapeError` so a blocked / timed-out / errored scrape is never
 *    silently a success.
 */

export type ErrorChannel = "problem" | "result";

export interface ErrorCodeMeta {
    code: string;
    http: number;
    retryable: boolean;
    channel: ErrorChannel;
    title: string;
    retryAfter: number | null;
}

// --- Generated from ghostcrawl/errors/codes.json (do not hand-diverge) -------
export const ERROR_CODES: Record<string, ErrorCodeMeta> = {
    bad_request: { code: "bad_request", http: 400, retryable: false, channel: "problem", title: "Malformed request", retryAfter: null },
    unauthorized: { code: "unauthorized", http: 401, retryable: false, channel: "problem", title: "Authentication required", retryAfter: null },
    forbidden: { code: "forbidden", http: 403, retryable: false, channel: "problem", title: "Insufficient permissions", retryAfter: null },
    payment_required: { code: "payment_required", http: 402, retryable: false, channel: "problem", title: "Payment required", retryAfter: null },
    not_found: { code: "not_found", http: 404, retryable: false, channel: "problem", title: "Resource not found", retryAfter: null },
    conflict: { code: "conflict", http: 409, retryable: false, channel: "problem", title: "Resource conflict", retryAfter: null },
    byo_proxy_invalid: { code: "byo_proxy_invalid", http: 422, retryable: false, channel: "problem", title: "BYO proxy URL invalid", retryAfter: null },
    tier_unavailable: { code: "tier_unavailable", http: 400, retryable: false, channel: "problem", title: "Requested proxy tier unavailable", retryAfter: null },
    rate_limited: { code: "rate_limited", http: 429, retryable: true, channel: "problem", title: "Rate limit exceeded", retryAfter: 5 },
    quota_backend_unavailable: { code: "quota_backend_unavailable", http: 503, retryable: true, channel: "problem", title: "Rate-limit service unavailable", retryAfter: 5 },
    pool_exhausted: { code: "pool_exhausted", http: 503, retryable: true, channel: "problem", title: "Proxy pool exhausted", retryAfter: 10 },
    egress_integrity_failed: { code: "egress_integrity_failed", http: 503, retryable: true, channel: "problem", title: "Egress integrity check failed", retryAfter: 5 },
    render_hung: { code: "render_hung", http: 503, retryable: true, channel: "problem", title: "Render did not progress (page wedged)", retryAfter: 5 },
    engine_crashed: { code: "engine_crashed", http: 503, retryable: true, channel: "problem", title: "Rendering engine crashed", retryAfter: 5 },
    render_timeout: { code: "render_timeout", http: 504, retryable: true, channel: "problem", title: "Render exceeded its time budget", retryAfter: 5 },
    engine_timeout: { code: "engine_timeout", http: 504, retryable: true, channel: "problem", title: "Request was not completed in time", retryAfter: 5 },
    service_unavailable: { code: "service_unavailable", http: 503, retryable: true, channel: "problem", title: "Service temporarily unavailable", retryAfter: 5 },
    internal_error: { code: "internal_error", http: 500, retryable: true, channel: "problem", title: "Internal server error", retryAfter: null },
    target_http_error: { code: "target_http_error", http: 200, retryable: false, channel: "result", title: "Target returned an HTTP error", retryAfter: null },
    navigation_failed: { code: "navigation_failed", http: 200, retryable: false, channel: "result", title: "Could not reach the target", retryAfter: null },
    blocked: { code: "blocked", http: 200, retryable: true, channel: "result", title: "Blocked by the target's anti-bot protection", retryAfter: null },
    captcha_required: { code: "captcha_required", http: 200, retryable: true, channel: "result", title: "The target presented a CAPTCHA", retryAfter: null },
    empty_content: { code: "empty_content", http: 200, retryable: false, channel: "result", title: "No extractable content", retryAfter: null },
};

/** Every canonical code string. */
export const ALL_CODES: readonly string[] = Object.keys(ERROR_CODES);

/** Codes whose channel is `"result"` (TARGET failures returned on HTTP 200). */
export const RESULT_CODES: ReadonlySet<string> = new Set(
    ALL_CODES.filter((c) => ERROR_CODES[c]!.channel === "result"),
);

/** Codes whose channel is `"problem"` (OUR failures returned as non-2xx). */
export const PROBLEM_CODES: ReadonlySet<string> = new Set(
    ALL_CODES.filter((c) => ERROR_CODES[c]!.channel === "problem"),
);

/** Fallback HTTP-status → canonical-code map for problem responses with no `code`. */
export const STATUS_TO_CODE: Record<number, string> = {
    400: "bad_request",
    401: "unauthorized",
    402: "payment_required",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "byo_proxy_invalid",
    429: "rate_limited",
    500: "internal_error",
    503: "service_unavailable",
    504: "engine_timeout",
};

/** Return the catalog `retryable` flag for `code` (false if unknown). */
export function isRetryable(code: string | undefined | null): boolean {
    return code != null && code in ERROR_CODES ? ERROR_CODES[code]!.retryable : false;
}
