import { Command } from "commander";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, appendFileSync, writeFileSync, renameSync } from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { getClient, emit, fail } from "../client.js";

/**
 * Resumable, plan-aware, machine-readable batch surface over the single-URL
 * scrape lane — parity with the Python CLI's `batch` command (which reads a
 * file of URLs, scrapes them in concurrency-bounded chunks via the batch
 * endpoint, writes NDJSON results, and checkpoints completed URLs so
 * `--resume` can skip them).
 */

interface Checkpoint {
  completed: string[];
}

function checkpointPath(inputFile: string): string {
  const abs = path.resolve(inputFile);
  const jobId = createHash("sha256").update(abs).digest("hex").slice(0, 16);
  const base = path.join(os.homedir(), ".ghostcrawl");
  mkdirSync(base, { recursive: true });
  return path.join(base, `batch-checkpoint-${jobId}.json`);
}

function loadCheckpoint(cpPath: string): Set<string> {
  try {
    const raw = readFileSync(cpPath, "utf-8");
    const data = JSON.parse(raw) as Checkpoint;
    if (Array.isArray(data.completed)) return new Set(data.completed.map(String));
  } catch {
    /* no checkpoint yet — normal on a fresh run */
  }
  return new Set();
}

function writeCheckpoint(cpPath: string, completed: Set<string>): void {
  // Atomic: write a temp file then rename it over the target. A crash mid-write
  // leaves the previous good checkpoint intact (a second writeFileSync would not
  // — a truncated JSON there makes --resume re-scrape everything, burning quota).
  const tmp = `${cpPath}.tmp`;
  writeFileSync(tmp, JSON.stringify({ completed: Array.from(completed).sort() }));
  renameSync(tmp, cpPath);
}

function readUrls(inputFile: string): string[] {
  const text = readFileSync(inputFile, "utf-8");
  const urls: string[] = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    urls.push(line);
  }
  return urls;
}

/** min(usage-reported cap, requested) — falls back to `requested` when the
 * /v1/me/usage report carries no concurrency field (a normal path, not an
 * error). */
function resolveConcurrency(usage: Record<string, unknown>, requested: number): number {
  let cap: number | undefined;
  for (const key of ["concurrency", "max_concurrency"]) {
    const val = usage[key];
    if (typeof val === "number") {
      cap = val;
      break;
    }
  }
  if (cap === undefined) {
    for (const parent of ["limits", "plan"]) {
      const nested = usage[parent];
      if (nested && typeof nested === "object") {
        const val = (nested as Record<string, unknown>)["concurrency"];
        if (typeof val === "number") {
          cap = val;
          break;
        }
      }
    }
  }
  if (cap === undefined) cap = requested;
  return Math.max(1, Math.min(cap, requested));
}

function chunk<T>(items: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += size) out.push(items.slice(i, i + size));
  return out;
}

export function batchCommand(): Command {
  return new Command("batch")
    .description("Batch-scrape every URL in --input-file, writing NDJSON to --output-dir")
    .requiredOption("--input-file <path>", "Text file of URLs, one per line (# comments allowed)")
    .requiredOption("--output-dir <path>", "Directory to write results.ndjson")
    .option("--concurrency <n>", "Max parallel scrapes; capped by the /usage plan limit", "5")
    .option("--resume", "Skip URLs already completed in the checkpoint for this input file", false)
    .action(
      async (opts: { inputFile: string; outputDir: string; concurrency: string; resume: boolean }) => {
        const client = getClient();
        try {
          let usage: Record<string, unknown> = {};
          try {
            usage = await client.usage();
          } catch {
            /* usage is best-effort — a missing cap falls back to --concurrency */
          }
          const requested = Number(opts.concurrency);
          if (!Number.isInteger(requested) || requested < 1) {
            throw new Error(
              `--concurrency must be a positive integer (got ${JSON.stringify(opts.concurrency)})`,
            );
          }
          const effectiveCap = resolveConcurrency(usage, requested);

          const allUrls = readUrls(opts.inputFile);
          const cpPath = checkpointPath(opts.inputFile);
          const already = opts.resume ? loadCheckpoint(cpPath) : new Set<string>();
          const work = allUrls.filter((u) => !already.has(u));
          const skipped = allUrls.length - work.length;

          mkdirSync(opts.outputDir, { recursive: true });
          const resultsPath = path.join(opts.outputDir, "results.ndjson");
          if (!existsSync(resultsPath)) writeFileSync(resultsPath, "");

          const completed = new Set(already);
          let completedCount = 0;
          let failedCount = 0;

          for (const group of chunk(work, effectiveCap)) {
            try {
              // POST /v1/scrape/batch — one call per concurrency-sized group,
              // mirroring the Python CLI's concurrency-bounded fan-out.
              const res = await client.scrapeBatch(group, {
                format: "html",
                javascript_enabled: false,
              });
              const results = Array.isArray((res as { results?: unknown[] }).results)
                ? ((res as { results?: unknown[] }).results as Array<Record<string, unknown>>)
                : [];
              // Associate each result with its URL by the result's own `url`
              // field when present (robust to reordering/dedup); fall back to
              // positional index only when the batch entry carries no url.
              const byUrl = new Map<string, Record<string, unknown>>();
              results.forEach((r) => {
                const u = r && typeof r.url === "string" ? r.url : undefined;
                if (u) byUrl.set(u, r);
              });
              for (let i = 0; i < group.length; i += 1) {
                const url = group[i];
                const result = byUrl.get(url) ?? results[i] ?? null;
                // A null/absent entry (or one flagged as an error) is a FAILED
                // URL — record it, count it as failed, and do NOT checkpoint it,
                // so --resume retries it instead of silently dropping it.
                const ok =
                  result !== null &&
                  typeof result === "object" &&
                  !("error" in result) &&
                  (result as Record<string, unknown>).status !== "error";
                appendFileSync(resultsPath, JSON.stringify({ url, result }) + "\n");
                if (ok) {
                  completed.add(url);
                  completedCount += 1;
                } else {
                  failedCount += 1;
                }
              }
              writeCheckpoint(cpPath, completed);
            } catch (e) {
              const msg = e instanceof Error ? `${e.name}: ${e.message}` : String(e);
              for (const url of group) {
                appendFileSync(resultsPath, JSON.stringify({ url, error: msg }) + "\n");
                failedCount += 1;
              }
            }
          }

          emit(
            {
              total: allUrls.length,
              completed: completedCount,
              failed: failedCount,
              skipped,
              concurrency: effectiveCap,
              output: resultsPath,
            },
            true,
          );
        } catch (e) {
          fail(e);
        }
      },
    );
}
