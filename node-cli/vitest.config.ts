import { defineConfig } from "vitest/config";

// Default `npm test` runs the OFFLINE unit suites only.
//
// tests/parity_e2e.test.ts is the live-network black-box sweep: it spawns the
// compiled CLI against the real cloud test tenant and hard-fails its auth gate
// when GHOSTCRAWL_API_KEY is unset (it fabricates nothing, by design). That is
// correct for a deliberate parity run and wrong for `npm test`, so it is
// excluded here and reached only through:
//
//   npm run test:parity                      # vitest.parity.config.ts
//   make -C sdks/node-cli parity-e2e         # builds SDK+CLI, flock-guarded
export default defineConfig({
  test: {
    include: ["test/**/*.test.ts"],
    exclude: ["tests/**", "node_modules/**", "dist/**"],
  },
});
