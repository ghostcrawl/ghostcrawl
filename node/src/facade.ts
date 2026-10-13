/**
 * GhostCrawl idiomatic facade — delegates to the Kiota-generated canonical core.
 *
 * Architecture:
 *   _generated/ Kiota core  — spec-faithful 98-op request-builder metadata, models, auth/transport
 *   This FACADE              — thin ergonomic layer that calls the generated builders
 *
 * Delegation contract:
 *   - All URL templates, HTTP methods, error mappings, and serialization metadata
 *     come from the _generated/ Kiota core (src/_generated/v1/ builders).
 *   - The facade constructs request bodies using the Kiota additionalData mechanism
 *     (the Kiota serializer writes all additional-data fields as top-level JSON keys).
 *   - Auth: BaseBearerTokenAuthenticationProvider + static AccessTokenProvider.
 *   - Transport: @microsoft/kiota-http-fetchlibrary FetchRequestAdapter.
 *
 * Note on body construction: The Kiota-generated model classes use a typed request-builder
 * pattern. We use the `additionalData` body mechanism (Kiota's serialization path that
 * writes all additional-data fields as top-level JSON keys) which is equivalent to
 * constructing the typed model instances. This keeps the facade independent of generated
 * model import churn when the spec changes. See sdks/FACADE-PATTERN.md for the design.
 *
 * Usage:
 *   ```typescript
 *   import { createGhostCrawlClient } from "@ghostcrawl/sdk";
 *   const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });
 *   const result = await client.scrape({ url: "https://example.com" });
 *   ```
 */

import {
    AllowedHostsValidator,
    BaseBearerTokenAuthenticationProvider,
    type AccessTokenProvider,
    apiClientProxifier,
    type RequestAdapter,
    type NavigationMetadata,
    ParseNodeFactoryRegistry,
    SerializationWriterFactoryRegistry,
} from "@microsoft/kiota-abstractions";
import { FetchRequestAdapter } from "@microsoft/kiota-http-fetchlibrary";
import { JsonParseNodeFactory, JsonSerializationWriterFactory } from "@microsoft/kiota-serialization-json";
import { TextParseNodeFactory, TextSerializationWriterFactory } from "@microsoft/kiota-serialization-text";
import { FormParseNodeFactory, FormSerializationWriterFactory } from "@microsoft/kiota-serialization-form";
import { MultipartSerializationWriterFactory } from "@microsoft/kiota-serialization-multipart";

// Build a pre-configured ParseNodeFactoryRegistry for this adapter instance.
// FetchRequestAdapter's constructor creates fresh registries by default (no global singleton),
// so we construct and configure them here and pass them in.
function buildSerializationRegistries(): {
    parseRegistry: ParseNodeFactoryRegistry;
    writeRegistry: SerializationWriterFactoryRegistry;
} {
    const parseRegistry = new ParseNodeFactoryRegistry();
    const writeRegistry = new SerializationWriterFactoryRegistry();
    // JSON (primary — required for application/json request bodies and responses)
    parseRegistry.contentTypeAssociatedFactories.set("application/json", new JsonParseNodeFactory());
    writeRegistry.contentTypeAssociatedFactories.set("application/json", new JsonSerializationWriterFactory());
    // Text
    parseRegistry.contentTypeAssociatedFactories.set("text/plain", new TextParseNodeFactory());
    writeRegistry.contentTypeAssociatedFactories.set("text/plain", new TextSerializationWriterFactory());
    // Form
    parseRegistry.contentTypeAssociatedFactories.set("application/x-www-form-urlencoded", new FormParseNodeFactory());
    writeRegistry.contentTypeAssociatedFactories.set("application/x-www-form-urlencoded", new FormSerializationWriterFactory());
    // Multipart
    writeRegistry.contentTypeAssociatedFactories.set("multipart/form-data", new MultipartSerializationWriterFactory());
    return { parseRegistry, writeRegistry };
}
// @ts-ignore — _generated/ is excluded from tsconfig compilation (rootDir=src, _generated is
// a symlink to the sibling directory). The import resolves at runtime. The static import
// is intentional: it loads the generated navigation metadata at module startup and enables
// apiClientProxifier to route all requests through the spec-generated core.
import { V1RequestBuilderNavigationMetadata } from "./_generated/v1/index.js";

// Canonical error surface — the ONE domain error set (src/errors.ts). The facade
// translates every Kiota transport error and scans every 200 result through these
// helpers, so a problem+json `code` becomes a typed error and an `ok:false`
// result raises `GhostCrawlScrapeError` instead of looking like a success.
import { translateKiotaError, scanResultError, classifyHttpError, GhostCrawlError } from "./errors.js";
// Branded User-Agent (ghostcrawl-node/<version> Node/<v> <os>/<arch>). Applied to
// the generic raw request() escape hatch so unmodeled endpoints carry the same
// UA the modeled (Kiota) requests do.
import { uaString } from "./branded.js";
// Timeout error raised when a wait()/start({wait:true}) call exceeds the caller
// deadline without the run reaching a terminal state.
import { GhostCrawlTimeoutError } from "./errors.js";
// SDK-owned bounded client-side poll for search({ wait: true }).
import { pollSearchJob, parseRetryAfter } from "./_searchPoll.js";

const DEFAULT_BASE_URL = "https://api.ghostcrawl.io";

/**
 * Best-effort read of `<keyName> = "..."` from the CLI's config files, matching
 * the CLI resolution order so `ghostcrawl init` output is honored by the SDK too:
 * `./ghostcrawl.toml` (cwd) first, then `$XDG_CONFIG_HOME/ghostcrawl/config.toml`.
 *
 * Node-only: returns `undefined` anywhere `fs` is unavailable (browsers, edge
 * runtimes) — the early `versions.node` guard runs before any `require`, so a
 * browser bundle never touches `node:fs`. Never throws; config is optional.
 */
function readConfigValue(keyName: "api_key" | "base_url"): string | undefined {
    const proc: any = typeof process !== "undefined" ? process : undefined;
    if (!proc?.versions?.node) return undefined;
    let fs: any, os: any, path: any;
    try {
        // `process.getBuiltinModule` (Node 22+) loads a builtin synchronously in
        // BOTH the ESM and CJS builds without a static import (which would break
        // browser bundles) and without `require` (absent in the ESM build). Fall
        // back to `require` on older CJS runtimes; give up gracefully otherwise.
        const getBuiltin: any = proc.getBuiltinModule?.bind(proc);
        const load: (m: string) => any = getBuiltin
            ? getBuiltin
            : typeof require === "function"
              ? (require as any)
              : (() => {
                    throw new Error("no builtin loader");
                });
        fs = load("node:fs");
        os = load("node:os");
        path = load("node:path");
    } catch {
        return undefined;
    }
    const xdg = (proc.env["XDG_CONFIG_HOME"] ?? "").trim();
    const xdgBase = xdg.length > 0 ? xdg : path.join(os.homedir(), ".config");
    const candidates = [
        path.join(proc.cwd(), "ghostcrawl.toml"),
        path.join(xdgBase, "ghostcrawl", "config.toml"),
    ];
    for (const p of candidates) {
        try {
            const txt: string = fs.readFileSync(p, "utf-8");
            for (const raw of txt.split(/\r?\n/)) {
                const line = raw.trim();
                if (!line || line.startsWith("#") || !line.startsWith(keyName)) continue;
                const idx = line.indexOf("=");
                if (idx < 0) continue;
                let rhs = line.slice(idx + 1).trim();
                if (rhs.startsWith('"') && rhs.endsWith('"')) {
                    rhs = rhs.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, "\\");
                }
                if (rhs) return rhs;
            }
        } catch {
            /* missing/unreadable file — try the next candidate */
        }
    }
    return undefined;
}

/**
 * Guarantee a STABLE `search` result shape regardless of poll outcome.
 *
 * The API carries the hit list under `items`, but the SDK's canonical parity
 * field is `results`. Beyond aliasing `items` → `results` (non-destructive —
 * `items` stays), the cold-rotation search-job contract can hand back a raw
 * *running* handle (`{ status: "running", job_id, poll_url, ... }` — no `items`)
 * when the client-side poll budget elapses before the job reaches terminal.
 * Left raw, `result.query` / `result.results` are `undefined` — a surprise
 * shape the caller cannot code against. This injects the caller's `query` and
 * `engine` (only the SDK knows them) and normalizes `results` to a non-null
 * array, so every `search` return — warm `200`, `wait: false` handle, or
 * timed-out poll — always carries `query`/`engine`/`results`.
 */
function finalizeSearch(data: unknown, query?: string, engine?: string): SearchResult {
    const obj = (
        data && typeof data === "object" ? { ...(data as Record<string, unknown>) } : {}
    ) as SearchResult;
    if (obj.results === undefined || obj.results === null) {
        const items = (obj as Record<string, unknown>)["items"];
        obj.results = Array.isArray(items) ? (items as unknown[]) : [];
    }
    // Real query/engine always win over an absent/empty value from a bare handle.
    if (query !== undefined && (obj.query === undefined || obj.query === null || obj.query === "")) {
        obj.query = query;
    }
    if (engine !== undefined && (obj.engine === undefined || obj.engine === null)) {
        obj.engine = engine;
    }
    return obj;
}

/** Small async sleep — used ONLY for transient-error backoff, never for polling. */
const sleep = (ms: number): Promise<void> => new Promise((r) => setTimeout(r, ms));

/**
 * Default per-request timeout (ms) for the raw-`fetch` escape-hatch paths
 * (pdf/screenshot/content/search-wait/request). The Kiota transport imposes no
 * client-side deadline; this bound keeps a stalled server from hanging a call
 * indefinitely. Overridable per client via `GhostCrawlClientOptions.timeoutMs`.
 */
const DEFAULT_REQUEST_TIMEOUT_MS = 60_000;

