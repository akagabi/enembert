from enembert.schema import Span
from enembert.labeling.agreement import span_f1, corpus_f1


def test_exact_match():
    g = [Span(0, 5, "AGENTE")]
    assert span_f1(g, [Span(0, 5, "AGENTE")], "exact")[2] == 1.0
    assert span_f1(g, [Span(0, 4, "AGENTE")], "exact")[2] == 0.0


def test_overlap_match():
    g = [Span(0, 10, "ACAO")]
    assert span_f1(g, [Span(2, 10, "ACAO")], "overlap")[2] == 1.0
    assert span_f1(g, [Span(2, 10, "MEIO")], "overlap")[2] == 0.0


def test_empty_both_is_perfect():
    assert span_f1([], [], "overlap")[2] == 1.0


def test_precision_recall_with_partial_matches():
    # 2 gold, 3 pred, 1 true positive: prec = 1/3, rec = 1/2.
    g = [Span(0, 5, "AGENTE"), Span(10, 20, "ACAO")]
    p = [Span(0, 5, "AGENTE"), Span(30, 40, "MEIO"), Span(50, 60, "EFEITO")]
    prec, rec, f1 = span_f1(g, p, "exact")
    assert prec == 1 / 3
    assert rec == 1 / 2
    assert f1 == 2 * prec * rec / (prec + rec)


def test_greedy_matching_is_one_to_one():
    # Two identical pred spans competing for a single gold span must yield
    # only ONE true positive -- a matched gold index cannot be reused by a
    # second pred span. This is the guard that makes matching 1-to-1.
    g = [Span(0, 10, "ACAO")]
    p = [Span(0, 10, "ACAO"), Span(0, 10, "ACAO")]
    prec, rec, f1 = span_f1(g, p, "exact")
    assert prec == 0.5  # tp=1 / 2 preds, NOT tp=2 / 2 preds
    assert rec == 1.0
    assert abs(f1 - (2 * 0.5 * 1.0 / 1.5)) < 1e-9


def test_no_zero_division_when_pred_empty():
    g = [Span(0, 5, "AGENTE")]
    prec, rec, f1 = span_f1(g, [], "exact")
    assert (prec, rec, f1) == (0.0, 0.0, 0.0)


def test_no_zero_division_when_gold_empty():
    p = [Span(0, 5, "AGENTE")]
    prec, rec, f1 = span_f1([], p, "exact")
    assert (prec, rec, f1) == (0.0, 0.0, 0.0)


def test_overlap_jaccard_below_threshold_does_not_match():
    # intersection=3 (7..10), union = 10+10-3 = 17, jaccard = 3/17 < 0.5
    g = [Span(0, 10, "ACAO")]
    p = [Span(7, 17, "ACAO")]
    assert span_f1(g, p, "overlap")[2] == 0.0


def test_corpus_f1_hand_computed():
    # Two essays, one paragraph each. Worked out by hand below; corpus_f1
    # must reproduce these exact numbers, exercising the aggregation path
    # (per-element tp/g/p accumulation across essays), not just a single
    # span_f1 call.
    #
    # essay e1, paragraph 0:
    #   gold: AGENTE(0,5), ACAO(10,20), MEIO(30,40)
    #   pred: AGENTE(0,5) [exact tp], ACAO(10,20) [exact tp], EFEITO(50,60) [extra]
    #   -> AGENTE tp=1 g=1 p=1 | ACAO tp=1 g=1 p=1 | MEIO tp=0 g=1 p=0 | EFEITO tp=0 g=0 p=1
    #
    # essay e2, paragraph 0:
    #   gold: AGENTE(0,5), DETALHAMENTO(60,70)
    #   pred: AGENTE(0,4) [off-by-one, exact mismatch], DETALHAMENTO(60,70) [exact tp]
    #   -> AGENTE tp=0 g=1 p=1 | DETALHAMENTO tp=1 g=1 p=1
    #
    # Per-element totals (tp, g, p):
    #   AGENTE:       tp=1, g=2, p=2 -> P=0.5, R=0.5, F1=0.5
    #   ACAO:         tp=1, g=1, p=1 -> F1=1.0
    #   MEIO:         tp=0, g=1, p=0 -> P=0.0 (p=0), R=0.0, F1=0.0
    #   EFEITO:       tp=0, g=0, p=1 -> P=0.0, R=0.0 (g=0), F1=0.0
    #   DETALHAMENTO: tp=1, g=1, p=1 -> F1=1.0
    #
    # Micro totals: tp=3, g=5, p=5 -> P=0.6, R=0.6, F1=0.6
    gold_rows = {
        "e1": [[Span(0, 5, "AGENTE"), Span(10, 20, "ACAO"), Span(30, 40, "MEIO")]],
        "e2": [[Span(0, 5, "AGENTE"), Span(60, 70, "DETALHAMENTO")]],
    }
    pred_rows = {
        "e1": [[Span(0, 5, "AGENTE"), Span(10, 20, "ACAO"), Span(50, 60, "EFEITO")]],
        "e2": [[Span(0, 4, "AGENTE"), Span(60, 70, "DETALHAMENTO")]],
    }
    report = corpus_f1(gold_rows, pred_rows, "exact")
    assert report["micro_f1"] == 0.6
    assert report["per_element"] == {
        "AGENTE": 0.5,
        "ACAO": 1.0,
        "MEIO": 0.0,
        "EFEITO": 0.0,
        "DETALHAMENTO": 1.0,
    }


def test_corpus_f1_missing_pred_row_treated_as_empty():
    # An essay present in gold but absent from pred must contribute pure
    # false negatives, not raise (pred_rows.get(eid, ...) fallback path).
    gold_rows = {"e1": [[Span(0, 5, "AGENTE")]]}
    pred_rows = {}
    report = corpus_f1(gold_rows, pred_rows, "exact")
    assert report["micro_f1"] == 0.0
    assert report["per_element"] == {"AGENTE": 0.0}
