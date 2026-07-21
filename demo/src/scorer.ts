// enemBERT demo — Competência 5 score estimator.
//
// A tiny multinomial logistic regression (6 classes: 0/40/80/120/160/200),
// trained offline on tagger-output features and shipped as static JSON
// (demo/public/score_model.json — coefficients only, no essay text, safe to
// commit). Everything below runs client-side; nothing is sent to a server.
//
// This estimates Competência 5 ONLY. It is not a grader: no other rubric
// competência (grammar, argumentation, cohesion, etc.) is evaluated here.
import { ELEMENTS, type Element, type TagSpan } from './tagger';

export interface ScoreModelRange {
  p10: number;
  p50: number;
  p90: number;
  n: number;
}

export interface ScoreModel {
  features: string[];
  classes: number[];
  coef: number[][];
  intercept: number[];
  total_range_by_c5: Record<string, ScoreModelRange>;
  meta: { qwk_c5: number; note: string };
}

export interface C5Estimate {
  /** Argmax class (one of the model's 6 C5 bands: 0/40/80/120/160/200). */
  c5: number;
  /** Softmax probability per class, same order as model.classes. */
  probs: number[];
  /** Lower bound of the honest confidence range around `c5` (a C5 band). */
  rangeLo: number;
  /** Upper bound of the honest confidence range around `c5` (a C5 band). */
  rangeHi: number;
  /** Historical total-score p10 for essays that landed in the `c5` band. */
  totalLo: number;
  /** Historical total-score p90 for essays that landed in the `c5` band. */
  totalHi: number;
}

const MODEL_URL = '/score_model.json';

/** Minimum probability mass the honest confidence range must cover. */
const RANGE_TARGET_MASS = 0.7;

let cachedModel: ScoreModel | null = null;
let modelPromise: Promise<ScoreModel> | null = null;

/** Fetches and caches /score_model.json. Safe to call multiple times. */
export function loadScoreModel(): Promise<ScoreModel> {
  if (!modelPromise) {
    modelPromise = fetch(MODEL_URL)
      .then((res) => {
        if (!res.ok) throw new Error(`falha ao carregar score_model.json: ${res.status}`);
        return res.json() as Promise<ScoreModel>;
      })
      .then((model) => {
        cachedModel = model;
        return model;
      })
      .catch((err) => {
        modelPromise = null; // allow a retry on the next call
        throw err;
      });
  }
  return modelPromise;
}

function buildFeatures(spansPerParagraph: TagSpan[][]): number[] {
  const found = new Set<Element>();
  let nSpans = 0;
  for (const spans of spansPerParagraph) {
    for (const s of spans) {
      found.add(s.label);
      nSpans += 1;
    }
  }
  const hasFlags = ELEMENTS.map((e) => (found.has(e) ? 1 : 0));
  // Must match model.features order exactly (element-based only — essay length was
  // deliberately dropped because it dominated the model and made a good short essay
  // score low; the estimate now comes from the intervention content):
  // has_AGENTE, has_ACAO, has_MEIO, has_EFEITO, has_DETALHAMENTO, n_elements, n_spans
  return [...hasFlags, found.size, nSpans];
}

function softmax(logits: number[]): number[] {
  const max = Math.max(...logits);
  const exps = logits.map((l) => Math.exp(l - max));
  const sum = exps.reduce((a, b) => a + b, 0);
  return exps.map((e) => e / sum);
}

/**
 * Smallest contiguous run of class indices around `centerIdx` whose combined
 * probability mass reaches `targetMass`. Grows one step at a time toward
 * whichever open neighbor currently holds more mass, so the range stays as
 * tight as the actual distribution allows instead of always widening evenly.
 */
function contiguousRange(probs: number[], centerIdx: number, targetMass: number): [number, number] {
  let lo = centerIdx;
  let hi = centerIdx;
  let mass = probs[centerIdx];
  while (mass < targetMass && (lo > 0 || hi < probs.length - 1)) {
    const leftMass = lo > 0 ? probs[lo - 1] : -Infinity;
    const rightMass = hi < probs.length - 1 ? probs[hi + 1] : -Infinity;
    if (rightMass >= leftMass) {
      hi += 1;
      mass += probs[hi];
    } else {
      lo -= 1;
      mass += probs[lo];
    }
  }
  return [lo, hi];
}

/**
 * Estimates Competência 5 from the whole essay's tagger output.
 * Requires `loadScoreModel()` to have resolved at least once before calling.
 */
export function estimateC5(spansPerParagraph: TagSpan[][]): C5Estimate {
  if (!cachedModel) {
    throw new Error('score model not loaded — call and await loadScoreModel() first');
  }
  const model = cachedModel;
  const x = buildFeatures(spansPerParagraph);

  const logits = model.coef.map(
    (row, c) => model.intercept[c] + row.reduce((sum, w, j) => sum + w * x[j], 0),
  );
  const probs = softmax(logits);

  let argmax = 0;
  for (let i = 1; i < probs.length; i++) {
    if (probs[i] > probs[argmax]) argmax = i;
  }

  const [loIdx, hiIdx] = contiguousRange(probs, argmax, RANGE_TARGET_MASS);
  const c5 = model.classes[argmax];
  const range = model.total_range_by_c5[String(c5)];

  return {
    c5,
    probs,
    rangeLo: model.classes[loIdx],
    rangeHi: model.classes[hiIdx],
    totalLo: range.p10,
    totalHi: range.p90,
  };
}
