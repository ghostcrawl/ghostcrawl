// Node SDK domain error set — the ONE canonical error surface.
//
// Forward-best-merged with the Python LangChain SDK's mapping
// (sdks/python-langchain/ghostcrawl_langchain/errors.py) and the Python SDK
// facade so that status-code / canonical-code → domain-class is uniform across
// all official ghostcrawl SDKs.
//
// `GhostCrawlError` (defined below) is the base class; these subclasses preserve
// its constructor surface and add a small set of stable, public class names users
// can catch by type. They also carry the canonical two-channel fields (`code`,
// `retryable`, `retryAfter`, `requestId`) so callers can route retries without
// re-parsing the body.
//
// This is the single set: the facade routes every Kiota transport error and
// every `ok:false` result through the helpers below. (The earlier disjoint
// facade-local `*Error` classes were removed — see git history.)

import { ALL_CODES, RESULT_CODES, STATUS_TO_CODE, isRetryable } from "./errorCodes.js";

// ---------------------------------------------------------------------------
// Base error classes (self-contained; no transport/runtime dependency).
//
// These were previously Fern-generated under src/errors/. The Kiota-only SDK
// owns them directly here so the canonical error surface has zero coupling to a
// generated transport runtime. Public shape is preserved: `GhostCrawlError`
// carries `statusCode` / `body` / `cause`; `GhostCrawlTimeoutError` carries
// `cause`. Both set `name` from the concrete constructor.
// ---------------------------------------------------------------------------

/** Base class for every GhostCrawl SDK error. */
export class GhostCrawlError extends Error {
    public readonly statusCode?: number;
    public readonly body?: unknown;
    public readonly cause?: unknown;

    constructor({
        message,
        statusCode,
        body,
        cause,
    }: {
        message?: string;
        statusCode?: number;
        body?: unknown;
        cause?: unknown;
    } = {}) {
        super(buildErrorMessage({ message, statusCode, body }));
        Object.setPrototypeOf(this, new.target.prototype);
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, this.constructor);
        }
        this.name = this.constructor.name;
        this.statusCode = statusCode;
        this.body = body;
        if (cause != null) {
            this.cause = cause;
        }
    }
}

/** Raised when a request exceeds the configured timeout. */
export class GhostCrawlTimeoutError extends Error {
    public readonly cause?: unknown;

    constructor(message: string, opts?: { cause?: unknown }) {
        super(message);
        Object.setPrototypeOf(this, new.target.prototype);
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, this.constructor);
        }
        this.name = this.constructor.name;
        if (opts?.cause != null) {
            this.cause = opts.cause;
        }
    }
}

function buildErrorMessage({
    message,
    statusCode,
    body,
}: {
    message: string | undefined;
    statusCode: number | undefined;
    body: unknown | undefined;
}): string {
    const lines: string[] = [];
    if (message != null) {
        lines.push(message);
    }
    if (statusCode != null) {
        lines.push(`Status code: ${statusCode.toString()}`);
    }
    if (body != null) {
        lines.push(`Body: ${JSON.stringify(body, undefined, 2)}`);
    }
    return lines.join("\n");
}

export interface GhostCrawlErrorInit {
    message?: string;
    statusCode?: number;
    body?: unknown;
    cause?: unknown;
    /** Canonical catalog code (e.g. "rate_limited", "blocked"). */
    code?: string;
    /** Whether the catalog marks this failure retryable. */
    retryable?: boolean;
    /** Seconds to wait before retrying, when advertised. */
    retryAfter?: number;
    /** The problem+json `instance` field (request id) — quote when reporting. */
    requestId?: string;
}

/** Attach the canonical two-channel fields onto a constructed error instance. */
function assignCanonical(err: GhostCrawlError, init: GhostCrawlErrorInit): void {
    const e = err as GhostCrawlError & {
        code?: string;
        retryable?: boolean;
        retryAfter?: number;
        requestId?: string;
    };
    if (init.code !== undefined) e.code = init.code;
    e.retryable = init.retryable ?? false;
    if (init.retryAfter !== undefined) e.retryAfter = init.retryAfter;
    if (init.requestId !== undefined) e.requestId = init.requestId;
}

