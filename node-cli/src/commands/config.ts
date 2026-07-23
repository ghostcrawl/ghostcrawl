import { Command } from "commander";
import { promises as fs } from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

function xdgConfigHome(): string {
  const raw = process.env["XDG_CONFIG_HOME"]?.trim();
  return raw && raw.length > 0 ? raw : path.join(os.homedir(), ".config");
}

function configPath(): string {
  return path.join(xdgConfigHome(), "ghostcrawl", "config.toml");
}

async function writeApiKey(key: string): Promise<string> {
  const p = configPath();
  await fs.mkdir(path.dirname(p), { recursive: true });
  const safe = key.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  await fs.writeFile(p, `api_key = "${safe}"\n`, { encoding: "utf-8", mode: 0o600 });
  return p;
}

async function readApiKey(): Promise<string | null> {
  const p = configPath();
  try {
    const txt = await fs.readFile(p, "utf-8");
    for (const raw of txt.split(/\r?\n/)) {
      const line = raw.trim();
      if (!line || line.startsWith("#")) continue;
      if (!line.startsWith("api_key")) continue;
      const idx = line.indexOf("=");
      if (idx < 0) continue;
      let rhs = line.slice(idx + 1).trim();
      if (rhs.startsWith('"') && rhs.endsWith('"')) {
        rhs = rhs.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, "\\");
      }
      return rhs || null;
    }
  } catch { return null; }
  return null;
}

export function configCommand(): Command {
  const cfg = new Command("config").description("API key + base URL configuration");

  cfg.command("set-key")
    .description("Persist API key to $XDG_CONFIG_HOME/ghostcrawl/config.toml")
    .argument("<key>", "Your ghostcrawl API key")
    .action(async (key: string) => {
      const p = await writeApiKey(key);
      console.log(`Wrote key to ${p}`);
    });

  cfg.command("show")
    .description("Print persisted config key (masked)")
    .action(async () => {
      const key = await readApiKey();
      if (!key) { console.error(`No key set. Path: ${configPath()}`); process.exit(1); }
      const masked = key.length > 12 ? `${key.slice(0, 7)}…${key.slice(-4)}` : "***";
      console.log(`api_key = ${masked}`);
      console.log(`Path: ${configPath()}`);
    });

  return cfg;
}
