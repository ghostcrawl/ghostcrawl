import { Command } from "commander";
import { writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { getClient, emit, fail } from "../client.js";

export function screenshotCommand(): Command {
  return new Command("screenshot")
    .description("Capture a screenshot via /v1/screenshot (writes image bytes to a file)")
    .argument("<url>", "URL to screenshot")
    .option("--format <fmt>", "Image format (png | jpeg | webp)", "png")
    .option("--full-page", "Capture the full scrollable page", false)
    .option("--selector <css>", "CSS selector scoping the capture to one element")
    .option("--out <path>", "Output file path (default: a temp file)")
    .option("--pretty", "Indent JSON output", false)
    .action(
      async (
        url: string,
        opts: { format: string; fullPage: boolean; selector?: string; out?: string; pretty: boolean },
      ) => {
        const client = getClient();
        try {
          // Wraps the real node SDK screenshot() method (Plan 02) → POST /v1/screenshot.
          // The route serves raw image bytes (Uint8Array), so write them to a file and
          // emit a small JSON manifest (path + byte count) to stdout.
          const options: { url: string; format?: string; full_page?: boolean; screenshot_selector?: string } = {
            url,
            format: opts.format,
            full_page: opts.fullPage,
          };
          if (opts.selector) options.screenshot_selector = opts.selector;
          const bytes = await client.screenshot(options);
          const out = opts.out ?? join(tmpdir(), `ghostcrawl-screenshot-${Date.now()}.${opts.format}`);
          writeFileSync(out, bytes);
          emit({ url, format: opts.format, bytes: bytes.length, path: out }, opts.pretty);
        } catch (e) {
          fail(e);
        }
      },
    );
}
