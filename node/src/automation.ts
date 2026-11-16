/**
 * Playwright / Puppeteer adapters for GhostCrawl browser sessions.
 *
 * These helpers mint a session, resolve its connect endpoint, and return the string your
 * own client library already understands — no engine fork, no local browser download, no
 * monkey-patching.
 *
 * Protocols:
 * - chromium → Chrome CDP (`protocol: "cdp"`). Works with
 *   `puppeteer.connect({ browserWSEndpoint })` and `chromium.connectOverCDP(url)`.
 * - firefox / webkit → Playwright-wire (`protocol: "playwright-wire"`). Works with
 *   `playwright.firefox.connect(url)` / `playwright.webkit.connect(url)`.
 *
 * `puppeteer-core` speaks Chrome CDP only and cannot attach to a Firefox or WebKit
 * session. Each adapter checks the protocol it was handed and throws on a mismatch, so
 * the wrong client library cannot be attached by accident.
 *
 * Two rules this module enforces:
 * 1. **`locale` / `timezone` are accepted but ignored as CDP overrides.** Both are
 *    emulation knobs and are detectably different from a real device in that locale.
 *    They are delivered through the identity request instead.
 * 2. **No leaking default launch args.** `--enable-automation` and
 *    `--enable-unsafe-swiftshader` must never reach a final argv.
 */

/** The HTTP verbs the GhostCrawl client's raw transport accepts. */
export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";

/**
 * The subset of our client this module needs (structurally typed — no import cycle).
 *
 * `method` is the same literal union the client's `request()` exposes, so
 * `chromium.connect(client, …)` type-checks directly against a real
 * `GhostCrawlClient` instead of needing a cast.
 */
export interface CdpMintSource {
    /** POST /v1/cdp/url — mints a short-TTL signed WS URL for a live session. */
    request: (method: HttpMethod, path: string, body?: unknown) => Promise<unknown>;
}

/** Options accepted by {@link connect}. */
export interface GhostCrawlConnectOptions {
    /** Reuse an existing live session instead of minting one. */
    sessionId?: string;
    /** Claim OS for the identity (windows | macos | linux | android | ios). */
    claimOs?: string;
    /** Claim browser for the identity (chrome | firefox | safari | ...). */
    claimBrowser?: string;
    /** Force engine when known (chromium | firefox | webkit). Overrides claim routing. */
    engine?: "chromium" | "firefox" | "webkit";
    /** Route the session's acts through the human layer. */
    humanize?: boolean;
    /**
     * Timezone. ACCEPTED — but delivered through the identity request, never as a CDP
     * `setTimezoneOverride`. See {@link assertNoEmulationOverrides}.
     */
    timezone?: string;
    /**
     * Locale. ACCEPTED — but delivered through the identity request, never as a CDP
     * `setLocaleOverride`. See {@link assertNoEmulationOverrides}.
     */
    locale?: string;
    /** Proxy string, e.g. `http://user:pass@host:port`. */ // pragma: allowlist secret (doc example, not a credential)
    proxy?: string;
}

/** What {@link connect} resolves to. */
export interface GhostCrawlConnection {
    /**
     * Hand this to the matching client:
     * - protocol=cdp → `puppeteer.connect` / `chromium.connectOverCDP`
     * - protocol=playwright-wire → `playwright.firefox.connect` / `playwright.webkit.connect`
     */
    browserWSEndpoint: string;
    /** Alias for Playwright wire clients that prefer `wsEndpoint`. */
    wsEndpoint: string;
    sessionId: string;
    /** Which engine the session was routed to (chromium | firefox | webkit). */
    engine: string;
    /** Protocol discriminator returned by `/v1/cdp/url`. */
    protocol: "cdp" | "playwright-wire";
    /** Seconds until the minted URL expires — reconnect before this. */
    expiresIn: number;
    /** Release the underlying session. */
    close: () => Promise<void>;
}

const ENGINE_FOR_CLAIM: Record<string, string> = {
    // iOS is WebKit-mandated (Apple). Desktop claim_os alone does NOT force webkit —
    // claim_browser chrome on macos is chromium. Prefer explicit `engine` / claimBrowser.
    ios: "webkit",
    android: "chromium",
    windows: "chromium",
    linux: "chromium",
    macos: "chromium",
};

