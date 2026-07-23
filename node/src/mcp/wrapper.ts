/**
 * GhostCrawlMCPClient — hand-written MCP wrapper.
 *
 * A standalone MCP transport client (independent of the @ghostcrawl/sdk REST
 * client). Provides typed async methods over the native GhostCrawl MCP server's
 * tool surface (ghostcrawl.mcp.tools.TOOL_REGISTRY — the ghostcrawl_* data-plane
 * and act_* browser-primitive tools), reconciled to the canonical registry names
 * by canonicalTool() below. This is an OPTIONAL convenience client — any standard
 * MCP client can drive the same hosted server.
 *
 * Transport: StreamableHTTPClientTransport (current; replaces deprecated SSE).
 * Security: API key passed as Bearer token in Authorization header only.
 *   No --api-key CLI arg, no process.argv exposure.
 *
 * Return type is Promise<unknown> — MCP server tool output schemas are absent
 * from openapi/v1.json (Q2). `unknown` forces callers to narrow, satisfying
 * Typed interfaces, not any.
 *
 * Each call opens a fresh MCP client connection and closes it in finally{}.
 * This matches the Python wrapper's per-call session pattern.
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

// ─── Canonical tool-name reconciliation (D-11) ──────────────────────────────
// The native GhostCrawl MCP server (ghostcrawl.mcp.tools.TOOL_REGISTRY) exposes
// every tool under the canonical `ghostcrawl_*` (data-plane) / `act_*` (browser
// primitive) / `action_record_*` namespaces — NOT the bare `navigate` / `act`
// aliases the retired standalone server used. This wrapper keeps ergonomic method
// names but reconciles each call to the real registry tool name before it hits the
// wire, so it drives the native streamable-HTTP server directly.
const TOOL_NAMES: Record<string, string> = {
  navigate: "ghostcrawl_navigate",
  act: "ghostcrawl_act",
  act_on: "ghostcrawl_act",
  observe: "ghostcrawl_observe",
  extract: "ghostcrawl_extract",
  scrape: "ghostcrawl_scrape",
  screenshot: "ghostcrawl_screenshot",
  screenshot_of: "ghostcrawl_screenshot",
  search: "ghostcrawl_search",
  google_search: "ghostcrawl_search",
  map_site: "ghostcrawl_map",
  pdf: "ghostcrawl_pdf",
  crawl: "ghostcrawl_crawl",
  eval: "act_evaluate",
  run_script: "ghostcrawl_script_run",
  upload_file: "act_upload",
  start: "ghostcrawl_session_create",
  end: "ghostcrawl_session_terminate",
  start_recording: "action_record_start",
  stop_recording: "action_record_stop",
  ping: "ping", // server health tool is registered literally as `ping`
};

const CANONICAL_PREFIXES = ["ghostcrawl_", "act_", "action_"];

/** Map a wrapper method's logical name to the real MCP registry tool name. */
function canonicalTool(name: string): string {
  if (name in TOOL_NAMES) return TOOL_NAMES[name];
  if (name === "ping" || CANONICAL_PREFIXES.some((p) => name.startsWith(p))) return name;
  return `ghostcrawl_${name}`;
}

/** Options accepted by GhostCrawlMCPClient constructor. */
export interface GhostCrawlMCPClientOptions {
  /** Full URL to the MCP HTTP endpoint, e.g. http://localhost:8090/mcp */
  mcpUrl: string;
  /** GhostCrawl API key — sourced from GHOSTCRAWL_API_KEY env var by callers */
  apiKey: string;
}

export class GhostCrawlMCPClient {
  private readonly mcpUrl: string;
  private readonly apiKey: string;

  constructor(options: GhostCrawlMCPClientOptions) {
    const { mcpUrl, apiKey } = options;
    if (!mcpUrl || typeof mcpUrl !== "string") {
      throw new TypeError("mcpUrl is required and must be a non-empty string");
    }
    if (!apiKey || typeof apiKey !== "string") {
      throw new TypeError("apiKey is required and must be a non-empty string");
    }
    this.mcpUrl = mcpUrl;
    this.apiKey = apiKey;
  }