/** 401 — Invalid API key or missing Authorization header. */
export class GhostCrawlAuthError extends GhostCrawlError {
    public readonly code?: string;
    public readonly retryable?: boolean;
    public readonly retryAfter?: number;
    public readonly requestId?: string;
    constructor(init: GhostCrawlErrorInit = {}) {
        super({ statusCode: 401, ...init });
        this.name = "GhostCrawlAuthError";
        Object.setPrototypeOf(this, new.target.prototype);
        assignCanonical(this, { retryable: false, ...init });
    }
}

/** 402 — Quota exceeded; upgrade your plan or contact us at https://ghostcrawl.io/billing. */
export class GhostCrawlQuotaError extends GhostCrawlError {
    public readonly code?: string;
    public readonly retryable?: boolean;
    public readonly retryAfter?: number;
    public readonly requestId?: string;
    constructor(init: GhostCrawlErrorInit = {}) {
        super({ statusCode: 402, ...init });
        this.name = "GhostCrawlQuotaError";
        Object.setPrototypeOf(this, new.target.prototype);
        assignCanonical(this, { retryable: false, ...init });
    }
}

/** 429 — Rate limited; check `retryAfter` (seconds) when present. */
export class GhostCrawlRateLimitError extends GhostCrawlError {
    public readonly code?: string;
    public readonly retryable?: boolean;
    public readonly retryAfter?: number;
    public readonly requestId?: string;
    constructor(init: GhostCrawlErrorInit = {}) {
        super({ statusCode: 429, ...init });
        this.name = "GhostCrawlRateLimitError";
        Object.setPrototypeOf(this, new.target.prototype);
        assignCanonical(this, { retryable: true, ...init });
    }
}

/** 400 / 422 — The request was rejected as invalid before it ran. */
export class GhostCrawlInvalidRequestError extends GhostCrawlError {
    public readonly code?: string;
    public readonly retryable?: boolean;
    public readonly retryAfter?: number;
    public readonly requestId?: string;
    constructor(init: GhostCrawlErrorInit = {}) {
        super({ statusCode: init.statusCode ?? 422, ...init });
        this.name = "GhostCrawlInvalidRequestError";
        Object.setPrototypeOf(this, new.target.prototype);
        assignCanonical(this, { retryable: false, ...init });
    }
}

/** 5xx / other OUR-side problem responses — typically retryable. */
export class GhostCrawlServerError extends GhostCrawlError {
    public readonly code?: string;
    public readonly retryable?: boolean;
    public readonly retryAfter?: number;
    public readonly requestId?: string;
    constructor(init: GhostCrawlErrorInit = {}) {
        super({ statusCode: init.statusCode ?? 500, ...init });
        this.name = "GhostCrawlServerError";
        Object.setPrototypeOf(this, new.target.prototype);
        assignCanonical(this, { retryable: true, ...init });
    }
}

/**
 * Raised when a 200 response reports a TARGET-side failure.
 *
 * The request reached the API fine, but the *target* failed in a way that means
 * the result is not usable — the site blocked us (`blocked`), presented a
 * CAPTCHA (`captcha_required`), returned an HTTP error (`target_http_error` with
 * `targetStatus`), could not be reached (`navigation_failed`), or yielded no
 * extractable content (`empty_content`). This prevents a blocked / errored
 * scrape from being silently counted as a success.
 */