/**
 * Map a non-2xx `fetch` Response to the canonical `GhostCrawl*` domain error —
 * the SAME typed family the Kiota-modeled paths produce via `classifyHttpError`
 * (a 402 → GhostCrawlQuotaError, 429 → GhostCrawlRateLimitError, …), keyed on
 * the problem+json `code` when present and the HTTP status otherwise. Replaces
 * the old bare untyped `Error` so callers of the raw-HTTP escape hatches route
 * on `code`/`statusCode` uniformly. Reads the body via clone so the caller may
 * still read it.
 */
async function httpErrorFromResponse(res: Response): Promise<GhostCrawlError> {
    let body: unknown;
    try {
        const text = await res.clone().text();
        body = text;
        if (text) {
            try {
                body = JSON.parse(text);
            } catch {
                /* leave as raw text */
            }
        }
    } catch {
        body = undefined;
    }
    const retryAfter = res.headers.get("retry-after");
    return classifyHttpError(res.status, {
        body,
        headers: retryAfter != null ? { "retry-after": retryAfter } : undefined,
    });
}

/**
 * `fetch` with a hard timeout (AbortController) and typed failure mapping. A
 * timeout raises `GhostCrawlTimeoutError`; a transport/connection failure (DNS,
 * refused, reset — normally a raw `TypeError: fetch failed`) is surfaced as a
 * `GhostCrawlError` carrying the underlying `cause`, never a bare `TypeError`.
 * A caller-supplied `signal` is honored alongside the timeout.
 */
async function fetchWithTimeout(
    url: string,
    init: RequestInit,
    timeoutMs: number,
    signal?: AbortSignal,
): Promise<Response> {
    const controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => {
        timedOut = true;
        controller.abort();
    }, timeoutMs);
    const onAbort = (): void => controller.abort();
    if (signal) {
        if (signal.aborted) controller.abort();
        else signal.addEventListener("abort", onAbort, { once: true });
    }
    try {
        return await fetch(url, { ...init, signal: controller.signal });
    } catch (err) {
        if (timedOut) {
            throw new GhostCrawlTimeoutError(
                `Request to ${url} timed out after ${timeoutMs.toString()}ms`,
                { cause: err },
            );
        }
        if (signal?.aborted) {
            throw new GhostCrawlTimeoutError(`Request to ${url} was aborted`, { cause: signal.reason ?? err });
        }
        throw new GhostCrawlError({ message: `Network request to ${url} failed`, cause: err });
    } finally {
        clearTimeout(timer);
        if (signal) signal.removeEventListener("abort", onAbort);
    }
}

/**
 * Read a `fetch` Response body as JSON, converting a malformed body into a typed
 * `GhostCrawlError` (never a raw `SyntaxError`). Used by the raw-HTTP success
 * paths so a garbage 200 fails in the canonical error family.
 */
async function parseJsonResponse<T>(res: Response): Promise<T> {
    const text = await res.text();
    try {
        return JSON.parse(text) as T;
    } catch (err) {
        throw new GhostCrawlError({
            message: `GhostCrawl returned a response body that could not be parsed as JSON (HTTP ${res.status.toString()}).`,
            statusCode: res.status,
            body: text,
            cause: err,
        });
    }
}

// ---------------------------------------------------------------------------
// Static bearer token provider
// ---------------------------------------------------------------------------

class StaticTokenProvider implements AccessTokenProvider {
    private readonly _validator = new AllowedHostsValidator(new Set<string>());

    constructor(private readonly _token: string) {}

    getAuthorizationToken = async (
        _url?: string,
        _additionalContext?: Record<string, unknown>,
    ): Promise<string> => {
        return this._token;
    };

    getAllowedHostsValidator = (): AllowedHostsValidator => {
        return this._validator;
    };
}

// ---------------------------------------------------------------------------
// Body factory: plain Kiota AdditionalDataHolder-compatible objects
//
// The Kiota serializer writes all entries in `additionalData` as top-level
// JSON fields when the object has no known-property serializers. This lets us
// pass plain `{additionalData: {...fields}}` objects when the generated model
// serializers are unavailable (e.g. truncated models/index.ts).
// ---------------------------------------------------------------------------

function makeBody(fields: Record<string, unknown>): { additionalData: Record<string, unknown> } {
    return { additionalData: fields };
}

// ---------------------------------------------------------------------------
// Kiota response unwrapper
//
// The Kiota TS generator wraps every deserialized field in a value-holder object
// { value: T, getValue: () => T }. The facade unwraps this automatically so
// callers receive plain JSON-compatible objects, not model instances.
//
// Additionally, operations whose generated response model declares no typed
// properties (an empty `AdditionalDataHolder` — e.g. /v1/extract) deserialize
// the ENTIRE JSON body into a single `additionalData`
// envelope: `{ additionalData: { ...all real fields... } }`. Left as-is, callers
// would see `result.additionalData.data` instead of `result.data`. We hoist that
// lone-`additionalData` envelope so every operation returns flat, plain JSON —
// matching the documented contract and the behavior of operations whose models
// DO declare properties (e.g. scrape returns top-level fields directly).
//
// Finally, operations whose model declares SOME typed properties but whose
// response also carries UNDECLARED JSON fields (e.g. /v1/scrape returns a
// top-level `identity_id` the generated ScrapeResponse never declared) land
// those overflow fields in the model's `additionalData` bucket ALONGSIDE the
// typed keys. We merge that overflow bucket up to top level so every undeclared
// field (identity_id today, any future addition) appears flat next to the typed
// ones — never nested under `result.additionalData`.
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function unwrapKiota(val: unknown): unknown {
    if (val === null || val === undefined) return val;
    if (typeof val !== "object") return val;
    if (Array.isArray(val)) return val.map(unwrapKiota);
    const obj = val as Record<string, unknown>;
    const keys = Object.keys(obj);
    // Kiota value-holder: exactly { value, getValue } or { value, getValue, ... } with getValue fn
    if (keys.includes("value") && keys.includes("getValue") && typeof obj["getValue"] === "function") {
        return unwrapKiota(obj["value"]);
    }
    // Lone-`additionalData` envelope from an empty AdditionalDataHolder response
    // model: hoist the inner object to the top level so callers get flat JSON.
    if (keys.length === 1 && keys[0] === "additionalData" && obj["additionalData"] !== null && typeof obj["additionalData"] === "object") {
        return unwrapKiota(obj["additionalData"]);
    }
    const out: Record<string, unknown> = {};
    for (const k of keys) {
        // Mixed envelope: typed keys plus an `additionalData` overflow bucket of
        // undeclared response fields (e.g. scrape's top-level `identity_id`).
        // Hoist the overflow entries to top level so undeclared fields appear
        // flat next to the typed ones. Existing typed keys win on collision.
        if (k === "additionalData" && obj[k] !== null && typeof obj[k] === "object" && !Array.isArray(obj[k])) {
            const overflow = unwrapKiota(obj[k]) as Record<string, unknown>;
            for (const ok of Object.keys(overflow)) {
                if (!(ok in out)) out[ok] = overflow[ok];
            }
            continue;
        }
        out[k] = unwrapKiota(obj[k]);
    }
    return out;
}

// ---------------------------------------------------------------------------
// Core Kiota v1 builder proxy
//
// V1RequestBuilderNavigationMetadata comes from _generated/v1/index.ts.
// We import it via require() at runtime (the _generated symlink makes it
// resolvable; excluded from tsconfig compilation to avoid type errors from
// the truncated models/index.ts).
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type V1Builder = Record<string, any>;

// Helper: call a Kiota builder method, translate transport errors to the
// canonical domain errors, unwrap the result, and scan it for a TARGET failure.
//
//  - A non-2xx problem+json response → typed `GhostCrawl*` error keyed on the
//    canonical `code` (translateKiotaError). Previously raw Kiota `ApiError`s
//    leaked here untranslated.
//  - A 200 response that reports `ok:false` / `result_error` → throws
//    `GhostCrawlScrapeError` (scanResultError) so a blocked / errored scrape is
//    never silently a success.
async function callKiota(promise: Promise<unknown>): Promise<Record<string, unknown>> {
    let raw: unknown;
    try {
        raw = await promise;
    } catch (err) {
        throw translateKiotaError(err);
    }
    const unwrapped = (raw === null || raw === undefined ? {} : unwrapKiota(raw)) as Record<string, unknown>;
    return scanResultError(unwrapped);
}

// ---------------------------------------------------------------------------
// Scrape content normalization
//
// The /v1/scrape response carries the rendered page under a FORMAT-SPECIFIC key
// ("markdown", or "html"/"text" per the requested format), but the documented
// SDK contract + README quickstart expect a generic `content` field. Mirror the
// verified Python reference: derive `content` from response.format's key (or the
// first of markdown/html/text that holds a string), keeping the original
// format-specific key intact for backward compatibility.
// ---------------------------------------------------------------------------

function normalizeScrapeContent(result: Record<string, unknown>): Record<string, unknown> {
    // Only for a plain object that does not already carry a `content` key.
    if (result === null || typeof result !== "object" || "content" in result) {
        return result;
    }

    const fmt = result.format;
    let value: unknown = typeof fmt === "string" ? result[fmt] : undefined;

    if (typeof value !== "string") {
        for (const key of ["markdown", "html", "text"]) {
            if (typeof result[key] === "string") {
                value = result[key];
                break;
            }
        }
    }

    if (typeof value === "string") {
        result.content = value;
    }
    return result;
}

