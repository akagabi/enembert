import json
from enembert.labeling.consistency import elements_found, spearman


def grade_correlation(predictor, gold_rows, corpus):
    xs, ys = [], []
    n_full = n_low = 0
    c5_full_sum = c5_low_sum = 0
    for r in gold_rows:
        eid = r["essay_id"]
        spans_per_para = predictor(eid)
        n_elems = len(elements_found(spans_per_para))
        c5 = corpus[eid]["c5"]
        xs.append(n_elems)
        ys.append(c5)
        if n_elems == 5:
            n_full += 1; c5_full_sum += c5
        elif n_elems <= 1:
            n_low += 1; c5_low_sum += c5
    return {"spearman": round(spearman(xs, ys), 3),
            "mean_c5_full": round(c5_full_sum / n_full, 1) if n_full else None,
            "mean_c5_low": round(c5_low_sum / n_low, 1) if n_low else None,
            "n": len(gold_rows), "n_full": n_full, "n_low": n_low}
