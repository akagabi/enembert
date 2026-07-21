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
env.allowRemoteModels = !import.meta.env.DEV;
env.localModelPath = '/models/';

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
  const spans: TagSpan[] = [];
  for (const e of out) {
    const label = e.entity_group;
    if (
      label != null &&
      isElement(label) &&
      typeof e.start === 'number' &&
      typeof e.end === 'number'
    ) {
      spans.push({ start: e.start, end: e.end, label, score: e.score });
    }
  }
  return spans;
}