// ---------------------------------------------------------------------------
// Body-capturing adapter
//
// Kiota's FetchRequestAdapter throws a bare DefaultApiError (only status +
// headers, no body) when the response status is not in a route's errorMappings
// — which is the case for 401 / 402 / 429 (the generated builders map only 422).
// The server's problem+json `detail` / `title` was therefore lost, leaving the
// typed error's message as the kiota repr ("no error class is registered for
// code N"). This subclass reads the response body (via a clone, so the adapter's
// own body handling is untouched) and attaches the parsed problem+json onto the
// thrown error as `body`, so translateKiotaError → classifyHttpError can recover
// `detail` / `code` / `instance`. Transparent on success; never swallows.
// ---------------------------------------------------------------------------

class BodyCapturingFetchRequestAdapter extends FetchRequestAdapter {
    constructor(...args: ConstructorParameters<typeof FetchRequestAdapter>) {
        super(...args);
        // eslint-disable-next-line @typescript-eslint/no-this-alias
        const self = this as unknown as {
            throwIfFailedResponse: (
                response: Response,
                errorMappings: unknown,
                span: unknown,
            ) => Promise<void>;
        };
        const original = self.throwIfFailedResponse.bind(this);
        self.throwIfFailedResponse = async (
            response: Response,
            errorMappings: unknown,
            span: unknown,
        ): Promise<void> => {
            const isError = !(
                response.ok ||
                (response.status >= 300 && response.status < 400)
            );
            let captured: unknown;
            if (isError) {
                try {
                    const ctype = response.headers.get("content-type") ?? "";
                    if (ctype.includes("json")) {
                        captured = await response.clone().json();
                    }
                } catch {
                    captured = undefined;
                }
            }
            try {
                await original(response, errorMappings, span);
            } catch (err) {
                if (
                    captured !== undefined &&
                    err !== null &&
                    typeof err === "object" &&
                    (err as Record<string, unknown>)["body"] === undefined
                ) {
                    try {
                        (err as Record<string, unknown>)["body"] = captured;
                    } catch {
                        /* defensive — never block the rethrow */
                    }
                }
                throw err;
            }
        };
    }
}

function buildV1Core(token: string, baseUrl: string): V1Builder {
    const authProvider = new BaseBearerTokenAuthenticationProvider(
        new StaticTokenProvider(token),
    );
    // Pass pre-configured registries directly — FetchRequestAdapter creates its own
    // fresh instances by default and there is no global singleton in this version.
    const { parseRegistry, writeRegistry } = buildSerializationRegistries();
    const adapter: RequestAdapter = new BodyCapturingFetchRequestAdapter(authProvider, parseRegistry, writeRegistry);
    adapter.baseUrl = baseUrl;

    // V1RequestBuilderNavigationMetadata is statically imported from _generated/v1/index.js.
    // It carries the full spec-generated URL templates, HTTP methods, and error mappings
    // for all 98 operations. apiClientProxifier creates a runtime proxy that routes
    // every method call through FetchRequestAdapter + the spec metadata.
    return apiClientProxifier<V1Builder>(
        adapter,
        { baseurl: baseUrl },
        // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
        V1RequestBuilderNavigationMetadata as unknown as Record<string, NavigationMetadata>,
        undefined,
    );
}

// ---------------------------------------------------------------------------
// Typed-but-index-accessible results
//
// Every per-lane result is BOTH statically typed (discoverable canonical fields)
// AND index-accessible (`result["identity_id"]`) via the `[k: string]: unknown`
// index signature, so existing callers that treat a result as a plain object
// keep working unchanged while new code gets typed field access. The field names
// are the SINGLE source of truth in parity/sdk_surface_contract.json (`lanes.*`)
// and MUST be byte-identical across all seven SDKs. The raw Kiota `_generated/`
// models are NEVER exposed to the user — the facade returns these owned
// types. NB: these are structural TS interfaces (zero runtime cost); an
// unwrapped response object IS one of these once cast, so index access to any
// extra/unknown server field is preserved.
// ---------------------------------------------------------------------------

/** Result of `scrape` / `content` — parity lane `scrape`. */
export interface ScrapeResult {
    status?: string;
    /** Cross-format alias for the rendered output (markdown/html/text). */
    content?: string;
    markdown?: string;
    html?: string;
    status_code?: number;
    bytes?: number;
    url?: string;
    format?: string;
    warnings?: unknown[];
    /** Any extra/unknown server field remains index-accessible. */
    [k: string]: unknown;
}

/** Result of `search` — parity lane `search`. */
export interface SearchResult {
    status?: string;
    results?: unknown[];
    query?: string;
    engine?: string;
    [k: string]: unknown;
}

/** A crawl run — parity lane `crawl`. Returned by `crawl` / `crawlRuns.*`. */
export interface CrawlRun {
    run_id?: string;
    status?: string;
    results?: unknown[];
    [k: string]: unknown;
}

/** A single crawled/searched document — parity lane `document`. */
export interface Document {
    title?: string;
    url?: string;
    content?: string;
    [k: string]: unknown;
}

/**
 * Binary lane result (`pdf` / `screenshot`) — parity lanes `pdf` / `screenshot`.
 * The binary methods return a raw `Uint8Array` for back-compat; this interface
 * documents the canonical parity field names (`bytes`, `content_type`) shared
 * across all seven SDKs.
 */
export interface BinaryResult {
    bytes?: Uint8Array;
    content_type?: string;
    [k: string]: unknown;
}

// ---------------------------------------------------------------------------
// Sub-client types
// ---------------------------------------------------------------------------

/** Terminal crawl-run states — a run in one of these will never change again. */
export const CRAWL_TERMINAL_STATES: ReadonlySet<string> = new Set(["completed", "failed", "cancelled"]);

/** Options for the event-driven completion wait ({@link CrawlRunsClient.wait}). */
export interface CrawlWaitOptions {
    /**
     * Overall client-side deadline, in seconds, for the run to reach a terminal
     * state. Default 300. On expiry a {@link GhostCrawlTimeoutError} is thrown
     * carrying the last observed (non-terminal) run on its `body`.
     */
    timeout?: number;
    /**
     * Length, in seconds, of each server-blocking long-poll window (the
     * `timeout_s` sent to `GET .../{id}?wait=true`). Default 30. The server may
     * cap this to its own maximum; each window that returns non-terminal is
     * immediately re-issued with no client-side sleep in between.
     */
    pollTimeout?: number;
    /** Optional AbortSignal to cancel the wait early. */
    signal?: AbortSignal;
}

/** Options for {@link CrawlRunsClient.start}. */
export interface CrawlStartOptions {
    url: string;
    maxDepth?: number;
    maxPages?: number;
    includePatterns?: string[];
    /**
     * When true, the call BLOCKS server-side (`wait_until: "completed"`) until
     * the run reaches a terminal state or `timeout` (seconds) elapses, then
     * returns the terminal run with results present. Default false (returns the
     * freshly-started run immediately — poll or {@link CrawlRunsClient.wait} it).
     */
    wait?: boolean;
    /** Server-side block deadline in seconds when `wait` is true. Default 300. */
    timeout?: number;
    [key: string]: unknown;
}

/** Manage crawl runs — /v1/crawl-runs */
export class CrawlRunsClient {
    /**
     * @param _v1 Kiota v1 request-builder proxy.
     * @param _request Raw authenticated JSON transport injected by the parent
     *   client. Used by the event-driven {@link wait} / start-and-wait paths,
     *   which need query-string support (`?wait=true&timeout_s=N`) and the raw,
     *   un-scanned run record (a terminal `status: "failed"` is a valid answer to
     *   return, not a `GhostCrawlScrapeError` to throw).
     */
    constructor(
        private readonly _v1: V1Builder,
        private readonly _request?: (method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH", path: string, body?: unknown) => Promise<unknown>,
    ) {}

    /**
     * Start a new crawl run. Delegates to POST /v1/crawl-runs.
     *
     * The /v1/crawl-runs endpoint takes a discriminated-union body keyed on
     * `action`; the start verb requires `action: "start"` and `seed_urls`
     * (a list). This method maps the ergonomic `{ url }` input onto that
     * contract — `seed_urls: [url]`, `action: "start"` — and translates
     * `includePatterns` to the API's `follow_patterns` field. (The body is
     * `extra="forbid"` server-side, so only contract field names are sent.)
     *
     * Pass `{ wait: true }` to BLOCK until the run is terminal (server-side
     * `wait_until: "completed"`, bounded by `timeout` seconds, default 300) and
     * receive the finished run with results — no client poll loop required.
     */
    async start(options: CrawlStartOptions): Promise<Record<string, unknown>> {
        const { url, maxDepth = 3, maxPages = 100, includePatterns, wait = false, timeout = 300, ...rest } = options;
        const fields: Record<string, unknown> = {
            ...rest,
            action: "start",
            seed_urls: [url],
            max_depth: maxDepth,
            max_pages: maxPages,
            ...(includePatterns ? { follow_patterns: includePatterns } : {}),
        };
        if (wait) {
            // Server blocks until terminal (or timeout) and returns the run with
            // results present. Route through the raw transport so we get the
            // un-scanned run record (a terminal failed/cancelled run is returned,
            // not thrown) — and only if the parent wired one in.
            fields.wait_until = "completed";
            fields.timeout_s = timeout;
            if (this._request) {
                return (await this._request("POST", "/v1/crawl-runs", fields)) as Record<string, unknown>;
            }
        }
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.crawlRuns.post(makeBody(fields)));
    }

