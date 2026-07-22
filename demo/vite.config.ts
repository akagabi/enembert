import { createReadStream, existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig, type Plugin } from 'vite';

// onnxruntime-web ships several wasm builds and picks one at runtime. Left to
// itself it fetches the chosen build from cdn.jsdelivr.net, which means a third
// party sees every visitor of a page whose entire pitch is that nothing leaves
// the browser. We serve one build ourselves instead and pin the runtime to it.
//
// It has to be a plugin rather than an import: onnxruntime-web's `exports` field
// refuses deep imports of ./dist/*.mjs, so `import ... from '...asyncify.mjs?url'`
// fails to resolve. Copying at build time also keeps the 22 MB binary out of git.
const ORT_DIR = 'ort';
const ORT_FILES = [
  'ort-wasm-simd-threaded.asyncify.wasm',
  'ort-wasm-simd-threaded.asyncify.mjs',
];

/** Locate onnxruntime-web/dist without going through `exports`, which blocks it. */
function ortDistDir(): string {
  const here = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    join(here, 'node_modules/onnxruntime-web/dist'),
    join(here, 'node_modules/@huggingface/transformers/node_modules/onnxruntime-web/dist'),
  ];
  for (const dir of candidates) {
    if (existsSync(join(dir, ORT_FILES[0]))) return dir;
  }
  // Failing loudly matters: a silent miss here means the runtime quietly goes
  // back to fetching itself from cdn.jsdelivr.net, breaking the privacy claim
  // the page makes, and nothing else would notice.
  throw new Error(
    `self-host-onnxruntime: could not find ${ORT_FILES[0]} in any of:\n  ${candidates.join('\n  ')}`,
  );
}

function selfHostOnnxRuntime(): Plugin {
  const distDir = ortDistDir();
  return {
    name: 'self-host-onnxruntime',

    // dev + preview: serve them from node_modules at the same public path
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const name = ORT_FILES.find((f) => req.url?.includes(`/${ORT_DIR}/${f}`));
        if (!name) return next();
        res.setHeader('Content-Type', name.endsWith('.wasm') ? 'application/wasm' : 'text/javascript');
        createReadStream(join(distDir, name)).pipe(res);
      });
    },

    async generateBundle(_options, bundle) {
      for (const name of ORT_FILES) {
        this.emitFile({
          type: 'asset',
          fileName: `${ORT_DIR}/${name}`, // stable path, no hash: tagger.ts builds the URL
          source: await readFile(join(distDir, name)),
        });
      }

      // transformers.js also references the wasm via `new URL(..., import.meta.url)`,
      // so Vite emits its own hashed copy into assets/. Since tagger.ts pins
      // wasmPaths to the ort/ copy above, that one is never requested — verified in
      // the browser — and shipping it would double the deploy for nothing.
      for (const fileName of Object.keys(bundle)) {
        if (/^assets\/ort-wasm.*\.wasm$/.test(fileName)) {
          delete bundle[fileName];
        }
      }
    },
  };
}

// GitHub Pages serves this project from https://akagabi.github.io/enembert/, so
// asset URLs need that prefix in production. Anything reading BASE_URL at
// runtime — scorer.ts fetching score_model.json, tagger.ts building the ORT
// paths — picks this up automatically. Set VITE_BASE to override.
//
// Keyed on `mode`, NOT `command`: `vite preview` runs with command === 'serve'
// just like the dev server, so keying on command gave preview a base of '/'
// while the files it serves have '/enembert/' baked in at build time. Every
// asset request then missed and fell through to index.html with a 200 and
// Content-Type: text/html, so the page silently rendered nothing. Mode is
// 'production' for both build and preview, which is what we want: preview
// should be a faithful rehearsal of Pages.
export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? (process.env.VITE_BASE ?? '/enembert/') : '/',
  plugins: [selfHostOnnxRuntime()],
  build: {
    // The ONNX runtime wasm is far past any sensible warning threshold and is
    // meant to be big; silence the warning rather than pretend it's a problem.
    chunkSizeWarningLimit: 30_000,
  },
}));
