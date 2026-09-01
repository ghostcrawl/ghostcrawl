// @ts-check
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

/**
 * Flat ESLint config for the hand-written SDK surface only.
 *
 * The Kiota-generated core lives under `_generated/` (and is symlinked in as
 * `src/_generated`). It is machine-emitted, ships as-is, and must never be
 * linted — so it is globally ignored below. We lint only the hand-authored
 * `src/*.ts` + `src/mcp/*.ts` facade at a meaningful (recommended) level.
 */
export default tseslint.config(
  {
    // Generated code + build output are never linted.
    ignores: [
      'src/_generated/**',
      '_generated/**',
      'dist/**',
      'node_modules/**',
      'examples/**',
      'scripts/**',
      '*.config.ts',
      '*.config.js',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    // The hand-written facade carries inline `eslint-disable` comments for the
    // type-aware rules (`no-unsafe-*`) that guard the untyped Kiota boundary.
    // We lint at the (fast, project-less) recommended level, so those rules are
    // not active here — don't flag their disable comments as "unused".
    linterOptions: {
      reportUnusedDisableDirectives: 'off',
    },
  },
  {
    files: ['src/**/*.ts'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
    },
    rules: {
      // Escape-hatch typing is used deliberately at the Kiota boundary; keep it
      // available but warn-free by requiring a description on suppressions.
      '@typescript-eslint/ban-ts-comment': [
        'error',
        { 'ts-ignore': 'allow-with-description', 'ts-expect-error': 'allow-with-description' },
      ],
      // The facade intentionally re-shapes untyped Kiota/JSON payloads.
      '@typescript-eslint/no-explicit-any': 'off',
      // Allow intentionally-unused args when prefixed with `_`.
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' },
      ],
    },
  },
);
