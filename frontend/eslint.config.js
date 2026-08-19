import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      // TanStack file routes intentionally export their Route definitions, and
      // several shared UI modules export both components and typed constants.
      'react-refresh/only-export-components': 'off',
      // Existing API boundaries are progressively typed; keep visibility in CI
      // without blocking production builds while those contracts are narrowed.
      '@typescript-eslint/no-explicit-any': 'warn',
      // Data-backed forms legitimately hydrate local controls after queries.
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
])
