from enembert.training.baseline import baseline_spans


def test_finds_marked_elements():
    p = ("Portanto, o governo deve criar programas educativos, por meio de campanhas, "
         "a fim de reduzir o problema.")
    labels = {s.label for s in baseline_spans(p)}
    assert {"AGENTE", "ACAO", "MEIO", "EFEITO"} <= labels


def test_no_elements_in_plain_text():
    assert baseline_spans("O problema é grave no país.") == []