    /** List crawl runs. Delegates to GET /v1/crawl-runs. */
    async list(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.crawlRuns.get());
    }

    /** Get a single crawl run by ID. Delegates to GET /v1/crawl-runs/{run_id}. */
    async get(runId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.crawlRuns.byRun_id(runId).get());
    }

    /**
     * Block until a crawl run reaches a terminal state, then return it.
     *
     * This is the event-driven replacement for a hand-written
     * `while (...) { await get(id); await sleep(...) }` poll loop. It long-polls
     * `GET /v1/crawl-runs/{id}?wait=true&timeout_s=N`, which BLOCKS server-side
     * until the run is terminal or the window elapses. Each window that returns a
     * still-running run is re-issued immediately — the wait is driven by the
     * server's completion event, not a client timer, so there is no polling sleep
     * and no wasted request storm.
     *
     * Resolves with the terminal run (`status` ∈ {@link CRAWL_TERMINAL_STATES};
     * results present when `completed`). Throws {@link GhostCrawlTimeoutError} if
     * the caller's `timeout` (default 300s) elapses first — the last observed run
     * is attached as the error's `body` so you may inspect progress or wait again.
     *
     * @example
     * ```typescript
     * const { run_id } = await client.crawlRuns.start({ url: "https://example.com" });
     * const run = await client.crawlRuns.wait(run_id, { timeout: 600 });
     * console.log(run.status, run.pages_crawled);
     * ```
     */
    async wait(runId: string, options: CrawlWaitOptions = {}): Promise<Record<string, unknown>> {
        const timeoutS = options.timeout ?? 300;
        const windowS = Math.max(1, options.pollTimeout ?? 30);
        const deadline = Date.now() + timeoutS * 1000;
        let last: Record<string, unknown> = {};

        // The raw transport is always wired by the parent client; fall back to the
        // Kiota get() (no server-side blocking) if a bare sub-client was built.
        for (;;) {
            if (options.signal?.aborted) {
                throw new GhostCrawlTimeoutError(`Wait for crawl run ${runId} aborted`, { cause: options.signal.reason });
            }
            const remainingMs = deadline - Date.now();
            if (remainingMs <= 0) {
                throw new GhostCrawlTimeoutError(
                    `Crawl run ${runId} did not reach a terminal state within ${timeoutS.toString()}s ` +
                        `(last status: ${String(last.status ?? "unknown")})`,
                );
            }
            // Ask the server to block for at most the remaining budget, capped at
            // one poll window. Ceil so a sub-second remainder still gets ≥1s.
            const blockS = Math.max(1, Math.min(windowS, Math.ceil(remainingMs / 1000)));

            let run: Record<string, unknown>;
            try {
                if (this._request) {
                    run = (await this._request(
                        "GET",
                        `/v1/crawl-runs/${encodeURIComponent(runId)}?wait=true&timeout_s=${blockS.toString()}`,
                    )) as Record<string, unknown>;
                } else {
                    // No raw transport wired — degrade to a non-blocking get + backoff.
                    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
                    run = await callKiota(this._v1.crawlRuns.byRun_id(runId).get());
                    if (!CRAWL_TERMINAL_STATES.has(String(run.status ?? ""))) await sleep(Math.min(blockS * 1000, remainingMs));
                }
            } catch (err) {
                const status = (err as { statusCode?: number; responseStatusCode?: number }).statusCode ?? (err as { responseStatusCode?: number }).responseStatusCode;
                // A just-started run may not be queryable yet (404), or a gateway
                // may briefly 5xx — both are transient. Back off briefly and retry
                // while budget remains; anything else propagates.
                if ((status === 404 || status === 502 || status === 503 || status === 504) && Date.now() < deadline) {
                    await sleep(Math.min(1000, Math.max(0, deadline - Date.now())));
                    continue;
                }
                throw err;
            }

            last = run;
            if (CRAWL_TERMINAL_STATES.has(String(run.status ?? ""))) {
                return run;
            }
            // Non-terminal at the server's window boundary → re-issue immediately.
        }
    }

    /**
     * Alias of {@link wait} — long-poll a crawl run to completion. Provided for
     * discoverability (parity with the `waitForCompletion` name).
     */
    async waitForCompletion(runId: string, options: CrawlWaitOptions = {}): Promise<Record<string, unknown>> {
        return this.wait(runId, options);
    }

    /** Cancel a crawl run. Delegates to POST /v1/crawl-runs/{run_id}/cancel. */
    async cancel(runId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.crawlRuns.byRun_id(runId).cancel.post(null));
    }

    /**
     * Resume a paused / interrupted crawl run.
     * Delegates to POST /v1/crawl-runs/{run_id}/resume via the generated builder.
     */
    async resume(runId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.crawlRuns.byRun_id(runId).resume.post(null));
    }
}

/** Manage browser sessions — /v1/sessions */
export class SessionsClient {
    /**
     * @param _v1 Kiota v1 request-builder proxy.
     * @param _request Raw authenticated JSON transport injected by the parent
     *   client — used by the session-lifecycle routes that have no generated
     *   builder (`takeover`, `terminate`), matching the me()/usage() delegation
     *   path (auth + base URL + branded User-Agent through the same client).
     */
    constructor(
        private readonly _v1: V1Builder,
        private readonly _request?: (method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH", path: string, body?: unknown) => Promise<unknown>,
    ) {}

    /** List all active sessions. Delegates to GET /v1/sessions. */
    async list(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.get());
    }

    /**
     * Create a new browser session. Delegates to POST /v1/sessions/create.
     *
     * Two creation modes (pass exactly one — passing both is a server-side
     * validation error):
     *   - profile-based: pass `profileName` to rehydrate a saved identity profile
     *     (the org must already own a profile of that name, else the API 404s).
     *   - engine-based (ad-hoc): omit `profileName` and the API opens a fresh
     *     session on `engine` (`"chrome"`/`"firefox"`/`"webkit"`/`"auto"`; default
     *     `"auto"`) with no saved profile required — the zero-setup path that works
     *     on a brand-new key with no profiles.
     */
    async create(options: { profileName?: string; engine?: string; [key: string]: unknown } = {}): Promise<Record<string, unknown>> {
        const { profileName, engine, ...rest } = options;
        const body = profileName != null
            ? { profile: profileName, ...rest }
            : { engine: engine ?? "auto", ...rest };
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.create.post(makeBody(body)));
    }

    /** Extend a session's TTL. Delegates to POST /v1/sessions/{id}/extend. */
    async extend(sessionId: string, durationSeconds = 300): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.byProfile_Id(sessionId).extend.post(makeBody({ duration_seconds: durationSeconds })));
    }

    /** Release a session. Delegates to POST /v1/sessions/{id}/release. */
    async release(sessionId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.byProfile_Id(sessionId).release.post(null));
    }

    /**
     * Pin a session so the pool keeps it warm for reuse.
     * Delegates to POST /v1/sessions/{session_id}/pin via the generated builder.
     */
    async pin(sessionId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.byProfile_Id(sessionId).pin.post(null));
    }

    /**
     * Terminate a session immediately (hard stop, no return-to-pool).
     * POST /v1/sessions/{session_id}/terminate. The generated core has no
     * `terminate` builder (the route is absent from the customer-facing OpenAPI),
     * so this is routed through the shared authenticated `request()` transport —
     * no hand-rolled HTTP client (matches me()/usage()).
     */
    async terminate(sessionId: string): Promise<Record<string, unknown>> {
        if (!this._request) throw new Error("terminate requires the parent client transport");
        return (await this._request("POST", `/v1/sessions/${encodeURIComponent(sessionId)}/terminate`, {})) as Record<string, unknown>;
    }

    /**
     * Take interactive control of a running session (human-in-the-loop).
     * POST /v1/sessions/{session_id}/takeover. The generated core has no
     * `takeover` builder, so this is routed through the shared authenticated
     * `request()` transport. `action` and any extra fields are sent in the body.
     */
    async takeover(sessionId: string, options: { action?: string; [key: string]: unknown } = {}): Promise<Record<string, unknown>> {
        if (!this._request) throw new Error("takeover requires the parent client transport");
        return (await this._request("POST", `/v1/sessions/${encodeURIComponent(sessionId)}/takeover`, options)) as Record<string, unknown>;
    }

    /**
     * Mint a one-time interactive-takeover token for a session.
     * Delegates to POST /v1/sessions/{session_id}/takeover_token via the
     * generated builder. The returned token authorizes a browser-based takeover UI.
     */
    async takeoverToken(sessionId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.byProfile_Id(sessionId).takeover_token.post(null));
    }

    /**
     * Release an interactive takeover and hand control back to automation.
     * Delegates to POST /v1/sessions/{session_id}/takeover_release via the
     * generated builder.
     */
    async takeoverRelease(sessionId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.byProfile_Id(sessionId).takeover_release.post(null));
    }

    /**
     * Start a session recording for `profileId`.
     * Delegates to POST /v1/sessions/{profile_id}/recording/start via the builder.
     */
    async recordingStart(profileId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.byProfile_Id(profileId).recording.start.post(null));
    }

    /**
     * Stop the in-progress session recording for `profileId`.
     * Delegates to POST /v1/sessions/{profile_id}/recording/stop via the builder.
     */
    async recordingStop(profileId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.byProfile_Id(profileId).recording.stop.post(null));
    }
}

/**
 * Low-level CDP primitives for a live session — /v1/cdp.
 *
 * These are first-class customer surface. Delegates to the generated
 * `v1.cdp` builders (`frame` / `url`); `input` has no generated builder (absent
 * from the customer-facing OpenAPI) and is routed through the shared authenticated
 * `request()` transport (auth + base URL + branded User-Agent) — no hand-rolled HTTP.
 */
export class CdpClient {
    constructor(
        private readonly _v1: V1Builder,
        private readonly _request?: (method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH", path: string, body?: unknown) => Promise<unknown>,
    ) {}

    /** Drive a CDP `frame` command against the live page — POST /v1/cdp/frame. */
    async frame(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.cdp.frame.post(makeBody(fields)));
    }

    /** Navigate / read the live page URL over CDP — POST /v1/cdp/url. */
    async url(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.cdp.url.post(makeBody(fields)));
    }

    /**
     * Dispatch a CDP `Input` event to the live page — POST /v1/cdp/input.
     * The generated core has no `cdp.input` builder, so this is routed through the
     * shared authenticated `request()` transport — no hand-rolled HTTP client.
     */
    async input(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        if (!this._request) throw new Error("cdp.input requires the parent client transport");
        return (await this._request("POST", "/v1/cdp/input", fields)) as Record<string, unknown>;
    }
}

