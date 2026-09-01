/**
 * SDK-owned bounded client-side poll for `search({ wait: true })`.
 *
 * Unlike `crawl` — whose `GET /v1/crawl-runs/{id}?wait=true&timeout_s=N` blocks
 * SERVER-side on a completion event — the search-job contract is a CLIENT poll:
 * `POST /v1/search` on a cold rotation returns
 * `202 { status: "running", poll_url, deadline, poll_max_seconds,
 * poll_terminal_on_404 }`, and `GET {poll_url}` returns `202 running` (with a
 * `Retry-After` header) until a terminal `200`. The SDK owns the loop so the
 * user writes zero poll code — same `wait: true` DX, different mechanism under
 * the hood.
 *
 * This is an INTERNAL module (never exported from the package index). It mirrors
 * the structure of the Python reference `_search_poll.py` and is unit-testable
 * in isolation from the Kiota generated core (it talks plain `fetch`).
 */

/** Terminal search-job states (mirrors the Python `SEARCH_TERMINAL_STATES`). */
export const SEARCH_TERMINAL_STATES: ReadonlySet<string> = new Set([
    "completed",
    "done",
    "failed",
    "cancelled",
    "error",
]);

/** Overall client-side wait budget (seconds) when the server gives no bound. */
export const DEFAULT_SEARCH_TIMEOUT = 300;
/** Fallback inter-poll interval (seconds) when the server sends no Retry-After. */
export const DEFAULT_SEARCH_POLL_INTERVAL = 3;

/** True when a search-job record has reached a terminal state. */
export function searchIsTerminal(job: unknown): boolean {
    return (
        job !== null &&
        typeof job === "object" &&
        SEARCH_TERMINAL_STATES.has(String((job as Record<string, unknown>).status ?? ""))
    );
}

/** Parse a Retry-After header value (delta-seconds) to a number >= 0, or undefined. */
export function parseRetryAfter(raw: string | null | undefined): number | undefined {
    if (raw === null || raw === undefined) return undefined;
    const n = Number(raw);
    if (Number.isFinite(n)) return Math.max(0, n);
    return undefined;
}

export interface SearchPollOptions {
    /** Auth + accept headers to send on every poll GET. */
    headers: Record<string, string>;
    /** Overall client-side wait budget (seconds). Overrides the server's bound. */
    timeout?: number;
    /** Retry-After (seconds) advertised on the initial 202. */
    initialRetry?: number;
    /** Maps a non-2xx poll response onto the caller's typed error. */
    errorFactory: (res: Response) => Promise<Error> | Error;
    /** Injectable fetch (tests). Defaults to globalThis.fetch. */
    fetchImpl?: typeof fetch;
    /** Injectable sleep (tests). Defaults to setTimeout. */
    sleepImpl?: (ms: number) => Promise<void>;
}

const defaultSleep = (ms: number): Promise<void> => new Promise((r) => setTimeout(r, ms));

/**
 * Bounded client-side poll of a cold search job to a terminal result.
 *
 * Copies the STRUCTURE of `CrawlRunsClient.wait` (deadline + re-arm loop) but
 * implements the client-poll contract: follows `poll_url` from the 202 body
 * (absolute or base-relative), honors `Retry-After` between polls bounded by
 * `poll_max_seconds` / explicit `timeout` / `DEFAULT_SEARCH_TIMEOUT`, treats a
 * terminal `200` (or a terminal-status body) as done, treats `404` as terminal
 * when `poll_terminal_on_404` (default true), and returns the latest
 * non-terminal record if the deadline elapses first.
 */
export async function pollSearchJob(
    baseUrl: string,
    job: Record<string, unknown>,
    opts: SearchPollOptions,
): Promise<Record<string, unknown>> {
    const fetchImpl = opts.fetchImpl ?? fetch;
    const sleep = opts.sleepImpl ?? defaultSleep;

    const pollUrlRaw = job.poll_url;
    if (typeof pollUrlRaw !== "string" || pollUrlRaw.length === 0) {
        // No poll handle — nothing to poll; the 202 body is all we have.
        return job;
    }
    const url = /^https?:\/\//.test(pollUrlRaw)
        ? pollUrlRaw
        : `${baseUrl.replace(/\/$/, "")}/${pollUrlRaw.replace(/^\//, "")}`;

    const pollMax = job.poll_max_seconds;
    const terminalOn404 = job.poll_terminal_on_404 !== false;

    let budgetS: number;
    if (typeof opts.timeout === "number") {
        budgetS = opts.timeout;
    } else if (typeof pollMax === "number") {
        budgetS = pollMax;
    } else {
        budgetS = DEFAULT_SEARCH_TIMEOUT;
    }
    const deadline = Date.now() + budgetS * 1000;

    let retryAfter = opts.initialRetry;
    let latest: Record<string, unknown> = job;

    for (;;) {
        const remainingMs = deadline - Date.now();
        if (remainingMs <= 0) return latest;

        const waitS = retryAfter ?? DEFAULT_SEARCH_POLL_INTERVAL;
        const waitMs = Math.max(0, Math.min(waitS * 1000, remainingMs));
        if (waitMs > 0) {
            await sleep(waitMs);
            if (Date.now() >= deadline) return latest;
        }

        const res = await fetchImpl(url, { method: "GET", headers: { ...opts.headers } });
        if (res.status === 404) {
            if (terminalOn404) throw await opts.errorFactory(res);
            return latest;
        }
        if (res.status >= 400) throw await opts.errorFactory(res);

        let data: Record<string, unknown> = {};
        try {
            data = (await res.json()) as Record<string, unknown>;
        } catch {
            data = {};
        }
        if (res.status === 200 || searchIsTerminal(data)) {
            return data;
        }
        // Still running (202) — re-arm with the server's next Retry-After.
        if (data && Object.keys(data).length > 0) latest = data;
        retryAfter = parseRetryAfter(res.headers.get("Retry-After"));
    }
}
