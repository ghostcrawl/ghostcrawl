export * from "./params.js";
export * from "./branded.js";
// Typed-but-index-accessible result types — the owned per-lane result
// surface the facade returns (raw Kiota models are never exposed).
export type {
    ScrapeResult,
    SearchResult,
    CrawlRun,
    Document,
    BinaryResult,
} from "./facade.js";
