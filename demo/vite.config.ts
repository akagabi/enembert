import { defineConfig } from 'vite';

// GitHub Pages serves this project from https://akagabi.github.io/enembert/, so
// asset URLs need that prefix in production. Anything reading BASE_URL at
// runtime — scorer.ts fetching score_model.json — picks this up automatically.
// Set VITE_BASE to override for a different host.
//
// Keyed on `mode`, NOT `command`: `vite preview` runs with command === 'serve'
// just like the dev server, so keying on command gave preview a base of '/'
// while the files it serves have '/enembert/' baked in from build time. Every
// asset request then missed and fell through to index.html with a 200 and
// Content-Type: text/html, so the page silently rendered nothing. Mode is
// 'production' for both build and preview, which is what we actually want:
// preview should be a faithful rehearsal of Pages.
export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? (process.env.VITE_BASE ?? '/enembert/') : '/',
  build: {
    // The ONNX runtime wasm is far past any sensible warning threshold and is
    // meant to be big; silence the warning rather than pretend it's a problem.
    chunkSizeWarningLimit: 30_000,
  },
}));
