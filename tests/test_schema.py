from enembert.schema import LABELS, ELEMENTS, Span, spans_to_bio, bio_to_spans

def test_labels_fixed_order():
    assert LABELS[0] == "O" and len(LABELS) == 11
    assert LABELS[1:3] == ["B-AGENTE", "I-AGENTE"]
    assert LABELS[9:] == ["B-DETALHAMENTO", "I-DETALHAMENTO"]

def test_bio_roundtrip():
    text = "o MEC deve criar campanhas"
    toks = [(0, 1), (2, 5), (6, 10), (11, 16), (17, 26)]
    spans = [Span(2, 5, "AGENTE"), Span(11, 26, "ACAO")]
    tags = spans_to_bio(text, spans, toks)
    assert tags == ["O", "B-AGENTE", "O", "B-ACAO", "I-ACAO"]
    assert bio_to_spans(toks, tags) == [Span(2, 5, "AGENTE"), Span(11, 26, "ACAO")]

def test_partial_token_overlap_counts():
    toks = [(0, 4), (4, 8)]
    spans = [Span(2, 6, "MEIO")]
    assert spans_to_bio("abcdabcd", spans, toks) == ["B-MEIO", "I-MEIO"]
