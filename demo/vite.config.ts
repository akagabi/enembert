import { defineConfig } from 'vite';

// GitHub Pages serves this project from https://akagabi.github.io/enembert/, so
// asset URLs need that prefix in production. Locally (dev and `vite preview`)
// the app is served from the root, hence the conditional.
//
// Anything reading BASE_URL at runtime — scorer.ts fetching score_model.json —
// picks this up automatically. Set VITE_BASE to override for a different host.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? (process.env.VITE_BASE ?? '/enembert/') : '/',
  build: {
    // The ONNX runtime wasm is far past any sensible warning threshold and is
    // meant to be big; silence the warning rather than pretend it's a problem.
    chunkSizeWarningLimit: 30_000,
  },
}));
