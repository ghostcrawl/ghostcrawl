// Idiomatic Kiota-only client surface.
//
// `GhostCrawlClient` is the idiomatic facade over the Kiota-generated canonical
// core (src/_generated/). `createGhostCrawlClient` / `createClient` are factory
// helpers, and `Client` is a Python-parity alias. All HTTP transport, auth,
// serialization, and URL routing come from the generated core; this package
// ships no hand-forked transport runtime.
export {
    GhostCrawlClient,
    GhostCrawlFacadeClient,
    createGhostCrawlClient,
    createClient,
    Client,
    CrawlRunsClient,
    CRAWL_TERMINAL_STATES,
    SessionsClient,
    ProfilesClient,
    WebhooksClient,
    SchedulesClient,
    DatasetsClient,
    RecordingsClient,
    KVClient,
} from "./facade.js";
export type { GhostCrawlClientOptions, CrawlWaitOptions, CrawlStartOptions } from "./facade.js";
// Base + timeout error classes (self-contained; defined in src/errors.ts).
export { GhostCrawlError, GhostCrawlTimeoutError } from "./errors.js";
// Domain error set (the ONE canonical surface) + status-code/code classifier +
// the result-scan / Kiota-translate helpers the facade wires in.
export {
    GhostCrawlAuthError,
    GhostCrawlQuotaError,
    GhostCrawlRateLimitError,
    GhostCrawlInvalidRequestError,
    GhostCrawlServerError,
    GhostCrawlScrapeError,
    classifyHttpError,
    translateKiotaError,
    scanResultError,
} from "./errors.js";
export type { GhostCrawlErrorInit } from "./errors.js";
// Canonical error-code catalog (mirror of the server's codes.json single source
// of truth). Re-exported so callers can branch on stable code strings.
export {
    ERROR_CODES,
    ALL_CODES,
    RESULT_CODES,
    PROBLEM_CODES,
    STATUS_TO_CODE,
    isRetryable,
} from "./errorCodes.js";
export type { ErrorChannel, ErrorCodeMeta } from "./errorCodes.js";
export * from "./exports.js";
// Hand-written MCP wrapper.
export { GhostCrawlMCPClient } from "./mcp/index.js";
export type { GhostCrawlMCPClientOptions } from "./mcp/index.js";
