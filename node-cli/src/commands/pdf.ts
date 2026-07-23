import { Command } from "commander";
import { writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { getClient, emit, fail } from "../client.js";

export function pdfCommand(): Command {
  return new Command("pdf")
    .description("Render a URL to PDF via /v1/pdf (Chrome-only; writes PDF bytes to a file)")
    .argument("<url>", "URL to render to PDF")
    .option("--paper-format <fmt>", "Paper format (a4 | letter | legal | tabloid)", "a4")
    .option("--landscape", "Landscape orientation", false)
    .option("--out <path>", "Output file path (default: a temp file)")
    .option("--pretty", "Indent JSON output", false)
    .action(
      async (
        url: string,
        opts: { paperFormat: string; landscape: boolean; out?: string; pretty: boolean },
      ) => {
        const client = getClient();
        try {
          // Wraps the real node SDK pdf() method → POST /v1/pdf. PDF is Chrome-only:
          // pin a chrome identity_spec so the server's random identity draw is
          // deterministic (else a non-chrome draw 400s), mirroring the reference lanes.
          const bytes = await client.pdf({
            url,
            paperFormat: opts.paperFormat as "a4" | "letter" | "legal" | "tabloid",
            landscape: opts.landscape,
            engine: "chrome",
            identity_spec: { claim_os: "windows", claim_browser: "chrome", viewport: "fullscreen" },
          });
          const out = opts.out ?? join(tmpdir(), `ghostcrawl-page-${Date.now()}.pdf`);
          writeFileSync(out, bytes);
          emit({ url, bytes: bytes.length, path: out }, opts.pretty);
        } catch (e) {
          fail(e);
        }
      },
    );
}