export class GhostCrawlScrapeError extends GhostCrawlError {
    public readonly code?: string;
    public readonly retryable?: boolean;
    public readonly requestId?: string;
    /** The target's HTTP status, when the failure was `target_http_error`. */
    public readonly targetStatus?: number;
    /** Optional finer-grained sub-reason (e.g. "dns_error"). */
    public readonly reason?: string;
    constructor(init: GhostCrawlErrorInit & { targetStatus?: number; reason?: string } = {}) {
        const { targetStatus, reason, ...rest } = init;
        super({ statusCode: 200, ...rest });
        this.name = "GhostCrawlScrapeError";
        Object.setPrototypeOf(this, new.target.prototype);
        assignCanonical(this, rest);
        this.targetStatus = targetStatus;
        this.reason = reason;
    }
}

function parseRetryAfterHeader(
    headers: Record<string, string | string[] | undefined> | undefined,
): number | undefined {
    const raw = headers?.["retry-after"] ?? headers?.["Retry-After"];
    const value = Array.isArray(raw) ? raw[0] : raw;
    if (value == null) return undefined;
    const n = Number.parseInt(String(value), 10);
    return Number.isFinite(n) ? n : undefined;
}

/**
 * Map an HTTP status code (and optional problem+json body / headers) to the
 * right `GhostCrawl*` subclass. Prefers the canonical `code` from the body,
 * falling back to the status. Returns the base `GhostCrawlError` for any
 * code/status that does not match a domain class — callers can still inspect
 * `statusCode` / `code` on the returned instance.
 *
 * Mirrors `_translate_kiota_error` in the Python SDK facade and `_handle_error`
 * in `sdks/python-langchain/ghostcrawl_langchain/tools.py`.
 */
export function classifyHttpError(
    statusCode: number,
    init: GhostCrawlErrorInit & {
        headers?: Record<string, string | string[] | undefined>;
    } = {},
): GhostCrawlError {
    const { headers, ...rest } = init;

    // Resolve the canonical code: explicit init.code → body.code → status fallback.
    const body = rest.body;
    let code = rest.code;
    if (code == null && body !== null && typeof body === "object") {
        const bc = (body as Record<string, unknown>)["code"];
        if (typeof bc === "string" && ALL_CODES.includes(bc)) code = bc;
    }
    if (code == null) code = STATUS_TO_CODE[statusCode];

    // request_id rides on the problem+json `instance` field.
    let requestId = rest.requestId;
    if (requestId == null && body !== null && typeof body === "object") {
        const inst = (body as Record<string, unknown>)["instance"] ?? (body as Record<string, unknown>)["request_id"];
        if (typeof inst === "string") requestId = inst;
    }

    // retryable: explicit body flag wins, else the catalog flag for the code.
    let retryable = rest.retryable;
    if (retryable == null && body !== null && typeof body === "object" && "retryable" in (body as object)) {
        retryable = Boolean((body as Record<string, unknown>)["retryable"]);
    }
    if (retryable == null) retryable = isRetryable(code);

    // retry_after: explicit → body → header.
    let retryAfter = rest.retryAfter;
    if (retryAfter == null && body !== null && typeof body === "object") {
        const ra = (body as Record<string, unknown>)["retry_after"];
        if (typeof ra === "number") retryAfter = ra;
    }
    if (retryAfter == null) retryAfter = parseRetryAfterHeader(headers);

    // message: prefer the server's problem+json human message (`detail`, then
    // `title`) over the kiota repr ("no error class is registered for code N")
    // that the adapter puts in `message` for statuses it doesn't error-map.
    let message = rest.message;
    if (body !== null && typeof body === "object") {
        const b = body as Record<string, unknown>;
        const serverMsg = b["detail"] ?? b["title"];
        if (typeof serverMsg === "string" && serverMsg.length > 0) message = serverMsg;
    }

    const common: GhostCrawlErrorInit = { ...rest, message, statusCode, code, retryable, retryAfter, requestId };

    if (code === "unauthorized" || statusCode === 401) {
        return new GhostCrawlAuthError(common);
    }
    if (code === "payment_required" || statusCode === 402) {
        return new GhostCrawlQuotaError(common);
    }
    if (code === "rate_limited" || statusCode === 429) {
        return new GhostCrawlRateLimitError(common);
    }
    if (
        code === "bad_request" ||
        code === "byo_proxy_invalid" ||
        code === "tier_unavailable" ||
        statusCode === 400 ||
        statusCode === 422
    ) {
        return new GhostCrawlInvalidRequestError(common);
    }
    if (statusCode >= 500 && statusCode < 600) {
        return new GhostCrawlServerError(common);
    }
    const err = new GhostCrawlError(common);
    assignCanonical(err, common);
    return err;
}