/**
 * High-level page primitives for a live session — /v1/page.
 *
 * These are first-class customer surface. Delegates to the generated
 * `v1.page` builders (cookies get/set/delete, dom_snapshot, download, eval, har,
 * scroll, upload, wait).
 */
export class PageClient {
    constructor(private readonly _v1: V1Builder) {}

    /** Read cookies from the live page — GET /v1/page/cookies. */
    async getCookies(options: { profileId?: string; domain?: string; name?: string } = {}): Promise<Record<string, unknown>> {
        const qp: Record<string, unknown> = {};
        if (options.profileId !== undefined) qp.profile_id = options.profileId;
        if (options.domain !== undefined) qp.domain = options.domain;
        if (options.name !== undefined) qp.name = options.name;
        return callKiota(
            // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
            this._v1.page.cookies.get({ queryParameters: qp }),
        );
    }

    /** Set cookies on the live page — POST /v1/page/cookies. */
    async setCookies(cookies: unknown[], fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.cookies.post(makeBody({ cookies, ...fields })));
    }

    /** Delete cookies from the live page — DELETE /v1/page/cookies. */
    async deleteCookies(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.cookies.delete(makeBody(fields)));
    }

    /** Capture a DOM snapshot of the live page — POST /v1/page/dom_snapshot. */
    async domSnapshot(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.dom_snapshot.post(makeBody(fields)));
    }

    /** Trigger / capture a file download on the live page — POST /v1/page/download. */
    async download(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.download.post(makeBody(fields)));
    }

    /** Evaluate an expression in the live page context — POST /v1/page/eval. */
    async eval(expression: string, fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // §0.6 facade-drift fix: the API EvalBody field is `script`, NOT `expression`
        // (parity/sdk_surface_contract.json / page_routes.py EvalBody). The method arg
        // stays `expression` for ergonomics but the wire body must send `script`.
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.eval.post(makeBody({ script: expression, ...fields })));
    }

    /** Capture the live page's network HAR log — POST /v1/page/har. */
    async har(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.har.post(makeBody(fields)));
    }

    /** Scroll the live page — POST /v1/page/scroll. */
    async scroll(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.scroll.post(makeBody(fields)));
    }

    /** Attach a file to a file input on the live page — POST /v1/page/upload. */
    async upload(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.upload.post(makeBody(fields)));
    }

    /**
     * Wait for a condition on the live page — POST /v1/page/wait.
     * e.g. `{ selector, timeout_ms, state: "visible" }` — passed through as body.
     */
    async wait(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.wait.post(makeBody(fields)));
    }

    /**
     * Replay a mouse op-stream on the live page — POST /v1/page/mouse.
     * `ops` is an ordered list of `{ kind: "move" | "down" | "up" | "wheel" | "dwell", ... }`
     * driven natively on the live page (engine-agnostic: the same trusted trajectory +
     * settled click on every engine). Extra fields (e.g. `session_id`) pass through.
     */
    async mouse(ops: Array<Record<string, unknown>>, fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.mouse.post(makeBody({ ops, ...fields })));
    }

    /**
     * Arrive at `destUrl` through a native link click from `sourceUrl` — POST /v1/page/arrival.
     * The live page's `document.referrer`, `Referer` and `Sec-Fetch-*` are produced natively
     * by the click (engine-agnostic). Optional fields: `referrer_shape` ("origin" | "full",
     * default "origin"), `source_title`, `session_id`.
     */
    async arrival(destUrl: string, sourceUrl: string, fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.arrival.post(makeBody({ dest_url: destUrl, source_url: sourceUrl, ...fields })));
    }

    /**
     * Visit a URL in a real new tab of the session's context, read it briefly, then close it
     * (the session continues on its original tab) — POST /v1/page/tab-visit.
     * e.g. `{ url, dwell_s: 3, session_id }`. Chrome engine only; other engines report
     * `unsupported`.
     */
    async tabVisit(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.page.tabVisit.post(makeBody(fields)));
    }
}

/**
 * Manage captured file downloads — /v1/downloads.
 *
 * The generated core has no `downloads` builder (the route family is absent from
 * the customer-facing OpenAPI), so every method is routed through the shared
 * authenticated `request()` transport — no hand-rolled HTTP client (matches
 * me()/usage()).
 */
export class DownloadsClient {
    constructor(
        private readonly _request: (method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH", path: string, body?: unknown) => Promise<unknown>,
    ) {}

    /** List captured downloads — GET /v1/downloads. */
    async list(): Promise<Record<string, unknown>> {
        return (await this._request("GET", "/v1/downloads")) as Record<string, unknown>;
    }

    /** Get a single download's metadata — GET /v1/downloads/{download_id}. */
    async get(downloadId: string): Promise<Record<string, unknown>> {
        return (await this._request("GET", `/v1/downloads/${encodeURIComponent(downloadId)}`)) as Record<string, unknown>;
    }

    /** Delete a captured download — DELETE /v1/downloads/{download_id}. */
    async delete(downloadId: string): Promise<Record<string, unknown>> {
        return (await this._request("DELETE", `/v1/downloads/${encodeURIComponent(downloadId)}`)) as Record<string, unknown>;
    }
}

/**
 * Manage reusable storage states (cookies/localStorage) — /v1/storage-states.
 *
 * Delegates to the generated `v1.storageStates` builders (collection get/post,
 * item get/delete/attach, and the top-level detach).
 */
export class StorageStatesClient {
    constructor(private readonly _v1: V1Builder) {}

    /** List saved storage states — GET /v1/storage-states. */
    async list(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.storageStates.get());
    }

    /** Create / capture a new storage state — POST /v1/storage-states. */
    async create(fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.storageStates.post(makeBody(fields)));
    }

    /** Get a storage state by id or name — GET /v1/storage-states/{id_or_name}. */
    async get(idOrName: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.storageStates.byId_or_name(idOrName).get());
    }

    /** Delete a storage state — DELETE /v1/storage-states/{id_or_name}. */
    async delete(idOrName: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.storageStates.byId_or_name(idOrName).delete());
    }

    /** Attach a storage state to a profile — POST /v1/storage-states/{id_or_name}/attach. */
    async attach(idOrName: string, options: { profileId: string }): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.storageStates.byId_or_name(idOrName).attach.post(makeBody({ profile_id: options.profileId })));
    }

    /** Detach the storage state from a profile — POST /v1/storage-states/detach. */
    async detach(options: { profileId: string }): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.storageStates.detach.post(makeBody({ profile_id: options.profileId })));
    }
}

/** Manage identity profiles — /v1/profiles */
export class ProfilesClient {
    constructor(private readonly _v1: V1Builder) {}

    /** List all profiles. Delegates to GET /v1/profiles. */
    async list(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.profiles.get());
    }

    /** Get a profile by name. Delegates to GET /v1/profiles/{name}. */
    async get(name: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.profiles.byName(name).get());
    }

    /** Create a profile. Delegates to POST /v1/profiles. */
    async create(name: string, config?: Record<string, unknown>): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.profiles.post(makeBody({ name, ...config })));
    }

    /** Update a profile. Delegates to PUT /v1/profiles/{name}. */
    async update(name: string, config: Record<string, unknown>): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.profiles.byName(name).put(makeBody(config)));
    }

    /** Delete a profile. Delegates to DELETE /v1/profiles/{name}. */
    async delete(name: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.profiles.byName(name).delete());
    }
}

/** Manage webhooks — /v1/webhooks */
export class WebhooksClient {
    constructor(private readonly _v1: V1Builder) {}

    async list(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.webhooks.get());
    }

    async get(webhookId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.webhooks.byWebhook_id(webhookId).get());
    }

    async create(options: { url: string; event_types?: string[]; events?: string[]; [key: string]: unknown }): Promise<Record<string, unknown>> {
        // The API field is `event_types`; `events` is accepted as a back-compat alias.
        const { events, ...rest } = options;
        const body = events !== undefined && rest.event_types === undefined ? { ...rest, event_types: events } : rest;
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.webhooks.post(makeBody(body as Record<string, unknown>)));
    }

    async delete(webhookId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.webhooks.byWebhook_id(webhookId).delete());
    }

    async rotateSecret(webhookId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.webhooks.byWebhook_id(webhookId).rotateSecret.post(null));
    }

    /**
     * List recent delivery attempts for a webhook — GET .../deliveries.
     * The delivery history (which events were sent, which failed and why) — the
     * input to {@link retryDelivery}.
     */
    async listDeliveries(webhookId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.webhooks.byWebhook_id(webhookId).deliveries.get());
    }

    /** Re-attempt a single failed delivery — POST .../deliveries/{id}/retry. */
    async retryDelivery(webhookId: string, deliveryId: string): Promise<Record<string, unknown>> {
        return callKiota(
            // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
            this._v1.webhooks.byWebhook_id(webhookId).deliveries.byDelivery_id(deliveryId).retry.post(null),
        );
    }
}

/** Manage schedules — /v1/schedules */
export class SchedulesClient {
    constructor(private readonly _v1: V1Builder) {}

