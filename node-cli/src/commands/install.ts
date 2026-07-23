/**
 * `ghostcrawl install` — install the native binaries and/or license
 * token (parity with Python CLI).
 *
 * Behavior mirrors `sdks/python/ghostcrawl/cli/main.py::install`:
 *   - --license-token <path>  Write the token to ~/.ghostcrawl/license.token
 *                             mode 0600 (atomic rename). Requires the token
 *                             body to start with "ghc_".
 *   - --os <target>           Scope: only "linux-x86_64" supported.
 *   - --install-dir <path>    Target directory (default ~/.ghostcrawl).
 *
 * Reads GHOSTCRAWL_BINARY_URL from env for the binary download. Skips
 * download when only --license-token is provided AND the env var is unset.
 */
import { Command } from "commander";
import * as os from "node:os";
import * as path from "node:path";
import * as fs from "node:fs";
import { pipeline } from "node:stream/promises";

interface InstallOpts {
  os: string;
  licenseToken?: string;
  installDir: string;
}

export function installCommand(): Command {
  return new Command("install")
    .description("Download the GhostCrawl native binaries and/or write a license token")
    .option("--os <target>", "Target OS/arch (e.g. linux-x86_64)", "linux-x86_64")
    .option("--license-token <path>", "Path to a license token file (written 0600 to install-dir)")
    .option("--install-dir <path>", "Target install directory", path.join(os.homedir(), ".ghostcrawl"))
    .action(async (opts: InstallOpts) => {
      // ---- license token write (atomic, mode 0600) ----
      if (opts.licenseToken) {
        if (!fs.existsSync(opts.licenseToken)) {
          process.stderr.write(`Error: --license-token path does not exist: ${opts.licenseToken}\n`);
          process.exit(1);
        }
        const token = fs.readFileSync(opts.licenseToken, "utf-8").trim();
        if (!token) {
          process.stderr.write("Error: license token file is empty.\n");
          process.exit(1);
        }
        if (!token.startsWith("ghc_")) {
          process.stderr.write("Error: token format invalid (expect ghc_...)\n");
          process.exit(1);
        }

        fs.mkdirSync(opts.installDir, { recursive: true, mode: 0o700 });
        try {
          fs.chmodSync(opts.installDir, 0o700);
        } catch {
          // best-effort
        }

        const tmp = path.join(opts.installDir, "license.token.tmp");
        fs.writeFileSync(tmp, token, { mode: 0o600 });
        try {
          fs.chmodSync(tmp, 0o600);
        } catch {
          // best-effort
        }
        const finalPath = path.join(opts.installDir, "license.token");
        fs.renameSync(tmp, finalPath); // atomic POSIX rename

        process.stdout.write(`License token written to ${finalPath}\n`);

        // Token-only invocation: skip binary download when GHOSTCRAWL_BINARY_URL is unset.
        if (!(process.env["GHOSTCRAWL_BINARY_URL"] ?? "").trim()) {
          return;
        }
      }

      // ---- binary download ----
      if (opts.os !== "linux-x86_64") {
        process.stderr.write(
          "Cross-platform binaries land at FUTURE milestone; v1.6 supports linux-x86_64 only.\n",
        );
        process.exit(1);
      }

      const binaryUrl = (process.env["GHOSTCRAWL_BINARY_URL"] ?? "").trim();
      if (!binaryUrl) {
        process.stderr.write(
          "Error: GHOSTCRAWL_BINARY_URL environment variable is not set.\n" +
            "Set it to the operator-provided artifact URL before running `ghostcrawl install`.\n",
        );
        process.exit(1);
      }
      if (!binaryUrl.startsWith("https://")) {
        process.stderr.write(
          "Error: GHOSTCRAWL_BINARY_URL must use HTTPS for security. Please set a valid HTTPS URL.\n",
        );
        process.exit(1);
      }

      const targetDir = path.join(opts.installDir, "binaries");
      fs.mkdirSync(targetDir, { recursive: true });

      const filename = binaryUrl.replace(/\/$/, "").split("/").pop() || "ghostcrawl-binary";
      const dest = path.join(targetDir, filename);

      process.stdout.write(`Downloading ${binaryUrl} ...\n`);
      const response = await fetch(binaryUrl);
      if (!response.ok || !response.body) {
        process.stderr.write(`Error: download failed: HTTP ${response.status}\n`);
        process.exit(1);
      }
      // Stream to disk. Node's fetch returns a web ReadableStream; convert via Readable.fromWeb.
      const { Readable } = await import("node:stream");
      // @ts-expect-error Readable.fromWeb is available in Node >= 17; types may lag.
      const nodeStream = Readable.fromWeb(response.body);
      await pipeline(nodeStream, fs.createWriteStream(dest));
      process.stdout.write(`Saved ${dest}\n`);
    });
}