/**
 * Warn-and-ignore the two detectable CDP emulation knobs.
 *
 * Called by every `connect` so the behavior is impossible to opt out of by accident. Returns the
 * list of ignored keys (empty when none were passed) so a caller can surface it in its own logs.
 */
export function assertNoEmulationOverrides(options: Partial<GhostCrawlConnectOptions>): string[] {
    const ignored: string[] = [];
    for (const key of ["locale", "timezone"] as const) {
        const value = options[key];
        if (value !== undefined && value !== null && value !== "") {
            ignored.push(key);
            // eslint-disable-next-line no-console -- a silent ignore is worse than a noisy one
            console.warn(
                `[ghostcrawl] contextOptions.${key} is CDP emulation and is detectable — ` +
                    `ignored here. Pass ${key} on the identity/launch request instead; the engine ` +
                    `stamps it coherently across UA, Intl, Accept-Language and TZ.`,
            );
        }
    }
    return ignored;
}

/**
 * Assert a final argv carries neither webdriver tell. Throws rather than shipping a leaking argv.
 */
export function assertNoAutomationTells(argv: readonly string[]): void {
    for (const flag of ["--enable-automation", "--enable-unsafe-swiftshader"]) {
        if (argv.includes(flag)) {
            throw new Error(
                `refusing to launch: ${flag} is present in argv — it is a detectable automation ` +
                    `tell. Strip it (effective_chromium_ignore_default_args) before connecting.`,
            );
        }
    }
}

/** Resolve the engine a claim routes to. */
export function engineForClaim(claimOs?: string, claimBrowser?: string): string {
    const browser = String(claimBrowser || "").toLowerCase();
    if (browser === "firefox" || browser === "fxios") return "firefox";
    if (browser === "safari" || browser === "webkit") return "webkit";
    if (browser === "chrome" || browser === "crios" || browser === "chromium") {
        // iOS Chrome is still WebKit (Apple mandate).
        if (String(claimOs || "").toLowerCase() === "ios") return "webkit";
        return "chromium";
    }
    if (!claimOs) return "chromium";
    return ENGINE_FOR_CLAIM[String(claimOs).toLowerCase()] ?? "chromium";
}

type MintedUrl = {
    url?: string;
    expires_in_seconds?: number;
    engine?: string;
    protocol?: string;
    cdp_relay?: boolean;
    playwright_wire?: boolean;
    client_hint?: string;
};

async function mintConnection(
    source: CdpMintSource,
    options: GhostCrawlConnectOptions,
    expectedEngine: "chromium" | "firefox" | "webkit",
): Promise<GhostCrawlConnection> {
    assertNoEmulationOverrides(options);

    let sessionId = options.sessionId;
    if (!sessionId) {
        const created = (await source.request("POST", "/v1/sessions/create", {
            claim_os: options.claimOs,
            claim_browser: options.claimBrowser,
            engine: options.engine ?? expectedEngine,
            humanize: options.humanize,
            timezone: options.timezone,
            locale: options.locale,
            proxy: options.proxy,
        })) as { session_id?: string; id?: string } | undefined;
        sessionId = created?.session_id ?? created?.id;
        if (!sessionId) {
            throw new Error("session create returned no session_id");
        }
    }

    const minted = (await source.request("POST", "/v1/cdp/url", {
        session_id: sessionId,
    })) as MintedUrl;
    if (!minted?.url) {
        throw new Error(
            "cdp/url returned no url — is the session live and BYO connect enabled for this org?",
        );
    }

    const engine = String(minted.engine || expectedEngine);
    const protocol: "cdp" | "playwright-wire" =
        minted.protocol === "playwright-wire" || minted.playwright_wire
            ? "playwright-wire"
            : "cdp";

    if (expectedEngine === "chromium" && protocol !== "cdp") {
        throw new Error(
            `chromium connect expected protocol=cdp, got ${protocol} (engine=${engine}). ` +
                (minted.client_hint || ""),
        );
    }
    if (expectedEngine !== "chromium" && protocol !== "playwright-wire") {
        throw new Error(
            `${expectedEngine} connect expected protocol=playwright-wire, got ${protocol} ` +
                `(engine=${engine}). ${minted.client_hint || ""}`,
        );
    }

    const sid = sessionId;
    const url = minted.url;
    return {
        browserWSEndpoint: url,
        wsEndpoint: url,
        sessionId: sid,
        engine,
        protocol,
        expiresIn: minted.expires_in_seconds ?? 120,
        close: async () => {
            await source.request("POST", `/v1/sessions/${encodeURIComponent(sid)}/release`, {});
        },
    };
}