    async list(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.schedules.get());
    }

    async get(scheduleId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.schedules.bySchedule_id(scheduleId).get());
    }

    /**
     * Create a schedule. Delegates to POST /v1/schedules.
     *
     * The API contract requires `name`, `job_type` ('scrape' | 'crawl' |
     * 'change_monitor'), `cron_expr` (5-field cron), and `job_params` (the full
     * scrape/crawl request body). This method maps the ergonomic `{ cron, task }`
     * input onto that contract:
     *   - `cron`  → `cron_expr`
     *   - `task.action` (or `task.job_type`) → `job_type`; the remaining `task`
     *     fields become `job_params` (or pass `task.job_params` explicitly)
     *   - `name`  → required; falls back to an auto-generated name
     * Explicit contract fields (`name`, `job_type`, `cron_expr`, `job_params`)
     * passed alongside always take precedence over the derived values.
     */
    async create(options: {
        cron: string;
        task: Record<string, unknown>;
        name?: string;
        [key: string]: unknown;
    }): Promise<Record<string, unknown>> {
        const { cron, task, name, ...rest } = options;
        const t = (task ?? {}) as Record<string, unknown>;
        const jobType = t.action ?? t.job_type ?? (rest as Record<string, unknown>).job_type;
        const { action: _a, job_type: _jt, job_params: _jp, ...taskParams } = t;
        const jobParams = (t.job_params as Record<string, unknown> | undefined) ?? taskParams;
        const body: Record<string, unknown> = {
            name: name ?? `schedule-${Date.now()}`,
            job_type: jobType,
            cron_expr: cron,
            job_params: jobParams,
            ...rest, // explicit contract fields win
        };
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.schedules.post(makeBody(body)));
    }

    async delete(scheduleId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.schedules.bySchedule_id(scheduleId).delete());
    }
}

/** Manage datasets — /v1/datasets */
export class DatasetsClient {
    /**
     * @param _v1 Kiota v1 request-builder proxy.
     * @param _rawPost Optional raw JSON POST transport injected by the parent
     *   client. Used by {@link append} to work around a Kiota untyped-`additionalData`
     *   serialization bug: Kiota's JSON writer emits invalid JSON for an array of
     *   objects (extra/trailing commas, e.g. `[{"a":1},,{"b":2},]`), so
     *   `datasets.append` — the only method that sends an array of objects — is
     *   routed through a plain `JSON.stringify` POST instead.
     */
    constructor(
        private readonly _v1: V1Builder,
        private readonly _rawPost?: (path: string, body: unknown) => Promise<unknown>,
    ) {}

    async list(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.datasets.get());
    }

    async get(name: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.datasets.byName(name).get());
    }

    async create(name: string, config?: Record<string, unknown>): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.datasets.post(makeBody({ name, ...config })));
    }

    async delete(name: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.datasets.byName(name).delete());
    }

    async rows(name: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.datasets.byName(name).rows.get());
    }

    async append(name: string, rows: unknown[]): Promise<Record<string, unknown>> {
        // Kiota's untyped-additionalData JSON writer serializes an array of
        // objects as malformed JSON (extra/trailing commas). Route the append
        // body through the raw JSON transport when the parent client provided
        // one — this is the ONLY method that ships an array of objects.
        if (this._rawPost) {
            const path = `/v1/datasets/${encodeURIComponent(name)}/rows/append`;
            return (await this._rawPost(path, { rows })) as Record<string, unknown>;
        }
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.datasets.byName(name).rows.append.post(makeBody({ rows })));
    }
}

/**
 * Live visual-recording lifecycle for one session — `recordings.visual`.
 *
 * Delegates to the generated `recordings.byRecording_Id(sessionId).visual`
 * builders (`start` / `stop` / `frames` + the manifest `get`). This is the
 * live-observability surface — watch your browser working in near real time.
 * The generated builders model an empty tenant body; it is ignored server-side
 * (the tenant comes from the Bearer token), so an empty `{}` body is sent.
 */
export class VisualRecordingClient {
    constructor(
        private readonly _v1: V1Builder,
        private readonly _sessionId: string,
    ) {}

    private _visual(): unknown {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-return
        return this._v1.recordings.byRecording_Id(this._sessionId).visual;
    }

    /** Start a visual recording for the live session — POST .../visual/start. */
    async start(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota((this._visual() as { start: { post: (b: unknown) => Promise<unknown> } }).start.post(makeBody({})));
    }

    /** Stop and finalise the visual recording — POST .../visual/stop. */
    async stop(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota((this._visual() as { stop: { post: (b: unknown) => Promise<unknown> } }).stop.post(makeBody({})));
    }

    /** Get the recording manifest pointer — GET .../visual. */
    async manifest(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota((this._visual() as { get: (b: unknown) => Promise<unknown> }).get(makeBody({})));
    }

    /**
     * List a page of frame references — GET .../visual/frames. Returns
     * `{ frames: string[], next_cursor: number, session_id: string }`;
     * `next_cursor === -1` means no more pages.
     */
    async frames(options: { cursor?: number; limit?: number } = {}): Promise<Record<string, unknown>> {
        const { cursor = 0, limit = 100 } = options;
        return callKiota(
            (this._visual() as {
                frames: { get: (b: unknown, cfg: unknown) => Promise<unknown> };
                // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
            }).frames.get(makeBody({}), { queryParameters: { cursor, limit } }),
        );
    }

    /**
     * Start recording and yield frame references as they are produced — a
     * convenience over `start` + repeated `frames` polling. Stops the recording
     * when iteration ends. Streaming is async:
     *
     * ```typescript
     * for await (const frameRef of client.recordings.visual(sessionId).watch()) {
     *   console.log(frameRef);
     * }
     * ```
     */
    async *watch(options: { intervalMs?: number; maxFrames?: number; autoStart?: boolean; autoStop?: boolean } = {}): AsyncGenerator<string> {
        const { intervalMs = 1000, maxFrames, autoStart = true, autoStop = true } = options;
        if (autoStart) await this.start();
        let seen = 0;
        let cursor = 0;
        try {
            for (;;) {
                const page = await this.frames({ cursor });
                const refs = (page.frames as string[] | undefined) ?? [];
                for (const ref of refs) {
                    yield ref;
                    seen += 1;
                    if (maxFrames !== undefined && seen >= maxFrames) return;
                }
                const nextCursor = page.next_cursor as number | undefined;
                if (typeof nextCursor === "number" && nextCursor >= 0) {
                    cursor = nextCursor;
                } else {
                    await new Promise((r) => setTimeout(r, intervalMs));
                }
            }
        } finally {
            if (autoStop) await this.stop();
        }
    }

    /** Alias for {@link watch} — the live-view frame stream. */
    liveView(options: { intervalMs?: number; maxFrames?: number; autoStart?: boolean; autoStop?: boolean } = {}): AsyncGenerator<string> {
        return this.watch(options);
    }
}

/** Manage session recordings — /v1/recordings */
export class RecordingsClient {
    constructor(private readonly _v1: V1Builder) {}

    async list(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.recordings.get());
    }

    async get(recordingId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.recordings.byRecording_Id(recordingId).get());
    }

    async delete(recordingId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.recordings.byRecording_Id(recordingId).delete());
    }

    /** Live visual-recording surface for `sessionId` (start/stop/frames/watch). */
    visual(sessionId: string): VisualRecordingClient {
        return new VisualRecordingClient(this._v1, sessionId);
    }

    /**
     * Convenience: start a live visual recording for `sessionId` and stream frame
     * references (see {@link VisualRecordingClient.watch}).
     */
    watch(sessionId: string, options: { intervalMs?: number; maxFrames?: number; autoStart?: boolean; autoStop?: boolean } = {}): AsyncGenerator<string> {
        return this.visual(sessionId).watch(options);
    }

    /** Alias for {@link watch} — the live-view frame stream for `sessionId`. */
    liveView(sessionId: string, options: { intervalMs?: number; maxFrames?: number; autoStart?: boolean; autoStop?: boolean } = {}): AsyncGenerator<string> {
        return this.visual(sessionId).watch(options);
    }
}

/** Key-value store — /v1/kv */
export class KVClient {
    constructor(private readonly _v1: V1Builder) {}

    async get(key: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.kv.byKey(key).get());
    }

    async set(key: string, value: unknown): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.kv.byKey(key).put(makeBody({ value })));
    }

    async delete(key: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.kv.byKey(key).delete());
    }
}

// ---------------------------------------------------------------------------
// Main facade
// ---------------------------------------------------------------------------

export interface GhostCrawlClientOptions {
    /** Your GhostCrawl API key (gck_live_...). Falls back to GHOSTCRAWL_API_KEY env var. */
    token?: string;
    /** Override the API base URL. Defaults to https://api.ghostcrawl.io. */
    baseUrl?: string;
    /**
     * Per-request timeout (milliseconds) for the raw-HTTP escape-hatch paths
     * (pdf/screenshot/content/search-wait/request). Defaults to 60000. A stalled
     * server aborts with a `GhostCrawlTimeoutError` instead of hanging the call.
     */
    timeoutMs?: number;
}

/**
 * GhostCrawl idiomatic API client.
 *
 * Delegates all HTTP transport, auth, serialization, and URL routing to the
 * Kiota-generated canonical core (_generated/). This client is the shipped API.
 *
 * @example
 * ```typescript
 * import { GhostCrawlClient, createGhostCrawlClient } from "@ghostcrawl/sdk";
 * const client = new GhostCrawlClient({ token: "gck_live_YOUR_KEY" });
 * // or: const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });
 * const result = await client.scrape({ url: "https://example.com" });
 * ```
 */
export class GhostCrawlClient {
    /** The Kiota v1 request builder proxy — canonical engine for all requests. */
    private readonly _v1: V1Builder;
    /** Bearer token + base URL retained for the generic raw request() escape hatch. */
    private readonly _token: string;
    private readonly _baseUrl: string;
    /** Per-request timeout (ms) for the raw-`fetch` escape-hatch paths. */
    private readonly _timeoutMs: number;

    private _crawlRuns?: CrawlRunsClient;
    private _sessions?: SessionsClient;
    private _profiles?: ProfilesClient;
    private _webhooks?: WebhooksClient;
    private _schedules?: SchedulesClient;
    private _datasets?: DatasetsClient;
    private _recordings?: RecordingsClient;
    private _kv?: KVClient;
    private _cdp?: CdpClient;
    private _page?: PageClient;
    private _downloads?: DownloadsClient;
    private _storageStates?: StorageStatesClient;

