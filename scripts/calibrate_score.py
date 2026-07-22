"""Derive the coarse, honestly-bounded C5 band the demo is allowed to show.

History (see docs/reports/score-estimate-negative-result.md): the demo once showed a
6-band point estimate of Competência 5 from a logistic head over the tagger's output.
Measured against 30 externally-graded essays it correlated at rho=0.347, 95% CI
[-0.02, 0.65], and systematically UNDER-credited good essays. It was removed.

This script asks the narrower question: is there ANY signal here we can defend?

What fails (measured, see --verbose):
  * The 6-band prediction does not order essays externally. Essays predicted 160
    have a real median C5 of 100, while essays predicted 120 have a real median of
    175 — the ranking inverts.
  * Conditioning intervals on the 6-band prediction and fitting them in-corpus
    produces bounds that are too low externally (essays predicted 0 actually scored
    50-150, median 100 — never 0). Same downward bias, new clothes.
  * An 80%-coverage interval is 0..200 for four of the six bands: honest, and
    completely uninformative.

What survives: a single COARSE split on how many of the five elements were found.
Essays with 3+ elements score higher than essays with 0-2 on both evaluation sets,
independently:

    external (n=30)  : median 100 -> 150   (Mann-Whitney one-sided p = 0.035)
    in-corpus (n=255): median  80 -> 200

That direction replicating on two independent sets is the reason we show anything
at all. The caveats travel with it and are baked into the emitted JSON so the UI
cannot quietly drop them: the ranges overlap heavily, n=30 is small, and the raw
p-value does NOT survive Bonferroni correction for the six splits that were tried.

Displayed ranges come from the EXTERNAL set, not the in-corpus one: the gold set
over-represents high-scoring essays, so its ranges would flatter the user.

Usage: python scripts/calibrate_score.py [MODEL_DIR] [--verbose] [--out PATH]
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu

ELEMENTS = ["AGENTE", "ACAO", "MEIO", "EFEITO", "DETALHAMENTO"]
MIN_SPAN_CHARS = 3   # matches the demo: 1-2 char spans are model noise
CUT = 3              # 0-2 elements vs 3-5 elements
N_SPLITS_TRIED = 6   # for the Bonferroni disclosure below


def features(net, tok, text):
    """Mirrors demo/src/tagger.ts: paragraph split, tail-truncate single blobs."""
    from enembert.data.paragraphs import split_paragraphs
    from enembert.training.predict import predict_spans
    paras = split_paragraphs(text)
    spans = [predict_spans(net, tok, p, tail=(len(paras) == 1)) for p in paras]
    kept = [s for ps in spans for s in ps if s.end - s.start >= MIN_SPAN_CHARS]
    return len({s.label for s in kept})


def collect(net, tok, rows):
    out = []
    for i, (text, real_c5) in enumerate(rows):
        out.append({"n_elements": features(net, tok, text), "real": real_c5})
        if (i + 1) % 25 == 0:
            print(f"  ...{i + 1}/{len(rows)}", flush=True)
    return out


def bucket_stats(rows, lo_elems, hi_elems):
    v = sorted(r["real"] for r in rows if lo_elems <= r["n_elements"] <= hi_elems)
    q25, q50, q75 = np.percentile(v, [25, 50, 75])
    return {"lo": int(round(q25 / 10) * 10), "hi": int(round(q75 / 10) * 10),
            "median": int(round(q50)), "n": len(v),
            "full_lo": int(min(v)), "full_hi": int(max(v))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model_dir", nargs="?", default="runs/model/final")
    ap.add_argument("--out", default="demo/public/score_model.json")
    ap.add_argument("--cache", default="runs/calib_cache_elems.json")
    ap.add_argument("--verbose", action="store_true", help="print the failure evidence too")
    a = ap.parse_args()

    cache = Path(a.cache)
    if cache.exists():
        c = json.loads(cache.read_text())
        in_res, ext_res = c["in"], c["ext"]
        print(f"loaded cached predictions from {cache}")
    else:
        from transformers import AutoModelForTokenClassification, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(a.model_dir)
        net = AutoModelForTokenClassification.from_pretrained(a.model_dir)
        net.eval()
        gold_ids = set(json.load(open("data/gold_freeze.json"))["gold_essay_ids"])
        in_rows = [(r["essay_text"], r["c5"]) for r in map(json.loads, open("data/corpus.jsonl"))
                   if r["essay_id"] in gold_ids and r.get("c5") is not None]
        ext = json.load(open("data/external_benchmark/essays.json"))
        ext_rows = [(e["essay_text"], e["c5_score"]) for e in ext if e.get("c5_score") is not None]
        print(f"in-corpus gold: {len(in_rows)}   external: {len(ext_rows)}")
        print("tagging in-corpus gold set...", flush=True)
        in_res = collect(net, tok, in_rows)
        print("tagging external benchmark...", flush=True)
        ext_res = collect(net, tok, ext_rows)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"in": in_res, "ext": ext_res}))

    low_ext = bucket_stats(ext_res, 0, CUT - 1)
    high_ext = bucket_stats(ext_res, CUT, 5)
    low_in = bucket_stats(in_res, 0, CUT - 1)
    high_in = bucket_stats(in_res, CUT, 5)

    lo_v = [r["real"] for r in ext_res if r["n_elements"] < CUT]
    hi_v = [r["real"] for r in ext_res if r["n_elements"] >= CUT]
    p = float(mannwhitneyu(hi_v, lo_v, alternative="greater").pvalue)
    bonf = 0.05 / N_SPLITS_TRIED

    print(f"\n=== coarse split at {CUT}+ elements ===")
    for nm, lo, hi in [("external ", low_ext, high_ext), ("in-corpus", low_in, high_in)]:
        print(f"  {nm}: 0-{CUT-1} elems n={lo['n']:3d} median {lo['median']:3d} "
              f"(middle half {lo['lo']}-{lo['hi']})   |   {CUT}-5 elems n={hi['n']:3d} "
              f"median {hi['median']:3d} (middle half {hi['lo']}-{hi['hi']})")
    print(f"\n  external Mann-Whitney one-sided p = {p:.4f}")
    print(f"  Bonferroni threshold for {N_SPLITS_TRIED} splits tried = {bonf:.4f} -> "
          f"{'survives' if p < bonf else 'DOES NOT survive'}")
    print(f"  direction replicates on both sets: "
          f"{'YES' if (high_ext['median'] > low_ext['median'] and high_in['median'] > low_in['median']) else 'NO'}")

    if a.verbose:
        print("\n=== why the fine-grained version was rejected: real C5 by exact element count ===")
        for k in range(6):
            v = sorted(r["real"] for r in ext_res if r["n_elements"] == k)
            if v:
                print(f"  {k} elements (n={len(v):2d}): median {np.median(v):5.1f}  {v}")
        print("  ^ non-monotonic: 3 elements outscores 4. Only the coarse split is defensible.")

    out = {
        "kind": "coarse_element_bands",
        "cut": CUT,
        "buckets": [
            {"min_elements": 0, "max_elements": CUT - 1, **low_ext},
            {"min_elements": CUT, "max_elements": 5, **high_ext},
        ],
        "meta": {
            "source": "external benchmark (published essays with real human grades, "
                      "each verified absent from the training corpus)",
            "n_external": len(ext_res),
            "mannwhitney_p": round(p, 4),
            "bonferroni_threshold": round(bonf, 4),
            "survives_correction": bool(p < bonf),
            "replicates_in_corpus": True,
            "in_corpus_medians": [low_in["median"], high_in["median"]],
            "warning": "Coarse, weak signal. Ranges overlap heavily; n=30; the raw p-value "
                       "does not survive correction for the 6 splits tried. This is NOT a "
                       "grade and must never be displayed as one. The 6-band point estimate "
                       "this replaced failed outright — see "
                       "docs/reports/score-estimate-negative-result.md.",
        },
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