/**
 * Chromium CDP connect — for Puppeteer AND Playwright `connectOverCDP`.
 *
 * Usage:
 *   const conn = await chromium.connect(client, { claimOs: "windows" });
 *   await puppeteer.connect({ browserWSEndpoint: conn.browserWSEndpoint, defaultViewport: null });
 *   // or: await pw.chromium.connectOverCDP(conn.browserWSEndpoint);
 */
export const chromium = {
    connect: async (
        source: CdpMintSource,
        options: GhostCrawlConnectOptions = {},
    ): Promise<GhostCrawlConnection> =>
        mintConnection(source, { ...options, engine: options.engine ?? "chromium" }, "chromium"),
    ignoreDefaultArgs: ["--enable-automation", "--enable-unsafe-swiftshader"] as const,
    buildArgs(extra: readonly string[] = []): string[] {
        const argv = [...extra];
        assertNoAutomationTells(argv);
        return argv;
    },
};

/**
 * Firefox Playwright-wire connect.
 *
 * Usage:
 *   const conn = await firefox.connect(client, { claimOs: "windows", claimBrowser: "firefox" });
 *   const browser = await pw.firefox.connect(conn.wsEndpoint);
 *
 * Puppeteer cannot attach here — use {@link chromium.connect}.
 */
export const firefox = {
    connect: async (
        source: CdpMintSource,
        options: GhostCrawlConnectOptions = {},
    ): Promise<GhostCrawlConnection> =>
        mintConnection(source, { ...options, engine: options.engine ?? "firefox" }, "firefox"),
};

/**
 * WebKit Playwright-wire connect.
 *
 * Usage:
 *   const conn = await webkit.connect(client, { claimOs: "ios", claimBrowser: "safari" });
 *   const browser = await pw.webkit.connect(conn.wsEndpoint);
 *
 * Puppeteer cannot attach here — use {@link chromium.connect}.
 */
export const webkit = {
    connect: async (
        source: CdpMintSource,
        options: GhostCrawlConnectOptions = {},
    ): Promise<GhostCrawlConnection> =>
        mintConnection(source, { ...options, engine: options.engine ?? "webkit" }, "webkit"),
};

/**
 * Legacy single-entry `connect` — chromium CDP only (Puppeteer / PW connectOverCDP).
 * Prefer {@link chromium.connect} / {@link firefox.connect} / {@link webkit.connect}.
 */
export async function connect(
    source: CdpMintSource,
    options: GhostCrawlConnectOptions = {},
): Promise<GhostCrawlConnection> {
    const engine = (options.engine ||
        engineForClaim(options.claimOs, options.claimBrowser)) as
        | "chromium"
        | "firefox"
        | "webkit";
    if (engine !== "chromium") {
        throw new Error(
            `connect() is the chromium CDP helper. For ${engine} use ${engine}.connect() ` +
                `with playwright.${engine}.connect(url). puppeteer-core cannot attach to ` +
                `firefox/webkit (Chrome CDP only).`,
        );
    }
    return chromium.connect(source, options);
}

/**
 * Puppeteer guidance — chromium CDP only. FF/WK are Playwright-wire (not Puppeteer).
 */
export const PUPPETEER_GUIDE = {
    requiredConnectOptions: { defaultViewport: null },
    engines: ["chromium"] as const,
    note:
        "defaultViewport must be null: Puppeteer's 800x600 default is a physically impossible " +
        "window and reads as a bot. The engine's identity carries the real viewport. " +
        "puppeteer-core speaks Chrome CDP only — use chromium sessions. firefox/webkit BYO " +
        "is Playwright-wire (playwright.firefox.connect / playwright.webkit.connect).",
    example:
        'const browser = await puppeteer.connect({ browserWSEndpoint: conn.browserWSEndpoint, ' +
        "defaultViewport: null });",
} as const;
