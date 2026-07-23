// Branded helpers — ghostcrawl-node User-Agent + raw Google SERP convenience
// reach. (no code copied from ScrapingBee — see THIRD-PARTY-NOTICES.md)

import * as os from "os";
// SDK_VERSION is generated from package.json by scripts/gen-version.mjs before
// every build. Reading it as a plain constant (instead of resolving package.json
// via createRequire(import.meta.url)) keeps the dual ESM+CJS build green —
// `import.meta` is a syntax error under the CommonJS build target.
import { SDK_VERSION } from "./version.js";

/**
 * Build the canonical User-Agent string for the ghostcrawl Node SDK.
 * Format: ghostcrawl-node/<version> Node/<v> <os>/<arch>
 */
export function uaString(): string {
    const v = SDK_VERSION || "0.0.0";
    return `ghostcrawl-node/${v} Node/${process.version} ${os.type()}/${os.arch()}`;
}

export interface GoogleHotelsOptions {
    adults?: number;
    rooms?: number;
    currency?: string;
    countryCode?: string;
    baseUrl?: string;
}

/**
 * Fetch Google Hotels (Travel) listings via POST /v1/google/hotels.
 *
 * Convenience peer of the Google SERP reach,
 * mirroring the Python `google_hotels` signature. Posts with branded UA + Bearer auth
 * and returns the parsed JSON SearchResult (hotels_results[] with name, price,
 * total_price, rating, amenities, booking_providers).
 *
 * @param checkIn  ISO 8601 (YYYY-MM-DD) — check_out must be after check_in (server-enforced).
 * @param checkOut ISO 8601 (YYYY-MM-DD).
 */
export async function googleHotels(
    apiKey: string,
    query: string,
    checkIn: string,
    checkOut: string,
    opts: GoogleHotelsOptions = {},
): Promise<unknown> {
    const baseUrl = (opts.baseUrl ?? "https://api.ghostcrawl.io").replace(/\/$/, "");
    const headers: Record<string, string> = {
        "User-Agent": uaString(),
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
    };
    const body = {
        q: query,
        check_in: checkIn,
        check_out: checkOut,
        adults: opts.adults ?? 2,
        rooms: opts.rooms ?? 1,
        currency: opts.currency ?? "USD",
        country_code: opts.countryCode ?? "us",
    };
    const resp = await fetch(`${baseUrl}/v1/google/hotels`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        throw new Error(`ghostcrawl googleHotels failed: HTTP ${resp.status}`);
    }
    return resp.json();
}

export interface GoogleSportsOptions {
    countryCode?: string;
    baseUrl?: string;
}

/**
 * Fetch the Google sports knowledge panel via POST /v1/google/sports.
 *
 * Convenience peer of the Google SERP reach,
 * mirroring the Python `google_sports` signature. Posts with branded UA + Bearer auth
 * and returns the parsed JSON SearchResult. The structured match + standings live under
 * `extras.sports_results` (match: {home_team, away_team, scores, status}; standings[]).
 */
export async function googleSports(
    apiKey: string,
    query: string,
    opts: GoogleSportsOptions = {},
): Promise<unknown> {
    const baseUrl = (opts.baseUrl ?? "https://api.ghostcrawl.io").replace(/\/$/, "");
    const headers: Record<string, string> = {
        "User-Agent": uaString(),
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
    };
    const body = {
        q: query,
        country_code: opts.countryCode ?? "us",
    };
    const resp = await fetch(`${baseUrl}/v1/google/sports`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
    });
    if (!resp.ok) {
        throw new Error(`ghostcrawl googleSports failed: HTTP ${resp.status}`);
    }
    return resp.json();
}