  /** Create a connected MCP Client for a single tool call. */
  private async createClient(): Promise<Client> {
    const transport = new StreamableHTTPClientTransport(new URL(this.mcpUrl), {
      requestInit: {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
        },
      },
    });
    const client = new Client({ name: "ghostcrawl-sdk", version: "0.2.0" });
    await client.connect(transport);
    return client;
  }

  /** Invoke a named MCP tool with arguments. Handles connect + close lifecycle. */
  private async callTool(
    name: string,
    args: Record<string, unknown>
  ): Promise<unknown> {
    const client = await this.createClient();
    try {
      // Reconcile to the canonical native-registry tool name (ghostcrawl_*/act_*).
      return await client.callTool({ name: canonicalTool(name), arguments: args });
    } finally {
      await client.close();
    }
  }

  // ─── Navigation & Interaction Tools ────────────────────────────────────────

  /** Navigate the browser to a URL. Required: url. */
  async navigate(params: { url: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("navigate", params);
  }

  /** Perform an action described in natural language. Required: goal. */
  async act(params: { goal: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("act", params);
  }

  /** Observe the current page state and return structured data. */
  async observe(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("observe", params);
  }

  /** Extract structured data from the current page. */
  async extract(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("extract", params);
  }

  // ─── Page Capture Tools ─────────────────────────────────────────────────────

  /** Scrape a URL and return content. Required: url. */
  async scrape(params: { url: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("scrape", params);
  }

  /** Take a screenshot of the page or a URL. */
  async screenshot(params: { url?: string; [key: string]: unknown } = {}): Promise<unknown> {
    return this.callTool("screenshot", params);
  }

  /** Take a screenshot of a specific DOM selector. Required: selector. */
  async screenshot_of(params: { selector: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("screenshot_of", params);
  }

  /** Perform an action on a specific element. Required: selector, goal. */
  async act_on(params: {
    selector: string;
    goal: string;
    [key: string]: unknown;
  }): Promise<unknown> {
    return this.callTool("act_on", params);
  }

  /** Capture network activity on the current page. */
  async network(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("network", params);
  }

  /** Capture a DOM snapshot of the current page. */
  async dom_snapshot(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("dom_snapshot", params);
  }

  /** Scroll on the current page. */
  async scroll(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("scroll", params);
  }

  /** Wait for a condition or duration on the current page. */
  async wait(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("wait", params);
  }

  /** Evaluate JavaScript on the current page. */
  async eval(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("eval", params);
  }

  /** Retrieve cookies from the current page context. */
  async cookies(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("cookies", params);
  }

  // ─── Crawl Tools ────────────────────────────────────────────────────────────

  /** Start a crawl operation. */
  async crawl(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("crawl", params);
  }

  // ─── Dataset Tools ──────────────────────────────────────────────────────────

  /** Interact with a dataset resource. */
  async dataset(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("dataset", params);
  }

  // ─── Script Tools ───────────────────────────────────────────────────────────

  /** Execute a server-side script. */
  async run_script(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("run_script", params);
  }

  // ─── Session Lifecycle Tools ─────────────────────────────────────────────────

  /** Start a new browser session. */
  async start(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("start", params);
  }

  /** End an active browser session. */
  async end(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("end", params);
  }

  /** Start multiple browser sessions. */
  async start_many(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("start_many", params);
  }

  /** End all active browser sessions. */
  async end_all(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("end_all", params);
  }

  // ─── File I/O Tools ──────────────────────────────────────────────────────────

  /** Upload a file to the browser session. */
  async upload_file(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("upload_file", params);
  }

  /** Download a file from the browser session. */
  async download_file(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("download_file", params);
  }

  // ─── Network & Storage Tools ─────────────────────────────────────────────────

  /** Capture HAR network trace. */
  async network_har(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("network_har", params);
  }

  /** Get or set browser storage state. */
  async storage_state(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("storage_state", params);
  }

  // ─── Recording Tools ─────────────────────────────────────────────────────────

  /** List available recordings. */
  async list_recordings(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("list_recordings", params);
  }

  /** Get a specific recording. */
  async get_recording(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("get_recording", params);
  }

  /** Start a new recording. */
  async start_recording(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("start_recording", params);
  }

  /** Stop an active recording. */
  async stop_recording(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("stop_recording", params);
  }

  /** Delete a recording. */
  async delete_recording(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("delete_recording", params);
  }

  /**
   * Health-check tool.  Returns 'pong'.  Verifies server is reachable.
   * Mirrors the server-side @mcp.tool() ping() in ghostcrawl_mcp_server/server.py.
   */
  async ping(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("ping", params);
  }

  // ─── Search Tools ────────────────────────────────────────────

  /** Search the web and return structured results. Required: query. */
  async search(params: { query: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("search", params);
  }

  /** Search Google or a Google vertical and return SERP results. Required: query. */
  async google_search(params: { query: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("google_search", params);
  }

  // ─── Site Map Tools ───────────────────────────────────────────

  /** Map all pages on a website starting from a URL. Required: url. */
  async map_site(params: { url: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("map_site", params);
  }

  /** Retrieve previously discovered links for a domain. Required: domain. */
  async discovery(params: { domain: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("discovery", params);
  }

  // ─── Identity / Profile Tools ─────────────────────────────────

  /** Materialise a fresh browser identity. */
  async identity(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("identity", params);
  }

  /** Create, get, list, delete, or view recent browser profiles. */
  async profiles(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("profiles", params);
  }

  // ─── PDF Tool ─────────────────────────────────────────────────

  /** Render a web page to PDF. Required: url. */
  async pdf(params: { url: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("pdf", params);
  }

  // ─── Key-Value Store ──────────────────────────────────────────

  /** Read, write, or delete entries in the persistent key-value store. */
  async kv(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("kv", params);
  }

  // ─── Schedule Tools ───────────────────────────────────────────

  /** Create, list, get, update, or delete recurring schedules. */
  async schedule(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("schedule", params);
  }

  // ─── Webhook Tools ────────────────────────────────────────────

  /** Register, list, inspect, retry, or rotate secrets for webhooks. */
  async webhook(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("webhook", params);
  }

  // ─── Budget / Usage Tools ─────────────────────────────────────

  /** Manage spending controls and view usage for the account. */
  async budget(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("budget", params);
  }

  // ─── Unblock Tool ─────────────────────────────────────────────

  /** Retrieve a URL reliably through the managed browser fleet. Required: url. */
  async unblock(params: { url: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("unblock", params);
  }

  // ─── Lighthouse Tool ──────────────────────────────────────────

  /** Run a performance and quality audit on a web page. Required: url. */
  async lighthouse(params: { url: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("lighthouse", params);
  }

  // ─── Queue Tools ──────────────────────────────────────────────

  /** Push, pop, acknowledge, or view stats for a named task queue. */
  async queue(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("queue", params);
  }

  // ─── Self-host / Account Utilities ────────────────────────────

  /** Check for available platform updates. */
  async check_updates(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("check_updates", params);
  }

  /** Obtain a short-lived container image pull token. */
  async registry_token(params: Record<string, unknown> = {}): Promise<unknown> {
    return this.callTool("registry_token", params);
  }

  // ─── Takeover Tools ───────────────────────────────────────────

  /** Mint a short-lived token to take live control of a session. Required: session_id. */
  async takeover_token(params: { session_id: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("takeover_token", params);
  }

  /** Release a live-view token for a session. Required: session_id. */
  async takeover_release(params: { session_id: string; [key: string]: unknown }): Promise<unknown> {
    return this.callTool("takeover_release", params);
  }
}
