from enembert.schema import Span
from enembert.training.evaluate import grade_correlation


def test_grade_correlation_positive_when_more_elements_higher_c5():
    # fake corpus: 4 essays, more elements -> higher real C5
    corpus = {f"e{i}": {"essay_id": f"e{i}", "essay_text": "p", "c5": c5}
              for i, c5 in enumerate([0, 80, 160, 200])}
    gold_rows = [{"essay_id": f"e{i}"} for i in range(4)]
    # predictor returns i distinct elements for essay e{i}
    ELEMS = ["AGENTE", "ACAO", "MEIO", "EFEITO", "DETALHAMENTO"]
    def predictor(essay_id):
        i = int(essay_id[1:])
        return [[Span(0, 1, ELEMS[j]) for j in range(i + 1)]]  # 1..4 distinct elements
    out = grade_correlation(predictor, gold_rows, corpus)
    assert out["spearman"] > 0.9
    assert out["n"] == 4
