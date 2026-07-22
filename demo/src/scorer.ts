// Coarse Competência 5 band, derived from score_model.json (see
// scripts/calibrate_score.py). Deliberately NOT a score.
//
// An earlier version of this file predicted a 0-200 C5 value from a logistic
// head over the tagger's output. Measured against 30 externally-graded essays
// it correlated at rho=0.347, 95% CI [-0.02, 0.65] — indistinguishable from
// chance — and under-credited good essays specifically. It was removed.
//
// What replaced it is the only claim the data supports: essays where the model
// finds 3+ of the five elements historically scored higher than essays where it
// finds 0-2. That direction replicates on two independent evaluation sets. It is
// still a weak signal with heavily overlapping ranges, which is why every caveat
// below travels with the numbers rather than living in a comment.

export interface CoarseBand {
  /** Middle-half range of real human C5 grades for essays in this bucket. */
  lo: number;
  hi: number;
  median: number;
  /** How many graded essays this bucket was measured on. */
  n: number;
  /** The bucket the user is NOT in — shown so the overlap is visible. */
  otherLo: number;
  otherHi: number;
  otherMedian: number;
  /** Number of distinct elements found, and the 3+ threshold. */
  nElements: number;
  cut: number;
  /** True when the model found 3+ elements. */
  isHigh: boolean;
}

interface Bucket {
  min_elements: number;
  max_elements: number;
  lo: number;
  hi: number;
  median: number;
  n: number;
}

interface ScoreModel {
  kind: string;
  cut: number;
  buckets: Bucket[];
}

const MODEL_URL = 'score_model.json';

let cached: ScoreModel | null = null;
let inflight: Promise<ScoreModel> | null = null;

/** Fetches and caches score_model.json. Safe to call multiple times. */
export async function loadScoreModel(): Promise<ScoreModel> {
  if (cached) return cached;
  if (!inflight) {
    // BASE_URL is a path ("/" locally, "/enembert/" on Pages) and always ends
    // in a slash, so plain concatenation is correct — `new URL(x, BASE_URL)`
    // throws, since a bare path is not a valid URL base.
    inflight = fetch(import.meta.env.BASE_URL + MODEL_URL, { cache: 'no-cache' })
      .then((res) => {
        if (!res.ok) throw new Error(`falha ao carregar score_model.json: ${res.status}`);
        return res.json() as Promise<ScoreModel>;
      })
      .then((m) => {
        if (m.kind !== 'coarse_element_bands' || !Array.isArray(m.buckets) || m.buckets.length !== 2) {
          // Refuse an unexpected shape rather than render numbers we can't vouch for.
          throw new Error(`score_model.json tem formato inesperado: ${m.kind}`);
        }
        cached = m;
        return m;
      })
      .finally(() => {
        inflight = null;
      });
  }
  return inflight;
}

/**
 * Which coarse band this essay falls in, based purely on how many distinct
 * elements the tagger found. No logistic head, no length, no essay text.
 */
export function coarseBand(nElements: number): CoarseBand {
  if (!cached) throw new Error('score_model.json ainda não foi carregado');
  const isHigh = nElements >= cached.cut;
  const mine = cached.buckets[isHigh ? 1 : 0];
  const other = cached.buckets[isHigh ? 0 : 1];
  return {
    lo: mine.lo,
    hi: mine.hi,
    median: mine.median,
    n: mine.n,
    otherLo: other.lo,
    otherHi: other.hi,
    otherMedian: other.median,
    nElements,
    cut: cached.cut,
    isHigh,
  };
}
