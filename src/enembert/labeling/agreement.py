from collections import defaultdict
from enembert.schema import Span


def _jaccard(a: Span, b: Span) -> float:
    inter = max(0, min(a.end, b.end) - max(a.start, b.start))
    union = (a.end - a.start) + (b.end - b.start) - inter
    return inter / union if union else 0.0


def _is_match(g: Span, p: Span, mode: str) -> bool:
    if g.label != p.label:
        return False
    if mode == "exact":
        return (g.start, g.end) == (p.start, p.end)
    return _jaccard(g, p) >= 0.5


def _count_matches(gold: list[Span], pred: list[Span], mode: str) -> int:
    """Greedy 1-to-1 span matching, shared by span_f1 and corpus_f1.

    Each gold span may match at most one pred span and vice versa: once a
    gold index is used it is skipped for the rest of the preds, so a second
    pred span overlapping an already-matched gold span never counts as a
    second true positive. Returns the true-positive count.
    """
    used: set[int] = set()
    tp = 0
    for p in pred:
        for i, g in enumerate(gold):
            if i in used:
                continue
            if _is_match(g, p, mode):
                used.add(i)
                tp += 1
                break
    return tp


def span_f1(gold: list[Span], pred: list[Span], mode: str) -> tuple[float, float, float]:
    if not gold and not pred:
        return (1.0, 1.0, 1.0)
    tp = _count_matches(gold, pred, mode)
    prec = tp / len(pred) if pred else 0.0
    rec = tp / len(gold) if gold else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return (prec, rec, f1)


def corpus_f1(gold_rows: dict, pred_rows: dict, mode: str) -> dict:
    """Aggregate per-element and micro-averaged F1 across a whole corpus.

    gold_rows / pred_rows: {essay_id: [[Span, ...] per paragraph, ...]}.
    An essay present in gold but missing from pred is treated as empty
    predictions for every paragraph (pure false negatives), never an error.
    """
    per = defaultdict(lambda: {"tp": 0, "g": 0, "p": 0})
    for eid, gold_paras in gold_rows.items():
        pred_paras = pred_rows.get(eid, [[] for _ in gold_paras])
        for g_spans, p_spans in zip(gold_paras, pred_paras):
            for el in {s.label for s in g_spans} | {s.label for s in p_spans}:
                g = [s for s in g_spans if s.label == el]
                p = [s for s in p_spans if s.label == el]
                tp = _count_matches(g, p, mode)
                per[el]["tp"] += tp
                per[el]["g"] += len(g)
                per[el]["p"] += len(p)

    def f(d):
        prec = d["tp"] / d["p"] if d["p"] else 0.0
        rec = d["tp"] / d["g"] if d["g"] else 0.0
        return round(2 * prec * rec / (prec + rec), 3) if prec + rec else 0.0

    tot = {"tp": sum(d["tp"] for d in per.values()),
           "g": sum(d["g"] for d in per.values()),
           "p": sum(d["p"] for d in per.values())}
    return {"micro_f1": f(tot), "per_element": {el: f(d) for el, d in per.items()}}