interface KiotaApiErrorLike {
    responseStatusCode?: number;
    responseHeaders?: Record<string, string | string[]>;
    message?: string;
    // Kiota attaches the deserialized error body when a mapping exists.
    [key: string]: unknown;
}

/** Best-effort extraction of a problem+json body off a thrown Kiota error. */
function extractProblemBody(err: unknown): unknown {
    if (err === null || typeof err !== "object") return undefined;
    const e = err as Record<string, unknown>;
    // Common shapes the Kiota fetch adapter / our wrappers attach the body under.
    for (const key of ["body", "error", "responseBody"]) {
        if (e[key] !== undefined && e[key] !== null) return e[key];
    }
    // Some adapters fold the JSON into the message.
    const msg = e["message"];
    if (typeof msg === "string" && msg.includes("{")) {
        try {
            return JSON.parse(msg.slice(msg.indexOf("{"), msg.lastIndexOf("}") + 1));
        } catch {
            /* not JSON */
        }
    }
    return undefined;
}

/**
 * Translate an error thrown by the Kiota request adapter into the canonical
 * `GhostCrawl*` domain error. Returns the original error unchanged if it
 * carries no HTTP status (e.g. a network/DNS error with no response).
 */
export function translateKiotaError(err: unknown): unknown {
    if (err === null || typeof err !== "object") return err;
    const k = err as KiotaApiErrorLike;
    const status = typeof k.responseStatusCode === "number" ? k.responseStatusCode : undefined;
    if (status === undefined) return err;
    const body = extractProblemBody(err);
    return classifyHttpError(status, {
        body,
        headers: k.responseHeaders,
        message: typeof k.message === "string" ? k.message : undefined,
        cause: err,
    });
}

/**
 * Scan a decoded 200 response and throw {@link GhostCrawlScrapeError} when it
 * reports a TARGET failure (`ok: false` / `result_error`). Otherwise returns
 * the result unchanged. Stops a blocked / timed-out / errored scrape from being
 * silently counted as a success.
 */
export function scanResultError<T>(result: T): T {
    if (result === null || typeof result !== "object" || Array.isArray(result)) return result;
    const r = result as Record<string, unknown>;
    // Descend into a `results` envelope (scrape/extract wrap per-URL results); the
    // target failure lives on the INNER result, not the envelope top level.
    const inner = r["results"];
    if (Array.isArray(inner)) {
        for (const item of inner) scanResultError(item);
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
        // The flat markdown-build envelope reports a target failure ONLY via
        // status="failed" (no ok/result_error). Don't count it as a success.
        code = typeof topCode === "string" ? topCode : undefined;
        if (typeof r["target_status"] === "number") targetStatus = r["target_status"] as number;
    } else {
        return result;
    }

    let detail = `Scrape failed (${code ?? "unknown"})`;
    if (targetStatus !== undefined) detail += `: target returned HTTP ${targetStatus}`;
    else if (reason) detail += `: ${reason}`;

    const requestId = typeof r["request_id"] === "string" ? (r["request_id"] as string) : typeof r["instance"] === "string" ? (r["instance"] as string) : undefined;

    throw new GhostCrawlScrapeError({
        message: detail,
        body: result,
        code,
        retryable: retryable || isRetryable(code),
        targetStatus,
        reason,
        requestId,
    });
}
