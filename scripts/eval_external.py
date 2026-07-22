"""Benchmark enemBERT against REAL published ENEM grades from outside the training corpus.

This is the honest out-of-distribution check: essays collected from INEP's Cartilha
do Participante and UOL's Banco de Redações, each verified ABSENT from the
kamel-usp training data, each carrying a published per-competency human grade.

THIS SCRIPT IS THE RECORD OF A NEGATIVE RESULT. It is what killed the C5 score
estimate: on n=30 the estimator's rank correlation with real human C5 grades was
0.347 with a 95% CI of [-0.02, 0.65] — indistinguishable from chance. The score
was removed from the demo; the estimator's coefficients survive only as
docs/reports/score_model_v1.json so this measurement stays reproducible.
See docs/reports/score-estimate-negative-result.md.

Usage:
    python scripts/eval_external.py [MODEL_DIR]        # default runs/model/final
    SCORE_MODEL=path/to/score_model.json python scripts/eval_external.py ...

Reads `data/external_benchmark/essays.json` (gitignored — it holds copyrighted
essay text, so it stays local and is never committed or published). Only
aggregate numbers from this script belong in reports.

Note on grids: UOL grades competencies on a 50-point scale (0/50/100/150/200)
while the model predicts on the ENEM 40-point grid, so exact equality is not a
fair metric. Rank correlation is grid-agnostic and is the number to watch.
"""
import json
import os
import sys

import numpy as np
from transformers import AutoModelForTokenClassification, AutoTokenizer

from enembert.data.paragraphs import split_paragraphs
from enembert.training.predict import predict_spans

ELEMENTS = ["AGENTE", "ACAO", "MEIO", "EFEITO", "DETALHAMENTO"]
BANDS = [0, 40, 80, 120, 160, 200]
ESSAYS = "data/external_benchmark/essays.json"


def estimate_c5(scorer, found, n_spans):
    """Mirrors the browser scorer exactly: 5 presence flags + n_elements + n_spans."""
    feat = [1.0 if e in found else 0.0 for e in ELEMENTS] + [float(len(found)), float(n_spans)]
    logits = [
        scorer["intercept"][c] + sum(scorer["coef"][c][j] * feat[j] for j in range(len(feat)))
        for c in range(len(scorer["classes"]))
    ]
    idx = int(np.argmax(logits))
    c5 = scorer["classes"][idx]
    rng = scorer["total_range_by_c5"][str(c5)]
    return c5, rng["p10"], rng["p90"]


def main():
    model_dir = sys.argv[1] if len(sys.argv) > 1 else "runs/model/final"
    scorer = json.load(open(os.environ.get("SCORE_MODEL", "docs/reports/score_model_v1.json")))
    essays = json.load(open(ESSAYS))
    tok = AutoTokenizer.from_pretrained(model_dir)
    net = AutoModelForTokenClassification.from_pretrained(model_dir)
    net.eval()
    print(f"### model: {model_dir}   essays: {len(essays)}")

    rows = []
    for e in essays:
        paras = split_paragraphs(e["essay_text"])
        spans = [predict_spans(net, tok, p, tail=(len(paras) == 1)) for p in paras]
        # match the demo: ignore 1-2 char spans, they are model noise
        found = {s.label for ps in spans for s in ps
                 if len(e["essay_text"]) and s.end - s.start >= 3}
        n_spans = sum(1 for ps in spans for s in ps if s.end - s.start >= 3)
        c5, tlo, thi = estimate_c5(scorer, found, n_spans)
        rows.append({"id": e["id"], "total": e.get("total_score"), "c5_real": e.get("c5_score"),
                     "c5_pred": c5, "found": sorted(found), "total_lo": tlo, "total_hi": thi})

    print(f"{'essay':34}{'realC5':>7}{'ourC5':>7}{'total':>7}{'our range':>11}  elements")
    print("-" * 92)
    for r in rows:
        hit = ""
        if r["total"] is not None:
            hit = " ok" if r["total_lo"] <= r["total"] <= r["total_hi"] else " miss"
        rng = f"{r['total_lo']}-{r['total_hi']}"
        print(f"{r['id'][:34]:34}{str(r['c5_real']):>7}{r['c5_pred']:>7}"
              f"{str(r['total']):>7}{rng:>11}{hit}  {','.join(x[:4] for x in r['found'])}")

    from scipy.stats import spearmanr
    wc = [r for r in rows if r["c5_real"] is not None]
    if len(wc) > 2:
        p = np.array([r["c5_pred"] for r in wc]); t = np.array([r["c5_real"] for r in wc])
        print(f"\nvs published C5 (n={len(wc)}): MAE={np.mean(np.abs(p - t)):.0f}pts  "
              f"within-50={np.mean(np.abs(p - t) <= 50):.0%}  within-100={np.mean(np.abs(p - t) <= 100):.0%}")
        print(f"  Spearman(our C5, real C5) = {spearmanr(p, t).correlation:.3f}   <- headline")
    wt = [r for r in rows if r["total"] is not None]
    if len(wt) > 2:
        p = np.array([r["c5_pred"] for r in wt]); t = np.array([r["total"] for r in wt])
        inr = np.mean([r["total_lo"] <= r["total"] <= r["total_hi"] for r in wt])
        print(f"vs published TOTAL (n={len(wt)}): Spearman={spearmanr(p, t).correlation:.3f}  "
              f"real total inside shown range: {inr:.0%}")


if __name__ == "__main__":
    main()
