import { defineConfig } from "vitest/config";

// Dedicated config for the real-network parity-e2e runner.
// It deliberately OMITS test/setup.ts (the MSW mock-server setupFile, which runs
// with onUnhandledRequest:"error"): this is the ONE suite that must hit the real
// cloud test tenant, so no request interception. The default vitest.config.ts
// (MSW-mocked unit tests) is unchanged.
export default defineConfig({
  test: {
    include: ["test/parity_e2e.test.ts"],
    environment: "node",
    testTimeout: 1_800_000, // 30 min — live-network sweep
    hookTimeout: 120_000,
  },
});
