// enemBERT tagger — runs entirely in the browser via transformers.js.
// The essay text passed to `tagParagraph` never leaves this machine: no network
// request is made with the essay content, only (once, at startup) the model
// weights themselves are fetched from a local path (dev) or Hugging Face (prod).
import {
  env,
  pipeline,
  type TokenClassificationPipeline,
  type ProgressInfo,
} from '@huggingface/transformers';

// Dev: load weights bundled under demo/public/models/ (gitignored, copied from
// runs/model/onnx/ by the build steps). Prod: fetch the published model from HF.
env.allowLocalModels = import.meta.env.DEV;   // dev: load bundled weights from /models/
env.allowRemoteModels = !import.meta.env.DEV;  // prod: stream from HF
env.localModelPath = '/models/';

// Pin the ONNX runtime to the copy we serve ourselves (see the
// self-host-onnxruntime plugin in vite.config.ts). Left unset, onnxruntime-web
// fetches its runtime -- a ~4.7 MB wasm plus JS glue -- from cdn.jsdelivr.net,
// which would let a third party see every visitor of a page whose whole pitch is
// that nothing leaves the browser.
//
// The explicit {wasm, mjs} pair matters: a bare path prefix would let the runtime
// pick a build variant we don't host and 404, and supplying only one of the two
// makes it ignore both and go to the CDN anyway.
const ortBase = `${import.meta.env.BASE_URL}ort/`;
const onnxWasm = env.backends?.onnx?.wasm;
if (onnxWasm) {
  onnxWasm.wasmPaths = {
    wasm: `${ortBase}ort-wasm-simd-threaded.asyncify.wasm`,
    mjs: `${ortBase}ort-wasm-simd-threaded.asyncify.mjs`,
  };
}

const MODEL_ID = import.meta.env.DEV ? 'enembert' : 'akagabi/enemBERT';

export const ELEMENTS = ['AGENTE', 'ACAO', 'MEIO', 'EFEITO', 'DETALHAMENTO'] as const;
export type Element = (typeof ELEMENTS)[number];

export interface TagSpan {
  start: number;
  end: number;
  label: Element;
  /** transformers.js confidence for this grouped entity, 0..1. */
  score: number;
}

/** Spans with a score below this are rendered "hedged" (dashed underline). */
export const LOW_CONFIDENCE_THRESHOLD = 0.6;

let pipe: TokenClassificationPipeline | null = null;

function isElement(x: string): x is Element {
  return (ELEMENTS as readonly string[]).includes(x);
}

/** @param onProgress called with an aggregate 0..100 download percentage. */
export async function loadModel(onProgress?: (p: number) => void): Promise<void> {
  pipe = (await pipeline('token-classification', MODEL_ID, {
    dtype: 'q8',
    progress_callback: (info: ProgressInfo) => {
      if (info.status === 'progress_total') {
        onProgress?.(info.progress);
      }
    },
  })) as TokenClassificationPipeline;
}

export function isModelLoaded(): boolean {
  return pipe !== null;
}

/**
 * The offsets contract: paragraphs are `text.split('\n')`, trimmed, empties
 * dropped — matching the Python `split_paragraphs` used throughout training.
 */
export function splitParagraphs(text: string): string[] {
  return text
    .split('\n')
    .map((p) => p.trim())
    .filter(Boolean);
}

export async function tagParagraph(paragraph: string): Promise<TagSpan[]> {
  if (!pipe) throw new Error('modelo ainda não carregado');
  if (!paragraph) return [];
  const out = await pipe(paragraph, { aggregation_strategy: 'simple' });
  // transformers.js does not return char offsets for this tokenizer, only the
  // grouped `word` text. Recover offsets by locating each entity's text in the
  // paragraph with a forward-moving cursor (verified exact on accented,
  // punctuated ENEM text). Skip anything we can't place, or punctuation-only
  // groups (occasional boundary noise), rather than mis-rendering.
  const spans: TagSpan[] = [];
  let cursor = 0;
  for (const e of out) {
    const label = e.entity_group;
    const word = (e.word ?? '').trim();
    if (label == null || !isElement(label) || !word) continue;
    if (!/\p{L}/u.test(word)) continue; // punctuation-only noise, e.g. a stray ","
    // A one-or-two-character "element" is model noise, never a real intervention
    // element (external testing surfaced a stray AGENTE span on the letter "a").
    if (word.length < 3) continue;
    const start = paragraph.indexOf(word, cursor);
    if (start < 0) continue;
    const end = start + word.length;
    cursor = end;
    spans.push({ start, end, label, score: e.score });
  }
  return spans;
}