    constructor(options: GhostCrawlClientOptions = {}) {
        const token =
            options.token ??
            (typeof process !== "undefined" ? process.env.GHOSTCRAWL_API_KEY : undefined) ??
            readConfigValue("api_key");
        if (!token) {
            throw new Error(
                "token is required (or set GHOSTCRAWL_API_KEY, or run `ghostcrawl init`). " +
                    "Get your key at https://ghostcrawl.io.",
            );
        }
        const baseUrl = (
            options.baseUrl ??
            (typeof process !== "undefined" ? process.env.GHOSTCRAWL_BASE_URL : undefined) ??
            readConfigValue("base_url") ??
            DEFAULT_BASE_URL
        ).replace(/\/$/, "");

        this._token = token;
        this._baseUrl = baseUrl;
        this._timeoutMs = options.timeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS;
        this._v1 = buildV1Core(token, baseUrl);
    }

    // Sub-client getters
    get crawlRuns(): CrawlRunsClient {
        return (this._crawlRuns ??= new CrawlRunsClient(
            this._v1,
            (method, path, body) => this.request(method, path, body),
        ));
    }
    get sessions(): SessionsClient {
        return (this._sessions ??= new SessionsClient(
            this._v1,
            (method, path, body) => this.request(method, path, body),
        ));
    }
    get profiles(): ProfilesClient {
        return (this._profiles ??= new ProfilesClient(this._v1));
    }
    get webhooks(): WebhooksClient {
        return (this._webhooks ??= new WebhooksClient(this._v1));
    }
    get schedules(): SchedulesClient {
        return (this._schedules ??= new SchedulesClient(this._v1));
    }
    get datasets(): DatasetsClient {
        return (this._datasets ??= new DatasetsClient(
            this._v1,
            (path, body) => this.request("POST", path, body),
        ));
    }
    get recordings(): RecordingsClient {
        return (this._recordings ??= new RecordingsClient(this._v1));
    }
    get kv(): KVClient {
        return (this._kv ??= new KVClient(this._v1));
    }
    /** Low-level CDP primitives for a live session — /v1/cdp (first-class). */
    get cdp(): CdpClient {
        return (this._cdp ??= new CdpClient(
            this._v1,
            (method, path, body) => this.request(method, path, body),
        ));
    }
    /** High-level page primitives for a live session — /v1/page (first-class). */
    get page(): PageClient {
        return (this._page ??= new PageClient(this._v1));
    }
    /** Manage captured file downloads — /v1/downloads. */
    get downloads(): DownloadsClient {
        return (this._downloads ??= new DownloadsClient(
            (method, path, body) => this.request(method, path, body),
        ));
    }
    /** Manage reusable storage states (cookies/localStorage) — /v1/storage-states. */
    get storageStates(): StorageStatesClient {
        return (this._storageStates ??= new StorageStatesClient(this._v1));
    }

    /**
     * Scrape a single URL and return the rendered content.
     * Delegates to POST /v1/scrape via the generated ScrapeRequestBuilder.
     */
    async scrape(options: {
        url: string;
        format?: "markdown" | "html" | "text";
        engine?: "auto" | "chrome" | "firefox" | "webkit";
        javascript?: boolean;
        extractSchema?: Record<string, unknown>;
        [key: string]: unknown;
    }): Promise<ScrapeResult> {
        const { url, format = "markdown", engine = "auto", javascript = true, extractSchema, ...rest } = options;
        const fields: Record<string, unknown> = {
            url,
            format,
            engine,
            javascript_enabled: javascript,
            ...rest,
        };
        if (extractSchema) fields.extract_schema = extractSchema;
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        const result = await callKiota(this._v1.scrape.post(makeBody(fields)));
        return normalizeScrapeContent(result) as ScrapeResult;
    }

    /**
     * Search the web and return results.
     * Delegates to POST /v1/search via the generated SearchRequestBuilder.
     *
     * `/v1/search` requires your own search-backend API key (BYO; ghostcrawl
     * charges no markup). Pass it as `providerKey` — it is sent as the
     * `X-Provider-Authorization: Bearer <providerKey>` header the backend
     * requires. Without it the API replies `401 search_backend_key_missing`.
     */
    async search(options: {
        query: string;
        engine?: "google" | "bing" | "duckduckgo";
        limit?: number;
        providerKey?: string;
        /**
         * When true, block until the search job is terminal via an SDK-owned
         * BOUNDED client-side poll — you write zero poll code. A warm
         * rotation returns immediately (server `200`); a cold rotation returns
         * `202 running` with a `poll_url`, which this polls (honoring
         * `Retry-After` / the server `deadline`) to a terminal result. Default
         * false (back-compat: the raw single-shot response is returned).
         *
         * NOTE: `search` wait is a CLIENT-side bounded poll (the search-job
         * contract has no server `?wait=true`); `crawl` wait is a SERVER-side
         * long-poll. Same `wait` DX, different mechanism under the hood.
         */
        wait?: boolean;
        /** Overall client-side wait budget in seconds (`wait: true` only). */
        timeout?: number;
        [key: string]: unknown;
    }): Promise<SearchResult> {
        const { query, engine = "google", limit = 10, providerKey, wait = false, timeout, ...rest } = options;

        if (!wait) {
            // Back-compat single-shot path through the generated core.
            const config = providerKey
                ? { headers: { "X-Provider-Authorization": `Bearer ${providerKey}` } }
                : undefined;
            // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
            return finalizeSearch(await callKiota(this._v1.search.post(makeBody({ query, engine, limit, ...rest }), config)), query, engine);
        }

        // wait path: talk raw HTTP so we can read the 202 status + poll handle +
        // Retry-After the generated core hides. Warm 200 returns immediately.
        const headers: Record<string, string> = {
            Authorization: `Bearer ${this._token}`,
            "User-Agent": uaString(),
            Accept: "application/json",
            "Content-Type": "application/json",
        };
        if (providerKey) headers["X-Provider-Authorization"] = `Bearer ${providerKey}`;

        const res = await fetchWithTimeout(
            `${this._baseUrl}/v1/search`,
            {
                method: "POST",
                headers,
                body: JSON.stringify({ query, engine, limit, ...rest }),
            },
            this._timeoutMs,
        );
        if (res.status === 200) {
            return finalizeSearch(await parseJsonResponse<SearchResult>(res), query, engine);
        }
        if (res.status !== 202) {
            throw await httpErrorFromResponse(res);
        }
        // Cold path: 202 running with a poll handle.
        let job: Record<string, unknown> = {};
        try {
            job = (await res.json()) as Record<string, unknown>;
        } catch {
            job = {};
        }
        const terminal = await pollSearchJob(this._baseUrl, job, {
            headers,
            timeout,
            initialRetry: parseRetryAfter(res.headers.get("Retry-After")),
            errorFactory: httpErrorFromResponse,
        });
        return finalizeSearch(terminal, query, engine);
    }

