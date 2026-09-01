/**
 * `ghostcrawl init` — interactive first-time setup (parity with the fixed
 * Python CLI).
 *
 * Resolves the API key (GHOSTCRAWL_API_KEY env wins, else a hidden stdin
 * prompt), validates it against the REAL auth path a working key passes — a
 * no-spend `GET /v1/me` when it accepts the key type, otherwise a trivial
 * `POST /v1/scrape` (never the old `/v1/profiles` false-negative path) — then
 * writes ~/.config/ghostcrawl/config.toml mode 0600 (XDG-compliant) and prints
 * EXACTLY ONE truthful outcome (never a "could not validate" warning AND a
 * "key validated" line at once).
 *
 * Security: the API key is read from stdin/env only — never passed as a CLI
 * argument, so it is not visible in ps(1) or shell history, and is never echoed.
 */
import { Command } from "commander";
import * as os from "node:os";
import * as path from "node:path";
import * as fs from "node:fs";
import * as readline from "node:readline";
import { createGhostCrawlClient } from "@ghostcrawl/sdk";

function _configDir(): string {
  const xdg = (process.env["XDG_CONFIG_HOME"] ?? "").trim();
  const base = xdg || path.join(os.homedir(), ".config");
  return path.join(base, "ghostcrawl");
}

function _configPath(): string {
  return path.join(_configDir(), "config.toml");
}

async function _promptHidden(question: string): Promise<string> {
  // Disable terminal echo while reading the API key.
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true });
  const stdout = process.stdout as NodeJS.WriteStream & { _writeToOutput?: (s: string) => void };
  // Suppress echo by overriding the prompt's output writer.
  const origWrite = stdout._writeToOutput;
  return await new Promise<string>((resolve) => {
    rl.question(question, (answer: string) => {
      rl.close();
      process.stdout.write("\n");
      resolve(answer);
    });
    // Squelch echoed bytes after the question prompt is printed.
    stdout._writeToOutput = function (stringToWrite: string) {
      if (stringToWrite === question || stringToWrite.includes(question)) {
        if (origWrite) origWrite.call(stdout, stringToWrite);
      }
      // else: drop (suppress echo)
    };
    rl.on("close", () => {
      stdout._writeToOutput = origWrite;
    });
  });
}

/** HTTP status carried by an SDK/transport error, across the shapes it may take. */
function _statusOf(e: unknown): number | undefined {
  return (
    (e as { statusCode?: number })?.statusCode ??
    (e as { response?: { status?: number } })?.response?.status
  );
}

/**
 * No-spend key probe against `GET /v1/me`. Returns `true` ONLY on a 2xx
 * (the endpoint exists AND accepts this key — zero scrape spend). Any non-2xx
 * (404/405 endpoint absent; 401/403 wrong key type) or transport error returns
 * `false` so the caller falls back to the real `POST /v1/scrape` auth path — a
 * `/v1/me` non-200 is NEVER a final auth verdict. Only attempted for live-format
 * keys (`gck_live_`); the key rides only in the Authorization header over HTTPS.
 */
async function _probeMeNoSpend(apiKey: string, baseUrl: string): Promise<boolean> {
  if (!apiKey.startsWith("gck_live_")) return false;
  try {
    const client = createGhostCrawlClient({ token: apiKey, baseUrl });
    // request() resolves on 2xx and throws (carrying statusCode) otherwise.
    await client.request("GET", "/v1/me");
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate `apiKey` against the REAL auth path a working key passes:
 * prefer a no-spend `GET /v1/me`; otherwise fall back to a trivial
 * `POST /v1/scrape` — the exact path a working `gck_live_` key passes. Throws on
 * genuine rejection (401) or transport failure; never calls `/v1/profiles`.
 */
async function _validateKey(apiKey: string, baseUrl: string): Promise<void> {
  if (await _probeMeNoSpend(apiKey, baseUrl)) return;
  const client = createGhostCrawlClient({ token: apiKey, baseUrl });
  await client.scrape({ url: "https://example.com", javascript: false });
}

function _writeConfig(apiKey: string): string {
  const dir = _configDir();
  fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
  try {
    fs.chmodSync(dir, 0o700);
  } catch {
    // best-effort
  }
  const configPath = _configPath();
  fs.writeFileSync(configPath, `api_key = "${apiKey}"\n`, { mode: 0o600 });
  try {
    fs.chmodSync(configPath, 0o600);
  } catch {
    // best-effort
  }
  return configPath;
}

export function initCommand(): Command {
  return new Command("init")
    .description("Interactive first-time setup: resolve/prompt for the API key and write config.toml")
    .action(async () => {
      const baseUrl = (process.env["GHOSTCRAWL_BASE_URL"] ?? "").trim() || "https://api.ghostcrawl.io";

      // Surface the resolution order (env wins over the home config file).
      process.stdout.write(
        "Resolution order: GHOSTCRAWL_API_KEY env > ~/.config/ghostcrawl/config.toml\n",
      );

      const envKey = (process.env["GHOSTCRAWL_API_KEY"] ?? "").trim();
      let apiKey: string;
      if (envKey) {
        apiKey = envKey;
        process.stdout.write("Using the key from GHOSTCRAWL_API_KEY (env overrides config.toml).\n");
      } else {
        apiKey = (await _promptHidden("GhostCrawl API key: ")).trim();
      }
      if (!apiKey) {
        process.stderr.write("Error: API key cannot be empty.\n");
        process.exit(1);
      }

      // Validate against the real auth path, then emit exactly ONE outcome.
      try {
        await _validateKey(apiKey, baseUrl);
      } catch (e: unknown) {
        if (_statusOf(e) === 401) {
          process.stderr.write("Key rejected (401). Run `ghostcrawl init` again with the correct key.\n");
          process.exit(1);
        }
        // Transient/transport failure: save so a network hiccup does not block
        // the user, but say so plainly — never a warning AND "validated".
        const configPath = _writeConfig(apiKey);
        const name = (e as { name?: string })?.name ?? "Error";
        process.stderr.write(
          `Saved to ${configPath}, but could not verify the key (check network/key): ${name}.\n`,
        );
        return;
      }

      const configPath = _writeConfig(apiKey);
      process.stdout.write(`Config written to ${configPath}; key validated.\n`);
    });
}
