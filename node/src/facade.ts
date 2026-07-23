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
import { translateKiotaError, scanResultError } from "./errors.js";
// Branded User-Agent (ghostcrawl-node/<version> Node/<v> <os>/<arch>). Applied to
// the generic raw request() escape hatch so unmodeled endpoints carry the same
// UA the modeled (Kiota) requests do.
import { uaString } from "./branded.js";
// Timeout error raised when a wait()/start({wait:true}) call exceeds the caller
// deadline without the run reaching a terminal state.
import { GhostCrawlTimeoutError } from "./errors.js";

const DEFAULT_BASE_URL = "https://api.ghostcrawl.io";

/** Small async sleep — used ONLY for transient-error backoff, never for polling. */
const sleep = (ms: number): Promise<void> => new Promise((r) => setTimeout(r, ms));

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
}

/** Manage browser sessions — /v1/sessions */
export class SessionsClient {
    constructor(private readonly _v1: V1Builder) {}

    /** List all active sessions. Delegates to GET /v1/sessions. */
    async list(): Promise<Record<string, unknown>> {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.get());
    }

    /** Create a new browser session. Delegates to POST /v1/sessions/create. */
    async create(options: { profileName: string; [key: string]: unknown }): Promise<Record<string, unknown>> {
        const { profileName, ...rest } = options;
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.sessions.create.post(makeBody({ profile: profileName, ...rest })));
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

    private _crawlRuns?: CrawlRunsClient;
    private _sessions?: SessionsClient;
    private _profiles?: ProfilesClient;
    private _webhooks?: WebhooksClient;
    private _schedules?: SchedulesClient;
    private _datasets?: DatasetsClient;
    private _recordings?: RecordingsClient;
    private _kv?: KVClient;

    constructor(options: GhostCrawlClientOptions = {}) {
        const token = options.token ?? (typeof process !== "undefined" ? process.env.GHOSTCRAWL_API_KEY : undefined);
        if (!token) {
            throw new Error("token is required (or set GHOSTCRAWL_API_KEY). Get your key at https://ghostcrawl.io.");
        }
        const baseUrl = (
            options.baseUrl ??
            (typeof process !== "undefined" ? process.env.GHOSTCRAWL_BASE_URL : undefined) ??
            DEFAULT_BASE_URL
        ).replace(/\/$/, "");

        this._token = token;
        this._baseUrl = baseUrl;
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
        return (this._sessions ??= new SessionsClient(this._v1));
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
    }): Promise<Record<string, unknown>> {
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
        return normalizeScrapeContent(result);
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
        [key: string]: unknown;
    }): Promise<Record<string, unknown>> {
        const { query, engine = "google", limit = 10, providerKey, ...rest } = options;
        const config = providerKey
            ? { headers: { "X-Provider-Authorization": `Bearer ${providerKey}` } }
            : undefined;
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.search.post(makeBody({ query, engine, limit, ...rest }), config));
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
    }): Promise<Record<string, unknown>> {
        const { url, maxDepth = 2, maxPages = 100, ...rest } = options;
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        return callKiota(this._v1.crawl.deep.post(makeBody({ seed_urls: [url], max_depth: maxDepth, max_urls: maxPages, ...rest })));
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
        const res = await fetch(`${this._baseUrl}/v1/pdf`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${this._token}`,
                "User-Agent": uaString(),
                "Content-Type": "application/json",
                Accept: "application/pdf",
            },
            body: JSON.stringify(body),
        });
        if (!res.ok) {
            const text = await res.text();
            let parsed: unknown = text;
            if (text) {
                try {
                    parsed = JSON.parse(text);
                } catch {
                    /* leave as raw text */
                }
            }
            const err = new Error(
                `Status code: ${res.status}` +
                    (typeof parsed === "string" ? `\nBody: ${parsed}` : `\nBody: ${JSON.stringify(parsed)}`),
            ) as Error & { statusCode: number; body?: unknown };
            err.statusCode = res.status;
            if (typeof parsed !== "string") err.body = parsed;
            throw err;
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
        const res = await fetch(`${this._baseUrl}/v1/screenshot`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${this._token}`,
                "User-Agent": uaString(),
                "Content-Type": "application/json",
                Accept: "image/png",
            },
            body: JSON.stringify(options),
        });
        if (!res.ok) {
            const text = await res.text();
            let parsed: unknown = text;
            if (text) {
                try {
                    parsed = JSON.parse(text);
                } catch {
                    /* leave as raw text */
                }
            }
            const err = new Error(
                `Status code: ${res.status}` +
                    (typeof parsed === "string" ? `\nBody: ${parsed}` : `\nBody: ${JSON.stringify(parsed)}`),
            ) as Error & { statusCode: number; body?: unknown };
            err.statusCode = res.status;
            if (typeof parsed !== "string") err.body = parsed;
            throw err;
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
    }): Promise<Record<string, unknown>> {
        const res = await fetch(`${this._baseUrl}/v1/content`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${this._token}`,
                "User-Agent": uaString(),
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: JSON.stringify(options),
        });
        if (!res.ok) {
            const text = await res.text();
            let parsed: unknown = text;
            if (text) {
                try {
                    parsed = JSON.parse(text);
                } catch {
                    /* leave as raw text */
                }
            }
            const err = new Error(
                `Status code: ${res.status}` +
                    (typeof parsed === "string" ? `\nBody: ${parsed}` : `\nBody: ${JSON.stringify(parsed)}`),
            ) as Error & { statusCode: number; body?: unknown };
            err.statusCode = res.status;
            if (typeof parsed !== "string") err.body = parsed;
            throw err;
        }
        return (await res.json()) as Record<string, unknown>;
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
        const res = await fetch(url, init);
        const text = await res.text();
        let parsed: unknown = text;
        if (text) {
            try {
                parsed = JSON.parse(text);
            } catch {
                /* leave as raw text */
            }
        }
        if (!res.ok) {
            const err = new Error(
                `Status code: ${res.status}` +
                    (typeof parsed === "string"
                        ? `\nBody: ${parsed}`
                        : `\nBody: ${JSON.stringify(parsed)}`),
            ) as Error & { statusCode: number; body?: unknown };
            err.statusCode = res.status;
            if (typeof parsed !== "string") err.body = parsed;
            throw err;
        }
        return parsed;
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
    const key = apiKey ?? (typeof process !== "undefined" ? process.env.GHOSTCRAWL_API_KEY : undefined);
    if (!key) {
        throw new Error("api_key is required (or set GHOSTCRAWL_API_KEY).");
    }
    const baseUrl =
        opts?.baseUrl ?? (typeof process !== "undefined" ? process.env.GHOSTCRAWL_BASE_URL : undefined);
    return new GhostCrawlClient({ token: key, ...(baseUrl ? { baseUrl } : {}) });
}

/**
 * `Client` alias for parity with the Python SDK (`from ghostcrawl import Client`).
 * Re-export of {@link GhostCrawlClient} — preserves `instanceof` semantics.
 */
export { GhostCrawlClient as Client };