    /**
     * Extract structured data from a URL using a JSON Schema.
     * Delegates to POST /v1/extract via the generated ExtractRequestBuilder.
     */
    async extract(options: {
        url: string;
        schema: Record<string, unknown>;
        [key: string]: unknown;
    }): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.extract.post(makeBody(options as Record<string, unknown>)));
    }

    /**
     * Start a deep crawl from a seed URL.
     * Delegates to POST /v1/crawl/deep via the generated DeepRequestBuilder.
     */
    async crawl(options: {
        url: string;
        maxDepth?: number;
        maxPages?: number;
        [key: string]: unknown;
    }): Promise<CrawlRun> {
        const { url, maxDepth = 2, maxPages = 100, ...rest } = options;
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return (await callKiota(this._v1.crawl.deep.post(makeBody({ seed_urls: [url], max_depth: maxDepth, max_urls: maxPages, ...rest })))) as CrawlRun;
    }

    /**
     * Map all URLs reachable from a seed URL.
     * Delegates to POST /v1/map via the generated MapRequestBuilder.
     */
    async map(options: { url: string; [key: string]: unknown }): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.map.post(makeBody(options as Record<string, unknown>)));
    }

    /**
     * Run an autonomous agent task. Delegates to POST /v1/agent. Parity with the
     * Python SDK's `agent()`. Note: the agent endpoint may be unavailable (404)
     * on a given deployment; callers should handle that status.
     */
    async agent(options: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        return (await this.request("POST", "/v1/agent", options)) as Record<string, unknown>;
    }

    /**
     * Render a URL to a PDF document and return the raw PDF bytes.
     * Delegates to POST /v1/pdf.
     *
     * Unlike the JSON endpoints, `/v1/pdf` responds with `application/pdf` binary
     * — so this bypasses the JSON transport and returns the bytes as a
     * `Uint8Array` you can write straight to disk:
     *
     * ```typescript
     * import { writeFileSync } from "node:fs";
     * const pdf = await client.pdf({ url: "https://example.com" });
     * writeFileSync("page.pdf", pdf);
     * ```
     *
     * PDF output is Chrome-only; a request that resolves to a Firefox or WebKit
     * identity is rejected with a 400 `pdf_engine_unsupported` (thrown as an
     * `Error` carrying `statusCode`).
     */
    async pdf(options: {
        url: string;
        paperFormat?: "a4" | "letter" | "legal" | "tabloid";
        landscape?: boolean;
        engine?: "auto" | "chrome" | "firefox" | "webkit";
        [key: string]: unknown;
    }): Promise<Uint8Array> {
        const { url, paperFormat = "a4", landscape = false, engine = "auto", ...rest } = options;
        const body = { url, paper_format: paperFormat, landscape, engine, ...rest };
        const res = await fetchWithTimeout(
            `${this._baseUrl}/v1/pdf`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${this._token}`,
                    "User-Agent": uaString(),
                    "Content-Type": "application/json",
                    Accept: "application/pdf",
                },
                body: JSON.stringify(body),
            },
            this._timeoutMs,
        );
        if (!res.ok) {
            throw await httpErrorFromResponse(res);
        }
        return new Uint8Array(await res.arrayBuffer());
    }

    /**
     * Capture a screenshot of a URL and return the raw image bytes.
     * Delegates to POST /v1/screenshot. Parity with the Python SDK's
     * `screenshot()`, and mirrors {@link pdf} exactly — the route serves binary
     * image data (not a modeled JSON envelope), so this bypasses the JSON
     * transport and returns the bytes as a `Uint8Array` you can write straight
     * to disk:
     *
     * ```typescript
     * import { writeFileSync } from "node:fs";
     * const png = await client.screenshot({ url: "https://example.com" });
     * writeFileSync("page.png", png);
     * ```
     *
     * `format` (png | jpeg | webp), `full_page`, and `screenshot_selector`
     * (a CSS selector scoping the capture to one element) are passed through
     * verbatim.
     */
    async screenshot(options: {
        url: string;
        format?: string;
        full_page?: boolean;
        screenshot_selector?: string;
        engine?: string;
        [key: string]: unknown;
    }): Promise<Uint8Array> {
        const res = await fetchWithTimeout(
            `${this._baseUrl}/v1/screenshot`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${this._token}`,
                    "User-Agent": uaString(),
                    "Content-Type": "application/json",
                    Accept: "image/png",
                },
                body: JSON.stringify(options),
            },
            this._timeoutMs,
        );
        if (!res.ok) {
            throw await httpErrorFromResponse(res);
        }
        return new Uint8Array(await res.arrayBuffer());
    }

    /**
     * Fetch the rendered content of a URL and return it as a parsed JSON object.
     * Delegates to POST /v1/content. Parity with the Python SDK's `content()`.
     * Mirrors {@link pdf}'s dispatch (Bearer auth + branded User-Agent + the same
     * error-envelope shape) but the route serves a JSON body, so this returns
     * the parsed rendered-content envelope.
     */
    async content(options: {
        url: string;
        engine?: string;
        [key: string]: unknown;
    }): Promise<ScrapeResult> {
        const res = await fetchWithTimeout(
            `${this._baseUrl}/v1/content`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${this._token}`,
                    "User-Agent": uaString(),
                    "Content-Type": "application/json",
                    Accept: "application/json",
                },
                body: JSON.stringify(options),
            },
            this._timeoutMs,
        );
        if (!res.ok) {
            throw await httpErrorFromResponse(res);
        }
        return await parseJsonResponse<ScrapeResult>(res);
    }

    /**
     * Scrape many URLs in one request — POST /v1/scrape/batch.
     * Delegates to the generated `v1.scrape.batch` builder. `urls` is the list of
     * URLs; any extra fields (format, engine, javascript_enabled, …) are shared
     * across the batch.
     */
    async scrapeBatch(urls: string[], fields: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.scrape.batch.post(makeBody({ urls, ...fields })));
    }

    /**
     * Poll a queued async search job to its terminal state —
     * GET /v1/search/jobs/{job_id}. The generated core has no `search.jobs`
     * builder (the route is absent from the customer-facing OpenAPI), so this is
     * routed through the shared authenticated `request()` transport — no
     * hand-rolled HTTP client (matches me()/usage()). Prefer `search({ wait: true })`
     * for the fully managed poll.
     */
    async searchJob(jobId: string): Promise<SearchResult> {
        // Same stable-shape normalization as search() — the terminal job payload
        // carries hits under `items`; without this `.results` is undefined. No
        // caller query is known here, so only `results` is guaranteed non-null.
        return finalizeSearch(await this.request("GET", `/v1/search/jobs/${encodeURIComponent(jobId)}`));
    }

    /**
     * Get the current status of a deep-crawl run — GET /v1/crawl/deep/{run_id}.
     * Delegates to the generated `v1.crawl.deep.byRun_id` builder. Returns the run
     * record (status + progress + results when terminal).
     */
    async crawlStatus(runId: string): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.crawl.deep.byRun_id(runId).get());
    }

    /**
     * Return the caller's account profile — GET /v1/me.
     *
     * The identity behind your API key: user, primary team, and tier. Routed
     * through the same authenticated `request()` path the other typed methods use
     * (Bearer token + base URL + branded User-Agent). The route is real and
     * in-schema but pruned from the published spec, so it has no generated builder.
     */
    async me(): Promise<Record<string, unknown>> {
        return (await this.request("GET", "/v1/me")) as Record<string, unknown>;
    }

    /**
     * Return the caller's usage + quota report — GET /v1/me/usage.
     *
     * The quota-visibility surface: cost/usage for the current billing window plus
     * the prepaid wallet balance, scoped to your team. `period` is one of `"day"`
     * (server default), `"week"`, or `"month"`.
     */
    async usage(options: { period?: "day" | "week" | "month" } = {}): Promise<Record<string, unknown>> {
        const path = options.period
            ? `/v1/me/usage?period=${encodeURIComponent(options.period)}`
            : "/v1/me/usage";
        return (await this.request("GET", path)) as Record<string, unknown>;
    }

    /**
     * Return the customer-safe persona for a running session — GET
     * /v1/me/identities/{session_id}/persona.
     *
     * Who a given session *is*, shaped for display: a whitelist of `device_class`
     * / `os_class` / `browser_class` / `locale` only — never a raw user-agent or
     * any internal detail. Session-scoped, so each session reports its own persona
     * distinct from the account-level entitlements on `me()`. An unknown session
     * raises a not-found error (same anti-enumeration shape as the rest of /v1/me).
     */
    async sessionPersona(sessionId: string): Promise<Record<string, unknown>> {
        return (await this.request(
            "GET",
            `/v1/me/identities/${encodeURIComponent(sessionId)}/persona`,
        )) as Record<string, unknown>;
    }

    /**
     * Generic authenticated request escape hatch for endpoints not surfaced as a
     * typed method. Applies the same Bearer token, base URL, and branded
     * User-Agent as the modeled calls.
     *
     * Returns the parsed JSON body on a 2xx response. On a non-2xx response it
     * throws an `Error` carrying a numeric `statusCode` property (and the parsed
     * `body` when JSON) so callers can route by HTTP status. JSON request bodies
     * are sent with `Content-Type: application/json`; an absent `body` sends no
     * payload.
     *
     * This is the low-level door; prefer the typed methods (scrape, map, extract,
     * crawlRuns, sessions, …) when one exists for the endpoint.
     */
    async request(
        method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH",
        path: string,
        body?: unknown,
    ): Promise<unknown> {
        const url = path.startsWith("http")
            ? path
            : `${this._baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
        const headers: Record<string, string> = {
            Authorization: `Bearer ${this._token}`,
            "User-Agent": uaString(),
        };
        const init: RequestInit = { method, headers };
        if (body !== undefined) {
            headers["Content-Type"] = "application/json";
            init.body = JSON.stringify(body);
        }
        const res = await fetchWithTimeout(url, init, this._timeoutMs);
        if (!res.ok) {
            throw await httpErrorFromResponse(res);
        }
        const text = await res.text();
        if (!text) return undefined;
        try {
            return JSON.parse(text) as unknown;
        } catch (err) {
            throw new GhostCrawlError({
                message: `GhostCrawl returned a response body that could not be parsed as JSON (HTTP ${res.status.toString()}).`,
                statusCode: res.status,
                body: text,
                cause: err,
            });
        }
    }
}

/**
 * Backwards-compatible alias for {@link GhostCrawlClient}. The client class was
 * formerly named `GhostCrawlFacadeClient`; the canonical name is now
 * `GhostCrawlClient`. This alias is retained so existing imports keep working.
 */
export { GhostCrawlClient as GhostCrawlFacadeClient };

/**
 * Convenience factory for the GhostCrawl client.
 *
 * @example
 * ```typescript
 * import { createGhostCrawlClient } from "@ghostcrawl/sdk";
 * const client = createGhostCrawlClient({ token: "gck_live_YOUR_KEY" });
 * const result = await client.scrape({ url: "https://example.com" });
 * ```
 */
export function createGhostCrawlClient(options: GhostCrawlClientOptions = {}): GhostCrawlClient {
    return new GhostCrawlClient(options);
}

/**
 * Zero-config convenience constructor — parity with the Python SDK's
 * `from ghostcrawl import Client; Client()`.
 *
 * Resolution: explicit `apiKey` arg wins, else `GHOSTCRAWL_API_KEY`, else throw
 * a clear Error naming the env var (never construct unauthenticated). `baseUrl`
 * falls back to `GHOSTCRAWL_BASE_URL`, then the canonical SaaS endpoint.
 */
export function createClient(apiKey?: string, opts?: { baseUrl?: string }): GhostCrawlClient {
    const key =
        apiKey ??
        (typeof process !== "undefined" ? process.env.GHOSTCRAWL_API_KEY : undefined) ??
        readConfigValue("api_key");
    if (!key) {
        throw new Error("api_key is required (or set GHOSTCRAWL_API_KEY, or run `ghostcrawl init`).");
    }
    const baseUrl =
        opts?.baseUrl ??
        (typeof process !== "undefined" ? process.env.GHOSTCRAWL_BASE_URL : undefined) ??
        readConfigValue("base_url");
    return new GhostCrawlClient({ token: key, ...(baseUrl ? { baseUrl } : {}) });
}

/**
 * `Client` alias for parity with the Python SDK (`from ghostcrawl import Client`).
 * Re-export of {@link GhostCrawlClient} — preserves `instanceof` semantics.
 */
export { GhostCrawlClient as Client };
