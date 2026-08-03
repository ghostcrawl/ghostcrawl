import { defineConfig } from "vitest/config";

// Dedicated config for the real-network parity-e2e sweep. It includes
// ONLY tests/parity_e2e.test.ts (the black-box CLI runner that hits the real backend)
// and deliberately excludes the offline unit suites under test/. No mocks/setup — this
// is the one suite that spawns the compiled CLI against the live cloud test tenant.
export default defineConfig({
  test: {
    include: ["tests/parity_e2e.test.ts"],
    testTimeout: 900_000,
    hookTimeout: 900_000,
    // Live-network sweep must not be parallelized with anything else.
    fileParallelism: false,
  },
});
