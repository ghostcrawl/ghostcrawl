// Adapted from ScrapingBee/scrapingbee-node ergonomics patterns
// (no code copied — see THIRD-PARTY-NOTICES.md)

/**
 * Base64-encode a JavaScript snippet string for use with the js_snippet param.
 */
export function encodeJsSnippet(code: string): string {
    return Buffer.from(code, "utf-8").toString("base64");
}

/**
 * Stringify a cookie dict to "key=value; key2=value2" format.
 */
export function formatCookies(cookies: Record<string, string>): string {
    return Object.entries(cookies).map(([k, v]) => `${k}=${v}`).join("; ");
}

/**
 * JSON-encode extract_rules for the schema param.
 */
export function buildExtractRules(rules: Record<string, unknown>): string {
    return JSON.stringify(rules);
}

/**
 * JSON-encode a js_scenario step list.
 */
export function buildJsScenario(steps: unknown[]): string {
    return JSON.stringify(steps);
}

/**
 * Number/boolean-safe emptiness check.
 *
 * Returns false for the number 0 and the boolean false — both are valid API
 * values that a naive `!value` falsiness test would wrongly drop. Strings are
 * empty when whitespace-only; arrays/objects when they carry no elements/keys.
 *
 * Forward-adapted from ScrapingBee/scrapingbee-node `is_empty()` (no code
 * copied — ghostcrawl idiom).
 */
export function isEmpty(value: unknown): boolean {
    if (value === null || value === undefined) {
        return true;
    }
    if (typeof value === "number") {
        // 0 (and even NaN) is a present value, not "empty".
        return false;
    }
    if (typeof value === "boolean") {
        // false is a present value, not "empty".
        return false;
    }
    if (typeof value === "string") {
        return value.trim().length === 0;
    }
    if (Array.isArray(value)) {
        return value.length === 0;
    }
    if (typeof value === "object") {
        return Object.keys(value as Record<string, unknown>).length === 0;
    }
    return false;
}

/**
 * JSON-encode any dict/list param values; String()-coerce everything else
 * Ensures complex params reach the API as string-encoded JSON.
 *
 * Forward-adapted from the langchain-scrapingbee `stringify_nested_objects()`
 * technique (no code copied — ghostcrawl idiom).
 */
export function stringifyNestedObjects(
    params: Record<string, unknown>,
): Record<string, string> {
    const out: Record<string, string> = {};
    for (const [key, value] of Object.entries(params)) {
        if (value !== null && typeof value === "object") {
            // Arrays and plain objects both JSON-encode.
            out[key] = JSON.stringify(value);
        } else {
            out[key] = String(value);
        }
    }
    return out;
}

/**
 * Like {@link formatCookies}, but URL-encodes each cookie value.
 *
 * Use when the cookie string is destined for a URL/query context; the plain
 * {@link formatCookies} joiner is preserved unchanged for header contexts.
 *
 * URL-encodes each cookie name/value pair (ghostcrawl idiom).
 */
export function formatCookiesEncoded(cookies: Record<string, string>): string {
    return Object.entries(cookies)
        .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
        .join("; ");
}
