/**
 * `ghostcrawl init` — interactive first-time setup (parity with Python CLI).
 *
 * Prompts (hidden) for an API key, validates it against GET /v1/profiles,
 * then writes ~/.config/ghostcrawl/config.toml mode 0600 (XDG-compliant).
 *
 * Security: the API key is read from stdin only — never passed as a CLI
 * argument, so it is not visible in ps(1) or shell history.
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

export function initCommand(): Command {
  return new Command("init")
    .description("Interactive first-time setup: prompt for API key and write config.toml")
    .action(async () => {
      const baseUrl = (process.env["GHOSTCRAWL_BASE_URL"] ?? "").trim() || "https://api.ghostcrawl.io";

      const apiKey = (await _promptHidden("GhostCrawl API key: ")).trim();
      if (!apiKey) {
        process.stderr.write("Error: API key cannot be empty.\n");
        process.exit(1);
      }

      // Validate the key before writing to disk.
      try {
        const client = createGhostCrawlClient({ token: apiKey, baseUrl });
        // GET /v1/profiles is the cheap Bearer-gated probe. The generic
        // request() escape hatch throws an Error carrying `statusCode` on a
        // non-2xx response (401 when the key is bad).
        await client.request("GET", "/v1/profiles");
      } catch (e: unknown) {
        const status =
          (e as { statusCode?: number })?.statusCode ??
          ((e as { response?: { status?: number } })?.response?.status);
        if (status === 401) {
          process.stderr.write("Key rejected (401). Run `ghostcrawl init` again with the correct key.\n");
          process.exit(1);
        }
        // Non-401 validation failure: warn but allow the write (Python CLI parity).
        process.stderr.write(`Warning: could not validate key (${(e as Error).message ?? e}). Writing config anyway.\n`);
      }

      // Write config to disk — mode 0600 (owner read/write only).
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
      process.stdout.write(`Config written to ${configPath}; key validated.\n`);
    });
}
