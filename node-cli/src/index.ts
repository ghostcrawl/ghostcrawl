#!/usr/bin/env node
/**
 * @ghostcrawl/cli — GhostCrawl command-line interface.
 *
 * Command surface (parity with the Python CLI):
 *   ghostcrawl scrape <url>
 *   ghostcrawl crawl <url> [--max-depth N] [--out PATH]
 *   ghostcrawl session list
 *   ghostcrawl auth login
 *
 * API key: GHOSTCRAWL_API_KEY env var, or a key saved via `ghostcrawl init`.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { Command } from "commander";
import { scrapeCommand } from "./commands/scrape.js";
import { crawlCommand } from "./commands/crawl.js";
import { crawlRunsCommand } from "./commands/crawlRuns.js";
import { sessionCommand } from "./commands/session.js";
import { authCommand } from "./commands/auth.js";
import { mapCommand } from "./commands/map.js";
import { extractCommand } from "./commands/extract.js";
import { contentCommand } from "./commands/content.js";
import { screenshotCommand } from "./commands/screenshot.js";
import { pdfCommand } from "./commands/pdf.js";
import { searchCommand } from "./commands/search.js";
import { configCommand } from "./commands/config.js";
import { initCommand } from "./commands/init.js";
import { installCommand } from "./commands/install.js";

// Read the CLI version from package.json so `--version` never drifts from the
// published package. dist/index.js sits at dist/, so package.json is one level up.
function resolveVersion(): string {
  try {
    const here = dirname(fileURLToPath(import.meta.url));
    const pkg = JSON.parse(readFileSync(join(here, "..", "package.json"), "utf8")) as { version?: string };
    if (typeof pkg.version === "string" && pkg.version) return pkg.version;
  } catch {
    /* fall through to compile-time fallback */
  }
  return "2.3.0";
}

const program = new Command();
program
  .name("ghostcrawl")
  .description("GhostCrawl command-line interface")
  .version(resolveVersion());

program.addCommand(scrapeCommand());
program.addCommand(contentCommand());
program.addCommand(screenshotCommand());
program.addCommand(pdfCommand());
program.addCommand(crawlCommand());
program.addCommand(crawlRunsCommand());
program.addCommand(sessionCommand());
program.addCommand(authCommand());
program.addCommand(mapCommand());
program.addCommand(searchCommand());
program.addCommand(extractCommand());
program.addCommand(configCommand());
// Parity with Python CLI
program.addCommand(initCommand());
program.addCommand(installCommand());

program.parse();
