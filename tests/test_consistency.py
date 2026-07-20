from enembert.schema import Span
from enembert.labeling.consistency import elements_found, spearman

def test_elements_found_distinct():
    spans = [[Span(0, 2, "AGENTE")], [Span(0, 2, "AGENTE"), Span(3, 5, "ACAO")]]
    assert elements_found(spans) == {"AGENTE", "ACAO"}

def test_spearman_perfect_and_inverse():
    assert abs(spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1.0) < 1e-9
    assert abs(spearman([1, 2, 3, 4], [40, 30, 20, 10]) + 1.0) < 1e-9
