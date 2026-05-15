import { defineConfig } from 'vite';

// The dev server (`npm run dev`) serves from `/`. Production builds
// default to `/cardmirror/` so the bundle works when hosted at
// `https://ant981228.github.io/cardmirror/` (the GitHub Pages URL
// derived from the repo name). Override with `VITE_BASE=/foo/` if
// deploying somewhere else.
export default defineConfig(({ command }) => ({
  base:
    process.env['VITE_BASE'] ??
    (command === 'build' ? '/cardmirror/' : '/'),
}));
